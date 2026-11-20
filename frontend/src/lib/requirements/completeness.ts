import { ProductCategory, CompletenessStatus } from "@/lib/api/types";

// 7 Top-Level Working Categories defined in Buyer Requirement Field Dictionary v1.2
export const PRODUCT_CATEGORIES: ProductCategory[] = [
  "Agriculture and Food",
  "Textiles",
  "Engineering Goods",
  "Electronic Goods",
  "Chemicals",
  "Minerals & Metals",
  "Marine Products",
];

export interface RequirementFormData {
  buyer_organisation_name: string;
  requirement_title: string;
  product_category_id: ProductCategory | string;
  quantity_value?: number | string;
  quantity_unit?: string;
  delivery_location?: string;
  target_price_min?: number | string;
  target_price_max?: number | string;
}

export interface CompletenessEvaluation {
  isReady: boolean;
  completenessStatus: CompletenessStatus;
  blockingReasons: string[];
  passedChecksCount: number;
  totalChecksCount: number;
  completionScore: number;
}

/**
 * M5-AC2 / BUY-032: Evaluates the completeness gate and matching readiness
 * of a procurement requirement.
 */
export function evaluateRequirementCompleteness(
  data: RequirementFormData,
  mandatoryCriteriaCount: number = 0
): CompletenessEvaluation {
  const blockingReasons: string[] = [];
  let passed = 0;
  const total = 6;

  // 1. Buyer Organisation Identity (BUY-002)
  if (data.buyer_organisation_name && data.buyer_organisation_name.trim()) {
    passed++;
  } else {
    blockingReasons.push("Buyer organisation name is required (BUY-002).");
  }

  // 2. Requirement Title (BUY-004)
  if (data.requirement_title && data.requirement_title.trim()) {
    passed++;
  } else {
    blockingReasons.push("Requirement title is required for commercial identification (BUY-004).");
  }

  // 3. Category (BUY-006)
  if (data.product_category_id && data.product_category_id.trim()) {
    passed++;
  } else {
    blockingReasons.push("A valid product category must be selected (BUY-006).");
  }

  // 4. Quantity & Unit (BUY-009, BUY-010)
  const qty = Number(data.quantity_value);
  if (qty > 0 && data.quantity_unit && data.quantity_unit.trim()) {
    passed++;
  } else {
    blockingReasons.push("Valid quantity value greater than 0 and commercial unit are required (BUY-009/010).");
  }

  // 5. Delivery Location (BUY-017)
  if (data.delivery_location && data.delivery_location.trim()) {
    passed++;
  } else {
    blockingReasons.push("Delivery destination / discharge port must be specified (BUY-017).");
  }

  // 6. Mandatory Eligibility Rule (BUY-022)
  if (mandatoryCriteriaCount > 0) {
    passed++;
  } else {
    blockingReasons.push("At least one mandatory eligibility condition is required for automated candidate filtering (BUY-022).");
  }

  const isReady = blockingReasons.length === 0;
  const completenessStatus: CompletenessStatus = isReady ? "Complete" : "Incomplete";
  const completionScore = Math.round((passed / total) * 100);

  return {
    isReady,
    completenessStatus,
    blockingReasons,
    passedChecksCount: passed,
    totalChecksCount: total,
    completionScore,
  };
}

/**
 * Validates budget pricing bounds (min <= max).
 */
export function validatePriceBounds(minPrice?: number | string, maxPrice?: number | string): {
  isValid: boolean;
  errorMessage?: string;
} {
  if (minPrice != null && minPrice !== "" && maxPrice != null && maxPrice !== "") {
    const min = Number(minPrice);
    const max = Number(maxPrice);
    if (!isNaN(min) && !isNaN(max) && min > max) {
      return {
        isValid: false,
        errorMessage: "Maximum price must be greater than or equal to minimum price.",
      };
    }
  }
  return { isValid: true };
}
