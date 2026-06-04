"""
PU-21: Aceptar issue donde start_date <= target_date
PU-22: Rechazar issue donde start_date > target_date
Tecnica: Analisis de valores limite
HU-19: Establecer fecha limite y prioridad en work item
"""
import pytest
from plane.api.serializers.issue import IssueSerializer


def make_serializer(data, project):
    return IssueSerializer(
        data=data,
        context={
            "project_id": project.id,
            "workspace_id": project.workspace.id,
        },
    )


def base_data(state, start_date, target_date):
    return {
        "name": "Test Issue",
        "state": state.id,
        "priority": "none",
        "start_date": start_date,
        "target_date": target_date,
    }


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPU21ValidDates:
    """PU-21: Fechas coherentes (start <= target) son aceptadas."""

    def test_accepts_start_date_before_target_date(self, project, default_state):
        serializer = make_serializer(base_data(default_state, "2026-06-01", "2026-06-15"), project)
        assert serializer.is_valid() is True

    def test_accepts_start_date_equal_to_target_date(self, project, default_state):
        serializer = make_serializer(base_data(default_state, "2026-06-01", "2026-06-01"), project)
        assert serializer.is_valid() is True

    def test_accepts_null_dates(self, project, default_state):
        serializer = make_serializer(base_data(default_state, None, None), project)
        assert serializer.is_valid() is True


@pytest.mark.qa
@pytest.mark.daniel
@pytest.mark.django_db
class TestPU22InvalidDates:
    """PU-22: start_date > target_date es rechazado."""

    @pytest.fixture(autouse=True)
    def setup(self, project, default_state):
        serializer = make_serializer(base_data(default_state, "2026-06-15", "2026-06-01"), project)
        serializer.is_valid()
        self.valid = serializer.is_valid()
        self.error_text = str(serializer.errors).lower()

    def test_serializer_is_invalid(self):
        assert self.valid is False

    def test_error_mentions_start_or_target_date(self):
        assert "start date" in self.error_text or "target date" in self.error_text
