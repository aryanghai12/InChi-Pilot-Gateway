# InChi Pilot Gateway — Centralized PostgreSQL Database Configuration

This repository provides a centralized, reusable PostgreSQL database connection configuration using Docker Compose and Django. It is built for the **InChi Pilot Gateway** data platform to provide all backend engineers with a consistent, isolated, and persistent local database environment.

---

## 1. Architecture & Technology Stack

- **Backend Framework:** Python 3.12+ / Django 5.2 LTS
- **Database:** PostgreSQL 17 (Official image with pgvector support)
- **Database Driver:** `psycopg 3` (with binary wheels and pool support)
- **Containerization:** Docker Compose
- **Default Database Port:** `5432`
- **Volume Persistence:** Named Docker volume `inchi_postgres_data`

---

## 2. Project Directory Structure

```text
config/
    __init__.py          # Package initialization
    database.py          # Centralized, environment-driven database configuration module
    settings.py          # Django settings integrating the centralized database config
docker-compose.yml       # Docker Compose definition for PostgreSQL with healthcheck
.env                     # Local environment credentials (git-ignored, never committed)
.env.example             # Template containing placeholder credentials and documentation
requirements.txt         # Core Python dependencies (Django, python-dotenv, psycopg 3)
.gitignore               # Git ignore rules protecting .env and local caches
README.md                # Setup guide, container lifecycle, and architectural notes
```

---

## 3. Required Environment Variables

All database credentials and settings are read from environment variables. Do **not** hardcode credentials anywhere in source code.

| Variable | Description | Default Local Value |
|---|---|---|
| `DB_NAME` | PostgreSQL database name | `inchi_db` |
| `DB_USER` | PostgreSQL user | `inchi_user` |
| `DB_PASSWORD` | PostgreSQL password | `change_me` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_CONN_MAX_AGE` | Connection reuse duration in seconds | `60` |
| `DB_CONN_HEALTH_CHECKS` | Validate connection liveness before reuse | `True` |
| `DB_POOL_ENABLED` | Enable client-side connection pooling | `False` |

---

## 4. Prerequisites

1. **Docker Desktop** installed and running on your machine.
2. **Python 3.12+** installed.

---

## 5. Quickstart: Step-by-Step Developer Setup

### Step 1: Clone and Prepare Environment File
Copy the example environment template to create your local `.env`:
```powershell
cp .env.example .env
```
*(Verify that the database parameters match your local development environment).*

### Step 2: Install Python Dependencies
Create a virtual environment and install the required dependencies:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Start PostgreSQL with Docker Compose
Start the PostgreSQL container in detached mode:
```powershell
docker compose up -d db
```

### Step 4: Verify Container Health
Verify that the PostgreSQL container is running and healthy:
```powershell
docker compose ps
```
The status should indicate `Up` with `(healthy)`.

### Step 5: Verify Django Database Connection
Run a quick connectivity check from Python:
```powershell
python -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from django.db import connection; connection.ensure_connection(); print('>>> Successfully connected to PostgreSQL!')"
```

### Step 6: Run Migrations
Apply Django migrations to the PostgreSQL database:
```powershell
python -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from django.core.management import call_command; call_command('migrate')"
```

---

## 6. Docker Container Management & Lifecycle

- **Start Database:**
  ```powershell
  docker compose up -d db
  ```
- **Stop Database (without losing data):**
  ```powershell
  docker compose stop db
  ```
- **Restart Database:**
  ```powershell
  docker compose restart db
  ```
- **View Container Logs:**
  ```powershell
  docker compose logs -f db
  ```
- **Tear Down Containers (data volume preserved):**
  ```powershell
  docker compose down
  ```
- **Inspect Health Check Status:**
  ```powershell
  docker inspect --format='{{json .State.Health.Status}}' inchi_postgres
  ```

---

## 7. Persistent Storage & Volume Safety

Database files are stored in a dedicated named Docker volume:
```yaml
volumes:
  inchi_postgres_data:
    name: inchi_postgres_data
```
- Stopping (`docker compose stop`), restarting (`docker compose restart`), or shutting down (`docker compose down`) the container **preserves all database tables and records**.
- **Important:** Never run `docker compose down -v` unless you explicitly intend to destroy all local database data.

---

## 8. Connection Reuse (`CONN_MAX_AGE`) vs Connection Pooling

### Connection Reuse (`CONN_MAX_AGE = 60`)
- **How it works:** By default, Django opens and closes a new database socket for every incoming HTTP request. Setting `CONN_MAX_AGE = 60` keeps the connection open for up to 60 seconds per thread/worker.
- **Benefit:** Dramatically reduces TCP handshake, TLS negotiation, and PostgreSQL authentication overhead under request traffic.
- **Health Checks:** With `DB_CONN_HEALTH_CHECKS=True` (Django 4.1+), Django pings the socket before reusing it, gracefully reconnecting if the database container was restarted.

### Dedicated Connection Pooling (`psycopg_pool` vs `PgBouncer`)
- **`CONN_MAX_AGE` vs Connection Pooling:** `CONN_MAX_AGE` maintains persistent connections per worker thread, but does not share connections across concurrent threads or worker processes.
- **Client-Side Pooling (`psycopg_pool`):** Supported natively in Django 5.1+ via `OPTIONS: {"pool": True}`. If your workload requires sharing a pool of connections across threads within a process, enable `DB_POOL_ENABLED=True` in your `.env`.
- **Server-Side Pooling (`PgBouncer`):** For massive multi-worker deployments (hundreds of worker processes multiplexed into a small database pool), PgBouncer can be placed in front of PostgreSQL. For local development and pilot workloads, `CONN_MAX_AGE=60` with native `psycopg_pool` provides optimal performance without additional infrastructure.

---

## 9. Security Guidelines for Database Credentials

1. **Never Commit Secrets:** `.env` is excluded in `.gitignore`. Never use `git add -f` to force-add `.env`.
2. **Commit Only Templates:** All configuration additions must update `.env.example` with sanitized placeholder values only.
3. **Secure Sharing:** Production and staging credentials must be distributed via encrypted team password managers or deployment secret managers, never via git, email, or chat channels.

