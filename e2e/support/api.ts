import { randomUUID } from "node:crypto";
import { test as base, expect, APIRequestContext, APIResponse } from "@playwright/test";

export type Role = "analyst" | "reviewer" | "admin";
export const backendEnabled = process.env.E2E_BACKEND === "1";
export const uniqueName = () => `QA-${randomUUID()}`;

export function credentials(role: Role) {
  const prefix = `E2E_${role.toUpperCase()}`;
  const email = process.env[`${prefix}_EMAIL`];
  const password = process.env[`${prefix}_PASSWORD`];
  if (!email || !password) throw new Error(`Set ${prefix}_EMAIL and ${prefix}_PASSWORD for synthetic test accounts`);
  return { email, password };
}

export async function csrf(api: APIRequestContext) {
  const response = await api.get("/api/v1/auth/csrf/");
  expect(response.status()).toBe(200);
  const cookie = (await api.storageState()).cookies.find(c => c.name === "csrftoken");
  expect(cookie, "CSRF bootstrap must issue a cookie").toBeDefined();
  return cookie!.value;
}

export async function login(api: APIRequestContext, role: Role) {
  const token = await csrf(api);
  const response = await api.post("/api/v1/auth/login/", {
    headers: { "X-CSRFToken": token }, data: credentials(role),
  });
  // Do not attach credentials or response bodies to execution reports.
  expect(response.status(), `Synthetic ${role} login`).toBe(200);
  const me = await api.get("/api/v1/auth/me/");
  expect(me.status()).toBe(200);
  const user = await me.json();
  expect(user.role).toBe({ analyst: "commercial_analyst", reviewer: "reviewer", admin: "platform_admin" }[role]);
  return user;
}

export async function mutate(api: APIRequestContext, method: "POST" | "PATCH" | "DELETE", path: string, data: unknown = {}) {
  const cookie = (await api.storageState()).cookies.find(c => c.name === "csrftoken");
  expect(cookie, "Authenticate/bootstrap before mutating requests").toBeDefined();
  return api.fetch(path, { method, headers: { "X-CSRFToken": cookie!.value }, data });
}

export async function errorBody(response: APIResponse, status: number, code: string) {
  expect(response.status()).toBe(status);
  expect(response.headers()["content-type"]).toContain("application/json");
  const body = await response.json();
  expect(body.code).toBe(code);
  return body;
}

type Fixtures = {
  analyst: APIRequestContext;
  reviewer: APIRequestContext;
  admin: APIRequestContext;
  supplier: { id: string; legal_name: string; version: number };
};

export const test = base.extend<Fixtures>({
  analyst: async ({ playwright, baseURL }, use) => {
    const api = await playwright.request.newContext({ baseURL });
    try { await login(api, "analyst"); await use(api); } finally { await api.dispose(); }
  },
  reviewer: async ({ playwright, baseURL }, use) => {
    const api = await playwright.request.newContext({ baseURL });
    try { await login(api, "reviewer"); await use(api); } finally { await api.dispose(); }
  },
  admin: async ({ playwright, baseURL }, use) => {
    const api = await playwright.request.newContext({ baseURL });
    try { await login(api, "admin"); await use(api); } finally { await api.dispose(); }
  },
  supplier: async ({ analyst }, use) => {
    const response = await mutate(analyst, "POST", "/api/v1/suppliers/", {
      legal_name: uniqueName(), country_of_registration: "IN",
    });
    expect(response.status()).toBe(201);
    const record = await response.json();
    try { await use(record); } finally {
      // No hard-delete contract: archive only this test's own synthetic supplier.
      const cleanup = await mutate(analyst, "POST", `/api/v1/suppliers/${record.id}/archive/`);
      expect(cleanup.status(), "Archive synthetic supplier after test").toBe(200);
    }
  },
});
export { expect };
