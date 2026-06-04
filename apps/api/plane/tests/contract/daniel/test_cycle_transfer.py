"""
PI-24: POST transfer-issues mueve issues incompletos al ciclo destino con progress_snapshot
Tecnica: Tabla de decision + Cobertura de sentencias
HU-29: Completar ciclo y transferir work items incompletos

Solo se transfieren issues con state.group in [backlog, unstarted, started].
Los issues completed/cancelled permanecen en el ciclo origen.
Se persiste progress_snapshot en el ciclo origen antes de transferir.
"""
import pytest
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta

from plane.db.models.cycle import Cycle, CycleIssue
from plane.tests.factories import CycleFactory, IssueFactory, StateFactory


def create_cycle_issue(cycle, issue, project, workspace_id, user):
    return CycleIssue.objects.create(
        cycle=cycle,
        issue=issue,
        project=project,
        workspace_id=workspace_id,
        created_by=user,
        updated_by=user,
    )


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI24TransferIncompleteIssues:
    """PI-24: Issues incompletos se transfieren al ciclo destino."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project, user):
        now = timezone.now()
        state_backlog = StateFactory(project=project, group="backlog")
        state_started = StateFactory(project=project, group="started")
        state_completed = StateFactory(project=project, group="completed")
        self.origin = CycleFactory(project=project, start_date=now - timedelta(days=10), end_date=now + timedelta(days=1))
        self.destination = CycleFactory(project=project, start_date=now, end_date=now + timedelta(days=14))
        self.issue_backlog = IssueFactory(project=project, state=state_backlog)
        self.issue_started = IssueFactory(project=project, state=state_started)
        self.issue_completed = IssueFactory(project=project, state=state_completed)
        create_cycle_issue(self.origin, self.issue_backlog, project, workspace.id, user)
        create_cycle_issue(self.origin, self.issue_started, project, workspace.id, user)
        create_cycle_issue(self.origin, self.issue_completed, project, workspace.id, user)
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/{self.origin.id}/transfer-issues/"
        with patch("plane.utils.cycle_transfer_issues.issue_activity.delay"):
            self.response = auth_client.post(url, data={"new_cycle_id": str(self.destination.id)}, format="json")
        self.dest_ids = set(CycleIssue.objects.filter(cycle=self.destination).values_list("issue_id", flat=True))

    def test_returns_200(self):
        assert self.response.status_code == 200

    def test_backlog_issue_moved_to_destination(self):
        assert self.issue_backlog.id in self.dest_ids

    def test_started_issue_moved_to_destination(self):
        assert self.issue_started.id in self.dest_ids


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI24CompletedIssuesStayInOrigin:
    """PI-24: Issues completados permanecen en el ciclo origen."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project, user):
        now = timezone.now()
        state_completed = StateFactory(project=project, group="completed")
        state_backlog = StateFactory(project=project, group="backlog")
        self.origin = CycleFactory(project=project, start_date=now - timedelta(days=10), end_date=now + timedelta(days=1))
        self.destination = CycleFactory(project=project, start_date=now, end_date=now + timedelta(days=14))
        self.issue_completed = IssueFactory(project=project, state=state_completed)
        issue_backlog = IssueFactory(project=project, state=state_backlog)
        create_cycle_issue(self.origin, self.issue_completed, project, workspace.id, user)
        create_cycle_issue(self.origin, issue_backlog, project, workspace.id, user)
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/{self.origin.id}/transfer-issues/"
        with patch("plane.utils.cycle_transfer_issues.issue_activity.delay"):
            auth_client.post(url, data={"new_cycle_id": str(self.destination.id)}, format="json")
        self.origin_ids = set(CycleIssue.objects.filter(cycle=self.origin).values_list("issue_id", flat=True))

    def test_completed_issue_stays_in_origin(self):
        assert self.issue_completed.id in self.origin_ids


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI24ProgressSnapshot:
    """PI-24: progress_snapshot queda persistido en el ciclo origen."""

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, workspace, project, user):
        now = timezone.now()
        state_backlog = StateFactory(project=project, group="backlog")
        state_completed = StateFactory(project=project, group="completed")
        self.origin = CycleFactory(project=project, start_date=now - timedelta(days=10), end_date=now + timedelta(days=1))
        destination = CycleFactory(project=project, start_date=now, end_date=now + timedelta(days=14))
        create_cycle_issue(self.origin, IssueFactory(project=project, state=state_backlog), project, workspace.id, user)
        create_cycle_issue(self.origin, IssueFactory(project=project, state=state_completed), project, workspace.id, user)
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/{self.origin.id}/transfer-issues/"
        with patch("plane.utils.cycle_transfer_issues.issue_activity.delay"):
            auth_client.post(url, data={"new_cycle_id": str(destination.id)}, format="json")
        self.origin.refresh_from_db()

    def test_progress_snapshot_is_not_none(self):
        assert self.origin.progress_snapshot is not None

    def test_progress_snapshot_is_not_empty(self):
        assert self.origin.progress_snapshot != {}

    def test_progress_snapshot_contains_total_issues(self):
        assert "total_issues" in self.origin.progress_snapshot


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPI24MissingNewCycleId:
    """POST sin new_cycle_id retorna 400."""

    def test_missing_new_cycle_id_returns_400(self, auth_client, workspace, project):
        now = timezone.now()
        origin = CycleFactory(project=project, start_date=now - timedelta(days=5), end_date=now + timedelta(days=1))
        url = f"/api/workspaces/{workspace.slug}/projects/{project.id}/cycles/{origin.id}/transfer-issues/"
        response = auth_client.post(url, data={}, format="json")
        assert response.status_code == 400
