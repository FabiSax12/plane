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
import { readWorkspaceSlug } from "./helpers";

test.describe("PS-16: Active cycles consolidated view @daniel @qa", () => {
  /**
   * beforeEach: navega directamente a /{workspace}/active-cycles/
   * La sesión autenticada (storageState) garantiza acceso.
   */
  test.beforeEach(async ({ page }) => {
    const workspaceSlug = readWorkspaceSlug();
    await page.goto(`/${workspaceSlug}/active-cycles/`);
    // Esperar a que la página cargue (heading o contenido principal)
    await page.waitForLoadState("networkidle", { timeout: 20_000 });
  });

  test("PS-16-a: la página de active cycles carga sin errores (status 200 implícito)", async ({ page }) => {
    // Verificar que el heading principal de la sección es visible
    await expect(
      page
        .getByRole("heading", { name: /active cycles/i })
        .or(page.locator('h1, h2, h3').filter({ hasText: /active.?cycles/i }))
        .first()
    ).toBeVisible();
  });

  test("PS-16-b: la URL contiene el segmento active-cycles", async ({ page }) => {
    // Verificar que navegamos al lugar correcto
    await expect(page).toHaveURL(/\/active-cycles\/?/);
  });

  test("PS-16-c: la vista muestra contenido principal (ciclos activos o empty state)", async ({ page }) => {
    // La página siempre renderiza algo: cards de ciclos activos O un empty state message
    // Ambos son indicadores válidos de que la vista consolidada funcionó
    await expect(
      page
        .locator('[class*="cycle"], [class*="empty-state"], [class*="no-results"]')
        .or(page.getByText(/no active cycles/i))
        .or(page.getByText(/monitor cycles/i))
        .first()
    ).toBeVisible();
  });
});
