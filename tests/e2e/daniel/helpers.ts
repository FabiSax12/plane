/**
 * helpers.ts — Utilidades compartidas para specs de Daniel Salas
 */
import fs from "fs";
import type { Page } from "@playwright/test";
import { WORKSPACE_FILE } from "../../../playwright-daniel.config";

/** Lee el workspace slug guardado por auth.setup.ts */
export function readWorkspaceSlug(): string {
  if (process.env.PLANE_WORKSPACE) return process.env.PLANE_WORKSPACE;
  const raw = fs.readFileSync(WORKSPACE_FILE, "utf-8");
  const { workspaceSlug } = JSON.parse(raw) as { workspaceSlug: string };
  return workspaceSlug;
}

/**
 * Navega al listado de issues del primer proyecto disponible.
 * Hace clic en el primer enlace de proyecto en el sidebar y luego en "Issues".
 * Retorna el workspaceSlug para uso posterior.
 */
export async function navigateToFirstProjectIssues(page: Page): Promise<string> {
  const workspaceSlug = readWorkspaceSlug();
  await page.goto(`/${workspaceSlug}`);
  // Esperar a que el sidebar cargue (links de proyectos en la barra lateral)
  await page.waitForSelector('[href*="/projects/"]', { timeout: 15_000 });
  // Obtener el primer enlace de proyecto con "/issues" en el href
  const issuesLink = page
    .locator('[href*="/projects/"][href*="/issues"]')
    .first();
  const href = await issuesLink.getAttribute("href");
  await page.goto(href!);
  // Esperar a que la lista de issues cargue
  await page.waitForURL(/\/projects\/.*\/issues/, { timeout: 15_000 });
  return workspaceSlug;
}
