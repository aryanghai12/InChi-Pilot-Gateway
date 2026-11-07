# Daily reports — Harish Pal

QA and Test Automation Engineer · Process, template and rules: [README.md](README.md)

Only Harish Pal writes in this file. Newest entry first.

<!-- Add new entries directly below this line. -->

## 2026-11-05 · Thu · Week 2

**Completed**
- Test strategy, `M#-AC#` traceability matrix (M1-AC1 to M11-AC11) and defect register — pushed to `test` branch — [`docs/qa/`](https://github.com/aryanghai12/InChi-Pilot-Gateway/tree/test/docs/qa)
- Playwright project with Week 2 auth, routing and API-contract smoke tests — pushed to `test` branch — [`e2e/`](https://github.com/aryanghai12/InChi-Pilot-Gateway/tree/test/e2e)
- CI test jobs (frontend lint, typecheck, Vitest, build; Playwright) — pushed to `test` branch — [`.github/workflows/ci.yml`](https://github.com/aryanghai12/InChi-Pilot-Gateway/blob/test/.github/workflows/ci.yml)
- Logged QA-001 (High, Priyanka: workspace shows a hardcoded demo user instead of redirecting to login, M1-AC2) and QA-002 (Low, Ajendra: `.env*` ignores `.env.example`) — [`docs/qa/defects.md`](https://github.com/aryanghai12/InChi-Pilot-Gateway/blob/test/docs/qa/defects.md)

**In progress**
- Backend 401, CSRF and JSON-404 cases written but skipped until the backend is on `main`; 403 role-denial case not yet written (needs seeded role accounts) — M1-AC2, M1-AC3

**Tests and validation**
- `npm run lint` and `npm run typecheck` in `frontend/` → no errors
- `npm test` in `frontend/` → 3 files, 12 passed
- `npx playwright test` in `e2e/` → 5 passed, 3 skipped (QA-001 reproduced as expected failure)
- CI workflow not yet run on GitHub

**Blocked, dependencies and decisions needed**
- Backend reverted from `main` (PR #14), so Gate 1 evidence for M1–M3 cannot be produced — waiting on Abhishek — since 2026-11-05 — to raise in team channel with Aryan

**Next**
- Open PR from `test` to `main` for QA files — M11-AC2
- Retest QA-001 when fixed; add backend API tests when backend lands — M1-AC2, M1-AC3

## 2026-11-04 · Wed · Week 2

_Recorded late on 2026-11-05._

No update.

## 2026-11-03 · Tue · Week 2

_Recorded late on 2026-11-05._

No update.

## 2026-11-02 · Mon · Week 2

_Recorded late on 2026-11-05._

No update.

## 2026-10-30 · Fri · Week 1

_Recorded late on 2026-11-05._

No update.

## 2026-10-29 · Thu · Week 1

_Recorded late on 2026-11-05._

**Completed**
- Week 1 QA deliverables: test strategy, provisional traceability matrix, 15 smoke test cases (M1–M5) and defect workflow — submitted on `test` branch — [`58411f2`](https://github.com/aryanghai12/InChi-Pilot-Gateway/commit/58411f2) (`docs/w1.md`)

**In progress**
- Map provisional test IDs to the real `M#-AC#` IDs — M11-AC2 — not started

**Tests and validation**
- None. No application code existed to test.

**Blocked, dependencies and decisions needed**
- Runnable environment, test accounts and API contract — waiting on Abhishek, Priyanka — since 2026-10-29 — raised in `docs/w1.md` §5

**Next**
- Align QA docs to `M#-AC#` and move them to `docs/qa/` — M11-AC2

## 2026-10-28 · Wed · Week 1

_Recorded late on 2026-11-05._

No update.
