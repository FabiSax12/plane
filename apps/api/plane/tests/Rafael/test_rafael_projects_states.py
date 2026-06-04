# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

# Pruebas de integración asignadas a Rafael Odio: PI-13, PI-14, PI-15, PI-16, PI-17, PI-18
# Ejecución:
#   docker compose -f deploy/docker-compose-test.yml exec api-tests \
#     python -m pytest plane/tests/Rafael/test_rafael_projects_states.py -v

import pytest
from rest_framework import status

from plane.db.models import Issue, IssueRelation, Project, ProjectMember, State, WorkspaceMember
from plane.db.models.state import StateGroup


# ---------------------------------------------------------------------------
# PI-13 — POST /api/v1/workspaces/{slug}/projects/ retorna 201 con 6 estados
# Técnica: Cobertura de sentencias
# ---------------------------------------------------------------------------

@pytest.mark.contract
@pytest.mark.rafael
class TestPI13CreateProjectWithStates:
    """PI-13: crear proyecto vía API v1 genera 6 estados automáticamente."""

    @pytest.mark.django_db
    def test_pi13_create_project_returns_201(self, api_key_client, workspace, create_user):
        """PI-13: POST /projects/ retorna 201 Created."""
        url = f"/api/v1/workspaces/{workspace.slug}/projects/"
        response = api_key_client.post(
            url,
            {"name": "PI13 Project", "identifier": "PI13", "description": "Integration test"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_pi13_create_project_seeds_six_states(self, api_key_client, workspace, create_user):
        """PI-13: bulk_create genera exactamente 6 estados."""
        url = f"/api/v1/workspaces/{workspace.slug}/projects/"
        response = api_key_client.post(
            url,
            {"name": "PI13b Project", "identifier": "PI13B", "description": "Integration test"},
            format="json",
        )
        project_id = response.json()["id"]
        assert State.all_state_objects.filter(project_id=project_id).count() == 6

    @pytest.mark.django_db
    def test_pi13_create_project_has_all_expected_groups(self, api_key_client, workspace, create_user):
        """PI-13: los 6 estados cubren todos los grupos esperados."""
        url = f"/api/v1/workspaces/{workspace.slug}/projects/"
        response = api_key_client.post(
            url,
            {"name": "PI13c Project", "identifier": "PI13C", "description": "Integration test"},
            format="json",
        )
        project_id = response.json()["id"]
        groups = set(State.all_state_objects.filter(project_id=project_id).values_list("group", flat=True))
        assert groups == {"backlog", "unstarted", "started", "completed", "cancelled", "triage"}


# ---------------------------------------------------------------------------
# PI-14 — GET /api/v1/workspaces/{slug}/projects/{id}/members/ lista miembros
# Técnica: Cobertura de sentencias
# ---------------------------------------------------------------------------

@pytest.mark.contract
@pytest.mark.rafael
class TestPI14ListProjectMembers:
    """PI-14: GET de miembros retorna la lista completa."""

    def _setup_project_with_members(self, api_key_client, workspace, create_user):
        from plane.db.models import User
        project = Project.objects.create(
            name="PI14 Project", identifier="PI14", workspace=workspace
        )
        member2 = User.objects.create_user(email="pi14m2@plane.so", username="pi14m2")
        member3 = User.objects.create_user(email="pi14m3@plane.so", username="pi14m3")
        WorkspaceMember.objects.get_or_create(workspace=workspace, member=member2, defaults={"role": 15})
        WorkspaceMember.objects.get_or_create(workspace=workspace, member=member3, defaults={"role": 15})
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
        ProjectMember.objects.create(project=project, member=member2, role=15, is_active=True)
        ProjectMember.objects.create(project=project, member=member3, role=15, is_active=True)
        return project

    @pytest.mark.django_db
    def test_pi14_get_members_returns_200(self, api_key_client, workspace, create_user):
        """PI-14: GET /members/ retorna 200 OK."""
        project = self._setup_project_with_members(api_key_client, workspace, create_user)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/members/"
        assert api_key_client.get(url).status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_pi14_get_members_returns_three_members(self, api_key_client, workspace, create_user):
        """PI-14: GET retorna exactamente 3 miembros."""
        project = self._setup_project_with_members(api_key_client, workspace, create_user)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/members/"
        assert len(api_key_client.get(url).json()) == 3

    @pytest.mark.django_db
    def test_pi14_members_response_excludes_role_field(self, api_key_client, workspace, create_user):
        """PI-14: la API v1 no expone 'role' en la respuesta (usa UserLiteSerializer)."""
        project = self._setup_project_with_members(api_key_client, workspace, create_user)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/members/"
        first_member = api_key_client.get(url).json()[0]
        assert "role" not in first_member


# ---------------------------------------------------------------------------
# PI-15 — POST archive/ archiva proyecto
# Técnica: Cobertura de decisiones
# ---------------------------------------------------------------------------

@pytest.mark.contract
@pytest.mark.rafael
class TestPI15ArchiveProject:
    """PI-15: archivar proyecto setea archived_at."""

    @pytest.mark.django_db
    def test_pi15_archive_returns_204(self, api_key_client, workspace, create_user):
        """PI-15: POST archive/ retorna 204 No Content."""
        project = Project.objects.create(
            name="PI15 Project", identifier="PI15", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/archive/"
        assert api_key_client.post(url).status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_pi15_archive_sets_archived_at(self, api_key_client, workspace, create_user):
        """PI-15: tras archivar, archived_at IS NOT NULL en DB."""
        project = Project.objects.create(
            name="PI15b Project", identifier="PI15B", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
        api_key_client.post(f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/archive/")
        project.refresh_from_db()
        assert project.archived_at is not None

    @pytest.mark.django_db
    def test_pi15_archived_project_still_visible_in_v1_list(self, api_key_client, workspace, create_user):
        """PI-15: la API v1 devuelve proyectos archivados en el listado estándar."""
        project = Project.objects.create(
            name="PI15c Project", identifier="PI15C", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
        api_key_client.post(f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/archive/")
        data = api_key_client.get(f"/api/v1/workspaces/{workspace.slug}/projects/").json()
        projects = data["results"] if isinstance(data, dict) else data
        assert str(project.id) in [p["id"] for p in projects]


# ---------------------------------------------------------------------------
# PI-16 — POST relations/ crea relación bidireccional blocked_by / blocking
# Técnica: Cobertura de sentencias
# ---------------------------------------------------------------------------

@pytest.mark.contract
@pytest.mark.rafael
class TestPI16IssueRelation:
    """PI-16: relación blocked_by genera relación inversa blocking."""

    def _setup(self, workspace, create_user):
        project = Project.objects.create(
            name="PI16 Project", identifier="PI16", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
        state = State.objects.create(
            name="Todo", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value,
        )
        issue_a = Issue.objects.create(
            name="Issue A", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        issue_b = Issue.objects.create(
            name="Issue B", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        return project, issue_a, issue_b

    @pytest.mark.django_db
    def test_pi16_post_relation_returns_201(self, api_key_client, workspace, create_user):
        """PI-16: POST relation blocked_by retorna 201 Created."""
        project, issue_a, issue_b = self._setup(workspace, create_user)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/{issue_a.id}/relations/"
        response = api_key_client.post(
            url, {"relation_type": "blocked_by", "issues": [str(issue_b.id)]}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_pi16_relation_stored_in_db(self, api_key_client, workspace, create_user):
        """PI-16: la relación blocked_by existe en IssueRelation."""
        project, issue_a, issue_b = self._setup(workspace, create_user)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/{issue_a.id}/relations/"
        api_key_client.post(url, {"relation_type": "blocked_by", "issues": [str(issue_b.id)]}, format="json")
        assert IssueRelation.objects.filter(
            issue=issue_a, related_issue=issue_b, relation_type="blocked_by"
        ).exists()

    @pytest.mark.django_db
    def test_pi16_issue_a_shows_blocked_by_issue_b(self, api_key_client, workspace, create_user):
        """PI-16: issue_b aparece en blocked_by de issue_a."""
        project, issue_a, issue_b = self._setup(workspace, create_user)
        rel_url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/{issue_a.id}/relations/"
        api_key_client.post(rel_url, {"relation_type": "blocked_by", "issues": [str(issue_b.id)]}, format="json")
        data = api_key_client.get(rel_url).json()
        blocked_by_ids = [r["issue_id"] for r in data.get("blocked_by", [])]
        assert str(issue_b.id) in blocked_by_ids

    @pytest.mark.django_db
    def test_pi16_issue_b_shows_blocking_issue_a(self, api_key_client, workspace, create_user):
        """PI-16: issue_a aparece en blocking de issue_b (relación inversa)."""
        project, issue_a, issue_b = self._setup(workspace, create_user)
        rel_url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/{issue_a.id}/relations/"
        api_key_client.post(rel_url, {"relation_type": "blocked_by", "issues": [str(issue_b.id)]}, format="json")
        get_b_url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/{issue_b.id}/relations/"
        data = api_key_client.get(get_b_url).json()
        blocking_ids = [r["issue_id"] for r in data.get("blocking", [])]
        assert str(issue_a.id) in blocking_ids


# ---------------------------------------------------------------------------
# PI-17 — DELETE state en uso retorna 400
# Técnica: Cobertura de decisiones (rama negativa)
# ---------------------------------------------------------------------------

@pytest.mark.contract
@pytest.mark.rafael
class TestPI17DeleteStateInUse:
    """PI-17: DELETE state con issues → 400 con mensaje específico."""

    def _setup(self, workspace, create_user):
        project = Project.objects.create(
            name="PI17 Project", identifier="PI17", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
        state = State.objects.create(
            name="PI17 State", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value, default=False,
        )
        Issue.objects.create(
            name="Blocking Issue", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        return project, state

    @pytest.mark.django_db
    def test_pi17_delete_state_in_use_returns_400(self, api_key_client, workspace, create_user):
        """PI-17: DELETE estado con issues retorna 400 Bad Request."""
        project, state = self._setup(workspace, create_user)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/states/{state.id}/"
        assert api_key_client.delete(url).status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_pi17_delete_state_in_use_returns_exact_error_message(self, api_key_client, workspace, create_user):
        """PI-17: el mensaje de error es exactamente el definido en state.py:244."""
        project, state = self._setup(workspace, create_user)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/states/{state.id}/"
        data = api_key_client.delete(url).json()
        assert data.get("error") == "The state is not empty, only empty states can be deleted"

    @pytest.mark.django_db
    def test_pi17_state_still_exists_after_failed_delete(self, api_key_client, workspace, create_user):
        """PI-17: el estado sigue en DB tras el DELETE rechazado."""
        project, state = self._setup(workspace, create_user)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/states/{state.id}/"
        api_key_client.delete(url)
        assert State.objects.filter(id=state.id).exists()


# ---------------------------------------------------------------------------
# PI-18 — POST work-items/ con sequence_id auto-generado
# Técnica: Cobertura de sentencias
# ---------------------------------------------------------------------------

@pytest.mark.contract
@pytest.mark.rafael
class TestPI18WorkItemSequenceId:
    """PI-18: crear segundo work item vía API retorna sequence_id == 2."""

    @pytest.mark.django_db(transaction=True)
    def test_pi18_second_work_item_returns_201(self, api_key_client, workspace, create_user):
        """PI-18: POST segundo work item retorna 201 Created."""
        project = Project.objects.create(
            name="PI18 Project", identifier="PI18", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
        state = State.objects.create(
            name="Todo", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value,
        )
        Issue.objects.create(
            name="First Issue", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/"
        response = api_key_client.post(url, {"name": "Second Issue"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db(transaction=True)
    def test_pi18_second_work_item_has_sequence_id_two(self, api_key_client, workspace, create_user):
        """PI-18: sequence_id del segundo issue es 2."""
        project = Project.objects.create(
            name="PI18b Project", identifier="PI18B", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
        state = State.objects.create(
            name="Todo", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value,
        )
        Issue.objects.create(
            name="First Issue", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/"
        data = api_key_client.post(url, {"name": "Second Issue"}, format="json").json()
        assert data["sequence_id"] == 2
