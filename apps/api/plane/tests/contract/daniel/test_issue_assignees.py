"""
PI-20: PATCH assignee con no-miembro: el ID se filtra silenciosamente del payload
Tecnica: Tabla de decision
HU-18: Asignar y reasignar work items a miembros del proyecto
"""
import pytest
from django.urls import reverse

from plane.tests.factories import IssueFactory, StateFactory, UserFactory, ProjectMemberFactory


@pytest.mark.django_db
class TestIssueAssigneeFiltering:

    def _patch_url(self, workspace, project, issue):
        return f"/api/workspaces/{workspace.slug}/projects/{project.id}/issues/{issue.id}/"

    def test_pi20_non_member_assignee_is_silently_filtered(self, auth_client, workspace, project, default_state, user):
        """PI-20: PATCH con [no-miembro, miembro-valido] retorna 200 y solo el miembro valido queda asignado."""
        outsider = UserFactory()
        valid_member = UserFactory()
        ProjectMemberFactory(project=project, member=valid_member, role=15)

        issue = IssueFactory(project=project, state=default_state)

        url = self._patch_url(workspace, project, issue)
        response = auth_client.patch(
            url,
            data={"assignees": [str(outsider.id), str(valid_member.id)]},
            format="json",
        )

        assert response.status_code == 200
        assignee_ids = [str(a) for a in response.data.get("assignees", [])]
        assert str(outsider.id) not in assignee_ids
        assert str(valid_member.id) in assignee_ids

    def test_all_non_members_results_in_empty_assignees(self, auth_client, workspace, project, default_state):
        """Si todos los IDs enviados son no-miembros, assignees queda vacio."""
        outsider_a = UserFactory()
        outsider_b = UserFactory()

        issue = IssueFactory(project=project, state=default_state)

        url = self._patch_url(workspace, project, issue)
        response = auth_client.patch(
            url,
            data={"assignees": [str(outsider_a.id), str(outsider_b.id)]},
            format="json",
        )

        assert response.status_code == 200
        assignee_ids = [str(a) for a in response.data.get("assignees", [])]
        assert str(outsider_a.id) not in assignee_ids
        assert str(outsider_b.id) not in assignee_ids

    def test_valid_member_assignee_is_accepted(self, auth_client, workspace, project, default_state, user):
        """Un miembro valido del proyecto queda asignado correctamente."""
        valid_member = UserFactory()
        ProjectMemberFactory(project=project, member=valid_member, role=15)

        issue = IssueFactory(project=project, state=default_state)

        url = self._patch_url(workspace, project, issue)
        response = auth_client.patch(
            url,
            data={"assignees": [str(valid_member.id)]},
            format="json",
        )

        assert response.status_code == 200
        assignee_ids = [str(a) for a in response.data.get("assignees", [])]
        assert str(valid_member.id) in assignee_ids
