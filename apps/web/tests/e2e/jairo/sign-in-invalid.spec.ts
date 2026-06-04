import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";

async function retry<T>(fn: () => Promise<T>, retries = 2, delayMs = 10000): Promise<T> {
  try {
    return await fn();
  } catch (e) {
    if (retries <= 0) throw e;
    await new Promise((r) => setTimeout(r, delayMs));
    return retry(fn, retries - 1, delayMs);
  }
}

async function signInWithWrongPassword(page: Page) {
  await retry(async () => {
    await page.goto("/sign-in", { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder("name@company.com").waitFor({ state: "visible", timeout: 5000 });
    await page.getByPlaceholder("name@company.com").fill("qa-tester@itcr.ac.cr");
    await page.getByRole("button", { name: "Continue" }).click();
    await page.getByPlaceholder("Enter password").waitFor({ state: "visible", timeout: 15000 });
    await page.getByPlaceholder("Enter password").fill("wrongpassword123");
    await page.getByRole("button", { name: /Continue|Go to workspace/ }).click();
    await page.waitForURL(/error_code=/, { timeout: 15000 });
  });
}

test.describe("PS-02", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/sign-in");
  });

  test("URL contains error_code after invalid login", async ({ page }) => {
    await signInWithWrongPassword(page);
    await expect(page).toHaveURL(/error_code=/, { timeout: 10000 });
  });

  test("error alert is visible with message after invalid login", async ({ page }) => {
    await signInWithWrongPassword(page);
    await expect(page.getByRole("alert")).toContainText("Authentication failed. Please try again.");
  });

  test("no session cookie after invalid login", async ({ page }) => {
    await signInWithWrongPassword(page);
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((c) => c.name === "session-id");
    expect(sessionCookie).toBeUndefined();
  });
});
