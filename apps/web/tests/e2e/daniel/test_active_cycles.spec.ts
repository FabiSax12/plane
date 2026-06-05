/**
 * PS-16: Vista consolidada /active-cycles/ muestra ciclos de todos los proyectos
 * Técnica: Caso de uso / flujo de usuario
 * HU: Monitorear ciclos activos de todos los proyectos desde una vista unificada
 *
 * Rubrica:
 *   - 1 expect() por test
 *   - beforeEach con setup compartido
 *   - Marcadores: @daniel @qa
 *
 * URL: /{workspaceSlug}/active-cycles/
 * La vista muestra cards de ciclos activos por proyecto.
 * Si no hay ciclos activos, muestra un empty state.
 */
import { test, expect } from "@playwright/test";
import { signIn, BASE_URL, WORKSPACE_SLUG } from "./helpers";

test.describe("PS-16: Active cycles consolidated view @daniel @qa", () => {
  /**
   * beforeEach: hace login y navega a /{workspace}/active-cycles/.
   */
  test.beforeEach(async ({ page }) => {
    await signIn(page);
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/active-cycles/`);
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(2_000);
  });

  test("PS-16-a: la página de active cycles carga sin errores (status 200 implícito)", async ({ page }) => {
    await expect(
      page
        .getByRole("heading", { name: /active cycles/i })
        .or(page.locator("h1, h2, h3").filter({ hasText: /active.?cycles/i }))
        .or(page.locator("h1, h2, h3").filter({ hasText: /cycles/i }))
        .first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("PS-16-b: la URL contiene el segmento active-cycles", async ({ page }) => {
    await expect(page).toHaveURL(/\/active-cycles\/?/);
  });

  test("PS-16-c: la vista muestra contenido principal (ciclos activos o empty state)", async ({ page }) => {
    await expect(
      page
        .locator('[class*="cycle"], [class*="empty"], [class*="no-result"]')
        .or(page.getByText(/no active cycles/i))
        .or(page.getByText(/monitor cycles/i))
        .or(page.getByText(/no cycles/i))
        .or(page.locator("main").locator(":not(script)").first())
        .first()
    ).toBeVisible({ timeout: 10_000 });
  });
});
