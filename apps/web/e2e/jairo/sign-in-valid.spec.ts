import { test, expect } from "@playwright/test";

test.describe("PS-01: Inicio de sesión válido", () => {
  test("el usuario inicia sesión con credenciales correctas y llega al workspace", async ({ page }) => {
    await page.goto("/sign-in");
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
    await page.getByPlaceholder("name@company.com").fill("qa-tester@itcr.ac.cr");
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByPlaceholder("Enter password")).toBeVisible({ timeout: 10000 });
    await page.getByPlaceholder("Enter password").fill("TestPass123!");
    await page.getByRole("button", { name: /Continue|Go to workspace/ }).click();
    await expect(page).toHaveURL(/\/[a-z0-9_-]+\//, { timeout: 20000 });
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((c) => c.name === "session-id");
    expect(sessionCookie).toBeDefined();
  });
});
