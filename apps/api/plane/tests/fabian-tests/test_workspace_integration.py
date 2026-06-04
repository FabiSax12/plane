"""
 * Author: Fabián Vargas
 * Test cases: PI-07, PI-08, PI-09, PI-10, PI-11, PI-12
"""

import pytest
from unittest.mock import patch
from rest_framework import status

from plane.db.models import (
    ProjectMember,
    Workspace,
    WorkspaceMember,
    WorkspaceMemberInvite,
)
from plane.tests.factories import ProjectFactory, UserFactory, WorkspaceFactory


# ---------------------------------------------------------------------------
# PI-11 — Role × action permission matrix
# ---------------------------------------------------------------------------
# 3 numeric roles (20=Admin, 15=Member, 5=Guest) × 8 actions = 24 cells.
#
# The `expected_status` per cell is derived from the *real* code paths in
# `plane.app.permissions.*` and the view bodies (NOT from the spec's ideal
# matrix). Discrepancies between the spec and the code are documented in
# the deliverable report and in the comments on each block below.
#
# Permission summary used to derive each cell:
#   * v1 invite endpoint  : WorkspaceOwnerPermission        -> role == 20 only
#   * change_role / remove_member / configure_settings /
#     delete_workspace    : @allow_permission([ADMIN], "WORKSPACE")
#                            (+ WorkSpaceBasePermission for class-level perms)
#   * add_to_project /
#     remove_from_project : @allow_permission([ADMIN]) at project level
#                            with workspace-admin fallback that is not met by
#                            non-admin parametrize cases
#   * toggle_visibility   : inline check in ProjectViewSet.partial_update
#                            (workspace admin OR project admin)
# ---------------------------------------------------------------------------
ROLE_ACTION_MATRIX = [
    # invite — v1 endpoint, WorkspaceOwnerPermission (Admin only)
    pytest.param(20, "invite", status.HTTP_201_CREATED, id="admin-invite"),
    pytest.param(15, "invite", status.HTTP_403_FORBIDDEN, id="member-invite"),
    pytest.param(5, "invite", status.HTTP_403_FORBIDDEN, id="guest-invite"),
    # change_role — WorkSpaceMemberViewSet.partial_update, Admin only
    pytest.param(20, "change_role", status.HTTP_200_OK, id="admin-change_role"),
    pytest.param(15, "change_role", status.HTTP_403_FORBIDDEN, id="member-change_role"),
    pytest.param(5, "change_role", status.HTTP_403_FORBIDDEN, id="guest-change_role"),
    # remove_member — WorkSpaceMemberViewSet.destroy, Admin only
    pytest.param(20, "remove_member", status.HTTP_204_NO_CONTENT, id="admin-remove_member"),
    pytest.param(15, "remove_member", status.HTTP_403_FORBIDDEN, id="member-remove_member"),
    pytest.param(5, "remove_member", status.HTTP_403_FORBIDDEN, id="guest-remove_member"),
    # configure_settings — WorkSpaceViewSet.partial_update; Admin via decorator
    # (Member is rejected by the decorator after passing the class permission;
    # Guest is rejected by WorkSpaceBasePermission at the class level.)
    pytest.param(20, "configure_settings", status.HTTP_200_OK, id="admin-configure_settings"),
    pytest.param(15, "configure_settings", status.HTTP_403_FORBIDDEN, id="member-configure_settings"),
    pytest.param(5, "configure_settings", status.HTTP_403_FORBIDDEN, id="guest-configure_settings"),
    # delete_workspace — WorkSpaceViewSet.destroy, Admin only (both class perm and decorator)
    pytest.param(20, "delete_workspace", status.HTTP_204_NO_CONTENT, id="admin-delete_workspace"),
    pytest.param(15, "delete_workspace", status.HTTP_403_FORBIDDEN, id="member-delete_workspace"),
    pytest.param(5, "delete_workspace", status.HTTP_403_FORBIDDEN, id="guest-delete_workspace"),
    # add_to_project — ProjectMemberViewSet.create, Admin at project level
    pytest.param(20, "add_to_project", status.HTTP_201_CREATED, id="admin-add_to_project"),
    pytest.param(15, "add_to_project", status.HTTP_403_FORBIDDEN, id="member-add_to_project"),
    pytest.param(5, "add_to_project", status.HTTP_403_FORBIDDEN, id="guest-add_to_project"),
    # remove_from_project — ProjectMemberViewSet.destroy, Admin at project level
    pytest.param(20, "remove_from_project", status.HTTP_204_NO_CONTENT, id="admin-remove_from_project"),
    pytest.param(15, "remove_from_project", status.HTTP_403_FORBIDDEN, id="member-remove_from_project"),
    pytest.param(5, "remove_from_project", status.HTTP_403_FORBIDDEN, id="guest-remove_from_project"),
    # toggle_visibility — ProjectViewSet.partial_update, workspace admin OR project admin
    pytest.param(20, "toggle_visibility", status.HTTP_200_OK, id="admin-toggle_visibility"),
    pytest.param(15, "toggle_visibility", status.HTTP_403_FORBIDDEN, id="member-toggle_visibility"),
    pytest.param(5, "toggle_visibility", status.HTTP_403_FORBIDDEN, id="guest-toggle_visibility"),
]


@pytest.mark.contract
@pytest.mark.qa
@pytest.mark.fabian
class TestWorkspaceIntegration:
    """Integration tests for the workspace and invitation endpoints"""

    @pytest.mark.django_db
    @patch("plane.bgtasks.workspace_seed_task.workspace_seed.delay")
    def test_create_workspace_valid_data_returns_201(self, mock_workspace_seed, session_client, create_user):
        """PI-07: POST /api/workspaces/ with valid data returns 201 and persists workspace with creator as Admin"""
        url = "/api/workspaces/"

        # Precondition: the slug does not exist
        assert not Workspace.objects.filter(slug="equipo-plane-qa").exists()

        workspace_data = {
            "name": "Equipo Plane QA",
            "slug": "equipo-plane-qa",
            "organization_size": "10-50",
        }

        response = session_client.post(url, workspace_data, format="json")

        # Verify the response status
        assert response.status_code == status.HTTP_201_CREATED

        # Verify the workspace was persisted in the database
        workspace = Workspace.objects.get(slug=workspace_data["slug"])
        assert workspace.name == workspace_data["name"]
        assert workspace.organization_size == workspace_data["organization_size"]
        assert workspace.owner == create_user

        # Verify the creator is registered as a WorkspaceMember with Admin role (20)
        workspace_member = WorkspaceMember.objects.get(workspace=workspace, member=create_user)
        assert workspace_member.role == 20

        # Verify the workspace_seed task was dispatched for the new workspace
        mock_workspace_seed.assert_called_once_with(response.data["id"])

    @pytest.mark.django_db
    def test_create_workspace_duplicate_slug_returns_409(self, session_client):
        """PI-08: POST /api/workspaces/ with an existing slug returns 409 with the expected error body"""
        url = "/api/workspaces/"

        # Precondition: a workspace with slug 'equipo-qa' already exists
        WorkspaceFactory(slug="equipo-qa", name="Equipo QA")
        assert Workspace.objects.filter(slug="equipo-qa").exists()

        # Attempt to create another workspace reusing the same slug
        duplicate_data = {
            "name": "Equipo QA Duplicado",
            "slug": "equipo-qa",
        }

        response = session_client.post(url, duplicate_data, format="json")

        # The API must signal the conflict via 409 with the documented error body
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data == {"slug": "The workspace with the slug already exists"}

    @pytest.mark.django_db
    def test_create_workspace_invitation_as_admin_returns_201(self, api_key_client, workspace, create_user):
        """PI-09: POST /api/v1/workspaces/{slug}/invitations/ as Admin (role=20) returns 201 and persists the invitation"""
        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"

        # Precondition: the requesting user is a WorkspaceMember with Admin role (20)
        assert WorkspaceMember.objects.filter(
            workspace=workspace, member=create_user, role=20
        ).exists()

        invitation_data = {
            "email": "invitee@plane.so",
            "role": 15,  # Member role
        }

        response = api_key_client.post(url, invitation_data, format="json")

        # Verify the response status
        assert response.status_code == status.HTTP_201_CREATED

        # Verify the invitation record was persisted with the expected fields
        invitation = WorkspaceMemberInvite.objects.get(
            workspace=workspace, email=invitation_data["email"]
        )
        assert invitation.role == invitation_data["role"]
        assert invitation.accepted is False
        assert invitation.responded_at is None
        # The model auto-populates a creation timestamp (used by the invite lifecycle)
        assert invitation.created_at is not None

    @pytest.mark.django_db
    def test_create_workspace_invitation_as_member_returns_403(self, api_key_client, workspace, create_user):
        """PI-10: POST /api/v1/workspaces/{slug}/invitations/ as Member (role=15) returns 403
        and persists no invitation row.

        The v1 invitations endpoint is guarded by `WorkspaceOwnerPermission`
        (apps/api/plane/utils/permissions/workspace.py:51), which only permits
        WorkspaceMember rows with role == 20 (Admin). A role=15 (Member) caller
        must be rejected with 403 *before* the serializer runs.
        """
        # Demote the (api-key-authenticated) caller from Admin (20) to Member (15)
        updated_rows = WorkspaceMember.objects.filter(
            workspace=workspace, member=create_user
        ).update(role=15)
        assert updated_rows == 1
        assert WorkspaceMember.objects.filter(
            workspace=workspace, member=create_user, role=15
        ).exists()

        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"

        invitation_data = {
            "email": "invitee-blocked@plane.so",
            "role": 15,
        }

        # Sanity check: no invitations exist for this workspace yet
        assert WorkspaceMemberInvite.objects.filter(workspace=workspace).count() == 0

        response = api_key_client.post(url, invitation_data, format="json")

        # WorkspaceOwnerPermission rejects non-admin members
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # No WorkspaceMemberInvite row was created
        assert WorkspaceMemberInvite.objects.filter(workspace=workspace).count() == 0
        assert not WorkspaceMemberInvite.objects.filter(
            workspace=workspace, email=invitation_data["email"]
        ).exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize("role,action,expected_status", ROLE_ACTION_MATRIX)
    def test_role_action_permission_matrix(
        self,
        session_client,
        create_user,
        workspace,
        role,
        action,
        expected_status,
    ):
        """PI-11: 3 roles × 8 actions = 24 parametrized permission cases.

        For each (role, action) cell:
          1. The caller (`create_user`) is set as a WorkspaceMember with the
             parametrized role; for project-scoped actions they are also
             registered as a ProjectMember with the same role.
          2. A `second_user` (workspace Member, role=15) is created and used as
             the target for action 2/3/6/7 (so admin requests don't trip the
             "cannot remove/update yourself" guards).
          3. The relevant endpoint is invoked through the session client.
          4. The response status is compared against the *real* code path,
             not the spec's ideal matrix (see ROLE_ACTION_MATRIX above).

        Background tasks dispatched by some actions are patched so the test
        only exercises the request/response cycle.
        """
        # 1. Set the caller's workspace role to the parametrized one
        updated = WorkspaceMember.objects.filter(
            workspace=workspace, member=create_user
        ).update(role=role)
        assert updated == 1

        # 2. Second user — workspace Member (role=15). Used as the action target.
        second_user = UserFactory()
        WorkspaceMember.objects.create(
            workspace=workspace, member=second_user, role=15
        )

        # 3. Project setup for project-scoped actions
        project = None
        if action in ("add_to_project", "remove_from_project", "toggle_visibility"):
            project = ProjectFactory(
                workspace=workspace,
                name="Matrix Project",
                identifier="MTX",
            )
            ProjectMember.objects.create(
                project=project,
                workspace=workspace,
                member=create_user,
                role=role,
            )
            if action == "remove_from_project":
                ProjectMember.objects.create(
                    project=project,
                    workspace=workspace,
                    member=second_user,
                    role=15,
                )

        # 4. Patch background tasks that successful admin paths enqueue, so
        #    Celery is not required by the test environment.
        with patch(
            "plane.bgtasks.project_add_user_email_task.project_add_user_email.delay"
        ), patch(
            "plane.bgtasks.webhook_task.model_activity.delay"
        ), patch(
            "plane.bgtasks.webhook_task.webhook_activity.delay"
        ), patch(
            "plane.bgtasks.event_tracking_task.track_event.delay"
        ):
            response = self._dispatch_matrix_action(
                action=action,
                session_client=session_client,
                workspace=workspace,
                second_user=second_user,
                project=project,
            )

        # 5. Assert against the expected status from the matrix
        assert response.status_code == expected_status, (
            f"role={role}, action={action}: expected {expected_status}, "
            f"got {response.status_code} (body={getattr(response, 'data', None)!r})"
        )

    def _dispatch_matrix_action(self, action, session_client, workspace, second_user, project):
        """PI-11 dispatcher — maps an action name to its URL + HTTP verb + body."""
        if action == "invite":
            # v1 endpoint; force_authenticate on session_client bypasses
            # APIKeyAuthentication so the permission class still runs against
            # the authenticated user.
            url = f"/api/v1/workspaces/{workspace.slug}/invitations/"
            return session_client.post(
                url,
                {"email": "matrix-invite@plane.so", "role": 5},
                format="json",
            )

        if action == "change_role":
            target = WorkspaceMember.objects.get(workspace=workspace, member=second_user)
            url = f"/api/workspaces/{workspace.slug}/members/{target.pk}/"
            return session_client.patch(url, {"role": 5}, format="json")

        if action == "remove_member":
            target = WorkspaceMember.objects.get(workspace=workspace, member=second_user)
            url = f"/api/workspaces/{workspace.slug}/members/{target.pk}/"
            return session_client.delete(url)

        if action == "configure_settings":
            url = f"/api/workspaces/{workspace.slug}/"
            return session_client.patch(
                url, {"name": "Matrix Updated Workspace"}, format="json"
            )

        if action == "delete_workspace":
            url = f"/api/workspaces/{workspace.slug}/"
            return session_client.delete(url)

        if action == "add_to_project":
            url = f"/api/workspaces/{workspace.slug}/projects/{project.pk}/members/"
            return session_client.post(
                url,
                {"members": [{"member_id": str(second_user.id), "role": 15}]},
                format="json",
            )

        if action == "remove_from_project":
            target_pm = ProjectMember.objects.get(project=project, member=second_user)
            url = (
                f"/api/workspaces/{workspace.slug}/projects/{project.pk}"
                f"/members/{target_pm.pk}/"
            )
            return session_client.delete(url)

        if action == "toggle_visibility":
            url = f"/api/workspaces/{workspace.slug}/projects/{project.pk}/"
            return session_client.patch(url, {"network": 2}, format="json")

        raise ValueError(f"Unknown PI-11 action: {action}")

    @pytest.mark.django_db
    def test_leave_workspace_as_last_admin_returns_400(self, session_client, workspace, create_user):
        """PI-12: POST /api/workspaces/{slug}/members/leave/ as the only Admin returns 400.

        Guard rail enforced in `WorkSpaceMemberViewSet.leave`
        (apps/api/plane/app/views/workspace/member.py:159-205): when the
        leaving member has role=20 and is the only active admin, the endpoint
        returns 400 with an error message that includes "only admin".
        The membership row must remain active in the DB afterwards.
        """
        # Precondition: create_user is the only active Admin (role=20)
        admin_member = WorkspaceMember.objects.get(workspace=workspace, member=create_user)
        assert admin_member.role == 20
        assert admin_member.is_active is True
        assert (
            WorkspaceMember.objects.filter(
                workspace=workspace, role=20, is_active=True
            ).count()
            == 1
        )

        url = f"/api/workspaces/{workspace.slug}/members/leave/"

        response = session_client.post(url)

        # The endpoint must refuse with 400 and a descriptive error message
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "only admin" in response.data["error"]

        # The admin remains active in the workspace (the leave was rejected)
        admin_member.refresh_from_db()
        assert admin_member.is_active is True
        assert admin_member.role == 20
        assert WorkspaceMember.objects.filter(
            workspace=workspace, member=create_user, role=20, is_active=True
        ).exists()
