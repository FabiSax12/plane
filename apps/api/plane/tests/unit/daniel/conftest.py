import pytest
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
    """Project inside the test workspace"""
    project = ProjectFactory(workspace=workspace, created_by=user, updated_by=user)
    ProjectMemberFactory(project=project, member=user, role=20)
    return project


@pytest.fixture
def default_state(db, project):
    """Default backlog state for the test project"""
    return StateFactory(project=project, group="backlog", default=True)
