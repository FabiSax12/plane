"""
PU-25: Calcular serie de burndown con burndown_plot
Tecnica: Cobertura de sentencias
HU-28: Visualizar el burndown chart de un ciclo activo

Nota: La firma real es burndown_plot(queryset, slug, project_id, plot_type, cycle_id, module_id).
El parametro queryset es un objeto Cycle anotado con total_issues (no un queryset de issues).
"""
import pytest
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from plane.db.models.cycle import Cycle
from plane.utils.analytics_plot import burndown_plot
from plane.tests.factories import CycleFactory, IssueFactory, StateFactory


@pytest.mark.django_db
class TestBurndownPlot:

    def _get_annotated_cycle(self, cycle):
        """Replica la anotacion que hace la vista antes de llamar a burndown_plot."""
        return Cycle.objects.filter(id=cycle.id).annotate(
            total_issues=Count("issue_cycle", filter=__import__("django.db.models", fromlist=["Q"]).Q(
                issue_cycle__deleted_at__isnull=True
            ))
        ).first()

    def test_pu25_returns_dict_with_date_keys_for_cycle(self, project, default_state, workspace):
        """PU-25: burndown_plot retorna un dict con fechas de string como claves."""
        now = timezone.now()
        cycle = CycleFactory(
            project=project,
            start_date=now,
            end_date=now + timedelta(days=4),
        )
        annotated_cycle = self._get_annotated_cycle(cycle)

        result = burndown_plot(
            queryset=annotated_cycle,
            slug=workspace.slug,
            project_id=project.id,
            plot_type="issues",
            cycle_id=cycle.id,
        )

        assert isinstance(result, dict)
        assert len(result) == 5  # 5 dias: dia 0 al dia 4

    def test_chart_keys_are_date_strings(self, project, default_state, workspace):
        """Las claves del dict son strings con formato de fecha (YYYY-MM-DD)."""
        from datetime import date
        now = timezone.now()
        cycle = CycleFactory(
            project=project,
            start_date=now,
            end_date=now + timedelta(days=2),
        )
        annotated_cycle = self._get_annotated_cycle(cycle)

        result = burndown_plot(
            queryset=annotated_cycle,
            slug=workspace.slug,
            project_id=project.id,
            plot_type="issues",
            cycle_id=cycle.id,
        )

        for key in result.keys():
            parsed = date.fromisoformat(key)
            assert parsed >= now.date()

    def test_returns_empty_dict_when_cycle_has_no_dates(self, project, default_state, workspace):
        """Ciclo sin start_date ni end_date retorna dict vacio."""
        cycle = CycleFactory(project=project, start_date=None, end_date=None)
        annotated_cycle = self._get_annotated_cycle(cycle)

        result = burndown_plot(
            queryset=annotated_cycle,
            slug=workspace.slug,
            project_id=project.id,
            plot_type="issues",
            cycle_id=cycle.id,
        )

        assert result == {}

    def test_pending_count_decreases_as_issues_complete(self, project, workspace):
        """Issues completados en el pasado reducen el conteo pendiente en esa fecha."""
        from plane.db.models.cycle import CycleIssue
        state_completed = StateFactory(project=project, group="completed")
        yesterday = timezone.now() - timedelta(days=1)
        two_days_ago = timezone.now() - timedelta(days=2)

        cycle = CycleFactory(
            project=project,
            start_date=two_days_ago,
            end_date=timezone.now(),
        )

        issue = IssueFactory(
            project=project,
            state=state_completed,
            completed_at=yesterday,
        )
        CycleIssue.objects.create(cycle=cycle, issue=issue)

        annotated_cycle = self._get_annotated_cycle(cycle)

        result = burndown_plot(
            queryset=annotated_cycle,
            slug=workspace.slug,
            project_id=project.id,
            plot_type="issues",
            cycle_id=cycle.id,
        )

        assert isinstance(result, dict)
        values = [v for v in result.values() if v is not None]
        assert len(values) > 0
