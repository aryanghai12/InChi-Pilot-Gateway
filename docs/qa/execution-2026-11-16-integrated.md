# Integrated QA execution — sanitized delivery record

Owner: Harish Pal · Executed: 16 November 2026 · Source: `test@a7cc398` plus QA-only working-tree changes.

The merge preserves prior QA work and includes GitHub main `e89ab65`. No branch/history operation, product-code change, commit or push was performed during verification. Historical pre-integration results are preserved separately. Restricted security details and raw machine reports are deliberately excluded from this public record.

## Actual results

| Suite/check | Result | Reviewed evidence |
|---|---|---|
| Existing backend | 22 passed | [output](evidence/delivery/sanitized-results.json) |
| QA backend controls | 5 passed, 1 failed (QA-005) | [output](evidence/delivery/sanitized-results.json) |
| Database model/seed tests | 5 passed | [output](evidence/delivery/sanitized-results.json) |
| Frontend unit | 15 passed | [output](evidence/delivery/sanitized-results.json) |
| QA configuration | 6 passed | [output](evidence/delivery/sanitized-results.json) |
| Frontend build/typecheck | Pass | [build](evidence/delivery/sanitized-results.json), [typecheck](evidence/delivery/sanitized-results.json) |
| Backend check/migration drift | Pass | [check](evidence/delivery/sanitized-results.json), [drift](evidence/delivery/sanitized-results.json) |
| Frontend lint | Fail: 36 errors, 5 warnings | [output](evidence/delivery/sanitized-results.json) |
| Clean frontend install | Fail: lock/override mismatch | [output](evidence/delivery/sanitized-results.json) |
| Latest public Playwright outcomes | 44 passed, 8 failed, 0 skipped, across 52 distinct public cases | [sanitized summary](evidence/delivery/sanitized-results.json) |

The Playwright row takes the latest observed result per public case across the original full run and focused retest. It is **not a single complete 52-case run**. A repaired alert locator passed on retest. Eight public failures map to QA-001 (four routes), QA-003 (one), QA-005 (two), QA-006 (one). One restricted case was present in the original 53-case collection; it and its execution evidence are now withheld from the public source/collection and maintained confidentially. No historical execution result was invented or silently converted to Pass. Delivery preparation rechecks collection/type safety/configuration; it does not claim a new application execution.

Delivery preparation checks passed: [52-case discovery](evidence/delivery/sanitized-results.json), [six configuration checks](evidence/delivery/sanitized-results.json), and [strict TypeScript](evidence/delivery/sanitized-results.json). These checks occurred after withholding the restricted case; they are distinct from the historical application executions.

## Environment and limits

Used Python 3.12, Node 22.19.0, disposable PostgreSQL 17.12 with pgvector 0.8.7, a built Next.js frontend and unchanged Django backend. The QA Compose project used tmpfs storage and loopback ports; both runs removed their own resources. [Database version](evidence/delivery/sanitized-results.json), [cleanup](evidence/delivery/sanitized-results.json), [Python versions](evidence/delivery/sanitized-results.json), [Node versions](evidence/delivery/sanitized-results.json).

`npm ci` cannot reproduce the current lock because tinypool 1.1.1 conflicts with the manifest override. Temporary local installation used `npm install --no-save --package-lock=false --ignore-scripts --no-audit --no-fund`. Actual Next 16.4.6 and tinypool 2.2.0 differ from locked 16.4.3/1.1.1; [differences](evidence/delivery/sanitized-results.json). Both tracked manifests remained unchanged. These are manifest-compatible local results, not clean-lock evidence.

M4 readiness backend workflow/API/schema and D-03 approval remain Blocked; D-09 permissions remain UNAPPROVED. Complete audit-event content, full seed reconciliation, remote CI, secrets scanning and acceptance/UAT remain Not Run or explicit coverage gaps. The confidential security record is handled separately and is not linked to a public reproduction.

## Delivery and next execution

QA changes add six backend controls, two browser workflow tests and seven route checks, repair the locator, and integrate existing database requirements/tests into test CI. The restricted case/diagnostic is excluded from public delivery without weakening the remaining assertions. Product files are unchanged.

Public issue drafts and the Draft PR description are in [delivery drafts](delivery/README.md). Their evidence is limited to reviewed files in `evidence/delivery/`; raw reports, traces, browser storage, local caches and the confidential report must not be staged. The clean delivery worktree is based only on origin/main; its own ancestry and candidate files are verified separately before approval. Historical results above do not imply transfer of the original branch history.

After owners fix public defects and CI blockers, run clean dependency installation and `.venv/Scripts/python.exe e2e/scripts/local-qa.py --evidence-dir <new directory>`. Use `--phase browser-retest` only for auth/workspace retests against an existing build. The runner creates synthetic accounts in an isolated test database and removes its own stack. No external publication is authorized by this record.
