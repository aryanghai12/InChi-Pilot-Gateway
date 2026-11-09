# Role-Based Access Control (RBAC) & Object-Level Permission Matrix

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Working Baseline — **Tagged `UNAPPROVED – D-09`** |
| **Authority** | [`../MVP_FEATURES.md`](../MVP_FEATURES.md) §5; [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §5 |
| **Enforcement Point** | `backend/apps/accounts/policy.py` (Abhishek Kumar) |
| **Reviewers** | Abhishek Kumar (Backend), Aryan Ghai (Coordination) |

---

## 1. Principles of Access Control

The InChi Pilot Gateway enforces access control strictly according to these foundational engineering rules:
1. **The Backend is the Single Authority**: Client-side UI route guarding only provides usability guidance. The Django REST Framework backend enforces 100% of authentication, role verification, and object-level scoping (AGENTS.md §B rule 10).
2. **Deny-by-Default Architecture**: Any action or resource not explicitly permitted to a role in `accounts/policy.py` is denied with an HTTP 403 `permission_denied` response.
3. **Least Privilege**: Users are granted access only to data and operations strictly required for their role.
4. **Isolated Policy Architecture**: To ensure that pending business decisions under **D-09** can be ratified without widespread code churn, all permission rules are centralized in `backend/apps/accounts/policy.py`. Views and serializers must never hard-code role strings.

---

## 2. Internal User Roles

The pilot defines exactly three authorized internal roles (MVP_FEATURES §5):

* **Platform Administrator (`platform_admin`)**: Responsible for internal user management, account activation/deactivation, and inspecting system audit records. Excluded from commercial transactions and review approvals.
* **Commercial Analyst (`commercial_analyst`)**: Creates and updates supplier, product, readiness, and buyer requirement records; triggers AI match runs; drafts commercial opportunities.
* **Reviewer / Approver (`reviewer`)**: Independent review authority. Formally evaluates China-readiness assessments, records human match dispositions (`Accepted` / `Rejected` / `On hold`), and approves opportunity stage closures.

*(Note: The fourth role "Read-only Auditor" from early blueprints was formally excluded from MVP scope to keep the attack surface minimal).*

---

## 3. Object-Level Permission Matrix (v0.1 Pilot)

**Status Notice**: Formal ratification of these permissions awaits BNCS approval under **Decision D-09**. In accordance with MVP_FEATURES §5, all entries are implemented using the **most restrictive reasonable baseline**.

> **Key**:  
> • **V**: View / Read  
> • **C**: Create / Add  
> • **E**: Edit / Update  
> • **S**: Submit / Advance State  
> • **R**: Formal Review / Approve / Reject  
> • **M**: Manage (Deactivate / Assign Roles)  
> • **—**: No Access (Refused with HTTP 403)

| Resource / Action | Platform Administrator | Commercial Analyst | Reviewer / Approver | Status & Guardrails |
|---|:---:|:---:|:---:|---|
| **User Accounts & Roles** | **V, C, E, M** | — | — | Restricted Django Admin only (`accounts/UserAdmin`). Cannot delete or self-deactivate. |
| **Active Criteria & Questions** | **V** | **V** | **V** | Read-only in application. Updated only via versioned config. |
| **Supplier Records** | **V** | **V, C, E, S** | **V** | Analyst can create, edit, draft, archive. Reviewer view only. |
| **Product Catalogue** | **V** | **V, C, E** | **V** | Linked to existing authorized supplier. |
| **Evidence Metadata** | **V** | **V, C, E** | **V, R** *(Verify)* | Metadata only (D-10). Reviewer marks "Verified" (`[OPEN]`). |
| **Readiness Assessment** | **V** | **V, C, E, S** | **V, R** | Analyst submits. Reviewer records outcome/more-info. |
| **Buyer Requirements** | **V** | **V, C, E, S** | **V** | Analyst defines mandatory/preference criteria and marks ready. |
| **Trigger Match Run** | — | **C** *(Execute)* | **C** *(Execute)* | Synchronous execution. Generates immutable `MatchRun`. |
| **Match Results & Explanations** | **V** | **V** | **V** | View-only for all authorized roles. |
| **Match Disposition** | **V** | *Recommend only* | **R** *(Decide)* | **M7-AC1**: Only Reviewer can record Accepted/Rejected/Hold (`[OPEN]`). |
| **Commercial Opportunity** | **V** | **V, C, E** | **V, E, Close** | Created *only* from Accepted disposition. Reviewer closes (`[OPEN]`). |
| **Dashboard Metrics** | **V** | **V** | **V** | Aggregate counts scoped to authorized data. |
| **Audit Log History** | **V** *(All)* | **V** *(Scoped)* | **V** *(All)* | Analyst sees audit events *only* for records they can access (`[OPEN]`). |

---

## 4. Separation of Duties & Conflict-of-Interest Guardrails

To prevent insider misuse and maintain commercial integrity, the backend enforces the following controls under **D-09**:

1. **Separation of Assessment Submission and Review**:
   - A Reviewer who originally drafted or submitted a China-readiness assessment for a supplier is blocked from approving or setting the final outcome on that same assessment (`submitted_by != reviewed_by`).
2. **Exclusion of Administrator from Commercial Editing**:
   - Platform Administrators possess zero create, edit, or approval permissions on suppliers, products, buyer requirements, or opportunities.
3. **Disposition Exclusivity**:
   - Commercial Analysts cannot mark match dispositions as `Accepted` or `Rejected`. Only the Reviewer role holds approval authority.
4. **Append-Only Audit Immutability**:
   - No user (including Platform Administrator) possesses permissions to edit or purge `AuditEvent` records.

---

## 5. Backend Enforcement Architecture

Every DRF view class must enforce permissions via:
```python
# Standard view configuration pattern (ARCHITECTURE.md §5)
permission_classes = [IsAuthenticated, HasRolePermission]
```
Where `HasRolePermission` checks the requesting user's `role` against the policy in `backend/apps/accounts/policy.py`. Object-level scoping is implemented within `get_queryset()` to ensure users never retrieve records outside their authorization boundary.

