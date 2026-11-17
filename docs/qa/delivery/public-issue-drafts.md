# Public GitHub Issue drafts ? not submitted

Prepared 16 November 2026 by Harish Pal. Source: `test@a7cc398` plus QA-only changes. All reproductions use an isolated synthetic environment. Suggested labels/owners require normal triage; no assignment or notification has occurred.

Duplicate check: read all 57 public repository items returned by GitHub (2 issues, 55 PRs, all states). No exact issue duplicates were found in the reviewed titles/bodies. Closed [issue #49](https://github.com/aryanghai12/InChi-Pilot-Gateway/issues/49) is related integration context, not verified as the same reproduction. Comments, private issues/advisories and inaccessible records were not searched. Recheck before submission. Related implementation PRs do not prove a defect is fixed.

Runtime results used a manifest-compatible local tree, not a clean lock install; see the [execution record](../execution-2026-11-16-integrated.md). Restricted security material is absent from these public drafts.

## QA-001: Unauthenticated workspace routes do not redirect to login

**Labels:** defect, severity:high, M1 ? **Owner for triage:** Priyanka; review Ajendra ? **Requirement:** M1-AC1, M1-AC2

- **Environment:** integrated `a7cc398`; 16 November 2026; synthetic local stack and recorded versions.
- **Steps:** With no session in a fresh browser, visit `/requirements`, `/matching`, `/opportunities` and `/audit` separately.
- **Expected:** Each route redirects to `/login?next=<requested path>` without an authenticated workspace.
- **Actual:** All four remain at their workspace URL. Dashboard/suppliers/products/readiness redirect checks pass; no protected backend-data exposure is claimed from this UI finding alone.
- **Evidence and retest:** `e2e/tests/auth.spec.ts`; focused retest has four failing route assertions. Retest all eight workspace routes after the shared guard is fixed.
- **Duplicate review:** No exact duplicate found; related closed issue #49 and implementation PR #47. Confirm current behavior before reopening any prior work.

## QA-002: Frontend ignore rules also ignore the configuration example

**Labels:** defect, severity:low, M1 ? **Owner for triage:** Ajendra / Priyanka ? **Requirement:** M1-AC6

- **Environment:** integrated `a7cc398`; 16 November 2026; synthetic local stack and recorded versions.
- **Steps:** Run `git check-ignore -v frontend/.env.example`.
- **Expected:** A placeholder-only example can be tracked while real environment files remain ignored.
- **Actual:** `frontend/.gitignore:34:.env*` matches the prospective example path. This is not evidence of a leaked credential.
- **Evidence and retest:** [Reviewed output](../evidence/delivery/sanitized-results.json). After owner fix, the same check must no longer identify an ignoring rule for the example; real environment files must stay ignored.
- **Duplicate review:** No exact duplicate found. Related security baseline PR #21 is implementation context only.

## QA-003: Priced product can be created without explicit currency

**Labels:** defect, severity:high, M3 ? **Owner for triage:** Abhishek / Vishal ? **Requirement:** M3-AC2

- **Environment:** integrated `a7cc398`; 16 November 2026; synthetic local stack and recorded versions.
- **Steps:** Authenticate a synthetic analyst, create a supplier, then create a product with positive `price_min` and `price_max`, omitting `currency`.
- **Expected:** HTTP 400 with a field-specific currency error; no invalid product is persisted.
- **Actual:** HTTP 201. The runtime confirms acceptance of omitted currency; the returned currency value was not separately captured.
- **Evidence and retest:** `e2e/tests/registry-api.spec.ts`: numeric price requires explicitly supplied currency. After fix, rerun omitted/blank/invalid/valid currency and persistence cases.
- **Duplicate review:** No exact duplicate found. Related registry implementation PR #11 is not a defect closure.

## QA-005: Login CSRF rejection returns HTML rather than the agreed JSON contract

**Labels:** defect, severity:medium, M1 ? **Owner for triage:** Abhishek ? **Requirement:** M1-AC3, TD-05

- **Environment:** integrated `a7cc398`; 16 November 2026; synthetic local stack and recorded versions.
- **Steps:** Against the synthetic stack, submit login without a CSRF cookie/header; separately bootstrap a cookie and send an invalid CSRF header.
- **Expected:** HTTP 403 JSON with `code=csrf_failed`; no session issued.
- **Actual:** HTTP 403 with `text/html`. Protection is enforced; the JSON error contract/client signal is missing.
- **Evidence and retest:** [Backend control output](../evidence/delivery/sanitized-results.json); missing/invalid-CSRF Playwright cases also fail. Retest both API clients and the proxy path; do not weaken assertions to accept HTML.
- **Duplicate review:** No exact duplicate found. Related auth/security implementation PRs #7 and #21 are context only.

## QA-006: Unknown API path through Next.js returns an HTML 404

**Labels:** defect, severity:medium, M1 ? **Owner for triage:** Abhishek / Priyanka ? **Requirement:** TD-09

- **Environment:** integrated `a7cc398`; 16 November 2026; synthetic local stack and recorded versions.
- **Steps:** GET `/api/v1/qa-no-such-endpoint/` through the Next.js test origin.
- **Expected:** Django JSON 404 with JSON content type, not an HTML page.
- **Actual:** HTTP 404 with `text/html`.
- **Evidence and retest:** `e2e/tests/api-contract.spec.ts`: unknown API path test. Retest a missing API URL, a real protected API URL and an unknown UI URL after the agreed handler/proxy correction.
- **Duplicate review:** No exact duplicate found; closed issue #49 and frontend proxy PR #47 are related context.

## QA-B04: Frontend clean installation fails because tinypool lock and override conflict

**Labels:** defect, severity:high, M11 ? **Owner for triage:** Priyanka / Ajendra ? **Requirement:** M11-AC3; CI frontend test gate

- **Environment:** integrated `a7cc398`; 16 November 2026; synthetic local stack and recorded versions.
- **Steps:** From `frontend/`, run `npm ci --ignore-scripts --no-audit --no-fund` with access to the configured registry.
- **Expected:** The committed manifest and lock install reproducibly without editing files.
- **Actual:** EUSAGE: locked tinypool 1.1.1 does not satisfy the override resolution (2.2.0 in this execution).
- **Evidence and retest:** [Reviewed clean-install failure](../evidence/delivery/sanitized-results.json). Local no-save installation was a temporary test setup, not a fix. Owner should regenerate/review the lock, then rerun clean install and all frontend/QA gates.
- **Duplicate review:** No exact duplicate found. Dependency PRs reviewed did not establish a tinypool lock correction.

## QA-B05: Frontend lint gate fails with 36 errors and 5 warnings

**Labels:** defect, severity:high, M11 ? **Owner for triage:** Priyanka ? **Requirement:** CI frontend test gate; M11

- **Environment:** integrated `a7cc398`; 16 November 2026; synthetic local stack and recorded versions.
- **Steps:** Install the documented manifest-compatible local dependency tree, then run `npm run lint` in `frontend/`.
- **Expected:** Lint exits 0 under the repository rules, with any accepted warnings documented.
- **Actual:** Exit 1: 36 errors and 5 warnings, including explicit-any and unescaped entities in product files.
- **Evidence and retest:** [Reviewed lint output](../evidence/delivery/sanitized-results.json). Product changes require owner review; do not suppress lint globally. After fixes, use the corrected clean lock and rerun lint/typecheck/unit/build.
- **Duplicate review:** No exact duplicate found. ESLint dependency PRs are not verified fixes for these source errors.
