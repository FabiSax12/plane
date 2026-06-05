# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
 * Author: Fabián Vargas
 * Shared fixtures for fabian-tests.
 *
 * These fixtures encapsulate the *precondition* validation that previously
 * lived inline in each test body. Tests opt-in by listing the fixture name
 * in their signature (they run before the test as part of pytest's
 * dependency resolution).
"""

import pytest

from plane.db.models import Workspace, WorkspaceMember, WorkspaceMemberInvite


DUPLICATE_SLUG = "equipo-qa"
NEW_WORKSPACE_SLUG = "equipo-plane-qa"


@pytest.fixture
def precondition_slug_not_in_use(db):
    """[PI/07] precondition: the new-workspace slug must not exist before the call."""
    assert not Workspace.objects.filter(slug=NEW_WORKSPACE_SLUG).exists()


@pytest.fixture
def precondition_workspace_with_duplicate_slug_exists(db, create_user):
    """[PI/08] precondition: a workspace with the target slug must already exist."""
    Workspace.objects.create(
        name="Equipo QA",
        slug=DUPLICATE_SLUG,
        owner=create_user,
    )
    assert Workspace.objects.filter(slug=DUPLICATE_SLUG).exists()


@pytest.fixture
def precondition_caller_is_workspace_admin(workspace, create_user):
    """[PI/09] precondition: the requesting user is registered as a WorkspaceMember Admin (20)."""
    assert WorkspaceMember.objects.filter(
        workspace=workspace, member=create_user, role=20
    ).exists()


@pytest.fixture
def precondition_demoted_to_member_and_no_invitations(workspace, create_user):
    """[PI/10] precondition: caller is demoted to Member (15) and no prior invitations exist."""
    updated_rows = WorkspaceMember.objects.filter(
        workspace=workspace, member=create_user
    ).update(role=15)
    assert updated_rows == 1
    assert WorkspaceMember.objects.filter(
        workspace=workspace, member=create_user, role=15
    ).exists()
    assert WorkspaceMemberInvite.objects.filter(workspace=workspace).count() == 0


@pytest.fixture
def precondition_only_active_admin(workspace, create_user):
    """[PI/12] precondition: caller is the only active Admin (role=20) in the workspace."""
    admin_member = WorkspaceMember.objects.get(workspace=workspace, member=create_user)
    assert admin_member.role == 20
    assert admin_member.is_active is True
    assert (
        WorkspaceMember.objects.filter(
            workspace=workspace, role=20, is_active=True
        ).count()
        == 1
    )
    return admin_member
