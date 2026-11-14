## Week 3 - 09 November-13 November 2026

**Completed**
- Shared security and negative-testing specification merged in [PR #21](https://github.com/aryanghai12/InChi-Pilot-Gateway/pull/21). The specification identifies Harish Pal as co-author and automation lead and defines SEC-TEST-01–12 for CSRF, session rotation, 401/403 behaviour, RBAC, object boundaries, audit immutability, matching fail-safe behaviour and error sanitisation — merged — [specification](https://github.com/aryanghai12/InChi-Pilot-Gateway/blob/main/docs/security/SECURITY_TEST_SPECIFICATIONS.md)

**Meetings, reviews and coordination**
- None recorded in the repository for this reporting period.

**In progress**
- Expand functional, API, permission and regression coverage for supplier registry, product catalogue and China-readiness workflows — M2–M4 — execution status needs to be updated in the traceability matrix.
- QA strategy, traceability, Playwright tests and test CI workflow remain on the `test` branch rather than `main` — integration PR/rebase remains outstanding — [QA files](https://github.com/aryanghai12/InChi-Pilot-Gateway/tree/test/docs/qa), [E2E suite](https://github.com/aryanghai12/InChi-Pilot-Gateway/tree/test/e2e), [CI workflow](https://github.com/aryanghai12/InChi-Pilot-Gateway/blob/test/.github/workflows/ci.yml)

**Tests and validation**
- None. No Week 3 QA test command or execution result is recorded in the report or QA branch.

**Blocked, dependencies and decisions needed**
- QA evidence is not yet integrated into `main`; as checked on 14 November, `test` is 4 commits ahead and 72 commits behind `main` — sync and review required — [branch comparison](https://github.com/aryanghai12/InChi-Pilot-Gateway/compare/main...test)

**Next week**
- Sync the QA branch with current `main` and open a focused PR for `docs/qa/`, `e2e/` and the test CI workflow — M11-AC2.
- Execute and record regression/API coverage for authentication, session/CSRF, 401/403 role boundaries, supplier/product CRUD and validation, and readiness workflows; update each M#-AC# status with actual results — M1–M4, M11-AC2.

## Week 2 - 02 November-06 November 2026

**Completed**
- Updated the QA strategy to map coverage against M1-AC1 through M11-AC11; added the traceability matrix and defect register — pushed to `test` — [QA documentation](https://github.com/aryanghai12/InChi-Pilot-Gateway/tree/test/docs/qa)
- Added the Playwright project with authentication, routing and API-contract smoke coverage — pushed to `test` — [E2E tests](https://github.com/aryanghai12/InChi-Pilot-Gateway/tree/test/e2e)
- Added GitHub Actions test jobs for frontend lint, type-check, Vitest, build and Playwright — pushed to `test` — [CI workflow](https://github.com/aryanghai12/InChi-Pilot-Gateway/blob/test/.github/workflows/ci.yml)
- Logged QA-001 (High: unauthenticated workspace renders through a hardcoded demo user; M1-AC1/M1-AC2) and QA-002 (Low: `.env*` ignores `.env.example`; M1-AC6) — [defect register](https://github.com/aryanghai12/InChi-Pilot-Gateway/blob/test/docs/qa/defects.md)

**Meetings, reviews and coordination**
- None recorded in the repository for this reporting period.

**In progress**
- Backend-dependent CSRF, unauthenticated 401 and JSON-404 API cases were written but skipped until the backend was available on `main`; the 403 role-denial case still required seeded role accounts — M1-AC2/M1-AC3.

**Tests and validation**
- `cd frontend && npm run lint` -> no errors; `npm run typecheck` -> no errors.
- `cd frontend && npm test` -> 3 test files, 12 passed.
- `cd e2e && npx playwright test` -> 5 passed, 3 skipped; QA-001 was reproduced as the expected failure.
- GitHub Actions CI workflow -> not yet run on GitHub.

**Blocked, dependencies and decisions needed**
- Backend had been reverted from `main` in PR #14, preventing Gate 1 evidence for M1–M3 — waiting on Abhishek — since 2026-11-05 — escalation to Aryan planned.

**Next week**
- Sync the QA branch and submit a focused PR for the QA documentation, Playwright suite and CI test jobs — M11-AC2.
- Retest QA-001 after the authentication fix and add backend/API and seeded-role tests once the backend is integrated — M1-AC1/M1-AC3, M2–M3.

## Week 1 - 26 October-30 October 2026

**Completed**
- Prepared and submitted the initial QA baseline on the `test` branch: test strategy, provisional traceability matrix, 15 smoke test cases covering M1–M5, and a defect workflow — submitted — [commit 58411f2](https://github.com/aryanghai12/InChi-Pilot-Gateway/commit/58411f2)

**Meetings, reviews and coordination**
- None recorded in the repository for this reporting period.

**In progress**
- Convert provisional test identifiers to the stable `M#-AC#` acceptance-criterion identifiers and align the matrix with the MVP baseline — M11-AC2 — not started at the end of the week.

**Tests and validation**
- None. No runnable application code/environment was available for QA execution during Week 1.

**Blocked, dependencies and decisions needed**
- Runnable environment, test accounts and API contract — waiting on Abhishek and Priyanka — since 2026-10-29 — recorded in `docs/w1.md` §5 on the `test` branch.

**Next week**
- Finalise the traceability matrix using the stable M#-AC# identifiers and prepare automated smoke coverage as the frontend/backend skeletons become available — M11-AC2, M1–M5.

