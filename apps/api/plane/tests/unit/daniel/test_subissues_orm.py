"""
PU-19: Calcular cantidad de sub-issues completados con ORM
Tecnica: Cobertura de sentencias
HU-20: Crear sub-work items dentro de un work item padre
"""
import pytest
from plane.db.models import Issue
from plane.tests.factories import IssueFactory, StateFactory


@pytest.mark.django_db
class TestSubIssuesCompletedCount:

    def test_pu19_counts_only_completed_sub_issues(self, project, default_state):
        """PU-19: De 4 sub-issues, 3 completados y 1 en started, el ORM retorna 3."""
        state_completed = StateFactory(project=project, group="completed")
        state_started = StateFactory(project=project, group="started")

        parent = IssueFactory(project=project, state=default_state)

        IssueFactory(project=project, state=state_completed, parent=parent)
        IssueFactory(project=project, state=state_completed, parent=parent)
        IssueFactory(project=project, state=state_completed, parent=parent)
        IssueFactory(project=project, state=state_started, parent=parent)

        count = Issue.objects.filter(
            parent_id=parent.id,
            state__group="completed",
        ).count()

        assert count == 3

    def test_counts_zero_when_no_sub_issues_completed(self, project, default_state):
        """Sin sub-issues completados el conteo es 0."""
        state_started = StateFactory(project=project, group="started")

        parent = IssueFactory(project=project, state=default_state)
        IssueFactory(project=project, state=state_started, parent=parent)
        IssueFactory(project=project, state=state_started, parent=parent)

        count = Issue.objects.filter(
            parent_id=parent.id,
            state__group="completed",
        ).count()

        assert count == 0

    def test_counts_zero_for_issue_without_children(self, project, default_state):
        """Un issue sin sub-issues retorna 0."""
        parent = IssueFactory(project=project, state=default_state)

        count = Issue.objects.filter(
            parent_id=parent.id,
            state__group="completed",
        ).count()

        assert count == 0

    def test_only_counts_children_of_the_correct_parent(self, project, default_state):
        """El filtro por parent_id no mezcla sub-issues de distintos padres."""
        state_completed = StateFactory(project=project, group="completed")

        parent_a = IssueFactory(project=project, state=default_state)
        parent_b = IssueFactory(project=project, state=default_state)

        IssueFactory(project=project, state=state_completed, parent=parent_a)
        IssueFactory(project=project, state=state_completed, parent=parent_a)
        IssueFactory(project=project, state=state_completed, parent=parent_b)

        count_a = Issue.objects.filter(
            parent_id=parent_a.id,
            state__group="completed",
        ).count()

        assert count_a == 2
