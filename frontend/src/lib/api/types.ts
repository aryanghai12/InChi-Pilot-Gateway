/**
 * Standard API error structure returned by Django backend custom exception handler.
 * ARCHITECTURE.md §5: {"code", "message", "field_errors": {field: [msg]}, "correlation_id"}
 */
export interface ApiErrorPayload {
  code: string;
  message: string;
  field_errors?: Record<string, string[]>;
  correlation_id?: string;
}

export class ApiError extends Error {
  status: number;
  code: string;
  fieldErrors?: Record<string, string[]>;
  correlationId?: string;

  constructor(status: number, payload: Partial<ApiErrorPayload>) {
    super(payload.message || `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.code = payload.code || "unknown_error";
    this.fieldErrors = payload.field_errors;
    this.correlationId = payload.correlation_id;
  }
}

/**
 * User roles as defined in MVP_FEATURES §5 and ARCHITECTURE.md §5
 */
export type UserRole = "platform_admin" | "commercial_analyst" | "reviewer";

export interface CurrentUser {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  role_display?: string;
  is_active: boolean;
  is_verified?: boolean;
  is_staff?: boolean;
  date_joined?: string;
  last_login?: string;
  version?: number;
}

export interface CsrfResponse {
  detail?: string;
}

/**
 * ============================================================================
 * M2: Supplier Registry Types (from Lean Field Dictionary)
 * Lifecycle: Draft / Complete / Archived only
 * ============================================================================
 */
export type SupplierStatus = "Draft" | "Complete" | "Archived";
export type SupplierType = "Manufacturer" | "Trader" | "Distributor" | "Service Provider" | "Other";

export interface SupplierContactDetails {
  contact_name?: string;
  email?: string;
  phone?: string;
}

export interface Supplier {
  supplier_id: string;
  legal_name: string;
  country_of_registration: string;
  supplier_type: SupplierType;
  address_registration_reference?: string;
  contact_details?: SupplierContactDetails;
  industry_description?: string;
  capability_attributes?: string;
  record_status: SupplierStatus;
  evidence_refs?: string[];
  version: number;
  created_at?: string;
  updated_at?: string;
}

/**
 * ============================================================================
 * M3: Product Catalogue Types (from Lean Field Dictionary)
 * ============================================================================
 */
export type TranslationStatus = "Not provided" | "Provided – unreviewed" | "Reviewed";

export interface Product {
  product_id: string;
  supplier_id: string;
  product_name: string;
  product_category: string;
  description?: string;
  specifications?: string;
  origin?: string;
  minimum_order_quantity?: number;
  minimum_order_unit?: string;
  indicative_price_min?: number;
  indicative_price_max?: number;
  currency?: string;
  price_basis?: string;
  capacity_quantity?: number;
  capacity_unit?: string;
  capacity_period?: string;
  lead_time_value?: number;
  lead_time_unit?: string;
  evidence_refs?: string[];
  product_name_zh?: string;
  short_description_zh?: string;
  translation_status: TranslationStatus;
  version: number;
  created_at?: string;
  updated_at?: string;
}

/**
 * ============================================================================
 * Evidence Metadata Types (from Lean Field Dictionary)
 * ============================================================================
 */
export type EvidencePresenceStatus = "Provided" | "Missing";
export type EvidenceReviewStatus = "Pending Review" | "Verified" | "Rejected";

export interface EvidenceMetadata {
  evidence_id: string;
  entity_type: "supplier" | "product";
  entity_id: string;
  document_type: string;
  evidence_reference: string;
  document_name?: string;
  issue_date?: string;
  expiry_date?: string | null;
  presence_status: EvidencePresenceStatus;
  review_status: EvidenceReviewStatus;
  created_at?: string;
}

/**
 * ============================================================================
 * M4: China-Readiness Assessment Types (Stage 3 & Component 1)
 * Workflow States: Draft | Submitted | More information required | Reviewed
 * Outcomes: Pending review | China-ready | Conditionally ready | Not ready
 * ============================================================================
 */
export type AssessmentStatus =
  | "Draft"
  | "Submitted"
  | "More information required"
  | "Reviewed";

export type AssessmentOutcome =
  | "Pending review"
  | "China-ready"
  | "Conditionally ready"
  | "Not ready";

export interface ReadinessQuestion {
  id: string;
  category: string;
  question_text: string;
  guidance: string;
  is_mandatory: boolean;
  required_evidence_type?: string;
}

export interface AssessmentAnswer {
  question_id: string;
  response: "Yes" | "No" | "In Progress" | "N/A" | "";
  notes?: string;
  evidence_reference?: string;
}

export interface AssessmentHistoryEntry {
  id: string;
  action: "Created" | "Submitted" | "Returned for info" | "Outcome recorded" | "Resubmitted";
  actor: string;
  timestamp: string;
  notes?: string;
  outcome?: AssessmentOutcome;
}

export interface SupplierAssessment {
  assessment_id: string;
  supplier_id: string;
  supplier_name: string;
  question_set_version: string;
  status: AssessmentStatus;
  completeness: CompletenessStatus;
  outcome: AssessmentOutcome;
  outcome_reason?: string;
  missing_items?: string[];
  submitted_by?: string;
  submitted_at?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  answers: AssessmentAnswer[];
  history?: AssessmentHistoryEntry[];
  created_at: string;
  updated_at: string;
}

/**
 * ============================================================================
 * M5: Buyer Requirement Types (from Buyer Requirement Field Dictionary v1.2)
 * ============================================================================
 */
export type RequirementStatus = "Draft" | "In Review" | "Ready for Matching" | "Closed" | "Archived";
export type CompletenessStatus = "Complete" | "Incomplete";
export type OrderFrequency = "One-off" | "Monthly" | "Quarterly" | "Annual";

export type ProductCategory =
  | "Agriculture and Food"
  | "Textiles"
  | "Engineering Goods"
  | "Electronic Goods"
  | "Chemicals"
  | "Minerals & Metals"
  | "Marine Products";

export interface RequirementCriterion {
  id: string;
  name: string;
  type: "mandatory" | "preferred";
  notes?: string;
}

export interface RequiredEvidenceItem {
  id: string;
  document_name: string;
  is_mandatory: boolean; // Mandatory eligibility vs Preference
}

export interface BuyerRequirement {
  requirement_id: string; // BUY-001
  buyer_organisation_name: string; // BUY-002
  buyer_reference?: string; // BUY-003
  owner_user_id: string; // BUY-004
  target_market: string; // BUY-005 (Target market != delivery destination)
  product_category_id: ProductCategory; // BUY-006 (One of the 7 working categories)
  requirement_title: string; // BUY-007
  product_specifications?: string; // BUY-008
  quantity_value?: number; // BUY-009
  quantity_unit?: string; // BUY-010
  order_frequency?: OrderFrequency; // BUY-011
  target_price_min?: number; // BUY-012
  target_price_max?: number; // BUY-013
  currency_code?: string; // BUY-014
  price_basis?: string; // BUY-015
  required_evidence?: RequiredEvidenceItem[]; // BUY-016
  delivery_location?: string; // BUY-017
  delivery_window_start?: string; // BUY-018
  delivery_window_end?: string; // BUY-019
  required_lead_time_value?: number; // BUY-020
  required_lead_time_unit?: string; // BUY-021
  mandatory_criteria?: RequirementCriterion[]; // BUY-022
  preferred_criteria?: RequirementCriterion[]; // BUY-023
  buyer_preferences?: string; // BUY-025
  requirement_notes?: string; // BUY-026
  buyer_verification_status?: string; // BUY-027
  requirement_status: RequirementStatus; // BUY-028
  completeness_status: CompletenessStatus; // BUY-029
  version: number; // BUY-030
  matching_ready: boolean; // BUY-032
  blocking_reasons?: string[]; // BUY-032
  created_at?: string; // BUY-031
  updated_at?: string; // BUY-031
  created_by?: string; // BUY-031
  updated_by?: string; // BUY-031
}
