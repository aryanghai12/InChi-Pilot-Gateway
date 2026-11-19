#!/bin/sh
# InChi Pilot Gateway — Django container start-up (ARCHITECTURE.md §8).
#
# 1. Wait for PostgreSQL to accept connections (Compose also waits on the db
#    healthcheck; this covers restarts and slow first initialisation).
# 2. Apply migrations and collect admin static files.
# 3. Optionally create the first platform administrator through the existing
#    create_platform_admin command (TD-08), only when both INITIAL_ADMIN_EMAIL
#    and INITIAL_ADMIN_PASSWORD are set and no platform_admin exists yet.
# 4. Hand over to the CMD (gunicorn).
#
# Secrets are never echoed.
set -eu

log() { printf '[entrypoint] %s\n' "$*"; }

if [ -z "${DATABASE_URL:-}" ]; then
    log "DATABASE_URL is not set; refusing to start against the SQLite fallback in a container."
    exit 1
fi

log "Waiting for the database..."
python - <<'PY'
import os, sys, time
import django
from django.db import connection
from django.db.utils import OperationalError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

deadline = time.monotonic() + int(os.getenv("DB_WAIT_TIMEOUT_SECONDS", "60"))
while True:
    try:
        connection.ensure_connection()
        break
    except OperationalError:
        if time.monotonic() > deadline:
            print("[entrypoint] Database did not become available in time.", file=sys.stderr)
            sys.exit(1)
        time.sleep(2)
PY
log "Database is available."

log "Applying migrations..."
python manage.py migrate --noinput

log "Collecting static files..."
python manage.py collectstatic --noinput --verbosity 0

if [ -n "${INITIAL_ADMIN_EMAIL:-}" ] && [ -n "${INITIAL_ADMIN_PASSWORD:-}" ]; then
    if python - <<'PY'
import os, sys
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from apps.accounts.models import Role, User
sys.exit(0 if User.objects.filter(role=Role.PLATFORM_ADMIN).exists() else 1)
PY
    then
        log "A platform administrator already exists; skipping bootstrap."
    else
        log "Creating the initial platform administrator..."
        python manage.py create_platform_admin --email "$INITIAL_ADMIN_EMAIL"
    fi
else
    log "INITIAL_ADMIN_EMAIL/INITIAL_ADMIN_PASSWORD not set; skipping admin bootstrap."
fi

log "Starting: $*"
exec "$@"
