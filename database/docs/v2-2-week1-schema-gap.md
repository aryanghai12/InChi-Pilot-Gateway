# Baseline v2.2 — Week 1 Database Gap Analysis

Status: Week 1 database analysis  
Implementation authority: `InChi_China_Readiness_Implementation_Baseline_v2.2.pdf`

This document records the database work Vishal must complete for the supplier,
product, readiness, evidence, demand, matching and audit portions of the MVP.
It does not change backend, frontend or AI implementation files.

## 1. Current database coverage

| Baseline area | Current database coverage | Gap |
|---|---|---|
| Buyer organisation | Buyer organisation name and buyer reference are stored directly on `BuyerRequirement` | Buyer organisation can remain a minimal direct field; no buyer profile is required |
| Buyer requirement | Stable requirement identity, version, quantity, commercial terms, delivery, criteria and blockers exist | Missing final readiness gate tests and controlled status enforcement |
| Supplier | No complete supplier entity mapping | `SUP-001` to `SUP-012` must be modelled |
| Product | No complete product entity mapping | `PRD-001` to `PRD-017` must be modelled |
| Assessment | No assessment entity or questionnaire response storage | `ASM-001` to `ASM-006` and CR-01 to CR-18 must be modelled |
| Evidence | No evidence entity | `EVD-001` to `EVD-009` must be modelled |
| Match run | No database model | `MCH-001` to `MCH-007` must be modelled |
| Disposition | No database model | `DSP-001` and `DSP-002` must be modelled |
| Audit event | Actor/time fields exist on some records, but no general audit entity is implemented | `AUD-001` and immutable material-action history must be modelled |

## 2. Supplier database model

Create a supplier entity covering:

| Field ID | Database field | Required database rule |
|---|---|---|
| SUP-001 | `supplier_id` | Immutable UUID or system-generated string |
| SUP-002 | `legal_name` | Required |
| SUP-003 | `trading_name` | Optional |
| SUP-004 | `supplier_type` | Controlled enum |
| SUP-005 | `registered_address` | Required |
| SUP-006 | `state_country` | Required; India in the MVP |
| SUP-007 | `gstin` | Conditional; syntax validation only |
| SUP-008 | `iec` | Conditional; required for export readiness where export is proposed |
| SUP-009 | `primary_contact` | Required |
| SUP-010 | `contact_email` | Required and valid email format |
| SUP-011 | `export_markets` | Optional list |
| SUP-012 | `record_status` | Controlled: Draft, Active or Archived |

### Supplier constraints

- Supplier IDs must be immutable.
- Product records must always reference an existing supplier.
- Email format must be validated.
- GSTIN must never be interpreted as legal verification.
- Supplier status must be separate from readiness outcome.

## 3. Product database model

Create a product entity covering:

| Field ID | Database field | Required database rule |
|---|---|---|
| PRD-001 | `product_id` | Immutable UUID or system-generated string |
| PRD-002 | `supplier_id` | Required foreign key with protected supplier deletion |
| PRD-003 | `product_name_en` | Required |
| PRD-004 | `product_name_zh_draft` | Optional; human-review status must remain separate |
| PRD-005 | `category_code` | Required controlled category |
| PRD-006 | `hs_code_declared` | Optional supplier declaration, not customs confirmation |
| PRD-007 | `model_grade` | Conditional |
| PRD-008 | `technical_specification` | Required |
| PRD-009 | `unit_of_measure` | Required controlled unit |
| PRD-010 | `declared_capacity` | Required positive decimal |
| PRD-011 | `capacity_period` | Required: Week, Month or Quarter |
| PRD-012 | `moq` | Required positive decimal |
| PRD-013 | `lead_time_days` | Required positive integer |
| PRD-014 | `price_amount` | Optional positive decimal |
| PRD-015 | `price_currency_basis` | Conditional when price is supplied |
| PRD-016 | `origin_country` | Required; India for the pilot |
| PRD-017 | `packaging_description` | Required |

### Product constraints

- A product cannot exist without a supplier.
- Capacity must be greater than zero.
- MOQ must be greater than zero.
- Lead time must be greater than zero.
- Currency and price basis must be explicit when price exists.
- Currency, unit and basis incompatibilities must remain `Unknown`, not guessed.

## 4. Readiness and evidence models

Create:

- An immutable assessment entity for `ASM-001` to `ASM-006`.
- A questionnaire response entity for CR-01 to CR-18.
- An evidence entity for `EVD-001` to `EVD-009`.
- A submission snapshot that preserves questionnaire version `2.2`.
- A criterion-level blocking-item entity.

Assessment fields must include:

- Assessment ID
- Supplier ID
- One or more product IDs
- Questionnaire version
- Workflow state
- Reviewer readiness outcome

Evidence fields must include:

- Evidence ID
- Criterion ID
- Evidence type
- Evidence condition
- Issuer/source
- Reference number
- Issue and expiry dates
- Approved storage reference
- Reviewer notes

Evidence conditions are categorical and nonordinal:

- `NOT_PROVIDED`
- `SELF_DECLARED`
- `DOCUMENT_RECEIVED_UNVERIFIED`
- `OFFICIAL_SOURCE_CHECKED`
- `THIRD_PARTY_REPORT_RECEIVED_UNVERIFIED`
- `THIRD_PARTY_REPORT_SOURCE_CHECKED`
- `EXPIRED`
- `DISCREPANCY`
- `NOT_APPLICABLE`

## 5. Workflow structures

### Assessment workflow

The database must represent and preserve these transitions:

- Draft -> Submitted
- Submitted -> Under Review
- Under Review -> Information Required
- Under Review -> Review Complete
- Information Required -> Submitted
- Review Complete -> Draft only through a new reassessment version
- Draft -> Archived

Readiness outcomes remain separate from workflow state:

- `READY_FOR_MATCHING`
- `INFORMATION_REQUIRED`
- `NOT_CURRENTLY_ELIGIBLE`

### Buyer requirement workflow

- Draft -> Ready for Matching
- Ready for Matching -> Draft after material edit
- Ready for Matching -> Closed
- Material edits create a new requirement version

The database must not expose `In Review` or `On Hold` as MVP requirement statuses.

## 6. Match and disposition structures

Database models must preserve:

### Match run

- Exact buyer requirement version
- Exact supplier/product snapshot
- Assessment version
- Rules/configuration version
- UTC execution timestamp
- Eligibility result
- Mandatory criterion findings
- Preference findings
- Deterministic explanation
- Missing information
- Unit incompatibilities
- Evidence limitations

### Disposition

- `ACCEPT_FOR_FOLLOW_UP`
- `HOLD_FOR_INFORMATION`
- `REJECT`
- Required human reason
- Requirement-specific association
- Actor and UTC timestamp
- Superseded status after changed input versions

## 7. Audit and immutability

Every material create, update, transition, match or disposition must create an
audit event with:

- Immutable audit event ID
- Actor
- UTC timestamp
- Action
- Object type
- Object ID and version
- Change summary
- Previous value
- New value
- Reason where required

The audit implementation must prevent normal application functions from
editing or deleting audit records.

## 8. Controlled reference values

The database must store approved codes rather than free text for:

- Supplier type
- Category
- Unit of measure
- Capacity period
- Requirement status
- Assessment workflow state
- Readiness outcome
- Evidence condition
- Evidence type
- Eligibility result
- Disposition

## 9. Database readiness gate

A buyer requirement can become `READY_FOR_MATCHING` only when:

- A buyer organisation or controlled buyer reference exists.
- Product category exists.
- Required specification exists.
- Quantity and quantity unit exist.
- Delivery destination exists.
- At least one mandatory criterion exists.
- Internal owner exists.
- If price is supplied:
  - Currency exists.
  - Unit exists.
  - Price basis exists.
  - Minimum price is not greater than maximum price.
- No active blocker prevents readiness.

Unknown, Not Provided, Expired and Discrepancy values must remain visible and
must not be silently converted to pass or verified states.

## 10. Minimum Week 1 deliverables

Week 1 database work should produce:

1. A supplier field mapping for `SUP-001` to `SUP-012`.
2. A product field mapping for `PRD-001` to `PRD-017`.
3. A readiness field mapping for `ASM-001` to `ASM-006`.
4. A CR-01 to CR-18 questionnaire storage mapping.
5. An evidence mapping for `EVD-001` to `EVD-009`.
6. Match and disposition entity requirements.
7. Audit and immutability requirements.
8. Controlled-value lists and database constraints.
9. An implementation order for Weeks 2 to 4.

These are database-only deliverables. Backend APIs, user interfaces, role
middleware and AI matching logic remain outside Vishal's responsibility.
