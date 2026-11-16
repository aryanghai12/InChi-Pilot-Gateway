import { randomUUID } from "node:crypto";
import { test, expect, backendEnabled, csrf, errorBody, login, mutate } from "../support/api";

test.use({ trace: "off" }); // API traces can contain login credentials and session cookies.
test.describe("M1 session regression @api @smoke", () => {
  test.skip(!backendEnabled, "Blocked: set E2E_BACKEND=1 against a synthetic test stack");

  for (const path of ["/api/v1/auth/me/", "/api/v1/suppliers/", "/api/v1/products/", "/api/v1/evidence/"]) {
    test(`M1-AC2 absent session denied: ${path}`, async ({ request }) => {
      await errorBody(await request.get(path), 401, "not_authenticated");
    });
  }

  test("M1-AC2 invalid session is rejected", async ({ request }) => {
    const response = await request.get("/api/v1/auth/me/", {
      headers: { Cookie: `sessionid=${randomUUID()}` },
    });
    await errorBody(response, 401, "not_authenticated");
  });

  test("M1-AC3 CSRF bootstrap and invalid token rejection", async ({ request }) => {
    await csrf(request);
    const response = await request.post("/api/v1/auth/login/", {
      headers: { "X-CSRFToken": "invalid" },
      data: { email: "qa-absent@example.test", password: randomUUID() },
    });
    await errorBody(response, 403, "csrf_failed");
    expect((await request.storageState()).cookies.some(c => c.name === "sessionid")).toBe(false);
  });

  test("M1-AC2 invalid credentials with valid CSRF create no session", async ({ request }) => {
    const token = await csrf(request);
    await errorBody(await request.post("/api/v1/auth/login/", {
      headers: { "X-CSRFToken": token },
      data: { email: `qa-${randomUUID()}@example.test`, password: randomUUID() },
    }), 400, "validation_error");
    await errorBody(await request.get("/api/v1/auth/me/"), 401, "not_authenticated");
  });

  // Restricted security coverage is maintained separately and excluded from public delivery.

  for (const role of ["analyst", "reviewer", "admin"] as const) {
    test(`M1-AC1 ${role} login rotates CSRF and issues protected session cookie`, async ({ request }) => {
      const before = await csrf(request);
      await login(request, role);
      const cookies = (await request.storageState()).cookies;
      const session = cookies.find(c => c.name === "sessionid");
      expect(session).toBeDefined();
      expect(session!.httpOnly).toBe(true);
      expect(session!.sameSite).toBe("Lax");
      expect(cookies.find(c => c.name === "csrftoken")!.value !== before, "CSRF token rotates without logging its value").toBe(true);
    });
  }

  test("M1-AC2 logout revokes session including replay of the old cookie", async ({ analyst, playwright, baseURL }) => {
    const oldState = await analyst.storageState();
    expect((await mutate(analyst, "POST", "/api/v1/auth/logout/")).status()).toBe(200);
    await errorBody(await analyst.get("/api/v1/auth/me/"), 401, "not_authenticated");
    const replay = await playwright.request.newContext({ baseURL, storageState: oldState });
    try { await errorBody(await replay.get("/api/v1/auth/me/"), 401, "not_authenticated"); }
    finally { await replay.dispose(); }
  });

  test("M1-AC3 analyst denied user administration retains session", async ({ analyst }) => {
    const before = await (await analyst.get("/api/v1/auth/me/")).json();
    await errorBody(await analyst.get("/api/v1/auth/users/"), 403, "permission_denied");
    const after = await analyst.get("/api/v1/auth/me/");
    expect(after.status()).toBe(200);
    expect((await after.json()).id).toBe(before.id);
  });
});
