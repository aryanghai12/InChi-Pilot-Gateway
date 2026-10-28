# AGENTS.md — InChi Pilot Gateway

This is the shared instruction manual for every team member and every AI coding agent working in this repository. It covers project rules and all eight role definitions, and it is the single source of truth for both.

- **What to build:** [`docs/MVP_FEATURES.md`](docs/MVP_FEATURES.md). It defines modules `M1` to `M11`, acceptance criteria, permissions, the matching process and open decisions `D-xx`.
- **How to build it:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). It sets out the stack, the repository layout and **who owns each area** (§4), the backend, frontend and matching conventions, CI, the technical decision record (§9) and the deviations from the build manual still awaiting approval (§10).
- **Current roles:** §C below, taken from `docs/InChi_Pilot_User_Delivery Ownership (revised).pdf`, effective 26 October 2026.
- **Daily progress:** [`docs/daily-reports/`](docs/daily-reports/README.md). Every member records their own work each working day (§B rule 15).
- `CLAUDE.md` only points here. Do not copy rules into other instruction files. Change them here.

---

## A. Project context

**What InChi is.** InChi Pilot Gateway v0.1 is a private internal web application for authorised users at BNCS Biz N Consumer Solutions Pte Ltd. It helps them organise supplier and product information, assess supplier readiness for China-related market development, capture buyer requirements, review explainable AI-assisted supplier matches, and track the resulting commercial opportunities.

**What it is not.** It is not a public marketplace, a public website, a production system, or a legal, regulatory or compliance tool. It is a **supervised, non-production pilot**, built by eight interns over eight weeks (26 Oct to 18 Dec 2026, per the revised timeline).

**End-to-end workflow (the priority journey):**

1. An authorised user signs in to a role-aware workspace.
2. The user creates or updates supplier and product records.
3. The user completes a China-readiness assessment, and a Reviewer records the outcome.
4. The user records a buyer requirement, with mandatory criteria kept separate from preferences.
5. The platform applies mandatory eligibility filters, then approved weighted scoring, then a bounded semantic similarity signal.
6. The platform shows ranked candidates with explanations and missing-information warnings.
7. An authorised person reviews the results and records a disposition with a reason.
8. An accepted match can become a tracked opportunity.
9. Users see a dashboard built from stored records and can trace material actions in the audit history.

**Principles (from the build manual):** a human approves before anything has consequences, because AI only advises. Mandatory rules apply before similarity. Every recommendation is explained. Access is least-privilege. Only synthetic or approved data is used. Every material action is auditable. English comes first; the data is Mandarin-ready, but there is no bilingual UI. Components must be replaceable.

**Out of scope** (full list in MVP_FEATURES §2): public access or registration, external buyer or supplier accounts, payments and contracts, legal, tax or customs certification, a full Mandarin UI or machine translation, unapproved integrations, mobile apps, extra microservices, production deployment, and real or confidential data.

**How success is judged.** Success means the full priority journey can be demonstrated on synthetic data, with its limitations stated honestly, including one denied-access case and one fallback or failure case, plus clean handover packs. The cohort is judged on evidence, reliability, usability and reusability, not on how much code it writes.

**Current repository state.** As of 28 Oct 2026 the repository contains documentation only. No application code, build tooling, tests or CI exist yet. Do not describe planned features as implemented.

**Technology stack (team-selected, revised 28 Oct 2026; D-01).** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) is authoritative for the stack, layout, ownership, conventions and technical decisions. This table is a summary only.

| Layer | Choice |
|---|---|
| Frontend | **Next.js (App Router), React, TypeScript.** TanStack Query, plain CSS Modules. Next.js renders pages and proxies `/api/` to Django; it holds no business logic, authorisation or secrets. |
| Backend | **Python 3.12, Django 5.2 LTS, Django REST Framework.** Session auth and CSRF from Django. OpenAPI via drf-spectacular. |
| Database | **PostgreSQL 17 with pgvector.** The Django ORM and Django migrations are authoritative for the schema, including the extension and vector columns. |
| Matching | **In-process Python package** in the backend (`backend/apps/matching/engine/`) with no Django imports. Deterministic rules-based matching is the baseline. Semantic similarity is optional and bounded. |
| Embeddings | **`sentence-transformers`**, run locally, optional install. **Embedding model: TBD (D-11).** |
| LLM | **None in v0.1. Provider and model TBD (D-20).** Not a prerequisite for the MVP. |
| Tests | pytest + pytest-django; Vitest + React Testing Library; Playwright for E2E |
| Tooling | Ruff; ESLint, Prettier, `tsc`; pip-audit, npm audit, gitleaks, Dependabot; GitHub Actions |
| Environment | Docker Compose: `db` (PostgreSQL 17 + pgvector), `backend` (Django), `frontend` (Next.js). The browser uses one origin. |

**Approval status.** The build manual makes the final stack and any material deviation subject to BNCS and technical-mentor approval. **That approval is still pending** (ARCHITECTURE.md §10). The deviations are:

- Django instead of Spring Boot;
- in-process matching instead of a separate FastAPI service;
- hosted staging made optional.

Build reversible skeletons on this stack meanwhile, and never describe it as approved.

**Never select an embedding model or an LLM in code, configuration defaults, examples or documentation.** Both stay TBD until D-11 and D-20 are recorded in ARCHITECTURE.md §9.

Build on this stack only. Adding a language, framework, database, service or hosted dependency needs a new entry in ARCHITECTURE.md §9.

---

## B. Shared engineering rules

These apply to every role.

1. **Read before you write.** Read the relevant code, this file, MVP_FEATURES and any interface contract before changing anything. Follow the existing structure, naming and idioms.
2. **Stay in scope.** Build only what an `M#` module and its acceptance criteria require. If something is useful but not listed, propose it as Phase 2 and do not build it.
3. **Respect ownership.** Change files in another member's area only when the task needs it. Tag the owner and get their review. Owners, reviewers and coordination triggers are in [ARCHITECTURE.md §4](docs/ARCHITECTURE.md#4-repository-layout-and-ownership).
4. **Follow contracts.** API contracts, data contracts and the matching contract are agreed between their owners and recorded in the interface register. Do not change one on your own. Any change must be versioned or backward-compatible, and every consumer must be informed.
5. **Keep PRs small and focused.** Each PR has one purpose and links to an issue and an `M#-AC#` ID. Do not include unrelated refactors, formatting churn or speculative abstractions.
6. **Tests and documentation come with the change.** Add or update the tests that prove the acceptance criteria, including denied and failure paths. Update setup notes, contracts and the data dictionary when they are affected.
7. **Protect secrets and data.**
   - Do not hardcode credentials, keys or tokens anywhere, including tests, examples and documentation.
   - Configuration comes from environment variables. Commit an `.env.example` with placeholder values only, and git-ignore real `.env` files.
   - Use synthetic data only. Never use real personal data, identity documents, client files or production credentials.
   - Do not paste confidential material into public AI services.
   - Never log secrets, tokens or passwords.
8. **Add dependencies carefully.** Each new library needs a reason in the PR, a licence that permits use, and an active maintainer. Prefer what the framework already provides.
9. **Don't invent business rules.** Readiness criteria, eligibility rules, weights, decision labels, opportunity stages and metric definitions need BNCS approval (D-03 to D-08). Until they are approved, use configuration clearly marked `UNAPPROVED` placeholder and record the assumption in the PR.
10. **The backend is the authority.** Authorisation, validation and workflow transitions are enforced on the server. UI checks only help usability.
11. **Design audit in from the start.** Every material create, edit, status change, review and decision writes an audit event, as part of the same change.
12. **Decide technical matters; escalate business matters.**
    - **Within your area:** make routine, reversible implementation choices yourself and note them in the PR.
    - **Stack-level changes** (new language, framework, service, database or hosted dependency): record them in ARCHITECTURE.md §9, reviewed by the affected owners and Ajendra.
    - **Business-owned decisions** go to BNCS through Aryan. These are commercial policy, readiness criteria, eligibility rules, weights, decision labels, opportunity stages, metric definitions, role permissions, scope and pilot acceptance.
    - **Material residual security risk** is accepted by BNCS or the mentor, not by the team.
13. **Report truthfully.** Never claim a test passed unless you ran it and it passed. Say what was not tested.
14. **Raise blockers quickly.** If blocked for more than 24 hours, raise it in the team channel and tag Aryan plus the dependency owner. Do not work around authority, architecture, data, AI-governance or security blockers in undocumented ways.
15. **Record your own work every working day.** Add an entry to your own file in [`docs/daily-reports/`](docs/daily-reports/README.md). An entry covers what you completed (with its state and evidence), what is in progress, the tests and checks you actually ran, your blockers and dependencies, and your next steps. Write `No update.` when there is nothing to report. Separate completed work from planned work, and never invent accomplishments or results. Never write in another member's file. The workflow and template are in that folder's README.

### Repository layout and ownership

Only `README.md`, `AGENTS.md`, `CLAUDE.md` and `docs/` (including `docs/daily-reports/`) exist today. The agreed target layout, the purpose of each directory, where code and tests go, every area's owner and reviewers, and when to coordinate with whom are all in **[ARCHITECTURE.md §4](docs/ARCHITECTURE.md#4-repository-layout-and-ownership)**. That section is the single source of truth for ownership. The "Owns" line in each role section below must agree with it.

Create each directory when your work begins. Do not create empty placeholder folders.

### Branches, commits and PRs

- Branch names follow `<area>/<short-description>`, for example `frontend/supplier-list`, `backend/rbac-object-checks` or `docs/field-dictionary-v1`. Weekly daily-report branches are `reports/<first-name>-week-<n>` (see `docs/daily-reports/README.md`).
- No direct pushes to `main`. Every change goes through a PR with at least one relevant peer review. Critical artefacts are never self-approved.
- Every PR description contains:

```
Requirement: M#-AC# (and issue link)
What changed:
Tests run (command → actual result):
Not tested / known limitations:
Assumptions or UNAPPROVED placeholders used:
Interfaces affected (and owners notified):
Reviewers:
```

---

## C. Current roles and individual build prompts

**Source of truth:** `docs/InChi_Pilot_User_Delivery Ownership (revised).pdf`, effective 26 October 2026. The build manual's role table is **out of date**. It swaps Aryan and Ajendra (see MVP_FEATURES DS-01). Never apply the manual's role names.

| Team member | Current role | `@role` aliases |
|---|---|---|
| Aryan Ghai | Technical Project Coordinator, Product Operations and Integration Governance | `coordinator`, `governance`, `pm` |
| Ajendra Nath Tripathi | Cybersecurity and DevSecOps Engineer | `security`, `devsecops` |
| Adrika T Kumar | Product UX and Commercial Workflow Analyst | `ux`, `product`, `workflow` |
| Priyanka Singh | Frontend Web and Client-Side Integration Engineer | `frontend` |
| Abhishek Kumar | Application Backend and Access-Control Engineer | `backend` |
| Vishal Chauhan | Data and Platform Services Engineer | `data`, `db` |
| Alok Tiwari | AI Matching and Data Intelligence Engineer | `ai`, `matching` |
| Harish Pal | QA and Test Automation Engineer | `qa`, `test` |

**Shared integration ownership.** There is no single full-stack integrator.

| Area | Owner |
|---|---|
| Workflow clarity and acceptance logic | Adrika |
| Client-side integration | Priyanka |
| Application services and access control | Abhishek |
| Data contracts | Vishal |
| Matching service | Alok |
| Independent verification | Harish |
| Security review | Ajendra |
| Dependency and integration governance | Aryan |

**Approvers above the team** (from the internship brief):

| Approver | Responsibility |
|---|---|
| BNCS Programme Sponsor | Final acceptance |
| BNCS Product and Venture Lead | Product priorities, workflows and scope |
| Senior Technical Mentor | Architecture and technical decisions |

---

### C1. Aryan Ghai — Technical Project Coordinator, Product Operations and Integration Governance

**Primary responsibility.** Keep delivery visible and integrated. That covers sprint cadence, the backlog, risks, dependencies, decisions, interface coordination, integration evidence and review packs. The outcome is that each Friday shows one integrated product with evidence, and handover is never rebuilt at the last minute.

**Owns:** `docs/governance/` and the daily-report process (`docs/daily-reports/README.md`), plus maintaining `README.md`, `AGENTS.md` and `CLAUDE.md`. Also the backlog and project board (D-18), the change record for `docs/MVP_FEATURES.md`, and the records in ARCHITECTURE.md §9 and §10. Writes only Aryan's own daily-report file.

**Interfaces.** Works with every member. Chairs Monday Sprint Start and Friday Sprint Review, and prepares the weekly report for BNCS. Escalates business decisions to BNCS and material security risk to BNCS or the mentor. Records technical decisions in ARCHITECTURE.md §9.

**MVP tasks, in order:**

1. **Week 1.**
   - Set up the backlog with one issue per `M#` module and acceptance criterion, each with owner, due date, evidence location and reviewer.
   - Create the registers: risk, issue, dependency, decision (seeded with D-01 to D-20 and DS-01 to DS-16), API and interface contract, and integration issues.
   - The technical decisions are recorded in ARCHITECTURE.md §9 with their status. Present the build-manual deviations in ARCHITECTURE.md §10 to the mentor and BNCS at the Week 1 Sprint Review, and **ask for approval**. Record each outcome with approver and date. Do not mark anything approved without that record. Keep the embedding model (D-11) and LLM (D-20) visibly open.
   - Get the business decisions D-02 and D-19 answered by BNCS this week, and D-09 (permissions) before the Week 2 auth work is finalised.
   - Set up GitHub Issues labels (module, severity, role, `daily-report`), the Project board, and branch protection on `main`. Once this baseline merges, start the daily-report routine (`docs/daily-reports/README.md`).
2. **Week 1.** Write the integration plan. It lists the contracts needed and their owners: frontend↔backend (generated OpenAPI), API layer↔models (Abhishek and Vishal), orchestration↔matching engine (the `engine.run()` dataclasses: Abhishek and Alok), audit-event schema. Include the dates each must be agreed.
3. **Week 2.** Track blockers, lock interface versions, and coordinate the Gate 1 integrated demo (6 Nov).
4. **Weeks 3 and 4.** Track dependencies and interface changes, and build the weekly evidence index. Run the **Gate 2 rule-approval gate** (20 Nov): fields, rules, criteria and interfaces must be approved before AI integration. Record the decisions.
5. **Weeks 5 and 6.** Run the integration and evaluation review. Prepare the **feature-freeze decision pack** for Gate 3 (4 Dec).
6. **Week 7.** Track UAT, defect triage and acceptance.
7. **Week 8.** Own the demo runbook, the handover index, the final report and the Phase 2 backlog.
8. **Every working day.** Check each member's open daily-report PR for the previous working day's entry, and send reminders for missing ones. List entries still missing at the next check in the weekly report. Never write another member's entry. Use the reports, with their linked evidence, as input to the Friday review and the weekly BNCS report.

**Must not decide alone.** Product policy, commercial rules, security-risk acceptance and release. Stack changes go through an ARCHITECTURE.md §9 entry reviewed by the affected owners. Does not write application features in other members' areas, and does not mark another member's work accepted without their reviewer.

**Evidence before done.** Registers are current. Every open decision has an approver and a date. Every Friday has a review record linking to working artefacts and test results. The handover index resolves to real files.

**Definition of Done.** Shared DoD (§F), plus: every governance artefact sits in `docs/governance/` and is linked from the weekly report.

**Build prompt:**

```
Role: Aryan Ghai | Technical Project Coordinator, Product Operations and Integration Governance

Read AGENTS.md, docs/MVP_FEATURES.md and docs/ARCHITECTURE.md (§4, §9, §10) first.
Act within my coordination role:
I coordinate delivery; I do not approve product policy, security risk or release, I
record (not invent) technical decisions in docs/ARCHITECTURE.md §9, and I do not
implement features in other members' areas.

Task: <describe, e.g. "create the Week 1 decision register and integration plan">

Do the following:
1. Inspect docs/governance/ and the current backlog/issues for existing material; extend
   rather than duplicate.
2. Map every item to an M#-AC#, D-xx or DS-xx ID from docs/MVP_FEATURES.md.
3. For every task or decision record: owner (from AGENTS.md §C), due date (revised
   timeline, MVP_FEATURES §13), acceptance criterion, evidence location, reviewer, approver.
4. Flag dependencies between members and contracts that are not yet agreed.
5. Use plain Markdown tables in docs/governance/; no new tools or services.
6. Do not present recommendations as approved decisions; mark status Open/Approved
   with approver and date.
Report: files changed, open decisions needing escalation this week, blockers, next step.
```

---

### C2. Ajendra Nath Tripathi — Cybersecurity and DevSecOps Engineer

**Primary responsibility.** Owns the security workstream: threat model, data classification, access-control review, secrets baseline, dependency and configuration checks, negative testing and remediation tracking. The outcome is no critical unresolved access-control defect at acceptance, and a clear residual-risk statement. **Technical owners implement fixes.** Ajendra validates them and escalates risk.

**Owns:** `docs/security/`, the security and dependency jobs in `.github/workflows/`, `.gitignore` (secrets baseline), and security test cases (shared with Harish).

**Interfaces.**

- **Abhishek:** auth, RBAC, sessions and error handling.
- **Vishal:** data protection, backups, audit integrity.
- **Alok:** AI-service threats, input manipulation, leakage.
- **Priyanka:** client-side storage and token handling.
- **Harish:** negative test automation.
- **Aryan:** remediation tracking and escalation.

**MVP tasks, in order:**

1. **Week 1.**
   - **Threat model**, covering broken access control, insecure direct object access, session abuse, unsafe input, manipulation of matching inputs, data leakage and insecure configuration.
   - **Data classification** of every entity in MVP_FEATURES §6.
   - **Access-control matrix** derived from MVP_FEATURES §5.
   - **Secrets baseline**: a `.gitignore` that excludes real environment files but keeps the committed example (`.env`, `.env.*`, `!.env.example`), a convention for `.env.example` (placeholder values only), and secret scanning on the repository.
2. **Week 2.** Auth threat review. Cover:
   - login CSRF protection (TD-05) and 401/403 semantics (TD-06);
   - session rotation on login, the restricted admin, and `create_platform_admin` (TD-08);
   - the Next.js single-origin proxy (TD-09): the rewrites, `CSRF_TRUSTED_ORIGINS`, `ALLOWED_HOSTS` and proxy headers;
   - the rendering boundary (TD-10): no secrets, Route Handlers, Server Actions or authorisation logic in Next.js.

   Write denied-access and object-boundary (IDOR) test cases with Harish. Review the auth, secrets and dependency choices in the first skeletons.
3. **Week 2 onward.** Add the security jobs in ARCHITECTURE.md §8 to CI: `pip-audit`, `npm audit --audit-level=high`, gitleaks, and `manage.py check --deploy` against the non-dev settings. Add `.github/dependabot.yml` for pip, npm and GitHub Actions. Review the Django security settings in `backend/config/` (cookies, CSRF, `DEBUG`, `ALLOWED_HOSTS`, the admin path). Decide on login throttling (TD-04).
4. **Week 3.** Review the registry and evidence-metadata handling. Evidence is metadata only (D-10, resolved).
5. **Week 4.** Review data flow, access and permissions for readiness and requirement workflows, including unauthorised review and status changes.
6. **Week 5.** Matching threat review: manipulated inputs, unsafe logging and match-review permissions. Also cover the embedding model proposal (D-11, model TBD): licence, `trust_remote_code` never enabled, only model weights downloaded, Hub telemetry off, no pilot data leaving the machine. Review the size and licences of the `sentence-transformers` and PyTorch dependencies. Confirm that no LLM dependency or configuration has been added (D-20).
7. **Week 6.** Security regression and configuration lock. Review the security headers set in `next.config.ts`, the Compose reference environment and backup protection. If BNCS provides hosted staging (D-16), run the staging checklist before it is used.
8. **Week 7.** Review access, secrets and dependencies, and verify each remediation.
9. **Week 8.** Deliver the security pack: threat model and data-flow view, classification, access matrix, scan evidence, remediation register, secure staging checklist and **residual-risk statement**.

**Must not decide alone.** Accepting material residual risk (BNCS or the mentor does), or certifying the platform as production-secure. Do not rewrite another owner's code to fix a finding. Provide a failing test or proof plus remediation guidance, and let the owner implement it. Do not run intrusive tests against any environment that is not the team's own non-production setup.

**Evidence before done.** Each finding is recorded with severity, owner, status and retest result. Each scan has the command and output saved. Each negative test is automated or documented with its result.

**Definition of Done.** Shared DoD, plus: the remediation register is current, and no critical access-control finding is open without an approved disposition.

**Build prompt:**

```
Role: Ajendra Nath Tripathi | Cybersecurity and DevSecOps Engineer

Read AGENTS.md, docs/MVP_FEATURES.md (§5 permissions, §8 security) and
docs/ARCHITECTURE.md (§5 backend conventions, §8 CI and secrets) first.
I own security review, threat modelling, secrets baseline, dependency/config checks,
negative tests and remediation tracking. Technical owners implement fixes; I validate.

Task: <describe, e.g. "draft the threat model and access-control matrix for M1–M10">

Do the following:
1. Inspect existing code, configs, CI and docs/security/ before writing.
2. Base the access matrix on MVP_FEATURES §5; mark anything not approved as OPEN (D-09).
3. Cover: broken access control, IDOR, session abuse, unsafe input, input/prompt
   manipulation of matching, data leakage, insecure configuration, secrets in repo.
4. For findings, record: ID, severity (Critical/High/Medium/Low per build manual),
   affected component, owner, reproduction, recommended fix, status, retest evidence.
5. Negative tests: write them as pytest API tests (backend/apps/<app>/tests/) or
   Playwright cases where the code exists, otherwise as precise manual cases for
   Harish to automate. Security tooling is fixed in ARCHITECTURE.md §1; don't add
   another scanner without a §9 entry.
6. Do not modify other owners' application logic; propose fixes or failing tests.
7. Do not claim production security or certification. Run only non-intrusive checks
   against our own non-production environment.
Report: files changed, findings by severity, checks run with actual results, items
needing BNCS/mentor risk decisions.
```

---

### C3. Adrika T Kumar — Product UX and Commercial Workflow Analyst

**Primary responsibility.** Defines workflow intent: user journeys, the field dictionary, wireframes, user stories, workflow states, acceptance criteria, usability, and human-review requirements. The outcome is that engineers and QA can tell what correct behaviour is without guessing. **BNCS keeps approval of material commercial and policy matters.**

**Owns:** `docs/product/` and the requirement content of `docs/MVP_FEATURES.md`.

**Interfaces.**

- **Priyanka:** screens and states.
- **Abhishek:** transitions and permissions.
- **Vishal:** field meanings and data dictionary.
- **Alok:** match inputs, explanation language, criteria drafts.
- **Harish:** acceptance criteria to tests, UAT.
- **Aryan:** decision register, BNCS approvals.

**MVP tasks, in order:**

1. **Week 1.**
   - **Field dictionary v1** for Supplier, Product, Evidence, Assessment and Buyer Requirement. Use the reduced column set in MVP_FEATURES §9 #45. Mark required-at-draft and required-at-submission separately.
   - **Workflow state maps** for every object in MVP_FEATURES §4.
   - Refine acceptance criteria for M1 to M3.
   - Bring D-02 (pilot sector and categories) to BNCS.
2. **Week 2.** Validate the supplier and product flow in the integrated build, and confirm acceptance scenarios with Harish.
3. **Week 3.** Draft the **readiness questions**, missing-information states and corrective-action text for BNCS approval (D-03). Draft the Mandarin-ready field list (D-14).
4. **Week 4.** Draft the **buyer-demand fields, mandatory eligibility criteria and weighted preference criteria** for BNCS approval at Gate 2 (D-04, D-05, D-13, D-15). Propose the disposition vocabulary (D-06).
5. **Week 5.** Define the result language, explanation wording, warnings and the disposition flow.
6. **Week 6.** Define opportunity stages and dashboard metric definitions (D-07, D-08), and validate the full journey.
7. **Week 7.** Run UAT and usability sessions. Approve only corrections within frozen scope.
8. **Week 8.** Deliver the product-UX pack, user guide, experience limitations and Phase 2 recommendations. Update the blueprint roadmap dates (DS-02).

**Must not decide alone.** Commercial policy, readiness criteria, eligibility rules, weights, decision labels or opportunity stages. Draft these and mark them `Proposed` until BNCS approves. Do not change the frozen scope after Week 6. Do not specify implementation technology.

**Evidence before done.** Each artefact is versioned in `docs/product/`, reviewed by the affected engineers, with BNCS approval recorded for policy items. Every acceptance criterion is testable.

**Definition of Done.** Shared DoD, plus: each requirement has an ID that Harish can trace, and unapproved items are visibly marked.

**Build prompt:**

```
Role: Adrika T Kumar | Product UX and Commercial Workflow Analyst

Read AGENTS.md, docs/MVP_FEATURES.md and the blueprint PDF in docs/ first.
I define workflow intent, fields, states and acceptance criteria. BNCS approves
material commercial and policy decisions; I must not invent them.

Task: <describe, e.g. "produce field dictionary v1 for Supplier and Product">

Do the following:
1. Start from MVP_FEATURES (modules, simplifications, §9 audit) — not the full blueprint
   scope; anything the audit marked SIMPLIFY/DEFER/REMOVE stays that way unless BNCS
   approves otherwise.
2. Write Markdown in docs/product/. Use stable IDs (field IDs, state IDs, M#-AC#).
3. For every field: label, api_name, type, required-at (draft/submission), allowed
   values, validation, sensitivity, owner, approval status (Proposed/Approved).
4. For every workflow: states, allowed transitions, who may perform each (per
   MVP_FEATURES §5), required reason/comment, audit event produced.
5. Write acceptance criteria as testable Given/When/Then including empty, error,
   denied and fallback cases.
6. Mark every rule, weight, label or stage that is not BNCS-approved as "Proposed – D-xx".
Report: files changed, items needing BNCS approval, questions for engineers, next step.
```

---

### C4. Priyanka Singh — Frontend Web and Client-Side Integration Engineer

**Primary responsibility.** Owns frontend delivery: the authenticated interface, reusable components, forms, client-side validation, journey screens, dashboards and client-side integration. Coordinates every service contract the interface uses. The outcome is a responsive, accessible UI that completes the priority journey against the real backend.

**Owns:** `frontend/`, a Next.js App Router app in React + TypeScript, using TanStack Query and CSS Modules (ARCHITECTURE.md §1, §7). This includes `next.config.ts` (rewrites to Django and security headers), `frontend/Dockerfile` and the `frontend` service in `docker-compose.yml`. Also frontend tests (Vitest + React Testing Library) and frontend setup documentation.

**Interfaces.**

- **Abhishek:** consumes the OpenAPI contract and the auth/session mechanism.
- **Adrika:** fields, states, wording, wireframes.
- **Alok:** how explanations and warnings are displayed.
- **Vishal:** dashboard data shapes, via Abhishek's API.
- **Harish:** E2E selectors and test hooks.
- **Ajendra:** client-side security review.

**MVP tasks, in order:**

1. **Week 1.** Frontend skeleton:
   - `create-next-app` with TypeScript, ESLint, the App Router and a `src/` directory, plus TanStack Query. Standalone output and a `frontend/Dockerfile`.
   - `next.config.ts` rewrites that forward `/api/`, the admin path and Django's static prefix to `BACKEND_ORIGIN`, so the browser sees one origin (TD-09). Agree the details with Abhishek and get Ajendra's review.
   - An authenticated `(workspace)` layout and the navigation shell for the MVP sections (MVP_FEATURES §9 #4). User management is in the restricted Django admin, so there is no frontend admin screen.
   - Shared form, table, status and empty-state components.
   - The `apiFetch()` wrapper: `X-CSRFToken` from the cookie and the standard error shape. Log out **only** on 401 `not_authenticated`. 403 `permission_denied` shows the access-denied state. 403 `csrf_failed` refreshes the token once and retries (ARCHITECTURE.md §7).
   - App Router routes with a `not-found.tsx`. Data pages are Client Components. There are no Route Handlers, Server Actions or `src/app/api/` directory (TD-10).
   - Types generated by `openapi-typescript` from `docs/api/openapi.yaml`.
   - npm scripts for `lint`, `typecheck`, `test` and `build`.
2. **Week 2.** Login and logout (session cookie, no tokens, `GET /api/v1/auth/csrf/` before the login form), route guards driven by `/api/v1/auth/me/`, role-aware navigation, supplier and product create, edit and detail screens, all UI states. Gate 1.
3. **Week 3.** Registry list, search and filters. **[DEFERRABLE]** pagination UI and duplicate-warning display (MVP_FEATURES §2). Readiness assessment UI with the missing-information list.
4. **Week 4.** Readiness review screen for Reviewers. Buyer requirement form with the mandatory/preference distinction and the completeness gate.
5. **Week 5.** Match request, ranked results, per-criterion breakdown, explanation, warnings, fallback label and disposition screens.
6. **Week 6.** Opportunity list and detail, dashboard, audit and history views. Security headers in `next.config.ts` for Ajendra's review. Stabilise integration. Feature freeze.
7. **Week 7.** Fix approved UI defects. Accessibility (keyboard, labels, contrast, focus), responsiveness, perceived speed.
8. **Week 8.** Frontend documentation, component notes, limitations, stable demo.

**Must not decide alone.** API shapes (agree them with Abhishek), business rules or scores (never compute eligibility or scores client-side), or authorisation. UI hiding is not access control.

Do not:

- store tokens or secrets in `localStorage`, in `NEXT_PUBLIC_*` variables or in client bundles;
- turn Next.js into a second backend. That means no Route Handlers, Server Actions, middleware authorisation or direct database access;
- change the rewrites, cookie or CSRF handling without Ajendra's review;
- add a UI framework, global state library or form library without an ARCHITECTURE.md §9 entry;
- build pages outside MVP_FEATURES.

**Evidence before done.** Component and page tests pass locally. Each screen shows loading, empty, error, denied and success states. A screenshot or recording goes in the PR for each new screen. Lint and type-check are clean.

**Definition of Done.** Shared DoD, plus: the screen works against the real backend (or a contract-matching mock, labelled as such), and success messages appear only after the server confirms.

**Build prompt:**

```
Role: Priyanka Singh | Frontend Web and Client-Side Integration Engineer

Read AGENTS.md, docs/MVP_FEATURES.md, docs/ARCHITECTURE.md (§1, §7) and
docs/api/openapi.yaml (if present) first.
I own frontend/ (Next.js App Router, React + TypeScript, TanStack Query, CSS
Modules) and client-side integration. The Django backend is the authority for
auth, permissions, validation and scoring; Next.js only renders and proxies /api/.

Task: <describe, e.g. "build the supplier list with search and filters (M2-AC3)">

Do the following:
1. Inspect frontend/ structure, existing components and the API contract before coding;
   reuse existing components and patterns.
2. Implement only the screens/fields in the referenced M#-AC# and Adrika's field
   dictionary; mark gaps as questions, don't invent fields. Build [DEFERRABLE] items
   only after the mandatory parts of the module work.
3. Every view: loading, empty (with guidance), error (structured message), access-denied,
   success-after-server-confirmation; plus fallback/conflict where relevant.
4. Call only documented endpoints; if one is missing, write down the needed contract
   for Abhishek instead of mocking silently. Label any mock clearly.
5. Accessibility: labels, keyboard, focus, contrast; responsive layout.
6. Use apiFetch() and TanStack Query for all server calls (same-origin session cookie +
   X-CSRFToken), from Client Components. No secrets or tokens in client storage,
   NEXT_PUBLIC_* variables or bundles; no client-side scoring or authorisation logic;
   no Route Handlers or Server Actions. No new UI/state/form libraries.
7. Add/update Vitest + React Testing Library tests; run `npm run lint`, `npm run
   typecheck` and `npm run test` and report actual output.
Report: files changed, tests run with results, contract questions, limitations, next step.
```

---

### C5. Abhishek Kumar — Application Backend and Access-Control Engineer

**Primary responsibility.** Owns the application services: authentication, RBAC with object-level checks, application APIs, workflow states and transitions, request validation, structured errors, match orchestration, and backend integration tests. The outcome is a secure, consistent API that enforces every rule in MVP_FEATURES. **Security review stays with Ajendra.**

**Owns:** the Django and DRF application layer: `backend/config/` and, in every app, serializers, views, permissions, services and URLs (ARCHITECTURE.md §4, §5). Models, migrations and seed data are Vishal's. The matching engine is Alok's. Also the generated `docs/api/openapi.yaml`, `requirements*.txt` (except the semantic extra), `backend/Dockerfile`, `docker-compose.yml` (with Vishal for `db` and Priyanka for `frontend`), `.env.example`, and backend setup notes.

**Interfaces.**

- **Priyanka:** API contract.
- **Vishal:** schema, repositories, migrations, audit storage.
- **Alok:** the `engine.run()` interface, provider selection, fallback and failure handling.
- **Ajendra:** auth design review, remediation.
- **Harish:** integration and contract tests.
- **Adrika:** transitions and permissions.

**MVP tasks, in order:**

1. **Week 1.**
   - Django 5.2 project skeleton under `backend/` with `config/` settings read from environment variables, DRF, drf-spectacular, Ruff and pytest-django configured, and a health endpoint.
   - The **custom `User` model with a `role` field**, agreed with Vishal, in the very first migration.
   - The conventions in ARCHITECTURE.md §5 as code: `SessionAuthentication`, deny-by-default permissions, the structured exception handler, the correlation-ID middleware, `version` conflict handling, pagination, and `accounts/policy.py` holding the whole `UNAPPROVED` permission matrix.
   - The exception handler maps `NotAuthenticated` to **401** `not_authenticated`, keeps permission denials at 403 `permission_denied`, and returns CSRF failures as 403 `csrf_failed` (TD-06).
   - The URLconf: `/api/v1/` with JSON 404s for unmatched `/api/` paths, the admin path, admin static files and the health endpoint. There is no frontend catch-all, because Next.js serves the UI (TD-09, which supersedes TD-07).
   - Proxy-aware settings from environment variables: `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SECURE_PROXY_SSL_HEADER` only behind a trusted HTTPS proxy. Ajendra reviews them.
   - `backend/Dockerfile` and a `docker-compose.yml` (`db`, `backend`, `frontend`) with Vishal and Priyanka.
   - `.env.example`. It includes `SEMANTIC_PROVIDER=none` and an **empty** `EMBEDDING_MODEL` marked "TBD (D-11)", and has no LLM variables (D-20).
2. **Week 2.** The `csrf` (with `ensure_csrf_cookie`), `login` (explicit `csrf_protect`; TD-05), `logout` and `me` endpoints. The `create_platform_admin` management command (TD-08). role and object-level authorisation, the restricted Django admin for user management (`platform_admin` only, `User` model only, path from environment), and validated supplier and product APIs that emit audit events. Generate `docs/api/openapi.yaml`. Gate 1.
3. **Week 3.** Registry search and filter APIs (using Vishal's queries) and the readiness assessment services with transitions.
4. **Week 4.** Readiness review and buyer-requirement APIs: completeness gate, versioning, workflow transitions, reviewer actions.
5. **Week 5.** Match orchestration in `matching/services.py`, following ARCHITECTURE.md §6. It checks the requirement gate, selects the provider from `SEMANTIC_PROVIDER`, and embeds the requirement text when a provider is available. It then loads candidates through Vishal's query, with pgvector similarity when a vector is available, and calls `engine.run()`. It persists the run, results and audit event in one transaction. If the engine raises, the run is stored as `failed` with no results. Disposition API with permissions and traceability. The API rejects `Accepted` for any candidate that is not eligible under the run's criteria version (M7-AC5).
6. **Week 6.** Opportunity APIs (create only from an accepted disposition, one opportunity per accepted disposition, with transitions), dashboard and audit APIs with access scoping. Feature freeze.
7. **Week 7.** Fix approved API, authorisation, validation and stability defects.
8. **Week 8.** API documentation, auth and RBAC notes, environment variables, backend setup and integration notes.

**Must not decide alone.** Schema changes (Vishal prepares them), business rules, weights or states (Adrika and BNCS), changes to the `engine.run()` interface (with Alok), or accepting security risk (Ajendra and the mentor). Never disable or weaken auth, CSRF or `DEBUG=False` to "unblock" testing, including to make the Next.js proxy work. Do not add queues, caches, extra services, token-based auth, CORS or any LLM integration without an ARCHITECTURE.md §9 entry.

**Evidence before done.** pytest API tests pass for allowed **and** denied paths, per role, on each endpoint. The OpenAPI drift check passes. Each material action has an audit-event assertion. The error format is consistent.

**Definition of Done.** Shared DoD, plus: the regenerated `docs/api/openapi.yaml` is committed in the same PR, and Ajendra has reviewed any auth, settings or security-sensitive change.

**Build prompt:**

```
Role: Abhishek Kumar | Application Backend and Access-Control Engineer

Read AGENTS.md, docs/MVP_FEATURES.md (§4, §5, §7, §8), docs/ARCHITECTURE.md (§4–§6)
and docs/api/openapi.yaml first.
I own the Django/DRF application layer: config/, serializers, views, permissions,
services, urls, auth, workflow transitions, validation, errors and match
orchestration. Vishal owns models/migrations; Alok owns matching/engine and
providers; Ajendra reviews security.

Task: <describe, e.g. "implement supplier CRUD API with object-level authorisation (M2, M1-AC3)">

Do the following:
1. Inspect backend/ conventions, existing security config, OpenAPI and the data model.
2. Enforce authentication, role permission and object-level access on every endpoint
   server-side, deny-by-default: anything not explicitly granted is refused. Return the
   structured error format (no stack traces).
   Use DRF SessionAuthentication, IsAuthenticated plus an explicit role permission
   class on every view, and object scoping in get_queryset()/has_object_permission().
   No permission is BNCS-approved yet (D-09). Put the whole MVP_FEATURES §5 matrix in
   accounts/policy.py marked UNAPPROVED; never hard-code role checks elsewhere.
   Implement unmarked entries as recommended and [OPEN] entries in the most
   restrictive reasonable way; list every policy entry you add or change in the PR.
   Do not remove UNAPPROVED until D-09 is recorded.
   Auth specifics (ARCHITECTURE.md §5): login view uses csrf_protect; NotAuthenticated
   → 401 not_authenticated; permission denial → 403 permission_denied.
   The backend enforces the rules regardless of what the frontend shows.
3. Validate all input in DRF serializers using the field dictionary; field-specific
   errors in the standard error shape.
4. Change state only through services.py transition functions; reject invalid
   transitions with a clear error. Enforce the `version` check (409 on conflict).
5. Call audit.services.record_event() inside the same transaction.atomic() as every
   material change; never log secrets.
6. If a model/schema change is needed, describe it for Vishal rather than editing
   models.py or migrations yourself.
7. Regenerate docs/api/openapi.yaml (manage.py spectacular) in the same change.
8. Add pytest API tests for allowed and denied paths per role; run `ruff check`,
   `ruff format --check` and `pytest` and report actual results.
Report: files changed, endpoints added/changed, tests run with results, contract or
schema requests, security items for Ajendra, next step.
```

---

### C6. Vishal Chauhan — Data and Platform Services Engineer

**Primary responsibility.** Owns platform data services: the relational schema, migrations, constraints, seed data, search, analytics and reporting queries, audit storage, data contracts, and backup and recovery evidence. The outcome is reliable, consistent data that every service can depend on. **Does not define commercial meaning alone.** Field meaning comes from Adrika and BNCS.

**Owns:** the Django data layer (ARCHITECTURE.md §4): `models.py` and `migrations/` in every app, `dashboard/queries.py` and candidate queries, and `backend/seed/` with the `seed_demo` management command. Also `docs/data/` (data dictionary, ERD, backup and recovery guide), the pgvector extension and vector-column migrations, and the PostgreSQL 17 + pgvector `db` service in `docker-compose.yml`.

**Interfaces.**

- **Abhishek:** repositories and queries used by the APIs.
- **Alok:** candidate queries, embedding storage, run and result storage.
- **Adrika:** field meanings.
- **Ajendra:** data classification, audit integrity, backup protection.
- **Harish:** seed data for tests, dashboard reconciliation.

**MVP tasks, in order:**

1. **Week 1.** Domain model and ERD from MVP_FEATURES §6. The `db` service on the `pgvector/pgvector` PostgreSQL 17 image, with the exact tag pinned. The custom `User` model with `role`, agreed with Abhishek, in the first migration. Initial models and migrations for suppliers and products. The `AuditEvent` model, plus a migration adding a PostgreSQL trigger that rejects `UPDATE` and `DELETE`. The seed-data plan.
2. **Week 2.** Models and migrations with constraints (foreign keys, not-null where approved, `CheckConstraint` for enums and units, a `version` field), the `seed_demo` command with synthetic data, and basic queries. Gate 1.
3. **Week 3.** Indexes, integrity rules, search (ORM `icontains` on indexed columns; no external search engine), readiness models, data dictionary v1.
4. **Week 4.** Buyer-requirement versioning, criteria storage, `CriteriaVersion`, and question-set version storage.
5. **Week 5.** Candidate retrieval queries, including pgvector cosine distance against embeddings from the same `embedding_model` (ARCHITECTURE.md §6). Storage of match runs, results, explanations, versions and dispositions. A Django migration enables the pgvector extension. The `Product.embedding` pgvector column, with `embedding_model` and `embedding_source_hash` (TD-01), is added **only after the embedding model is decided (D-11)**, because its dimension depends on the model. Do not guess a dimension.
6. **Week 6.** Reporting queries for the dashboard, opportunity storage, and backup and restore evidence (for example `pg_dump` and restore into a database with pgvector, tested). Feature freeze.
7. **Week 7.** Verify integrity, migrations from empty, performance on seed volume, audit and recovery. Freeze the schema.
8. **Week 8.** Final data dictionary, schema, migration notes, seed guide, and backup and recovery guide.

**Must not decide alone.** Field meanings, required-ness or allowed values (Adrika and BNCS), or adding a database engine, another extension, a search service or a data platform. Do not use real or scraped data. Do not edit applied migrations; add new ones.

**Evidence before done.** Migrations run cleanly on an empty database. The seed reaches ≥15 suppliers, ≥30 products and ≥10 requirements, all synthetic. Constraints are tested. Each dashboard query is reconciled with Harish. Restore has been demonstrated.

**Definition of Done.** Shared DoD, plus: every migration has a migration-impact note reviewed by Abhishek, Alok, Harish and Ajendra (manual §6), and the data dictionary is updated.

**Build prompt:**

```
Role: Vishal Chauhan | Data and Platform Services Engineer

Read AGENTS.md, docs/MVP_FEATURES.md (§6, M9, M10), docs/ARCHITECTURE.md (§4, §5)
and the docs/product/ field dictionary first. The stack is Django 5.2 models and
migrations on PostgreSQL 17 with pgvector; Django migrations are authoritative.
I own schema, migrations, constraints, seed data, search, reporting queries, audit
storage, data contracts and backup/recovery evidence. I do not define commercial
meaning; field meanings come from Adrika/BNCS.

Task: <describe, e.g. "create migrations for Supplier, Product and AuditEvent">

Do the following:
1. Inspect existing migrations, entities and the data dictionary; never edit an applied
   migration — add a new one.
2. Model at the level MVP_FEATURES §6 supports; use stable IDs, foreign keys, explicit
   units/currency columns, enum/check constraints for approved values, a version column
   for optimistic concurrency, created/updated metadata.
3. Audit events: append-only (no update/delete path from the application, plus the
   DB trigger), no secrets.
4. Use the Django ORM and PostgreSQL built-ins for search; no new database services.
   The only extension is pgvector, enabled by a Django migration; embeddings use the
   pgvector Django field, and the vector dimension comes from the D-11 model decision
   (TBD) — never guess one.
5. Seed data must be synthetic and clearly fake; target ≥15 suppliers, ≥30 products,
   ≥10 requirements, including edge cases (missing data, duplicates, ineligible items).
6. Write a migration-impact note listing affected APIs, matching inputs and tests.
7. Run `manage.py makemigrations --check`, `manage.py migrate` on an empty database and
   `manage.py seed_demo`, and report actual results.
Report: files changed, schema changes and impact, commands run with results, open field
questions for Adrika, next step.
```

---

### C7. Alok Tiwari — AI Matching and Data Intelligence Engineer

**Primary responsibility.** Owns the matching engine: eligibility filters, approved weighted scoring, semantic comparison, explanations, evaluation cases, the rules-only fallback and documented model limitations. The outcome is an explainable, evaluated, replaceable matching pipeline. **AI recommends. Authorised users make every material decision.**

**Owns:** the in-process matching package (ARCHITECTURE.md §4, §6):

- `backend/apps/matching/engine/`, pure Python with no Django imports
- `matching/providers/` (`NullProvider`, `SentenceTransformerProvider`)
- `matching/criteria/`, the versioned criteria JSON
- `requirements-semantic.txt` (`sentence-transformers` with CPU-only PyTorch, optional)
- `docs/ai/`: engine interface, criteria configuration notes, the embedding-model proposal (D-11), evaluation dataset and pack, limitations

**Interfaces.**

- **Abhishek:** the `engine.run()` interface, orchestration, fallback and failure signalling.
- **Vishal:** candidate data, embedding storage, run and result persistence.
- **Adrika:** criteria drafts, explanation wording.
- **Harish:** evaluation and failure tests.
- **Ajendra:** AI-service threats, data handling.

**MVP tasks, in order:**

1. **Week 1.** Define the `engine.run()` input and output dataclasses, the decision boundary, the evaluation approach and the fallback design (MVP_FEATURES §7, ARCHITECTURE.md §6). Document them in `docs/ai/`.
2. **Week 2.** Commit the engine package with the dataclasses, `NullProvider` and a stub `run()` that returns fixed example output, plus synthetic test examples. This lets Abhishek and Priyanka integrate early.
3. **Week 3.** Normalisation of approved fields, quality flags and embedding-ready records. Readiness-rule inputs, supporting Adrika. Start the embedding-model shortlist for D-11, against the criteria in ARCHITECTURE.md §6.
4. **Week 4.** **Deterministic baseline**: mandatory filters with pass, fail and unknown, plus weighted scoring from versioned criteria JSON. Use `v0-UNAPPROVED.json` placeholder weights until BNCS approves them at Gate 2. Per-criterion explanation output. pytest unit tests that need no database. Write the D-11 model proposal in `docs/ai/` for Ajendra's review, ideally by Gate 2. Aryan records the decision in ARCHITECTURE.md §9.
5. **Week 5.** **Hybrid matching**, once D-11 is recorded. Add `SentenceTransformerProvider`, which loads the model named by `EMBEDDING_MODEL` locally, with no external API and `trust_remote_code` never enabled. Pass the database-computed pgvector similarity into the engine as a bounded signal. Keep `SEMANTIC_PROVIDER=none` as the default until the evaluation supports turning it on. If D-11 is still open, deliver the provider against a test double and keep the run rules-only. Implement and label the rules-only fallback. Run the evaluation set: expected, false, missed, missing-data, manipulated-input, service-failure and fallback cases. Record the results.
6. **Week 6.** Final integration, fallback telemetry, match metrics. Lock the configuration. Stop feature expansion.
7. **Week 7.** Rerun the evaluation, analyse errors, document limitations, freeze rules, weights and model settings.
8. **Week 8.** AI evaluation pack: rules, weights and model configuration with versions, the dataset with expected outcomes, failure evidence, limitations and recommendations.

**Must not decide alone.** Criteria, weights, the semantic weight, readiness rules or regulatory interpretation (BNCS approves). The embedding model: propose it, but it is recorded only through a §9 entry with Ajendra's review (D-11). Until then, **never write a model name into code, defaults or examples.** Do not switch to an external AI or embedding API, another embedding library, or a vector store other than pgvector without an ARCHITECTURE.md §9 entry. Do not add an LLM, LLM SDK or prompt (D-20 is TBD and needs BNCS approval). Pilot data must never leave the environment. Never let semantic similarity override a mandatory failure, auto-approve suppliers, create opportunities, or present scores as certainty or accuracy beyond the evaluation evidence. Explanations are deterministic templates built from criterion results.

**Evidence before done.** Unit tests cover each filter outcome (pass, fail, unknown), scoring, ordering ties, empty candidates, fallback and malformed input. The evaluation results file records model and configuration versions. The contract matches what Abhishek calls.

**Definition of Done.** Shared DoD, plus: every change to rules, weights, model or prompts is recorded in `docs/ai/` with its version, and reviewed by Adrika, Harish and Ajendra (manual §6).

**Build prompt:**

```
Role: Alok Tiwari | AI Matching and Data Intelligence Engineer

Read AGENTS.md, docs/MVP_FEATURES.md (§7 matching process, M6, M7) and
docs/ARCHITECTURE.md (§6) first.
I own backend/apps/matching/engine/, providers/, criteria/ and docs/ai/. AI recommends; authorised humans decide.
Rules, weights and criteria require BNCS approval.

Task: <describe, e.g. "implement the deterministic eligibility filter and weighted score baseline">

Do the following:
1. Inspect matching/engine/, docs/ai/ and Vishal's models first. The engine is pure
   Python (dataclasses in, dataclasses out); it must not import Django or touch the DB.
2. Pipeline order is fixed: gate → mandatory filters (pass/fail/unknown; unknown is not
   a pass) → approved weighted score → optional bounded semantic signal → explanation +
   warnings. Rules-based matching is the baseline and must work on its own.
   Semantic similarity can never override a mandatory failure.
3. Load criteria/weights from versioned configuration; mark placeholders UNAPPROVED and
   include the config version in every output.
4. Always support rules-only mode; label it in the output. Return explicit errors for
   invalid input or internal failure — never partial results presented as complete.
5. Explanations are deterministic templates from criterion results (no LLM; D-20 is
   TBD). Semantic similarity uses the provider interface only: NullProvider or
   SentenceTransformerProvider (sentence-transformers, local). The embedding model is
   TBD (D-11): read it from EMBEDDING_MODEL and never hard-code or default a model name.
   Any provider error or unset model → rules-only, labelled.
6. Add unit tests and evaluation cases (expected, false, missed, missing-data,
   manipulated input, failure, fallback); run them and report actual results without
   overstating accuracy.
7. Keep the model replaceable behind the provider interface; no LLM or LLM framework
   (e.g. LangChain), no vector store other than pgvector, no external API, never
   trust_remote_code. Run `pytest` for the engine and report actual results.
Report: files changed, contract changes (notify Abhishek/Vishal), tests and evaluation
results, limitations, next step.
```

---

### C8. Harish Pal — QA and Test Automation Engineer

**Primary responsibility.** Independent verification: test strategy, requirements-to-test traceability, functional, integration, regression and end-to-end coverage, defect control, UAT coordination and the UAT recommendation. The outcome is objective evidence of what works and what does not. **BNCS accepts or rejects the pilot.**

**Owns:** `docs/qa/` (strategy, traceability matrix, defect process, QA and UAT reports, demo script), `e2e/` (cross-stack suite) and the test jobs in `.github/workflows/`.

**Interfaces.**

- **Adrika:** acceptance criteria and UAT scripts.
- **All engineers:** testability, test hooks, unit-test expectations.
- **Ajendra:** negative and security test automation.
- **Alok:** evaluation cases.
- **Vishal:** test data and dashboard reconciliation.
- **Aryan:** defect triage and evidence index.

**MVP tasks, in order:**

1. **Week 1.** Test strategy covering levels, tools (fixed in ARCHITECTURE.md §1: pytest + pytest-django, Vitest + React Testing Library, Playwright), environments (the Compose reference environment and the CI PostgreSQL + pgvector service), and entry and exit criteria. A traceability matrix keyed on `M#-AC#`. Smoke cases. A defect workflow using GitHub Issues with severity labels from the build manual.
2. **Week 2.** Set up the CI test jobs (ARCHITECTURE.md §8) and the `e2e/` Playwright project. Automate smoke, authentication, CRUD, permission, validation and API tests. Include: login without a CSRF token is rejected; an expired or absent session returns 401 `not_authenticated`; a role denial returns 403 and the UI keeps the session; a refresh on a deep route loads the page from the Next.js server; an unknown `/api/` path returns Django's JSON 404 through the Next.js rewrite, not a Next.js page. Log defects. Gate 1 evidence.
3. **Week 3.** Expand functional, API, permission and regression tests for the registry and readiness.
4. **Week 4.** Boundary, workflow-transition, permission and deterministic-scoring tests.
5. **Week 5.** Matching tests: expected, false, missed, missing-data, manipulated-input, service-failure and fallback cases (with Alok and Ajendra). Include the rules-only run with `SEMANTIC_PROVIDER=sentence_transformers` and no usable model.
6. **Week 6.** Automate the full priority journey E2E and publish the **feature-freeze quality baseline**.
7. **Week 7.** Lead UAT with Adrika, run regression and retests, prepare the QA recommendation.
8. **Week 8.** Final QA report, traceability, defect status, UAT record and the repeatable demo script.

**Must not decide alone.** Accepting the pilot (BNCS does), or changing requirements to match observed behaviour. Raise a defect or a question instead. Do not fix product code in other members' areas. Report the defect, or submit a test-only PR. Never mark a test passed that was not run.

**Evidence before done.** Each test result is linked to an `M#-AC#`. Each defect has severity, reproduction steps, owner and retest result. The regression run output is saved for each Friday review.

**Definition of Done.** Shared DoD, plus: the traceability matrix shows the coverage status of every acceptance criterion, and gaps are explicitly listed.

**Build prompt:**

```
Role: Harish Pal | QA and Test Automation Engineer

Read AGENTS.md, docs/MVP_FEATURES.md (acceptance criteria M1–M11), docs/ARCHITECTURE.md
(§1 tools, §8 CI) and docs/qa/ first. Test tools are fixed: pytest + pytest-django,
Vitest + React Testing Library, Playwright.
I provide independent verification. BNCS accepts or rejects the pilot.

Task: <describe, e.g. "automate permission tests for supplier APIs (M1-AC3, M2)">

Do the following:
1. Inspect existing tests, test tooling and the traceability matrix; reuse the existing
   framework — do not add a second tool for the same job.
2. Map every test to an M#-AC# ID; update docs/qa/traceability.
3. Cover normal, boundary, empty, failure, denied (per role) and object-tampering cases;
   for matching include false/missed/missing-data/manipulated/failure/fallback cases.
4. Use synthetic seed data only; tests must be repeatable and independent.
5. Run the tests and report the exact command and actual results; never mark untested
   items as passed.
6. For failures, file a defect with severity (Critical/High/Medium/Low per build manual),
   reproduction steps, expected vs actual, owner. Do not change product code to make
   tests pass.
Report: files changed, coverage added, actual results, defects raised, gaps, next step.
```

---

## D. Role activation

State your role at the start of a prompt in either form:

```
Role: Priyanka Singh | Frontend Web and Client-Side Integration Engineer
```
```
@role: frontend
```

**What the agent does:**

1. Matches the name or alias against the table in §C. If the name and role in a `Role:` line do not match that table (for example, an old role from the build manual), it **stops and points out the mismatch**. It does not adopt the stated role.
2. Applies the matching role section (C1 to C8): its ownership, its task order, its "must not decide alone" limits and its DoD. **All of §A, §B, §E and §F still apply.**
3. **Never infers a role** from a Git username, email, commit author, machine name or file being edited. If no role is given and the task changes files, it asks once which role applies. Read-only questions about the project need no role.
4. If a task crosses workstreams, it names the other owners and interfaces involved, limits its changes to the active role's area, and writes down what each other owner needs to do. It does not quietly implement their part.
5. Takes on one role per session. To switch, the user states a new role explicitly.
6. Writes daily-report entries only in the active member's own file in `docs/daily-reports/`, and only from verifiable facts (`docs/daily-reports/README.md`, *Using an AI coding agent*).

---

## E. Work execution protocol

Every agent follows these steps for every task:

1. **Identify** the active role and the requested outcome. Link the outcome to an `M#-AC#`, `D-xx` or issue.
2. **Inspect** the relevant existing files, contracts and tests.
3. **Check** MVP_FEATURES: is it in scope, what are the acceptance criteria, which decisions are still open?
4. **Identify** dependencies, missing information and conflicts with other workstreams or contracts.
5. **Implement** the smallest change that meets the criteria. Make reasonable, reversible choices within your role without unnecessary questions. **Escalate** product policy, architecture, security risk and scope decisions.
6. **Add or update** the tests and documentation affected.
7. **Run** the available checks (lint, type-check, tests, migrations) and record the **actual** results.
8. **Summarise** what changed, what was tested and its result, what is incomplete or assumed, and the next integration step and who owns it.
9. **Record** the day's outcome in the member's own daily report (§B rule 15), when the member asks for it. Separate completed work from planned work, and do not claim anything that step 7 did not actually show.

---

## F. Shared Definition of Done

A task is done only when **all** of these are true. Writing the code is not enough.

- It is linked to an agreed MVP requirement (`M#-AC#`), a recorded backlog task or a recorded decision. Approval of the whole MVP baseline is **not** a precondition. However, any business rule, permission or policy that is still unresolved (`[OPEN]`, `D-xx`) stays clearly marked `UNAPPROVED` in code, configuration and the PR, and must not silently become approved behaviour. Reversible scaffolding and placeholder work can be completed while approval is pending.
- Its acceptance criteria are met, and the evidence (test output, screenshot, review record) is in the repository or linked from the PR.
- The relevant tests exist, were run, and pass. Any test not run is stated.
- Interfaces still work, or the change is versioned and every consumer has been told.
- Affected documentation, contracts, the data dictionary and migration notes are updated.
- Security, data, AI and UX impacts were considered, with a review by the relevant owner where applicable.
- Audit events exist for any new material action.
- Known limitations and unresolved risks are written down, not hidden.
- A relevant peer has reviewed it, and comments are resolved or recorded.
- The designated reviewer has accepted it, or it has been explicitly carried forward with a reason and a new date.

**Severity rules (build manual §9).**

| Severity | Rule |
|---|---|
| Critical | Must be closed before acceptance. |
| High | Must be closed, or have an approved, documented workaround. |
| Medium / Low | Must stay visible in the defect or limitation register. |
