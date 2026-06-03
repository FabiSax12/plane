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
from plane.tests.factories import CycleFactory, IssueFactory, StateFactory


@pytest.mark.django_db
class TestCycleCreateAPI:

    def _cycles_url(self, workspace, project):
        return f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/"

    def test_pi22_only_start_date_returns_400(self, auth_client, workspace, project):
        """PI-22: POST con start_date sin end_date retorna 400 con mensaje especifico."""
        url = self._cycles_url(workspace, project)
        response = auth_client.post(
            url,
            data={"name": "Sprint 1", "start_date": "2026-06-01T00:00:00Z"},
            format="json",
        )

        assert response.status_code == 400
        assert "error" in response.data
        assert "start date" in response.data["error"].lower() or "end date" in response.data["error"].lower()

    def test_pi22_only_end_date_returns_400(self, auth_client, workspace, project):
        """POST con end_date sin start_date retorna 400."""
        url = self._cycles_url(workspace, project)
        response = auth_client.post(
            url,
            data={"name": "Sprint 1", "end_date": "2026-06-15T00:00:00Z"},
            format="json",
        )

        assert response.status_code == 400
        assert "error" in response.data

    def test_cycle_without_dates_is_accepted(self, auth_client, workspace, project):
        """POST sin fechas retorna 201 (fechas son opcionales)."""
        url = self._cycles_url(workspace, project)
        response = auth_client.post(
            url,
            data={"name": "Sprint sin fechas"},
            format="json",
        )

        assert response.status_code == 201

    def test_cycle_with_both_dates_is_accepted(self, auth_client, workspace, project):
        """POST con start_date y end_date coherentes retorna 201."""
        url = self._cycles_url(workspace, project)
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


@pytest.mark.django_db
class TestCycleIssueAssociationAPI:

    def _cycle_issues_url(self, workspace, project, cycle):
        return f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/{cycle.id}/cycle-issues/"

    def test_pi23_issues_are_linked_to_cycle(self, auth_client, workspace, project, default_state):
        """PI-23: POST cycle-issues con 3 issues los asocia correctamente al ciclo."""
        now = timezone.now()
        cycle = CycleFactory(
            project=project,
            start_date=now,
            end_date=now + timedelta(days=14),
        )
        issue1 = IssueFactory(project=project, state=default_state)
        issue2 = IssueFactory(project=project, state=default_state)
        issue3 = IssueFactory(project=project, state=default_state)

        url = self._cycle_issues_url(workspace, project, cycle)
        response = auth_client.post(
            url,
            data={"issues": [str(issue1.id), str(issue2.id), str(issue3.id)]},
            format="json",
        )

        assert response.status_code in [200, 201]

        linked_issue_ids = set(
            CycleIssue.objects.filter(cycle=cycle).values_list("issue_id", flat=True)
        )
        assert issue1.id in linked_issue_ids
        assert issue2.id in linked_issue_ids
        assert issue3.id in linked_issue_ids

    def test_pi23_empty_issues_returns_400(self, auth_client, workspace, project):
        """POST sin issues en el body retorna 400."""
        now = timezone.now()
        cycle = CycleFactory(
            project=project,
            start_date=now,
            end_date=now + timedelta(days=14),
        )

        url = self._cycle_issues_url(workspace, project, cycle)
        response = auth_client.post(url, data={"issues": []}, format="json")

        assert response.status_code == 400

    def test_pi23_completed_cycle_rejects_new_issues(self, auth_client, workspace, project, default_state):
        """No se pueden agregar issues a un ciclo ya completado (end_date en el pasado)."""
        past = timezone.now() - timedelta(days=5)
        cycle = CycleFactory(
            project=project,
            start_date=past - timedelta(days=10),
            end_date=past,
        )
        issue = IssueFactory(project=project, state=default_state)

        url = self._cycle_issues_url(workspace, project, cycle)
        response = auth_client.post(
            url,
            data={"issues": [str(issue.id)]},
            format="json",
        )

        assert response.status_code == 400
        assert "completed" in response.data.get("error", "").lower()
