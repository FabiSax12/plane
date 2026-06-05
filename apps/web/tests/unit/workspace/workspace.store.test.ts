/**
 * Author: Fabián Vargas
 * Test cases: PU-09
 */

import { beforeEach, describe, expect, it, vi } from "vitest";

const { updateWorkspaceMock } = vi.hoisted(() => ({
  updateWorkspaceMock: vi.fn(),
}));

vi.mock("@plane/services", () => ({
  APITokenService: vi.fn(),
}));

vi.mock("@/services/workspace.service", () => ({
  WorkspaceService: class {
    updateWorkspace = updateWorkspaceMock;
  },
}));

const createTestStore = async () => {
  const { BaseWorkspaceRootStore } = await import("@/store/workspace");

  class TestWorkspaceStore extends BaseWorkspaceRootStore {
    mutateWorkspaceMembersActivity = async (_workspaceSlug: string) => {
      // no-op for tests
    };
  }

  const rootStoreMock = {
    router: {
      workspaceSlug: "acme",
    },
    user: {},
  } as any;

  const store = new TestWorkspaceStore(rootStoreMock);
  store.workspaces = {
    "workspace-1": {
      id: "workspace-1",
      slug: "acme",
      name: "Old Workspace",
    } as any,
  };

  return store;
};

describe("WorkspaceRootStore", () => {
  beforeEach(() => {
    updateWorkspaceMock.mockReset();
  });

  it("PU-09a: updateWorkspace calls API with correct payload", async () => {
    const store = await createTestStore();

    updateWorkspaceMock.mockResolvedValueOnce({
      id: "workspace-1",
    });

    await store.updateWorkspace("acme", { name: "Renamed Workspace" } as any);

    expect(updateWorkspaceMock).toHaveBeenCalledWith("acme", { name: "Renamed Workspace" });
  }, 15000);

  it("PU-09b: updateWorkspace updates workspace name in store", async () => {
    const store = await createTestStore();

    updateWorkspaceMock.mockResolvedValueOnce({
      id: "workspace-1",
    });

    await store.updateWorkspace("acme", { name: "Renamed Workspace" } as any);

    expect(store.workspaces["workspace-1"]?.name).toBe("Renamed Workspace");
  }, 15000);
});
