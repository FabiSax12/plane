/**
 * auth.setup.ts — Autenticación compartida para pruebas de sistema
 * Daniel Salas · PS-13 a PS-16
 *
 * Ejecuta una sola vez antes de todos los specs (proyecto "setup").
 * Guarda:
 *   - storageState (cookies/localStorage) → .auth/user.json
 *   - workspace slug extraído del redirect → .auth/workspace.json
 */
import fs from "fs";
import path from "path";
import { test as setup } from "@playwright/test";
import { STORAGE_STATE, WORKSPACE_FILE } from "../../../playwright-daniel.config";

const EMAIL = "salasdaniel@gmail.com";
const PASSWORD = "#Plane1234";

setup("authenticate as Daniel Salas", async ({ page }) => {
  // 1. Navegar a la raíz; si no está autenticado redirige al formulario de login
  await page.goto("/");

  // 2. Esperar a que aparezca el input de email (login form)
  //    Plane muestra el formulario en la misma ruta "/"
  const emailInput = page.locator('input[type="email"]');
  await emailInput.waitFor({ state: "visible", timeout: 15_000 });

  // 3. Paso 1: ingresar email y continuar
  await emailInput.fill(EMAIL);
  await page.locator('button[type="submit"]').first().click();

  // 4. Paso 2: ingresar password y continuar
  const passwordInput = page.locator('input[type="password"]');
  await passwordInput.waitFor({ state: "visible", timeout: 10_000 });
  await passwordInput.fill(PASSWORD);
  await page.locator('button[type="submit"]').first().click();

  // 5. Plane es una SPA: tras el login puede no cambiar la URL.
  //    Esperar a que aparezca un link de proyecto en el sidebar como indicador
  //    de que el workspace cargó correctamente.
  await page.waitForSelector('a[href*="/projects/"]', { timeout: 30_000 });

  // 6. Extraer el workspace slug desde el href del primer link de proyecto.
  //    Formato del href: "/{workspaceSlug}/projects/{projectId}/..."
  let workspaceSlug = process.env.PLANE_WORKSPACE;
  if (!workspaceSlug) {
    const firstProjectLink = page.locator('a[href*="/projects/"]').first();
    const href = await firstProjectLink.getAttribute("href");
    workspaceSlug = href?.split("/").find(Boolean);
  }

  if (!workspaceSlug) {
    throw new Error("No se pudo extraer el workspace slug. Verifica que la cuenta tiene al menos un proyecto.");
  }

  // 7. Persistir workspace slug para que los specs lo lean
  const authDir = path.dirname(WORKSPACE_FILE);
  fs.mkdirSync(authDir, { recursive: true });
  fs.writeFileSync(WORKSPACE_FILE, JSON.stringify({ workspaceSlug }, null, 2));

  // 8. Persistir sesión (cookies + localStorage)
  await page.context().storageState({ path: STORAGE_STATE });

  console.log(`✓ Autenticado. Workspace: ${workspaceSlug}`);
});
