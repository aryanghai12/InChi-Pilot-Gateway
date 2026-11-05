import { test, expect } from "@playwright/test";

// TD-09 / ARCHITECTURE.md §7: Next.js serves deep links and unknown UI routes.
test.describe("routing and headers", () => {
  test("refresh on a deep workspace route is served by Next.js", async ({ request }) => {
    const res = await request.get("/suppliers");
    expect(res.status()).toBe(200);
    expect(res.headers()["content-type"]).toContain("text/html");
  });

  test("unknown UI route shows the Next.js not-found page", async ({ page }) => {
    const res = await page.goto("/qa-no-such-page");
    expect(res?.status()).toBe(404);
    await expect(page.getByRole("heading", { name: "Page Not Found" })).toBeVisible();
  });

  test("security headers are set on pages", async ({ request }) => {
    const res = await request.get("/login");
    const headers = res.headers();
    expect(headers["x-content-type-options"]).toBe("nosniff");
    expect(headers["x-frame-options"]).toBe("DENY");
    expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
  });
});
