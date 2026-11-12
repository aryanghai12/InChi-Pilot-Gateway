"use client";

import React, { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import styles from "./readiness.module.css";
import { apiFetch } from "@/lib/api/client";
import {
  SupplierAssessment,
  AssessmentStatus,
  AssessmentOutcome,
  CompletenessStatus,
  ReadinessQuestion,
  AssessmentAnswer,
  AssessmentHistoryEntry,
  Supplier,
  PaginatedSupplierList,
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

// ============================================================================
// Fixed, Versioned Question Set (v1.0-pilot-baseline per Build Manual §7 / D-03)
// ============================================================================
const QUESTION_SET_VERSION = "v1.0-pilot";

const READINESS_QUESTIONS: ReadinessQuestion[] = [
  // 1. Regulatory & Customs (GACC)
  {
    id: "Q-GACC-01",
    category: "Regulatory & Customs (GACC)",
    question_text: "Does the enterprise hold valid registration with China's General Administration of Customs (GACC / Decree 248/249) where applicable?",
    guidance: "Mandatory for food, agricultural, and regulated commodities entering mainland China.",
    is_mandatory: true,
    required_evidence_type: "GACC Registration Certificate",
  },
  {
    id: "Q-GACC-02",
    category: "Regulatory & Customs (GACC)",
    question_text: "Does the facility hold valid export phytosanitary or sanitary clearance from an authorized Indian agency (e.g. APEDA, EIA, FSSAI)?",
    guidance: "Must be active and accompanied by official laboratory inspection certificate.",
    is_mandatory: true,
    required_evidence_type: "Sanitary / Phytosanitary Certificate",
  },

  // 2. Standards & Chinese Labeling (GB Standards)
  {
    id: "Q-GB-01",
    category: "Standards & Packaging (GB)",
    question_text: "Are product technical specifications, formulation, and laboratory assays verified compliant with relevant National Standards of China (GB Standards)?",
    guidance: "Requires third-party or authorized lab test report referencing the relevant GB standard number.",
    is_mandatory: true,
    required_evidence_type: "GB Compliance Test Report",
  },
  {
    id: "Q-GB-02",
    category: "Standards & Packaging (GB)",
    question_text: "Are packaging formats and bilingual/Mandarin labels prepared in compliance with GB 7718 and China customs labelling rules?",
    guidance: "Outer carton and consumer packaging must include Chinese artwork spec with importer/distributor details.",
    is_mandatory: true,
    required_evidence_type: "Chinese Label Artwork Spec",
  },

  // 3. Mandarin Commercial Capability
  {
    id: "Q-MAND-01",
    category: "Mandarin Commercial Capability",
    question_text: "Does the supplier possess commercial product catalogs and technical specification sheets translated into Simplified Chinese?",
    guidance: "Improves buyer qualification speed and reduces trade negotiation friction.",
    is_mandatory: false,
    required_evidence_type: "Mandarin Product Catalog",
  },
  {
    id: "Q-MAND-02",
    category: "Mandarin Commercial Capability",
    question_text: "Does the enterprise have dedicated personnel, trade agents, or channels capable of real-time commercial communication in Beijing time zone?",
    guidance: "Evaluated during buyer matching to ensure responsive commercial follow-ups.",
    is_mandatory: false,
  },

  // 4. Financial Settlement & Logistics
  {
    id: "Q-FIN-01",
    category: "Financial Settlement & Logistics",
    question_text: "Does the supplier maintain active cross-border commercial banking channels supporting RMB (CIPS/CNY) or standard USD/EUR documentary letter of credit (L/C)?",
    guidance: "Bank must be able to receive cross-border remittances and comply with FEMA/RBI export settlement rules.",
    is_mandatory: true,
    required_evidence_type: "Bank Compliance Letter / Swift Confirmation",
  },
  {
    id: "Q-FIN-02",
    category: "Financial Settlement & Logistics",
    question_text: "Can the supplier provide verifiable Certificates of Origin (COO) for customs clearance at Chinese destination ports?",
    guidance: "Official COO issued by authorized agency (e.g. Export Promotion Council or Chamber of Commerce).",
    is_mandatory: true,
    required_evidence_type: "Certificate of Origin (COO) Template",
  },
];

export default function ReadinessPage() {
  const queryClient = useQueryClient();

  // Search & Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"All" | AssessmentStatus>("All");
  const [outcomeFilter, setOutcomeFilter] = useState<"All" | AssessmentOutcome>("All");
  const [completenessFilter, setCompletenessFilter] = useState<"All" | CompletenessStatus>("All");

  // Local state for standalone UI interaction (Zero Mock Data)
  const [localAssessments, setLocalAssessments] = useState<SupplierAssessment[]>([]);

  // Active Assessment Drawer
  const [activeAssessmentId, setActiveAssessmentId] = useState<string | null>(null);
  const [drawerTab, setDrawerTab] = useState<"questionnaire" | "decision" | "history">("questionnaire");
  const [showMissingDetails, setShowMissingDetails] = useState(false);

  // New Assessment Modal
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [newSupplierId, setNewSupplierId] = useState("");

  // Reviewer Decision Form State
  const [decisionOutcome, setDecisionOutcome] = useState<AssessmentOutcome>("China-ready");
  const [decisionReason, setDecisionReason] = useState("");
  const [decisionActionType, setDecisionActionType] = useState<"record_outcome" | "request_info">("record_outcome");

  // Notifications
  const [notification, setNotification] = useState<{
    type: "success" | "warning" | "error";
    title?: string;
    message: string;
  } | null>(null);

  // ==========================================================================
  // Backend Queries (TanStack Query — Dynamic Zero-Mock)
  // ==========================================================================
  const { data: remoteSuppliers = [] } = useQuery<Supplier[]>({
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

  const { data: remoteAssessments, isLoading } = useQuery<SupplierAssessment[]>({
    queryKey: ["assessments"],
    queryFn: async () => {
      try {
        const res = await apiFetch<SupplierAssessment[] | PaginatedResponse<SupplierAssessment>>("/api/v1/assessments/");
        return unwrapPaginated(res);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return [];
        throw err;
      }
    },
    retry: false,
  });

  // Effective assessments list
  const assessments: SupplierAssessment[] = remoteAssessments && remoteAssessments.length > 0
    ? remoteAssessments
    : localAssessments;

  // Active Assessment object
  const activeAssessment = useMemo(() => {
    return assessments.find((a) => a.assessment_id === activeAssessmentId) || null;
  }, [assessments, activeAssessmentId]);

  // ==========================================================================
  // Helper: Live Completeness Evaluation (M4-AC1)
  // ==========================================================================
  const calculateCompleteness = (answers: AssessmentAnswer[]): {
    completeness: CompletenessStatus;
    missingItems: string[];
  } => {
    const missing: string[] = [];

    READINESS_QUESTIONS.forEach((q) => {
      if (!q.is_mandatory) return;
      const ans = answers.find((a) => a.question_id === q.id);
      if (!ans || !ans.response || ans.response.trim() === "") {
        missing.push(`${q.category}: "${q.question_text}" is unanswered.`);
      }
    });

    return {
      completeness: missing.length === 0 ? "Complete" : "Incomplete",
      missingItems: missing,
    };
  };

  // Grouped questions by Category
  const questionsByCategory = useMemo(() => {
    const groups: Record<string, ReadinessQuestion[]> = {};
    READINESS_QUESTIONS.forEach((q) => {
      if (!groups[q.category]) groups[q.category] = [];
      groups[q.category].push(q);
    });
    return groups;
  }, []);

  // Filtered List
  const filteredAssessments = useMemo(() => {
    return assessments.filter((a) => {
      const matchSearch =
        a.supplier_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        a.assessment_id.toLowerCase().includes(searchTerm.toLowerCase());

      const matchStatus = statusFilter === "All" || a.status === statusFilter;
      const matchOutcome = outcomeFilter === "All" || a.outcome === outcomeFilter;
      const matchCompleteness = completenessFilter === "All" || a.completeness === completenessFilter;

      return matchSearch && matchStatus && matchOutcome && matchCompleteness;
    });
  }, [assessments, searchTerm, statusFilter, outcomeFilter, completenessFilter]);

  // Statistics
  const stats = useMemo(() => {
    const total = assessments.length;
    const submitted = assessments.filter((a) => a.status === "Submitted").length;
    const chinaReady = assessments.filter((a) => a.outcome === "China-ready" || a.outcome === "Conditionally ready").length;
    const incomplete = assessments.filter((a) => a.completeness === "Incomplete" || a.status === "More information required").length;
    return { total, submitted, chinaReady, incomplete };
  }, [assessments]);

  // Status counts for segmented tabs
  const statusCounts = useMemo(() => {
    return {
      All: assessments.length,
      Draft: assessments.filter((a) => a.status === "Draft").length,
      Submitted: assessments.filter((a) => a.status === "Submitted").length,
      "More information required": assessments.filter((a) => a.status === "More information required").length,
      Reviewed: assessments.filter((a) => a.status === "Reviewed").length,
    };
  }, [assessments]);

  const isAnyFilterActive = Boolean(
    searchTerm.trim() ||
    statusFilter !== "All" ||
    outcomeFilter !== "All" ||
    completenessFilter !== "All"
  );

  const handleResetFilters = () => {
    setSearchTerm("");
    setStatusFilter("All");
    setOutcomeFilter("All");
    setCompletenessFilter("All");
  };

  // ==========================================================================
  // Backend Mutations: REST Integration with Graceful 404 Fallback
  // ==========================================================================
  const createAssessmentMutation = useMutation({
    mutationFn: (payload: any) =>
      apiFetch<SupplierAssessment>("/api/v1/assessments/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (newAssessment) => {
      queryClient.invalidateQueries({ queryKey: ["assessments"] });
      setActiveAssessmentId(newAssessment.assessment_id || (newAssessment as any).id);
      setIsNewModalOpen(false);
      setNotification({
        type: "success",
        title: "Assessment Synchronized",
        message: `Assessment ${newAssessment.assessment_id || ""} successfully recorded in backend.`,
      });
    },
    onError: (err, variables: SupplierAssessment) => {
      if (err instanceof ApiError && err.status === 404) {
        // Fallback to local session preview if backend 404
        setLocalAssessments((prev) => [variables, ...prev]);
        setActiveAssessmentId(variables.assessment_id);
        setIsNewModalOpen(false);
        setNotification({
          type: "warning",
          title: "Preview Mode (Backend 404)",
          message: "Endpoint /api/v1/assessments/ is under construction. Assessment saved in local preview mode.",
        });
      } else {
        setNotification({
          type: "error",
          title: "Save Failed",
          message: err instanceof ApiError ? err.message : "Failed to create assessment.",
        });
      }
    },
  });

  const updateAssessmentMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) =>
      apiFetch<SupplierAssessment>(`/api/v1/assessments/${encodeURIComponent(id)}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assessments"] });
    },
    onError: (err, { id, payload }) => {
      if (err instanceof ApiError && err.status === 404) {
        setLocalAssessments((prev) =>
          prev.map((a) => (a.assessment_id === id ? { ...a, ...payload, updated_at: new Date().toISOString() } : a))
        );
      }
    },
  });

  // ==========================================================================
  // Actions: Answer Update
  // ==========================================================================
  const handleUpdateAnswer = (
    questionId: string,
    field: "response" | "notes" | "evidence_reference",
    value: string
  ) => {
    if (!activeAssessment) return;

    const existingAnswers = [...activeAssessment.answers];
    const idx = existingAnswers.findIndex((ans) => ans.question_id === questionId);

    if (idx >= 0) {
      existingAnswers[idx] = {
        ...existingAnswers[idx],
        [field]: value,
      };
    } else {
      existingAnswers.push({
        question_id: questionId,
        response: field === "response" ? (value as any) : "",
        notes: field === "notes" ? value : "",
        evidence_reference: field === "evidence_reference" ? value : "",
      });
    }

    const compResult = calculateCompleteness(existingAnswers);
    const updatedFields = {
      answers: existingAnswers,
      completeness: compResult.completeness,
      missing_items: compResult.missingItems,
    };

    setLocalAssessments((prev) =>
      prev.map((a) => {
        if (a.assessment_id !== activeAssessment.assessment_id) return a;
        return {
          ...a,
          ...updatedFields,
          updated_at: new Date().toISOString(),
        };
      })
    );

    updateAssessmentMutation.mutate({
      id: activeAssessment.assessment_id,
      payload: updatedFields,
    });
  };

  // ==========================================================================
  // Actions: Submit Assessment (M4-AC1 Guardrail)
  // ==========================================================================
  const handleSubmitAssessment = async () => {
    if (!activeAssessment) return;

    const comp = calculateCompleteness(activeAssessment.answers);
    if (comp.completeness === "Incomplete") {
      setNotification({
        type: "error",
        title: "Submission Blocked (M4-AC1)",
        message: `Assessment cannot be submitted while mandatory questions remain unanswered (${comp.missingItems.length} missing).`,
      });
      return;
    }

    const newHistoryEntry: AssessmentHistoryEntry = {
      id: `h-${Date.now()}`,
      action: activeAssessment.status === "More information required" ? "Resubmitted" : "Submitted",
      actor: "priyanka.singh",
      timestamp: new Date().toISOString(),
      notes: "Submitted for formal China-Readiness reviewer review.",
    };

    const payload = {
      status: "Submitted" as AssessmentStatus,
      outcome: "Pending review" as AssessmentOutcome,
      submitted_by: "priyanka.singh",
      submitted_at: new Date().toISOString(),
      history: [...(activeAssessment.history || []), newHistoryEntry],
    };

    setLocalAssessments((prev) =>
      prev.map((a) => {
        if (a.assessment_id !== activeAssessment.assessment_id) return a;
        return {
          ...a,
          ...payload,
          updated_at: new Date().toISOString(),
        };
      })
    );

    updateAssessmentMutation.mutate({
      id: activeAssessment.assessment_id,
      payload,
    });

    setNotification({
      type: "success",
      title: "Assessment Submitted",
      message: `${activeAssessment.assessment_id} for ${activeAssessment.supplier_name} has been submitted to the review queue.`,
    });
  };

  // ==========================================================================
  // Actions: Reviewer Decision (M4-AC2, M4-AC3)
  // ==========================================================================
  const handleRecordReview = () => {
    if (!activeAssessment) return;

    if (!decisionReason.trim()) {
      setNotification({
        type: "error",
        title: "Review Reason Required (M4-AC3)",
        message: "You must record an explicit reason or audit note when setting an outcome or requesting clarification.",
      });
      return;
    }

    if (decisionActionType === "request_info") {
      const newHistoryEntry: AssessmentHistoryEntry = {
        id: `h-${Date.now()}`,
        action: "Returned for info",
        actor: "aryan.ghai (Reviewer)",
        timestamp: new Date().toISOString(),
        notes: decisionReason,
      };

      const payload = {
        status: "More information required" as AssessmentStatus,
        outcome_reason: decisionReason,
        history: [...(activeAssessment.history || []), newHistoryEntry],
      };

      setLocalAssessments((prev) =>
        prev.map((a) => {
          if (a.assessment_id !== activeAssessment.assessment_id) return a;
          return {
            ...a,
            ...payload,
            updated_at: new Date().toISOString(),
          };
        })
      );

      updateAssessmentMutation.mutate({
        id: activeAssessment.assessment_id,
        payload,
      });

      setNotification({
        type: "warning",
        title: "Clarification Requested",
        message: `Assessment ${activeAssessment.assessment_id} returned to Commercial Analyst for more information.`,
      });
    } else {
      // Record final human-set outcome (M4-AC2)
      const newHistoryEntry: AssessmentHistoryEntry = {
        id: `h-${Date.now()}`,
        action: "Outcome recorded",
        actor: "aryan.ghai (Reviewer)",
        timestamp: new Date().toISOString(),
        outcome: decisionOutcome,
        notes: decisionReason,
      };

      const payload = {
        status: "Reviewed" as AssessmentStatus,
        outcome: decisionOutcome,
        outcome_reason: decisionReason,
        reviewed_by: "aryan.ghai (Reviewer)",
        reviewed_at: new Date().toISOString(),
        history: [...(activeAssessment.history || []), newHistoryEntry],
      };

      setLocalAssessments((prev) =>
        prev.map((a) => {
          if (a.assessment_id !== activeAssessment.assessment_id) return a;
          return {
            ...a,
            ...payload,
            updated_at: new Date().toISOString(),
          };
        })
      );

      updateAssessmentMutation.mutate({
        id: activeAssessment.assessment_id,
        payload,
      });

      setNotification({
        type: "success",
        title: "Outcome Recorded",
        message: `Outcome "${decisionOutcome}" recorded for ${activeAssessment.supplier_name}.`,
      });
    }

    setDecisionReason("");
  };

  // ==========================================================================
  // Actions: Initiate New Assessment
  // ==========================================================================
  const handleCreateAssessment = () => {
    const selectedSupplier = remoteSuppliers.find((s) => s.supplier_id === newSupplierId);
    if (!selectedSupplier && !newSupplierId) {
      setNotification({
        type: "error",
        title: "Supplier Required",
        message: "Please select a registered supplier to initiate an assessment.",
      });
      return;
    }

    const supplierId = selectedSupplier?.supplier_id || newSupplierId;
    const supplierName = selectedSupplier?.legal_name || "Registered Supplier";

    const newId = `ASM-2026-${String(assessments.length + 1).padStart(3, "0")}`;
    const initialAnswers: AssessmentAnswer[] = READINESS_QUESTIONS.map((q) => ({
      question_id: q.id,
      response: "",
      notes: "",
    }));

    const initialComp = calculateCompleteness(initialAnswers);

    const newAssessment: SupplierAssessment = {
      assessment_id: newId,
      supplier_id: supplierId,
      supplier_name: supplierName,
      question_set_version: QUESTION_SET_VERSION,
      status: "Draft",
      completeness: initialComp.completeness,
      outcome: "Pending review",
      missing_items: initialComp.missingItems,
      answers: initialAnswers,
      history: [
        {
          id: `h-${Date.now()}`,
          action: "Created",
          actor: "priyanka.singh",
          timestamp: new Date().toISOString(),
          notes: "Initial readiness assessment record created.",
        },
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setDrawerTab("questionnaire");
    createAssessmentMutation.mutate(newAssessment);
  };

  const handleOpenNewModal = () => {
    if (!newSupplierId && remoteSuppliers.length > 0) {
      setNewSupplierId(remoteSuppliers[0].supplier_id);
    }
    setIsNewModalOpen(true);
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <h1>China-Readiness Assessments</h1>
          <p className={styles.subtitle}>
            Stage 3 & Component 1 — Evaluate supplier trade compliance, National Standards (GB), and GACC registration.
          </p>
        </div>
        <div>
          <Button variant="primary" onClick={handleOpenNewModal}>
            + Initiate New Assessment
          </Button>
        </div>
      </div>

      {/* Notification Banner */}
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
          <span className={styles.statLabel}>Total Assessments</span>
          <span className={styles.statValue}>{stats.total}</span>
          <span className={styles.statHint}>Across active pilot suppliers</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Submitted / In Review</span>
          <span className={styles.statValue}>{stats.submitted}</span>
          <span className={styles.statHint}>Awaiting Reviewer action</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>China-Ready or Conditional</span>
          <span className={styles.statValue} style={{ color: "var(--color-primary)" }}>
            {stats.chinaReady}
          </span>
          <span className={styles.statHint}>Qualified for AI matching desk</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Gaps / Action Required</span>
          <span className={styles.statValue} style={{ color: "#b91c1c" }}>
            {stats.incomplete}
          </span>
          <span className={styles.statHint}>Mandatory items missing</span>
        </div>
      </div>

      {/* Controls & Filter Section (Elegant Toolbar & Status Tabs) */}
      <div className={styles.controlsSection}>
        {/* Status Segmented Tabs */}
        <div className={styles.statusTabsContainer}>
          <div className={styles.statusTabs} role="tablist">
            {(
              [
                { label: "All", value: "All" },
                { label: "Draft", value: "Draft" },
                { label: "Submitted", value: "Submitted" },
                { label: "More Info Required", value: "More information required" },
                { label: "Reviewed", value: "Reviewed" },
              ] as const
            ).map((tab) => {
              const isActive = statusFilter === tab.value;
              const count = statusCounts[tab.value];
              return (
                <button
                  key={tab.value}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  className={`${styles.statusTab} ${isActive ? styles.statusTabActive : ""}`}
                  onClick={() => setStatusFilter(tab.value as any)}
                >
                  <span>{tab.label}</span>
                  <span className={styles.tabBadge}>{count}</span>
                </button>
              );
            })}
          </div>

          {isAnyFilterActive && (
            <button
              type="button"
              className={styles.resetFiltersBtn}
              onClick={handleResetFilters}
            >
              ✕ Clear Filters
            </button>
          )}
        </div>

        {/* Toolbar: Search & Inline Filter Controls */}
        <div className={styles.toolbarCard}>
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
              placeholder="Search by supplier name or assessment ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button
                type="button"
                className={styles.searchClearBtn}
                onClick={() => setSearchTerm("")}
                aria-label="Clear search"
              >
                &times;
              </button>
            )}
          </div>

          <div className={styles.filterControlsRow}>
            <div className={styles.filterSelectWrapper}>
              <span className={styles.filterLabel}>Outcome:</span>
              <select
                className={styles.filterSelect}
                value={outcomeFilter}
                onChange={(e) => setOutcomeFilter(e.target.value as any)}
              >
                <option value="All">All Outcomes</option>
                <option value="Pending review">Pending Review</option>
                <option value="China-ready">China-Ready</option>
                <option value="Conditionally ready">Conditionally Ready</option>
                <option value="Not ready">Not Ready</option>
              </select>
            </div>

            <div className={styles.filterSelectWrapper}>
              <span className={styles.filterLabel}>Completeness:</span>
              <select
                className={styles.filterSelect}
                value={completenessFilter}
                onChange={(e) => setCompletenessFilter(e.target.value as any)}
              >
                <option value="All">All Completeness</option>
                <option value="Complete">Complete (Passed)</option>
                <option value="Incomplete">Incomplete (Blocked)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Assessments Roster */}
      <div className={styles.tableCard}>
        {isLoading ? (
          <div style={{ padding: "3rem", textAlign: "center" }}>
            <LoadingSpinner label="Loading assessments..." />
          </div>
        ) : filteredAssessments.length === 0 ? (
          <EmptyState
            title={isAnyFilterActive ? "No Matching Assessments" : "No Assessments Recorded"}
            guidance={
              isAnyFilterActive
                ? "No China-Readiness assessments match the selected search or filter criteria."
                : "No China-Readiness assessments have been created yet. Click '+ Initiate New Assessment' to evaluate a supplier."
            }
            action={
              isAnyFilterActive ? (
                <Button
                  variant="secondary"
                  onClick={handleResetFilters}
                >
                  Reset Filters
                </Button>
              ) : (
                <Button
                  variant="primary"
                  onClick={handleOpenNewModal}
                >
                  + Initiate New Assessment
                </Button>
              )
            }
          />
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Assessment ID</th>
                <th>Supplier Legal Name</th>
                <th>Question Set</th>
                <th>Workflow Status</th>
                <th>Completeness</th>
                <th>Human Outcome</th>
                <th>Last Updated</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredAssessments.map((a) => {
                const isComplete = a.completeness === "Complete";
                const isReady = a.outcome === "China-ready" || a.outcome === "Conditionally ready";

                return (
                  <tr key={a.assessment_id}>
                    <td>
                      <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{a.assessment_id}</span>
                    </td>
                    <td>
                      <strong>{a.supplier_name}</strong>
                    </td>
                    <td>
                      <span style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                        {a.question_set_version}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={a.status} />
                    </td>
                    <td>
                      <span className={`${styles.pillBadge} ${isComplete ? styles.pillReady : styles.pillBlocked}`}>
                        {isComplete ? "✓ Complete" : "⚠️ Incomplete"}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`${styles.pillBadge} ${
                          isReady
                            ? styles.pillReady
                            : a.outcome === "Not ready"
                            ? styles.pillBlocked
                            : styles.pillNeutral
                        }`}
                      >
                        {a.outcome}
                      </span>
                    </td>
                    <td style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                      {a.updated_at ? new Date(a.updated_at).toLocaleDateString() : "—"}
                    </td>
                    <td>
                      <Button
                        variant="secondary"
                        onClick={() => {
                          setActiveAssessmentId(a.assessment_id);
                          setDrawerTab("questionnaire");
                        }}
                      >
                        Open Assessment
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* ==================================================================== */}
      {/* Drawer: Assessment Questionnaire & Review Area                       */}
      {/* ==================================================================== */}
      {activeAssessment && (
        <div className={styles.drawerOverlay} onClick={() => setActiveAssessmentId(null)}>
          <div className={styles.drawer} onClick={(e) => e.stopPropagation()}>
            {/* Drawer Header */}
            <div className={styles.drawerHeader}>
              <div>
                <div className={styles.drawerTitle}>
                  {activeAssessment.assessment_id} — {activeAssessment.supplier_name}
                </div>
                <div className={styles.drawerMeta}>
                  <span>Version: {activeAssessment.question_set_version}</span>
                  <span>•</span>
                  <span>Status: <strong>{activeAssessment.status}</strong></span>
                  <span>•</span>
                  <span>Outcome: <strong>{activeAssessment.outcome}</strong></span>
                </div>
              </div>
              <button
                className={styles.closeButton}
                onClick={() => setActiveAssessmentId(null)}
                aria-label="Close drawer"
              >
                &times;
              </button>
            </div>

            {/* Drawer Tabs */}
            <div className={styles.drawerTabs}>
              <button
                className={`${styles.tabButton} ${drawerTab === "questionnaire" ? styles.tabButtonActive : ""}`}
                onClick={() => setDrawerTab("questionnaire")}
              >
                1. Questionnaire & Evidence
              </button>
              <button
                className={`${styles.tabButton} ${drawerTab === "decision" ? styles.tabButtonActive : ""}`}
                onClick={() => setDrawerTab("decision")}
              >
                2. Reviewer Decision (M4-AC2)
              </button>
              <button
                className={`${styles.tabButton} ${drawerTab === "history" ? styles.tabButtonActive : ""}`}
                onClick={() => setDrawerTab("history")}
              >
                3. Audit History ({activeAssessment.history?.length || 0})
              </button>
            </div>

            {/* Drawer Content */}
            <div className={styles.drawerBody}>
              {/* Tab 1: Questionnaire */}
              {drawerTab === "questionnaire" && (
                <>
                  {/* Completeness / Gate Alert */}
                  {activeAssessment.completeness === "Incomplete" ? (
                    <div className={`${styles.bannerBox} ${styles.bannerWarning}`}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                        <div className={styles.bannerTitle}>
                          ⚠️ Incomplete Assessment — Submission Blocked (M4-AC1)
                        </div>
                        <span style={{ fontSize: "0.75rem", fontWeight: 700, backgroundColor: "#fef3c7", color: "#92400e", padding: "0.2rem 0.5rem", borderRadius: "var(--radius-sm)" }}>
                          {activeAssessment.missing_items?.length || 0} Criteria Remaining
                        </span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.25rem", flexWrap: "wrap", gap: "0.5rem" }}>
                        <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                          Answer the criteria marked with the red <strong>Mandatory</strong> badge below to unlock submission.
                        </p>
                        {activeAssessment.missing_items && activeAssessment.missing_items.length > 0 && (
                          <button
                            type="button"
                            onClick={() => setShowMissingDetails(!showMissingDetails)}
                            style={{
                              background: "none",
                              border: "none",
                              fontSize: "0.75rem",
                              fontWeight: 600,
                              color: "var(--color-primary)",
                              cursor: "pointer",
                              textDecoration: "underline",
                              padding: 0,
                            }}
                          >
                            {showMissingDetails ? "Hide Missing List ▲" : `View Missing List (${activeAssessment.missing_items.length}) ▼`}
                          </button>
                        )}
                      </div>
                      {showMissingDetails && activeAssessment.missing_items && (
                        <ul className={styles.missingList} style={{ marginTop: "0.5rem" }}>
                          {activeAssessment.missing_items.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ) : (
                    <div className={`${styles.bannerBox} ${styles.bannerSuccess}`}>
                      <div className={styles.bannerTitle}>
                        ✓ All Mandatory Compliance Criteria Answered
                      </div>
                      <p style={{ margin: 0, fontSize: "0.8125rem" }}>
                        Completeness verified. Assessment is eligible for review queue submission. Note per M4-AC2: Completeness alone does not constitute "China-ready" status.
                      </p>
                    </div>
                  )}

                  {/* Clarification Note if More Info Required */}
                  {activeAssessment.status === "More information required" && activeAssessment.outcome_reason && (
                    <div className={`${styles.bannerBox} ${styles.bannerWarning}`}>
                      <div className={styles.bannerTitle}>
                        Clarification Requested by Reviewer:
                      </div>
                      <p style={{ margin: 0, fontSize: "0.8125rem" }}>
                        {activeAssessment.outcome_reason}
                      </p>
                    </div>
                  )}

                  {/* Render Questions by Category */}
                  {Object.entries(questionsByCategory).map(([category, questions]) => {
                    const answeredCount = questions.filter((q) => {
                      const ans = activeAssessment.answers.find((a) => a.question_id === q.id);
                      return ans && ans.response && ans.response.trim() !== "";
                    }).length;
                    const isCategoryComplete = answeredCount === questions.length;

                    return (
                      <div key={category} className={styles.categorySection}>
                        <div className={styles.categoryHeader}>
                          <span className={styles.categoryTitle}>{category}</span>
                          <span
                            className={styles.categoryProgress}
                            style={{
                              fontWeight: 600,
                              color: isCategoryComplete ? "var(--color-success-text)" : "var(--color-text-muted)",
                            }}
                          >
                            {isCategoryComplete ? "✓ All Answered" : `${answeredCount} of ${questions.length} Answered`}
                          </span>
                        </div>
                        <div className={styles.questionsList}>
                        {questions.map((q) => {
                          const answer = activeAssessment.answers.find((ans) => ans.question_id === q.id) || {
                            question_id: q.id,
                            response: "",
                            notes: "",
                            evidence_reference: "",
                          };

                          return (
                            <div key={q.id} className={styles.questionItem}>
                              <div className={styles.questionTop}>
                                <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                    <span className={styles.questionText}>{q.question_text}</span>
                                    {q.is_mandatory ? (
                                      <span className={styles.mandatoryBadge}>Mandatory</span>
                                    ) : (
                                      <span className={styles.optionalBadge}>Optional</span>
                                    )}
                                  </div>
                                  <span className={styles.questionGuidance}>{q.guidance}</span>
                                </div>
                              </div>

                              {/* Radio Response Options */}
                              <div className={styles.responseOptions}>
                                {(["Yes", "No", "In Progress", "N/A"] as const).map((opt) => {
                                  const isSelected = answer.response === opt;
                                  let selectedClass = "";
                                  if (isSelected) {
                                    if (opt === "Yes") selectedClass = styles.responseSelectedYes;
                                    else if (opt === "No") selectedClass = styles.responseSelectedNo;
                                    else if (opt === "In Progress") selectedClass = styles.responseSelectedInProgress;
                                    else if (opt === "N/A") selectedClass = styles.responseSelectedNA;
                                  }

                                  return (
                                    <button
                                      key={opt}
                                      type="button"
                                      className={`${styles.responseButton} ${selectedClass}`}
                                      onClick={() => handleUpdateAnswer(q.id, "response", opt)}
                                    >
                                      {opt}
                                    </button>
                                  );
                                })}
                              </div>

                              {/* Notes & Evidence Link Inputs */}
                              <div className={styles.questionDetails}>
                                <Input
                                  placeholder="Compliance notes / qualification details..."
                                  value={answer.notes || ""}
                                  onChange={(e) => handleUpdateAnswer(q.id, "notes", e.target.value)}
                                />
                                <Input
                                  placeholder={q.required_evidence_type ? `Evidence ref (e.g. ${q.required_evidence_type})...` : "Optional evidence metadata reference..."}
                                  value={answer.evidence_reference || ""}
                                  onChange={(e) => handleUpdateAnswer(q.id, "evidence_reference", e.target.value)}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
                </>
              )}

              {/* Tab 2: Reviewer Decision (M4-AC2, M4-AC3) */}
              {drawerTab === "decision" && (
                <div className={styles.reviewBox}>
                  <div className={styles.reviewBoxHeader}>
                    Reviewer Assessment Decision (M4-AC2 / M4-AC3)
                  </div>
                  <p style={{ fontSize: "0.875rem", color: "var(--color-text-muted)", margin: 0 }}>
                    In accordance with InChi Pilot AI Governance, readiness outcomes cannot be assigned automatically. Only an authorized Reviewer can set the outcome or request clarification.
                  </p>

                  <FormField label="Review Action Type">
                    <Select
                      value={decisionActionType}
                      onChange={(e) => setDecisionActionType(e.target.value as any)}
                    >
                      <option value="record_outcome">Record Final Assessment Outcome</option>
                      <option value="request_info">Return for Clarification (More Information Required)</option>
                    </Select>
                  </FormField>

                  {decisionActionType === "record_outcome" && (
                    <FormField label="China-Readiness Outcome (Human-Set)">
                      <Select
                        value={decisionOutcome}
                        onChange={(e) => setDecisionOutcome(e.target.value as any)}
                      >
                        <option value="China-ready">China-Ready (Full trade compliance verified)</option>
                        <option value="Conditionally ready">Conditionally Ready (Actionable minor conditions pending)</option>
                        <option value="Not ready">Not Ready (Significant regulatory / standards gaps)</option>
                      </Select>
                    </FormField>
                  )}

                  <FormField
                    label="Decision Rationale / Review Notes (Mandatory)"
                    required
                    hint="Explain evidence reviewed, conditions required, or reasons for return."
                  >
                    <Textarea
                      rows={4}
                      placeholder="e.g. GACC registration verified against Decree 248. Lab reports confirmed GB compliance. Approved for AI Match Desk."
                      value={decisionReason}
                      onChange={(e) => setDecisionReason(e.target.value)}
                    />
                  </FormField>

                  <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "0.5rem" }}>
                    <Button
                      variant={decisionActionType === "request_info" ? "secondary" : "primary"}
                      onClick={handleRecordReview}
                    >
                      {decisionActionType === "request_info" ? "Request Clarification" : "Record Assessment Outcome"}
                    </Button>
                  </div>
                </div>
              )}

              {/* Tab 3: History Timeline */}
              {drawerTab === "history" && (
                <div className={styles.historyTimeline}>
                  {(!activeAssessment.history || activeAssessment.history.length === 0) ? (
                    <p style={{ color: "var(--color-text-muted)", fontSize: "0.875rem" }}>No audit history recorded yet.</p>
                  ) : (
                    activeAssessment.history.map((h) => (
                      <div key={h.id} className={styles.historyItem}>
                        <div className={styles.historyDot} />
                        <div className={styles.historyHeader}>
                          <span className={styles.historyAction}>
                            {h.action} {h.outcome ? `→ ${h.outcome}` : ""}
                          </span>
                          <span className={styles.historyTime}>
                            {new Date(h.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <div style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                          Actor: <strong>{h.actor}</strong>
                        </div>
                        {h.notes && <div className={styles.historyNotes}>{h.notes}</div>}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Drawer Footer Actions */}
            <div className={styles.drawerFooter}>
              <div>
                <span style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                  Current Completeness: <strong>{activeAssessment.completeness}</strong>
                </span>
              </div>
              <div style={{ display: "flex", gap: "0.75rem" }}>
                <Button variant="secondary" onClick={() => setActiveAssessmentId(null)}>
                  Close
                </Button>
                {activeAssessment.status !== "Reviewed" && (
                  <Button
                    variant="primary"
                    disabled={activeAssessment.completeness === "Incomplete"}
                    onClick={handleSubmitAssessment}
                  >
                    {activeAssessment.status === "Submitted" ? "Update Submission" : "Submit for Review"}
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* Modal: Initiate New Assessment                                       */}
      {/* ==================================================================== */}
      {isNewModalOpen && (
        <div className={styles.modalOverlay} onClick={() => setIsNewModalOpen(false)}>
          <div
            className={styles.modalDialog}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "0.5rem", color: "var(--color-text-main)" }}>
              Initiate China-Readiness Assessment
            </h2>
            <p style={{ fontSize: "0.875rem", color: "var(--color-text-muted)", marginBottom: "1.25rem" }}>
              Select a registered supplier to begin an evaluation against the approved {QUESTION_SET_VERSION} criteria set.
            </p>

            <FormField label="Supplier Organisation" required>
              <Select
                value={newSupplierId}
                onChange={(e) => setNewSupplierId(e.target.value)}
              >
                {remoteSuppliers.length === 0 ? (
                  <option value="">No registered suppliers found</option>
                ) : (
                  remoteSuppliers.map((s) => (
                    <option key={s.supplier_id} value={s.supplier_id}>
                      {s.legal_name} ({s.supplier_id})
                    </option>
                  ))
                )}
              </Select>
            </FormField>

            <div style={{ marginTop: "1rem", fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
              Question Set Version: <strong>{QUESTION_SET_VERSION}</strong> (GACC, GB Standards, Packaging, Cross-border Settlement).
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.5rem" }}>
              <Button variant="secondary" onClick={() => setIsNewModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                disabled={!newSupplierId && remoteSuppliers.length === 0}
                onClick={handleCreateAssessment}
              >
                Begin Assessment
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
