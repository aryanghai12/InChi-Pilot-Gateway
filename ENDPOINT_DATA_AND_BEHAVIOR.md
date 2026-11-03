# InChi Pilot Gateway — Backend API & Data Specification
**Target Audience:** Technical Researchers, Mentors, Evaluators  
**Author:** Abhishek Kumar (Application Backend & Access-Control Engineer)  
**Status:** Operational (Week 1 Baseline)  
**Generated PDF Companion:** [`ENDPOINT_DATA_AND_BEHAVIOR.pdf`](./ENDPOINT_DATA_AND_BEHAVIOR.pdf)

---

## 1. Global Standard Error Contract

Every non-2xx response across the entire backend strictly complies with this unified error envelope:

```json
{
  "code": "string",
  "message": "string",
  "field_errors": {
    "field_name": ["Specific field error description."]
  },
  "correlation_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

| Field | Type | Description |
|---|---|---|
| `code` | `string` | Machine-readable identifier: `not_authenticated`, `permission_denied`, `validation_error`, `not_found`, `method_not_allowed`, `internal_error`. |
| `message` | `string` | Human-readable error description. |
| `field_errors` | `object<string, list>` | Detailed validation failures mapped to specific parameter keys. |
| `correlation_id` | `string (UUID)` | Injected by `CorrelationIdMiddleware` (`X-Correlation-ID`) for distributed tracing. |

---

## 2. Authentication & Session Lifecycle

### 2.1 CSRF Bootstrap
- **Endpoint:** `GET /api/v1/auth/csrf/`
- **Access:** Public
- **Headers:** None required.
- **Request Body:** None.
- **Response `200 OK`:**
  ```json
  { "detail": "CSRF cookie set." }
  ```
- **Response Headers:** `Set-Cookie: csrftoken=<token>; Path=/; SameSite=Lax`
- **Behavior:**
  - Decorated with `@ensure_csrf_cookie`.
  - Sets the `csrftoken` cookie required by the browser client to send the `X-CSRFToken` header on state-modifying requests.

---

### 2.2 User Login
- **Endpoint:** `POST /api/v1/auth/login/`
- **Access:** Public (Protected with explicit CSRF)
- **Headers:** `X-CSRFToken: <token>`, `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "email": "analyst@bncs.local",
    "password": "StrongPassword123!"
  }
  ```
  | Field | Type | Required | Description |
  |---|---|---|---|
  | `email` | `string (email)` | Yes | Normalized to lowercase, whitespace stripped. |
  | `password` | `string` | Yes | Raw string. Never logged or exposed. |

- **Response `200 OK`:**
  ```json
  {
    "message": "Login successful.",
    "user": {
      "id": "e6e5f83f-5edd-48c0-bbce-d37bebc52c6f",
      "email": "analyst@bncs.local",
      "first_name": "Aarav",
      "last_name": "Sharma",
      "role": "commercial_analyst",
      "role_display": "Commercial Analyst",
      "is_active": true,
      "is_verified": true,
      "is_staff": false,
      "date_joined": "2026-10-29T10:00:00Z",
      "last_login": "2026-10-29T13:45:00Z",
      "version": 1
    }
  }
  ```
- **Response `400 Bad Request` (Invalid Credentials or Deactivated Account):**
  ```json
  {
    "code": "validation_error",
    "message": "Input validation failed. Please check field errors.",
    "field_errors": {
      "non_field_errors": ["Invalid email or password."]
    },
    "correlation_id": "a90b4cf2-..."
  }
  ```
- **Behavior:**
  - Enforces `@csrf_protect`.
  - Calls `django.contrib.auth.login()`, automatically rotating the session key and the CSRF token to prevent session fixation.
  - Generic error messages prevent username enumeration.

---

### 2.3 Current Authenticated User Profile
- **Endpoint:** `GET /api/v1/auth/me/`
- **Access:** Authenticated (All Roles)
- **Headers:** Session cookie (`sessionid=<id>`)
- **Request Body:** None.
- **Response `200 OK`:** Same `user` object shape as in `POST /login/`.
- **Response `401 Unauthorized`:**
  ```json
  {
    "code": "not_authenticated",
    "message": "Authentication credentials were not provided or are invalid.",
    "field_errors": {},
    "correlation_id": "5fae76c1-..."
  }
  ```
- **Behavior:**
  - Evaluates session cookie; returns active role and profile for frontend route guards.

---

### 2.4 User Logout
- **Endpoint:** `POST /api/v1/auth/logout/`
- **Access:** Authenticated (All Roles)
- **Headers:** Session cookie (`sessionid=<id>`), `X-CSRFToken: <token>`
- **Request Body:** None.
- **Response `200 OK`:**
  ```json
  { "detail": "Logged out successfully." }
  ```
- **Behavior:**
  - Calls `django.contrib.auth.logout()`, immediately flushing server session records and expiring client cookies.

---

## 3. User Onboarding & Account Verification

### 3.1 Register User Account
- **Endpoint:** `POST /api/v1/auth/register/`
- **Access:** Public / Admin Onboarding
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "email": "new.member@bncs.local",
    "password": "SecurePassword123!",
    "first_name": "Rohan",
    "last_name": "Verma",
    "role": "commercial_analyst"
  }
  ```
  | Field | Type | Required | Description |
  |---|---|---|---|
  | `email` | `string (email)` | Yes | Unique, max 254 chars. |
  | `password` | `string` | Yes | Min 8 chars, validated by Django password validators. |
  | `first_name` | `string` | No | Max 150 chars. |
  | `last_name` | `string` | No | Max 150 chars. |
  | `role` | `string` | No | Choice: `platform_admin`, `commercial_analyst`, `reviewer`. Default: `commercial_analyst`. |

- **Response `201 Created`:**
  ```json
  {
    "message": "User registered successfully. Please complete verification.",
    "user": {
      "id": "78b4a112-9c22-482d-8f20-fa728c312741",
      "email": "new.member@bncs.local",
      "first_name": "Rohan",
      "last_name": "Verma",
      "role": "commercial_analyst",
      "role_display": "Commercial Analyst",
      "is_active": true,
      "is_verified": false
    },
    "verification_token": "f2905b63-8a32-4752-9ef8-e160e90c6792"
  }
  ```
- **Behavior:**
  - Instantiates user with `is_verified=False` and generates a single-use UUID v4 `verification_token`.

---

### 3.2 Verify User Account
- **Endpoint:** `POST /api/v1/auth/verify/`
- **Access:** Public
- **Headers:** `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "email": "new.member@bncs.local",
    "token": "f2905b63-8a32-4752-9ef8-e160e90c6792"
  }
  ```
  | Field | Type | Required | Description |
  |---|---|---|---|
  | `email` | `string (email)` | Yes | Target account email. |
  | `token` | `string` | Yes | Matching verification token. |

- **Response `200 OK`:**
  ```json
  {
    "message": "Account successfully verified. You may now log in.",
    "user": {
      "id": "78b4a112-9c22-482d-8f20-fa728c312741",
      "email": "new.member@bncs.local",
      "is_verified": true
    }
  }
  ```
- **Behavior:**
  - On token match: sets `is_verified = True`, clears `verification_token = null` (token exhaustion protection), and increments record `version`.

---

### 3.3 Check Verification Status
- **Endpoint:** `GET /api/v1/auth/verify/status/?email=<address>`
- **Access:** Public
- **Query Parameter:** `email` (`string`, required)
- **Response `200 OK`:**
  ```json
  {
    "email": "new.member@bncs.local",
    "is_verified": true,
    "is_active": true
  }
  ```

---

## 4. Role-Based User Administration (Platform Admin Only)

### 4.1 List All Internal Users
- **Endpoint:** `GET /api/v1/auth/users/`
- **Access:** **Platform Administrator Only** (`role == "platform_admin"`)
- **Headers:** Session cookie
- **Response `200 OK`:**
  ```json
  {
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "e6e5f83f-5edd-48c0-bbce-d37bebc52c6f",
        "email": "admin@bncs.local",
        "role": "platform_admin",
        "role_display": "Platform Administrator",
        "is_active": true,
        "is_verified": true,
        "is_staff": true,
        "date_joined": "2026-10-29T10:00:00Z",
        "version": 1
      }
    ]
  }
  ```
- **Response `403 Forbidden` (If called by Commercial Analyst or Reviewer):**
  ```json
  {
    "code": "permission_denied",
    "message": "You do not have permission to perform this action.",
    "field_errors": {},
    "correlation_id": "7cb419e2-..."
  }
  ```

---

### 4.2 Deactivate User Account
- **Endpoint:** `POST /api/v1/auth/users/{id}/deactivate/`
- **Access:** **Platform Administrator Only**
- **URL Parameter:** `{id}` (UUID of target user)
- **Response `200 OK` (Valid Target):**
  ```json
  {
    "message": "User analyst@bncs.local has been deactivated.",
    "user": {
      "id": "...",
      "email": "analyst@bncs.local",
      "is_active": false,
      "version": 2
    }
  }
  ```
- **Response `403 Forbidden` (Self-Deactivation Guard):**
  ```json
  {
    "code": "permission_denied",
    "message": "You cannot deactivate your own account.",
    "field_errors": {},
    "correlation_id": "..."
  }
  ```
- **Behavior:**
  - Soft-deactivates the user (`is_active = False`).
  - Strict guard: Prevents administrators from deactivating themselves, avoiding administrative lockout.

---

### 4.3 Reactivate User Account
- **Endpoint:** `POST /api/v1/auth/users/{id}/activate/`
- **Access:** **Platform Administrator Only**
- **Response `200 OK`:**
  ```json
  {
    "message": "User analyst@bncs.local has been activated.",
    "user": {
      "id": "...",
      "email": "analyst@bncs.local",
      "is_active": true,
      "version": 3
    }
  }
  ```

---

## 5. System Health & Documentation Endpoints

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| `GET` | `/api/v1/health/` | Public | System liveness probe returning `{"status": "ok", "service": "inchi-backend"}`. |
| `GET` | `/api/docs/` | Public | Interactive Swagger UI documentation with interactive testing. |
| `GET` | `/api/schema/` | Public | OpenAPI 3.0 schema definition in YAML/JSON. |

---

*Report prepared by Abhishek Kumar — Application Backend & Access-Control Engineer*
