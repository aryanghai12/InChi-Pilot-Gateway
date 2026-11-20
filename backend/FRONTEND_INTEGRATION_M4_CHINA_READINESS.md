# Frontend Integration Guide — Module M4: China Readiness Assessment

**Author:** Abhishek Kumar (Application Backend & Access-Control Engineer)  
**Target:** Priyanka Singh (Frontend Web & Client Integration Engineer)  
**Baseline Authority:** *InChi China Readiness Implementation Baseline Version 2.2*  
**Base URL:** `/api/v1/assessments/` and `/api/v1/assessment-evidence/`  
**Test Suite:** 100% Passing (`project-documentation/tests/readiness/test_readiness.py`)

---

## 1. Overview & Architecture Alignment

Module M4 evaluates Indian exporters against the China trade compliance baseline before supplier-demand matching occurs (M6/M7).

### Key Architectural Rules (Mentor Baseline v2.2):
1. **Separation of Supplier & Readiness State (§2.3):**
   - Core `Supplier` and `Product` records remain separate.
   - An assessment links to 1 `Supplier` and $\ge 1$ `Product`.
2. **Dual-Compatibility for Frontend (Zero-Breaking Design):**
   - Both `workflow_state` (backend authoritative) and `status` (frontend alias) are supported in read & write.
   - Both `readiness_outcome` (backend authoritative) and `outcome` (frontend alias) are supported in read & write.
   - Accepts both structured list `[{question_id, response, notes}]` and dict `{"CR-01": {"response": "..."}}`.
3. **Strict Categorical Outcomes — NO Percentage Scores (§8.1):**
   - Evaluated outcome is strictly qualitative: `READY_FOR_MATCHING`, `INFORMATION_REQUIRED`, or `NOT_CURRENTLY_ELIGIBLE`.
   - The UI shows `completeness` (0–100%) indicating question progress, but readiness disposition is never a numeric score.
4. **RBAC & Object Rules (`deny_self_review`):**
   - **Commercial Analyst:** Creates drafts, edits answers, links products, and submits (`POST /submit/`).
   - **Reviewer:** Requests more information (`POST /request-information/`) or approves outcome (`POST /complete-review/`).
   - **Self-Review Guard:** If a Reviewer submitted the assessment, they **cannot** review/approve it. A 403 Forbidden is raised with message `"Reviewer cannot approve an assessment they submitted."`

---

## 2. API Endpoints Reference

| Method | Endpoint | Action Description | Allowed Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/assessments/` | List assessments (supports filter by supplier, status, outcome) | Admin, Analyst, Reviewer |
| `POST` | `/api/v1/assessments/` | Create a new assessment draft | Commercial Analyst |
| `GET` | `/api/v1/assessments/{id}/` | Retrieve assessment details with linked products & evidence | Admin, Analyst, Reviewer |
| `PATCH` | `/api/v1/assessments/{id}/` | Update questionnaire answers, notes, linked products | Commercial Analyst |
| `GET` | `/api/v1/assessments/{id}/submission-gate/` | Live pre-submission check (returns blocking reasons) | Admin, Analyst, Reviewer |
| `POST` | `/api/v1/assessments/{id}/submit/` | Submit assessment for review (validates Section 6.1 gate) | Commercial Analyst |
| `POST` | `/api/v1/assessments/{id}/request-information/` | Request additional evidence/answers from analyst | Reviewer |
| `POST` | `/api/v1/assessments/{id}/complete-review/` | Record final outcome (`READY_FOR_MATCHING`, etc.) | Reviewer (Non-submitter) |
| `GET` | `/api/v1/assessments/criteria/` | Get full 18-question reference metadata | Admin, Analyst, Reviewer |
| `GET` | `/api/v1/assessment-evidence/` | List evidence items attached to assessments | Admin, Analyst, Reviewer |
| `POST` | `/api/v1/assessment-evidence/` | Upload / attach evidence record to assessment | Commercial Analyst |

---

## 3. Workflow States & Outcomes

### Workflow States (`workflow_state` / `status`):
- `draft` — "Draft"
- `submitted` — "Submitted"
- `under_review` — "Under Review"
- `information_required` — "Information Required"
- `review_complete` — "Review Complete"
- `archived` — "Archived"

### Readiness Outcomes (`readiness_outcome` / `outcome`):
- `ready_for_matching` — "Ready for matching" (Supplier is eligible for Alok's matching engine)
- `information_required` — "Information required" (More docs/clarifications required)
- `not_currently_eligible` — "Not currently eligible" (Exclusion criteria / non-compliant)

### 9 Categorical Evidence Conditions (`evidence_condition` per §7):
1. `NOT_PROVIDED`
2. `SELF_DECLARED`
3. `DOCUMENT_RECEIVED_UNVERIFIED` (Default upon upload)
4. `OFFICIAL_SOURCE_CHECKED` (Verified by analyst against DGFT/GACC/ROC portal)
5. `THIRD_PARTY_REPORT_RECEIVED_UNVERIFIED`
6. `THIRD_PARTY_REPORT_SOURCE_CHECKED`
7. `EXPIRED`
8. `DISCREPANCY`
9. `NOT_APPLICABLE`

---

## 4. The 18 China Readiness Criteria Baseline (§6)

The frontend can dynamically fetch this list from `GET /api/v1/assessments/criteria/`, or use this static reference:

| ID | Category | Title | Mandatory | Evidence Req. |
| :--- | :--- | :--- | :---: | :---: |
| **CR-01** | Corporate & Legal Identity | Indian Legal Entity Identity & Verification | Yes | Yes |
| **CR-02** | Corporate & Legal Identity | CIN / Corporate Registration Details | Yes | Yes |
| **CR-03** | Tax & Export Identity | GSTIN Registration & Tax Compliance | No | No |
| **CR-04** | Tax & Export Identity | IEC Validity & DGFT Authorisation | Yes | Yes |
| **CR-05** | Manufacturing & Capacity | Production Plant & Infrastructure | No | No |
| **CR-06** | Customs & Sanitary | GACC Registration Status (Decree 248/249) | Yes | Yes |
| **CR-07** | Customs & Sanitary | CIQ Phytosanitary / Sanitary Compliance | Yes | Yes |
| **CR-08** | Packaging & Regulatory | Chinese GB Labeling & Packaging (GB 7718/5296) | Yes | Yes |
| **CR-09** | Traceability & Quality | Lot Traceability & Recall Protocols | Yes | No |
| **CR-10** | Certifications | Quality Accreditations (ISO 22000, HACCP, BRCGS) | Yes | Yes |
| **CR-11** | Cold-Chain & Logistics | Reefer / Cold Storage Temperature Integrity | Yes | No |
| **CR-12** | Cold-Chain & Logistics | Shelf-Life Buffer & Sea Transit Window | Yes | No |
| **CR-13** | Commercial Experience | Historical Export Experience to East Asia | Yes | No |
| **CR-14** | Communication | Mandarin Technical & Commercial Interface | Yes | No |
| **CR-15** | Banking & Currency | Cross-Border Settlement (L/C, RMB, USD) | Yes | No |
| **CR-16** | Legal & Governance | International Dispute Resolution (SIAC, CIETAC) | Yes | No |
| **CR-17** | Legal & Governance | Sanctions & Customs Blacklist Absence Declaration | Yes | Yes |
| **CR-18** | Legal Declaration | China Readiness Limitation Confirmation | Yes | No |

> **Section 6.1 Submission Gate Rule:**
> To submit, the assessment must have:
> 1. Linked Supplier
> 2. $\ge 1$ Linked Product
> 3. Mandatory criteria answered: `CR-01`, `CR-02`, `CR-04`, `CR-06` through `CR-18`
> 4. `CR-18` response explicitly confirmed (`"confirmed"`, `"yes"`, or `"true"`).

---

## 5. Request & Response Payload Examples

### A. Create Assessment Draft
`POST /api/v1/assessments/`
```json
{
  "supplier": "e0b57116-c875-4fc1-a8bb-37d4554b7c12",
  "linked_products": [
    "f27a69cb-6ec8-49ee-848e-f182c814b727"
  ],
  "submission_notes": "Initial assessment for Organic Herbal extracts.",
  "answers": {
    "CR-01": { "response": "Himalayan Extracts Ltd", "notes": "Verified ROC" },
    "CR-04": { "response": "0512019988", "notes": "Active IEC" }
  }
}
```

### B. Response Structure
`GET /api/v1/assessments/{id}/`
```json
{
  "id": "b160b73c-23a1-4048-b39b-e8df9911e860",
  "supplier": "e0b57116-c875-4fc1-a8bb-37d4554b7c12",
  "supplier_name": "Himalayan Herbal Extracts Ltd",
  "linked_products": ["f27a69cb-6ec8-49ee-848e-f182c814b727"],
  "linked_product_details": [
    {
      "id": "f27a69cb-6ec8-49ee-848e-f182c814b727",
      "product_name": "Organic Ashwagandha Extract KSM-66",
      "category": "Agriculture and Food"
    }
  ],
  "questionnaire_version": "2.2",
  "workflow_state": "draft",
  "status": "draft",
  "state_display": "Draft",
  "readiness_outcome": null,
  "outcome": null,
  "outcome_display": null,
  "assigned_analyst": "466c4233-363b-4fa5-b475-52d2ba4b257e",
  "submitted_by": null,
  "reviewer": null,
  "answers": { ... },
  "submission_notes": "Initial assessment for Organic Herbal extracts.",
  "reviewer_notes": "",
  "information_request_notes": "",
  "version": 1,
  "completeness": 35,
  "evidence_items": [],
  "created_by": "466c4233-363b-4fa5-b475-52d2ba4b257e",
  "created_at": "2026-11-19T14:30:00Z",
  "updated_at": "2026-11-19T14:35:00Z"
}
```

### C. Live Submission Gate Evaluation (Pre-check)
`GET /api/v1/assessments/{id}/submission-gate/`
```json
{
  "can_submit": false,
  "blocking_reasons": [
    "Mandatory criterion CR-06 must be answered.",
    "CR-18 China Readiness Assessment Limitation Confirmation must be explicitly confirmed."
  ],
  "completeness": 88,
  "workflow_state": "draft"
}
```

### D. Submit Assessment
`POST /api/v1/assessments/{id}/submit/`
```json
{
  "submission_notes": "All 18 compliance criteria completed and verified."
}
```

### E. Request More Information (Reviewer)
`POST /api/v1/assessments/{id}/request-information/`
```json
{
  "request_notes": "Please provide Chinese packaging layout showing GB 7718 nutrition declaration."
}
```

### F. Complete Review (Reviewer Final Outcome)
`POST /api/v1/assessments/{id}/complete-review/`
```json
{
  "readiness_outcome": "ready_for_matching",
  "reviewer_notes": "GACC registration verified on single window portal. Ready for buyer matching."
}
```

---

## 6. TypeScript Types for Frontend (`src/lib/api/types.ts`)

```typescript
export type WorkflowState =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'information_required'
  | 'review_complete'
  | 'archived';

export type ReadinessOutcome =
  | 'ready_for_matching'
  | 'information_required'
  | 'not_currently_eligible';

export type EvidenceCondition =
  | 'not_provided'
  | 'self_declared'
  | 'document_received_unverified'
  | 'official_source_checked'
  | 'third_party_report_received_unverified'
  | 'third_party_report_source_checked'
  | 'expired'
  | 'discrepancy'
  | 'not_applicable';

export interface AssessmentEvidence {
  id: string;
  assessment: string;
  criterion_id: string;
  document_name: string;
  evidence_condition: EvidenceCondition;
  condition_display: string;
  issuer_source: string;
  reference_number: string;
  issue_date?: string | null;
  expiry_date?: string | null;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface LinkedProductSummary {
  id: string;
  product_name: string;
  category: string;
}

export interface ReadinessAssessment {
  id: string;
  supplier: string;
  supplier_name: string;
  linked_products: string[];
  linked_product_details: LinkedProductSummary[];
  questionnaire_version: string;
  workflow_state: WorkflowState;
  status: string; // Dual-alias
  state_display: string;
  readiness_outcome: ReadinessOutcome | null;
  outcome: string | null; // Dual-alias
  outcome_display: string | null;
  assigned_analyst?: string | null;
  submitted_by?: string | null;
  reviewer?: string | null;
  answers: Record<string, { response: string; notes?: string; evidence_reference?: string } | string>;
  submission_notes: string;
  reviewer_notes: string;
  information_request_notes: string;
  version: number;
  completeness: number; // 0 to 100
  evidence_items: AssessmentEvidence[];
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}
```

---

## 7. Troubleshooting & Frontend Tips

1. **CSRF & Cookie Protection:**  
   Next.js fetches must include credentials (`credentials: 'include'`) and send the `X-CSRFToken` header for all `POST`, `PATCH`, and `PUT` calls.
2. **Optimistic Locking:**  
   Always submit the current `version` integer when sending `PATCH` updates. If another user edited the assessment concurrently, the backend will respond with HTTP 409 Conflict.
3. **Submission Gate Validation:**  
   Use `/submission-gate/` to display real-time feedback (e.g., an alert banner with remaining criteria) so the user doesn't hit a submission error unexpectedly.
