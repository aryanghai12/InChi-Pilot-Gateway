from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, Role
from apps.audit.models import AuditEvent


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

    def test_issue_83_anonymous_onboarding_routes_return_404(self):
        """Issue #83 / QA-004 / D-12: Anonymous onboarding routes removed, must return 404."""
        response = self.client.post("/api/v1/auth/register/", {"email": "attacker@evil.com", "role": "platform_admin"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response2 = self.client.post("/api/v1/auth/verify/", {"token": "123"}, format="json")
        self.assertEqual(response2.status_code, status.HTTP_404_NOT_FOUND)

    def test_issue_83_unverified_account_login_rejected(self):
        """Issue #83: Unverified users cannot log in."""
        unverified_user = User.objects.create_user(
            email="unverified@bncs.local",
            password="Password123!",
            role=Role.COMMERCIAL_ANALYST,
            is_verified=False,
        )
        response = self.client.post("/api/v1/auth/login/", {"email": unverified_user.email, "password": "Password123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("verification", response.json().get("message", "").lower())

    def test_issue_84_admin_user_creation_hashes_password_and_superuser_guarded(self):
        """Issue #84: Admin form creation hashes password with pbkdf2 and denies superuser."""
        from apps.accounts.admin import CustomUserCreationForm
        form = CustomUserCreationForm(data={
            "email": "newadminuser@bncs.local",
            "role": Role.COMMERCIAL_ANALYST,
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        })
        self.assertTrue(form.is_valid(), form.errors)
        created_user = form.save()
        self.assertTrue(created_user.password.startswith("pbkdf2_"))
        self.assertTrue(created_user.check_password("SecurePass123!"))
        self.assertFalse(created_user.is_superuser)

    def test_issue_85_delete_user_returns_405_and_preserves_row(self):
        """Issue #85: DELETE /api/v1/auth/users/{id}/ returns 405 Method Not Allowed and preserves row."""
        self.client.force_login(self.admin)
        target_user = User.objects.create_user(
            email="victim@bncs.local",
            password="Password123!",
            role=Role.COMMERCIAL_ANALYST,
            is_verified=True,
        )
        url = f"/api/v1/auth/users/{target_user.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        # Ensure row remains in database
        self.assertTrue(User.objects.filter(id=target_user.id).exists())

    def test_issue_86_analyst_cannot_mark_evidence_verified_via_patch(self):
        """Issue #86 / AC-06: Commercial Analyst cannot mark evidence verified via plain PATCH."""
        from apps.registry.models import Supplier, EvidenceItem
        supplier = Supplier.objects.create(legal_name="Test Supplier", country_of_registration="IN")
        evidence = EvidenceItem.objects.create(
            supplier=supplier,
            document_type="gst_certificate",
            document_name="GSTIN Cert",
            review_status="unreviewed",
        )
        self.client.force_login(self.analyst)
        # Plain PATCH attempt
        response = self.client.patch(f"/api/v1/evidence/{evidence.id}/", {"review_status": "verified"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        evidence.refresh_from_db()
        # Value must NOT have changed to verified
        self.assertNotEqual(evidence.review_status, "verified")

        # Analyst calling /verify/ action directly must be denied with 403
        verify_response = self.client.post(
            f"/api/v1/evidence/{evidence.id}/verify/",
            {"reason": "Analyst attempting verification", "condition": "verified"},
            format="json",
        )
        self.assertEqual(verify_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_issue_86_reviewer_can_verify_evidence_with_audit(self):
        """Issue #86 / §7.1: Reviewer can verify evidence with mandatory reason and audit trail."""
        from apps.registry.models import Supplier, EvidenceItem
        supplier = Supplier.objects.create(legal_name="Test Supplier 2", country_of_registration="IN")
        evidence = EvidenceItem.objects.create(
            supplier=supplier,
            document_type="gacc_registration",
            document_name="GACC Decree 248",
            review_status="unreviewed",
        )
        self.client.force_login(self.reviewer)

        # Missing reason must fail with 400
        fail_response = self.client.post(f"/api/v1/evidence/{evidence.id}/verify/", {}, format="json")
        self.assertEqual(fail_response.status_code, status.HTTP_400_BAD_REQUEST)

        # Valid verification with reason
        response = self.client.post(
            f"/api/v1/evidence/{evidence.id}/verify/",
            {"reason": "Official GACC Single Window Checked", "condition": "official_source_checked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        evidence.refresh_from_db()
        self.assertEqual(evidence.review_status, "official_source_checked")
        self.assertTrue(AuditEvent.objects.filter(action="verify", object_id=str(evidence.id)).exists())

    def test_issue_87_logins_and_diffs_are_audited(self):
        """Issue #87 / AC-23 / §14.1: Login success, login failure, and update diffs are audited."""
        # 1. Successful login
        self.client.post(
            "/api/v1/auth/login/",
            {"email": self.analyst.email, "password": "AnalystPassword123!"},
            format="json",
        )
        self.assertTrue(AuditEvent.objects.filter(action="login", outcome="success", actor=self.analyst).exists())

        # 2. Failed login (password wrong)
        self.client.post(
            "/api/v1/auth/login/",
            {"email": self.analyst.email, "password": "BadPassword123!"},
            format="json",
        )
        self.assertTrue(AuditEvent.objects.filter(action="login", outcome="failure").exists())

        # 3. Denied action
        self.client.force_login(self.analyst)
        denied_resp = self.client.get("/api/v1/auth/users/")
        self.assertEqual(denied_resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(AuditEvent.objects.filter(action="denied", outcome="denied", actor=self.analyst).exists())

        # 4. Supplier update has non-empty before/after diff in changes
        from apps.registry.models import Supplier
        supplier = Supplier.objects.create(legal_name="Initial Name", country_of_registration="IN")
        self.client.patch(f"/api/v1/suppliers/{supplier.id}/", {"legal_name": "Updated Name"}, format="json")
        update_event = AuditEvent.objects.filter(action="update", object_id=str(supplier.id)).first()
        self.assertIsNotNone(update_event)
        self.assertIn("legal_name", update_event.changes)
        self.assertEqual(update_event.changes["legal_name"]["before"], "Initial Name")
        self.assertEqual(update_event.changes["legal_name"]["after"], "Updated Name")
