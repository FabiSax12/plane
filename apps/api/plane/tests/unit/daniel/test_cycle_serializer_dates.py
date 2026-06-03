"""
PU-24: Aceptar fechas de ciclo coherentes (start <= end) en CycleCreateSerializer
Tecnica: Analisis de valores limite
HU-26: Crear ciclo con fecha de inicio y fecha de fin
"""
import pytest
from plane.api.serializers.cycle import CycleCreateSerializer


@pytest.mark.django_db
class TestCycleCreateSerializerDateValidation:

    def _make_serializer(self, project, user, start_date, end_date):
        data = {
            "name": "Sprint 1",
            "owned_by": user.id,
        }
        if start_date is not None:
            data["start_date"] = start_date
        if end_date is not None:
            data["end_date"] = end_date

        return CycleCreateSerializer(
            data=data,
            context={"project_id": project.id},
        )

    def test_pu24_accepts_start_before_end(self, project, user):
        """PU-24 (caso valido): start_date < end_date es aceptado."""
        serializer = self._make_serializer(project, user, "2026-06-01T00:00:00Z", "2026-06-15T00:00:00Z")

        assert serializer.is_valid(), serializer.errors

    def test_rejects_start_after_end(self, project, user):
        """start_date > end_date lanza ValidationError."""
        serializer = self._make_serializer(project, user, "2026-06-15T00:00:00Z", "2026-06-01T00:00:00Z")

        assert not serializer.is_valid()
        error_text = str(serializer.errors).lower()
        assert "start date" in error_text or "end date" in error_text

    def test_accepts_both_dates_null(self, project, user):
        """Sin fechas el ciclo es valido (fechas opcionales)."""
        serializer = self._make_serializer(project, user, None, None)

        assert serializer.is_valid(), serializer.errors

    def test_rejects_when_cycle_view_disabled(self, workspace, user):
        """Si el proyecto no tiene cycle_view=True el serializer rechaza la creacion."""
        from plane.tests.factories import ProjectFactory, ProjectMemberFactory

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

        assert not serializer.is_valid()
        error_text = str(serializer.errors).lower()
        assert "cycle" in error_text or "not enabled" in error_text
