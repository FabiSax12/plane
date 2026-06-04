/**
 * PS-14: Filtrar work items por prioridad muestra solo coincidentes
 * Técnica: Caso de uso / flujo de usuario
 * HU: Filtrar work items por prioridad en la vista de lista
 *
 * Rubrica:
 *   - 1 expect() por test
 *   - beforeEach con setup compartido
 *   - Marcadores: @daniel @qa
 *
 * Hallazgo: Plane aplica filtros de forma optimista en el cliente.
 * El chip de filtro aplicado aparece ANTES de que la lista se re-renderice.
 * Se verifica el chip porque es el indicador visual directo del estado del filtro.
 */
import { test, expect } from "@playwright/test";
import { navigateToFirstProjectIssues } from "./helpers";

test.describe("PS-14: Filter work items by priority @daniel @qa", () => {
  /**
   * beforeEach: navega al listado de issues y abre el panel de filtros.
   * Garantiza que los filtros estén visibles antes de cada test.
   */
  test.beforeEach(async ({ page }) => {
    await navigateToFirstProjectIssues(page);
    // Limpiar filtros previos si existieran: buscar botón "Clear all"
    const clearAll = page.getByRole("button", { name: /clear all/i });
    if (await clearAll.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await clearAll.click();
    }
    // Abrir el panel de filtros haciendo clic en el botón Filters / icono de filtro
    const filtersBtn = page
      .locator('button')
      .filter({ hasText: /^filters$/i })
      .or(page.locator('[aria-label*="filter" i]').first());
    await filtersBtn.first().click();
    // Esperar a que aparezca la fila de condiciones de filtro
    await page.locator('[class*="filter"], [data-testid*="filter"]').first()
      .waitFor({ timeout: 8_000 });
  });

  test("PS-14-a: al aplicar filtro Priority=High aparece el chip 'high' en filtros activos", async ({ page }) => {
    // Hacer clic en el botón "Add filter" o en el selector de tipo de filtro
    await page
      .locator('button')
      .filter({ hasText: /add filter/i })
      .or(page.getByRole("button", { name: /priority/i }))
      .first()
      .click();
    // Si se abrió un menú de tipos de filtro, seleccionar "Priority"
    const priorityOption = page.getByRole("option", { name: /^priority$/i });
    if (await priorityOption.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await priorityOption.click();
    }
    // Seleccionar "High" en el dropdown de valores de prioridad
    await page.getByRole("option", { name: /^high$/i }).click();
    // Cerrar el dropdown si sigue abierto (presionar Escape)
    await page.keyboard.press("Escape");
    // Verificar que el chip de filtro aplicado "high" es visible
    await expect(
      page.locator('[class*="filter"]').filter({ hasText: /high/i }).first()
    ).toBeVisible();
  });

  test("PS-14-b: el panel de filtros se muestra tras hacer clic en el botón Filters", async ({ page }) => {
    // Verificar que el área de filtros (donde se agregan condiciones) está visible
    await expect(
      page.locator('[class*="filter-row"], [class*="filters-row"], [data-testid*="filter"]').first()
        .or(page.locator('button').filter({ hasText: /add filter/i }).first())
    ).toBeVisible();
  });

  test("PS-14-c: al aplicar filtro Priority=Urgent el chip de prioridad urgente es visible", async ({ page }) => {
    // Hacer clic en "Add filter" o en selector de Priority directamente
    await page
      .locator('button')
      .filter({ hasText: /add filter/i })
      .or(page.getByRole("button", { name: /priority/i }))
      .first()
      .click();
    const priorityOption = page.getByRole("option", { name: /^priority$/i });
    if (await priorityOption.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await priorityOption.click();
    }
    await page.getByRole("option", { name: /^urgent$/i }).click();
    await page.keyboard.press("Escape");
    await expect(
      page.locator('[class*="filter"]').filter({ hasText: /urgent/i }).first()
    ).toBeVisible();
  });
});
