# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

# Pruebas unitarias asignadas a Rafael Odio: PU-13, PU-14, PU-15, PU-16, PU-17, PU-18
# Ejecución:
#   docker compose -f deploy/docker-compose-test.yml exec api-tests \
#     python -m pytest plane/tests/Rafael/test_rafael_states_issues.py -v

import pytest

from plane.db.models import Issue, Label, Project, State
from plane.db.models.state import DEFAULT_STATES, StateGroup
from plane.app.serializers import LabelSerializer


# ---------------------------------------------------------------------------
# PU-13 — Estado sin issues asociados puede borrarse
# Técnica: Cobertura de decisiones
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.rafael
class TestPU13StateWithoutIssues:
    """PU-13: estado sin issues → query False → borrado permitido."""

    @pytest.mark.django_db
    def test_pu13_state_without_issues_query_returns_false(self, workspace, create_user):
        """PU-13: Issue.objects.filter(state=state).exists() retorna False."""
        project = Project.objects.create(
            name="PU13 Project", identifier="PU13", workspace=workspace
        )
        state = State.objects.create(
            name="PU13 State", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value, default=False,
        )
        assert Issue.objects.filter(state=state.id).exists() is False

    @pytest.mark.django_db
    def test_pu13_empty_state_is_removed_from_db(self, workspace, create_user):
        """PU-13: tras delete(), el estado ya no existe en DB."""
        project = Project.objects.create(
            name="PU13b Project", identifier="PU13B", workspace=workspace
        )
        state = State.objects.create(
            name="PU13b State", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value, default=False,
        )
        state.delete()
        assert not State.all_state_objects.filter(id=state.id, deleted_at__isnull=True).exists()


# ---------------------------------------------------------------------------
# PU-14 — Estado con issues asociados no puede borrarse
# Técnica: Cobertura de decisiones
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.rafael
class TestPU14StateWithIssues:
    """PU-14: estado con issues → query True → borrado bloqueado."""

    @pytest.mark.django_db
    def test_pu14_state_with_issues_query_returns_true(self, workspace, create_user):
        """PU-14: Issue.objects.filter(state=state).exists() retorna True."""
        project = Project.objects.create(
            name="PU14 Project", identifier="PU14", workspace=workspace
        )
        state = State.objects.create(
            name="PU14 State", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value, default=False,
        )
        Issue.objects.create(
            name="Blocking Issue", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        assert Issue.objects.filter(state=state.id).exists() is True

    @pytest.mark.django_db
    def test_pu14_state_with_issues_remains_in_db(self, workspace, create_user):
        """PU-14: estado con issues no se borra cuando la guardia aplica."""
        project = Project.objects.create(
            name="PU14b Project", identifier="PU14B", workspace=workspace
        )
        state = State.objects.create(
            name="PU14b State", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value, default=False,
        )
        Issue.objects.create(
            name="Blocking Issue", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        issue_exist = Issue.objects.filter(state=state.id).exists()
        if not issue_exist:
            state.delete()
        assert State.all_state_objects.filter(id=state.id, deleted_at__isnull=True).exists()


# ---------------------------------------------------------------------------
# PU-15 — DEFAULT_STATES incluye estado con grupo 'completed'
# PU-16 — DEFAULT_STATES define exactamente 6 estados
# Técnica: Inspección de constante
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.rafael
class TestDefaultStatesConstant:
    """PU-15 / PU-16: estructura y contenido de DEFAULT_STATES."""

    def test_pu15_default_states_has_completed_group(self):
        """PU-15: DEFAULT_STATES contiene al menos un estado con group='completed'."""
        completed = [s for s in DEFAULT_STATES if s.get("group") == "completed"]
        assert len(completed) >= 1

    def test_pu16_default_states_has_exactly_six_entries(self):
        """PU-16: DEFAULT_STATES define exactamente 6 estados."""
        assert len(DEFAULT_STATES) == 6

    def test_pu16_default_states_has_expected_names(self):
        """PU-16 (complementario): DEFAULT_STATES contiene los nombres esperados."""
        expected = {"Backlog", "Todo", "In Progress", "Done", "Cancelled", "Triage"}
        assert {s.get("name") for s in DEFAULT_STATES} == expected


# ---------------------------------------------------------------------------
# PU-17 — LabelSerializer acepta color hex válido / rechaza nombre duplicado
# Técnica: Partición de equivalencia
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.rafael
class TestLabelSerializerColor:
    """PU-17: validación de color y unicidad de nombre en LabelSerializer."""

    @pytest.mark.django_db
    def test_pu17_label_serializer_accepts_valid_hex_color(self, workspace):
        """PU-17: serializer.is_valid() == True con color='#1F3864'."""
        project = Project.objects.create(
            name="PU17 Project", identifier="PU17", workspace=workspace
        )
        serializer = LabelSerializer(
            data={"name": "TestLabel", "color": "#1F3864"},
            context={"project_id": project.id},
        )
        assert serializer.is_valid()

    @pytest.mark.django_db
    def test_pu17_label_serializer_rejects_duplicate_name(self, workspace):
        """PU-17 (complementario): serializer.is_valid() == False con nombre duplicado."""
        project = Project.objects.create(
            name="PU17b Project", identifier="PU17B", workspace=workspace
        )
        Label.objects.create(
            name="ExistingLabel", color="#000000", project=project, workspace=workspace,
        )
        serializer = LabelSerializer(
            data={"name": "ExistingLabel", "color": "#1F3864"},
            context={"project_id": project.id},
        )
        assert not serializer.is_valid()

    @pytest.mark.django_db
    def test_pu17_duplicate_name_error_is_on_name_field(self, workspace):
        """PU-17 (complementario): el error de duplicado apunta al campo 'name'."""
        project = Project.objects.create(
            name="PU17c Project", identifier="PU17C", workspace=workspace
        )
        Label.objects.create(
            name="DupLabel", color="#000000", project=project, workspace=workspace,
        )
        serializer = LabelSerializer(
            data={"name": "DupLabel", "color": "#1F3864"},
            context={"project_id": project.id},
        )
        serializer.is_valid()
        assert "name" in serializer.errors


# ---------------------------------------------------------------------------
# PU-18 — sequence_id autoincremental al crear Issue
# Técnica: Cobertura de sentencias
# Nota: transaction=True requerido para pg_advisory_xact_lock en Issue.save()
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.rafael
class TestIssueSequenceId:
    """PU-18: sequence_id se auto-incrementa por proyecto."""

    @pytest.mark.django_db(transaction=True)
    def test_pu18_second_issue_has_incremented_sequence_id(self, workspace, create_user):
        """PU-18: issue2.sequence_id == issue1.sequence_id + 1."""
        project = Project.objects.create(
            name="PU18 Project", identifier="PU18", workspace=workspace
        )
        state = State.objects.create(
            name="Todo", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value,
        )
        issue1 = Issue.objects.create(
            name="Issue 1", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        issue2 = Issue.objects.create(
            name="Issue 2", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        assert issue2.sequence_id == issue1.sequence_id + 1

    @pytest.mark.django_db(transaction=True)
    def test_pu18_first_issue_in_new_project_has_sequence_id_one(self, workspace, create_user):
        """PU-18 (complementario): primer issue de un proyecto nuevo tiene sequence_id == 1."""
        project = Project.objects.create(
            name="PU18b Project", identifier="PU18B", workspace=workspace
        )
        state = State.objects.create(
            name="Todo", color="#FFFFFF", project=project,
            workspace=workspace, group=StateGroup.UNSTARTED.value,
        )
        issue = Issue.objects.create(
            name="First Issue", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        assert issue.sequence_id == 1
