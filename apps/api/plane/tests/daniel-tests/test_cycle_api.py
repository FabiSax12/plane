"""
PI-22: POST ciclo con fechas inconsistentes (start sin end) retorna 400
PI-23: POST cycle-issues asocia work items al ciclo correctamente
Tecnica: Analisis de valores limite + Cobertura de sentencias
HU-26: Crear ciclo con fecha de inicio y fecha de fin
HU-27: Agregar work items existentes a un ciclo
"""
import pytest
from django.utils import timezone
from datetime import timedelta

from plane.db.models.cycle import CycleIssue
from plane.tests.factories import CycleFactory, IssueFactory


# ---------------------------------------------------------------------------
# PI-22: Fechas inconsistentes
# ---------------------------------------------------------------------------

@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI22OnlyStartDate:
    """POST con start_date pero sin end_date retorna 400."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project):
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/"
        self.response = auth_client.post(
            url,
            data={"name": "Sprint 1", "start_date": "2026-06-01T00:00:00Z"},
            format="json",
        )

    def test_status_code_is_400(self):
        assert self.response.status_code == 400

    def test_response_contains_error_key(self):
        assert "error" in self.response.data


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI22OnlyEndDate:
    """POST con end_date pero sin start_date retorna 400."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project):
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/"
        self.response = auth_client.post(
            url,
            data={"name": "Sprint 1", "end_date": "2026-06-15T00:00:00Z"},
            format="json",
        )

    def test_status_code_is_400(self):
        assert self.response.status_code == 400

    def test_response_contains_error_key(self):
        assert "error" in self.response.data


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI22NoDates:
    """POST sin fechas retorna 201 (fechas son opcionales)."""

    def test_cycle_without_dates_returns_201(self, auth_client, workspace, project):
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/"
        response = auth_client.post(url, data={"name": "Sprint sin fechas"}, format="json")
        assert response.status_code == 201


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI22BothDates:
    """POST con start_date y end_date coherentes retorna 201."""

    def test_cycle_with_both_dates_returns_201(self, auth_client, workspace, project):
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/"
        response = auth_client.post(
            url,
            data={
                "name": "Sprint completo",
                "start_date": "2026-06-01T00:00:00Z",
                "end_date": "2026-06-15T00:00:00Z",
            },
            format="json",
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# PI-23: Asociar issues al ciclo
# ---------------------------------------------------------------------------

@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI23LinkIssuesToCycle:
    """PI-23: POST cycle-issues con 3 issues los vincula al ciclo."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project, default_state, user):
        now = timezone.now()
        self.cycle = CycleFactory(project=project, owned_by=user, start_date=now, end_date=now + timedelta(days=14))
        self.issue1 = IssueFactory(project=project, state=default_state)
        self.issue2 = IssueFactory(project=project, state=default_state)
        self.issue3 = IssueFactory(project=project, state=default_state)
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/{self.cycle.id}/cycle-issues/"
        self.response = auth_client.post(
            url,
            data={"issues": [str(self.issue1.id), str(self.issue2.id), str(self.issue3.id)]},
            format="json",
        )
        self.linked_ids = set(CycleIssue.objects.filter(cycle=self.cycle).values_list("issue_id", flat=True))

    def test_status_code_is_success(self):
        assert self.response.status_code in [200, 201]

    def test_first_issue_linked(self):
        assert self.issue1.id in self.linked_ids

    def test_second_issue_linked(self):
        assert self.issue2.id in self.linked_ids

    def test_third_issue_linked(self):
        assert self.issue3.id in self.linked_ids


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI23EmptyIssues:
    """POST sin issues en el body retorna 400."""

    def test_empty_issues_returns_400(self, auth_client, workspace, project, user):
        now = timezone.now()
        cycle = CycleFactory(project=project, owned_by=user, start_date=now, end_date=now + timedelta(days=14))
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/{cycle.id}/cycle-issues/"
        response = auth_client.post(url, data={"issues": []}, format="json")
        assert response.status_code == 400


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI23CompletedCycle:
    """No se pueden agregar issues a un ciclo ya completado."""

    def test_completed_cycle_rejects_new_issues(self, auth_client, workspace, project, default_state, user):
        past = timezone.now() - timedelta(days=5)
        cycle = CycleFactory(project=project, owned_by=user, start_date=past - timedelta(days=10), end_date=past)
        issue = IssueFactory(project=project, state=default_state)
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/{cycle.id}/cycle-issues/"
        response = auth_client.post(url, data={"issues": [str(issue.id)]}, format="json")
        assert response.status_code == 400
