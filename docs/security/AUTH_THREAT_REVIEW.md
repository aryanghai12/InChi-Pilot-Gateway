# Authentication & Session Security Review (Week 2 Baseline)

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Working Baseline & Design Verification |
| **Target Architecture** | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §5, §7, §9 (TD-04, TD-05, TD-06, TD-08, TD-09, TD-10) |
| **Component Owners** | Abhishek Kumar (Backend), Priyanka Singh (Frontend) |

---

## 1. Executive Summary

This security review formally evaluates the authentication, session lifecycle, CSRF protection, and reverse-proxy architecture for the InChi Pilot Gateway.

The application implements a **Single-Origin Session Architecture** utilizing Django's built-in session framework, reverse-proxied through the Next.js App Router. This approach was selected to eliminate the risks of token theft (such as JWT exfiltration from `localStorage`) and cross-origin resource sharing (CORS) misconfigurations.

---

## 2. Review of Technical Decisions

### 2.1 Login CSRF Protection & Bootstrap (TD-05)

* **Threat**: Login CSRF attacks where an attacker forces a victim's browser to authenticate with attacker-controlled credentials, thereby logging user activity.
* **Vulnerability in Standard DRF**: Standard Django REST Framework `SessionAuthentication` does *not* enforce CSRF validation on unauthenticated endpoints. An anonymous login view is therefore vulnerable unless explicitly hardened.
* **Required Implementation**:
  1. The login endpoint (`POST /api/v1/auth/login/`) must be explicitly decorated with `@method_decorator(csrf_protect)` and set `authentication_classes = []`.
  2. The bootstrap endpoint `GET /api/v1/auth/csrf/` must be decorated with `@ensure_csrf_cookie` so that the client receives the `csrftoken` cookie prior to presenting the login form.
  3. The frontend `apiFetch()` wrapper reads `csrftoken` from `document.cookie` and transmits it in the `X-CSRFToken` request header for all state-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`).

---

### 2.2 Error Semantics: 401 vs 403 Distinction (TD-06)

* **Threat**: Session state ambiguity where permission denials trigger unwanted session terminations, or unauthenticated requests produce unclear client behavior.
* **Required Implementation**:
  * **HTTP 401 `not_authenticated`**: Returned when a session is absent, invalid, or expired. The Next.js frontend catches this code, clears its client query cache, and redirects the user to `/login`.
  * **HTTP 403 `permission_denied`**: Returned when a user is validly authenticated but attempts an operation prohibited for their role (e.g. an Analyst attempting to approve an assessment). The frontend displays the inline `<AccessDenied />` state and **preserves the active user session**.
  * **HTTP 403 `csrf_failed`**: Returned on CSRF token mismatch or absence. The frontend executes exactly one silent `GET /api/v1/auth/csrf/` call to refresh the token and retries the request once before showing an error.

---

### 2.3 Session Lifecycle & Rotation (TD-08)

* **Threat**: Session fixation and persistent credentials.
* **Required Implementation**:
  1. **Key Rotation on Login**: Calling Django's `login(request, user)` immediately invalidates the pre-authentication session key and assigns a new cryptographically random key.
  2. **Cookie Attributes**:
     * `SESSION_COOKIE_HTTPONLY = True`: Blocks client JavaScript (`document.cookie`) from accessing the session token.
     * `SESSION_COOKIE_SAMESITE = 'Lax'`: Mitigates cross-site request forgery while permitting top-level navigation.
     * `SESSION_COOKIE_SECURE = True`: Enforced whenever TLS/HTTPS is active.
     * `SESSION_COOKIE_AGE = 28800`: 8-hour maximum session lifetime.
  3. **First Platform Administrator**:
     * Accounts must be provisioned via `manage.py create_platform_admin --email <email>`.
     * Direct database manipulation and raw `createsuperuser` are prohibited. The admin user is provisioned with `is_superuser=False` and restricted to user lifecycle administration.

---

### 2.4 Single-Origin Proxy Boundary (TD-09) & Rendering Boundary (TD-10)

* **Threat**: Architecture bypass where Next.js acts as an unsanctioned secondary backend, or header spoofing compromises backend trust.
* **Required Guardrails**:
  1. **Next.js Reverse Proxy (`next.config.ts`)**:
     * Next.js App Router forwards all `/api/:path*`, the admin URL, and static Django assets to `BACKEND_ORIGIN`.
     * The browser interacts with a single origin (`http://localhost:3000` in local dev).
  2. **Django Host Configuration**:
     * `ALLOWED_HOSTS` must strictly validate the hostname.
     * `CSRF_TRUSTED_ORIGINS` must include the public browser origin.
     * `SECURE_PROXY_SSL_HEADER` must only be configured when operating behind a verified reverse proxy that sets `X-Forwarded-Proto`.
  3. **Strict Rendering Boundary (TD-10)**:
     * Next.js pages displaying pilot data are Client Components (`'use client'`).
     * **No Route Handlers** (no `src/app/api/` folder).
     * **No Server Actions**.
     * Next.js server holds zero secrets and enforces zero authorization logic.

---

### 2.5 Login Throttling & Brute-Force Defense (TD-04)

* **Assessment**: The pilot system uses internal user accounts with PBKDF2 hashing. In non-production local development, brute-force threats are low; however, for staging or multi-user validation, unthrottled endpoints represent an operational risk.
* **Recommendation**:
  * Implement an IP and username based throttle on `POST /api/v1/auth/login/` (e.g. max 5 attempts per minute).
  * Abhishek will configure this via DRF's `ScopedRateThrottle` or a custom throttle class in `backend/apps/accounts/throttling.py`.

---

## 3. Negative Security Verification Test Cases (for Harish / QA)

To verify the authentication posture, Harish and Ajendra have defined the following automated negative test cases:

1. **TEST-AUTH-01: Login without CSRF token is rejected**:
   * Request: `POST /api/v1/auth/login/` with credentials but without `X-CSRFToken` header.
   * Expected: HTTP 403 with `{"code": "csrf_failed"}`.
2. **TEST-AUTH-02: Expired or missing session returns 401**:
   * Request: `GET /api/v1/suppliers/` without session cookie.
   * Expected: HTTP 401 with `{"code": "not_authenticated"}`.
3. **TEST-AUTH-03: Role boundary violation returns 403**:
   * Request: `POST /api/v1/assessments/1/review/` executed by a user with role `commercial_analyst`.
   * Expected: HTTP 403 with `{"code": "permission_denied"}`. Session remains active.
4. **TEST-AUTH-04: Session key rotation on login**:
   * Sequence: Obtain pre-login session cookie; execute successful login; assert new session cookie value does not match initial cookie.

