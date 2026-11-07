/**
 * Placeholder for OpenAPI types generated from docs/api/openapi.yaml.
 * Generated via: npm run generate-types
 * Abhishek (Backend) owns openapi.yaml generation via drf-spectacular.
 */
export interface paths {
  "/api/v1/auth/csrf/": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": {
              detail?: string;
            };
          };
        };
      };
    };
  };
  "/api/v1/auth/login/": {
    post: {
      requestBody: {
        content: {
          "application/json": {
            username?: string;
            password?: string;
          };
        };
      };
      responses: {
        200: {
          content: {
            "application/json": {
              id: string | number;
              username: string;
              email: string;
              role: "platform_admin" | "commercial_analyst" | "reviewer";
            };
          };
        };
      };
    };
  };
  "/api/v1/auth/logout/": {
    post: {
      responses: {
        200: {
          content: {
            "application/json": {
              detail: string;
            };
          };
        };
      };
    };
  };
  "/api/v1/auth/me/": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": {
              id: string | number;
              username: string;
              email: string;
              role: "platform_admin" | "commercial_analyst" | "reviewer";
              is_active: boolean;
            };
          };
        };
      };
    };
  };
}
