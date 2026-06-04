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

function isWorkspaceUrl(url: URL): boolean {
  if (url.pathname === "/") return true;
  if (/^\/[a-z0-9_-]+\/$/.test(url.pathname)) {
    const excluded = ["/sign-in/", "/sign-up/", "/error/", "/accounts/"];
    return !excluded.includes(url.pathname);
  }
  return false;
}

async function signIn(page: Page) {
  await retry(async () => {
    await page.goto("/sign-in", { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder("name@company.com").waitFor({ state: "visible", timeout: 5000 });
    await page.getByPlaceholder("name@company.com").fill("qa-tester@itcr.ac.cr");
    await page.getByRole("button", { name: "Continue" }).click();
    await page.getByPlaceholder("Enter password").waitFor({ state: "visible", timeout: 15000 });
    await page.getByPlaceholder("Enter password").fill("TestPass123!");
    await page.getByRole("button", { name: /Continue|Go to workspace/ }).click();
    await page.waitForURL(isWorkspaceUrl, { timeout: 30000 });
  });
}

test.describe("PS-01", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/sign-in");
  });

  test("email field is visible on sign-in page", async ({ page }) => {
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
  });

  test("password field appears after entering email", async ({ page }) => {
    await page.getByPlaceholder("name@company.com").fill("qa-tester@itcr.ac.cr");
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByPlaceholder("Enter password")).toBeVisible({ timeout: 10000 });
  });

  test("redirects to workspace URL after valid login", async ({ page }) => {
    await signIn(page);
    await expect(page).not.toHaveURL(/\/sign-in\/|\/sign-up\//);
  });

  test("session cookie is set after valid login", async ({ page }) => {
    await signIn(page);
    const cookies = await page.context().cookies();
    const sessionCookie = cookies.find((c) => c.name === "session-id");
    expect(sessionCookie).toBeDefined();
  });
});
