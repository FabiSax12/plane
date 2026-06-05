/**
 * Author: Fabián Vargas
 * Test cases: PS-06, PS-07
 */

import { expect, test } from "@playwright/test";
import { hasCredentials, signIn } from "../helpers/auth";

const EXISTING_WORKSPACE_SLUG = process.env.E2E_EXISTING_WORKSPACE_SLUG ?? "qa-proyecto-1";

test.describe("Create workspace", () => {
  test.beforeEach(async ({ page: _page }, testInfo) => {
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

      await page.getByRole("textbox", { name: "Name your workspace*" }).fill(newName);
      await page.getByRole("textbox", { name: "Set your workspace's URL*" }).fill(newSlug);

      await page.getByRole("button", { name: "Select a range" }).first().click();
      await page.getByText("11-50", { exact: true }).first().click();

      await page.getByRole("button", { name: "11-50" }).first().click();

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

      await page.getByRole("textbox", { name: "Name your workspace*" }).fill("qa proyecto 1");
      await page.getByRole("textbox", { name: "Set your workspace's URL*" }).fill(EXISTING_WORKSPACE_SLUG);

      await page.getByRole("button", { name: "Select a range" }).first().click();
      await page.getByText("11-50", { exact: true }).first().click();

      await page.getByRole("button", { name: "11-50" }).first().click();

      await page.getByRole("button", { name: /create workspace/i }).click();
      await page.waitForLoadState("networkidle");

      await expect(page.getByText(/workspace.*url.*already.*taken/i)).toBeVisible({ timeout: 10_000 });
    }
  );
});
