# Requirements-to-test traceability (M11-AC2)

**Owner:** Harish Pal · **Updated:** 16 November 2026 · QA base `test@a7cc398` plus QA-only working-tree changes.

Current evidence: [sanitized integrated report](execution-2026-11-16-integrated.md). Source main `e89ab65` is integrated and QA preserved. Latest observed public-case ledger: **44 Pass / 8 Fail across 52 cases**, combining full and focused runs, not a single complete 52-case execution. One restricted case/evidence is maintained privately and excluded from the public collection. Historical raw reports remain local.

Status values: Pass / Fail (executed), Not Run (not attempted), Blocked (missing dependency), Gap (missing design/automation). Pass applies to the stated checks, not automatic approval of an entire criterion. D-09 permissions remain UNAPPROVED. All current results link to the report and raw evidence; later-week planning rows are retained as historical planning notes.

## M1 — Authentication and access

| AC | Existing/new test coverage | Current status and remaining gap |
|---|---|---|
| M1-AC1 | Per-role login/cookie checks in `session-api.spec.ts` pass. | **Partial Pass** for public login checks. A related confidential finding is tracked privately as QA-004. Full role-navigation coverage remains Gap. |
| M1-AC2 | `auth.spec.ts` now checks all eight workspace routes; API absent/invalid sessions, invalid login, logout/replay pass. QA backend expiry test passes. | **Fail QA-001** on requirements/matching/opportunities/audit. Dashboard/suppliers/products/readiness redirect cases pass. |
| M1-AC3 | Allowed/denied registry/user-management API cases pass with unchanged state and session preservation. `workspace.spec.ts` real 403 UI/session test passes after locator repair. | **Fail QA-005**: missing/invalid login CSRF returns HTML instead of structured JSON. Other inaccessible object scopes remain partial. |
| M1-AC4 | `e2e/backend/test_controls.py` deactivates a disposable account through the admin API and verifies the next protected request is 401. | **Pass** on PostgreSQL; existing shared role accounts were not deactivated. |
| M1-AC5 | Planned login success/failure/denial audit assertions including actor/outcome and absence of secrets. SQL immutability is covered separately under M10. | **Gap / Not Run** for authentication event completeness/content; immutability alone does not satisfy this criterion. |
| M1-AC6 | `git check-ignore -v frontend/.env.example` confirms the frontend ignore pattern. Runtime secrets generated in process environments; API traces disabled. | **Fail QA-002** for environment-example tracking. Complete repository secrets scan **Not Run**. |

## M2 — Supplier registry

| AC | Existing/new test coverage | Current status and remaining gap |
|---|---|---|
| M2-AC1 | API draft create/retrieve/search, stable ID, persisted edit; `workspace.spec.ts` creates a draft through the browser and reloads persisted data. | **Pass** for executed supplier flows. Archive semantics retained; no invented hard-delete requirement. |
| M2-AC2 | Complete validation rejection leaves draft/version unchanged; valid Complete persists. Existing backend tests also pass. | **Pass** for current implementation fields; business field approval remains separate. |
| M2-AC3 | API search, status/country match, mismatch and empty results pass. | **Partial Pass**; full approved seed-size, category/sort and UI empty-guidance breadth remain Gap. |
| M2-AC4 [DEFERRABLE] | Planned duplicate warning without merging/deleting either record. | **Gap / Not Run** pending duplicate contract or deferral decision. |
| M2-AC5 | Planned evidence provided-versus-verified and reviewer restrictions. | **Gap / Not Run** for full evidence verification workflow. |
| M2-AC6 | Existing backend create/Complete audit-existence assertions pass. | **Partial Pass**; exactly-one event, actor/time/changed-fields and rollback assertions remain Gap. |
| M2-AC7 | API persisted winning edit/version, 409 stale write, and unchanged data after rejection pass; backend conflict test passes. | **Pass** for executed stale-write scenarios on PostgreSQL; simultaneous transaction race coverage remains Gap. |

## M3 — Product catalogue

| AC | Existing/new test coverage | Current status and remaining gap |
|---|---|---|
| M3-AC1 | Linked product create/retrieve/update, invalid/missing supplier rejection, role-denied direct mutations and archived-supplier backend check pass. | **Pass** for implemented checks; broader ownership scopes require agreed object policy. |
| M3-AC2 | Numeric nulls, units, zero/negative MOQ, price bounds and invalid/blank currency checks pass. Omitted-currency assertion fails. | **Fail QA-003**: positive prices accepted with implicit USD. UI numeric boundary breadth remains partial. |
| M3-AC3 | API search/supplier/category inclusion and exclusion pass. | **Partial Pass**; at least 30-product seed reconciliation/pagination still Gap. |
| M3-AC4 | Mandarin update remains provided_unreviewed; backend translation check passes. | **Partial Pass**; full UI labels/reviewer-only verification need further coverage. |
| M3-AC5 | Denied edits preserve product data; audit service exists. | **Gap / Not Run** for material-change audit event content/exact count. |

## M4 — China-readiness assessment

These are designed functional/API/regression cases, **not automated or executed cases**. The inspected backend has only app scaffolding and no readiness API. Do not guess URLs/payloads or treat local UI rules as approved business criteria. Dependencies: Abhishek workflow/API, Vishal storage/history, Adrika question schema, BNCS D-03; reviewer permissions D-09.

| AC / case | Preconditions and steps | Expected result | Status |
|---|---|---|---|
| M4-AC1 / TC-M4-01 | Versioned approved questions and supplier; omit each mandatory answer in turn; submit through UI and direct API; retrieve assessment. | Field-specific missing list and corrective guidance; no submitted status or new review outcome. | Blocked; automation Gap |
| M4-AC2 / TC-M4-02 | Analyst completes every required answer; save/submit and retrieve status/outcome. | Completeness never automatically grants a readiness outcome; human review still required. | Blocked; automation Gap |
| M4-AC3 / TC-M4-03 | Analyst/admin/reviewer sessions; try outcome and more-information actions with valid, missing and blank reason; try self-review. | Only permitted reviewer succeeds with reason; denied request changes no data and preserves session. Self-review follows agreed security contract. | Blocked; automation Gap |
| M4-AC4 / TC-M4-04 | Reviewer requests more information; analyst changes answer and resubmits; retrieve history before/after. | Prior answers, comments and outcomes remain; new submission is distinguishable. | Blocked; automation Gap |
| M4-AC5 / TC-M4-05 | Submit then review with different authorised users; inspect record and audit events. | Correct submitted/reviewed actor/time, outcome and reason persist; each material action is auditable. | Blocked; automation Gap |
| M4-AC6 / TC-M4-06 | Create assessment using question set A, introduce version B, retrieve original and new assessments. | Original references A; new assessment references B; historical interpretation is preserved. | Blocked; automation Gap |

## Later-week scope retained

The following planned M5–M11 baseline is outside Week 1–3 execution; its dependency statements are planning notes, not a new run result.
## M5 — Buyer requirement capture

| AC | Test(s) | Status |
|---|---|---|
| M5-AC1 – M5-AC5 | Planned Week 4 (mandatory vs preference, ready gate, versioning, criteria version, audit) | Blocked — backend, D-04/D-05 |

## M6 — Explainable matching

| AC | Test(s) | Status |
|---|---|---|
| M6-AC1 – M6-AC7 | Planned Week 5 with Alok: expected, false, missed, missing-data, manipulated-input, semantic-failure (run `Failed`, no partial results) | Blocked — engine not on `main`, D-11 |

## M7 — Human review and disposition

| AC | Test(s) | Status |
|---|---|---|
| M7-AC1 – M7-AC5 | Planned Week 5 (deciding role only, server-confirmed success, no auto-disposition, no `Accepted` for ineligible) | Blocked — backend, D-06 |

## M8 — Opportunity pipeline

| AC | Test(s) | Status |
|---|---|---|
| M8-AC1 – M8-AC5 | Planned Week 6 (only from accepted match, stage transitions, one per disposition) | Blocked — backend, D-07 |

## M9 — Dashboard

| AC | Test(s) | Status |
|---|---|---|
| M9-AC1 | Manual reconciliation of every figure against direct queries on seed data (with Vishal) | Blocked |
| M9-AC2 – M9-AC4 | Definitions reviewed; no hard-coded figures; permission-scoped data | Blocked — D-08 |

## M10 — Audit history

| AC | Test(s) | Status |
|---|---|---|
| M10-AC1 ? M10-AC4 | `e2e/backend/test_controls.py` raw SQL UPDATE/DELETE trigger tests pass on PostgreSQL (M10-AC2); other event completeness/content/visibility checks remain planned. | Partial Pass; remaining audit coverage Gap |

## M11 — Security, QA, documentation and demo

| AC | Test(s) | Status |
|---|---|---|
| M11-AC1 | Defect register shows no open Critical at acceptance | Not run — see [defects.md](defects.md) |
| M11-AC2 | This matrix | In progress |
| M11-AC3 | Isolated stack ran, but clean frontend install rejects lock/override mismatch. | Blocked ? QA-B04; fresh-clone reproducibility not established |
| M11-AC4 | 8-step demo script incl. denied case + failure case | Gap — Week 8 |
| M11-AC5 – M11-AC11 | Handover packs verified against their checklists | Gap — Weeks 7–8 |

## Supporting technical checks

| Check | Test | Current status |
|---|---|---|
| Next.js deep route / unknown UI 404 / security headers | `routing.spec.ts` | Pass, full run |
| Unknown API path returns JSON 404 | `api-contract.spec.ts` | Fail QA-006: HTML response |
| Actual session-key rotation / expiry | `e2e/backend/test_controls.py` | Pass on disposable PostgreSQL |
| Database audit immutability | Raw SQL UPDATE and DELETE tests in QA controls | Pass: both rejected by PostgreSQL trigger |
| QA configuration / TypeScript / discovery | Existing QA tooling | Pass: 6 configuration checks; 52 public cases collected (restricted coverage excluded); strict TypeScript passes |
| Build / clean install / lint | Frontend commands | Build Pass; clean install Fail QA-B04; lint Fail QA-B05 |

## Remaining execution dependencies

1. M4 workflow/API/question schema and D-03 approval remain absent; no readiness acceptance result is claimed.
2. D-09 business permission approval remains open. Tested provisional rules are not approved policy.
3. Owners must fix QA-001?006 and frontend lock/lint failures; remote CI and acceptance/UAT remain Not Run.
4. Local frontend runs used recorded manifest-compatible versions (Next 16.4.6, tinypool 2.2.0), not the inconsistent clean lock. Owner reconciliation is required before clean-clone evidence.
