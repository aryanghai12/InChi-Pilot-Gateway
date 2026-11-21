# InChi Pilot Gateway

InChi Pilot Gateway is a private internal web application for authorised users at BNCS Biz N Consumer Solutions Pte Ltd. It is used to organise supplier and product information, assess supplier readiness for China-related market development, capture buyer requirements, review explainable supplier matches, and track the resulting commercial opportunities.

> **Status: supervised, non-production pilot (v0.1) — Week 4 Delivery Complete (Gate 2 Passed).**  
> Modules M1 (Auth & RBAC), M2–M3 (Supplier & Product Registry), M4 (China Readiness Assessment Baseline v2.2), M5 (Buyer Procurement Demand & Readiness Gate), and M10 (Append-Only Audit Events) are implemented and integrated across the full-stack reference environment. Module M6 (AI Matching Engine) baseline is established in `backend/ai_matching/` and progressing into Week 5 end-to-end matching integration.

---

## Quick Start & Implementation Guide

For the complete technical walkthrough, architecture diagrams, local native setup, environment variables, and testing procedures, see:

👉 **[docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) — Implementation & Setup Guide**

To start the entire multi-service stack with a single command (requires Docker with Compose v2):

```bash
cp .env.example .env          # Set POSTGRES_PASSWORD and DJANGO_SECRET_KEY
docker compose up --build     # Add -d to run in background
```

Then access the workspace at **[http://localhost:3000](http://localhost:3000)**.

---

## The Problem

BNCS needs one structured, traceable place to answer a commercial question: which suppliers and products could credibly meet a given buyer requirement for the China market, why, and what is still missing? Today that assessment depends on scattered information and individual judgement. The pilot tests whether a controlled internal tool can make the assessment consistent, explainable, and auditable. Humans retain final authority on every decision.

---

## MVP Workflow (The Priority Journey)

1. **Access Workspace:** An authorised user signs in to a role-aware workspace (`platform_admin`, `commercial_analyst`, or `reviewer`).
2. **Registry Management:** The user creates or updates supplier and product records with commercial terms and Mandarin-ready attributes.
3. **China-Readiness Assessment:** The user completes a China-readiness assessment against 18 compliance criteria (`CR-01` to `CR-18`), and an authorised Reviewer records a categorical qualitative outcome (`ready_for_matching`, `information_required`, or `not_currently_eligible`).
4. **Buyer Requirement Capture:** The user records buyer requirements, with mandatory hard constraints separated from weighted commercial preferences.
5. **AI Matching Execution:** The platform applies mandatory hard eligibility filters, approved weighted preference scoring, and bounded local semantic similarity. Semantic processing failures fail explicitly (no silent fallback).
6. **Explainable Recommendations:** The platform presents ranked candidate suppliers with score breakdowns, missing-information warnings, and plain-English rationales.
7. **Human Disposition:** An authorised Reviewer evaluates candidates and records an explicit disposition (`Accepted`, `Rejected`, `On Hold`) with mandatory justification.
8. **Opportunity Pipeline:** An accepted match converts into a commercial opportunity tracked through structured pipeline stages.
9. **Dashboard & Audit:** Real-time metrics compute from stored database records, while an append-only audit trail logs every material change.

---

## Feature Modules Status (v0.1 Pilot)

| Module | Summary | Implementation Status |
|---|---|---|
| **M1 Access** | Session auth, PBKDF2 hashing, 3 internal roles, backend RBAC policy, CSRF bootstrap, object-level checks. | **Implemented & Verified** (`backend/apps/accounts/`) |
| **M2–M3 Registry** | Supplier and product records, optimistic concurrency, bilingual Mandarin attributes, evidence metadata. | **Implemented & Verified** (`backend/apps/registry/`) |
| **M4 Readiness** | *China Readiness Baseline v2.2*, 18 criteria, 9 evidence conditions, submission gate, `deny_self_review` desk. | **Implemented & Verified** (`backend/apps/readiness/`) |
| **M5 Requirements** | Buyer demand capture, category/port constraints, conditional pricing validation, `mark_ready` gate. | **Implemented & Verified** (`backend/apps/demand/`) |
| **M6 Matching** | FastAPI AI matching engine, local embeddings interface, hard eligibility filters, hybrid scoring, ranking. | **Baseline Implemented** (`backend/ai_matching/`, `backend/apps/matching/`) |
| **M7 Disposition** | Reviewer decision desk, disposition states (`Accepted`, `Rejected`, `On Hold`), justification logging. | **Drafted** (Week 5 Target) |
| **M8 Opportunities**| Structured pipeline stages (`Initiated` $\to$ `Closed`), created strictly from accepted matches. | **Scaffolded** (`backend/apps/opportunities/`, Week 6 Target) |
| **M9 Dashboard** | Current-state metrics and summary counts computed from stored records. | **Scaffolded** (`backend/apps/dashboard/`, Week 5/6 Target) |
| **M10 Audit** | Append-only audit history capturing actor, action, timestamp, correlation IDs, and state diffs. | **Implemented & Verified** (`backend/apps/audit/`) |
| **M11 Quality** | Multi-service CI, security scans (pip-audit, npm audit, gitleaks), Playwright E2E, handover packs. | **Active & Continuous** (`.github/workflows/`, `e2e/`) |

Full acceptance criteria and the role permission matrix are in [docs/MVP_FEATURES.md](docs/MVP_FEATURES.md).

---

## Exclusions and Non-Production Limitations

- **Private internal pilot only:** No public marketplace, self-registration, external supplier portals, or external buyer accounts.
- **Decision support only:** AI recommendations only advise; humans approve every material decision. Scores do not guarantee regulatory or commercial compliance.
- **Zero real personal/commercial data:** The platform runs exclusively on synthetic seed data. Never commit real credentials, identity documents, or client records.
- **No external AI APIs:** Vector embeddings execute locally on CPU (`sentence-transformers` interface). Zero data leaves the environment.
- **No LLM in v0.1:** Explanations are generated deterministically from criteria evaluation templates (D-20).
- **Out of scope:** Payments, purchase orders, legal contracting, tax/customs filings, mobile native applications, and autonomous decision-making.

---

## Architecture and Technology Stack

The application stack follows the architecture specification in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md):

| Layer | Choice | Rationale |
|---|---|---|
| **Frontend** | **Next.js 16 (App Router), React 19, TypeScript** | Modern SSR/client routing, TanStack Query for caching, CSS Modules. Proxies `/api/` to Django without holding secrets. |
| **Backend** | **Python 3.12, Django 5.2 LTS, Django REST Framework** | Robust session auth, CSRF, ORM, migrations, RBAC policy engine, and OpenAPI 3.0.3 via drf-spectacular. |
| **Database** | **PostgreSQL 17 with `pgvector`** | Relational transactions and vector embeddings in a single database. Schema managed authoritatively via Django migrations. |
| **Matching Engine**| **Two-Component Architecture (FastAPI + Django)** | Django (`backend/apps/matching/`) coordinates data and persistence; FastAPI (`backend/ai_matching/`) executes vector operations and scoring. |
| **Embeddings** | **Local CPU (`sentence-transformers` interface)** | Local processing ensures no pilot data leaves the environment. Model selection pending D-11. |
| **Testing** | **pytest, Vitest, React Testing Library, Playwright** | Unit, integration, component, and full-stack browser E2E test coverage. |
| **Reference Env** | **Docker Compose v2** | 4-service topology: `db`, `matching`, `backend`, `frontend` operating on a unified host origin. |

---

## Repository Structure

```
.
├── AGENTS.md                  Shared engineering manual, team roles, and prompts (source of truth)
├── CLAUDE.md                  Points AI tools to AGENTS.md
├── README.md                  Project overview, status, and directory roadmap
├── docker-compose.yml         Reference multi-service environment definition
├── .env.example               Environment template with synthetic placeholders
├── backend/                   Django backend & FastAPI AI Matching Engine
│   ├── config/                Django configuration (settings, URLs, exception handlers)
│   ├── apps/                  Modular Django applications
│   │   ├── accounts/          M1: User models, session auth, RBAC policy, admin commands
│   │   ├── registry/          M2-M3: Supplier & Product models, bilingual fields, evidence
│   │   ├── readiness/         M4: China Readiness Assessment models & lifecycle APIs (Baseline v2.2)
│   │   ├── demand/            M5: Buyer Requirement models & readiness gates
│   │   ├── matching/          M6: Django matching integration layer & candidate selectors
│   │   ├── audit/             M10: Append-only audit trail service & models
│   │   ├── dashboard/         M9: Operational dashboard summary services
│   │   └── opportunities/     M8: Commercial opportunity pipeline tracking
│   └── ai_matching/           FastAPI AI Matching Engine (preprocessing, filters, scoring, ranking)
├── frontend/                  Next.js App Router web application
│   ├── src/app/               App router pages: /login, (workspace)/ suppliers, products, readiness, requirements
│   ├── src/components/        Shared design tokens, UI components, navigation, tables
│   ├── src/lib/api/           Centralized `apiFetch` client, generated TypeScript schema, query clients
│   └── src/middleware.ts      Route protection middleware enforcing login redirects
├── e2e/                       Playwright automated browser and API contract test suite
└── docs/                      Project documentation suite
    ├── IMPLEMENTATION.md      Comprehensive implementation and setup guide
    ├── ARCHITECTURE.md        Architecture, stack rationale, layout ownership, decisions (§9, §10)
    ├── MVP_FEATURES.md        Module scope, acceptance criteria, timeline, permissions
    ├── governance/            Delivery registers, integration plan, and review records
    ├── daily-reports/         Weekly progress logs across all 8 team members
    ├── security/              Threat model, access control matrix, data classification, audit reviews
    ├── qa/                    Test strategy, traceability matrix, defect logs, verification records
    ├── ai/                    Matching engine contract, embedding selection, fallback design
    ├── api/                   Generated OpenAPI 3.0.3 specification (`openapi.yaml`)
    └── source-documents/      Original program and specification PDFs (read-only reference)
```

---

## Running the Application

### Full-Stack Docker Compose Reference Environment
```bash
# 1. Setup environment
cp .env.example .env

# 2. Start all services
docker compose up --build

# 3. Create initial platform administrator (if not set in .env)
docker compose exec backend python manage.py create_platform_admin --email admin@inchi.local
```

| Service | Container Name | Host Port | Description |
|---|---|---|---|
| `frontend` | `inchi-pilot-frontend` | `http://localhost:3000` | Next.js Web UI & reverse proxy |
| `backend` | `inchi-pilot-backend` | Internal `:8000` | Django 5.2 & DRF REST API |
| `matching` | `inchi-pilot-matching` | Internal `:8001` | FastAPI AI Matching Engine |
| `db` | `inchi-pilot-db` | `127.0.0.1:5432` | PostgreSQL 17 + pgvector |

For native host development instructions, see [docs/IMPLEMENTATION.md §4](docs/IMPLEMENTATION.md#4-option-2-native-local-development).

---

## Running Tests & Quality Checks

```bash
# Backend Django & Matching Tests
docker compose exec backend python -m pytest
# Or natively inside backend/: python manage.py test apps

# Frontend Unit Tests, Types & Linting
cd frontend
npm test               # Vitest unit test suites
npm run typecheck      # TypeScript compilation check
npm run lint           # ESLint analysis

# End-to-End Automation (Playwright)
npx playwright test

# Security Audits
pip-audit
npm audit --audit-level=high
gitleaks detect --source . --verbose
```

---

## Key Documentation Links

- **Setup & Implementation:** [`docs/IMPLEMENTATION.md`](docs/IMPLEMENTATION.md)
- **Architecture & Technical Decisions:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Features & Acceptance Criteria:** [`docs/MVP_FEATURES.md`](docs/MVP_FEATURES.md)
- **Engineering Rules & Team Roles:** [`AGENTS.md`](AGENTS.md)
- **Governance & Delivery Registers:** [`docs/governance/REGISTERS.md`](docs/governance/REGISTERS.md)
- **Integration Plan & Contracts:** [`docs/governance/INTEGRATION_PLAN.md`](docs/governance/INTEGRATION_PLAN.md)
- **Weekly Progress Logs:** [`docs/daily-reports/README.md`](docs/daily-reports/README.md)
- **Security Pack:** [`docs/security/README.md`](docs/security/README.md)
- **QA Strategy & Traceability:** [`docs/qa/README.md`](docs/qa/README.md)
- **AI Matching Specification:** [`docs/ai/README.md`](docs/ai/README.md)
- **OpenAPI 3.0.3 Specification:** [`docs/api/openapi.yaml`](docs/api/openapi.yaml)
- **Source & Reference PDFs:** [`docs/source-documents/README.md`](docs/source-documents/README.md)

---

## Team and Delivery Ownership

The pilot is delivered by eight interns under BNCS and Senior Technical Mentor supervision (effective 26 October 2026):

| Team Member | Role | Primary Areas | Weekly Progress |
|---|---|---|---|
| **Aryan Ghai** | Technical Project Coordinator, Product Operations and Integration Governance | `docs/governance/`, Backlog, Registers, README/AGENTS, Handover Index | [aryan-ghai.md](docs/daily-reports/aryan-ghai.md) |
| **Ajendra Nath Tripathi** | Cybersecurity and DevSecOps Engineer | `docs/security/`, Security CI jobs, Dependabot, Threat Modeling | [ajendra-nath-tripathi.md](docs/daily-reports/ajendra-nath-tripathi.md) |
| **Adrika T Kumar** | Product UX and Commercial Workflow Analyst | `docs/product/`, Requirement dictionaries, Acceptance criteria, Workflow design | [adrika-t-kumar.md](docs/daily-reports/adrika-t-kumar.md) |
| **Priyanka Singh** | Frontend Web and Client-Side Integration Engineer | `frontend/` (Next.js App Router, UI components, API client) | [priyanka-singh.md](docs/daily-reports/priyanka-singh.md) |
| **Abhishek Kumar** | Application Backend and Access-Control Engineer | `backend/apps/` (Django, DRF API, RBAC policy, Session Auth, Docker) | [abhishek-kumar.md](docs/daily-reports/abhishek-kumar.md) |
| **Vishal Chauhan** | Data and Platform Services Engineer | Database schema, pgvector migrations, query optimization, audit events | [vishal-chauhan.md](docs/daily-reports/vishal-chauhan.md) |
| **Alok Tiwari** | AI Matching and Data Intelligence Engineer | `backend/ai_matching/`, `backend/apps/matching/`, `docs/ai/` | [alok-tiwari.md](docs/daily-reports/alok-tiwari.md) |
| **Harish Pal** | QA and Test Automation Engineer | `e2e/`, Automated Playwright tests, QA traceability, defect triage | [harish-pal.md](docs/daily-reports/harish-pal.md) |
