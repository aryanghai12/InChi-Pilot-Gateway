import { describe, it, expect } from "vitest";
import {
  calculateReadinessCompleteness,
  canSubmitAssessment,
  validateReviewDecision,
  READINESS_QUESTIONS,
} from "./evaluation";
import { AssessmentAnswer } from "@/lib/api/types";

describe("M4 China-Readiness Evaluation & Reviewer Decision Engine", () => {
  const mandatoryQuestionIds = READINESS_QUESTIONS.filter((q) => q.is_mandatory).map((q) => q.id);

  it("identifies all unanswered mandatory questions when answers are empty", () => {
    const result = calculateReadinessCompleteness([]);
    expect(result.completeness).toBe("Incomplete");
    expect(result.missingItems.length).toBe(mandatoryQuestionIds.length);
  });

  it("marks assessment as Complete when all mandatory questions are answered", () => {
    const completeAnswers: AssessmentAnswer[] = mandatoryQuestionIds.map((qid) => ({
      question_id: qid,
      response: "Yes",
      evidence_reference: "EVD-2026-001",
    }));

    const result = calculateReadinessCompleteness(completeAnswers);
    expect(result.completeness).toBe("Complete");
    expect(result.missingItems).toHaveLength(0);
  });

  it("enforces M4-AC1 guardrail: blocks reviewer submission if mandatory questions are incomplete", () => {
    // Only answer 1 mandatory question
    const partialAnswers: AssessmentAnswer[] = [
      {
        question_id: mandatoryQuestionIds[0],
        response: "Yes",
      },
    ];

    const submissionCheck = canSubmitAssessment(partialAnswers);
    expect(submissionCheck.canSubmit).toBe(false);
    expect(submissionCheck.missingCount).toBeGreaterThan(0);
    expect(submissionCheck.message).toContain("mandatory questions remain unanswered");
  });

  it("allows reviewer submission when all mandatory questions are answered", () => {
    const completeAnswers: AssessmentAnswer[] = mandatoryQuestionIds.map((qid) => ({
      question_id: qid,
      response: "Yes",
    }));

    const submissionCheck = canSubmitAssessment(completeAnswers);
    expect(submissionCheck.canSubmit).toBe(true);
    expect(submissionCheck.missingCount).toBe(0);
  });

  describe("M4-AC3 Reviewer Decision Audit Validation", () => {
    it("fails validation if decision reason is empty when recording outcome", () => {
      const result = validateReviewDecision("record_outcome", "", "China-ready");
      expect(result.isValid).toBe(false);
      expect(result.error).toContain("must record an explicit reason or audit note");
    });

    it("fails validation if decision reason is only whitespace", () => {
      const result = validateReviewDecision("record_outcome", "   \t\n  ", "China-ready");
      expect(result.isValid).toBe(false);
    });

    it("passes validation when a valid reason and outcome are provided", () => {
      const result = validateReviewDecision(
        "record_outcome",
        "Enterprise holds active GACC registration and verified ISO 22000 certificate.",
        "China-ready"
      );
      expect(result.isValid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it("requires reason when requesting clarification / more info", () => {
      const emptyCheck = validateReviewDecision("request_info", "");
      expect(emptyCheck.isValid).toBe(false);

      const validCheck = validateReviewDecision(
        "request_info",
        "Mandarin commercial catalog missing required nutrition facts panel."
      );
      expect(validCheck.isValid).toBe(true);
    });
  });
});
