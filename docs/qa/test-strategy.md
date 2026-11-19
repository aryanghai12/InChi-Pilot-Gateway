# Test strategy — InChi Pilot Gateway

**Owner:** Harish Pal ? **Updated:** 16 November 2026 ? **Status:** Integrated verification executed; confirmed defects and readiness gaps remain open.

QA independently verifies acceptance criteria; BNCS accepts the pilot. Use the existing pytest/pytest-django, Vitest/React Testing Library and Playwright stack. No replacement framework is introduced.

## Scope and ownership

Weeks 1–3 cover M1 authentication/permissions, M2 supplier registry, M3 products and M4 China readiness, with M10 audit assertions where observable. Later modules remain planned in the traceability matrix. Cross-stack tests and API regression belong in `e2e/`; backend unit/API tests belong to their code owners under `backend/apps/<app>/tests/`, frontend unit tests beside their code. Harish owns `docs/qa/` and test CI jobs. Coordinate product fixes with Abhishek/Priyanka, data/trigger evidence with Vishal, negative/security cases with Ajendra, criteria with Adrika, and triage with Aryan.

## Risk priorities and test design

- P0: anonymous access, CSRF, role/object bypass, session revocation, missing mandatory inputs and unintended workflow progression.
- P1: authenticated create/read/update/archive, persistence, search/filter correctness, conflicts, product supplier linkage and audit integrity.
- P2: boundary breadth, empty states and usability.

Assert rejection and unchanged state, not status alone. Exercise roles through direct API requests; hiding buttons is insufficient. Unknown numeric data remains null, never silently zero. Currency/units must be explicit. Use archive semantics rather than inventing permanent deletion. Role rules are provisional under **UNAPPROVED D-09**; readiness rules require D-03. Tests must not approve business policy.

## Environments and data

`test@a7cc398` now includes application source and preserves the prior QA baseline. Main `e89ab65` was verified against GitHub. Authentication/registry exist; readiness backend workflow/API remains absent. Earlier same-day blocked-environment evidence is historical.

Playwright can start the frontend or use an existing Next.js origin. The QA local runner now supplies a disposable PostgreSQL 17 + pgvector stack, separate database-model test database, generated synthetic role accounts, loopback-only Django/frontend and deterministic cleanup. No shared volume or .env is used. PostgreSQL trigger checks ran successfully. See `e2e/README.md` and the integrated report for actual versions and install limitations.

Test names use UUIDs, each role has its own session, and test-owned suppliers are archived in teardown. Products remain under archived suppliers; dispose of the synthetic test database after a run. Restricted security coverage and its evidence are maintained privately and omitted from public delivery. Do not run against shared or real data. Do not commit credentials or storage state. API traces are disabled to avoid retaining authentication payloads/cookies.

## Entry, exit and evidence

Entry: relevant implementation and agreed API contract, running isolated stack, account roles, versioned source and synthetic fixtures. Missing prerequisites are **Blocked**, not Pass. Configuration checks and discovery can run independently.

Exit: planned cases executed; failures reproducible and linked to an owner/defect; open Critical/High items visible to Aryan; traceability and reviewed evidence current. Passing tooling or smoke alone does not establish release readiness. No unexecuted test receives Pass, and known failures are not hidden with expected-failure markers.

Record command, date, QA revision, stack revision, environment, counts, status and evidence path. Use Pass/Fail only for executed behavior, Not Run for unattempted cases with available dependencies, Blocked for missing dependencies, and Gap for missing design/automation. Historical results stay attributed to their original report and are not current execution evidence.

## Smoke and regression

Reuse `docs/w1.md` smoke designs and stable IDs; current implementation mapping is in `traceability.md`. Minimum smoke: login form, unauthenticated denial, CSRF, session login/logout, supplier save/retrieve, invalid Complete rejection, product supplier link and unknown values, deep route, JSON API 404 and security headers. Full API regression adds role denial/session preservation, stale writes, search/filter/empty results and table-driven validation.

M4-AC1–6 have individually designed blocked cases in traceability. No guessed endpoint or UI mock counts as readiness API coverage. Timed expiry, deactivation, actual pre-login session-key rotation, full audit assertions and UI session retention after a server denial remain explicit gaps.

## Commands and CI

See `e2e/README.md` for environment variables and commands. `npm test` performs preflight before Playwright; `npm run test:list` collects without application startup. API-only mode cannot silently skip all backend tests.

CI checks QA configuration/discovery independently, explicitly fails the application-source gate when source is absent, retains JSON/JUnit/HTML output, and provides frontend test/build and PostgreSQL backend regression jobs for integrated source. The manual external API job requires stack origin, deployed revision and role secrets. It does not start or deploy a stack. Ajendra's security workflow is outside this change.

Backend CI now installs the existing database requirements alongside backend development requirements, supplying psycopg without changing product manifests. It runs existing backend tests, QA controls and database model tests. The complete workflow remains unexecuted remotely. Local clean frontend installation and lint fail; these gates must be fixed by their owners before CI can be green.

Current results and remaining blockers: [integrated execution report](execution-2026-11-16-integrated.md). Earlier reports and weekly entries are preserved as historical evidence.