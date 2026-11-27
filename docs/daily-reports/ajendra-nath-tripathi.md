# Weekly reports — Ajendra Nath Tripathi

Cybersecurity and DevSecOps Engineer. Process, template and rules: [README.md](README.md)

Only Ajendra Nath Tripathi writes in this file. Newest report first.

<!-- Add new reports directly below this line. -->

## Week 5 - 23-27 November 2026

_Recorded on 23 November 2026._

**Completed**
- Authored Matching & AI Threat Review covering input manipulation, unredacted logging, and match-review RBAC - drafted - evidence: [`docs/security/MATCHING_THREAT_REVIEW.md`](../security/MATCHING_THREAT_REVIEW.md)
- Conducted security and license audit of embedding model candidate `sentence-transformers/all-MiniLM-L6-v2` under D-11 (Apache 2.0 verified, `trust_remote_code=False` enforced, offline execution guaranteed) - drafted - evidence: [`docs/security/MATCHING_THREAT_REVIEW.md`](../security/MATCHING_THREAT_REVIEW.md) §4
- Formally resolved and implemented Login Throttling (TD-04) via DRF `ScopedRateThrottle` (`5/minute` on `/api/v1/auth/login/`) with uniform HTTP 429 error mapping - resolved - evidence: [`docs/security/LOGIN_THROTTLING_DECISION_TD04.md`](../security/LOGIN_THROTTLING_DECISION_TD04.md), [`backend/config/settings.py`](../../backend/config/settings.py)
- Verified zero external LLM dependencies and zero network telemetry across matching engine (D-20 / Baseline v2.2 §14.2) - drafted - evidence: [`docs/security/MATCHING_THREAT_REVIEW.md`](../security/MATCHING_THREAT_REVIEW.md) §5
- Expanded automated negative security test suite to 19 tests in `test_security_posture.py` covering TD-04 rate limit semantics, match disposition Reviewer exclusivity, and LLM absence - drafted - evidence: [`backend/apps/accounts/tests/test_security_posture.py`](../../backend/apps/accounts/tests/test_security_posture.py)

**Meetings, reviews and coordination**
- Coordinated with Alok Tiwari (AI Lead) on embedding model security constraints (offline weights, CPU-only execution, D-11).
- Coordinated with Abhishek Kumar on login rate limiting (TD-04) and match disposition permissions.
- Reviewed Aryan Ghai's Week 5 integration plan and logged TD-04 resolution.

**In progress**
- Monitoring upcoming backend integration of MatchRun and MatchResult models for audit and version consistency (AC-18).

**Tests and validation**
- `cd backend; .\.venv\Scripts\python.exe -m pytest apps\accounts\tests\test_security_posture.py --ds=config.settings -v` -> 19 passed, 0 failed, 13 warnings in 49.93s.
- `python manage.py check` (backend) -> `System check identified no issues (0 silenced)`.
- Static code audit of `ai_matching/` -> confirmed zero generative LLM packages or external HTTP client calls.

**Blocked, dependencies and decisions needed**
- AUD-01 (Critical: Anonymous registration as platform_admin) - waiting on Abhishek Kumar for remediation - since 2026-11-21 - blocks Gate 4.
- D-21 (Deterministic rules-only matching approach) - waiting on BNCS and mentor - since 2026-11-21 - blocks Week 5 matching integration.
- D-22 (Five-role RBAC ratification) - waiting on BNCS via Aryan - since 2026-11-21.

**Next week**
- Week 6: Security regression and configuration lock. Review the security headers set in `next.config.ts`, Docker Compose reference environment, and backup protection.
- Staging checklist execution upon provision of hosted staging (D-16).


## Week 4 - 16-20 November 2026

_Recorded on 23 November 2026._

**Completed**
- Executed comprehensive security posture review for Gate 2 and updated STRIDE threat model to incorporate Baseline v2.2 §14.3 threat-focused specifications - drafted - evidence: [`docs/security/THREAT_MODEL.md`](../security/THREAT_MODEL.md)
- Implemented and validated 16 automated negative security and RBAC posture tests covering 401/403 semantics, two-person assessment review rule (AC-06), platform admin isolation, audit immutability, and serializer secret masking - drafted - evidence: [`backend/apps/accounts/tests/test_security_posture.py`](../../backend/apps/accounts/tests/test_security_posture.py)
- Completed Security Headers and Container Hardening Review covering Next.js edge headers and CIS Docker benchmarks - drafted - evidence: [`docs/security/SECURITY_HEADERS_AND_CONTAINER_REVIEW.md`](../security/SECURITY_HEADERS_AND_CONTAINER_REVIEW.md)
- Realigned Access Control Matrix with Baseline v2.2 5-role taxonomy and mapped transition under Decision D-22 - drafted - evidence: [`docs/security/ACCESS_CONTROL_MATRIX.md`](../security/ACCESS_CONTROL_MATRIX.md)
- Triaged and logged Critical defect AUD-01 (anonymous self-registration / privilege escalation) and High defect AUD-15 (admin plaintext passwords) in remediation ledger - drafted - evidence: [`docs/security/REMEDIATION_REGISTER.md`](../security/REMEDIATION_REGISTER.md)
- Aligned Security & Negative Test Specifications with Baseline v2.2 acceptance criteria (AC-06, AC-19, AC-22, AC-23) - drafted - evidence: [`docs/security/SECURITY_TEST_SPECIFICATIONS.md`](../security/SECURITY_TEST_SPECIFICATIONS.md)

**Meetings, reviews and coordination**
- Participated in Gate 2 sprint review on 20 Nov 2026; confirmed security review status and identified D-22 role divergence against Baseline v2.2 §4.2.
- Escalated Critical finding AUD-01 to Abhishek Kumar (Backend lead) and Aryan Ghai (Coordination). Provided failing reproduction test and remediation specification.
- Coordinated with Harish Pal (QA) on integrating negative security test fixtures into CI automation.

**In progress**
- Validation of Abhishek's upcoming remediation patch for AUD-01 (anonymous registration removal) and AUD-15 (admin password hashing).

**Tests and validation**
- `cd backend; .\.venv\Scripts\python.exe -m pytest apps\accounts\tests\test_security_posture.py --ds=config.settings -v` -> 16 passed, 0 failed, 13 warnings in 41.24s.
- `python manage.py check` (backend) -> `System check identified no issues (0 silenced)`.
- Automated secret scan -> verified zero plaintext secrets committed across repository.

**Blocked, dependencies and decisions needed**
- AUD-01 (Critical: Anonymous registration as platform_admin) - waiting on Abhishek Kumar for remediation - since 2026-11-21 - blocks Gate 4.
- D-22 (Five-role RBAC ratification) - waiting on BNCS via Aryan - since 2026-11-21 - tracked in decision register.
- D-21 (Deterministic rules-only matching approach) - waiting on BNCS and mentor - since 2026-11-21 - blocks Week 5 matching integration.

**Next week**
- Week 5: Validate and retest AUD-01 and AUD-15 fixes upon submission by Abhishek.
- Review deterministic matching engine input sanitization and verify no LLM/external dependencies are introduced (D-20).

## Week 3 - 9-13 November 2026

_Recorded late on 23 November 2026._

**Completed**
- Conducted security review of Supplier & Product registry schemas (M2/M3) and confirmed metadata-only evidence model (D-10) - drafted - evidence: [`docs/security/DATA_CLASSIFICATION.md`](../security/DATA_CLASSIFICATION.md)
- Evaluated Docker Compose container configurations and non-root user execution (`USER inchi:1001` in backend, `USER nextjs:1001` in frontend) - drafted - evidence: [`docs/security/SECURITY_HEADERS_AND_CONTAINER_REVIEW.md`](../security/SECURITY_HEADERS_AND_CONTAINER_REVIEW.md)
- Formulated negative test specifications for M2/M3 commercial data isolation (preventing platform_admin from editing suppliers/products) - drafted - evidence: [`docs/security/SECURITY_TEST_SPECIFICATIONS.md`](../security/SECURITY_TEST_SPECIFICATIONS.md)

**Meetings, reviews and coordination**
- Reviewed Vishal's `AuditEvent` model and PostgreSQL immutability trigger migration (`TD-03`).
- Coordinated with Priyanka on Next.js `rewrites()` edge proxying and `BACKEND_ORIGIN` configuration (`TD-09`).

**In progress**
- Assessment workflow (M4) and buyer requirement (M5) security and permission boundary review.

**Tests and validation**
- `git status` -> confirmed no sensitive `.env` files or credentials committed.
- CI security workflow verification -> `.github/workflows/security.yml` passed dependency checks (`pip-audit`, `npm audit`) and `gitleaks`.

**Blocked, dependencies and decisions needed**
- D-09 (RBAC Matrix approval) - waiting on BNCS via Aryan - since 2026-10-26 - active under interim baseline.
- D-10 (File upload exclusion) - resolved as metadata-only in Week 3.

**Next week**
- Perform security and workflow state transition review for China Readiness (M4) and Buyer Requirements (M5).
- Prepare security evaluation pack for Gate 2 review on 20 November 2026.


## Week 2 - 2-6 November 2026

_Recorded on 9 November 2026._

**Completed**
- Authored canonical root `.env.example` defining sanitized environment variables across Django, FastAPI, Next.js, and PostgreSQL - drafted - evidence: [`.env.example`](../../.env.example)
- Created automated negative security test specifications and Pytest reference implementation covering CSRF, RBAC, IDOR, and audit immutability - drafted - evidence: [`docs/security/SECURITY_TEST_SPECIFICATIONS.md`](../security/SECURITY_TEST_SPECIFICATIONS.md)
- Conducted security headers and container hardening review for Next.js CSP and Docker CIS benchmarks - drafted - evidence: [`docs/security/SECURITY_HEADERS_AND_CONTAINER_REVIEW.md`](../security/SECURITY_HEADERS_AND_CONTAINER_REVIEW.md)
- Established DevSecOps CI automation workflow including Gitleaks secret scanning, frontend `npm audit`, backend `pip-audit`, and Bandit SAST - drafted - evidence: [`.github/workflows/security.yml`](../../.github/workflows/security.yml)
- Configured automated multi-ecosystem dependency monitoring - drafted - evidence: [`.github/dependabot.yml`](../../.github/dependabot.yml)

**Meetings, reviews and coordination**
- Coordinated with Abhishek on Django authentication, CSRF token bootstrap (`TD-05`), session key rotation, and 401/403 semantics (`TD-06`).
- Coordinated with Harish on negative security test cases and automated Pytest execution plan.
- Coordinated with Priyanka on Next.js security headers and frontend Dockerfile non-root configuration.

**In progress**
- Verify Abhishek's merged `backend/apps/accounts/` implementation against `AUTH_THREAT_REVIEW.md` requirements - Gate 1 / TD-05 / TD-08.

**Tests and validation**
- `git status` -> verified tracked files and confirmed zero plaintext credentials or real `.env` files.
- `git diff --stat origin/main` -> verified baseline alignment with latest upstream contributions.
- Secret scanning syntax check -> validated regex allowlist in `.gitleaks.toml` against `.env.example`.

**Blocked, dependencies and decisions needed**
- D-09 (RBAC Matrix approval) - waiting on BNCS via Aryan - since 2026-10-26 - tracked in decision register (`UNAPPROVED` baseline active).
- D-11 (Embedding model selection) - waiting on mentor and AI lead (Alok) - since 2026-10-26 - tracked in decision register (strict CPU local baseline active).
- D-16 (Hosted staging decision) - waiting on BNCS confirmation - since 2026-10-26 - tracked in decision register (`STAGING_CHECKLIST` ready).

**Next week**
- Review Supplier & Product registry schemas and evidence metadata security controls (D-10) in merged `backend/` and `database/`.
- Coordinate with Harish Pal on integrating negative security test fixtures into CI test runner.

## Week 1 - 26-30 October 2026

_Recorded on 9 November 2026._

**Completed**
- Established complete Security Handover Pack v0.1: STRIDE Threat Model, Data Classification Matrix (15 entities), RBAC Matrix, Auth Threat Review, Active Remediation Register, Staging Checklist, and Residual Risk Statement - drafted - evidence: [`docs/security/`](../security/)
- Enforced secrets baseline and repository exclusion rules - drafted - evidence: [`.gitignore`](../../.gitignore) and [`.gitleaks.toml`](../../.gitleaks.toml)

**Meetings, reviews and coordination**
- Conducted sprint planning on security workstream boundaries and initial threat surface analysis.
- Reviewed architectural decisions regarding single-origin proxying (`TD-09`) and rendering boundary (`TD-10`).

**In progress**
- Initial threat modeling and access-control matrix formulation - M11-AC9.

**Tests and validation**
- Validated GitHub Actions workflow YAML syntax for `.github/workflows/security.yml` and `.github/dependabot.yml`.
- Local inspection of repository tree to ensure zero unapproved `.env` or credential files are tracked.

**Blocked, dependencies and decisions needed**
- D-09 (RBAC Matrix approval) - waiting on BNCS via Aryan - since 2026-10-26.
- D-19 (Timeline approval) - waiting on BNCS & University Coordinator - since 2026-10-26.

**Next week**
- Deliver canonical `.env.example` template and negative test specifications for Week 2 vertical-slice workflows.
