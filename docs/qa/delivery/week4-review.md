# Week 4 review and commit preparation

Branch: `qa/week4-demand-readiness-boundaries`; base `e4e320dcf8bb23f267e8450c77a109981832adc0`. No commit, push, issue or PR created. Product files and `test` are unchanged.

## Actionable review result

Final runner: **116 passed, 17 failed, 10 Blocked, 0 errors**. New Week 4 cases: 90 passed, 17 failed, 8 Blocked. Existing regression: 26 passed, 2 PostgreSQL-only Blocked. Lint, formatting, YAML parsing and whitespace checks pass. CI explicitly collects `../e2e/backend/test_week4_workflows.py`; the local runner also collects it. The application CI job will fail on the retained product regressions; this is a Draft review contribution, not a green acceptance claim.

The earlier 19-failure/five-defect claim is corrected. W4-04's two fixtures only describe evidence as mandatory in prose and cannot establish its applicability through an agreed API contract. They remain Blocked with assertions retained; no issue is proposed for publication. The other 17 failures are ordinary failing assertions with successful authorized/validation controls, and map exactly to four independent product findings:

| Finding | Failing cases | GitHub disposition |
|---|---:|---|
| W4-01 readiness protected fields/actor spoofing | 6 | New; related protected-field pattern to #86, distinct readiness resource; audit work belongs to #87 |
| W4-02 review source-state enforcement | 8 | New; no duplicate |
| W4-03 missing referenced Evidence record | 1 | New; separate from #86 registry verification |
| W4-05 missing buyer specification readiness gate | 2 | New; closed #60 is product pricing/currency, not this gate |

Current open/closed issue inventory was fetched on 23 November and reviewed (14 non-PR issues); sanitized titles/states/URLs are in [environment.json](../evidence/week4/environment.json). Issue drafts use only synthetic repro data. No raw logs/JUnit, credential values, real personal/commercial data, dependency caches or public issue-response bodies belong in the commit. No unnecessary product/dependency files are included.

## Exact commit file list (12 files)

```text
.github/workflows/ci.yml
docs/qa/defects.md
docs/qa/delivery/week4-review.md
docs/qa/evidence/week4/environment.json
docs/qa/evidence/week4/summary.json
docs/qa/execution-2026-11-23-week4.md
docs/qa/traceability.md
docs/qa/week4-issue-drafts.md
e2e/README.md
e2e/backend/test_week4_workflows.py
e2e/scripts/local-qa.py
e2e/scripts/week4-qa.py
```

Commit message:

```text
test(qa): cover Week 4 readiness and demand boundaries
```

## Draft PR text

Title: `test(qa): Week 4 readiness and buyer-demand boundaries`

```markdown
Requirement: M4-AC1–AC6, M5-AC1–AC5 (partial/Blocked coverage documented), M11-AC2. Findings W4-01/02/03/05: docs/qa/week4-issue-drafts.md; new issues pending authorization. Related existing issues: https://github.com/aryanghai12/InChi-Pilot-Gateway/issues/86 and https://github.com/aryanghai12/InChi-Pilot-Gateway/issues/87.

What changed: Add M4/M5 API boundary, workflow, permission and persistence tests, an isolated runner, CI collection and sanitized traceability/evidence. Product regressions remain ordinary failures. Final review moves two W4-04 cases to Blocked because mandatory evidence applicability has no agreed API contract.

Tests run (command → actual result):
- `.cache/week4-venv/Scripts/python.exe e2e/scripts/week4-qa.py` → 116 passed, 17 failed, 10 Blocked, 0 errors; exit 1 on disposable SQLite. New Week 4 cases: 90/17/8.
- Ruff check and format check for the two new Python files → passed.
- CI YAML parse; `git diff --check` → passed.

Not tested / known limitations: PostgreSQL/browser execution and missing contracts remain Blocked; no Gate 2 acceptance. CI collects the new tests and will remain red on four confirmed product findings (6 + 8 + 1 + 2 cases). GitHub CI has not executed this uncommitted contribution.

Assumptions or UNAPPROVED placeholders used: Current three-role/category/unit fixtures characterize existing behavior; they do not approve D-22/D-23 deviations. W4-04 is a blocked scenario, not a confirmed defect.

Interfaces affected (and owners notified): No API/schema change; backend CI and local QA collection extended. No notifications sent; Abhishek/Ajendra review requested when the PR is authorized.

Reviewers: Abhishek (API/workflow), Ajendra (permissions/evidence). Vishal consulted if storage semantics require clarification; Aryan for triage.
```

## Exact next steps

1. Review these 12 files and approve the local commit when ready; stage only this list, not caches or raw evidence.
2. After separate publication authorization, submit W4-01/02/03/05 from the sanitized drafts and add their issue links to the PR description. Keep W4-04 Blocked until its contract is agreed.
3. After push/PR authorization, open a Draft PR against `main` with the text above and the named reviewers. Do not mark it merge-ready while its product regressions fail.
