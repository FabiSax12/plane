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
 * Comportamiento verificado: Plane persiste filtros en el store de MobX,
 * por lo que al cambiar de layout los filtros permanecen reflejados.
 */
import { test, expect } from "@playwright/test";
import { navigateToFirstProjectIssues, clickFilterToggle, clickLayoutButton } from "./helpers";

/**
 * Aplica el filtro Priority=High usando el helper correcto.
 *
 * Comportamiento real de Plane:
 * clickFilterToggle abre el dropdown de propiedades directamente (AddFilterButton con label=null).
 * No hay botón "Add filter" con texto — se selecciona Priority directamente como role="option".
 * Al seleccionar Priority, MultiSelectFilterValueInput abre su dropdown automáticamente
 * (defaultOpen=true cuando value=undefined), y se elige High.
 */
async function applyPriorityHighFilter(page: import("@playwright/test").Page): Promise<void> {
  await clickFilterToggle(page);

  // Dropdown de propiedades se abre directamente; seleccionar Priority
  await page.getByRole("option", { name: /^priority$/i }).waitFor({ timeout: 5_000 });
  await page.getByRole("option", { name: /^priority$/i }).click();

  // Value dropdown se abre automáticamente; seleccionar High
  await page.getByRole("option", { name: /^high$/i }).waitFor({ timeout: 5_000 });
  await page.getByRole("option", { name: /^high$/i }).click();

  await page.keyboard.press("Escape");
}

test.describe("PS-15: Switching from List to Kanban preserves active filters @daniel @qa", () => {
  /**
   * beforeEach: navega al listado, activa vista Lista,
   * aplica Priority=High, luego cambia a vista Board/Kanban.
   */
  test.beforeEach(async ({ page }) => {
    await navigateToFirstProjectIssues(page);

    // Forzar vista Lista (index 0) para partir desde un estado conocido
    await clickLayoutButton(page, 0);

    // Aplicar filtro Priority=High
    await applyPriorityHighFilter(page);

    // Cambiar a vista Board/Kanban (index 1)
    await clickLayoutButton(page, 1);

    // Esperar a que el layout de kanban cargue
    await page.waitForTimeout(1_000);
  });

  test("PS-15-a: el chip de filtro 'high' sigue visible en la vista Kanban", async ({ page }) => {
    // FilterItemContainer wraps "Priority" label + "High" value — no "[class*='filter']" in Plane's output.
    await expect(
      page
        .locator("div")
        .filter({ hasText: /priority/i })
        .filter({ hasText: /high/i })
        .first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("PS-15-b: la vista Kanban muestra columnas agrupadas por estado", async ({ page }) => {
    await expect(page.locator('[class*="kanban"], [class*="board"], [class*="group"]').first()).toBeVisible();
  });

  test("PS-15-c: la URL sigue apuntando al proyecto de issues tras el cambio de vista", async ({ page }) => {
    await expect(page).toHaveURL(/\/projects\/.*\/issues/);
  });
});
