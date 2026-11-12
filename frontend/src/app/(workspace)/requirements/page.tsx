"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import styles from "./requirements.module.css";
import { apiFetch } from "@/lib/api/client";
import {
  BuyerRequirement,
  RequirementStatus,
  ProductCategory,
  OrderFrequency,
  RequirementCriterion,
  RequiredEvidenceItem,
  PaginatedResponse,
  unwrapPaginated,
  ApiError,
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

// 7 Top-Level Working Categories defined in Buyer Requirement Field Dictionary v1.2
const PRODUCT_CATEGORIES: ProductCategory[] = [
  "Agriculture and Food",
  "Textiles",
  "Engineering Goods",
  "Electronic Goods",
  "Chemicals",
  "Minerals & Metals",
  "Marine Products",
];

export default function RequirementsPage() {
  const queryClient = useQueryClient();

  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"All" | RequirementStatus>("All");
  const [categoryFilter, setCategoryFilter] = useState<string>("All");
  const [readinessFilter, setReadinessFilter] = useState<"All" | "Ready" | "Blocked">("All");

  // Local fallback storage (Clean zero-state)
  const [localRequirements, setLocalRequirements] = useState<BuyerRequirement[]>([]);

  // Modals & Details State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedReqId, setSelectedReqId] = useState<string | null>(null);
  const [detailTab, setDetailTab] = useState<"overview" | "criteria" | "evidence" | "matching">("overview");

  // Notifications
  const [notification, setNotification] = useState<{
    type: "success" | "warning" | "error";
    title?: string;
    message: string;
  } | null>(null);

  // ==========================================================================
  // Backend Queries (Dynamic Integration)
  // ==========================================================================
  const { data: remoteRequirements, isLoading } = useQuery<BuyerRequirement[]>({
    queryKey: ["requirements"],
    queryFn: async () => {
      try {
        const res = await apiFetch<BuyerRequirement[] | PaginatedResponse<BuyerRequirement>>("/api/v1/requirements/");
        return unwrapPaginated(res);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return [];
        throw err;
      }
    },
    staleTime: 30 * 1000,
    retry: false,
  });

  const requirements = (remoteRequirements && remoteRequirements.length > 0) ? remoteRequirements : localRequirements;
  const selectedReq = requirements.find((r) => r.requirement_id === selectedReqId) || null;

  // Filtered requirements list
  const filteredRequirements = requirements.filter((r) => {
    const matchesSearch =
      r.requirement_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.buyer_organisation_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.requirement_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "All" || r.requirement_status === statusFilter;
    const matchesCategory = categoryFilter === "All" || r.product_category_id === categoryFilter;
    const matchesReadiness =
      readinessFilter === "All" ||
      (readinessFilter === "Ready" && r.matching_ready) ||
      (readinessFilter === "Blocked" && !r.matching_ready);
    return matchesSearch && matchesStatus && matchesCategory && matchesReadiness;
  });

  // ==========================================================================
  // Form State: Capture New Requirement (BUY-SCR-02 - BUY-SCR-06)
  // ==========================================================================
  const [formData, setFormData] = useState({
    buyer_organisation_name: "",
    buyer_reference: "",
    requirement_title: "",
    target_market: "China",
    product_category_id: "Agriculture and Food" as ProductCategory,
    product_specifications: "",
    quantity_value: "",
    quantity_unit: "tonnes",
    order_frequency: "One-off" as OrderFrequency,
    target_price_min: "",
    target_price_max: "",
    currency_code: "USD",
    price_basis: "FOB",
    delivery_location: "",
    delivery_window_start: "",
    delivery_window_end: "",
    required_lead_time_value: "",
    required_lead_time_unit: "days",
    requirement_notes: "",
  });

  // Dynamic Criteria lists in creation form
  const [mandatoryList, setMandatoryList] = useState<string[]>([
    "Valid Organic / Quality Accreditation Certificate",
  ]);
  const [newMandatoryInput, setNewMandatoryInput] = useState("");

  const [preferredList, setPreferredList] = useState<string[]>([
    "Prior China export track record preferred",
  ]);
  const [newPreferredInput, setNewPreferredInput] = useState("");

  const [formErrors, setFormErrors] = useState<Record<string, string[]>>({});

  const handleResetForm = () => {
    setFormData({
      buyer_organisation_name: "",
      buyer_reference: "",
      requirement_title: "",
      target_market: "China",
      product_category_id: "Agriculture and Food",
      product_specifications: "",
      quantity_value: "",
      quantity_unit: "tonnes",
      order_frequency: "One-off",
      target_price_min: "",
      target_price_max: "",
      currency_code: "USD",
      price_basis: "FOB",
      delivery_location: "",
      delivery_window_start: "",
      delivery_window_end: "",
      required_lead_time_value: "",
      required_lead_time_unit: "days",
      requirement_notes: "",
    });
    setMandatoryList(["Valid Organic / Quality Accreditation Certificate"]);
    setPreferredList(["Prior China export track record preferred"]);
    setFormErrors({});
  };

  const handleAddMandatory = () => {
    if (newMandatoryInput.trim()) {
      setMandatoryList([...mandatoryList, newMandatoryInput.trim()]);
      setNewMandatoryInput("");
    }
  };

  const handleRemoveMandatory = (idx: number) => {
    setMandatoryList(mandatoryList.filter((_, i) => i !== idx));
  };

  const handleAddPreferred = () => {
    if (newPreferredInput.trim()) {
      setPreferredList([...preferredList, newPreferredInput.trim()]);
      setNewPreferredInput("");
    }
  };

  const handleRemovePreferred = (idx: number) => {
    setPreferredList(preferredList.filter((_, i) => i !== idx));
  };

  // ==========================================================================
  // Backend Mutations: REST Integration with Graceful 404 Fallback
  // ==========================================================================
  const createRequirementMutation = useMutation({
    mutationFn: (payload: any) =>
      apiFetch<BuyerRequirement>("/api/v1/requirements/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (newReq) => {
      queryClient.invalidateQueries({ queryKey: ["requirements"] });
      setIsCreateOpen(false);
      handleResetForm();
      setNotification({
        type: "success",
        title: "Requirement Synchronized",
        message: `Requirement "${newReq.requirement_title}" successfully saved to backend.`,
      });
    },
    onError: (err, variables: BuyerRequirement) => {
      if (err instanceof ApiError && err.status === 404) {
        setLocalRequirements((prev) => [variables, ...prev]);
        setIsCreateOpen(false);
        handleResetForm();
        setNotification({
          type: "warning",
          title: "Preview Mode (Backend 404)",
          message: "Endpoint /api/v1/requirements/ is under construction. Requirement saved in local preview mode.",
        });
      } else {
        setNotification({
          type: "error",
          title: "Save Failed",
          message: err instanceof ApiError ? err.message : "Failed to create requirement.",
        });
      }
    },
  });

  const updateRequirementMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) =>
      apiFetch<BuyerRequirement>(`/api/v1/requirements/${encodeURIComponent(id)}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["requirements"] });
      setNotification({
        type: "success",
        title: "Status Synchronized",
        message: "Requirement status successfully updated in backend.",
      });
    },
    onError: (err, { id, payload }) => {
      if (err instanceof ApiError && err.status === 404) {
        setLocalRequirements((prev) =>
          prev.map((r) => (r.requirement_id === id ? { ...r, ...payload, version: (r.version || 1) + 1 } : r))
        );
        setNotification({
          type: "warning",
          title: "Status Updated (Preview)",
          message: "Endpoint /api/v1/requirements/ is under construction. Status updated in local session.",
        });
      } else {
        setNotification({
          type: "error",
          title: "Update Failed",
          message: err instanceof ApiError ? err.message : "Failed to update requirement status.",
        });
      }
    },
  });

  // ==========================================================================
  // Form Submission
  // ==========================================================================
  const handleSaveRequirement = (targetStatus: RequirementStatus) => {
    const errors: Record<string, string[]> = {};

    // Validate minimum inputs per BUY-SCR-07 & BUY-D12
    if (!formData.buyer_organisation_name.trim()) {
      errors.buyer_organisation_name = ["Buyer organisation name is required."];
    }
    if (!formData.requirement_title.trim()) {
      errors.requirement_title = ["Requirement title is required for display."];
    }
    if (formData.quantity_value && Number(formData.quantity_value) <= 0) {
      errors.quantity_value = ["Quantity must be greater than zero."];
    }
    if (formData.target_price_min && formData.target_price_max) {
      if (Number(formData.target_price_min) > Number(formData.target_price_max)) {
        errors.target_price_max = ["Maximum price must be greater than or equal to minimum price."];
      }
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    // Determine matching readiness gate (BUY-032)
    const blockingReasons: string[] = [];
    if (!formData.quantity_value || !formData.quantity_unit) {
      blockingReasons.push("Quantity value and approved unit are required for matching.");
    }
    if (!formData.delivery_location.trim()) {
      blockingReasons.push("Delivery destination must be specified.");
    }
    if (mandatoryList.length === 0) {
      blockingReasons.push("At least one mandatory eligibility condition is required.");
    }

    const isReady = blockingReasons.length === 0 && targetStatus !== "Draft";
    const completeness = blockingReasons.length === 0 ? "Complete" : "Incomplete";

    const newReq: BuyerRequirement = {
      requirement_id: `REQ-${new Date().getFullYear()}-${String(requirements.length + 1).padStart(3, "0")}`,
      buyer_organisation_name: formData.buyer_organisation_name.trim(),
      buyer_reference: formData.buyer_reference.trim() || undefined,
      owner_user_id: "priyanka.singh",
      target_market: formData.target_market,
      product_category_id: formData.product_category_id,
      requirement_title: formData.requirement_title.trim(),
      product_specifications: formData.product_specifications.trim() || undefined,
      quantity_value: formData.quantity_value ? Number(formData.quantity_value) : undefined,
      quantity_unit: formData.quantity_unit,
      order_frequency: formData.order_frequency,
      target_price_min: formData.target_price_min ? Number(formData.target_price_min) : undefined,
      target_price_max: formData.target_price_max ? Number(formData.target_price_max) : undefined,
      currency_code: formData.currency_code,
      price_basis: formData.price_basis,
      delivery_location: formData.delivery_location.trim() || undefined,
      delivery_window_start: formData.delivery_window_start || undefined,
      delivery_window_end: formData.delivery_window_end || undefined,
      required_lead_time_value: formData.required_lead_time_value ? Number(formData.required_lead_time_value) : undefined,
      required_lead_time_unit: formData.required_lead_time_unit,
      mandatory_criteria: mandatoryList.map((m, i) => ({ id: `m-${i}`, name: m, type: "mandatory" })),
      preferred_criteria: preferredList.map((p, i) => ({ id: `p-${i}`, name: p, type: "preferred" })),
      requirement_notes: formData.requirement_notes.trim() || undefined,
      requirement_status: isReady ? "Ready for Matching" : targetStatus,
      completeness_status: completeness,
      matching_ready: isReady,
      blocking_reasons: blockingReasons.length > 0 ? blockingReasons : undefined,
      version: 1,
      created_at: new Date().toISOString(),
    };

    createRequirementMutation.mutate(newReq);
  };

  const handleUpdateStatus = (reqId: string, newStatus: RequirementStatus) => {
    const payload = {
      requirement_status: newStatus,
      matching_ready: newStatus === "Ready for Matching" ? true : undefined,
    };
    updateRequirementMutation.mutate({ id: reqId, payload });
  };

  return (
    <div className={styles.container}>
      {/* ====================================================================
          PAGE HEADER
          ==================================================================== */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Buyer Procurement Requirements</h1>
          <p className={styles.pageSubtitle}>
            Capture commercial demand, enforce mandatory eligibility rules separately from preferences,
            and evaluate matching readiness gates before running candidate discovery.
          </p>
        </div>
        <div className={styles.headerActions}>
          <Button variant="primary" onClick={() => setIsCreateOpen(true)}>
            + Capture Requirement
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
            placeholder="Search by title, buyer organisation or ID..."
            className={styles.searchInput}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search buyer requirements"
          />
        </div>

        <div className={styles.filterGroup}>
          {/* Status Tabs */}
          <div className={styles.statusTabs} role="tablist" aria-label="Filter by requirement status">
            {(["All", "Draft", "In Review", "Ready for Matching", "Closed"] as const).map((status) => (
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

          {/* Category Filter */}
          <Select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{ width: "auto", fontSize: "0.8125rem", padding: "0.35rem 0.75rem" }}
            aria-label="Filter by category"
          >
            <option value="All">All Categories</option>
            {PRODUCT_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </Select>

          {/* Readiness Gate Filter */}
          <Select
            value={readinessFilter}
            onChange={(e) => setReadinessFilter(e.target.value as "All" | "Ready" | "Blocked")}
            style={{ width: "auto", fontSize: "0.8125rem", padding: "0.35rem 0.75rem" }}
            aria-label="Filter by matching readiness"
          >
            <option value="All">All Gates</option>
            <option value="Ready">Matching Ready</option>
            <option value="Blocked">Gate Blocked</option>
          </Select>
        </div>
      </div>

      {/* ====================================================================
          REQUIREMENTS ROSTER TABLE (BUY-SCR-01)
          ==================================================================== */}
      <div className={styles.tableCard}>
        <div className={styles.tableHeaderRow}>
          <span className={styles.tableCounter}>
            Showing {filteredRequirements.length} of {requirements.length} buyer requirements
          </span>
        </div>

        {isLoading ? (
          <div style={{ padding: "3rem" }}>
            <LoadingSpinner label="Loading buyer requirements..." />
          </div>
        ) : filteredRequirements.length === 0 ? (
          <EmptyState
            title="No Buyer Requirements Found"
            guidance={
              searchTerm || statusFilter !== "All"
                ? "No demand records match the current filter criteria."
                : "No buyer requirements have been captured yet. Create a requirement to define target criteria."
            }
            action={
              <Button variant="primary" onClick={() => setIsCreateOpen(true)}>
                Capture First Requirement
              </Button>
            }
          />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--color-border)", backgroundColor: "#FAF7F2", textAlign: "left" }}>
                  <th style={{ padding: "0.75rem 1.25rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Requirement / Buyer
                  </th>
                  <th style={{ padding: "0.75rem 1rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Category
                  </th>
                  <th style={{ padding: "0.75rem 1rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Quantity
                  </th>
                  <th style={{ padding: "0.75rem 1rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Target Price
                  </th>
                  <th style={{ padding: "0.75rem 1rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Status
                  </th>
                  <th style={{ padding: "0.75rem 1rem", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-text-muted)", letterSpacing: "0.05em" }}>
                    Matching Gate
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
                {filteredRequirements.map((req, idx) => (
                  <tr
                    key={req.requirement_id || (req as any).id || `req-${idx}`}
                    style={{ borderBottom: "1px solid var(--color-border-subtle)", transition: "background 0.15s ease" }}
                  >
                    <td style={{ padding: "0.9rem 1.25rem" }}>
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        <span style={{ fontWeight: 600, color: "var(--color-text-main)", fontSize: "0.9375rem" }}>
                          {req.requirement_title}
                        </span>
                        <span style={{ fontSize: "0.78rem", color: "var(--color-primary)", fontWeight: 500 }}>
                          {req.buyer_organisation_name}
                        </span>
                        <span style={{ fontSize: "0.72rem", color: "var(--color-text-muted)", fontFamily: "var(--font-family-mono)" }}>
                          {req.requirement_id} {req.buyer_reference && `· Ref: ${req.buyer_reference}`}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: "0.9rem 1rem", fontSize: "0.875rem", color: "var(--color-text-main)" }}>
                      {req.product_category_id}
                    </td>
                    <td style={{ padding: "0.9rem 1rem", fontSize: "0.875rem" }}>
                      {req.quantity_value ? (
                        <span>
                          <strong>{req.quantity_value.toLocaleString()}</strong> {req.quantity_unit}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td style={{ padding: "0.9rem 1rem", fontSize: "0.875rem" }}>
                      {req.target_price_min != null && req.target_price_max != null ? (
                        <span>
                          {req.currency_code} {req.target_price_min}–{req.target_price_max} ({req.price_basis})
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td style={{ padding: "0.9rem 1rem" }}>
                      <StatusBadge status={req.requirement_status} />
                    </td>
                    <td style={{ padding: "0.9rem 1rem" }}>
                      {req.matching_ready ? (
                        <span className={styles.readyBadge}>
                          ✓ Ready
                        </span>
                      ) : (
                        <span className={styles.blockedBadge} title={req.blocking_reasons?.join("; ")}>
                          ⚠ Incomplete
                        </span>
                      )}
                    </td>
                    <td style={{ padding: "0.9rem 1rem", fontSize: "0.75rem", color: "var(--color-text-muted)", fontFamily: "var(--font-family-mono)" }}>
                      v{req.version}
                    </td>
                    <td style={{ padding: "0.9rem 1.25rem", textAlign: "right" }}>
                      <div className={styles.actionBtnGroup} style={{ justifyContent: "flex-end" }}>
                        <button
                          type="button"
                          className={styles.actionLink}
                          onClick={() => {
                            setSelectedReqId(req.requirement_id);
                            setDetailTab("overview");
                          }}
                        >
                          Manage
                        </button>
                        {req.matching_ready && (
                          <Link href="/matching" className={styles.actionLink} style={{ color: "var(--color-success-text)" }}>
                            Match →
                          </Link>
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
          MODAL: CAPTURE NEW REQUIREMENT (BUY-SCR-02 - BUY-SCR-06)
          ==================================================================== */}
      {isCreateOpen && (
        <div className={styles.modalBackdrop} role="dialog" aria-modal="true" aria-labelledby="create-req-title">
          <div className={`${styles.modalCard} ${styles.modalCardWide}`}>
            <div className={styles.modalHeader}>
              <h2 id="create-req-title" className={styles.modalTitle}>Capture Buyer Requirement</h2>
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
              {/* SECTION 1: IDENTITY & TARGET DEMAND */}
              <span className={styles.sectionTitle}>1. Buyer Identity & Scope (BUY-002–007)</span>

              <div className={styles.formRow2}>
                <FormField
                  label="Buyer / Organisation Name"
                  htmlFor="buyer_name"
                  required
                  hint="Commercial demand entity (no external login implied)"
                  errors={formErrors.buyer_organisation_name}
                >
                  <Input
                    id="buyer_name"
                    required
                    placeholder="e.g. Shanghai Food & Spice Import Corp"
                    value={formData.buyer_organisation_name}
                    onChange={(e) => setFormData({ ...formData, buyer_organisation_name: e.target.value })}
                    hasError={Boolean(formErrors.buyer_organisation_name)}
                  />
                </FormField>

                <FormField label="Buyer Reference (Optional)" htmlFor="buyer_ref">
                  <Input
                    id="buyer_ref"
                    placeholder="e.g. BR-2026-088"
                    value={formData.buyer_reference}
                    onChange={(e) => setFormData({ ...formData, buyer_reference: e.target.value })}
                  />
                </FormField>
              </div>

              <div className={styles.formRow2}>
                <FormField
                  label="Requirement Title"
                  htmlFor="req_title"
                  required
                  errors={formErrors.requirement_title}
                >
                  <Input
                    id="req_title"
                    required
                    placeholder="e.g. Organic Tellicherry Black Pepper (500 MT)"
                    value={formData.requirement_title}
                    onChange={(e) => setFormData({ ...formData, requirement_title: e.target.value })}
                    hasError={Boolean(formErrors.requirement_title)}
                  />
                </FormField>

                <FormField label="Target Market (BUY-005)" htmlFor="target_market" hint="Intended market (distinct from delivery location)">
                  <Select
                    id="target_market"
                    value={formData.target_market}
                    onChange={(e) => setFormData({ ...formData, target_market: e.target.value })}
                  >
                    <option value="China">China (Mainland)</option>
                    <option value="India">India</option>
                    <option value="Southeast Asia">Southeast Asia</option>
                    <option value="Global">Global</option>
                  </Select>
                </FormField>
              </div>

              <div className={styles.formRow2}>
                <FormField label="Top-Level Category (BUY-006)" htmlFor="prod_cat" hint="7 approved working categories">
                  <Select
                    id="prod_cat"
                    value={formData.product_category_id}
                    onChange={(e) => setFormData({ ...formData, product_category_id: e.target.value as ProductCategory })}
                  >
                    {PRODUCT_CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </Select>
                </FormField>

                <FormField label="Delivery Destination (BUY-017)" htmlFor="delivery_loc" hint="Port or city where goods must arrive">
                  <Input
                    id="delivery_loc"
                    placeholder="e.g. Shanghai Port, China"
                    value={formData.delivery_location}
                    onChange={(e) => setFormData({ ...formData, delivery_location: e.target.value })}
                  />
                </FormField>
              </div>

              <FormField label="Product Technical Specifications (BUY-008)" htmlFor="specs">
                <Textarea
                  id="specs"
                  rows={2}
                  placeholder="Required chemistry, grade, mesh size, denier, dimensions, standard compliance..."
                  value={formData.product_specifications}
                  onChange={(e) => setFormData({ ...formData, product_specifications: e.target.value })}
                />
              </FormField>

              {/* SECTION 2: QUANTITY & COMMERCIAL TERMS */}
              <span className={styles.sectionTitle}>2. Quantity & Commercial Budget (BUY-009–015)</span>

              <div className={styles.formRow3}>
                <FormField
                  label="Quantity Value"
                  htmlFor="q_val"
                  errors={formErrors.quantity_value}
                >
                  <Input
                    id="q_val"
                    type="number"
                    min="1"
                    placeholder="e.g. 500"
                    value={formData.quantity_value}
                    onChange={(e) => setFormData({ ...formData, quantity_value: e.target.value })}
                    hasError={Boolean(formErrors.quantity_value)}
                  />
                </FormField>

                <FormField label="Quantity Unit (BUY-010)" htmlFor="q_unit">
                  <Select
                    id="q_unit"
                    value={formData.quantity_unit}
                    onChange={(e) => setFormData({ ...formData, quantity_unit: e.target.value })}
                  >
                    <option value="tonnes">tonnes</option>
                    <option value="kg">kg</option>
                    <option value="pieces">pieces</option>
                    <option value="meters">meters</option>
                    <option value="cartons">cartons</option>
                  </Select>
                </FormField>

                <FormField label="Order Frequency (BUY-011)" htmlFor="order_freq">
                  <Select
                    id="order_freq"
                    value={formData.order_frequency}
                    onChange={(e) => setFormData({ ...formData, order_frequency: e.target.value as OrderFrequency })}
                  >
                    <option value="One-off">One-off Demand</option>
                    <option value="Monthly">Monthly</option>
                    <option value="Quarterly">Quarterly</option>
                    <option value="Annual">Annual</option>
                  </Select>
                </FormField>
              </div>

              <div className={styles.formRow4}>
                <FormField label="Target Min Price" htmlFor="t_pmin">
                  <Input
                    id="t_pmin"
                    type="number"
                    step="0.01"
                    placeholder="Min"
                    value={formData.target_price_min}
                    onChange={(e) => setFormData({ ...formData, target_price_min: e.target.value })}
                  />
                </FormField>

                <FormField
                  label="Target Max Price"
                  htmlFor="t_pmax"
                  errors={formErrors.target_price_max}
                >
                  <Input
                    id="t_pmax"
                    type="number"
                    step="0.01"
                    placeholder="Max"
                    value={formData.target_price_max}
                    onChange={(e) => setFormData({ ...formData, target_price_max: e.target.value })}
                    hasError={Boolean(formErrors.target_price_max)}
                  />
                </FormField>

                <FormField label="Currency" htmlFor="t_curr">
                  <Select
                    id="t_curr"
                    value={formData.currency_code}
                    onChange={(e) => setFormData({ ...formData, currency_code: e.target.value })}
                  >
                    <option value="USD">USD ($)</option>
                    <option value="INR">INR (₹)</option>
                    <option value="CNY">CNY (¥)</option>
                  </Select>
                </FormField>

                <FormField label="Price Basis" htmlFor="t_basis">
                  <Select
                    id="t_basis"
                    value={formData.price_basis}
                    onChange={(e) => setFormData({ ...formData, price_basis: e.target.value })}
                  >
                    <option value="FOB">FOB</option>
                    <option value="CIF">CIF</option>
                    <option value="EXW">EXW</option>
                    <option value="Per piece">Per piece</option>
                    <option value="Per kg">Per kg</option>
                  </Select>
                </FormField>
              </div>

              {/* SECTION 3: DELIVERY DATES & LEAD TIME */}
              <span className={styles.sectionTitle}>3. Delivery Schedule & Lead Time (BUY-018–021)</span>

              <div className={styles.formRow3}>
                <FormField label="Delivery Window Start" htmlFor="d_start">
                  <Input
                    id="d_start"
                    type="date"
                    value={formData.delivery_window_start}
                    onChange={(e) => setFormData({ ...formData, delivery_window_start: e.target.value })}
                  />
                </FormField>

                <FormField label="Delivery Window End" htmlFor="d_end">
                  <Input
                    id="d_end"
                    type="date"
                    value={formData.delivery_window_end}
                    onChange={(e) => setFormData({ ...formData, delivery_window_end: e.target.value })}
                  />
                </FormField>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                  <FormField label="Max Lead Time" htmlFor="req_lt">
                    <Input
                      id="req_lt"
                      type="number"
                      placeholder="e.g. 30"
                      value={formData.required_lead_time_value}
                      onChange={(e) => setFormData({ ...formData, required_lead_time_value: e.target.value })}
                    />
                  </FormField>
                  <FormField label="Unit" htmlFor="req_lt_u">
                    <Select
                      id="req_lt_u"
                      value={formData.required_lead_time_unit}
                      onChange={(e) => setFormData({ ...formData, required_lead_time_unit: e.target.value })}
                    >
                      <option value="days">days</option>
                      <option value="weeks">weeks</option>
                      <option value="months">months</option>
                    </Select>
                  </FormField>
                </div>
              </div>

              {/* SECTION 4: MANDATORY ELIGIBILITY VS PREFERENCES BUILDER (BUY-SCR-06) */}
              <span className={styles.sectionTitle}>4. Eligibility Rules vs. Ranking Preferences (BUY-022 / BUY-023)</span>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                {/* Mandatory Box */}
                <div className={styles.criteriaBox}>
                  <div className={styles.criteriaHeader}>
                    <span style={{ fontWeight: 700, fontSize: "0.875rem", color: "var(--color-text-main)" }}>
                      Mandatory Eligibility Filters
                    </span>
                    <span className={styles.criteriaBadgeMandatory}>Hard Filter (Pass/Fail)</span>
                  </div>
                  <p style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                    Candidates failing any condition are excluded immediately. Preferences cannot override a failed rule.
                  </p>

                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {mandatoryList.map((crit, idx) => (
                      <div key={idx} className={styles.criteriaItemRow}>
                        <span style={{ fontSize: "0.8125rem", color: "var(--color-text-main)" }}>✓ {crit}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveMandatory(idx)}
                          style={{ border: "none", background: "none", color: "var(--color-danger-text)", cursor: "pointer", fontSize: "0.75rem" }}
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>

                  <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
                    <Input
                      placeholder="Add mandatory rule (e.g. Must have Organic Certificate)..."
                      value={newMandatoryInput}
                      onChange={(e) => setNewMandatoryInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddMandatory())}
                      style={{ fontSize: "0.8125rem" }}
                    />
                    <Button variant="secondary" type="button" onClick={handleAddMandatory}>
                      Add
                    </Button>
                  </div>
                </div>

                {/* Preference Box */}
                <div className={styles.criteriaBox}>
                  <div className={styles.criteriaHeader}>
                    <span style={{ fontWeight: 700, fontSize: "0.875rem", color: "var(--color-text-main)" }}>
                      Ranking Preferences
                    </span>
                    <span className={styles.criteriaBadgePreferred}>Soft Criteria (Scoring)</span>
                  </div>
                  <p style={{ fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
                    Desirable candidate attributes used strictly for score ranking among eligible candidates.
                  </p>

                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {preferredList.map((pref, idx) => (
                      <div key={idx} className={styles.criteriaItemRow}>
                        <span style={{ fontSize: "0.8125rem", color: "var(--color-text-main)" }}>★ {pref}</span>
                        <button
                          type="button"
                          onClick={() => handleRemovePreferred(idx)}
                          style={{ border: "none", background: "none", color: "var(--color-danger-text)", cursor: "pointer", fontSize: "0.75rem" }}
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>

                  <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
                    <Input
                      placeholder="Add preference (e.g. Prefer prompt lead time < 30 days)..."
                      value={newPreferredInput}
                      onChange={(e) => setNewPreferredInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddPreferred())}
                      style={{ fontSize: "0.8125rem" }}
                    />
                    <Button variant="secondary" type="button" onClick={handleAddPreferred}>
                      Add
                    </Button>
                  </div>
                </div>
              </div>

              {/* Context Notes */}
              <FormField label="Commercial Notes & Context (BUY-026)" htmlFor="notes">
                <Textarea
                  id="notes"
                  rows={2}
                  placeholder="Sampling protocol, commercial background, port handling notes..."
                  value={formData.requirement_notes}
                  onChange={(e) => setFormData({ ...formData, requirement_notes: e.target.value })}
                />
              </FormField>
            </div>

            <div className={styles.modalFooter}>
              <Button
                variant="outline"
                type="button"
                onClick={() => {
                  setIsCreateOpen(false);
                  handleResetForm();
                }}
              >
                Cancel
              </Button>
              <Button
                variant="secondary"
                type="button"
                onClick={() => handleSaveRequirement("Draft")}
              >
                Save as Draft
              </Button>
              <Button
                variant="primary"
                type="button"
                onClick={() => handleSaveRequirement("In Review")}
              >
                Validate & Evaluate Matching Gate
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ====================================================================
          MODAL: REQUIREMENT DETAILS & MATCHING READINESS GATE (BUY-SCR-07 - 09)
          ==================================================================== */}
      {selectedReq && (
        <div className={styles.modalBackdrop} role="dialog" aria-modal="true" aria-labelledby="detail-title">
          <div className={`${styles.modalCard} ${styles.modalCardWide}`}>
            <div className={styles.modalHeader}>
              <div>
                <h2 id="detail-title" className={styles.modalTitle}>{selectedReq.requirement_title}</h2>
                <span style={{ fontSize: "0.75rem", color: "var(--color-text-muted)", fontFamily: "var(--font-family-mono)" }}>
                  ID: {selectedReq.requirement_id} · Buyer: {selectedReq.buyer_organisation_name} · Version: v{selectedReq.version}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <StatusBadge status={selectedReq.requirement_status} />
                <button
                  type="button"
                  className={styles.modalCloseBtn}
                  onClick={() => setSelectedReqId(null)}
                  aria-label="Close details"
                >
                  &times;
                </button>
              </div>
            </div>

            {/* Navigation Tabs inside Detail Drawer */}
            <div style={{ padding: "0 1.75rem", backgroundColor: "#FAFAF8" }}>
              <div className={styles.detailTabs}>
                <button
                  type="button"
                  className={`${styles.detailTab} ${detailTab === "overview" ? styles.detailTabActive : ""}`}
                  onClick={() => setDetailTab("overview")}
                >
                  Overview & Commercial Terms
                </button>
                <button
                  type="button"
                  className={`${styles.detailTab} ${detailTab === "criteria" ? styles.detailTabActive : ""}`}
                  onClick={() => setDetailTab("criteria")}
                >
                  Eligibility vs. Preferences ({(selectedReq.mandatory_criteria?.length || 0) + (selectedReq.preferred_criteria?.length || 0)})
                </button>
                <button
                  type="button"
                  className={`${styles.detailTab} ${detailTab === "matching" ? styles.detailTabActive : ""}`}
                  onClick={() => setDetailTab("matching")}
                >
                  Matching Readiness Gate (BUY-032)
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
                        Target Market
                      </span>
                      <div style={{ fontSize: "0.9375rem", fontWeight: 600 }}>{selectedReq.target_market}</div>
                    </div>
                    <div>
                      <span style={{ fontSize: "0.6875rem", textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: 700 }}>
                        Delivery Destination
                      </span>
                      <div style={{ fontSize: "0.9375rem", fontWeight: 600 }}>{selectedReq.delivery_location || "Not specified"}</div>
                    </div>
                    <div>
                      <span style={{ fontSize: "0.6875rem", textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: 700 }}>
                        Category
                      </span>
                      <div style={{ fontSize: "0.9375rem", fontWeight: 600 }}>{selectedReq.product_category_id}</div>
                    </div>
                    <div>
                      <span style={{ fontSize: "0.6875rem", textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: 700 }}>
                        Completeness State
                      </span>
                      <div><StatusBadge status={selectedReq.completeness_status} /></div>
                    </div>
                  </div>

                  <div>
                    <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--color-primary)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                      Demand Specifications & Quantity
                    </h3>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem", fontSize: "0.875rem" }}>
                      <div>
                        <span style={{ color: "var(--color-text-muted)", display: "block" }}>Requested Quantity</span>
                        <strong>{selectedReq.quantity_value ? `${selectedReq.quantity_value.toLocaleString()} ${selectedReq.quantity_unit}` : "—"}</strong>
                      </div>
                      <div>
                        <span style={{ color: "var(--color-text-muted)", display: "block" }}>Cadence / Frequency</span>
                        <strong>{selectedReq.order_frequency || "One-off"}</strong>
                      </div>
                      <div>
                        <span style={{ color: "var(--color-text-muted)", display: "block" }}>Budget Range</span>
                        <strong>
                          {selectedReq.target_price_min != null && selectedReq.target_price_max != null
                            ? `${selectedReq.currency_code} ${selectedReq.target_price_min}–${selectedReq.target_price_max} (${selectedReq.price_basis})`
                            : "—"}
                        </strong>
                      </div>
                    </div>
                  </div>

                  {selectedReq.product_specifications && (
                    <div>
                      <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--color-primary)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                        Technical Specifications (BUY-008)
                      </h3>
                      <p style={{ fontSize: "0.875rem", color: "var(--color-text-main)", backgroundColor: "#FFFFFF", border: "1px solid var(--color-border-subtle)", padding: "0.75rem", borderRadius: "var(--radius-sm)" }}>
                        {selectedReq.product_specifications}
                      </p>
                    </div>
                  )}

                  <div>
                    <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--color-primary)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                      Delivery Window & Lead Time
                    </h3>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", fontSize: "0.875rem" }}>
                      <div>
                        <span style={{ color: "var(--color-text-muted)", display: "block" }}>Delivery Date Window</span>
                        <strong>
                          {selectedReq.delivery_window_start && selectedReq.delivery_window_end
                            ? `${selectedReq.delivery_window_start} to ${selectedReq.delivery_window_end}`
                            : "Flexible / Not defined"}
                        </strong>
                      </div>
                      <div>
                        <span style={{ color: "var(--color-text-muted)", display: "block" }}>Max Acceptable Lead Time</span>
                        <strong>
                          {selectedReq.required_lead_time_value ? `${selectedReq.required_lead_time_value} ${selectedReq.required_lead_time_unit}` : "—"}
                        </strong>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: CRITERIA BUILDER VIEW */}
              {detailTab === "criteria" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                  <div>
                    <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--color-danger-text)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                      Mandatory Eligibility Conditions (Hard Filters — Pass/Fail)
                    </h3>
                    <p style={{ fontSize: "0.78rem", color: "var(--color-text-muted)", marginBottom: "0.5rem" }}>
                      Evaluated first. Candidates that fail any mandatory condition cannot be promoted by preferences.
                    </p>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                      {selectedReq.mandatory_criteria && selectedReq.mandatory_criteria.length > 0 ? (
                        selectedReq.mandatory_criteria.map((crit) => (
                          <div key={crit.id} className={styles.criteriaItemRow} style={{ borderLeft: "3px solid var(--color-danger-text)" }}>
                            <span style={{ fontSize: "0.875rem", fontWeight: 600 }}>{crit.name}</span>
                            <span className={styles.criteriaBadgeMandatory}>Mandatory</span>
                          </div>
                        ))
                      ) : (
                        <span style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>No mandatory conditions defined.</span>
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--color-info-text)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                      Ranking Preferences (Soft Criteria — Scoring)
                    </h3>
                    <p style={{ fontSize: "0.78rem", color: "var(--color-text-muted)", marginBottom: "0.5rem" }}>
                      Applied strictly among eligible candidates to compute weighted similarity and fit ranking.
                    </p>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                      {selectedReq.preferred_criteria && selectedReq.preferred_criteria.length > 0 ? (
                        selectedReq.preferred_criteria.map((pref) => (
                          <div key={pref.id} className={styles.criteriaItemRow} style={{ borderLeft: "3px solid var(--color-info-text)" }}>
                            <span style={{ fontSize: "0.875rem", fontWeight: 600 }}>{pref.name}</span>
                            <span className={styles.criteriaBadgePreferred}>Preference</span>
                          </div>
                        ))
                      ) : (
                        <span style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>No preference criteria defined.</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: MATCHING READINESS GATE (BUY-032 / BUY-SCR-07) */}
              {detailTab === "matching" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                  <div className={`${styles.readinessGateCard} ${selectedReq.matching_ready ? styles.gateReady : styles.gateBlocked}`}>
                    <div>
                      <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>
                        {selectedReq.matching_ready ? "✓ Matching Readiness Gate Passed" : "⚠ Matching Gate Blocked — Incomplete Inputs"}
                      </h3>
                      <p style={{ fontSize: "0.8125rem", marginTop: "0.25rem" }}>
                        {selectedReq.matching_ready
                          ? "All minimum completeness requirements, commercial units, and mandatory eligibility criteria are satisfied. This demand is qualified to execute matching runs."
                          : "The matching engine cannot execute candidate discovery until all blocking reasons are resolved."}
                      </p>
                      {selectedReq.blocking_reasons && selectedReq.blocking_reasons.length > 0 && (
                        <ul className={styles.gateReasonsList}>
                          {selectedReq.blocking_reasons.map((reason, idx) => (
                            <li key={idx}><strong>Missing:</strong> {reason}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {selectedReq.matching_ready && (
                      <Link href="/matching" className={styles.actionLink} style={{ backgroundColor: "var(--color-primary)", color: "#FFFFFF", padding: "0.6rem 1.25rem", borderRadius: "var(--radius-full)", textDecoration: "none" }}>
                        Initiate Match Run →
                      </Link>
                    )}
                  </div>

                  <div style={{ backgroundColor: "#FAF7F2", border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)", padding: "1rem" }}>
                    <h4 style={{ fontSize: "0.8125rem", fontWeight: 700, color: "var(--color-primary)", textTransform: "uppercase", marginBottom: "0.4rem" }}>
                      Traceability & Versioning (BUY-030 / BUY-031)
                    </h4>
                    <p style={{ fontSize: "0.78rem", color: "var(--color-text-muted)" }}>
                      Every match run permanently records requirement <strong>v{selectedReq.version}</strong>. Any subsequent edits to criteria or commercial budget will generate a new immutable version without rewriting historical match runs.
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className={styles.modalFooter}>
              <div style={{ marginRight: "auto", display: "flex", gap: "0.5rem" }}>
                {selectedReq.requirement_status === "Draft" && (
                  <Button
                    variant="primary"
                    onClick={() => handleUpdateStatus(selectedReq.requirement_id, "Ready for Matching")}
                  >
                    Promote to Ready for Matching
                  </Button>
                )}
                {selectedReq.requirement_status === "Ready for Matching" && (
                  <Button
                    variant="outline"
                    onClick={() => handleUpdateStatus(selectedReq.requirement_id, "Closed")}
                  >
                    Close Requirement
                  </Button>
                )}
              </div>
              <Button variant="outline" onClick={() => setSelectedReqId(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
