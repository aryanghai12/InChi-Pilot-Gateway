# InChi Pilot Gateway — Integration Plan & Interface Contracts

**Owner:** Aryan Ghai (Technical Project Coordinator)  
**Co-Owners:** Abhishek Kumar (Backend), Priyanka Singh (Frontend), Alok Tiwari (AI Matching), Vishal Chauhan (Database), Harish Pal (QA), Ajendra Nath Tripathi (Security)  
**Status:** Baseline Active — Updated for Week 4 (21 November 2026)

---

## 1. Integration Scope & Objectives

The integration plan coordinates data flows, contract boundaries, validation rules, and deployment interfaces across the four core runtime components:

1. **Frontend Web Layer (`frontend/`):** Next.js App Router presentation, client-side queries, and single-origin proxying.
2. **Backend Application Layer (`backend/apps/`):** Django REST Framework API, session management, RBAC policy enforcement, and workflow state machines.
3. **Database & Persistence Layer (`backend/` ORM):** PostgreSQL 17 + pgvector, migrations, relational integrity, and audit events.
4. **AI Matching Engine (`backend/ai_matching/`):** FastAPI AI service handling preprocessing, hard filtering, local vector embeddings, cosine similarity, hybrid scoring, and explainability.

---

## 2. Interface Contract Boundaries

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend Client                         │
└───────────────────▲────────────────────────────────▲───────────────────┘
                    │                                │
      Contract IF-01│ (Auth, CSRF, Session)          │ Contract IF-02/03/04
                    ▼                                ▼ (CRUD, Readiness, Demand)
┌────────────────────────────────────────────────────────────────────────┐
│                        Django 5.2 Application                          │
│                                                                        │
│  apps/accounts   apps/registry   apps/readiness   apps/demand          │
│        ▲               ▲                ▲               ▲              │
│        │               │                │               │              │
│        └───────────────┴────────┬───────┴───────────────┘              │
│                                 ▼ Contract IF-06 (Internal Audit Event)│
│                            apps/audit                                  │
│                                 │                                      │
│                                 ▼ Contract IF-05 (HTTP JSON)           │
│                           apps/matching (Integration Layer)            │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   FastAPI AI Matching Engine                           │
│  - Preprocessing                                                       │
│  - Mandatory Eligibility Filters (Hard Rules)                          │
│  - Semantic Similarity & Hybrid Scorer                                 │
│  - Ranking & Explainable Rationale                                     │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Contract IF-01: Authentication & User Session
- **Parties:** Frontend (Priyanka) $\leftrightarrow$ Backend (Abhishek)
- **Transport:** HTTP Cookie Session (`sessionid`), CSRF token (`csrftoken`), JSON envelope
- **Endpoints:**
  - `GET /api/v1/auth/csrf/` — bootstrap CSRF cookie and token
  - `POST /api/v1/auth/login/` — credentials submission (`email`, `password`), session establishment
  - `POST /api/v1/auth/logout/` — session invalidation and cookie clearing
  - `GET /api/v1/auth/me/` — current user identity, role, and permissions
- **Status Codes:** 401 `not_authenticated` for anonymous requests on protected routes; 403 `permission_denied` for role violations.
- **Agreement Date:** Week 2 (Locked)

### 2.2 Contract IF-02: Supplier & Product Registry
- **Parties:** Frontend (Priyanka) $\leftrightarrow$ Backend (Abhishek & Vishal)
- **Transport:** DRF REST APIs, JSON payloads with OpenAPI 3.0.3 schema
- **Endpoints:**
  - `/api/v1/suppliers/` — Supplier CRUD, state transitions (`Draft`, `Complete`, `Archived`), optimistic locking (`version`)
  - `/api/v1/products/` — Product CRUD, supplier linking, MOQ, pricing, bilingual fields (`product_name_zh`, `translation_status`)
  - `/api/v1/evidence/` — Evidence item metadata references (EVD-01 to EVD-10)
- **Agreement Date:** Week 3 (Locked)

### 2.3 Contract IF-03: China-Readiness Assessment
- **Parties:** Frontend (Priyanka) $\leftrightarrow$ Backend (Abhishek) $\leftrightarrow$ Product (Adrika)
- **Transport:** DRF REST APIs conforming to *China Readiness Baseline v2.2*
- **Endpoints:**
  - `GET /api/v1/assessments/` — List assessments with dual-aliasing (`status` / `workflow_state`)
  - `POST /api/v1/assessments/` — Create assessment draft against 18 compliance criteria (`CR-01` to `CR-18`)
  - `GET /api/v1/assessments/{id}/submission-gate/` — Pre-submission completeness validation
  - `POST /api/v1/assessments/{id}/submit/` — Transition draft to submitted
  - `POST /api/v1/assessments/{id}/complete-review/` — Reviewer disposition (`ready_for_matching`, `information_required`, `not_currently_eligible`) with `deny_self_review`
- **Agreement Date:** Week 4 (Locked)

### 2.4 Contract IF-04: Buyer Procurement Requirements
- **Parties:** Frontend (Priyanka) $\leftrightarrow$ Backend (Abhishek) $\leftrightarrow$ Product (Adrika)
- **Transport:** DRF REST APIs conforming to Buyer Requirement Field Dictionary v1.4
- **Endpoints:**
  - `/api/v1/requirements/` — Requirement CRUD (`draft`, `ready_for_matching`, `closed`)
  - `POST /api/v1/requirements/{id}/mark-ready/` — Readiness validation gate checking China destination port, positive quantity, and pricing rules
- **Agreement Date:** Week 4 (Locked)

### 2.5 Contract IF-05: AI Matching Engine Integration
- **Parties:** Backend Matching Orchestration (Abhishek) $\leftrightarrow$ AI Matching Engine (Alok)
- **Transport:** HTTP Client / Internal Docker Network (`http://matching:8001`)
- **Endpoints:**
  - `GET /health` — Service readiness and provider state
  - `POST /api/v1/match/` — Full candidate evaluation and scoring pipeline
- **Request Payload:**
  - `requirement`: Buyer requirement criteria, category, target port, delivery timeline.
  - `candidate_pool`: List of active suppliers with `READY_FOR_MATCHING` readiness outcomes and associated product specifications.
  - `weights`: Approved preference weights (D-05).
- **Response Payload:**
  - `results`: Ranked candidates with overall score, eligibility flag, similarity score, weighted component breakdown, missing info flags, and explainability text.
- **Failure Policy:** Explicit failure (HTTP 500/503) — no silent fallback or unverified substitution (MVP_FEATURES M6-AC5).
- **Agreement Date:** Week 4 (Engine drafted; live pipeline integration active in Week 5).

### 2.6 Contract IF-06: Internal Audit Trail
- **Parties:** All Django Apps $\leftrightarrow$ Audit App (Vishal & Abhishek)
- **Transport:** Internal Python service call `apps.audit.services.record_event()`
- **Schema:** Actor ID, Action Type, Entity Name, Entity ID, Changes (diff), IP Address, Correlation ID, Timestamp.
- **Immutability:** Write-only via ORM; updates and deletions rejected at database level.
- **Agreement Date:** Week 2 (Locked)

---

## 3. Integration Gates & Verification Schedule

| Gate | Target Date | Milestone Focus | Integration Deliverables | Status |
|---|---|---|---|---|
| **Gate 1** | Week 2 (06 Nov 2026) | Authenticated Vertical Slice | Session login, CSRF bootstrap, Supplier CRUD, Audit logging, Single-origin proxy. | **Passed** |
| **Gate 2** | Week 4 (20 Nov 2026) | Workflow & Rule Approval | China Readiness Baseline v2.2 (M4), Buyer Demand Gate (M5), OpenAPI 3.0.3 Sync, Full-Stack Docker Compose. | **Passed** |
| **Gate 3** | Week 6 (04 Dec 2026) | Integrated MVP & Feature Freeze | End-to-end matching runs (M6), Reviewer match disposition (M7), Opportunity pipeline (M8), Dashboard (M9). | Scheduled |
| **Gate 4** | Week 7 (11 Dec 2026) | Security & UAT Readiness | Zero high/critical access vulnerabilities, automated regression suite, residual risk statement. | Scheduled |
| **Gate 5** | Week 8 (18 Dec 2026) | Demonstration & Final Handover | Live demonstration on synthetic data, 6 complete handover packs, final project archive. | Scheduled |

