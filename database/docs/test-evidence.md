# Database Test Evidence

## Environment

- Date: 21 November 2026
- Database: PostgreSQL 17.11
- Container: `inchi_postgres`
- Host port: `5434`
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

## Week 2 — Supplier and product registry

Date: 21 November 2026

### Migration and test environment

- Migrations: `registry.0001_initial`, `registry.0002`, `registry.0003`
- Database: PostgreSQL 17 pgvector
- Container: `inchi_postgres`
- Host port: `5434`
- Database migration consistency: passed
- PostgreSQL migration execution: passed
- PostgreSQL database test suite: 14 tests passed
- Live supplier count: 3
- Live product count: 6

The dedicated InChi container no longer uses SQLite or the occupied
shared `5433` port.

### Week 2 automated coverage

The tests in `apps/registry/tests.py` verify:

- A product is linked to an existing supplier.
- Declared capacity must be positive.
- MOQ must be positive.
- Lead time must be positive.
- Priced products require currency/basis information.
- Priced products accept explicit currency/basis information.
- GSTIN and IEC supplied values are syntax-validated.
- Supplier and product seed data is repeatable.

### Week 2 synthetic counts

| Table | Count |
|---|---:|
| `supplier` | 3 |
| `product` | 6 |

## Week 3 — Readiness and evidence

Date: 21 November 2026

### Migration and PostgreSQL validation

- Migration: `readiness.0001_initial`
- PostgreSQL append-only migration: `readiness.0002`
- Migration consistency: passed
- PostgreSQL migration execution: passed
- Database test suite: 22 tests passed

### Week 3 automated coverage

- Assessment products and questionnaire version `2.2` are retained.
- Questionnaire responses are unique per assessment and criterion.
- Document receipt defaults to Document Received Unverified.
- Expired evidence remains visible.
- Discrepancy creates a criterion-level blocker.
- Not Applicable requires a reason.
- Audit events retain previous and new values.
- PostgreSQL rejects updates to readiness audit rows.

### Live PostgreSQL Week 3 counts

| Table | Count |
|---|---:|
| `readiness_assessment` | 3 |
| `readiness_response` | 45 |
| `readiness_evidence` | 3 |
| `readiness_blocker` | 2 |
| `readiness_submission_snapshot` | 3 |

## Week 4 — Buyer demand readiness gate

Date: 21 November 2026

### Migration and PostgreSQL validation

- Migration: `demand.0003_alter_buyerrequirement_completeness_status_and_more`
- PostgreSQL immutability migration: `demand.0004_requirement_version_append_only`
- Migration consistency: passed
- PostgreSQL migration execution: passed
- Full database test suite: 28 tests passed

### Week 4 automated coverage

- Approved requirement statuses are enforced in the Django model.
- Quantity requires both value and unit.
- Priced requirements require currency and price basis.
- Invalid price ranges are rejected.
- Invalid delivery windows are rejected.
- A complete requirement can transition to Ready for Matching.
- Missing internal owner blocks Ready for Matching.
- Closing a requirement disables matching readiness.
- Buyer requirement versions cannot be updated or deleted.
- Synthetic buyer-demand records are repeatable.

### Live PostgreSQL Week 4 counts

| Table | Count |
|---|---:|
| `buyer_requirement` | 20 |
| `buyer_requirement_version` | 20 |
| `requirement_quantity` | 20 |
| `requirement_commercial_terms` | 20 |
| `requirement_delivery` | 20 |
| `matching_readiness_blocker` | 15 |
