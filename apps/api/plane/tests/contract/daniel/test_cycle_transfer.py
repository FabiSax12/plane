"""
PI-24: POST transfer-issues mueve issues incompletos al ciclo destino con progress_snapshot
Tecnica: Tabla de decision + Cobertura de sentencias
HU-29: Completar ciclo y transferir work items incompletos

Flujo real verificado en cycle_transfer_issues.py:
- Solo se transfieren issues con state.group in [backlog, unstarted, started]
- Los issues completed y cancelled permanecen en el ciclo origen
- Se persiste progress_snapshot en el ciclo origen antes de transferir
"""
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta

from plane.db.models.cycle import Cycle, CycleIssue
from plane.tests.factories import CycleFactory, IssueFactory, StateFactory


@pytest.mark.django_db
class TestTransferCycleIssues:

    def _transfer_url(self, workspace, project, cycle):
        return f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/{cycle.id}/transfer-issues/"

    def _create_cycle_issue(self, cycle, issue, project, workspace_id, user):
        return CycleIssue.objects.create(
            cycle=cycle,
            issue=issue,
            project=project,
            workspace_id=workspace_id,
            created_by=user,
            updated_by=user,
        )

    @patch("plane.utils.cycle_transfer_issues.issue_activity.delay")
    def test_pi24_incomplete_issues_move_to_new_cycle(self, mock_delay, auth_client, workspace, project, user):
        """PI-24: Los issues incompletos (backlog/unstarted/started) se transfieren al ciclo destino."""
        now = timezone.now()
        state_backlog = StateFactory(project=project, group="backlog")
        state_started = StateFactory(project=project, group="started")
        state_completed = StateFactory(project=project, group="completed")

        origin = CycleFactory(project=project, start_date=now - timedelta(days=10), end_date=now + timedelta(days=1))
        destination = CycleFactory(project=project, start_date=now, end_date=now + timedelta(days=14))

        issue_backlog = IssueFactory(project=project, state=state_backlog)
        issue_started = IssueFactory(project=project, state=state_started)
        issue_completed = IssueFactory(project=project, state=state_completed)

        self._create_cycle_issue(origin, issue_backlog, project, workspace.id, user)
        self._create_cycle_issue(origin, issue_started, project, workspace.id, user)
        self._create_cycle_issue(origin, issue_completed, project, workspace.id, user)

        url = self._transfer_url(workspace, project, origin)
        response = auth_client.post(url, data={"new_cycle_id": str(destination.id)}, format="json")

        assert response.status_code == 200

        dest_issue_ids = set(CycleIssue.objects.filter(cycle=destination).values_list("issue_id", flat=True))
        assert issue_backlog.id in dest_issue_ids
        assert issue_started.id in dest_issue_ids

    @patch("plane.utils.cycle_transfer_issues.issue_activity.delay")
    def test_pi24_completed_issues_stay_in_origin(self, mock_delay, auth_client, workspace, project, user):
        """PI-24: Los issues completados permanecen en el ciclo origen tras la transferencia."""
        now = timezone.now()
        state_completed = StateFactory(project=project, group="completed")
        state_backlog = StateFactory(project=project, group="backlog")

        origin = CycleFactory(project=project, start_date=now - timedelta(days=10), end_date=now + timedelta(days=1))
        destination = CycleFactory(project=project, start_date=now, end_date=now + timedelta(days=14))

        issue_completed = IssueFactory(project=project, state=state_completed)
        issue_backlog = IssueFactory(project=project, state=state_backlog)

        self._create_cycle_issue(origin, issue_completed, project, workspace.id, user)
        self._create_cycle_issue(origin, issue_backlog, project, workspace.id, user)

        url = self._transfer_url(workspace, project, origin)
        auth_client.post(url, data={"new_cycle_id": str(destination.id)}, format="json")

        origin_issue_ids = set(CycleIssue.objects.filter(cycle=origin).values_list("issue_id", flat=True))
        assert issue_completed.id in origin_issue_ids

    @patch("plane.utils.cycle_transfer_issues.issue_activity.delay")
    def test_pi24_progress_snapshot_is_saved_in_origin(self, mock_delay, auth_client, workspace, project, user):
        """PI-24: El progress_snapshot queda persistido en el ciclo origen tras la transferencia."""
        now = timezone.now()
        state_backlog = StateFactory(project=project, group="backlog")
        state_completed = StateFactory(project=project, group="completed")

        origin = CycleFactory(project=project, start_date=now - timedelta(days=10), end_date=now + timedelta(days=1))
        destination = CycleFactory(project=project, start_date=now, end_date=now + timedelta(days=14))

        issue_backlog = IssueFactory(project=project, state=state_backlog)
        issue_completed = IssueFactory(project=project, state=state_completed)

        self._create_cycle_issue(origin, issue_backlog, project, workspace.id, user)
        self._create_cycle_issue(origin, issue_completed, project, workspace.id, user)

        url = self._transfer_url(workspace, project, origin)
        auth_client.post(url, data={"new_cycle_id": str(destination.id)}, format="json")

        origin.refresh_from_db()
        assert origin.progress_snapshot is not None
        assert origin.progress_snapshot != {}
        assert "total_issues" in origin.progress_snapshot

    def test_pi24_missing_new_cycle_id_returns_400(self, auth_client, workspace, project):
        """POST sin new_cycle_id retorna 400."""
        now = timezone.now()
        origin = CycleFactory(project=project, start_date=now - timedelta(days=5), end_date=now + timedelta(days=1))

        url = self._transfer_url(workspace, project, origin)
        response = auth_client.post(url, data={}, format="json")

        assert response.status_code == 400
        assert "error" in response.data
