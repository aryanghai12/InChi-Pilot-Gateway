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
        """Negative test: Invalid password rejected with standard error shape."""
        payload = {
            "email": "analyst@bncs.local",
            "password": "WrongPassword!",
        }
        response = self.client.post("/api/v1/auth/login/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
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
