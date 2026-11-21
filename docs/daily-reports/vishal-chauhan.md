# Daily reports — Vishal Chauhan

Data and Platform Services Engineer 


### Week 1 — Definition, architecture and delivery skeleton

- Reviewed the Buyer Requirement Field Dictionary v1.2.
- Analysed the InChi Pilot Build Sequence Timeline and identified database
  responsibilities for Weeks 1 to 4.
- Analysed the China Readiness Implementation Baseline v2.2 and confirmed it
  is the implementation authority for the MVP.
- Prepared the buyer-requirement field mapping and the initial buyer-demand
  schema mapping.
- Mapped the buyer-demand field groups, including buyer organisation,
  requirement version, specification, quantity, commercial terms, delivery,
  mandatory criteria, preference criteria and required evidence.
- Reviewed supplier fields SUP-001 to SUP-012 and identified that the shared
  database package still requires supplier identity, status, business
  identifiers, contact details and export-market storage.
- Reviewed product fields PRD-001 to PRD-017 and identified the database
  requirements for supplier linkage, category, technical specification,
  capacity, MOQ, lead time, commercial terms, origin and packaging.
- Reviewed readiness assessment fields ASM-001 to ASM-006 and questionnaire
  questions CR-01 to CR-18 for the next database implementation phase.
- Reviewed evidence fields EVD-001 to EVD-009 and recorded the controlled
  evidence conditions used by the baseline: Not Provided, Self-Declared,
  Document Received Unverified, Official Source Checked,
  Third-Party Report Received Unverified,
  Third-Party Report Source Checked, Expired, Discrepancy and
  Not Applicable.
- Reviewed match fields MCH-001 to MCH-007 and disposition fields DSP-001
  and DSP-002 to document requirements for immutable match runs,
  criterion findings, explanations and human disposition.
- Reviewed audit field AUD-001 and the required audit event information:
  actor, UTC timestamp, action, affected object, object version and change
  summary.
- Documented the MVP-controlled values for supplier types, category codes,
  units of measure, readiness outcomes, eligibility results and dispositions.
- Documented the approved buyer-requirement statuses:
  Draft, Ready for Matching and Closed.
- Documented the database versioning approach: immutable requirement,
  assessment and match-run versions must remain unchanged after material
  edits or completed executions.
- Documented the readiness gate fields and blocker conditions for buyer
  organisation, target category, specification, quantity, unit, delivery
  location, mandatory criteria and conditional price information.
- Documented the data-dictionary rules and open data decisions for owner,
  schema, migration and integration boundaries.
- Confirmed that database work remains separate from backend APIs,
  frontend screens and AI matching implementation.
- Completed a database-only Week 1 gap analysis against Baseline v2.2.
- Mapped missing supplier fields SUP-001 to SUP-012 and product fields
  PRD-001 to PRD-017 to proposed database entities and constraints.
- Mapped readiness fields ASM-001 to ASM-006, questionnaire CR-01 to CR-18,
  evidence fields EVD-001 to EVD-009 and audit field AUD-001.
- Mapped match fields MCH-001 to MCH-007 and disposition fields DSP-001 to
  DSP-002 for later immutable database implementation.
- Added `../../database/docs/v2-2-week1-schema-gap.md` with the Week 1 field
  coverage, missing models, workflow structures, controlled values and
  implementation order.
- Updated the buyer-requirement mapping to remove buyer verification from the
  MVP scope and retain only Draft, Ready for Matching and Closed statuses.

### Week 2 — Authenticated supplier-product vertical slice

- Created the centralized PostgreSQL database connection configuration.
- Created the buyer-requirement Django models.
- Added initial migrations, database constraints and indexes.
- Added requirement versioning, quantity, pricing, delivery and criteria tables.
- Added the initial synthetic seed-data structure.
- Added a separate database registry app for supplier and product records.
- Implemented SUP-001 to SUP-012 supplier fields in the supplier model.
- Implemented PRD-001 to PRD-017 product fields in the product model.
- Added a mandatory protected supplier-to-product foreign-key relationship.
- Added controlled choices for supplier type, category, unit of measure,
  capacity period and supplier record status.
- Added database constraints for positive capacity, MOQ and lead time.
- Added GSTIN and IEC syntax validation for conditional supplier identifiers.
- Updated the approved product categories to Agriculture and Food,
  Minerals and Metals, Marine Products, Chemicals and Petroleum Products.
- Updated supplier/product category choices and synthetic product records.
- Generated migration `registry.0003_alter_product_category_code`.
- Started a dedicated PostgreSQL 17 pgvector container on host port `5434`.
- Applied all database migrations successfully against PostgreSQL.
- Ran 14 supplier, product and buyer-demand database tests successfully
  against PostgreSQL.
- Verified live PostgreSQL counts: 3 suppliers and 6 products.
- Added conditional database validation requiring currency/basis text for a
  priced product.
- Added migration `registry.0001_initial` for the supplier and product tables.
- Added repeatable CSV seed fixtures for three suppliers and six products.
- Updated `seed_demo` so it seeds and updates supplier and product records
  without duplication.
- Added database tests for supplier linkage, positive values and priced
  products.
- Ran the database migration consistency check and migration validation.
- Ran 13 database tests successfully using the SQLite offline test fallback.
- Added `supplier-product-schema-mapping.md` and updated database test evidence.

### Week 3 — Supplier registry and profile quality

- Added the 20-row synthetic CSV test fixture and repeatable seed command.
- Added database tests for validation, constraints and seed repeatability.
- Validated migrations, seed data and tests on PostgreSQL.
- Verified PostgreSQL backup and restore.
- Copied the reviewed database package into the shared project database folder.
- Added a separate readiness database app for assessment, questionnaire
  response, evidence, blocker and audit data.
- Implemented immutable assessment versions for supplier and product
  readiness records.
- Added questionnaire version `2.2` and supplier-product assessment links.
- Added CR-01 to CR-18 response storage with Unknown and Not Applicable states.
- Added evidence records for EVD-001 to EVD-009.
- Added all approved categorical evidence conditions, with Document Received
  Unverified as the document default.
- Added assessment workflow states and readiness outcomes.
- Added criterion-level readiness blockers for missing, expired and
  discrepant information.
- Added immutable submission snapshots.
- Added readiness audit events with actor, UTC timestamp, object version,
  previous value, new value and change summary.
- Added PostgreSQL triggers preventing update or delete operations on
  readiness audit events.
- Generated and applied `readiness.0001_initial` and
  `readiness.0002_readiness_audit_append_only`.
- Added repeatable synthetic readiness records: 3 assessments,
  45 questionnaire responses, 3 evidence records and 3 submission snapshots.
- Ran 22 database tests successfully against PostgreSQL.

### Week 4 — Buyer demand and rule approval gate

- Completed the database implementation for buyer organisations and
  versioned buyer requirements.
- Added the approved buyer-requirement statuses: Draft,
  Ready for Matching and Closed.
- Mapped `IN_REVIEW` and incomplete legacy statuses to the MVP Draft state.
- Added uppercase controlled completeness values: Incomplete and Complete.
- Added database constraints linking Ready for Matching with
  `matching_ready=True`.
- Implemented the ready-for-matching gate for buyer organisation, category,
  specification, quantity, unit, delivery location, mandatory criteria,
  internal owner and conditional price details.
- Added active-field readiness blockers with field ID, reason code and detail.
- Added conditional currency and price-basis constraints.
- Added quantity-unit and positive-quantity constraints.
- Added a Close transition that disables matching readiness.
- Generated migration `demand.0003_alter_buyerrequirement_completeness_status_and_more`.
- Added PostgreSQL append-only protection for buyer requirement versions.
- Generated migration `demand.0004_requirement_version_append_only`.
- Normalized legacy buyer-demand categories to the five approved categories.
- Added Week 4 tests for quantity/unit, price terms, readiness gate,
  closing requirements and immutable requirement versions.
- Ran 28 database tests successfully against PostgreSQL.
- Verified live PostgreSQL counts of 20 requirements and 20 requirement
  versions.
- Added `week4-ready-for-matching-gate.md` to the database documentation.
- Added repeatable synthetic role-account seed contract for
  `platform.admin@example.com`, `commercial.analyst@example.com` and
  `reviewer@example.com`.
- Added `DEMO_USER_PASSWORD` support to the seed command and environment
  template. Password values are read from local environment configuration
  only and are never written to source files or reports.
