import { test, expect } from "@playwright/test";

test.describe("PS-04: Registro de usuario", () => {
  test("el usuario se registra con datos válidos", async ({ page }) => {
    const timestamp = Date.now();
    const email = `qa-signup-${timestamp}@itcr.ac.cr`;
    const password = "TestPass2026!";

    await page.goto("/sign-up");
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
    await page.getByPlaceholder("name@company.com").fill(email);
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByPlaceholder("Enter password")).toBeVisible({ timeout: 10000 });
    await page.getByPlaceholder("Enter password").fill(password);
    await page.getByPlaceholder("Confirm password").fill(password);
    await page.getByRole("button", { name: "Create account" }).click();

    await expect(page).toHaveURL(/\/[a-z0-9_-]+\/|\/onboard/, { timeout: 20000 });
    await expect(page).not.toHaveURL(/error_code=/, { timeout: 10000 });

    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((c) => c.name === "session-id");
    expect(sessionCookie).toBeDefined();

    const nameField = page.getByPlaceholder("Enter your full name");
    if (await nameField.isVisible({ timeout: 5000 }).catch(() => false)) {
      await nameField.fill("QA Tester");
      await page.getByRole("button", { name: "Continue" }).click();
    }
  });
});
