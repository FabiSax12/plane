"""
PI-19: PATCH state de work item registra entrada en IssueActivity
Tecnica: Cobertura de sentencias
HU-17: Actualizar estado de work item arrastrandolo entre columnas

Celery no corre en modo eager en el entorno de test.
Se usa unittest.mock para interceptar .delay() y ejecutar el task de forma sincrona.
"""
import pytest
from unittest.mock import patch

from plane.bgtasks.issue_activities_task import issue_activity
from plane.db.models import IssueActivity
from plane.tests.factories import IssueFactory, StateFactory


def run_sync(*args, **kwargs):
    """Ejecuta issue_activity de forma sincrona en lugar de enviarlo a Celery."""
    issue_activity(*args, **kwargs)


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI19StateChangeActivity:
    """PI-19: PATCH state genera entrada en IssueActivity con datos correctos."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project, default_state, user):
        self.new_state = StateFactory(project=project, group="started", name="En Progreso")
        issue = IssueFactory(project=project, state=default_state)
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/issues/{issue.id}/"
        with patch("plane.app.views.issue.base.issue_activity.delay", side_effect=run_sync):
            self.response = auth_client.patch(url, data={"state": str(self.new_state.id)}, format="json")
        self.activity = IssueActivity.objects.filter(issue=issue, field="state").first()
        self.user = user

    def test_patch_returns_200(self):
        assert self.response.status_code == 200

    def test_activity_entry_was_created(self):
        assert self.activity is not None

    def test_activity_actor_is_correct_user(self):
        assert self.activity.actor == self.user

    def test_activity_new_identifier_matches_new_state(self):
        assert str(self.activity.new_identifier) == str(self.new_state.id)

    def test_activity_new_value_is_state_name(self):
        assert self.activity.new_value == "En Progreso"


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI19DelayIsCalled:
    """PI-19: issue_activity.delay es invocado al hacer PATCH state."""

    def test_delay_was_called(self, auth_client, workspace, project, default_state):
        new_state = StateFactory(project=project, group="started")
        issue = IssueFactory(project=project, state=default_state)
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/issues/{issue.id}/"
        with patch("plane.app.views.issue.base.issue_activity.delay", side_effect=run_sync) as mock_delay:
            auth_client.patch(url, data={"state": str(new_state.id)}, format="json")
        assert mock_delay.called
