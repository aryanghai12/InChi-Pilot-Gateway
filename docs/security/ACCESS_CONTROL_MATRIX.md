# Role-Based Access Control (RBAC) & Object-Level Permission Matrix

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Governing Authority** | [`InChi_China_Readiness_Implementation_Baseline_v2.2.pdf`](../source-documents/InChi_China_Readiness_Implementation_Baseline_v2.2.pdf) §4, §4.2; [`../MVP_FEATURES.md`](../MVP_FEATURES.md) §5 |
| **Status** | Governing Baseline: **Baseline v2.2 Five-Role Standard** / Interim Code: **3 Roles (Pending Decision D-22)** |
| **Enforcement Point** | `backend/apps/accounts/policy.py` (Abhishek Kumar) |
| **Reviewers** | Abhishek Kumar (Backend), Aryan Ghai (Coordination), Harish Pal (QA) |

---

## 1. Principles of Access Control

The InChi Pilot Gateway enforces access control strictly according to these foundational engineering rules:
1. **The Backend is the Single Authority**: Client-side UI route guarding only provides usability guidance. The Django REST Framework backend enforces 100% of authentication, role verification, and object-level scoping (AGENTS.md §B rule 10).
2. **Deny-by-Default Architecture**: Any action or resource not explicitly permitted to an authenticated role is denied with an HTTP 403 `permission_denied` response.
3. **No Anonymous Access / No Self-Registration**: In accordance with Baseline v2.2 §14.1 and D-12, all application functionality requires an authenticated internal session. **Public registration is prohibited** (see critical vulnerability AUD-01).
4. **Least Privilege**: Users are granted access only to data and operations strictly required for their role.
5. **Separation of Assessment Submission and Review**: A user who submitted an assessment cannot review or approve that same assessment (`submitted_by != reviewed_by`).

---

## 2. Governing Baseline v2.2 Roles (§4)

Baseline v2.2 defines exactly **five internal roles** for the InChi Pilot:

| Role | Permitted Actions (v2.2 §4) | Operational Boundary (v2.2 §4) |
|---|---|---|
| **Administrator** | Manage internal users, reference values, and configuration versions. | Cannot change historical match results or approve own configuration changes without Product Authority approval. Cannot edit commercial data. |
| **Data Contributor** | Create and edit draft supplier, product, assessment, and buyer requirement records. | Cannot mark evidence as source checked, verify evidence, or record final dispositions. |
| **Analyst** | Review completeness, record evidence conditions (including official source checks), request information, and run matching. | Cannot alter locked master data during a match run or record final disposition unless also assigned Reviewer. |
| **Reviewer** | Review assessments and match explanations; record readiness outcomes and final dispositions. | Cannot silently alter source responses or evidence history. Cannot review assessments they submitted. |
| **Viewer** | Read approved internal records and reports. | Strict read-only. Zero create, edit, verify, run, or decide permissions (AC-22, SEC-01). |

---

## 3. Governing Permissions Matrix (Baseline v2.2 §4.2)

This matrix governs product behavior for the MVP build. Any deviation requires an approved Change Request (`CRQ-###` per v2.2 §15.3).

| Action | Administrator | Data Contributor | Analyst | Reviewer | Viewer | Governed Test ID |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Create or edit draft supplier/product** | **Yes** | **Yes** | Read | Read | No | AC-01, AC-02, SEC-01 |
| **Submit assessment** | **Yes** | **Yes** | **Yes** | Read | No | AC-04, SEC-01 |
| **Set evidence condition** | **Yes** | No | **Yes** | Review | No | AC-05, AC-07, SEC-02 |
| **Mark official source checked** | **Yes** | No | **Yes** | Review | No | AC-06, SEC-02 |
| **Create buyer requirement** | **Yes** | **Yes** | **Yes** | Read | No | AC-11, SEC-01 |
| **Run matching** | **Yes** | No | **Yes** | **Yes** | No | AC-12, SEC-01 |
| **Record final disposition** | **Yes** | No | No | **Yes** | No | AC-19, SEC-01 |
| **Manage users / configuration** | **Yes** | No | No | No | No | SEC-01, AUD-01 |
| **Audit log access** | View (All) | No | View (Scoped) | View (All) | No | AC-23, SEC-06 |

---

## 4. Current As-Built Implementation & Transition (Decision D-22)

### 4.1 Interim 3-Role Mapping in Code (`policy.py`)

As discovered in the Week 4 Repository Audit (`docs/governance/AUDIT_2026-11-21.md` §3), the current codebase implements three roles:
* `Role.PLATFORM_ADMIN`
* `Role.COMMERCIAL_ANALYST`
* `Role.REVIEWER`

Under **Decision D-22** (escalated to BNCS on 21 Nov 2026), the team will transition to the v2.2 five-role model. Until D-22 is formally closed, the interim roles map to the baseline as follows:

| Baseline v2.2 Target Role | Current Interim Role in Code | Temporary Permission Compromise |
|---|---|---|
| **Administrator** | `platform_admin` | Matches baseline; user management and configuration. |
| **Data Contributor** & **Analyst** | `commercial_analyst` (Combined) | Current code allows `commercial_analyst` to both draft and set evidence metadata, which will be separated once D-22 merges. |
| **Reviewer** | `reviewer` | Matches baseline; records readiness outcomes and match dispositions. |
| **Viewer** | *Unimplemented in code* | Currently blocked from API by default; must be added to `accounts.models.Role`. |

---

## 5. Separation of Duties & Conflict-of-Interest Guardrails

To prevent insider misuse and maintain commercial integrity, the backend enforces the following controls:

1. **Separation of Assessment Submission and Review (AC-06 / SEC-TEST-06)**:
   - A Reviewer who originally drafted or submitted a China-readiness assessment for a supplier is blocked from approving or setting the final outcome on that same assessment (`submitted_by != reviewed_by`).
2. **Exclusion of Administrator from Commercial Editing**:
   - Platform Administrators possess zero create, edit, or approval permissions on suppliers, products, buyer requirements, or opportunities.
3. **Disposition Exclusivity (AC-19 / M7-AC1)**:
   - Analysts and Contributors cannot mark match dispositions as `ACCEPT_FOR_FOLLOW_UP`, `HOLD_FOR_INFORMATION`, or `REJECT`. Only Reviewers hold disposition authority, and a mandatory text reason is required.
4. **Append-Only Audit Immutability (AC-23 / SEC-06 / TD-03)**:
   - No user (including Administrator) possesses permissions to edit or purge `AuditEvent` records. The PostgreSQL database trigger rejects all SQL `UPDATE` and `DELETE` queries.
5. **No Self-Registration or Role Elevation (AUD-01)**:
   - User creation is strictly restricted to authenticated Administrators via `UserAdmin` or CLI `create_platform_admin`. Any anonymous endpoint capable of creating accounts with arbitrary roles is a Critical defect.

---

## 6. Backend Enforcement Architecture

Every DRF view class must enforce permissions via:
```python
# Standard view configuration pattern (ARCHITECTURE.md §5)
permission_classes = [IsAuthenticated, RolePermission]
policy_resource = "<resource_name>"
```
Where `RolePermission` checks the requesting user's `role` against the policy in `backend/apps/accounts/policy.py`. Object-level scoping is implemented within `check_object_permissions()` and `get_queryset()` to ensure users never retrieve or mutate records outside their authorization boundary.
