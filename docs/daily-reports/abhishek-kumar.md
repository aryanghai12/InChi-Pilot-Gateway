# Weekly reports — Abhishek Kumar

Application Backend and Access-Control Engineer · Process, template and rules: [README.md](README.md)

Only Abhishek Kumar writes in this file. Newest entry first.

<!-- Add new entries directly below this line. -->

## Week 3 - 9-13 November 2026

**Completed**
- M2 Supplier Registry: Implemented `Supplier` model, Draft/Complete/Archived lifecycle, optimistic concurrency tracking with `version` field, and 409 Conflict handling - merged - evidence: [apps/registry/models.py](../../backend/apps/registry/models.py), [apps/registry/views.py](../../backend/apps/registry/views.py).
- M3 Product Catalogue: Implemented `Product` model linked to suppliers, Mandarin attributes (`product_name_zh`, `short_description_zh`), automated translation status tracking, MOQ/pricing validations, and technical capacity/lead-time constraints - merged - evidence: [apps/registry/models.py](../../backend/apps/registry/models.py).
- Evidence Metadata: Implemented `EvidenceItem` model supporting both supplier and product document metadata references (EVD-01 to EVD-10) - merged - evidence: [apps/registry/models.py](../../backend/apps/registry/models.py).
- M10 Audit Events: Implemented append-only `AuditEvent` model and `record_event()` service logging every state transition and administrative action with correlation IDs - merged - evidence: [apps/audit/](../../backend/apps/audit/).
- Frontend Integration & Compatibility: Resolved exception handler message masking in `config/exceptions.py` so descriptive validation/auth messages pass through cleanly; added dual-compatibility in `apps/registry/serializers.py` (support for `supplier_id`/`product_id` aliases, nested `contact_details`, address alias, Title Case enum normalization) - merged - evidence: [config/exceptions.py](../../backend/config/exceptions.py), [apps/registry/serializers.py](../../backend/apps/registry/serializers.py).
- Buyer Demand Field Dictionary Alignment: Reviewed Adrika's Buyer Requirement Field Dictionary v1.2 and v1.4, confirmed 100% alignment with `MVP_FEATURES.md (M5)` (3 statuses: Draft / Ready for matching / Closed, direct `buyer_organisation_name`, buyer verification excluded for MVP, explicit `mark_ready` gate) - completed - evidence: team review record.

**Meetings, reviews and coordination**
- Frontend integration review: Analyzed Next.js frontend (`frontend/src/`) against backend endpoints; communicated DRF pagination unwrapping requirements (`res.results || res`), D-12 admin-provisioned auth model, and module roadmap to Priyanka Singh - completed.
- Buyer requirements alignment: Coordinated with Adrika T Kumar on Buyer Requirement Field Dictionary v1.4; finalized validation gate rules for M5 - completed.
- Matching architecture review: Aligned with Alok Tiwari regarding `backend/ai_matching/` separation and backend orchestration interface - completed.

**In progress**
- Module M5 (Buyer Demand / Procurement Requirements): Implementation of `backend/apps/demand/` (`BuyerRequirement`, `RequirementCriterion`, `RequirementEvidence` models, serializers, `mark_ready` gate, viewsets) - M5-AC1 to M5-AC10 - models and serializers being drafted.
- China Readiness Assessment (M4): Architecture and integration design on hold pending Adrika's finalized question schema and field dictionary.

**Tests and validation**
- `cd backend && .\venv\Scripts\python manage.py test apps` -> Ran 22 tests in 31.757s. OK (100% passing).
- Validated auth login error passthrough, supplier lifecycle transitions, product catalogue validations, optimistic concurrency conflict detection, and frontend payload compatibility tests.

**Blocked, dependencies and decisions needed**
- China Readiness Assessment (M4) question schema and field dictionary - waiting on Adrika T Kumar.

**Next week**
- Implement Module M5 (`apps/demand/`) including models, serializers, validation rules (`mark_ready` gate), viewsets, and automated tests.
- Implement `apps/dashboard/summary/` aggregate metrics endpoint once M5 is complete.
- Coordinate matching orchestration endpoints with Alok's `backend/ai_matching/` engine.

## Week 2 - 2-6 November 2026

**Completed**
- M1 Authentication & Access Control: Implemented custom `User` model with UUID v4 primary keys, PBKDF2 password hashing, session authentication, and CSRF token rotation (TD-08) - merged - evidence: [apps/accounts/](../../backend/apps/accounts/).
- Central RBAC Policy: Created `apps/accounts/policy.py` containing complete role-permission matrix (`platform_admin`, `commercial_analyst`, `reviewer`) with deny-by-default `RolePermission` enforcement - merged - evidence: [apps/accounts/policy.py](../../backend/apps/accounts/policy.py), [apps/accounts/permissions.py](../../backend/apps/accounts/permissions.py).
- Initial Administrator Provisioning: Implemented `manage.py create_platform_admin` command with password validation and audit logging - merged - evidence: [apps/accounts/management/commands/create_platform_admin.py](../../backend/apps/accounts/management/commands/create_platform_admin.py).
- Standardized Error Handling: Implemented custom DRF exception handler in `config/exceptions.py` enforcing standard error envelope (`code`, `message`, `field_errors`, `correlation_id`) - merged - evidence: [config/exceptions.py](../../backend/config/exceptions.py).
- CSRF Bootstrap Endpoint: Implemented `GET /api/v1/auth/csrf/` to support client-side token bootstrapping - merged - evidence: [apps/accounts/views.py](../../backend/apps/accounts/views.py).

**Meetings, reviews and coordination**
- Gate 1 coordination: Participated in Sprint Review with Aryan Ghai, Priyanka Singh, and Ajendra Nath Tripathi to review Gate 1 vertical slice - completed.
- Frontend contract alignment: Agreed with Priyanka on single-origin Next.js proxy rewrites (`/api/:path*`) to forward requests to Django backend on `:8000` - completed.

**In progress**
- Registry data models and serialization design for M2 (Suppliers) and M3 (Products).

**Tests and validation**
- `cd backend && .\venv\Scripts\python manage.py test apps.accounts` -> All security posture, login session, user administration, and self-deactivation protection tests passed.

**Blocked, dependencies and decisions needed**
- None.

**Next week**
- Implement Module M2 (Supplier Registry), Module M3 (Product Catalogue), and Module M10 (Audit Events).

## Week 1 - 26-30 October 2026

**Completed**
- Django 5.1 Project Setup: Initialized backend project structure with modular apps (`accounts`, `registry`, `readiness`, `demand`, `matching`, `opportunities`, `audit`, `dashboard`) - merged - evidence: [backend/config/](../../backend/config/).
- Configuration & Security Baselines: Established `.env.example`, settings separation, security middleware, session lifetime controls, and CORS/CSRF trusted origins - merged - evidence: [backend/.env.example](../../backend/.env.example), [backend/config/settings.py](../../backend/config/settings.py).
- Database Infrastructure Baseline: Configured development SQLite fallback and production PostgreSQL integration via `DATABASE_URL` - merged.

**Meetings, reviews and coordination**
- Sprint Start meeting with team; reviewed `ARCHITECTURE.md` and `MVP_FEATURES.md` specifications - completed.
- Security alignment: Reviewed access control matrix and threat model with Ajendra Nath Tripathi - completed.

**In progress**
- Custom User model and authentication system design.

**Tests and validation**
- `python manage.py check` -> 0 issues identified.

**Blocked, dependencies and decisions needed**
- Formal approval of proposed revised timeline (D-19) - waiting on BNCS and University Coordinator.

**Next week**
- Implement M1 Authentication, Access Control, and Gate 1 vertical slice.
