import { test, expect } from "@playwright/test";

test.describe("PS-02: Inicio de sesión inválido", () => {
  test("el usuario ingresa credenciales incorrectas y ve un mensaje de error", async ({ page }) => {
    const email = process.env.E2E_EMAIL!;

    // Use email that exists but wrong password
    await page.goto("/sign-in");
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
    await page.getByPlaceholder("name@company.com").fill(email);
    await page.getByRole("button", { name: "Continue" }).click();

    await expect(page.getByPlaceholder("Enter password")).toBeVisible({ timeout: 10000 });
    await page.getByPlaceholder("Enter password").fill("wrongpassword123");
    await page.getByRole("button", { name: /Continue|Go to workspace/ }).click();

    // Wait for error banner (role="alert")
    await expect(page.locator('[role="alert"]')).toBeVisible({ timeout: 10000 });
  });
});
