# Threat Model — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Working Baseline (Updated Post-Week 4 Audit, 21 Nov 2026) |
| **Methodology** | STRIDE Framework + OWASP Top 10:2021 + Baseline v2.2 §14.3 Threat-Focused Architecture |
| **Governing Baseline** | [`InChi_China_Readiness_Implementation_Baseline_v2.2.pdf`](../source-documents/InChi_China_Readiness_Implementation_Baseline_v2.2.pdf) §14; [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §3, §6, §7 |

---

## 1. Scope & System Architecture

InChi Pilot Gateway is a private, internal decision-support web application for authorised BNCS users. This threat model evaluates the software architecture, inter-service communication, data flows, and trust boundaries defined in [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) and governed by Baseline v2.2.

```
[ Browser (Untrusted Client) ]
       │  Single Origin (http://localhost:3000)
───────┼─────────────────────────────────────────────────────────────
       ▼  TRUST BOUNDARY 1 (Edge / Single-Origin Reverse Proxy)
[ Next.js Server (Node.js) ]
  • Client Component rendering
  • Proxies /api/v1/ to Django (TD-09)
  • Injects client security headers (nosniff, DENY, Referrer-Policy)
  • NO Route Handlers, NO Server Actions, NO Secrets (TD-10)
───────┼─────────────────────────────────────────────────────────────
       ▼  TRUST BOUNDARY 2 (Application & Authorization Authority)
[ Django 5.2 LTS + DRF Application Layer ]
  • SessionAuthentication + CSRF Validation (TD-05, TD-06)
  • RBAC & Object-Level Checks (accounts/policy.py)
  • Transactional Audit Logging (M10, TD-03)
  • NO self-registration; all accounts provisioned by Administrator
───────┼─────────────────────────────────────────────────────────────
       ├──────────────────────────────────────────┐
       ▼ TRUST BOUNDARY 3                         ▼ TRUST BOUNDARY 4
[ FastAPI AI Matching Engine ]             [ PostgreSQL 17 + pgvector ]
  • Strict Pydantic input validation         • Persistent relation store
  • Deterministic rules first (v2.2 §9)      • pgvector similarity (TD-01)
  • Local embeddings only (D-11, TBD)        • DB trigger: UPDATE/DELETE blocked
  • Explicit failure on error (M6-AC5)         on AuditEvent table (TD-03)
```

---

## 2. Trust Boundaries & Attack Surfaces

| Boundary | Interface | Primary Attack Surfaces & Risk Factors |
|---|---|---|
| **Boundary 1** | Browser $\rightarrow$ Next.js | XSS, CSRF token theft, unauthorized client storage access, session hijacking. |
| **Boundary 2** | Next.js Proxy $\rightarrow$ Django | Header spoofing (`X-Forwarded-For`), host header poisoning (`ALLOWED_HOSTS`), CSRF origin mismatch (`CSRF_TRUSTED_ORIGINS`), proxy bypass, anonymous self-registration bypass (AUD-01). |
| **Boundary 3** | Django $\rightarrow$ FastAPI AI Engine | Unbounded payloads, input manipulation to distort matching scores, unhandled timeouts/exceptions. |
| **Boundary 4** | Django $\rightarrow$ PostgreSQL 17 | SQL injection, unauthorized audit modification, vector data tampering, unhashed password insertion (AUD-15). |

---

## 3. STRIDE Threat Analysis

### 3.1 Spoofing (Identity & Authentication)

* **T-SP-01: Session Fixation & Cookie Hijacking**
  * *Threat*: An attacker intercepts or fixes an active session ID to impersonate an authorized BNCS internal user.
  * *Impact*: High (Unauthorized access to supplier registry and commercial requirements).
  * *Mitigation*: Django's `login()` rotates session keys automatically (`TD-08`). Cookies configured with `HttpOnly=True`, `SameSite='Lax'`, and `Secure=True` in staging. Absolute session timeout enforced via `SESSION_COOKIE_AGE=28800`.
* **T-SP-02: Proxy Header & Host Spoofing**
  * *Threat*: An attacker sends fabricated `X-Forwarded-Host` or `X-Forwarded-Proto` headers to bypass origin restrictions.
  * *Impact*: High (CSRF bypass, cache poisoning).
  * *Mitigation*: Django settings strictly configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`. `SECURE_PROXY_SSL_HEADER` is enabled *only* behind verified trusted reverse proxies.

---

### 3.2 Tampering (Data Integrity & Insecure Direct Object References)

* **T-TM-01: Insecure Direct Object Reference (IDOR) on Commercial Records (SEC-03)**
  * *Threat*: An authenticated user modifies or deletes supplier/product/requirement records owned by another user or in a finalized/locked state.
  * *Impact*: High (Unauthorized record alteration, data corruption).
  * *Mitigation*: Backend enforces object-level permissions in DRF `check_object_permissions()` and `get_queryset()`. State transitions strictly restricted via transition services with optimistic concurrency locking (`version` column checking; returns 409 Conflict on mismatch).
* **T-TM-02: Audit Log Tampering or Deletion (SEC-06)**
  * *Threat*: A malicious insider attempts to delete or alter historical audit logs to conceal unauthorized activities.
  * *Impact*: Critical (Breakdown of pilot accountability and compliance).
  * *Mitigation*: `AuditEvent` model exposes no `UPDATE` or `DELETE` endpoints. Database layer enforces an immutable PostgreSQL trigger rejecting all `UPDATE` and `DELETE` operations at the database engine level (`TD-03`).
* **T-TM-03: Matching Input Manipulation (Criteria Tampering)**
  * *Threat*: An operator crafts or tampers with buyer requirement inputs to force an ineligible supplier to be recommended.
  * *Impact*: Critical (Loss of decision integrity, biased recommendations).
  * *Mitigation*: Baseline v2.2 §9 deterministic matching rules: category fit, MOQ, capacity, lead time, and required evidence evaluate as hard mandatory gates. Failing a mandatory filter *permanently excludes* the candidate (`NOT_ELIGIBLE`). Missing mandatory fields produce `INFORMATION_REQUIRED`. Preferences never override mandatory failure.
* **T-TM-04: Workflow State Tampering (Readiness & Demand)**
  * *Threat*: A Contributor attempts to advance an assessment directly to `Review Complete` or an unapproved user transitions a buyer requirement to `Ready for Matching`.
  * *Impact*: High (Circumvention of quality and verification gates).
  * *Mitigation*: State transitions enforced strictly in backend service methods. The submission gate checks that all 18 baseline questions and evidence links are complete before allowing `Submitted` status. Only Reviewers can trigger `complete_review`.

---

### 3.3 Repudiation

* **T-RP-01: Unattributable Commercial Decisions & Dispositions**
  * *Threat*: An internal user records a match disposition (`Accept for Follow-up`, `Hold for Information`, `Reject`) or closes a requirement without attribution.
  * *Impact*: Medium (Loss of traceability).
  * *Mitigation*: M10 audit architecture records actor, timestamp (UTC), correlation ID, target object ID, before/after values, and mandatory justification reasons inside an atomic transaction (AC-19, AC-23).

---

### 3.4 Information Disclosure

* **T-ID-01: Accidental Secret / Credential Leakage in Source Control (SEC-05)**
  * *Threat*: Committing real API keys, database credentials, or local environment files into git.
  * *Impact*: Critical (Unauthorized environment compromise).
  * *Mitigation*: Root `.gitignore` enforces exclusion of `.env` and `.env.*` while preserving `.env.example`. Automated `gitleaks` job in CI blocks PRs containing plaintext secrets.
* **T-ID-02: Verbose Error & Stack Trace Leakage**
  * *Threat*: Database or internal application exceptions return raw stack traces to the Next.js frontend or browser.
  * *Impact*: Low/Medium (Reconnaissance aid for internal attackers).
  * *Mitigation*: Django custom exception handler maps all unhandled exceptions into the uniform error shape: `{"code", "message", "field_errors", "correlation_id"}`. `DEBUG=False` enforced in deployed environments.
* **T-ID-03: Pilot Data Exfiltration via External AI APIs**
  * *Threat*: Sending supplier capabilities or buyer requirements to public LLMs or hosted cloud embedding APIs.
  * *Impact*: Critical (Breach of BNCS confidentiality, violating project charter).
  * *Mitigation*: Architectural rule: **Zero external AI/LLM APIs in v0.1 (Baseline v2.2 §14.2)**. Embedding generation executes strictly locally on CPU (D-11). No LLM dependencies or prompts permitted in codebase (D-20).
* **T-ID-04: Plaintext Password Storage in Administrative Provisioning (AUD-15)**
  * *Threat*: Platform Administrator creates a user via Django admin `UserAdmin` without password hashing, storing plaintext credentials in the database.
  * *Impact*: High (Exposure of credentials to database administrators and compromised database dumps; inability of user to authenticate).
  * *Mitigation*: Custom `UserAdmin` must inherit from Django's `UserAdmin` or override `save_model` to enforce `user.set_password()`, guaranteeing PBKDF2 hashing.

---

### 3.5 Denial of Service

* **T-DS-01: AI Matching Processing Exhaustion**
  * *Threat*: Flooding computationally expensive matching requests into the FastAPI AI matching engine, causing CPU starvation.
  * *Impact*: Medium (Service unavailability for internal analysts).
  * *Mitigation*: Strict Pydantic input schemas in FastAPI with length constraints; synchronous execution bounded by candidate query filters in PostgreSQL.
* **T-DS-02: Authentication Brute Force**
  * *Threat*: Credential guessing against `/api/v1/auth/login/`.
  * *Impact*: Medium (Account lockouts or credential compromise).
  * *Mitigation*: Login rate limiting evaluated under TD-04.

---

### 3.6 Elevation of Privilege

* **T-EP-01: Privilege Escalation across Internal Roles (SEC-01, SEC-02)**
  * *Threat*: A Data Contributor or Commercial Analyst attempts to perform Reviewer tasks (recording match dispositions or approving readiness assessments) or Platform Administrator tasks (user role management).
  * *Impact*: High (Circumvention of two-person workflow integrity).
  * *Mitigation*: Explicit DRF permission classes on every endpoint, backed by `backend/apps/accounts/policy.py`. Deny-by-default access model.
* **T-EP-02: Administrator Interference in Commercial Operations**
  * *Threat*: A Platform Administrator uses administrative privileges to alter supplier records or buyer requirements.
  * *Impact*: Medium (Violation of least-privilege principle).
  * *Mitigation*: Platform Admin access is restricted strictly to user account provisioning and role assignments via the restricted Django admin. Platform Admin possesses view-only or no access to commercial workflows (Baseline v2.2 §4).
* **T-EP-03: Anonymous Self-Registration with Arbitrary Role Assignment (AUD-01)**
  * *Threat*: An anonymous attacker calls `POST /api/v1/auth/register/` with payload `{"role": "platform_admin", ...}` to create an unverified administrator account, retrieves the verification token returned in the response, verifies via `POST /verify/`, and logs in as a Platform Administrator.
  * *Impact*: **Critical (Total System Takeover)**. Violates D-12, Baseline v2.2 §14.1, and blocks Gate 4 acceptance.
  * *Mitigation*: Disable anonymous self-registration endpoints. Account creation must be restricted strictly to authenticated Administrators via `UserAdmin` or CLI `create_platform_admin`.

---

## 4. Threat Summary & Security Verification Matrix (Baseline v2.2 §14.3)

| Test ID | Baseline Threat Description | Severity | Target Component | Status / Verification Method | Lead Owner |
|---|---|---|---|---|---|
| **SEC-01** | A Viewer cannot call create or update endpoints directly | High | All write endpoints | Automated negative pytest in `test_security_posture.py` | Abhishek / Ajendra |
| **SEC-02** | A Contributor cannot mark evidence as Official Source Checked | High | `AssessmentEvidenceViewSet` | Automated negative pytest asserting Contributor rejection | Abhishek / Ajendra |
| **SEC-03** | A user cannot alter another record by changing a URL or identifier (IDOR) | High | `Supplier`, `Product`, `Requirement` | Object-level permission test across user scopes | Abhishek / Harish |
| **SEC-04** | Unsupported file extensions and oversized files are rejected if upload implemented | Medium | Evidence upload (D-10) | Verified: File upload excluded from v0.1 (metadata only) | Abhishek / Ajendra |
| **SEC-05** | Sensitive values do not appear in browser console logs, error messages or source control | Critical | Git repo, API responses | CI Gitleaks check; serializer output password redaction test | Ajendra / Harish |
| **SEC-06** | Audit records cannot be edited through normal application functions | Critical | `AuditEvent` PostgreSQL table | Database trigger test: `UPDATE` and `DELETE` raise PermissionDenied | Vishal / Ajendra |
| **AUD-01** | Anonymous self-registration privilege escalation exploit | Critical | `RegisterView`, `VerifyAccountView` | Negative security test asserting endpoint restriction / non-exposure | Abhishek / Ajendra |
| **AUD-15** | Plaintext password persistence via Django Admin user creation | High | `accounts/admin.py` | Unit test verifying password hashing on admin save | Abhishek / Ajendra |
