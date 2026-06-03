import { test, expect } from "@playwright/test";

test.describe("PS-04: Registro de usuario", () => {
  test("el usuario se registra con datos válidos", async ({ page }) => {
    const timestamp = Date.now();
    const email = `e2e-test-${timestamp}@example.com`;

    await page.goto("/sign-up");
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
    await page.getByPlaceholder("name@company.com").fill(email);
    await page.getByRole("button", { name: "Continue" }).click();

    await expect(page.getByPlaceholder("Enter password")).toBeVisible({ timeout: 10000 });
    await page.getByPlaceholder("Enter password").fill("Test1234!");
    await page.getByPlaceholder("Confirm password").fill("Test1234!");
    await page.getByRole("button", { name: "Create account" }).click();

    // Verify we left the sign-up page (redirect to confirm-email, onboarding, or workspace)
    await expect(page).not.toHaveURL(/\/sign-up/, { timeout: 20000 });
  });
});
