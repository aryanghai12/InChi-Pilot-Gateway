# Security Remediation Register — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author & Maintainer** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Active Ledger |
| **Severity Taxonomy** | Build Manual §9; [`../MVP_FEATURES.md`](../MVP_FEATURES.md) §15 |
| **Review Cadence** | Weekly at Friday Sprint Review |

---

## 1. Severity Definitions & Action Rules

Per **Build Manual §9** and **MVP_FEATURES §15**:

* **Critical**: Exposes unauthorized data or actions, risks data loss, breaks the priority journey, or makes the pilot unsafe to demonstrate. **Must be resolved before final acceptance. At Gate 4, no critical unresolved access-control defect may remain.**
* **High**: Blocks a major MVP function or produces materially incorrect decisions. **Must be closed or have an approved, documented workaround before final review.**
* **Medium / Low**: Does not block the priority journey but must remain visible in the defect or limitation register with a recommended next action.

---

## 2. Active Vulnerability & Remediation Ledger

| Finding ID | Severity | Component | Owner | Finding Summary | Status | Retest / Verification Evidence |
|---|---|---|---|---|---|---|
| **SEC-01** | High | Repository | Ajendra | Lack of root `.gitignore` risking credential or local environment leaks. | **Resolved** | Root `.gitignore` created excluding all `.env*` except `.env.example`. |
| **SEC-02** | High | CI / Automation | Ajendra | Absence of automated dependency vulnerability and secret scanning in CI. | **Resolved** | Added `.github/workflows/security.yml` (Gitleaks, pip-audit, npm audit) & `.github/dependabot.yml`. |
| **SEC-03** | High | Backend Auth | Abhishek | Anonymous DRF login endpoint bypasses CSRF validation unless explicitly decorated. | **In Progress** | Target for Week 2: Apply `@method_decorator(csrf_protect)` on `LoginView` (TD-05). |
| **SEC-04** | High | Backend RBAC | Abhishek | Unapproved permissions matrix must be isolated to prevent widespread code changes. | **In Progress** | Centralize in `backend/apps/accounts/policy.py` tagged `UNAPPROVED` (TD-08). |
| **SEC-05** | Critical | Database / Audit | Vishal | Audit logs could be modified or deleted without a database-level constraint. | **Pending** | Vishal to add PostgreSQL trigger rejecting `UPDATE` and `DELETE` on `AuditEvent` (TD-03). |
| **SEC-06** | Critical | AI Matching | Alok | Risk of semantic similarity overriding mandatory eligibility failures. | **Verified Design** | Two-component matching architecture enforces hard filters before similarity (M6-AC1). |
| **SEC-07** | Medium | Backend Auth | Abhishek | Lack of login attempt throttling on `/api/v1/auth/login/` (TD-04). | **In Review** | Ajendra recommended DRF scoped throttle for staging; review with Abhishek in Week 2. |
| **SEC-08** | High | Backend Dependencies | Abhishek / Ajendra | Known DoS vulnerabilities in DRF 3.15.2 (CVE-2026-114138, PYSEC-2026-3827). | **Resolved** | Upgraded `djangorestframework>=3.18.2,<4.0.0` in `backend/requirements.txt`. |
| **SEC-09** | Medium | Frontend Dev Tooling | Priyanka / Ajendra | Prototype pollution in offline test runner devDependency tinypool (GHSA-85c8-ppgw-ccpr). | **Mitigated** | Scoped production CI gate strictly to runtime dependencies (`--omit=dev`); tracked for Phase 2 Vitest 4 upgrade. |

---

## 3. Detailed Finding Records

### Finding SEC-01: Absence of Root `.gitignore` Secrets Baseline
* **Severity**: High
* **Affected Component**: Repository Root
* **Discovered**: Week 1 Baseline Review
* **Reproduction**: Prior to remediation, only `frontend/.gitignore` existed, leaving root `.env` files vulnerable to accidental commits.
* **Remediation**: Implemented root `.gitignore` strictly excluding `.env`, `.env.*`, and virtualenvs, while preserving `!.env.example`.
* **Resolution**: Merged in `security/devsecops-baseline-and-security-pack`.

---

### Finding SEC-02: Absence of Automated CI Security Tooling
* **Severity**: High
* **Affected Component**: `.github/workflows/`
* **Discovered**: Week 1 Baseline Review
* **Reproduction**: CI had no automated secret or dependency vulnerability checking.
* **Remediation**: Implemented multi-job workflow `.github/workflows/security.yml` incorporating `gitleaks`, `pip-audit`, and `npm audit --audit-level=high`, plus `.github/dependabot.yml`.
* **Resolution**: Verified workflow syntax; active in CI pipeline.

---

### Finding SEC-03: Anonymous Login Endpoint CSRF Exemption
* **Severity**: High
* **Affected Component**: `backend/apps/accounts/views.py`
* **Lead Owner**: Abhishek Kumar (Backend)
* **Description**: DRF's `SessionAuthentication` does not enforce CSRF checks on unauthenticated users. An attacker could perform Login CSRF.
* **Remediation Guidance**: Abhishek must decorate `LoginView.post` with `@method_decorator(csrf_protect)` and define `authentication_classes = []`. Bootstrap token via `GET /api/v1/auth/csrf/` decorated with `@ensure_csrf_cookie`.
* **Status**: In progress (tracked for Week 2 Gate 1).

---

### Finding SEC-08: Inefficient Algorithmic Complexity / DoS in DRF (CVE-2026-114138)
* **Severity**: High
* **Affected Component**: `backend/requirements.txt` (`djangorestframework`)
* **Discovered**: CI Pipeline execution via `pip-audit`
* **Vulnerability ID**: CVE-2026-114138 / PYSEC-2026-3827
* **Description**: DRF < 3.18.2 suffers from quadratic parsing complexity when processing crafted HTTP `Accept` headers with excessive semicolons, leading to worker CPU exhaustion and DoS.
* **Remediation**: Upgraded `djangorestframework` constraint in `backend/requirements.txt` from `>=3.15.0,<3.16.0` to `>=3.18.2,<4.0.0`.
* **Resolution**: Pushed in PR #21; verified against pip-audit database.

