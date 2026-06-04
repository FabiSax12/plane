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
import { test as setup, expect } from "@playwright/test";
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

  // 5. Esperar redirect al workspace (URL con al menos un segmento después del host)
  await page.waitForURL(/\/[^/]+\//, { timeout: 30_000 });

  // 6. Extraer el workspace slug de la URL resultante
  const workspaceSlug =
    process.env.PLANE_WORKSPACE ??
    new URL(page.url()).pathname.split("/").filter(Boolean)[0];

  // 7. Persistir workspace slug para que los specs lo lean
  const authDir = path.dirname(WORKSPACE_FILE);
  fs.mkdirSync(authDir, { recursive: true });
  fs.writeFileSync(WORKSPACE_FILE, JSON.stringify({ workspaceSlug }, null, 2));

  // 8. Persistir sesión (cookies + localStorage)
  await page.context().storageState({ path: STORAGE_STATE });

  console.log(`✓ Autenticado. Workspace: ${workspaceSlug}`);
});
