/**
 * Author: Fabián Vargas
 * Test cases: PU-07, PU-08
 */

import { beforeEach, describe, expect, it, vi } from "vitest";

const { updateWorkspaceMemberMock } = vi.hoisted(() => ({
  updateWorkspaceMemberMock: vi.fn(),
}));

vi.mock("@/services/workspace.service", () => ({
  WorkspaceService: class {
    updateWorkspaceMember = updateWorkspaceMemberMock;
  },
}));

const createDeferred = <T>() => {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, resolve, reject };
};

describe("WorkspaceMemberStore", () => {
  beforeEach(() => {
    updateWorkspaceMemberMock.mockReset();
  });

  it("PU-07: optimistically updates member role in updateMember before API resolves", async () => {
    const { WorkspaceMemberStore } = await import("@/store/member/workspace/workspace-member.store");

    const rootStoreMock = {
      router: {
        workspaceSlug: "acme",
      },
      user: {
        data: {
          id: "current-user",
        },
      },
    } as any;

    const memberRootMock = {
      memberMap: {},
    } as any;

    const store = new WorkspaceMemberStore(memberRootMock, rootStoreMock);
    store.workspaceMemberMap = {
      acme: {
        "user-123": {
          id: "workspace-member-123",
          member: "user-123",
          role: 15,
          is_active: true,
        },
      },
    };

    const deferredRequest = createDeferred<unknown>();
    updateWorkspaceMemberMock.mockReturnValueOnce(deferredRequest.promise);

    let isSettled = false;
    const updatePromise = store.updateMember("acme", "user-123", { role: 5 }).finally(() => {
      isSettled = true;
    });

    expect(store.workspaceMemberMap.acme?.["user-123"]?.role).toBe(5);
    expect(updateWorkspaceMemberMock).toHaveBeenCalledWith("acme", "workspace-member-123", { role: 5 });

    await Promise.resolve();
    expect(isSettled).toBe(false);

    deferredRequest.resolve({});
    await updatePromise;

    expect(store.workspaceMemberMap.acme?.["user-123"]?.role).toBe(5);
  });

  it("PU-08: rolls back member role when updateMember API fails", async () => {
    const { WorkspaceMemberStore } = await import("@/store/member/workspace/workspace-member.store");

    const rootStoreMock = {
      router: {
        workspaceSlug: "acme",
      },
      user: {
        data: {
          id: "current-user",
        },
      },
    } as any;

    const memberRootMock = {
      memberMap: {
        "user-123": {
          id: "user-123",
          display_name: "User 123",
        },
      },
    } as any;

    const store = new WorkspaceMemberStore(memberRootMock, rootStoreMock);
    store.workspaceMemberMap = {
      acme: {
        "user-123": {
          id: "workspace-member-123",
          member: "user-123",
          role: 15,
          original_role: 15,
          is_active: true,
        } as any,
      },
    };

    const apiError = new Error("update failed");
    updateWorkspaceMemberMock.mockRejectedValueOnce(apiError);

    await expect(store.updateMember("acme", "user-123", { role: 5 as any })).rejects.toThrow("update failed");

    expect(updateWorkspaceMemberMock).toHaveBeenCalledWith("acme", "workspace-member-123", { role: 5 });
    expect(store.workspaceMemberMap.acme?.["user-123"]?.role).toBe(15);
    expect((store.workspaceMemberMap.acme?.["user-123"] as any)?.original_role).toBe(15);
  });
});
