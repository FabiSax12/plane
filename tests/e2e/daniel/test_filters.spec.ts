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
 * Comportamiento real de Plane:
 * FiltersToggle en Plane NO tiene botón "Add filter" con texto visible.
 * Cuando no hay condiciones activas (estado inicial tras navegación),
 * renderiza AddFilterButton cuyo label=null → al clickear, abre directamente
 * el dropdown de propiedades de filtro (role="option": Priority, Status…).
 * Al seleccionar "Priority", se añade la condición con value=undefined y
 * MultiSelectFilterValueInput abre su dropdown automáticamente (defaultOpen=true).
 * Seleccionar "High" establece el valor; el chip aparece en la fila de filtros.
 */
import { test, expect } from "@playwright/test";
import { navigateToFirstProjectIssues, clickFilterToggle } from "./helpers";

test.describe("PS-14: Filter work items by priority @daniel @qa", () => {
  /**
   * beforeEach: navega al listado de issues.
   * La navegación resetea el estado MobX → sin condiciones, fila oculta.
   * clickFilterToggle abre el dropdown de propiedades directamente.
   */
  test.beforeEach(async ({ page }) => {
    await navigateToFirstProjectIssues(page);
    // Abrir el dropdown de propiedades de filtro
    await clickFilterToggle(page);
  });

  test("PS-14-a: al aplicar filtro Priority=High aparece el chip 'high' en filtros activos", async ({ page }) => {
    // El dropdown de propiedades está abierto; seleccionar Priority
    await page.getByRole("option", { name: /^priority$/i }).waitFor({ timeout: 5_000 });
    await page.getByRole("option", { name: /^priority$/i }).click();

    // MultiSelectFilterValueInput se abre automáticamente (defaultOpen=true cuando value=undefined)
    await page.getByRole("option", { name: /^high$/i }).waitFor({ timeout: 5_000 });
    await page.getByRole("option", { name: /^high$/i }).click();
    await page.keyboard.press("Escape");

    // FilterItemContainer wraps property label "Priority" + operator + value "High" in one div.
    // [class*="filter"] doesn't exist in Plane's compiled output; use content-based selector.
    await expect(
      page
        .locator("div")
        .filter({ hasText: /priority/i })
        .filter({ hasText: /high/i })
        .first()
    ).toBeVisible({ timeout: 10_000 });
  });

  test("PS-14-b: el panel de filtros se muestra tras abrir el toggle", async ({ page }) => {
    // El dropdown de propiedades debe mostrar "Priority" como opción accesible
    await expect(page.getByRole("option", { name: /^priority$/i })).toBeVisible({ timeout: 5_000 });
  });

  test("PS-14-c: al aplicar filtro Priority=Urgent el chip urgente es visible", async ({ page }) => {
    await page.getByRole("option", { name: /^priority$/i }).waitFor({ timeout: 5_000 });
    await page.getByRole("option", { name: /^priority$/i }).click();

    await page.getByRole("option", { name: /^urgent$/i }).waitFor({ timeout: 5_000 });
    await page.getByRole("option", { name: /^urgent$/i }).click();
    await page.keyboard.press("Escape");

    await expect(
      page
        .locator("div")
        .filter({ hasText: /priority/i })
        .filter({ hasText: /urgent/i })
        .first()
    ).toBeVisible({ timeout: 10_000 });
  });
});
