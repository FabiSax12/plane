/**
 * Author: Fabián Vargas
 * Test cases: PS-08
 */

import { expect, test } from "@playwright/test";
import { hasCredentials, signIn, WORKSPACE_SLUG } from "../helpers/auth";

test.describe("Profile", () => {
  test.beforeEach(async ({ page: _page }, testInfo) => {
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

      const newDisplayName = `Test User ${Date.now()}`.slice(0, 20);

      await page.goto(`/${slug}/settings/account`);
      // if (!page.url().includes("/settings/profile/")) {
      //   await page.waitForURL(/\/settings\/profile\//, { timeout: 15_000 });
      // }

      const displayNameInput = page.getByRole("textbox", { name: "Enter your display name" });
      const saveButton = page.getByRole("button", { name: /save changes/i });

      await expect(displayNameInput).toBeVisible();
      await expect(saveButton).toBeEnabled();

      await displayNameInput.fill(newDisplayName);
      await saveButton.click();

      await expect(displayNameInput).toHaveValue(newDisplayName);
      await expect(saveButton).toBeEnabled();

      await page.reload();
      await expect(page.getByText(newDisplayName)).toBeVisible();
    }
  );
});
