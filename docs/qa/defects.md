# Defect process and register

**Owner:** Harish Pal · **Triage:** Aryan

## Process

Defects are GitHub Issues with labels `defect`, `severity:<critical|high|medium|low>` and the module label (`M1` … `M11`). This file mirrors open items for the Friday review until the issue labels exist (Aryan, Week 1 task).

Lifecycle: `New → Triaged → Assigned → In progress → Fixed → Retest → Closed` (or `Reopened`, `Deferred` / `Duplicate` with a recorded reason).

Every defect records: ID, title, `M#-AC#`, environment and commit, steps, expected vs actual, severity, owner, status, retest result. QA does not fix product code; the owner does, QA retests.

| Severity (build manual §9) | Rule |
|---|---|
| Critical | Closed before acceptance |
| High | Closed, or approved documented workaround |
| Medium / Low | Stays visible in this register |

## Register

| ID | Title | AC | Severity | Owner | Status |
|---|---|---|---|---|---|
| QA-001 | Workspace renders for unauthenticated users via hardcoded demo user | M1-AC1, M1-AC2 | High | Priyanka | New |
| QA-002 | `frontend/.gitignore` pattern `.env*` also ignores `.env.example` | M1-AC6 | Low | Ajendra | New |

### QA-001 — Workspace renders for unauthenticated users via hardcoded demo user

- **Environment:** `main` @ `33f337b`, `next build && next start`, no backend.
- **Steps:** 1. With no session, open `/dashboard` (or any `(workspace)` route). 2. Alternatively, open `/login` and click **Explore with Demo Session**.
- **Expected:** `/api/v1/auth/me/` fails → the user is sent to `/login?next=/dashboard` (ARCHITECTURE §7: "a 401 there means show login"; M1-AC2).
- **Actual:** `frontend/src/app/(workspace)/layout.tsx` falls back to `FALLBACK_DEMO_USER` on any error and renders the workspace with `commercial_analyst` navigation and a "Frontend Standalone Mode" banner. `login/page.tsx` seeds the same fake user into the query cache without calling the backend. The fake user reuses a team member's name and an internal-looking address.
- **Impact:** No data is exposed by itself (the backend remains the authority), but the UI auth guard is bypassed, role-aware navigation (M1-AC1) is shown for a role the user does not hold, and auth failures are masked during Gate 1 testing.
- **Suggested fix (owner decides):** remove the fallback user and demo button, or gate them behind an explicit dev-only flag that is off in builds; redirect to login on 401 from `/auth/me/`.
- **Test:** `e2e/tests/auth.spec.ts` (marked `test.fail` with this ID until fixed).

### QA-002 — `frontend/.gitignore` pattern `.env*` also ignores `.env.example`

- **Expected:** secrets baseline `.env`, `.env.*`, `!.env.example` (AGENTS.md §C2).
- **Actual:** `frontend/.gitignore` has `.env*` with no `!.env.example` exception, so a frontend `.env.example` would be silently ignored. No root `.gitignore` exists.
- **Impact:** Low. No secret is exposed; documented configuration could go missing.
