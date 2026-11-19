import { randomUUID } from "node:crypto";
import { test, expect, backendEnabled, errorBody, mutate, uniqueName } from "../support/api";

test.use({ trace: "off" });
test.describe("M2–M3 registry regression @api", () => {
  test.skip(!backendEnabled, "Blocked: requires synthetic stack and seeded role accounts");

  test("M2-AC1 draft persists with stable ID and appears in search @smoke", async ({ analyst, supplier }) => {
    const response = await analyst.get(`/api/v1/suppliers/${supplier.id}/`);
    expect(response.status()).toBe(200);
    expect(await response.json()).toMatchObject({ id: supplier.id, legal_name: supplier.legal_name, record_status: "draft" });
    const list = await analyst.get("/api/v1/suppliers/", { params: { search: supplier.legal_name } });
    expect(list.status()).toBe(200);
    expect((await list.json()).results).toEqual(expect.arrayContaining([expect.objectContaining({ id: supplier.id })]));
  });

  test("M2-AC1/7 edit persists and stale edit cannot overwrite it", async ({ analyst, supplier }) => {
    const path = `/api/v1/suppliers/${supplier.id}/`;
    const update = await mutate(analyst, "PATCH", path, { trade_name: "QA Updated", version: supplier.version });
    expect(update.status()).toBe(200);
    const saved = await update.json();
    expect(saved.id).toBe(supplier.id);
    expect(saved.version).toBe(supplier.version + 1);
    await errorBody(await mutate(analyst, "PATCH", path, { trade_name: "Stale overwrite", version: supplier.version }), 409, "conflict");
    const persisted = await analyst.get(path);
    expect(persisted.status()).toBe(200);
    expect(await persisted.json()).toMatchObject({ trade_name: "QA Updated", version: saved.version });
  });

  test("M2-AC2 incomplete Complete transition is rejected without changing draft", async ({ analyst, supplier }) => {
    const path = `/api/v1/suppliers/${supplier.id}/`;
    const body = await errorBody(await mutate(analyst, "POST", `${path}complete/`), 400, "validation_error");
    expect(body.field_errors.supplier_type).toBeDefined();
    expect(await (await analyst.get(path)).json()).toMatchObject({ record_status: "draft", version: supplier.version });
  });

  test("M2-AC1/2 complete and archive persist", async ({ analyst, supplier }) => {
    const path = `/api/v1/suppliers/${supplier.id}/`;
    expect((await mutate(analyst, "PATCH", path, { supplier_type: "manufacturer", version: supplier.version })).status()).toBe(200);
    expect((await mutate(analyst, "POST", `${path}complete/`)).status()).toBe(200);
    expect((await (await analyst.get(path)).json()).record_status).toBe("complete");
    expect((await mutate(analyst, "POST", `${path}archive/`)).status()).toBe(200);
    expect((await (await analyst.get(path)).json()).record_status).toBe("archived");
  });

  test("M2-AC3 filters include matching record and exclude wrong country; empty search", async ({ analyst, supplier }) => {
    for (const [country, count] of [["IN", 1], ["CN", 0]] as const) {
      const response = await analyst.get("/api/v1/suppliers/", { params: { search: supplier.legal_name, country, status: "draft" } });
      expect(response.status()).toBe(200);
      expect((await response.json()).results).toHaveLength(count);
    }
    const empty = await analyst.get("/api/v1/suppliers/", { params: { search: uniqueName() } });
    expect(empty.status()).toBe(200);
    expect(await empty.json()).toMatchObject({ count: 0, results: [] });
  });

  for (const role of ["reviewer", "admin"] as const) {
    test(`M1-AC3 ${role} can read but cannot edit, create, archive or delete suppliers`, async ({ reviewer, admin, supplier, analyst }) => {
      const api = role === "reviewer" ? reviewer : admin;
      const path = `/api/v1/suppliers/${supplier.id}/`;
      expect((await api.get(path)).status()).toBe(200);
      const name = uniqueName();
      await errorBody(await mutate(api, "POST", "/api/v1/suppliers/", { legal_name: name, country_of_registration: "IN" }), 403, "permission_denied");
      await errorBody(await mutate(api, "PATCH", path, { legal_name: name, version: supplier.version }), 403, "permission_denied");
      await errorBody(await mutate(api, "POST", `${path}archive/`), 403, "permission_denied");
      await errorBody(await mutate(api, "DELETE", path), 403, "permission_denied");
      expect(await (await analyst.get(path)).json()).toMatchObject({ legal_name: supplier.legal_name, record_status: "draft", version: supplier.version });
      expect((await api.get("/api/v1/auth/me/")).status()).toBe(200);
    });
  }

  for (const role of ["reviewer", "admin"] as const) {
    test(`M1-AC3/M3-AC1 ${role} cannot create or alter product by direct ID`, async ({ reviewer, admin, analyst, supplier }) => {
      const api = role === "reviewer" ? reviewer : admin;
      const payload = { supplier: supplier.id, product_name: uniqueName(), product_category: "rice" };
      const created = await mutate(analyst, "POST", "/api/v1/products/", payload);
      expect(created.status()).toBe(201);
      const product = await created.json();
      const path = `/api/v1/products/${product.id}/`;
      expect((await api.get(path)).status()).toBe(200);
      await errorBody(await mutate(api, "POST", "/api/v1/products/", { ...payload, product_name: uniqueName() }), 403, "permission_denied");
      await errorBody(await mutate(api, "PATCH", path, { product_name: "Denied edit", version: product.version }), 403, "permission_denied");
      expect(await (await analyst.get(path)).json()).toMatchObject({ product_name: product.product_name, version: product.version });
      expect((await api.get("/api/v1/auth/me/")).status()).toBe(200);
    });
  }

  test("M3-AC1/2/3/4 product persists, edits, filters and preserves unknown numbers @smoke", async ({ analyst, supplier }) => {
    const name = uniqueName();
    const created = await mutate(analyst, "POST", "/api/v1/products/", { supplier: supplier.id, product_name: name, product_category: "rice" });
    expect(created.status()).toBe(201);
    const product = await created.json();
    expect(product.supplier).toBe(supplier.id);
    for (const field of ["moq_value", "price_min", "price_max", "capacity_quantity", "lead_time_value"]) expect(product[field]).toBeNull();
    const path = `/api/v1/products/${product.id}/`;
    const updated = await mutate(analyst, "PATCH", path, { product_name_zh: "测试产品", version: product.version });
    expect(updated.status()).toBe(200);
    const saved = await updated.json();
    expect(saved.translation_status).toBe("provided_unreviewed");
    await errorBody(await mutate(analyst, "PATCH", path, { product_name: "Stale", version: product.version }), 409, "conflict");
    expect(await (await analyst.get(path)).json()).toMatchObject({ product_name: name, product_name_zh: "测试产品", version: saved.version });
    const list = await analyst.get("/api/v1/products/", { params: { search: name, supplier_id: supplier.id, category: "rice" } });
    expect(list.status()).toBe(200);
    expect((await list.json()).results).toEqual([expect.objectContaining({ id: product.id })]);
    const empty = await analyst.get("/api/v1/products/", { params: { search: name, category: "spices" } });
    expect((await empty.json()).results).toEqual([]);
  });

  const invalidInputs = [
    ["moq_unit", { moq_value: "1.00" }],
    ["moq_value", { moq_value: "0", moq_unit: "MT" }],
    ["moq_value", { moq_value: "-1", moq_unit: "MT" }],
    ["capacity_unit", { capacity_quantity: "1", capacity_period: "MONTH" }],
    ["capacity_period", { capacity_quantity: "1", capacity_unit: "MT" }],
    ["lead_time_unit", { lead_time_value: 1 }],
    ["price_max", { price_min: "20", price_max: "10", currency: "USD" }],
    ["currency", { price_min: "10", price_max: "20", currency: "INVALID" }],
    ["currency", { price_min: "10", price_max: "20", currency: "" }],
  ] as const;
  for (const [index, [field, data]] of invalidInputs.entries()) {
    test(`M3-AC2 validation ${index + 1}: ${field} rejection creates no product`, async ({ analyst, supplier }) => {
      const name = uniqueName();
      const response = await mutate(analyst, "POST", "/api/v1/products/", { supplier: supplier.id, product_name: name, product_category: "rice", ...data });
      const body = await errorBody(response, 400, "validation_error");
      expect(body.field_errors[field]).toBeDefined();
      const list = await analyst.get("/api/v1/products/", { params: { search: name } });
      expect((await list.json()).results).toEqual([]);
    });
  }

  test("M3-AC2 numeric price requires explicitly supplied currency", async ({ analyst, supplier }) => {
    // Requirement assertion deliberately detects the inspected serializer's USD default.
    const response = await mutate(analyst, "POST", "/api/v1/products/", {
      supplier: supplier.id, product_name: uniqueName(), product_category: "rice", price_min: "10", price_max: "20",
    });
    const body = await errorBody(response, 400, "validation_error");
    expect(body.field_errors.currency).toBeDefined();
  });

  for (const reference of [undefined, "invalid-uuid", randomUUID()]) {
    test(`M3-AC1 rejects ${reference === undefined ? "missing" : reference === "invalid-uuid" ? "malformed" : "nonexistent"} supplier`, async ({ analyst }) => {
      const body = await errorBody(await mutate(analyst, "POST", "/api/v1/products/", {
        supplier: reference, product_name: uniqueName(), product_category: "rice",
      }), 400, "validation_error");
      expect(body.field_errors.supplier).toBeDefined();
    });
  }
});
