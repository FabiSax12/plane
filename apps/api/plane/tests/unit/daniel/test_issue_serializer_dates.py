"""
PU-21: Aceptar issue donde start_date <= target_date
PU-22: Rechazar issue donde start_date > target_date
Tecnica: Analisis de valores limite
HU-19: Establecer fecha limite y prioridad en work item
"""
import pytest
from plane.api.serializers.issue import IssueSerializer


@pytest.mark.django_db
class TestIssueSerializerDateValidation:

    def _base_data(self, project, state, start_date, target_date):
        """Payload minimo valido para IssueSerializer."""
        return {
            "name": "Test Issue",
            "state": state.id,
            "priority": "none",
            "start_date": start_date,
            "target_date": target_date,
        }

    def _make_serializer(self, data, project):
        return IssueSerializer(
            data=data,
            context={
                "project_id": project.id,
                "workspace_id": project.workspace.id,
            },
        )

    def test_pu21_accepts_start_date_before_target_date(self, project, default_state):
        """PU-21: start_date < target_date debe ser valido."""
        data = self._base_data(project, default_state, "2026-06-01", "2026-06-15")
        serializer = self._make_serializer(data, project)

        assert serializer.is_valid(), serializer.errors

    def test_pu21_accepts_start_date_equal_to_target_date(self, project, default_state):
        """PU-21 (limite exacto): start_date == target_date debe ser valido."""
        data = self._base_data(project, default_state, "2026-06-01", "2026-06-01")
        serializer = self._make_serializer(data, project)

        assert serializer.is_valid(), serializer.errors

    def test_pu22_rejects_start_date_after_target_date(self, project, default_state):
        """PU-22: start_date > target_date debe ser invalido."""
        data = self._base_data(project, default_state, "2026-06-15", "2026-06-01")
        serializer = self._make_serializer(data, project)

        assert not serializer.is_valid()
        error_text = str(serializer.errors).lower()
        assert "start date" in error_text or "target date" in error_text

    def test_pu21_accepts_null_dates(self, project, default_state):
        """Fechas nulas (sin start ni target) son validas, no hay restriccion."""
        data = self._base_data(project, default_state, None, None)
        serializer = self._make_serializer(data, project)

        assert serializer.is_valid(), serializer.errors
