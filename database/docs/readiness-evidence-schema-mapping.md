# Week 3 — Readiness and Evidence Schema Mapping

Implementation authority: Baseline v2.2, sections 6–8 and acceptance criteria.

## Assessment entity

Table: `readiness_assessment`

Stores:

- Immutable assessment ID.
- Supplier link.
- One or more product links.
- Assessment version.
- Questionnaire version `2.2`.
- Workflow state.
- Reviewer readiness outcome.
- Outcome reason.
- Contributor confirmation.
- Submission, review and update timestamps.

## Questionnaire response entity

Table: `readiness_response`

Stores CR-01 to CR-18 responses. Each assessment and criterion pair is unique.

The response model distinguishes:

- Unknown
- Not Applicable
- No explicit special state

Not Applicable responses require a reviewer or contributor reason.

## Evidence entity

Table: `readiness_evidence`

Stores:

- Evidence ID
- Assessment and criterion
- Evidence type
- Evidence condition
- Issuer/source
- Reference number
- Issue and expiry dates
- Storage reference
- Reviewer notes
- Condition actor and timestamp

New document references default to `DOCUMENT_RECEIVED_UNVERIFIED`.

## Controlled evidence conditions

- `NOT_PROVIDED`
- `SELF_DECLARED`
- `DOCUMENT_RECEIVED_UNVERIFIED`
- `OFFICIAL_SOURCE_CHECKED`
- `THIRD_PARTY_REPORT_RECEIVED_UNVERIFIED`
- `THIRD_PARTY_REPORT_SOURCE_CHECKED`
- `EXPIRED`
- `DISCREPANCY`
- `NOT_APPLICABLE`

These values are categorical and are not converted to scores.

## Workflow values

Assessment workflow:

- `DRAFT`
- `SUBMITTED`
- `UNDER_REVIEW`
- `INFORMATION_REQUIRED`
- `REVIEW_COMPLETE`
- `ARCHIVED`

Readiness outcome:

- `READY_FOR_MATCHING`
- `INFORMATION_REQUIRED`
- `NOT_CURRENTLY_ELIGIBLE`

## Blocking and submission

Table: `readiness_blocker`

Stores active criterion-level blocking reasons for missing, expired,
discrepant or unverified information.

Table: `readiness_submission_snapshot`

Stores an immutable JSON submission snapshot and questionnaire version.

## Audit

Table: `readiness_audit_event`

Stores:

- Actor
- UTC timestamp
- Action
- Object type and ID
- Object version
- Previous value
- New value
- Change summary
- Reason

PostgreSQL triggers prevent update and delete operations on audit rows.
