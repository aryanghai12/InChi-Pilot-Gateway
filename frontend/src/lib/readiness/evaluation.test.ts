import { describe, it, expect } from "vitest";
import {
  calculateReadinessCompleteness,
  canSubmitAssessment,
  evaluateReadinessOutcome,
  validateReviewDecision,
  READINESS_QUESTIONS,
  QUESTION_SET_VERSION,
} from "./evaluation";
import { AssessmentAnswer } from "@/lib/api/types";

describe("China-Readiness Baseline v2.2 Evaluation & Reviewer Decision Engine", () => {
  const mandatoryQuestions = READINESS_QUESTIONS.filter((q) => q.is_mandatory);
  const mandatoryQuestionIds = mandatoryQuestions.map((q) => q.id);

  it("verifies questionnaire version 2.2 and exactly 18 baseline questions", () => {
    expect(QUESTION_SET_VERSION).toBe("Version 2.2");
    expect(READINESS_QUESTIONS).toHaveLength(18);
    expect(READINESS_QUESTIONS[0].id).toBe("CR-01");
    expect(READINESS_QUESTIONS[17].id).toBe("CR-18");
  });

  it("identifies all unanswered mandatory questions when answers are empty", () => {
    const result = calculateReadinessCompleteness([]);
    expect(result.completeness).toBe("Incomplete");
    expect(result.missingItems.length).toBe(mandatoryQuestionIds.length);
  });

  it("marks assessment as Complete when all mandatory questions are answered including CR-18 confirmation", () => {
    const completeAnswers: AssessmentAnswer[] = mandatoryQuestionIds.map((qid) => ({
      question_id: qid,
      response: qid === "CR-06" ? "PRD-2026-001" : "Verified details",
      is_limitation_declared: qid === "CR-18" ? true : undefined,
    }));

    const result = calculateReadinessCompleteness(completeAnswers);
    expect(result.completeness).toBe("Complete");
    expect(result.missingItems).toHaveLength(0);
  });

  it("enforces Section 6.1 Submission Gate: blocks submission if CR-18 declaration is unconfirmed", () => {
    const answersWithoutCR18: AssessmentAnswer[] = mandatoryQuestionIds.map((qid) => ({
      question_id: qid,
      response: qid === "CR-06" ? "PRD-2026-001" : "Yes",
      is_limitation_declared: false, // Not confirmed
    }));

    const submissionCheck = canSubmitAssessment(answersWithoutCR18);
    expect(submissionCheck.canSubmit).toBe(false);
    expect(submissionCheck.blockingItems.some((item) => item.includes("CR-18"))).toBe(true);
  });

  it("enforces Section 6.1: blocks submission if referenced document has no evidence condition", () => {
    const answersWithUnassignedDoc: AssessmentAnswer[] = mandatoryQuestionIds.map((qid) => ({
      question_id: qid,
      response: qid === "CR-06" ? "PRD-2026-001" : "Yes",
      evidence_reference: qid === "CR-13" ? "ISO-9001-CERT.pdf" : undefined,
      evidence_condition: undefined, // Missing condition
      is_limitation_declared: qid === "CR-18" ? true : undefined,
    }));

    const check = canSubmitAssessment(answersWithUnassignedDoc);
    expect(check.canSubmit).toBe(false);
    expect(check.blockingItems.some((item) => item.includes("ISO-9001-CERT.pdf"))).toBe(true);
  });

  it("allows submission when all mandatory questions, CR-18 declaration, and evidence conditions are valid", () => {
    const validAnswers: AssessmentAnswer[] = mandatoryQuestionIds.map((qid) => ({
      question_id: qid,
      response: qid === "CR-06" ? "PRD-2026-001" : "Valid input",
      evidence_reference: qid === "CR-13" ? "ISO-9001-CERT.pdf" : undefined,
      evidence_condition: qid === "CR-13" ? "DOCUMENT_RECEIVED_UNVERIFIED" : undefined,
      is_limitation_declared: qid === "CR-18" ? true : undefined,
    }));

    const check = canSubmitAssessment(validAnswers);
    expect(check.canSubmit).toBe(true);
    expect(check.blockingItems).toHaveLength(0);
  });

  describe("Section 6.2 Readiness Outcome Rule (Rule-based, No Numeric Score)", () => {
    it("evaluates to 'Ready for Matching' when all criteria pass and no discrepancies exist", () => {
      const answers: AssessmentAnswer[] = [
        { question_id: "CR-04", response: "0123456789" },
        { question_id: "CR-08", response: "Yes" },
        { question_id: "CR-14", response: "No" },
      ];

      const { outcome } = evaluateReadinessOutcome(answers);
      expect(outcome).toBe("Ready for Matching");
    });

    it("evaluates to 'Information Required' when IEC is Unknown", () => {
      const answers: AssessmentAnswer[] = [
        { question_id: "CR-04", response: "Unknown" },
        { question_id: "CR-08", response: "Yes" },
        { question_id: "CR-14", response: "No" },
      ];

      const { outcome, reasons } = evaluateReadinessOutcome(answers);
      expect(outcome).toBe("Information Required");
      expect(reasons.some((r) => r.includes("IEC"))).toBe(true);
    });

    it("evaluates to 'Information Required' when technical specs are Partial", () => {
      const answers: AssessmentAnswer[] = [
        { question_id: "CR-04", response: "0123456789" },
        { question_id: "CR-08", response: "Partial" },
        { question_id: "CR-14", response: "No" },
      ];

      const { outcome, reasons } = evaluateReadinessOutcome(answers);
      expect(outcome).toBe("Information Required");
      expect(reasons.some((r) => r.includes("CR-08"))).toBe(true);
    });

    it("evaluates to 'Information Required' when evidence has condition EXPIRED or DISCREPANCY", () => {
      const answers: AssessmentAnswer[] = [
        { question_id: "CR-04", response: "0123456789" },
        { question_id: "CR-08", response: "Yes" },
        { question_id: "CR-13", response: "Test Report", evidence_condition: "EXPIRED" },
        { question_id: "CR-14", response: "Yes" },
      ];

      const { outcome, reasons } = evaluateReadinessOutcome(answers);
      expect(outcome).toBe("Information Required");
      expect(reasons.some((r) => r.includes("EXPIRED"))).toBe(true);
    });
  });

  describe("Section 4 Reviewer Decision Audit Validation (M4-AC3)", () => {
    it("fails validation if reviewer decision reason is empty", () => {
      const result = validateReviewDecision("record_outcome", "", "Ready for Matching");
      expect(result.isValid).toBe(false);
      expect(result.error).toContain("must record an explicit reason or audit note");
    });

    it("fails validation if decision reason is whitespace", () => {
      const result = validateReviewDecision("record_outcome", "   \t\n  ", "Ready for Matching");
      expect(result.isValid).toBe(false);
    });

    it("passes validation when a valid reason and outcome are provided", () => {
      const result = validateReviewDecision(
        "record_outcome",
        "Mandatory baseline questions verified and IEC active; ready for matching run.",
        "Ready for Matching"
      );
      expect(result.isValid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it("requires reason when requesting clarification / more info", () => {
      const emptyCheck = validateReviewDecision("request_info", "");
      expect(emptyCheck.isValid).toBe(false);

      const validCheck = validateReviewDecision(
        "request_info",
        "Test report is expired; please provide current laboratory certificate."
      );
      expect(validCheck.isValid).toBe(true);
    });
  });
});
