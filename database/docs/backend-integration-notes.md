# Backend Integration Notes

## Package location

The database package is currently developed in `database_backup_temp/`.
After review, copy the complete sanitized package into the shared
`InChi-Pilot-Gateway/database/` folder.

## Django integration

The backend should use the same Django app configuration:

```python
INSTALLED_APPS = [
    "apps.demand.apps.DemandConfig",
]
```

The backend must use the database package's PostgreSQL settings and the
existing environment variables:

```text
DB_NAME
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
DB_CONN_MAX_AGE
DB_CONN_HEALTH_CHECKS
DB_POOL_ENABLED
```

The current reference environment uses `DB_HOST=localhost` and
`DB_PORT=5433`.

## Backend responsibilities

The backend member owns APIs, serializers, permissions and workflow services.
Those services should:

1. Treat `BuyerRequirement.requirement_id` as immutable.
2. Create a new `BuyerRequirementVersion` for each material edit.
3. Never update or delete historical versions.
4. Keep completeness separate from workflow status.
5. Keep matching readiness separate from completeness.
6. Prevent matching when active readiness blockers exist.
7. Keep mandatory eligibility criteria separate from preferences.
8. Record the exact requirement and matching-configuration versions used by a
   future match run.
9. Enforce field-level access rules for commercial terms and notes.
10. Emit audit events without passwords, tokens or unnecessary personal data.

## Local setup

```powershell
cd database_backup_temp
python -m pip install -r requirements.txt
docker compose up -d db
python -m django migrate
python -m django seed_demo
python -m django test apps.demand.tests
```

Do not set `USE_SQLITE=True` for the shared/reference environment. PostgreSQL
is the required database.

## Data source

The reviewable synthetic fixture is
`seed/synthetic_buyer_requirements.csv`. It is synthetic and contains no real
buyer, supplier or personal data.
