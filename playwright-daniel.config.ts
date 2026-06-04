/**
 * Configuración personal de Playwright — Daniel Salas
 * Ejecutar: npx playwright test --config=playwright-daniel.config.ts
 *
 * Variables de entorno:
 *   PLAYWRIGHT_BASE_URL  → URL base (default: https://makeplane.r-odio.com)
 *   PLANE_WORKSPACE      → slug del workspace (si no se pasa, se extrae del redirect post-login)
 */
import path from "path";
import { defineConfig, devices } from "@playwright/test";

export const STORAGE_STATE = path.join(__dirname, "tests/e2e/daniel/.auth/user.json");
export const WORKSPACE_FILE = path.join(__dirname, "tests/e2e/daniel/.auth/workspace.json");

export default defineConfig({
  testDir: "./tests/e2e/daniel",
  fullyParallel: false,
  forbidOnly: false,
  retries: 0,
  workers: 1,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "https://makeplane.r-odio.com",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: [
    {
      name: "setup",
      testMatch: /auth\.setup\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "daniel",
      testMatch: /test_.*\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        storageState: STORAGE_STATE,
      },
      dependencies: ["setup"],
    },
  ],
});
