/**
 * helpers.ts — Utilidades compartidas para specs de Daniel Salas (PS-13 a PS-16)
 *
 * Patrón de auth: login directo en cada beforeEach, sin storageState.
 * Workspace slug: variable de entorno E2E_WORKSPACE_SLUG o valor por defecto.
 */
import type { Page } from "@playwright/test";

export const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "https://makeplane.r-odio.com";
const EMAIL = process.env.E2E_USER_EMAIL_DANIEL ?? "salasdaniel@gmail.com";
const PASSWORD = process.env.E2E_USER_PASSWORD_DANIEL ?? "#Plane1234";
export const WORKSPACE_SLUG = process.env.E2E_WORKSPACE_SLUG ?? "hola";

async function retry<T>(fn: () => Promise<T>, retries = 2, delayMs = 8_000): Promise<T> {
  try {
    return await fn();
  } catch (e) {
    if (retries <= 0) throw e;
    await new Promise((r) => setTimeout(r, delayMs));
    return retry(fn, retries - 1, delayMs);
  }
}

/**
 * Hace login con las credenciales de Daniel.
 * Si ya hay sesión activa (URL no es sign-in ni raíz), retorna sin hacer nada.
 */
export async function signIn(page: Page): Promise<void> {
  await retry(async () => {
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState("networkidle");

    const pathname = new URL(page.url()).pathname;
    if (pathname !== "/" && !pathname.startsWith("/sign-in")) return;

    await page.getByLabel(/email/i).first().waitFor({ state: "visible", timeout: 10_000 });
    await page.getByLabel(/email/i).first().fill(EMAIL);
    await page
      .getByRole("button", { name: /continue/i })
      .first()
      .click();

    await page.getByRole("textbox", { name: /password/i }).waitFor({ state: "visible", timeout: 10_000 });
    await page.getByRole("textbox", { name: /password/i }).fill(PASSWORD);
    await page
      .getByRole("button", { name: /sign in|continue|go to workspace/i })
      .first()
      .click();

    await page.waitForURL(/\/[a-z0-9-]+/i, { timeout: 20_000 });
  });
}

/**
 * Navega al listado de issues del primer proyecto disponible.
 * Incluye login y retorna el workspaceSlug usado.
 */
export async function navigateToFirstProjectIssues(page: Page): Promise<string> {
  await signIn(page);

  await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}`);
  await page.waitForSelector('[href*="/projects/"]', { timeout: 20_000 });

  const issuesLink = page.locator('[href*="/projects/"][href*="/issues"]').first();
  const href = await issuesLink.getAttribute("href");
  await page.goto(`${BASE_URL}${href}`);

  await page.waitForURL(/\/projects\/.*\/issues/, { timeout: 15_000 });
  return WORKSPACE_SLUG;
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
      let btns = child.querySelectorAll("button");
      if (btns.length >= 3) {
        if (!btns[idx]) throw new Error(`Layout button ${idx} not found (${btns.length} total)`);
        (btns[idx] as HTMLElement).click();
        return;
      }
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
    await page.keyboard.press("Escape");
    await clickFilterToggle(page);
    return;
  }
  // Estrategia 2: botones X individuales en chips de filtro
  const clearButtons = await page
    .locator('[class*="remove"], [aria-label="Remove filter"], button:has-text("×")')
    .all();
  await Promise.all(
    clearButtons.map(async (btn) => {
      const isVisible = await btn.isVisible().catch(() => false);
      if (isVisible) {
        await btn.click();
        await page.waitForTimeout(300);
      }
    })
  );
  await page.keyboard.press("Escape");
}
