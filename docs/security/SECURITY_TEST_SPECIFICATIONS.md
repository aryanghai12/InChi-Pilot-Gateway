# Security & Negative Test Specifications — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Co-Author & Automation Lead** | Harish Pal (QA and Test Automation Engineer) |
| **Enforcement & Implementation** | Abhishek Kumar (Backend), Vishal Chauhan (Database), Alok Tiwari (AI) |
| **Governing Baseline** | [`InChi_China_Readiness_Implementation_Baseline_v2.2.pdf`](../source-documents/InChi_China_Readiness_Implementation_Baseline_v2.2.pdf) §12, §14.3; [`../../AGENTS.md`](../../AGENTS.md) §C2, §C8 |
| **Status** | Approved Baseline Specification (Updated Post-Week 4 Audit) |

---

## 1. Objectives & Testing Principles

As mandated by **AGENTS.md §B rule 10 & §C2**:
> *"The backend is the single authority. Technical owners implement fixes; Security defines negative test cases and verifies remediation."*

This specification aligns the automated negative test suite with:
1. **Baseline v2.2 §14.3 Threat-Focused Security Tests** (`SEC-01` through `SEC-06`).
2. **Baseline v2.2 §12 Acceptance Criteria** (`AC-06`, `AC-19`, `AC-22`, `AC-23`).
3. **Week 4 Security Audit Defect Verifications** (`AUD-01` privilege escalation & `AUD-15` plaintext password storage).

---

## 2. Test Suite Matrix & Traceability

| Test ID | Baseline Ref | Category | Target Component | Threat ID | Expected Result | Lead Executor |
|---|---|---|---|---|---|---|
| **SEC-TEST-01** | §14.1 | Authentication | `POST /api/v1/auth/login/` | T-SP-01 | Rejection without CSRF cookie (`403 csrf_failed`) | Abhishek / Ajendra |
| **SEC-TEST-02** | §14.1 | Authentication | `POST /api/v1/auth/login/` | T-SP-01 | Session key rotates upon successful authentication (TD-08) | Abhishek / Ajendra |
| **SEC-TEST-03** | §14.1, SEC-01 | Authentication | `GET /api/v1/auth/me/` | T-SP-01 | Unauthenticated access yields `401 not_authenticated` | Abhishek / Ajendra |
| **SEC-TEST-04** | §4.2, SEC-01 | RBAC | User Management API | T-EP-01 | Commercial Analyst gets `403 permission_denied` on user admin | Abhishek / Ajendra |
| **SEC-TEST-05** | §4, §4.2 | RBAC | `POST /api/v1/suppliers/` | T-EP-02 | Platform Admin gets `403 permission_denied` on commercial edit | Abhishek / Ajendra |
| **SEC-TEST-06** | AC-06, §8.1 | Workflow RBAC | `POST /api/v1/assessments/{id}/complete-review/` | T-TM-04 | Reviewer blocked from approving own assessment (`submitted_by != reviewer`) | Abhishek / Ajendra |
| **SEC-TEST-07** | §4, §14.1 | Admin Safety | `POST /api/v1/auth/users/{id}/deactivate/` | T-EP-02 | Platform Admin cannot deactivate own account (`403 permission_denied`) | Abhishek / Ajendra |
| **SEC-TEST-08** | §14.1 | Session Hygiene | `POST /api/v1/auth/logout/` | T-SP-01 | Session terminated and cookies invalidated | Abhishek / Ajendra |
| **SEC-TEST-09** | SEC-06, AC-23 | Audit Integrity | `AuditEvent` PostgreSQL table | T-TM-02 | SQL `UPDATE` or `DELETE` aborts via database trigger (TD-03) | Vishal / Ajendra |
| **SEC-TEST-10** | SEC-01, AC-22 | Authentication | Core Write APIs (`/suppliers`, `/assessments`, `/requirements`) | T-EP-01 | Unauthenticated write attempts rejected with `401 not_authenticated` | Abhishek / Ajendra |
| **SEC-TEST-11** | §4.2, SEC-01 | Workflow RBAC | `POST /api/v1/assessments/{id}/complete-review/` | T-EP-01 | Commercial Analyst forbidden from completing readiness reviews (`403`) | Abhishek / Ajendra |
| **SEC-TEST-12** | §4, §4.2 | RBAC | `POST /api/v1/requirements/` | T-EP-02 | Platform Admin forbidden from creating demand records (`403`) | Abhishek / Ajendra |
| **SEC-TEST-13** | SEC-05 | Info Disclosure | User Serializers & Responses | T-ID-02 | Zero password hashes or verification tokens exposed in user payload | Abhishek / Ajendra |
| **SEC-TEST-14** | §14.1, AUD-15 | Password Security | User Model & Django Admin | T-ID-04 | Password hashing enforced via PBKDF2 (`pbkdf2_sha256$`) | Abhishek / Ajendra |
| **SEC-TEST-15** | §14.1, AUD-01 | Elevation Threat | `POST /api/v1/auth/register/` | T-EP-03 | Proves AUD-01 defect; asserts unauthenticated privilege assignment is blocked | Abhishek / Ajendra |
| **SEC-TEST-16** | SEC-05, T-ID-01 | Secret Leakage | Repository Root & CI | T-ID-01 | Automated Gitleaks scan blocks plaintext secret commits | Ajendra |

---

## 3. Detailed Specifications for Core Security Invariants

### 3.1 Two-Person Rule on Assessment Review (SEC-TEST-06 / AC-06)
* **Threat**: A rogue reviewer creates a fraudulent China-readiness assessment for a supplier and approves it without independent verification.
* **Preconditions**: User R possesses `role="reviewer"`.
* **Execution**:
  1. User R creates or submits assessment record `A` for Supplier `S` (`A.submitted_by = User R`).
  2. User R sends `POST /api/v1/assessments/{A.id}/complete-review/` with outcome `READY_FOR_MATCHING`.
* **Pass Criteria**:
  * HTTP status: `403 Forbidden`.
  * Response body: `{"code": "permission_denied", "message": "Reviewer cannot approve an assessment they submitted."}`.
  * Assessment workflow state remains unchanged in database.

### 3.2 Audit Log Database Immutability (SEC-TEST-09 / SEC-06 / TD-03)
* **Threat**: A compromised administrative account attempts to erase records of unauthorized actions.
* **Execution**:
  ```python
  event = AuditEvent.objects.create(actor=user, action="test", ...)
  event.action = "tampered"
  event.save()  # Attempt update
  event.delete() # Attempt delete
  ```
* **Pass Criteria**:
  * Both operations raise `django.core.exceptions.PermissionDenied` or PostgreSQL aborts with SQL error.
  * Historical record remains intact.

### 3.3 Anonymous Registration Privilege Escalation (SEC-TEST-15 / AUD-01)
* **Threat**: Anonymous visitor calls `POST /api/v1/auth/register/` with `role: platform_admin` to hijack platform administration.
* **Execution**:
  * Send `POST /api/v1/auth/register/` with synthetic test payload containing `"role": "platform_admin"`.
* **Target Security Policy**:
  * Endpoint must be removed or restricted strictly to authenticated administrators.
  * Unauthenticated callers must receive `401 Unauthorized` or `403 Forbidden`.

---

## 4. Automated Pytest Verification Suite

The authoritative implementation of these test specifications is located in:
[`backend/apps/accounts/tests/test_security_posture.py`](../../backend/apps/accounts/tests/test_security_posture.py)

**Execution Command**:
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest apps\accounts\tests\test_security_posture.py --ds=config.settings -v
```

**Observed Execution Evidence (23 Nov 2026)**:
```
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_01_csrf_cookie_endpoint_bootstraps_token PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_02_unauthenticated_requests_return_401_not_authenticated PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_03_login_establishes_session_and_rotates_credentials PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_04_login_invalid_credentials_returns_400 PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_05_analyst_forbidden_from_admin_user_management PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_06_admin_isolated_from_commercial_operations PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_07_platform_admin_cannot_deactivate_self PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_08_logout_terminates_session PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_09_audit_event_cannot_be_updated_or_deleted PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_10_unauthenticated_api_endpoints_return_401 PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_11_reviewer_cannot_approve_own_submitted_assessment PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_12_analyst_forbidden_from_completing_readiness_review PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_13_platform_admin_isolated_from_buyer_requirements PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_14_user_serializer_does_not_leak_password_or_tokens PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_15_password_hashing_enforced_on_user_creation PASSED
apps/accounts/tests/test_security_posture.py::SecurityPostureTests::test_sec_16_audit_01_self_registration_reproduction_proof PASSED
====================== 16 passed, 13 warnings in 41.24s =======================
```
