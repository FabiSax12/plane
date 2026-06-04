/**
 * Author: Fabián Vargas
 * Test cases: PU-09
 */

import { beforeEach, describe, expect, it, vi } from "vitest";

const { updateWorkspaceMock } = vi.hoisted(() => ({
  updateWorkspaceMock: vi.fn(),
}));

vi.mock("@/services/workspace.service", () => ({
  WorkspaceService: class {
    updateWorkspace = updateWorkspaceMock;
  },
}));

describe("WorkspaceRootStore", () => {
  beforeEach(() => {
    updateWorkspaceMock.mockReset();
  });

  it("PU-09: updateWorkspace updates workspace name in store and calls API with payload", async () => {
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

    updateWorkspaceMock.mockResolvedValueOnce({
      id: "workspace-1",
    });

    await store.updateWorkspace("acme", { name: "Renamed Workspace" } as any);

    expect(updateWorkspaceMock).toHaveBeenCalledWith("acme", { name: "Renamed Workspace" });
    expect(store.workspaces["workspace-1"]?.name).toBe("Renamed Workspace");
  }, 15000);
});
