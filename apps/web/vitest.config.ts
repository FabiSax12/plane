import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: [
      "tests/unit/**/*.test.ts",
      "tests/unit/**/*.test.tsx",
      "tests/unit/**/*.spec.ts",
      "tests/unit/**/*.spec.tsx",
    ],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: ["app/**/*.ts", "app/**/*.tsx", "core/**/*.ts", "core/**/*.tsx", "helpers/**/*.ts"],
      exclude: ["app/**/*.d.ts", "core/**/*.d.ts", "app/types/**"],
    },
    pool: "threads",
    poolOptions: {
      threads: {
        minThreads: 1,
        maxThreads: 2,
      },
    },
    testTimeout: 20000,
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./core"),
      "@/plane-web": path.resolve(__dirname, "./ce"),
      "@plane/constants": path.resolve(__dirname, "../../packages/constants/src/index.ts"),
      "@plane/types": path.resolve(__dirname, "../../packages/types/src/index.ts"),
      "@plane/utils": path.resolve(__dirname, "../../packages/utils/src/index.ts"),
      "@plane/services": path.resolve(__dirname, "../../packages/services/src/index.ts"),
    },
  },
});
