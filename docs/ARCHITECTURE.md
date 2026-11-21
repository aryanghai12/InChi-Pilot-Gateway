# InChi Pilot Gateway v0.1 — Architecture and Technology Stack

| | |
|---|---|
| **Status** | **Implemented baseline (end of Week 4, 21 Nov 2026; D-01), verified in the [audit](governance/AUDIT_2026-11-21.md).** Four Compose services run healthy. Approval of the Django deviation is still pending (§10). **Baseline v2.2 (BNCS, 16 Nov 2026) conflicts with §6** (rules-only matching vs mandatory semantic hybrid scoring): see D-21. Embedding model (D-11) not recorded; no LLM in v0.1 (D-20). |
| **Applies to** | All code in this repository. |
| **Change rule** | Changing anything in §1 (adding a language, framework, database, service or hosted dependency) needs a new entry in §9, reviewed by the affected owners and Ajendra and recorded by Aryan. Routine libraries inside an owner's area follow the dependency rule in AGENTS.md §B. |
| **Section owners** | Abhishek (backend, conventions, §5), Priyanka (§7), Vishal (database and data sections), Alok (§6). Aryan records §9 and §10. Ajendra reviews security-relevant changes. *21 Nov 2026: Aryan corrected factual state in the status line, §1, §4, §6.3 and §8 after the audit; section owners to review.* |

This document fixes **what** the team builds on, **where** each part lives, and records the architectural contracts governing implementation across all components.

**How to read decisions here.** **Selected**: chosen by the team, and still waiting for an approval named in §10. **Resolved**: a team technical decision with no further approval needed. **TBD / Open**: not decided; do not pick a value in code. **Superseded**: replaced by a later entry, kept so that existing references still resolve.

---

## 1. Stack

| Layer | Choice | Version line | Owner | Status |
|---|---|---|---|---|
| Frontend framework | **Next.js with the App Router**, React and TypeScript | Next.js: latest stable major at skeleton. React 19 (as Next.js requires). TypeScript pinned at skeleton. | Priyanka | Selected (D-01) |
| Frontend runtime | Node.js, running the Next.js server (`next start` / standalone output) | Active LTS line at skeleton, pinned in `package.json` `engines` | Priyanka | Selected (D-01) |
| Frontend libraries | TanStack Query (server state: loading, error, retry). Routing comes from the App Router. | pinned at skeleton | Priyanka | Selected |
| API types | `openapi-typescript` generates TS types from the backend schema | dev only | Priyanka | Selected |
| Backend language | Python | 3.12 | Abhishek | Selected (D-01) |
| Backend framework | Django | 5.2 LTS | Abhishek | Selected (D-01) |
| API layer | Django REST Framework, plus drf-spectacular for the OpenAPI schema | pinned at skeleton | Abhishek | Selected (D-01) |
| Auth | Django's built-in auth: session cookie, CSRF protection, PBKDF2 password hashing | (built-in) | Abhishek | Resolved (D-12) |
| Database | **PostgreSQL with the pgvector extension**, accessed through the Django ORM with psycopg 3 | PostgreSQL 17. pgvector version pinned at skeleton through the database image tag. | Vishal | Selected (D-01) |
| Schema management | **Django ORM and Django migrations are authoritative.** The pgvector extension and every vector column are created by Django migrations, using the `pgvector` Python package's Django integration. No hand-written schema outside migrations. | (built-in) | Vishal | Selected (D-01) |
| Matching engine | **Two-component architecture:** Django matching integration layer (`backend/apps/matching/`) coordinating data collection and persistence, communicating with the FastAPI AI Matching Engine (`backend/ai_matching/`) for input validation, embeddings, mandatory eligibility evaluation, semantic similarity, hybrid scoring, ranking, and explainability. Semantic matching is mandatory; semantic processing failure explicitly fails the run (no silent fallback). | — | Alok | Implemented as a separate service (TD-11); design conflicts with Baseline v2.2 (D-21) |
| Semantic embeddings | Local embedding generation with `sentence-transformers` (optional install, `backend/ai_matching/requirements-semantic.txt`). **Embedding model: not recorded (D-11).** Under Baseline v2.2 semantic similarity is only an optional *Could* (D-21). | `sentence-transformers==6.3.0` pinned in the optional file; not in the Docker image | Alok | Library selected; **model Open** |
| LLM | **None in v0.1. Provider and model TBD (D-20).** An LLM is not a prerequisite for the MVP. No LLM SDK, configuration or prompt is added to the codebase. | — | — | **TBD** |
| Backend tests | pytest + pytest-django | — | code owners; Harish | Selected |
| Frontend tests | Vitest + React Testing Library | — | Priyanka; Harish | Selected |
| End-to-end tests | Playwright (TypeScript) | — | Harish | Selected |
| Lint and format | Python: Ruff (lint, format, and `S` security rules). TS: ESLint with the Next.js config, Prettier and `tsc`. | — | owners | Selected |
| Security checks | `pip-audit`, `npm audit`, gitleaks, Dependabot, `manage.py check --deploy` | — | Ajendra | Selected |
| Packaging | pip with pinned `requirements*.txt`; npm with `package-lock.json` | — | owners | Selected |
| Local environment | Docker Compose: `db` (`pgvector/pgvector:0.8.6-pg17-bookworm`), `matching` (FastAPI under uvicorn), `backend` (Django under gunicorn) and `frontend` (Next.js standalone server) | Compose v2 | Abhishek, Vishal (db), Alok (matching), Priyanka (frontend service) | Implemented |
| CI | GitHub Actions | — | Harish (tests), Ajendra (security) | Selected |
| Tracking | GitHub Issues and Projects in this repository | — | Aryan | Resolved (D-18) |

**Runtime requirements.** To run the full stack you need:

- Docker with Compose v2. For native development, also Python 3.12 and the pinned Node.js LTS.
- The default images install **no PyTorch and no model**. With the current engine design (semantic stage mandatory) a match run therefore fails explicitly until D-21 and D-11 are resolved.
- Semantic matching adds the optional `requirements-semantic.txt` install (CPU-only PyTorch, roughly a few hundred MB). The model's own download size is unknown until D-11 is decided.
- No GPU is required or assumed.

**Version rule.** "Pinned at skeleton" means:

- When the owner creates the skeleton, they choose the latest stable release that fits the version lines above.
- They pin exact versions in `requirements*.txt`, `package-lock.json` and the database image tag.
- They record those versions in the skeleton PR.

After that, versions change only through Dependabot or an owner PR that runs the full CI. Major-version upgrades need a §9 entry.

**Explicitly not used in v0.1:**

- Spring Boot or a JVM.
- External hosted AI or embedding APIs (all embeddings and matching execute locally).
- Any vector database other than pgvector inside PostgreSQL.
- An external AI, embedding or LLM API. Pilot data never leaves the environment.
- An LLM of any kind, until D-20 is decided and approved.
- Next.js as a second backend. That rules out Route Handlers, Server Actions and middleware holding business logic, authorisation or secrets (§7).
- Redis, message queues or Celery; Elasticsearch; Kubernetes; cloud-managed services.
- A UI component framework, a global state library or a form library.
- GPU-specific dependencies.

A proposal to add any of these needs a §9 entry.

---

## 2. Why this stack

The build manual (§7) recommends a baseline of Next.js, Spring Boot, PostgreSQL, a separate Python/FastAPI matching service, and pgvector "where approved". The team kept the parts that fit an eight-week internal pilot and removed the parts that add integration risk without user value. §10 lists every difference and the approval each one needs.

| Decision | Reason |
|---|---|
| **Next.js App Router + React + TypeScript** | Follows the manual's frontend baseline, and the App Router is the current Next.js routing model. The cost is a Node.js server at runtime. The team limits that cost with one rule: **Next.js renders and proxies, Django decides.** All business logic, validation and authorisation live in Django (§7). |
| **One backend in Python (Django), not Spring Boot plus FastAPI** | Matching must be Python because of the embedding ecosystem. Putting the application backend in Python too gives one backend language, one dependency tool, one test runner, one backend deployable and one set of backend security checks. |
| **Django rather than FastAPI** | Django ships the parts this pilot most needs to get right, already reviewed and secure by default: users, password hashing, sessions, CSRF, ORM, migrations, transactions and an admin. Auth is where the pilot can least afford mistakes. |
| **DRF** | Mature serializers (validation with field-specific errors), permission classes (deny-by-default plus object checks), pagination, and OpenAPI generation through drf-spectacular. |
| **Two-component matching architecture (Django layer + FastAPI AI engine)** | Aligns with the Build Manual §7 baseline recommendation ("Python and FastAPI for the isolated matching service"). Keeps a clean architectural boundary between Django business orchestration and pure AI/vector computation. The FastAPI engine (`backend/ai_matching/`) handles validation, embeddings, similarity, scoring, ranking, and explainability, while Django (`backend/apps/matching/`) retains business data authority, persistence, and workflow integration. The engine runs as a separate Compose service (TD-11). |
| **PostgreSQL 17 + pgvector, managed by Django migrations** | Keeps vectors in the same transactional database as the records they describe, inside the existing backup and access controls. The pgvector extension and vector columns are created by Django migrations, so the ORM stays the single authority for schema. Cosine distance is computed in SQL. At pilot volume (≥30 products, at most hundreds), an exact scan is enough and no approximate index is needed. |
| **`sentence-transformers` for embeddings, model TBD** | A widely used library that runs models locally on CPU, so **pilot data never leaves the machine**. It also leaves the model choice open across many openly licensed models. The cost is PyTorch, which is large. It is therefore an **optional** install: without it, matching runs rules-only, which is the required fallback. The model is chosen later under D-11 (§6). |
| **No LLM in the MVP** | The MVP needs deterministic, explainable output. Explanations are templates built from criterion results. Any LLM use is a later decision (D-20) with security, data-handling and BNCS review. |
| **Single browser origin through Next.js rewrites** | The browser talks only to the Next.js server. Next.js forwards `/api/`, the admin path and Django's static prefix to Django. Session cookies and CSRF work without CORS or tokens. No JWTs exist to leak, and none are stored in the browser (TD-09). |
| **Docker Compose for the reference environment** | `docker compose up` gives every member and BNCS the same demo environment (M11-AC3). Developers may run Python and Node natively against the Compose database. |

---

## 3. System shape

```
Browser
   │  one origin (http://localhost:3000 locally; HTTPS in any hosted staging)
   ▼
Next.js server (App Router)  ── renders pages; holds no secrets and no business logic
   │  rewrites: /api/v1/...      → Django
   │            <ADMIN_URL_PATH> → Django admin
   │            Django static    → Django (admin assets only)
   ▼
Django + DRF (gunicorn)
   ├─ accounts      users, roles, login/logout, session, policy.py
   ├─ registry      suppliers, products, evidence metadata
   ├─ readiness     question sets, assessments, reviews
   ├─ demand        buyer requirements (versioned), criteria
   ├─ apps/matching (Django layer: selectors, services, persistence) ── HTTP / API ──► ai_matching (FastAPI AI engine: eligibility, embeddings, similarity, scoring, ranking, explain)
   │                  └─ providers: none | sentence_transformers (model TBD, D-11), local only
   ├─ opportunities opportunities, activities
   ├─ audit         append-only audit events
   └─ dashboard     read-only aggregate queries
   ▼
PostgreSQL 17 + pgvector   (schema owned by Django migrations)
```

---

## 4. Repository layout and ownership

This section is the **single source of truth** for where code and documents live and who owns them. AGENTS.md (role definitions) and README.md (overview) link here and do not repeat it.

Create a directory when your work starts. Do not create empty placeholder folders. The tree below shows the layout **as built on 21 Nov 2026**. Items marked *(planned)* are agreed but do not exist yet.

### 4.1 Layout

```
.
├── README.md, AGENTS.md, CLAUDE.md     project overview; team and AI-agent instructions
├── .env.example                        every environment variable, placeholder values only
├── .gitignore                          .env, .env.*, !.env.example, venvs, node_modules, .next, caches
├── docker-compose.yml                  db (PostgreSQL 17 + pgvector), matching, backend, frontend
├── .github/
│   ├── workflows/ci.yml                test jobs (Harish)
│   ├── workflows/security.yml          gitleaks, npm audit, pip-audit, bandit (Ajendra)
│   └── dependabot.yml                  pip, npm, GitHub Actions
│
├── backend/                            Django project + FastAPI engine: the only API and the only authority
│   ├── manage.py, Dockerfile           Dockerfile targets: `django` (gunicorn) and `matching` (uvicorn)
│   ├── docker-entrypoint.sh            wait for DB, migrate, collectstatic, optional admin bootstrap
│   ├── requirements.txt                runtime dependencies (Django, DRF, drf-spectacular, psycopg, gunicorn, whitenoise)
│   ├── requirements-dev.txt            pytest, pytest-django, ruff
│   ├── .env.example                    native-run variables (unprefixed names read by config/settings.py)
│   ├── config/                         settings (from env vars), urls, exception handler, middleware
│   ├── apps/
│   │   ├── accounts/                   custom User + role, auth endpoints, policy.py, permissions.py, create_platform_admin (M1)
│   │   ├── registry/                   suppliers, products, evidence metadata               (M2, M3)
│   │   ├── readiness/                  assessments, criteria, evidence conditions, review   (M4)
│   │   ├── demand/                     buyer requirements, mark-ready gate                  (M5)
│   │   ├── audit/                      AuditEvent model, record_event(), immutability trigger (M10)
│   │   ├── matching/                   Django matching integration layer                    (M6, M7)
│   │   │   ├── services/               matching_service.py, request_builder.py, supplier_selector.py,
│   │   │   │                           result_handler.py, weekly_summary.py (Alok; queries designed with Vishal)
│   │   │   ├── integrations/           ai_engine_client.py: HTTP client for the engine (Alok)
│   │   │   ├── schemas/, exceptions/   request/response dataclasses and errors (Alok)
│   │   │   ├── tests/                  integration and workflow tests (Alok)
│   │   │   └── models.py, views.py, serializers.py, urls.py, permissions.py   (planned: Vishal models, Abhishek API)
│   │   ├── dashboard/                  empty app shell; queries.py and read-only API (planned, M9)
│   │   └── opportunities/              empty app shell (planned, M8; scope pending D-24)
│   │   (each app grows: models.py, migrations/, serializers.py, views.py, urls.py, tests/)
│   └── ai_matching/                    FastAPI AI matching engine (separate Compose service, TD-11; Alok)
│       ├── main.py                     app, middleware, error handlers
│       ├── api/                        dependencies.py, routes/health.py (GET /health), routes/matching.py (POST /match)
│       ├── core/                       config.py, constants.py, exceptions.py, logging.py, scoring_config.py
│       ├── schemas/                    buyer.py, supplier.py, matching.py, result.py, common.py
│       ├── services/                   preprocessing, eligibility, similarity, semantic_matcher, hybrid_scorer,
│       │                               ranking, explainability, matching_pipeline
│       ├── providers/                  embedding provider interface and download_model.py
│       ├── criteria/                   v0-UNAPPROVED.json (no approved weights; D-05 decided "no weights" by v2.2)
│       ├── requirements.txt, requirements-dev.txt, requirements-semantic.txt (optional)
│       └── tests/                      eligibility, preprocessing, similarity, embeddings, scoring, pipeline, API
│   (planned: seed_demo management command with the v2.2 §3.2 synthetic dataset — Vishal)
│
├── database/                           data-workstream prototype Django project (Vishal): demand models,
│                                       buyer-requirement seed_demo, docs/. Not part of the running stack.
├── frontend/                           Next.js App Router app (React + TypeScript)
│   ├── package.json, package-lock.json
│   ├── next.config.ts                  rewrites to Django, security headers, standalone output
│   ├── tsconfig.json, eslint.config.mjs, vitest.config.ts
│   ├── Dockerfile                      frontend image (Next.js standalone server)
│   └── src/
│       ├── app/                        routes: layout.tsx, not-found.tsx, login/, and an authenticated
│       │                               (workspace)/ group with dashboard/, suppliers/, readiness/,
│       │                               requirements/, matching/, opportunities/, audit/
│       ├── components/                 shared form, table, status and empty-state components
│       └── lib/api/                    apiFetch(), generated OpenAPI types, TanStack Query hooks
│       (unit tests sit beside the code as *.test.ts(x))
│
├── e2e/                                Playwright end-to-end and regression suite
│
└── docs/
    ├── IMPLEMENTATION.md               setup and implementation guide (Aryan)
    ├── MVP_FEATURES.md                 what to build: modules, acceptance criteria, business decisions
    ├── ARCHITECTURE.md                 how to build it: this file
    ├── source-documents/               original program and specification PDFs (read-only reference)
    ├── daily-reports/                  weekly progress log: process README + one file per member (legacy path retained)
    ├── governance/                     registers, integration plan, audit reports, gate records
    ├── product/                        (planned) journeys, field dictionary, workflow states, wireframes, user guide
    ├── security/                       threat model, data classification, access matrix, remediation register
    ├── api/openapi.yaml                generated by drf-spectacular; CI checks drift
    ├── data/                           (planned) data dictionary, ERD, migration notes; today these live in database/docs/
    ├── ai/                             engine interface, criteria notes, model decision, evaluation pack, limitations
    └── qa/                             test strategy, traceability, defect process, QA and UAT reports, demo script
```

**Where tests go.**

| Test type | Location | Owner |
|---|---|---|
| Backend unit and API tests | `backend/apps/<app>/tests/` | Owner of the code under test |
| Django matching integration and workflow tests | `backend/apps/matching/tests/` | Alok |
| AI matching algorithm and engine unit tests | `backend/ai_matching/tests/` | Alok |
| Frontend component and hook tests | beside the code in `frontend/src/` | Priyanka |
| Cross-stack end-to-end and regression | `e2e/` | Harish |
| Test strategy, traceability and results | `docs/qa/` | Harish |

**How the parts fit together.**

- **Frontend.** The Next.js app only calls `/api/v1/`, through `apiFetch()`.
- **Backend.** Django is the only component that reads or writes the database. It is also the only place where permission and workflow decisions are made.
- **Matching.** Django's `matching/services.py` calls the engine with plain data, and the engine never touches the database.
- **Database.** Its shape is defined only by Django migrations.
- **Documentation.** The docs record the contracts between these parts:
  - the OpenAPI file (frontend ↔ backend);
  - the data dictionary (API layer ↔ models);
  - the engine interface in `docs/ai/` (orchestration ↔ engine);
  - the field dictionary (product intent ↔ everything).

### 4.2 Ownership

The **owner** does the work and keeps the area consistent. **Reviewers** must review changes that touch the area.

| Path | Owner | Reviewers |
|---|---|---|
| `README.md`, `AGENTS.md`, `CLAUDE.md` | Aryan (maintainer) | A role section's member reviews changes to it; the team reviews changes to shared rules |
| `docs/MVP_FEATURES.md` | Adrika (requirement content), Aryan (change record) | BNCS approves material changes |
| `docs/ARCHITECTURE.md` | Abhishek (backend and conventions); Priyanka, Vishal and Alok for their sections; Aryan records §9 and §10 | Ajendra for security-relevant changes |
| `docs/IMPLEMENTATION.md` | Aryan (integration and setup guide) | Abhishek, Priyanka, Alok, Harish |
| `docs/source-documents/` | Original source and specification PDFs (read-only reference). Do not edit, move or delete them. | — |
| `docs/daily-reports/README.md` (weekly-report process) | Aryan | Team |
| `docs/daily-reports/<member>.md` (weekly report) | **That member only** | Any other member (format check only) |
| `docs/governance/` | Aryan | — |
| `docs/product/` | Adrika | Aryan, affected engineers |
| `docs/security/` | Ajendra | Abhishek, Vishal, Aryan |
| `docs/api/openapi.yaml` (generated) | Abhishek | Priyanka, Alok, Harish |
| `docs/data/` | Vishal | Abhishek, Alok |
| `docs/ai/` | Alok | Adrika, Harish, Ajendra |
| `docs/qa/` | Harish | Aryan, Adrika |
| `frontend/` (including `next.config.ts` and `frontend/Dockerfile`) | Priyanka | Abhishek for API usage; Ajendra for rewrites, headers and anything touching cookies or CSRF |
| `backend/config/`; in every app `serializers.py`, `views.py`, `permissions.py`, `services.py`, `urls.py`; `accounts/policy.py`; `audit/services.py`; `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `backend/Dockerfile` | Abhishek | Ajendra for auth, settings and security-sensitive code |
| `backend/apps/<app>/models.py`, `migrations/` (including the pgvector extension migration), `dashboard/queries.py`, candidate queries, `backend/seed/` | Vishal | Abhishek, Alok, Harish, Ajendra |
| `backend/apps/matching/services/`, `selectors/`, `backend/apps/matching/tests/` (matching integration), `backend/ai_matching/` (FastAPI AI engine), `docs/ai/` | Alok | Abhishek (matching API/integration contract), Vishal (database models & vector storage), Ajendra |
| `backend/apps/<app>/tests/` | Owner of the code under test | Harish |
| `e2e/` | Harish | Priyanka |
| `docker-compose.yml` | Abhishek; Vishal for the `db` service; Priyanka for the `frontend` service | Ajendra |
| `.env.example` | Abhishek (Vishal, Alok and Priyanka add their variables) | Ajendra |
| `.github/workflows/` | Harish (test jobs), Ajendra (security and dependency jobs) | Aryan |
| `.github/dependabot.yml`, `.gitignore` (secrets baseline) | Ajendra | — |

**Ownership seams inside the backend.** In each Django app, Vishal owns all models, migrations, database schemas, PostgreSQL tables, pgvector extensions/vector columns, and database-level candidate queries and query optimization, while Abhishek owns the API layer. Alok owns the matching workflow services (`matching_client.py`, `request_builder.py`, `result_handler.py`), selector workflow and integration (`supplier_selector.py`), and integration tests in `backend/apps/matching/`, as well as the entire `backend/ai_matching/` engine. Database query design, optimization, and schema implementation remain Vishal's responsibility, coordinated with Vishal. Alok's `result_handler.py` handles FastAPI response processing and persistence coordination; it does not independently own or modify database models, migrations, or schema. A change that crosses a seam, for example a model change plus a serializer change, is reviewed by both owners.

### 4.3 When to coordinate

| If your change… | Coordinate with | Notes |
|---|---|---|
| adds or changes an API endpoint, field or error code | Abhishek + Priyanka; Vishal or Alok if data or matching is affected; Harish for tests | Regenerate `docs/api/openapi.yaml` in the same PR |
| changes a model, migration, constraint or vector column | Vishal prepares the migration-impact note; Abhishek, Alok, Harish and Ajendra review | Never edit an applied migration |
| changes the Django-to-FastAPI matching schema contract, provider interface, or candidate query | Alok + Abhishek (+ Vishal for the query) | Versioned or backward-compatible; recorded in `docs/ai/` |
| changes criteria, weights, the semantic weight, readiness rules, labels or stages | Adrika drafts → Aryan → BNCS approves | Until approved: `UNAPPROVED` placeholder config only |
| touches auth, sessions, CSRF, cookies, `next.config.ts` rewrites or headers, settings or secrets | Abhishek or Priyanka + **Ajendra** | Security review is required |
| chooses or changes the embedding model (D-11) or proposes any LLM (D-20) | Alok + Ajendra; Aryan records in §9; BNCS for D-20 | See §6 and §9 |
| changes CI jobs | Harish or Ajendra; Aryan reviews | — |
| adds a language, framework, service, database or hosted dependency | Affected owners + Ajendra; Aryan records a §9 entry | Approval as in §10 if it deviates from the build manual |

---

## 5. Backend conventions

These are binding. Owners may refine them by updating this section in a PR.

| Topic | Convention |
|---|---|
| API base | `/api/v1/`. Plural resource nouns, e.g. `/api/v1/suppliers/{id}/`. Workflow actions as POST sub-resources, e.g. `/api/v1/assessments/{id}/submit/`. |
| Auth | DRF `SessionAuthentication` only. Endpoints: `GET /api/v1/auth/csrf/`, `POST /api/v1/auth/login/`, `POST /api/v1/auth/logout/`, and `GET /api/v1/auth/me/` (returns the role, used by the UI for navigation). Login calls Django's `login()`, which rotates the session key and the CSRF token. |
| CSRF on login | DRF does **not** CSRF-check anonymous requests, so the login view needs explicit protection. Decorate it with `@method_decorator(csrf_protect)` and use `authentication_classes = []` so DRF does not exempt it. **Bootstrap:** the frontend calls `GET /api/v1/auth/csrf/` (decorated with `ensure_csrf_cookie`) before showing the login form, then sends the `csrftoken` cookie value as `X-CSRFToken`. After login and logout the frontend re-reads the rotated cookie. Logout is a POST with CSRF. |
| Requests through the Next.js proxy | Requests reach Django through the Next.js rewrites (TD-09). Configure these settings from environment variables, and have Ajendra review them: (1) `CSRF_TRUSTED_ORIGINS` lists the public browser origin; (2) `ALLOWED_HOSTS` includes the host Django is reached on; (3) `SECURE_PROXY_SSL_HEADER` is set only where a trusted HTTPS proxy sets `X-Forwarded-Proto`. Never disable CSRF to make the proxy work. |
| 401 vs 403 | DRF returns `NotAuthenticated` as 403 under session auth. The custom exception handler converts `NotAuthenticated` (and expired sessions) to **401** with `code: "not_authenticated"`. Every real permission denial stays **403** with `code: "permission_denied"`. A CSRF failure returns **403** with `code: "csrf_failed"`. The frontend acts on these codes (§7). |
| Cookies | Session cookie `HttpOnly`, `SameSite=Lax`, `Secure` whenever served over HTTPS. CSRF token sent in the `X-CSRFToken` header. Session timeout set by environment variable (default 8 hours). |
| Users and roles | A custom `User` model (created in the first migration) with a single `role` field: `platform_admin`, `commercial_analyst` or `reviewer`. No self-registration. |
| User management | The Django admin, mounted at a path set by `ADMIN_URL_PATH`. Only the `User` model is registered, through a custom `UserAdmin` whose `has_module_permission`, `has_view_permission`, `has_add_permission` and `has_change_permission` return true only for `role == platform_admin`. `has_delete_permission` is always false; deactivate users instead. `is_staff` is derived from the role when the user is saved, and `is_superuser` is never set outside local development. A user cannot deactivate themselves or change their own role. Admin changes write audit events. This replaces a custom admin screen in the frontend. |
| First administrator | The `manage.py create_platform_admin --email <email>` command (Abhishek): (1) creates a `platform_admin` user with `is_superuser=False`; (2) reads the password interactively with `getpass`, or from the `INITIAL_ADMIN_PASSWORD` environment variable when run non-interactively, for example in Compose; (3) runs Django's password validators; (4) refuses if any `platform_admin` already exists, unless `--allow-additional` is passed; (5) writes an audit event with actor `system`. `createsuperuser` and direct database edits are not used for pilot accounts. `seed_demo` creates one synthetic user per role, with passwords taken from `DEMO_USER_PASSWORD`. No password is ever committed. |
| Authorisation | `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]`, plus one explicit role-permission class per view. **Deny-by-default.** Object-level access is enforced in `get_queryset()` and in `has_object_permission()`. The **whole** role-permission matrix lives in one module, `accounts/policy.py`, marked `UNAPPROVED` until BNCS decides D-09. Views reference the policy and never hard-code role checks. See MVP_FEATURES §5. |
| Validation | DRF serializers, using the field dictionary. Model constraints back up serializer checks. |
| Errors | A custom DRF exception handler. Every error is `{"code", "message", "field_errors": {field: [msg]}, "correlation_id"}`. No stack traces. `DEBUG=False` outside local dev. |
| Correlation ID | Middleware reads or generates `X-Correlation-ID`, returns it, and includes it in logs and audit events. |
| Concurrency | Editable records have an integer `version`. PATCH and PUT must send it. A mismatch returns `409 conflict`. |
| Pagination | `PageNumberPagination`, default page size 25. |
| Workflow | State transitions only happen through service functions in `services.py` that check the allowed-transition table. Never set a state by writing a field directly. |
| Audit | `audit.services.record_event(actor, action, obj, outcome, reason=None, changes=None)` is called inside the same `transaction.atomic()` as the change. The `AuditEvent` table has no update or delete path in the app, and a migration adds a PostgreSQL trigger that rejects `UPDATE` and `DELETE`. |
| Search | ORM `icontains` (ILIKE) on indexed columns. Full-text search only if seed-volume tests show a need. |
| Vectors | The `pgvector` Python package provides the Django field, the `VectorExtension` migration operation and the distance functions (Vishal). The extension is enabled by a Django migration. If the database role cannot create extensions, for example in a hosted database, an administrator creates it once before `migrate`. |
| URL routing | Django serves only: (1) `/api/v1/...`, where unmatched `/api/` paths return the JSON error shape with 404; (2) the admin path; (3) Django's own static files for the admin, served by WhiteNoise under a prefix that Next.js forwards; (4) a health endpoint. Django does **not** serve the frontend, so there is no catch-all (TD-07 is superseded by TD-09). |
| OpenAPI | Generated by drf-spectacular. CI runs `manage.py spectacular --file docs/api/openapi.yaml` and fails if the committed file is out of date. The frontend generates types from that file. |
| Configuration | All settings come from environment variables (`os.environ`). `.env.example` lists every variable. There is no settings file holding secrets. |
| Logging | Standard `logging` writing JSON-ish lines to stdout. Never log passwords, session IDs, CSRF tokens or full request bodies. |

---

## 6. Matching implementation

This implements MVP_FEATURES §7 and module M6. The matching engine combines mandatory business eligibility checks, semantic embeddings, hybrid scoring, ranking, and explainability. **Semantic matching is mandatory; failures fail explicitly with no silent fallback.**

> [!IMPORTANT]
> **Conflict with Baseline v2.2 (BNCS, 16 Nov 2026), decision D-21 open.** v2.2 §9 makes MVP matching deterministic and rules-only, with preferences shown as "Met X of Y" and no hidden weights, no confidence percentage, and a journey that works with AI disabled. Semantic similarity is only an optional *Could* that needs explicit human confirmation (§3). The design below (mandatory semantic stage, hybrid score, ranking by score) is on hold until D-21 is recorded. Under v2.2, results are `ELIGIBLE` / `INFORMATION_REQUIRED` / `NOT_ELIGIBLE` with per-criterion Pass / Unknown / Fail, and dispositions are `ACCEPT_FOR_FOLLOW_UP` / `HOLD_FOR_INFORMATION` / `REJECT` (D-06). Section owner: Alok.

### 6.1 Two-Component Architecture

The matching system is partitioned into two distinct components within `backend/`:

1. **Component A: Django Matching Integration Layer (`backend/apps/matching/`)**
   - **Role:** Coordinates the matching workflow within Django, collects business data, prepares matching requests, calls the FastAPI engine, and persists results.
   - **`selectors/supplier_selector.py`:** Owns matching selector workflow and integration. Database query design, candidate queries, and query optimization remain Vishal's responsibility (coordinated with Vishal).
   - **`services/request_builder.py`:** Validates and formats the payload into the required schema.
   - **`services/matching_client.py`:** Communicates with the FastAPI AI Matching Engine over HTTP.
   - **`services/result_handler.py`:** Handles FastAPI response processing and persistence coordination in atomic transactions. It does not independently own or modify database models, migrations, or schema (models and migrations owned by Vishal).
   - **`views.py` & `serializers.py`:** DRF endpoints for triggering matching and retrieving results for authorized users and review workflows (M8).
   - **`permissions.py`:** Enforces role-based access for matching operations.
   - **`tests/`:** Django integration, workflow, request builder, and client communication tests.

2. **Component B: FastAPI AI Matching Engine (`backend/ai_matching/`)**
   - **Role:** The core AI matching engine, running as an independent service or process.
   - **`main.py`:** FastAPI application entry point, lifecycle events, and middleware.
   - **`api/routes/`:** Endpoints including `/health` and `/matching` (`POST /match`).
   - **`schemas/`:** Pydantic models defining strict request and response schemas (`supplier.py`, `requirement.py`, `matching_request.py`, `matching_response.py`).
   - **`core/`:** Engine configuration (`config.py`), constants, and custom domain exceptions.
   - **`engine/eligibility/`:** Evaluates mandatory criteria as hard gates.
   - **`engine/semantic/`:** Computes semantic similarity between buyer requirements and supplier capabilities via vector embeddings and cosine similarity.
   - **`engine/scoring/`:** Combines rule scores and semantic scores into approved hybrid scores.
   - **`engine/ranking/`:** Sorts eligible suppliers by hybrid score descending (tie-breaking: rule score DESC → supplier ID ASC).
   - **`engine/explainability/`:** Generates deterministic Python-based explanations and missing data warnings.
   - **`embeddings/` & `providers/`:** Local embedding model management, vector mathematics, and provider abstraction.
   - **`tests/`:** Algorithm-level unit tests for eligibility, embeddings, semantic similarity, scoring, ranking, and explainability.

---

### 6.2 The Complete 9-Stage Matching Pipeline

```mermaid
flowchart TD
    A["1. Data Preparation & Normalisation<br/>(Django selectors -> request_builder)"] --> B["2. Mandatory Eligibility Checks<br/>(Hard gates; unknown != pass)"]
    B --> C{"Eligible?"}
    C -->|"Fail / Unknown"| D["Excluded / Flagged as Insufficient Data<br/>(Cannot be overridden by similarity)"]
    C -->|"Pass"| E["3. Semantic Matching<br/>(Local vector embeddings)"]
    E --> F["4. Cosine Similarity Calculation<br/>(Bounded similarity signal)"]
    F --> G{"Semantic Success?"}
    G -->|"Failure / Unset"| H["Match Run FAILS Explicitly<br/>(No silent rules-only fallback)"]
    G -->|"Success"| I["5. Hybrid Scoring<br/>(Approved weights: w_rule + w_sem)"]
    I --> J["6. Supplier Ranking<br/>(hybrid_score DESC -> rule_score DESC)"]
    J --> K["7. Explainability Generation<br/>(Python-based logic; NO external LLM)"]
    K --> L["8. Structured API Response<br/>(Returned to Django result_handler)"]
    L --> M["9. Human Review & Disposition<br/>(M8 human review: Accept / Hold / Reject)"]
```

1. **Stage 1 — Data Preparation and Normalisation:** Buyer requirements and supplier capabilities are assembled, validated, cleaned, and normalised into structured schemas.
2. **Stage 2 — Mandatory Eligibility Checks (Hard Gates):**
   - Each candidate is evaluated against mandatory criteria (e.g., category, MOQ, certifications, capacity, export capability, delivery terms — illustrative criteria examples pending formal BNCS approval under D-03).
   - **Safeguard 1:** Failing a mandatory criterion **cannot be overridden by a high semantic similarity score**. Failing suppliers are marked `Excluded`.
   - **Safeguard 2:** Missing or unknown mandatory data is **never treated as a pass**; it is marked `Insufficient Data` with an explicit warning.
3. **Stage 3 — Semantic Matching (Mandatory):**
   - Vector embeddings are generated for buyer requirement text and supplier capability text using local embedding execution.
   - Semantic matching is mandatory. Rules-only matching is **not** an alternative successful path.
4. **Stage 4 — Cosine Similarity Calculation:**
   - Computes cosine similarity between requirement and supplier vectors.
   - **Explicit Failure Policy:** If semantic processing fails or the provider raises an error, the matching run **fails explicitly** with status `Failed`. No silent fallback to rules-only matching is permitted.
5. **Stage 5 — Hybrid Scoring:**
   - Combines the weighted rule score and the bounded semantic similarity score using approved business weights:
     $$	ext{hybrid\_score} = w_{	ext{rule}} 	imes 	ext{rule\_score} + w_{	ext{sem}} 	imes 	ext{semantic\_score}$$
   - Weights and criteria are business-approved; placeholders are marked `UNAPPROVED` until formally ratified.
6. **Stage 6 — Supplier Ranking:**
   - Eligible candidates are sorted by `hybrid_score` descending.
   - Tie-breaking: `rule_score` descending, then `supplier_id` ascending.
7. **Stage 7 — Explainability Generation:**
   - Python-based deterministic logic generates structured explanations: passed/failed criteria, score contributions, similarity value, and missing-information warnings.
   - **No external LLM** is used for explainability (D-20).
8. **Stage 8 — Structured Response to Django:**
   - The FastAPI engine returns a structured JSON response (`MatchingResponse`) to Django's `result_handler.py`.
   - Results are persisted atomically in `MatchRun` and `MatchResult` records along with an immutable `AuditEvent`.
9. **Stage 9 — Human Review and Decision (M8):**
   - Authorised users review the recommendations, inspect explanations, and record a disposition (`Accepted`, `Rejected`, `On hold`) with a mandatory reason.
   - **Human-in-the-loop boundary:** AI recommends, ranks, explains, and flags uncertainty; **AI must never autonomously approve or reject suppliers**.

---

### 6.3 Technical Decisions and Open Items

- **Embedding Model (D-11):** **Not recorded.** `.env.example` currently names a model without a §9 record or Ajendra's review, and the Docker image does not install the library (AUD-07). Pilot data never leaves the environment.
- **Vector Storage (TD-01):** pgvector column design on `Product` is **Proposed / Pending Confirmation** (co-owned with Vishal; Vishal owns database models and migrations).
- **Runtime and Deployment (TD-11):** Implemented as a separate `matching` Compose service on the internal network (`http://matching:8001`); mentor confirmation pending. Contracts are in `docs/ai/`.
- **Weights and criteria (D-04, D-05, D-06):** Decided by Baseline v2.2: fixed mandatory rule sequence, no weights, v2.2 disposition codes. The engine's `v0-UNAPPROVED.json` stays unapproved until D-21 decides how the engine is aligned.

---

## 7. Frontend conventions

| Topic | Convention |
|---|---|
| Structure | `src/app/` holds App Router routes: `login/`, an authenticated `(workspace)/` route group with one folder per MVP section, and `not-found.tsx`. `src/components/` holds shared form, table, status and empty-state components. `src/lib/api/` holds the fetch wrapper, generated types and query hooks. |
| Rendering boundary (TD-10) | **Next.js renders and proxies; Django decides.** Pages that show pilot data are Client Components (`'use client'`) that fetch through `apiFetch()` and TanStack Query in the browser. Server Components are used for layout and static content only. **No** Route Handlers (there is no `src/app/api/` directory, because `/api/` belongs to Django). **No** Server Actions. **No** Next.js middleware making authorisation decisions. The Next.js server holds no secrets and never calls Django on a user's behalf except through the rewrites. |
| Rewrites (TD-09) | `next.config.ts` forwards `/api/:path*`, the admin path and Django's static prefix to `BACKEND_ORIGIN`. This is a server-side variable, not `NEXT_PUBLIC_`, and it is fixed when the frontend image is built. The browser therefore sees one origin. |
| API calls | One `apiFetch()` wrapper. It sends `credentials: 'same-origin'` and `X-CSRFToken` (read from the `csrftoken` cookie) and parses the standard error shape. All server state goes through TanStack Query. |
| Session expiry | **Only** a 401 with `code: "not_authenticated"` clears the query cache and sends the user to login, with a return URL. A 403 `permission_denied` shows the access-denied state and keeps the session. A 403 `csrf_failed` triggers one silent `GET /api/v1/auth/csrf/` and one retry of the request, then shows an error. |
| Auth in UI | Call `GET /api/v1/auth/csrf/` on app start. The `(workspace)` layout reads the role from `/api/v1/auth/me/` to guard routes and show or hide navigation (a 401 there means show login). Never treat UI hiding as authorisation. No tokens in `localStorage` or `sessionStorage`. |
| Environment variables | Only `NEXT_PUBLIC_*` variables reach the browser bundle, and none may hold a secret. Prefer none at all. |
| Forms | Controlled components with native HTML validation attributes for usability. The server's `field_errors` are shown next to the field. A success message appears only after a 2xx response. |
| Styling | Plain CSS (CSS Modules) and semantic HTML elements (`<table>`, `<dialog>`, `<label>`). No UI framework. Accessibility basics come first. |
| Security headers | Set in `next.config.ts` (`headers()`): at least a Content Security Policy suited to the app, `X-Content-Type-Options`, `Referrer-Policy` and frame protection. Priyanka implements them and Ajendra reviews (Week 6). |
| Dev server | `npm run dev` (Next.js on port 3000), with `BACKEND_ORIGIN=http://localhost:8000`, so cookies stay same-origin. |
| Routing | App Router file-system routing. Deep links and refreshes are served by the Next.js server. `not-found.tsx` handles unknown routes. |
| Tests | Vitest + React Testing Library for Client Components, hooks and `apiFetch()`. Async Server Components are covered by Playwright, not Vitest. |

---

## 8. Environments, CI and operations

| Item | Decision |
|---|---|
| Local dev | `docker compose up db`, then run Django (`manage.py runserver`) and Next.js (`npm run dev`) natively, and open `http://localhost:3000`. Or run `docker compose up` for the full stack. |
| Compose services | **As built:** `db` (`pgvector/pgvector:0.8.6-pg17-bookworm`, named volume `postgres_data`, published on `127.0.0.1` only); `matching` (FastAPI engine, internal port 8001, no semantic library installed); `backend` (Django under gunicorn, internal port 8000; starts after `db` and `matching` are healthy; entrypoint migrates, collects static and optionally bootstraps the first admin); `frontend` (Next.js standalone, published on `${FRONTEND_BIND:-127.0.0.1}:3000`). All four have health checks. |
| Reference demo environment | `docker compose up --build` on any machine with Docker; the first admin comes from `INITIAL_ADMIN_*` or `create_platform_admin`. **`seed_demo` does not exist in `backend/` yet** (AUD-08). This is the environment used for gate demos, UAT and handover. Step by step: [IMPLEMENTATION.md](IMPLEMENTATION.md). |
| Hosted staging (D-16) | **Not required for v0.1.** If BNCS provides a non-production host, the same images deploy there behind an HTTPS reverse proxy supplied by the host. Ajendra runs the staging checklist first. |
| CI (GitHub Actions) | **As built (`ci.yml`, `security.yml`):** frontend `eslint`, `tsc --noEmit`, `vitest run`, `next build`; backend `manage.py check`, `makemigrations --check`, pytest for `apps/accounts` and `apps/registry` plus `e2e/backend/test_controls.py` against a PostgreSQL service; `database/` tests; Playwright smoke; gitleaks, `npm audit`, `pip-audit`, bandit. **Target, not yet in CI (AUD-05):** Ruff, OpenAPI drift check, pgvector service image, tests for `apps/readiness`, `apps/demand`, `apps/matching` and `ai_matching`, a separate semantic-provider job, `manage.py check --deploy`. |
| Branch protection | `main` requires a PR, one approving review, and passing CI. |
| Backup and recovery | `pg_dump -Fc` and `pg_restore` through `docker compose exec db`. Restore into a database that has the pgvector extension available. Vishal documents and demonstrates the steps in Week 6. |
| Secrets | Only in local `.env` files (git-ignored) or GitHub Actions secrets. The CI database uses throwaway credentials defined in the workflow. |

---

## 9. Technical decision record

Recorded by Aryan; last updated 21 Nov 2026 after the [audit](governance/AUDIT_2026-11-21.md). Business-owned decisions are in [MVP_FEATURES §12](MVP_FEATURES.md#12-open-decisions) and the [decision register](governance/REGISTERS.md#1-decision-register). Where an entry deviates from the build manual, its approval is tracked in §10. **Resolved** means a team technical decision needing no further approval. It does not mean the code is free of defects; open defects are noted.

| ID | Decision | Resolution | Status |
|---|---|---|---|
| **D-01** | Technology stack | §1 and §2: Next.js 16 (App Router) + React 19 + TypeScript; Python 3.12 + Django 5.2 LTS + DRF; PostgreSQL 17 + pgvector, schema by Django migrations; Django matching layer + FastAPI engine; Docker Compose; GitHub Actions. | **Implemented.** BNCS + mentor approval pending (§10) |
| **D-10** | Evidence file uploads | Metadata only for v0.1. Uploads would add storage, malware scanning and document access control. Baseline v2.2 makes upload a *Should*, only if secure storage is approved. | **Resolved** |
| **D-11** | Embedding library and model | Library: `sentence-transformers`, local CPU, optional install (`ai_matching/requirements-semantic.txt`). **Model: not recorded.** `.env.example` names a model selected by Alok on 19 Nov without Ajendra's review or an entry here (AUD-07). Offline operation and telemetry-off settings are in place. | Library selected; **model Open**. Non-blocking if D-21 adopts v2.2 rules-only |
| **D-12** | Authentication and provisioning | Django session auth. Admin-provisioned local accounts through a restricted Django admin. No SSO, self-registration or email password reset. | **Resolved.** Defects open: AUD-01 (self-registration endpoint), AUD-15 (admin add form stores plaintext passwords) |
| **D-16** | Staging | The Compose reference environment is the v0.1 demo and UAT environment. Hosted staging is optional (§8). | Selected; deviates from manual, BNCS confirmation pending (§10) |
| **D-17** | Results after data changes | Runs and results are immutable and store the requirement version, criteria/rules version and embedding model (or "none"). The UI shows "data changed since this run". Consistent with v2.2 AC-18 and AC-21. | **Resolved** (not built yet) |
| **D-18** | Tracking tool | GitHub Issues (labels: module `M#`, severity, role, `weekly-report`) and one GitHub Project board. | **Resolved** |
| **D-20** | LLM provider and model | **None in v0.1.** No LLM SDK, configuration, prompts or API keys. Explanations are deterministic. Baseline v2.2 §14.2 allows only one isolated assistive experiment after Must scope passes, with human confirmation; that would need a new entry here, Ajendra's review and BNCS approval. | **None in v0.1** |
| **TD-01** | Vector storage | pgvector `vector` column in PostgreSQL 17, exact cosine distance in SQL, created by Django migrations, added only after D-11 fixes the dimension. (Formerly also labelled "D-12" in §6.3; that label is retired.) | Resolved (design); not built |
| **TD-02** | Matching boundary | Django (`apps/matching/`) owns data, persistence and workflow; the FastAPI engine (`ai_matching/`) computes and never touches the database. | **Resolved** |
| **TD-03** | Audit immutability | Append-only `AuditEvent` with no update or delete path in the app; migration `audit/0002_enforce_audit_immutability.py` adds a PostgreSQL trigger rejecting UPDATE and DELETE. | **Resolved, implemented** |
| **TD-04** | Login throttling | **Not implemented.** No throttle classes or rates are configured in `config/settings.py`, although an earlier record said "baseline throttling applied". | **Open** (Ajendra to decide; Gate 4 evidence) |
| **TD-05** | Login CSRF | `csrf_protect` on the login view plus `GET /api/v1/auth/csrf/` bootstrap. | **Resolved, verified 21 Nov** |
| **TD-06** | 401 vs 403 | 401 `not_authenticated`; 403 `permission_denied`; 403 `csrf_failed`; all in the structured error shape. | **Resolved, verified 21 Nov** |
| **TD-07** | SPA routing fallback | Was: Django served the built SPA through a GET-only catch-all. | **Superseded by TD-09** |
| **TD-08** | First administrator | `manage.py create_platform_admin --email …` (password by prompt or `INITIAL_ADMIN_PASSWORD`); the Compose entrypoint runs it once when `INITIAL_ADMIN_*` is set and no admin exists. | **Resolved, verified 21 Nov** |
| **TD-09** | Single origin through Next.js | The browser talks only to Next.js on port 3000; `next.config.ts` rewrites `/api/*`, the admin path and the static prefix to `BACKEND_ORIGIN` (build time). No CORS, no tokens in the browser. | **Resolved, verified 21 Nov** |
| **TD-10** | Next.js rendering boundary | No business logic, authorisation, secrets, Route Handlers or Server Actions in Next.js; data pages are Client Components using `apiFetch()` and TanStack Query. | **Resolved.** Review AUD-11: `middleware.ts` redirects on a missing session cookie (UX only; backend still enforces) |
| **TD-11** | FastAPI engine runtime | The engine runs as its own Compose service (`matching`, internal port 8001), built from the `matching` target of `backend/Dockerfile`; Django calls it through `apps/matching/integrations/ai_engine_client.py` (`FASTAPI_MATCHING_URL`). Previously recorded as "D-15", which collided with the business decision D-15. | **Implemented.** Mentor confirmation pending (§10) |

**Decision IDs.** `D-15` is reserved for the business question "does a Reviewer approve a requirement before matching?" (decided by Baseline v2.2 §8.2: no). Do not reuse `D-xx` numbers for technical items; add the next `TD-xx`.

---

## 10. Build manual deviations and pending approvals

The build manual (§7) gives a **recommended** baseline and states that "the final stack and material deviations remain subject to BNCS and appointed technical-mentor approval". **As of 21 Nov 2026 no such approval has been recorded.** It was due at the Week 1 Sprint Review (30 Oct 2026) and is on the [escalation list](governance/REGISTERS.md#13-pending-decisions--escalation-list). When an outcome is given, Aryan records it here and in the decision register with approver and date. If an item is rejected, Aryan re-plans with the affected owners.

| Area | Build manual §7 baseline | This architecture | Assessment | Approval needed | Status |
|---|---|---|---|---|---|
| Frontend | Next.js, React and TypeScript | Next.js 16 App Router, React 19, TypeScript | Aligned | Part of overall stack approval | Pending |
| Application backend | Spring Boot | Python 3.12, Django 5.2 LTS, DRF | **Material deviation** | BNCS + mentor | **Pending (overdue)** |
| Matching service | Python and FastAPI, as an isolated service | FastAPI engine as a separate Compose service (TD-11) plus a Django integration layer | Aligned with the manual | Mentor confirmation | Pending |
| Matching method | "Bounded semantic comparison" alongside rules | Mandatory semantic stage with hybrid scoring | **Conflicts with Baseline v2.2** (rules-only, no hidden weights; semantic only an optional *Could*) | BNCS Product Authority (D-21) | **Open — blocks Week 5** |
| Database | PostgreSQL | PostgreSQL 17, Django ORM and migrations | Aligned | Part of overall stack approval | Pending |
| Vector capability | pgvector or equivalent, "where approved" | pgvector in the same database (TD-01); not yet created | Aligned; use subject to approval and D-21 | BNCS + mentor | Pending |
| Embeddings | Not specified | `sentence-transformers`, local; model not recorded (D-11) | Consistent with AI governance; optional under v2.2 | Team decision with Ajendra's review | Open |
| LLM | Not specified | None in v0.1 (D-20) | No deviation | BNCS before any use | — |
| Authentication | Role-based authentication | Django session auth + RBAC (D-12); three roles vs v2.2's five (D-22) | Aligned on mechanism; role model pending D-22 | BNCS (D-22) | Open |
| Workflow and setup | GitHub pull-request workflow; containerised local setup | GitHub PRs and Actions; Docker Compose (four services) | Aligned | — | — |
| Staging | Non-production staging | Compose reference environment for demo and UAT; hosted staging optional (D-16) | **Deviation** | BNCS | Pending |

Business decisions (D-02 to D-09, D-13 to D-15, D-19, D-21 to D-25) are recorded in MVP_FEATURES §12 and the decision register.
