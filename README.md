# InChi Pilot Gateway

A private internal web application for authorised users at **BNCS Biz N Consumer Solutions Pte Ltd**. It helps them register Indian suppliers and products, assess their **China readiness**, capture defined **Chinese buyer requirements**, run **explainable, deterministic matching**, and record a **human decision** with a complete audit history.

> **Supervised, non-production pilot (v0.1).** Built by eight interns over eight weeks (26 Oct – 18 Dec 2026, proposed revised timeline, D-19 pending). Synthetic data only. AI only advises; a person makes every material decision. Not a marketplace, certification service, customs system or transaction platform.

> [!WARNING]
> **Open Critical security defect (AUD-01, 21 Nov 2026).** The API currently lets an anonymous visitor create a `platform_admin` account. Run the stack only on your own machine (the default binds to `127.0.0.1`) until it is fixed. See the [audit](docs/governance/AUDIT_2026-11-21.md#4-findings-register).

---

## Quick start

You need **Git** and **Docker with Compose v2**. Full beginner guide, native setup and troubleshooting: **[docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)**.

```bash
git clone https://github.com/aryanghai12/InChi-Pilot-Gateway.git
cd InChi-Pilot-Gateway
cp .env.example .env
#   edit .env: set POSTGRES_PASSWORD (letters, digits, - and _ only), DJANGO_SECRET_KEY,
#   and INITIAL_ADMIN_EMAIL + INITIAL_ADMIN_PASSWORD to create the first administrator
docker compose up --build -d
docker compose ps        # wait until all four services show "healthy"
```

Open **http://localhost:3000** and sign in with the administrator you configured.

| Address (all through port 3000) | What |
|---|---|
| http://localhost:3000 | Workspace |
| http://localhost:3000/admin/ | Django admin (user roles) |
| http://localhost:3000/api/docs/ | Swagger UI for the API |
| http://localhost:3000/api/v1/health/ | Backend health |

Stop with `docker compose down`. Reset all data with `docker compose down -v`.

---

## Current status

Position: **end of Week 4** (16–20 Nov 2026). Week 5 (23–27 Nov) targets explainable matching and the human decision. Verified on 21 Nov 2026 against the running stack and test suites ([audit §1](docs/governance/AUDIT_2026-11-21.md#1-checks-actually-run)).

| Module | What it covers | State on 21 Nov 2026 |
|---|---|---|
| **M1** Access | Session login, CSRF, 401/403 semantics, three roles, backend permission policy, Django admin for users | **Live.** 9 tests. **Open defects:** AUD-01 (anonymous admin sign-up), AUD-15 (admin-created users get plaintext passwords). Role model pending D-22 (v2.2 defines five roles). |
| **M2–M3** Registry | Suppliers and products, evidence metadata, optimistic concurrency | **Live.** 13 tests. Controlled values to align with v2.2 (D-23). |
| **M4** China readiness | Baseline v2.2 questionnaire CR-01–CR-18, submission gate, workflow, three categorical outcomes, nine evidence conditions | **Live API and UI. No backend tests yet.** |
| **M5** Buyer requirements | Draft → Ready for Matching → Closed, completeness gate, mandatory vs preferred criteria | **Live API and UI. No backend tests yet.** |
| **M6** Matching | FastAPI engine and Django integration client | **Engine runs (148 tests); Django client has 62 tests. Not wired into the API or UI.** Approach pending **D-21** (v2.2 requires rules-only, no hidden weights). |
| **M7** Disposition | Accept for Follow-up / Hold for Information / Reject, with reason | Not started (Week 5) |
| **M8** Opportunities | Opportunity pipeline | Not started. Scope pending D-24. |
| **M9** Dashboard | v2.2 SCR-01 counts and work queue | Not started (API missing; page shows empty state) |
| **M10** Audit | Append-only audit events, DB trigger blocks UPDATE/DELETE | **Write side live.** History screen API not started. |
| **M11** Quality | CI, security scans, Playwright, Compose reference environment | Compose verified (4 healthy services). CI covers accounts, registry and frontend; not readiness, demand or matching (AUD-05). |

**Gates.** Gate 1 (6 Nov) was demonstrated. The Gate 2 review was held on 20 Nov; its outcome is not yet recorded, and decisions D-21 to D-25 are open. Gate 3 (integrated MVP and feature freeze) is on **4 Dec 2026**. See the [gate register](docs/governance/REGISTERS.md#7-gate-register).

**Decisions pending now:** see the [escalation list](docs/governance/REGISTERS.md#13-pending-decisions--escalation-list).

---

## The problem and the journey

BNCS needs one structured, traceable place to answer: *which Indian suppliers and products could credibly meet a defined Chinese buyer requirement, why, and what is still missing?* The pilot tests whether a controlled internal tool makes that assessment consistent, explainable and auditable.

The journey the pilot must demonstrate ([Baseline v2.2 §2.1](docs/source-documents/InChi_China_Readiness_Implementation_Baseline_v2.2.pdf)):

1. **Sign in** to a role-aware workspace.
2. **Create a supplier** (Indian business identity, contact, export identifiers).
3. **Add a product** with technical and commercial attributes.
4. **Assess readiness**: answer the 18-question questionnaire and record evidence conditions. A reviewer records *Ready for Matching*, *Information Required* or *Not Currently Eligible*. No numeric score.
5. **Capture buyer demand**: one versioned Chinese buyer requirement, with mandatory criteria kept apart from preferences.
6. **Run matching**: mandatory rules first (any confirmed fail → *Not Eligible*; any unknown → *Information Required*), then preferences shown as "Met X of Y". No hidden weights and no confidence percentage.
7. **Review the explanation**: matches, failures, unknowns, evidence limitations, data age.
8. **Record a disposition**: *Accept for Follow-up*, *Hold for Information* or *Reject for this requirement*, with a reason.
9. **Trace it**: every material action appears in the audit history; a basic dashboard shows current counts.

The build manual also includes an opportunity pipeline after step 8; whether it stays in scope is decision D-24.

---

## What the pilot will not do

- No public access, self-registration, or external supplier or buyer accounts.
- No payments, orders, contracts, customs filing, live registry integrations or scraping.
- No factory audits, automatic verification or certification, and no "Verified" badges.
- No autonomous AI decisions, AI scoring or compliance conclusions. No LLM in v0.1 (D-20). Any embedding work runs locally; pilot data never leaves the environment.
- No real personal or commercial data, and no production deployment.

---

## Architecture

```
Browser ──► Next.js (frontend, :3000) ──/api/*, /admin/*, /static/*──► Django + DRF (backend, :8000) ──► PostgreSQL 17 + pgvector (db)
                                                                              │
                                                                              └── HTTP ──► FastAPI matching engine (matching, :8001)
```

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, TanStack Query, CSS Modules | Renders and proxies only. No business logic, authorisation or secrets (TD-10). |
| Backend | Python 3.12, Django 5.2 LTS, Django REST Framework, drf-spectacular | The single authority for auth, permissions, validation, workflow and audit. |
| Database | PostgreSQL 17 with pgvector (`pgvector/pgvector:0.8.6-pg17-bookworm`) | Schema owned by Django migrations. |
| Matching engine | FastAPI, Pydantic, uvicorn (`backend/ai_matching/`) | Separate Compose service (TD-11). Embedding library optional; model not decided (D-11). |
| Tests | pytest + pytest-django, Vitest + React Testing Library, Playwright | |
| Tooling | GitHub Actions, gitleaks, pip-audit, bandit, npm audit, Dependabot | |
| Environment | Docker Compose v2: `db`, `matching`, `backend`, `frontend` | The demo and UAT environment (D-16). |

The stack is the team's selection (D-01). **Django instead of the build manual's Spring Boot still needs BNCS and mentor approval** ([ARCHITECTURE §10](docs/ARCHITECTURE.md#10-build-manual-deviations-and-pending-approvals)).

---

## Repository layout

```
.
├── README.md · AGENTS.md · CLAUDE.md   overview; shared rules and the eight role definitions; AI-agent pointer
├── docker-compose.yml · .env.example   reference environment and its settings template
├── backend/                            Django project + FastAPI engine (one Dockerfile, two targets)
│   ├── config/                         settings, URLs, error handling
│   ├── apps/accounts/                  M1 users, roles, auth, policy.py, create_platform_admin
│   ├── apps/registry/                  M2–M3 suppliers, products, evidence metadata
│   ├── apps/readiness/                 M4 China-readiness assessments (Baseline v2.2)
│   ├── apps/demand/                    M5 buyer requirements
│   ├── apps/matching/                  M6 Django integration client (no API yet)
│   ├── apps/audit/                     M10 append-only audit events
│   ├── apps/dashboard/, opportunities/ M9, M8 (empty shells)
│   └── ai_matching/                    FastAPI matching engine
├── frontend/                           Next.js app (src/app, src/components, src/lib/api)
├── e2e/                                Playwright suite
├── database/                           data-workstream prototype project (not part of the running stack)
├── .github/                            CI, security workflow, Dependabot
└── docs/                               all documentation (map below)
```

Ownership of every path: [ARCHITECTURE.md §4](docs/ARCHITECTURE.md#4-repository-layout-and-ownership).

---

## Tests

| Suite | Command | Result on 21 Nov 2026 |
|---|---|---|
| Backend (Django) | `cd backend && SECRET_KEY=local DATABASE_URL= python -m pytest --ds=config.settings apps` | 84 passed, 1 skipped |
| Matching engine | `cd backend && python -m pytest ai_matching/tests` | 148 passed, 2 skipped |
| Frontend | `cd frontend && npm run lint && npm run typecheck && npm test` | clean, clean, 42 passed |
| End-to-end | `cd e2e && npm ci && npm test` (see `e2e/README.md`) | not run in the audit |

Details, PostgreSQL runs and security scans: [IMPLEMENTATION.md §6](docs/IMPLEMENTATION.md#6-running-tests-and-quality-checks).

---

## Documentation map

| If you want to… | Read |
|---|---|
| Set up and run the project | [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) |
| Know the rules and your role (people and AI agents) | [AGENTS.md](AGENTS.md) |
| Know what to build and the acceptance criteria | [docs/MVP_FEATURES.md](docs/MVP_FEATURES.md) and [Baseline v2.2](docs/source-documents/InChi_China_Readiness_Implementation_Baseline_v2.2.pdf) |
| Know how it is built, who owns what, technical decisions | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| See decisions, risks, issues, dependencies, gates | [docs/governance/REGISTERS.md](docs/governance/REGISTERS.md) |
| See interface contracts and the integration plan | [docs/governance/INTEGRATION_PLAN.md](docs/governance/INTEGRATION_PLAN.md) |
| Read the latest audit | [docs/governance/AUDIT_2026-11-21.md](docs/governance/AUDIT_2026-11-21.md) |
| Read the API contract | [docs/api/](docs/api/README.md) and Swagger at `/api/docs/` |
| Security pack | [docs/security/](docs/security/README.md) |
| QA strategy, traceability, defects | [docs/qa/](docs/qa/README.md) |
| Matching engine design | [docs/ai/](docs/ai/README.md) |
| Data dictionary, schema, backup | [database/docs/](database/docs/) |
| Weekly progress | [docs/daily-reports/](docs/daily-reports/README.md) |
| Original source PDFs and precedence | [docs/source-documents/](docs/source-documents/README.md) |

**Which source wins.** Baseline v2.2 (BNCS, 16 Nov 2026) governs readiness, buyer requirements, matching and disposition. The revised ownership and timeline govern people and dates. The build manual governs everything else.

---

## Team

Roles effective 26 Oct 2026 ([revised ownership PDF](docs/source-documents/InChi_Pilot_User_Delivery%20Ownership%20(revised).pdf)). Approvers above the team: BNCS Programme Sponsor (final acceptance), BNCS Product and Venture Lead (scope and workflows), Senior Technical Mentor (architecture); Baseline v2.2 names the Venture Build Director and CPO as Product Authority.

| Member | Role | Owns | Weekly report |
|---|---|---|---|
| Aryan Ghai | Technical Project Coordinator, Product Operations and Integration Governance | `docs/governance/`, README, AGENTS, IMPLEMENTATION, decision records | [aryan-ghai.md](docs/daily-reports/aryan-ghai.md) |
| Ajendra Nath Tripathi | Cybersecurity and DevSecOps Engineer | `docs/security/`, security CI, secrets baseline | [ajendra-nath-tripathi.md](docs/daily-reports/ajendra-nath-tripathi.md) |
| Adrika T Kumar | Product UX and Commercial Workflow Analyst | `docs/product/`, requirement content of MVP_FEATURES | [adrika-t-kumar.md](docs/daily-reports/adrika-t-kumar.md) |
| Priyanka Singh | Frontend Web and Client-Side Integration Engineer | `frontend/` | [priyanka-singh.md](docs/daily-reports/priyanka-singh.md) |
| Abhishek Kumar | Application Backend and Access-Control Engineer | Django config, views, serializers, permissions; OpenAPI; backend Dockerfile; Compose | [abhishek-kumar.md](docs/daily-reports/abhishek-kumar.md) |
| Vishal Chauhan | Data and Platform Services Engineer | Models, migrations, seed data, queries, `db` service, data docs | [vishal-chauhan.md](docs/daily-reports/vishal-chauhan.md) |
| Alok Tiwari | AI Matching and Data Intelligence Engineer | `backend/ai_matching/`, `backend/apps/matching/` services, `docs/ai/` | [alok-tiwari.md](docs/daily-reports/alok-tiwari.md) |
| Harish Pal | QA and Test Automation Engineer | `e2e/`, `docs/qa/`, test CI jobs | [harish-pal.md](docs/daily-reports/harish-pal.md) |

Contributing: branch `<area>/<short-description>`, one purpose per PR, linked to an `M#-AC#` or `D-xx`, with the PR template in [AGENTS.md §B](AGENTS.md#branches-commits-and-prs). No direct pushes to `main`.
