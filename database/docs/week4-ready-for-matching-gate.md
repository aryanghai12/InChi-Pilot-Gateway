# Week 4 — Ready-for-Matching Database Gate

## Approved requirement statuses

- `DRAFT`
- `READY_FOR_MATCHING`
- `CLOSED`

`IN_REVIEW` and `ON_HOLD` are not MVP requirement statuses.

## Required gate fields

A requirement can become `READY_FOR_MATCHING` only when:

- Buyer organisation name exists.
- Target product category exists.
- Required specification exists.
- Quantity value and quantity unit exist.
- Delivery location includes a city and country.
- At least one mandatory eligibility criterion exists.
- Internal owner exists.
- If price is supplied:
  - Currency exists.
  - Price basis exists.
  - Minimum price is not greater than maximum price.

## Blocker storage

`MatchingReadinessBlocker` records:

- Field ID
- Reason code
- Reason detail
- Active state

The evaluator deactivates resolved blockers and creates or reactivates active
blockers for missing gate fields.

## Status and completeness

Database values:

- `DRAFT`
- `READY_FOR_MATCHING`
- `CLOSED`

Completeness values:

- `INCOMPLETE`
- `COMPLETE`

A requirement that is ready for matching must have `matching_ready=True`.
Closing a requirement sets `matching_ready=False`.

## Commercial and quantity constraints

The database rejects:

- Negative or zero quantity.
- Quantity without a unit.
- Negative or zero price.
- Minimum price greater than maximum price.
- Supplied price without currency.
- Supplied price without price basis.
- Delivery window with an end before its start.

## Version immutability

Buyer requirement versions cannot be updated or deleted through normal ORM
operations or PostgreSQL triggers. Material edits must create a new version
number.
