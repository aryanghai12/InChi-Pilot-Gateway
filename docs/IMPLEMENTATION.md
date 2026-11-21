# InChi Pilot Gateway — Implementation and Setup Guide

This guide takes you from an empty machine to a running InChi Pilot Gateway, then explains how the code is organised, how to run every test, and how to fix the problems people usually hit. It assumes no prior knowledge of Docker, Django or Next.js.

| | |
|---|---|
| **Applies to** | Repository state of 21 November 2026 (end of Week 4) |
| **Verified** | Every command in §3 and the smoke checks in §3.6 were run on that date. The full stack built and all four services became healthy. Test results are in §6. |
| **Owner** | Aryan Ghai (integration and setup guide). Reviewers: Abhishek, Priyanka, Alok, Harish. |
| **Status of the product** | Supervised, non-production pilot. Synthetic data only. See [README](../README.md#current-status) for what works today and what does not. |

> [!WARNING]
> **Known Critical security defect (AUD-01).** Anyone who can reach the app can create a `platform_admin` account through `POST /api/v1/auth/register/`. Keep the frontend bound to `127.0.0.1` (the default) and do not expose this environment on a shared network until the defect is closed. Details: [governance/AUDIT_2026-11-21.md](governance/AUDIT_2026-11-21.md#4-findings-register).

**Contents**

1. [What you are setting up](#1-what-you-are-setting-up)
2. [Install the prerequisites](#2-install-the-prerequisites)
3. [Option A: run everything with Docker (recommended)](#3-option-a-run-everything-with-docker-recommended)
4. [Option B: native development](#4-option-b-native-development)
5. [How the code is organised](#5-how-the-code-is-organised)
6. [Running tests and quality checks](#6-running-tests-and-quality-checks)
7. [The matching engine today](#7-the-matching-engine-today)
8. [Everyday tasks](#8-everyday-tasks)
9. [Environment variable reference](#9-environment-variable-reference)
10. [Troubleshooting](#10-troubleshooting)
11. [Glossary](#11-glossary)

---

## 1. What you are setting up

The application has four parts. Each runs as its own Docker container (a "service"):

```
            Your browser
                 │  http://localhost:3000   (the only address you ever open)
                 ▼
   ┌───────────────────────────────┐
   │ frontend  · Next.js (port 3000)│  Draws the pages. Forwards /api/*, /admin/*
   │                               │  and /static/* to the backend ("proxy").
   └───────────────┬───────────────┘
                   ▼
   ┌───────────────────────────────┐        ┌───────────────────────────────┐
   │ backend · Django + DRF (8000) │──HTTP─►│ matching · FastAPI (8001)     │
   │ Login, permissions, records,  │        │ AI matching engine. Never     │
   │ workflows, audit trail        │        │ touches the database.         │
   └───────────────┬───────────────┘        └───────────────────────────────┘
                   ▼
   ┌───────────────────────────────┐
   │ db · PostgreSQL 17 + pgvector │  Stores everything. Data survives restarts
   │ (port 5432, local machine only)│  in a Docker "volume" called postgres_data.
   └───────────────────────────────┘
```

Only the frontend is published to your machine (plus the database on `127.0.0.1` for developers). The backend and the engine are reachable only inside Docker's private network. This "single origin" design is why login cookies and CSRF protection work without extra configuration (decision TD-09).

---

## 2. Install the prerequisites

### 2.1 For Option A (Docker) — everyone

| Tool | Version | How to check | Where to get it |
|---|---|---|---|
| Git | any recent | `git --version` | https://git-scm.com/downloads |
| Docker with Compose v2 | Docker Engine 24+ / Docker Desktop 4.x | `docker --version` and `docker compose version` (note: **space**, not hyphen) | Windows and macOS: Docker Desktop. Linux: Docker Engine plus the `docker-compose-plugin` package. |
| Free disk space | about 5 GB | — | Images for Python, Node and PostgreSQL |

**Windows users, read this before cloning.** The backend container runs a shell script (`backend/docker-entrypoint.sh`). If Git converts it to Windows line endings, the container fails with `exec /app/docker-entrypoint.sh: no such file or directory`. Run this once **before** you clone:

```powershell
git config --global core.autocrlf input
```

Use Docker Desktop with the WSL 2 backend. Run the commands below in PowerShell or in a WSL terminal.

**Linux users.** If `docker` needs `sudo`, add yourself to the `docker` group (`sudo usermod -aG docker $USER`, then log out and in).

### 2.2 For Option B (native) — developers only

Everything in 2.1, plus:

| Tool | Version | How to check |
|---|---|---|
| Python | **3.12** | `python3 --version` (Windows: `py -3.12 --version`) |
| Node.js | **20 or newer** (CI uses 22) | `node --version` |
| npm | 10 or newer | `npm --version` |

---

## 3. Option A: run everything with Docker (recommended)

This is the reference environment used for demos, UAT and handover.

### 3.1 Get the code

```bash
git clone https://github.com/aryanghai12/InChi-Pilot-Gateway.git
cd InChi-Pilot-Gateway
```

### 3.2 Create your `.env` file

The `.env` file holds your local settings and secrets. It is git-ignored and must never be committed.

```bash
# macOS / Linux / WSL
cp .env.example .env
```
```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

Open `.env` in any text editor and change these values:

| Variable | What to put | Why |
|---|---|---|
| `POSTGRES_PASSWORD` | A new password using **only letters, digits, `-` and `_`** | It is inserted into a database URL; other characters break it. |
| `DJANGO_SECRET_KEY` | A long random string. Generate one with `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` | Signs sessions and CSRF tokens. |
| `INITIAL_ADMIN_EMAIL` | A synthetic address, e.g. `admin@inchi.local` | If this and the next value are set, the first administrator is created automatically on first start. |
| `INITIAL_ADMIN_PASSWORD` | At least 8 characters, not all digits, not a common password, not similar to the email | Must pass Django's password validators or the account is not created. |

Leave everything else as it is. Notes:

- The `DATABASE_URL` line in the root `.env` is **not used** by Docker Compose. Compose builds the database URL itself from `POSTGRES_*`.
- Do not use real personal data or real passwords anywhere. This pilot runs on synthetic data only.

### 3.3 Build and start

```bash
docker compose up --build -d
```

- `--build` builds the images (the first time takes several minutes; later starts take seconds).
- `-d` runs in the background. Leave it off if you want to watch the logs in this terminal (stop with `Ctrl+C`).

What happens, in order: `db` and `matching` start → once both are healthy, `backend` waits for the database, applies migrations, collects admin static files, creates the first administrator if `INITIAL_ADMIN_*` is set, and starts gunicorn → once `backend` is healthy, `frontend` starts.

### 3.4 Check it is running

```bash
docker compose ps
```

All four services should show `Up … (healthy)`. On first start the backend can take 30–60 seconds. If one is not healthy after two minutes, see [§10](#10-troubleshooting) and `docker compose logs backend`.

### 3.5 Open the application

| What | Address |
|---|---|
| Workspace (login) | http://localhost:3000 (redirects to `/dashboard`, then to `/login` if you are not signed in) |
| Django admin (user management) | http://localhost:3000/admin/ |
| API documentation (Swagger UI) | http://localhost:3000/api/docs/ |
| OpenAPI schema (YAML) | http://localhost:3000/api/schema/ |
| Backend health check | http://localhost:3000/api/v1/health/ |

Sign in with the `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` you set.

**If you did not set `INITIAL_ADMIN_*`**, create the administrator now. You will be asked for the password twice:

```bash
docker compose exec backend python manage.py create_platform_admin --email admin@inchi.local
```

The command refuses to create a second administrator unless you add `--allow-additional`.

### 3.6 Smoke-test it (optional, 1 minute)

These are the checks run when this guide was verified:

```bash
curl -s http://localhost:3000/api/v1/health/          # {"status": "ok", ...}
curl -s http://localhost:3000/api/v1/auth/me/         # 401 {"code":"not_authenticated",...}
curl -s http://localhost:3000/api/v1/does-not-exist/  # 404 {"code":"not_found",...}
docker compose exec backend python -c "import urllib.request;print(urllib.request.urlopen('http://matching:8001/health').read().decode())"
```

### 3.7 Create more users (one per role)

There is no self-service sign-up in the pilot. A platform administrator creates accounts.

> [!CAUTION]
> **Do not use "Add user" in the Django admin for now (finding AUD-15).** The admin form saves the password as plain text, and the new user cannot log in. Use the shell command below until the owner (Abhishek) fixes the admin. Editing role or active status of an existing user in the admin is fine; do not type into its password field.

Create one synthetic user per role (passwords must pass Django's validators):

```bash
docker compose exec backend python manage.py shell -c "
from apps.accounts.models import User, Role
User.objects.create_user(email='analyst@inchi.local', password='Analyst-Synthetic-2026', role=Role.COMMERCIAL_ANALYST, is_verified=True)
User.objects.create_user(email='reviewer@inchi.local', password='Reviewer-Synthetic-2026', role=Role.REVIEWER, is_verified=True)
print('created')
"
```

Natively, run the same `python manage.py shell -c "..."` from `backend/`.

The three roles implemented today are `platform_admin`, `commercial_analyst` and `reviewer`. Baseline v2.2 defines five roles; the change is pending decision D-22.

### 3.8 Add data (there is no seed script yet)

The integrated backend has **no demo dataset or `seed_demo` command yet** (finding AUD-08; owner Vishal). Create records through the UI. A sensible first walk-through:

1. **Suppliers** → create a supplier (synthetic name), then mark it complete.
2. **Products** → add a product under that supplier (capacity, MOQ, lead time, unit).
3. **Readiness** → start an assessment for the supplier and product, answer CR-01 to CR-18, check the submission gate, submit. Sign in as a *different* user with the Reviewer role to complete the review (a reviewer cannot review their own submission).
4. **Requirements** → create a buyer requirement and use **Mark ready** when it is complete.

Matching, disposition, dashboard counts and audit history are not wired up yet (see the [README status table](../README.md#current-status)).

### 3.9 Stop, restart, reset

```bash
docker compose stop            # stop containers, keep everything
docker compose start           # start them again
docker compose down            # remove containers, KEEP the database volume
docker compose down -v         # remove containers AND DELETE ALL DATA (fresh start)
docker compose up --build -d   # rebuild after pulling new code
docker compose logs -f backend # follow logs (also: frontend, matching, db)
```

---

## 4. Option B: native development

Use this when you are changing code and want fast reloads. You run the database in Docker and the three applications directly on your machine, in three terminals.

### 4.1 Start only the database

From the repository root, with `.env` created as in §3.2:

```bash
docker compose up -d db
```

PostgreSQL is now on `127.0.0.1:5432` (change `DB_HOST_PORT` in `.env` if that port is taken).

### 4.2 Terminal 1 — Django backend

```bash
cd backend
python3.12 -m venv .venv                 # Windows: py -3.12 -m venv .venv
source .venv/bin/activate                # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt      # runtime + pytest, pytest-django, ruff
cp .env.example .env                     # Windows: Copy-Item .env.example .env
```

**Important: the backend's own `.env` uses different variable names from the root `.env`.** `backend/config/settings.py` reads `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL` and so on, without the `DJANGO_` prefix. Docker Compose translates the names for you; natively you set them directly. Edit `backend/.env`:

```dotenv
SECRET_KEY=<any random string for local use>
DEBUG=True
# Use the Compose database (password = POSTGRES_PASSWORD from the root .env):
DATABASE_URL=postgres://inchi_user:<POSTGRES_PASSWORD>@127.0.0.1:5432/inchi_pilot
# Needed only for matching integration code:
FASTAPI_MATCHING_URL=http://127.0.0.1:8001
```

If you leave `DATABASE_URL` empty, Django falls back to a local SQLite file (`backend/db.sqlite3`). That is fine for quick experiments and is what the unit tests use, but it is not the reference database.

Then:

```bash
python manage.py migrate
python manage.py create_platform_admin --email admin@inchi.local   # prompts for a password
python manage.py runserver 8000
```

### 4.3 Terminal 2 — matching engine (optional today)

Run from the `backend/` directory (the engine is imported as the `ai_matching` package):

```bash
cd backend
source .venv/bin/activate
pip install -r ai_matching/requirements-dev.txt
uvicorn ai_matching.main:app --host 127.0.0.1 --port 8001 --reload
```

Check http://127.0.0.1:8001/health. Nothing in the UI calls the engine yet (see §7), so you can skip this terminal unless you are working on matching.

### 4.4 Terminal 3 — Next.js frontend

```bash
cd frontend
npm ci              # installs exactly what package-lock.json specifies
npm run dev         # http://localhost:3000
```

`next.config.ts` forwards `/api/*` to `http://localhost:8000` by default. To point elsewhere, create `frontend/.env.local` with `BACKEND_ORIGIN=http://127.0.0.1:8000`. Always open **http://localhost:3000**, not port 8000, so the session cookie and CSRF token stay on one origin.

---

## 5. How the code is organised

Ownership of each path is defined in [ARCHITECTURE.md §4](ARCHITECTURE.md#4-repository-layout-and-ownership). Change files outside your area only with the owner's review (AGENTS.md §B rule 3).

### 5.1 Backend — `backend/`

| Path | What it does | Module | Status |
|---|---|---|---|
| `config/` | Settings from environment variables, URL routes, structured error handler (`{code, message, field_errors, correlation_id}`), JSON 404 for unknown `/api/` paths | — | Live |
| `apps/accounts/` | Custom `User` (UUID, email login, `role`), session login/logout, CSRF bootstrap, `/me`, `policy.py` (whole role matrix, marked UNAPPROVED), `create_platform_admin`, restricted Django admin | M1 | Live. **AUD-01 open** (`register/`, `verify/`) |
| `apps/registry/` | Suppliers (draft → complete → archived), products linked to suppliers, evidence metadata; `version` field for 409-on-conflict edits | M2, M3 | Live; 13 tests |
| `apps/readiness/` | China-readiness assessments: 18 questions (CR-01–CR-18), submission gate, six workflow states, three outcomes, nine evidence conditions, reviewer cannot review own submission | M4 | Live; **no tests** |
| `apps/demand/` | Buyer requirements: draft → ready_for_matching → closed, `mark-ready` completeness gate, mandatory vs preferred criteria | M5 | Live; **no tests** |
| `apps/audit/` | Append-only `AuditEvent`, `record_event()`; migration `0002` adds a PostgreSQL trigger that rejects UPDATE/DELETE | M10 | Write side live; no read API |
| `apps/matching/` | Django side of matching: `supplier_selector.py`, `request_builder.py`, `integrations/ai_engine_client.py`, `result_handler.py`, `weekly_summary.py` | M6 | Code and 62 tests; **no models, views or URLs yet** |
| `apps/dashboard/`, `apps/opportunities/` | Empty app shells | M9, M8 | Not started |
| `ai_matching/` | FastAPI engine: `services/` (preprocessing, eligibility, similarity, semantic matcher, hybrid scorer, ranking, explainability, pipeline), `providers/` (embedding providers), `criteria/v0-UNAPPROVED.json`, `schemas/`, `tests/` | M6 | Runs; 148 tests. Design pending D-21 |
| `Dockerfile` | Two targets: `django` (gunicorn) and `matching` (uvicorn) | — | Live |
| `docker-entrypoint.sh` | Waits for DB, migrates, collects static, bootstraps admin | — | Live |

**API routes served today** (all under the Next.js origin; full list in Swagger at `/api/docs/`):

| Area | Routes |
|---|---|
| Auth | `GET /api/v1/auth/csrf/`, `POST /api/v1/auth/login/`, `POST /api/v1/auth/logout/`, `GET /api/v1/auth/me/`, `/api/v1/auth/users/` |
| Registry | `/api/v1/suppliers/` (+ `{id}/complete/`, `{id}/archive/`), `/api/v1/products/`, `/api/v1/evidence/` |
| Readiness | `/api/v1/assessments/` (+ `criteria/`, `{id}/submission-gate/`, `{id}/submit/`, `{id}/request-information/`, `{id}/complete-review/`), `/api/v1/assessment-evidence/` |
| Demand | `/api/v1/requirements/` (+ `{id}/mark-ready/`, `{id}/close/`) |
| Ops | `GET /api/v1/health/`, `GET /api/schema/`, `GET /api/docs/` |

### 5.2 Frontend — `frontend/src/`

| Path | What it does |
|---|---|
| `app/login/` | Login page (fetches the CSRF cookie first) |
| `app/(workspace)/` | Signed-in area: `dashboard`, `suppliers`, `products`, `readiness`, `requirements`, `documents`, `reports`, `matching`, `opportunities`, `audit` |
| `middleware.ts` | Redirects to `/login` when there is no session cookie (convenience only; the backend enforces access) |
| `lib/api/client.ts` | `apiFetch()`: same-origin cookies, `X-CSRFToken`, standard error parsing, 401 → login |
| `lib/api/schema.d.ts` | Types generated from `docs/api/openapi.yaml` (currently stale, AUD-06) |
| `lib/readiness/`, `lib/requirements/` | Client-side display helpers (with tests). The server remains the authority. |
| `components/` | Shared form, table, feedback and navigation components |

The `matching`, `opportunities`, `audit` and `dashboard` pages call endpoints that do not exist yet and show empty states.

### 5.3 Other top-level folders

| Path | What it is |
|---|---|
| `e2e/` | Playwright suite (Harish). See [`e2e/README.md`](../e2e/README.md). |
| `database/` | A separate Django project used by the data workstream for schema and seed prototyping (Vishal). It is **not** part of the running stack; CI uses its buyer-requirement tests. |
| `.github/workflows/` | `ci.yml` (tests) and `security.yml` (gitleaks, npm audit, pip-audit, bandit) |
| `docs/` | All documentation. Start at the [README documentation map](../README.md#documentation-map). |

---

## 6. Running tests and quality checks

Results recorded on 21 Nov 2026 are shown so you can tell whether your run matches.

### 6.1 Backend (Django apps)

From `backend/` with the virtual environment active. With `DATABASE_URL` empty the tests use SQLite:

```bash
SECRET_KEY=local-test DATABASE_URL= python -m pytest --ds=config.settings apps
# 21 Nov: 84 passed, 1 skipped  (accounts 9, registry 13, matching 62 + 1 skipped; readiness 0, demand 0)
```

PowerShell: `$env:SECRET_KEY="local-test"; $env:DATABASE_URL=""; python -m pytest --ds=config.settings apps`

Other checks:

```bash
python manage.py check                                # no issues
python manage.py makemigrations --check --dry-run     # "No changes detected"
ruff check .                                          # not yet run in CI
```

### 6.2 Matching engine

```bash
python -m pytest ai_matching/tests
# 21 Nov: 148 passed, 2 skipped (the skips need a real embedding model)
```

### 6.3 Frontend

From `frontend/`:

```bash
npm run lint        # 21 Nov: clean
npm run typecheck   # 21 Nov: clean
npm test            # 21 Nov: 42 passed (5 files)
npm run build       # production build
```

### 6.4 End-to-end (Playwright)

Owned by Harish. Follow [`e2e/README.md`](../e2e/README.md): `cd e2e && npm ci && npm run preflight && npx playwright install chromium && npm test`. API tests need a running stack and synthetic users per role passed as environment variables (`E2E_BASE_URL`, `E2E_BACKEND=1`, `E2E_*_EMAIL`/`PASSWORD`). Not run during the 21 Nov audit.

### 6.5 Security checks

```bash
pip install pip-audit && pip-audit -r backend/requirements.txt
cd frontend && npm audit --audit-level=high
gitleaks detect --source . --verbose        # needs gitleaks installed
```

### 6.6 What CI runs

On every pull request, `ci.yml` runs frontend lint, typecheck, Vitest and build; backend `check`, `makemigrations --check`, the **accounts and registry** tests and `e2e/backend/test_controls.py` on PostgreSQL; the `database/` tests; and Playwright smoke. `security.yml` runs gitleaks, npm audit, pip-audit and bandit. CI does **not** yet run the `apps/matching`, `ai_matching`, readiness or demand tests, Ruff, or an OpenAPI drift check (AUD-05).

---

## 7. The matching engine today

Be clear about what is and is not working, so nobody demos something that cannot run:

- The `matching` container starts and `/health` responds. Nothing in the UI or the Django API calls it yet: there is no endpoint to run a match and no table to store results.
- `.env.example` sets `EMBEDDING_PROVIDER=sentence_transformers` and names a model, but the Docker image does **not** include the `sentence-transformers` library. The engine's design makes semantic matching mandatory, so a match run inside Compose would fail explicitly. This is tracked as AUD-07.
- The scoring configuration `criteria/v0-UNAPPROVED.json` has no approved weights, so the engine refuses to score (QA-008).
- **Baseline v2.2 (BNCS, 16 Nov 2026) says MVP matching is deterministic and rules-only, with no hidden weights**, and that the journey must work with AI disabled. How the engine is aligned is decision **D-21**, due Monday 23 Nov. Do not build further semantic features until it is recorded.

To experiment with semantic matching natively (optional, not needed for the MVP):

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r ai_matching/requirements-semantic.txt
HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 python -m ai_matching.providers.download_model
```

The embedding model is not an approved decision (D-11). Never commit a different model name as a default.

---

## 8. Everyday tasks

### Pull new code and rebuild

```bash
git pull
docker compose up --build -d     # migrations run automatically on backend start
```

### Regenerate the API schema and frontend types

Do this in the same PR as any API change (owner: Abhishek; types: Priyanka). Run natively from `backend/`:

```bash
python manage.py spectacular --file ../docs/api/openapi.yaml
cd ../frontend && npm run generate-types
```

(The container cannot write to `docs/`, because only `backend/` is copied into the image.)

### Open a Django shell or database prompt

```bash
docker compose exec backend python manage.py shell
docker compose exec db psql -U inchi_user -d inchi_pilot
```

### Back up and restore the database

```bash
docker compose exec db pg_dump -U inchi_user -Fc inchi_pilot > inchi_backup.dump
docker compose exec -T db pg_restore -U inchi_user -d inchi_pilot --clean < inchi_backup.dump
```

Full procedure: [`database/docs/backup-recovery.md`](../database/docs/backup-recovery.md).

### Change the admin URL

Set `ADMIN_URL_PATH` in `.env`, then rebuild **both** images (`docker compose up --build -d`). The Next.js rewrites are fixed at build time.

---

## 9. Environment variable reference

Root `.env` (used by Docker Compose). Compose passes each service only the variables it needs.

| Variable | Default in `.env.example` | Used by | Notes |
|---|---|---|---|
| `POSTGRES_DB`, `POSTGRES_USER` | `inchi_pilot`, `inchi_user` | db, backend | |
| `POSTGRES_PASSWORD` | placeholder | db, backend | **Required.** Letters, digits, `-`, `_` only. Changing it after the first start needs `docker compose down -v` (deletes data). |
| `DJANGO_SECRET_KEY` | placeholder | backend (`SECRET_KEY`) | **Required.** |
| `DJANGO_DEBUG` | `True` | backend (`DEBUG`) | Compose falls back to `False` if unset. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,frontend,backend` | backend | |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | backend | Add your origin if you change the port or host. |
| `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE` | `False` | backend | `True` only behind HTTPS. |
| `DJANGO_SESSION_COOKIE_AGE` | `28800` (8 h) | backend | |
| `ADMIN_URL_PATH`, `DJANGO_STATIC_PREFIX` | `admin`, `static` | backend, frontend build | Rebuild after changing. |
| `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD` | empty | backend entrypoint | Both set and no admin exists → admin created on start. |
| `MATCHING_ENGINE_TIMEOUT_SECONDS` | `30` | backend | |
| `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL_NAME` | `sentence_transformers`, a model name | matching | See §7 and AUD-07. Model not approved (D-11). |
| `MATCHING_CRITERIA_VERSION`, `MATCHING_ALLOW_UNAPPROVED_CONFIG` | `v0-UNAPPROVED`, `false` | matching (native) | |
| `HF_HUB_*`, `TRANSFORMERS_OFFLINE`, `TOKENIZERS_PARALLELISM` | offline, telemetry off | matching | Keeps pilot data on the machine. |
| `FRONTEND_HOST_PORT`, `FRONTEND_BIND` | `3000`, `127.0.0.1` | frontend | `FRONTEND_BIND=0.0.0.0` exposes it on your network. Do not do this while AUD-01 is open. |
| `DB_HOST_PORT` | `5432` | db | Always bound to `127.0.0.1`. |
| `GUNICORN_WORKERS` | `3` | backend | |

Native backend (`backend/.env`, read by `config/settings.py`): `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL` (empty = SQLite), `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `SESSION_COOKIE_AGE`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `ADMIN_URL_PATH`, `FASTAPI_MATCHING_URL`, `MATCHING_ENGINE_TIMEOUT_SECONDS`.

Native frontend (`frontend/.env.local`, optional): `BACKEND_ORIGIN` (default `http://localhost:8000`), `ADMIN_URL_PATH`, `DJANGO_STATIC_PREFIX`.

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Set POSTGRES_PASSWORD in .env` or `Set DJANGO_SECRET_KEY in .env` | No `.env`, or the value is empty | §3.2 |
| `docker: 'compose' is not a docker command` | Compose v1 or no plugin | Install Docker Desktop, or the `docker-compose-plugin` package on Linux. Use `docker compose` (space). |
| `bind: address already in use` on 3000 or 5432 | Another app uses the port | Set `FRONTEND_HOST_PORT=3001` or `DB_HOST_PORT=5433` in `.env`, then `docker compose up -d`. Add the new origin (e.g. `http://localhost:3001`) to `DJANGO_CSRF_TRUSTED_ORIGINS`. |
| Backend restarts with `exec /app/docker-entrypoint.sh: no such file or directory` | Windows line endings | `git config --global core.autocrlf input`, delete the clone, clone again, rebuild. |
| Backend log: `password authentication failed for user "inchi_user"` | You changed `POSTGRES_PASSWORD` after the database volume was created | `docker compose down -v` (deletes data), then `docker compose up --build -d`. |
| Backend log: database URL / port parse error | Special characters in `POSTGRES_PASSWORD` | Use letters, digits, `-`, `_` only; then `down -v` and start again. |
| Login says "Invalid email or password" for the bootstrap admin | `INITIAL_ADMIN_PASSWORD` failed the validators, so no admin was created; or an admin already existed | `docker compose logs backend \| grep -i admin`; create one with `create_platform_admin` (§3.5). |
| Saving a form returns 403 `csrf_failed` | You opened the site on a different host or port from the trusted origins | Use `http://localhost:3000` (or add your origin to `DJANGO_CSRF_TRUSTED_ORIGINS`), clear cookies, sign in again. |
| Redirect loop to `/login` | Stale `sessionid` cookie | Clear cookies for `localhost` and sign in again. |
| Admin page has no styling | Static prefix mismatch after changing `DJANGO_STATIC_PREFIX` | Rebuild both images. |
| `/matching`, `/audit`, `/opportunities` or `/dashboard` pages are empty | Their APIs are not built yet | Expected today (§7, AUD-09). |
| Swagger at `/api/schema/swagger-ui/` is 404 | Wrong path | Use `/api/docs/`. |
| `npm ci` fails with an engine error | Node older than 20 | Install Node 20 or 22. |
| Native backend: `ModuleNotFoundError: django` | Virtual environment not active | `source .venv/bin/activate` (Windows: `.\.venv\Scripts\Activate.ps1`). If PowerShell blocks scripts: `Set-ExecutionPolicy -Scope Process Bypass`. |
| Native engine: `ModuleNotFoundError: ai_matching` | Started from the wrong folder | Run `uvicorn ai_matching.main:app` from `backend/`, not from `backend/ai_matching/`. |

---

## 11. Glossary

| Term | Meaning |
|---|---|
| **Baseline v2.2** | BNCS's China Readiness Implementation Baseline (16 Nov 2026). Governs readiness, evidence, buyer requirements, matching and disposition. In `docs/source-documents/`. |
| **Readiness outcome** | Reviewer's categorical result: Ready for Matching, Information Required, or Not Currently Eligible. Never a score. |
| **Evidence condition** | One of nine named, non-ordinal states (e.g. Self Declared, Document Received Unverified, Expired). Receipt of a file is not verification. |
| **Eligibility result** | Matching outcome per supplier-product: Eligible, Information Required, Not Eligible. |
| **Disposition** | The human decision on a match: Accept for Follow-up, Hold for Information, or Reject, always with a reason. |
| **CSRF** | Cross-Site Request Forgery protection. The browser sends a token cookie back as the `X-CSRFToken` header. |
| **Single origin** | The browser only talks to `localhost:3000`; Next.js forwards API calls to Django. |
| **UNAPPROVED** | Label on any business rule, weight or permission that BNCS has not approved. |
| **D-xx / TD-xx / DS-xx / AUD-xx / CRQ-xxx** | Business decision / technical decision / source discrepancy / audit finding / change request. See [governance/REGISTERS.md](governance/REGISTERS.md). |
