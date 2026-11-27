# Week 4 issue drafts - not submitted

Reproduced 23 November 2026 on `main@e4e320d` plus uncommitted QA tests, Python 3.12, Django/DRF and disposable SQLite. All data is synthetic. Run from `backend/` with the isolated environment variables set by `e2e/scripts/week4-qa.py`; the full reproducible command from repository root is:

```powershell
.cache/week4-venv/Scripts/python.exe e2e/scripts/week4-qa.py
```

Sanitized evidence: [summary](evidence/week4/summary.json); [execution and limitations](execution-2026-11-23-week4.md). The common runner above reproduces every proposed issue; test-name selectors below identify exact cases in its output. Four drafts propose High severity; owner Abhishek, data support Vishal, security review Ajendra, triage Aryan. Ownership is a coordination proposal, not a notification or accepted assignment.

GitHub REST issue inventory was rechecked during final review on 23 November: all 14 non-PR issues returned (open and closed). Open #83-#87 cover anonymous onboarding, admin passwords, user deletion, registry evidence verification and audit completeness; closed issues #48/49/58-64 concern pagination/authentication and earlier QA findings. No existing issue describes W4-01/02/03/05. The sanitized inventory is recorded in [environment.json](evidence/week4/environment.json). No issue was created.

| Finding | Duplicate/related issue | Publication disposition |
|---|---|---|
| W4-01 | Related to [#86](https://github.com/aryanghai12/InChi-Pilot-Gateway/issues/86): writable protected fields, but different model/action. Audit effects belong to [#87](https://github.com/aryanghai12/InChi-Pilot-Gateway/issues/87). | New readiness authorization defect; draft below |
| W4-02 | No duplicate; #87 covers audit content, not source-state validation | New workflow defect; draft below |
| W4-03 | Related evidence area to #86; missing assessment Evidence linkage is a separate submission gate | New gate defect; draft below |
| W4-04 | Related evidence area to #86; mandatory applicability cannot be established by current fixture contract | **Blocked; no issue draft for publication** |
| W4-05 | No duplicate; closed #60 concerns product pricing/currency, not demand specifications | New demand gate defect; draft below |

## W4-01: Analyst can bypass readiness review and forge workflow identities

Requirement: M4-AC2, M4-AC3, M4-AC5; v2.2 sections 4, 8.1, 14.1.

Reproduction: authenticate an existing synthetic commercial analyst; create a Draft assessment; PATCH its detail URL with each of `readiness_outcome=ready_for_matching`, `outcome=ready_for_matching`, `workflow_state=review_complete`, `status=review_complete`, or another synthetic user's ID in `submitted_by`/`reviewer`. Reload the record.

Actual: six requests return 200 and unauthorized field values persist. Expected: plain source-data edits cannot set reviewer outcomes, bypass workflow gates or forge workflow actors; rejecting or ignoring protected fields must preserve authoritative state.

Evidence/selectors: `analyst_cannot_bypass_review_with_patch` (4 failures), `analyst_cannot_forge_workflow_actors` (2 failures). Keep both aliases protected. Dedicated review/self-review role tests already pass, demonstrating why field-level protection is also necessary. Owner fix should cover create and update paths without weakening review permissions.

Acceptance: all six regressions pass; valid source edits and permitted review actions continue to pass. Audit remediation belongs with existing [#87](https://github.com/aryanghai12/InChi-Pilot-Gateway/issues/87), not another audit issue.

## W4-02: Readiness review actions accept invalid source states

Requirement: M4-AC3/4; v2.2 section 8.1.

Reproduction: set up a synthetic assessment in each of Draft, Submitted, Review Complete and Archived; as Reviewer POST `complete-review/` with a valid outcome/reason, or `request-information/` with valid request notes.

Actual: all eight combinations return 200. Expected: only Under Review is a valid source for these actions; invalid transitions must return a client error and preserve state/version. This is separate from assignment API absence, which remains Blocked.

Evidence/selector: `review_actions_require_under_review_state` (8 failures). Positive Under Review action tests pass. Acceptance: invalid transitions reject without mutation, and valid actions remain functional.

## W4-03: Assessment submission accepts a document without an Evidence record

Requirement: M4-AC1; v2.2 section 6.1.

Reproduction: provide section 6.1 answers, a linked Product and confirmed CR-18; in CR-13 reference `missing-report` with a condition, but create no AssessmentEvidence record; POST `submit/` as Analyst.

Actual: 200. Expected: 400 with an actionable document blocker; no submission/version change. A condition string inside answer JSON does not establish the required Evidence record.

Evidence/selector: `gate_requires_referenced_evidence_record` (1 failure). Acceptance: missing referenced evidence blocks submission; explicit `None` (no documents) and valid linked evidence cases remain distinct.

## W4-04: Blocked contract check - do not publish as a confirmed defect

The two `unresolved_mandatory_evidence_blocks_ready` fixtures describe the report as mandatory only in prose. `AssessmentEvidence` and the agreed assessment API expose no machine-readable mandatory applicability contract. An Expired/Discrepancy condition alone does not establish that this document is mandatory. The earlier HTTP 200 observations are retained in ignored historical raw evidence, but do not prove a violation of AC-07/08. Both cases now explicitly skip as Blocked with assertions retained for future activation after Adrika/Abhishek agree the applicability contract. No schema, API or product rule is added in this QA contribution.

## W4-05: Buyer requirement becomes ready without a product specification

Requirement: M5-AC2; v2.2 AC-11 and section 8.2.

Reproduction: create a Draft buyer requirement with current category/unit values, positive quantity, market, delivery location and a mandatory criterion; leave `product_specifications` blank. Try both POST `mark-ready/` and PATCH detail with `requirement_status=ready_for_matching` on independent records.

Actual: both requests return 200. Expected: reject readiness with a specification field blocker and keep the requirement Draft. No new commercial rule or criteria vocabulary is needed for this finalized completeness requirement.

Evidence/selector: `ready_gate_cannot_be_bypassed` with `product_specifications` (2 failures). Acceptance: both paths reject incomplete specifications and the valid create/ready/close test continues to pass.
