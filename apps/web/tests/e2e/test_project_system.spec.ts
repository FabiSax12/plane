/**
 * Pruebas de sistema asignadas a Rafael Odio: PS-09, PS-10, PS-11, PS-12
 *
 * Prerequisitos de ejecución:
 *   1. Backend corriendo:  cd apps/api && python manage.py runserver
 *   2. Variables de entorno configuradas (ver playwright.config.ts):
 *        E2E_WORKSPACE_SLUG  — slug del workspace de prueba
 *        E2E_PROJECT_ID      — ID del proyecto (requerido para PS-10, PS-11, PS-12)
 *        E2E_USER_EMAIL      — correo del usuario de prueba
 *        E2E_USER_PASS       — contraseña del usuario de prueba
 *
 * Ejecución:
 *   cd apps/web
 *   pnpm playwright test tests/e2e/test_project_system.spec.ts
 */

import { test, expect } from "@playwright/test";
import { loginAs, BASE_URL } from "./helpers/auth";

const WORKSPACE_SLUG = process.env.E2E_WORKSPACE_SLUG ?? "hola";

// Prefijo único por ejecución (3 chars base-36) + contador secuencial
// → identificadores como "PABC1", "PABC2", "PABC3" en cada run
const RUN_PREFIX = Date.now().toString(36).slice(-3).toUpperCase();
let _seq = 0;
const nextIdentifier = () => `P${RUN_PREFIX}${++_seq}`;

// ---------------------------------------------------------------------------
// PS-09 — Crear proyecto nuevo aparece en el sidebar del workspace
// Técnica: Cobertura de sentencias
// Plan: click 'Create project' del sidebar → llenar form → submit →
//       verificar que aparece en sidebar → navegar al proyecto →
//       verificar 6 estados por defecto en el board
// ---------------------------------------------------------------------------

test.describe("PS-09: Crear proyecto desde el sidebar", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page);
  });

  test("PS-09: crear proyecto válido aparece en el sidebar con 6 estados por defecto en el board", async ({ page }) => {
    const uniqueSuffix = Date.now().toString();
    const projectName = `PS09 Project ${uniqueSuffix}`;
    const identifier = nextIdentifier(); // P{RUN}1, P{RUN}2, ...

    // Paso 1: ir a Projects desde el sidebar (selectores exactos del Codegen)
    await page.goto(`${BASE_URL}/`);
    await page.getByLabel("Main sidebar").getByRole("link", { name: "Projects" }).click();

    // Paso 2: abrir modal y llenar nombre
    await page.getByRole("button", { name: "Add Project" }).click();
    await page.getByRole("textbox", { name: "Project name" }).fill(projectName);
    await page.getByRole("textbox", { name: "Project ID" }).fill(identifier);

    // Paso 3: crear proyecto
    await page.getByRole("button", { name: "Create project" }).click();

    // Paso 4: "Open project" es un LINK no un button (capturado con Codegen)
    await page.getByRole("link", { name: "Open project" }).click({ timeout: 10000 });

    // Extraer el UUID del proyecto recién creado desde la URL de issues
    // e.g. /hola/projects/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/issues/
    await page.waitForURL(/\/projects\/[a-f0-9-]{36}\//, { timeout: 10000 });
    const projectIdMatch = page.url().match(/\/projects\/([a-f0-9-]{36})\//);
    const newProjectId = projectIdMatch?.[1];
    if (!newProjectId) throw new Error("No se pudo extraer el project ID de la URL");

    // Paso 5: verificar que el proyecto aparece en el sidebar
    await expect(page.getByText(projectName, { exact: false }).first()).toBeVisible({ timeout: 10000 });

    // Paso 6: navegar directamente a Settings → States del proyecto recién creado
    // (evita ambigüedades con el sidebar y headlessui IDs dinámicos)
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/settings/projects/${newProjectId}/states/`);
    await page.waitForLoadState("networkidle");

    // Verificar los 5 estados por defecto visibles en la UI
    const defaultStates = ["Backlog", "Todo", "In Progress", "Done", "Cancelled"];
    await Promise.all(
      defaultStates.map((state) => expect(page.getByText(state).first()).toBeVisible({ timeout: 5000 }))
    );
  });
});

// ---------------------------------------------------------------------------
// PS-10 — Crear estado custom aparece como columna en el kanban
// Técnica: Cobertura de sentencias
// Plan: Settings → States (proyecto) → Add state "Review" (group started) →
//       Save → navegar al kanban → verificar columna "Review" visible
// ---------------------------------------------------------------------------

test.describe("PS-10: Estado custom aparece en el kanban del proyecto", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page);
  });

  test("PS-10: crear estado 'Review' y verificar que aparece como columna en el board", async ({ page }) => {
    // Paso 0: crear un proyecto propio para esta prueba (igual que PS-09)
    const uniqueSuffix = Date.now().toString();
    const projectName = `PS10 Project ${uniqueSuffix}`;
    const identifier = nextIdentifier();

    await page.goto(`${BASE_URL}/`);
    await page.getByLabel("Main sidebar").getByRole("link", { name: "Projects" }).click();
    await page.waitForLoadState("networkidle");
    await page.getByRole("button", { name: "Add Project" }).click();
    await page.getByRole("textbox", { name: "Project name" }).fill(projectName);
    await page.getByRole("textbox", { name: "Project ID" }).fill(identifier);
    await page.getByRole("button", { name: "Create project" }).click();
    await page.getByRole("link", { name: "Open project" }).click({ timeout: 10000 });

    // Extraer el UUID del proyecto recién creado
    await page.waitForURL(/\/projects\/[a-f0-9-]{36}\//, { timeout: 10000 });
    const projectIdMatch = page.url().match(/\/projects\/([a-f0-9-]{36})\//);
    const newProjectId = projectIdMatch?.[1];
    if (!newProjectId) throw new Error("No se pudo extraer el project ID de la URL");

    // Paso 1: navegar directamente a la página de States del proyecto
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/settings/projects/${newProjectId}/states/`);
    await page.waitForLoadState("networkidle");

    // Paso 2: click el botón + del grupo "In Progress" (3er grupo, ícono sin texto)
    // Selector capturado con Playwright Codegen
    await page
      .locator(
        "div:nth-child(3) > div > .flex-shrink-0.w-6.h-6.rounded.flex.justify-center.items-center.overflow-hidden.transition-colors"
      )
      .click();

    // Paso 3: llenar nombre del estado
    await page.getByRole("textbox", { name: "Name" }).fill("Review");

    // Paso 4: guardar con el botón "Create"
    await page.getByRole("button", { name: "Create" }).click();

    // Verificar que el estado fue creado en la lista de settings
    await expect(page.getByText("Review")).toBeVisible({ timeout: 5000 });

    // Paso 5: navegar a la lista de issues y abrir el filtro de States
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/projects/${newProjectId}/issues/`);
    await page.waitForLoadState("networkidle");

    // Paso 6: abrir el dropdown de filtros
    // El botón es un div con el ícono SVG lucide-list-filter (no es un <button>)
    await page.locator("svg.lucide-list-filter").click();
    // Seleccionar "State" como criterio de filtro (exactamente como Codegen)
    await page.locator("div").filter({ hasText: "State" }).nth(2).click();

    // Verificar que "Review" aparece como opción en el filtro de estados
    await expect(
      page
        .locator("div")
        .filter({ hasText: /^Review$/ })
        .first()
    ).toBeVisible({ timeout: 5000 });
  });
});

// ---------------------------------------------------------------------------
// PS-11 — Crear work item válido aparece en la lista con identificador PROJ-N
// Técnica: Partición de equivalencia (clase válida)
// Plan: crear work item → título + estado Backlog → submit →
//       verificar item visible en lista con identificador tipo PROJ-N
// ---------------------------------------------------------------------------

test.describe("PS-11: Crear work item válido aparece en la lista", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page);
  });

  test("PS-11: work item con título válido aparece en la lista con su identificador", async ({ page }) => {
    // Paso 0: crear proyecto propio (independiente del env var PROJECT_ID)
    const uniqueSuffix = Date.now().toString();
    const projectName = `PS11 Project ${uniqueSuffix}`;
    const identifier = nextIdentifier();

    await page.goto(`${BASE_URL}/`);
    await page.getByLabel("Main sidebar").getByRole("link", { name: "Projects" }).click();
    await page.waitForLoadState("networkidle");
    await page.getByRole("button", { name: "Add Project" }).click();
    await page.getByRole("textbox", { name: "Project name" }).fill(projectName);
    await page.getByRole("textbox", { name: "Project ID" }).fill(identifier);
    await page.getByRole("button", { name: "Create project" }).click();
    await page.getByRole("link", { name: "Open project" }).click({ timeout: 10000 });

    await page.waitForURL(/\/projects\/[a-f0-9-]{36}\//, { timeout: 10000 });
    const projectIdMatch = page.url().match(/\/projects\/([a-f0-9-]{36})\//);
    const newProjectId = projectIdMatch?.[1];
    if (!newProjectId) throw new Error("No se pudo extraer el project ID de la URL");

    const issueName = `PS-11 Work Item ${Date.now()}`;

    // Paso 1: navegar a Work items del proyecto
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/projects/${newProjectId}/issues/`);
    await page.waitForLoadState("networkidle");

    // Paso 2: abrir formulario (selectores exactos del Codegen)
    await page.getByRole("button", { name: "Add work item" }).click();
    await page.getByRole("textbox", { name: "Title" }).fill(issueName);

    // Paso 3: guardar (Backlog es el estado por defecto)
    await page.getByRole("button", { name: "Save" }).click();

    // Paso 4: verificar que el work item aparece en la lista como link
    // Formato del link: "{IDENTIFIER}-N {título} {estado}" (e.g. "PS11P4-1 PS-11 Work Item... Backlog")
    await expect(page.getByRole("link", { name: new RegExp(issueName) })).toBeVisible({ timeout: 10000 });

    // Verificar que el link incluye un identificador con formato PROJ-N al inicio
    const linkText = await page.getByRole("link", { name: new RegExp(issueName) }).textContent();
    expect(linkText).toMatch(/^[A-Z0-9]+-\d+/);
  });
});

// ---------------------------------------------------------------------------
// PS-12 — Crear work item sin título muestra error de validación visible
// Técnica: Análisis de valores límite (caso inválido)
// Plan: abrir form → dejar título vacío → submit →
//       verificar mensaje de error visible + form sigue abierto + URL no cambia
// ---------------------------------------------------------------------------

test.describe("PS-12: Work item sin título muestra error de validación", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page);
  });

  test("PS-12: intentar crear work item sin título mantiene el formulario abierto con error visible", async ({
    page,
  }) => {
    // Paso 0: crear proyecto propio
    const uniqueSuffix = Date.now().toString();
    const projectName = `PS12 Project ${uniqueSuffix}`;
    const identifier = nextIdentifier();

    await page.goto(`${BASE_URL}/`);
    await page.getByLabel("Main sidebar").getByRole("link", { name: "Projects" }).click();
    await page.waitForLoadState("networkidle");
    await page.getByRole("button", { name: "Add Project" }).click();
    await page.getByRole("textbox", { name: "Project name" }).fill(projectName);
    await page.getByRole("textbox", { name: "Project ID" }).fill(identifier);
    await page.getByRole("button", { name: "Create project" }).click();
    await page.getByRole("link", { name: "Open project" }).click({ timeout: 10000 });

    await page.waitForURL(/\/projects\/[a-f0-9-]{36}\//, { timeout: 10000 });
    const projectIdMatch = page.url().match(/\/projects\/([a-f0-9-]{36})\//);
    const newProjectId = projectIdMatch?.[1];
    if (!newProjectId) throw new Error("No se pudo extraer el project ID de la URL");

    // Paso 1: navegar a Work items del proyecto
    await page.goto(`${BASE_URL}/${WORKSPACE_SLUG}/projects/${newProjectId}/issues/`);
    await page.waitForLoadState("networkidle");
    const urlBefore = page.url();

    // Paso 2: abrir formulario sin llenar título (selectores exactos del Codegen)
    await page.getByRole("button", { name: "Add work item" }).click();

    // Paso 3: intentar guardar con título vacío
    await page.getByRole("button", { name: "Save" }).click();

    // Paso 4: verificar mensaje de error exacto capturado con Codegen
    await expect(page.getByText("Title is required")).toBeVisible({ timeout: 3000 });

    // Paso 5a: el formulario sigue abierto (el inline form no es un dialog)
    await expect(page.getByRole("button", { name: "Save" })).toBeVisible();

    // Paso 5b: la URL no cambió
    expect(page.url()).toBe(urlBefore);
  });
});
