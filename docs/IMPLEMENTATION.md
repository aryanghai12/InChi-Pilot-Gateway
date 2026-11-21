# InChi Pilot Gateway — Implementation & Setup Guide

This guide provides the complete technical walkthrough for setting up, running, testing, and developing the **InChi Pilot Gateway v0.1** platform.

---

## 1. System Overview & Architecture

The InChi Pilot Gateway is structured into four core service containers operating on a single browser origin via Next.js proxy rewrites:

```
                  ┌────────────────────────────────────────┐
                  │          Browser (User Agent)          │
                  └───────────────────┬────────────────────┘
                                      │ http://localhost:3000
                                      ▼
                  ┌────────────────────────────────────────┐
                  │    Next.js Frontend (Port 3000)        │
                  │   - App Router, React 19, TypeScript   │
                  │   - Static/SSR & API Proxy Rewrites    │
                  └─────────┬───────────────────┬──────────┘
           /api/v1/*, admin │                   │
                            ▼                   │
       ┌──────────────────────────────┐         │
       │    Django 5.2 Backend (:8000)│         │
       │  - DRF REST API              │         │
       │  - Session Auth & RBAC       │         │
       │  - Business State Machines   │         │
       │  - Append-Only Audit Trail   │         │
       └──────┬───────────────────────┘         │
              │                                 │
              │ ORM / pgvector                  │ HTTP Client (:8001)
              ▼                                 ▼
┌──────────────────────────────┐ ┌────────────────────────────────┐
│   PostgreSQL 17 + pgvector   │ │  FastAPI Matching Engine (:8001│
│  - Relational Schema         │ │  - Candidate Eligibility Filter│
│  - Vector Embeddings Storage │ │  - Local Vector Embeddings     │
│  - Named Volume: postgres_data│ │  - Cosine Similarity & Scorer  │
└──────────────────────────────┘ └────────────────────────────────┘
```

### Key Technologies
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, TanStack Query, CSS Modules.
- **Backend:** Python 3.12, Django 5.2 LTS, Django REST Framework (DRF), drf-spectacular (OpenAPI 3.0.3).
- **Database:** PostgreSQL 17 with `pgvector` extension (Docker image: `pgvector/pgvector:0.8.6-pg17-bookworm`).
- **Matching Engine:** FastAPI, Pydantic v2, local embedding providers (`sentence-transformers` interface), NumPy.
- **Testing:** pytest & pytest-django, Vitest & React Testing Library, Playwright E2E.
- **Security:** Gitleaks, pip-audit, npm audit, PBKDF2 password hashing, Django Session CSRF rotation.

---

## 2. Environment Configuration

The repository uses environment variables for all operational configuration. Real credentials are never committed.

### Root `.env` Setup
Copy the template at repository root:
```bash
cp .env.example .env
```

Key environment settings in `.env`:

| Variable | Recommended Default | Description |
|---|---|---|
| `POSTGRES_DB` | `inchi_pilot` | Database name |
| `POSTGRES_USER` | `inchi_user` | Database username |
| `POSTGRES_PASSWORD` | `<secure-synthetic-password>` | Database password (alphanumeric, `-`, `_`) |
| `DATABASE_URL` | `postgresql://inchi_user:<password>@db:5432/inchi_pilot` | Django database connection string |
| `DJANGO_SECRET_KEY` | `<secure-random-string>` | Django cryptographic signing key |
| `DJANGO_DEBUG` | `True` (dev) / `False` (staging) | Django debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,backend` | Permitted Host headers |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Trusted CSRF origins for frontend proxy |
| `FASTAPI_MATCHING_URL` | `http://matching:8001` | Matching engine endpoint for Django |
| `INITIAL_ADMIN_EMAIL` | `admin@inchi.local` | Auto-provisioned platform administrator |
| `INITIAL_ADMIN_PASSWORD` | `<synthetic-admin-password>` | Auto-provisioned administrator password |
| `EMBEDDING_PROVIDER` | `none` | Vector embedding engine (`none` for rules baseline) |
| `BACKEND_ORIGIN` | `http://backend:8000` | Backend upstream URL for Next.js proxy |
| `FRONTEND_HOST_PORT` | `3000` | Host port mapped to frontend |
| `DB_HOST_PORT` | `5432` | Host port mapped to PostgreSQL |

---

## 3. Option 1: Full-Stack Docker Compose (Recommended)

Docker Compose provides the single authoritative reference environment replicating the entire multi-service stack with a single command.

### Prerequisites
- Docker Engine 24+ and Docker Compose v2.

### Step-by-Step Launch
1. **Initialize configuration:**
   ```bash
   cp .env.example .env
   # Edit .env to supply POSTGRES_PASSWORD and DJANGO_SECRET_KEY
   ```

2. **Build and start all services:**
   ```bash
   docker compose up --build
   ```
   *(Add `-d` to run in detached background mode)*

3. **Verify service startup and health:**
   ```bash
   docker compose ps
   ```
   All 4 containers (`db`, `matching`, `backend`, `frontend`) should display `healthy` or `running`.

4. **Access the application:**
   - **Frontend Workspace:** [http://localhost:3000](http://localhost:3000)
   - **Django Admin:** [http://localhost:3000/admin/](http://localhost:3000/admin/)
   - **OpenAPI Documentation:** [http://localhost:3000/api/schema/swagger-ui/](http://localhost:3000/api/schema/swagger-ui/)
   - **FastAPI Matching Health:** internal `:8001/health`

5. **Create Initial Platform Administrator:**
   If `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` were set in `.env`, the administrator account is created automatically upon backend startup.
   Alternatively, create an administrator manually:
   ```bash
   docker compose exec backend python manage.py create_platform_admin --email admin@inchi.local
   ```

6. **Viewing Logs:**
   ```bash
   docker compose logs -f backend
   docker compose logs -f frontend
   docker compose logs -f matching
   ```

7. **Stopping and Teardown:**
   ```bash
   # Stop services (persists database volume)
   docker compose down

   # Stop and purge all data (resets database volume)
   docker compose down -v
   ```

---

## 4. Option 2: Native Local Development

For active feature coding, developers can run the PostgreSQL database in Docker while running the Django backend, FastAPI matching engine, and Next.js frontend natively on the host.

### Prerequisites
- Python 3.12+
- Node.js 20+ (Active LTS) and npm 10+
- Docker (for database container)

### 4.1 Start Local PostgreSQL with pgvector
Start only the database service via Docker Compose:
```bash
docker compose up -d db
```
The database will be accessible on `127.0.0.1:5432`.

### 4.2 Backend Setup (Django)
1. **Navigate to backend and create virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # Linux/macOS:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure local environment:**
   Copy `backend/.env.example` to `backend/.env` and update `DATABASE_URL`:
   ```bash
   DATABASE_URL=postgresql://inchi_user:<password>@localhost:5432/inchi_pilot
   SECRET_KEY=dev-secret-key-for-local-testing-only-12345
   DEBUG=True
   ```

4. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Provision administrator account:**
   ```bash
   python manage.py create_platform_admin --email admin@inchi.local
   ```

6. **Start Django development server:**
   ```bash
   python manage.py runserver 8000
   ```

### 4.3 AI Matching Engine Setup (FastAPI)
1. **Open a new terminal, navigate to matching engine and activate environment:**
   ```bash
   cd backend/ai_matching
   # You may reuse the backend venv or create an isolated one
   pip install -r requirements.txt
   ```

2. **Start FastAPI with uvicorn:**
   ```bash
   uvicorn main:app --host 127.0.0.1 --port 8001 --reload
   ```
   Verify at [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health).

### 4.4 Frontend Setup (Next.js)
1. **Open a new terminal and navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Install npm dependencies:**
   ```bash
   npm install
   ```

3. **Configure local environment (optional):**
   By default, `next.config.ts` rewrites `/api/:path*` to `http://localhost:8000/api/:path*`.
   To specify a custom backend origin, set:
   ```bash
   # In frontend/.env.local
   BACKEND_ORIGIN=http://127.0.0.1:8000
   ```

4. **Start Next.js dev server:**
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Module Implementation Breakdown

The codebase is organized strictly into modular domains conforming to the architecture specification:

### Backend Apps (`backend/apps/`)
- **`accounts/` (Module M1):**
  - Custom `User` model with UUID v4 primary keys.
  - PBKDF2 password security, session authentication, CSRF bootstrap endpoint (`GET /api/v1/auth/csrf/`).
  - Central RBAC policy engine (`policy.py`, `permissions.py`) enforcing least-privilege for `platform_admin`, `commercial_analyst`, and `reviewer`.
  - `create_platform_admin` management command.
- **`registry/` (Modules M2 & M3):**
  - `Supplier` model with lifecycle states (`draft`, `complete`, `archived`) and optimistic concurrency versioning.
  - `Product` model linked to suppliers, supporting commercial terms (MOQ, price, capacity, lead times) and bilingual Mandarin attributes (`product_name_zh`).
  - `EvidenceItem` model storing document metadata references (EVD-01 to EVD-10).
- **`readiness/` (Module M4):**
  - Implements *China Readiness Baseline v2.2*.
  - 18 compliance criteria (`CR-01` to `CR-18`) questionnaire across 6 workflow states (`draft`, `submitted`, `under_review`, `information_required`, `review_complete`, `archived`).
  - 3 categorical qualitative outcomes (`ready_for_matching`, `information_required`, `not_currently_eligible` — zero numeric scoring).
  - Reviewer decision desk with object-level `deny_self_review` enforcement.
- **`demand/` (Module M5):**
  - `BuyerRequirement` model with `draft`, `ready_for_matching`, and `closed` states.
  - Section 6.1 readiness gate validating mandatory volume, destination ports in China, and commercial terms.
- **`matching/` (Module M6 Integration Layer):**
  - Django orchestration service communicating with the FastAPI matching engine.
  - Candidate supplier selector (`services/supplier_selector.py`) filtering `ready_for_matching` candidates.
- **`audit/` (Module M10):**
  - Append-only `AuditEvent` model and `record_event()` helper capturing actor, action, timestamp, correlation IDs, and state diffs.
- **`dashboard/` (Module M9):**
  - Aggregation services providing real-time counts from stored database records.
- **`opportunities/` (Module M8):**
  - Commercial pipeline tracking for accepted match dispositions.

### FastAPI AI Matching Engine (`backend/ai_matching/`)
- **`core/`:** Configuration, logging, domain exceptions, and matching constants.
- **`schemas/`:** Pydantic v2 schemas for buyers, suppliers, candidate pools, and match results.
- **`providers/`:** Pluggable embedding interfaces (`EmbeddingProvider`) with CPU-local execution.
- **`services/`:**
  - `preprocessing.py`: Text sanitization, normalisation, and quality flag evaluation.
  - `eligibility.py`: Hard boundary filtering (mandatory buyer constraints).
  - `similarity.py`: Vector cosine similarity computation.
  - `hybrid_scorer.py`: Weighted combination of semantic and preference signals.
  - `ranking.py`: Deterministic ordering and missing-information penalty calculation.
  - `explainability.py`: Explainable rationale generator based on criteria match breakdowns.
  - `matching_pipeline.py`: 9-stage orchestrator executing the full matching cycle.

### Frontend (`frontend/src/`)
- **`(workspace)/`:** Role-aware workspace layout (`AppSidebar`, `AppHeader`, `workspace.module.css`).
  - `/suppliers`: Supplier registry list, filters, and creation drawer.
  - `/products`: Product catalogue, bilingual fields, and supplier association.
  - `/readiness`: China-readiness assessment desk, 18-criteria form, submission gate, reviewer decision desk.
  - `/requirements`: Buyer procurement requirements desk, completeness gate, and criterion builder.
  - `/reports`: Insights and operational summary metrics.
  - `/documents`: Evidence metadata registry.
- **`lib/api/`:** Centralized `apiFetch` client with automatic CSRF token management, typing, and standard error envelopes.
- **`middleware.ts`:** Next.js route guard enforcing HTTP 307 login redirects for unauthenticated users.

---

## 6. Running Tests & Quality Verification

Consistent with project rules, every change must be verified with automated test suites:

### 6.1 Backend Unit & Integration Tests
Run all backend Django tests:
```bash
# In backend/ (with venv activated) or via docker compose:
docker compose exec backend python -m pytest
# Or natively:
python manage.py test apps
```

Run specific test suites:
```bash
# Auth & RBAC controls
python -m pytest apps/accounts/tests

# Supplier & Product Registry
python -m pytest apps/registry/tests

# China Readiness Assessment Lifecycle
python -m pytest apps/readiness/tests
```

### 6.2 AI Matching Engine Tests
Run FastAPI unit tests:
```bash
cd backend
python -m pytest ai_matching/tests
```
Tests cover data preprocessing, eligibility gates, similarity calculations, and pipeline execution.

### 6.3 Frontend Unit Tests & Linting
Run frontend Vitest suites, type checks, and linter:
```bash
cd frontend

# Unit tests (Vitest)
npm test

# TypeScript type validation
npm run typecheck

# Code linting (ESLint)
npm run lint

# Production build test
npm run build
```

### 6.4 End-to-End (E2E) Tests (Playwright)
Run Playwright browser automation suites against running containers:
```bash
# From repository root or e2e/
npx playwright test
```

### 6.5 Security & Dependency Audits
Run local security baseline checks:
```bash
# Python dependency vulnerability scan
pip-audit

# Node.js dependency vulnerability scan
npm audit --audit-level=high

# Secret scanning
gitleaks detect --source . --verbose
```

---

## 7. API Schema & TypeScript Synchronization

The frontend utilizes TypeScript interfaces generated directly from the backend OpenAPI 3.0.3 specification:

1. **Export the backend schema:**
   ```bash
   docker compose exec backend python manage.py spectacular --file ../docs/api/openapi.yaml
   ```

2. **Generate TypeScript types for frontend:**
   ```bash
   cd frontend
   npx openapi-typescript ../docs/api/openapi.yaml -o src/lib/api/schema.d.ts
   ```

---

## 8. Common Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| Compose error: `Set POSTGRES_PASSWORD in .env` | Missing root `.env` | Run `cp .env.example .env` and specify a password |
| Frontend shows `403 Forbidden` on POST/PUT | CSRF token missing or mismatch | Ensure `DJANGO_CSRF_TRUSTED_ORIGINS` includes `http://localhost:3000` |
| Route redirects loop on `/login` | Expired or invalid session cookie | Clear browser cookies for `localhost` and re-authenticate |
| Matching engine returns `503 stage_not_available` | Eligibility / weights pending BNCS (D-04/D-05) | Expected behavior until Gate 2 rules are marked active in config |
| `DATABASE_URL` special characters error | Password contains URL-reserved chars | Use alphanumeric characters, `-`, or `_` only in `POSTGRES_PASSWORD` |

