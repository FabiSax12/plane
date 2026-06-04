import { defineConfig, devices } from "@playwright/test";

/**
 * Configuración de Playwright para pruebas de sistema (PS-*).
 * Requiere que el servidor esté corriendo en http://localhost:3000
 * y el backend Django en http://localhost:8000.
 *
 * Configurar variables de entorno antes de ejecutar:
 *   E2E_BASE_URL   — URL del frontend (default: http://localhost:3000)
 *   E2E_USER_EMAIL — correo del usuario de prueba
 *   E2E_USER_PASS  — contraseña del usuario de prueba
 */

export default defineConfig({
  testDir: "./tests/e2e/Rafael",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 2,
  workers: 1,
  reporter: [["html", { outputFolder: "playwright-report" }], ["list"]],

  timeout: 120000,

  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
