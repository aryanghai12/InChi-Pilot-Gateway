# Repository-Wide Code Audit – InChi Pilot Gateway

| | |
|---|---|
| **Audit date** | 19 November 2026 (Week 4 of the proposed revised timeline) |
| **Revision audited** | Branch `fix/issue-found` at `681608a` (equal to `origin/main`). The unmerged C7 commit `ae9884b` (branch `feature/my-updates`) is reviewed separately in the C7 section and labelled as such. |
| **Prepared by** | AI-assisted audit run for Alok Tiwari (C7). Findings are technical observations, not judgements of any person. |
| **Method** | Source reading, execution-flow tracing, the existing test suites, and purpose-built reproduction tests run against an in-memory test database outside the repository. No product code was changed. |

---

## 1. Audit Summary

**Scope.** All application code and its configuration, CI and documentation, measured against `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/MVP_FEATURES.md`, `docs/security/`, `docs/qa/` and `database/docs/`.

**Modules inspected**

- `backend/config/`: settings, URLs, exception handler, middleware.
- `backend/apps/accounts/`: models, views, serializers, permissions, policy, admin, management command, tests.
- `backend/apps/registry/`, `backend/apps/demand/`, `backend/apps/audit/`.
- The empty `readiness`, `opportunities` and `dashboard` apps.
- `backend/apps/matching/` and `backend/ai_matching/`, plus `ae9884b`.
- `database/` (the separate Django package).
- `frontend/`: the App Router pages, components, `lib/api/` and `next.config.ts`.
- `e2e/`, `.github/workflows/`, `.github/dependabot.yml`, `.env.example` files and `.gitignore`.
- All `docs/` folders.

| Measure | Count |
|---|---|
| Issues reported | **48** |
| Confirmed defects (Critical/High/Medium/Low) | **41** |
| Improvement or status items (`[INFO]`) | **6** |
| Suspected, needs verification | **1** |
| Automated tests executed | **426** test executions across 9 suites, plus 22 audit reproduction scenarios (§6) |

**Overall testing status.** Every existing test suite that could run in this environment passed. That doesn't mean the code is correct: most confirmed defects below sit in paths the existing tests don't exercise.

**Important limitations**

- Docker Desktop wasn't running, so nothing that needs PostgreSQL was executed: the audit-trigger tests, Vishal's database package on Postgres, and the Playwright E2E suite against the Compose stack.
- The audit reproduction tests ran on branch `feature/my-updates`. That branch differs from this one **only** in C7 files, `docs/ai/`, one weekly report and the C7 section of `.env.example`. Every non-C7 file exercised is byte-identical, so the evidence applies to this branch.
- Browser behaviour was verified only where stated. Frontend findings rely on source analysis plus lint, typecheck, unit tests and build.

## 2. Severity Summary

| Severity | Count | IDs |
|---|---|---|
| Critical | 1 | 001 |
| High | 6 | 002, 003, 004, 005, 041, 042 |
| Medium | 20 | 006–013, 019, 021, 022, 023, 025, 029, 030, 039, 043–046 |
| Low | 14 | 014–018, 020, 026, 027, 031, 032, 034, 035, 038, 040 |
| Info | 6 | 028, 033, 036, 037, 047, 048 |
| Needs Verification | 1 | 024 (suspected Medium) |

---

## 3. Team Member-Wise Findings

Field order for every issue: Severity · Category · Module/File · Location · Expected · Actual · Root cause · Evidence · Reproduction · Impact · Recommended fix · Verification status.

### Team Member: Abhishek Kumar
**Assigned Responsibility:** Application backend and access control. Owns `backend/config/` and, in every app, serializers, views, permissions, services and URLs; also `accounts/policy.py`, `audit/services.py`, the requirements files, the restricted Django admin and auth (AGENTS.md C5; ARCHITECTURE.md §4.2).

#### ISSUE-001 — Unauthenticated account onboarding contradicts D-12 and allows privilege escalation
- **Severity:** `[CRITICAL]` · **Category:** `[SECURITY]` `[AUTH]` `[BACKEND]`
- **Module/File:** `backend/apps/accounts/views.py`, `backend/apps/accounts/urls.py`, `backend/apps/accounts/serializers.py`
- **Location:** `RegisterView` (views.py:113–139), `VerifyAccountView` (views.py:142–197), routes at urls.py:24–26, `RegisterSerializer` (serializers.py:60–89)
- **Expected:** D-12 and MVP_FEATURES M1: no self-registration. Accounts are provisioned only through the restricted admin or `create_platform_admin`. Least privilege.
- **Actual:** Unauthenticated onboarding endpoints exist. A confirmed test showed they can produce a working account with elevated privileges and no administrator involvement.
- **Root cause:** The onboarding endpoints are open to anonymous callers and don't constrain which privileges an account receives.
- **Evidence:** Reproduced on 19 Nov 2026 against the test database. The detailed steps are **intentionally omitted from this file**: the repository is public, and this overlaps the confidential QA-004 in `docs/qa/defects.md`. The full reproduction is available privately to Abhishek, Ajendra and Aryan.
- **Reproduction steps:** Withheld (see Evidence).
- **Impact:** Complete loss of access control (M1-AC1 to AC3) on any reachable deployment, including user management.
- **Recommended fix:** Remove the anonymous onboarding routes, or put them behind the platform-admin policy, following D-12. Never let a caller choose a privileged role. Add negative tests. Ajendra to review, and Aryan to record the outcome under QA-004. Treat as a release blocker.
- **Verification Status:** `CONFIRMED`

#### ISSUE-002 — `DELETE /api/v1/auth/users/{id}/` permanently deletes user accounts
- **Severity:** `[HIGH]` · **Category:** `[BACKEND]` `[AUTH]` `[DATABASE]`
- **Module/File:** `backend/apps/accounts/permissions.py`, `backend/apps/accounts/views.py`
- **Location:** `RolePermission.ACTION_MAP` (`"DELETE": "deactivate"`, permissions.py:21); `destroy → deactivate` mapping (permissions.py:36–37); `UserManagementViewSet(viewsets.ModelViewSet)` (views.py:200)
- **Expected:** ARCHITECTURE.md §5: users are deactivated, never deleted. The restricted admin has `has_delete_permission = False`.
- **Actual:** HTTP **204**, and the user row is removed.
- **Root cause:** The permission class turns `destroy` into the policy action `deactivate`, which admins are granted. The viewset inherits DRF's real `destroy()`, which performs a hard delete.
- **Evidence:** Audit test A3: `[A3 DELETE user by admin] HTTP 204` and `analyst row still exists: False`.
- **Reproduction steps:** As platform_admin, send `DELETE /api/v1/auth/users/<analyst id>/`.
- **Impact:** Accounts and their attribution are destroyed. On PostgreSQL, deleting a user who has audit history is expected to fail instead (the audit trigger blocks the `SET_NULL` update), so behaviour differs by database. That part is **not verified**: PostgreSQL wasn't available.
- **Recommended fix:** Disable `destroy` on this viewset (for example `http_method_names` without `delete`, or override it to return 405). Don't map DELETE to `deactivate`. Add tests.
- **Verification Status:** `CONFIRMED` (SQLite); the PostgreSQL behaviour `NEEDS VERIFICATION`

#### ISSUE-003 — The "restricted" Django admin lets platform admins grant superuser, change their own role and store plain-text passwords
- **Severity:** `[HIGH]` · **Category:** `[SECURITY]` `[AUTH]` `[BACKEND]`
- **Module/File:** `backend/apps/accounts/admin.py`
- **Location:** `UserAdmin.fieldsets` (admin.py:21–26); `has_*_permission` (admin.py:28–42)
- **Expected:** ARCHITECTURE.md §5:
  - `is_superuser` is never set outside local dev, and `is_staff` is derived from the role.
  - A user can't change their own role or deactivate themselves.
  - Admin changes write audit events.
- **Actual:**
  - The change form exposes `is_superuser`, `is_staff`, `role` and a raw `password` field, and saving `is_superuser=on` takes effect.
  - Typed passwords are stored verbatim, so the account can no longer log in.
  - No self-edit guard exists, although the docstring claims one.
  - No audit event is written.
- **Root cause:** It's a plain `ModelAdmin` over the custom user, not `django.contrib.auth.admin.UserAdmin` with a password-hashing form, and the fields aren't restricted.
- **Evidence:** Audit test A6: `form has is_superuser: True; password input: True`, then POST → `is_superuser=True; stored password == plain text: True; check_password works: False; audit events for admin change: 0`.
- **Reproduction steps:** As platform_admin, open `/<ADMIN_URL_PATH>/accounts/user/<id>/change/`, tick `is_superuser`, type a password, save.
- **Impact:** Privilege escalation beyond the designed role model; broken credentials; unaudited user administration (M1-AC5, M10-AC1).
- **Recommended fix:** Base the admin on `UserAdmin` with `UserChangeForm`/`AdminPasswordChangeForm`. Make `is_superuser`, `is_staff` and the self-role read-only. Block self-deactivation and self-role-change in `get_readonly_fields`/`save_model`. Write audit events in `save_model`.
- **Verification Status:** `CONFIRMED`

#### ISSUE-004 — Material actions are not audited, and audited updates carry no changed fields
- **Severity:** `[HIGH]` · **Category:** `[BACKEND]` `[SECURITY]`
- **Module/File:** `backend/apps/accounts/views.py`, `backend/apps/registry/views.py`, `backend/apps/accounts/admin.py`
- **Location:**
  - `LoginView.post` (views.py:61–74) and the logout view: no audit call.
  - `UserManagementViewSet` (`deactivate`, `activate`, `update`, `create`, `destroy`; views.py:200–254): no audit calls.
  - `EvidenceItemViewSet` (registry/views.py:210–232): no audit calls.
  - Every `record_event(...)` call in registry and demand omits `changes=`.
- **Expected:**
  - M1-AC5: successful logins, failed logins and denied actions create audit events.
  - M2-AC6: create, edit, status change and archive record actor, time **and changed fields**.
  - M10-AC1: every material action produces exactly one event.
- **Actual:** Zero events for logins, failed logins, deactivations and evidence edits. Supplier and product update events store `changes = {}`.
- **Root cause:** Audit calls were added to the supplier, product and requirement viewsets only, and without before/after diffs.
- **Evidence:**
  - Test A7: `audit events after 1 good login, 1 failed login, 1 deactivation: 0`.
  - Test R2: `audit events for evidence: 0`.
  - Test R5: `update audit changes field: {}`.
- **Reproduction steps:** Log in, log in with a wrong password, deactivate a user, PATCH an evidence item; then query `AuditEvent`.
- **Impact:** The audit trail can't answer "who changed what" (Stage 8 of the journey, M10). It's an acceptance criterion in every module's Definition of Done.
- **Recommended fix:** Emit events for login success/failure (with no credentials logged), denied actions, every user-management action, evidence create/update, and admin saves. Pass a changed-field diff (`serializer.initial_data` vs instance) as `changes`. Add audit assertions to the tests.
- **Verification Status:** `CONFIRMED`

#### ISSUE-005 — Commercial Analysts can mark evidence as "verified"
- **Severity:** `[HIGH]` · **Category:** `[BACKEND]` `[AUTH]`
- **Module/File:** `backend/apps/registry/serializers.py`, `backend/apps/registry/views.py`, `backend/apps/accounts/policy.py`
- **Location:** `EvidenceItemSerializer.Meta.fields` includes a writable `review_status` (serializers.py:350–371); `EvidenceItemViewSet` (views.py:210); policy `"evidence": {"update": [COMMERCIAL_ANALYST], "verify": [REVIEWER]}`
- **Expected:** M2-AC5: evidence shows "provided", not "verified", unless a reviewer has recorded verification. The MVP §5 matrix gives "mark verified" to Reviewers only.
- **Actual:** An Analyst PATCH `{"review_status": "verified"}` returns **200**. There is no verify action, so the policy's `verify` entry is never used.
- **Root cause:** Verification is modelled as an ordinary writable field, not a reviewer-only transition.
- **Evidence:** Test R2: `analyst PATCH evidence review_status=verified → HTTP 200`.
- **Reproduction steps:** As an analyst, `PATCH /api/v1/evidence/<id>/ {"review_status":"verified"}`.
- **Impact:** A separation-of-duties bypass. Reviewers and the matching engine (evidence inputs) can be shown unverified documents as verified.
- **Recommended fix:** Make `review_status` read-only in the serializer. Add a `verify` action restricted to `policy["evidence"]["verify"]`, with a reason and an audit event. Add negative tests.
- **Verification Status:** `CONFIRMED`

#### ISSUE-006 — Audit writes aren't atomic with the change, and audit failures are silently swallowed
- **Severity:** `[MEDIUM]` · **Category:** `[BACKEND]` `[SECURITY]`
- **Module/File:** `backend/apps/audit/services.py`; the `perform_create`/`perform_update`/action methods in `registry/views.py` and `demand/views.py`
- **Location:** `record_event` `try/except Exception → logger.error; return None` (services.py:7–28); callers have no `transaction.atomic()`
- **Expected:** ARCHITECTURE.md §5: `record_event()` is called inside the same `transaction.atomic()` as the change, so a change without its audit event can't be committed.
- **Actual:** With the audit insert forced to fail, the supplier create still returns **201** and persists, with **0** audit rows.
- **Root cause:** Exceptions are caught inside `record_event`, and the callers don't wrap the save and the audit in one transaction.
- **Evidence:** Test R4: `supplier create while audit insert fails → HTTP 201; supplier persisted: True; audit rows: 0`.
- **Reproduction steps:** Patch `AuditEvent.objects.create` to raise, then POST `/api/v1/suppliers/`.
- **Impact:** Silent audit gaps under database errors (M10-AC1). The audit log line also interpolates the exception text.
- **Recommended fix:** Let `record_event` raise. Wrap each save and its `record_event` in `transaction.atomic()` (or use `ATOMIC_REQUESTS`). Add a test that a failing audit rolls back the change.
- **Verification Status:** `CONFIRMED`

#### ISSUE-007 — Requirement status can be changed by a plain PATCH, bypassing the `mark-ready` gate and reopening closed requirements
- **Severity:** `[MEDIUM]` · **Category:** `[BACKEND]` `[API]`
- **Module/File:** `backend/apps/demand/serializers.py`, `backend/apps/demand/views.py`
- **Location:** `requirement_status` is writable (serializers.py:56; it isn't in `read_only_fields`, 65–74); the partial gate in `validate()` (171–185); `perform_update` (views.py:64–74); `mark_ready` refuses closed requirements (views.py:86–97)
- **Expected:** ARCHITECTURE.md §5: state changes only through transition functions. MVP M5 states: Draft → Ready for matching → Closed. A closed requirement can't be reopened through `mark-ready`.
- **Actual:**
  - PATCH `requirement_status=ready_for_matching` → **200**, recorded only as a generic `update` audit event.
  - PATCH on a **closed** requirement with `requirement_status=draft` → **200**; the status is now `draft`.
  - The serializer gate is a subset of `evaluate_readiness()` (for example, no `price_basis` check).
- **Root cause:** The workflow field is exposed for direct writing, and the transition rules live only in the custom actions.
- **Evidence:** Test D1: `HTTP 200; audit actions: ['update']`. Test D2: `PATCH closed -> draft → 200; status now: draft`.
- **Reproduction steps:** As an analyst, PATCH a closed requirement with `{"requirement_status":"draft","version":<v>}`.
- **Impact:** Workflow integrity (M5-AC2). Matching could be run on requirements that never passed the readiness gate.
- **Recommended fix:** Make `requirement_status` read-only. Do all transitions in service functions with an allowed-transition table, used by `mark_ready` and `close`. Add negative tests.
- **Verification Status:** `CONFIRMED`

#### ISSUE-008 — Editing a "ready" requirement overwrites it in place; no version history exists
- **Severity:** `[MEDIUM]` · **Category:** `[BACKEND]` `[DATABASE]`
- **Module/File:** `backend/apps/demand/serializers.py`, `backend/apps/demand/models.py`
- **Location:** `BuyerRequirementSerializer.update` (serializers.py:192–200); a single-row model with an integer `version` (models.py:115–118)
- **Expected:** M5-AC3: editing a ready requirement creates a new version, and earlier match runs still reference the version they used (also D-17).
- **Actual:** The PATCH succeeds, the status stays `ready_for_matching`, `version` goes from 1 to 2, and the same single row is overwritten. Nothing keeps version 1.
- **Root cause:** `version` serves only as an optimistic-concurrency counter. The versioned schema designed in `database/` (`BuyerRequirementVersion`) isn't used (see ISSUE-042).
- **Evidence:** Test D3: `PATCH ready requirement HTTP 200; status=ready_for_matching; version=2; rows for requirement=1`.
- **Reproduction steps:** Create a ready requirement, PATCH `quantity_value`, and inspect the stored rows.
- **Impact:** Match runs (M6-AC6) can't be traced to the exact requirement content they used.
- **Recommended fix:** With Vishal, adopt a version snapshot model. Editing a ready requirement should create a new version, or move it back to draft. Store the version on runs.
- **Verification Status:** `CONFIRMED`

#### ISSUE-009 — The currency gate rejects partial updates of products that already have a price
- **Severity:** `[MEDIUM]` · **Category:** `[BACKEND]` `[API]`
- **Module/File:** `backend/apps/registry/serializers.py`
- **Location:** `ProductSerializer.validate`, `raw_currency = self.initial_data.get("currency")` (serializers.py:289), from fix `baeb8c9` (QA-003)
- **Expected:** M3-AC2 requires an explicit currency when pricing is given. A PATCH that doesn't touch pricing should succeed when the stored product already has a currency.
- **Actual:** `PATCH {"product_name":"Renamed"}` on a priced product → **400** `currency: Currency is required when product pricing is specified.`
- **Root cause:** The check reads the request body (`initial_data`), not the effective value (`attrs` falling back to `instance.currency`).
- **Evidence:** Test R1: `HTTP 400 … {"currency":["Currency is required when product pricing is specified."]}`.
- **Reproduction steps:** Create a product with prices and USD, then PATCH only its name.
- **Impact:** Edit flows that send partial payloads fail. It's a regression introduced by the QA-003 fix.
- **Recommended fix:** Resolve the currency from `attrs.get("currency", getattr(self.instance, "currency", None))` for updates, and require it in the request body only on create, or when pricing fields change. Add a partial-update test.
- **Verification Status:** `CONFIRMED`

#### ISSUE-010 — User-management API defects: activate always denied, an admin can change their own role, created users have no password
- **Severity:** `[MEDIUM]` · **Category:** `[BACKEND]` `[AUTH]`
- **Module/File:** `backend/apps/accounts/policy.py`, `views.py`, `serializers.py`
- **Location:** The policy `"user"` dict has no `activate` key (policy.py:18–24); the `activate` action (views.py:244–254); `UserAdminUpdateSerializer` (serializers.py:117–134); `create` uses `UserSerializer`, which has no password field (views.py:200–214)
- **Expected:** Admins can reactivate users. ARCHITECTURE.md §5: "a user cannot … change their own role". Created accounts are usable.
- **Actual:**
  - (a) `POST …/activate/` as admin → **403** `permission_denied`.
  - (b) An admin's PATCH of their own `role` → **200**, and the role changes.
  - (c) `POST /auth/users/` → **201**, with an empty password field, so the account can never log in.
- **Root cause:** (a) A missing policy entry. (b) No object rule for `user.update` on self. (c) The serializer chosen for `create` doesn't set a password.
- **Evidence:** Test A4 (403), Test A5 (`admin role now: reviewer`), Test U1 (`HTTP 201 … password field empty: True`).
- **Reproduction steps:** As described in (a)–(c).
- **Impact:** Account lifecycle can't be completed through the API. An admin can demote themselves, possibly leaving no admin.
- **Recommended fix:** Add `activate` to the policy. Add a deny-self object rule for role changes. Either disable `create` (provisioning goes through admin or the command, D-12) or add a validated password field. Add tests for each.
- **Verification Status:** `CONFIRMED`

#### ISSUE-011 — CSRF failures on authenticated API calls return `permission_denied`, not `csrf_failed` (QA-005 only partly fixed)
- **Severity:** `[MEDIUM]` · **Category:** `[API]` `[SECURITY]` `[INTEGRATION]`
- **Module/File:** `backend/config/exceptions.py`, `backend/config/settings.py`
- **Location:** `csrf_failure` view (exceptions.py:23), which only Django's middleware path uses (`CSRF_FAILURE_VIEW`, settings.py:154). The DRF path maps `PermissionDenied` to `permission_denied` (exceptions.py:117).
- **Expected:** ARCHITECTURE.md §5: a CSRF failure returns 403 with `code: "csrf_failed"`, so the frontend can refresh the token and retry once (§7).
- **Actual:**
  - The anonymous login without a token gives `csrf_failed`, which is correct.
  - **An authenticated** POST without a token gives `403 {"code":"permission_denied","message":"CSRF Failed: CSRF cookie not set."}`.
- **Root cause:** DRF's `SessionAuthentication.enforce_csrf` raises `PermissionDenied`. It never goes through `CSRF_FAILURE_VIEW`.
- **Evidence:** Test A8 (permission_denied) vs Test A9 (csrf_failed).
- **Reproduction steps:** Use a logged-in session with CSRF enforcement and POST `/api/v1/suppliers/` without `X-CSRFToken`.
- **Impact:** The frontend's retry in `frontend/src/lib/api/client.ts:105–108` (Priyanka) never fires for authenticated writes. Users see "access denied" instead of a silent token refresh. Fix the backend first, then confirm the client retry with Priyanka.
- **Recommended fix:** In `custom_exception_handler`, recognise DRF CSRF `PermissionDenied` (by its message prefix, or with a custom `SessionAuthentication` subclass that raises a dedicated exception) and return `csrf_failed`. Add a test for the authenticated path.
- **Verification Status:** `CONFIRMED`

#### ISSUE-012 — The backend defaults to SQLite, and its requirements can't connect to PostgreSQL
- **Severity:** `[MEDIUM]` · **Category:** `[CONFIG]` `[DATABASE]`
- **Module/File:** `backend/config/settings.py`, `backend/requirements.txt`
- **Location:** settings.py:74–97 (SQLite fallback when `DATABASE_URL` is unset); `requirements.txt` has no `psycopg`
- **Expected:** ARCHITECTURE.md §1: PostgreSQL 17 + pgvector is authoritative; the audit trigger (TD-03) is PostgreSQL-only.
- **Actual:** Without `DATABASE_URL`, the app silently uses SQLite, where the audit trigger is skipped. With it set, the backend's own requirements lack a driver. CI works around this by also installing `database/requirements.txt` (QA-B03).
- **Root cause:** Development convenience defaults that diverge from the architecture.
- **Evidence:** settings.py:91–97; `backend/requirements.txt`; `ci.yml:104`; `docs/qa/defects.md` QA-B03.
- **Reproduction steps:** `pip install -r backend/requirements.txt`, set `DATABASE_URL=postgresql://…`, run `manage.py check` → psycopg import error. That last step was not executed here.
- **Impact:** Environments can run without the database-level audit protection, without anyone noticing.
- **Recommended fix:** Pin `psycopg[binary]` in `backend/requirements.txt`. Make SQLite an explicit opt-in (as in `database/config/database.py`). Ajendra to review.
- **Verification Status:** `CONFIRMED` (by configuration analysis; the PostgreSQL connection wasn't executed)

#### ISSUE-013 — No automated tests for the demand API (M5)
- **Severity:** `[MEDIUM]` · **Category:** `[TESTING]` `[BACKEND]`
- **Module/File:** `backend/apps/demand/`
- **Location:** No `tests/` package exists
- **Expected:** AGENTS.md §B rule 6 and the C5 DoD: allowed **and** denied tests per role and endpoint, with audit assertions.
- **Actual:** `BuyerRequirementViewSet`, `mark_ready` and `close` have no tests. ISSUE-007 and ISSUE-008 went undetected.
- **Root cause:** The tests weren't added together with the feature.
- **Evidence:** `find backend/apps -path "*tests*" -name "test_*.py"` lists none for demand.
- **Reproduction steps:** n/a
- **Impact:** M5-AC1 to AC5 are unverified.
- **Recommended fix:** Add API tests for CRUD, the readiness gate, transitions (including invalid ones), version conflict, role denials and audit events.
- **Verification Status:** `CONFIRMED`

#### ISSUE-014 — Anonymous account enumeration via `GET /api/v1/auth/verify/status/`
- **Severity:** `[LOW]` · **Category:** `[SECURITY]` `[AUTH]`
- **Module/File:** `backend/apps/accounts/views.py`
- **Location:** `VerifyAccountView.get` (views.py:182–197)
- **Expected:** Unauthenticated callers can't learn which internal accounts exist.
- **Actual:** An existing email returns `200 {"email", "is_verified", "is_active"}`; an unknown email returns `404`.
- **Root cause:** `AllowAny`, with distinct responses.
- **Evidence:** Test A2.
- **Reproduction steps:** `GET /api/v1/auth/verify/status/?email=<address>` without a session.
- **Impact:** Helps targeted credential attacks (no login throttling exists yet, TD-04).
- **Recommended fix:** Remove this endpoint together with ISSUE-001, or make it admin-only.
- **Verification Status:** `CONFIRMED`

#### ISSUE-015 — The OpenAPI schema and Swagger UI are served to anonymous users
- **Severity:** `[LOW]` · **Category:** `[SECURITY]` `[API]`
- **Module/File:** `backend/config/urls.py`, `backend/config/settings.py`
- **Location:** urls.py:28–30; `SPECTACULAR_SETTINGS` (settings.py:137) has no `SERVE_PERMISSIONS`
- **Expected:** Deny-by-default (ARCHITECTURE.md §5). Through the Next.js rewrite (TD-09), `/api/schema/` is reachable on the public origin.
- **Actual:** Anonymous `GET /api/schema/` → 200 (OpenAPI); `GET /api/docs/` → 200 (HTML).
- **Root cause:** drf-spectacular's default serve permission is `AllowAny`.
- **Evidence:** Audit test S1.
- **Reproduction steps:** Send both GETs without a session.
- **Impact:** Full API surface disclosure, including the ISSUE-001 endpoints.
- **Recommended fix:** Set `SERVE_PERMISSIONS: ["rest_framework.permissions.IsAuthenticated"]`, or don't mount these outside development.
- **Verification Status:** `CONFIRMED`

#### ISSUE-016 — Evidence can be created with neither a supplier nor a product
- **Severity:** `[LOW]` · **Category:** `[BACKEND]` `[DATABASE]`
- **Module/File:** `backend/apps/registry/serializers.py` (`EvidenceItemSerializer`, from line 350), `backend/apps/registry/models.py` (`EvidenceItem`)
- **Location:** No `validate()` on the serializer; both FKs are nullable
- **Expected:** MVP §6: an EvidenceItem belongs to a supplier or a product.
- **Actual:** `POST /api/v1/evidence/ {"document_type":"X","evidence_reference":"SYN-2"}` → 201 with both null.
- **Root cause:** No exactly-one-parent validation or constraint.
- **Evidence:** Test R3.
- **Reproduction steps:** As shown.
- **Impact:** Orphan records that never appear on any supplier or product.
- **Recommended fix:** Add serializer validation (Abhishek) and a `CheckConstraint` (Vishal, through a new migration).
- **Verification Status:** `CONFIRMED`

#### ISSUE-017 — CORS middleware with credentials is installed, contrary to TD-09
- **Severity:** `[LOW]` · **Category:** `[CONFIG]` `[SECURITY]`
- **Module/File:** `backend/config/settings.py`, `backend/requirements.txt`
- **Location:** settings.py:27 (`corsheaders`), :44 (middleware), :159–162 (`CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_CREDENTIALS = True`)
- **Expected:** ARCHITECTURE.md §1/§2/TD-09: single origin; **no CORS**.
- **Actual:** Credentialed CORS is enabled for the configured origins.
- **Root cause:** A leftover from the pre-proxy design.
- **Evidence:** settings lines cited.
- **Reproduction steps:** n/a (configuration).
- **Impact:** Unneeded attack surface. A mis-set `CORS_ALLOWED_ORIGINS` would allow credentialed cross-origin reads.
- **Recommended fix:** Remove `django-cors-headers` and its settings, with Ajendra's review.
- **Verification Status:** `CONFIRMED`

#### ISSUE-018 — The OpenAPI file is in the wrong place and out of date; frontend type generation points at a missing file
- **Severity:** `[LOW]` · **Category:** `[API]` `[DOCUMENTATION]` `[INTEGRATION]`
- **Module/File:** `backend/openapi-schema.yaml`; `frontend/package.json` (`generate-types` reads `../docs/api/openapi.yaml`)
- **Location:** Repository root layout
- **Expected:** ARCHITECTURE.md §5/§8: a generated `docs/api/openapi.yaml`, committed together with API changes, with a CI drift check.
- **Actual:** `docs/api/` doesn't exist. `backend/openapi-schema.yaml` differs from a fresh `manage.py spectacular` run (2,549 vs 2,684 lines). There's no drift check in CI.
- **Root cause:** The schema was generated to a different path and not regenerated after recent API changes.
- **Evidence:** A `diff` of the committed and regenerated schema reports differences throughout.
- **Reproduction steps:** `cd backend && python manage.py spectacular --file /tmp/x.yaml && diff openapi-schema.yaml /tmp/x.yaml`.
- **Impact:** Frontend types and other consumers drift from the real API.
- **Recommended fix:** Generate to `docs/api/openapi.yaml`, and add the drift check (with Harish, in CI).
- **Verification Status:** `CONFIRMED`

*Also involving Abhishek: ISSUE-041, 042, 043, 044, 046, 047 (§4).*

---

### Team Member: Ajendra Nath Tripathi
**Assigned Responsibility:** Cybersecurity and DevSecOps. Owns `docs/security/`, the security CI jobs, `.github/dependabot.yml` and the `.gitignore` secrets baseline; validates fixes rather than implementing them (AGENTS.md C2).

#### ISSUE-019 — The security CI and Dependabot don't cover all dependency sets; `check --deploy` isn't run
- **Severity:** `[MEDIUM]` · **Category:** `[SECURITY]` `[TESTING]` `[CONFIG]`
- **Module/File:** `.github/workflows/security.yml`, `.github/dependabot.yml`
- **Location:** `pip-audit -r backend/requirements.txt` only (security.yml:90); Dependabot covers `/backend`, `/frontend` and actions only
- **Expected:** AGENTS.md C2 Week 2: `pip-audit`, `npm audit`, gitleaks, and `manage.py check --deploy` against the non-dev settings. Dependabot for pip, npm and Actions.
- **Actual:** Not scanned:
  - `backend/requirements-dev.txt`
  - `database/requirements.txt` (psycopg)
  - `backend/ai_matching/requirements*.txt` (FastAPI, uvicorn; sentence-transformers and torch on `ae9884b`)
  - `e2e/package-lock.json`

  There's no `check --deploy` step. Run locally with default settings, it reports 9 warnings, including `security.W018` (DEBUG) and W012/W016 (insecure cookies).
- **Root cause:** The workflows predate the new dependency files.
- **Evidence:** security.yml:90; the dependabot.yml directories; `manage.py check --deploy` output (§6).
- **Reproduction steps:** Read the workflow; run `python manage.py check --deploy`.
- **Impact:** Vulnerable dependencies in the matching engine and QA tooling go unreported.
- **Recommended fix:** Loop pip-audit over every requirements file. Add `/database`, `/backend/ai_matching` and `/e2e` to Dependabot. Add `check --deploy` with production-like env values.
- **Verification Status:** `CONFIRMED`

#### ISSUE-020 — The security register is out of date, and one security-pack document is empty
- **Severity:** `[LOW]` · **Category:** `[DOCUMENTATION]` `[SECURITY]`
- **Module/File:** `docs/security/REMEDIATION_REGISTER.md`, `docs/security/SECURITY_HEADERS_AND_CONTAINER_REVIEW.md`
- **Location:** SEC-03 ("In Progress", line 28) and SEC-05 ("Pending", line 30), although both controls now exist in code; the review document is 0 bytes
- **Expected:** C2 Evidence-before-done: each finding has severity, owner, status and retest result.
- **Actual:** No register entries for ISSUE-001, 003, 041 or the other confirmed auth findings. The statuses don't reflect the code (login `csrf_protect` exists; the audit trigger migration `audit/0002` exists).
- **Root cause:** The register hasn't been updated since the Week 2 code landed.
- **Evidence:** The cited lines; `wc -c` of the review file is 0.
- **Reproduction steps:** n/a
- **Impact:** The security pack (M11-AC9) misrepresents current risk.
- **Recommended fix:** Retest and update SEC-03/SEC-05; add entries for this audit's security findings; write or remove the empty document.
- **Verification Status:** `CONFIRMED`

*Also involving Ajendra: ISSUE-041 (`.env.example` variable names), ISSUE-044 and ISSUE-048 (§4); reviewer for ISSUE-001, 003, 015 and 017.*

---

### Team Member: Adrika T Kumar
**Assigned Responsibility:** Product UX and commercial workflow. Owns `docs/product/`: field dictionary, workflow states, acceptance criteria, and the readiness and criteria drafts for BNCS (AGENTS.md C3).

#### ISSUE-021 — The product artefacts for Weeks 1–4 aren't in the repository
- **Severity:** `[MEDIUM]` · **Category:** `[DOCUMENTATION]`
- **Module/File:** `docs/product/` (missing); `docs/daily-reports/adrika-t-kumar.md`
- **Location:** n/a
- **Expected:** AGENTS.md C3:
  - Week 1: field dictionary v1 and workflow state maps.
  - Week 3: readiness questions (D-03).
  - Week 4: mandatory and preference criteria drafts for Gate 2 (D-04/D-05) and the disposition vocabulary (D-06).

  All versioned in `docs/product/`, and recorded in weekly reports (§B rule 15).
- **Actual:** `docs/product/` doesn't exist. `database/docs/` cites an external `InChi_Buyer_Requirement_Field_Dictionary_v1.2_Consolidated.xlsx` that isn't in the repository. The weekly report file has no entries.
- **Root cause:** Not determinable from the repository. The artefacts may exist outside it.
- **Evidence:** `ls docs/product` → not found; the report file contains only its header.
- **Reproduction steps:** n/a
- **Impact:** Engineers implement without a shared, versioned definition of fields and states: free-text criteria (ISSUE-046), status values (ISSUE-007), category codes. The Gate 2 rule approval (20 Nov) has no draft in the repository to approve.
- **Recommended fix:** Commit the field dictionary, state maps and criteria drafts (marked "Proposed – D-xx") to `docs/product/`, and add weekly reports.
- **Verification Status:** `CONFIRMED` (absent from the repository; whether they exist elsewhere `NEEDS VERIFICATION`)

*Also involving Adrika: ISSUE-046 (§4) and items 8.1–8.4.*

---

### Team Member: Priyanka Singh
**Assigned Responsibility:** Frontend web and client-side integration. Owns `frontend/` (Next.js App Router, TanStack Query, CSS Modules), `next.config.ts`, and the frontend tests (AGENTS.md C4).

#### ISSUE-022 — The workspace renders with a fabricated identity whenever `/auth/me/` fails with anything other than 401
- **Severity:** `[MEDIUM]` · **Category:** `[FRONTEND]` `[AUTH]`
- **Module/File:** `frontend/src/app/(workspace)/layout.tsx`
- **Location:** `FALLBACK_DEMO_USER` (lines 13–23); `const user = fetchedUser || FALLBACK_DEMO_USER` (line 68); the banner (83–91)
- **Expected:** M1-AC1: users see only the navigation their role permits. The guard is driven by `/auth/me/` (ARCHITECTURE.md §7), and failure states show an error, not a session.
- **Actual:** The 401 redirect works, so QA-001 is fixed for that case. On a network error, 5xx or 403 from `/auth/me/`, the layout renders the full workspace as a hard-coded "Commercial Analyst" with a named team member's details.
- **Root cause:** A standalone-preview fallback was left in the production layout.
- **Evidence:** Lines 67–68 (`isDemo = isError || !fetchedUser`). Not executed in a browser.
- **Reproduction steps:** Stop the backend (or make `/auth/me/` return 500) and open `/dashboard`.
- **Impact:** A misleading authenticated UI with the wrong role navigation; it hides outages. The backend still rejects the data calls.
- **Recommended fix:** Remove the fallback user. Render an error or retry state for non-401 failures.
- **Verification Status:** `CONFIRMED` (source analysis)

#### ISSUE-023 — "Explore with Demo Session" fabricates a client-side session on any login failure
- **Severity:** `[MEDIUM]` · **Category:** `[FRONTEND]` `[SECURITY]` `[AUTH]`
- **Module/File:** `frontend/src/app/login/page.tsx`
- **Location:** `handleDemoSignIn` (lines 34–70); the button is rendered unconditionally (line 235)
- **Expected:** Success only after the server confirms (MVP §8, ARCHITECTURE.md §7). No credentials in client code (AGENTS.md §B rule 7).
- **Actual:**
  - The button posts fixed credentials (lines 44–45; see ISSUE-044).
  - If that request fails for **any** reason, including wrong credentials, it writes a fake `currentUser` into the query cache and navigates into the workspace.
  - The normal login form (`handleSubmit`) handles errors correctly.
- **Root cause:** A preview-mode helper shipped in the production login page.
- **Evidence:** Source lines cited. Not executed in a browser.
- **Reproduction steps:** With the backend unreachable or without the demo account, click the demo button.
- **Impact:** The fake session combines with ISSUE-022 to show a working-looking workspace without authentication.
- **Recommended fix:** Remove the demo button, or gate it behind a development-only build flag, with no embedded credentials and no fake session.
- **Verification Status:** `CONFIRMED` (source analysis)

#### ISSUE-024 — The post-login `next` parameter is used without validation (possible open redirect)
- **Severity:** `[NEEDS VERIFICATION]` (suspected `[MEDIUM]`) · **Category:** `[FRONTEND]` `[SECURITY]`
- **Module/File:** `frontend/src/app/login/page.tsx`
- **Location:** `const nextUrl = searchParams.get("next") || "/dashboard"` (line 21); `router.push(nextUrl)` (lines 52, 66, 94)
- **Expected:** Only same-origin relative paths are accepted as a return URL.
- **Actual:** Any value is passed to `router.push`.
- **Root cause:** No allow-list check (for example "starts with `/` and not `//`").
- **Evidence:** Source lines. **Not verified:** how Next.js 16 `router.push` treats absolute or external URLs wasn't tested in a browser.
- **Reproduction steps (to verify):** Open `/login?next=https://example.org`, log in, and observe the navigation target.
- **Impact:** If confirmed, a phishing aid after a genuine login.
- **Recommended fix:** Accept only paths matching `^/(?!/)`; otherwise fall back to `/dashboard`.
- **Verification Status:** `NEEDS VERIFICATION`

#### ISSUE-025 — Dashboard totals are wrong beyond 25 records, and errors are shown as zero
- **Severity:** `[MEDIUM]` · **Category:** `[FRONTEND]` `[INTEGRATION]`
- **Module/File:** `frontend/src/app/(workspace)/dashboard/page.tsx`
- **Location:** The supplier and product queries (lines 48–74) return only the first page and turn any error into `[]`; `totalSuppliers`/`totalProducts = …length` (79–80); `readinessScore … ?? 0` (84)
- **Expected:**
  - M9-AC1: figures match direct queries on the seed (≥15 suppliers, ≥30 products).
  - M9-AC3: no fabricated metric; an empty dataset shows zeros *with guidance*, while an error shows an error.
- **Actual:**
  - With 30 products, the API returns `count=30` but only 25 results, so the dashboard shows 25.
  - Failed requests show 0.
  - The readiness average shows 0 when it's unknown.
- **Root cause:** It uses `results.length` instead of the paginated `count`, and errors are swallowed.
- **Evidence:** Audit test P1: `count=30 results=25 next=…?page=2`, combined with lines 79–80.
- **Reproduction steps:** Seed 30 products; open the dashboard while `/dashboard/summary/` returns 404.
- **Impact:** Dashboard figures misreport the data (Stage 8).
- **Recommended fix:** Use `count` from the paginated response, show error states, and render unknown as "—". The real fix is the backend summary endpoint (ISSUE-047).
- **Verification Status:** `CONFIRMED`

#### ISSUE-026 — The requirements page reports "Preview mode" success without server confirmation
- **Severity:** `[LOW]` · **Category:** `[FRONTEND]`
- **Module/File:** `frontend/src/app/(workspace)/requirements/page.tsx`
- **Location:** The create and update mutations' `onError` on 404 (lines 205–212, 239–245)
- **Expected:** Success messages appear only after a 2xx response (ARCHITECTURE.md §7).
- **Actual:** On 404, the record is added to local component state and shown with a "Preview Mode" notice. The data is lost on reload.
- **Root cause:** The pre-backend preview fallback wasn't removed after `/api/v1/requirements/` was delivered.
- **Evidence:** Source lines cited.
- **Reproduction steps:** Make the create request return 404 (for example via a proxy misconfiguration).
- **Impact:** A user may believe unsaved data was saved.
- **Recommended fix:** Remove the local fallback; show an error.
- **Verification Status:** `CONFIRMED` (source analysis)

#### ISSUE-027 — The installed Next.js version has two moderate advisories
- **Severity:** `[LOW]` · **Category:** `[SECURITY]` `[FRONTEND]`
- **Module/File:** `frontend/package.json` (`"next": "^16.4.3"`), lockfile
- **Location:** n/a
- **Expected:** No known-vulnerable dependency versions.
- **Actual:** `npm audit --omit=dev` reports 1 moderate package (`next` 16.2.0–16.4.4): GHSA-mfr8-8qww-v76h and GHSA-vc7v-qv4w-wrv8. Both concern `use cache` / `unstable_cache`, which the app doesn't use (no matches in `src/`). The first `next build` stopped with a security notice; a rerun built successfully.
- **Root cause:** A dependency version.
- **Evidence:** npm audit output (§6).
- **Reproduction steps:** `cd frontend && npm audit --omit=dev`.
- **Impact:** Low exposure, because the affected features are unused.
- **Recommended fix:** Upgrade `next` to a patched release through the normal Dependabot/PR route, with Ajendra's review.
- **Verification Status:** `CONFIRMED`

#### ISSUE-028 — No Content-Security-Policy header yet
- **Severity:** `[INFO]` · **Category:** `[FRONTEND]` `[SECURITY]`
- **Module/File:** `frontend/next.config.ts` (`headers()`)
- **Location:** n/a
- **Expected:** ARCHITECTURE.md §7: at least a CSP, `X-Content-Type-Options`, `Referrer-Policy` and frame protection. These are scheduled for Week 6 with Ajendra's review.
- **Actual:** Every header except CSP is present.
- **Root cause:** Not yet due.
- **Evidence:** next.config.ts.
- **Reproduction steps:** n/a
- **Impact:** None yet; tracking item.
- **Recommended fix:** Add a CSP in Week 6 as planned.
- **Verification Status:** `CONFIRMED`

**Fixed since QA's last register:** `npm ci` now succeeds (QA-B04), `npm run lint` passes (QA-B05), `frontend/.env.example` is tracked (QA-002), and the 401 redirect works (QA-001, partially; see ISSUE-022).

*Also involving Priyanka: ISSUE-043, 044, 046, 047 (§4).*

---

### Team Member: Vishal Chauhan
**Assigned Responsibility:** Data and platform services. Owns all `models.py` and migrations, candidate and reporting queries, `seed_demo`, audit storage, `docs/data/`, and the `database/` package (AGENTS.md C6; ARCHITECTURE.md §4.2).

#### ISSUE-029 — There is no synthetic seed for suppliers, products or users
- **Severity:** `[MEDIUM]` · **Category:** `[DATABASE]` `[TESTING]`
- **Module/File:** `database/apps/demand/management/commands/seed_demo.py`; `backend/` (no seed command)
- **Location:** n/a
- **Expected:** C6 Week 2 and M11-AC3: a `seed_demo` command loading ≥15 suppliers, ≥30 products and ≥10 requirements, plus one synthetic user per role (ARCHITECTURE.md §5), from the README alone.
- **Actual:** `seed_demo` exists only in the separate `database/` project and seeds 20 buyer requirements. Nothing seeds suppliers, products or users in the running backend.
- **Root cause:** The seed was scoped to the demand schema in the separate package.
- **Evidence:** `seed_demo.py`; `backend/apps/*/management/commands/` contains only `create_platform_admin`.
- **Reproduction steps:** n/a
- **Impact:** Demos, the E2E journey and dashboard reconciliation (M9-AC1) can't be reproduced from seed.
- **Recommended fix:** Provide `seed_demo` in the backend for registry, demand and users, with edge cases (missing data, duplicates, ineligible items), using synthetic data only.
- **Verification Status:** `CONFIRMED`

#### ISSUE-030 — Product model gaps: no certifications field, and assumed default values
- **Severity:** `[MEDIUM]` · **Category:** `[DATABASE]`
- **Module/File:** `backend/apps/registry/models.py`
- **Location:** `Product` (from line 106): `origin` default `"India"` (line 132), `currency` default USD (line 142), no certifications field
- **Expected:**
  - M3: certifications are a core commercial field.
  - M3-AC2: unknown values are stored and shown as unknown, never as a default.
- **Actual:**
  - Certifications can only be inferred from free-text `EvidenceItem.document_type`.
  - A product with an unknown origin is stored as "India".
  - The currency defaults to USD (now guarded for priced products only, by ISSUE-009's gate).
- **Root cause:** Model defaults chosen for convenience.
- **Evidence:** Model source.
- **Reproduction steps:** Create a product without `origin` and read it back.
- **Impact:** The matching engine's mandatory-origin checks see "India" for unknown origins. That can make a candidate falsely **eligible** (M6-AC2) once origin criteria are used.
- **Recommended fix:** A new migration making `origin` blank by default (unknown). Agree a certifications representation with Adrika and Alok.
- **Verification Status:** `CONFIRMED` (source analysis)

#### ISSUE-031 — Seed criteria conflict with M6-AC2, and their code values don't match the registry
- **Severity:** `[LOW]` · **Category:** `[DATABASE]` `[AI-MATCHING]`
- **Module/File:** `database/apps/demand/management/commands/seed_demo.py`
- **Location:** The `RequirementEligibilityCriterion.objects.create(...)` block (lines 132–139)
- **Expected:** M6-AC2: unknown on a mandatory criterion means "insufficient data", not exclusion. Coded values should share one vocabulary across modules.
- **Actual:** `unknown_policy="exclude"`. `origin_country` is compared with `"IN"` while the registry stores "India".
- **Root cause:** No shared reference vocabulary yet (BUY-D04 open).
- **Evidence:** Seed source.
- **Reproduction steps:** n/a
- **Impact:** Seeded requirements demonstrate the wrong unknown-handling. The C7 normalisation compensates for the country spelling only.
- **Recommended fix:** Use `insufficient_data` (or omit `unknown_policy`), and agree the code lists with Adrika.
- **Verification Status:** `CONFIRMED`

#### ISSUE-032 — The database integration notes are stale
- **Severity:** `[LOW]` · **Category:** `[DOCUMENTATION]`
- **Module/File:** `database/docs/backend-integration-notes.md`
- **Location:** "Package location" and "Local setup" sections
- **Expected:** Instructions that work on the current repository.
- **Actual:** They refer to `database_backup_temp/` and `DB_PORT=5433`, while `database/docker-compose.yml` and `.env.example` use 5432.
- **Root cause:** Written before the package moved.
- **Evidence:** Document text.
- **Reproduction steps:** Follow the notes literally.
- **Impact:** Onboarding friction (M11-AC3).
- **Recommended fix:** Update the paths and port.
- **Verification Status:** `CONFIRMED`

*Also involving Vishal: ISSUE-042 (two demand schemas), ISSUE-008, 016 and 047 (models for missing modules).* Not verified: the `database/` tests on PostgreSQL. They pass in the documented `USE_SQLITE=True` mode (§6).

---

### Team Member: Alok Tiwari
**Assigned Responsibility:** AI matching and data intelligence. Owns `backend/apps/matching/` services, selectors and tests, `backend/ai_matching/` and `docs/ai/` (AGENTS.md C7).

**Safeguard verification**

| Safeguard | On this branch (`681608a`) | On unmerged `ae9884b` |
|---|---|---|
| Eligibility before semantics; failure can't be overridden | Not reachable (pipeline stops at eligibility) | **Verified**: `test_mandatory_failure_never_ranked_despite_perfect_similarity`, plus a live run with the real model |
| Unknown mandatory data never passes | n/a | **Verified** by tests (unknown value, unit mismatch, unrecorded evidence, free text → `insufficient_data`) |
| No silent rules-only fallback | **Verified**: every request ends in 503 `stage_not_available` | **Verified**: embedding failure or no provider → explicit failure |
| Embedding failures handled explicitly | `none` provider raises (tested) | **Verified**: load, inference, count, dimension and non-finite checks |
| No invented or unapproved weights | No scoring code | **Verified**: weights only from `criteria/<version>.json`; committed `v0-UNAPPROVED.json` has none and is refused |
| Human decision only | No disposition code in C7 (correct; M7 is C5's) | Same; every explanation ends with the decision-support note |
| Model config environment-based and lazy-loaded | No model configured | **Verified**: `EMBEDDING_MODEL_NAME` only, lazy single load, `trust_remote_code=False`, local files only |

#### ISSUE-033 — The matching pipeline beyond Stage 1 isn't on `main`
- **Severity:** `[INFO]` · **Category:** `[AI-MATCHING]` `[INTEGRATION]`
- **Module/File:** `backend/ai_matching/services/matching_pipeline.py` (`run_pipeline`); `eligibility.py`, `hybrid_scorer.py`, `ranking.py`, `explainability.py` and `apps/matching/services/matching_service.py`, `result_handler.py` are docstring stubs here
- **Location:** n/a
- **Expected:** The Week 4 duty is the deterministic filters and weighted-score baseline.
- **Actual:** That's implemented and tested on `ae9884b` (branch `feature/my-updates`), not merged. This branch can't produce a match result.
- **Root cause:** Pending PR.
- **Evidence:** Engine tests: 63 passed here; 144 passed and 2 skipped on `ae9884b`.
- **Reproduction steps:** n/a
- **Impact:** Integration status only.
- **Recommended fix:** Raise and merge the PR after review by Abhishek, Vishal and Ajendra.
- **Verification Status:** `CONFIRMED`

#### ISSUE-034 — Criterion and preference `value` objects are unbounded
- **Severity:** `[LOW]` · **Category:** `[AI-MATCHING]` `[SECURITY]`
- **Module/File:** `backend/ai_matching/schemas/buyer.py`
- **Location:** `MandatoryCriteriaInput.value` (line 44), `PreferenceCriteriaInput.value` (line 52): `dict[str, Any]` (same on `ae9884b`)
- **Expected:** THREAT_MODEL T-DS-01: bounded inputs. Every other text and list field is bounded.
- **Actual:** Arbitrarily large or deep JSON is accepted inside `value`.
- **Root cause:** `value` mirrors the free `JSONField`.
- **Evidence:** Schema source.
- **Reproduction steps:** POST `/match` with a very large nested `value`.
- **Impact:** CPU and memory pressure on the engine. It's internal-only, so exposure is limited.
- **Recommended fix:** Validate the key count, depth and serialised size of `value` (for example ≤ 4 KB).
- **Verification Status:** `CONFIRMED` (source analysis)

#### ISSUE-035 — `weekly_summary` assigns programme weeks by UTC date *(only on `ae9884b`)*
- **Severity:** `[LOW]` · **Category:** `[AI-MATCHING]`
- **Module/File:** `backend/apps/matching/services/weekly_summary.py` (`ae9884b`)
- **Location:** `programme_week(record.started_at.date(), …)` (line 83)
- **Expected:** Programme weeks follow the team's local calendar (Monday start).
- **Actual:** An aware UTC timestamp's `.date()` is used. Runs between 00:00 and 05:30 IST on a Monday are counted in the previous week.
- **Root cause:** No timezone conversion before taking the date.
- **Evidence:** Source line.
- **Reproduction steps:** A record with `started_at = 2026-11-22T20:00Z` (that's 23 Nov in IST) is assigned week 4, not 5.
- **Impact:** Weekly counts are off at week boundaries.
- **Recommended fix:** Use `django.utils.timezone.localtime(record.started_at).date()` with a configured `TIME_ZONE`, or a parameter.
- **Verification Status:** `CONFIRMED` (source analysis)

#### ISSUE-036 — The requirement's product category isn't a hard gate unless it's stated as a mandatory criterion *(design point, `ae9884b`)*
- **Severity:** `[INFO]` · **Category:** `[AI-MATCHING]`
- **Module/File:** `backend/ai_matching/services/eligibility.py` (`ae9884b`)
- **Location:** Only criteria supplied in `mandatory_criteria` are evaluated
- **Expected:** Undecided. MVP §7 lists category among the *illustrative* hard filters, pending D-04.
- **Actual:** In the live smoke test, a textile candidate was ranked (below the relevant one) for an electronics requirement, because no category criterion was supplied.
- **Root cause:** A deliberate choice to invent no implicit rules.
- **Evidence:** The 19 Nov smoke-test output.
- **Reproduction steps:** n/a
- **Impact:** Possibly surprising ranked lists until D-04 is decided.
- **Recommended fix:** Decide under D-04 whether category is always mandatory (item 8.1).
- **Verification Status:** `CONFIRMED`

#### ISSUE-037 — The embedding model is named in `.env.example` before its ARCHITECTURE.md §9 record *(`ae9884b`)*
- **Severity:** `[INFO]` · **Category:** `[AI-MATCHING]` `[CONFIG]` `[DOCUMENTATION]`
- **Module/File:** `.env.example` (`ae9884b`, lines 70–71)
- **Location:** `EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2`
- **Expected:** AGENTS.md §A: no model is named in configuration examples until D-11 is recorded in ARCHITECTURE.md §9.
- **Actual:** Selected by the C7 owner on 19 Nov 2026. The code reads it only from the environment and hard-codes nothing, but the §9 record and Ajendra's review are pending.
- **Root cause:** The decision record is lagging behind the implementation.
- **Evidence:** `.env.example` on `ae9884b`; ARCHITECTURE.md §1/§9 still say "TBD".
- **Reproduction steps:** n/a
- **Impact:** Governance only.
- **Recommended fix:** Ajendra reviews; Aryan records D-11 in §9 before merge.
- **Verification Status:** `CONFIRMED`

*Also involving Alok: ISSUE-045 (matching tests not in CI), ISSUE-046 (criteria format), ISSUE-048 (Compose engine image).*

---

### Team Member: Harish Pal
**Assigned Responsibility:** QA and test automation. Owns `docs/qa/`, `e2e/` and the CI test jobs (AGENTS.md C8).

#### ISSUE-038 — The defect register is out of date with the fixes and their partial retests
- **Severity:** `[LOW]` · **Category:** `[DOCUMENTATION]` `[TESTING]`
- **Module/File:** `docs/qa/defects.md`
- **Location:** The "Confirmed open defects" table (updated 16 Nov)
- **Expected:** Defects carry their retest result (C8 Evidence-before-done).
- **Actual:**
  - QA-001 to QA-006 are still "open", although GitHub issues #58–#64 are closed and fixes have merged.
  - This audit finds QA-003's fix introduced a regression (ISSUE-009).
  - QA-005 is only partly fixed (ISSUE-011).
  - QA-001 is only partly fixed (ISSUE-022).
- **Root cause:** No retest has been recorded since the fixes merged.
- **Evidence:** defects.md vs the GitHub issues API (all 9 issues closed) and this audit's tests.
- **Reproduction steps:** n/a
- **Impact:** The traceability matrix and Friday evidence don't reflect reality.
- **Recommended fix:** Retest QA-001–006, update the statuses, and link ISSUE-009, 011 and 022 as reopen or partial-fix notes.
- **Verification Status:** `CONFIRMED`

*Also involving Harish: ISSUE-045 (CI coverage), ISSUE-018 (OpenAPI drift check).* Not verified: the Playwright E2E suite (it needs the running stack; Docker wasn't available).

---

### Team Member: Aryan Ghai
**Assigned Responsibility:** Technical project coordination and integration governance. Owns `docs/governance/`, the decision records in ARCHITECTURE.md §9/§10, and maintenance of README, AGENTS and CLAUDE (AGENTS.md C1).

#### ISSUE-039 — The governance artefacts aren't in the repository
- **Severity:** `[MEDIUM]` · **Category:** `[DOCUMENTATION]`
- **Module/File:** `docs/governance/` (missing)
- **Location:** n/a
- **Expected:** C1 Week 1: the risk, issue, dependency, decision and interface (API contract) registers and the integration plan in `docs/governance/`, with approver and date for every decision.
- **Actual:** The folder doesn't exist. Decisions are referenced ("tracked in decision register") but there's no register to resolve them.
- **Root cause:** Not determinable from the repository (they may be on the GitHub Project board, D-18).
- **Evidence:** `ls docs/governance` → not found.
- **Reproduction steps:** n/a
- **Impact:** Interface contracts, such as the proposed matching contract, have no place to be recorded. The handover index (M11-AC11) can't resolve.
- **Recommended fix:** Create the registers as Markdown tables in `docs/governance/`.
- **Verification Status:** `CONFIRMED` (absent from the repository)

#### ISSUE-040 — The decision records and status statements are inconsistent with the code
- **Severity:** `[LOW]` · **Category:** `[DOCUMENTATION]`
- **Module/File:** `docs/ARCHITECTURE.md`, `docs/MVP_FEATURES.md`, `README.md`, `AGENTS.md`
- **Location:**
  - README.md:6, MVP_FEATURES.md:34 and AGENTS.md §A ("documentation only").
  - ARCHITECTURE.md §6.3 uses "D-15" for engine deployment, but D-15 is "Does a Reviewer approve a requirement" in MVP §12.
  - The rules-only fallback is described contradictorily (§1/§2/D-11 vs §6/M6-AC5).
- **Expected:** One consistent decision record.
- **Actual:** As listed.
- **Root cause:** The documents have evolved separately.
- **Evidence:** The cited sections.
- **Reproduction steps:** n/a
- **Impact:** Contributors and AI agents follow contradictory instructions.
- **Recommended fix:** Give the deployment decision its own §9 ID, record the fallback decision once taken (item 8.2), and update the status statements.
- **Verification Status:** `CONFIRMED`

---

## 4. Cross-Team Integration Issues

#### ISSUE-041 — The root `.env.example` variable names don't match what Django reads, so security settings silently fall back to insecure defaults
- **Severity:** `[HIGH]` · **Category:** `[SECURITY]` `[CONFIG]` `[INTEGRATION]`
- **Primary module:** `backend/config/settings.py` (Abhishek). **Also affected:** `.env.example` (authored by Ajendra; Abhishek owns it per ARCHITECTURE.md §4.2).
- **Expected:** Copying `.env.example` to `.env` configures Django (ARCHITECTURE.md §5 "Configuration").
- **Actual:**
  - `.env.example` sets `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_SESSION_COOKIE_*` and `DJANGO_CSRF_COOKIE_SECURE` (lines 29–45).
  - `settings.py` reads `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SESSION_COOKIE_*` and `CSRF_COOKIE_SECURE` (lines 10–13, 146–158), with defaults of a hard-coded key and `DEBUG=True`.
- **Evidence:** With only the `.env.example` names set (`DJANGO_DEBUG=False`, secure-cookie flags `True`), the loaded settings were: `SECRET_KEY is hard-coded default: True`, `DEBUG: True`, `SESSION_COOKIE_SECURE: False`, `CSRF_COOKIE_SECURE: False`.
- **Impact:** Any environment configured from the template runs with a **public signing key** (session and CSRF forgery) and debug pages, while appearing correctly configured.
- **Suggested coordination:** Abhishek and Ajendra agree one naming scheme. Settings should **fail fast** when `SECRET_KEY` is unset outside local dev, and `DEBUG` should default to `False`. Add the `check --deploy` CI step (ISSUE-019).
- **Verification Status:** `CONFIRMED`

#### ISSUE-042 — Two divergent buyer-requirement schemas; the `database/` package isn't integrated
- **Severity:** `[HIGH]` · **Category:** `[DATABASE]` `[INTEGRATION]` `[BACKEND]`
- **Primary modules:** `database/apps/demand/models.py` (Vishal); `backend/apps/demand/models.py` (owned by Vishal per ARCHITECTURE.md §4.2, written within the backend workstream).
- **Expected:** One schema, defined by the backend's Django migrations, implementing versioning (M5-AC3), separate criteria tables (M5-AC1), approved criteria configuration (M5-AC4) and the readiness blockers.
- **Actual:**
  - `database/` is a standalone Django project. It has its own `demand` app label, **no `AUTH_USER_MODEL`** (so its FKs target `auth.User`, not `accounts.User`), and a versioned, normalised design (`BuyerRequirementVersion`, criteria tables, `MatchingConfiguration`, `ReferenceValue`).
  - The running backend uses a different flat model with JSON criteria and no versions.
  - The two can't both be installed (same app label), and the richer design isn't used.
- **Evidence:** Both `models.py` files; `database/config/settings.py` (`INSTALLED_APPS` has no accounts app or `AUTH_USER_MODEL`).
- **Impact:** This is the root of ISSUE-008 and ISSUE-046. Two seed and test sets diverge. Matching run traceability can't be built.
- **Suggested coordination:** Vishal and Abhishek choose one schema for the backend (or migrate the versioned design into `backend/apps/demand`), with Alok for the matching inputs and Harish to re-point tests. Aryan records the decision.
- **Verification Status:** `CONFIRMED`

#### ISSUE-043 — List screens silently hide records beyond the first 25
- **Severity:** `[MEDIUM]` · **Category:** `[INTEGRATION]` `[FRONTEND]` `[API]`
- **Primary modules:** `frontend/src/app/(workspace)/suppliers|products|requirements/page.tsx` (Priyanka). **Also affected:** `backend/config/settings.py` `PAGE_SIZE: 25` (Abhishek).
- **Expected:** MVP M2/M3 [DEFERRABLE] rule: if the pagination UI is deferred, the list endpoints return a page size that covers the whole seed (for example 100), "and a test shows no seed records are hidden".
- **Actual:** The pages read only `results` from the first page. With the seed target of ≥30 products, the API returns 25 plus `next`, and records 26 onward never appear.
- **Evidence:** Audit test P1 (`count=30 results=25`); no page parameter in the list pages.
- **Impact:** M2-AC3 and M3-AC3 (search and filters on the seed dataset) fail.
- **Suggested coordination:** Either implement pagination UI (Priyanka), or raise the list page size per the MVP rule (Abhishek), with a test (Harish).
- **Verification Status:** `CONFIRMED`

#### ISSUE-044 — Shared demo credentials are published in client code and documentation
- **Severity:** `[MEDIUM]` · **Category:** `[SECURITY]` `[FRONTEND]` `[DOCUMENTATION]`
- **Primary modules:** `frontend/src/app/login/page.tsx:44–45` (Priyanka); `backend/README.md:119–128` (Abhishek).
- **Expected:** AGENTS.md §B rule 7: no hard-coded credentials anywhere, including examples and documentation. `seed_demo` passwords come from `DEMO_USER_PASSWORD` (ARCHITECTURE.md §5).
- **Actual:** The same fixed passwords (`AdminPass123!`, `AnalystPass123!`) are documented as "seeded credentials", and one is embedded in the public frontend bundle.
- **Evidence:** `git grep` of the tracked files.
- **Impact:** Any environment whose accounts were created by following the README is accessible with publicly known passwords, and the demo button logs straight in.
- **Suggested coordination:** Remove both. Use `INITIAL_ADMIN_PASSWORD`/`DEMO_USER_PASSWORD` placeholders. Ajendra adds a gitleaks rule for these literals.
- **Verification Status:** `CONFIRMED`

#### ISSUE-045 — CI doesn't run the matching or engine tests, and the contract tests skip silently
- **Severity:** `[MEDIUM]` · **Category:** `[TESTING]` `[AI-MATCHING]` `[INTEGRATION]`
- **Primary modules:** `.github/workflows/ci.yml:108` (Harish). **Also affected:** `backend/apps/matching/tests/test_contract.py:43` (Alok).
- **Expected:** ARCHITECTURE.md §8: the backend job runs `pytest`, and a semantic job runs the provider tests with a test double.
- **Actual:** CI runs only `apps/accounts/tests`, `apps/registry/tests` and `e2e/backend/test_controls.py`. Neither `apps/matching/tests` nor `backend/ai_matching/tests` runs. The Django–engine contract tests are marked `skipUnless(ENGINE_AVAILABLE)`, so they would pass silently as "skipped" wherever FastAPI isn't installed. Open PR #71 reports "4 skipped".
- **Evidence:** ci.yml:108; test_contract.py:43.
- **Impact:** Regressions in the safeguards (M6-AC1/AC2/AC5) wouldn't be detected by CI.
- **Suggested coordination:** Harish adds a job installing `backend/ai_matching/requirements-dev.txt` and running both suites. Alok turns the silent skip into a failure when an env flag (for example `REQUIRE_ENGINE_TESTS=1`) is set.
- **Verification Status:** `CONFIRMED`

#### ISSUE-046 — The criteria format isn't agreed: the UI stores free text, the API accepts any JSON, and the engine needs structured criteria
- **Severity:** `[MEDIUM]` · **Category:** `[INTEGRATION]` `[API]` `[AI-MATCHING]`
- **Modules:**
  - `frontend/src/app/(workspace)/requirements/page.tsx:321–322` (Priyanka) saves `{id, name, type}` free text.
  - `backend/apps/demand/models.py:89–104` and its serializer (Abhishek) accept arbitrary JSON (audit test D5: `[{"anything":"goes"}, 42, "free text"]` and `priority_weights {"x":999}` → 201).
  - The engine (Alok) evaluates structured `criterion_key/operator/value` only; free text becomes `manual_review` (never a pass) on `ae9884b`.
  - Adrika defines the criteria.
- **Expected:** M5-AC1 (structurally distinct mandatory and preference criteria) and M5-AC4 ("only criteria types from the active approved criteria version can be selected").
- **Actual:** No validation and no shared vocabulary. Real requirements can't make any candidate eligible on a free-text criterion. Buyer-entered `priority_weights` could be mistaken for approved weights (D-05).
- **Evidence:** Test D5; the source lines cited.
- **Impact:** Blocks meaningful matching on real data after Gate 2.
- **Suggested coordination:** Adrika drafts the criteria types (D-04). Abhishek validates against an approved criteria version. Priyanka renders structured inputs. Alok keeps the engine vocabulary (`docs/ai/MATCHING_CONTRACT.md` §6 on `ae9884b`) aligned. Aryan records the contract.
- **Verification Status:** `CONFIRMED`

#### ISSUE-047 — The frontend calls endpoints that don't exist yet
- **Severity:** `[INFO]` · **Category:** `[INTEGRATION]` `[API]`
- **Modules:** The frontend pages (Priyanka) call `/api/v1/dashboard/summary/`, `/api/v1/audit/events/`, `/api/v1/opportunities/`, `/api/v1/assessments/` and `/api/v1/matching/runs/`. None is routed in `backend/config/urls.py` (Abhishek), and the readiness, opportunity, dashboard and match-run models don't exist (Vishal).
- **Expected:** The schedule for these: readiness (Weeks 3–4), matching and disposition (Week 5), opportunities and dashboard (Week 6). Readiness is behind schedule (QA-B02).
- **Actual:** The pages show "under construction" on 404, which is correct for now.
- **Evidence:** urls.py:24–42; the page sources.
- **Impact:** Journey stages 3 and 5–8 can't be demonstrated.
- **Suggested coordination:** Track in the integration plan (Aryan). The endpoint paths must match the frontend's (`/matching/runs/` vs the security specs' `/matching/run/`).
- **Verification Status:** `CONFIRMED`

#### ISSUE-048 — Engine deployment: open PR #71's image lacks the semantic dependencies, and there's no service-to-service authentication
- **Severity:** `[INFO]` · **Category:** `[INTEGRATION]` `[SECURITY]` `[CONFIG]`
- **Modules:**
  - Open PR #71 (Aryan): its `matching` target installs only `ai_matching/requirements.txt`.
  - `ae9884b` (Alok) needs `requirements-semantic.txt` plus pre-downloaded weights.
  - THREAT_MODEL Boundary 3 (Ajendra): the engine has no caller authentication (`ai_matching/api/dependencies.py` note).
- **Expected:** A reproducible Compose demo with semantic matching, and an internal-only engine.
- **Actual:** Once both PRs merge, matching in Compose will fail explicitly ("library not installed"). The engine accepts any caller on its network. PR #71 keeps it unpublished, which mitigates this.
- **Evidence:** The PR #71 file list (read through the GitHub API); the C7 source.
- **Impact:** Integration planning only, before the Week 5 demo.
- **Suggested coordination:** Aryan and Alok agree the image build. Ajendra and Abhishek decide on service auth (for example a shared secret header from an env var).
- **Verification Status:** `CONFIRMED`

---

## 5. Security and Reliability Findings

| Area | Issues |
|---|---|
| Authentication | 001 (Critical), 022, 023, 024 (NV), 044 |
| Authorisation | 002, 003, 005, 007, 010 |
| Input validation | 009, 016, 034, 046 |
| Data exposure | 014, 015, 041 |
| Error handling | 006, 011, 025, 026 |
| Configuration | 012, 017, 019, 041, 048 |
| Sensitive information | 003 (plain-text passwords), 041 (public signing key), 044 |
| Reliability and auditability | 004, 006, 008, 038, 045 |

---

## 6. Testing Report

| # | Command (environment) | Result |
|---|---|---|
| 1 | `python manage.py test apps` (this branch, SQLite) | **60 tests, OK** |
| 2 | `python manage.py test apps` (`feature/my-updates` incl. `ae9884b`) | **81 tests, OK** |
| 3 | `python -m pytest ai_matching/tests` (this branch) | **63 passed** |
| 4 | `python -m pytest ai_matching/tests` (`ae9884b`) | **144 passed, 2 skipped** (opt-in real-model tests) |
| 5 | `RUN_REAL_MODEL_TESTS=1 … pytest ai_matching/tests/test_real_model.py` (`ae9884b`, offline, all-MiniLM-L6-v2) | **2 passed** |
| 6 | CI backend command `pytest --ds=config.settings apps/accounts/tests apps/registry/tests ../e2e/backend/test_controls.py` (SQLite) | **26 passed, 2 skipped** (PostgreSQL-only trigger tests) |
| 7 | `cd database && USE_SQLITE=True pytest --ds=config.settings apps/demand/tests` | **5 passed** |
| 8 | `manage.py check` / `makemigrations --check --dry-run` | No issues / no changes |
| 9 | `manage.py check --deploy` (default env) | **9 warnings** (W018 DEBUG, W012/W016 cookies, W004/W008 HSTS/SSL, 4 schema-naming warnings) |
| 10 | `frontend: npm ci` | Success (477 packages) |
| 11 | `npm run lint` / `npm run typecheck` | Pass / pass |
| 12 | `npm test` (Vitest) | **19 passed** (3 files) |
| 13 | `npm run build` | First run exit 1 (Next.js security notice after a successful compile); rerun **exit 0** |
| 14 | `npm audit --omit=dev` | 1 moderate (`next`) |
| 15 | `manage.py spectacular` + `diff` | Committed schema differs from generated |
| 16 | 22 audit reproduction scenarios (scratch Django `TestCase`s, in-memory DB, outside the repository) | All executed; outcomes quoted as evidence above |

**Test execution total:** 426. That's rows 1–7, 12 and 16 (60 + 81 + 63 + 146 + 2 + 28 + 5 + 19 + 22, including skipped tests). Rows 1–2 and 3–4 run overlapping test files on two revisions, so they're counted once per revision.

**Not executed:**
- Playwright E2E (`e2e/`). It needs the running stack, and Docker Desktop wasn't running.
- The PostgreSQL-only tests: the audit trigger tests and `database/` on Postgres.
- gitleaks and pip-audit (not installed locally; CI runs them).
- Browser checks for ISSUE-022, 023 and 024.

**Observations:** All existing suites pass, but none of them covers the paths in ISSUE-001–011. Passing tests here mean "the tested behaviour works", not "the module is correct".

---

## 7. Recommended Priority Order

**A. Fix before any shared or hosted environment (security blockers)**
1. ISSUE-001: unauthenticated onboarding (Abhishek, Ajendra review).
2. ISSUE-041: configuration names and insecure defaults (Abhishek, Ajendra).
3. ISSUE-003, ISSUE-002: admin privilege escalation and the hard delete (Abhishek).
4. ISSUE-044, ISSUE-023, ISSUE-022: published credentials and fabricated sessions (Priyanka, Abhishek).

**B. Integrity of the journey (before Gate 3)**

5. ISSUE-005, ISSUE-007: evidence verification and requirement-status bypasses.
6. ISSUE-004, ISSUE-006: audit coverage and atomicity.
7. ISSUE-042, ISSUE-008, ISSUE-046: one demand schema with versioning and a criteria format.
8. ISSUE-009, ISSUE-010, ISSUE-011: API regressions and user lifecycle.
9. ISSUE-043, ISSUE-025: hidden records and dashboard figures.
10. ISSUE-045, ISSUE-013: CI coverage and demand tests.

**C. Remaining defects**

11. ISSUE-012, 029, 030, 019, 021, 039, then all Low items.

**D. Verify first:** ISSUE-024; the PostgreSQL part of ISSUE-002.

**E. Optional and tracking:** ISSUE-028, 033, 036, 037, 047, 048.

---

## 8. Items Requiring Team Discussion

These are open questions, not existing decisions.

1. **D-04 eligibility criteria** (Gate 2, 20 Nov): which criteria apply, whether product category is always a hard gate (ISSUE-036), and how unknown values are handled (M6-AC2 vs the seed's `exclude`). Adrika drafts; BNCS approves.
2. **Rules-only fallback conflict:** the Build Manual requires one; MVP M6-AC5 forbids one (`docs/ai/EVALUATION_AND_FALLBACK_DESIGN.md`). Aryan to take this to the mentor and BNCS.
3. **D-05 weights and the semantic-score mapping:** none are approved; the engine refuses to score until they are.
4. **Criteria representation:** structured vs free text, and the "approved criteria version" source for M5-AC4 (ISSUE-046).
5. **D-11:** record `all-MiniLM-L6-v2` in ARCHITECTURE.md §9 after Ajendra's review (ISSUE-037).
6. **Engine deployment ID and service auth:** a new §9 entry, not "D-15" (ISSUE-040, ISSUE-048).
7. **Which demand schema is authoritative** (ISSUE-042).
8. **Readiness module (M4):** Week 3–4 scope, not started (QA-B02). It needs D-03 and a plan.
9. **Pagination:** implement the UI, or use the MVP's large-page fallback (ISSUE-043).
10. **Disclosure handling:** ISSUE-001 (QA-004) lives in a public repository. Agree with Ajendra and Aryan how security findings are tracked privately.
11. **D-19 programme dates:** affect the weekly-report and summary week numbering.

## 9. Final Audit Conclusion

The repository has a working, well-structured foundation:
- The authentication flow and CSRF bootstrap.
- Supplier, product and requirement CRUD with optimistic concurrency.
- A centralised policy module.
- An append-only audit model with a database trigger.
- A frontend that builds, lints and tests cleanly.
- An engine whose matching safeguards are verified by tests on the pending C7 branch.

Every existing test suite that could run here passed.

However, the access-control layer has **one Critical and several High** defects that the existing tests don't cover: unauthenticated privileged onboarding, insecure configuration fallbacks, the admin privilege escalation, the user hard-delete, and the evidence-verification bypass. Audit coverage is also incomplete and not atomic. These should be fixed before any environment outside a developer's machine is used, and certainly before Gate 3. On the integration side, the two demand schemas, the unagreed criteria format and the missing backend endpoints are now the main blockers to demonstrating the full journey. None of these findings is a judgement on any individual; most are the expected seams of parallel work that hasn't been integrated yet.
