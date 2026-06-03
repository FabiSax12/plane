# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Pruebas de integración asignadas a Rafael Odio: PI-13, PI-14, PI-15, PI-16, PI-17, PI-18
#
# Todos los endpoints son de la API externa (/api/v1/) y usan api_key_client.
# URLs confirmadas en apps/api/plane/api/urls/

import pytest
import uuid
from rest_framework import status

from plane.db.models import (
    Project,
    ProjectMember,
    State,
    Issue,
    IssueRelation,
    WorkspaceMember,
)
from plane.db.models.state import StateGroup


# ---------------------------------------------------------------------------
# PI-13 — POST /api/v1/workspaces/{slug}/projects/ retorna 201 con 6 estados
# Técnica: Cobertura de sentencias
# Módulo: API de Proyectos / ProjectListCreateAPIEndpoint (project.py:240-254)
# Plan: verificar 201 + State.objects.filter(project).count() == 6
#       + los grupos backlog, unstarted, started, completed, cancelled representados
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestPI13CreateProjectWithStates:
    """PI-13: crear proyecto vía API v1 genera 6 estados automáticamente."""

    @pytest.mark.django_db
    def test_pi13_create_project_returns_201_and_seeds_six_states(self, api_key_client, workspace, create_user):
        """PI-13: POST retorna 201 y bulk_create genera exactamente 6 estados."""
        url = f"/api/v1/workspaces/{workspace.slug}/projects/"
        response = api_key_client.post(
            url,
            {"name": "QA Tests", "identifier": "QAT", "description": "Integration test project"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        project_id = response.json()["id"]

        # Verificar que se crearon exactamente 6 estados (DEFAULT_STATES via bulk_create)
        state_count = State.all_state_objects.filter(project_id=project_id).count()
        assert state_count == 6, (
            f"Se esperaban 6 estados creados automáticamente, se encontraron {state_count}"
        )

        # Verificar que los grupos esperados están todos representados
        groups = set(
            State.all_state_objects.filter(project_id=project_id).values_list("group", flat=True)
        )
        expected_groups = {"backlog", "unstarted", "started", "completed", "cancelled", "triage"}
        assert expected_groups == groups, (
            f"Grupos esperados: {expected_groups}\nGrupos encontrados: {groups}"
        )


# ---------------------------------------------------------------------------
# PI-14 — GET /api/v1/workspaces/{slug}/projects/{id}/members/ lista miembros
# Técnica: Cobertura de sentencias
# Módulo: API / ProjectMemberListCreateAPIEndpoint (member.py:15-19)
# Plan: crear project + 3 members, GET, verificar 200 y len == 3
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestPI14ListProjectMembers:
    """PI-14: GET de miembros retorna la lista completa con id, role y user info."""

    @pytest.mark.django_db
    def test_pi14_get_members_returns_200_with_three_members(self, api_key_client, workspace, create_user):
        """PI-14: 3 ProjectMembers creados → GET retorna lista de 3."""
        from plane.db.models import User

        project = Project.objects.create(
            name="PI14 Project", identifier="PI14", workspace=workspace
        )

        # Crear 3 miembros vía ORM (como indica el plan: "vía factories")
        member1 = create_user  # el usuario del token ya existe
        member2 = User.objects.create_user(email="pi14m2@plane.so", username="pi14m2")
        member3 = User.objects.create_user(email="pi14m3@plane.so", username="pi14m3")

        WorkspaceMember.objects.get_or_create(workspace=workspace, member=member2, defaults={"role": 15})
        WorkspaceMember.objects.get_or_create(workspace=workspace, member=member3, defaults={"role": 15})

        ProjectMember.objects.create(project=project, member=member1, role=20, is_active=True)
        ProjectMember.objects.create(project=project, member=member2, role=15, is_active=True)
        ProjectMember.objects.create(project=project, member=member3, role=15, is_active=True)

        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/members/"
        response = api_key_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 3, f"Se esperaban 3 miembros, se recibieron {len(data)}"

        # El endpoint retorna UserLiteSerializer: id, email, display_name.
        # Nota: el plan esperaba 'role' en la respuesta, pero la API v1 usa
        # UserLiteSerializer (member.py:140) que no incluye ese campo.
        for member in data:
            assert "id" in member
            assert "email" in member
            assert "display_name" in member
            assert "role" not in member, (
                "La API v1 no expone 'role' en este endpoint — "
                "si esto cambia, el plan debe actualizarse."
            )


# ---------------------------------------------------------------------------
# PI-15 — POST /api/v1/workspaces/{slug}/projects/{id}/archive/ archiva proyecto
# Técnica: Cobertura de decisiones
# Módulo: API / ProjectArchiveUnarchiveAPIEndpoint (project.py:25-28)
# Plan: POST → 200, archived_at IS NOT NULL en DB, no aparece en listado
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestPI15ArchiveProject:
    """PI-15: archivar proyecto setea archived_at y lo excluye del listado."""

    @pytest.mark.django_db
    def test_pi15_archive_project_sets_archived_at(self, api_key_client, workspace, create_user):
        """PI-15: POST archive → 200 + archived_at IS NOT NULL en DB."""
        project = Project.objects.create(
            name="PI15 Project", identifier="PI15", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)

        # Verificar precondición: proyecto activo
        assert project.archived_at is None

        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/archive/"
        response = api_key_client.post(url)

        # El endpoint retorna 204 (no 200) — confirmado en project.py:533
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verificar que archived_at fue poblado en DB
        project.refresh_from_db()
        assert project.archived_at is not None, "El proyecto debería tener archived_at poblado tras archivarlo"

    @pytest.mark.django_db
    def test_pi15_archived_project_still_visible_in_v1_list(self, api_key_client, workspace, create_user):
        """PI-15: la API v1 NO filtra proyectos archivados del listado — comportamiento documentado.

        El plan especificaba que el proyecto archivado no aparecería en el listado.
        La API v1 (a diferencia de la app API) no aplica ese filtro: el proyecto
        archivado sigue devuelto por GET /projects/. Este test verifica ese
        comportamiento real para que una futura restricción quede detectada.
        """
        project = Project.objects.create(
            name="PI15b Project", identifier="PI15B", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)

        # Archivar el proyecto
        archive_url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/archive/"
        archive_response = api_key_client.post(archive_url)
        assert archive_response.status_code == status.HTTP_204_NO_CONTENT

        # Verificar que archived_at fue poblado
        project.refresh_from_db()
        assert project.archived_at is not None

        # Verificar comportamiento real del listado: API v1 devuelve el proyecto archivado
        list_url = f"/api/v1/workspaces/{workspace.slug}/projects/"
        list_response = api_key_client.get(list_url)
        assert list_response.status_code == status.HTTP_200_OK
        project_ids = [p["id"] for p in list_response.json()]
        assert str(project.id) in project_ids, (
            "La API v1 devuelve proyectos archivados en el listado estándar. "
            "Si este assert falla, el endpoint fue actualizado para filtrarlos."
        )


# ---------------------------------------------------------------------------
# PI-16 — POST work-items/{A}/relations/ crea relación bidireccional
# Técnica: Cobertura de sentencias
# Módulo: API / IssueRelationListCreateAPIEndpoint (work_item.py:149-153)
# Plan: POST {related_to_id: B, relation_type: 'blocked_by'} →
#       201, A tiene 'blocked_by' B, B tiene 'blocking' A
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestPI16IssueRelation:
    """PI-16: crear relación blocked_by genera relación inversa blocking."""

    @pytest.mark.django_db
    def test_pi16_blocked_by_relation_creates_inverse_blocking(self, api_key_client, workspace, create_user):
        """PI-16: POST relation 'blocked_by' → 201, A bloqueado por B, B bloquea A."""
        project = Project.objects.create(
            name="PI16 Project", identifier="PI16", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)

        state = State.objects.create(
            name="Todo", color="#FFFFFF",
            project=project, workspace=workspace,
            group=StateGroup.UNSTARTED.value,
        )

        issue_a = Issue.objects.create(
            name="Issue A", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )
        issue_b = Issue.objects.create(
            name="Issue B", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )

        # Formato correcto: relation_type + issues (lista de UUIDs)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/{issue_a.id}/relations/"
        response = api_key_client.post(
            url,
            {"relation_type": "blocked_by", "issues": [str(issue_b.id)]},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        # La relación se almacena como un único registro (issue_a blocked_by issue_b)
        assert IssueRelation.objects.filter(
            issue=issue_a, related_issue=issue_b, relation_type="blocked_by"
        ).exists(), "Debe existir la relación: issue_a blocked_by issue_b"

        # Perspectiva de A: issue_b debe aparecer en blocked_by de issue_a
        get_a_url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/{issue_a.id}/relations/"
        get_a_response = api_key_client.get(get_a_url)
        assert get_a_response.status_code == status.HTTP_200_OK
        data_a = get_a_response.json()
        blocked_by_ids = [r["issue_id"] for r in data_a.get("blocked_by", [])]
        assert str(issue_b.id) in blocked_by_ids, "issue_b debe aparecer en blocked_by de issue_a"

        # Perspectiva de B (paso 5 del plan): issue_a debe aparecer en blocking de issue_b.
        # La vista deriva ambas perspectivas del mismo registro almacenado (issue.py:2362-2372).
        get_b_url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/{issue_b.id}/relations/"
        get_b_response = api_key_client.get(get_b_url)
        assert get_b_response.status_code == status.HTTP_200_OK
        data_b = get_b_response.json()
        blocking_ids = [r["issue_id"] for r in data_b.get("blocking", [])]
        assert str(issue_a.id) in blocking_ids, "issue_a debe aparecer en blocking de issue_b"


# ---------------------------------------------------------------------------
# PI-17 — DELETE state en uso retorna 400 con mensaje específico
# Técnica: Cobertura de decisiones (rama negativa)
# Módulo: API de Estados / StateDetailAPIEndpoint (state.py:225-249)
# Plan: DELETE → 400 + mensaje exacto 'The state is not empty, only empty states can be deleted'
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestPI17DeleteStateInUse:
    """PI-17: DELETE state con issues → 400 con mensaje específico del plan."""

    @pytest.mark.django_db
    def test_pi17_delete_state_with_issue_returns_400_with_exact_message(self, api_key_client, workspace, create_user):
        """PI-17: estado con issue asociado retorna 400 y el mensaje exacto de Plane."""
        project = Project.objects.create(
            name="PI17 Project", identifier="PI17", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)

        state = State.objects.create(
            name="PI17 State", color="#FFFFFF",
            project=project, workspace=workspace,
            group=StateGroup.UNSTARTED.value, default=False,
        )
        Issue.objects.create(
            name="Blocking Issue", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )

        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/states/{state.id}/"
        response = api_key_client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Verificar mensaje exacto según el plan y el código (state.py:244)
        data = response.json()
        assert data.get("error") == "The state is not empty, only empty states can be deleted"

        # El estado sigue existiendo en DB
        assert State.objects.filter(id=state.id).exists()


# ---------------------------------------------------------------------------
# PI-18 — POST work-items/ con sequence_id auto-generado
# Técnica: Cobertura de sentencias
# Módulo: API / IssueListCreateAPIEndpoint + Issue.save() (work_item.py:99-103)
# Plan: crear primer issue, POST segundo → 201, response['sequence_id'] == 2
# ---------------------------------------------------------------------------

@pytest.mark.contract
class TestPI18WorkItemSequenceId:
    """PI-18: crear segundo work item vía API retorna sequence_id == 2."""

    @pytest.mark.django_db(transaction=True)
    def test_pi18_second_work_item_has_sequence_id_two(self, api_key_client, workspace, create_user):
        """PI-18: POST crea segundo issue → 201 + sequence_id == 2 en la respuesta."""
        project = Project.objects.create(
            name="PI18 Project", identifier="PI18", workspace=workspace
        )
        ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)

        state = State.objects.create(
            name="Todo", color="#FFFFFF",
            project=project, workspace=workspace,
            group=StateGroup.UNSTARTED.value,
        )

        # Crear primer issue (sequence_id = 1) vía ORM como fixture
        Issue.objects.create(
            name="First Issue", project=project, workspace=workspace,
            state=state, created_by=create_user, updated_by=create_user,
        )

        # Crear segundo issue vía HTTP (es el que prueba el plan)
        url = f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}/work-items/"
        response = api_key_client.post(
            url,
            {"name": "Second Issue", "description": "Created via API"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["sequence_id"] == 2, (
            f"Se esperaba sequence_id == 2 para el segundo issue, se obtuvo {data.get('sequence_id')}"
        )
