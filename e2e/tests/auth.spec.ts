import { test, expect } from "@playwright/test";

test.describe("M1-AC2 unauthenticated access @smoke", () => {
  test("login page renders the sign-in form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel("Email Address")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign In" })).toBeVisible();
  });

  test("workspace route without a session redirects to login", async ({ page }) => {
    // QA-001 remains a release-visible failure until the product owner fixes it.
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login\?next=%2Fdashboard/, { timeout: 10_000 });
  });

  for (const path of ["/suppliers", "/products", "/readiness", "/requirements", "/matching", "/opportunities", "/audit"]) {
    test(`M1-AC2 anonymous ${path} redirects to login`, async ({ page }) => {
      await page.goto(path);
      await expect(page).toHaveURL(url => url.pathname === "/login" && url.searchParams.get("next") === path, { timeout: 10_000 });
    });
  }
});
