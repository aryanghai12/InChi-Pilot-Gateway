# Test strategy — InChi Pilot Gateway v0.1

**Owner:** Harish Pal (QA and Test Automation Engineer) · **Reviewers:** Aryan, Adrika
**Status:** Draft v0.2, 5 Nov 2026 (Week 2, revised timeline). Supersedes the Week 1 draft on the `test` branch (`docs/w1.md`), now aligned to the real `M#-AC#` IDs in [MVP_FEATURES.md](../MVP_FEATURES.md).

QA provides independent verification. It does not accept the pilot (BNCS does) and does not change requirements to match observed behaviour.

## 1. Scope

Every acceptance criterion `M1-AC1` to `M11-AC11` maps to at least one automated test or a documented manual check (M11-AC2). Coverage status lives in [traceability.md](traceability.md). Out-of-scope items (MVP_FEATURES §2) are not tested.

## 2. Test levels and tools

Tools are fixed by ARCHITECTURE.md §1. No second tool is added for the same job.

| Level | Tool | Location | Owner |
|---|---|---|---|
| Backend unit and API (incl. permission and denied paths) | pytest + pytest-django | `backend/apps/<app>/tests/` | Code owner; Harish reviews |
| Matching integration / engine | pytest | `backend/apps/matching/tests/`, `backend/ai_matching/tests/` | Alok; Harish reviews evaluation cases |
| Frontend components, hooks, `apiFetch()` | Vitest + React Testing Library | beside the code in `frontend/src/` | Priyanka; Harish reviews |
| Cross-stack E2E, smoke and regression | Playwright (TypeScript) | `e2e/` | Harish |
| Negative / security cases | pytest or Playwright | as above | Ajendra designs, Harish automates |
| Manual checks (UAT, dashboard reconciliation) | Documented scripts | `docs/qa/` | Harish with Adrika / Vishal |

## 3. Risk-based priorities

| Priority | Focus | Criteria |
|---|---|---|
| P0 | Access control, mandatory validation, audit, no silent fallback | M1-AC2/3/4/5, M2-AC2, M4-AC1/3, M5-AC2, M6-AC1/2/5, M7-AC1/5, M8-AC1, M10-AC1/2/3 |
| P1 | Core CRUD and workflow | M2–M5 remaining, M7, M8 |
| P2 | Boundary values, usability, regression breadth | everything else |

Defect severity follows the build manual §9 (see [defects.md](defects.md)).

## 4. Environments

| Environment | Use |
|---|---|
| Local / CI frontend only (`next build` + `next start`) | Frontend-only E2E (routing, headers, auth redirect). Runs today. |
| Compose reference environment (`docker compose up`, `create_platform_admin`, `seed_demo`) | Full-stack E2E, Gate demos, UAT. **Not available yet** (no backend or compose on `main`). |
| CI PostgreSQL 17 + pgvector service container | Backend pytest. Added to CI when `backend/` lands. |

Test data is synthetic only (≥15 suppliers, ≥30 products, ≥10 requirements from `seed_demo`). Tests must be repeatable and independent of run order.

## 5. Entry and exit criteria

**Entry (per feature):** code merged to `main` or available on a PR branch; acceptance criteria agreed; test accounts per role and seed data available; API contract published in `docs/api/openapi.yaml`.

**Exit (per cycle / Friday review):** planned tests executed with real results recorded; every failure has a defect with severity and owner; Critical/High items reported to Aryan; regression output saved for the review. Passing smoke tests alone does not mean release readiness.

## 6. CI

`.github/workflows/ci.yml` (test jobs owned by Harish; security jobs belong to Ajendra and are not added here):

- **frontend:** `npm ci`, `eslint`, `tsc --noEmit`, `vitest run`, `next build`.
- **e2e:** Playwright against the built frontend. Backend-dependent cases skip until `E2E_BACKEND=1` and the Compose stack exist.
- **backend:** to be added with the backend skeleton (`ruff`, `makemigrations --check`, `pytest` on PostgreSQL + pgvector).

## 7. Week 2 automation scope (AGENTS.md §C8)

| Case | Criterion | Status |
|---|---|---|
| Unauthenticated workspace visit goes to login | M1-AC2 | Automated as `test.fail` (QA-001); flips red once fixed so the marker gets removed |
| Login without CSRF token is rejected | M1-AC3 / TD-05 | Automated, skipped until backend |
| Absent session returns 401 `not_authenticated` | M1-AC2 / TD-06 | Automated, skipped until backend |
| Role denial returns 403 and keeps the session | M1-AC3 | Needs seeded role accounts; not written yet |
| Refresh on a deep route is served by Next.js | TD-09 | Automated |
| Unknown `/api/` path returns Django JSON 404, not a Next.js page | TD-09 | Automated, skipped until backend |
| Security headers present | ARCHITECTURE §7 | Automated |

## 8. Known gaps and dependencies

- The backend was reverted from `main` (PR #14). Gate 1 (6 Nov) evidence for create/retrieve supplier and product, persistence, validation and audit (M1–M3) cannot be produced until it is re-merged. Owner: Abhishek; raised to Aryan.
- `feature/ai-matching-structure` contains empty test files under `ai-matching-service/`, which does not match the agreed `backend/ai_matching/` location (ARCHITECTURE §4). Matching tests are planned for Week 5 with Alok.
- Role permissions are `UNAPPROVED` until D-09; permission tests will be rerun when it is recorded.
