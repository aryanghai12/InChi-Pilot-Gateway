# InChi Pilot Gateway v0.1 — MVP Feature Specification

| | |
|---|---|
| **Status** | Working baseline for team and BNCS review. Business rules marked [OPEN] await BNCS. The technology stack and technical decisions are **final**: see [`ARCHITECTURE.md`](ARCHITECTURE.md). |
| **Prepared** | 28 October 2026 (revised Week 1) |
| **Maintained by** | Aryan Ghai (coordination and change record). Requirement content: Adrika T Kumar. Material changes need BNCS approval. |
| **Applies to** | Every contributor and every AI coding agent working in this repository. See [`../AGENTS.md`](../AGENTS.md). |

## How to read this document

Every statement is one of four kinds. Where it matters, it is tagged:

| Tag | Meaning |
|---|---|
| **[SRC]** | Set by the project source documents listed below. |
| **[REC]** | Recommended by the feature audit (28 Oct 2026). Recommendations that touch scope or business rules need BNCS confirmation. Purely technical recommendations are decided in [ARCHITECTURE.md](ARCHITECTURE.md). |
| **[REPO]** | Checked against this repository. |
| **[OPEN]** | Needs a business decision from BNCS. Each one has a `D-xx` reference in [§12](#12-open-decisions). Technical decisions are resolved in [ARCHITECTURE.md §9](ARCHITECTURE.md#9-technical-decision-record). |

**Source documents reviewed** (all in [`docs/`](./)):

| File | Used for | Notes |
|---|---|---|
| `InChi_Pilot_Gateway_Build_Manual.pdf` | Scope, components, governance, AI and security rules, acceptance gates | Its role table and dates are **out of date**. See [§11](#11-source-document-discrepancies). |
| `InChi_Pilot_User_Delivery Ownership (revised).pdf` | **Source of truth for current roles** (effective 26 Oct 2026) | Page 4 of 6 of "User Journey and Build Ownership". |
| `InChi_Pilot_Build Sequence Timeline (revised).pdf` | **Current week-by-week duties and dates** (26 Oct to 18 Dec 2026) | Pages 5 to 6 of the same document. |
| `InChi_Pilot_User_Journey_Proposed.pdf` | Eight-stage journey and per-stage owners | Pages 1 to 3 of the same document. The filename says "Proposed" but the footer says "Current 26 October 2026". |
| `InChi_University_Collaboration_Internship_Program.pdf` | Programme objective, modules, AI framework, success metrics | Earlier team structure. Some module scope is broader than the manual. |
| `InChi_Mapped_Website_Feature_Blueprint.pdf` | Proposed pages, fields, states and acceptance criteria (v1.0, 27 Oct 2026) | Audited in [§9](#9-feature-blueprint-audit). |

**Not available:** `InChi_Internship_Role_Assignment_Brief.pdf` is not in the repository. The original role assignment was therefore checked only through the build manual's role table, which shows the pre-swap assignments.

**Repository state [REPO]:** as of 28 Oct 2026 the repository holds only documentation. There is no application code, build configuration, test suite or CI pipeline yet. Everything below describes **planned** functionality.

---

## 1. Purpose and target users

InChi Pilot Gateway v0.1 is a **private, controlled internal web application** for authorised BNCS Biz N Consumer Solutions Pte Ltd users [SRC]. It helps them:

- organise supplier and product information,
- assess supplier readiness for China-related market development,
- capture buyer requirements,
- get explainable, ranked supplier matches that a human reviews, and
- track the resulting commercial opportunities with a dashboard and an audit history.

It is a **supervised, demonstrable, non-production pilot**. It is not a public marketplace and not a production trade platform [SRC].

**What the pilot must prove [SRC, build manual §2]:** can an authorised BNCS user create a supplier and product, complete a China-readiness assessment, capture a buyer requirement, receive an explainable ranked match, record a human disposition, convert the outcome into an opportunity, view the dashboard and review a reliable audit history, without the platform presenting AI output as an autonomous commercial decision?

**Target users [SRC]:** internal BNCS users only, in three roles: Platform Administrator, Commercial Analyst and Reviewer/Approver. See [§5](#5-user-roles-and-permission-matrix).

**Not a public website.** The blueprint's title says "Website", but its sitemap describes the authenticated application. No public informational website or public marketplace is in scope [REC, consistent with SRC]. The login page is the only screen that unauthenticated visitors can see.

---

## 2. Scope and limitations

### In scope for v0.1 [SRC]

1. Authentication and role-based access control, enforced by the backend.
2. Supplier and product registry, with create, view, edit, search and filter.
3. A structured China-readiness assessment with missing-information indicators and human review.
4. Buyer requirement capture, separating mandatory eligibility criteria from weighted preferences.
5. Explainable matching: mandatory filters, then approved weighted scoring, then bounded semantic comparison, then explanations and warnings.
6. Human review and a recorded disposition for each match.
7. An opportunity pipeline with a small set of approved states.
8. A dashboard computed from stored records.
9. Audit history for material changes, reviews and decisions.
10. Security testing, QA, UAT evidence, documentation and a repeatable demo setup.

### Explicitly out of scope [SRC unless marked]

- Public launch, production operation, or any claim of production readiness.
- A public marketplace, public supplier self-registration, external supplier self-service, or external buyer accounts.
- Payments, escrow, transaction settlement, contracting, purchase orders, or automated negotiation.
- Legal, regulatory, tax, customs or market-entry certification or interpretation.
- A complete Mandarin user interface, or machine translation that is not reviewed.
- Real personal data, client-confidential files, production credentials, or third-party data without written approval.
- Unapproved third-party integrations, mobile apps, microservices beyond the approved baseline, or additional product modules.
- Live chat, notifications, logistics booking and marketplace mechanics [REC; blueprint §2 already flags these].

### Limitations to state openly

- Matching output is **decision support only**. Scores are not a certainty, a compliance judgement or a guarantee of commercial fit [SRC].
- Readiness criteria, eligibility rules, weights, decision labels and opportunity stages are **not yet approved** [OPEN D-03 to D-07]. Until approval, implementations must use clearly labelled placeholder configuration.
- The app uses synthetic data only. Results on synthetic data do not show performance on real data.
- The internship does not provide penetration-test certification or production security assurance [SRC].

### If delivery gets tight [REC]

This list consolidates the eight-stage journey (§3) into delivery priorities. It does **not** replace the journey, which remains the demo script and the acceptance path.

Protect the central workflow first:

1. Login and backend-enforced permissions.
2. Supplier and product records.
3. Readiness assessment and human review.
4. Buyer requirement capture.
5. Rules-based matching first, then evaluated semantic matching where feasible.
6. Human disposition and controlled opportunity creation.
7. Basic dashboard, audit history, testing and handover.

Cut extras before any of these. Items tagged **[DEFERRABLE]** in the modules below are the first to cut:

- duplicate warnings (M2-AC4),
- list pagination UI (M2, M3),
- clickable dashboard metrics (M9),
- audit filters by actor and date (M10).

Deferring one of these is recorded in the decision register by Aryan. It does not need BNCS approval, because none of them is a business rule.

Never cut:

- the underlying audit events,
- essential permission checks,
- the matching safeguards (M6-AC1, M6-AC2, M7-AC5),
- human review.

The Phase 2 list (§10) holds ideas for later, not extra obligations.

---

## 3. End-to-end user journey

From the user journey document and build manual [SRC]. Owners come from the revised ownership pages.

| # | Stage | User action | Platform response | Primary build owners | Support and control | Exit evidence |
|---|---|---|---|---|---|---|
| 1 | Access workspace | Sign in and enter a role-aware workspace | Authenticates, applies permissions, records session activity | Abhishek, Priyanka | Ajendra (access risk), Harish (allowed and denied paths) | Approved roles sign in. Denied actions fail safely and leave an audit record. |
| 2 | Register supplier and product | Create supplier and product records with supporting evidence metadata | Validates fields, stores structured data, writes an audit event | Priyanka, Abhishek, Vishal | Adrika (fields, workflow), Ajendra (data protection), Harish (CRUD, permissions) | An authorised user creates, retrieves, edits and searches a valid record. |
| 3 | Assess China readiness | Complete the assessment and resolve missing information | Applies approved rules, shows gaps, routes for review | Adrika, Priyanka, Abhishek | Vishal (evidence storage), Alok (rule design), Harish and Ajendra (quality, control cases) | The assessment produces a traceable status and blocks incomplete progression. |
| 4 | Capture buyer requirement | Record demand, eligibility conditions and priorities | Validates and versions the requirement for matching | Adrika, Priyanka, Abhishek | Vishal (data contracts), Alok (match inputs), Harish (workflow boundaries) | The approved requirement is complete, versioned and ready for matching. |
| 5 | Generate match | Run matching for an approved requirement | Mandatory filters, weighted scoring, bounded semantic comparison, ranked results, rule and model version, fallback, evaluation logging | Alok | Vishal (retrieval, storage), Abhishek (orchestration), Adrika, Ajendra, Harish (meaning, risk, quality) | Expected candidates rank correctly on test cases. Rules-only fallback stays available. |
| 6 | Review and decide | Compare candidates, inspect reasons, record a disposition | Shows explanations, warnings and missing data. Captures the human decision and reason. | Adrika, Priyanka, Abhishek | Alok (explanations), Vishal (stores inputs and decisions), Harish and Ajendra (misuse, denied access) | The user understands why candidates ranked and records a traceable decision. |
| 7 | Manage opportunity | Convert an accepted match into an opportunity | Tracks stage, owner, next action, due date and history | Priyanka, Abhishek, Vishal | Adrika (states), Harish (transitions), Aryan (integration governance) | An accepted match becomes an opportunity and moves through approved states. |
| 8 | Monitor and audit | Review dashboard status, unresolved items and audit trail | Aggregates metrics from stored records, preserves traceability | Vishal, Priyanka | Abhishek (secures queries), Harish (reconciles), Aryan (governance), Ajendra (security evidence) | Dashboard figures match source records. Audit shows who changed what and when. |

**Final demo script [SRC, build manual §10]:** stages 1 to 8 in order, plus one denied-permission case and one controlled service-failure or fallback case.

---

## 4. MVP modules

Module IDs (`M1` to `M11`) and acceptance-criterion IDs (`M2-AC3`) are stable. Use them in issues, PRs, tests and the traceability matrix.

### M1 — Authentication and role-based access

| | |
|---|---|
| **What** | Login and logout, session handling, protected routes and APIs, role-aware navigation, access-denied state, admin-managed internal users, login and denied-access events in the audit log. |
| **Why** | Stage 1. It is a precondition for every other module and for least-privilege access [SRC]. |
| **Owner** | Abhishek (auth, RBAC, object-level checks). Priyanka (login UI, route guards, role-aware navigation). Ajendra (review and negative tests). |
| **Depends on** | Permission matrix (§5, D-09), the custom `User` model with `role` (Vishal, Abhishek). |
| **Decided (D-12)** | Django session auth with CSRF. Three fixed roles, one role per user. A Platform Administrator creates and deactivates users and resets passwords in a restricted Django admin. No self-registration, email password reset or SSO. |

| ID | Acceptance criterion |
|---|---|
| M1-AC1 | A valid user of each role signs in and sees only the navigation and actions their role permits. |
| M1-AC2 | Unauthenticated requests to any protected page or API are rejected. No protected data is returned. |
| M1-AC3 | A permitted UI action that is blocked server-side returns a structured 403. Direct API calls cannot bypass role or object-level checks. |
| M1-AC4 | Deactivating a user ends their access on the next request. |
| M1-AC5 | Successful logins, failed logins and denied actions create audit events, with no passwords or tokens logged. |
| M1-AC6 | No credentials or secrets are in source control. Configuration comes from environment variables. |

**Verify:** automated allowed and denied tests per role and endpoint (Harish), a negative-test pack including object-ID tampering (Ajendra), and the demo's denied-permission case.

### M2 — Supplier registry

| | |
|---|---|
| **What** | Supplier list (search by name, filter by status, country and category, sort), create, edit and save draft, detail page with products, evidence metadata and history. **[DEFERRABLE]** pagination UI and duplicate warning. |
| **Why** | Stage 2 and Component 1 [SRC]. |
| **Owner** | Priyanka (UI), Abhishek (APIs, validation), Vishal (schema, search, constraints), Adrika (fields, required-at-which-step rules). |
| **Depends on** | Field dictionary v1 (Adrika), M1, audit storage (M10). |
| **Simplifications [REC]** | No separate supplier review workflow; review happens in M4. Record status: `Draft`, `Complete` (required fields present, checked by the system) and `Archived`. **[DEFERRABLE]** Duplicate check uses normalised legal name plus country, and warns without blocking or merging. **[DEFERRABLE]** Pagination UI: if deferred, the list endpoints return a page size that covers the whole seed dataset (for example 100), and a test shows no seed records are hidden. Evidence is **metadata only** (type, description or reference, status, expiry date). File uploads are Phase 2 (D-10, resolved). Contact details are synthetic. |

| ID | Acceptance criterion |
|---|---|
| M2-AC1 | An Analyst can save a draft with only the draft-minimum fields. The record gets a stable, immutable ID and appears in the list. |
| M2-AC2 | Marking a supplier `Complete` fails with field-specific messages when required fields are missing. |
| M2-AC3 | Search and filters return the correct records on the seed dataset. An empty result shows guidance, not an error. |
| M2-AC4 **[DEFERRABLE]** | A likely duplicate (same normalised name and country) shows a warning. Nothing is merged or deleted silently. |
| M2-AC5 | Evidence status shows "provided", not "verified", unless a reviewer has recorded verification. |
| M2-AC6 | Each create, edit, status change and archive writes an audit event with actor, time and changed fields. |
| M2-AC7 | Saving over a newer version is rejected with a conflict message. Nothing is silently overwritten. |

**Verify:** API and UI tests on the seed data, plus audit-event assertions.

### M3 — Product catalogue

| | |
|---|---|
| **What** | Products linked to one supplier. List with search and filter. Create, edit, detail. Core commercial fields (category, description, MOQ with unit, indicative price range with currency, capacity with unit, lead time, certifications). |
| **Why** | Stage 2. Products are the matching candidates [SRC]. |
| **Owner** | Same as M2. |
| **Depends on** | M2, pilot sector and category list (D-02). |
| **Simplifications [REC]** | One pilot sector with a small controlled category list. Specifications are a few typed fields plus free text; no per-category dynamic form builder. No product-level review workflow. Optional Mandarin-ready fields (name, short description) with a translation status of `Not provided`, `Provided – unreviewed` or `Reviewed` (D-14). |

| ID | Acceptance criterion |
|---|---|
| M3-AC1 | A product cannot be saved without a link to an existing supplier the user may access. |
| M3-AC2 | Numeric fields need an explicit unit or currency. Unknown values are stored and shown as unknown, never as zero or a default. |
| M3-AC3 | Product search and filters work on the seed dataset (≥30 products). |
| M3-AC4 | Mandarin-ready fields show their translation status. Unreviewed text is never labelled as verified. |
| M3-AC5 | Material product changes write audit events. |

### M4 — China-readiness assessment

| | |
|---|---|
| **What** | A fixed, versioned question set per supplier. Answers with evidence references. A computed missing-information list with corrective-action text. Submit for review. The reviewer records the outcome and reason, or returns the assessment for more information. History is kept. |
| **Why** | Stage 3 and Component 1 [SRC]. |
| **Owner** | Adrika (questions, missing-info states, criteria draft for BNCS approval), Priyanka (UI), Abhishek (workflow, transitions), Vishal (storage), Alok (rule inputs, normalisation). |
| **Depends on** | Approved readiness questions, criteria and outcome labels (D-03). M2. |
| **Simplifications [REC]** | The question set is versioned seed or configuration data, with no questionnaire-builder UI. States: `Draft`, `Submitted`, `More information required`, `Reviewed` (resubmitting moves the assessment back to `Submitted`). Three separate values: **completeness** (computed), **status** (workflow) and **outcome** (set by a human, from approved labels). No in-app policy register; Adrika keeps that as a document. |

| ID | Acceptance criterion |
|---|---|
| M4-AC1 | Submission is blocked while mandatory questions are unanswered, and the missing items are listed. |
| M4-AC2 | A complete assessment is **not** automatically "China-ready". Only a reviewer sets the outcome. |
| M4-AC3 | Only a Reviewer/Approver can record an outcome or request more information, and a reason is required. The API enforces this. |
| M4-AC4 | Resubmission keeps prior answers, review comments and outcomes in history. |
| M4-AC5 | Submitted-by, submitted-at, reviewed-by, reviewed-at, outcome and reason are stored and audited. |
| M4-AC6 | The assessment records which question-set version it used. |

### M5 — Buyer requirement capture

| | |
|---|---|
| **What** | Requirement form: buyer organisation name and market, product category, specification text, quantity and unit, target price range and currency, required certifications, delivery location and date, lead time, notes. Each criterion is marked **mandatory** or **preference**. A completeness gate before matching. Versioning. |
| **Why** | Stage 4 and Component 2 [SRC]. |
| **Owner** | Adrika (fields, rules draft), Priyanka (UI), Abhishek (APIs, versioning, gate), Vishal (storage), Alok (confirms match inputs). |
| **Depends on** | Approved eligibility criteria (D-04), buyer representation (D-13), requirement approval step (D-15). |
| **Simplifications [REC]** | Buyer details are fields on the requirement, with no buyer accounts or profiles. States: `Draft`, `Ready for matching`, `Closed`. A version number increases on each edit after `Ready for matching`, and each match run stores the version it used. |

| ID | Acceptance criterion |
|---|---|
| M5-AC1 | Mandatory criteria and preferences are visibly and structurally distinct in the UI, API and stored data. |
| M5-AC2 | A requirement cannot be marked ready, or matched, while mandatory inputs are missing. Errors are field-specific. |
| M5-AC3 | Editing a ready requirement creates a new version. Earlier match runs still reference the version they used. |
| M5-AC4 | Only criteria types from the active approved criteria version can be selected. |
| M5-AC5 | Create, edit and status changes are audited. |

### M6 — Explainable matching

| | |
|---|---|
| **What** | Run matching for a ready requirement. The pipeline is in [§7](#7-matching-process). Results are ranked eligible candidates, plus a separate list of candidates excluded or lacking data, with reasons. |
| **Why** | Stage 5 and Component 2 [SRC]. |
| **Owner** | Alok (matching engine, rules, scoring, semantic signal, explanations, evaluation, fallback), Abhishek (orchestration API, failure handling), Vishal (candidate queries, storage of runs, results and versions). |
| **Depends on** | M3, M5, approved criteria and weights (D-04, D-05). Embedding model fixed by D-11 (ARCHITECTURE.md §6). |
| **Simplifications [REC]** | Synchronous run with no job queue. Run status: `Completed`, `Completed – rules-only fallback` or `Failed`. The candidate is a product together with its supplier. Semantic comparison is English-only. |

| ID | Acceptance criterion |
|---|---|
| M6-AC1 | A candidate that fails any mandatory criterion is never ranked as eligible, whatever its preference or semantic score. |
| M6-AC2 | An unknown value on a mandatory criterion is **not** a pass. The candidate is shown as "insufficient data" with a warning. |
| M6-AC3 | Each ranked candidate shows the per-criterion result, weighted contributions, the semantic signal (labelled as such), missing-information warnings and the supplier's readiness status. |
| M6-AC4 | Zero eligible candidates is shown honestly. Ineligible candidates are never promoted to fill the list. |
| M6-AC5 | If the semantic component is unavailable, the run completes rules-only and is clearly labelled. If the matching engine raises an error, the run is recorded as `Failed`, the user sees a clear failure, and no results are stored. |
| M6-AC6 | Each run stores: run ID, actor, timestamp, requirement version, criteria/weights version, model ID and version (or "none"), mode, status and per-candidate results. |
| M6-AC7 | On the agreed evaluation set, expected candidates appear in the expected positions or bands, and the results are recorded in the AI evaluation pack. No accuracy claim goes beyond that evidence. |

### M7 — Human review and disposition

| | |
|---|---|
| **What** | For each ranked candidate, an authorised user records a disposition (proposed: `Accepted`, `Rejected`, `On hold`) with a mandatory reason. Consequential actions ask for confirmation. |
| **Why** | Stage 6. AI advises and people decide [SRC]. |
| **Owner** | Adrika (vocabulary, result language), Priyanka (UI), Abhishek (disposition API, permissions), Vishal (storage), Alok (explanations shown). |
| **Depends on** | M6, disposition vocabulary and deciding role (D-06). |
| **Simplifications [REC]** | Three outcomes plus `Pending`. "Request more information" is recorded as `On hold` with a reason. No second-reviewer step. A disposition can be changed, but only by a new audited disposition; history is never overwritten. |

| ID | Acceptance criterion |
|---|---|
| M7-AC1 | Only the approved deciding role can record a disposition. Others are blocked in the UI and the API. |
| M7-AC2 | Actor, time, outcome, reason and the run and result IDs are saved and audited. |
| M7-AC3 | The UI shows success only after the server confirms. A failed save never shows a match as accepted. |
| M7-AC4 | The system never sets a disposition automatically. |
| M7-AC5 | `Accepted` can be recorded only for a candidate marked eligible under the criteria version used by its match run. The backend rejects acceptance of `Excluded` candidates and of candidates with `Insufficient data` on a mandatory criterion. `Rejected` and `On hold` stay available for any candidate. |

### M8 — Opportunity pipeline

| | |
|---|---|
| **What** | Create an opportunity **only** from an `Accepted` disposition. Fields: owner, stage, links to supplier, product, requirement and match, next action, due date, notes and activity entries, closure outcome and reason. List view with stage, owner and blocked filters. |
| **Why** | Stage 7 and Component 3 [SRC]. |
| **Owner** | Priyanka (UI), Abhishek (API, transitions), Vishal (storage), Adrika (stages, rules). |
| **Depends on** | M7, approved stages (D-07). |
| **Simplifications [REC]** | Proposed stages: `Initial contact`, `Clarification`, `Commercial discussion`, `Closed`, plus a `Blocked` flag with reason. Closure outcome: `Won`, `Lost` or `Withdrawn`. No kanban board, RFQ, quotation, sample or PO tracking. |

| ID | Acceptance criterion |
|---|---|
| M8-AC1 | An opportunity cannot be created from a match that is not accepted, through either the UI or the API. |
| M8-AC2 | Only approved stage transitions are allowed. Each records actor and time in history. |
| M8-AC3 | Closing needs an outcome and reason. Open, blocked and closed opportunities are visually distinct. |
| M8-AC4 | The opportunity detail links back to its supplier, product, requirement and match run. |
| M8-AC5 | One accepted disposition creates at most one opportunity [REC, unless BNCS approves otherwise under D-07]. A second create attempt is rejected and points to the existing opportunity. |

### M9 — Dashboard

| | |
|---|---|
| **What** | Counts from stored records: suppliers and products by status, assessments by status and outcome, requirements by status, match runs and dispositions, opportunities by stage and blocked. A "needs attention" list (assessments awaiting review, blocked or overdue opportunities, pending dispositions). **[DEFERRABLE]** Each figure links to the filtered list behind it. |
| **Why** | Stage 8 and Component 3 [SRC]. |
| **Owner** | Vishal (reporting queries), Abhishek (dashboard API, access scoping), Priyanka (UI), Adrika (metric definitions). |
| **Depends on** | M2 to M8, metric definitions (D-08). |
| **Simplifications [REC]** | Current-state counts only. No trend charts, time-series analytics, conversion funnels or exports. |

| ID | Acceptance criterion |
|---|---|
| M9-AC1 | Every figure matches a direct query on the seed dataset (reconciled by Harish). |
| M9-AC2 | Each metric has a written definition (source, filter, exclusions). |
| M9-AC3 | No metric is fabricated or hard-coded. An empty dataset shows zeros with guidance. |
| M9-AC4 | Dashboard data respects the viewer's permissions. |

### M10 — Audit history

| | |
|---|---|
| **What** | An append-only audit event for each material action: actor, timestamp, action, object type and ID, outcome, reason where applicable, and before/after values for changed material fields. History tab on record detail pages, which is mandatory. An audit view filtered by record. **[DEFERRABLE]** Filters by actor and date range. |
| **Why** | Auditable material action is a core principle and is in every component's Definition of Done [SRC]. |
| **Owner** | Vishal (storage, immutability, queries), Abhishek (emits events from every workflow), Priyanka (history and audit views), Ajendra (integrity review). |
| **Depends on** | Built **with** M1 to M8, not afterwards [SRC]. |

| ID | Acceptance criterion |
|---|---|
| M10-AC1 | Every action listed as material in M1 to M8 produces exactly one audit event. |
| M10-AC2 | The application cannot update or delete audit events. |
| M10-AC3 | Audit events never contain passwords, tokens, secrets or unnecessary personal data. |
| M10-AC4 | Audit visibility follows the permission matrix (D-09). |

### M11 — Security, QA, documentation and demo setup

| | |
|---|---|
| **What** | Threat model, data classification, access-control matrix, secrets handling, dependency and configuration checks, negative tests, remediation register (Ajendra). Test strategy, traceability, automated regression, UAT, QA report (Harish). Containerised local setup, synthetic seed data (≥15 suppliers, ≥30 products, ≥10 requirements), demo runbook, handover packs (all owners, coordinated by Aryan). |
| **Why** | Component 4 [SRC]. Seed volumes come from the internship brief's success metrics [SRC]. |

| ID | Acceptance criterion |
|---|---|
| M11-AC1 | No critical unresolved access-control defect at final acceptance. |
| M11-AC2 | Each M1 to M10 acceptance criterion maps to at least one test or a documented manual check, with recorded results. |
| M11-AC3 | A new contributor can start the full stack locally and load seed data from the README instructions alone. |
| M11-AC4 | The demo runs end-to-end on seed data, including the denied-access and fallback cases. |
| M11-AC5 | The known-limitations register and the Phase 2 backlog exist and are reviewed by BNCS. |

---

## 5. User roles and permission matrix

### Roles [SRC: build manual §2]

| Role | Purpose |
|---|---|
| **Platform Administrator** | Manages approved internal users, their roles and the pilot configuration that is needed. |
| **Commercial Analyst** | Creates and maintains supplier, product, readiness and buyer-requirement information, and reviews match results. |
| **Reviewer / Approver** | Reviews material readiness, matching and opportunity decisions within the controlled workflow. |

The blueprint proposes a fourth role, *Read-only Auditor*. It is not in the build manual and is **not included** [REC]. Add it only if BNCS asks. No other roles are planned.

**Authentication** establishes who the user is. **Authorisation** decides what that user may do with a specific record. The **backend is the only authority** for both. The frontend hides actions only for usability.

### Proposed permission matrix [REC — confirm under D-09]

Key: **V** view · **C** create · **E** edit · **S** submit / mark ready · **R** review / decide · **M** manage · — no access

| Object / action | Platform Administrator | Commercial Analyst | Reviewer / Approver |
|---|---|---|---|
| Internal users and role assignment | V C E M (deactivate) | — | — |
| Active criteria / question-set version (read-only in UI) | V | V | V |
| Supplier records | V | V C E S (archive) | V |
| Product records | V | V C E | V |
| Evidence metadata | V | V C E | V, mark verified [OPEN] |
| Readiness assessment | V | V C E S | V R (outcome, request more info) |
| Buyer requirement | V | V C E S, close | V, approve for matching only if D-15 requires it |
| Run matching | — | C (run) | C (run) |
| Match results | V | V | V |
| Match disposition | V | Comment / recommend [OPEN] | R (record disposition) |
| Opportunity | V | V C E (stage, notes, next action) | V E, close [OPEN] |
| Dashboard | V | V | V |
| Audit history | V (all) | V (on records they can view) [OPEN] | V (all) |

Open points to confirm under D-09:

1. **Separation of duties.** Should a Reviewer be blocked from reviewing an assessment they submitted? Recommended: yes.
2. **Administrator scope.** Should the Platform Administrator be kept out of commercial edits? Recommended: yes, for least privilege.
3. **Disposition authority.** May an Analyst record dispositions, or only a Reviewer? Recommended: only a Reviewer.
4. **Audit visibility.** Who can see which audit events?

**Implementation rule until D-09 is decided.** **No entry in this matrix is BNCS-approved yet.** The table is a recommendation [REC], and `[OPEN]` marks the entries where the recommendation itself is uncertain.

- Access control is **deny-by-default**: anything not explicitly granted is refused.
- The **entire** matrix is implemented as one policy module (`backend/apps/accounts/policy.py`, ARCHITECTURE.md §5), marked `UNAPPROVED`. No role check is hard-coded anywhere else, so BNCS's decision changes one file.
- Entries without `[OPEN]` are implemented as recommended, so the journey can be built and tested. They remain `UNAPPROVED` until D-09 is recorded.
- `[OPEN]` entries and the four open points above use the most restrictive reasonable option (for example, only a Reviewer records dispositions, no self-review, Administrator has no commercial edits, Analysts see audit events only on records they can view).
- Every PR that adds or changes a policy entry lists it.
- When D-09 is recorded, Abhishek updates the policy module, removes the `UNAPPROVED` marker for approved entries, and Harish reruns the permission tests.
- The backend enforces the rules regardless of what the frontend shows.

Rules, weights and question sets have no editing UI in the MVP. They change only through versioned configuration, after BNCS approval and a reviewed PR [REC].

---

## 6. Core data entities

Requirements-level only. Vishal owns the physical schema, migrations and data dictionary. Field meanings come from Adrika's field dictionary, and engineers must not invent them [SRC].

| Entity | Key relationships | Notes |
|---|---|---|
| User | has one Role | Internal accounts only. Status active or deactivated. |
| Supplier | 1 → many Product, many EvidenceItem, many ReadinessAssessment | Record status separate from readiness outcome. |
| Product | many → 1 Supplier; may have an embedding | Explicit units and currency. Optional Mandarin-ready fields with translation status. |
| EvidenceItem | belongs to a Supplier or Product | Metadata only (D-10). "Provided" is not "verified". |
| ReadinessQuestionSet | versioned; 1 → many questions | Seed or configuration data, approved by BNCS. |
| ReadinessAssessment | many → 1 Supplier; uses one QuestionSet version; 1 → many answers and review records | Completeness, status and outcome kept separate. |
| BuyerRequirement | versioned; 1 → many Criterion; 1 → many MatchRun | Buyer organisation stored as fields (D-13). |
| Criterion | belongs to a BuyerRequirement version | Type `mandatory` or `preference`. References an approved criterion definition. |
| CriteriaVersion | referenced by MatchRun | Approved filter definitions, weights and semantic weight, with approver and date. |
| MatchRun | many → 1 BuyerRequirement version; 1 → many MatchResult | Mode, status, model version, actor, timestamp. |
| MatchResult | many → 1 MatchRun; references Product and Supplier | Eligibility per criterion, contributions, semantic signal, explanation, warnings. |
| MatchDisposition | many → 1 MatchResult (history kept) | Outcome, reason, actor, time. |
| Opportunity | created from an `Accepted` MatchDisposition | Stage, owner, next action, due date, blocked flag, outcome. |
| OpportunityActivity | many → 1 Opportunity | Notes, interactions, stage changes. |
| AuditEvent | references any material object | Append-only. |

---

## 7. Matching process

From build manual §7 *AI Governance* and the internship brief's *AI Matching Framework* [SRC]. Implementation details are [REC].

```
Ready requirement (version N) + active CriteriaVersion
        │
        ▼
1. Gate ............ requirement is Ready for matching; criteria version is approved
2. Candidates ...... non-archived products with their supplier (Vishal's candidate query)
3. Mandatory filters  each criterion → pass / fail / unknown
                      any fail    → Excluded (with reason)
                      any unknown → Insufficient data (with warning), not ranked as eligible
4. Weighted score .. approved preference criteria × approved weights → per-criterion contribution
5. Semantic signal . similarity between requirement text and product description embeddings,
                      added with an approved, bounded weight; can never override step 3
6. Rank + explain .. per-criterion results, contributions, semantic signal (labelled),
                      missing-information warnings, supplier readiness status
7. Persist run ..... versions, mode, status, results (Vishal's storage)
8. Human decision .. authorised user records disposition (M7)
```

**Rules-only fallback [SRC].** Steps 1 to 4 and 6 to 7 run without step 5. This happens when the embedding model is unavailable, disabled by configuration, or unsuitable for a given input. The run and every result are labelled `Rules-only fallback`. Fallback is a supported mode, not an error.

**Failure.** If the matching engine raises an error, the run is stored as `Failed` with no results, and the backend returns a clear error.

**Implementation (decided; see [ARCHITECTURE.md §6](ARCHITECTURE.md#6-matching-implementation)).**

- **The engine.** Matching is an in-process, pure-Python package inside the Django backend (`backend/apps/matching/engine/`). It has no Django imports, no database access and one `engine.run()` function. It is replaceable as a package, so no separate service is needed.
- **Orchestration.** The backend's service layer loads the requirement and candidates, calls the engine and persists the run.
- **Embeddings.** Stored as a PostgreSQL `real[]` column, compared with NumPy cosine similarity (no pgvector).
- **Model (D-11, resolved).** `fastembed` with `BAAI/bge-small-en-v1.5`, run locally on CPU, so pilot data never leaves the environment. Only model weights are downloaded. No external AI API and no LLM.
- **Default mode.** The semantic provider is off by default (`SEMANTIC_PROVIDER=none`, rules-only) until the Week 5 evaluation supports enabling it.

**Evaluation [SRC].** Alok and Harish build a synthetic evaluation set with expected outcomes. It covers expected matches, false matches, missed matches, missing data, manipulated input, service failure and rules-only fallback. Report results as observed on that set. Do not claim accuracy beyond it.

**Not allowed [SRC].** The AI must not approve suppliers, interpret law or regulation, set commercial policy, create opportunities, or present scores as certainty. Rules, weights and model settings are versioned and frozen after Week 7 validation.

---

## 8. Cross-cutting expectations

| Area | Expectation |
|---|---|
| **Validation** | Validate on the server; client-side validation only helps usability. Field-specific messages. Controlled values for enums, units and currency. Draft-minimum and required-at-submission rules come from the field dictionary. |
| **Errors** | One structured error format across the API (code, message, field errors, correlation ID). No stack traces or internal details sent to the client. |
| **UI states** | Every data view handles loading, empty, error, access-denied and success. Workflow views also show fallback and conflict [SRC]. |
| **Concurrency** | A version check on edits. A stale save returns a conflict and never silently overwrites. |
| **Audit** | Designed with each workflow (M10). Append-only. No secrets in logs. |
| **Security** | Least privilege. Object-level authorisation on every record endpoint. Negative tests from Week 2. Secrets only in environment variables or approved secret storage, with `.env` files git-ignored. Dependency and configuration checks with tracked remediation. The threat model covers broken access control, insecure direct object access, session abuse, unsafe input, prompt or input manipulation, data leakage and insecure configuration [SRC]. |
| **Data** | Synthetic or explicitly approved data only. No real personal data, identity documents or production credentials [SRC]. |
| **Accessibility** | Keyboard use, labels, contrast, focus, readable responsive layouts [SRC]. |
| **Testing** | Unit tests next to the code, owned by the component owner. Integration and API tests for every endpoint, including denied paths. A small end-to-end suite for the demo journey. Regression runs before each Friday review. |
| **Development AI** | Contributors stay accountable for AI-generated output. Do not paste confidential material into public AI services [SRC]. |

---

## 9. Feature blueprint audit

Audit of `InChi_Mapped_Website_Feature_Blueprint.pdf` (v1.0, 27 Oct 2026) against the build manual, the internship brief, the revised journey, ownership and timeline, and the repository. All decisions are **[REC]**.

**Overall finding.** The blueprint is careful about scope. It already rules out a public marketplace, checkout, payments, chat and logistics, and it labels unapproved rules as open. Its main risk is **breadth**: nine navigation areas, a seven-state assessment workflow, separate review workflows for suppliers and products, notifications, exports, an in-app policy register, a board view and a fourth role. Together these would roughly double the screens and transitions without adding to what the pilot must prove. It also uses the superseded 19 Oct to 11 Dec dates.

| # | Blueprint feature (section) | Decision | Rationale |
|---|---|---|---|
| 1 | Public informational website (implied by the title) | **REMOVE FROM MVP** | No source requests a public site. The pilot is a private internal application. The only unauthenticated screen is login. |
| 2 | Secure login/logout, role-aware navigation, backend-enforced permissions (§4) | **KEEP** | Stage 1 and a core principle. → M1 |
| 3 | Fourth role "Read-only Auditor" (§4, US-06) | **REMOVE FROM MVP** | Not in the build manual. Reviewer and Admin can view audit history. Add only if BNCS asks. |
| 4 | Nine-section left navigation (§2) | **SIMPLIFY** | Use Dashboard, Suppliers (with products), Readiness, Requirements, Matching, Opportunities, Audit, and Users (Admin only). "Reports" merges into Dashboard. |
| 5 | Top bar notifications and task indicator (§2) | **DEFER TO PHASE 2** | Needs a notification model. The dashboard's "needs attention" list covers the pilot. |
| 6 | Help navigation, Pinduoduo-style rules pages (§2, §17) | **SIMPLIFY** | Inline field guidance and help text only. |
| 7 | Loading, empty, error, denied and success states for every view (§4, §15) | **KEEP** | Required by the build manual's UX section. |
| 8 | Dashboard task queue and metric filters (§4, §12) | **SIMPLIFY** | Current-state counts plus a "needs attention" list. No time windows, trends or charts. → M9 |
| 9 | Supplier list with search, filters, sort and pagination (§5) | **KEEP** (bounded) | Component 1 DoD. Keep the filters few. The pagination UI is deferrable. → M2 |
| 10 | Save draft (§5, US-01) | **KEEP** | Cheap, and stops incomplete data looking complete. |
| 11 | Evidence/documents section with uploads (§5, §6) | **SIMPLIFY** | Metadata only (type, reference, status, expiry). File upload adds storage, malware and access-control risk. Resolved under D-10; uploads are Phase 2. |
| 12 | Separate supplier and product review workflows with review history (§5, §6, §14) | **SIMPLIFY** | Review happens once, at the readiness assessment. Supplier and product use Draft, Complete and Archived. Removes two review queues. |
| 13 | Extended company fields such as address, registration reference and contact (§5, §13) | **SIMPLIFY** | Keep only fields that matching, readiness or the demo need. Contact data stays synthetic. Adrika confirms. |
| 14 | Duplicate warning (§5) | **SIMPLIFY** | Normalised name and country check, warning only. No merge tool. |
| 15 | Category-specific conditional product fields (§6) | **SIMPLIFY** | One pilot sector (D-02), a few typed fields plus text. No dynamic form engine. |
| 16 | Product re-review triggers (§6) | **REMOVE FROM MVP** | There is no product review workflow once #12 is simplified. |
| 17 | Readiness questionnaire, missing-info list, corrective actions (§7) | **KEEP** | Stage 3 and Component 1. → M4 |
| 18 | Seven-state assessment workflow (§7, §14) | **SIMPLIFY** | Four states: Draft, Submitted, More information required, Reviewed. Resubmission returns to Submitted, so "Resubmitted" and "Under review" add nothing. |
| 19 | Four separate concepts: completeness, progress, outcome, review status (§7) | **SIMPLIFY** | Three: completeness (computed), status (workflow), outcome (human). Progress is the status. |
| 20 | "Configurable questionnaire" (journey, stage 3) | **SIMPLIFY** | Versioned seed or configuration data. No builder UI. |
| 21 | In-app China-market policy register (§7, §22) | **DEFER TO PHASE 2** | Valuable, but as a maintained document now (Adrika). Building it in-app is a separate product. |
| 22 | Buyer requirement with mandatory vs preference criteria (§8) | **KEEP** | Component 2 DoD. → M5 |
| 23 | Requirement owner assignment (§8) | **SIMPLIFY** | Owner defaults to the creator and can be edited. No assignment workflow. |
| 24 | Requirement versioning after matching (§8) | **KEEP** (simple) | Needed for traceable runs. A version number plus the stored version on each run. |
| 25 | Matching run status: queued, running, completed, failed, partial, fallback (§9, §14) | **SIMPLIFY** | Run synchronously: Completed, Completed – rules-only fallback, Failed. A queue is unnecessary at pilot volume. |
| 26 | Ranked candidates with eligibility, score, explanation, evidence links, warnings (§9) | **KEEP** | The core of the pilot. → M6 |
| 27 | Honest zero-results; distinguish ineligible, not assessed, insufficient data (§9) | **KEEP** | Prevents false confidence. → M6-AC2, AC4 |
| 28 | Run record with versions (§9) | **KEEP** | Build manual AI governance. → M6-AC6 |
| 29 | Side-by-side candidate compare view (§2, §10) | **SIMPLIFY** | A score breakdown per candidate in the results view. Multi-select compare goes to Phase 2. |
| 30 | Disposition: accept, reject, hold/defer, request more info (§10) | **SIMPLIFY** | Accepted, Rejected, On hold, each with a reason. "Request info" is On hold with a reason. Vocabulary under D-06. |
| 31 | Confirmation for consequential actions; success only after server confirms (§10) | **KEEP** | Cheap, and prevents false states. |
| 32 | Second reviewer for some transitions (§14 question) | **DEFER TO PHASE 2** | Not required by the sources. |
| 33 | Opportunity only from an approved match; owner, stage, links, next action, outcome (§11) | **KEEP** | Component 3 DoD. → M8 |
| 34 | Interaction history (§11) and the internship brief's RFQ, sample, quotation, negotiation and PO tracking | **SIMPLIFY** | Activity notes (date, type, summary). No commercial-document tracking. |
| 35 | Opportunity board/kanban view (§11) | **SIMPLIFY** | A list with stage and blocked filters. A board is Phase 2. |
| 36 | Audit event with before/after; protected from silent editing (§12) | **KEEP** | Core principle. → M10 |
| 37 | Searchable audit (§12) | **SIMPLIFY** | Filter by record. Actor and date filters are deferrable. |
| 38 | Approved exports (§2) | **DEFER TO PHASE 2** | Not required to prove the journey. Adds data-leakage review. |
| 39 | English and Mandarin-ready fields with translation status (§12) | **SIMPLIFY** | A few optional Mandarin fields on supplier and product, with a status. No machine translation. D-14. |
| 40 | Bilingual "Profile Preview" page (internship brief module; Week 6) | **DEFER TO PHASE 2** | The build manual promises Mandarin-ready fields, not a bilingual presentation. Fields show on the detail page. Discrepancy DS-08. |
| 41 | Admin: users and roles (§12) | **KEEP** | Platform Administrator role. → M1 |
| 42 | Admin: edit reference data and criteria versions (§2, §12) | **SIMPLIFY** | Read-only display of the active version. Changes go through reviewed configuration after approval. |
| 43 | Admin: system status page (§2) | **REMOVE FROM MVP** | A developer health endpoint is enough. Not a user need. |
| 44 | Concurrent-edit warning (§15) | **SIMPLIFY** | Optimistic version check, then a conflict message. |
| 45 | Field dictionary with 18 tracked columns (§13) | **SIMPLIFY** | Start with entity, field, API name, type, required-at, allowed values, validation, sensitivity, owner and approval status. Add columns when needed. |
| 46 | Marketplace inspiration: Alibaba, Tmall Global, Pinduoduo patterns (§17) | **REMOVE FROM MVP** (as features) | Useful only as UX reference. Do not copy marketplace mechanics, fees or trust badges. |
| 47 | Error and exception catalogue (§15) | **KEEP** | Drives UI states and tests. |
| 48 | Sample user stories (§16) and UAT checklist (§21) | **KEEP** | Seed for traceability and UAT. UAT-16 (translation) applies only to the simplified fields. |
| 49 | Containerised local setup and non-production staging (§18) | **KEEP** local; hosted staging optional (D-16) | A repeatable local setup is required for handover. The Docker Compose reference environment is the demo and UAT environment. Hosted staging is used only if BNCS provides a host. |
| 50 | Phase 2 candidates listed in the blueprint (§23) | **DEFER TO PHASE 2** | Already labelled as post-approval. Carried into §10. |

---

## 10. Phase 2 candidates

Not commitments. Each needs BNCS approval, an owner and an effort trade-off [SRC: build manual §8, §11].

- External supplier self-service onboarding and document submission.
- Public or partner supplier discovery portal; public informational website.
- Evidence file upload with malware scanning and document access control.
- A separate matching service or vector database, if candidate volumes grow well beyond pilot scale (ARCHITECTURE.md TD-01, TD-02).
- In-app China-market policy register with versioned sources.
- Bilingual profile preview, translation management, bilingual or multilingual semantic search.
- Notifications for pending reviews, stale records and document expiry.
- Side-by-side candidate comparison; opportunity board view.
- Second-reviewer approvals; configurable workflow rules.
- Admin UI for question sets, criteria and weights (with approval workflow).
- Trend analytics, conversion funnels and approved exports.
- Commercial-document tracking (RFQ, sample, quotation, PO).
- Read-only Auditor role.
- Approved trade, customs, logistics, regulatory, CRM or communication integrations, after security and data-governance review.

---

## 11. Source document discrepancies

| ID | Affected documents | What each says | Practical impact | Recommendation |
|---|---|---|---|---|
| **DS-01** | Build manual §4 to §6 vs revised ownership | The manual makes **Ajendra** the Technical Project Coordinator and **Aryan** the Cybersecurity and DevSecOps Engineer, and names them that way in every weekly duty, the meeting rules and the review process. The revised ownership (effective 26 Oct 2026) **swaps them**. All other roles are unchanged. | Anyone reading the manual's weekly tables gets the wrong owner for coordination and security. | **Resolved by the revised document.** Read the manual's "Ajendra" coordination duties as Aryan's and its "Aryan" security duties as Ajendra's. AGENTS.md uses the revised roles only. Keep the manual unedited as a historical source. |
| **DS-02** | Build manual §5, blueprint §20 vs revised timeline | Manual and blueprint: 19 Oct to 11 Dec 2026, feature freeze after 27 Nov. Revised: 26 Oct to 18 Dec 2026, Week 6 (feature freeze) ends 4 Dec. | Gate dates move by one week. The blueprint roadmap is out of date. | Use the revised dates (§13). BNCS should confirm that final acceptance is 18 Dec. Adrika should update the blueprint roadmap. |
| **DS-03** | Build manual §5 vs revised timeline | Manual: Week 3 is registry and profile quality, Week 4 is readiness plus buyer demand. Revised: Week 3 is registry plus China-readiness, Week 4 is buyer demand plus the rule-approval gate. | Readiness work starts a week earlier relative to the restart. | Follow the revised sequence. |
| **DS-04** | Internship brief vs build manual and revised ownership | The brief has a "Full Stack Integration Engineer" and a "Backend and Data Engineer". The manual and the revised ownership have "Application Backend and Access-Control" and "Data and Platform Services", and state there is no separate full-stack integrator. | Integration ownership is shared, not held by one person. | Follow the revised ownership. Integration responsibilities are set out in AGENTS.md. |
| **DS-05** | Blueprint §4 vs build manual §2 | The blueprint proposes a fourth role, "Read-only Auditor". | Extra RBAC scope. | Exclude unless BNCS requests it (§5). |
| **DS-06** | Internship brief, user journey, build manual Week 5, blueprint §10 | Disposition labels differ: approve/reject/defer; accept/hold/reject; approve/reject/defer/request; accept/reject/hold/request info. | Inconsistent UI, API and test vocabulary. | Decide under D-06. Proposed: Accepted, Rejected, On hold. |
| **DS-07** | Internship brief vs blueprint §11 vs manual | The brief lists introductions, meetings, RFQs, samples, quotations, negotiations, POs and outcome. The blueprint has five illustrative stages. The manual says "approved states". | Risk of a long pipeline with document tracking. | A small stage set (§4, M8). Decide under D-07. |
| **DS-08** | Internship brief (Profile Preview module; Week 6 "controlled bilingual supplier profile") vs build manual §2 | The brief implies a bilingual presentation. The manual allows only structured Mandarin-ready fields and promises no bilingual interface. | Possible scope creep into translation. | Follow the manual. The preview page is Phase 2. |
| **DS-09** | Internship brief Week 4 ("buyer profiles") vs manual and journey | The brief mentions buyer profiles. The manual and journey mention only buyer requirements. | A possible extra entity and screens. | Buyer organisation as fields on the requirement. Decide under D-13. |
| **DS-10** | Internship brief Week 2 ("in staging") vs build manual Week 6 (staging) | Different staging timing. | Infrastructure effort in Week 2. | Local containerised setup is the reference environment. Hosted staging is optional (D-16, resolved). |
| **DS-11** | Internship brief AI framework ("multilingual terminology") vs build manual ("bounded semantic comparison") | The brief suggests multilingual semantic matching. | Model and evaluation scope. | English-only semantic signal in the MVP. Multilingual is Phase 2. |
| **DS-12** | Internship brief ("verification status" on buyer requirements) | What is being verified, and by whom, is not defined anywhere. | Unclear field. | Decide under D-13 or D-15. Do not implement until defined. |
| **DS-13** | Internship brief ("one pilot sector") | The sector is never named. | Blocks the category list, seed data and filter design. | Decide under D-02 urgently (Week 1). |
| **DS-14** | User journey PDF filename vs footer | The filename says "Proposed". The footer says "Current 26 October 2026", and it shares a page sequence with the revised ownership and timeline. | Status unclear. | Treat as the current working journey. Aryan confirms with BNCS. |
| **DS-15** | Build manual §7 | The stack is a "recommended baseline … subject to BNCS and appointed technical-mentor approval". | Engineers cannot be sure which stack to scaffold. | **Resolved (D-01).** The team selected a simpler stack (Django + DRF, PostgreSQL, in-process matching, Vite React SPA). Rationale in ARCHITECTURE.md §2; shared with the mentor for visibility. |
| **DS-16** | `InChi_Internship_Role_Assignment_Brief.pdf` | Not in the repository. | The original assignment cannot be checked directly. | Add it to `docs/` if available. It does not change current roles, because the revised ownership governs. |

---

## 12. Open decisions

Aryan records each decision in the decision register with its approver and date.

### Business decisions awaiting BNCS

These are business-owned. Until one is decided, implement only reversible placeholders, clearly labelled `UNAPPROVED`.

| ID | Decision | Approver | Needed by | Recommendation [REC] |
|---|---|---|---|---|
| D-02 | Pilot sector and product category list | BNCS Product Lead | Week 1 | One sector, at most about 10 categories. |
| D-03 | Readiness questions, criteria and outcome labels | BNCS | Week 3 (build), Week 4 gate | Adrika drafts. Outcomes are human-set. |
| D-04 | Mandatory eligibility criteria and handling of unknown values | BNCS | Week 4 gate | Start from the brief's list. Unknown is not a pass. |
| D-05 | Weighted preference criteria, weights and the semantic signal weight | BNCS | Week 4 gate | A small set, a bounded semantic weight, versioned. |
| D-06 | Disposition vocabulary, deciding role, reason required | BNCS | Week 4 | Accepted, Rejected, On hold. Reviewer decides. Reason always required. Accepted only for eligible candidates (M7-AC5). |
| D-07 | Opportunity stages, transitions, closure outcomes, who can close | BNCS | Week 5 | As in M8. One opportunity per accepted disposition (M8-AC5). |
| D-08 | Dashboard metric definitions | BNCS | Week 5 | Current-state counts as in M9. |
| D-09 | Permission matrix: who may do what, separation of duties, audit visibility | BNCS; Ajendra reviews | Week 2 | As in §5. The **enforcement mechanism** (deny-by-default, backend-enforced, `UNAPPROVED` entries isolated in one module) is already decided. |
| D-13 | Meaning of buyer "verification status" | BNCS | Week 4 | Leave it out until defined. The **data shape** is decided: buyer details are fields on the requirement, with no buyer accounts. |
| D-14 | Which Mandarin-ready fields | BNCS | Week 3 | Supplier and product name and short description only. |
| D-15 | Does a Reviewer approve a requirement before matching? | BNCS | Week 4 | No. The completeness gate is enough for the pilot. |
| D-19 | Confirm revised programme dates and final acceptance date | BNCS + university coordinator | Week 1 | 18 Dec 2026, per the revised timeline. |

### Technical decisions — resolved 28 Oct 2026

Full reasoning is in [ARCHITECTURE.md §9](ARCHITECTURE.md#9-technical-decision-record). These are final and need no further approval. Changes go through a new ARCHITECTURE.md §9 entry.

| ID | Decision | Resolution |
|---|---|---|
| D-01 | Technology stack | Python 3.12, Django 5.2 LTS + DRF, PostgreSQL 17, in-process matching package, React + TypeScript (Vite) SPA, Docker Compose, GitHub Actions. |
| D-10 | Evidence uploads | Metadata only. Uploads are Phase 2. |
| D-11 | Embedding model | `fastembed` + `BAAI/bge-small-en-v1.5`, local. No external AI API. Rules-only by default until the Week 5 evaluation. |
| D-12 | Authentication and provisioning | Django session auth + CSRF. Admin-provisioned accounts via a restricted Django admin. |
| D-16 | Staging | The Docker Compose reference environment is the demo and UAT environment. Hosted staging is optional. |
| D-17 | Results after data changes | Runs are immutable and versioned. The UI shows "data changed since this run". |
| D-18 | Tracking tool | GitHub Issues + Projects in this repository. |

---

## 13. Timeline and acceptance gates (revised)

Week dates are from the revised timeline [SRC]. Gate dates come from applying the manual's gate structure to the revised weeks [REC; confirm under D-19].

| Week | Dates (2026) | Product target | Gate (Friday) |
|---|---|---|---|
| 1 | 26–30 Oct | Definition, architecture and delivery skeleton | — |
| 2 | 2–6 Nov | Authenticated supplier-product vertical slice | **Gate 1**, 6 Nov: login, supplier and product create, persist, retrieve, baseline audit event |
| 3 | 9–13 Nov | Supplier registry and China-readiness workflow | — |
| 4 | 16–20 Nov | Buyer demand and rule-approval gate | **Gate 2**, 20 Nov: fields, rules, criteria and interfaces approved before AI integration |
| 5 | 23–27 Nov | Explainable AI-assisted matching | — |
| 6 | 30 Nov–4 Dec | Opportunity, dashboard and **feature freeze** | **Gate 3**, 4 Dec: full journey works through audit; scope frozen |
| 7 | 7–11 Dec | Hardening, security validation and UAT | **Gate 4**, 11 Dec: critical issues closed; UAT, regression and residual-risk evidence |
| 8 | 14–18 Dec | Demonstration, handover and Phase 2 backlog | **Gate 5**, 18 Dec: BNCS can run the demo, review evidence and continue the build |

After the Week 6 review, new features need written BNCS approval and removal of equal or greater effort [SRC].
