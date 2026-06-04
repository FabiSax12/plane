/**
 * PS-13: Asignar prioridad y fecha límite a work item se refleja en la tarjeta
 * Técnica: Caso de uso / exploración de flujo
 * HU: Gestionar propiedades de un work item desde la vista de lista
 *
 * Rubrica:
 *   - 1 expect() por test
 *   - beforeEach con setup compartido
 *   - Marcadores: @daniel @qa
 *
 * Hallazgo: La vista de issues puede cargarse en Board/Kanban por defecto.
 * Se fuerza la vista Lista (index 0) para garantizar que los issue rows
 * con [data-entity-id] estén disponibles antes de interactuar.
 */
import { test, expect } from "@playwright/test";
import { navigateToFirstProjectIssues, clickLayoutButton } from "./helpers";

test.describe("PS-13: Priority and due date visible on issue card @daniel @qa", () => {
  /**
   * beforeEach: navega al listado en vista Lista y abre el detalle del primer issue.
   */
  test.beforeEach(async ({ page }) => {
    await navigateToFirstProjectIssues(page);

    // Forzar vista Lista para garantizar que los issue rows sean accesibles
    await clickLayoutButton(page, 0);

    // Esperar a que aparezca al menos un issue en la lista
    const firstIssue = page.locator('[id^="issue-"]').first();
    await firstIssue.waitFor({ timeout: 15_000 });
    await firstIssue.click();

    // Esperar a que el panel de detalle esté visible
    await page
      .locator('[data-testid="issue-detail-root"], aside, [role="dialog"]')
      .first()
      .waitFor({ timeout: 10_000 });
  });

  test("PS-13-a: al seleccionar prioridad High, el badge muestra 'high'", async ({ page }) => {
    // Clic en el selector de prioridad dentro del detalle del issue
    await page
      .locator(
        'button[aria-label*="priority" i], button:has-text("None"), button:has-text("high"), button:has-text("medium"), button:has-text("low"), button:has-text("urgent")'
      )
      .first()
      .click();

    // Seleccionar "High" del dropdown
    await page.getByRole("option", { name: /^high$/i }).click();

    // Verificar que el badge de prioridad muestra "high"
    await expect(page.locator('button, [class*="priority"]').filter({ hasText: /high/i }).first()).toBeVisible();
  });

  test("PS-13-b: al asignar due date, la fecha queda visible en el detalle del issue", async ({ page }) => {
    // Clic en la fila de due date del sidebar y abrir su dropdown
    const dueDateRow = page
      .locator("div")
      .filter({ has: page.getByText(/^Due date$/i) })
      .first();
    await dueDateRow.locator("button").first().click();

    // Seleccionar el día 28 del mes actual en el calendar picker
    await page.getByRole("button", { name: "28" }).first().click();

    // Verificar que un elemento con texto de fecha aparece en la sección de due date
    await expect(
      page
        .locator('[class*="due-date"], [class*="dueDate"], [aria-label*="due date" i]')
        .filter({ hasText: /\d/ })
        .first()
    ).toBeVisible();
  });

  test("PS-13-c: el panel de detalle del issue está abierto y es visible", async ({ page }) => {
    await expect(page.locator('[data-testid="issue-detail-root"], aside, [role="dialog"]').first()).toBeVisible();
  });
});
