import { Page } from "@playwright/test";

const BASE_URL = process.env.E2E_BASE_URL ?? "https://makeplane.r-odio.com";
const EMAIL = process.env.E2E_USER_EMAIL ?? "rafaelodio09@gmail.com";
const PASSWORD = process.env.E2E_USER_PASS ?? ".RaOdMe7232";

async function retry<T>(fn: () => Promise<T>, retries = 2, delayMs = 10000): Promise<T> {
  try {
    return await fn();
  } catch (e) {
    if (retries <= 0) throw e;
    await new Promise((r) => setTimeout(r, delayMs));
    return retry(fn, retries - 1, delayMs);
  }
}

export async function loginAs(page: Page, email = EMAIL, password = PASSWORD) {
  await retry(async () => {
    await page.goto(`${BASE_URL}/`);

    // Selectores exactos capturados con Playwright Codegen
    await page.getByRole("textbox", { name: "Email" }).fill(email);
    await page.getByRole("button", { name: "Continue" }).click();
    await page.getByRole("textbox", { name: "Password" }).fill(password);
    await page.getByRole("button", { name: "Go to workspace" }).click();

    await page.waitForURL((url) => !url.href.includes("/sign-in"), { timeout: 30000 });
    // Esperar a que el sidebar esté hidratado antes de continuar
    await page.getByLabel("Main sidebar").waitFor({ state: "visible", timeout: 30000 });
  });
}

export { BASE_URL, EMAIL, PASSWORD };
