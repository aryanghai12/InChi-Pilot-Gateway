# Draft PR: Deliver Week 1-3 QA automation and verified evidence

Base: `main` | Head: `qa/week1-3-delivery` | Draft text only; no PR opened.

Requirement: M1-AC2/3/4, M2-AC1/2/7, M3-AC1/2, M10-AC2, M11-AC2. Public issue drafts are prepared; issue URLs pending submission.

What changed: Add the complete existing Playwright framework, QA backend controls, browser/API/permission regression, a disposable PostgreSQL 17 local runner and test CI. Update traceability and reviewed evidence. This candidate is based directly on main and excludes the original QA branch history and restricted material. Product code is unchanged.

Tests run: On this clean worktree, backend 22 passed; database 5 passed; frontend 15 passed; QA configuration 6 passed; QA backend controls 5 passed/1 failed; full public Playwright 44 passed/8 failed (52 cases, no skips/flaky). Build/typechecks passed. Lint and clean install fail on existing owner-controlled blockers. [Verification](verification.md) records details; no green acceptance claim is made.

Not tested / known limitations: Readiness API/schema and D-03 remain Blocked; D-09 permissions provisional. Clean frontend installation/lint require owner fixes. Remote CI, UAT and complete secret scanning are not claimed. Restricted coverage is maintained separately.

Assumptions or UNAPPROVED placeholders: existing D-09 provisional permissions; D-03 pending.

Interfaces affected (and owners notified): test CI uses existing backend/database requirements. No product contract change; no notifications sent.

Reviewers: Aryan, Priyanka, Abhishek, Vishal, Ajendra.
