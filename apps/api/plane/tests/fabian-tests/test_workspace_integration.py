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

    # ------------------------------------------------------------------
    # PI-07 — POST /api/workspaces/ with valid data
    # ------------------------------------------------------------------
    URL_CREATE_WORKSPACE = "/api/workspaces/"
    NEW_WORKSPACE_PAYLOAD = {
        "name": "Equipo Plane QA",
        "slug": "equipo-plane-qa",
        "organization_size": "10-50",
    }

    @pytest.mark.django_db
    @patch("plane.bgtasks.workspace_seed_task.workspace_seed.delay")
    def test_create_workspace_returns_201(
        self, mock_workspace_seed, session_client, precondition_slug_not_in_use
    ):
        """[PI/07] POST /api/workspaces/ with valid data returns 201."""
        response = session_client.post(
            self.URL_CREATE_WORKSPACE, self.NEW_WORKSPACE_PAYLOAD, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    @patch("plane.bgtasks.workspace_seed_task.workspace_seed.delay")
    def test_create_workspace_persists_name(
        self, mock_workspace_seed, session_client, precondition_slug_not_in_use
    ):
        """[PI/07] the created workspace persists the `name` field as submitted."""
        session_client.post(
            self.URL_CREATE_WORKSPACE, self.NEW_WORKSPACE_PAYLOAD, format="json"
        )

        workspace = Workspace.objects.get(slug=self.NEW_WORKSPACE_PAYLOAD["slug"])
        assert workspace.name == self.NEW_WORKSPACE_PAYLOAD["name"]

    @pytest.mark.django_db
    @patch("plane.bgtasks.workspace_seed_task.workspace_seed.delay")
    def test_create_workspace_persists_organization_size(
        self, mock_workspace_seed, session_client, precondition_slug_not_in_use
    ):
        """[PI/07] the created workspace persists the `organization_size` field."""
        session_client.post(
            self.URL_CREATE_WORKSPACE, self.NEW_WORKSPACE_PAYLOAD, format="json"
        )

        workspace = Workspace.objects.get(slug=self.NEW_WORKSPACE_PAYLOAD["slug"])
        assert workspace.organization_size == self.NEW_WORKSPACE_PAYLOAD["organization_size"]

    @pytest.mark.django_db
    @patch("plane.bgtasks.workspace_seed_task.workspace_seed.delay")
    def test_create_workspace_sets_owner(
        self, mock_workspace_seed, session_client, create_user, precondition_slug_not_in_use
    ):
        """[PI/07] the created workspace's `owner` is the requesting user."""
        session_client.post(
            self.URL_CREATE_WORKSPACE, self.NEW_WORKSPACE_PAYLOAD, format="json"
        )

        workspace = Workspace.objects.get(slug=self.NEW_WORKSPACE_PAYLOAD["slug"])
        assert workspace.owner == create_user

    @pytest.mark.django_db
    @patch("plane.bgtasks.workspace_seed_task.workspace_seed.delay")
    def test_create_workspace_creates_admin_member(
        self, mock_workspace_seed, session_client, create_user, precondition_slug_not_in_use
    ):
        """[PI/07] the creator is registered as a WorkspaceMember with Admin role (20)."""
        session_client.post(
            self.URL_CREATE_WORKSPACE, self.NEW_WORKSPACE_PAYLOAD, format="json"
        )

        workspace = Workspace.objects.get(slug=self.NEW_WORKSPACE_PAYLOAD["slug"])
        workspace_member = WorkspaceMember.objects.get(workspace=workspace, member=create_user)
        assert workspace_member.role == 20

    @pytest.mark.django_db
    @patch("plane.bgtasks.workspace_seed_task.workspace_seed.delay")
    def test_create_workspace_dispatches_seed_task(
        self, mock_workspace_seed, session_client, precondition_slug_not_in_use
    ):
        """[PI/07] the workspace_seed task is dispatched for the new workspace."""
        response = session_client.post(
            self.URL_CREATE_WORKSPACE, self.NEW_WORKSPACE_PAYLOAD, format="json"
        )

        mock_workspace_seed.assert_called_once_with(response.data["id"])

    # ------------------------------------------------------------------
    # PI-08 — POST /api/workspaces/ with an existing slug
    # ------------------------------------------------------------------
    DUPLICATE_PAYLOAD = {
        "name": "Equipo QA Duplicado",
        "slug": "equipo-qa",
    }

    @pytest.mark.django_db
    def test_create_workspace_duplicate_slug_returns_400(
        self, session_client, precondition_workspace_with_duplicate_slug_exists
    ):
        """[PI/08] POST /api/workspaces/ with an existing slug returns 400.

        The Workspace.slug field is a `models.SlugField(unique=True)`, so DRF
        auto-generates a `UniqueValidator` on the serializer. The view uses
        `is_valid(raise_exception=True)`, which short-circuits with 400
        before the view's `try/except IntegrityError` (which would have
        returned 409) can run.
        """
        response = session_client.post(
            self.URL_CREATE_WORKSPACE, self.DUPLICATE_PAYLOAD, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_create_workspace_duplicate_slug_error_body(
        self, session_client, precondition_workspace_with_duplicate_slug_exists
    ):
        """[PI/08] the 400 response carries the unique-violation error for slug."""
        response = session_client.post(
            self.URL_CREATE_WORKSPACE, self.DUPLICATE_PAYLOAD, format="json"
        )

        assert response.data == {"slug": ["Workspace with this slug already exists."]}

    # ------------------------------------------------------------------
    # PI-09 — POST /api/v1/workspaces/{slug}/invitations/ as Admin
    # ------------------------------------------------------------------
    @pytest.mark.django_db
    def test_invitation_as_admin_returns_201(
        self, api_key_client, workspace, precondition_caller_is_workspace_admin
    ):
        """[PI/09] POST /api/v1/workspaces/{slug}/invitations/ as Admin returns 201."""
        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"
        payload = {"email": "invitee@plane.so", "role": 15}

        response = api_key_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_invitation_as_admin_persists_role(
        self, api_key_client, workspace, precondition_caller_is_workspace_admin
    ):
        """[PI/09] the invitation record is persisted with the requested role."""
        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"
        payload = {"email": "invitee@plane.so", "role": 15}

        api_key_client.post(url, payload, format="json")

        invitation = WorkspaceMemberInvite.objects.get(
            workspace=workspace, email=payload["email"]
        )
        assert invitation.role == payload["role"]

    @pytest.mark.django_db
    def test_invitation_as_admin_accepted_false(
        self, api_key_client, workspace, precondition_caller_is_workspace_admin
    ):
        """[PI/09] the invitation is stored with `accepted=False`."""
        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"
        payload = {"email": "invitee-accepted@plane.so", "role": 15}

        api_key_client.post(url, payload, format="json")

        invitation = WorkspaceMemberInvite.objects.get(
            workspace=workspace, email=payload["email"]
        )
        assert invitation.accepted is False

    @pytest.mark.django_db
    def test_invitation_as_admin_responded_at_null(
        self, api_key_client, workspace, precondition_caller_is_workspace_admin
    ):
        """[PI/09] the invitation has no `responded_at` timestamp yet."""
        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"
        payload = {"email": "invitee-responded@plane.so", "role": 15}

        api_key_client.post(url, payload, format="json")

        invitation = WorkspaceMemberInvite.objects.get(
            workspace=workspace, email=payload["email"]
        )
        assert invitation.responded_at is None

    @pytest.mark.django_db
    def test_invitation_as_admin_created_at_not_null(
        self, api_key_client, workspace, precondition_caller_is_workspace_admin
    ):
        """[PI/09] the invitation has a populated `created_at` timestamp."""
        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"
        payload = {"email": "invitee-created@plane.so", "role": 15}

        api_key_client.post(url, payload, format="json")

        invitation = WorkspaceMemberInvite.objects.get(
            workspace=workspace, email=payload["email"]
        )
        assert invitation.created_at is not None

    # ------------------------------------------------------------------
    # PI-10 — POST /api/v1/workspaces/{slug}/invitations/ as Member
    # ------------------------------------------------------------------
    @pytest.mark.django_db
    def test_invitation_as_member_returns_403(
        self, api_key_client, workspace, precondition_demoted_to_member_and_no_invitations
    ):
        """[PI/10] WorkspaceOwnerPermission rejects non-admin members with 403."""
        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"
        payload = {"email": "invitee-blocked@plane.so", "role": 15}

        response = api_key_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_invitation_as_member_no_invitations_total(
        self, api_key_client, workspace, precondition_demoted_to_member_and_no_invitations
    ):
        """[PI/10] no WorkspaceMemberInvite rows are created for the workspace."""
        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"
        payload = {"email": "invitee-count@plane.so", "role": 15}

        api_key_client.post(url, payload, format="json")

        assert WorkspaceMemberInvite.objects.filter(workspace=workspace).count() == 0

    @pytest.mark.django_db
    def test_invitation_as_member_no_specific_invite(
        self, api_key_client, workspace, precondition_demoted_to_member_and_no_invitations
    ):
        """[PI/10] no WorkspaceMemberInvite row exists for the rejected email."""
        url = f"/api/v1/workspaces/{workspace.slug}/invitations/"
        payload = {"email": "invitee-specific@plane.so", "role": 15}

        api_key_client.post(url, payload, format="json")

        assert not WorkspaceMemberInvite.objects.filter(
            workspace=workspace, email=payload["email"]
        ).exists()

    # ------------------------------------------------------------------
    # PI-11 — 3 roles × 8 actions = 24 parametrized permission cases.
    # ------------------------------------------------------------------
    # This test is intentionally kept as a single parametrized body: each
    # (role, action) cell already has exactly one assertion against the
    # expected status. The `assert updated == 1` for the role update is part
    # of the arrange/act phase (it verifies the precondition fixture worked),
    # not an independent behaviour assertion.
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
        """[PI/11] For each (role, action) cell, the response status matches the
        *real* code path (see ROLE_ACTION_MATRIX above)."""
        # Arrange: set the caller's workspace role
        updated = WorkspaceMember.objects.filter(
            workspace=workspace, member=create_user
        ).update(role=role)
        assert updated == 1

        # Arrange: a second user used as the action target for 2/3/6/7
        second_user = UserFactory(username=f"second-user-{action}-{role}")
        WorkspaceMember.objects.create(
            workspace=workspace, member=second_user, role=15
        )

        # Arrange: project setup for project-scoped actions
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

        assert response.status_code == expected_status, (
            f"role={role}, action={action}: expected {expected_status}, "
            f"got {response.status_code} (body={getattr(response, 'data', None)!r})"
        )

    def _dispatch_matrix_action(self, action, session_client, workspace, second_user, project):
        """[PI/11] dispatcher — maps an action name to its URL + HTTP verb + body."""
        if action == "invite":
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

    # ------------------------------------------------------------------
    # PI-12 — POST /api/workspaces/{slug}/members/leave/ as the only Admin
    # ------------------------------------------------------------------
    @pytest.mark.django_db
    def test_leave_workspace_as_last_admin_returns_400(
        self, session_client, workspace, precondition_only_active_admin
    ):
        """[PI/12] The leave endpoint refuses with 400 when the only Admin tries to leave."""
        url = f"/api/workspaces/{workspace.slug}/members/leave/"

        response = session_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_leave_workspace_as_last_admin_error_contains_only_admin(
        self, session_client, workspace, precondition_only_active_admin
    ):
        """[PI/12] The 400 error message describes the only-admin constraint."""
        url = f"/api/workspaces/{workspace.slug}/members/leave/"

        response = session_client.post(url)

        assert "only admin" in response.data["error"]

    @pytest.mark.django_db
    def test_leave_workspace_as_last_admin_keeps_is_active(
        self, session_client, workspace, precondition_only_active_admin
    ):
        """[PI/12] The admin's `is_active` flag is preserved after the rejected leave."""
        url = f"/api/workspaces/{workspace.slug}/members/leave/"

        session_client.post(url)

        admin_member = WorkspaceMember.objects.get(workspace=workspace, member=precondition_only_active_admin.member)
        assert admin_member.is_active is True

    @pytest.mark.django_db
    def test_leave_workspace_as_last_admin_keeps_role(
        self, session_client, workspace, precondition_only_active_admin
    ):
        """[PI/12] The admin's `role` is preserved (still 20) after the rejected leave."""
        url = f"/api/workspaces/{workspace.slug}/members/leave/"

        session_client.post(url)

        admin_member = WorkspaceMember.objects.get(workspace=workspace, member=precondition_only_active_admin.member)
        assert admin_member.role == 20

    @pytest.mark.django_db
    def test_leave_workspace_as_last_admin_keeps_membership(
        self, session_client, workspace, create_user, precondition_only_active_admin
    ):
        """[PI/12] The admin's active membership row still exists after the rejected leave."""
        url = f"/api/workspaces/{workspace.slug}/members/leave/"

        session_client.post(url)

        assert WorkspaceMember.objects.filter(
            workspace=workspace, member=create_user, role=20, is_active=True
        ).exists()
