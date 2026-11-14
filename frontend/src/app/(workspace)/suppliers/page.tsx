"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import styles from "./suppliers.module.css";
import { apiFetch } from "@/lib/api/client";
import {
  Supplier,
  SupplierStatus,
  SupplierType,
  Product,
  EvidenceMetadata,
  TranslationStatus,
  ApiError,
  unwrapPaginated,
  PaginatedSupplierList,
  PaginatedProductList,
  PaginatedEvidenceItemList,
} from "@/lib/api/types";
import { Button } from "@/components/forms/Button";
import { FormField } from "@/components/forms/FormField";
import { Input } from "@/components/forms/Input";
import { Select } from "@/components/forms/Select";
import { Textarea } from "@/components/forms/Textarea";
import { StatusBadge } from "@/components/feedback/StatusBadge";
import { EmptyState } from "@/components/feedback/EmptyState";
import { AlertBanner } from "@/components/feedback/AlertBanner";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

export default function SuppliersPage() {
  const queryClient = useQueryClient();

  // Filters & Search
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"All" | SupplierStatus>("All");
  const [typeFilter, setTypeFilter] = useState<string>("All");

  // Selection & Detail Tabs
  const [selectedSupplierId, setSelectedSupplierId] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState<"overview" | "products" | "evidence">("overview");

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isAddProductOpen, setIsAddProductOpen] = useState(false);
  const [isAddEvidenceOpen, setIsAddEvidenceOpen] = useState(false);

  // Notification Banner
  const [notification, setNotification] = useState<{
    type: "success" | "warning" | "error" | "info";
    title?: string;
    message: string;
  } | null>(null);

  // ==========================================================================
  // Backend Queries (Dynamic — Zero Mock Data)
  // ==========================================================================
  const {
    data: suppliers = [],
    isLoading: isLoadingSuppliers,
    isError: isSuppliersError,
    error: suppliersError,
  } = useQuery<Supplier[]>({
    queryKey: ["suppliers"],
    queryFn: async () => {
      try {
        const res = await apiFetch<Supplier[] | PaginatedSupplierList>("/api/v1/suppliers/");
        return unwrapPaginated(res).map((s) => ({
          ...s,
          supplier_id: s.id || s.supplier_id || "",
        }));
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          // Endpoint not mounted yet on backend
          return [];
        }
        throw err;
      }
    },
    staleTime: 30 * 1000,
    retry: false,
  });

  const selectedSupplier = suppliers.find((s) => (s.id || s.supplier_id) === selectedSupplierId) || null;

  // Products Query for Selected Supplier (supports ?supplier= or ?supplier_id=)
  const {
    data: products = [],
    isLoading: isLoadingProducts,
  } = useQuery<Product[]>({
    queryKey: ["products", selectedSupplierId],
    queryFn: async () => {
      if (!selectedSupplierId) return [];
      try {
        const res = await apiFetch<Product[] | PaginatedProductList>(`/api/v1/products/?supplier=${encodeURIComponent(selectedSupplierId)}`);
        return unwrapPaginated(res).map((p) => ({
          ...p,
          product_id: p.id || p.product_id || "",
          supplier_id: p.supplier || p.supplier_id || "",
          minimum_order_quantity: p.moq_value ? Number(p.moq_value) : p.minimum_order_quantity,
          minimum_order_unit: p.moq_unit || p.minimum_order_unit || "PIECES",
          indicative_price_min: p.price_min ? Number(p.price_min) : p.indicative_price_min,
          indicative_price_max: p.price_max ? Number(p.price_max) : p.indicative_price_max,
        }));
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return [];
        throw err;
      }
    },
    enabled: Boolean(selectedSupplierId),
    staleTime: 30 * 1000,
    retry: false,
  });

  // Evidence Query for Selected Supplier
  const {
    data: evidence = [],
    isLoading: isLoadingEvidence,
  } = useQuery<EvidenceMetadata[]>({
    queryKey: ["evidence", selectedSupplierId],
    queryFn: async () => {
      if (!selectedSupplierId) return [];
      try {
        const res = await apiFetch<EvidenceMetadata[] | PaginatedEvidenceItemList>(`/api/v1/evidence/?supplier=${encodeURIComponent(selectedSupplierId)}`);
        return unwrapPaginated(res).map((e) => ({
          ...e,
          evidence_id: e.id || e.evidence_id || "",
        }));
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return [];
        throw err;
      }
    },
    enabled: Boolean(selectedSupplierId),
    staleTime: 30 * 1000,
    retry: false,
  });

  // ==========================================================================
  // Supplier Form State (M2)
  // ==========================================================================
  const [formData, setFormData] = useState({
    legal_name: "",
    country_of_registration: "IN",
    supplier_type: "Manufacturer" as SupplierType,
    contact_name: "",
    email: "",
    phone: "",
    address_registration_reference: "",
    industry_description: "",
    capability_attributes: "",
  });

  const [formErrors, setFormErrors] = useState<Record<string, string[]>>({});

  const handleResetForm = () => {
    setFormData({
      legal_name: "",
      country_of_registration: "IN",
      supplier_type: "Manufacturer",
      contact_name: "",
      email: "",
      phone: "",
      address_registration_reference: "",
      industry_description: "",
      capability_attributes: "",
    });
    setFormErrors({});
  };

  // ==========================================================================
  // Product Form State (M3)
  // ==========================================================================
  const [productFormData, setProductFormData] = useState({
    product_name: "",
    product_category: "Textiles & Garments",
    description: "",
    specifications: "",
    origin: "India",
    minimum_order_quantity: "",
    minimum_order_unit: "PIECES",
    indicative_price_min: "",
    indicative_price_max: "",
    currency: "USD",
    price_basis: "FOB",
    capacity_quantity: "",
    capacity_unit: "pieces",
    capacity_period: "per month",
    lead_time_value: "",
    lead_time_unit: "days",
    product_name_zh: "",
    short_description_zh: "",
  });

  const [productFormErrors, setProductFormErrors] = useState<Record<string, string[]>>({});

  // ==========================================================================
  // Evidence Form State (EVD)
  // ==========================================================================
  const [evidenceFormData, setEvidenceFormData] = useState({
    document_type: "Export License",
    document_name: "",
    evidence_reference: "",
    issue_date: "",
    expiry_date: "",
  });

  // ==========================================================================
  // Mutations
  // ==========================================================================
  const createSupplierMutation = useMutation({
    mutationFn: (payload: Partial<Supplier>) =>
      apiFetch<Supplier>("/api/v1/suppliers/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (newSupplier) => {
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      setIsCreateOpen(false);
      handleResetForm();
      setNotification({
        type: "success",
        title: "Supplier Created",
        message: `Supplier "${newSupplier.legal_name}" successfully recorded in the registry.`,
      });
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        if (err.fieldErrors) setFormErrors(err.fieldErrors);
        setNotification({
          type: "error",
          title: "Failed to Create Supplier",
          message: err.message || "Could not save supplier record to backend.",
        });
      } else {
        setNotification({
          type: "error",
          title: "Connection Error",
          message: "Backend service is currently unreachable.",
        });
      }
    },
  });

  const updateSupplierMutation = useMutation({
    mutationFn: ({
      supplierId,
      action,
      payload,
    }: {
      supplierId: string;
      action?: "complete" | "archive";
      payload?: Partial<Supplier>;
    }) => {
      if (action === "complete") {
        return apiFetch<Supplier>(`/api/v1/suppliers/${encodeURIComponent(supplierId)}/complete/`, {
          method: "POST",
        });
      }
      if (action === "archive") {
        return apiFetch<Supplier>(`/api/v1/suppliers/${encodeURIComponent(supplierId)}/archive/`, {
          method: "POST",
        });
      }
      return apiFetch<Supplier>(`/api/v1/suppliers/${encodeURIComponent(supplierId)}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["suppliers"] });
      setNotification({
        type: "success",
        title: "Status Updated",
        message: `Supplier transitioned to ${updated.record_status} (v${updated.version}).`,
      });
    },
    onError: (err) => {
      setNotification({
        type: "error",
        title: "Update Failed",
        message: err instanceof ApiError ? err.message : "Could not update supplier record.",
      });
    },
  });

  const createProductMutation = useMutation({
    mutationFn: (payload: Partial<Product>) =>
      apiFetch<Product>("/api/v1/products/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (newProduct) => {
      queryClient.invalidateQueries({ queryKey: ["products", selectedSupplierId] });
      setIsAddProductOpen(false);
      setProductFormErrors({});
      setProductFormData({
        product_name: "",
        product_category: "Textiles & Garments",
        description: "",
        specifications: "",
        origin: "India",
        minimum_order_quantity: "",
        minimum_order_unit: "PIECES",
        indicative_price_min: "",
        indicative_price_max: "",
        currency: "USD",
        price_basis: "FOB",
        capacity_quantity: "",
        capacity_unit: "pieces",
        capacity_period: "per month",
        lead_time_value: "",
        lead_time_unit: "days",
        product_name_zh: "",
        short_description_zh: "",
      });
      setNotification({
        type: "success",
        title: "Product Added",
        message: `Product "${newProduct.product_name}" added to catalogue.`,
      });
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        if (err.fieldErrors) setProductFormErrors(err.fieldErrors);
        setNotification({
          type: "error",
          title: "Product Save Failed",
          message: err.message || "Could not save product to database.",
        });
      } else {
        setNotification({
          type: "error",
          title: "Connection Error",
          message: "Backend service is currently unreachable.",
        });
      }
    },
  });

  const createEvidenceMutation = useMutation({
    mutationFn: (payload: Partial<EvidenceMetadata>) =>
      apiFetch<EvidenceMetadata>("/api/v1/evidence/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (newEvd) => {
      queryClient.invalidateQueries({ queryKey: ["evidence", selectedSupplierId] });
      setIsAddEvidenceOpen(false);
      setEvidenceFormData({
        document_type: "Export License",
        document_name: "",
        evidence_reference: "",
        issue_date: "",
        expiry_date: "",
      });
      setNotification({
        type: "success",
        title: "Evidence Reference Recorded",
        message: `Attached metadata for ${newEvd.document_type}.`,
      });
    },
    onError: (err) => {
      setNotification({
        type: "error",
        title: "Evidence Save Failed",
        message: err instanceof ApiError ? err.message : "Could not record evidence reference.",
      });
    },
  });

  // ==========================================================================
  // Form Submission Handlers
  // ==========================================================================
  const handleSaveSupplier = (targetStatus: SupplierStatus) => {
    const errors: Record<string, string[]> = {};

    // Validate Complete gate per Lean Field Dictionary: legal_name, country_of_registration, supplier_type
    if (targetStatus === "Complete") {
      if (!formData.legal_name.trim()) {
        errors.legal_name = ["Legal name is required to mark a supplier record as Complete."];
      }
      if (!formData.country_of_registration) {
        errors.country_of_registration = ["Country of registration is required."];
      }
      if (!formData.supplier_type) {
        errors.supplier_type = ["Supplier type classification is required."];
      }
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    const typeMapping: Record<string, any> = {
      Manufacturer: "manufacturer",
      Trader: "trader",
      "Merchant Exporter": "merchant_exporter",
    };
    const statusMapping: Record<string, any> = {
      Draft: "draft",
      Complete: "complete",
      Archived: "archived",
    };

    createSupplierMutation.mutate({
      legal_name: formData.legal_name.trim(),
      country_of_registration: formData.country_of_registration,
      supplier_type: typeMapping[formData.supplier_type] || (formData.supplier_type ? formData.supplier_type.toLowerCase() : "manufacturer"),
      address: formData.address_registration_reference.trim() || undefined,
      address_registration_reference: formData.address_registration_reference.trim() || undefined,
      contact_name: formData.contact_name.trim() || undefined,
      contact_email: formData.email.trim() || undefined,
      contact_phone: formData.phone.trim() || undefined,
      contact_details: {
        contact_name: formData.contact_name.trim() || undefined,
        email: formData.email.trim() || undefined,
        phone: formData.phone.trim() || undefined,
      },
      industry_description: formData.industry_description.trim() || undefined,
      capability_attributes: formData.capability_attributes.trim() || undefined,
      record_status: statusMapping[targetStatus] || targetStatus.toLowerCase(),
    });
  };

  const handleUpdateStatus = (supplierId: string, newStatus: SupplierStatus) => {
    const target = suppliers.find((s) => (s.id || s.supplier_id) === supplierId);
    if (!target) return;

    // Transition Validation Gate
    if (newStatus === "Complete" || newStatus === "complete") {
      if (!target.legal_name || !target.country_of_registration || !target.supplier_type) {
        setNotification({
          type: "error",
          title: "Transition Rejected",
          message: "Cannot mark as Complete: Legal Name, Country, and Supplier Type must be defined.",
        });
        return;
      }
      updateSupplierMutation.mutate({
        supplierId,
        action: "complete",
      });
      return;
    }

    if (newStatus === "Archived" || newStatus === "archived") {
      updateSupplierMutation.mutate({
        supplierId,
        action: "archive",
      });
      return;
    }

    updateSupplierMutation.mutate({
      supplierId,
      payload: {
        record_status: (newStatus.toLowerCase()) as any,
        version: target.version,
      },
    });
  };

  const handleCreateProduct = (e: React.FormEvent) => {
    e.preventDefault();
    setProductFormErrors({});

    if (!productFormData.product_name.trim()) {
      setProductFormErrors({ product_name: ["Product name is required."] });
      return;
    }
    if (!selectedSupplierId) {
      setNotification({
        type: "error",
        title: "No Supplier Selected",
        message: "Please select a supplier from the registry first.",
      });
      return;
    }

    const hasMandarin = Boolean(
      productFormData.product_name_zh.trim() || productFormData.short_description_zh.trim()
    );
    const translationStatus = hasMandarin ? "provided_unreviewed" : "not_provided";

    createProductMutation.mutate({
      supplier: selectedSupplierId,
      supplier_id: selectedSupplierId,
      product_name: productFormData.product_name.trim(),
      product_category: productFormData.product_category,
      description: productFormData.description.trim() || undefined,
      specifications: productFormData.specifications.trim() || undefined,
      origin: productFormData.origin || "India",
      moq_value: productFormData.minimum_order_quantity ? String(productFormData.minimum_order_quantity) : null,
      moq_unit: (productFormData.minimum_order_unit || "PIECES").toUpperCase(),
      minimum_order_quantity: productFormData.minimum_order_quantity ? Number(productFormData.minimum_order_quantity) : undefined,
      minimum_order_unit: productFormData.minimum_order_unit || undefined,
      price_min: productFormData.indicative_price_min ? String(productFormData.indicative_price_min) : null,
      price_max: productFormData.indicative_price_max ? String(productFormData.indicative_price_max) : null,
      indicative_price_min: productFormData.indicative_price_min ? Number(productFormData.indicative_price_min) : undefined,
      indicative_price_max: productFormData.indicative_price_max ? Number(productFormData.indicative_price_max) : undefined,
      currency: productFormData.currency || "USD",
      price_basis: productFormData.price_basis || "FOB",
      capacity_quantity: productFormData.capacity_quantity ? String(productFormData.capacity_quantity) : null,
      capacity_unit: (productFormData.capacity_unit || "PIECES").toUpperCase(),
      capacity_period: "MONTH",
      lead_time_value: productFormData.lead_time_value ? Number(productFormData.lead_time_value) : null,
      lead_time_unit: "DAYS",
      product_name_zh: productFormData.product_name_zh.trim() || undefined,
      short_description_zh: productFormData.short_description_zh.trim() || undefined,
      translation_status: translationStatus as TranslationStatus,
    });
  };

  const handleCreateEvidence = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSupplierId || !evidenceFormData.evidence_reference.trim()) return;

    createEvidenceMutation.mutate({
      supplier: selectedSupplierId,
      product: null,
      entity_type: "supplier",
      entity_id: selectedSupplierId,
      document_type: evidenceFormData.document_type,
      document_name: evidenceFormData.document_name.trim() || evidenceFormData.evidence_reference.trim(),
      evidence_reference: evidenceFormData.evidence_reference.trim(),
      issue_date: evidenceFormData.issue_date || null,
      expiry_date: evidenceFormData.expiry_date || null,
      presence_status: "Provided",
      review_status: "Pending Review",
    });
  };

  // Filtered suppliers
  const filteredSuppliers = suppliers.filter((s) => {
    const matchesSearch =
      (s.legal_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.supplier_id || s.id || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.industry_description && s.industry_description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus =
      statusFilter === "All" ||
      s.record_status.toLowerCase() === statusFilter.toLowerCase();
    const matchesType =
      typeFilter === "All" ||
      s.supplier_type.toLowerCase() === typeFilter.toLowerCase();
    return matchesSearch && matchesStatus && matchesType;
  });

  return (
    <div className={styles.container}>
      {/* ====================================================================
          PAGE HEADER
          ==================================================================== */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Supplier Registry & Catalogue</h1>
          <p className={styles.pageSubtitle}>
            Maintain supplier profiles, products, commercial specifications and evidence metadata.
            Statuses strictly adhere to <strong>Draft</strong>, <strong>Complete</strong>, and <strong>Archived</strong> lifecycle gates.
          </p>
        </div>
        <div className={styles.headerActions}>
          <Button variant="primary" onClick={() => setIsCreateOpen(true)}>
            + New Supplier Draft
          </Button>
        </div>
      </div>

      {notification && (
        <AlertBanner
          type={notification.type}
          title={notification.title}
          message={notification.message}
        />
      )}

      {isSuppliersError && (
        <AlertBanner
          type="info"
          title="Backend Disconnected"
          message="Django API (:8000) not responding. Once the backend server is started, suppliers will stream directly from the database."
        />
      )}

      {/* ====================================================================
          CONTROLS BAR: Search & Filters
          ==================================================================== */}
      <div className={styles.controlsBar}>
        <div className={styles.searchBox}>
          <svg className={styles.searchIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="search"
            placeholder="Search by legal name, supplier ID or capability..."
            className={styles.searchInput}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search suppliers"
          />
        </div>

        <div className={styles.filterGroup}>
          {/* Status Tabs */}
          <div className={styles.statusTabs} role="tablist" aria-label="Filter by lifecycle status">
            {(["All", "Draft", "Complete", "Archived"] as const).map((status) => (
              <button
                key={status}
                type="button"
                role="tab"
                aria-selected={statusFilter === status}
                className={`${styles.statusTab} ${statusFilter === status ? styles.statusTabActive : ""}`}
                onClick={() => setStatusFilter(status)}
              >
                {status}
              </button>
            ))}
          </div>

          {/* Type Filter */}
          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{ width: "auto", fontSize: "0.8125rem", padding: "0.35rem 0.75rem" }}
            aria-label="Filter by supplier type"
          >
            <option value="All">All Types</option>
            <option value="Manufacturer">Manufacturer</option>
            <option value="Trader">Trader</option>
            <option value="Distributor">Distributor</option>
            <option value="Service Provider">Service Provider</option>
            <option value="Other">Other</option>
          </Select>
        </div>
      </div>

      {/* ====================================================================
          TABLE ROSTER / ROSTER LIST
          ==================================================================== */}
      <div className={styles.tableCard}>
        <div className={styles.tableHeaderRow}>
          <span className={styles.tableCounter}>
            Showing {filteredSuppliers.length} of {suppliers.length} suppliers
          </span>
        </div>

        {isLoadingSuppliers ? (
          <div style={{ padding: "3rem" }}>
            <LoadingSpinner label="Loading supplier registry from database..." />
          </div>
        ) : filteredSuppliers.length === 0 ? (
          <EmptyState
            title="No Suppliers Registered"
            guidance={
              searchTerm || statusFilter !== "All"
                ? "No records match the current filter criteria."
                : "No supplier records exist in the database yet. Create a draft to begin capturing company data and products."
            }
            action={
              <Button variant="primary" onClick={() => setIsCreateOpen(true)}>
                Create First Supplier
              </Button>
            }
          />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--color-border)", backgroundColor: "#FAF7F2", textAlign: "left" }}>
                  <th style={{ padding: "0.75rem 1.25rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Supplier / Legal Name
                  </th>
                  <th style={{ padding: "0.75rem 1rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Type
                  </th>
                  <th style={{ padding: "0.75rem 1rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Country
                  </th>
                  <th style={{ padding: "0.75rem 1rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Status
                  </th>
                  <th style={{ padding: "0.75rem 1rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Ver.
                  </th>
                  <th style={{ padding: "0.75rem 1.25rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em", textAlign: "right" }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredSuppliers.map((supplier, idx) => (
                  <tr
                    key={supplier.id || supplier.supplier_id || `supplier-${idx}`}
                    style={{ borderBottom: "1px solid var(--color-border-subtle)", transition: "background 0.15s ease" }}
                  >
                    <td style={{ padding: "0.9rem 1.25rem" }}>
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        <span style={{ fontWeight: 600, color: "var(--color-text-main)", fontSize: "0.9375rem" }}>
                          {supplier.legal_name || "(Draft Supplier)"}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontFamily: "var(--font-family-mono)" }}>
                          {supplier.supplier_id}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: "0.9rem 1rem", fontSize: "0.875rem", color: "var(--color-text-main)" }}>
                      {supplier.supplier_type}
                    </td>
                    <td style={{ padding: "0.9rem 1rem", fontSize: "0.875rem" }}>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem", fontWeight: 500 }}>
                        {supplier.country_of_registration === "IN" ? "🇮🇳 India" : supplier.country_of_registration === "CN" ? "🇨🇳 China" : supplier.country_of_registration}
                      </span>
                    </td>
                    <td style={{ padding: "0.9rem 1rem" }}>
                      <StatusBadge status={supplier.record_status} />
                    </td>
                    <td style={{ padding: "0.9rem 1rem", fontSize: "0.75rem", color: "var(--color-text-muted)", fontFamily: "var(--font-family-mono)" }}>
                      v{supplier.version}
                    </td>
                    <td style={{ padding: "0.9rem 1.25rem", textAlign: "right" }}>
                      <div className={styles.actionBtnGroup} style={{ justifyContent: "flex-end" }}>
                        <button
                          type="button"
                          className={styles.actionLink}
                          onClick={() => {
                            setSelectedSupplierId(supplier.supplier_id);
                            setDetailTab("overview");
                          }}
                        >
                          Manage
                        </button>
                        {supplier.record_status === "Draft" && (
                          <button
                            type="button"
                            className={styles.actionLink}
                            onClick={() => handleUpdateStatus(supplier.supplier_id, "Complete")}
                          >
                            Complete
                          </button>
                        )}
                        {supplier.record_status === "Complete" && (
                          <button
                            type="button"
                            className={`${styles.actionLink} ${styles.actionLinkDanger}`}
                            onClick={() => handleUpdateStatus(supplier.supplier_id, "Archived")}
                          >
                            Archive
                          </button>
                        )}
                        {supplier.record_status === "Archived" && (
                          <button
                            type="button"
                            className={styles.actionLink}
                            onClick={() => handleUpdateStatus(supplier.supplier_id, "Draft")}
                          >
                            Restore
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ====================================================================
          MODAL: CREATE NEW SUPPLIER (M2)
          ==================================================================== */}
      {isCreateOpen && (
        <div className={styles.modalBackdrop} role="dialog" aria-modal="true" aria-labelledby="create-modal-title">
          <div className={styles.modalCard}>
            <div className={styles.modalHeader}>
              <h2 id="create-modal-title" className={styles.modalTitle}>New Supplier Record</h2>
              <button
                type="button"
                className={styles.modalCloseBtn}
                onClick={() => {
                  setIsCreateOpen(false);
                  handleResetForm();
                }}
                aria-label="Close modal"
              >
                &times;
              </button>
            </div>

            <div className={styles.modalBody}>
              <p style={{ fontSize: "0.875rem", color: "var(--color-text-muted)" }}>
                Drafts allow partial saves. Transitioning to <strong>Complete</strong> requires Legal Name, Country, and Supplier Type.
              </p>

              <FormField
                label="Legal Registered Name"
                htmlFor="legal_name"
                hint="Registered commercial entity name"
                errors={formErrors.legal_name}
              >
                <Input
                  id="legal_name"
                  placeholder="e.g. Bharat Agro Exports Pvt Ltd"
                  value={formData.legal_name}
                  onChange={(e) => setFormData({ ...formData, legal_name: e.target.value })}
                  hasError={Boolean(formErrors.legal_name)}
                />
              </FormField>

              <div className={styles.formRow2}>
                <FormField
                  label="Country of Registration"
                  htmlFor="country_of_registration"
                  errors={formErrors.country_of_registration}
                >
                  <Select
                    id="country_of_registration"
                    value={formData.country_of_registration}
                    onChange={(e) => setFormData({ ...formData, country_of_registration: e.target.value })}
                  >
                    <option value="IN">India (IN)</option>
                    <option value="CN">China (CN)</option>
                    <option value="SG">Singapore (SG)</option>
                    <option value="VN">Vietnam (VN)</option>
                    <option value="MY">Malaysia (MY)</option>
                    <option value="OTHER">Other Country</option>
                  </Select>
                </FormField>

                <FormField
                  label="Supplier Classification"
                  htmlFor="supplier_type"
                  errors={formErrors.supplier_type}
                >
                  <Select
                    id="supplier_type"
                    value={formData.supplier_type}
                    onChange={(e) => setFormData({ ...formData, supplier_type: e.target.value as SupplierType })}
                  >
                    <option value="Manufacturer">Manufacturer</option>
                    <option value="Trader">Trader</option>
                    <option value="Distributor">Distributor</option>
                    <option value="Service Provider">Service Provider</option>
                    <option value="Other">Other</option>
                  </Select>
                </FormField>
              </div>

              <span className={styles.sectionTitle}>Contact & Location (Optional in Draft)</span>

              <div className={styles.formRow3}>
                <FormField label="Contact Person" htmlFor="contact_name">
                  <Input
                    id="contact_name"
                    placeholder="e.g. Rajesh Patel"
                    value={formData.contact_name}
                    onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                  />
                </FormField>

                <FormField label="Email" htmlFor="email">
                  <Input
                    id="email"
                    type="email"
                    placeholder="contact@company.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </FormField>

                <FormField label="Phone" htmlFor="phone">
                  <Input
                    id="phone"
                    placeholder="+91 98..."
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  />
                </FormField>
              </div>

              <FormField label="Registered Address / License Reference" htmlFor="address">
                <Textarea
                  id="address"
                  rows={2}
                  placeholder="Plot/Street, City, State, Registration / Tax number..."
                  value={formData.address_registration_reference}
                  onChange={(e) => setFormData({ ...formData, address_registration_reference: e.target.value })}
                />
              </FormField>

              <FormField label="Industry & Capability Overview" htmlFor="industry">
                <Textarea
                  id="industry"
                  rows={2}
                  placeholder="Summary of manufacturing capacity, facilities, standards..."
                  value={formData.industry_description}
                  onChange={(e) => setFormData({ ...formData, industry_description: e.target.value })}
                />
              </FormField>
            </div>

            <div className={styles.modalFooter}>
              <Button
                variant="outline"
                onClick={() => {
                  setIsCreateOpen(false);
                  handleResetForm();
                }}
              >
                Cancel
              </Button>
              <Button
                variant="secondary"
                isLoading={createSupplierMutation.isPending}
                onClick={() => handleSaveSupplier("Draft")}
              >
                Save as Draft
              </Button>
              <Button
                variant="primary"
                isLoading={createSupplierMutation.isPending}
                onClick={() => handleSaveSupplier("Complete")}
              >
                Validate & Save as Complete
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ====================================================================
          MODAL: SUPPLIER DETAILS & PRODUCTS CATALOGUE (M2 / M3 / EVD)
          ==================================================================== */}
      {selectedSupplier && (
        <div className={styles.modalBackdrop} role="dialog" aria-modal="true" aria-labelledby="detail-modal-title">
          <div className={`${styles.modalCard} ${styles.modalCardWide}`}>
            <div className={styles.modalHeader}>
              <div>
                <h2 id="detail-modal-title" className={styles.modalTitle}>{selectedSupplier.legal_name}</h2>
                <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontFamily: "var(--font-family-mono)" }}>
                  ID: {selectedSupplier.supplier_id} · Version: v{selectedSupplier.version}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <StatusBadge status={selectedSupplier.record_status} />
                <button
                  type="button"
                  className={styles.modalCloseBtn}
                  onClick={() => setSelectedSupplierId(null)}
                  aria-label="Close details"
                >
                  &times;
                </button>
              </div>
            </div>

            {/* Navigation Tabs inside Supplier Detail */}
            <div style={{ padding: "0 1.75rem", backgroundColor: "#FAFAF8" }}>
              <div className={styles.detailTabs}>
                <button
                  type="button"
                  className={`${styles.detailTab} ${detailTab === "overview" ? styles.detailTabActive : ""}`}
                  onClick={() => setDetailTab("overview")}
                >
                  Overview & Details
                </button>
                <button
                  type="button"
                  className={`${styles.detailTab} ${detailTab === "products" ? styles.detailTabActive : ""}`}
                  onClick={() => setDetailTab("products")}
                >
                  Product Catalogue ({products.length})
                </button>
                <button
                  type="button"
                  className={`${styles.detailTab} ${detailTab === "evidence" ? styles.detailTabActive : ""}`}
                  onClick={() => setDetailTab("evidence")}
                >
                  Evidence & Documents ({evidence.length})
                </button>
              </div>
            </div>

            <div className={styles.modalBody}>
              {/* TAB 1: OVERVIEW */}
              {detailTab === "overview" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", backgroundColor: "#FAF7F2", padding: "1rem", borderRadius: "var(--radius-md)" }}>
                    <div>
                      <span style={{ fontSize: "0.6875rem", textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: 700 }}>
                        Supplier Type
                      </span>
                      <div style={{ fontSize: "0.9375rem", fontWeight: 600 }}>{selectedSupplier.supplier_type}</div>
                    </div>
                    <div>
                      <span style={{ fontSize: "0.6875rem", textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: 700 }}>
                        Country of Registration
                      </span>
                      <div style={{ fontSize: "0.9375rem", fontWeight: 600 }}>
                        {selectedSupplier.country_of_registration === "IN" ? "India (IN)" : selectedSupplier.country_of_registration}
                      </div>
                    </div>
                    <div>
                      <span style={{ fontSize: "0.6875rem", textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: 700 }}>
                        Lifecycle State
                      </span>
                      <div><StatusBadge status={selectedSupplier.record_status} /></div>
                    </div>
                  </div>

                  <div>
                    <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--color-primary)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                      Contact Information
                    </h3>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem", fontSize: "0.875rem" }}>
                      <div>
                        <span style={{ color: "var(--color-text-muted)", display: "block" }}>Contact Name</span>
                        <strong>{selectedSupplier.contact_details?.contact_name || "—"}</strong>
                      </div>
                      <div>
                        <span style={{ color: "var(--color-text-muted)", display: "block" }}>Email</span>
                        <strong>{selectedSupplier.contact_details?.email || "—"}</strong>
                      </div>
                      <div>
                        <span style={{ color: "var(--color-text-muted)", display: "block" }}>Phone</span>
                        <strong>{selectedSupplier.contact_details?.phone || "—"}</strong>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--color-primary)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                      Address & Registration Reference
                    </h3>
                    <p style={{ fontSize: "0.875rem", color: "var(--color-text-main)" }}>
                      {selectedSupplier.address_registration_reference || "No address details supplied."}
                    </p>
                  </div>

                  <div>
                    <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--color-primary)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                      Industry & Business Capabilities
                    </h3>
                    <p style={{ fontSize: "0.875rem", color: "var(--color-text-main)", marginBottom: "0.5rem" }}>
                      {selectedSupplier.industry_description || "No industry overview supplied."}
                    </p>
                    {selectedSupplier.capability_attributes && (
                      <p style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                        <strong>Capabilities:</strong> {selectedSupplier.capability_attributes}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 2: PRODUCT CATALOGUE (M3) */}
              {detailTab === "products" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.875rem", color: "var(--color-text-muted)" }}>
                      Registered products for {selectedSupplier.legal_name}. Includes source and optional Mandarin-ready specifications.
                    </span>
                    <Button variant="primary" onClick={() => setIsAddProductOpen(true)}>
                      + Add Product
                    </Button>
                  </div>

                  {isLoadingProducts ? (
                    <LoadingSpinner label="Loading products..." />
                  ) : products.length === 0 ? (
                    <EmptyState
                      title="No Products Registered"
                      guidance="Add products with commercial attributes (MOQ, indicative pricing, lead time) to enable matching against buyer requirements."
                      action={
                        <Button variant="primary" onClick={() => setIsAddProductOpen(true)}>
                          Add First Product
                        </Button>
                      }
                    />
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      {products.map((product, idx) => (
                        <div key={product.id || product.product_id || `product-${idx}`} className={styles.productCard}>
                          <div className={styles.productHeader}>
                            <div>
                              <div className={styles.productName}>{product.product_name}</div>
                              {product.product_name_zh && (
                                <div className={styles.productMandarin}>{product.product_name_zh}</div>
                              )}
                              <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                                {product.product_category} · ID: {product.product_id}
                              </span>
                            </div>
                            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                              <StatusBadge status={product.translation_status} />
                            </div>
                          </div>

                          {product.description && (
                            <p style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                              {product.description}
                            </p>
                          )}

                          <div className={styles.productGrid}>
                            <div className={styles.productMetaItem}>
                              <span className={styles.productMetaLabel}>Origin</span>
                              <span className={styles.productMetaValue}>{product.origin || "India"}</span>
                            </div>
                            <div className={styles.productMetaItem}>
                              <span className={styles.productMetaLabel}>MOQ</span>
                              <span className={styles.productMetaValue}>
                                {product.minimum_order_quantity ? `${product.minimum_order_quantity} ${product.minimum_order_unit}` : "—"}
                              </span>
                            </div>
                            <div className={styles.productMetaItem}>
                              <span className={styles.productMetaLabel}>Indicative Price</span>
                              <span className={styles.productMetaValue}>
                                {product.indicative_price_min != null && product.indicative_price_max != null
                                  ? `${product.currency} ${product.indicative_price_min}–${product.indicative_price_max} (${product.price_basis})`
                                  : "—"}
                              </span>
                            </div>
                            <div className={styles.productMetaItem}>
                              <span className={styles.productMetaLabel}>Capacity</span>
                              <span className={styles.productMetaValue}>
                                {product.capacity_quantity ? `${product.capacity_quantity} ${product.capacity_unit} ${product.capacity_period}` : "—"}
                              </span>
                            </div>
                            <div className={styles.productMetaItem}>
                              <span className={styles.productMetaLabel}>Lead Time</span>
                              <span className={styles.productMetaValue}>
                                {product.lead_time_value ? `${product.lead_time_value} ${product.lead_time_unit}` : "—"}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: EVIDENCE METADATA (EVD) */}
              {detailTab === "evidence" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.875rem", color: "var(--color-text-muted)" }}>
                      Regulatory licenses, test reports, and compliance document metadata references.
                    </span>
                    <Button variant="primary" onClick={() => setIsAddEvidenceOpen(true)}>
                      + Add Evidence Ref
                    </Button>
                  </div>

                  {isLoadingEvidence ? (
                    <LoadingSpinner label="Loading evidence..." />
                  ) : evidence.length === 0 ? (
                    <EmptyState
                      title="No Supporting Documents"
                      guidance="Attach metadata references for licenses, ISO certifications, or lab test reports. Document presence is recorded separately from human verification."
                      action={
                        <Button variant="primary" onClick={() => setIsAddEvidenceOpen(true)}>
                          Add Evidence Reference
                        </Button>
                      }
                    />
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      {evidence.map((evd, idx) => (
                        <div key={evd.id || evd.evidence_id || `evidence-${idx}`} className={styles.evidenceRow}>
                          <div className={styles.evidenceLeft}>
                            <span className={styles.evidenceDocType}>{evd.document_type}</span>
                            <span style={{ fontSize: "0.8125rem", color: "var(--color-text-main)" }}>
                              {evd.document_name}
                            </span>
                            <span className={styles.evidenceRef}>Ref: {evd.evidence_reference}</span>
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                            {evd.expiry_date && (
                              <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                                Expires: {evd.expiry_date}
                              </span>
                            )}
                            <StatusBadge status={evd.presence_status} />
                            <StatusBadge status={evd.review_status} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className={styles.modalFooter}>
              <div style={{ marginRight: "auto", display: "flex", gap: "0.5rem" }}>
                {selectedSupplier.record_status === "Draft" && (
                  <Button
                    variant="primary"
                    isLoading={updateSupplierMutation.isPending}
                    onClick={() => handleUpdateStatus(selectedSupplier.supplier_id, "Complete")}
                  >
                    Mark as Complete
                  </Button>
                )}
                {selectedSupplier.record_status === "Complete" && (
                  <Button
                    variant="danger"
                    isLoading={updateSupplierMutation.isPending}
                    onClick={() => handleUpdateStatus(selectedSupplier.supplier_id, "Archived")}
                  >
                    Archive Supplier
                  </Button>
                )}
                {selectedSupplier.record_status === "Archived" && (
                  <Button
                    variant="secondary"
                    isLoading={updateSupplierMutation.isPending}
                    onClick={() => handleUpdateStatus(selectedSupplier.supplier_id, "Draft")}
                  >
                    Restore to Draft
                  </Button>
                )}
              </div>
              <Button variant="outline" onClick={() => setSelectedSupplierId(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ====================================================================
          SUB-MODAL: ADD PRODUCT (M3)
          ==================================================================== */}
      {isAddProductOpen && (
        <div className={styles.modalBackdrop} role="dialog" aria-modal="true" aria-labelledby="add-product-title">
          <div className={styles.modalCard}>
            <div className={styles.modalHeader}>
              <h2 id="add-product-title" className={styles.modalTitle}>Add Product to Catalogue</h2>
              <button
                type="button"
                className={styles.modalCloseBtn}
                onClick={() => setIsAddProductOpen(false)}
                aria-label="Close modal"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateProduct}>
              <div className={styles.modalBody}>
                {productFormErrors.non_field_errors && (
                  <div style={{ marginBottom: "1rem" }}>
                    <AlertBanner
                      type="error"
                      title="Validation Error"
                      message={productFormErrors.non_field_errors.join(" ")}
                    />
                  </div>
                )}
                <FormField label="Product Name (English / Source)" htmlFor="p_name" required errors={productFormErrors.product_name}>
                  <Input
                    id="p_name"
                    required
                    placeholder="e.g. Mulberry Raw Silk Yarn (20/22D)"
                    value={productFormData.product_name}
                    onChange={(e) => setProductFormData({ ...productFormData, product_name: e.target.value })}
                  />
                </FormField>

                <div className={styles.formRow2}>
                  <FormField label="Product Category" htmlFor="p_cat" errors={productFormErrors.product_category}>
                    <Select
                      id="p_cat"
                      value={productFormData.product_category}
                      onChange={(e) => setProductFormData({ ...productFormData, product_category: e.target.value })}
                    >
                      <option value="Textiles & Garments">Textiles & Garments</option>
                      <option value="Agricultural Products">Agricultural Products</option>
                      <option value="Home & Living">Home & Living</option>
                      <option value="Chemicals & Polymers">Chemicals & Polymers</option>
                      <option value="Electronics & Components">Electronics & Components</option>
                      <option value="Machinery & Tools">Machinery & Tools</option>
                      <option value="Other">Other</option>
                    </Select>
                  </FormField>

                  <FormField label="Country of Origin" htmlFor="p_origin" errors={productFormErrors.origin}>
                    <Input
                      id="p_origin"
                      placeholder="e.g. India"
                      value={productFormData.origin}
                      onChange={(e) => setProductFormData({ ...productFormData, origin: e.target.value })}
                    />
                  </FormField>
                </div>

                <FormField label="Product Description" htmlFor="p_desc" errors={productFormErrors.description}>
                  <Textarea
                    id="p_desc"
                    rows={2}
                    placeholder="Grade, process, features, intended applications..."
                    value={productFormData.description}
                    onChange={(e) => setProductFormData({ ...productFormData, description: e.target.value })}
                  />
                </FormField>

                <FormField label="Technical Specifications" htmlFor="p_spec" errors={productFormErrors.specifications}>
                  <Input
                    id="p_spec"
                    placeholder="e.g. Grade 4A, Moisture <11%, Denier 20/22D"
                    value={productFormData.specifications}
                    onChange={(e) => setProductFormData({ ...productFormData, specifications: e.target.value })}
                  />
                </FormField>

                <span className={styles.sectionTitle}>Commercial Terms (M3)</span>

                <div className={styles.formRow2}>
                  <FormField label="Minimum Order Qty (MOQ)" htmlFor="p_moq" errors={productFormErrors.moq_value || productFormErrors.minimum_order_quantity}>
                    <Input
                      id="p_moq"
                      type="number"
                      min="0"
                      placeholder="e.g. 100"
                      value={productFormData.minimum_order_quantity}
                      onChange={(e) => setProductFormData({ ...productFormData, minimum_order_quantity: e.target.value })}
                    />
                  </FormField>

                  <FormField label="MOQ Unit" htmlFor="p_moq_unit" errors={productFormErrors.moq_unit || productFormErrors.minimum_order_unit}>
                    <Select
                      id="p_moq_unit"
                      value={productFormData.minimum_order_unit}
                      onChange={(e) => setProductFormData({ ...productFormData, minimum_order_unit: e.target.value })}
                    >
                      <option value="PIECES">PIECES</option>
                      <option value="KG">KG</option>
                      <option value="MT">MT (Metric Tonnes)</option>
                      <option value="BOXES">BOXES</option>
                      <option value="CONTAINERS">CONTAINERS</option>
                    </Select>
                  </FormField>
                </div>

                <div className={styles.formRow4}>
                  <FormField label="Min Price" htmlFor="p_pmin" errors={productFormErrors.price_min || productFormErrors.indicative_price_min}>
                    <Input
                      id="p_pmin"
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={productFormData.indicative_price_min}
                      onChange={(e) => setProductFormData({ ...productFormData, indicative_price_min: e.target.value })}
                    />
                  </FormField>
                  <FormField label="Max Price" htmlFor="p_pmax" errors={productFormErrors.price_max || productFormErrors.indicative_price_max}>
                    <Input
                      id="p_pmax"
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={productFormData.indicative_price_max}
                      onChange={(e) => setProductFormData({ ...productFormData, indicative_price_max: e.target.value })}
                    />
                  </FormField>
                  <FormField label="Currency" htmlFor="p_curr">
                    <Select
                      id="p_curr"
                      value={productFormData.currency}
                      onChange={(e) => setProductFormData({ ...productFormData, currency: e.target.value })}
                    >
                      <option value="USD">USD</option>
                      <option value="INR">INR</option>
                      <option value="CNY">CNY</option>
                    </Select>
                  </FormField>
                  <FormField label="Basis" htmlFor="p_basis">
                    <Select
                      id="p_basis"
                      value={productFormData.price_basis}
                      onChange={(e) => setProductFormData({ ...productFormData, price_basis: e.target.value })}
                    >
                      <option value="FOB">FOB</option>
                      <option value="CIF">CIF</option>
                      <option value="EXW">EXW</option>
                    </Select>
                  </FormField>
                </div>

                <div className={styles.formRow2}>
                  <FormField label="Lead Time (Value)" htmlFor="p_lt">
                    <Input
                      id="p_lt"
                      type="number"
                      min="1"
                      placeholder="e.g. 15"
                      value={productFormData.lead_time_value}
                      onChange={(e) => setProductFormData({ ...productFormData, lead_time_value: e.target.value })}
                    />
                  </FormField>

                  <FormField label="Lead Time Unit" htmlFor="p_lt_unit">
                    <Select
                      id="p_lt_unit"
                      value={productFormData.lead_time_unit}
                      onChange={(e) => setProductFormData({ ...productFormData, lead_time_unit: e.target.value })}
                    >
                      <option value="days">days</option>
                      <option value="weeks">weeks</option>
                      <option value="months">months</option>
                    </Select>
                  </FormField>
                </div>

                <span className={styles.sectionTitle}>Mandarin-Ready Fields (Optional per M3-AC4)</span>

                <FormField label="Mandarin Product Name (中文名称)" htmlFor="p_zh_name">
                  <Input
                    id="p_zh_name"
                    placeholder="e.g. 桑蚕生丝纱线"
                    value={productFormData.product_name_zh}
                    onChange={(e) => setProductFormData({ ...productFormData, product_name_zh: e.target.value })}
                  />
                </FormField>

                <FormField label="Mandarin Short Description (中文简述)" htmlFor="p_zh_desc">
                  <Input
                    id="p_zh_desc"
                    placeholder="e.g. 高等级环保天然丝绸原料"
                    value={productFormData.short_description_zh}
                    onChange={(e) => setProductFormData({ ...productFormData, short_description_zh: e.target.value })}
                  />
                </FormField>
              </div>

              <div className={styles.modalFooter}>
                <Button variant="outline" type="button" onClick={() => setIsAddProductOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit" isLoading={createProductMutation.isPending}>
                  Save Product to Catalogue
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ====================================================================
          SUB-MODAL: ADD EVIDENCE REFERENCE (EVD)
          ==================================================================== */}
      {isAddEvidenceOpen && (
        <div className={styles.modalBackdrop} role="dialog" aria-modal="true" aria-labelledby="add-evd-title">
          <div className={styles.modalCard}>
            <div className={styles.modalHeader}>
              <h2 id="add-evd-title" className={styles.modalTitle}>Add Evidence Reference</h2>
              <button
                type="button"
                className={styles.modalCloseBtn}
                onClick={() => setIsAddEvidenceOpen(false)}
                aria-label="Close modal"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateEvidence}>
              <div className={styles.modalBody}>
                <p style={{ fontSize: "0.875rem", color: "var(--color-text-muted)" }}>
                  Records a supporting document reference. Document presence is separate from reviewer verification.
                </p>

                <FormField label="Document Type" htmlFor="evd_type" required>
                  <Select
                    id="evd_type"
                    value={evidenceFormData.document_type}
                    onChange={(e) => setEvidenceFormData({ ...evidenceFormData, document_type: e.target.value })}
                  >
                    <option value="Export License">Export License / IEC</option>
                    <option value="Business Registration">Business Registration / Incorporation</option>
                    <option value="ISO Certificate">ISO Quality Certification</option>
                    <option value="Test Report">Lab Test / Purity Report</option>
                    <option value="Tax Certificate">Tax / GST Registration</option>
                    <option value="Other">Other Supporting Document</option>
                  </Select>
                </FormField>

                <FormField label="Document Title / Name" htmlFor="evd_name">
                  <Input
                    id="evd_name"
                    placeholder="e.g. Certificate of Incorporation or IEC 2026"
                    value={evidenceFormData.document_name}
                    onChange={(e) => setEvidenceFormData({ ...evidenceFormData, document_name: e.target.value })}
                  />
                </FormField>

                <FormField label="Evidence Reference / File Key" htmlFor="evd_ref" required hint="File name, registry index or reference ID">
                  <Input
                    id="evd_ref"
                    required
                    placeholder="e.g. IEC-REG-2024-IN.pdf"
                    value={evidenceFormData.evidence_reference}
                    onChange={(e) => setEvidenceFormData({ ...evidenceFormData, evidence_reference: e.target.value })}
                  />
                </FormField>

                <div className={styles.formRow2}>
                  <FormField label="Issue Date" htmlFor="evd_issue">
                    <Input
                      id="evd_issue"
                      type="date"
                      value={evidenceFormData.issue_date}
                      onChange={(e) => setEvidenceFormData({ ...evidenceFormData, issue_date: e.target.value })}
                    />
                  </FormField>

                  <FormField label="Expiry Date (if applicable)" htmlFor="evd_exp" hint="Leave blank if non-expiring">
                    <Input
                      id="evd_exp"
                      type="date"
                      value={evidenceFormData.expiry_date}
                      onChange={(e) => setEvidenceFormData({ ...evidenceFormData, expiry_date: e.target.value })}
                    />
                  </FormField>
                </div>
              </div>

              <div className={styles.modalFooter}>
                <Button variant="outline" type="button" onClick={() => setIsAddEvidenceOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit" isLoading={createEvidenceMutation.isPending}>
                  Record Evidence Reference
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
