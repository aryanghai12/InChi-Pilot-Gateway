# Database Schema Summary

## Scope

The database package provides the buyer-demand schema defined by the
`BUY-001` to `BUY-032` field dictionary. Django migrations are authoritative.
PostgreSQL 17 with the pgvector image is the reference database.

## Tables

| Table | Purpose |
|---|---|
| `demand_reference_value` | Versioned markets, categories, units, currencies, price bases and evidence types |
| `matching_configuration` | Versioned matching configuration with approval state |
| `buyer_requirement` | Stable buyer-demand identity and current workflow/readiness state |
| `buyer_requirement_version` | Immutable material snapshot for traceability |
| `requirement_specification` | Versioned structured product attributes |
| `requirement_quantity` | Quantity, unit and order frequency |
| `requirement_commercial_terms` | Price range, currency and price basis |
| `requirement_delivery` | Destination, delivery dates and lead time |
| `requirement_evidence_criterion` | Required evidence and mandatory/preferred classification |
| `requirement_eligibility_criterion` | Mandatory hard matching criteria |
| `requirement_preference` | Non-mandatory preference criteria |
| `matching_readiness_blocker` | Field-specific reasons matching is blocked |

## Relationships

- One `buyer_requirement` has many `buyer_requirement_version` rows.
- Each version has at most one specification, quantity, commercial-term and
  delivery record.
- Each version can have many evidence, eligibility, preference and readiness
  blocker rows.
- Historical versions use `PROTECT` relationships and must not be deleted or
  overwritten.
- Matching services must reference the exact requirement version and
  configuration version used.

## Migration history

| Migration | Contents |
|---|---|
| `0001_initial` | Buyer requirement schema, constraints and indexes |
| `0002_matchingconfiguration_referencevalue` | Reference values and matching configuration |

## Synthetic data

The fixture at `../seed/synthetic_buyer_requirements.csv` contains 20
synthetic requirements. The `seed_demo` command also creates their related
version, quantity, commercial, delivery, evidence, eligibility, preference and
readiness-blocker records.
