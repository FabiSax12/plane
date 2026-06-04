/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

/**
 * Author: Fabián Vargas
 * Test cases: PS-08
 */

import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const USER_EMAIL = process.env.E2E_USER_EMAIL;
const USER_PASSWORD = process.env.E2E_USER_PASSWORD;
const WORKSPACE_SLUG = process.env.E2E_WORKSPACE_SLUG;

function hasCredentials(): boolean {
  return Boolean(USER_EMAIL && USER_PASSWORD && WORKSPACE_SLUG);
}

async function signIn(page: Page): Promise<void> {
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  const pathname = new URL(page.url()).pathname;
  if (pathname !== "/" && !pathname.startsWith("/sign-in")) return;

  await page.getByLabel(/email/i).first().waitFor({ state: "visible", timeout: 10_000 });
  await page.getByLabel(/email/i).first().fill(USER_EMAIL!);
  await page
    .getByRole("button", { name: /continue/i })
    .first()
    .click();

  await page.getByLabel(/password/i).waitFor({ state: "visible", timeout: 5_000 });
  await page.getByLabel(/password/i).fill(USER_PASSWORD!);
  await page
    .getByRole("button", { name: /sign in|continue|go to workspace/i })
    .first()
    .click();

  await page.waitForURL(/\/[a-z0-9-]+/i, { timeout: 15_000 });
}

test.describe("Profile", () => {
  test.beforeEach(async (_, testInfo) => {
    if (!hasCredentials()) {
      testInfo.skip(true, "E2E_USER_EMAIL / E2E_USER_PASSWORD / E2E_WORKSPACE_SLUG not set");
    }
  });

  test(
    "PS-08: update profile display name reflects immediately in UI",
    { tag: ["@e2e", "@profile", "@PS-08"] },
    async ({ page }) => {
      const slug = WORKSPACE_SLUG!;
      await signIn(page);

      const newDisplayName = `Test User ${Date.now()}`;

      await page.goto(`/${slug}/settings/account`);
      if (!page.url().includes("/settings/profile/")) {
        await page.waitForURL(/\/settings\/profile\//, { timeout: 10_000 });
      }

      const displayNameInput = page.getByLabel(/display name/i);
      const saveButton = page.getByRole("button", { name: /save changes/i });

      await expect(displayNameInput).toBeVisible();
      await expect(saveButton).toBeEnabled();

      await displayNameInput.fill(newDisplayName);
      await saveButton.click();

      await expect(displayNameInput).toHaveValue(newDisplayName);
      await expect(saveButton).toBeEnabled();

      await page.reload();
      await expect(page.getByLabel(/display name/i)).toHaveValue(newDisplayName);
    }
  );
});
