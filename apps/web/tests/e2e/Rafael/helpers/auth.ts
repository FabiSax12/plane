import { Page } from "@playwright/test";

const BASE_URL = process.env.E2E_BASE_URL ?? "https://makeplane.r-odio.com";
const EMAIL = process.env.E2E_USER_EMAIL ?? "rafaelodio09@gmail.com";
const PASSWORD = process.env.E2E_USER_PASS ?? ".RaOdMe7232";

export async function loginAs(page: Page, email = EMAIL, password = PASSWORD) {
  await page.goto(`${BASE_URL}/`);

  // Selectores exactos capturados con Playwright Codegen
  await page.getByRole("textbox", { name: "Email" }).fill(email);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("textbox", { name: "Password" }).fill(password);
  await page.getByRole("button", { name: "Go to workspace" }).click();

  await page.waitForURL((url) => !url.href.includes("/sign-in"), { timeout: 20000 });
  await page.waitForLoadState("networkidle");
}

export { BASE_URL, EMAIL, PASSWORD };
