# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file in the LICENSE file for details.

# Pruebas unitarias asignadas a Rafael Odio: PU-13, PU-14, PU-15, PU-16, PU-17, PU-18

import pytest

from plane.db.models import Project, State, Issue, Label
from plane.db.models.state import DEFAULT_STATES, StateGroup
from plane.app.serializers import LabelSerializer


# ---------------------------------------------------------------------------
# PU-13 — Detectar estado sin issues asociados (puede borrarse)
# Técnica: Cobertura de decisiones
# Módulo: API de estados / Validador de uso
# Plan: ejecutar Issue.objects.filter(state=state.id).exists() y verificar False
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestStateUsageQuery:
    """PU-13 / PU-14: consulta ORM que determina si un estado tiene issues asociados."""

    @pytest.mark.django_db
    def test_pu13_state_without_issues_query_returns_false(self, workspace, create_user):
        """PU-13: query retorna False → estado sin issues puede borrarse efectivamente."""
        project = Project.objects.create(
            name="PU13 Project", identifier="PU13", workspace=workspace
        )
        state = State.objects.create(
            name="PU13 State",
            color="#FFFFFF",
            project=project,
            workspace=workspace,
            group=StateGroup.UNSTARTED.value,
            default=False,
        )

        # Consulta exacta del código en apps/api/plane/api/views/state.py:240
        issue_exist = Issue.objects.filter(state=state.id).exists()

        # Sin issues asociados la consulta retorna False
        assert issue_exist is False

        # Confirmar la consecuencia del plan: "el borrado es permitido"
        state.delete()
        assert not State.all_state_objects.filter(id=state.id, deleted_at__isnull=True).exists(), (
            "El estado debería haber sido borrado pero aún existe en la base de datos."
        )

    @pytest.mark.django_db
    def test_pu14_state_with_issues_query_returns_true(self, workspace, create_user):
        """PU-14: query retorna True → el borrado debe ser bloqueado, estado permanece en DB."""
        project = Project.objects.create(
            name="PU14 Project", identifier="PU14", workspace=workspace
        )
        state = State.objects.create(
            name="PU14 State",
            color="#FFFFFF",
            project=project,
            workspace=workspace,
            group=StateGroup.UNSTARTED.value,
            default=False,
        )
        Issue.objects.create(
            name="Blocking Issue",
            project=project,
            workspace=workspace,
            state=state,
            created_by=create_user,
            updated_by=create_user,
        )

        # Consulta exacta del código en apps/api/plane/api/views/state.py:240
        issue_exist = Issue.objects.filter(state=state.id).exists()

        # Con issues asociados retorna True
        assert issue_exist is True

        # Confirmar la consecuencia del plan: "el sistema bloqueará el borrado"
        # Replica la guardia del view: solo se borra si issue_exist es False
        if not issue_exist:
            state.delete()

        assert State.all_state_objects.filter(id=state.id, deleted_at__isnull=True).exists(), (
            "El estado no debería haberse borrado mientras tenga issues asociados."
        )


# ---------------------------------------------------------------------------
# PU-15 — Verificar que DEFAULT_STATES incluye un estado con grupo 'completed'
# PU-16 — Verificar que DEFAULT_STATES define exactamente 6 estados
# Técnica: Inspección de constante
# Módulo: Modelo State / DEFAULT_STATES
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDefaultStatesConstant:
    """PU-15 / PU-16: estructura y contenido de DEFAULT_STATES."""

    def test_pu15_default_states_has_at_least_one_completed_group(self):
        """PU-15: DEFAULT_STATES debe incluir al menos un estado con group='completed'."""
        completed = [s for s in DEFAULT_STATES if s.get("group") == "completed"]
        assert len(completed) >= 1, (
            "DEFAULT_STATES no contiene ningún estado con group='completed'. "
            f"Grupos presentes: {[s.get('group') for s in DEFAULT_STATES]}"
        )

    def test_pu16_default_states_has_exactly_six_entries(self):
        """PU-16: DEFAULT_STATES debe definir exactamente 6 estados."""
        assert len(DEFAULT_STATES) == 6, (
            f"Se esperaban 6 estados en DEFAULT_STATES, se encontraron {len(DEFAULT_STATES)}"
        )

    def test_pu16_default_states_expected_names(self):
        """PU-16 (complementario): DEFAULT_STATES contiene los nombres esperados."""
        expected_names = {"Backlog", "Todo", "In Progress", "Done", "Cancelled", "Triage"}
        actual_names = {s.get("name") for s in DEFAULT_STATES}
        assert actual_names == expected_names, (
            f"Nombres inesperados en DEFAULT_STATES.\n"
            f"Esperados: {expected_names}\n"
            f"Encontrados: {actual_names}"
        )


# ---------------------------------------------------------------------------
# PU-17 — Aceptar string de color hex en LabelSerializer
# Técnica: Partición de equivalencia
# Módulo: Modelo Label / LabelSerializer
# Plan: verificar que LabelSerializer acepta color='#1F3864'
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLabelSerializerColor:
    """PU-17: LabelSerializer acepta color hex válido."""

    @pytest.mark.django_db
    def test_pu17_label_serializer_accepts_hex_color(self, workspace):
        """PU-17: serializer es válido con name='TestLabel' y color='#1F3864'."""
        project = Project.objects.create(
            name="PU17 Project", identifier="PU17", workspace=workspace
        )
        serializer = LabelSerializer(
            data={"name": "TestLabel", "color": "#1F3864"},
            context={"project_id": project.id},
        )
        assert serializer.is_valid(), (
            f"LabelSerializer rechazó datos válidos con color hex. Errores: {serializer.errors}"
        )

    @pytest.mark.django_db
    def test_pu17_label_serializer_rejects_duplicate_name(self, workspace):
        """PU-17 (complementario): serializer rechaza un nombre de etiqueta duplicado en el mismo proyecto."""
        project = Project.objects.create(
            name="PU17b Project", identifier="PU17B", workspace=workspace
        )
        # Crear etiqueta existente directamente en DB
        Label.objects.create(
            name="ExistingLabel",
            color="#000000",
            project=project,
            workspace=workspace,
        )
        serializer = LabelSerializer(
            data={"name": "ExistingLabel", "color": "#1F3864"},
            context={"project_id": project.id},
        )
        assert not serializer.is_valid(), (
            "LabelSerializer debería rechazar un nombre duplicado dentro del mismo proyecto."
        )
        assert "name" in serializer.errors, (
            f"Se esperaba error en el campo 'name'. Errores recibidos: {serializer.errors}"
        )


# ---------------------------------------------------------------------------
# PU-18 — Generar sequence_id autoincremental al crear Issue
# Técnica: Cobertura de sentencias
# Módulo: Modelo Issue / método save()
# Plan: issue2.sequence_id == issue1.sequence_id + 1
# Nota: transaction=True requerido para pg_advisory_xact_lock en Issue.save()
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestIssueSequenceId:
    """PU-18: sequence_id se auto-incrementa correctamente por proyecto."""

    @pytest.mark.django_db(transaction=True)
    def test_pu18_sequence_id_increments_per_project(self, workspace, create_user):
        """PU-18: issue2.sequence_id == issue1.sequence_id + 1 dentro del mismo proyecto."""
        project = Project.objects.create(
            name="PU18 Project", identifier="PU18", workspace=workspace
        )
        state = State.objects.create(
            name="Todo",
            color="#FFFFFF",
            project=project,
            workspace=workspace,
            group=StateGroup.UNSTARTED.value,
        )
        issue1 = Issue.objects.create(
            name="Issue 1",
            project=project,
            workspace=workspace,
            state=state,
            created_by=create_user,
            updated_by=create_user,
        )
        issue2 = Issue.objects.create(
            name="Issue 2",
            project=project,
            workspace=workspace,
            state=state,
            created_by=create_user,
            updated_by=create_user,
        )
        assert issue2.sequence_id == issue1.sequence_id + 1

    @pytest.mark.django_db(transaction=True)
    def test_pu18_sequence_id_independent_per_project(self, workspace, create_user):
        """PU-18 (complementario): sequence_id reinicia en 1 para proyectos distintos."""
        project_a = Project.objects.create(
            name="PU18 Project A", identifier="PU18A", workspace=workspace
        )
        project_b = Project.objects.create(
            name="PU18 Project B", identifier="PU18B", workspace=workspace
        )
        state_a = State.objects.create(
            name="Todo", color="#FFFFFF", project=project_a,
            workspace=workspace, group=StateGroup.UNSTARTED.value,
        )
        state_b = State.objects.create(
            name="Todo", color="#FFFFFF", project=project_b,
            workspace=workspace, group=StateGroup.UNSTARTED.value,
        )
        Issue.objects.create(
            name="A-1", project=project_a, workspace=workspace,
            state=state_a, created_by=create_user, updated_by=create_user,
        )
        issue_b = Issue.objects.create(
            name="B-1", project=project_b, workspace=workspace,
            state=state_b, created_by=create_user, updated_by=create_user,
        )
        assert issue_b.sequence_id == 1
