/**
 * PS-13: Asignar prioridad y fecha límite a work item se refleja en la tarjeta
 * Técnica: Caso de uso / exploración de flujo
 * HU: Gestionar propiedades de un work item desde la vista de lista
 *
 * Rubrica:
 *   - 1 expect() por test
 *   - beforeEach con setup compartido
 *   - Marcadores: @daniel @qa
 */
import { test, expect } from "@playwright/test";
import { navigateToFirstProjectIssues } from "./helpers";

test.describe("PS-13: Priority and due date visible on issue card @daniel @qa", () => {
  /**
   * beforeEach: navega al listado de issues del primer proyecto
   * y abre el panel de detalle del primer work item disponible.
   */
  test.beforeEach(async ({ page }) => {
    await navigateToFirstProjectIssues(page);
    // Abrir el primer issue haciendo clic en su título (primera fila)
    const firstIssueRow = page.locator("[data-entity-id]").first();
    await firstIssueRow.waitFor({ timeout: 10_000 });
    await firstIssueRow.click();
    // Esperar a que el panel de detalle esté visible
    await page.locator('[data-testid="issue-detail-root"], aside, [role="dialog"]')
      .first()
      .waitFor({ timeout: 10_000 });
  });

  test("PS-13-a: al seleccionar prioridad High, el badge muestra 'high'", async ({ page }) => {
    // Hacer clic en el selector de prioridad dentro del detalle del issue
    await page
      .locator('button[aria-label*="priority" i], button:has-text("None"), button:has-text("high"), button:has-text("medium"), button:has-text("low"), button:has-text("urgent")')
      .first()
      .click();
    // Seleccionar "High" del dropdown de prioridades
    await page.getByRole("option", { name: /^high$/i }).click();
    // Verificar que el badge de prioridad ahora muestra "high"
    await expect(
      page.locator('button, [class*="priority"]').filter({ hasText: /high/i }).first()
    ).toBeVisible();
  });

  test("PS-13-b: al asignar due date, la fecha queda visible en el detalle del issue", async ({ page }) => {
    // Hacer clic en el campo de fecha límite
    await page
      .locator('button:has-text("Due date"), button:has-text("Add due date"), [aria-label*="due date" i]')
      .first()
      .click();
    // Seleccionar el día 28 del mes actual en el calendar picker
    await page.getByRole("button", { name: "28" }).first().click();
    // Verificar que un elemento con texto de fecha (dd o número) aparece en la sección de due date
    await expect(
      page.locator('[class*="due-date"], [class*="dueDate"], [aria-label*="due date" i]')
        .filter({ hasText: /\d/ })
        .first()
    ).toBeVisible();
  });

  test("PS-13-c: el panel de detalle del issue está abierto y es visible", async ({ page }) => {
    // Verificar que el detalle abrió correctamente (precondición de los tests anteriores)
    await expect(
      page.locator('[data-testid="issue-detail-root"], aside, [role="dialog"]').first()
    ).toBeVisible();
  });
});
