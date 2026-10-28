# InChi Pilot Gateway v0.1 — Architecture and Technology Stack

| | |
|---|---|
| **Status** | **Authoritative.** D-01 resolved 28 Oct 2026. |
| **Applies to** | All code in this repository. |
| **Change rule** | Changing anything in §1 (adding a language, framework, database, service or hosted dependency) needs a new entry in §9, reviewed by the affected owners and Ajendra and recorded by Aryan. Routine libraries inside an owner's area follow the dependency rule in AGENTS.md §B. |

Nothing below is implemented yet. This document fixes **what** the team builds on, so the Week 1 skeletons can start.

The build manual (§7) says material stack deviations are subject to BNCS and mentor approval. This record is therefore shared with the mentor at the Week 1 Sprint Review for visibility. Work proceeds on it now.

---

## 1. Final stack

| Layer | Choice | Version line | Owner |
|---|---|---|---|
| Backend language | Python | 3.12 | — |
| Backend framework | Django | 5.2 LTS | Abhishek |
| API layer | Django REST Framework, plus drf-spectacular for the OpenAPI schema | pinned at skeleton | Abhishek |
| Auth | Django's built-in auth: session cookie, CSRF protection, PBKDF2 password hashing | (built-in) | Abhishek |
| Database | PostgreSQL, accessed through the Django ORM with psycopg 3 | 17 | Vishal |
| Migrations | Django migrations | (built-in) | Vishal |
| Matching | In-process Python package inside the backend. Pure-Python engine, NumPy for similarity. | — | Alok |
| Semantic embeddings | `fastembed` (ONNX Runtime, no PyTorch) with `BAAI/bge-small-en-v1.5` (384 dimensions, MIT licence), run locally. Optional install. | pinned at skeleton | Alok |
| Frontend | React with TypeScript, built with Vite, as a single-page app | React 19; Vite and TypeScript pinned at skeleton | Priyanka |
| Frontend libraries | React Router (routing), TanStack Query (server state: loading, error and retry) | pinned at skeleton | Priyanka |
| API types | `openapi-typescript` generates TS types from the backend schema | dev only | Priyanka |
| Backend tests | pytest + pytest-django | — | owners; Harish |
| Frontend tests | Vitest + React Testing Library | — | Priyanka; Harish |
| End-to-end tests | Playwright (TypeScript) | — | Harish |
| Lint and format | Python: Ruff (lint, format, and `S` security rules). TS: ESLint, Prettier and `tsc`. | — | owners |
| Security checks | `pip-audit`, `npm audit`, gitleaks, Dependabot, `manage.py check --deploy` | — | Ajendra |
| Packaging | pip with pinned `requirements*.txt`; npm with `package-lock.json` | — | owners |
| Local environment | Docker Compose: `db` (Postgres) and `app` (Django serving API plus built SPA through gunicorn and WhiteNoise) | Compose v2 | Abhishek, Vishal |
| CI | GitHub Actions | — | Harish (tests), Ajendra (security) |
| Tracking | GitHub Issues and Projects in this repository | — | Aryan |

**Version rule.** "Pinned at skeleton" means the following:

- When the owner creates the skeleton, they choose the latest stable release that is compatible with the fixed version lines above (Python 3.12, Django 5.2, PostgreSQL 17, React 19).
- They pin exact versions in `requirements*.txt` and `package-lock.json`.
- They record the versions in the skeleton PR.

After that, versions change only through Dependabot or an owner PR that runs the full CI. Major-version upgrades need a §9 entry.

**Explicitly not used:**

- Next.js or any server-side rendering
- Spring Boot or a JVM
- a separate matching microservice
- pgvector or any vector database
- an external AI or embedding API
- an LLM
- Redis, message queues or Celery
- Elasticsearch
- Kubernetes
- cloud-managed services
- a UI component framework
- a global state library
- a form library

A proposal to add any of these needs a §9 entry.

---

## 2. Why this stack

The manual's baseline (Next.js, Spring Boot, PostgreSQL, separate Python/FastAPI matching service, pgvector) works, but it needs **four runtimes** (Node, JVM, Python, Postgres), **two backend languages**, a network contract between backend and matching, and service-to-service authentication and failure handling. For eight interns and eight weeks, that is integration risk without user value.

| Decision | Reason |
|---|---|
| **One backend in Python (Django), not Spring Boot plus FastAPI** | Matching must be Python because of the embedding ecosystem. Putting the application backend in Python too gives one backend language, one dependency tool, one test runner, one deployable and one set of security checks. |
| **Django rather than FastAPI** | Django ships the parts this pilot most needs to get right, already reviewed and secure by default: users, password hashing, sessions, CSRF, ORM, migrations, transactions and an admin. FastAPI would make the team build or assemble those, and auth is where the pilot can least afford mistakes. |
| **DRF** | Mature serializers (validation with field-specific errors), permission classes (deny-by-default plus object checks), pagination, and OpenAPI generation through drf-spectacular. It is extensively documented for learners. |
| **Matching in-process, not a microservice** | Removes a network hop, inter-service auth, a second deployable, contract drift, and a whole class of failures. Replaceability (manual §2) comes from a **code** boundary instead: the engine is a pure-Python package with no Django imports, behind one function and one embedding-provider interface. If BNCS later wants a service, the package can be wrapped without rewriting it. |
| **No pgvector** | Pilot volume is ≥30 products, at most hundreds. Cosine similarity over 384-dimension vectors in NumPy takes milliseconds. Vectors are stored in a PostgreSQL `real[]` column. This avoids a database extension and its image and version coupling. |
| **fastembed + bge-small-en-v1.5** | Runs on CPU with no GPU, about 130 MB of model files, and no PyTorch, which keeps the container small and installs reliable on Windows and Linux. The licence is permissive. **Pilot data never leaves the machine.** Only model weights are downloaded once. The package is optional: without it, matching runs rules-only. That is the required fallback, and it comes for free. |
| **Vite React SPA, not Next.js** | The app is entirely authenticated and internal, so SSR, SEO and server components add nothing. A static SPA has no Node server in production, a smaller attack surface, and one clear rule: **all logic and authorisation live in Django**. React + TypeScript stays in line with the manual. |
| **Same-origin serving** | Django serves the built SPA, and the dev server proxies `/api`. Session cookies and CSRF work without CORS or token handling. No JWTs exist to leak, and none are stored in the browser. |
| **PostgreSQL** | Kept from the manual: relational integrity, transactions for audit-with-change, constraints, `pg_dump` backups. Runs in one Compose container. |
| **Docker Compose for the reference environment** | `docker compose up` gives every member and BNCS the same demo environment, which covers the repeatable-setup requirement (M11-AC3). Developers may run Python and Node natively against the Compose database. |

---

## 3. System shape

```
Browser (React SPA)
   │  same origin: /            → built SPA (WhiteNoise)
   │                /api/v1/... → JSON over HTTPS in staging / HTTP locally
   ▼
Django app (gunicorn)
   ├─ accounts      users, roles, login/logout, session
   ├─ registry      suppliers, products, evidence metadata
   ├─ readiness     question sets, assessments, reviews
   ├─ demand        buyer requirements (versioned), criteria
   ├─ matching      runs, results, dispositions  ── calls ──► matching.engine (pure Python)
   │                                                           └─ providers: none | fastembed
   ├─ opportunities opportunities, activities
   ├─ audit         append-only audit events
   └─ dashboard     read-only aggregate queries
   ▼
PostgreSQL 17
```

---

## 4. Repository layout and ownership

Create directories when work starts. Do not create empty placeholders.

```
backend/
  manage.py
  requirements.txt              runtime deps, pinned            Abhishek
  requirements-semantic.txt     fastembed (optional)            Alok
  requirements-dev.txt          pytest, ruff, pip-audit         Abhishek
  pyproject.toml                ruff + pytest config            Abhishek
  config/                       settings, urls, wsgi            Abhishek (security settings reviewed by Ajendra)
  apps/
    <app>/models.py             schema                          Vishal
    <app>/migrations/           generated + data migrations     Vishal
    <app>/serializers.py, views.py, permissions.py, services.py, urls.py   Abhishek
    <app>/tests/                tests for that app              code owner (Harish reviews)
    matching/engine/            pure-Python matching core       Alok
    matching/providers/         embedding provider interface    Alok
    audit/services.py           record_event()                  Abhishek (model: Vishal)
    dashboard/queries.py        reporting queries               Vishal
  seed/                         synthetic seed data + `seed_demo` management command   Vishal
frontend/                       Vite React TS app               Priyanka
e2e/                            Playwright suite                Harish
docker-compose.yml              db + app                        Abhishek, Vishal
Dockerfile                      multi-stage: build SPA, then Python image   Abhishek
.env.example                    placeholders only               Abhishek (Ajendra reviews)
.gitignore                      .env, .env.*, !.env.example, venvs, node_modules, caches   Ajendra
.github/workflows/ci.yml        test jobs / security jobs       Harish / Ajendra
.github/dependabot.yml                                          Ajendra
```

**Ownership seam inside the backend.** In each Django app:

- Vishal owns `models.py`, migrations and query modules.
- Abhishek owns the API layer: serializers, views, permissions, services and URLs.
- Alok owns `matching/engine/` and `matching/providers/`, which must not import Django.

A change crossing a seam is reviewed by both owners.

---

## 5. Backend conventions

These are binding. Owners may refine them by updating this section in a PR.

| Topic | Convention |
|---|---|
| API base | `/api/v1/`. Plural resource nouns, e.g. `/api/v1/suppliers/{id}/`. Workflow actions as POST sub-resources, e.g. `/api/v1/assessments/{id}/submit/`. |
| Auth | DRF `SessionAuthentication` only. Endpoints: `GET /api/v1/auth/csrf/`, `POST /api/v1/auth/login/`, `POST /api/v1/auth/logout/`, and `GET /api/v1/auth/me/` (returns the role, used by the UI for navigation). Login calls Django's `login()`, which rotates the session key and the CSRF token. |
| CSRF on login | DRF does **not** CSRF-check anonymous requests, so the login view needs explicit protection. Decorate it with `@method_decorator(csrf_protect)` and use `authentication_classes = []` so DRF does not exempt it. **Bootstrap:** the SPA calls `GET /api/v1/auth/csrf/` (decorated with `ensure_csrf_cookie`) before showing the login form, then sends the `csrftoken` cookie value as `X-CSRFToken`. After login and logout the SPA re-reads the rotated cookie. Logout is a POST with CSRF. |
| 401 vs 403 | DRF returns `NotAuthenticated` as 403 under session auth. The custom exception handler converts `NotAuthenticated` (and expired sessions) to **401** with `code: "not_authenticated"`. Every real permission denial stays **403** with `code: "permission_denied"`. A CSRF failure returns **403** with `code: "csrf_failed"`. The frontend acts on these codes (§7). |
| Cookies | Session cookie `HttpOnly`, `SameSite=Lax`, `Secure` whenever served over HTTPS. CSRF token sent in the `X-CSRFToken` header. Session timeout set by environment variable (default 8 hours). |
| Users and roles | A custom `User` model (created in the first migration) with a single `role` field: `platform_admin`, `commercial_analyst` or `reviewer`. No self-registration. |
| User management | The Django admin, mounted at a path set by `ADMIN_URL_PATH`. Only the `User` model is registered, through a custom `UserAdmin` whose `has_module_permission`, `has_view_permission`, `has_add_permission` and `has_change_permission` return true only for `role == platform_admin`. `has_delete_permission` is always false; deactivate users instead. `is_staff` is derived from the role when the user is saved, and `is_superuser` is never set outside local development. A user cannot deactivate themselves or change their own role. Admin changes write audit events. This replaces a custom admin screen in the SPA. |
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
| SPA routing fallback | URL order in `config/urls.py`: (1) `/api/v1/...` (unmatched `/api/` paths return the JSON error shape with 404, never `index.html`); (2) the admin path; (3) static assets, served by WhiteNoise from the built `frontend/dist`; (4) a final catch-all `re_path` for GET requests that returns the SPA `index.html`. The catch-all excludes paths starting with `api/`, the admin path, and `static/`. It also excludes paths with a file extension, which return a real 404. Non-GET requests to unknown paths return 404 or 405. Unknown client routes are handled by the SPA's own not-found page. In development, Vite serves the SPA and proxies `/api` and the admin path. |
| OpenAPI | Generated by drf-spectacular. CI runs `manage.py spectacular --file docs/api/openapi.yaml` and fails if the committed file is out of date. The SPA generates types from that file. |
| Configuration | All settings come from environment variables (`os.environ`). `.env.example` lists every variable. There is no settings file holding secrets. |
| Logging | Standard `logging` writing JSON-ish lines to stdout. Never log passwords, session IDs, CSRF tokens or full request bodies. |

---

## 6. Matching implementation

This implements MVP_FEATURES §7.

- **Engine API (Alok).** `engine.run(requirement, candidates, criteria_version, provider) -> MatchOutput`. The inputs and outputs are plain dataclasses. The function is pure and deterministic for a given input and provider, makes no database calls and imports nothing from Django. The output carries a status and mode for each candidate:
  - **Status:** `eligible`, `excluded` or `insufficient_data`.
  - **Mode:** `hybrid` or `rules_only`.
  - **Per candidate:** criterion results, weighted contributions, the semantic score, explanation lines and warnings.
- **Orchestration (Abhishek).** `matching/services.py` performs these steps:
  1. Checks the requirement gate.
  2. Loads candidates through Vishal's query.
  3. Selects the provider.
  4. Calls the engine.
  5. Persists the `MatchRun` and `MatchResult` rows and the audit event in one transaction.

  If the engine raises, the run is stored as `failed` with no results, and the API returns a structured error.
- **Criteria configuration.** Versioned JSON files in `backend/apps/matching/criteria/` (for example `v0-UNAPPROVED.json`), loaded into a `CriteriaVersion` row by a migration or command. The active version is set by environment variable. Changing weights is a reviewed PR with a new version file, after BNCS approval (D-04, D-05).
- **Providers.**
  - `NullProvider` always returns "unavailable", giving rules-only mode.
  - `FastEmbedProvider` loads the model lazily. If the import, download or inference fails, it reports "unavailable" and the run falls back to rules-only with a label.
  - Selection: `SEMANTIC_PROVIDER=none|fastembed`. The default is `none` until the Week 5 evaluation passes.
- **Embeddings.** Product embeddings are stored in `Product.embedding real[]`, together with `embedding_model` and `embedding_source_hash`. They are recomputed when the source text changes, or by `manage.py embed_products`. Requirement text is embedded at run time. The model cache path is set by `FASTEMBED_CACHE_PATH` and mounted as a Compose volume. Pilot data stays local; only model weights are downloaded, once.
- **Explanations.** Deterministic templates built from criterion results. No LLM.
- **Demo failure case (build manual §10, item 8).** Run with `SEMANTIC_PROVIDER=fastembed` and the model cache made unavailable, which shows the labelled rules-only fallback. Then show a requirement that fails the gate.

---

## 7. Frontend conventions

| Topic | Convention |
|---|---|
| Structure | `src/routes/` (one folder per MVP section), `src/components/` (shared form, table, status and empty-state components), `src/api/` (fetch wrapper, generated types, query hooks). |
| API calls | One `apiFetch()` wrapper. It sends `credentials: 'same-origin'` and `X-CSRFToken` (read from the `csrftoken` cookie) and parses the standard error shape. All server state goes through TanStack Query. |
| Session expiry | **Only** a 401 with `code: "not_authenticated"` clears the query cache and sends the user to login, with a return URL. A 403 `permission_denied` shows the access-denied state and keeps the session. A 403 `csrf_failed` triggers one silent `GET /api/v1/auth/csrf/` and one retry of the request, then shows an error. |
| Auth in UI | Call `GET /api/v1/auth/csrf/` on app start. Read the role from `/api/v1/auth/me/` to show or hide navigation (a 401 there means show login). Never treat UI hiding as authorisation. No tokens in `localStorage` or `sessionStorage`. |
| Forms | Controlled components with native HTML validation attributes for usability. The server's `field_errors` are shown next to the field. A success message appears only after a 2xx response. |
| Styling | Plain CSS (CSS Modules) and semantic HTML elements (`<table>`, `<dialog>`, `<label>`). No UI framework. Accessibility basics come first. |
| Dev server | Vite proxies `/api` and the admin path to `http://localhost:8000`, so cookies stay same-origin. |
| Routing | React Router with browser history. Django's catch-all (§5) serves `index.html` on refresh or direct navigation. Include a client-side not-found route. |

---

## 8. Environments, CI and operations

| Item | Decision |
|---|---|
| Local dev | `docker compose up db`, then run Django (`manage.py runserver`) and Vite (`npm run dev`) natively. Or `docker compose up` for the full stack. |
| Reference demo environment | `docker compose up` on any machine with Docker, seeded by `manage.py seed_demo`. This is the environment used for Gate demos, UAT and handover. |
| Hosted staging (D-16) | **Not required for v0.1.** If BNCS provides a non-production host, the same container image deploys there behind HTTPS. Ajendra runs the staging checklist first. |
| CI (GitHub Actions) | On every PR. **Backend:** `ruff check`, `ruff format --check`, `manage.py makemigrations --check`, `pytest` against a Postgres service container, the OpenAPI drift check, `pip-audit`. **Frontend:** `eslint`, `tsc --noEmit`, `vitest run`, `npm audit --audit-level=high`. **Repo:** gitleaks. **E2E:** Playwright against the Compose stack, from Week 2 on `main` and nightly, on PRs once it is stable. |
| Branch protection | `main` requires a PR, one approving review, and passing CI. |
| Backup and recovery | `pg_dump -Fc` and `pg_restore` through `docker compose exec db`, with the steps documented and demonstrated by Vishal in Week 6. |
| Secrets | Only in local `.env` files (git-ignored) or GitHub Actions secrets. The CI database uses throwaway credentials defined in the workflow. |

---

## 9. Technical decision record

Technical decisions resolved by the team on 28 Oct 2026. Business-owned decisions stay in MVP_FEATURES §12.

| ID | Decision | Resolution |
|---|---|---|
| **D-01** | Technology stack | §1 and §2. **Resolved.** |
| **D-10** | Evidence file uploads | **Metadata only for v0.1.** Uploads add file storage, malware scanning and document access control, which is a Phase 2 item. BNCS can request it as a scope substitution. |
| **D-11** | Embedding model and hosting | `fastembed` + `BAAI/bge-small-en-v1.5`, run locally. No external AI API. Rules-only by default until the Week 5 evaluation. |
| **D-12** | Authentication and provisioning | Django session auth. Admin-provisioned local accounts through a restricted Django admin. No SSO, self-registration or email password reset. |
| **D-16** | Staging | The Docker Compose reference environment is the v0.1 demo and UAT environment. Hosted staging is optional (§8). |
| **D-17** | Results after data changes | Runs and results are immutable and store the requirement version, criteria version and model. The UI shows "data changed since this run" when the current requirement version or product `updated_at` is newer. Users re-run to refresh. |
| **D-18** | Tracking tool | GitHub Issues (labels: module `M#`, severity, role) and one GitHub Project board. Evidence is linked from `docs/governance/`. |
| **TD-01** | Vectors | PostgreSQL `real[]` + NumPy cosine. Revisit only if the candidate count goes above about 10,000. |
| **TD-02** | Matching boundary | In-process package with a pure engine. No microservice. |
| **TD-03** | Audit immutability | App-level (no update or delete path) plus a database trigger. |
| **TD-04** | Login throttling | Not in the first skeleton. Ajendra assesses it in the Week 2 auth review. If needed, add it with one maintained package or a small custom throttle on the login view. |
| **TD-05** | Login CSRF | Explicit `csrf_protect` on the login view, plus a `GET /auth/csrf/` bootstrap (§5). |
| **TD-06** | 401 vs 403 semantics | `NotAuthenticated` is mapped to 401 `not_authenticated`. The frontend logs out only on that code (§5, §7). |
| **TD-07** | SPA routing fallback | Ordered URLconf with a GET-only catch-all that excludes the API, admin, static and file paths (§5). |
| **TD-08** | First administrator | The `create_platform_admin` management command. No superuser, no manual DB edits (§5). |
