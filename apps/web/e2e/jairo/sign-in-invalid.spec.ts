import { test, expect } from "@playwright/test";

test.describe("PS-02: Inicio de sesión inválido", () => {
  test("el usuario ingresa credenciales incorrectas y ve un mensaje de error", async ({ page }) => {
    await page.goto("/sign-in");
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
    await page.getByPlaceholder("name@company.com").fill("qa-tester@itcr.ac.cr");
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByPlaceholder("Enter password")).toBeVisible({ timeout: 10000 });
    await page.getByPlaceholder("Enter password").fill("wrongpassword123");
    await page.getByRole("button", { name: /Continue|Go to workspace/ }).click();
    await expect(page).toHaveURL(/error_code=/, { timeout: 10000 });
    await expect(page.getByRole("alert")).toContainText("Authentication failed. Please try again.", { timeout: 10000 });
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((c) => c.name === "session-id");
    expect(sessionCookie).toBeUndefined();
  });
});
