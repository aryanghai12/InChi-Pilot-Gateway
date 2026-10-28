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

**The stack is final (decision D-01, 28 Oct 2026). Nothing is implemented yet.** Full details, conventions and rationale are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

| Layer | Choice |
|---|---|
| Frontend | React + TypeScript single-page app (Vite), React Router, TanStack Query |
| Backend | Python 3.12, Django 5.2 LTS, Django REST Framework. Session auth with CSRF. OpenAPI via drf-spectacular. |
| Database | PostgreSQL 17 (Django ORM and migrations) |
| Matching | In-process Python package inside the backend. Rules first, with optional local embeddings (`fastembed`, `BAAI/bge-small-en-v1.5`) and a rules-only fallback. No external AI API. |
| Tests | pytest, Vitest + React Testing Library, Playwright |
| Environment | Docker Compose (PostgreSQL + one app container that serves the API and the built SPA) |
| Delivery | GitHub pull requests and GitHub Actions CI. Hosted staging is optional. |

This is simpler than the build manual's suggested baseline. It uses one backend language and one deployable, has no separate matching service and no vector database, and relies on Django's built-in authentication and security. The reasons are in ARCHITECTURE.md §2.

## Repository structure

What exists today:

```
.
├── AGENTS.md        Shared team and AI-agent instructions, all eight roles (source of truth)
├── CLAUDE.md        Points Claude Code to AGENTS.md
├── README.md
└── docs/
    ├── MVP_FEATURES.md                                     Definitive v0.1 scope, acceptance criteria, decisions
    ├── ARCHITECTURE.md                                     Final stack, layout, conventions, technical decisions
    ├── InChi_Pilot_Gateway_Build_Manual.pdf                Source: scope, governance (roles and dates superseded)
    ├── InChi_Pilot_User_Delivery Ownership (revised).pdf   Source: current roles (from 26 Oct 2026)
    ├── InChi_Pilot_Build Sequence Timeline (revised).pdf   Source: current weekly plan (26 Oct – 18 Dec 2026)
    ├── InChi_Pilot_User_Journey_Proposed.pdf               Source: eight-stage journey and stage owners
    ├── InChi_University_Collaboration_Internship_Program.pdf  Source: programme brief
    └── InChi_Mapped_Website_Feature_Blueprint.pdf          Source: proposed feature blueprint (audited)
```

The planned layout (`backend/` Django project with one app per module, `frontend/`, `e2e/`, `docker-compose.yml`, and subfolders of `docs/`) and its owners are set out in [docs/ARCHITECTURE.md §4](docs/ARCHITECTURE.md#4-repository-layout-and-ownership) and [AGENTS.md § B](AGENTS.md#proposed-repository-layout-and-ownership). Directories will be created as work begins.

## Setup and running

There is nothing to run yet. Setup steps, environment variables (via `.env.example`) and seed-data loading will be documented here once the backend and frontend skeletons land (Week 1 target). The planned entry point is `docker compose up`, followed by the `seed_demo` command (ARCHITECTURE.md §8). These commands do not exist yet.

## Tests and validation

No test suites or CI workflows exist yet. The test strategy and traceability matrix will be in `docs/qa/`, and commands will be listed here once they exist and have been verified.

## Documentation

- [docs/MVP_FEATURES.md](docs/MVP_FEATURES.md): what is in v0.1, acceptance criteria, permissions, matching process, feature-blueprint audit, Phase 2 list, source discrepancies and open decisions.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): final technology stack, repository layout, backend, frontend and matching conventions, CI, technical decision record.
- [AGENTS.md](AGENTS.md): engineering rules, ownership, role prompts and Definition of Done.
- [docs/](docs/): original project source documents (PDF). Where they conflict with the revised ownership and timeline, the revised documents take precedence. See MVP_FEATURES §11.

## Team and contribution

The pilot is built by eight interns under BNCS and mentor supervision. Current roles are from the revised ownership, effective 26 October 2026:

| Member | Workstream |
|---|---|
| Aryan Ghai | Project coordination, product operations and integration governance |
| Ajendra Nath Tripathi | Cybersecurity and DevSecOps |
| Adrika T Kumar | Product UX and commercial workflow |
| Priyanka Singh | Frontend and client-side integration |
| Abhishek Kumar | Application backend and access control |
| Vishal Chauhan | Data and platform services |
| Alok Tiwari | AI matching and data intelligence |
| Harish Pal | QA and test automation |

**How we work:**

- Every change goes through a focused pull request with at least one relevant peer review.
- Each PR links to an `M#-AC#` requirement and reports the tests that were actually run.
- Technical decisions are made by the team and recorded in ARCHITECTURE.md §9. Business decisions (commercial policy, readiness criteria, eligibility rules and weights, decision labels, permissions, scope) and acceptance of material security risk go to BNCS.
- If you use an AI coding agent, state your role at the start of your prompt (for example `@role: backend`). See [AGENTS.md § D](AGENTS.md#d-role-activation).

The pilot runs from 26 October to 18 December 2026, with feature freeze after Week 6 (4 December).
