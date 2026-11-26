# Week 6 — Database Index Review

Date: 26 November 2026

## Review outcome

The existing models already covered most lookup fields. After PostgreSQL
became available, representative recent-first list and audit-history queries
were run with `EXPLAIN (ANALYZE, BUFFERS)`. Added composite indexes for the
common filter-plus-order patterns:

- Supplier status and most-recent update.
- Product category and unit, then most-recent update.
- Buyer requirement status and matching readiness, then most-recent update.
- Assessment workflow state, then most-recent update.
- Audit object type and ID, then most-recent event.

These are workload-shaped indexes, not a claim that the currently small demo
dataset has measurable latency problems. The dashboard app has no reporting
queries yet; confirm these candidates against the final dashboard SQL and
representative-volume data before treating them as production performance
evidence.

## Existing model indexes

| Area | Indexed fields | Expected lookup |
|---|---|---|
| Suppliers | `legal_name`; `supplier_type, record_status`; `updated_at` descending | Search/list, type/status filtering and recent updates |
| Products | `supplier, category_code`; `category_code, unit_of_measure`; `supplier, updated_at` descending | Supplier catalogue, category/unit filtering and recent supplier products |
| Buyer requirements | `requirement_status`; `completeness_status`; `matching_ready`; `owner_user`; `target_market`; `product_category_id`; `updated_at` descending | Status, owner, market, category, readiness and recent-update filters |
| Requirement versions | `requirement, version`; `created_at` descending | Requirement history and recent version lookup |
| Readiness assessments | `supplier, workflow_state`; `workflow_state, readiness_outcome`; `updated_at` descending | Supplier assessment history and review/outcome filtering |
| Questionnaire responses | `assessment, criterion_id`; `response_state` | Assessment detail and response-state filtering |
| Evidence | `assessment, criterion_id`; `evidence_condition`; `expiry_date` | Assessment evidence, condition and expiration queries |
| Readiness blockers | `assessment, active` | Active blockers for an assessment |
| Audit events | `object_type, object_id`; `occurred_at` descending | Object history and recent audit events |

### Week 6 composite indexes added

| Model/table | Index | Intended query shape |
|---|---|---|
| `Supplier` / `supplier` | `record_status, updated_at DESC` | Status-filtered supplier list ordered newest first |
| `Product` / `product` | `category_code, unit_of_measure, updated_at DESC` | Category/unit-filtered product list ordered newest first |
| `BuyerRequirement` / `buyer_requirement` | `requirement_status, matching_ready, updated_at DESC` | Buyer readiness queue ordered newest first |
| `ReadinessAssessment` / `readiness_assessment` | `workflow_state, updated_at DESC` | Review queue ordered newest first |
| `ReadinessAuditEvent` / `readiness_audit_event` | `object_type, object_id, occurred_at DESC` | Recent audit history for an object |

Definitions are in:

- `apps/registry/models.py`
- `apps/demand/models.py`
- `apps/readiness/models.py`

PostgreSQL also creates indexes for primary keys, foreign keys and unique
constraints; these are not repeated in the table above.

## PostgreSQL plan validation

Migrations applied:

- `demand.0005_buyerrequirement_buyer_status_ready_upd_idx`
- `registry.0004_product_prod_cat_unit_upd_idx_and_more`
- `readiness.0003_readinessassessment_assess_state_updated_idx_and_more`

Representative queries were checked before and after the migration:

| Query shape | Before | After | Notes |
|---|---|---|---|
| Supplier status list | Sequential scan and sort | Sequential scan and sort | Only 3 supplier rows; planner correctly prefers scanning the tiny table |
| Product category/unit list | Existing category/unit index, then sort | Sequential scan and sort | Only 6 product rows; too small to prove an index benefit |
| Buyer readiness queue | Sequential scan and sort | Sequential scan and sort | Only 20 buyer requirement rows |
| Assessment review queue | Existing workflow index with bitmap scan, then sort | Sequential scan and sort | Only 3 assessment rows |
| Audit history by object | Existing object index, then sort | Composite audit index; no explicit sort | Query returned no matching sample object rows |

The observed execution times were sub-millisecond and varied with cache state;
they are not used as a performance claim. PostgreSQL connected to
`inchi_db` on host port `5434`.

## Workload evidence and limitations

- The database package has no dashboard reporting query module yet.
- The backend dashboard app currently contains only its app configuration,
  so there are no dashboard SQL or ORM queries to benchmark against this
  database package.
- The backend dashboard app has no reporting query definitions to benchmark
  yet.
- The available seed data is small; planner choices against a few dozen rows
  do not represent production-scale performance.

## Next validation before adding indexes

1. Agree on dashboard and audit queries with the backend/dashboard owner.
2. Record their filter, join and sort fields.
3. Run the exact queries on PostgreSQL with representative-volume synthetic
   data using `EXPLAIN (ANALYZE, BUFFERS)`.
4. Compare the plans with the existing indexes listed above.
5. Confirm or remove these candidate composite indexes using the actual
   dashboard query plans at representative data volumes.
6. Re-run the query plan and migration checks, then record before/after
   evidence.
