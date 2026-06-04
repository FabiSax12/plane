/**
 * PS-15: Cambiar de vista Lista a Kanban preserva los filtros activos
 * Técnica: Caso de uso / flujo de usuario
 * HU: Cambiar entre vistas de issues sin perder filtros aplicados
 *
 * Rubrica:
 *   - 1 expect() por test
 *   - beforeEach con setup compartido
 *   - Marcadores: @daniel @qa
 *
 * Comportamiento verificado: Plane persiste los filtros en el store de MobX
 * (no en la URL), por lo que al cambiar de layout los filtros permanecen
 * reflejados en el área de filtros aplicados.
 */
import { test, expect } from "@playwright/test";
import { navigateToFirstProjectIssues } from "./helpers";

/**
 * Aplica el filtro Priority=High y retorna true si tuvo éxito.
 * Helper interno para el beforeEach de PS-15.
 */
async function applyPriorityHighFilter(page: import("@playwright/test").Page): Promise<void> {
  const filtersBtn = page
    .locator('button')
    .filter({ hasText: /^filters$/i })
    .or(page.locator('[aria-label*="filter" i]').first());
  await filtersBtn.first().click();
  // Abrir selector de tipo de filtro
  const addFilterBtn = page
    .locator('button')
    .filter({ hasText: /add filter/i })
    .or(page.getByRole("button", { name: /priority/i }));
  await addFilterBtn.first().click();
  // Seleccionar "Priority" si apareció un menú de tipos
  const priorityOption = page.getByRole("option", { name: /^priority$/i });
  if (await priorityOption.isVisible({ timeout: 3_000 }).catch(() => false)) {
    await priorityOption.click();
  }
  // Seleccionar valor "High"
  await page.getByRole("option", { name: /^high$/i }).click();
  await page.keyboard.press("Escape");
}

test.describe("PS-15: Switching from List to Kanban preserves active filters @daniel @qa", () => {
  /**
   * beforeEach: navega al listado en vista Lista, aplica Priority=High,
   * luego cambia a la vista Kanban (Board Layout).
   */
  test.beforeEach(async ({ page }) => {
    await navigateToFirstProjectIssues(page);
    // Asegurar vista Lista activa: clic en el primer botón del layout switcher
    // (List Layout es el primero en el array BASE_LAYOUTS del código fuente)
    const layoutSwitcher = page.locator('[class*="rounded-md"][class*="bg-layer"]').first();
    await layoutSwitcher.locator("button").first().click();
    await page.waitForTimeout(500);
    // Aplicar filtro Priority=High
    await applyPriorityHighFilter(page);
    // Cambiar a vista Kanban: segundo botón del layout switcher (Board Layout)
    await layoutSwitcher.locator("button").nth(1).click();
    // Esperar a que el layout de kanban cargue (columnas de estado visibles)
    await page.waitForTimeout(1_000);
  });

  test("PS-15-a: el chip de filtro 'high' sigue visible en la vista Kanban", async ({ page }) => {
    // El filtro Priority=High debe persistir al cambiar de vista
    await expect(
      page.locator('[class*="filter"]').filter({ hasText: /high/i }).first()
    ).toBeVisible();
  });

  test("PS-15-b: la vista Kanban muestra columnas agrupadas por estado", async ({ page }) => {
    // Verificar que al menos una columna del tablero kanban es visible
    // Las columnas muestran grupos de estados (Backlog, Todo, In Progress, Done…)
    await expect(
      page
        .locator('[class*="kanban"], [class*="board"], [class*="group"]')
        .first()
    ).toBeVisible();
  });

  test("PS-15-c: la URL sigue apuntando al proyecto de issues tras el cambio de vista", async ({ page }) => {
    // El cambio de layout no debe redirigir fuera del contexto del proyecto
    await expect(page).toHaveURL(/\/projects\/.*\/issues/);
  });
});
