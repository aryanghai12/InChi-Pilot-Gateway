# Defect process and register

**Week 4 execution update, 23 November 2026:** [execution evidence](execution-2026-11-23-week4.md), [unsubmitted issue drafts](week4-issue-drafts.md). Base main `e4e320d`, QA branch `qa/week4-demand-readiness-boundaries`. Final run: 116 passed / 17 genuine product failures / 10 Blocked, 0 errors. No product changes or external issues/messages.

| ID | Finding | Requirement | Proposed severity | Owner / reviewer | Actual result / status |
|---|---|---|---|---|---|
| W4-01 | Analyst PATCH bypasses reviewer outcome/status and can forge submitted-by/reviewer | M4-AC2/3/5 | High | Abhishek / Ajendra | 6 failures; 200 and unauthorized values stored; reproduced, draft only |
| W4-02 | Review actions accept Draft, Submitted, Review Complete and Archived | M4-AC3/4, v2.2 section 8.1 | High | Abhishek / Adrika | 8 failures; 200; reproduced, draft only |
| W4-03 | Submission accepts referenced document without Evidence record | M4-AC1, v2.2 section 6.1 | High | Abhishek / Vishal | 1 failure; 200; reproduced, draft only |
| W4-04 | Mandatory assessment evidence applicability contract absent | v2.2 AC-07/08, M4-AC2/3 | Not assigned | Adrika / Abhishek | 2 cases Blocked at final review; mandatory status was only prose in the fixture; no confirmed defect draft |
| W4-05 | Buyer readiness omits specification gate on action and PATCH | M5-AC2, v2.2 AC-11 | High | Abhishek / Adrika | 2 failures; 200; reproduced, draft only |

GitHub open and closed issues were checked through the public REST API on 23 November. Existing open **#83 (QA-004/AUD-01), #84 (AUD-15), #85, #86 and #87** remain their existing records; none was recreated. W4-03/04 concern assessment evidence linkage/outcome guards, distinct from #86's registry verification write. Missing audit content belongs to #87. Existing security issues were not re-executed as part of this focused run and are not claimed fixed. The old QA-001/003/005/006 statuses below describe 16 November evidence; governance records later fixes. Closed clean-install/lint issues #63/#64 are not current blockers.

Blocked work: mandatory assessment evidence applicability (W4-04), five-role acceptance (D-22), immutable version/history and match-run APIs, assignment/reassessment/archive contracts, approved criteria/reference API (D-23), SEC-03 record boundary definition, PostgreSQL trigger/concurrency and live browser stack. Final review corrected the earlier 19-failure/five-defect claim: 17 failures establish four findings; two cases require the applicability contract. These are deferred dependencies, not passing tests or newly reproduced defects. No Gate 2 acceptance is claimed.

---

The remainder preserves the original Week 1-3 defect record and execution context.

**Owner:** Harish Pal · **Triage:** Aryan · **Updated:** 16 November 2026, integrated verification on `test@a7cc398` plus QA-only changes.

All QA-001–004 findings are now confirmed by execution or a deterministic repository check; they are no longer suspected. [Execution report](execution-2026-11-16-integrated.md) links commands, environment and raw output. Product code remains unchanged. No GitHub Issues or messages were sent; owners below identify the required coordination, not a completed notification or accepted assignment.

## Process

Use GitHub Issues/Projects (D-18), with `defect`, severity and module labels. This local register carries the findings for review; external issues were not created in this session.

Lifecycle: `New → Triaged → Assigned → In progress → Fixed → Retest → Closed`, or `Reopened`, `Deferred` / `Duplicate` with a recorded reason. Every record needs requirement, environment/revision, steps, expected/actual, severity, owner and retest evidence. QA reports product defects; the product owner fixes them. Critical defects must close before acceptance; High defects need closure or an approved documented workaround; Medium/Low remain visible.

## Confirmed open defects

| ID | Finding | Requirement | Severity | Owner for coordination | Status |
|---|---|---|---|---|---|
| QA-001 | Anonymous workspace routes render without login | M1-AC1/AC2 | High | Priyanka | Confirmed/reproduced; open |
| QA-002 | Frontend ignore pattern hides `.env.example` | M1-AC6 | Low | Ajendra/Priyanka | Confirmed repository check; open |
| QA-003 | Priced product creation accepts omitted currency | M3-AC2 | High | Abhishek/Vishal | Confirmed API failure; open |
| QA-004 | Confidential security finding; details withheld | M1, D-12 | Critical | Abhishek/Ajendra; triage Aryan | Confirmed; private review required |
| QA-005 | Login CSRF rejection returns HTML instead of structured JSON | M1-AC3, TD-05 | Medium | Abhishek | Confirmed backend/API contract failure; open |
| QA-006 | Unknown API path returns HTML 404 through proxy | TD-09 | Medium | Abhishek/Priyanka | Confirmed API routing contract failure; open |

### QA-001 — Unauthenticated workspace access

- **Environment:** integrated source `a7cc398`, built frontend, PostgreSQL 17 synthetic stack; see report for manifest-compatible dependency versions and clean-lock limitation.
- **Steps:** fresh browser context, no session; open `/requirements`, `/matching`, `/opportunities`, `/audit` individually.
- **Expected:** redirect to `/login?next=<requested path>`; no authenticated workspace.
- **Actual:** all four remain on their workspace URL. The fallback demo-user implementation is still present. Dashboard/suppliers/products/readiness redirect cases pass; those passing cases do not close the remaining route failures. No protected backend-data exposure is claimed from this UI finding alone.
- **Evidence/retest:** [sanitized execution record](execution-2026-11-16-integrated.md); four normal failing assertions in `auth.spec.ts`. Owner must fix the shared guard, then rerun all eight routes.

### QA-002 — `.env.example` ignored

- **Steps:** `git check-ignore -v frontend/.env.example`.
- **Expected:** placeholder configuration can be tracked.
- **Actual:** `frontend/.gitignore:34:.env*` matches. Root ignore exceptions do not override the deeper frontend rule. This proves the prospective example would be ignored; it is not evidence of a leaked secret.
- **Evidence/retest:** [raw check](evidence/delivery/sanitized-results.json). Fix belongs to Ajendra/Priyanka; QA did not edit either ignore file.

### QA-003 — Explicit currency validation

- **Steps:** authenticate synthetic analyst, create supplier, POST a product with positive `price_min`/`price_max` and no `currency`.
- **Expected:** HTTP 400 with a currency field error (M3-AC2).
- **Actual:** HTTP **201**. Source defines a USD default and lacks the explicit-currency gate; the runtime test confirms acceptance of the incomplete input. The response currency itself was not separately captured as evidence.
- **Evidence/retest:** `registry-api.spec.ts` omitted-currency assertion in [sanitized execution record](execution-2026-11-16-integrated.md). Remains a normal failing test.

### QA-004 ? Confidential security finding

Details and restricted evidence are preserved in a separate local confidential report. No public reproduction or diagnostic is included. Private owner review is required before any disclosure.

### QA-005 — Structured CSRF response missing

- **Steps:** send anonymous login with missing CSRF cookie/token, then with a bootstrapped cookie but invalid header.
- **Expected:** HTTP 403 JSON with `code=csrf_failed`; no session is issued.
- **Actual:** HTTP **403**, content type **text/html**. CSRF protection is enforced, but its required JSON error contract and client retry signal are absent.
- **Evidence/retest:** [QA backend controls](evidence/delivery/sanitized-results.json), plus missing/invalid-CSRF failures in the [sanitized execution record](execution-2026-11-16-integrated.md). Do not weaken the tests to accept HTML.

### QA-006 — API 404 content type

- **Steps:** GET `/api/v1/qa-no-such-endpoint/` through Next.js.
- **Expected:** Django JSON 404, not an HTML page (TD-09).
- **Actual:** HTTP **404** with **text/html**.
- **Evidence/retest:** `api-contract.spec.ts` in [sanitized execution record](execution-2026-11-16-integrated.md). Owner should supply the agreed JSON handler; QA leaves product routing unchanged.

## Dependencies and build blockers

| ID | Current state | Required action |
|---|---|---|
| QA-B01 | **Resolved for local verification:** source integrated, isolated stack executed and removed | Preserve the new evidence; earlier blocked results remain historical |
| QA-B02 | **Blocked:** readiness backend workflow/API/schema absent; D-03 open, D-09 unapproved | Abhishek/Adrika/Vishal provide contract/schema; BNCS approval recorded before acceptance |
| QA-B03 | **Locally unblocked / source dependency still open:** backend requirements omit psycopg; existing database requirements provide it | QA CI/local runner install both existing requirement files; Abhishek/Vishal reconcile standalone backend dependency declaration |
| QA-B04 | **Confirmed clean-install blocker:** `npm ci` rejects tinypool 1.1.1 versus override resolving 2.2.0 | Priyanka/Ajendra regenerate/review the lockfile; local no-save install is temporary evidence, not clean-clone proof |
| QA-B05 | **Confirmed CI blocker:** frontend lint reports 36 errors and 5 warnings | Priyanka fixes product files; QA reruns the gate afterward |

The initial browser 403 test failed because an unscoped alert locator matched Next.js's route announcer as well as the product alert. QA scoped it to the error banner and the focused retest passed, including live 403 and session preservation. This was a repaired test defect, not an unresolved product defect. No expected-failure marker or skipped case hides any remaining failure.
