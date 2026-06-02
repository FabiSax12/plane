import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["tests/**/*.test.ts", "tests/**/*.test.tsx", "tests/**/*.spec.ts", "tests/**/*.spec.tsx"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: ["app/**/*.ts", "app/**/*.tsx", "core/**/*.ts", "core/**/*.tsx", "helpers/**/*.ts"],
      exclude: ["app/**/*.d.ts", "core/**/*.d.ts", "app/types/**"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./core"),
    },
  },
});
