import pytest
from rest_framework.test import APIClient
from plane.tests.factories import (
    UserFactory,
    WorkspaceFactory,
    WorkspaceMemberFactory,
    ProjectFactory,
    ProjectMemberFactory,
    StateFactory,
)


@pytest.fixture
def user(db):
    """Standard test user"""
    return UserFactory()


@pytest.fixture
def workspace(db, user):
    """Workspace owned by the test user"""
    ws = WorkspaceFactory(owner=user)
    WorkspaceMemberFactory(workspace=ws, member=user, role=20)
    return ws


@pytest.fixture
def project(db, workspace, user):
    """Project with cycles and modules enabled"""
    p = ProjectFactory(
        workspace=workspace,
        created_by=user,
        updated_by=user,
        cycle_view=True,
        module_view=True,
    )
    ProjectMemberFactory(project=p, member=user, role=20)
    return p


@pytest.fixture
def default_state(db, project):
    """Default backlog state for the test project"""
    return StateFactory(project=project, group="backlog", default=True)


@pytest.fixture
def auth_client(db, user):
    """Authenticated API client via force_authenticate"""
    client = APIClient()
    client.force_authenticate(user=user)
    return client
