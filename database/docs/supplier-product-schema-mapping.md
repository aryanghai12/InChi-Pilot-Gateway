# Supplier and Product Schema Mapping

Status: Week 2 database implementation

Implementation authority: Baseline v2.2, sections 5 and 12.

## Supplier entity

Database table: `supplier`

| Baseline field | Database field | Database rule |
|---|---|---|
| SUP-001 | `supplier_id` | Immutable UUID primary key |
| SUP-002 | `legal_name` | Required text |
| SUP-003 | `trading_name` | Optional text |
| SUP-004 | `supplier_type` | Controlled: Manufacturer, Trader, Distributor, Agent or Hybrid |
| SUP-005 | `registered_address` | Required text |
| SUP-006 | `state_country` | Required text; India for the pilot |
| SUP-007 | `gstin` | Optional text; syntax validation only |
| SUP-008 | `iec` | Optional text; export-readiness information |
| SUP-009 | `primary_contact` | Required text |
| SUP-010 | `contact_email` | Required valid email |
| SUP-011 | `export_markets` | Optional structured JSON list |
| SUP-012 | `record_status` | Controlled: Draft, Active or Archived |

## Product entity

Database table: `product`

| Baseline field | Database field | Database rule |
|---|---|---|
| PRD-001 | `product_id` | Immutable UUID primary key |
| PRD-002 | `supplier_id` | Required supplier foreign key |
| PRD-003 | `product_name_en` | Required text |
| PRD-004 | `product_name_zh_draft` | Optional text; no certification status |
| PRD-005 | `category_code` | Controlled MVP category |
| PRD-006 | `hs_code_declared` | Optional supplier declaration |
| PRD-007 | `model_grade` | Optional text |
| PRD-008 | `technical_specification` | Required text |
| PRD-009 | `unit_of_measure` | Controlled MVP unit |
| PRD-010 | `declared_capacity` | Positive decimal |
| PRD-011 | `capacity_period` | Week, Month or Quarter |
| PRD-012 | `moq` | Positive decimal |
| PRD-013 | `lead_time_days` | Positive integer |
| PRD-014 | `price_amount` | Optional positive decimal |
| PRD-015 | `price_currency_basis` | Required when price is supplied |
| PRD-016 | `origin_country` | India for the pilot |
| PRD-017 | `packaging_description` | Required text |

## Database constraints

- A product cannot exist without a supplier.
- Supplier deletion is protected when a product references the supplier.
- Declared capacity must be greater than zero.
- MOQ must be greater than zero.
- Lead time must be at least one day.
- A priced product must have explicit currency and basis information.
- GSTIN and IEC fields use syntax validation when supplied.
- HS code remains a supplier declaration, not customs confirmation.
- A supplier status is separate from readiness outcome.

## Controlled values

- Supplier types: `MANUFACTURER`, `TRADER`, `DISTRIBUTOR`, `AGENT`, `HYBRID`.
- Category codes: `AGRICULTURE_FOOD`, `MINERALS_METALS`, `MARINE_PRODUCTS`,
  `CHEMICALS`, `PETROLEUM_PRODUCTS`.
- Units: `PIECE`, `KILOGRAM`, `METRIC_TONNE`, `LITRE`, `CARTON`.
- Capacity periods: `WEEK`, `MONTH`, `QUARTER`.
- Supplier statuses: `DRAFT`, `ACTIVE`, `ARCHIVED`.

## Synthetic dataset

The repeatable seed creates three suppliers and six products, with two
products for each supplier. The seed is idempotent by supplier ID and
product ID.
