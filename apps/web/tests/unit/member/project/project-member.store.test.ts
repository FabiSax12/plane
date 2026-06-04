/**
 * Author: Fabián Vargas
 * Test cases: PU-12
 */

import { beforeEach, describe, expect, it, vi } from "vitest";

const { bulkAddMembersToProjectMock } = vi.hoisted(() => ({
  bulkAddMembersToProjectMock: vi.fn(),
}));

vi.mock("@/services/project", () => ({
  ProjectMemberService: class {
    bulkAddMembersToProject = bulkAddMembersToProjectMock;
  },
  ProjectService: vi.fn(),
}));

describe("ProjectMemberStore", () => {
  beforeEach(() => {
    bulkAddMembersToProjectMock.mockReset();
  });

  it("PU-12: bulkAddMembersToProject avoids duplicates in member maps", async () => {
    const { BaseProjectMemberStore } = await import("@/store/member/project/base-project-member.store");

    class TestProjectMemberStore extends BaseProjectMemberStore {
      getUserProjectRole = (userId: string, projectId: string) =>
        this.getRoleFromProjectMembership(userId, projectId) as any;

      getProjectMemberRoleForUpdate = (_projectId: string, _userId: string, role: any) => role;

      processMemberRemoval = (projectId: string, userId: string) => this.handleMemberRemoval(projectId, userId);
    }

    const rootStoreMock = {
      router: {
        projectId: "project-1",
      },
      user: {
        data: {
          id: "current-user",
        },
      },
      projectRoot: {
        project: {
          projectMap: {
            "project-1": {
              id: "project-1",
              members: ["user-existing"],
            },
          },
        },
      },
    } as any;

    const memberRootMock = {
      memberMap: {
        "user-existing": {
          id: "user-existing",
          display_name: "Existing User",
        },
        "user-new": {
          id: "user-new",
          display_name: "New User",
        },
      },
    } as any;

    const store = new TestProjectMemberStore(memberRootMock, rootStoreMock);
    store.projectMemberMap = {
      "project-1": {
        "user-existing": {
          id: "membership-existing",
          member: "user-existing",
          role: 20,
          original_role: 20,
        } as any,
      },
    };

    bulkAddMembersToProjectMock.mockResolvedValueOnce([
      {
        id: "membership-existing-2",
        member: "user-existing",
        role: 20,
      },
      {
        id: "membership-new",
        member: "user-new",
        role: 15,
      },
    ]);

    await store.bulkAddMembersToProject("acme", "project-1", {
      members: [{ member_id: "user-existing" }, { member_id: "user-new" }],
    } as any);

    expect(bulkAddMembersToProjectMock).toHaveBeenCalledWith("acme", "project-1", {
      members: [{ member_id: "user-existing" }, { member_id: "user-new" }],
    });

    expect(Object.keys(store.projectMemberMap["project-1"]).toSorted()).toEqual(["user-existing", "user-new"]);
    expect(rootStoreMock.projectRoot.project.projectMap["project-1"].members).toEqual(["user-existing", "user-new"]);
  }, 15000);
});
