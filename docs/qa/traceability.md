# Requirements-to-test traceability (M11-AC2)

**Owner:** Harish Pal · **Last updated:** 5 Nov 2026, commit base `33f337b` (`main`)

Status values: `Not run` · `Pass` · `Fail` · `Blocked` (dependency missing) · `Gap` (no test designed yet).
A status is only `Pass` or `Fail` when the test was actually executed; the run is linked in *Evidence*.

**State of `main` at this update:** frontend only. The backend was reverted (PR #14), so every criterion that needs the API, database or audit is `Blocked`.

## M1 — Authentication and role-based access

| AC | Test(s) | Level | Status | Evidence / defect |
|---|---|---|---|---|
| M1-AC1 | E2E per-role navigation (to write once role accounts are seeded) | E2E | Blocked | Needs `create_platform_admin` + seeded roles |
| M1-AC2 | `e2e/tests/auth.spec.ts` › unauthenticated workspace visit redirects to login | E2E | Fail | QA-001 (reproduced locally 5 Nov, `npx playwright test`) |
| M1-AC2 | `e2e/tests/api-contract.spec.ts` › absent session returns 401 `not_authenticated` | E2E (API) | Blocked | Skipped until `E2E_BACKEND=1` |
| M1-AC3 | `e2e/tests/api-contract.spec.ts` › login without CSRF token is rejected | E2E (API) | Blocked | Skipped until `E2E_BACKEND=1` |
| M1-AC3 | Role denial returns 403 and UI keeps session | E2E | Gap | Needs role accounts |
| M1-AC3 | `frontend/src/lib/api/client.test.ts` (403 handling in `apiFetch`) | Unit | Pass | `npm test` 5 Nov: 12/12 passed |
| M1-AC4 | Deactivated user denied on next request | pytest API | Blocked | Backend |
| M1-AC5 | Login success / failure / denial audit events, no secrets | pytest API | Blocked | Backend |
| M1-AC6 | Secret scan (gitleaks) | CI | Gap | Ajendra's security job; see QA-002 |

## M2 — Supplier registry

| AC | Test(s) | Level | Status | Evidence / defect |
|---|---|---|---|---|
| M2-AC1 | Save draft with draft-minimum fields; stable ID | pytest API + E2E | Blocked | Backend |
| M2-AC2 | Mark `Complete` with missing fields → field errors | pytest API + E2E | Blocked | Backend |
| M2-AC3 | Search/filter on seed data; empty result guidance | pytest API + E2E | Blocked | Backend, `seed_demo` |
| M2-AC4 [DEFERRABLE] | Duplicate warning | pytest API | Blocked | Backend |
| M2-AC5 | Evidence shows "provided" not "verified" | pytest API + E2E | Blocked | Backend |
| M2-AC6 | Audit event per create/edit/status/archive | pytest API | Blocked | Backend |
| M2-AC7 | Stale `version` save → 409 conflict | pytest API | Blocked | Backend |

## M3 — Product catalogue

| AC | Test(s) | Level | Status | Evidence / defect |
|---|---|---|---|---|
| M3-AC1 | Product needs an accessible supplier | pytest API | Blocked | Backend |
| M3-AC2 | Units/currency required; unknown ≠ zero | pytest API + E2E | Blocked | Backend |
| M3-AC3 | Product search on ≥30 seed products | pytest API | Blocked | Backend, `seed_demo` |
| M3-AC4 | Translation status shown; unreviewed ≠ verified | E2E | Blocked | Backend, D-14 |
| M3-AC5 | Audit events on material changes | pytest API | Blocked | Backend |

## M4 — China-readiness assessment

| AC | Test(s) | Status |
|---|---|---|
| M4-AC1 – M4-AC6 | Planned Week 3–4 (submission gate, reviewer-only outcome, history, question-set version) | Blocked — backend, D-03 |

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
| M10-AC1 – M10-AC4 | Exactly one event per material action; UPDATE/DELETE rejected; no secrets; visibility per D-09 | Blocked — backend |

## M11 — Security, QA, documentation and demo

| AC | Test(s) | Status |
|---|---|---|
| M11-AC1 | Defect register shows no open Critical at acceptance | Not run — see [defects.md](defects.md) |
| M11-AC2 | This matrix | In progress |
| M11-AC3 | Fresh-clone setup from README | Blocked — no Compose / backend |
| M11-AC4 | 8-step demo script incl. denied case + failure case | Gap — Week 8 |
| M11-AC5 – M11-AC11 | Handover packs verified against their checklists | Gap — Weeks 7–8 |

## Supporting technical checks (not acceptance criteria)

| Check | Source | Test | Status |
|---|---|---|---|
| Deep-route refresh served by Next.js | TD-09 | `e2e/tests/routing.spec.ts` | Pass (local, 5 Nov) |
| Unknown UI route → Next.js 404 page | ARCHITECTURE §7 | `e2e/tests/routing.spec.ts` | Pass (local, 5 Nov) |
| Unknown `/api/` path → Django JSON 404 | TD-09 | `e2e/tests/api-contract.spec.ts` | Blocked |
| Security headers set | ARCHITECTURE §7 | `e2e/tests/routing.spec.ts` | Pass (local, 5 Nov) |

## Explicit gaps

1. No backend on `main`: M1-AC1/3/4/5 and all of M2–M10 cannot be executed.
2. No seeded role accounts: per-role navigation and 403 cases not yet written.
3. No Compose stack: M11-AC3 and full-stack E2E cannot run in CI.
