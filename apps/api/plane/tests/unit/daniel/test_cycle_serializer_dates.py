"""
PU-24: Aceptar fechas de ciclo coherentes (start <= end) en CycleCreateSerializer
Tecnica: Analisis de valores limite
HU-26: Crear ciclo con fecha de inicio y fecha de fin
"""
import pytest
from plane.api.serializers.cycle import CycleCreateSerializer
from plane.tests.factories import ProjectFactory, ProjectMemberFactory


def make_cycle_serializer(project, user, start_date, end_date):
    data = {"name": "Sprint 1", "owned_by": user.id}
    if start_date is not None:
        data["start_date"] = start_date
    if end_date is not None:
        data["end_date"] = end_date
    return CycleCreateSerializer(data=data, context={"project_id": project.id})


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPU24ValidCycleDates:
    """PU-24: Fechas coherentes son aceptadas por CycleCreateSerializer."""

    def test_accepts_start_before_end(self, project, user):
        serializer = make_cycle_serializer(project, user, "2026-06-01T00:00:00Z", "2026-06-15T00:00:00Z")
        assert serializer.is_valid() is True

    def test_accepts_both_dates_null(self, project, user):
        serializer = make_cycle_serializer(project, user, None, None)
        assert serializer.is_valid() is True


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPU24InvalidCycleDates:
    """start_date > end_date es rechazado."""

    @pytest.fixture(autouse=True)
    def setup(self, project, user):
        serializer = make_cycle_serializer(project, user, "2026-06-15T00:00:00Z", "2026-06-01T00:00:00Z")
        serializer.is_valid()
        self.valid = serializer.is_valid()
        self.error_text = str(serializer.errors).lower()

    def test_serializer_is_invalid(self):
        assert self.valid is False

    def test_error_mentions_start_or_end_date(self):
        assert "start date" in self.error_text or "end date" in self.error_text


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPU24CycleViewDisabled:
    """CycleCreateSerializer rechaza si el proyecto no tiene cycle_view=True."""

    @pytest.fixture(autouse=True)
    def setup(self, workspace, user):
        project_no_cycles = ProjectFactory(
            workspace=workspace,
            created_by=user,
            updated_by=user,
            cycle_view=False,
        )
        ProjectMemberFactory(project=project_no_cycles, member=user, role=20)
        serializer = CycleCreateSerializer(
            data={"name": "Sprint", "owned_by": user.id},
            context={"project_id": project_no_cycles.id},
        )
        serializer.is_valid()
        self.valid = serializer.is_valid()
        self.error_text = str(serializer.errors).lower()

    def test_serializer_is_invalid(self):
        assert self.valid is False

    def test_error_mentions_cycle(self):
        assert "cycle" in self.error_text or "not enabled" in self.error_text
