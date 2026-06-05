"""
PU-25: Calcular serie de burndown con burndown_plot
Tecnica: Cobertura de sentencias
HU-28: Visualizar el burndown chart de un ciclo activo

Nota: La firma real es burndown_plot(queryset, slug, project_id, plot_type, cycle_id, module_id).
El parametro queryset es un objeto Cycle anotado con total_issues, no un queryset de issues.
"""
import pytest
from datetime import date, timedelta
from django.db.models import Count, Q
from django.utils import timezone

from plane.db.models.cycle import Cycle, CycleIssue
from plane.utils.analytics_plot import burndown_plot
from plane.tests.factories import CycleFactory, IssueFactory, StateFactory


def get_annotated_cycle(cycle):
    """Replica la anotacion que hace la vista antes de llamar a burndown_plot."""
    return Cycle.objects.filter(id=cycle.id).annotate(
        total_issues=Count(
            "issue_cycle",
            filter=Q(issue_cycle__deleted_at__isnull=True),
        )
    ).first()


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestBurndownPlotReturnShape:
    """PU-25: burndown_plot retorna un dict con fechas como claves."""

    @pytest.fixture(autouse=True)
    def setup(self, project, default_state, workspace, user):
        now = timezone.now()
        self.cycle = CycleFactory(project=project, owned_by=user, start_date=now, end_date=now + timedelta(days=4))
        annotated = get_annotated_cycle(self.cycle)
        self.result = burndown_plot(
            queryset=annotated,
            slug=workspace.slug,
            project_id=project.id,
            plot_type="issues",
            cycle_id=self.cycle.id,
        )

    def test_result_is_a_dict(self):
        assert isinstance(self.result, dict)

    def test_result_has_correct_number_of_days(self):
        assert len(self.result) == 5

    def test_all_keys_are_valid_iso_date_strings(self):
        assert all(date.fromisoformat(k) is not None for k in self.result.keys())


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestBurndownPlotEmptyCycle:
    """Ciclo sin fechas retorna dict vacio."""

    def test_returns_empty_dict_when_cycle_has_no_dates(self, project, default_state, workspace, user):
        cycle = CycleFactory(project=project, owned_by=user, start_date=None, end_date=None)
        annotated = get_annotated_cycle(cycle)
        result = burndown_plot(
            queryset=annotated,
            slug=workspace.slug,
            project_id=project.id,
            plot_type="issues",
            cycle_id=cycle.id,
        )
        assert result == {}


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestBurndownPlotWithCompletedIssues:
    """Ciclo con issues completados en el pasado genera valores no vacios."""

    @pytest.fixture(autouse=True)
    def setup(self, project, workspace, user):
        state_completed = StateFactory(project=project, group="completed")
        two_days_ago = timezone.now() - timedelta(days=2)
        yesterday = timezone.now() - timedelta(days=1)
        self.cycle = CycleFactory(
            project=project,
            owned_by=user,
            start_date=two_days_ago,
            end_date=timezone.now(),
        )
        issue = IssueFactory(project=project, state=state_completed, completed_at=yesterday)
        CycleIssue.objects.create(
            cycle=self.cycle,
            issue=issue,
            project=project,
            workspace_id=self.cycle.workspace_id,
            created_by=user,
            updated_by=user,
        )
        annotated = get_annotated_cycle(self.cycle)
        self.result = burndown_plot(
            queryset=annotated,
            slug=workspace.slug,
            project_id=project.id,
            plot_type="issues",
            cycle_id=self.cycle.id,
        )

    def test_result_is_a_dict(self):
        assert isinstance(self.result, dict)

    def test_result_has_non_null_values(self):
        non_null_values = [v for v in self.result.values() if v is not None]
        assert len(non_null_values) > 0
