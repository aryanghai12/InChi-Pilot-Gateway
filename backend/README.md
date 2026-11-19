# InChi Pilot Gateway — Backend Service

Application backend for the **InChi Pilot Gateway (v0.1)**, built with **Django 5.1** and **Django REST Framework (DRF)**. 
Provides authenticated session management, centralised Role-Based Access Control (RBAC), Supplier Registry, Product Catalogue, Evidence Metadata, Audit Logging, and Buyer Procurement Requirements.

---

## 1. Prerequisites

- **Python:** 3.11 or higher
- **Package Manager:** `pip` (v23.0+)
- **OS:** Windows, macOS, or Linux
- **Optional Database:** PostgreSQL with `pgvector` (Docker container ready in `../database/`). SQLite is used by default for local development.

---

## 2. Quickstart & Local Setup

Follow these steps to set up the local backend environment from scratch:

### Step 1: Navigate to the Backend Directory
```bash
cd backend
```

### Step 2: Create a Python Virtual Environment
Creating an isolated virtual environment (`venv`) prevents dependency conflicts with global packages:

- **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv venv
  ```

### Step 3: Activate the Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(Note: If script execution is restricted on Windows, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*
- **Windows (Command Prompt):**
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### Step 4: Install Dependencies
Upgrade `pip` and install all required packages specified in `requirements.txt`:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Environment Variables Configuration (`.env`)

The backend reads environment variables from a `.env` file located in the `backend/` directory.

### Create `.env` from the provided template:
- **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
- **macOS / Linux:**
  ```bash
  cp .env.example .env
  ```

### Explanation of `.env` Parameters:

| Variable | Recommended Dev Value | Description |
| :--- | :--- | :--- |
| `DJANGO_SETTINGS_MODULE` | `config.settings` | Points to the Django settings package. |
| `SECRET_KEY` | *(any secure random string)* | Used for cryptographic signing and session security. Never commit production keys. |
| `DEBUG` | `True` | Enables debug mode and descriptive errors in local development. Must be `False` in production. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,testserver` | Comma-separated list of hostnames allowed to access the backend. |
| `DATABASE_URL` | *(leave blank for SQLite)* | Leave empty to use local development `db.sqlite3`. Set to `postgresql://<user>:<password>@localhost:5432/<dbname>` for PostgreSQL. |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Whitelists frontend origins (Next.js) for CSRF validation during state-mutating requests (`POST`, `PATCH`, `DELETE`). |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed origins for Cross-Origin Resource Sharing. |
| `SESSION_COOKIE_AGE` | `28800` | Session lifetime in seconds (`28800` = 8 hours). |
| `SESSION_COOKIE_SECURE`| `False` | Set `False` for local HTTP development; set `True` in production for HTTPS. |
| `CSRF_COOKIE_SECURE` | `False` | Set `False` for local HTTP development; set `True` in production for HTTPS. |
| `ADMIN_URL_PATH` | `admin/` | Custom URL prefix for the restricted Django administration portal. |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 4. Database Setup & Initial Migration

Apply database migrations to create all database tables (custom user model, RBAC policies, supplier registry, product catalogue, evidence items, and audit trail):

```bash
python manage.py migrate
```

---

## 5. Provisioning Initial Users (Decision D-12)

Per architectural decision **D-12**, public self-registration is disabled. All user accounts are provisioned by an administrator.

### Create the First Platform Administrator:
Run the custom management command to create a Platform Admin account:

- **Interactive prompt (prompts for password securely):**
  ```bash
  python manage.py create_platform_admin --email admin@inchi.local
  ```
- **Non-interactive / Scripted (useful for automation):**
  - **Windows (PowerShell):**
    ```powershell
    $env:INITIAL_ADMIN_PASSWORD="AdminPass123!"; python manage.py create_platform_admin --email admin@inchi.local
    ```
  - **macOS / Linux:**
    ```bash
    INITIAL_ADMIN_PASSWORD="AdminPass123!" python manage.py create_platform_admin --email admin@inchi.local
    ```

### Seeded Credentials for Testing:
- **Platform Administrator:** `admin@inchi.local` / `AdminPass123!`
- **Commercial Analyst:** `analyst@inchi.local` / `AnalystPass123!`

---

## 6. Running the Development Server

Start the Django development server:
```bash
python manage.py runserver 0.0.0.0:8000
```

- **Backend Root:** `http://localhost:8000`
- **API Base:** `http://localhost:8000/api/v1/`
- **Django Admin:** `http://localhost:8000/admin/`

---

## 7. Running Automated Tests

Run the comprehensive unit and integration test suite to verify security, access control, and API contracts:

```bash
# Run all application tests (22+ tests)
python manage.py test apps

# Run specific app test suites:
python manage.py test apps.accounts    # M1: Auth, CSRF, RBAC isolation, session security
python manage.py test apps.registry    # M2 & M3: Suppliers, Products, Concurrency, Validations
```

---

## 8. API Architecture & Frontend Integration

The backend is configured for single-origin proxy integration with the Next.js frontend (`frontend/`):

1. **Single-Origin Proxy (`next.config.ts`):**
   The Next.js dev server on `http://localhost:3000` automatically proxies all `/api/:path*` requests to `http://localhost:8000/api/:path*`.
2. **CSRF Bootstrap:**
   Before authentication or mutating calls, frontend requests `GET /api/v1/auth/csrf/` to bootstrap the `csrftoken` cookie.
3. **Session Authentication:**
   `POST /api/v1/auth/login/` authenticates credentials and establishes an `HttpOnly` session cookie (`sessionid`).
4. **Standard Error Schema:**
   Every API error response follows the standard envelope:
   ```json
   {
     "code": "validation_error",
     "message": "Descriptive reason for failure",
     "field_errors": { "field_name": ["Specific validation message"] },
     "correlation_id": "uuid-v4-string"
   }
   ```
5. **DRF Pagination Envelope:**
   List endpoints return standard paginated structures:
   ```json
   {
     "count": 10,
     "next": null,
     "previous": null,
     "results": [ ... ]
   }
   ```

---

## 9. Codebase Structure

```
backend/
├── ai_matching/               # AI matching engine scaffolding (Alok Tiwari)
├── apps/
│   ├── accounts/              # M1: Custom User, RBAC policy.py, permissions, auth views
│   ├── audit/                 # M10: Immutable AuditEvent model & record_event service
│   ├── dashboard/             # M8: Summary metrics and dashboard aggregation
│   ├── demand/                # M5: Buyer requirements, procurement criteria & status gates
│   ├── matching/              # M6 & M7: Matching run orchestration & selectors
│   ├── opportunities/         # M9: Commercial pipeline & accepted match stages
│   ├── readiness/             # M4: China-readiness assessments
│   └── registry/              # M2 & M3: Supplier registry, product catalogue, evidence items
├── config/
│   ├── exceptions.py          # Central DRF exception handler & error envelope
│   ├── settings.py            # Main Django configuration
│   ├── urls.py                # Top-level API routing & mounting
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```
