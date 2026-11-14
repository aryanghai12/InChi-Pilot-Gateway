# Open Buyer-Requirement Data Decisions

Source: `InChi_Buyer_Requirement_Field_Dictionary_v1.2_Consolidated.xlsx`

These decisions are recorded as unresolved. Database implementation should
provide configuration points and approval state, not invent final values.

| ID | Decision | Database impact | Current guardrail | Decision owner |
|---|---|---|---|---|
| BUY-D01 | Buyer organisation: profile table or free text | `buyer_organisation_name` versus `buyer_organisation_id` | Keep both integration paths possible | BNCS / Backend |
| BUY-D02 | Buyer verification scope and authority | Verification fields and allowed states | Do not mark a buyer verified without an approved process | BNCS / Admin |
| BUY-D03 | Supported target markets | Market reference data and validation | Keep target market separate from delivery destination | BNCS / Commercial |
| BUY-D04 | Product taxonomy, goods, subcategories and HS codes | Category, goods and taxonomy tables | Seven category names are provisional; do not seed goods-level values | Data / Matching |
| BUY-D05 | Quantity units and conversions | Unit reference data and conversion rules | Require an approved unit; do not assume conversions | Data |
| BUY-D06 | Order-frequency vocabulary and annualisation | Frequency and interval fields | Store the stated frequency; do not infer annual totals | Commercial |
| BUY-D07 | Currencies, price basis, visibility and FX | Commercial terms and access policy | Do not compare unlike currencies or bases without approval | Commercial / Security |
| BUY-D08 | Delivery date convention and timezone | Delivery fields and validation | Store dates consistently in UTC policy; do not assume business days | Commercial |
| BUY-D09 | Evidence taxonomy and mandatory/preferred applicability | Evidence reference and classification tables | Do not invent document requirements | BNCS / Reviewer |
| BUY-D10 | Eligibility versus preference classification | Separate criteria entities and evaluation order | Mandatory filters precede preferences; unknown is not pass | BNCS / Matching |
| BUY-D11 | Scoring weights, normalisation and authority | Versioned matching configuration | No default weights or thresholds | BNCS / Matching |
| BUY-D12 | Minimum completeness and matching-readiness gate | Gate configuration and blocker records | Keep `matching_ready` blocked until approved | BNCS / Product |
| BUY-D13 | Requirement workflow states and transitions | Status reference data and transition rules | Do not invent final labels or transitions | Product / Backend |
| BUY-D14 | Versioning, audit and retention policy | Snapshot, audit and retention design | Preserve historical match inputs and material changes | Backend / Security |
| BUY-D15 | Permissions for identity, price, notes and evidence | Access metadata and field visibility | Apply least privilege; backend remains authority | BNCS / Security |

## Decision closure requirements

Each decision should be closed with:

- Decision value or approved alternative
- Approver
- Approval date
- Rationale
- Affected field IDs
- Affected configuration/schema version
- Migration impact, if any

Until closure, the database must support a draft or inactive state and must not
present provisional values as approved production behaviour.
