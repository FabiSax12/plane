/**
 * helpers.ts — Utilidades compartidas para specs de Daniel Salas
 */
import fs from "fs";
import type { Page } from "@playwright/test";
import { WORKSPACE_FILE } from "../../../playwright-daniel.config";

const EMAIL = "salasdaniel@gmail.com";
const PASSWORD = "#Plane1234";

/** Lee el workspace slug guardado por auth.setup.ts */
export function readWorkspaceSlug(): string {
  if (process.env.PLANE_WORKSPACE) return process.env.PLANE_WORKSPACE;
  const raw = fs.readFileSync(WORKSPACE_FILE, "utf-8");
  const { workspaceSlug } = JSON.parse(raw) as { workspaceSlug: string };
  return workspaceSlug;
}

/**
 * Si la sesión no persistió, Plane muestra el login form en la misma URL.
 * Detecta el form y hace login completo si es necesario.
 */
export async function ensureAuthenticated(page: Page): Promise<void> {
  const emailInput = page.locator('input[type="email"]');
  const isLoginPage = await emailInput.isVisible({ timeout: 4_000 }).catch(() => false);
  if (!isLoginPage) return;

  await emailInput.fill(EMAIL);
  await page.locator('button[type="submit"]').first().click();

  const passwordInput = page.locator('input[type="password"]');
  await passwordInput.waitFor({ state: "visible", timeout: 10_000 });
  await passwordInput.fill(PASSWORD);
  await page.locator('button[type="submit"]').first().click();

  await page.waitForURL(/\/[^/]+\//, { timeout: 30_000 });
}

/**
 * Navega al listado de issues del primer proyecto disponible.
 * Incluye fallback de autenticación y retorna el workspaceSlug.
 */
export async function navigateToFirstProjectIssues(page: Page): Promise<string> {
  const workspaceSlug = readWorkspaceSlug();
  await page.goto(`/${workspaceSlug}`);

  await ensureAuthenticated(page);

  await page.waitForSelector('[href*="/projects/"]', { timeout: 20_000 });

  const issuesLink = page.locator('[href*="/projects/"][href*="/issues"]').first();
  const href = await issuesLink.getAttribute("href");
  await page.goto(href!);

  await page.waitForURL(/\/projects\/.*\/issues/, { timeout: 15_000 });
  return workspaceSlug;
}

/**
 * Espera que el toolbar de issues esté completamente renderizado.
 * Indicador: existe un botón con texto "Display" en el DOM.
 */
async function waitForToolbar(page: Page): Promise<void> {
  await page.waitForFunction(
    () => Array.from(document.querySelectorAll("button")).some((b) => (b.textContent ?? "").trim().includes("Display")),
    { timeout: 15_000 }
  );
}

/**
 * Hace click en el toggle de filtros de la vista de issues.
 *
 * ESTRUCTURA DOM real (Plane source code):
 *   toolbar
 *     ├── div  → LayoutSelection (wrapper)
 *     ├── div  → MobileLayoutSelection (wrapper)
 *     ├── div|button → FiltersToggle:
 *     │     • AddFilterButton → div.relative > CustomSearchSelect > <button>
 *     │     • IconButton      → <button> directamente
 *     └── div  → FiltersDropdown Popover (as="div")
 *           └── div (ref)
 *                 └── div.hidden @4xl:flex
 *                       └── <button>Display</button>
 *
 * El button "Display" está 3 niveles dentro del Popover.
 * Popover.previousElementSibling = filter toggle (div o button).
 * Si es div → querySelector("button"); si ES un button → click directo.
 */
export async function clickFilterToggle(page: Page): Promise<void> {
  await waitForToolbar(page);
  await page.evaluate(() => {
    const allBtns = Array.from(document.querySelectorAll("button"));
    const displayBtn = allBtns.find(
      (b) => (b.textContent ?? "").trim().includes("Display") && !(b.textContent ?? "").trim().includes("Analytics")
    );
    if (!displayBtn) throw new Error("Display button not found in DOM");

    const popoverDiv = displayBtn.parentElement?.parentElement?.parentElement;
    if (!popoverDiv) throw new Error("Popover container not found (3 levels up from Display)");

    const filterWrapper = popoverDiv.previousElementSibling as HTMLElement | null;
    if (!filterWrapper) throw new Error("No element before Popover div in toolbar");

    const target =
      filterWrapper.tagName === "BUTTON" ? filterWrapper : (filterWrapper.querySelector("button") ?? filterWrapper);
    (target as HTMLElement).click();
  });
  await page.waitForTimeout(500);
}

/**
 * Hace click en el n-ésimo botón de layout (0=List, 1=Board/Kanban, 2=Calendar…).
 *
 * Sube desde el button "Display" hasta el toolbar container (4 niveles),
 * luego busca el primer hijo con ≥3 botones internos = LayoutSelection.
 * No depende de clases CSS que pueden cambiar al compilar con Tailwind.
 */
export async function clickLayoutButton(page: Page, index: number): Promise<void> {
  await waitForToolbar(page);
  await page.evaluate((idx: number) => {
    const allBtns = Array.from(document.querySelectorAll("button"));
    const displayBtn = allBtns.find(
      (b) => (b.textContent ?? "").trim().includes("Display") && !(b.textContent ?? "").trim().includes("Analytics")
    );
    if (!displayBtn) throw new Error("Display button not found");

    // Subir 4 niveles: button → div.hidden → div(ref) → div(Popover) → toolbar
    const toolbarDiv = displayBtn.parentElement?.parentElement?.parentElement?.parentElement;
    if (!toolbarDiv) throw new Error("Toolbar container not found (4 levels up)");

    // LayoutSelection es el primer hijo del toolbar que tiene ≥3 botones directos o anidados
    for (const child of Array.from(toolbarDiv.children)) {
      // Buscar directo
      let btns = child.querySelectorAll("button");
      if (btns.length >= 3) {
        if (!btns[idx]) throw new Error(`Layout button ${idx} not found (${btns.length} total)`);
        (btns[idx] as HTMLElement).click();
        return;
      }
      // Buscar un nivel más profundo (wrapper div → inner div con botones)
      for (const grandchild of Array.from(child.children)) {
        btns = grandchild.querySelectorAll("button");
        if (btns.length >= 3) {
          if (!btns[idx]) throw new Error(`Layout button ${idx} not found (${btns.length} total)`);
          (btns[idx] as HTMLElement).click();
          return;
        }
      }
    }

    throw new Error("Layout selection container not found in toolbar children");
  }, index);
  await page.waitForTimeout(800);
}

/**
 * Limpia todos los filtros activos.
 * Estrategia primaria: botón "Clear all" (aparece en la barra cuando hay filtros).
 * Cuando lo encuentra, también re-abre el dropdown de propiedades para que el test
 * pueda aplicar un nuevo filtro sin necesidad de llamar a clickFilterToggle de nuevo.
 * Estrategia fallback: buscar botones X individuales en los chips.
 */
export async function clearActiveFilters(page: Page): Promise<void> {
  // Estrategia 1: botón "Clear all" visible en la barra de filtros activos
  const clearAllBtn = page.getByRole("button", { name: /^clear all$/i });
  const hasClearAll = await clearAllBtn.isVisible({ timeout: 1_000 }).catch(() => false);
  if (hasClearAll) {
    await clearAllBtn.click();
    await page.waitForTimeout(500);
    // El dropdown anterior estaba abierto sin "Priority" (ya estaba en uso).
    // Cerrar y re-abrir para obtener un dropdown fresco que incluya Priority.
    await page.keyboard.press("Escape");
    await clickFilterToggle(page);
    return;
  }
  // Estrategia 2: botones X individuales en chips de filtro
  const clearButtons = await page.locator('[class*="remove"], [aria-label*="remove"], button:has-text("×")').all();
  for (const btn of clearButtons) {
    const isVisible = await btn.isVisible().catch(() => false);
    if (isVisible) {
      await btn.click();
      await page.waitForTimeout(300);
    }
  }
  // Presionar Escape para cerrar cualquier dropdown abierto
  await page.keyboard.press("Escape");
}
