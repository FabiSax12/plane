import { test, expect } from "@playwright/test";

test.describe("PS-03: Cerrar sesión", () => {
  test("el usuario inicia sesión y cierra sesión correctamente", async ({ page }) => {
    const email = process.env.E2E_EMAIL!;
    const password = process.env.E2E_PASSWORD!;

    // Sign in first
    await page.goto("/sign-in");
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
    await page.getByPlaceholder("name@company.com").fill(email);
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByPlaceholder("Enter password")).toBeVisible({ timeout: 10000 });
    await page.getByPlaceholder("Enter password").fill(password);
    await page.getByRole("button", { name: /Continue|Go to workspace/ }).click();
    await expect(page).toHaveURL(/\/[a-z0-9_-]+\//, { timeout: 20000 });

    // Open user menu by clicking the avatar (shows initial letter, e.g. "G")
    await page.locator("button:has-text('G')").first().click();
    await page.waitForTimeout(500);

    // Click "Sign out" in the menu
    await page.getByRole("button", { name: "Sign out" }).first().click();

    // Verify redirect to sign-in page (root route)
    await expect(page).toHaveURL(/\/$/, { timeout: 15000 });
  });
});
