# InChi Pilot Gateway: Frontend Implementation Plan

**Owner:** Priyanka Singh, Frontend Web and Client-Side Integration Engineer
**Product:** InChi Pilot Gateway v0.1 (private, supervised, non-production pilot)
**Sponsor:** BNCS Biz N Consumer Solutions Pte Ltd, Singapore
**Programme window (current, post-restart):** 26 October 2026 to 18 December 2026 (8 weeks, Mon to Fri, 6 working hours per day)
**Document status:** Planning baseline, drafted 28 October 2026 (Week 1, Wednesday)

> **How to read this document.** Items marked **[Source]** come directly from the five programme documents. Items marked **[Proposed]** are my own implementation proposals, made so the plan can be executed. They need review by the Senior Technical Mentor or BNCS before being treated as approved.

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Source Reconciliation (read first)](#2-source-reconciliation-read-first)
3. [My Role, Authority and Boundaries](#3-my-role-authority-and-boundaries)
4. [Product Context the Frontend Must Respect](#4-product-context-the-frontend-must-respect)
5. [Technical Baseline and Conventions](#5-technical-baseline-and-conventions)
6. [Users, Roles and Frontend Permission Behaviour](#6-users-roles-and-frontend-permission-behaviour)
7. [Screen, Route and Journey Inventory](#7-screen-route-and-journey-inventory)
8. [Reusable Component Library Plan](#8-reusable-component-library-plan)
9. [Mandatory UI State Matrix](#9-mandatory-ui-state-matrix)
10. [Service Contract Register (Frontend View)](#10-service-contract-register-frontend-view)
11. [Weekly Plan](#11-weekly-plan)
12. [Frontend Testing Strategy](#12-frontend-testing-strategy)
13. [Accessibility, Responsiveness and Performance](#13-accessibility-responsiveness-and-performance)
14. [Frontend Security Rules](#14-frontend-security-rules)
15. [Weekly Operating Rhythm and Evidence Discipline](#15-weekly-operating-rhythm-and-evidence-discipline)
16. [Review, PR and Escalation Process](#16-review-pr-and-escalation-process)
17. [Frontend Risk Register](#17-frontend-risk-register)
18. [Definition of Done](#18-definition-of-done)
19. [Final Handover Checklist (Frontend)](#19-final-handover-checklist-frontend)
20. [My Part of the Final Demonstration](#20-my-part-of-the-final-demonstration)
21. [Open Questions to Resolve](#21-open-questions-to-resolve)

---

## 1. Purpose and Scope

### 1.1 What this document is
A week-by-week, goal-driven plan for everything I own on the InChi Pilot Gateway frontend, from the first skeleton to the final stable demo and documentation.

### 1.2 What the frontend must prove **[Source]**
An authorised BNCS user can: sign in, create a supplier and product, complete a China-readiness assessment, capture a buyer requirement, receive an explainable ranked match, record a human disposition, convert the accepted match into an opportunity, view the dashboard, and review a reliable audit history. At no point may the UI present AI output as an autonomous commercial decision.

### 1.3 My deliverables **[Source]**
| # | Deliverable | Final form |
|---|---|---|
| D1 | Working application interface | Authenticated, responsive Next.js app covering all 8 journey stages |
| D2 | Reusable component library | Documented, typed, accessible UI components |
| D3 | Frontend tests | Unit/component, integration and E2E journey tests with evidence |
| D4 | Frontend setup documentation | README, setup guide, component notes, known limits |

### 1.4 In scope for the frontend **[Source]**
- Authenticated layouts, navigation, forms, lists, dashboards, status components
- Supplier, product, readiness, buyer requirement, matching, opportunity and dashboard/audit screens
- Client-side form validation and clear error states
- Responsive layouts and reusable components
- Controlled English-first, Mandarin-ready profile preview (structured fields only)
- Client-side integration with every service contract the interface uses

### 1.5 Explicitly out of scope **[Source]**
- Public launch, production readiness claims
- Supplier self-service, public registration or public buyer access
- Payments, contracting, transaction settlement
- A complete Mandarin UI or uncontrolled machine translation
- Mobile native applications and unapproved integrations or additional modules
- Real personal data, client-confidential data, production credentials

> **Scope substitution rule:** Any new feature requires written BNCS approval **and removal of equal or greater effort**. New feature development ends after the Week 6 Sprint Review.

---

## 2. Source Reconciliation (read first)

The five documents disagree in places. I treat the documents marked "revised" and "current 26 October 2026" as authoritative and flag everything else here so nothing is silently assumed.

| Topic | Older document | Revised/current document | What I will follow |
|---|---|---|---|
| Programme dates | Build Manual: 19 Oct to 11 Dec 2026 | Build Sequence: 26 Oct to 18 Dec 2026 | **26 Oct to 18 Dec** (restart) |
| Coordinator | Build Manual: Ajendra | Ownership (revised): **Aryan Ghai** | **Aryan** is coordinator |
| Security/DevSecOps | Build Manual: Aryan | Ownership (revised): **Ajendra Nath Tripathi** | **Ajendra** owns security |
| Week 3 focus | Manual: registry and profile quality | Sequence: registry **and China-readiness workflow** | Sequence (readiness UI starts Week 3) |
| Week 4 focus | Manual: readiness and demand review gate | Sequence: **buyer demand and rule approval gate** | Sequence (requirement screens Week 4) |
| Week 6 name | Both: opportunity, dashboard, feature freeze | Same | Same (30 Nov to 4 Dec) |
| Team size | Internship brief: 8 roles incl. a **Full Stack Integration Engineer** | Manual: "There is no separate full-stack integrator" | **No separate integrator**; I own client-side integration |
| Language scope | Brief: "English and Mandarin-ready presentation" | Manual: "a full bilingual interface is not promised" | English-first, Mandarin-ready fields only |

**Consequences for me:**
- I must coordinate with **Aryan** (not Ajendra) for backlog, blockers and integration evidence, and with **Ajendra** (not Aryan) for security review of the frontend.
- Because there is no separate full-stack integrator, **I coordinate every service contract the interface uses** and cannot assume someone else will wire screens to APIs.
- All dates in this plan use the revised calendar.

**Action item:** Confirm with Aryan that the Build Manual will be reissued with the revised dates and roles, so my traceability does not point at a stale document.

---

## 3. My Role, Authority and Boundaries

### 3.1 What I own **[Source]**
- The authenticated interface and all journey screens
- Components, forms, validation, dashboards
- Client-side integration, and coordination of every service contract the interface uses

### 3.2 What I do not own **[Source]**
| Topic | Owner |
|---|---|
| Workflow intent, field definitions, acceptance criteria | **Adrika** (BNCS keeps material commercial/policy approval) |
| Authentication, RBAC, application APIs, workflow states | **Abhishek** |
| Schema, migrations, search, analytics queries, audit storage | **Vishal** |
| Matching rules, scoring, explanations, fallback | **Alok** |
| Security review, threat model, negative tests | **Ajendra** |
| Independent verification, UAT recommendation | **Harish** |
| Sprint cadence, backlog, risks, integration governance | **Aryan** |
| Product scope, architecture, security-risk, release approval | **BNCS and the Senior Technical Mentor** |

### 3.3 Hard rules for me
- I do not invent commercial policy, field meaning, scoring wording or workflow states. I implement what Adrika specifies and BNCS approves.
- I do not approve my own critical artefacts. At least one peer review is required before mentor/BNCS review.
- I do not bypass blockers with undocumented workarounds. Anything past 24 hours is escalated.
- No credentials or secrets in source code, ever.

---

## 4. Product Context the Frontend Must Respect

### 4.1 Core platform principles and their UI consequences **[Source principles, Proposed UI implications]**

| Principle | What it means in the UI |
|---|---|
| Human approval before consequence | Accept/Hold/Reject controls require a recorded reason. No auto-created opportunities. A confirm step precedes consequential actions. |
| Mandatory rules before similarity | Match results display eligibility filter outcome first, then weighted score, then semantic component. Never reorder this in the UI. |
| Explain every recommendation | Each candidate shows contributing criteria, score breakdown, missing information and limitations. |
| Least privilege | Navigation, buttons and routes reflect permitted actions. The backend remains the real enforcement point; the UI is never the only control. |
| Synthetic and approved data only | A persistent "Pilot / synthetic data / non-production" banner. No real data in fixtures, screenshots or demos. |
| Auditable material action | Every material action surfaces a confirmation with a link or reference to its audit event where available. |
| English-first, Mandarin-ready | Structured, controlled Mandarin-ready fields. Machine-translated text must never be shown as authoritative. |
| Replaceable components | UI must not depend on a specific AI vendor. Match UI binds to the contract, not to a model. |

### 4.2 Language rules for results **[Source]**
- Do **not** present similarity or weighted scores as certainty, legal approval or guaranteed commercial fit.
- Use advisory wording: "Suggested fit", "Recommended for review", never "Approved", "Guaranteed" or "Best supplier".
- AI recommends; authorised users decide. Result language is defined by Adrika (Week 5).

---

## 5. Technical Baseline and Conventions

### 5.1 Recommended baseline **[Source]**
Next.js, React, TypeScript (frontend); Spring Boot (backend); PostgreSQL; Python/FastAPI (isolated matching service); role-based authentication; GitHub pull-request workflow; containerised local setup; non-production staging. Material deviations need BNCS and mentor approval.

### 5.2 Frontend tooling choices **[Proposed, to be confirmed with the Senior Technical Mentor in Week 1]**

| Concern | Proposed choice | Reason |
|---|---|---|
| Framework | Next.js (App Router) + React + TypeScript (strict) | Matches the baseline |
| Styling | Tailwind CSS + CSS variables for design tokens | Fast, consistent, themeable |
| Component primitives | Accessible headless primitives (e.g., Radix UI or equivalent) | Keyboard/ARIA handled correctly |
| Forms and validation | React Hook Form + Zod | Typed schemas, shared validation rules |
| Server state | TanStack Query | Caching, loading/error states, retries |
| Tables | TanStack Table | Sorting/filtering/pagination for registry lists |
| Charts (dashboard) | A lightweight chart library, Week 6 | Only after metrics contract is agreed |
| Unit/component tests | Vitest + React Testing Library | Fast, standard |
| API mocking | Mock Service Worker (MSW) | Lets me build before the backend is ready |
| E2E tests | Playwright | Journey automation, aligned with Harish |
| Accessibility checks | axe-core (jest-axe + Playwright) + manual keyboard pass | Evidence for Week 7 |
| Lint/format | ESLint, Prettier, TypeScript strict, Husky pre-commit | Enforces review discipline |
| API types | Types generated from or checked against Abhishek's API contract (OpenAPI if available) | Prevents contract drift |

### 5.3 Proposed repository layout **[Proposed]**
```
frontend/
  src/
    app/                      # Next.js routes (login, suppliers, requirements, matches, opportunities, dashboard, audit)
    components/
      ui/                     # Reusable library (Button, Input, Table, Badge, Dialog, ...)
      patterns/               # Composed patterns (FormSection, StatusPill, ExplanationPanel, AuditTimeline)
      layout/                 # AppShell, SideNav, TopBar, PilotBanner
    features/
      auth/  suppliers/  products/  readiness/  requirements/  matching/  opportunities/  dashboard/  audit/
    lib/
      api/                    # Typed API client, error normaliser, auth interceptors
      validation/             # Zod schemas mirroring the field dictionary
      permissions/            # Role/permission helpers
      i18n/                   # English-first, Mandarin-ready field labels
    mocks/                    # MSW handlers and synthetic fixtures
    styles/                   # Tokens, globals
  tests/
    unit/  component/  e2e/  a11y/
  docs/
    SETUP.md  COMPONENTS.md  CONTRACTS.md  LIMITATIONS.md  DECISIONS.md
  .env.example                # Variable names only, never values
```

### 5.4 Coding conventions **[Proposed]**
- TypeScript `strict: true`; no `any` without a commented justification.
- One feature = one folder under `features/`; shared things go to `components/ui` only when used by two or more features.
- Branch naming: `feat/<stage>-<short-name>`, `fix/<id>-<short-name>`, `docs/<topic>`.
- Commits reference the backlog item ID (e.g., `FE-2.3: supplier form validation`).
- Every PR includes: linked story/acceptance criteria, screenshots or recording of all UI states, test evidence, accessibility note, and list of contracts touched.
- Environment variables are read only through a single typed config module. `.env.example` lists names only.

### 5.5 Backlog ID scheme **[Proposed]**
`FE-<week>.<n>` (e.g., `FE-2.4`). Every task has: **owner, due date, acceptance criteria, evidence location, reviewer** **[Source rule]**. Work is not complete until reviewed and accepted, or explicitly carried forward with a reason and a new date.

---

## 6. Users, Roles and Frontend Permission Behaviour

### 6.1 Prototype users **[Source]**
- **Platform Administrator:** manages approved internal users, access and pilot configuration.
- **Commercial Analyst:** creates and maintains supplier, product, readiness and buyer requirement information and reviews match results.
- **Reviewer or Approver:** reviews material readiness, matching and opportunity decisions.

External supplier self-service and public/buyer access are out of MVP.

### 6.2 Proposed permission matrix for UI behaviour **[Proposed; Abhishek and Adrika must confirm; Ajendra reviews]**

| Capability | Platform Admin | Commercial Analyst | Reviewer/Approver |
|---|---|---|---|
| Sign in | Yes | Yes | Yes |
| Manage internal users | Yes | No | No |
| Create/edit supplier and product | Confirm | Yes | Read only (confirm) |
| Complete readiness assessment | Confirm | Yes | Read only |
| Review/approve readiness | No (confirm) | No | Yes |
| Create buyer requirement | Confirm | Yes | Read only |
| Run match | Confirm | Yes | Confirm |
| Record accept/hold/reject | No | Confirm | Yes |
| Convert accepted match to opportunity | Confirm | Yes | Confirm |
| Update opportunity stage | Confirm | Yes | Confirm |
| View dashboard | Yes | Yes | Yes |
| View audit history | Yes (full) | Role-aware subset | Role-aware subset |

"Confirm" means I must not guess. I will build the UI against a single `can(permission)` helper so that changing the matrix is a one-file change.

### 6.3 Frontend permission rules **[Source and Proposed]**
- **Protected routes:** unauthenticated users are redirected to login; authenticated users without permission see a dedicated **access-denied** state and not a blank page or a raw error.
- **Hide vs disable:** actions a role can never perform are hidden. Actions blocked by record state (e.g., an incomplete readiness assessment) are disabled with a visible explanation.
- **The backend is the source of truth.** If the server returns 401/403 despite the UI allowing the action, the UI handles it gracefully (safe failure, message, no data leak), and I log it as a defect for Abhishek/Ajendra.
- **Session expiry:** a clear re-authentication prompt that preserves unsaved form input where safe.
- **Denied actions must fail safely and leave an audit record** (the audit record is backend-side; the UI shows a neutral denied message).

---

## 7. Screen, Route and Journey Inventory

### 7.1 Journey to screen mapping **[Source stages, Proposed screens]**

| Stage | Journey step | My role | Screens I build | Co-owners |
|---|---|---|---|---|
| 1 | Access workspace | Primary (with Abhishek) | Login, role-aware app shell, access-denied, session-expired | Abhishek; review: Ajendra; test: Harish |
| 2 | Register supplier and product | **Primary** (with Abhishek, Vishal) | Supplier list/detail/create/edit, product list/detail/create/edit, evidence metadata panel, search/filter | Adrika (fields), Vishal, Abhishek |
| 3 | Assess China readiness | Primary (with Adrika, Abhishek) | Readiness questionnaire, missing-info indicators, score/status view, reviewer state, review queue | Adrika, Abhishek, Vishal, Alok (rules) |
| 4 | Capture buyer requirement | Primary (with Adrika, Abhishek) | Requirement form (specs, quantity, exclusions, priority weights), versions view, approval state | Adrika, Abhishek, Vishal, Alok |
| 5 | Generate match | Supports (Alok is primary) | Match request screen, run status, ranked results, fallback indicator | Alok, Abhishek, Vishal |
| 6 | Review and decide | **Primary** (with Adrika, Abhishek) | Candidate comparison, score breakdown, explanation panel, warnings, missing data, disposition form (accept/hold/reject + reason) | Adrika, Alok, Abhishek |
| 7 | Manage opportunity | **Primary** | Convert-to-opportunity, pipeline board/list, opportunity detail (stage, owner, next action, due date, notes, links to supplier/product/requirement/match) | Abhishek, Vishal, Adrika |
| 8 | Monitor and audit | Primary (with Vishal) | Dashboard (counts, status filters, readiness/match/pipeline views, unresolved-items list), audit history | Vishal, Aryan, Harish, Ajendra |

### 7.2 Proposed route map **[Proposed]**
```
/login                                  Public
/access-denied                          Authenticated
/dashboard                              Landing after login
/suppliers                              List, search, filters
/suppliers/new
/suppliers/[id]                         Detail (profile, products, readiness, preview)
/suppliers/[id]/edit
/suppliers/[id]/products/new
/products/[id]  and  /products/[id]/edit
/suppliers/[id]/readiness               Assessment form + result
/readiness/review                       Reviewer queue
/requirements                           List
/requirements/new
/requirements/[id]                      Detail and versions
/requirements/[id]/match                Request and run match
/matches/[id]                           Ranked results, comparison, disposition
/opportunities                          Pipeline
/opportunities/[id]
/audit                                  Role-aware audit history
/admin/users                            Only if confirmed in scope (see Open Questions)
```

### 7.3 Controlled profile preview **[Source]**
A read-only, controlled presentation of **approved** supplier and product information, English with Mandarin-ready structured fields. Only approved fields are shown. Unreviewed machine translation is never rendered as authoritative. This is built in the Week 3 to 6 window and finalised with the dashboard work.

---

## 8. Reusable Component Library Plan

Built progressively, not at the end. Each component ships with: TypeScript props, all states, keyboard/ARIA behaviour, a usage note in `COMPONENTS.md`, and a test.

### 8.1 Foundations
Design tokens (colour, spacing, type scale, radii, focus ring), light-theme baseline with sufficient contrast, responsive breakpoints.

### 8.2 Primitives (Weeks 1 to 2)
Button, IconButton, Link, Input, Textarea, Select, Combobox, Checkbox, Radio, Switch, DatePicker, FormField (label, hint, error), Badge, Tooltip, Dialog/ConfirmDialog, Toast/InlineAlert, Spinner, Skeleton, Tabs, Breadcrumb.

### 8.3 Layout and navigation (Week 1 to 2)
AppShell, SideNav (role-aware), TopBar (user menu, session), PilotBanner ("Pilot, synthetic data, non-production"), PageHeader, SectionCard, EmptyState, ErrorState, AccessDenied.

### 8.4 Data display (Weeks 2 to 3)
DataTable (sort, filter, pagination, empty/loading/error), FilterBar, SearchBox, Pagination, DescriptionList, StatusPill (draft, in review, approved, rejected, on hold, blocked, completed), CompletenessMeter, MissingInfoList.

### 8.5 Workflow patterns (Weeks 3 to 6)
FormSection with progress and autosave-warning, QuestionnaireRenderer (configurable, required-field logic), ReviewerActionBar, VersionHistory, ScoreBreakdown, ExplanationPanel, WarningList, CandidateComparison, DispositionForm, OpportunityStageTracker, KpiCard, AuditTimeline, UnresolvedItemsList, FallbackNotice, ConfidenceHint (advisory only).

### 8.6 Bilingual-ready helpers (Week 3)
`BilingualField` renders English as primary and an optional Mandarin value as a labelled, structured field. Includes a "not reviewed" badge when status is unapproved.

---

## 9. Mandatory UI State Matrix

Every screen and data-bound component must implement and have evidence for the states below **[Source: loading, empty, error, denied, fallback]**, plus the form states I add.

| State | Required behaviour | Evidence |
|---|---|---|
| Loading | Skeleton or spinner, no layout jump, announced to assistive tech | Screenshot + test |
| Empty | Explains why it is empty and offers the next action | Screenshot |
| Error (server/network) | Plain-language message, retry, no stack traces, correlation/reference ID if provided | Screenshot + test |
| Denied (403) | Access-denied view, no data leakage, link back | Screenshot + E2E |
| Unauthenticated (401) | Redirect to login with return path | E2E |
| Validation error | Inline per field + summary, focus moves to first error | Test + a11y check |
| Success | Confirmation plus reference to the created or changed record | Screenshot |
| Conflict/stale | Message when a record changed since it was loaded (version mismatch) | Test (if backend supports) |
| Fallback | Visible notice when matching uses the rules-only fallback, with what it means | Screenshot + E2E |
| Missing information | Warnings for incomplete data, blocking progression where rules require | Test |
| Read-only | Clear indication for roles without edit permission | Screenshot |

---

## 10. Service Contract Register (Frontend View)

Because there is no full-stack integrator, I keep this register and keep it current. **Each row needs a named backend owner, a versioned contract and a mock before I build the screen.**

| ID | Area | Provider | Used by (screens) | Needed by week | Status |
|---|---|---|---|---|---|
| C1 | Auth: login, session, logout, current user and role | Abhishek | Login, shell, route guards | W2 (mock W1) | To confirm |
| C2 | Supplier CRUD + search/filter | Abhishek / Vishal | Supplier screens | W2 to W3 | To confirm |
| C3 | Product CRUD | Abhishek / Vishal | Product screens | W2 | To confirm |
| C4 | Evidence/document-status metadata | Abhishek / Vishal | Supplier/product detail | W3 | To confirm |
| C5 | Readiness questionnaire config, answers, scoring, review actions | Abhishek / Vishal; rules by Adrika/Alok | Readiness screens | W3 to W4 | To confirm |
| C6 | Buyer requirement CRUD + versioning + approval | Abhishek / Vishal | Requirement screens | W4 | To confirm |
| C7 | Match request, results, explanations, warnings, fallback flag, disposition | Abhishek (orchestration), Alok (service) | Matching screens | W5 (mock contract W2) | To confirm |
| C8 | Opportunity create/update/stages/notes/links | Abhishek / Vishal | Pipeline screens | W6 | To confirm |
| C9 | Dashboard metrics | Vishal / Abhishek | Dashboard | W6 | To confirm |
| C10 | Audit history (role-aware) | Vishal / Abhishek | Audit screen | W6 | To confirm |
| C11 | Structured error format | Abhishek | All | W1 | To confirm |

**Contract rules:**
- No UI built against an unversioned contract. Contract changes follow the rule: **Priyanka and Abhishek coordinate; Vishal and Alok are included when data or matching interfaces change** **[Source]**.
- Each contract has an MSW mock so I can progress when the backend is late. A mock never replaces a real integration check on Friday.
- Error responses are normalised in one place (`lib/api/errors.ts`) into: `code`, `message`, `fieldErrors[]`, `reference`.
- Any contract mismatch found is logged in the integration issue register maintained by Aryan.

---

## 11. Weekly Plan

> Dates follow the revised build sequence. Each weekly section lists: **Goal, Product target, My duties (named), Detailed tasks, Dependencies, Deliverables, Friday exit evidence, Definition of success, Risks**. Daily rhythm: Monday 60-min Sprint Start; Tue to Thu 15-min stand-ups (Wednesday includes a health checkpoint); Friday 90-min Sprint Review and live demo. Meetings are inside the six-hour day.

---

### WEEK 1: Definition, Architecture and Delivery Skeleton
**26 to 30 October 2026** (in progress at time of writing)

**Goal:** Agree scope and interfaces, and have a running frontend skeleton with routes and initial screens.

**Product target [Source]:** Definition, architecture and delivery skeleton.

**My named duty [Source]:** Frontend skeleton, routes and initial screens.

**Friday exit review [Source]:** Scope, interfaces and evidence rules agreed. Frontend, backend and data skeletons run.

#### Tasks
| ID | Task | Acceptance criteria | Evidence |
|---|---|---|---|
| FE-1.1 | Attend Sprint Start; confirm sprint goal, frontend tasks, dependencies, reviewers | Tasks on the board with owner, due date, acceptance criteria, evidence location, reviewer | Board snapshot |
| FE-1.2 | Read and annotate scope: MVP boundary, journey, roles, out-of-scope list | Written one-page scope summary reviewed by Adrika | Doc link |
| FE-1.3 | Confirm frontend stack choices (Section 5.2) with the Senior Technical Mentor | Decision recorded in `DECISIONS.md` and the decision register (Aryan) | Decision entry |
| FE-1.4 | Initialise repository: Next.js + TypeScript strict, ESLint, Prettier, Husky, commit conventions, `.env.example`, `.gitignore` covering secrets | Clean clone, `install` + `dev` + `build` + `lint` + `test` work; no secrets present | CI/log output |
| FE-1.5 | Containerised local setup that runs alongside the backend skeleton | `docker compose up` (or agreed equivalent) starts the frontend | Setup note |
| FE-1.6 | Design tokens, global styles, responsive breakpoints | Tokens documented; contrast checked for text/background | Storybook-style page or `COMPONENTS.md` |
| FE-1.7 | App shell: AppShell, TopBar, SideNav (static), PilotBanner, PageHeader | Renders on desktop, tablet and mobile widths | Screenshots |
| FE-1.8 | Route skeleton for all stages (placeholder pages) with a consistent layout | Every route in 7.2 resolves to a titled placeholder | Route list + screenshots |
| FE-1.9 | Initial screens: Login (UI only), Dashboard placeholder, Supplier list placeholder | Visual review by Adrika against draft journey | Screenshots |
| FE-1.10 | Typed API client with error normaliser and auth-aware wrapper (against mocks) | Unit tests for success, 401, 403, 422, 500, network failure | Test report |
| FE-1.11 | MSW mock setup and first mocks (auth, suppliers) | Dev server runs with mocks on; toggle for real API | Setup note |
| FE-1.12 | Agree API and error conventions with Abhishek; draft Contract Register (Section 10) | C1 and C11 drafted and versioned | Contract doc link |
| FE-1.13 | Review Adrika's draft journeys, field list and workflow states for UI feasibility | Feedback logged; open questions listed | Comment log |
| FE-1.14 | Smoke test hook-up with Harish: agree selectors/test IDs convention (`data-testid`) | Convention written; 2 smoke cases agreed | Test doc |
| FE-1.15 | Share frontend data-handling needs with Ajendra (what is stored client-side, tokens, cookies) | Input recorded in the threat model | Review note |
| FE-1.16 | Friday: demo skeleton running; capture lessons and next-week dependencies | Demo recorded; carry-forward items logged | Review notes |

#### Suggested day plan
| Day | Focus |
|---|---|
| Mon | Sprint Start (60 min). Scope reading, stack decision proposal, repo init |
| Tue | Stand-up (15). Tooling, linting, container setup, tokens |
| Wed | Stand-up with health checkpoint (15). App shell, route skeleton, mocks |
| Thu | Stand-up (15). API client, error normaliser, initial screens, contract draft; demo readiness |
| Fri | Sprint Review (90). Demo, evidence, retrospective, Week 2 prep |

#### Dependencies
- Abhishek: API and error conventions, auth design (C1, C11).
- Adrika: draft journeys, roles, workflow states.
- Senior Technical Mentor: stack approval.

#### Deliverables
Running frontend skeleton, repo with tooling, token set, app shell, route skeleton, typed API client with tests, MSW mocks, Contract Register v0.1, `SETUP.md` v0.1.

#### Risks and handling
- Stack not approved in time: proceed on the proposed baseline, record the assumption, and isolate framework-specific decisions.
- Contracts unavailable: build against mocks and log the dependency.

---

### WEEK 2: Authenticated Supplier-Product Vertical Slice
**2 to 6 November 2026**

**Goal:** A real, end-to-end authorised flow: sign in, create and retrieve a supplier and product.

**Product target [Source]:** Authenticated supplier-product vertical slice.

**My named duty [Source]:** Login, role-aware navigation and supplier-product UI.

**Friday exit review [Source]:** An authorised user signs in, creates and retrieves a supplier and product end-to-end. (**Gate 1 at end of Week 2.**)

#### Tasks
| ID | Task | Acceptance criteria | Evidence |
|---|---|---|---|
| FE-2.1 | Login screen (real): email/credential form, validation, error and locked/denied messaging | Valid login lands on dashboard; invalid shows safe, non-leaking message | Test + screenshots |
| FE-2.2 | Session handling: token/cookie handling per Abhishek's design, logout, expiry, refresh behaviour | No tokens in `localStorage` unless explicitly approved by Ajendra; expiry prompts re-login | Review note |
| FE-2.3 | Route guards and role-aware SideNav using `can()` helper | Admin/Analyst/Reviewer see only permitted items; direct URL access to forbidden route shows access-denied | E2E tests |
| FE-2.4 | Access-denied and session-expired views | Both implemented and reachable | Screenshots |
| FE-2.5 | Supplier create form (fields from Adrika's field dictionary) | All required fields, controlled values, client validation mirrors server rules | Component tests |
| FE-2.6 | Supplier detail and edit view | Retrieve after create shows saved values; edit persists | E2E |
| FE-2.7 | Product create/detail/edit linked to supplier | Product appears under its supplier | E2E |
| FE-2.8 | Validation and error rendering: inline errors, error summary, server field-error mapping | Server 422 maps to the right fields | Tests |
| FE-2.9 | All UI states for these screens (Section 9) | Loading, empty, error, denied, success verified | Screenshot set |
| FE-2.10 | Show baseline audit confirmation after create/edit (reference or "recorded" notice) | User sees a traceable action confirmation | Screenshot |
| FE-2.11 | Swap mocks for the real API for C1 to C3; log mismatches | Integration issues logged with Aryan | Issue log |
| FE-2.12 | Review mock match contract from Alok (C7 draft) for UI implications | Feedback recorded | Comment log |
| FE-2.13 | Support Harish: stable `data-testid`s, test accounts per role, smoke/auth/CRUD tests pass | Smoke suite green | CI log |
| FE-2.14 | Fix defects raised in the week | No open critical defects in my area | Defect register |
| FE-2.15 | Prepare for Friday's first integrated demo | Script: login, create supplier, create product, retrieve, view confirmation | Demo script |

#### Suggested day plan
| Day | Focus |
|---|---|
| Mon | Sprint Start. Finalise field list with Adrika; login UI; mock-to-real plan |
| Tue | Session handling, route guards, role-aware nav |
| Wed | Supplier and product forms with validation; health checkpoint |
| Thu | Detail/edit, all UI states, real-API integration, test support; demo rehearsal |
| Fri | Sprint Review. Gate 1 evidence; retrospective |

#### Dependencies
Abhishek (auth, RBAC, supplier-product APIs), Vishal (migrations, seed data), Adrika (final fields and acceptance), Ajendra (auth review), Harish (tests).

#### Deliverables
Working login with role-aware navigation, supplier and product screens against the real API, state coverage, tests, Contract Register v0.2.

#### Gate 1 checklist
- [ ] Login works for each role
- [ ] Denied path works and fails safely
- [ ] Supplier and product created, persisted, retrieved
- [ ] Baseline audit action visible
- [ ] Evidence linked in the repository

---

### WEEK 3: Supplier Registry and China-Readiness Workflow
**9 to 13 November 2026**

**Goal:** A searchable, validated supplier/product registry and the first working readiness assessment UI.

**Product target [Source]:** Supplier registry and China-readiness workflow.

**My named duty [Source]:** Registry, search and readiness UI.

**Friday exit review [Source]:** Validated records are searchable. Readiness status and changes remain auditable.

> **Reconciliation note:** The older Build Manual places readiness in Week 4. I follow the revised sequence, so I start readiness UI this week. I will confirm the readiness rules and questionnaire with Adrika early on Monday, because the rules are not approved until the Week 4 gate. Where rules are not final I build the questionnaire as **configuration-driven** so that approved rules do not require a rebuild.

#### Tasks
| ID | Task | Acceptance criteria | Evidence |
|---|---|---|---|
| FE-3.1 | Registry list: responsive DataTable with sorting, pagination | Handles 15+ suppliers and 30+ products smoothly | Screenshots + test |
| FE-3.2 | Search and filters (category, status, completeness, certification, export experience as defined by Adrika) | Filters combine; URL reflects filter state; clear-all works | E2E |
| FE-3.3 | Supplier detail enhancements: product list, certification and document-status metadata, completeness meter | Metadata displays; missing items flagged | Screenshots |
| FE-3.4 | Bilingual-ready fields: `BilingualField` for approved structured fields with "not reviewed" badge | English-first display; Mandarin value shown only as labelled structured field | Component test |
| FE-3.5 | Data-quality indicators: missing-info states and quality flags | Incomplete records are visibly flagged | Screenshot |
| FE-3.6 | Edit flows with update audit confirmation and version/conflict handling | Edits show confirmation; stale edit handled if supported | Tests |
| FE-3.7 | Readiness questionnaire UI: configurable renderer, required-field logic, save draft, submit | Questionnaire renders from config; incomplete submission blocked with explicit reasons | Component + E2E |
| FE-3.8 | Readiness status and gaps view: score or status, warnings, corrective-action indicators | Status shown with traceable inputs | Screenshot |
| FE-3.9 | Readiness change history shown on the supplier (who, what, when) | Auditable changes visible | Screenshot |
| FE-3.10 | All UI states for registry and readiness (Section 9) | Evidence set complete | Screenshots |
| FE-3.11 | Integrate C2, C4, C5 with the real API; log mismatches | Issue log updated | Log |
| FE-3.12 | Permission behaviour on registry (object-level): cannot open/edit records outside role | Denied tested | E2E |
| FE-3.13 | Respond to Ajendra's registry and evidence-handling security review | Findings tracked and fixed or escalated | Remediation register |
| FE-3.14 | Support Harish's functional, API, permission and regression tests | Regression suite stays green | CI log |
| FE-3.15 | Update `COMPONENTS.md`, `CONTRACTS.md`, `LIMITATIONS.md` | Docs match the code | Doc diffs |

#### Suggested day plan
| Day | Focus |
|---|---|
| Mon | Sprint Start. Confirm readiness questionnaire and filters with Adrika; build registry list |
| Tue | Search/filters, detail enhancements, bilingual field component |
| Wed | Readiness renderer and submit logic; health checkpoint |
| Thu | Readiness status/gaps view, history, state coverage, integration; rehearse |
| Fri | Sprint Review and retrospective |

#### Dependencies
Adrika (readiness questions, missing-info states, acceptance), Abhishek (registry/readiness services), Vishal (indexes, search, readiness data), Alok (rule inputs and normalisation), Ajendra, Harish.

#### Deliverables
Demonstration supplier registry with search/filter, readiness UI, bilingual-ready field component, state coverage, updated docs.

---

### WEEK 4: Buyer Demand and Rule Approval Gate
**16 to 20 November 2026**

**Goal:** Buyer requirement capture and readiness review screens work end-to-end. All fields, rules, criteria and interfaces are approved **before AI integration**.

**Product target [Source]:** Buyer demand and rule approval gate.

**My named duty [Source]:** Readiness review and requirement screens.

**Friday exit review [Source]:** Fields, rules, criteria and interfaces receive approval before AI integration. (**Gate 2 at end of Week 4.**)

#### Tasks
| ID | Task | Acceptance criteria | Evidence |
|---|---|---|---|
| FE-4.1 | Readiness reviewer queue and review screen: approve, request changes, reject with reason | Only the Reviewer role can act; state changes shown; audit confirmation | E2E |
| FE-4.2 | Block incomplete progression: suppliers with incomplete readiness cannot be marked eligible for matching | Blocked with a clear explanation | Test |
| FE-4.3 | Buyer requirement form: specifications, quantity, commercial parameters, certification needs, exclusions, verification status | All fields from the dictionary; validation mirrors server | Component tests |
| FE-4.4 | Priority weights UI: weights set only per approved criteria; totals validated | Invalid weights cannot be submitted | Test |
| FE-4.5 | Requirement versioning view and approval state | Each save is versioned; approved version identifiable | Screenshot |
| FE-4.6 | Requirement list and detail with status filters | Searchable, role-aware | E2E |
| FE-4.7 | Access separation: confirm role-based visibility for demand data | Unauthorised roles denied | E2E |
| FE-4.8 | Show approved criteria and rules read-only where users need to understand matching inputs | No ability to edit approved rules in the UI | Screenshot |
| FE-4.9 | Prepare a match-request UI draft against the mock contract (C7) | Reviewed with Alok and Adrika | Mockup/screens |
| FE-4.10 | Integrate C5 (review) and C6 (requirements) against the real API | Mismatches logged | Log |
| FE-4.11 | Gate 2 pack: screens, contracts, field and rule approvals, and open decisions | Pack submitted to Aryan for the gate | Pack link |
| FE-4.12 | Address Ajendra's data-flow and access review | Findings fixed or escalated | Register |
| FE-4.13 | Support Harish: boundary, workflow, permission tests | Green or defects logged | CI + defects |

#### Suggested day plan
| Day | Focus |
|---|---|
| Mon | Sprint Start. Reviewer queue and review actions |
| Tue | Requirement form and weights |
| Wed | Versioning, lists, access separation; health checkpoint |
| Thu | Integration, Gate 2 pack, match-request draft; rehearse |
| Fri | Sprint Review and Gate 2 decision |

#### Gate 2 checklist
- [ ] Readiness workflow works including review
- [ ] Buyer requirement captured, validated, versioned
- [ ] Fields, interfaces, eligibility rules and scoring criteria approved by BNCS/mentor
- [ ] Access separation demonstrated
- [ ] Match contract (C7) agreed as the basis for Week 5

---

### WEEK 5: Explainable AI-Assisted Matching
**23 to 27 November 2026**

**Goal:** Ranked candidates with explanations and warnings; human disposition works end-to-end, including the rules-only fallback.

**Product target [Source]:** Explainable AI-assisted matching.

**My named duty [Source]:** Ranked-result, explanation and warning UI. Journey stages 5 and 6 build requirements.

**Friday exit review [Source]:** Explainable candidates and a human decision work end-to-end with fallback.

#### Tasks
| ID | Task | Acceptance criteria | Evidence |
|---|---|---|---|
| FE-5.1 | Match request screen: select an approved requirement, run match | Only approved requirements are selectable | E2E |
| FE-5.2 | Run status handling: in progress, success, partial, failure | Uses loading/error patterns; no silent failure | Tests |
| FE-5.3 | Ranked results list: rank, supplier/product, eligibility outcome, weighted score, semantic indicator | Filter outcome shown before scores; scores labelled as advisory | Screenshot |
| FE-5.4 | Score breakdown and explanation panel: contributing criteria, gaps, limitations | Each candidate explains why it ranked | Component tests |
| FE-5.5 | Missing-information warnings per candidate | Warnings visible and not collapsed by default | Screenshot |
| FE-5.6 | Rule and model version display on results | Version visible for traceability | Screenshot |
| FE-5.7 | Candidate comparison view (side by side) | At least 2 candidates comparable | Screenshot |
| FE-5.8 | Disposition form: Accept / Hold / Reject with mandatory reason | Cannot submit without reason; confirmation shown; audit reference displayed | E2E |
| FE-5.9 | Rules-only fallback UI: clear fallback notice when AI service is unavailable; results still usable | Fallback notice shown; results labelled "rules-only" | E2E (simulated failure) |
| FE-5.10 | Authorisation: only permitted roles can request matches or record dispositions | Denied tested | E2E |
| FE-5.11 | Wording review with Adrika: no language implying certainty, approval or autonomous decisions | Copy approved | Copy sheet |
| FE-5.12 | Handle manipulated or odd data safely: long text, special characters, markup are escaped | No script injection in explanations | Test |
| FE-5.13 | Integrate C7 with the real service via Abhishek's orchestration | Mismatches logged | Log |
| FE-5.14 | Support Harish: expected, false, missed, missing-data, fallback tests; Ajendra: abuse, leakage and unsafe-logging checks | Tests green; no sensitive data in console/logs | Test + review |

#### Suggested day plan
| Day | Focus |
|---|---|
| Mon | Sprint Start. Match request, run states, results list |
| Tue | Score breakdown, explanation, warnings, version display |
| Wed | Comparison view, disposition form; health checkpoint |
| Thu | Fallback UI, copy review, integration, security checks; rehearse |
| Fri | Sprint Review: live match, decision, fallback demo |

---

### WEEK 6: Opportunity, Dashboard and Feature Freeze
**30 November to 4 December 2026**

**Goal:** The full priority journey works from access through audit review, and the feature scope is frozen.

**Product target [Source]:** Opportunity, dashboard and feature freeze.

**My named duty [Source]:** Pipeline, dashboard and audit screens.

**Friday exit review [Source]:** Priority journey works from access through audit review. Feature scope freezes. (**Gate 3 at end of Week 6.**)

#### Tasks
| ID | Task | Acceptance criteria | Evidence |
|---|---|---|---|
| FE-6.1 | Convert accepted match to opportunity: only from an Accepted disposition | Not possible from Hold/Reject; confirmation step | E2E |
| FE-6.2 | Opportunity pipeline (list and stage view): introductions, meetings, RFQs, samples, quotations, negotiations, purchase orders, outcome (stages per Adrika) | Stages match approved states only | Screenshot |
| FE-6.3 | Opportunity detail: stage, owner, next action, due date, notes, links to supplier, product, requirement and match, decision history | All links work | E2E |
| FE-6.4 | Stage transitions with validation: only approved transitions allowed | Invalid transitions blocked | Tests |
| FE-6.5 | Open / blocked / completed items distinguishable | Visual and filterable | Screenshot |
| FE-6.6 | Dashboard: supplier, buyer, matching, opportunity, activity and conversion indicators; status filters; unresolved-items list | Every figure traceable to source records | Screenshot + reconciliation with Harish |
| FE-6.7 | Audit screen: role-aware history showing who changed what and when | Matches the backend audit data | E2E |
| FE-6.8 | Controlled bilingual supplier profile preview finalised | Approved fields only | Screenshot |
| FE-6.9 | Stabilise frontend integration: remove all mocks from production-path code, fix integration defects | Real API used for all journey stages | Log |
| FE-6.10 | Full-journey E2E automation with Harish | Journey passes in staging | CI log |
| FE-6.11 | Frontend configuration lock; list open defects and limitations | Limitations register current | Doc |
| FE-6.12 | Feature-freeze decision pack input for Aryan | Pack submitted; carry-forward items classified | Pack |
| FE-6.13 | Security regression and configuration lock with Ajendra | No open critical items | Report |

#### Feature freeze rule
After the Week 6 Sprint Review, **no new features**. Any exception needs written BNCS approval and removal of equal or greater effort. Corrections to frozen scope go through Adrika, and Aryan records them.

#### Gate 3 checklist
- [ ] Priority journey works end-to-end through audit review
- [ ] Open defects and limitations visible
- [ ] Dashboard agrees with source records
- [ ] Feature baseline frozen and recorded

---

### WEEK 7: Hardening, Security Validation and UAT
**7 to 11 December 2026**

**Goal:** Close critical issues, validate UX, accessibility and responsiveness, and finish UAT, regression and residual-risk evidence. **No new features.**

**Product target [Source]:** Hardening, security validation and UAT.

**My named duty [Source]:** UX, accessibility and responsive fixes.

**Friday exit review [Source]:** Critical issues close. UAT, regression and residual-risk evidence are complete. (**Gate 4 at end of Week 7.**)

#### Tasks
| ID | Task | Acceptance criteria | Evidence |
|---|---|---|---|
| FE-7.1 | Triage frontend defects with Aryan and Harish by severity (Critical, High, Medium/Low) | All triaged and owned | Defect register |
| FE-7.2 | Fix approved UI defects (only frozen-scope corrections approved by Adrika) | Fixes retested by Harish | Retest evidence |
| FE-7.3 | Accessibility pass: keyboard-only walkthrough of every journey, labels, focus order and visibility, contrast, error announcements, screen-reader smoke test | No blocking accessibility issues; findings logged | A11y report |
| FE-7.4 | Automated a11y checks (axe) in component and E2E tests | Zero serious/critical violations on journey screens | CI report |
| FE-7.5 | Responsive pass on phone, tablet, laptop widths | No horizontal scroll or clipped actions on key screens | Screenshot matrix |
| FE-7.6 | Performance pass: bundle size, slow lists, unnecessary refetches, image sizes | Obvious bottlenecks removed; findings recorded | Perf notes |
| FE-7.7 | Support UAT run by Harish and Adrika: test accounts, data reset, issue capture | UAT record complete | UAT log |
| FE-7.8 | Verify permissions in the UI across all three roles | Role matrix tested and matches Ajendra's access matrix | Test report |
| FE-7.9 | Remediate frontend security findings: dependency audit, headers consumption, token handling, XSS review | Critical and High remediated; residual risk written | Remediation register |
| FE-7.10 | Regression run on the release candidate | Regression green | CI log |
| FE-7.11 | Draft frontend documentation (setup, components, contracts, limitations) | Draft reviewed by a peer | Doc draft |

#### Gate 4 checklist
- [ ] No critical unresolved access-control defect
- [ ] Priority defects closed or accepted with documented workaround
- [ ] UAT, regression and residual-risk evidence documented
- [ ] Accessibility and responsive findings recorded

---

### WEEK 8: Demonstration, Handover and Phase 2 Backlog
**14 to 18 December 2026**

**Goal:** A stable demo, a repeatable setup, and frontend documentation that allows BNCS to run, review and continue the build.

**Product target [Source]:** Demonstration, handover and Phase 2 backlog.

**My named duty [Source]:** Frontend documentation and stable demo.

**Friday exit review [Source]:** BNCS can run the demonstration, review evidence and continue the build. (**Gate 5.**)

#### Tasks
| ID | Task | Acceptance criteria | Evidence |
|---|---|---|---|
| FE-8.1 | Finalise `SETUP.md`: prerequisites, install, env variable names, run local and staging, build, test, troubleshooting | A fresh machine follows it successfully (peer-verified) | Peer sign-off |
| FE-8.2 | Finalise `COMPONENTS.md`: every component, props, states, accessibility notes, examples | Matches the code | Doc |
| FE-8.3 | Finalise `CONTRACTS.md` listing all service contracts, versions and known mismatches | Matches the API documentation | Doc |
| FE-8.4 | Finalise `LIMITATIONS.md`: known defects, unsupported features, accessibility gaps, browser support, non-production caveats | Honest and complete | Doc |
| FE-8.5 | Architecture note: frontend structure, state management, routing, auth handling | Reviewed by the mentor | Doc |
| FE-8.6 | Demo stability: demo data reset, demo accounts, rehearsed script, fallback plan if a service fails | Two full clean rehearsals | Rehearsal log |
| FE-8.7 | Merge branches, tag the final frontend build, clean dead code and unused mocks | Tagged release; no secrets; lint/tests green | Tag + CI |
| FE-8.8 | Frontend test report: coverage, E2E results, accessibility results | Linked in the QA pack | Report |
| FE-8.9 | Contribute to Phase 2 backlog: frontend items, deferred features, tech debt | Items prioritised with rationale | Backlog |
| FE-8.10 | Contribute to Aryan's demo runbook and handover index | Entries accurate | Index |
| FE-8.11 | Final retrospective: lessons, failures, reusable assets | Logged in the Innovation/Delivery log inputs | Log |

---

## 12. Frontend Testing Strategy

| Layer | Tooling | Coverage target (proposed) | Owner |
|---|---|---|---|
| Unit | Vitest | Validation schemas, permission helpers, API error normaliser, formatters | Priyanka |
| Component | Vitest + React Testing Library | Every library component, every state in Section 9 | Priyanka |
| Accessibility | jest-axe, Playwright + axe, manual keyboard pass | Every journey screen | Priyanka (with Harish) |
| Contract | MSW + schema checks against Abhishek's contract | Every contract in Section 10 | Priyanka and Abhishek |
| E2E | Playwright | Each journey stage, denied paths, fallback path, full journey | Harish (primary), Priyanka (support) |
| Visual/responsive | Screenshot matrix at 3 widths | Key screens | Priyanka |

**Rules**
- Tests are written alongside features, not at the end.
- Every acceptance criterion maps to at least one test or a documented manual check, supporting Harish's traceability matrix.
- Test data is synthetic only. Fixtures contain no real names, contacts or confidential details.
- A failing test blocks merge. Flaky tests are fixed or quarantined with a logged reason.

---

## 13. Accessibility, Responsiveness and Performance

### 13.1 Accessibility basics **[Source: keyboard use, labels, contrast, focus, readable responsive layouts]**
- Every input has a programmatic label; errors are tied to inputs with `aria-describedby`.
- Full keyboard operation including dialogs, menus, tables and comboboxes; visible focus indicator; logical focus order; focus returns after dialogs close.
- Sufficient colour contrast; status is never conveyed by colour alone (icon plus text).
- Loading and result changes are announced politely (`aria-live`).
- Headings and landmarks structured per page.

### 13.2 Responsive layout
Mobile-first breakpoints; tables degrade to stacked cards or scroll containers on small screens; no clipped primary actions; touch target sizes adequate.

### 13.3 Performance
Perceived speed is checked at each weekly demo **[Source]**. Practices: route-level code splitting, paginated lists, debounced search, cached queries, optimised assets, no blocking third-party scripts.

### 13.4 Browser support (proposed; confirm with mentor)
Latest two versions of Chrome, Edge, Firefox and Safari. Record in `LIMITATIONS.md`.

---

## 14. Frontend Security Rules

Aligned to the programme's security governance **[Source]**; Ajendra reviews and tests.

- No credentials, API keys or secrets in source; names only in `.env.example`. Only public, non-secret values use the `NEXT_PUBLIC_` prefix.
- Least privilege, with UI gating as convenience and the backend as enforcement.
- Token/session storage follows Abhishek's design and Ajendra's review (prefer HTTP-only cookies; avoid `localStorage` for tokens unless explicitly approved).
- Escape all rendered user and AI-generated content; avoid `dangerouslySetInnerHTML`; sanitise any rich text if introduced.
- Do not log personal data, tokens or full API payloads to the console.
- No sensitive data in URLs or query strings.
- Dependencies pinned via lockfile; run dependency audits; review new packages for licence and maintenance; record external assets with attribution **[Source: licensing]**.
- Do not paste confidential information, credentials or personal data into public AI tools; review and verify all AI-generated code before submission **[Source]**.
- Threat topics I help cover: broken access control, insecure direct object access, session abuse, unsafe input, prompt manipulation (UI display side), data leakage, insecure configuration.
- The pilot makes **no claim of penetration-test certification or production security assurance**.

---

## 15. Weekly Operating Rhythm and Evidence Discipline

### 15.1 Cadence **[Source]**
| Day | Activity | Duration |
|---|---|---|
| Monday | Sprint Start: goal, priorities, owners, dependencies, acceptance criteria, Friday demo | 60 min |
| Tue to Thu | Stand-up (Wednesday includes a health checkpoint) | 15 min |
| Friday | Sprint Review and live demo; accept, reject or carry forward; retrospective | 90 min |

### 15.2 Daily stand-up template **[Source format]**
1. **Completed since last stand-up** (with evidence link)
2. **Next** (and the acceptance criterion it supports)
3. **Blocked or dependent** (on whom)
4. **Need reviewed or decided** (by whom, by when)

### 15.3 Daily time allocation (6 hours) **[Source categories, Proposed split]**
| Block | Approx. share |
|---|---|
| Primary build work | ~3 h |
| Integration, peer review, pairing | ~1 h |
| Testing and defect correction | ~1 h |
| Documentation and tracker updates | ~1 h (includes meetings on Mon/Fri) |

### 15.4 Evidence rule
Attendance is not progress. Every update links to a working artefact, decision, test result, review record or documented blocker. Evidence lives in the agreed project repository, not in private messages or personal devices.

### 15.5 Weekly Friday checklist
- [ ] Integrated build runs in staging
- [ ] Demo script ready; screenshots/recording saved
- [ ] All tasks reviewed and accepted, or carried forward with reason and new date
- [ ] Contract Register, `COMPONENTS.md`, `LIMITATIONS.md` updated
- [ ] Evidence sent to Aryan for the weekly report
- [ ] Next-week dependencies stated

---

## 16. Review, PR and Escalation Process

### 16.1 PR flow **[Source and Proposed]**
1. Branch from `main`; small, focused PRs.
2. PR description: story link, acceptance criteria, UI-state evidence, tests, a11y note, contracts touched, docs updated.
3. At least one relevant peer review (no self-approval of critical artefacts), then mentor/BNCS review where applicable.
4. Frontend and API contract changes: Priyanka and Abhishek coordinate; Vishal and Alok included where data or matching interfaces are affected.
5. AI-affected display changes: reviewed by Alok (accuracy), Adrika (user meaning), Harish (quality), Ajendra (risk).
6. No feature merges to the shared build without review.

### 16.2 Escalation
- **Blocked more than 24 hours:** post in the team channel, tag **Aryan** and the dependency owner, and state the decision needed.
- Product-authority, architecture, data, AI-governance or security blockers must be escalated and never bypassed with an undocumented workaround.
- Critical defects take priority over new features.

### 16.3 Decisions I must not take alone
Scope changes, commercial policy wording, readiness/eligibility/scoring rules, architecture deviations, security-risk acceptance, release decisions.

---

## 17. Frontend Risk Register

| # | Risk | Impact | Likelihood | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Backend contracts late or changing | Rework, blocked screens | High | Contract Register, MSW mocks, weekly contract review with Abhishek | Priyanka |
| R2 | Readiness and scoring rules not approved until Week 4 | Readiness UI built on assumptions | High | Config-driven questionnaire; no hard-coded rules; Adrika confirmation | Priyanka / Adrika |
| R3 | Source documents conflict (dates, roles) | Wrong coordination, missed dates | Medium | Section 2 reconciliation; confirm with Aryan | Priyanka |
| R4 | No separate integrator, so integration falls through gaps | Late integration surprises | Medium | Integrate real APIs from Week 2; Friday integrated demo | Priyanka / Aryan |
| R5 | Scope creep (extra screens, full Mandarin UI, admin screens) | Missed gates | Medium | Scope substitution rule; park in Phase 2 backlog | Aryan |
| R6 | UI implies AI certainty or approval | Governance breach | Medium | Approved wording; "advisory" labels; mandatory human reason | Priyanka / Adrika |
| R7 | Access-control gaps visible only in UI | Security failure | Medium | Server enforcement, negative tests, Ajendra review | Abhishek / Ajendra |
| R8 | Late accessibility and responsive work | Rework in Week 7 | Medium | Accessible primitives from Week 1; axe in CI from Week 2 | Priyanka |
| R9 | Late documentation | Weak handover | Medium | Update docs every Friday | Priyanka |
| R10 | AI service instability during demo | Failed demo | Medium | Fallback UI; demo fallback plan; rehearsals | Priyanka / Alok |
| R11 | Week 1 already partly elapsed at time of planning (restart) | Compressed Week 1 | Medium | Prioritise skeleton and contracts; carry non-critical items forward visibly | Priyanka / Aryan |
| R12 | Real data accidentally used | Governance breach | Low | Synthetic fixtures only; banner; reviews | All |

---

## 18. Definition of Done

### 18.1 Any deliverable **[Source]**
- Linked to an approved user story, requirement or decision
- Acceptance criteria satisfied with evidence in the repository
- Relevant peer review complete; comments resolved or recorded
- Affected tests, documentation, interfaces and migration notes updated
- Security, data, AI and UX impacts reviewed where applicable
- Known limitations and unresolved risks stated, not hidden
- Designated reviewer has accepted, or explicitly carried it forward

### 18.2 Frontend-specific additions **[Proposed]**
- [ ] All Section 9 states implemented and evidenced
- [ ] Works with keyboard only; axe shows no serious/critical violations
- [ ] Responsive at phone, tablet and laptop widths
- [ ] Role behaviour verified for all three roles
- [ ] Uses the real API (no hidden mock dependency)
- [ ] No console errors or sensitive logging
- [ ] No secrets; lint, type-check and tests pass
- [ ] Component documented in `COMPONENTS.md` (if reusable)

### 18.3 Defect severity **[Source]**
| Severity | Meaning | Required action |
|---|---|---|
| Critical | Exposes unauthorised data/action, risks data loss, breaks the priority journey, or makes the pilot unsafe to demo | Must be closed before acceptance |
| High | Blocks a major MVP function or yields materially incorrect decisions | Closed, or approved documented workaround, before final review |
| Medium/Low | Does not block the priority journey | Stays visible in the defect/limitation register with a recommended next action |

---

## 19. Final Handover Checklist (Frontend)

- [ ] Repository merged, tagged final build, clean history
- [ ] `README.md` and `SETUP.md`: reproducible local and staging run, verified by a peer on a clean machine
- [ ] Environment variable names documented (no values)
- [ ] `COMPONENTS.md` covering the full library
- [ ] `CONTRACTS.md` and the contract register matching the API docs
- [ ] `DECISIONS.md` of frontend decisions
- [ ] `LIMITATIONS.md`: known defects, unsupported browsers, accessibility gaps, non-production caveats
- [ ] Frontend test report: unit, component, E2E, accessibility
- [ ] Demo script, demo accounts per role, data-reset procedure
- [ ] Dependency inventory with licences
- [ ] Phase 2 frontend backlog with priorities
- [ ] Input to the QA pack (traceability), security pack (frontend findings and remediation), and Aryan's governance pack

---

## 20. My Part of the Final Demonstration

Frontend responsibility within the eight-step live demo **[Source steps]**:

1. Sign in as an authorised user; show role-aware navigation.
2. Create and review a supplier and product record.
3. Complete a China-readiness assessment; show missing-information or review status.
4. Create a buyer requirement and run explainable matching.
5. Review ranked candidates, criteria, warnings and the rules-only fallback position.
6. Record the human disposition; convert the accepted result into an opportunity.
7. Show the pipeline, dashboard, unresolved items and audit history.
8. Demonstrate **one denied permission case** and **one controlled service-failure or fallback case**.

**Demo readiness rules:** two clean rehearsals; reset data; accounts per role prepared; a pre-recorded backup of each step in case staging fails.

---

## 21. Open Questions to Resolve

| # | Question | Ask | Needed by |
|---|---|---|---|
| Q1 | Which dates and role assignments are final? Will the Build Manual be reissued? | Aryan | Week 1 |
| Q2 | Is the proposed frontend stack (Section 5.2) approved? | Senior Technical Mentor | Week 1 |
| Q3 | Is an admin user-management screen in scope for the MVP, or handled by the backend or seed only? | Adrika / BNCS | Week 2 |
| Q4 | Final permission matrix per role (Section 6.2) | Adrika, Abhishek, Ajendra | Week 2 |
| Q5 | Auth mechanism and token/session storage design | Abhishek, Ajendra | Week 1 to 2 |
| Q6 | Is an OpenAPI spec available for typed client generation? | Abhishek | Week 1 |
| Q7 | Readiness questionnaire content, scoring and statuses | Adrika, BNCS | Week 3 (approval Week 4) |
| Q8 | Exact opportunity stages and allowed transitions | Adrika, BNCS | Week 5 |
| Q9 | Dashboard metric definitions | Adrika, Vishal | Week 5 |
| Q10 | Which Mandarin-ready fields exist and who reviews/approves translations? | Adrika, BNCS | Week 3 |
| Q11 | Staging environment URL, access, and deployment ownership for the frontend | Aryan, Mentor | Week 2 |
| Q12 | Browser support matrix | Mentor | Week 3 |
| Q13 | Does the frontend need a visible match-run history or only the latest run? | Adrika, Alok | Week 4 |

---

*This plan is a living document. Update it every Friday after the Sprint Review: tick completed items, move carry-forwards with reasons and new dates, and record changes in `DECISIONS.md`.*
