# Security Remediation Register — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author & Maintainer** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Active Ledger (Updated Post-Week 4 Audit, 21 Nov 2026) |
| **Severity Taxonomy** | Build Manual §9; [`../MVP_FEATURES.md`](../MVP_FEATURES.md) §15; [`InChi_China_Readiness_Implementation_Baseline_v2.2.pdf`](../source-documents/InChi_China_Readiness_Implementation_Baseline_v2.2.pdf) §15.3 |
| **Review Cadence** | Weekly at Friday Sprint Review |

---

## 1. Severity Definitions & Action Rules

Per **Build Manual §9**, **MVP_FEATURES §15**, and **Baseline v2.2 §15.3**:

* **Critical**: Exposes unauthorized data or actions, risks data loss, breaks the priority journey, or makes the pilot unsafe to demonstrate. **Must be resolved before final acceptance. At Gate 4, no critical unresolved access-control defect may remain.**
* **High**: Blocks a major MVP function or produces materially incorrect decisions. **Must be closed or have an approved, documented workaround before final review.**
* **Medium / Low**: Does not block the priority journey but must remain visible in the defect or limitation register with a recommended next action.

---

## 2. Active Vulnerability & Remediation Ledger

| Finding ID | Audit Ref | Severity | Component | Owner | Finding Summary | Status | Retest / Verification Evidence |
|---|---|---|---|---|---|---|---|
| **SEC-01** | — | High | Repository Root | Ajendra | Lack of root `.gitignore` risking credential or local environment leaks. | **Resolved** | Root `.gitignore` created excluding `.env*` except `.env.example`. |
| **SEC-02** | — | High | CI / Automation | Ajendra | Absence of automated dependency vulnerability and secret scanning in CI. | **Resolved** | Added `.github/workflows/security.yml` (Gitleaks, pip-audit, npm audit) & `.github/dependabot.yml`. |
| **SEC-03** | — | High | Backend Auth | Abhishek | Anonymous DRF login endpoint bypasses CSRF validation unless explicitly decorated. | **Resolved** | Verified `@method_decorator(csrf_protect)` on `LoginView` and `@ensure_csrf_cookie` on `CsrfCookieView` (TD-05). |
| **SEC-04** | — | High | Backend RBAC | Abhishek | Unapproved permissions matrix must be isolated to prevent widespread code changes. | **In Progress** | Centralized in `backend/apps/accounts/policy.py`. Transitioning to 5-role baseline under D-22. |
| **SEC-05** | — | Critical | Database / Audit | Vishal | Audit logs could be modified or deleted without a database-level constraint. | **Resolved** | Implemented PostgreSQL trigger blocking `UPDATE` and `DELETE` on `AuditEvent` (TD-03). Verified via pytest. |
| **SEC-06** | — | Critical | AI Matching | Alok | Risk of semantic similarity overriding mandatory eligibility failures. | **Resolved Design** | Baseline v2.2 §9 establishes deterministic rules first. D-21 clarifies rules-only MVP scope. |
| **SEC-07** | — | Medium | Backend Auth | Abhishek / Ajendra | Lack of login attempt throttling on `/api/v1/auth/login/` (TD-04). | **Resolved** | Implemented DRF `ScopedRateThrottle` (`5/minute`), configured `THROTTLE_RATES` in settings, and verified via `test_sec_17` (TD-04). |
| **SEC-08** | — | High | Backend Dependencies | Abhishek / Ajendra | Known DoS vulnerabilities in DRF 3.15.2 (CVE-2026-114138, PYSEC-2026-3827). | **Resolved** | Upgraded `djangorestframework>=3.18.2,<4.0.0` in `backend/requirements.txt`. |
| **SEC-09** | — | Medium | Frontend Dev Tooling | Priyanka / Ajendra | Prototype pollution in offline test runner devDependency tinypool (GHSA-85c8-ppgw-ccpr). | **Mitigated** | Scoped production CI gate strictly to runtime dependencies (`--omit=dev`). |
| **SEC-10** | **AUD-01** | **Critical** | Backend Auth / M1 | Abhishek | Anonymous self-registration with arbitrary role assignment allows unauthenticated attacker to become platform_admin. | **Open / Escalated** | Reproduced on audit stack (check 13). Blocks Gate 4 acceptance. Negative test authored in `test_security_posture.py`. |
| **SEC-11** | **AUD-15** | **High** | Backend Admin / M1 | Abhishek | `UserAdmin` in Django admin stores plaintext passwords, breaking authentication and password hashing. | **Open** | Reproduced on test database: user created via admin has unhashed password; `check_password` false. |
| **SEC-12** | **AUD-03** | **High** | Frontend UI / M2 | Priyanka | Documents page displays "Verified" badges and "Verified Compliance" count, violating AC-09 and Baseline v2.2 §10.1. | **Open** | Identified in `frontend/src/app/(workspace)/documents/page.tsx` (lines 19, 56, 101, 151). |
| **SEC-13** | **AUD-05** | **High** | Quality / CI | Abhishek / Harish | Readiness (M4) and Demand (M5) have 0 backend tests; CI does not run matching or lint checks. | **Open** | Audit check 4 confirmed 0 tests for M4 and M5. Test specifications drafted in `SECURITY_TEST_SPECIFICATIONS.md`. |
| **SEC-14** | **AUD-07** | **Medium** | AI Matching Runtime | Alok | Matching Docker image missing sentence-transformers runtime dependency; model unapproved under D-11. | **Open** | Audit check 11 confirmed `ModuleNotFoundError` on container import. |

---

## 3. Detailed Finding Records (New & Active Findings)

### Finding SEC-10 / AUD-01: Anonymous Self-Registration with Arbitrary Role Assignment
* **Severity**: **Critical** (Exposes unauthorized actions, complete privilege escalation)
* **Affected Component**: `backend/apps/accounts/views.py` (`RegisterView`, `VerifyAccountView`), `serializers.py` (`RegisterSerializer`)
* **Discovered**: Week 4 Audit (21 Nov 2026, Check 13)
* **Lead Owner**: Abhishek Kumar (Backend)
* **Reviewer**: Ajendra Nath Tripathi (Cybersecurity & DevSecOps)
* **Reproduction**:
  1. Call `POST /api/v1/auth/register/` with payload:
     ```json
     {"email": "attacker@evil.local", "password": "EvilPassword123!", "role": "platform_admin"}
     ```
  2. Endpoint returns HTTP 201 with `verification_token` in response body.
  3. Call `POST /api/v1/auth/verify/` with token from response: returns 200 OK (`is_verified = True`).
  4. Call `POST /api/v1/auth/login/`: returns 200 OK. Attacker now possesses full `platform_admin` session and can access `/api/v1/auth/users/`.
* **Violation**: Breaks Decision D-12 ("no self-registration"), Baseline v2.2 §14.1 ("Use internal test accounts only... least privilege"), and MVP_FEATURES M1. Blocks Gate 4.
* **Remediation Guidance**:
  - Remove `RegisterView` and `VerifyAccountView` from public URL routing or restrict them strictly to `permission_classes = [IsAuthenticated, IsPlatformAdmin]`.
  - Ensure all internal user accounts are created via Django Admin or CLI `create_platform_admin`.
  - Author automated negative test in `test_security_posture.py` to prevent regression.

---

### Finding SEC-11 / AUD-15: Plaintext Password Storage in Django Admin User Creation
* **Severity**: **High** (Violates credential protection baseline and prevents admin-created user logins)
* **Affected Component**: `backend/apps/accounts/admin.py` (`UserAdmin`)
* **Discovered**: Week 4 Audit (21 Nov 2026, Check 15)
* **Lead Owner**: Abhishek Kumar (Backend)
* **Reviewer**: Ajendra Nath Tripathi (Cybersecurity & DevSecOps)
* **Reproduction**:
  1. Authenticate to Django admin as platform admin.
  2. Navigate to *Add User* and input email and password.
  3. Save user. Inspect database record: password field contains raw plaintext, not `pbkdf2_sha256$...`.
  4. Attempt to log in with new user credentials via `/api/v1/auth/login/`: fails because `check_password` expects cryptographic hash.
* **Violation**: Breaks Baseline v2.2 §14.1 ("Do not store passwords in plain text. Use approved authentication method and secure password handling").
* **Remediation Guidance**:
  - Update `backend/apps/accounts/admin.py` to inherit from `django.contrib.auth.admin.UserAdmin` or override `save_model(request, obj, form, change)`:
    ```python
    def save_model(self, request, obj, form, change):
        if not change or "password" in form.changed_data:
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)
    ```
  - Implement custom `UserCreationForm` to mask password fields during user creation.

---

### Finding SEC-12 / AUD-03: Prohibited "Verified" Badges on Documents UI
* **Severity**: **High** (False compliance claims in UI, direct acceptance criteria failure)
* **Affected Component**: `frontend/src/app/(workspace)/documents/page.tsx` (lines 19, 56, 101, 151)
* **Discovered**: Week 4 Audit (21 Nov 2026)
* **Lead Owner**: Priyanka Singh (Frontend)
* **Reviewer**: Adrika T Kumar (Product), Ajendra Nath Tripathi (Security)
* **Reproduction**: Open `/documents` in browser. Observe "Verified" status pill and "Verified Compliance" aggregate count displayed for suppliers with completed documentation.
* **Violation**: Direct violation of Acceptance Criterion **AC-09** ("Given an existing third-party report, when recorded, then the interface does not label the supplier or factory Verified") and Baseline v2.2 §3.1, §7.1, §10.1 ("Never use green Verified or Approved badges for suppliers, products, factories or documents").
* **Remediation Guidance**: Replace "Verified" label with approved neutral states from Baseline v2.2 §7: `Document Received Unverified`, `Official Source Checked`, or `Self-Declared`. Remove "Verified Compliance" metric.

---

### Finding SEC-13 / AUD-05: Absence of Automated Backend Tests for M4 & M5 in CI
* **Severity**: **High** (Risk of untested authorization flaws and regressions in core workflows)
* **Affected Component**: `backend/apps/readiness/`, `backend/apps/demand/`, `.github/workflows/ci.yml`
* **Discovered**: Week 4 Audit (21 Nov 2026, Check 4)
* **Lead Owner**: Abhishek Kumar (Backend), Harish Pal (QA)
* **Reviewer**: Ajendra Nath Tripathi (DevSecOps)
* **Reproduction**: Run `python -m pytest apps/readiness apps/demand`: returns 0 tests collected.
* **Violation**: Breaks ARCHITECTURE.md §8 and AGENTS.md §B rule 6 ("Tests and documentation come with the change").
* **Remediation Guidance**: Abhishek and Harish must add unit and permission tests for readiness submission gates, reviewer completion, and buyer requirement validation. Ajendra provides negative security test specifications.

---

### Finding SEC-14 / AUD-07: Matching Runtime Missing Library and Unapproved Model Default
* **Severity**: **Medium** (Runtime failure on semantic execution; governance violation)
* **Affected Component**: `backend/Dockerfile` (matching target), `.env.example`
* **Discovered**: Week 4 Audit (21 Nov 2026, Checks 10 & 11)
* **Lead Owner**: Alok Tiwari (AI)
* **Reviewer**: Ajendra Nath Tripathi (Security), Aryan Ghai (Coordination)
* **Reproduction**: Execute `python -c "import sentence_transformers"` inside the `matching` container: raises `ModuleNotFoundError`.
* **Violation**: Violates AGENTS.md §A rule ("Never select an embedding model or an LLM in code, configuration defaults, examples or documentation. Both stay TBD until D-11 and D-20 are recorded").
* **Remediation Guidance**: Revert committed model default in `.env.example` to placeholder. Install required dependencies in Dockerfile only after D-11 is formally decided.
