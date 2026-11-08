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
