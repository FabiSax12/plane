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

const createTestStore = async () => {
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

  return { store, rootStoreMock };
};

describe("WorkspaceMemberStore", () => {
  beforeEach(() => {
    updateWorkspaceMemberMock.mockReset();
  });

  it("PU-07a: updateMember optimistically updates role before API resolves", async () => {
    const { store } = await createTestStore();

    const deferredRequest = createDeferred<unknown>();
    updateWorkspaceMemberMock.mockReturnValueOnce(deferredRequest.promise);

    store.updateMember("acme", "user-123", { role: 5 });

    expect(store.workspaceMemberMap.acme?.["user-123"]?.role).toBe(5);

    deferredRequest.resolve({});
  }, 15000);

  it("PU-07b: updateMember calls API with correct payload", async () => {
    const { store } = await createTestStore();

    updateWorkspaceMemberMock.mockResolvedValueOnce({});

    await store.updateMember("acme", "user-123", { role: 5 });

    expect(updateWorkspaceMemberMock).toHaveBeenCalledWith("acme", "workspace-member-123", { role: 5 });
  }, 15000);

  it("PU-07c: updateMember maintains optimistic role after API resolves", async () => {
    const { store } = await createTestStore();

    updateWorkspaceMemberMock.mockResolvedValueOnce({});

    await store.updateMember("acme", "user-123", { role: 5 });

    expect(store.workspaceMemberMap.acme?.["user-123"]?.role).toBe(5);
  }, 15000);

  it("PU-08a: updateMember calls API with correct payload even when it fails", async () => {
    const { store } = await createTestStore();

    const apiError = new Error("update failed");
    updateWorkspaceMemberMock.mockRejectedValueOnce(apiError);

    try {
      await store.updateMember("acme", "user-123", { role: 5 as any });
    } catch {
      // expected to throw
    }

    expect(updateWorkspaceMemberMock).toHaveBeenCalledWith("acme", "workspace-member-123", { role: 5 });
  }, 15000);

  it("PU-08b: updateMember rolls back role when API fails", async () => {
    const { store } = await createTestStore();

    const apiError = new Error("update failed");
    updateWorkspaceMemberMock.mockRejectedValueOnce(apiError);

    try {
      await store.updateMember("acme", "user-123", { role: 5 as any });
    } catch {
      // expected to throw
    }

    expect(store.workspaceMemberMap.acme?.["user-123"]?.role).toBe(15);
  }, 15000);
});
