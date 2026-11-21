# InChi Pilot Gateway — Integration Plan and Interface Contracts

| | |
|---|---|
| **Owner** | Aryan Ghai, Technical Project Coordinator |
| **Contract owners** | Abhishek (Django API, IF-01–IF-04, IF-07, IF-08), Priyanka (frontend consumer), Vishal (models, audit storage), Alok (IF-05 engine), Harish (contract tests), Ajendra (security review) |
| **Last updated** | 21 November 2026 (end of Week 4), verified against the running stack ([audit §1](AUDIT_2026-11-21.md#1-checks-actually-run)) |
| **Rule** | A contract changes only with its consumer's agreement, is versioned or backward-compatible, and the OpenAPI file is regenerated in the same PR (AGENTS.md §B rule 4). |

---

## 1. Components

| Component | Path | Runtime (Compose service) | Owner |
|---|---|---|---|
| Frontend | `frontend/` | `frontend`, Next.js standalone, the only public entry point (`http://localhost:3000`) | Priyanka |
| Application API | `backend/config/`, `backend/apps/*` (views, serializers, permissions, URLs) | `backend`, Django + DRF under gunicorn, internal port 8000 | Abhishek |
| Data layer | `backend/apps/*/models.py`, `migrations/` | `db`, PostgreSQL 17 + pgvector image | Vishal |
| Matching integration | `backend/apps/matching/` (services, client, schemas, tests) | Runs inside `backend` | Alok |
| Matching engine | `backend/ai_matching/` | `matching`, FastAPI under uvicorn, internal port 8001 (TD-11) | Alok |

```
Browser ──► Next.js (frontend:3000) ──rewrites /api/*, /admin/*, /static/*──► Django (backend:8000) ──ORM──► PostgreSQL (db:5432)
                                                                                   │
                                                                                   └─HTTP JSON (IF-05)──► FastAPI engine (matching:8001)
```

The browser never talks to Django or the engine directly. The engine never touches the database (TD-02).

---

## 2. Contracts

Wiring status: **Live** = verified on 21 Nov through the Next.js origin. **Partial** = provider exists, consumer or storage missing. **Planned** = not built.

### IF-01 Authentication and session — Live, defect open

- **Endpoints:** `GET /api/v1/auth/csrf/` (sets `csrftoken`), `POST /api/v1/auth/login/` (`email`, `password`; rotates session and CSRF), `POST /api/v1/auth/logout/`, `GET /api/v1/auth/me/`, `/api/v1/auth/users/` (user management, admin only).
- **Errors:** 401 `not_authenticated`; 403 `permission_denied`; 403 `csrf_failed`. All errors use `{code, message, field_errors, correlation_id}`.
- **Defect AUD-01:** `POST /api/v1/auth/register/`, `POST /api/v1/auth/verify/` and `/verify/status/` are anonymous and allow self-registration with any role. They are not part of this contract and must be removed or restricted (D-12, v2.2 §14.1).

### IF-02 Supplier, product and evidence registry — Live

- `/api/v1/suppliers/` CRUD, `POST {id}/complete/`, `POST {id}/archive/`. States: draft, complete, archived. `version` for optimistic concurrency (409 on conflict).
- `/api/v1/products/` CRUD, linked to a supplier (AC-02).
- `/api/v1/evidence/` evidence metadata only (D-10).
- **To align:** controlled values (category, supplier type, units, capacity period) under D-23.

### IF-03 China-readiness assessment — Live; missing from committed OpenAPI

- `GET /api/v1/assessments/criteria/` (CR-01–CR-18 definitions).
- `/api/v1/assessments/` CRUD; `GET {id}/submission-gate/`; `POST {id}/submit/`; `POST {id}/request-information/`; `POST {id}/complete-review/` (outcome + reason; reviewer cannot review own submission).
- `/api/v1/assessment-evidence/` evidence conditions per criterion (nine v2.2 codes).
- **Gaps:** no backend tests (AUD-05); paths absent from `docs/api/openapi.yaml` (AUD-06); role checks to align under D-22.

### IF-04 Buyer requirement — Live

- `/api/v1/requirements/` CRUD; `POST {id}/mark-ready/` (completeness gate, AC-11); `POST {id}/close/`. States: draft, ready_for_matching, closed (v2.2 §8.2).
- **Gaps:** no backend tests; Buyer Organisation entity and v2.2 category codes (D-23); requirement version history for match inputs (AC-18).

### IF-05 Django ↔ matching engine — Partial

- **Provider:** `GET http://matching:8001/health`, `POST http://matching:8001/match`. Contract version `0.2.0-proposed` ([docs/ai/MATCHING_CONTRACT.md](../ai/MATCHING_CONTRACT.md)).
- **Consumer:** `backend/apps/matching/integrations/ai_engine_client.py` with `services/request_builder.py`, `supplier_selector.py` and `result_handler.py`; 62 Django-side tests pass.
- **Missing:** no Django API to trigger a run, no `MatchRun`/`MatchResult` storage, no URL route.
- **Blocked by D-21.** Under v2.2 the response must carry per-criterion Pass / Unknown / Fail, preference Met / Not Met / Unknown, eligibility ELIGIBLE / INFORMATION_REQUIRED / NOT_ELIGIBLE, the rules version, input versions and a deterministic explanation, with **no score or confidence percentage** (v2.2 §9.3, §9.4, AC-18).
- **Failure policy:** an engine error stores the run as failed with no results (never a silent substitute).

### IF-06 Audit events — Live (write side)

- `apps.audit.services.record_event()` inside the same transaction as the change. Append-only in the app; a database trigger rejects UPDATE and DELETE (TD-03).
- **Missing:** read API for the SCR-07 audit history screen (`/audit` page currently shows an empty state).

### IF-07 Dashboard — Planned

- One read-only endpoint returning the v2.2 SCR-01 counts (suppliers, products, assessments needing review, open buyer requirements) and the work queue. The frontend must not show readiness percentages or match scores (AUD-04).

### IF-08 Match run, results and disposition — Planned

- Run a match for one requirement (gate: requirement must be Ready for Matching, AC-12), list runs and results (SCR-05), open one result (SCR-06), record a disposition `ACCEPT_FOR_FOLLOW_UP` / `HOLD_FOR_INFORMATION` / `REJECT` with a mandatory reason (AC-19), and mark earlier dispositions `Superseded` when inputs change (AC-21).

---

## 3. Integration gates

| Gate | Date | Integration content | Status |
|---|---|---|---|
| Gate 1 | 6 Nov | IF-01, IF-02, IF-06 (write), single-origin proxy | Demonstrated; gate record to be added |
| Gate 2 | 20 Nov | IF-03, IF-04 live; rule baseline (v2.2) available before AI integration | Review held; **outcome not recorded**; open: D-21 to D-25, AUD-01 |
| Gate 3 | 4 Dec | IF-05, IF-07, IF-08 live; audit read API; full journey on seeded synthetic data; feature freeze | Scheduled |
| Gate 4 | 11 Dec | No critical access-control defect; regression and UAT evidence | Scheduled |
| Gate 5 | 18 Dec | Repeatable demo and handover | Scheduled |

---

## 4. Week 5 and Week 6 integration sequence

Assumes D-21 is decided on Mon 23 Nov. If it is not, matching items slip day for day and Aryan escalates under AGENTS.md §B rule 14.

| Day | Item | Owner | Depends on |
|---|---|---|---|
| Mon 23 Nov | Close AUD-01; record D-21 to D-25 and Gate 2 outcome | Abhishek, Ajendra; Aryan | — |
| Tue 24 Nov | Engine contract v0.3 aligned to v2.2 §9 (or to the approved CRQ) | Alok, agreed with Abhishek | D-21 |
| Tue 24 – Wed 25 Nov | `MatchRun`, `MatchResult`, disposition models with exact input versions | Vishal | D-21, D-23 |
| Wed 25 – Thu 26 Nov | Match orchestration and disposition API (IF-08); OpenAPI regenerated | Abhishek, Alok | DEP-04, DEP-05 |
| Thu 26 – Fri 27 Nov | SCR-05 and SCR-06 screens | Priyanka | IF-08 |
| Fri 27 Nov | Week 5 review: explainable result and human decision end-to-end | All; Harish verifies | — |
| Mon 30 Nov – Tue 1 Dec | Dashboard and audit read APIs (IF-07, IF-06 read); opportunity API only if D-24 keeps M8 | Abhishek, Vishal | D-24 |
| Tue 1 – Wed 2 Dec | `seed_demo` with the v2.2 §3.2 dataset | Vishal | D-23 |
| Wed 2 – Thu 3 Dec | Full-journey E2E on seeded data (AC-25) | Harish | DEP-07 |
| Fri 4 Dec | Gate 3 and feature freeze | Aryan | — |
