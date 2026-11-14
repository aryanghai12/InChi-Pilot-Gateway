/**
 * Complete OpenAPI 3.0.3 Types for InChi Pilot Gateway API (v0.1.0)
 * Aligned with docs/api/openapi.yaml generated via drf-spectacular.
 */

export interface paths {
  "/api/v1/auth/csrf/": {
    get: {
      responses: {
        200: {
          description: "CSRF cookie set successfully.";
        };
      };
    };
  };
  "/api/v1/auth/login/": {
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["LoginRequest"];
          "application/x-www-form-urlencoded": components["schemas"]["LoginRequest"];
          "multipart/form-data": components["schemas"]["LoginRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["User"];
          };
        };
        400: {
          description: "Invalid credentials or inactive account.";
        };
      };
    };
  };
  "/api/v1/auth/logout/": {
    post: {
      responses: {
        200: {
          description: "Logged out successfully.";
        };
      };
    };
  };
  "/api/v1/auth/me/": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["User"];
          };
        };
      };
    };
  };
  "/api/v1/auth/register/": {
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["RegisterRequest"];
          "application/x-www-form-urlencoded": components["schemas"]["RegisterRequest"];
          "multipart/form-data": components["schemas"]["RegisterRequest"];
        };
      };
      responses: {
        201: {
          content: {
            "application/json": components["schemas"]["User"];
          };
        };
      };
    };
  };
  "/api/v1/auth/users/": {
    get: {
      parameters?: {
        query?: {
          page?: number;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["PaginatedUserList"];
          };
        };
      };
    };
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["UserRequest"];
          "application/x-www-form-urlencoded": components["schemas"]["UserRequest"];
          "multipart/form-data": components["schemas"]["UserRequest"];
        };
      };
      responses: {
        201: {
          content: {
            "application/json": components["schemas"]["User"];
          };
        };
      };
    };
  };
  "/api/v1/auth/users/{id}/": {
    get: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["User"];
          };
        };
      };
    };
    put: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody?: {
        content: {
          "application/json": components["schemas"]["UserAdminUpdateRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["UserAdminUpdate"];
          };
        };
      };
    };
    patch: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody?: {
        content: {
          "application/json": components["schemas"]["PatchedUserAdminUpdateRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["UserAdminUpdate"];
          };
        };
      };
    };
    delete: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        204: {
          description: "No response body";
        };
      };
    };
  };
  "/api/v1/auth/users/{id}/activate/": {
    post: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody: {
        content: {
          "application/json": components["schemas"]["UserRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["User"];
          };
        };
      };
    };
  };
  "/api/v1/auth/users/{id}/deactivate/": {
    post: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody: {
        content: {
          "application/json": components["schemas"]["UserRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["User"];
          };
        };
      };
    };
  };
  "/api/v1/auth/verify/": {
    get: {
      responses: {
        200: {
          description: "Returns verification status.";
        };
      };
    };
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["VerifyAccountRequest"];
        };
      };
      responses: {
        200: {
          description: "Account verified successfully.";
        };
        400: {
          description: "Invalid or expired token.";
        };
      };
    };
  };
  "/api/v1/auth/verify/status/": {
    get: {
      responses: {
        200: {
          description: "Returns verification status.";
        };
      };
    };
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["VerifyAccountRequest"];
        };
      };
      responses: {
        200: {
          description: "Account verified successfully.";
        };
        400: {
          description: "Invalid or expired token.";
        };
      };
    };
  };
  "/api/v1/evidence/": {
    get: {
      parameters?: {
        query?: {
          page?: number;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["PaginatedEvidenceItemList"];
          };
        };
      };
    };
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["EvidenceItemRequest"];
        };
      };
      responses: {
        201: {
          content: {
            "application/json": components["schemas"]["EvidenceItem"];
          };
        };
      };
    };
  };
  "/api/v1/evidence/{id}/": {
    get: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["EvidenceItem"];
          };
        };
      };
    };
    put: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody: {
        content: {
          "application/json": components["schemas"]["EvidenceItemRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["EvidenceItem"];
          };
        };
      };
    };
    patch: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody?: {
        content: {
          "application/json": components["schemas"]["PatchedEvidenceItemRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["EvidenceItem"];
          };
        };
      };
    };
    delete: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        204: {
          description: "No response body";
        };
      };
    };
  };
  "/api/v1/products/": {
    get: {
      parameters?: {
        query?: {
          page?: number;
          search?: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["PaginatedProductList"];
          };
        };
      };
    };
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["ProductRequest"];
        };
      };
      responses: {
        201: {
          content: {
            "application/json": components["schemas"]["Product"];
          };
        };
      };
    };
  };
  "/api/v1/products/{id}/": {
    get: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Product"];
          };
        };
      };
    };
    put: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody: {
        content: {
          "application/json": components["schemas"]["ProductRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Product"];
          };
        };
      };
    };
    patch: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody?: {
        content: {
          "application/json": components["schemas"]["PatchedProductRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Product"];
          };
        };
      };
    };
    delete: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        204: {
          description: "No response body";
        };
      };
    };
  };
  "/api/v1/suppliers/": {
    get: {
      parameters?: {
        query?: {
          page?: number;
          search?: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["PaginatedSupplierList"];
          };
        };
      };
    };
    post: {
      requestBody?: {
        content: {
          "application/json": components["schemas"]["SupplierRequest"];
        };
      };
      responses: {
        201: {
          content: {
            "application/json": components["schemas"]["Supplier"];
          };
        };
      };
    };
  };
  "/api/v1/suppliers/{id}/": {
    get: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Supplier"];
          };
        };
      };
    };
    put: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody?: {
        content: {
          "application/json": components["schemas"]["SupplierRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Supplier"];
          };
        };
      };
    };
    patch: {
      parameters: {
        path: {
          id: string;
        };
      };
      requestBody?: {
        content: {
          "application/json": components["schemas"]["PatchedSupplierRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Supplier"];
          };
        };
      };
    };
    delete: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        204: {
          description: "No response body";
        };
      };
    };
  };
  "/api/v1/suppliers/{id}/archive/": {
    post: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Supplier"];
          };
        };
      };
    };
  };
  "/api/v1/suppliers/{id}/complete/": {
    post: {
      parameters: {
        path: {
          id: string;
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["Supplier"];
          };
        };
        400: {
          description: "Validation failed.";
        };
      };
    };
  };
}

export interface components {
  schemas: {
    RoleEnum: "platform_admin" | "commercial_analyst" | "reviewer";
    SupplierTypeEnum: "manufacturer" | "merchant_exporter" | "trader";
    RecordStatusEnum: "draft" | "complete" | "archived";
    TranslationStatusEnum: "not_provided" | "provided_unreviewed" | "reviewed";
    MoqUnitEnum: "MT" | "KG" | "PIECES" | "BOXES" | "CONTAINERS";
    CurrencyEnum: "USD" | "INR" | "CNY" | "EUR";
    CapacityUnitEnum: "MT" | "KG" | "PIECES" | "BOXES" | "CONTAINERS";
    CapacityPeriodEnum: "MONTH" | "YEAR" | "QUARTER";
    LeadTimeUnitEnum: "DAYS" | "WEEKS" | "MONTHS";

    User: {
      id: string;
      email: string;
      first_name?: string;
      last_name?: string;
      role: components["schemas"]["RoleEnum"];
      role_display: string;
      is_active: boolean;
      is_verified: boolean;
      is_staff: boolean;
      date_joined: string;
      last_login: string | null;
      version: number;
    };
    UserRequest: {
      email: string;
      first_name?: string;
      last_name?: string;
      role: components["schemas"]["RoleEnum"];
      is_active?: boolean;
      is_verified?: boolean;
    };
    UserAdminUpdate: {
      role: components["schemas"]["RoleEnum"];
      is_active?: boolean;
      is_verified?: boolean;
      first_name?: string;
      last_name?: string;
      version: number;
    };
    UserAdminUpdateRequest: {
      role: components["schemas"]["RoleEnum"];
      is_active?: boolean;
      is_verified?: boolean;
      first_name?: string;
      last_name?: string;
      version?: number;
    };
    PatchedUserAdminUpdateRequest: Partial<components["schemas"]["UserAdminUpdateRequest"]>;
    LoginRequest: {
      email: string;
      password: string;
    };
    RegisterRequest: {
      email: string;
      password: string;
      first_name?: string;
      last_name?: string;
      role?: components["schemas"]["RoleEnum"];
    };
    VerifyAccountRequest: {
      email: string;
      token: string;
    };
    PaginatedUserList: {
      count: number;
      next: string | null;
      previous: string | null;
      results: components["schemas"]["User"][];
    };

    Supplier: {
      id: string;
      legal_name: string;
      trade_name?: string;
      country_of_registration: string;
      supplier_type: components["schemas"]["SupplierTypeEnum"] | "";
      address?: string;
      contact_name?: string;
      contact_email?: string;
      contact_phone?: string;
      industry_description?: string;
      record_status: components["schemas"]["RecordStatusEnum"];
      version: number;
      created_by: string | null;
      created_at: string;
      updated_at: string;
    };
    SupplierRequest: {
      legal_name?: string;
      trade_name?: string;
      country_of_registration?: string;
      supplier_type?: components["schemas"]["SupplierTypeEnum"] | "";
      address?: string;
      contact_name?: string;
      contact_email?: string;
      contact_phone?: string;
      industry_description?: string;
      record_status?: components["schemas"]["RecordStatusEnum"];
      version?: number;
    };
    PatchedSupplierRequest: Partial<components["schemas"]["SupplierRequest"]>;
    PaginatedSupplierList: {
      count: number;
      next: string | null;
      previous: string | null;
      results: components["schemas"]["Supplier"][];
    };

    Product: {
      id: string;
      supplier: string;
      supplier_name: string;
      product_name: string;
      product_category: string;
      description?: string;
      product_name_zh?: string;
      short_description_zh?: string;
      translation_status: components["schemas"]["TranslationStatusEnum"];
      origin?: string;
      specifications?: string;
      moq_value: string | null;
      moq_unit: components["schemas"]["MoqUnitEnum"] | "";
      price_min: string | null;
      price_max: string | null;
      currency: components["schemas"]["CurrencyEnum"];
      price_basis?: string;
      capacity_quantity: string | null;
      capacity_unit: components["schemas"]["CapacityUnitEnum"] | "";
      capacity_period: components["schemas"]["CapacityPeriodEnum"] | "";
      lead_time_value: number | null;
      lead_time_unit: components["schemas"]["LeadTimeUnitEnum"] | "";
      version: number;
      created_by: string | null;
      created_at: string;
      updated_at: string;
    };
    ProductRequest: {
      supplier: string;
      product_name: string;
      product_category: string;
      description?: string;
      product_name_zh?: string;
      short_description_zh?: string;
      translation_status?: components["schemas"]["TranslationStatusEnum"];
      origin?: string;
      specifications?: string;
      moq_value?: string | null;
      moq_unit?: components["schemas"]["MoqUnitEnum"] | "";
      price_min?: string | null;
      price_max?: string | null;
      currency?: components["schemas"]["CurrencyEnum"];
      price_basis?: string;
      capacity_quantity?: string | null;
      capacity_unit?: components["schemas"]["CapacityUnitEnum"] | "";
      capacity_period?: components["schemas"]["CapacityPeriodEnum"] | "";
      lead_time_value?: number | null;
      lead_time_unit?: components["schemas"]["LeadTimeUnitEnum"] | "";
      version?: number;
    };
    PatchedProductRequest: Partial<components["schemas"]["ProductRequest"]>;
    PaginatedProductList: {
      count: number;
      next: string | null;
      previous: string | null;
      results: components["schemas"]["Product"][];
    };

    EvidenceItem: {
      id: string;
      supplier: string | null;
      product: string | null;
      document_type: string;
      evidence_reference: string;
      document_name?: string;
      issue_date: string | null;
      expiry_date: string | null;
      presence_status: string;
      review_status: string;
      created_at: string;
      updated_at: string;
    };
    EvidenceItemRequest: {
      supplier?: string | null;
      product?: string | null;
      document_type: string;
      evidence_reference: string;
      document_name?: string;
      issue_date?: string | null;
      expiry_date?: string | null;
      presence_status?: string;
      review_status?: string;
    };
    PatchedEvidenceItemRequest: Partial<components["schemas"]["EvidenceItemRequest"]>;
    PaginatedEvidenceItemList: {
      count: number;
      next: string | null;
      previous: string | null;
      results: components["schemas"]["EvidenceItem"][];
    };
  };
}
