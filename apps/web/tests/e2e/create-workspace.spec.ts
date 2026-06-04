/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

/**
 * Author: Fabián Vargas
 * Test cases: PS-06, PS-07
 */

import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const USER_EMAIL = process.env.E2E_USER_EMAIL;
const USER_PASSWORD = process.env.E2E_USER_PASSWORD;
const WORKSPACE_SLUG = process.env.E2E_WORKSPACE_SLUG;
const EXISTING_WORKSPACE_SLUG = process.env.E2E_EXISTING_WORKSPACE_SLUG ?? "qa-proyecto-1";

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

test.describe("Create workspace", () => {
  test.beforeEach(async (_, testInfo) => {
    if (!hasCredentials()) {
      testInfo.skip(true, "E2E_USER_EMAIL / E2E_USER_PASSWORD / E2E_WORKSPACE_SLUG not set");
    }
  });

  test(
    "PS-06: create new workspace appears in the switcher",
    { tag: ["@e2e", "@workspace", "@PS-06"] },
    async ({ page }) => {
      await signIn(page);

      const newName = `E2E Workspace ${Date.now()}`;
      const newSlug = `e2e-ws-${Date.now()}`;

      await page.goto("/create-workspace");
      await page.waitForLoadState("networkidle");

      await page.getByLabel(/workspace name/i).fill(newName);
      await page.getByLabel(/workspace url/i).fill(newSlug);

      await page
        .getByText(/organization size/i)
        .first()
        .click();
      await page.getByText("1-50", { exact: true }).first().click();

      await page.getByRole("button", { name: /create workspace/i }).click();

      await page.waitForURL(new RegExp(`/${newSlug}(/|$|\\?)`), { timeout: 20_000 });
      await expect(page).toHaveURL(new RegExp(`/${newSlug}(/|$|\\?)`));

      const switcherButton = page
        .getByRole("button")
        .filter({ has: page.locator("h4", { hasText: newName }) })
        .first();
      await switcherButton.click();

      const switcherPanel = page.getByRole("menu");
      await expect(switcherPanel).toBeVisible();
      await expect(switcherPanel).toContainText(newName);
    }
  );

  test(
    "PS-07: create workspace with duplicate slug shows visible error",
    { tag: ["@e2e", "@workspace", "@PS-07"] },
    async ({ page }) => {
      await signIn(page);

      await page.goto("/create-workspace");
      await page.waitForLoadState("networkidle");

      await page.getByLabel(/workspace name/i).fill("qa proyecto 1");
      await page.getByLabel(/workspace url/i).fill(EXISTING_WORKSPACE_SLUG);

      await page
        .getByText(/organization size/i)
        .first()
        .click();
      await page.getByText("1-50", { exact: true }).first().click();

      await page.getByRole("button", { name: /create workspace/i }).click();

      await expect(page.getByText(/workspace.*slug.*exists|slug.*already.*taken/i)).toBeVisible({ timeout: 10_000 });
    }
  );
});
