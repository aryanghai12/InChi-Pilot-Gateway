import { test, expect } from "@playwright/test";

// These go through the Next.js /api/ rewrite to Django, so they need the backend.
// Run with E2E_BACKEND=1 against the Compose stack.
test.describe("API contract through the proxy", () => {
  test.skip(!process.env.E2E_BACKEND, "Backend not available (set E2E_BACKEND=1)");

  test("M1-AC2: absent session returns 401 not_authenticated", async ({ request }) => {
    const res = await request.get("/api/v1/auth/me/");
    expect(res.status()).toBe(401);
    expect((await res.json()).code).toBe("not_authenticated");
  });

  test("M1-AC3 / TD-05: login without a CSRF token is rejected", async ({ request }) => {
    // Synthetic, non-existent account: the request must fail on CSRF before any credential check.
    const res = await request.post("/api/v1/auth/login/", {
      data: { email: "qa.no-such-user@example.test", password: "not-a-real-password" },
    });
    expect(res.status()).toBe(403);
    expect((await res.json()).code).toBe("csrf_failed");
  });

  test("TD-09: unknown /api/ path returns Django's JSON 404", async ({ request }) => {
    const res = await request.get("/api/v1/qa-no-such-endpoint/");
    expect(res.status()).toBe(404);
    expect(res.headers()["content-type"]).toContain("application/json");
  });
});
