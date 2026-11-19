# Security & Negative Test Specifications — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Co-Author & Automation Lead** | Harish Pal (QA and Test Automation Engineer) |
| **Enforcement & Implementation** | Abhishek Kumar (Backend), Vishal Chauhan (Database), Alok Tiwari (AI) |
| **Authority** | [`../../AGENTS.md`](../../AGENTS.md) §C2, §C8; [`AUTH_THREAT_REVIEW.md`](AUTH_THREAT_REVIEW.md); [`ACCESS_CONTROL_MATRIX.md`](ACCESS_CONTROL_MATRIX.md) |
| **Status** | Approved Baseline Specification (v0.1 Pilot) |

---

## 1. Objectives & Testing Principles

As mandated by **AGENTS.md §B rule 10 & §C2**:
> *"The backend is the single authority. Technical owners implement fixes; Security defines negative test cases and verifies remediation."*

This document defines the automated negative security test cases covering:
1. Authentication & Session Hygiene (CSRF, Session Rotation, 401 Semantics)
2. Role-Based Access Control (RBAC) & Principle of Least Privilege
3. Insecure Direct Object References (IDOR) & State Transition Integrity
4. Database Audit Immutability (PostgreSQL Trigger Enforcement)
5. AI Matching Hard Gates & Information Leakage Prevention
6. Error Sanitization & Information Disclosure Suppression

---

## 2. Test Suite Matrix

| Test ID | Category | Target Component | Threat ID | Expected Result | Lead Executor |
|---|---|---|---|---|---|
| **SEC-TEST-01** | Authentication | `POST /api/v1/auth/login/` | T-SP-01 | Rejection without CSRF cookie (`403 csrf_failed`) | Harish / Abhishek |
| **SEC-TEST-02** | Authentication | `POST /api/v1/auth/login/` | T-SP-01 | Session key rotates upon successful authentication | Harish / Abhishek |
| **SEC-TEST-03** | Authentication | Protected APIs | T-SP-01 | Unauthenticated access yields `401 not_authenticated` | Harish / Abhishek |
| **SEC-TEST-04** | RBAC | Reviewer Endpoints | T-EP-01 | Commercial Analyst gets `403 permission_denied`; session intact | Harish / Abhishek |
| **SEC-TEST-05** | RBAC | Commercial Endpoints | T-EP-02 | Platform Admin gets `403 permission_denied` on commercial edit | Harish / Abhishek |
| **SEC-TEST-06** | RBAC / Conflict | Assessment Review | T-EP-01 | Self-review denied (`submitted_by != reviewed_by`) | Harish / Abhishek |
| **SEC-TEST-07** | IDOR | `PATCH /api/v1/suppliers/{id}/` | T-TM-01 | User cannot modify supplier record in finalized state | Harish / Abhishek |
| **SEC-TEST-08** | Audit Integrity | `AuditEvent` PostgreSQL table | T-TM-02 | SQL `UPDATE` or `DELETE` aborts via database trigger (TD-03) | Harish / Vishal |
| **SEC-TEST-09** | AI Hard Gate | `POST /api/v1/matching/run/` | T-TM-03 | Candidate failing mandatory criteria is excluded regardless of similarity | Harish / Alok |
| **SEC-TEST-10** | AI Fail-Safe | `POST /api/v1/matching/run/` | T-TM-03 | Engine failure explicitly fails run; zero silent fallback (M6-AC5) | Harish / Alok |
| **SEC-TEST-11** | Info Disclosure | Unhandled Server Exception | T-ID-02 | `500 Internal Server Error` returns sanitized JSON without traceback | Harish / Abhishek |
| **SEC-TEST-12** | Secret Leakage | Git Repository & CI | T-ID-01 | Zero plaintext secrets or unapproved `.env` files committed | Ajendra |

---

## 3. Detailed Test Case Specifications

### 3.1 Authentication & Session Security

#### SEC-TEST-01: CSRF Enforcement on Anonymous Login
* **Description**: Verify that the login endpoint rejects credential submission when CSRF token is omitted.
* **Preconditions**: Client has no active session.
* **Execution**:
  1. `POST /api/v1/auth/login/` with valid JSON payload `{"email": "analyst@bncs.local", "password": "ValidPassword123"}`.
  2. Ensure header `X-CSRFToken` is intentionally omitted.
* **Pass Criteria**:
  * HTTP status: `403 Forbidden`.
  * Response body: `{"code": "csrf_failed", "message": "CSRF verification failed."}`.
  * No session cookie (`sessionid`) issued.

#### SEC-TEST-02: Cryptographic Session Key Rotation on Login
* **Description**: Verify that pre-login session cookies cannot be hijacked (Session Fixation defense).
* **Execution**:
  1. `GET /api/v1/auth/csrf/` -> record initial session / CSRF cookies.
  2. `POST /api/v1/auth/login/` with valid credentials and CSRF header.
* **Pass Criteria**:
  * Response status: `200 OK`.
  * `Set-Cookie` header returns a new `sessionid` distinct from the initial pre-auth cookie value.
  * Cookie attributes contain `HttpOnly`, `SameSite=Lax`.

#### SEC-TEST-03: 401 Not Authenticated vs 403 Permission Denied Semantics
* **Description**: Verify strict adherence to TD-06 semantics.
* **Execution**:
  1. Call `GET /api/v1/suppliers/` with no cookies -> expect `401 {"code": "not_authenticated"}`.
  2. Authenticate as `commercial_analyst`.
  3. Call `POST /api/v1/assessments/1/review/` -> expect `403 {"code": "permission_denied"}`.
* **Pass Criteria**:
  * Response 1 returns `401` causing frontend to redirect to login.
  * Response 2 returns `403` and the user's active session remains valid without logout.

---

### 3.2 Role-Based Access Control (RBAC) & Object Boundaries

#### SEC-TEST-04: Analyst Prohibited from Review Decisions
* **Description**: Ensure commercial analysts cannot record match dispositions or approve readiness assessments.
* **Execution**:
  * Authenticate as user with `role="commercial_analyst"`.
  * Send `POST /api/v1/matches/{id}/disposition/` with `{"disposition": "Accepted", "reason": "Test"}`.
* **Pass Criteria**:
  * HTTP status: `403 Forbidden`.
  * Error code: `permission_denied`.
  * Database state of match disposition remains untouched.

#### SEC-TEST-05: Platform Administrator Commercial Isolation
* **Description**: Verify least-privilege isolation preventing platform administrators from tampering with commercial data.
* **Execution**:
  * Authenticate as user with `role="platform_admin"`.
  * Send `POST /api/v1/suppliers/` with valid supplier creation payload.
* **Pass Criteria**:
  * HTTP status: `403 Forbidden`.
  * Administrator accounts restricted strictly to user provisioning.

#### SEC-TEST-06: Two-Person Rule on Assessment Review
* **Description**: Ensure an author/submitter cannot approve their own readiness assessment.
* **Execution**:
  * User A (Reviewer) submits an assessment for Supplier X.
  * User A attempts to call `POST /api/v1/assessments/{id}/approve/`.
* **Pass Criteria**:
  * HTTP status: `403 Forbidden` with message `"Reviewers cannot approve assessments they submitted."`.

---

### 3.3 Data Integrity & Audit Immutability

#### SEC-TEST-08: Database Trigger Rejects Audit Tampering (TD-03)
* **Description**: Verify that direct SQL `UPDATE` or `DELETE` operations on `AuditEvent` table are aborted at the database engine level.
* **Execution**:
  ```sql
  -- Direct database trigger test
  UPDATE audit_auditevent SET action = 'tampered' WHERE id = 1;
  DELETE FROM audit_auditevent WHERE id = 1;
  ```
* **Pass Criteria**:
  * PostgreSQL aborts with `ERROR: UPDATE and DELETE operations are prohibited on table audit_auditevent`.

---

### 3.4 AI Matching Engine Safeguards

#### SEC-TEST-09: Mandatory Eligibility Filter Override Prevention
* **Description**: Prove that candidate failing a mandatory criterion (e.g., MOQ mismatch or missing China certification) is completely excluded even when semantic similarity score is 1.0 (100%).
* **Execution**:
  * Submit MatchRun where Supplier S has perfect capability description match to Requirement R, but fails mandatory MOQ requirement.
* **Pass Criteria**:
  * Supplier S is classified as `Excluded` in Stage 2.
  * Supplier S receives zero hybrid score and does not appear in ranked recommendations.

#### SEC-TEST-10: Explicit Failure on Semantic Engine Failure
* **Description**: Verify that if FastAPI AI matching engine returns 500 or timeout, the match run transitions to `Failed` (no silent rules-only fallback per M6-AC5).
* **Pass Criteria**:
  * `MatchRun.status` is saved as `Failed`.
  * Error message recorded in audit log.
  * UI displays explicit AI processing failure.

---

## 4. Pytest Test Reference Implementation

This reference test file is prepared for Abhishek and Harish to place in `backend/apps/accounts/tests/test_security_posture.py`:

```python
"""
Automated Security & Access-Control Verification Test Suite
Owned by: Harish Pal (QA) & Ajendra Nath Tripathi (DevSecOps)
AGENTS.md §C2, §C8; ARCHITECTURE.md §5, §8
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestAuthenticationSecurity:
    def test_login_requires_csrf_cookie(self, client):
        """SEC-TEST-01: Anonymous POST to login without CSRF must return 403."""
        login_url = reverse("auth-login")
        response = client.post(
            login_url,
            {"email": "test@bncs.local", "password": "SomePassword123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("code") == "csrf_failed"

    def test_session_rotates_on_successful_login(self, client, user_factory):
        """SEC-TEST-02: Session ID must rotate after authentication."""
        user = user_factory(email="analyst@bncs.local", role="commercial_analyst")
        csrf_url = reverse("auth-csrf")
        login_url = reverse("auth-login")

        # 1. Obtain initial CSRF cookie & pre-session
        init_res = client.get(csrf_url)
        initial_session = client.session.session_key

        # 2. Authenticate
        client.post(
            login_url,
            {"email": "analyst@bncs.local", "password": "DefaultPassword123!"},
            format="json",
        )
        post_login_session = client.session.session_key

        assert post_login_session is not None
        assert post_login_session != initial_session

@pytest.mark.django_db
class TestRoleBasedAccessControl:
    def test_analyst_cannot_record_match_disposition(self, auth_client_factory, match_result):
        """SEC-TEST-04: Commercial Analyst forbidden from recording Reviewer disposition."""
        client = auth_client_factory(role="commercial_analyst")
        url = reverse("match-disposition", kwargs={"pk": match_result.id})
        
        response = client.post(
            url,
            {"outcome": "Accepted", "reason": "Analyst attempted approval"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("code") == "permission_denied"

    def test_admin_cannot_create_commercial_records(self, auth_client_factory):
        """SEC-TEST-05: Platform Admin isolated from commercial transactions."""
        client = auth_client_factory(role="platform_admin")
        url = reverse("supplier-list")

        response = client.post(
            url,
            {"name": "Synthetic Supplier Pte Ltd", "country": "Singapore"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("code") == "permission_denied"
```

---

## 5. DevSecOps Sign-off & Continuous Automation

Every pull request impacting authentication, session management, or role definitions must successfully execute this test suite in GitHub Actions prior to merging to `main`.

