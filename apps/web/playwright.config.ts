import { defineConfig } from "@playwright/test";
import { config } from "dotenv";
import { fileURLToPath } from "url";
import path from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

config({ path: path.resolve(__dirname, ".env.e2e") });

export default defineConfig({
  testDir: "./e2e/jairo",
  testMatch: "**/*.spec.ts",
  timeout: 30000,
  retries: 0,
  use: {
    baseURL: "https://makeplane.r-odio.com",
    headless: true,
    screenshot: "only-on-failure",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
