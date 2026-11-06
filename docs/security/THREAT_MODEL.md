# Threat Model — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Working Baseline (v0.1) |
| **Methodology** | STRIDE Framework + OWASP Top 10:2021 + AI Risk Surface Analysis |
| **Target Architecture** | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §3, §6, §7; [`../MVP_FEATURES.md`](../MVP_FEATURES.md) §7, §8 |

---

## 1. Scope & System Architecture

InChi Pilot Gateway is a private, internal decision-support web application for authorised BNCS users. This threat model evaluates the software architecture, inter-service communication, data flows, and trust boundaries defined in [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md).

```
[ Browser (Untrusted Client) ]
       │  Single Origin (http://localhost:3000)
───────┼─────────────────────────────────────────────────────────────
       ▼  TRUST BOUNDARY 1 (Edge / Single-Origin Reverse Proxy)
[ Next.js Server (Node.js) ]
  • Client Component rendering
  • Proxies /api/v1/ to Django (TD-09)
  • NO Route Handlers, NO Server Actions, NO Secrets (TD-10)
───────┼─────────────────────────────────────────────────────────────
       ▼  TRUST BOUNDARY 2 (Application & Authorization Authority)
[ Django 5.2 LTS + DRF Application Layer ]
  • SessionAuthentication + CSRF Validation (TD-05, TD-06)
  • RBAC & Object-Level Checks (accounts/policy.py)
  • Transactional Audit Logging (M10, TD-03)
───────┼─────────────────────────────────────────────────────────────
       ├──────────────────────────────────────────┐
       ▼ TRUST BOUNDARY 3                         ▼ TRUST BOUNDARY 4
[ FastAPI AI Matching Engine ]             [ PostgreSQL 17 + pgvector ]
  • Strict Pydantic input validation         • Persistent relation store
  • Local embeddings (D-11, local only)      • pgvector similarity (TD-01)
  • Hard eligibility gates + hybrid score     • DB trigger: UPDATE/DELETE blocked
  • Explicit failure on error (M6-AC5)         on AuditEvent table (TD-03)
```

---

## 2. Trust Boundaries & Attack Surfaces

| Boundary | Interface | Primary Attack Surfaces & Risk Factors |
|---|---|---|
| **Boundary 1** | Browser $\rightarrow$ Next.js | XSS, CSRF token theft, unauthorized client storage access, session hijacking. |
| **Boundary 2** | Next.js Proxy $\rightarrow$ Django | Header spoofing (`X-Forwarded-For`), host header poisoning (`ALLOWED_HOSTS`), CSRF origin mismatch (`CSRF_TRUSTED_ORIGINS`), proxy bypass. |
| **Boundary 3** | Django $\rightarrow$ FastAPI AI Engine | Unbounded payloads, input manipulation to distort hybrid matching scores, unexpected exception propagation. |
| **Boundary 4** | Django $\rightarrow$ PostgreSQL 17 | SQL injection, unauthorized audit modification, vector data tampering. |

---

## 3. STRIDE Threat Analysis

### 3.1 Spoofing (Identity & Authentication)

* **T-SP-01: Session Fixation & Cookie Hijacking**
  * *Threat*: An attacker intercepts or fixes an active session ID to impersonate an authorized BNCS internal user.
  * *Impact*: High (Unauthorized access to supplier registry and commercial requirements).
  * *Mitigation*: Django's `login()` rotates session keys automatically. Cookies must be configured with `HttpOnly=True`, `SameSite='Lax'`, and `Secure=True` in production/staging. Absolute session timeout enforced via `SESSION_COOKIE_AGE` (default 8 hours).

* **T-SP-02: Proxy Header & Host Spoofing**
  * *Threat*: An attacker sends fabricated `X-Forwarded-Host` or `X-Forwarded-Proto` headers to bypass origin restrictions.
  * *Impact*: High (CSRF bypass, cache poisoning).
  * *Mitigation*: Django settings strictly configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`. `SECURE_PROXY_SSL_HEADER` is enabled *only* behind verified trusted reverse proxies.

---

### 3.2 Tampering (Data Integrity & Insecure Direct Object References)

* **T-TM-01: Insecure Direct Object Reference (IDOR) on Commercial Records**
  * *Threat*: An authenticated Commercial Analyst modifies or deletes supplier/product records owned by another user or in a finalized state.
  * *Impact*: High (Unauthorized record alteration, data corruption).
  * *Mitigation*: Backend enforces object-level permissions in DRF `get_queryset()` and `has_object_permission()`. State transitions strictly restricted via `services.py` transition functions with optimistic locking (`version` column checking; returns 409 Conflict on mismatch).

* **T-TM-02: Audit Log Tampering or Deletion**
  * *Threat*: A malicious insider attempts to delete or alter historical audit logs to conceal unauthorized activities.
  * *Impact*: Critical (Breakdown of pilot accountability and compliance).
  * *Mitigation*: `AuditEvent` model exposes no `UPDATE` or `DELETE` endpoints. Database layer enforces an immutable PostgreSQL trigger rejecting all `UPDATE` and `DELETE` operations at the engine level (TD-03).

* **T-TM-03: Matching Input Manipulation (Criteria Tampering)**
  * *Threat*: An operator crafts or tampers with buyer requirement inputs to force an ineligible supplier to be recommended.
  * *Impact*: Critical (Loss of decision integrity, biased AI recommendations).
  * *Mitigation*: Mandatory eligibility evaluation (Stage 2) operates as hard gates. Failing a mandatory filter *permanently excludes* the candidate. Unknown mandatory fields are classified as `Insufficient Data` and never treated as a pass. Semantic similarity *cannot* override a mandatory failure.

---

### 3.3 Repudiation

* **T-RP-01: Unattributable Commercial Decisions & Dispositions**
  * *Threat*: An internal user records a match disposition (`Accepted` / `Rejected`) or closes an opportunity without attribution.
  * *Impact*: Medium (Loss of traceability).
  * *Mitigation*: M10 audit architecture records actor, timestamp, correlation ID, target object ID, before/after values, and mandatory justification reasons inside an atomic transaction.

---

### 3.4 Information Disclosure

* **T-ID-01: Accidental Secret / Credential Leakage in Source Control**
  * *Threat*: Committing real API keys, database credentials, or local environment files into git.
  * *Impact*: Critical (Unauthorized environment compromise).
  * *Mitigation*: Root `.gitignore` enforces exclusion of `.env` and `.env.*` while preserving `.env.example`. Automated `gitleaks` job in CI blocks PRs containing plaintext secrets.

* **T-ID-02: Verbose Error & Stack Trace Leakage**
  * *Threat*: Database or internal application exceptions return raw stack traces to the Next.js frontend or browser.
  * *Impact*: Low/Medium (Reconnaissance aid for internal attackers).
  * *Mitigation*: Django custom exception handler maps all unhandled exceptions into the uniform error shape: `{"code", "message", "field_errors", "correlation_id"}`. `DEBUG=False` enforced in all deployed/staging environments.

* **T-ID-03: Pilot Data Exfiltration via External AI APIs**
  * *Threat*: Sending supplier capabilities or buyer requirements to public LLMs or hosted cloud embedding APIs.
  * *Impact*: Critical (Breach of BNCS confidentiality, violating project charter).
  * *Mitigation*: Architectural rule: **Zero external AI/LLM APIs in v0.1**. Embedding generation executes strictly locally on CPU (D-11). No LLM dependencies or prompts permitted in codebase (D-20).

---

### 3.5 Denial of Service

* **T-DS-01: AI Matching Processing Exhaustion**
  * *Threat*: Large unstructured specification payloads flooded into the FastAPI AI matching engine, causing CPU starvation.
  * *Impact*: Medium (Service unavailability for internal analysts).
  * *Mitigation*: Strict Pydantic input schemas in FastAPI with length constraints; synchronous execution bounded by candidate query filters in PostgreSQL.

* **T-DS-02: Authentication Brute Force**
  * *Threat*: Credential guessing against `/api/v1/auth/login/`.
  * *Impact*: Medium (Account lockouts or credential compromise).
  * *Mitigation*: Login rate limiting evaluated under TD-04.

---

### 3.6 Elevation of Privilege

* **T-EP-01: Privilege Escalation across Internal Roles**
  * *Threat*: A Commercial Analyst attempts to perform Reviewer tasks (recording match dispositions or approving readiness assessments) or Platform Administrator tasks (user role management).
  * *Impact*: High (Circumvention of two-person workflow integrity).
  * *Mitigation*: Explicit DRF permission classes on every endpoint, backed by the centralized `backend/apps/accounts/policy.py` policy matrix. Deny-by-default access model.

* **T-EP-02: Administrator Interference in Commercial Operations**
  * *Threat*: A Platform Administrator uses administrative privileges to alter supplier records or buyer requirements.
  * *Impact*: Medium (Violation of least-privilege principle).
  * *Mitigation*: Platform Admin access is restricted strictly to user account provisioning and role assignments via the restricted Django admin (`accounts/UserAdmin`). Platform Admin possesses view-only or no access to commercial workflows (MVP_FEATURES §5).

---

## 4. Threat Summary & Security Verification Matrix

| Threat ID | Category | Component | Severity | Test & Verification Strategy | Owner |
|---|---|---|---|---|---|
| **T-SP-01** | Spoofing | Django Auth | High | Automated negative test: session rotation on login/logout; cookie flag assertions. | Abhishek / Ajendra |
| **T-SP-02** | Spoofing | Next.js / Django | High | Integration test: verify CSRF origin rejection on spoofed host headers. | Abhishek / Ajendra |
| **T-TM-01** | Tampering | DRF Views | High | Automated negative test: analyst attempt to edit another user's draft. | Abhishek / Harish |
| **T-TM-02** | Tampering | PostgreSQL / ORM | Critical | Migration test: verify database trigger raises exception on `UPDATE AuditEvent`. | Vishal / Ajendra |
| **T-TM-03** | Tampering | AI Matching | Critical | Algorithm test: candidate with failing mandatory criterion must be `Excluded`. | Alok / Harish |
| **T-RP-01** | Repudiation | Audit Service | Medium | API test: verify audit event emission on all state transitions. | Abhishek / Harish |
| **T-ID-01** | Info Disclosure | Git / CI | Critical | Automated CI Gitleaks scan on every commit and PR. | Ajendra |
| **T-ID-02** | Info Disclosure | DRF Exceptions | Low | Negative test: 500 error returns standard JSON shape without traceback. | Abhishek / Harish |
| **T-ID-03** | Info Disclosure | AI Engine | Critical | Dependency check & code audit: verify no external HTTP calls or LLM libraries. | Alok / Ajendra |
| **T-EP-01** | Privilege Escalation | DRF Permissions | High | Role boundary negative tests for all 3 internal roles against all endpoints. | Abhishek / Ajendra |
