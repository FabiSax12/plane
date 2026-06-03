import { test, expect } from "@playwright/test";

test.describe("PS-01: Inicio de sesión válido", () => {
  test("el usuario inicia sesión con credenciales correctas y llega al workspace", async ({ page }) => {
    const email = process.env.E2E_EMAIL!;
    const password = process.env.E2E_PASSWORD!;

    await page.goto("/sign-in");
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
    await page.getByPlaceholder("name@company.com").fill(email);
    await page.getByRole("button", { name: "Continue" }).click();

    await expect(page.getByPlaceholder("Enter password")).toBeVisible({ timeout: 10000 });
    await page.getByPlaceholder("Enter password").fill(password);
    await page.getByRole("button", { name: /Continue|Go to workspace/ }).click();

    await expect(page).toHaveURL(/\/[a-z0-9_-]+\//, { timeout: 20000 });
  });
});
