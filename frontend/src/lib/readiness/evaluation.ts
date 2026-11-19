import {
  ReadinessQuestion,
  AssessmentAnswer,
  CompletenessStatus,
  AssessmentOutcome,
} from "@/lib/api/types";

export const QUESTION_SET_VERSION = "v1.0-pilot";

export const READINESS_QUESTIONS: ReadinessQuestion[] = [
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

export interface CompletenessResult {
  completeness: CompletenessStatus;
  missingItems: string[];
}

/**
 * M4-AC1: Evaluates live completeness of assessment responses against the mandatory question set.
 */
export function calculateReadinessCompleteness(
  answers: AssessmentAnswer[],
  questions: ReadinessQuestion[] = READINESS_QUESTIONS
): CompletenessResult {
  const missing: string[] = [];

  questions.forEach((q) => {
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
}

/**
 * M4-AC1 Guardrail: Checks whether an assessment is eligible for formal reviewer submission.
 */
export function canSubmitAssessment(
  answers: AssessmentAnswer[],
  questions: ReadinessQuestion[] = READINESS_QUESTIONS
): { canSubmit: boolean; missingCount: number; message?: string } {
  const { completeness, missingItems } = calculateReadinessCompleteness(answers, questions);
  if (completeness === "Incomplete") {
    return {
      canSubmit: false,
      missingCount: missingItems.length,
      message: `Assessment cannot be submitted while mandatory questions remain unanswered (${missingItems.length} missing).`,
    };
  }
  return {
    canSubmit: true,
    missingCount: 0,
  };
}

/**
 * M4-AC3 Guardrail: Validates reviewer decision inputs, enforcing mandatory reasoning.
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
