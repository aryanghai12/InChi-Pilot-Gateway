# InChi Pilot Gateway

InChi Pilot Gateway is a private internal web application for authorised users at BNCS Biz N Consumer Solutions Pte Ltd. It is used to organise supplier and product information, assess supplier readiness for China-related market development, capture buyer requirements, review explainable supplier matches, and track the resulting commercial opportunities.

> **Status: supervised, non-production pilot (v0.1), in early development.**
> As of 28 October 2026 (Week 1 of 8) this repository contains planning and specification documents only. No application code, build tooling or tests exist yet. Everything listed under *Features* is planned work.

## The problem

BNCS needs one structured, traceable place to answer a commercial question: which suppliers and products could credibly meet a given buyer requirement for the China market, why, and what is still missing? Today that assessment depends on scattered information and individual judgement. The pilot tests whether a controlled internal tool can make the assessment consistent, explainable and auditable. People still make every decision.

## MVP workflow

1. An authorised user signs in to a role-aware workspace.
2. The user creates or updates supplier and product records.
3. The user completes a China-readiness assessment, and a Reviewer records the outcome.
4. The user records a buyer requirement, with mandatory criteria kept separate from preferences.
5. The platform applies mandatory eligibility filters, then approved weighted scoring, then a bounded semantic-similarity signal. A rules-only fallback is available.
6. The platform shows ranked candidates with explanations and missing-information warnings.
7. An authorised person records a disposition with a reason.
8. An authorised user can convert an accepted match into a tracked opportunity.
9. A dashboard and an audit history show the current status and who did what.

## Features (planned for v0.1)

| Module | Summary |
|---|---|
| M1 Access | Login, three internal roles, backend-enforced and object-level authorisation |
| M2–M3 Registry | Supplier and product records: create, edit, search, filter, evidence metadata |
| M4 Readiness | Versioned question set, missing-information list, human review and outcome |
| M5 Requirements | Buyer requirement capture with mandatory and preference criteria, versioning |
| M6 Matching | Eligibility filters, weighted score, semantic signal, explanations, fallback |
| M7 Disposition | Human decision (proposed: accepted, rejected or on hold) with a reason |
| M8 Opportunities | A small, approved set of pipeline stages, created only from accepted matches |
| M9 Dashboard | Current-state counts computed from stored records |
| M10 Audit | Append-only history of material changes, reviews and decisions |
| M11 Quality | Security testing, QA and UAT evidence, synthetic seed data, demo runbook |

Full scope, acceptance criteria and the permission matrix are in [docs/MVP_FEATURES.md](docs/MVP_FEATURES.md).

## Exclusions and limitations

- The pilot is **not** a public website or marketplace. There is no self-registration, and there are no external supplier or buyer accounts.
- No payments, contracts, purchase orders, negotiation, or legal, tax, customs or regulatory certification.
- No full Mandarin interface or machine translation. Only selected fields are Mandarin-ready.
- Synthetic data only. The repository must never contain real personal or confidential data, or production credentials.
- Matching output is decision support. Scores are not guarantees of fit or compliance, and no accuracy is claimed beyond the documented evaluation results.
- Readiness criteria, eligibility rules, weights, decision labels and opportunity stages are **awaiting BNCS approval**.
- Not production-ready, and not security-certified.

## Architecture and technology

**The team has selected this stack (decision D-01, revised 28 Oct 2026). Nothing is implemented yet.** Full details, conventions and rationale are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router), React, TypeScript, TanStack Query. Next.js renders pages and forwards `/api/` to Django; it holds no business logic. |
| Backend | Python 3.12, Django 5.2 LTS, Django REST Framework. Session auth with CSRF. OpenAPI via drf-spectacular. |
| Database | PostgreSQL 17 with pgvector. Django ORM and Django migrations are authoritative for the schema. |
| Matching | In-process Python package inside the backend. Deterministic rules-based matching is the baseline. Semantic similarity is an optional, bounded signal, with a rules-only fallback. |
| Embeddings | `sentence-transformers`, run locally (optional install). **Embedding model: TBD (D-11).** |
| LLM | **None in v0.1. Provider and model TBD (D-20).** Not needed for the MVP. |
| Tests | pytest, Vitest + React Testing Library, Playwright |
| Environment | Docker Compose: PostgreSQL + pgvector, Django backend, Next.js frontend, all on one browser origin |
| Delivery | GitHub pull requests and GitHub Actions CI. Hosted staging is optional. |

**Approval status.** The build manual makes the final stack subject to BNCS and technical-mentor approval. **That approval has not been recorded yet.** The material deviations from the manual's baseline are:

- Django instead of Spring Boot;
- matching inside the backend instead of a separate FastAPI service;
- hosted staging made optional.

They are listed with their status in [ARCHITECTURE.md §10](docs/ARCHITECTURE.md#10-build-manual-deviations-and-pending-approvals).

## Repository structure

What exists today:

```
.
├── AGENTS.md        Shared team and AI-agent instructions, all eight roles (source of truth)
├── CLAUDE.md        Points Claude Code to AGENTS.md
├── README.md
└── docs/
    ├── MVP_FEATURES.md                                     v0.1 scope, acceptance criteria, business decisions
    ├── ARCHITECTURE.md                                     Stack, repository layout and ownership, conventions, technical decisions
    ├── daily-reports/                                      Daily progress log: process README and one file per member
    ├── InChi_Pilot_Gateway_Build_Manual.pdf                Source: scope, governance (roles and dates superseded)
    ├── InChi_Pilot_User_Delivery Ownership (revised).pdf   Source: current roles (from 26 Oct 2026)
    ├── InChi_Pilot_Build Sequence Timeline (revised).pdf   Source: current weekly plan (26 Oct – 18 Dec 2026)
    ├── InChi_Pilot_User_Journey_Proposed.pdf               Source: eight-stage journey and stage owners
    ├── InChi_University_Collaboration_Internship_Program.pdf  Source: programme brief
    └── InChi_Mapped_Website_Feature_Blueprint.pdf          Source: proposed feature blueprint (audited)
```

Planned top-level layout. Each directory is created when work on it starts:

| Path | What goes there | Primary owner |
|---|---|---|
| `frontend/` | Next.js App Router app: pages, shared components, API client and frontend unit tests | Priyanka |
| `backend/` | Django project: API, auth and permissions, workflow services (Abhishek); models, migrations, queries and seed data (Vishal); matching engine and providers (Alok); unit and API tests beside each app | Abhishek, Vishal, Alok |
| `e2e/` | Playwright end-to-end and regression suite | Harish |
| `docker-compose.yml`, `.env.example` | Local and demo environment: `db`, `backend`, `frontend` | Abhishek (with Vishal and Priyanka) |
| `.github/` | CI workflows and Dependabot | Harish (tests), Ajendra (security) |
| `docs/governance/`, `docs/product/`, `docs/security/`, `docs/data/`, `docs/ai/`, `docs/qa/`, `docs/api/` | Registers and reports; product definitions; security pack; data dictionary; matching and evaluation; QA evidence; generated OpenAPI | Aryan, Adrika, Ajendra, Vishal, Alok, Harish, Abhishek |

The full tree, file-level ownership, reviewers and "when to coordinate with whom" are in **[docs/ARCHITECTURE.md §4](docs/ARCHITECTURE.md#4-repository-layout-and-ownership)**, the single source of truth for ownership.

## Setup and running

There is nothing to run yet. Setup steps, environment variables (via `.env.example`) and seed-data loading will be documented here once the backend and frontend skeletons land (Week 1 target). The planned entry point is `docker compose up`, followed by the `create_platform_admin` and `seed_demo` commands, with the app opened at `http://localhost:3000` (ARCHITECTURE.md §8). These commands do not exist yet.

## Tests and validation

No test suites or CI workflows exist yet. The test strategy and traceability matrix will be in `docs/qa/`, and commands will be listed here once they exist and have been verified.

## Documentation

- [docs/MVP_FEATURES.md](docs/MVP_FEATURES.md): what is in v0.1, acceptance criteria, permissions, matching process, feature-blueprint audit, Phase 2 list, source discrepancies and open decisions.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): technology stack, repository layout and ownership, backend, frontend and matching conventions, CI, technical decision record, build-manual deviations awaiting approval.
- [AGENTS.md](AGENTS.md): engineering rules, role definitions and prompts, and the Definition of Done.
- [docs/daily-reports/](docs/daily-reports/README.md): how each member records daily progress, and the shared log.
- [docs/](docs/): original project source documents (PDF). Where they conflict with the revised ownership and timeline, the revised documents take precedence. See MVP_FEATURES §11.

## Team and contribution

The pilot is built by eight interns under BNCS and mentor supervision. Current roles are from the revised ownership, effective 26 October 2026:

| Member | Role | Primary areas |
|---|---|---|
| Aryan Ghai | Technical Project Coordinator, Product Operations and Integration Governance | `docs/governance/`, backlog and decision records, README/AGENTS/CLAUDE, daily-report process |
| Ajendra Nath Tripathi | Cybersecurity and DevSecOps Engineer | `docs/security/`, security CI jobs, Dependabot, `.gitignore` |
| Adrika T Kumar | Product UX and Commercial Workflow Analyst | `docs/product/`, requirement content of MVP_FEATURES |
| Priyanka Singh | Frontend Web and Client-Side Integration Engineer | `frontend/` (Next.js) |
| Abhishek Kumar | Application Backend and Access-Control Engineer | Django config and API layer, `docs/api/`, Compose and backend image |
| Vishal Chauhan | Data and Platform Services Engineer | Models, migrations (including pgvector), queries, seed data, `docs/data/` |
| Alok Tiwari | AI Matching and Data Intelligence Engineer | `backend/apps/matching/engine/`, providers, criteria, `docs/ai/` |
| Harish Pal | QA and Test Automation Engineer | `e2e/`, test CI jobs, `docs/qa/` |

**How we work:**

- Every change goes through a focused pull request with at least one relevant peer review.
- Each PR links to an `M#-AC#` requirement and reports the tests that were actually run.
- Every member records their own progress each working day in [docs/daily-reports/](docs/daily-reports/README.md), including completed work with evidence, work in progress, tests run, blockers and next steps.
- Technical decisions are recorded in ARCHITECTURE.md §9. Deviations from the build manual need BNCS and mentor approval (ARCHITECTURE.md §10). Business decisions (commercial policy, readiness criteria, eligibility rules and weights, decision labels, permissions, scope) and acceptance of material security risk go to BNCS.
- If you use an AI coding agent, state your role at the start of your prompt (for example `@role: backend`). See [AGENTS.md § D](AGENTS.md#d-role-activation).

The pilot runs from 26 October to 18 December 2026, with feature freeze after Week 6 (4 December).
