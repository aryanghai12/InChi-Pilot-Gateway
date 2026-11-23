# Week 4 boundary, workflow and permission execution

Owner: Harish Pal (QA). Responsibility window: 16-20 November 2026. Actual execution: **23 November 2026**; this is not backdated sprint-review evidence.

Branch: `qa/week4-demand-readiness-boundaries`, created from verified GitHub main `e4e320dcf8bb23f267e8450c77a109981832adc0`. Tests/configuration are uncommitted changes on that base. `test` was not modified. No product code, commits, pushes, issues or PRs were created.

## Execution

From the repository root, using an isolated Python 3.12 virtual environment with the repository's existing `backend/requirements-dev.txt`:

```powershell
.cache/week4-venv/Scripts/python.exe e2e/scripts/week4-qa.py
```

The runner disables dotenv, generates a signing key in memory, uses pytest-django's disposable in-memory SQLite test database, and runs actual Django URLs/middleware/session authentication through DRF APIClient. Each test rolls back its synthetic users and records. This is backend API integration evidence, not browser/proxy or PostgreSQL acceptance. No shared database or live application server is used.

| Suite | Passed | Failed | Blocked/skipped | Errors |
|---|---:|---:|---:|---:|
| New Week 4 tests (`e2e/backend/test_week4_workflows.py`) | 90 | 17 | 8 | 0 |
| Existing accounts | 9 | 0 | 0 | 0 |
| Existing registry | 13 | 0 | 0 | 0 |
| Existing QA backend controls | 4 | 0 | 2 | 0 |
| **Total** | **116** | **17** | **10** | **0** |

Exit code **1** is retained because product assertions fail. There are no xfails. Six explicit blocked cases document absent contracts; two further AC-07/08 cases are Blocked because their fixtures establish mandatory evidence only in prose. No supported product assertion was relaxed. Two existing raw-SQL audit-trigger cases skip because they require PostgreSQL.

Sanitized per-case results: [summary.json](evidence/week4/summary.json). Environment versions, source hashes, failure grouping and current issue inventory: [environment.json](evidence/week4/environment.json). Final-review raw logs/JUnit remain ignored in `.cache/qa-week4/20261123T074848Z/`. The final runner returned exit 1 in 61.70 seconds.

Initial run: 102 passed / 21 failed / 8 skipped. Four failures were a QA fixture string-versus-Decimal comparison after database reload, fixed by reloading the fixture before comparisons. The next run added 12 cases and returned 116 passed / 19 failed / 8 skipped. Final review established that W4-04's two cases could not prove mandatory evidence applicability from a free-text fixture; they are now Blocked with assertions retained. This corrects the earlier five-confirmed-defect claim to four. Historical raw evidence remains ignored; the linked sanitized summary records the final runner execution.

## Confirmed product failures

| Local ID | Cases | Observed result | Expected baseline behavior |
|---|---:|---|---|
| W4-01 | 6 | Analyst PATCH persists outcome/status aliases and forged submitted-by/reviewer identities; HTTP 200 | Reviewer outcome and workflow identities cannot be supplied by an unauthorized source-data edit (M4-AC2/3/5) |
| W4-02 | 8 | Reviewer complete-review/request-information returns 200 from Draft, Submitted, Review Complete and Archived | v2.2 section 8.1 permits these actions from Under Review; reject invalid source states without mutation |
| W4-03 | 1 | Submit returns 200 when CR-13 references a document with no Evidence record | Section 6.1 requires every referenced document to have an Evidence record and condition |
| W4-05 | 2 | Both mark-ready and direct status PATCH return 200 with blank product specifications | Section 8.2 and M5-AC2 require specification completeness before Ready for Matching |

These four findings are High proposed severity, owned by Abhishek for API enforcement, with Vishal for any storage changes and Ajendra reviewing access-control findings. W4-04 remains a blocked applicability check, not a publishable defect. Drafts, duplicate-check results and reproduction command: [week4-issue-drafts.md](week4-issue-drafts.md). No owner was messaged and no review or assignment acceptance is claimed.

## Coverage and limits

Passing cases cover all 16 section 6.1 required-answer omissions; blank/null response and CR-18 boundaries; product linkage; valid submission and allowed reviewer actions; blank reviewer reasons and self-review denial; evidence default/invalid conditions; buyer quantity precision/range, price ordering and date ordering; required-field readiness failures; demand create/ready/close persistence and audit existence; stale PATCH 409 conflicts; current-role denials; anonymous requests; CSRF; and information-request/resubmission note retention.

Current three-role policy tests are explicitly characterization, not five-role acceptance. Demand fixtures use current `Engineering Goods`/`PIECES` compatibility values; this does not approve them under D-23. Omission tests follow the explicit section 6.1 list. The questionnaire lists CR-05 as required while section 6.1 omits it; CR-03/11 also have applicability conditions. Broader applicability checks need an agreed schema rather than invented rules. Persistence of current records and notes does not prove immutable history or complete audit diffs.

Blocked: mandatory assessment evidence applicability (W4-04), Contributor/Viewer matrix (D-22), immutable assessment/requirement history and match-run references, assignment/reassessment/archive action contracts, active approved criteria/reference API (D-23), and SEC-03's undefined record-access boundary. Deterministic matching/rule-approval acceptance remains dependent on D-21 and the missing integrated match-run API; no weighted/semantic tests were added. Gate 2's approver/outcome remains unrecorded.

Infrastructure: `docker info` reports the Docker Desktop Linux engine pipe absent. PostgreSQL and live full-stack/browser execution are blocked; frontend/E2E dependencies and browsers are not installed. No infrastructure or product dependency repair was attempted. SQLite cannot prove PostgreSQL constraints/triggers or concurrency behavior. The existing local Compose runner and CI now collect this Week 4 file when their infrastructure is available. GitHub CI has not run these uncommitted changes.

Final QA checks actually run:

```text
python -m ruff check e2e/backend/test_week4_workflows.py e2e/scripts/week4-qa.py -> All checks passed
python -m ruff format --check e2e/backend/test_week4_workflows.py e2e/scripts/week4-qa.py -> 2 files already formatted
git diff --check -> exit 0
python -c "import yaml,pathlib; yaml.safe_load(pathlib.Path('.github/workflows/ci.yml').read_text())" -> parsed successfully
```

The final run emitted 132 WhiteNoise warnings because `backend/staticfiles/` is absent in this backend-only environment; no static UI behavior is claimed. Tests alone do not approve the Rule Approval Gate or the pilot. Final review verified every remaining failing case maps to W4-01/02/03/05, retained ordinary failing assertions, and excluded W4-04 from confirmed defects. Commit candidates contain only synthetic test data and sanitized result metadata; raw outputs, credentials and issue-response bodies remain ignored. See [review/commit preparation](delivery/week4-review.md) for the exact file list and Draft PR text.
