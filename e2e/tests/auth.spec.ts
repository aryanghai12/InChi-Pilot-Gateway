import { test, expect } from "@playwright/test";

test.describe("M1-AC2 unauthenticated access", () => {
  test("login page renders the sign-in form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel("Email Address")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign In" })).toBeVisible();
  });

  test("workspace route without a session redirects to login", async ({ page }) => {
    // Known defect: the workspace falls back to a hardcoded demo user. Remove
    // test.fail() once QA-001 is fixed (docs/qa/defects.md).
    test.fail(true, "QA-001");
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login\?next=%2Fdashboard/, { timeout: 10_000 });
  });
});
