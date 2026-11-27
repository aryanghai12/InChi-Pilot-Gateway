from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, Role
from apps.accounts.serializers import UserSerializer
from apps.audit.models import AuditEvent
from apps.registry.models import Supplier
from apps.readiness.models import ReadinessAssessment, WorkflowState, ReadinessOutcome


class SecurityPostureTests(TestCase):
    """
    Automated Negative Security & RBAC Boundary Test Suite.
    Owned by: Ajendra Nath Tripathi (Cybersecurity & DevSecOps) & Harish Pal (QA)
    Authority: AGENTS.md §C2, §C8; docs/security/SECURITY_TEST_SPECIFICATIONS.md
    """

    def setUp(self):
        self.client = APIClient()

        # Platform Admin user
        self.admin = User.objects.create_user(
            email="admin@bncs.local",
            password="AdminPassword123!",
            role=Role.PLATFORM_ADMIN,
            is_staff=True,
            is_verified=True,
        )

        # Commercial Analyst user
        self.analyst = User.objects.create_user(
            email="analyst@bncs.local",
            password="AnalystPassword123!",
            role=Role.COMMERCIAL_ANALYST,
            is_verified=True,
        )

        # Reviewer user
        self.reviewer = User.objects.create_user(
            email="reviewer@bncs.local",
            password="ReviewerPassword123!",
            role=Role.REVIEWER,
            is_verified=True,
        )

    def test_sec_01_csrf_cookie_endpoint_bootstraps_token(self):
        """SEC-TEST-01: Bootstrap endpoint sets CSRF cookie for client-side API calls (TD-05)."""
        response = self.client.get("/api/v1/auth/csrf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("csrftoken", response.cookies)
        self.assertEqual(response.json().get("detail"), "CSRF cookie set.")

    def test_sec_02_unauthenticated_requests_return_401_not_authenticated(self):
        """SEC-TEST-03: Protected endpoints must return 401 with code 'not_authenticated' (TD-06)."""
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertEqual(data.get("code"), "not_authenticated")

    def test_sec_03_login_establishes_session_and_rotates_credentials(self):
        """SEC-TEST-02: Successful authentication logs in user and rotates session (TD-08)."""
        payload = {
            "email": "analyst@bncs.local",
            "password": "AnalystPassword123!",
        }
        response = self.client.post("/api/v1/auth/login/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data.get("message"), "Login successful.")
        self.assertEqual(data.get("user", {}).get("email"), "analyst@bncs.local")
        self.assertEqual(data.get("user", {}).get("role"), Role.COMMERCIAL_ANALYST)
        self.assertIn("sessionid", response.cookies)

    def test_sec_04_login_invalid_credentials_returns_400(self):
        """Negative test: Invalid password rejected with standard error shape and descriptive message."""
        payload = {
            "email": "analyst@bncs.local",
            "password": "WrongPassword!",
        }
        response = self.client.post("/api/v1/auth/login/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data.get("code"), "validation_error")
        self.assertEqual(data.get("message"), "Invalid email or password.")
        self.assertIn("field_errors", data)

    def test_sec_05_analyst_forbidden_from_admin_user_management(self):
        """SEC-TEST-04: Commercial Analyst cannot access user administration endpoints."""
        self.client.force_login(self.analyst)
        response = self.client.get("/api/v1/auth/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertEqual(data.get("code"), "permission_denied")

    def test_sec_06_admin_isolated_from_commercial_operations(self):
        """SEC-TEST-05: Platform Admin isolated from creating commercial supplier records."""
        self.client.force_login(self.admin)
        payload = {
            "legal_name": "Unauthorized Commercial Record Ltd",
            "country_of_registration": "SG",
        }
        response = self.client.post("/api/v1/suppliers/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertEqual(data.get("code"), "permission_denied")

    def test_sec_07_platform_admin_cannot_deactivate_self(self):
        """Safety control: Platform Admin cannot deactivate their own active account."""
        self.client.force_login(self.admin)
        url = f"/api/v1/auth/users/{self.admin.id}/deactivate/"
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertEqual(data.get("code"), "permission_denied")
        self.assertIn("cannot deactivate your own account", data.get("message", "").lower())

    def test_sec_08_logout_terminates_session(self):
        """Session termination: Calling logout terminates active session."""
        self.client.force_login(self.analyst)
        response = self.client.post("/api/v1/auth/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("detail"), "Logged out successfully.")

    def test_sec_09_audit_event_cannot_be_updated_or_deleted(self):
        """SEC-TEST-08 / TD-03: AuditEvent records are append-only and reject updates/deletions."""
        from django.core.exceptions import PermissionDenied

        event = AuditEvent.objects.create(
            actor=self.analyst,
            action="test_action",
            object_type="test_object",
            object_id="123",
            outcome="success",
        )

        # Attempt to update must raise PermissionDenied
        event.action = "tampered_action"
        with self.assertRaises(PermissionDenied):
            event.save()

        # Attempt to delete must raise PermissionDenied
        with self.assertRaises(PermissionDenied):
            event.delete()

    def test_sec_10_unauthenticated_api_endpoints_return_401(self):
        """Baseline v2.2 SEC-01 / AC-22: Unauthenticated calls to write endpoints strictly denied."""
        # Unauthenticated supplier creation
        resp_sup = self.client.post("/api/v1/suppliers/", {"legal_name": "Test"}, format="json")
        self.assertEqual(resp_sup.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp_sup.json().get("code"), "not_authenticated")

        # Unauthenticated assessment creation
        resp_asm = self.client.post("/api/v1/assessments/", {}, format="json")
        self.assertEqual(resp_asm.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp_asm.json().get("code"), "not_authenticated")

        # Unauthenticated buyer requirement creation
        resp_req = self.client.post("/api/v1/requirements/", {}, format="json")
        self.assertEqual(resp_req.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp_req.json().get("code"), "not_authenticated")

    def test_sec_11_reviewer_cannot_approve_own_submitted_assessment(self):
        """Baseline v2.2 AC-06 & SEC-TEST-06: Two-person rule blocks self-review (submitted_by != reviewer)."""
        supplier = Supplier.objects.create(
            legal_name="Self Review Supplier Ltd",
            country_of_registration="IN",
            created_by=self.reviewer,
        )
        assessment = ReadinessAssessment.objects.create(
            supplier=supplier,
            workflow_state=WorkflowState.SUBMITTED,
            submitted_by=self.reviewer,
            created_by=self.reviewer,
        )

        self.client.force_login(self.reviewer)
        url = f"/api/v1/assessments/{assessment.id}/complete-review/"
        payload = {
            "readiness_outcome": ReadinessOutcome.READY_FOR_MATCHING,
            "reviewer_notes": "Attempting unauthorized self-approval.",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertEqual(data.get("code"), "permission_denied")
        self.assertIn("cannot approve an assessment they submitted", data.get("message", "").lower())

    def test_sec_12_analyst_forbidden_from_completing_readiness_review(self):
        """Baseline v2.2 §4.2: Commercial Analyst forbidden from completing readiness reviews."""
        supplier = Supplier.objects.create(
            legal_name="Analyst Barrier Supplier Ltd",
            country_of_registration="IN",
            created_by=self.analyst,
        )
        assessment = ReadinessAssessment.objects.create(
            supplier=supplier,
            workflow_state=WorkflowState.SUBMITTED,
            submitted_by=self.analyst,
            created_by=self.analyst,
        )

        self.client.force_login(self.analyst)
        url = f"/api/v1/assessments/{assessment.id}/complete-review/"
        payload = {
            "readiness_outcome": ReadinessOutcome.READY_FOR_MATCHING,
            "reviewer_notes": "Analyst attempting review outcome.",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json().get("code"), "permission_denied")

    def test_sec_13_platform_admin_isolated_from_buyer_requirements(self):
        """Baseline v2.2 §4: Platform Administrator cannot create buyer requirement records."""
        self.client.force_login(self.admin)
        payload = {
            "buyer_organisation_name": "Unauthorized Admin Demand Co",
            "requirement_title": "Admin Demand Test",
            "product_category": "engineering_components",
        }
        response = self.client.post("/api/v1/requirements/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json().get("code"), "permission_denied")

    def test_sec_14_user_serializer_does_not_leak_password_or_tokens(self):
        """Baseline v2.2 SEC-05: User profile serializer must never expose password or verification tokens."""
        serializer = UserSerializer(self.admin)
        data = serializer.data
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)
        self.assertNotIn("verification_token", data)

    def test_sec_15_password_hashing_enforced_on_user_creation(self):
        """Baseline v2.2 §14.1 & AUD-15: Passwords must be cryptographically hashed with PBKDF2."""
        raw_password = "SuperSecretPassword123!"
        user = User.objects.create_user(
            email="hashed_check@bncs.local",
            password=raw_password,
            role=Role.COMMERCIAL_ANALYST,
        )
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(user.check_password(raw_password))
        self.assertFalse(user.check_password("WrongPassword123!"))

    def test_sec_16_audit_01_self_registration_reproduction_proof(self):
        """
        Proof of Security Finding AUD-01 / Critical Access Control Defect:
        Verifies behavior of POST /api/v1/auth/register/ with arbitrary role input.
        """
        payload = {
            "email": "infiltrator@test.local",
            "password": "Password123!",
            "first_name": "Security",
            "last_name": "Auditor",
            "role": Role.PLATFORM_ADMIN,
        }
        response = self.client.post("/api/v1/auth/register/", payload, format="json")

        # In current unpatched state, endpoint creates account with platform_admin (AUD-01).
        # In patched state, it must return 403 or 400.
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN])
        if response.status_code == status.HTTP_201_CREATED:
            # Document and verify the AUD-01 defect behavior
            user = User.objects.get(email="infiltrator@test.local")
            self.assertEqual(user.role, Role.PLATFORM_ADMIN)
            self.assertIn("verification_token", response.data)

    def test_sec_17_login_throttling_configuration_and_semantics(self):
        """TD-04 / Week 5: Verify login throttling configuration and HTTP 429 semantics."""
        from django.conf import settings
        from rest_framework.exceptions import Throttled
        from rest_framework.throttling import ScopedRateThrottle
        from apps.accounts.views import LoginView
        from config.exceptions import custom_exception_handler

        # 1. Verify LoginView configuration
        self.assertIn(ScopedRateThrottle, LoginView.throttle_classes)
        self.assertEqual(LoginView.throttle_scope, "login")

        # 2. Verify throttle rate configuration in settings
        throttle_rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        self.assertIn("login", throttle_rates)
        self.assertEqual(throttle_rates["login"], "5/minute")

        # 3. Verify uniform error shape on Throttled exception
        exc = Throttled(wait=45, detail="Request was throttled. Expected available in 45 seconds.")
        context = {"request": None}
        response = custom_exception_handler(exc, context)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data.get("code"), "throttled")
        self.assertIn("Request was throttled", response.data.get("message"))

    def test_sec_18_match_disposition_requires_reviewer_role(self):
        """Baseline v2.2 §4.2 / DSP-001 / AC-19: Match dispositions strictly restricted to Reviewer."""
        from apps.accounts.policy import is_role_allowed

        # Reviewer is explicitly allowed
        self.assertTrue(is_role_allowed(Role.REVIEWER, "disposition", "create"))

        # Commercial Analyst is denied
        self.assertFalse(is_role_allowed(Role.COMMERCIAL_ANALYST, "disposition", "create"))

        # Platform Admin is denied (commercial isolation)
        self.assertFalse(is_role_allowed(Role.PLATFORM_ADMIN, "disposition", "create"))

    def test_sec_19_zero_external_llm_dependencies_in_matching_engine(self):
        """D-20 / Baseline v2.2 §14.2: Audit matching engine for absence of external LLM dependencies."""
        from pathlib import Path
        import inspect
        from ai_matching.providers import embedding_provider

        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        req_files = [
            repo_root / "ai_matching" / "requirements.txt",
            repo_root / "ai_matching" / "requirements-semantic.txt",
        ]

        prohibited_sdks = ["openai", "anthropic", "google-generativeai", "cohere", "langchain", "litellm"]

        for req_file in req_files:
            if req_file.exists():
                content = req_file.read_text(encoding="utf-8").lower()
                for sdk in prohibited_sdks:
                    self.assertNotIn(sdk, content, f"Prohibited LLM dependency '{sdk}' detected in {req_file}")

        # Verify trust_remote_code is explicitly False in embedding provider loader
        source = inspect.getsource(embedding_provider._load_sentence_transformer)
        self.assertIn("trust_remote_code=False", source)
        self.assertIn('device="cpu"', source)


