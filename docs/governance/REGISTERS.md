# InChi Pilot Gateway — Delivery Registers

| | |
|---|---|
| **Maintained by** | Aryan Ghai, Technical Project Coordinator (AGENTS.md §C1) |
| **Last updated** | 21 November 2026 (end of Week 4), after the [repository audit](AUDIT_2026-11-21.md) |
| **Status rule** | Nothing is marked **Approved** or **Decided** without a named approver and a date (AGENTS.md §C1). Values that are only the team's working assumption are marked **Proposed** or **Open**. |

**Governing sources, in order of precedence**

1. [`InChi_China_Readiness_Implementation_Baseline_v2.2.pdf`](../source-documents/InChi_China_Readiness_Implementation_Baseline_v2.2.pdf) (16 Nov 2026, Product Authority: Venture Build Director and Chief Product Officer, BNCS) governs the **China-readiness and supplier–demand matching portion** of the MVP. Its final authority statement: when an earlier framework, note, spreadsheet or verbal instruction conflicts, v2.2 governs unless the VBD and CPO approve a documented change (`CRQ-###`, §15.3).
2. The revised ownership, journey and timeline PDFs (26 Oct 2026) govern roles, stage owners and dates (D-19 pending).
3. The build manual governs everything else (scope outside v2.2, gates, governance, severity, AI and security rules).

Contents: [1 Decisions](#1-decision-register) · [2 Risks](#2-risk-register) · [3 Issues](#3-issue-register) · [4 Dependencies](#4-dependency-register) · [5 Interfaces](#5-interface-contract-register) · [6 Change requests](#6-change-request-log-v22-153) · [7 Gates](#7-gate-register) · [8 Source discrepancies](#8-source-discrepancy-register)

---

## 1. Decision register

**Approver abbreviations.** *BNCS-PA*: BNCS Product Authority named in v2.2 (Venture Build Director and Chief Product Officer). *BNCS-PS*: BNCS Programme Sponsor. *BNCS-PVL*: BNCS Product and Venture Lead. *Mentor*: Senior Technical Mentor.

### 1.1 Business decisions

| ID | Decision | Status | Decided value / working assumption | Approver · date · record | Implementation gap |
|---|---|---|---|---|---|
| D-02 | Pilot sector and category list | **Decided** | Categories `ENG_COMPONENT`, `INDUSTRIAL_INPUT`, `SHELF_STABLE_FOOD` (v2.2 §5.1). Direction: Indian suppliers matched to Chinese buyer demand (v2.2 §1). | BNCS-PA · 16 Nov 2026 · v2.2 §1, §5.1 | Code uses seven "Field Dictionary v1.4" categories in `demand`, and free text in `registry`. **D-23.** The earlier register entry "Agribusiness, F&B, manufactured goods, Approved for Pilot" had no source and is withdrawn. |
| D-03 | Readiness questions, criteria, outcomes | **Decided** | 18 questions CR-01–CR-18, submission gate §6.1, outcomes READY_FOR_MATCHING / INFORMATION_REQUIRED / NOT_CURRENTLY_ELIGIBLE (§6.2), nine evidence conditions (§7), no numeric readiness score. | BNCS-PA · 16 Nov 2026 · v2.2 §6, §7 | M4 implemented to this. No backend tests yet (AUD-05). |
| D-04 | Mandatory eligibility and unknown handling | **Decided** | Deterministic sequence v2.2 §9.2 (requirement gate → category → specification → quantity/capacity → MOQ → lead time → evidence → commercial → export/language). Result logic §9.3: any confirmed Fail → NOT_ELIGIBLE; else any Unknown → INFORMATION_REQUIRED; else ELIGIBLE. No unit or currency conversion is invented (AC-16, AC-17). | BNCS-PA · 16 Nov 2026 · v2.2 §9 | Engine uses its own criteria model; must be aligned after D-21. |
| D-05 | Preference criteria, weights, semantic weight | **Decided** | **No weights.** Preferences evaluated for eligible candidates only, shown as "Met X of Y / Not Met / Unknown". No hidden weights, no confidence percentage (§9.2 rule 10, §9.4). Semantic similarity is a *Could* with explicit human confirmation (§3). | BNCS-PA · 16 Nov 2026 · v2.2 §3, §9 | **Conflicts** with the hybrid-scoring architecture and the "working weights 30/30/20/20" previously recorded here (withdrawn). **D-21.** |
| D-06 | Disposition vocabulary, deciding role, reason | **Decided** | `ACCEPT_FOR_FOLLOW_UP`, `HOLD_FOR_INFORMATION`, `REJECT`, plus `Superseded` when a new run replaces the input (§8.3). Reason mandatory (DSP-002, AC-19). Recorded by Reviewer or Administrator (§4.2). A rejection applies to one requirement only (AC-20). | BNCS-PA · 16 Nov 2026 · v2.2 §5, §8.3 | Not built yet (Week 5). The earlier "Accepted / Rejected / On hold, Approved for Pilot" entry is withdrawn. |
| D-07 | Opportunity stages, transitions, closure | **Open** | Proposed: Initiated, Discovery, Negotiation, Closed; created only from an accepted disposition. | BNCS-PVL · — | Depends on **D-24** (is M8 in scope?). |
| D-08 | Dashboard metric definitions | **Decided** | SCR-01: counts of Suppliers, Products, Assessments needing review, Open buyer requirements; work queue (Record ID, Type, State, Owner, Age, Action). Computed from stored records. | BNCS-PA · 16 Nov 2026 · v2.2 SCR-01 | No dashboard API. The frontend expects different fields (AUD-04). |
| D-09 | Permission matrix and separation of duties | **Decided** | Five roles (Administrator, Data Contributor, Analyst, Reviewer, Viewer) and the §4.2 matrix. Backend enforcement, deny by default (§14.1). | BNCS-PA · 16 Nov 2026 · v2.2 §4, §4.2 | Code has three roles. **D-22.** `policy.py` must stay marked `UNAPPROVED` until it matches the decided matrix or a CRQ is approved. |
| D-13 | Meaning of buyer "verification status" | **Decided (not in baseline)** | v2.2 defines no buyer verification field. Buyer Organisation is a minimal profile (BYR-001–003). Do not implement a verification status. | BNCS-PA · 16 Nov 2026 · v2.2 §5 | Buyer Organisation entity missing (**D-23**). |
| D-14 | Mandarin-ready fields | **Decided (partly)** | `product_name_zh_draft` (PRD-004), human-reviewed draft, not a certified translation. CR-16 status: Not Available / Draft / Human Reviewed; machine output alone is Draft. | BNCS-PA · 16 Nov 2026 · v2.2 PRD-004, CR-16 | Registry has `product_name_zh` and a translation status with different values. Align under D-23. |
| D-15 | Does a Reviewer approve a requirement before matching? | **Decided** | No. An **Analyst** moves Draft → Ready for Matching when category, specification, quantity/unit and mandatory criteria are complete (§8.2). | BNCS-PA · 16 Nov 2026 · v2.2 §8.2 | Matches the current `mark-ready` gate (role check to be aligned under D-22). *This ID is the business decision only; the FastAPI runtime decision is now TD-11.* |
| D-19 | Revised programme dates and final acceptance date | **Open (overdue)** | Working baseline 26 Oct – 18 Dec 2026. | BNCS-PS + University Coordinator · — | Raised every week since 26 Oct. |
| **D-21** | **Matching approach for the MVP** | **Open — blocks Week 5** | Options: (a) adopt v2.2: deterministic rules engine per §9.2/§9.3, preferences as Met X of Y, semantic similarity optional and human-confirmed, journey works with AI disabled; (b) raise CRQ-001 to keep mandatory semantic matching with hybrid scoring. **Coordinator recommendation: (a)**, keeping the existing FastAPI engine as the host of the rules engine, with the semantic provider off by default. | BNCS-PA (scope), Mentor (architecture) · — | AUD-02 |
| **D-22** | **Role model** | **Open** | Adopt the v2.2 five-role matrix (migration: add `data_contributor`, `viewer`; map `commercial_analyst` → `analyst`), or CRQ to keep three roles. | BNCS-PA · — | Ajendra reviews; Abhishek and Vishal implement. |
| **D-23** | **Controlled reference values and Buyer Organisation** | **Open** | Adopt v2.2 §5.1 codes (category, supplier type, unit, outcome, eligibility, disposition), capacity period week/month/quarter, and a separate Buyer Organisation object, or CRQ. | BNCS-PA · — | Vishal (models and migration), Abhishek (serializers), Adrika (field dictionary). |
| **D-24** | **Opportunity pipeline (M8) in MVP scope** | **Open** | v2.2 Must scope and build order stop at disposition and history; the build manual and MVP_FEATURES include M8 and Gate 3 requires it. Confirm whether M8 stays. | BNCS-PVL · — | Affects Gate 3 content and Week 6 plan. |
| **D-25** | **Approver of record and change control** | **Open** | Confirm that the v2.2 Product Authority (VBD + CPO) is the approver for scope and business rules, and adopt the CRQ process (§15.3) for every deviation. | BNCS-PS · — | Needed so D-21 to D-24 can be closed. |

### 1.2 Technical decisions

Full reasoning is in [ARCHITECTURE.md §9](../ARCHITECTURE.md#9-technical-decision-record); build-manual deviations awaiting approval are in [§10](../ARCHITECTURE.md#10-build-manual-deviations-and-pending-approvals).

| ID | Decision | Status | Note |
|---|---|---|---|
| D-01 | Stack: Next.js + Django/DRF + PostgreSQL 17/pgvector + FastAPI engine + Compose | **Implemented; approval pending** | Django instead of Spring Boot needs BNCS + mentor approval (§10). Not recorded. |
| D-10 | Evidence uploads | Resolved | Metadata only; upload is a *Should* only if secure storage is approved (v2.2 §3). |
| D-11 | Embedding library and model | **Open** | Library: `sentence-transformers` (optional install). Model: **not recorded.** `.env.example` names one (selected by Alok on 19 Nov). It needs Ajendra's review and a §9 record, or removal (AUD-07). Non-blocking if D-21 adopts rules-only. |
| D-12 | Authentication and provisioning | Resolved — **defects open** | Session auth + CSRF; admin-provisioned accounts; no self-registration. **AUD-01**: an open `register/` endpoint breaks this. **AUD-15**: admin-created users get plaintext passwords. |
| D-16 | Staging | Selected; BNCS confirmation pending | Compose is the demo and UAT environment. |
| D-17 | Results after data changes | Resolved | Runs immutable; matches v2.2 AC-18, AC-21. Not built yet. |
| D-18 | Tracking tool | Resolved | GitHub Issues + Projects. |
| D-20 | LLM | **None in v0.1** | Any future use is the optional, isolated §14.2 experiment after Must scope passes, with a §9 entry, Ajendra's review and BNCS approval. |
| TD-01 | Vector storage | Resolved (design); not built | pgvector column added only after D-11. This replaces the "D-12 vector storage" label once used in ARCHITECTURE §6.3. |
| TD-02 | Matching boundary | Resolved | Django owns data and persistence; the engine never touches the database. |
| TD-03 | Audit immutability | Resolved, implemented | App has no update/delete path; migration `audit/0002_enforce_audit_immutability.py` adds the trigger. |
| TD-04 | Login throttling | **Open** | Previously recorded as "baseline throttling applied". No throttle settings exist in `config/settings.py`. Ajendra to decide. |
| TD-05 | Login CSRF | Resolved, implemented | Verified in the audit smoke test. |
| TD-06 | 401 vs 403 | Resolved, implemented | Verified: anonymous `/auth/me/` → 401 `not_authenticated`. |
| TD-07 | SPA catch-all | Superseded by TD-09 | |
| TD-08 | First administrator | Resolved, implemented | `create_platform_admin`; Compose bootstrap from `INITIAL_ADMIN_*`. Verified. |
| TD-09 | Single origin through Next.js | Resolved, implemented | Verified: `/api/*`, admin and static proxied; unknown `/api/*` returns Django JSON 404. |
| TD-10 | Next.js rendering boundary | Resolved — **check AUD-11** | `middleware.ts` cookie-presence redirect to be accepted as UX-only or removed. |
| **TD-11** | **FastAPI engine runtime** | **Implemented; mentor confirmation pending** | Separate `matching` Compose service on the internal network (`http://matching:8001`). Previously mislabelled "D-15" in AGENTS, ARCHITECTURE and this register. |

### 1.3 Pending decisions — escalation list

This is the list Aryan takes to BNCS. Order = urgency.

| # | ID | Question | Approver | Needed by | Blocks |
|---|---|---|---|---|---|
| 1 | D-21 | Rules-only matching per v2.2, or CRQ for semantic hybrid? | BNCS-PA, Mentor | Mon 23 Nov | Week 5 matching (M6, M7) |
| 2 | D-25 | Confirm VBD + CPO as approver of record; adopt CRQ process | BNCS-PS | Mon 23 Nov | Closing D-21 to D-24 |
| 3 | D-22 | Five roles per v2.2, or CRQ for three? | BNCS-PA | Mon 23 Nov | Disposition permissions, AC-06, AC-22, SEC-01/02 |
| 4 | D-23 | v2.2 controlled values and Buyer Organisation, or CRQ? | BNCS-PA | Tue 24 Nov | Category rule (§9.2 rule 2), demo dataset |
| 5 | D-24 | Opportunity pipeline (M8) in or out of MVP? | BNCS-PVL | Wed 25 Nov | Week 6, Gate 3 |
| 6 | Gate 2 | Record the 20 Nov Gate 2 outcome, approver and conditions | Aryan records; BNCS / Mentor confirm | Mon 23 Nov | Gate evidence trail |
| 7 | D-19 | Approve revised dates and final acceptance date | BNCS-PS + University Coordinator | Overdue | Gate dates |
| 8 | D-01 | Approve Django instead of Spring Boot (§10) | BNCS + Mentor | Overdue | Formal stack acceptance |
| 9 | TD-11 | Confirm FastAPI engine as a separate service | Mentor | Week 5 | — |
| 10 | D-11 | Record or remove the embedding model named in `.env.example` | Team + Ajendra (BNCS if used) | Before any semantic work | — |
| 11 | TD-04 | Login throttling | Ajendra | Week 5 | Gate 4 security evidence |
| 12 | D-16 | Hosted staging optional | BNCS | Week 6 | — |
| 13 | D-07 | Opportunity stages (if M8 stays) | BNCS-PVL | Week 5 | M8 |
| 14 | D-20 | LLM / optional AI experiment | BNCS | Week 7 at earliest | — |

---

## 2. Risk register

| ID | Category | Risk | Impact | Likelihood | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|
| RSK-01 | Governance | Revised timeline (D-19) never formally approved | High | Medium | Raise weekly; plan against both calendars | Aryan | Open |
| RSK-02 | Scope | v2.2 conflicts with the built architecture (matching, roles, values) cause Week 5 rework | **High** | **High** | Decide D-21 to D-23 on 23–24 Nov; rules engine first | Aryan, Alok, Abhishek | **New** |
| RSK-03 | Security | Anonymous privilege escalation through `register/` (AUD-01); plaintext passwords for admin-created users (AUD-15) | **Critical** | Confirmed | Remove or lock the endpoint; use Django `UserAdmin` forms; negative tests; retest | Abhishek, Ajendra | **Open** |
| RSK-04 | Quality | Implemented modules without backend tests (readiness, demand); CI does not run matching tests | High | High | Add tests and CI jobs in Week 5 | Abhishek, Harish, Alok | Open |
| RSK-05 | Integration | M6–M9 APIs not built; six working days to Gate 3 | High | High | Weekly integration plan ([INTEGRATION_PLAN §4](INTEGRATION_PLAN.md#4-week-5-and-week-6-integration-sequence)); D-24 to trim scope | Aryan | Open |
| RSK-06 | Demo | No reproducible synthetic demo dataset (v2.2 §3.2, AC-25) | High | Medium | `seed_demo` in `backend/` by Week 6 | Vishal, Harish | Open |
| RSK-07 | AI / data | Embedding model named in config without D-11 review; library missing from the image | Medium | Confirmed | Remove default or record D-11; decide after D-21 | Alok, Ajendra | Open |
| RSK-08 | Architecture | CSRF/proxy breakage in demos | High | Low | Single-origin proxy verified on 21 Nov | Priyanka, Abhishek | Mitigated |
| RSK-09 | Contract | Stale OpenAPI and generated frontend types | Medium | Confirmed | Regenerate; add CI drift check | Abhishek, Harish | Open |
| RSK-10 | Compliance UX | UI shows "Verified" and percentage scores that v2.2 forbids | High | Confirmed | Remove before Gate 3 | Priyanka | Open |

---

## 3. Issue register

QA defects keep their QA IDs (`docs/qa/defects.md`). Audit findings use `AUD-xx` (details in the [audit](AUDIT_2026-11-21.md#4-findings-register)).

| ID | Sev. | Module | Issue | Owner | Raised | Resolved in | Status |
|---|---|---|---|---|---|---|---|
| QA-001 | High | M1 | Unauthenticated workspace rendered an empty shell before redirecting | Priyanka | Week 3 | PR #75 (`middleware.ts` 307 redirect) | Closed (retest by Harish pending) |
| QA-003 | Medium | M3 | Product price accepted without currency | Abhishek | Week 3 | PR #70 | Closed |
| QA-005 | Medium | M1 | CSRF failure returned HTML instead of JSON 403 | Abhishek | Week 4 | PR #70 | Closed |
| QA-006 | Medium | API | Unmatched `/api/` returned HTML 404 | Abhishek | Week 4 | PR #70; verified 21 Nov | Closed |
| QA-007 | Low | M4 | `status` / `workflow_state` aliasing for the frontend | Abhishek, Priyanka | Week 4 | PR #77 | Closed |
| QA-008 | Medium | M6 | Engine `/match` refuses to score with `v0-UNAPPROVED` criteria | Alok | Week 4 | — | Open (depends on D-21) |
| **AUD-01** | **Critical** | M1 | Anonymous self-registration as `platform_admin` | Abhishek | 21 Nov | — | **Open** |
| AUD-15 | High | M1 | Django admin "Add user" stores plaintext passwords; `is_superuser` editable | Abhishek | 21 Nov | — | Open |
| AUD-02 | High | M6 | Matching architecture conflicts with v2.2 | Alok, Abhishek | 21 Nov | — | Open (D-21) |
| AUD-03 | High | M2 UI | "Verified" labels on Documents page (AC-09) | Priyanka | 21 Nov | — | Open |
| AUD-04 | Medium | M9 UI | Readiness % and "% Match" on dashboard | Priyanka | 21 Nov | — | Open |
| AUD-05 | High | QA | No readiness/demand backend tests; CI gaps | Abhishek, Harish, Alok | 21 Nov | — | Open |
| AUD-06 | Medium | API | Stale `docs/api/openapi.yaml`; duplicate `backend/openapi-schema.yaml` | Abhishek | 21 Nov | — | Open |
| AUD-07 | Medium | M6 | Model named in `.env.example`; library not in image | Alok | 21 Nov | — | Open |
| AUD-08 | Medium | Data | No demo dataset / `seed_demo` in `backend/` | Vishal | 21 Nov | — | Open |
| AUD-09 | Medium | M6–M9 | Matching, audit, dashboard, opportunity APIs absent | Vishal, Abhishek, Alok | 21 Nov | — | Open (Week 5–6 plan) |
| AUD-10 | Low | Docs | Stale owner documents | Owners | 21 Nov | — | Open |
| AUD-11 | Low | Frontend | `middleware.ts` vs TD-10 | Priyanka | 21 Nov | — | Open |
| AUD-12 | Low | QA | v2.2 AC/SEC IDs not mapped | Harish | 21 Nov | — | Open |
| AUD-13 | Low | Product | `docs/product/` and Field Dictionary v1.4 missing | Adrika | 21 Nov | — | Open |
| AUD-14 | Low | Reports | Missing weekly reports | Members | 21 Nov | — | Open |

---

## 4. Dependency register

| ID | Consumer → Provider | What is needed | Needed by | Status |
|---|---|---|---|---|
| DEP-01 | All matching work → BNCS | D-21 decision | 23 Nov | Waiting |
| DEP-02 | Abhishek (role model) → BNCS | D-22 decision | 23 Nov | Waiting |
| DEP-03 | Vishal (models) → BNCS / Adrika | D-23 decision; field dictionary in `docs/product/` | 24 Nov | Waiting |
| DEP-04 | Abhishek (match orchestration) → Vishal | `MatchRun`, `MatchResult`, disposition models storing exact input versions (AC-18) | 25 Nov | Not started |
| DEP-05 | Abhishek → Alok | Engine request/response contract aligned to v2.2 §9 (Pass/Unknown/Fail, Met X of Y) | 25 Nov | Contract `0.2.0-proposed`; awaits D-21 |
| DEP-06 | Priyanka (matching, review, dashboard, audit screens) → Abhishek | Matching, disposition, dashboard (SCR-01) and audit-history APIs plus regenerated OpenAPI | 26 Nov – 1 Dec | Not started |
| DEP-07 | Harish (E2E, AC-25) → Vishal | Synthetic demo dataset and `seed_demo` in `backend/` | 2 Dec | Not started |
| DEP-08 | Gate 4 → Ajendra | AUD-01 retest; TD-04 decision; access matrix updated for D-22 | 9 Dec | Open |
| DEP-09 | Docs → Adrika | `docs/product/` field dictionary and workflow maps aligned to v2.2 | 27 Nov | Not started |

---

## 5. Interface contract register

| ID | Contract | Consumer ↔ Provider | Real endpoints (verified 21 Nov) | Status |
|---|---|---|---|---|
| IF-01 | Auth and session | Frontend ↔ Django (`accounts`) | `GET /api/v1/auth/csrf/`, `POST /login/`, `POST /logout/`, `GET /me/`, `/api/v1/auth/users/` (admin). Also `register/`, `verify/`, `verify/status/` — **must be removed or locked (AUD-01)**. | Active; **defect open** |
| IF-02 | Supplier, product, evidence | Frontend ↔ Django (`registry`) | `/api/v1/suppliers/` (+ `{id}/complete/`, `{id}/archive/`), `/api/v1/products/`, `/api/v1/evidence/` | Active |
| IF-03 | China-readiness assessment | Frontend ↔ Django (`readiness`) | `/api/v1/assessments/` (+ `criteria/`, `{id}/submission-gate/`, `{id}/submit/`, `{id}/request-information/`, `{id}/complete-review/`), `/api/v1/assessment-evidence/` | Active; **missing from committed OpenAPI (AUD-06)** |
| IF-04 | Buyer requirement | Frontend ↔ Django (`demand`) | `/api/v1/requirements/` (+ `{id}/mark-ready/`, `{id}/close/`) | Active; values to align under D-23 |
| IF-05 | Matching engine | Django (`apps/matching/integrations/ai_engine_client.py`) ↔ FastAPI (`ai_matching`) | `GET http://matching:8001/health`, `POST http://matching:8001/match` | Engine contract `0.2.0-proposed`; Django side has no API yet; awaits D-21 |
| IF-06 | Audit events | Django apps ↔ `audit` | `apps.audit.services.record_event()` (internal) | Active; no read API yet (SCR-07) |
| IF-07 | Dashboard | Frontend ↔ Django (`dashboard`) | Planned per SCR-01 | Not built |
| IF-08 | Match run, results, disposition | Frontend ↔ Django (`matching`) | Planned per SCR-05, SCR-06 | Not built |

---

## 6. Change request log (v2.2 §15.3)

A change request states the problem, proposed change, affected requirements, fields, screens, tests, security impact, effort and sprint impact. Aryan records it here. **No one implements it until the Product Authority marks it Approved.** Rejected or deferred requests stay in this log.

| ID | Raised | Title | Affects | Decision | Authority · date |
|---|---|---|---|---|---|
| — | — | No change requests raised yet. D-21 to D-23 become CRQ-001 to CRQ-003 if BNCS chooses to keep current behaviour instead of adopting v2.2. | — | — | — |

---

## 7. Gate register

| Gate | Date (revised) | Exit focus | Evidence in repo | Recorded outcome |
|---|---|---|---|---|
| Gate 1 | Fri 6 Nov 2026 | Authorised user signs in, creates and retrieves a supplier and product end-to-end | Backend accounts/registry tests; [QA integrated execution, 16 Nov](../qa/execution-2026-11-16-integrated.md); audit smoke test 21 Nov | Demonstrated. **No signed gate record in `docs/governance/`**; to be added with approver. |
| Gate 2 | Fri 20 Nov 2026 | Fields, rules, criteria and interfaces approved before AI integration | v2.2 (16 Nov) supplies the rule baseline; M4 and M5 APIs live; review held 20 Nov (Aryan's report) | **Outcome not recorded.** Open conditions: D-21 to D-25, AUD-01. |
| Gate 3 | Fri 4 Dec 2026 | Priority journey works from access through audit review; feature freeze | — | Scheduled |
| Gate 4 | Fri 11 Dec 2026 | Critical issues closed; UAT, regression and residual-risk evidence | — | Scheduled. AUD-01 must be closed. |
| Gate 5 | Fri 18 Dec 2026 | BNCS can run the demo, review evidence and continue the build | — | Scheduled |

---

## 8. Source discrepancy register

**DS-01 to DS-16 are defined in [MVP_FEATURES.md §11](../MVP_FEATURES.md#11-source-document-discrepancies)** and are not repeated here. The previous version of this register carried a different, conflicting DS list (for example its DS-03 and DS-05 had no basis in §11); that list is withdrawn. Discrepancies introduced by Baseline v2.2:

| ID | Documents | Discrepancy | Resolution |
|---|---|---|---|
| DS-17 | v2.2 §1, §3, §9 vs build manual §7 / ARCHITECTURE §6 | Rules-only, no weights, AI optional vs "bounded semantic signal" and mandatory semantic hybrid scoring | v2.2 governs its portion. Decide under D-21. |
| DS-18 | v2.2 §4 vs build manual §2 | Five roles vs three | v2.2 governs. D-22. |
| DS-19 | v2.2 §3, §15.2 vs build manual / MVP_FEATURES M8 | No opportunity pipeline in v2.2 Must scope | v2.2 is silent; D-24. |
| DS-20 | v2.2 §4.1 role names vs revised ownership | v2.2 names generic intern functions ("Project Manager Intern", "Data and AI Intern", "QA and Integration Intern"), not people | Revised ownership PDF governs people and roles (AGENTS.md §C). Map: Project Manager → Aryan; Product UX → Adrika; Frontend → Priyanka; Backend → Abhishek **and** Vishal (data model); Data and AI → Alok; Cybersecurity → Ajendra; QA and Integration → Harish. |
| DS-21 | v2.2 §2.2 vs `demand` model | Buyer Organisation as its own versioned-independently object vs a name field on the requirement | v2.2 governs. D-23. |
