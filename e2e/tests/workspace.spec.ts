import { test, expect, backendEnabled, login, mutate, uniqueName } from "../support/api";

test.use({ trace: "off" });
test.describe("Week 2 supplier browser integration", () => {
  test.skip(!backendEnabled, "Blocked: isolated full stack required");

  test("M2-AC1 browser creates draft and reload retrieves persisted supplier", async ({ page }) => {
    await login(page.request, "analyst");
    const name = uniqueName();
    let id: string | undefined;
    try {
      await page.goto("/suppliers");
      await page.getByRole("button", { name: /New Supplier Draft/ }).click();
      await page.getByLabel("Legal Registered Name").fill(name);
      const savedResponse = page.waitForResponse(r => r.url().endsWith("/api/v1/suppliers/") && r.request().method() === "POST");
      await page.getByRole("button", { name: "Save as Draft" }).click();
      const saved = await savedResponse;
      const body = await saved.json();
      id = body.id;
      expect(saved.status()).toBe(201);
      expect(id).toBeTruthy();
      await page.reload();
      await expect(page.getByRole("row").filter({ hasText: name })).toBeVisible();
      const retrieved = await page.request.get(`/api/v1/suppliers/${id}/`);
      expect(retrieved.status()).toBe(200);
      expect(await retrieved.json()).toMatchObject({ id, legal_name: name, record_status: "draft" });
    } finally {
      if (id) expect((await mutate(page.request, "POST", `/api/v1/suppliers/${id}/archive/`)).status()).toBe(200);
    }
  });

  test("M1-AC3 real server 403 surfaces in UI without ending reviewer session", async ({ page }) => {
    const user = await login(page.request, "reviewer");
    await page.goto("/suppliers");
    await page.getByRole("button", { name: /New Supplier Draft/ }).click();
    await page.getByLabel("Legal Registered Name").fill(uniqueName());
    const deniedResponse = page.waitForResponse(r => r.url().endsWith("/api/v1/suppliers/") && r.request().method() === "POST");
    await page.getByRole("button", { name: "Save as Draft" }).click();
    const denied = await deniedResponse;
    expect(denied.status()).toBe(403);
    expect((await denied.json()).code).toBe("permission_denied");
    await expect(page.getByRole("alert").filter({ hasText: "Failed to Create Supplier" })).toContainText(/permission/i);
    await expect(page).toHaveURL(/\/suppliers$/);
    const me = await page.request.get("/api/v1/auth/me/");
    expect(me.status()).toBe(200);
    expect((await me.json()).id).toBe(user.id);
  });
});
