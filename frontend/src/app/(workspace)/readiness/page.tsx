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
  EvidenceCondition,
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

import {
  QUESTION_SET_VERSION,
  READINESS_QUESTIONS,
  EVIDENCE_CONDITIONS,
  calculateReadinessCompleteness,
  canSubmitAssessment,
  validateReviewDecision,
} from "@/lib/readiness/evaluation";

/**
 * Baseline v2.2 Section 11 Worked Examples:
 * Canonical test data representing an Eligible match, Information Required result, and Not Eligible case.
 */
const BASELINE_WORKED_EXAMPLES: SupplierAssessment[] = [
  {
    assessment_id: "ASM-2026-001",
    supplier_id: "SUP-001",
    supplier_name: "Bharat Precision Components Pvt Ltd",
    product_ids: ["PRD-001"],
    product_name: "Stainless steel valve body VB-40",
    questionnaire_version: QUESTION_SET_VERSION,
    status: "Review Complete",
    completeness: "Complete",
    outcome: "Ready for Matching",
    outcome_reason: "Mandatory criteria satisfied; ISO document authenticity to be checked before commercial commitment.",
    answers: [
      { question_id: "CR-01", response: "Bharat Precision Components Pvt Ltd, Plot 42, GIDC Industrial Estate, Vadodara, Gujarat, India" },
      { question_id: "CR-02", response: "MANUFACTURER - Direct manufacturer of precision industrial valves" },
      { question_id: "CR-03", response: "24AAACB1234D1Z5" },
      { question_id: "CR-04", response: "0310029384" },
      { question_id: "CR-05", response: "Germany, UAE, Vietnam" },
      { question_id: "CR-06", response: "PRD-001 (Stainless steel valve body VB-40)" },
      { question_id: "CR-07", response: "ENG_COMPONENT - HS Code 8481.80.30" },
      { question_id: "CR-08", response: "Yes", notes: "Complete technical drawings, alloy specs, and tolerances documented." },
      { question_id: "CR-09", response: "10,000 pieces per month" },
      { question_id: "CR-10", response: "MOQ: 1,000 pieces; Lead time: 28 calendar days" },
      { question_id: "CR-11", response: "45 USD / piece FOB Nhava Sheva" },
      { question_id: "CR-12", response: "Individual poly-wrapped, export wooden crates (IPPC ISPM-15 compliant)" },
      {
        question_id: "CR-13",
        response: "ISO 9001:2015 Certificate, Dimensional Test Report",
        evidence_reference: "ISO-9001-2015-BPC.pdf",
        evidence_condition: "DOCUMENT_RECEIVED_UNVERIFIED",
      },
      { question_id: "CR-14", response: "No", notes: "All test reports within 12 months validity." },
      { question_id: "CR-15", response: "GB/T 12224-2015 standard compliance declared." },
      { question_id: "CR-16", response: "English: Available; Mandarin: Draft technical datasheet" },
      { question_id: "CR-17", response: "Nhava Sheva Port, Ocean Freight, FOB" },
      { question_id: "CR-18", response: "Confirmed", is_limitation_declared: true, notes: "No known discrepancies." },
    ],
    history: [
      { id: "h-01", action: "Created", actor: "priyanka.singh", timestamp: "2026-11-16T09:00:00Z" },
      { id: "h-02", action: "Submitted", actor: "priyanka.singh", timestamp: "2026-11-16T11:30:00Z" },
      { id: "h-03", action: "Assignment accepted", actor: "aryan.ghai (Reviewer)", timestamp: "2026-11-16T14:00:00Z" },
      {
        id: "h-04",
        action: "Outcome recorded",
        actor: "aryan.ghai (Reviewer)",
        timestamp: "2026-11-16T15:30:00Z",
        outcome: "Ready for Matching",
        notes: "Mandatory criteria satisfied; ISO document authenticity to be checked before commercial commitment.",
      },
    ],
    created_at: "2026-11-16T09:00:00Z",
    updated_at: "2026-11-16T15:30:00Z",
  },
  {
    assessment_id: "ASM-2026-002",
    supplier_id: "SUP-002",
    supplier_name: "Southern Harvest Foods LLP",
    product_ids: ["PRD-002"],
    product_name: "Shelf-stable mango pulp",
    questionnaire_version: QUESTION_SET_VERSION,
    status: "Information Required",
    completeness: "Incomplete",
    outcome: "Information Required",
    outcome_reason: "Hold for Information, requesting a current laboratory report and confirmation of the required Brix specification.",
    missing_items: ["CR-14: Microbiological test report passed applicable expiry date."],
    answers: [
      { question_id: "CR-01", response: "Southern Harvest Foods LLP, 12 Krishnagiri Road, Salem, Tamil Nadu, India" },
      { question_id: "CR-02", response: "MANUFACTURER - Food processing and aseptic fruit puree canning" },
      { question_id: "CR-03", response: "33AABCS5678E1Z1" },
      { question_id: "CR-04", response: "0519098412" },
      { question_id: "CR-05", response: "Japan, Saudi Arabia" },
      { question_id: "CR-06", response: "PRD-002 (Shelf-stable mango pulp)" },
      { question_id: "CR-07", response: "SHELF_STABLE_FOOD - HS Code 2008.99.11" },
      { question_id: "CR-08", response: "Partial", notes: "Brix range 28-30% pending latest laboratory assay confirmation." },
      { question_id: "CR-09", response: "20 metric tonnes per month" },
      { question_id: "CR-10", response: "MOQ: 5 metric tonnes; Lead time: 21 calendar days" },
      { question_id: "CR-11", response: "1200 USD / metric tonne CIF Shanghai" },
      { question_id: "CR-12", response: "Aseptic bag in 215kg steel drums, 80 drums per 20ft FCL" },
      {
        question_id: "CR-13",
        response: "Product Test Report, Packaging Declaration",
        evidence_reference: "Microbial-Assay-2025.pdf",
        evidence_condition: "EXPIRED",
      },
      { question_id: "CR-14", response: "Yes", notes: "Microbial test report expired on 2026-09-30." },
      { question_id: "CR-15", response: "Unknown - GB 7718 China labelling compliance under review." },
      { question_id: "CR-16", response: "English: Available; Mandarin: Not Available" },
      { question_id: "CR-17", response: "Chennai Port, Ocean Freight, CIF" },
      { question_id: "CR-18", response: "Confirmed", is_limitation_declared: true, notes: "Expired test report declared." },
    ],
    history: [
      { id: "h-05", action: "Created", actor: "priyanka.singh", timestamp: "2026-11-17T10:00:00Z" },
      { id: "h-06", action: "Submitted", actor: "priyanka.singh", timestamp: "2026-11-17T12:00:00Z" },
      {
        id: "h-07",
        action: "Returned for info",
        actor: "aryan.ghai (Reviewer)",
        timestamp: "2026-11-17T14:45:00Z",
        notes: "Hold for Information, requesting a current report and confirmation of the required Brix specification.",
      },
    ],
    created_at: "2026-11-17T10:00:00Z",
    updated_at: "2026-11-17T14:45:00Z",
  },
  {
    assessment_id: "ASM-2026-003",
    supplier_id: "SUP-003",
    supplier_name: "Apex Chemical Industries",
    product_ids: ["PRD-003"],
    product_name: "Industrial additive",
    questionnaire_version: QUESTION_SET_VERSION,
    status: "Review Complete",
    completeness: "Complete",
    outcome: "Not Currently Eligible",
    outcome_reason: "Confirmed inability to supply small-batch trial demand; supplier MOQ is strictly fixed at 500 kg lots.",
    answers: [
      { question_id: "CR-01", response: "Apex Chemical Industries, GIDC Naroda, Ahmedabad, Gujarat, India" },
      { question_id: "CR-02", response: "TRADER - Chemical distribution without production facility" },
      { question_id: "CR-03", response: "24AAACA9876F1Z3" },
      { question_id: "CR-04", response: "0399887766" },
      { question_id: "CR-05", response: "None" },
      { question_id: "CR-06", response: "PRD-003 (Industrial additive)" },
      { question_id: "CR-07", response: "INDUSTRIAL_INPUT - HS Code 3824.99.00" },
      { question_id: "CR-08", response: "Yes", notes: "Standard technical datasheet provided." },
      { question_id: "CR-09", response: "5 metric tonnes per month" },
      { question_id: "CR-10", response: "MOQ: 500 kg; Lead time: 45 calendar days" },
      { question_id: "CR-11", response: "15 USD / kg FOB Mundra" },
      { question_id: "CR-12", response: "25kg multi-wall HDPE lined bags, shrink-wrapped on ISPM pallets" },
      { question_id: "CR-13", response: "Certificate of Analysis (COA)", evidence_reference: "COA-APEX.pdf", evidence_condition: "SELF_DECLARED" },
      { question_id: "CR-14", response: "No" },
      { question_id: "CR-15", response: "Unknown" },
      { question_id: "CR-16", response: "English: Available; Mandarin: Not Available" },
      { question_id: "CR-17", response: "Mundra Port, Ocean Freight, FOB" },
      { question_id: "CR-18", response: "Confirmed", is_limitation_declared: true, notes: "Strict MOQ 500kg confirmed." },
    ],
    history: [
      { id: "h-08", action: "Created", actor: "priyanka.singh", timestamp: "2026-11-18T08:30:00Z" },
      { id: "h-09", action: "Submitted", actor: "priyanka.singh", timestamp: "2026-11-18T10:15:00Z" },
      {
        id: "h-10",
        action: "Outcome recorded",
        actor: "aryan.ghai (Reviewer)",
        timestamp: "2026-11-18T13:00:00Z",
        outcome: "Not Currently Eligible",
        notes: "Confirmed inability to supply small-batch trial demand; supplier MOQ is strictly fixed at 500 kg lots.",
      },
    ],
    created_at: "2026-11-18T08:30:00Z",
    updated_at: "2026-11-18T13:00:00Z",
  },
];

export default function ReadinessPage() {
  const queryClient = useQueryClient();

  // Search & Filters (Baseline v2.2 Section 10.1)
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"All" | AssessmentStatus>("All");
  const [outcomeFilter, setOutcomeFilter] = useState<"All" | AssessmentOutcome>("All");
  const [completenessFilter, setCompletenessFilter] = useState<"All" | CompletenessStatus>("All");

  // Local state seeded with canonical Worked Examples from Section 11
  const [localAssessments, setLocalAssessments] = useState<SupplierAssessment[]>(BASELINE_WORKED_EXAMPLES);

  // Active Assessment Drawer State (SCR-03)
  const [activeAssessmentId, setActiveAssessmentId] = useState<string | null>(null);
  const [drawerTab, setDrawerTab] = useState<"questionnaire" | "decision" | "history">("questionnaire");
  const [showMissingDetails, setShowMissingDetails] = useState(false);

  // New Assessment Modal
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [newSupplierId, setNewSupplierId] = useState("");
  const [newProductName, setNewProductName] = useState("");

  // Reviewer Decision Form State (M4-AC2 / M4-AC3)
  const [decisionOutcome, setDecisionOutcome] = useState<AssessmentOutcome>("Ready for Matching");
  const [decisionReason, setDecisionReason] = useState("");
  const [decisionActionType, setDecisionActionType] = useState<"record_outcome" | "request_info">("record_outcome");

  // Notifications
  const [notification, setNotification] = useState<{
    type: "success" | "warning" | "error";
    title?: string;
    message: string;
  } | null>(null);

  // ==========================================================================
  // Backend Queries
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

  const assessments: SupplierAssessment[] =
    remoteAssessments && remoteAssessments.length > 0 ? remoteAssessments : localAssessments;

  const activeAssessment = useMemo(() => {
    return assessments.find((a) => a.assessment_id === activeAssessmentId) || null;
  }, [assessments, activeAssessmentId]);

  // Grouped questions by Category per Baseline v2.2 Section 6
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
        a.assessment_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (a.product_name && a.product_name.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchStatus = statusFilter === "All" || a.status === statusFilter;
      const matchOutcome = outcomeFilter === "All" || a.outcome === outcomeFilter;
      const matchCompleteness = completenessFilter === "All" || a.completeness === completenessFilter;

      return matchSearch && matchStatus && matchOutcome && matchCompleteness;
    });
  }, [assessments, searchTerm, statusFilter, outcomeFilter, completenessFilter]);

  // Summary Metrics (Strictly NO numeric score)
  const stats = useMemo(() => {
    const total = assessments.length;
    const submittedOrUnderReview = assessments.filter(
      (a) => a.status === "Submitted" || a.status === "Under Review"
    ).length;
    const readyForMatching = assessments.filter((a) => a.outcome === "Ready for Matching").length;
    const infoRequired = assessments.filter(
      (a) => a.outcome === "Information Required" || a.status === "Information Required"
    ).length;
    const notEligible = assessments.filter((a) => a.outcome === "Not Currently Eligible").length;
    return { total, submittedOrUnderReview, readyForMatching, infoRequired, notEligible };
  }, [assessments]);

  // Status counts for segmented tabs
  const statusCounts = useMemo(() => {
    return {
      All: assessments.length,
      Draft: assessments.filter((a) => a.status === "Draft").length,
      Submitted: assessments.filter((a) => a.status === "Submitted").length,
      "Under Review": assessments.filter((a) => a.status === "Under Review").length,
      "Information Required": assessments.filter(
        (a) => a.status === "Information Required" || a.status === "More information required"
      ).length,
      "Review Complete": assessments.filter(
        (a) => a.status === "Review Complete" || a.status === "Reviewed"
      ).length,
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
  // Backend Mutations
  // ==========================================================================
  const createAssessmentMutation = useMutation({
    mutationFn: (payload: SupplierAssessment) =>
      apiFetch<SupplierAssessment>("/api/v1/assessments/", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (newAssessment) => {
      queryClient.invalidateQueries({ queryKey: ["assessments"] });
      setActiveAssessmentId(newAssessment.assessment_id || null);
      setIsNewModalOpen(false);
      setNotification({
        type: "success",
        title: "Assessment Synchronized",
        message: `Assessment ${newAssessment.assessment_id} recorded in backend.`,
      });
    },
    onError: (err, variables: SupplierAssessment) => {
      setLocalAssessments((prev) => [variables, ...prev]);
      setActiveAssessmentId(variables.assessment_id);
      setIsNewModalOpen(false);
      setNotification({
        type: "warning",
        title: "Session Saved",
        message: "Assessment saved successfully in your active workspace session.",
      });
    },
  });

  const updateAssessmentMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<SupplierAssessment> | Record<string, unknown> }) =>
      apiFetch<SupplierAssessment>(`/api/v1/assessments/${encodeURIComponent(id)}/`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assessments"] });
    },
    onError: (err, { id, payload }) => {
      setLocalAssessments((prev) =>
        prev.map((a) => (a.assessment_id === id ? { ...a, ...payload, updated_at: new Date().toISOString() } : a))
      );
    },
  });

  // ==========================================================================
  // Answer Update Handler (Baseline v2.2 Section 6)
  // ==========================================================================
  const handleUpdateAnswer = (
    questionId: string,
    field: "response" | "notes" | "evidence_reference" | "evidence_condition" | "is_limitation_declared",
    value: unknown
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
        response: field === "response" ? String(value) : "",
        notes: field === "notes" ? String(value) : "",
        evidence_reference: field === "evidence_reference" ? String(value) : "",
        evidence_condition: field === "evidence_condition" ? (value as EvidenceCondition) : undefined,
        is_limitation_declared: field === "is_limitation_declared" ? Boolean(value) : undefined,
      });
    }

    const compResult = calculateReadinessCompleteness(existingAnswers);
    const updatedFields: Partial<SupplierAssessment> = {
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
  // Section 6.1 Submission Gate Execution
  // ==========================================================================
  const handleSubmitAssessment = async () => {
    if (!activeAssessment) return;

    const submissionCheck = canSubmitAssessment(activeAssessment.answers);
    if (!submissionCheck.canSubmit) {
      setNotification({
        type: "error",
        title: "Submission Blocked (Section 6.1 Gate)",
        message:
          submissionCheck.message ||
          "Assessment cannot be submitted while mandatory questions remain unanswered or unverified.",
      });
      return;
    }

    const newHistoryEntry: AssessmentHistoryEntry = {
      id: `h-${Date.now()}`,
      action: "Submitted",
      actor: "priyanka.singh (Contributor)",
      timestamp: new Date().toISOString(),
      notes: "Submitted for formal Reviewer China-Readiness assessment review.",
    };

    const payload: Partial<SupplierAssessment> = {
      status: "Submitted",
      outcome: "Pending review",
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
      message: `${activeAssessment.assessment_id} submitted to Reviewer queue under Baseline ${QUESTION_SET_VERSION}.`,
    });
  };

  // ==========================================================================
  // Reviewer Workflow: Accept Assignment (Section 8.1)
  // ==========================================================================
  const handleAcceptAssignment = () => {
    if (!activeAssessment) return;

    const newHistoryEntry: AssessmentHistoryEntry = {
      id: `h-${Date.now()}`,
      action: "Assignment accepted",
      actor: "aryan.ghai (Reviewer)",
      timestamp: new Date().toISOString(),
      notes: "Reviewer assigned and assessment moved to Under Review.",
    };

    const payload: Partial<SupplierAssessment> = {
      status: "Under Review",
      history: [...(activeAssessment.history || []), newHistoryEntry],
    };

    setLocalAssessments((prev) =>
      prev.map((a) => (a.assessment_id === activeAssessment.assessment_id ? { ...a, ...payload } : a))
    );

    updateAssessmentMutation.mutate({
      id: activeAssessment.assessment_id,
      payload,
    });

    setDrawerTab("decision");
    setNotification({
      type: "success",
      title: "Assignment Accepted",
      message: `${activeAssessment.assessment_id} is now Under Review.`,
    });
  };

  // ==========================================================================
  // Reviewer Workflow: Record Decision or Request Information (Section 4 & 8.1)
  // ==========================================================================
  const handleRecordReview = () => {
    if (!activeAssessment) return;

    const validation = validateReviewDecision(decisionActionType, decisionReason, decisionOutcome);
    if (!validation.isValid) {
      setNotification({
        type: "error",
        title: "Audit Rationale Required (M4-AC3)",
        message: validation.error || "Reviewer must record an explicit reason for the decision.",
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

      const payload: Partial<SupplierAssessment> = {
        status: "Information Required",
        outcome: "Information Required",
        outcome_reason: decisionReason,
        history: [...(activeAssessment.history || []), newHistoryEntry],
      };

      setLocalAssessments((prev) =>
        prev.map((a) => (a.assessment_id === activeAssessment.assessment_id ? { ...a, ...payload } : a))
      );

      updateAssessmentMutation.mutate({
        id: activeAssessment.assessment_id,
        payload,
      });

      setNotification({
        type: "warning",
        title: "Returned for Information",
        message: `Assessment ${activeAssessment.assessment_id} returned to Contributor for clarification.`,
      });
    } else {
      const newHistoryEntry: AssessmentHistoryEntry = {
        id: `h-${Date.now()}`,
        action: "Outcome recorded",
        actor: "aryan.ghai (Reviewer)",
        timestamp: new Date().toISOString(),
        outcome: decisionOutcome,
        notes: decisionReason,
      };

      const payload: Partial<SupplierAssessment> = {
        status: "Review Complete",
        outcome: decisionOutcome,
        outcome_reason: decisionReason,
        reviewed_by: "aryan.ghai (Reviewer)",
        reviewed_at: new Date().toISOString(),
        history: [...(activeAssessment.history || []), newHistoryEntry],
      };

      setLocalAssessments((prev) =>
        prev.map((a) => (a.assessment_id === activeAssessment.assessment_id ? { ...a, ...payload } : a))
      );

      updateAssessmentMutation.mutate({
        id: activeAssessment.assessment_id,
        payload,
      });

      setNotification({
        type: "success",
        title: "Review Complete",
        message: `Readiness outcome "${decisionOutcome}" officially recorded. Assessment locked.`,
      });
    }
  };

  // ==========================================================================
  // Initiate New Assessment (SCR-02 -> SCR-03)
  // ==========================================================================
  const handleCreateAssessment = () => {
    const selectedSupplier = remoteSuppliers.find((s) => s.supplier_id === newSupplierId);
    const supplierId = selectedSupplier?.supplier_id || newSupplierId || `SUP-${Date.now()}`;
    const supplierName = selectedSupplier?.legal_name || "Registered Supplier Enterprise";

    const newId = `ASM-2026-${String(assessments.length + 1).padStart(3, "0")}`;
    const initialAnswers: AssessmentAnswer[] = READINESS_QUESTIONS.map((q) => ({
      question_id: q.id,
      response: q.id === "CR-01" ? supplierName : q.id === "CR-06" ? newProductName || "" : "",
      notes: "",
      evidence_condition: undefined,
    }));

    const initialComp = calculateReadinessCompleteness(initialAnswers);

    const newAssessment: SupplierAssessment = {
      assessment_id: newId,
      supplier_id: supplierId,
      supplier_name: supplierName,
      product_ids: newProductName ? ["PRD-NEW"] : [],
      product_name: newProductName || undefined,
      questionnaire_version: QUESTION_SET_VERSION,
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
          notes: `Initial readiness assessment created under Baseline ${QUESTION_SET_VERSION}.`,
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

  // Check submission gate status for active assessment
  const activeSubmissionCheck = useMemo(() => {
    if (!activeAssessment) return { canSubmit: false, missingCount: 0, blockingItems: [] };
    return canSubmitAssessment(activeAssessment.answers);
  }, [activeAssessment]);

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <h1>China-Readiness Assessments</h1>
          <p className={styles.subtitle}>
            Baseline v2.2 — Standardized 18-question evaluation of Indian suppliers against Chinese buyer demand.
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

      {/* Stats Summary (Section 1: Categorical outcomes only, NO numeric score) */}
      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Total Assessments</span>
          <span className={styles.statValue}>{stats.total}</span>
          <span className={styles.statHint}>Baseline v2.2 registered evaluations</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Submitted / In Review</span>
          <span className={styles.statValue}>{stats.submittedOrUnderReview}</span>
          <span className={styles.statHint}>Awaiting Reviewer disposition</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Ready for Matching</span>
          <span className={styles.statValue} style={{ color: "var(--color-primary)" }}>
            {stats.readyForMatching}
          </span>
          <span className={styles.statHint}>Passed mandatory baseline gates</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statLabel}>Information Required</span>
          <span className={styles.statValue} style={{ color: "#b45309" }}>
            {stats.infoRequired}
          </span>
          <span className={styles.statHint}>Missing / expired evidence</span>
        </div>
      </div>

      {/* Controls & Filter Section (Section 8.1 Workflow States) */}
      <div className={styles.controlsSection}>
        <div className={styles.statusTabsContainer}>
          <div className={styles.statusTabs} role="tablist">
            {(
              [
                { label: "All", value: "All" },
                { label: "Draft", value: "Draft" },
                { label: "Submitted", value: "Submitted" },
                { label: "Under Review", value: "Under Review" },
                { label: "Info Required", value: "Information Required" },
                { label: "Review Complete", value: "Review Complete" },
              ] as const
            ).map((tab) => {
              const isActive = statusFilter === tab.value;
              const count = statusCounts[tab.value as keyof typeof statusCounts] ?? 0;
              return (
                <button
                  key={tab.value}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  className={`${styles.statusTab} ${isActive ? styles.statusTabActive : ""}`}
                  onClick={() => setStatusFilter(tab.value as "All" | AssessmentStatus)}
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

        {/* Toolbar: Search & Outcome Filter Controls */}
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
              placeholder="Search by supplier name, product, or assessment ID..."
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
                onChange={(e) => setOutcomeFilter(e.target.value as "All" | AssessmentOutcome)}
              >
                <option value="All">All Outcomes</option>
                <option value="Ready for Matching">Ready for Matching</option>
                <option value="Information Required">Information Required</option>
                <option value="Not Currently Eligible">Not Currently Eligible</option>
                <option value="Pending review">Pending Review</option>
              </select>
            </div>

            <div className={styles.filterSelectWrapper}>
              <span className={styles.filterLabel}>Completeness:</span>
              <select
                className={styles.filterSelect}
                value={completenessFilter}
                onChange={(e) => setCompletenessFilter(e.target.value as "All" | CompletenessStatus)}
              >
                <option value="All">All Completeness</option>
                <option value="Complete">Complete</option>
                <option value="Incomplete">Incomplete</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* SCR-02 / SCR-03 Assessment Table */}
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
                ? "No assessments match the selected search or filter criteria."
                : "No assessments have been recorded yet. Click '+ Initiate New Assessment' to evaluate a supplier."
            }
            action={
              isAnyFilterActive ? (
                <Button variant="secondary" onClick={handleResetFilters}>
                  Reset Filters
                </Button>
              ) : (
                <Button variant="primary" onClick={handleOpenNewModal}>
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
                <th>Assessed Product</th>
                <th>Baseline Version</th>
                <th>Workflow State</th>
                <th>Readiness Outcome</th>
                <th>Last Updated</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredAssessments.map((a, idx) => {
                const isReady = a.outcome === "Ready for Matching";
                const isInfoReq = a.outcome === "Information Required";
                const isNotEligible = a.outcome === "Not Currently Eligible";

                return (
                  <tr key={a.assessment_id || `assessment-${idx}`}>
                    <td>
                      <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{a.assessment_id}</span>
                    </td>
                    <td>
                      <strong>{a.supplier_name}</strong>
                    </td>
                    <td>
                      <span style={{ fontSize: "0.8125rem", color: "var(--color-text-main)" }}>
                        {a.product_name || a.product_ids?.[0] || "All supplier products"}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                        {a.questionnaire_version || QUESTION_SET_VERSION}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={a.status} />
                    </td>
                    <td>
                      <span
                        className={`${styles.pillBadge} ${
                          isReady
                            ? styles.pillReady
                            : isInfoReq
                            ? styles.pillBlocked
                            : isNotEligible
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
      {/* SCR-03 Readiness Assessment Drawer (Section 6 & 10)                  */}
      {/* ==================================================================== */}
      {activeAssessment && (
        <div className={styles.drawerOverlay} onClick={() => setActiveAssessmentId(null)}>
          <div className={styles.drawer} onClick={(e) => e.stopPropagation()}>
            {/* Drawer Header & SCR-03 Context Bar */}
            <div className={styles.drawerHeader}>
              <div>
                <div className={styles.drawerTitle}>
                  {activeAssessment.assessment_id} — {activeAssessment.supplier_name}
                </div>
                <div className={styles.drawerMeta}>
                  <span>Version: <strong>{activeAssessment.questionnaire_version}</strong></span>
                  <span>•</span>
                  <span>State: <strong>{activeAssessment.status}</strong></span>
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

            {/* SCR-03 Context Info Bar */}
            <div style={{ padding: "0.75rem 1.5rem", borderBottom: "1px solid var(--color-border)" }}>
              <div className={styles.contextBar}>
                <div className={styles.contextItem}>
                  <span className={styles.contextLabel}>Supplier</span>
                  <span className={styles.contextValue}>{activeAssessment.supplier_name}</span>
                </div>
                <div className={styles.contextItem}>
                  <span className={styles.contextLabel}>Product Record</span>
                  <span className={styles.contextValue}>{activeAssessment.product_name || "Linked via CR-06"}</span>
                </div>
                <div className={styles.contextItem}>
                  <span className={styles.contextLabel}>Baseline Specification</span>
                  <span className={styles.contextValue}>{activeAssessment.questionnaire_version}</span>
                </div>
                <div className={styles.contextItem}>
                  <span className={styles.contextLabel}>Human Disposition</span>
                  <span className={styles.contextValue}>{activeAssessment.outcome}</span>
                </div>
              </div>
            </div>

            {/* Drawer Tabs */}
            <div className={styles.drawerTabs}>
              <button
                className={`${styles.tabButton} ${drawerTab === "questionnaire" ? styles.tabButtonActive : ""}`}
                onClick={() => setDrawerTab("questionnaire")}
              >
                1. Questionnaire & Evidence (18 Items)
              </button>
              <button
                className={`${styles.tabButton} ${drawerTab === "decision" ? styles.tabButtonActive : ""}`}
                onClick={() => setDrawerTab("decision")}
              >
                2. Reviewer Decision Desk
              </button>
              <button
                className={`${styles.tabButton} ${drawerTab === "history" ? styles.tabButtonActive : ""}`}
                onClick={() => setDrawerTab("history")}
              >
                3. Audit History ({activeAssessment.history?.length || 0})
              </button>
            </div>

            {/* Drawer Body */}
            <div className={styles.drawerBody}>
              {/* Tab 1: Questionnaire */}
              {drawerTab === "questionnaire" && (
                <>
                  {/* Section 6.1 Submission Gate Progress Banner */}
                  {!activeSubmissionCheck.canSubmit ? (
                    <div className={`${styles.bannerBox} ${styles.bannerWarning}`}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                        <div className={styles.bannerTitle}>
                          ⚠️ Submission Gate: {activeSubmissionCheck.missingCount} Criteria Unresolved
                        </div>
                        <span style={{ fontSize: "0.75rem", fontWeight: 700, backgroundColor: "#fef3c7", color: "#92400e", padding: "0.2rem 0.5rem", borderRadius: "var(--radius-sm)" }}>
                          Submission Blocked
                        </span>
                      </div>
                      <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
                        Per Baseline v2.2 Section 6.1, all mandatory baseline questions must be answered, at least one Product record linked, and CR-18 confirmed.
                      </p>
                      {activeSubmissionCheck.blockingItems.length > 0 && (
                        <div>
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
                              marginTop: "0.25rem",
                            }}
                          >
                            {showMissingDetails ? "Hide Blocking Items ▲" : `View Blocking Items (${activeSubmissionCheck.blockingItems.length}) ▼`}
                          </button>
                          {showMissingDetails && (
                            <ul className={styles.missingList} style={{ marginTop: "0.5rem" }}>
                              {activeSubmissionCheck.blockingItems.map((item, idx) => (
                                <li key={idx}>{item}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className={`${styles.bannerBox} ${styles.bannerSuccess}`}>
                      <div className={styles.bannerTitle}>
                        ✓ Section 6.1 Submission Gate Passed
                      </div>
                      <p style={{ margin: 0, fontSize: "0.8125rem" }}>
                        All 18 baseline criteria verified and confirmed. Ready for formal Reviewer evaluation.
                      </p>
                    </div>
                  )}

                  {/* Clarification Note if More Info Required */}
                  {activeAssessment.status === "Information Required" && activeAssessment.outcome_reason && (
                    <div className={`${styles.bannerBox} ${styles.bannerWarning}`}>
                      <div className={styles.bannerTitle}>
                        Clarification Requested by Reviewer:
                      </div>
                      <p style={{ margin: 0, fontSize: "0.8125rem" }}>
                        {activeAssessment.outcome_reason}
                      </p>
                    </div>
                  )}

                  {/* 18 Baseline Questions Grouped by Category */}
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
                              evidence_condition: undefined,
                            };

                            return (
                              <div key={q.id} className={styles.questionItem}>
                                <div className={styles.questionTop}>
                                  <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                      <span style={{ fontFamily: "monospace", fontWeight: 700, color: "var(--color-primary)" }}>
                                        {q.id}
                                      </span>
                                      <span className={styles.questionText}>{q.question_text}</span>
                                      {q.is_mandatory ? (
                                        <span className={styles.mandatoryBadge}>Mandatory</span>
                                      ) : (
                                        <span className={styles.optionalBadge}>Conditional</span>
                                      )}
                                    </div>
                                    <span className={styles.questionGuidance}>{q.guidance}</span>
                                  </div>
                                </div>

                                {/* Custom Input Controls based on Question Type */}
                                {q.id === "CR-08" || q.id === "CR-14" ? (
                                  <div className={styles.responseOptions}>
                                    {(q.id === "CR-08" ? ["Yes", "Partial", "No"] : ["No", "Yes", "Unknown"]).map((opt) => {
                                      const isSelected = answer.response === opt;
                                      return (
                                        <button
                                          key={opt}
                                          type="button"
                                          className={`${styles.responseButton} ${isSelected ? styles.responseSelectedYes : ""}`}
                                          onClick={() => handleUpdateAnswer(q.id, "response", opt)}
                                        >
                                          {opt}
                                        </button>
                                      );
                                    })}
                                  </div>
                                ) : q.id === "CR-18" ? (
                                  <div className={styles.declarationBox}>
                                    <label className={styles.declarationLabel}>
                                      <input
                                        type="checkbox"
                                        className={styles.declarationCheckbox}
                                        checked={Boolean(answer.is_limitation_declared || answer.response === "Confirmed")}
                                        onChange={(e) => {
                                          handleUpdateAnswer(q.id, "is_limitation_declared", e.target.checked);
                                          handleUpdateAnswer(q.id, "response", e.target.checked ? "Confirmed" : "Unconfirmed");
                                        }}
                                      />
                                      <span>I confirm that all known limitations, discrepancies, and export constraints have been declared.</span>
                                    </label>
                                    <Input
                                      placeholder="Notes on declared limitations (required if any limitation exists)..."
                                      value={answer.notes || ""}
                                      onChange={(e) => handleUpdateAnswer(q.id, "notes", e.target.value)}
                                    />
                                  </div>
                                ) : (
                                  <Input
                                    placeholder={`Enter response for ${q.id}...`}
                                    value={answer.response || ""}
                                    onChange={(e) => handleUpdateAnswer(q.id, "response", e.target.value)}
                                  />
                                )}

                                {/* Evidence Condition & Reference Inputs (Section 7) */}
                                {q.id !== "CR-18" && (
                                  <div className={styles.questionDetails}>
                                    <select
                                      className={styles.evidenceConditionSelect}
                                      value={answer.evidence_condition || ""}
                                      onChange={(e) =>
                                        handleUpdateAnswer(
                                          q.id,
                                          "evidence_condition",
                                          e.target.value ? (e.target.value as EvidenceCondition) : undefined
                                        )
                                      }
                                    >
                                      <option value="">Select Evidence Condition (Section 7)...</option>
                                      {EVIDENCE_CONDITIONS.map((cond) => (
                                        <option key={cond.code} value={cond.code}>
                                          {cond.label} ({cond.code})
                                        </option>
                                      ))}
                                    </select>
                                    <Input
                                      placeholder="Supporting evidence reference / file name..."
                                      value={answer.evidence_reference || ""}
                                      onChange={(e) => handleUpdateAnswer(q.id, "evidence_reference", e.target.value)}
                                    />
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </>
              )}

              {/* Tab 2: Reviewer Decision Desk (SCR-03 / M4-AC2 / M4-AC3) */}
              {drawerTab === "decision" && (
                <div className={styles.reviewBox}>
                  <div className={styles.reviewBoxHeader}>
                    Reviewer Assessment Decision Desk
                  </div>
                  <p style={{ fontSize: "0.875rem", color: "var(--color-text-muted)", margin: 0 }}>
                    In accordance with InChi Pilot AI Governance, readiness outcomes cannot be assigned automatically. Only an authorized Reviewer can set the outcome or request clarification.
                  </p>

                  {/* Accept assignment action if status is Submitted */}
                  {activeAssessment.status === "Submitted" && (
                    <div style={{ padding: "1rem", backgroundColor: "var(--color-bg-subtle)", borderRadius: "var(--radius-md)", border: "1px solid var(--color-border)" }}>
                      <div style={{ fontWeight: 600, marginBottom: "0.5rem" }}>Assignment Pending:</div>
                      <p style={{ fontSize: "0.8125rem", color: "var(--color-text-muted)", margin: 0, marginBottom: "0.75rem" }}>
                        Accept this assessment assignment to place it Under Review.
                      </p>
                      <Button variant="primary" onClick={handleAcceptAssignment}>
                        Accept Assignment (Move to Under Review)
                      </Button>
                    </div>
                  )}

                  <FormField label="Review Action Type">
                    <Select
                      value={decisionActionType}
                      onChange={(e) => setDecisionActionType(e.target.value as "record_outcome" | "request_info")}
                    >
                      <option value="record_outcome">Record Official Readiness Outcome</option>
                      <option value="request_info">Return for Clarification (Information Required)</option>
                    </Select>
                  </FormField>

                  {decisionActionType === "record_outcome" && (
                    <FormField label="China-Readiness Outcome (Section 1 / Section 5.1)">
                      <Select
                        value={decisionOutcome}
                        onChange={(e) => setDecisionOutcome(e.target.value as AssessmentOutcome)}
                      >
                        <option value="Ready for Matching">Ready for Matching (All mandatory baseline criteria satisfied)</option>
                        <option value="Information Required">Information Required (Unresolved discrepancy or expired evidence)</option>
                        <option value="Not Currently Eligible">Not Currently Eligible (Confirmed baseline failure)</option>
                      </Select>
                    </FormField>
                  )}

                  <FormField
                    label="Decision Rationale / Audit Notes (Mandatory)"
                    required
                    hint="Explain evidence verified, discrepancies, or reasons for return."
                  >
                    <Textarea
                      rows={4}
                      placeholder="e.g. All mandatory baseline criteria verified against registered product. No discrepancies found. Qualified for deterministic matching desk."
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
                  Status: <strong>{activeAssessment.status}</strong>
                </span>
              </div>
              <div style={{ display: "flex", gap: "0.75rem" }}>
                <Button variant="secondary" onClick={() => setActiveAssessmentId(null)}>
                  Close
                </Button>
                {activeAssessment.status !== "Review Complete" && activeAssessment.status !== "Reviewed" && (
                  <Button
                    variant="primary"
                    disabled={!activeSubmissionCheck.canSubmit}
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
          <div className={styles.modalDialog} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "0.5rem", color: "var(--color-text-main)" }}>
              Initiate China-Readiness Assessment
            </h2>
            <p style={{ fontSize: "0.875rem", color: "var(--color-text-muted)", marginBottom: "1.25rem" }}>
              Select a registered Indian supplier to begin evaluation against the approved {QUESTION_SET_VERSION} criteria set.
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

            <FormField label="Product Name / Variant (CR-06)" hint="Must link to at least one product record.">
              <Input
                placeholder="e.g. Stainless steel valve body VB-40"
                value={newProductName}
                onChange={(e) => setNewProductName(e.target.value)}
              />
            </FormField>

            <div style={{ marginTop: "1rem", fontSize: "0.8125rem", color: "var(--color-text-muted)" }}>
              Baseline Specification: <strong>{QUESTION_SET_VERSION}</strong> (18 baseline criteria, categorical evidence conditions).
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
