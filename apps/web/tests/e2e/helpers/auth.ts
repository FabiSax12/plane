/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import type { Page } from "@playwright/test";

export const USER_EMAIL = process.env.E2E_USER_EMAIL ?? "vargasarayafabian11@gmail.com";
export const USER_PASSWORD = process.env.E2E_USER_PASSWORD ?? "Fabian12Plane*";
export const WORKSPACE_SLUG = process.env.E2E_WORKSPACE_SLUG ?? "test";

export function hasCredentials(): boolean {
  return Boolean(USER_EMAIL && USER_PASSWORD && WORKSPACE_SLUG);
}

export async function signIn(page: Page): Promise<void> {
  await page.goto("/");
  await page.waitForLoadState("networkidle");

  const pathname = new URL(page.url()).pathname;
  if (pathname !== "/" && !pathname.startsWith("/sign-in")) return;

  await page.getByLabel(/email/i).first().waitFor({ state: "visible", timeout: 10_000 });
  await page.getByLabel(/email/i).first().fill(USER_EMAIL!);
  await page
    .getByRole("button", { name: /continue/i })
    .first()
    .click();

  await page.getByRole("textbox", { name: "Password" }).waitFor({ state: "visible", timeout: 5_000 });
  await page.getByRole("textbox", { name: "Password" }).fill(USER_PASSWORD!);
  await page
    .getByRole("button", { name: /sign in|continue|go to workspace/i })
    .first()
    .click();

  await page.waitForURL(/\/[a-z0-9-]+/i, { timeout: 15_000 });
}
