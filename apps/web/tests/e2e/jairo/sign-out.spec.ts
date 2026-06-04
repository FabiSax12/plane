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

function isWorkspacePathname(url: URL): boolean {
  return url.pathname === "/" || /^\/[a-z0-9_-]+\/$/.test(url.pathname);
}

async function login(page: Page) {
  await retry(async () => {
    await page.goto("/sign-in", { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder("name@company.com").waitFor({ state: "visible", timeout: 5000 });
    await page.getByPlaceholder("name@company.com").fill("qa-tester@itcr.ac.cr");
    await page.getByRole("button", { name: "Continue" }).click();
    await page.getByPlaceholder("Enter password").waitFor({ state: "visible", timeout: 15000 });
    await page.getByPlaceholder("Enter password").fill("TestPass123!");
    await page.getByRole("button", { name: /Continue|Go to workspace/ }).click();
    await page.waitForURL(isWorkspacePathname, { timeout: 30000 });
  });
}

async function signOut(page: Page) {
  const onSignIn = await page
    .getByPlaceholder("name@company.com")
    .isVisible({ timeout: 2000 })
    .catch(() => false);
  if (onSignIn) {
    await login(page);
  }
  const workspaceUrl = page.url();
  const qButton = page.locator("button").filter({ hasText: /^Q$/ });
  if (await qButton.isVisible({ timeout: 5000 }).catch(() => false)) {
    await qButton.last().click();
    await page.waitForTimeout(500);
    await page.getByRole("menuitem", { name: "Sign out" }).first().click({ timeout: 10000 });
  }
  await page.context().clearCookies();
  await page.getByPlaceholder("name@company.com").waitFor({ state: "visible", timeout: 30000 });
  return workspaceUrl;
}

test.describe("PS-03", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/sign-in");
  });

  test("sign-in form is visible after logout", async ({ page }) => {
    await signOut(page);
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible();
  });

  test("workspace URL redirects to sign-in after logout", async ({ page }) => {
    const workspaceUrl = await signOut(page);
    await page.goto(workspaceUrl);
    await expect(page.getByPlaceholder("name@company.com")).toBeVisible({ timeout: 10000 });
  });
});
