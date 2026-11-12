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
 * Generic DRF Paginated Response structure returned by PageNumberPagination
 * ============================================================================
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Safely unwraps paginated DRF results or returns a raw array.
 */
export function unwrapPaginated<T>(data: T[] | PaginatedResponse<T> | null | undefined): T[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object" && "results" in data && Array.isArray((data as PaginatedResponse<T>).results)) {
    return (data as PaginatedResponse<T>).results;
  }
  return [];
}

/**
 * ============================================================================
 * M2: Supplier Registry Types (OpenAPI 3.0.3 Compatible)
 * Lifecycle: draft / complete / archived
 * ============================================================================
 */
export type SupplierStatus =
  | "draft"
  | "complete"
  | "archived"
  | "Draft"
  | "Complete"
  | "Archived";

export type SupplierType =
  | "manufacturer"
  | "merchant_exporter"
  | "trader"
  | "Manufacturer"
  | "Merchant Exporter"
  | "Trader"
  | "Distributor"
  | "Service Provider"
  | "Other";

export interface SupplierContactDetails {
  contact_name?: string;
  email?: string;
  phone?: string;
}

export interface Supplier {
  id: string;
  supplier_id: string; // Backwards compatibility alias for id
  legal_name: string;
  trade_name?: string;
  country_of_registration: string;
  supplier_type: SupplierType;
  address?: string;
  address_registration_reference?: string; // Backwards compatibility alias for address
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  contact_details?: SupplierContactDetails; // Backwards compatibility alias
  industry_description?: string;
  capability_attributes?: string;
  record_status: SupplierStatus;
  evidence_refs?: string[];
  version: number;
  created_by?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface SupplierRequest {
  legal_name: string;
  trade_name?: string;
  country_of_registration: string;
  supplier_type?: SupplierType | "";
  address?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  industry_description?: string;
  record_status?: SupplierStatus;
  version?: number;
}

export type PaginatedSupplierList = PaginatedResponse<Supplier>;

/**
 * ============================================================================
 * M3: Product Catalogue Types (OpenAPI 3.0.3 Compatible)
 * ============================================================================
 */
export type TranslationStatus =
  | "not_provided"
  | "provided_unreviewed"
  | "reviewed"
  | "Not provided"
  | "Provided – unreviewed"
  | "Reviewed";

export type MoqUnit = "MT" | "KG" | "PIECES" | "BOXES" | "CONTAINERS" | string;
export type CurrencyCode = "USD" | "INR" | "CNY" | "EUR" | string;
export type CapacityUnit = "MT" | "KG" | "PIECES" | "BOXES" | "CONTAINERS" | string;
export type CapacityPeriod = "MONTH" | "YEAR" | "QUARTER" | string;
export type LeadTimeUnit = "DAYS" | "WEEKS" | "MONTHS" | string;

export interface Product {
  id: string;
  product_id: string; // Backwards compatibility alias for id
  supplier: string; // Supplier UUID foreign key
  supplier_id: string; // Backwards compatibility alias for supplier
  supplier_name?: string;
  product_name: string;
  product_category: string;
  description?: string;
  product_name_zh?: string;
  short_description_zh?: string;
  translation_status: TranslationStatus;
  origin?: string;
  specifications?: string;
  moq_value?: string | number | null;
  moq_unit?: MoqUnit;
  minimum_order_quantity?: number; // Backwards compatibility alias for moq_value
  minimum_order_unit?: string; // Backwards compatibility alias for moq_unit
  price_min?: string | number | null;
  price_max?: string | number | null;
  indicative_price_min?: number; // Backwards compatibility alias for price_min
  indicative_price_max?: number; // Backwards compatibility alias for price_max
  currency?: CurrencyCode;
  price_basis?: string;
  capacity_quantity?: string | number | null;
  capacity_unit?: CapacityUnit;
  capacity_period?: CapacityPeriod;
  lead_time_value?: number | null;
  lead_time_unit?: LeadTimeUnit;
  evidence_refs?: string[];
  version: number;
  created_by?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ProductRequest {
  supplier: string;
  product_name: string;
  product_category: string;
  description?: string;
  product_name_zh?: string;
  short_description_zh?: string;
  translation_status?: TranslationStatus;
  origin?: string;
  specifications?: string;
  moq_value?: string | null;
  moq_unit?: MoqUnit;
  price_min?: string | null;
  price_max?: string | null;
  currency?: CurrencyCode;
  price_basis?: string;
  capacity_quantity?: string | null;
  capacity_unit?: CapacityUnit;
  capacity_period?: CapacityPeriod;
  lead_time_value?: number | null;
  lead_time_unit?: LeadTimeUnit;
  version?: number;
}

export type PaginatedProductList = PaginatedResponse<Product>;

/**
 * ============================================================================
 * Evidence Metadata Types (OpenAPI 3.0.3 Compatible)
 * ============================================================================
 */
export type EvidencePresenceStatus = "Provided" | "Missing" | string;
export type EvidenceReviewStatus = "Pending Review" | "Verified" | "Rejected" | string;

export interface EvidenceItem {
  id: string;
  evidence_id: string; // Backwards compatibility alias for id
  supplier?: string | null;
  product?: string | null;
  entity_type?: "supplier" | "product"; // Backwards compatibility alias
  entity_id?: string; // Backwards compatibility alias
  document_type: string;
  evidence_reference: string;
  document_name?: string;
  issue_date?: string | null;
  expiry_date?: string | null;
  presence_status: EvidencePresenceStatus;
  review_status: EvidenceReviewStatus;
  created_at?: string;
  updated_at?: string;
}

export interface EvidenceItemRequest {
  supplier?: string | null;
  product?: string | null;
  document_type: string;
  evidence_reference: string;
  document_name?: string;
  issue_date?: string | null;
  expiry_date?: string | null;
  presence_status?: string;
  review_status?: string;
}

// Backwards compatibility alias
export type EvidenceMetadata = EvidenceItem;
export type PaginatedEvidenceItemList = PaginatedResponse<EvidenceItem>;

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
