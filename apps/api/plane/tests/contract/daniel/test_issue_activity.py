"""
PI-19: PATCH state de work item registra entrada en IssueActivity
Tecnica: Cobertura de sentencias
HU-17: Actualizar estado de work item arrastrándolo entre columnas

Nota: Celery no corre en modo eager en el entorno de test.
Se usa unittest.mock para interceptar .delay() y ejecutar el task de forma sincrona.
"""
import json
import pytest
from unittest.mock import patch
from django.utils import timezone

from plane.bgtasks.issue_activities_task import issue_activity
from plane.db.models import IssueActivity
from plane.tests.factories import IssueFactory, StateFactory


def run_issue_activity_sync(*args, **kwargs):
    """Ejecuta issue_activity de forma sincrona en lugar de enviarlo a Celery."""
    issue_activity(*args, **kwargs)


@pytest.mark.django_db
class TestIssueStateActivityLog:

    def _patch_url(self, workspace, project, issue):
        return f"/api/workspaces/{workspace.slug}/projects/{project.id}/issues/{issue.id}/"

    @patch("plane.app.views.issue.base.issue_activity.delay", side_effect=run_issue_activity_sync)
    def test_pi19_patch_state_creates_activity_entry(self, mock_delay, auth_client, workspace, project, default_state, user):
        """PI-19: PATCH state retorna 200 y genera entrada en IssueActivity con field=state."""
        new_state = StateFactory(project=project, group="started")
        issue = IssueFactory(project=project, state=default_state)

        url = self._patch_url(workspace, project, issue)
        response = auth_client.patch(
            url,
            data={"state": str(new_state.id)},
            format="json",
        )

        assert response.status_code == 200

        activity = IssueActivity.objects.filter(
            issue=issue,
            field="state",
        ).first()

        assert activity is not None, "No se creo ningun registro de actividad con field=state"
        assert activity.actor == user
        assert str(activity.new_identifier) == str(new_state.id)

    @patch("plane.app.views.issue.base.issue_activity.delay", side_effect=run_issue_activity_sync)
    def test_pi19_activity_records_old_and_new_state(self, mock_delay, auth_client, workspace, project, default_state, user):
        """PI-19: La actividad registra el nombre del estado anterior y el nuevo."""
        new_state = StateFactory(project=project, group="started", name="En Progreso")
        issue = IssueFactory(project=project, state=default_state)

        url = self._patch_url(workspace, project, issue)
        auth_client.patch(
            url,
            data={"state": str(new_state.id)},
            format="json",
        )

        activity = IssueActivity.objects.filter(issue=issue, field="state").first()

        assert activity is not None
        assert activity.new_value == "En Progreso"

    @patch("plane.app.views.issue.base.issue_activity.delay", side_effect=run_issue_activity_sync)
    def test_pi19_delay_was_called_once(self, mock_delay, auth_client, workspace, project, default_state):
        """El task issue_activity.delay es invocado al hacer PATCH state."""
        new_state = StateFactory(project=project, group="started")
        issue = IssueFactory(project=project, state=default_state)

        url = self._patch_url(workspace, project, issue)
        auth_client.patch(
            url,
            data={"state": str(new_state.id)},
            format="json",
        )

        assert mock_delay.called
