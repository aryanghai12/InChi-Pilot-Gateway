# Clean QA candidate verification

Date: 16 November 2026. Branch: `qa/week1-3-delivery`. Base and current HEAD: `e89ab65c8d07848c6bb30d06dc5d826978138b70` (origin/main). QA additions are staged for review only; no commit exists yet. Product source/manifests are unchanged.

## New worktree execution

Command from this worktree: `.venv/Scripts/python.exe e2e/scripts/local-qa.py --evidence-dir .cache/qa-clean-verification`.

| Suite/check | Actual result |
|---|---|
| Existing backend tests | 22 passed |
| QA backend controls | 5 passed, 1 failed: QA-005 JSON error contract |
| Database model/seed tests | 5 passed |
| Frontend unit tests | 15 passed |
| QA configuration | 6 passed |
| Full public Playwright suite | **44 passed, 8 failed, 0 skipped, 0 flaky** across 52 cases |
| Frontend/QA TypeScript, production build, preflight | Pass |
| Backend system check and migration drift | Pass |
| Frontend clean-install dry run | Fail: override/lock mismatch |
| Frontend lint | Fail: 36 errors, 5 warnings |

This is one complete 52-case run, not the earlier combined ledger. Eight public failures remain: QA-001 (four route cases), QA-003 (one currency case), QA-005 (two CSRF contract cases), QA-006 (one JSON 404 case). Tests execute correctly and leave real product failures visible. M4 remains Blocked; remote CI/UAT and a complete secrets scan are not claimed.

[Reviewed structured results](../evidence/delivery/clean-worktree-results.json) include exact runtime versions, check exit codes and cleanup. Raw logs/JSON/JUnit/traces remain in ignored `.cache/qa-clean-verification` or ignored Playwright output directories and are excluded from the proposed commit. The older [historical sanitized record](../execution-2026-11-16-integrated.md) is separate evidence.

Used a new virtual environment, an independent frontend dependency tree and separate ignored browser runtime copies. The known clean-lock conflict required `npm install --no-save --package-lock=false --ignore-scripts --no-audit --no-fund`; no product manifest changed. Dependency versions are recorded in the structured results. PostgreSQL 17 + pgvector ran under the isolated QA Compose project with tmpfs data. Cleanup removed that project and closed all three loopback ports.

## History and disclosure checks

The candidate worktree was created directly from origin/main. No commits from the original QA branch were merged, rebased or cherry-picked. Restricted commits are not ancestors of the new branch. Their identified QA blob versions and known restricted disclosure markers are absent from candidate additions. The shared local Git object database still retains original private work; that does not make it reachable from the clean branch.

Only QA/framework source, safe test CI, planning/traceability/defect records, public drafts and structured summaries are allowlisted. Confidential reports/diagnostics, restricted mechanics, historical/raw machine output, credentials, caches and generated files are excluded. Targeted credential/disclosure checks are not a complete secret scan. The proposed commit's files are listed exactly in [commit-files.json](commit-files.json).

Preservation check passed: the original test ref, original index hash and all 293 tracked/untracked file-content hashes match the pre-worktree snapshot; no original working file changed. No original checkout file is used as a writable runtime dependency. A future push must select only this delivery branch; pushing all local branches could publish excluded history. No commit, push, issue or PR was made.

## Approval blockers and next action

Product owners must fix QA-001/003/005/006, frontend lock/lint blockers and the readiness dependencies. These do not prevent reviewing a QA-only commit, but prevent green release/acceptance claims. After staged review, obtain commit approval using the prepared message. Publication and a Draft PR require separate approval. No product fixes are included.
