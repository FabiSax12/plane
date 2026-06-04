/**
 * Author: Fabián Vargas
 * Test cases: PU-11
 */

import { describe, expect, it, vi } from "vitest";

vi.mock("@plane/utils", () => ({
  orderProjects: vi.fn((projects) => projects),
  shouldFilterProject: vi.fn(() => true),
}));

vi.mock("@/services/project", () => ({
  ProjectService: vi.fn(),
  ProjectStateService: vi.fn(),
  ProjectArchiveService: vi.fn(),
}));

vi.mock("@/services/issue", () => ({
  IssueLabelService: vi.fn(),
  IssueService: vi.fn(),
}));

const createRootStoreMock = () =>
  ({
    workspaceRoot: {
      currentWorkspace: null,
    },
    projectRoot: {
      projectFilter: {
        currentWorkspaceDisplayFilters: null,
        currentWorkspaceFilters: null,
        searchQuery: "",
      },
    },
    router: {},
    favorite: {
      entityMap: {},
    },
    user: {
      permission: {
        workspaceProjectsPermissions: {
          acme: {},
        },
        projectUserInfo: {},
      },
    },
  }) as any;

describe("ProjectStore", () => {
  it("PU-11: processProjectAfterCreation adds project and workspace permission", async () => {
    const { ProjectStore } = await import("@/store/project/project.store");

    const rootStoreMock = createRootStoreMock();

    const store = new ProjectStore(rootStoreMock);

    const createdProject = {
      id: "project-2",
      workspace: "workspace-1",
      name: "New Project",
      member_role: 20,
    } as any;

    store.processProjectAfterCreation("acme", createdProject);

    expect(store.projectMap["project-2"]).toEqual(createdProject);
    expect(rootStoreMock.user.permission.workspaceProjectsPermissions.acme["project-2"]).toBe(20);
  });
});
