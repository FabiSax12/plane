import { test, expect } from "@playwright/test";

test.describe("PS-03: Cerrar sesión", () => {
  test("el usuario inicia sesión y cierra sesión correctamente", async ({ page }) => {
    await page.goto("/sign-in");
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
    await page.getByPlaceholder("name@company.com").fill("qa-tester@itcr.ac.cr");
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByPlaceholder("Enter password")).toBeVisible({ timeout: 10000 });
    await page.getByPlaceholder("Enter password").fill("TestPass123!");
    await page.getByRole("button", { name: /Continue|Go to workspace/ }).click();
    await expect(page).toHaveURL(/\/[a-z0-9_-]+\//, { timeout: 20000 });

    const workspaceUrl = page.url();

    await page.locator("button").filter({ hasText: /^Q$/ }).last().click();
    await page.waitForTimeout(500);
    await page.getByRole("menuitem", { name: "Sign out" }).first().click();

    await expect(page.getByPlaceholder("name@company.com")).toBeVisible({ timeout: 15000 });

    await page.goto(workspaceUrl);
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible({ timeout: 10000 });
  });
});
