"""
PI-20: PATCH assignee con no-miembro: el ID se filtra silenciosamente del payload
Tecnica: Tabla de decision
HU-18: Asignar y reasignar work items a miembros del proyecto
"""
import pytest
from plane.tests.factories import IssueFactory, UserFactory, ProjectMemberFactory


def patch_issue(auth_client, workspace, project, issue, assignees):
    url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/issues/{issue.id}/"
    return auth_client.patch(url, data={"assignees": assignees}, format="json")


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI20MixedAssignees:
    """PI-20: Payload con un no-miembro y un miembro valido."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project, default_state, user):
        self.outsider = UserFactory()
        self.valid_member = UserFactory()
        ProjectMemberFactory(project=project, member=self.valid_member, role=15)
        issue = IssueFactory(project=project, state=default_state)
        self.response = patch_issue(
            auth_client, workspace, project, issue,
            [str(self.outsider.id), str(self.valid_member.id)],
        )
        self.assignee_ids = [str(a) for a in self.response.data.get("assignees", [])]

    def test_returns_200(self):
        assert self.response.status_code == 200

    def test_outsider_not_in_assignees(self):
        assert str(self.outsider.id) not in self.assignee_ids

    def test_valid_member_in_assignees(self):
        assert str(self.valid_member.id) in self.assignee_ids


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI20AllOutsiders:
    """PI-20: Todos los IDs son no-miembros — assignees queda vacio."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project, default_state):
        self.outsider_a = UserFactory()
        self.outsider_b = UserFactory()
        issue = IssueFactory(project=project, state=default_state)
        self.response = patch_issue(
            auth_client, workspace, project, issue,
            [str(self.outsider_a.id), str(self.outsider_b.id)],
        )
        self.assignee_ids = [str(a) for a in self.response.data.get("assignees", [])]

    def test_returns_200(self):
        assert self.response.status_code == 200

    def test_first_outsider_not_in_assignees(self):
        assert str(self.outsider_a.id) not in self.assignee_ids

    def test_second_outsider_not_in_assignees(self):
        assert str(self.outsider_b.id) not in self.assignee_ids


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI20ValidMemberOnly:
    """PI-20: Solo un miembro valido — queda asignado correctamente."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project, default_state, user):
        self.valid_member = UserFactory()
        ProjectMemberFactory(project=project, member=self.valid_member, role=15)
        issue = IssueFactory(project=project, state=default_state)
        self.response = patch_issue(
            auth_client, workspace, project, issue,
            [str(self.valid_member.id)],
        )
        self.assignee_ids = [str(a) for a in self.response.data.get("assignees", [])]

    def test_returns_200(self):
        assert self.response.status_code == 200

    def test_valid_member_in_assignees(self):
        assert str(self.valid_member.id) in self.assignee_ids
