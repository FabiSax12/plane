/**
 * Pruebas de sistema asignadas a Rafael Odio: PS-09, PS-10, PS-11, PS-12
 *
 * Ejecución:
 *   cd apps/web
 *   pnpm playwright test tests/e2e/Rafael/test_project_system.spec.ts
 */

import { test, expect } from "@playwright/test";
import { loginAs, BASE_URL } from "./helpers/auth";

const WORKSPACE_SLUG = process.env.E2E_WORKSPACE_SLUG ?? "hola";

// Identificador único: timestamp al momento de llamada (3 chars) + random (3 chars)
// Formato: P + 6 chars → e.g. "PLDF3K2". Nunca reutiliza valores anteriores.
const nextIdentifier = () => {
  const ts = Date.now().toString(36).slice(-3).toUpperCase();
  const rnd = Math.random().toString(36).slice(2, 5).toUpperCase();
  return `P${ts}${rnd}`;
};

/** Crea un proyecto nuevo y retorna su UUID extraído de la URL. */
async function createProject(page: Parameters<typeof loginAs>[0], name: string, identifier: string) {
  await page.goto(`${BASE_URL}/`);
  await page.getByLabel("Main sidebar").waitFor({ state: "visible", timeout: 30000 });
  await page.getByLabel("Main sidebar").getByRole("link", { name: "Projects" }).click();
  await page.getByRole("button", { name: "Add Project" }).waitFor({ state: "visible", timeout: 20000 });
  await page.getByRole("button", { name: "Add Project" }).click();
  await page.getByRole("textbox", { name: "Project name" }).fill(name);
  await page.getByRole("textbox", { name: "Project ID" }).fill(identifier);
  await page.getByRole("button", { name: "Create project" }).click();
  await page.getByRole("link", { name: "Open project" }).click({ timeout: 20000 });
  await page.waitForURL(/\/projects\/[a-f0-9-]{36}\//, { timeout: 20000 });
  const match = page.url().match(/\/projects\/([a-f0-9-]{36})\//);
  if (!match?.[1]) throw new Error("No se pudo extraer el project ID de la URL");
  return match[1];
}

// ---------------------------------------------------------------------------
// PS-09 — Crear proyecto válido aparece en el sidebar con estados por defecto
// Técnica: Cobertura de sentencias
// ---------------------------------------------------------------------------

test.describe("PS-09: Crear proyecto desde el sidebar", () => {
  let newProjectId: string;
  let projectName: string;

  test.beforeEach(async ({ page }) => {
    await loginAs(page);
    projectName = `PS09 Project ${Date.now()}`;
    newProjectId = await createProject(page, projectName, nextIdentifier());
  });

  test("PS-09-a: proyecto recién creado aparece en el sidebar", async ({ page }) => {
    await expect(page.getByText(projectName, { exact: false }).first()).toBeVisible({ timeout: 10000 });
  });

  test("PS-09-b: estado Backlog visible en Settings por defecto", async ({ page }) => {
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/settings/projects/${newProjectId}/states/`);
    await expect(page.getByText("Backlog").first()).toBeVisible({ timeout: 15000 });
  });

  test("PS-09-c: estado Todo visible en Settings por defecto", async ({ page }) => {
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/settings/projects/${newProjectId}/states/`);
    await expect(page.getByText("Todo").first()).toBeVisible({ timeout: 15000 });
  });

  test("PS-09-d: estado In Progress visible en Settings por defecto", async ({ page }) => {
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/settings/projects/${newProjectId}/states/`);
    await expect(page.getByText("In Progress").first()).toBeVisible({ timeout: 15000 });
  });

  test("PS-09-e: estado Done visible en Settings por defecto", async ({ page }) => {
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/settings/projects/${newProjectId}/states/`);
    await expect(page.getByText("Done").first()).toBeVisible({ timeout: 15000 });
  });

  test("PS-09-f: estado Cancelled visible en Settings por defecto", async ({ page }) => {
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/settings/projects/${newProjectId}/states/`);
    await expect(page.getByText("Cancelled").first()).toBeVisible({ timeout: 15000 });
  });

  // Nota: Triage es el 6to estado por defecto pero no aparece en la UI (ni en board ni en Settings).
  // Su existencia se verifica a nivel de DB en PU-16 (DEFAULT_STATES) y PI-13 (count == 6).
});

// ---------------------------------------------------------------------------
// PS-10 — Estado custom aparece en el filtro del proyecto
// Técnica: Cobertura de sentencias
// ---------------------------------------------------------------------------

test.describe("PS-10: Estado custom aparece en el filtro del proyecto", () => {
  let newProjectId: string;

  test.beforeEach(async ({ page }) => {
    await loginAs(page);
    newProjectId = await createProject(page, `PS10 Project ${Date.now()}`, nextIdentifier());
  });

  test("PS-10: estado 'Review' creado en Settings aparece como opción en el filtro", async ({ page }) => {
    // Crear estado Review en Settings
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/settings/projects/${newProjectId}/states/`);
    await page
      .locator(
        "div:nth-child(3) > div > .flex-shrink-0.w-6.h-6.rounded.flex.justify-center.items-center.overflow-hidden.transition-colors"
      )
      .click();
    await page.getByRole("textbox", { name: "Name" }).fill("Review");
    await page.getByRole("button", { name: "Create" }).click();
    await page.getByText("Review").waitFor({ state: "visible", timeout: 10000 });

    // Verificar en filtro de issues
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/projects/${newProjectId}/issues/`);
    await page.locator("svg.lucide-list-filter").click();
    await page.locator("div").filter({ hasText: "State" }).nth(2).click();
    await expect(
      page
        .locator("div")
        .filter({ hasText: /^Review$/ })
        .first()
    ).toBeVisible({ timeout: 5000 });
  });
});

// ---------------------------------------------------------------------------
// PS-11 — Work item válido aparece en la lista con identificador PROJ-N
// Técnica: Partición de equivalencia (clase válida)
// ---------------------------------------------------------------------------

test.describe("PS-11: Crear work item válido aparece en la lista", () => {
  let newProjectId: string;

  test.beforeEach(async ({ page }) => {
    await loginAs(page);
    newProjectId = await createProject(page, `PS11 Project ${Date.now()}`, nextIdentifier());
  });

  test("PS-11: work item creado aparece en la lista con formato de identificador PROJ-N", async ({ page }) => {
    const issueName = `PS-11 Work Item ${Date.now()}`;
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/projects/${newProjectId}/issues/`);
    await page.getByRole("button", { name: "Add work item" }).waitFor({ state: "visible", timeout: 10000 });
    await page.getByRole("button", { name: "Add work item" }).click();
    await page.getByRole("textbox", { name: "Title" }).fill(issueName);
    await page.getByRole("button", { name: "Save" }).click();

    const linkText = await page.getByRole("link", { name: new RegExp(issueName) }).textContent({ timeout: 10000 });
    expect(linkText).toMatch(/^[A-Z0-9]+-\d+/);
  });
});

// ---------------------------------------------------------------------------
// PS-12 — Work item sin título muestra error de validación
// Técnica: Análisis de valores límite (caso inválido)
// ---------------------------------------------------------------------------

test.describe("PS-12: Work item sin título muestra error de validación", () => {
  let newProjectId: string;
  let urlBefore: string;

  test.beforeEach(async ({ page }) => {
    await loginAs(page);
    newProjectId = await createProject(page, `PS12 Project ${Date.now()}`, nextIdentifier());
    // Navegar a issues, abrir form y hacer submit vacío — estado compartido para los 3 asserts
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/projects/${newProjectId}/issues/`);
    await page.getByRole("button", { name: "Add work item" }).waitFor({ state: "visible", timeout: 10000 });
    urlBefore = page.url();
    await page.getByRole("button", { name: "Add work item" }).click();
    await page.getByRole("button", { name: "Save" }).click();
  });

  test("PS-12-a: intentar guardar sin título muestra 'Title is required'", async ({ page }) => {
    await expect(page.getByText("Title is required")).toBeVisible({ timeout: 5000 });
  });

  test("PS-12-b: el formulario permanece abierto tras submit vacío", async ({ page }) => {
    await expect(page.getByRole("button", { name: "Save" })).toBeVisible({ timeout: 5000 });
  });

  test("PS-12-c: la URL no cambia tras submit vacío", async ({ page }) => {
    expect(page.url()).toBe(urlBefore);
  });
});
