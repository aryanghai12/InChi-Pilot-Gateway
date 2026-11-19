import {
  ReadinessQuestion,
  AssessmentAnswer,
  CompletenessStatus,
  AssessmentOutcome,
  EvidenceCondition,
} from "@/lib/api/types";

export const QUESTION_SET_VERSION = "Version 2.2";

/**
 * Standard Evidence Conditions per Baseline v2.2 Section 7 (Categorical, non-ordinal)
 */
export const EVIDENCE_CONDITIONS = [
  {
    code: "NOT_PROVIDED" as EvidenceCondition,
    label: "Not Provided",
    description: "No response or evidence was received. Never a pass.",
  },
  {
    code: "SELF_DECLARED" as EvidenceCondition,
    label: "Self-Declared",
    description: "Information entered by supplier or contributor without corroboration.",
  },
  {
    code: "DOCUMENT_RECEIVED_UNVERIFIED" as EvidenceCondition,
    label: "Document Received (Unverified)",
    description: "Document received; authenticity, issuer, or scope not checked. (Default)",
  },
  {
    code: "OFFICIAL_SOURCE_CHECKED" as EvidenceCondition,
    label: "Official Source Checked",
    description: "Authorised analyst checked relevant official source and recorded query/result.",
  },
  {
    code: "THIRD_PARTY_REPORT_RECEIVED_UNVERIFIED" as EvidenceCondition,
    label: "Third-Party Report (Received Unverified)",
    description: "Existing external report was received without independent verification.",
  },
  {
    code: "THIRD_PARTY_REPORT_SOURCE_CHECKED" as EvidenceCondition,
    label: "Third-Party Report (Source Checked)",
    description: "Report issuer or source checked; findings not independently re-performed.",
  },
  {
    code: "EXPIRED" as EvidenceCondition,
    label: "Expired",
    description: "Evidence passed its applicable expiry date. Cannot satisfy mandatory requirement.",
  },
  {
    code: "DISCREPANCY" as EvidenceCondition,
    label: "Discrepancy",
    description: "Evidence conflicts with another response, document, or source.",
  },
  {
    code: "NOT_APPLICABLE" as EvidenceCondition,
    label: "Not Applicable",
    description: "The criterion does not apply for a recorded reason.",
  },
] as const;

/**
 * 18 Baseline China-Readiness Questions per Section 6 of Baseline v2.2
 */
export const READINESS_QUESTIONS: ReadinessQuestion[] = [
  // 1. Legal & Business Identity
  {
    id: "CR-01",
    category: "Legal & Business Identity",
    question_text: "What is the supplier legal name and registered Indian address?",
    guidance: "Registered business name, registered office address in India, and state.",
    is_mandatory: true,
    response_type: "text",
    evidence_rule: "No evidence required at draft; identity document may be referenced.",
  },
  {
    id: "CR-02",
    category: "Legal & Business Identity",
    question_text: "What is the supplier type and its relationship to the product?",
    guidance: "Specify whether Manufacturer, Trader, Distributor, Agent, or Hybrid, and relationship to the product.",
    is_mandatory: true,
    response_type: "enum_text",
    options: ["MANUFACTURER", "TRADER", "DISTRIBUTOR", "AGENT", "HYBRID"],
    evidence_rule: "If not manufacturer, record authorisation or supply relationship as self-declared or document received.",
  },
  {
    id: "CR-03",
    category: "Legal & Business Identity",
    question_text: "What GSTIN applies?",
    guidance: "Required when legally applicable. Format check only (e.g. 22AAAAA0000A1Z5) or N/A.",
    is_mandatory: false,
    response_type: "text_or_na",
    evidence_rule: "Required when legally applicable. Syntax check only; no legal conclusion.",
  },

  // 2. Export Authorization
  {
    id: "CR-04",
    category: "Export Authorization",
    question_text: "What IEC applies to the proposed export?",
    guidance: "10-digit Importer Exporter Code issued by DGFT. Unknown is permitted in draft, but blocks Ready for Matching.",
    is_mandatory: true,
    response_type: "text_or_unknown",
    evidence_rule: "Unknown permitted in draft; blocks Ready for Matching when export is proposed.",
  },
  {
    id: "CR-05",
    category: "Export Authorization",
    question_text: "Which countries or regions has the supplier exported to in the last three years?",
    guidance: "List of countries or regions, or 'None' if first-time exporter.",
    is_mandatory: true,
    response_type: "text",
    evidence_rule: "Self-declaration is sufficient for MVP; optional document reference.",
  },

  // 3. Product & Specification
  {
    id: "CR-06",
    category: "Product & Specification",
    question_text: "What specific product, model, grade or variant is being assessed?",
    guidance: "Must link to at least one specific product record in the catalogue (e.g. PRD-001).",
    is_mandatory: true,
    response_type: "linked_product",
    evidence_rule: "Must link at least one Product record.",
  },
  {
    id: "CR-07",
    category: "Product & Specification",
    question_text: "What product category and declared HS code apply?",
    guidance: "One of the 3 MVP categories (ENG_COMPONENT, INDUSTRIAL_INPUT, SHELF_STABLE_FOOD) and declared 6/8-digit HS code.",
    is_mandatory: true,
    response_type: "enum_text",
    options: ["ENG_COMPONENT", "INDUSTRIAL_INPUT", "SHELF_STABLE_FOOD"],
    evidence_rule: "Category required. HS code may be Unknown and is never treated as customs confirmation.",
  },
  {
    id: "CR-08",
    category: "Product & Specification",
    question_text: "Are the technical specifications complete enough for buyer comparison?",
    guidance: "Verify if technical attributes (composition, dimensions, tolerances, grade) are documented. No or Partial produces Information Required.",
    is_mandatory: true,
    response_type: "choice",
    options: ["Yes", "Partial", "No"],
    evidence_rule: "No or Partial produces Information Required.",
  },

  // 4. Production & Commercial Terms
  {
    id: "CR-09",
    category: "Production & Commercial Terms",
    question_text: "What available capacity can be supplied and over what period?",
    guidance: "Specify quantity value (> 0), unit of measure (PIECE, KILOGRAM, METRIC_TONNE, LITRE, CARTON), and period (MONTH, YEAR, QUARTER).",
    is_mandatory: true,
    response_type: "number_unit_period",
    evidence_rule: "All three values required; value must be greater than zero.",
  },
  {
    id: "CR-10",
    category: "Production & Commercial Terms",
    question_text: "What are the MOQ and declared lead time?",
    guidance: "Minimum Order Quantity in product units and production/dispatch lead time in calendar days.",
    is_mandatory: true,
    response_type: "number_unit_days",
    evidence_rule: "MOQ and lead time must be positive and use approved units.",
  },
  {
    id: "CR-11",
    category: "Production & Commercial Terms",
    question_text: "What indicative price, currency and price basis apply?",
    guidance: "Indicative supplier pricing (e.g. 50 USD/kg FOB Nhava Sheva). Conditional: required only when buyer requirement makes price mandatory.",
    is_mandatory: false,
    response_type: "amount_text_unknown",
    evidence_rule: "Required only when the buyer requirement includes price as mandatory.",
  },

  // 5. Packaging & Logistics
  {
    id: "CR-12",
    category: "Packaging & Logistics",
    question_text: "What packaging and shipping configuration is offered?",
    guidance: "Pack size, outer carton material, palletization standard, container load type (FCL/LCL).",
    is_mandatory: true,
    response_type: "text",
    evidence_rule: "Must state pack size and shipping unit.",
  },

  // 6. Quality & Regulatory Evidence
  {
    id: "CR-13",
    category: "Quality & Regulatory Evidence",
    question_text: "Which quality certificates, test reports or product documents are available?",
    guidance: "List available certificates (ISO, test reports, mill test certificate, COA, Phytosanitary, GACC). 'None' is allowed but must be explicit.",
    is_mandatory: true,
    response_type: "multi_select",
    evidence_rule: "None is allowed but must be explicit; each referenced item receives an evidence condition.",
  },
  {
    id: "CR-14",
    category: "Quality & Regulatory Evidence",
    question_text: "Are any required documents expired, inconsistent or limited in scope?",
    guidance: "Check document validity dates and consistency with declared product specs. Yes produces Expired or Discrepancy condition.",
    is_mandatory: true,
    response_type: "choice",
    options: ["No", "Yes", "Unknown"],
    evidence_rule: "Yes requires a note and condition Expired or Discrepancy.",
  },

  // 7. China Market Preparedness
  {
    id: "CR-15",
    category: "China Market Preparedness",
    question_text: "What is known about China-specific product or market requirements?",
    guidance: "Declared knowledge of China GB standards, customs inspection rules, or target buyer specs. Self-declaration only.",
    is_mandatory: true,
    response_type: "text_or_unknown",
    evidence_rule: "A declaration only; no automatic regulatory or customs conclusion.",
  },
  {
    id: "CR-16",
    category: "China Market Preparedness",
    question_text: "Are English product information and Mandarin-ready fields available?",
    guidance: "English product spec availability and Mandarin status: Not Available, Draft, or Human Reviewed.",
    is_mandatory: true,
    response_type: "status_pair",
    evidence_rule: "Mandarin may be Not Available, Draft or Human Reviewed. Machine output alone is Draft.",
  },
  {
    id: "CR-17",
    category: "Packaging & Logistics",
    question_text: "What logistics route, dispatch point and proposed Incoterm are available?",
    guidance: "Dispatch port (e.g. Mundra, Nhava Sheva, Chennai), transit route, and proposed Incoterm (FOB, CIF, CFR).",
    is_mandatory: true,
    response_type: "text_or_unknown",
    evidence_rule: "Unknown is allowed but may block a requirement with mandatory delivery terms.",
  },

  // 8. Contributor Declaration
  {
    id: "CR-18",
    category: "Contributor Declaration",
    question_text: "Has the contributor declared all known limitations and discrepancies?",
    guidance: "Mandatory confirmation before submission. Contributor certifies that all known limitations or discrepancies have been noted.",
    is_mandatory: true,
    response_type: "declaration_checkbox",
    evidence_rule: "Submission blocked until checked. Notes required when any limitation exists.",
  },
];

export interface CompletenessResult {
  completeness: CompletenessStatus;
  missingItems: string[];
}

/**
 * Section 6.1: Evaluates completeness of assessment answers against mandatory questions.
 * Mandatory questions that MUST have responses: CR-01, CR-02, CR-04, and CR-06 through CR-18.
 * CR-03 and CR-11 are conditional.
 */
export function calculateReadinessCompleteness(
  answers: AssessmentAnswer[],
  questions: ReadinessQuestion[] = READINESS_QUESTIONS
): CompletenessResult {
  const missing: string[] = [];

  questions.forEach((q) => {
    // Only mandatory questions block completeness
    if (!q.is_mandatory) return;

    const ans = answers.find((a) => a.question_id === q.id);
    if (!ans || !ans.response || ans.response.trim() === "") {
      missing.push(`${q.id} (${q.category}): "${q.question_text}" is unanswered.`);
      return;
    }

    // Special validation for CR-06 (linked product)
    if (q.id === "CR-06" && (!ans.response || ans.response.trim() === "" || ans.response === "None")) {
      missing.push("CR-06: At least one Product record must be linked.");
    }

    // Special validation for CR-18 (contributor declaration)
    if (q.id === "CR-18") {
      const isConfirmed =
        ans.is_limitation_declared === true ||
        (ans.is_limitation_declared !== false && (
          ans.response.toLowerCase().includes("confirmed") ||
          ans.response.toLowerCase() === "true"
        ));
      if (!isConfirmed) {
        missing.push("CR-18: Contributor declaration must be confirmed before submission.");
      }
    }
  });

  return {
    completeness: missing.length === 0 ? "Complete" : "Incomplete",
    missingItems: missing,
  };
}

/**
 * Section 6.1 Submission Gate:
 * Enforces all submission criteria before an assessment can transition from Draft to Submitted.
 */
export function canSubmitAssessment(
  answers: AssessmentAnswer[],
  questions: ReadinessQuestion[] = READINESS_QUESTIONS
): { canSubmit: boolean; missingCount: number; blockingItems: string[]; message?: string } {
  const { missingItems } = calculateReadinessCompleteness(answers, questions);

  // Check that every referenced document has an evidence condition
  const evidenceBlockers: string[] = [];
  answers.forEach((ans) => {
    if (ans.evidence_reference && ans.evidence_reference.trim() !== "") {
      if (!ans.evidence_condition) {
        evidenceBlockers.push(
          `Document "${ans.evidence_reference}" referenced in ${ans.question_id} must have an evidence condition.`
        );
      }
    }
  });

  const allBlocking = [...missingItems, ...evidenceBlockers];

  if (allBlocking.length > 0) {
    return {
      canSubmit: false,
      missingCount: allBlocking.length,
      blockingItems: allBlocking,
      message: `Assessment submission blocked: ${allBlocking.length} required items or conditions remain unresolved.`,
    };
  }

  return {
    canSubmit: true,
    missingCount: 0,
    blockingItems: [],
  };
}

/**
 * Section 6.2 Readiness Outcome Rule (Rule-based evaluation):
 * - Ready for Matching: All mandatory baseline questions complete; IEC present; technical specs usable;
 *                       capacity, MOQ, lead time, packaging usable; no unresolved mandatory discrepancy.
 * - Information Required: Required comparison value is Unknown, Partial, expired, unverified where source checking
 *                         is mandatory, or affected by an unresolved discrepancy.
 * - Not Currently Eligible: Confirmed mandatory baseline failure (e.g. no legal identity, confirmed inability).
 *
 * NOTE: Strictly NO numeric readiness score.
 */
export function evaluateReadinessOutcome(
  answers: AssessmentAnswer[]
): {
  outcome: AssessmentOutcome;
  reasons: string[];
} {
  const reasons: string[] = [];

  // Check IEC (CR-04)
  const iecAns = answers.find((a) => a.question_id === "CR-04")?.response?.trim();
  if (!iecAns || iecAns.toLowerCase() === "unknown") {
    reasons.push("CR-04: Export proposed but IEC is Unknown or not provided.");
  }

  // Check Technical Specifications (CR-08)
  const specAns = answers.find((a) => a.question_id === "CR-08")?.response?.trim();
  if (specAns === "Partial" || specAns === "No") {
    reasons.push(`CR-08: Technical specifications are marked as "${specAns}".`);
  }

  // Check Documents & Discrepancies (CR-14)
  const docCheckAns = answers.find((a) => a.question_id === "CR-14");
  if (docCheckAns?.response === "Yes") {
    reasons.push("CR-14: One or more documents are expired, inconsistent, or limited in scope.");
  }

  // Check for expired or discrepant evidence conditions
  const expiredDocs = answers.filter((a) => a.evidence_condition === "EXPIRED");
  if (expiredDocs.length > 0) {
    reasons.push(`${expiredDocs.length} evidence item(s) have condition EXPIRED.`);
  }

  const discrepancyDocs = answers.filter((a) => a.evidence_condition === "DISCREPANCY");
  if (discrepancyDocs.length > 0) {
    reasons.push(`${discrepancyDocs.length} evidence item(s) have condition DISCREPANCY.`);
  }

  if (reasons.length > 0) {
    return {
      outcome: "Information Required",
      reasons,
    };
  }

  return {
    outcome: "Ready for Matching",
    reasons: ["All mandatory baseline criteria satisfied; no unresolved discrepancies or expired items."],
  };
}

/**
 * Section 4 & Section 8.1 / M4-AC3:
 * Reviewer decision audit validation. Requires an explicit reason for any outcome or clarification request.
 */
export function validateReviewDecision(
  actionType: "record_outcome" | "request_info",
  reason: string,
  outcome?: AssessmentOutcome
): { isValid: boolean; error?: string } {
  if (!reason || !reason.trim()) {
    return {
      isValid: false,
      error: "You must record an explicit reason or audit note when setting an outcome or requesting clarification (M4-AC3).",
    };
  }

  if (actionType === "record_outcome") {
    if (!outcome) {
      return {
        isValid: false,
        error: "A valid readiness outcome must be selected when recording a review decision.",
      };
    }
  }

  return { isValid: true };
}
