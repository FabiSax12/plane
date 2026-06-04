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

function isSignUpUrl(url: URL): boolean {
  if (url.pathname === "/" || url.pathname === "/onboard") return true;
  if (/^\/[a-z0-9_-]+\/$/.test(url.pathname)) {
    const excluded = ["/sign-in/", "/sign-up/", "/error/", "/accounts/"];
    return !excluded.includes(url.pathname);
  }
  return false;
}

async function registerUser(page: Page, email: string, password: string) {
  await retry(async () => {
    await page.goto("/sign-up", { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder("name@company.com").waitFor({ state: "visible", timeout: 5000 });
    await page.getByPlaceholder("name@company.com").fill(email);
    await page.getByRole("button", { name: "Continue" }).click();
    await page.getByPlaceholder("Enter password").waitFor({ state: "visible", timeout: 5000 });
    await page.getByPlaceholder("Enter password").fill(password);
    await page.getByPlaceholder("Confirm password").fill(password);
    await page.getByRole("button", { name: "Create account" }).click();
    await page.waitForURL(isSignUpUrl, { timeout: 20000 });
    const nameField = page.getByPlaceholder("Enter your full name");
    if (await nameField.isVisible({ timeout: 5000 }).catch(() => false)) {
      await nameField.fill("QA Tester");
      await page.getByRole("button", { name: "Continue" }).click();
    }
  });
}

test.describe.serial("PS-04", () => {
  test.setTimeout(120000);

  test.beforeEach(async ({ page }) => {
    await page.goto("/sign-up");
  });

  test("registration form is visible on sign-up page", async ({ page }) => {
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
  });

  test("redirects to workspace or onboarding after sign-up", async ({ page }) => {
    const timestamp = Date.now();
    const email = `qa-signup-${timestamp}@itcr.ac.cr`;
    await registerUser(page, email, "TestPass2026!");
    await expect(page).not.toHaveURL(/\/sign-in\/|\/sign-up\//);
  });

  test("no error_code in URL after sign-up", async ({ page }) => {
    const timestamp = Date.now();
    const email = `qa-signup-${timestamp}@itcr.ac.cr`;
    await registerUser(page, email, "TestPass2026!");
    await expect(page).not.toHaveURL(/error_code=/, { timeout: 10000 });
  });

  test("session cookie is set after sign-up", async ({ page }) => {
    const timestamp = Date.now();
    const email = `qa-signup-${timestamp}@itcr.ac.cr`;
    await registerUser(page, email, "TestPass2026!");
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((c) => c.name === "session-id");
    expect(sessionCookie).toBeDefined();
  });
});
