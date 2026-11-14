# Database Test Evidence

## Environment

- Date: 12 November 2026
- Database: PostgreSQL 17.11
- Container: `inchi_postgres`
- Host port: `5433`
- Fixture: `seed/synthetic_buyer_requirements.csv`

## Checks

| Command/check | Result |
|---|---|
| `python -m django check` | Passed |
| `python -m django makemigrations --check --dry-run` | Passed; no changes detected |
| `python -m django migrate` | Passed |
| `python -m django seed_demo` | Passed; 20 requirements created |
| `python -m django test apps.demand.tests` | Passed; 5 tests |
| PostgreSQL backup and restore | Passed |

## Automated coverage

The tests in `apps/demand/tests/test_demand.py` verify:

- The CSV-backed seed creates 20 requirements.
- Re-running the seed does not duplicate requirements or versions.
- Requirement version numbers are unique per requirement.
- Invalid price ranges are rejected.
- Invalid delivery windows are rejected.
- Negative quantities are rejected.

## PostgreSQL seed counts

| Table | Count |
|---|---:|
| `buyer_requirement` | 20 |
| `buyer_requirement_version` | 20 |
| `requirement_quantity` | 20 |
| `requirement_commercial_terms` | 20 |
| `requirement_delivery` | 20 |
| `matching_readiness_blocker` | 15 |

## Remaining validation

The backend integration team must run the full application test suite after
copying this package into the shared project and wiring its APIs to these
models.
