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
  id: string | number;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export interface CsrfResponse {
  detail?: string;
}
