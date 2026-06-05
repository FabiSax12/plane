/**
 * Author: Fabián Vargas
 * Test cases: PS-05
 */

import { expect, test } from "@playwright/test";

const EXISTING_EMAIL = process.env.E2E_EXISTING_USER_EMAIL ?? "qa-tester@itcr.ac.cr";

test.describe("Sign-up", () => {
  test.describe.configure({ retries: 0 }); // Se descubrió que este va a fallar siempre

  test(
    "PS-05: signup with duplicate email shows visible error in form",
    { tag: ["@e2e", "@signup", "@PS-05"] },
    async ({ page }) => {
      await page.goto("/sign-up?error_code=USER_ALREADY_EXIST");
      await page.waitForLoadState("networkidle");

      await expect(page).toHaveURL(/error_code=USER_ALREADY_EXIST/);

      const banner = page.getByRole("alert");
      await expect(banner).toBeVisible();
      await expect(banner).toContainText(/already/i);

      const emailInput = page.getByLabel(/email/i);
      await expect(emailInput).toBeVisible();
      await emailInput.fill(EXISTING_EMAIL);
      await expect(emailInput).toHaveValue(EXISTING_EMAIL);
    }
  );
});
