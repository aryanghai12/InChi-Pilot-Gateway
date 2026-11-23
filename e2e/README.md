# QA automation

Owner: Harish Pal. Uses the existing Playwright stack. Current results: [integrated execution report](../docs/qa/execution-2026-11-16-integrated.md).

Week 4 API results (executed 23 November): [execution report](../docs/qa/execution-2026-11-23-week4.md). From the root, run `<QA Python> e2e/scripts/week4-qa.py` with `backend/requirements-dev.txt` installed in an isolated virtual environment. It runs the new M4/M5 cases plus existing backend regression on a disposable SQLite test database, disables dotenv and writes raw output under ignored `.cache/qa-week4/`. Pass `--postgres` only with `DATABASE_URL` explicitly configured for a disposable synthetic PostgreSQL server with test-database creation permission. SQLite runs cannot prove PostgreSQL triggers or live browser/proxy behavior. The existing Compose runner and backend CI also collect the Week 4 file. Genuine product failures produce a nonzero exit; explicit Blocked cases do not count as acceptance passes. Historical blocked M4 statements below are superseded by this execution report.

From `e2e/`, run `npm ci`, `npm run test:config`, `npm run test:list`, `npm run preflight`, `npx playwright install chromium`, then `npm test`. On Windows use `npm.cmd` if PowerShell blocks `npm.ps1`.

Without `E2E_BASE_URL`, Playwright builds and starts the integrated `../frontend`. Preflight reports missing source or role configuration; dependency installation is separate. Discovery validates collection only; it requires neither the application nor browsers.

## Full-stack / API execution

Use an already running isolated synthetic test stack. Point to its **Next.js origin**, including the Django proxy, and record the stack source revision with QA results. Supply these environment variables through your shell or CI secrets, never tracked files:

| Variable | Value |
|---|---|
| `E2E_BASE_URL` | HTTP(S) origin, e.g. `http://127.0.0.1:3000` |
| `E2E_BACKEND` | Exactly `1` enables API tests; `0`/unset skips them |
| `E2E_API_ONLY` | `1` selects API specs without frontend startup or browser installation; requires backend mode |
| `E2E_ANALYST_EMAIL`, `E2E_ANALYST_PASSWORD` | Active, verified synthetic commercial analyst |
| `E2E_REVIEWER_EMAIL`, `E2E_REVIEWER_PASSWORD` | Active, verified synthetic reviewer |
| `E2E_ADMIN_EMAIL`, `E2E_ADMIN_PASSWORD` | Active, verified synthetic platform administrator |

Run `npm run preflight` and `npm test`. For original browser smoke, omit API-only mode and run `npm test -- auth.spec.ts routing.spec.ts`. Tagged smoke uses `npm test -- --grep @smoke` (API and browser smoke, or API smoke alone in API-only mode); full regression uses the entire suite.

Each role authenticates with CSRF in a separate request context. Tests use unique names and archive their own suppliers at teardown. Products remain under those archived suppliers because there is no approved hard-delete contract: dispose of the isolated test database after the run. Role assertions verify the provisional **UNAPPROVED D-09 implementation**, not business approval. Expiry, deactivation, existing-session rotation and raw SQL audit-trigger enforcement are covered by `backend/test_controls.py` against an isolated database.

API traces are off to avoid retaining login credentials/cookies. HTML, JSON and JUnit reports are generated in ignored `playwright-report/` and `test-results/`. Do not attach storage state. QA-001 is an ordinary failing assertion, not an expected failure. Discovery and backend-disabled skips are not application pass evidence.

Readiness M4-AC1–6 is Blocked on workflow/API, schema and D-03. The individual designed cases are in [traceability](../docs/qa/traceability.md). No guessed assessment endpoint or mock-only result counts as backend acceptance.


## Isolated local execution

The repository now includes frontend/backend/database source. Install Python dependencies into `.venv` with `uv pip install --python .venv/Scripts/python.exe -r backend/requirements-dev.txt -r database/requirements.txt`; use a workspace `UV_CACHE_DIR` if the user cache is not writable. Install the existing E2E dependencies. Set `PLAYWRIGHT_BROWSERS_PATH` to `<repository>/.cache/qa-browsers` when running `node node_modules/playwright/cli.js install chromium` from `e2e/`.

Frontend `npm ci` is currently blocked by the committed tinypool override/lock mismatch. The verified temporary setup used `npm install --no-save --package-lock=false --ignore-scripts --no-audit --no-fund`; this changes only the installed dependency tree. It produced Next 16.4.6 and tinypool 2.2.0 rather than locked 16.4.3/1.1.1, so it is not clean-lock evidence. Product owners must reconcile the lockfile.

From repository root, run `.venv/Scripts/python.exe e2e/scripts/local-qa.py --evidence-dir <new evidence directory>`. It requires Docker Desktop's `desktop-linux` context, runs only on `test` or `qa/week1-3-delivery`, refuses prior evidence summaries, starts `docker-compose.qa.yml` under its own project with tmpfs data, generates credentials in memory, executes suites, redacts known secrets, and stops its own services. Required free loopback ports: 55439, 58001, 53001. No fixed shared container or volume is reused. A nonzero result preserves real product/test failures.

Use `--phase browser-retest` only for auth/workspace tests against an already built frontend; it still provisions fresh disposable data. Default evidence goes to ignored `.cache/qa-evidence/`. Do not rerun into an existing evidence directory. Remote CI remains separately reviewed/executed.


Public delivery contains 52 Playwright cases. One restricted security case and its diagnostic/evidence are maintained privately; the public runner does not invoke them. Only reviewed structured summaries under `docs/qa/evidence/delivery/` are intended for staging. Raw integrated-run reports, caches and runtime artifacts remain excluded.
