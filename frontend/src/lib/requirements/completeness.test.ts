import { describe, it, expect } from "vitest";
import {
  evaluateRequirementCompleteness,
  validatePriceBounds,
  RequirementFormData,
} from "./completeness";

describe("M5 Buyer Requirement Completeness Gate (BUY-032 / M5-AC2)", () => {
  const validData: RequirementFormData = {
    buyer_organisation_name: "Shanghai Food Trading Co.",
    requirement_title: "Organic Turmeric Powder (200 MT)",
    product_category_id: "Agriculture and Food",
    quantity_value: 200,
    quantity_unit: "tonnes",
    delivery_location: "Shanghai Port, China",
    target_price_min: 1500,
    target_price_max: 1800,
  };

  it("marks requirement as Matching Ready and Complete when all mandatory gates are met", () => {
    const result = evaluateRequirementCompleteness(validData, 1);
    expect(result.isReady).toBe(true);
    expect(result.completenessStatus).toBe("Complete");
    expect(result.blockingReasons).toHaveLength(0);
    expect(result.completionScore).toBe(100);
    expect(result.passedChecksCount).toBe(6);
  });

  it("blocks matching readiness if buyer organisation name is missing", () => {
    const incompleteData = { ...validData, buyer_organisation_name: "" };
    const result = evaluateRequirementCompleteness(incompleteData, 1);
    expect(result.isReady).toBe(false);
    expect(result.completenessStatus).toBe("Incomplete");
    expect(result.blockingReasons).toContain("Buyer organisation name is required (BUY-002).");
  });

  it("blocks matching readiness if quantity is 0 or negative", () => {
    const invalidQty = { ...validData, quantity_value: 0 };
    const result = evaluateRequirementCompleteness(invalidQty, 1);
    expect(result.isReady).toBe(false);
    expect(result.blockingReasons.some((r) => r.includes("quantity value greater than 0"))).toBe(true);
  });

  it("blocks matching readiness if delivery destination is missing", () => {
    const missingDelivery = { ...validData, delivery_location: "" };
    const result = evaluateRequirementCompleteness(missingDelivery, 1);
    expect(result.isReady).toBe(false);
    expect(result.blockingReasons).toContain("Delivery destination / discharge port must be specified (BUY-017).");
  });

  it("enforces M5-AC1/BUY-022: blocks matching readiness if zero mandatory eligibility rules exist", () => {
    const result = evaluateRequirementCompleteness(validData, 0); // 0 mandatory rules
    expect(result.isReady).toBe(false);
    expect(result.blockingReasons.some((r) => r.includes("mandatory eligibility condition is required"))).toBe(true);
  });

  describe("validatePriceBounds", () => {
    it("validates when min price is less than max price", () => {
      const check = validatePriceBounds(100, 200);
      expect(check.isValid).toBe(true);
    });

    it("validates when min price equals max price", () => {
      const check = validatePriceBounds(150, 150);
      expect(check.isValid).toBe(true);
    });

    it("fails when min price exceeds max price", () => {
      const check = validatePriceBounds(300, 200);
      expect(check.isValid).toBe(false);
      expect(check.errorMessage).toContain("Maximum price must be greater than or equal to minimum price");
    });

    it("passes when either bound is omitted", () => {
      expect(validatePriceBounds(100, "").isValid).toBe(true);
      expect(validatePriceBounds("", 200).isValid).toBe(true);
      expect(validatePriceBounds(undefined, undefined).isValid).toBe(true);
    });
  });
});
