"use client";

import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import styles from "./products.module.css";
import { apiFetch } from "@/lib/api/client";
import {
  Product,
  ProductRequest,
  ProductCategory,
  TranslationStatus,
  Supplier,
  PaginatedProductList,
  PaginatedSupplierList,
  unwrapPaginated,
  ApiError,
} from "@/lib/api/types";
import { Button } from "@/components/forms/Button";
import { FormField } from "@/components/forms/FormField";
import { Input } from "@/components/forms/Input";
import { Select } from "@/components/forms/Select";
import { Textarea } from "@/components/forms/Textarea";
import { EmptyState } from "@/components/feedback/EmptyState";
import { AlertBanner } from "@/components/feedback/AlertBanner";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

// 7 Top-Level Working Categories defined in Lean Field Dictionary / Buyer Dictionary v1.2
const PRODUCT_CATEGORIES: ProductCategory[] = [
  "Agriculture and Food",
  "Textiles",
  "Engineering Goods",
  "Electronic Goods",
  "Chemicals",
  "Minerals & Metals",
  "Marine Products",
];

export default function ProductsPage() {
  const queryClient = useQueryClient();

  // Search & Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("All");
  const [translationFilter, setTranslationFilter] = useState<string>("All");

  // Local state (Clean zero-state)
  const [localProducts, setLocalProducts] = useState<(Product & { supplier_name?: string })[]>([]);

  // Modals
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<(Product & { supplier_name?: string }) | null>(null);

  // Notifications
  const [notification, setNotification] = useState<{
    type: "success" | "warning" | "error";
    title?: string;
    message: string;
  } | null>(null);

  // Dynamic Query for registered suppliers (unwraps paginated or raw list)
  const { data: suppliers = [] } = useQuery<Supplier[]>({
    queryKey: ["suppliers"],
    queryFn: async () => {
      try {
        const res = await apiFetch<Supplier[] | PaginatedSupplierList>("/api/v1/suppliers/");
        return unwrapPaginated(res).map((s) => ({
          ...s,
          supplier_id: s.id || s.supplier_id || "",
        }));
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return [];
        throw err;
      }
    },
    staleTime: 30 * 1000,
    retry: false,
  });

  // Form State for New Product
  const [formData, setFormData] = useState({
    supplier_id: "",
    product_name: "",
    product_category: PRODUCT_CATEGORIES[0],
    description: "",
    specifications: "",
    origin: "India",
    minimum_order_quantity: "",
    minimum_order_unit: "pieces",
    indicative_price_min: "",
    indicative_price_max: "",
    currency: "USD",
    price_basis: "FOB",
    lead_time_value: "",
    lead_time_unit: "days",
    product_name_zh: "",
    short_description_zh: "",
  });

  // Backend Mutation: POST /api/v1/products/
  const createProductMutation = useMutation({
    mutationFn: (payload: ProductRequest) =>
      apiFetch<Product>("/api/v1/products/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (newProduct) => {
      queryClient.invalidateQueries({ queryKey: ["all_products"] });
      setNotification({
        type: "success",
        title: "Product Synchronized",
        message: `"${newProduct.product_name}" successfully recorded in the backend catalogue.`,
      });
    },
    onError: (err) => {
      // Keep optimistic local copy with warning banner if backend is unavailable
      if (err instanceof ApiError && err.status !== 404) {
        setNotification({
          type: "warning",
          title: "Product Saved Locally",
          message: `Backend validation notice: ${err.message}`,
        });
      }
    },
  });

  // Backend Query: GET /api/v1/products/ (supports paginated results)
  const { data: remoteProducts, isLoading } = useQuery<Product[]>({
    queryKey: ["all_products"],
    queryFn: async () => {
      try {
        const res = await apiFetch<Product[] | PaginatedProductList>("/api/v1/products/");
        return unwrapPaginated(res).map((p) => ({
          ...p,
          product_id: p.id || p.product_id || "",
          supplier_id: p.supplier || p.supplier_id || "",
          minimum_order_quantity: p.moq_value ? Number(p.moq_value) : p.minimum_order_quantity,
          minimum_order_unit: p.moq_unit || p.minimum_order_unit || "pieces",
          indicative_price_min: p.price_min ? Number(p.price_min) : p.indicative_price_min,
          indicative_price_max: p.price_max ? Number(p.price_max) : p.indicative_price_max,
        }));
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return [];
        throw err;
      }
    },
    retry: false,
  });

  const products = remoteProducts && remoteProducts.length > 0 ? remoteProducts : localProducts;

  // Filtered Products (Case-insensitive matching for OpenAPI enum compatibility)
  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      const matchSearch =
        p.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (p.product_name_zh && p.product_name_zh.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (p.id && p.id.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (p.product_id && p.product_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
        p.product_category.toLowerCase().includes(searchTerm.toLowerCase());

      const matchCategory = categoryFilter === "All" || p.product_category === categoryFilter;

      const trans = p.translation_status.toLowerCase();
      const matchTrans =
        translationFilter === "All" ||
        trans === translationFilter.toLowerCase() ||
        (translationFilter === "Reviewed" && (trans === "reviewed")) ||
        (translationFilter === "Provided – unreviewed" && (trans === "provided_unreviewed" || trans === "provided – unreviewed")) ||
        (translationFilter === "Not provided" && (trans === "not_provided" || trans === "not provided"));

      return matchSearch && matchCategory && matchTrans;
    });
  }, [products, searchTerm, categoryFilter, translationFilter]);

  // Stats
  const stats = useMemo(() => {
    const total = products.length;
    const reviewed = products.filter((p) => {
      const t = p.translation_status.toLowerCase();
      return t === "reviewed";
    }).length;
    const unreviewed = products.filter((p) => {
      const t = p.translation_status.toLowerCase();
      return t === "provided_unreviewed" || t === "provided – unreviewed";
    }).length;
    const missing = products.filter((p) => {
      const t = p.translation_status.toLowerCase();
      return t === "not_provided" || t === "not provided";
    }).length;
    return { total, reviewed, unreviewed, missing };
  }, [products]);

  const isAnyFilterActive = Boolean(
    searchTerm.trim() || categoryFilter !== "All" || translationFilter !== "All"
  );

  const handleResetFilters = () => {
    setSearchTerm("");
    setCategoryFilter("All");
    setTranslationFilter("All");
  };

  const handleCreateProduct = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.product_name.trim()) {
      setNotification({
        type: "error",
        title: "Validation Error",
        message: "Product name is required.",
      });
      return;
    }

    const supplier = suppliers.find((s) => (s.id || s.supplier_id) === formData.supplier_id);
    const newId = `PRD-2026-${String(localProducts.length + 1).padStart(3, "0")}`;
    const supplierId = supplier?.id || supplier?.supplier_id || formData.supplier_id || `SUP-${Date.now()}`;
    const supplierName = supplier?.legal_name || "Registered Supplier";

    let transStatus: TranslationStatus = "not_provided";
    if (formData.product_name_zh.trim() || formData.short_description_zh.trim()) {
      transStatus = "provided_unreviewed";
    }

    const payload: ProductRequest = {
      supplier: supplierId,
      product_name: formData.product_name.trim(),
      product_category: formData.product_category,
      description: formData.description.trim() || undefined,
      specifications: formData.specifications.trim() || undefined,
      origin: formData.origin.trim() || undefined,
      moq_value: formData.minimum_order_quantity ? String(formData.minimum_order_quantity) : null,
      moq_unit: (formData.minimum_order_unit || "PIECES").toUpperCase(),
      price_min: formData.indicative_price_min ? String(formData.indicative_price_min) : null,
      price_max: formData.indicative_price_max ? String(formData.indicative_price_max) : null,
      currency: formData.currency || "USD",
      price_basis: formData.price_basis || "FOB",
      lead_time_value: formData.lead_time_value ? Number(formData.lead_time_value) : null,
      lead_time_unit: "DAYS",
      product_name_zh: formData.product_name_zh.trim() || undefined,
      short_description_zh: formData.short_description_zh.trim() || undefined,
      translation_status: transStatus,
    };

    const newProduct: Product & { supplier_name: string } = {
      ...payload,
      id: newId,
      product_id: newId,
      supplier_id: supplierId,
      supplier_name: supplierName,
      minimum_order_quantity: formData.minimum_order_quantity ? Number(formData.minimum_order_quantity) : undefined,
      minimum_order_unit: formData.minimum_order_unit,
      indicative_price_min: formData.indicative_price_min ? Number(formData.indicative_price_min) : undefined,
      indicative_price_max: formData.indicative_price_max ? Number(formData.indicative_price_max) : undefined,
      currency: formData.currency,
      price_basis: formData.price_basis,
      lead_time_unit: formData.lead_time_unit,
      translation_status: transStatus,
      version: 1,
      created_by: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setLocalProducts([newProduct, ...localProducts]);
    setIsAddModalOpen(false);

    setNotification({
      type: "success",
      title: "Product Added",
      message: `"${newProduct.product_name}" has been registered into the catalogue.`,
    });

    createProductMutation.mutate(payload);
  };

  const handleOpenAddModal = () => {
    if (!formData.supplier_id && suppliers.length > 0) {
      setFormData((prev) => ({ ...prev, supplier_id: suppliers[0].id || suppliers[0].supplier_id || "" }));
    }
    setIsAddModalOpen(true);
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <h1>Product Catalogue</h1>
          <p className={styles.subtitle}>
            Module M3 — Browse commercial specifications, MOQ, pricing terms, and Mandarin translation readiness.
          </p>
        </div>
        <div>
          <Button variant="primary" onClick={handleOpenAddModal}>
            + Add Product to Catalogue
          </Button>
        </div>
      </div>

      {/* Notification */}
      {notification && (
        <AlertBanner
          type={notification.type}
          title={notification.title}
          message={notification.message}
        />
      )}

      {/* Stats Summary */}
      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Total Products</span>
          <span className={styles.statValue}>{stats.total}</span>
          <span className={styles.statHint}>Across all registered suppliers</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Mandarin Translation Verified</span>
          <span className={styles.statValue} style={{ color: "var(--color-primary)" }}>
            {stats.reviewed}
          </span>
          <span className={styles.statHint}>Verified for Chinese buyers</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Pending Translation Review</span>
          <span className={styles.statValue} style={{ color: "#92400e" }}>
            {stats.unreviewed}
          </span>
          <span className={styles.statHint}>Draft translations entered</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>English Only</span>
          <span className={styles.statValue} style={{ color: "var(--color-text-muted)" }}>
            {stats.missing}
          </span>
          <span className={styles.statHint}>Requires Chinese translation</span>
        </div>
      </div>

      {/* Controls & Filter Toolbar */}
      <div className={styles.controlsBar}>
        <div className={styles.searchContainer}>
          <svg
            className={styles.searchIcon}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            className={styles.searchInput}
            placeholder="Search by product name, Chinese title, or category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className={styles.filterControlsRow}>
          <select
            className={styles.filterSelect}
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="All">All Categories</option>
            {PRODUCT_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>

          <select
            className={styles.filterSelect}
            value={translationFilter}
            onChange={(e) => setTranslationFilter(e.target.value)}
          >
            <option value="All">All Translations</option>
            <option value="Reviewed">Reviewed</option>
            <option value="Provided – unreviewed">Provided – Unreviewed</option>
            <option value="Not provided">Not Provided</option>
          </select>

          {isAnyFilterActive && (
            <button
              type="button"
              className={styles.resetFiltersBtn}
              onClick={handleResetFilters}
            >
              ✕ Clear
            </button>
          )}
        </div>
      </div>

      {/* Products Table */}
      <div className={styles.tableCard}>
        {isLoading ? (
          <div style={{ padding: "3rem", textAlign: "center" }}>
            <LoadingSpinner label="Loading products..." />
          </div>
        ) : filteredProducts.length === 0 ? (
          <EmptyState
            title={isAnyFilterActive ? "No Matching Products" : "No Products in Catalogue"}
            guidance={
              isAnyFilterActive
                ? "No products match your search or filter criteria."
                : "No products have been added to the catalogue yet. Click '+ Add Product to Catalogue' to register a product specification."
            }
            action={
              isAnyFilterActive ? (
                <Button variant="secondary" onClick={handleResetFilters}>
                  Reset Filters
                </Button>
              ) : (
                <Button variant="primary" onClick={handleOpenAddModal}>
                  + Add Product to Catalogue
                </Button>
              )
            }
          />
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Product ID & Title</th>
                <th>Supplier Organisation</th>
                <th>Category</th>
                <th>MOQ</th>
                <th>Indicative Price</th>
                <th>Lead Time</th>
                <th>Mandarin Readiness</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map((p) => {
                const supplierName = (p as any).supplier_name || "Registered Supplier";
                let badgeClass = styles.transMissing;
                if (p.translation_status === "Reviewed") badgeClass = styles.transReviewed;
                else if (p.translation_status === "Provided – unreviewed") badgeClass = styles.transUnreviewed;

                return (
                  <tr key={p.product_id}>
                    <td>
                      <div>
                        <strong>{p.product_name}</strong>
                        {p.product_name_zh && (
                          <div className={styles.mandarinTag}>
                            {p.product_name_zh}
                          </div>
                        )}
                        <div style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                          {p.product_id}
                        </div>
                      </div>
                    </td>
                    <td>
                      <span style={{ fontWeight: 500 }}>{supplierName}</span>
                    </td>
                    <td>
                      <span style={{ fontSize: "0.8125rem" }}>{p.product_category}</span>
                    </td>
                    <td>
                      {p.minimum_order_quantity ? (
                        <span>
                          {p.minimum_order_quantity.toLocaleString()} {p.minimum_order_unit || ""}
                        </span>
                      ) : (
                        <span style={{ color: "var(--color-text-muted)" }}>Negotiable</span>
                      )}
                    </td>
                    <td>
                      {p.indicative_price_min && p.indicative_price_max ? (
                        <span>
                          {p.currency || "USD"} {p.indicative_price_min} – {p.indicative_price_max}{" "}
                          <small style={{ color: "var(--color-text-muted)" }}>({p.price_basis || "FOB"})</small>
                        </span>
                      ) : (
                        <span style={{ color: "var(--color-text-muted)" }}>On Inquiry</span>
                      )}
                    </td>
                    <td>
                      {p.lead_time_value ? (
                        <span>
                          {p.lead_time_value} {p.lead_time_unit || "days"}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>
                      <span className={`${styles.translationBadge} ${badgeClass}`}>
                        {p.translation_status}
                      </span>
                    </td>
                    <td>
                      <Button
                        variant="secondary"
                        onClick={() => setSelectedProduct(p as any)}
                      >
                        View Specs
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal: View Product Specs */}
      {selectedProduct && (
        <div className={styles.modalOverlay} onClick={() => setSelectedProduct(null)}>
          <div className={styles.modalDialog} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2 className={styles.modalTitle}>{selectedProduct.product_name}</h2>
                {selectedProduct.product_name_zh && (
                  <div style={{ fontSize: "0.9375rem", color: "var(--color-primary)", fontWeight: 600 }}>
                    {selectedProduct.product_name_zh}
                  </div>
                )}
              </div>
              <button
                className={styles.closeButton}
                onClick={() => setSelectedProduct(null)}
                aria-label="Close"
              >
                &times;
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              <div>
                <span style={{ fontSize: "0.75rem", textTransform: "uppercase", fontWeight: 700, color: "var(--color-text-muted)" }}>
                  Commercial Description
                </span>
                <p style={{ margin: "0.25rem 0 0", fontSize: "0.875rem", lineHeight: 1.5 }}>
                  {selectedProduct.description || "No commercial description provided."}
                </p>
              </div>

              {selectedProduct.short_description_zh && (
                <div style={{ backgroundColor: "var(--color-bg-subtle)", padding: "0.75rem 1rem", borderRadius: "var(--radius-md)" }}>
                  <span style={{ fontSize: "0.75rem", textTransform: "uppercase", fontWeight: 700, color: "var(--color-text-muted)" }}>
                    Mandarin Commercial Summary (中文简述)
                  </span>
                  <p style={{ margin: "0.25rem 0 0", fontSize: "0.875rem", lineHeight: 1.5 }}>
                    {selectedProduct.short_description_zh}
                  </p>
                </div>
              )}

              <div>
                <span style={{ fontSize: "0.75rem", textTransform: "uppercase", fontWeight: 700, color: "var(--color-text-muted)" }}>
                  Technical Specifications
                </span>
                <p style={{ margin: "0.25rem 0 0", fontSize: "0.875rem", lineHeight: 1.5, fontFamily: "monospace" }}>
                  {selectedProduct.specifications || "No technical specifications recorded."}
                </p>
              </div>

              <div className={styles.formGrid}>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--color-text-muted)" }}>Category:</span>{" "}
                  <span style={{ fontSize: "0.875rem" }}>{selectedProduct.product_category}</span>
                </div>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--color-text-muted)" }}>Origin:</span>{" "}
                  <span style={{ fontSize: "0.875rem" }}>{selectedProduct.origin || "India"}</span>
                </div>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--color-text-muted)" }}>MOQ:</span>{" "}
                  <span style={{ fontSize: "0.875rem" }}>
                    {selectedProduct.minimum_order_quantity} {selectedProduct.minimum_order_unit}
                  </span>
                </div>
                <div>
                  <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--color-text-muted)" }}>Lead Time:</span>{" "}
                  <span style={{ fontSize: "0.875rem" }}>
                    {selectedProduct.lead_time_value} {selectedProduct.lead_time_unit}
                  </span>
                </div>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1.5rem" }}>
              <Button variant="secondary" onClick={() => setSelectedProduct(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Add New Product */}
      {isAddModalOpen && (
        <div className={styles.modalOverlay} onClick={() => setIsAddModalOpen(false)}>
          <div className={styles.modalDialog} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>Add Product to Catalogue</h2>
              <button
                className={styles.closeButton}
                onClick={() => setIsAddModalOpen(false)}
                aria-label="Close"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateProduct}>
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <FormField label="Supplier Organisation" required>
                  <Select
                    value={formData.supplier_id}
                    onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}
                  >
                    {suppliers.length === 0 ? (
                      <option value="">No suppliers found (Register supplier first)</option>
                    ) : (
                      suppliers.map((s) => (
                        <option key={s.supplier_id} value={s.supplier_id}>
                          {s.legal_name} ({s.supplier_id})
                        </option>
                      ))
                    )}
                  </Select>
                </FormField>

                <div className={styles.formGrid}>
                  <FormField label="Product Name (English)" required>
                    <Input
                      placeholder="e.g. Organic Black Pepper"
                      value={formData.product_name}
                      onChange={(e) => setFormData({ ...formData, product_name: e.target.value })}
                    />
                  </FormField>

                  <FormField label="Mandarin Name (中文名称)" hint="Optional per M3-AC4">
                    <Input
                      placeholder="e.g. 有机黑胡椒"
                      value={formData.product_name_zh}
                      onChange={(e) => setFormData({ ...formData, product_name_zh: e.target.value })}
                    />
                  </FormField>
                </div>

                <div className={styles.formGrid}>
                  <FormField label="Product Category" required>
                    <Select
                      value={formData.product_category}
                      onChange={(e) => setFormData({ ...formData, product_category: e.target.value as ProductCategory })}
                    >
                      {PRODUCT_CATEGORIES.map((cat) => (
                        <option key={cat} value={cat}>
                          {cat}
                        </option>
                      ))}
                    </Select>
                  </FormField>

                  <FormField label="Country of Origin">
                    <Input
                      value={formData.origin}
                      onChange={(e) => setFormData({ ...formData, origin: e.target.value })}
                    />
                  </FormField>
                </div>

                <FormField label="Commercial Description">
                  <Textarea
                    rows={2}
                    placeholder="General description of product quality, harvest, and packaging..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </FormField>

                <FormField label="Technical Specifications & Lab Standards">
                  <Textarea
                    rows={2}
                    placeholder="Moisture limits, bulk density, grade standards (e.g. GB compliance)..."
                    value={formData.specifications}
                    onChange={(e) => setFormData({ ...formData, specifications: e.target.value })}
                  />
                </FormField>

                <div className={styles.formGrid}>
                  <FormField label="Minimum Order Quantity (MOQ)">
                    <Input
                      type="number"
                      placeholder="e.g. 500"
                      value={formData.minimum_order_quantity}
                      onChange={(e) => setFormData({ ...formData, minimum_order_quantity: e.target.value })}
                    />
                  </FormField>

                  <FormField label="MOQ Unit">
                    <Select
                      value={formData.minimum_order_unit}
                      onChange={(e) => setFormData({ ...formData, minimum_order_unit: e.target.value })}
                    >
                      <option value="tonnes">tonnes</option>
                      <option value="kg">kg</option>
                      <option value="pieces">pieces</option>
                      <option value="metres">metres</option>
                    </Select>
                  </FormField>
                </div>

                <div className={styles.formGrid}>
                  <FormField label="Min Price">
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="e.g. 7.50"
                      value={formData.indicative_price_min}
                      onChange={(e) => setFormData({ ...formData, indicative_price_min: e.target.value })}
                    />
                  </FormField>

                  <FormField label="Max Price">
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="e.g. 8.50"
                      value={formData.indicative_price_max}
                      onChange={(e) => setFormData({ ...formData, indicative_price_max: e.target.value })}
                    />
                  </FormField>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.5rem" }}>
                <Button variant="secondary" type="button" onClick={() => setIsAddModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit">
                  Save Product to Catalogue
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

