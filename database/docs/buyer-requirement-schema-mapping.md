# Buyer Requirement Schema Mapping

Status: Draft database contract  
Source: `InChi_Buyer_Requirement_Field_Dictionary_v1.2_Consolidated.xlsx`  
Scope: `BUY-001` to `BUY-032`

The source dictionary is a working document and is not approved for final
implementation. This mapping preserves the source field IDs and API/database
names while keeping open business decisions configurable.

## Proposed entities

| Entity | Purpose |
|---|---|
| `BuyerRequirement` | Stable identity, ownership, workflow and current-state pointer |
| `BuyerRequirementVersion` | Immutable snapshot of material requirement data |
| `RequirementSpecification` | Category-dependent structured specifications |
| `RequirementQuantity` | Quantity and order-frequency information |
| `RequirementCommercialTerms` | Price, currency and price-basis information |
| `RequirementDelivery` | Destination, delivery window and lead time |
| `RequirementEvidenceCriterion` | Required documents/certifications and classification |
| `RequirementEligibilityCriterion` | Mandatory hard criteria |
| `RequirementPreference` | Preferred and non-mandatory criteria |
| `MatchingReadinessBlocker` | Field-specific reasons matching is blocked |
| `RequirementAuditMetadata` | Creation and update actor/time metadata |

## Field mapping

| ID | API/DB name | Proposed entity.column | Type | Nullability | Database rule |
|---|---|---|---|---|---|
| BUY-001 | `requirement_id` | `BuyerRequirement.requirement_id` | UUID | Not null | Unique and immutable |
| BUY-002 | `buyer_organisation_name` | `BuyerRequirement.buyer_organisation_name` | String or future FK | Nullable | Keep buyer registry decision configurable |
| BUY-003 | `buyer_reference` | `BuyerRequirement.buyer_reference` | String | Nullable | Uniqueness policy remains open |
| BUY-004 | `owner_user_id` | `BuyerRequirement.owner_user_id` | UUID/FK | Nullable until approved | Must reference an active authorised user when supplied |
| BUY-005 | `target_market` | `BuyerRequirement.target_market` | Reference/code | Nullable until approved | Must remain separate from delivery location |
| BUY-006 | `product_category_id` | `BuyerRequirement.product_category_id` | UUID/FK | Nullable until approved | Do not load unapproved goods or HS-code values |
| BUY-007 | `requirement_title` | `BuyerRequirement.requirement_title` | String | Nullable | Does not replace structured fields |
| BUY-008 | `product_specifications` | `RequirementSpecification.attributes` | JSONB | Nullable | Store schema version and explicit unknown/not-supplied states |
| BUY-009 | `quantity_value` | `RequirementQuantity.quantity_value` | Decimal | Nullable | Must be greater than zero when supplied |
| BUY-010 | `quantity_unit` | `RequirementQuantity.quantity_unit` | Reference/code | Conditional | Required when quantity is supplied |
| BUY-011 | `order_frequency` | `RequirementQuantity.order_frequency` | Enum/config code | Nullable | Recurrence interval required for recurring demand |
| BUY-012 | `target_price_min` | `RequirementCommercialTerms.target_price_min` | Decimal | Nullable | Positive; cannot exceed maximum |
| BUY-013 | `target_price_max` | `RequirementCommercialTerms.target_price_max` | Decimal | Nullable | Positive; cannot be below minimum |
| BUY-014 | `currency_code` | `RequirementCommercialTerms.currency_code` | ISO code | Conditional | Required when either price bound is supplied |
| BUY-015 | `price_basis` | `RequirementCommercialTerms.price_basis` | Reference/code | Conditional | Required when price is supplied |
| BUY-016 | `required_evidence` | `RequirementEvidenceCriterion` | Child rows | Nullable | Every item needs approved type and mandatory/preferred classification |
| BUY-017 | `delivery_location` | `RequirementDelivery.delivery_location` | Structured JSONB/FK | Nullable | Must remain separate from buyer address and target market |
| BUY-018 | `delivery_window_start` | `RequirementDelivery.window_start` | Date | Nullable | Must be less than or equal to end |
| BUY-019 | `delivery_window_end` | `RequirementDelivery.window_end` | Date | Nullable | Must be greater than or equal to start |
| BUY-020 | `required_lead_time_value` | `RequirementDelivery.lead_time_value` | Positive integer | Nullable | Must be positive when supplied |
| BUY-021 | `required_lead_time_unit` | `RequirementDelivery.lead_time_unit` | Reference/code | Conditional | Required when lead time is supplied |
| BUY-022 | `mandatory_criteria` | `RequirementEligibilityCriterion` | Child rows | Nullable | Hard criteria evaluated before preferences |
| BUY-023 | `preferred_criteria` | `RequirementPreference` | Child rows | Nullable | Cannot override failed mandatory criteria |
| BUY-024 | `priority_weights` | `MatchingConfiguration` reference | Versioned JSON/config | Nullable | No weights until approved |
| BUY-025 | `buyer_preferences` | `RequirementPreference` | Child rows | Nullable | Must never be silently promoted to mandatory |
| BUY-026 | `requirement_notes` | `BuyerRequirementVersion.requirement_notes` | Text | Nullable | Apply approved length and access policy |
| BUY-027 | `buyer_verification_status` | Deferred buyer profile/config field | Enum/config code | Nullable | Do not expose `Verified` without an approved process |
| BUY-028 | `requirement_status` | `BuyerRequirement.requirement_status` | Enum/config code | Not null after creation | Transitions require approved workflow |
| BUY-029 | `completeness_status` | `BuyerRequirement.completeness_status` | Derived enum | Not null after evaluation | Separate from workflow status |
| BUY-030 | `version` | `BuyerRequirementVersion.version` | Positive integer | Not null | Unique per requirement and immutable |
| BUY-031 | `created_by`, `created_at`, `updated_by`, `updated_at` | `RequirementAuditMetadata` | UUID/timestamps | System-generated | UTC timestamps; material changes audited |
| BUY-032 | `matching_ready` | `BuyerRequirement.matching_ready` plus blockers | Boolean/child rows | System-derived | Matching blocked until approved gate passes |

## Proposed relational rules

1. A `BuyerRequirement` has one current version and one or more immutable
   `BuyerRequirementVersion` rows.
2. Material edits create a new version; historical versions are never updated
   or deleted.
3. Child records that affect matching reference the requirement version.
4. Mandatory eligibility criteria and preferences are stored in separate entity
   types or have an enforced classification boundary.
5. Completeness and matching readiness are derived from versioned,
   approved configuration; they are not inferred from arbitrary non-empty
   fields.
6. Configuration and taxonomy records require an approval state and version.
7. Matching runs must later reference the exact requirement version and
   matching-configuration version used.

## Approval dependencies

Implementation must remain configurable until the decisions in
`open-data-decisions.md` are resolved. In particular, do not hardcode the
product catalogue, mandatory fields, status transitions, scoring weights,
currency conversion or matching-readiness gate.
