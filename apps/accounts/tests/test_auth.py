from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, Role


class AuthAndRBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Platform Admin
        self.admin_user = User.objects.create_user(
            email="admin@bncs.local",
            password="AdminPassword123!",
            role=Role.PLATFORM_ADMIN,
            is_staff=True,
            is_verified=True,
        )

        # Create Commercial Analyst
        self.analyst_user = User.objects.create_user(
            email="analyst@bncs.local",
            password="AnalystPassword123!",
            role=Role.COMMERCIAL_ANALYST,
            is_staff=False,
            is_verified=True,
        )

        # Create Reviewer
        self.reviewer_user = User.objects.create_user(
            email="reviewer@bncs.local",
            password="ReviewerPassword123!",
            role=Role.REVIEWER,
            is_staff=False,
            is_verified=True,
        )

    def test_health_check(self):
        """Verify health check probe returns 200."""
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("status"), "ok")

    def test_csrf_cookie_endpoint(self):
        """Verify CSRF bootstrap endpoint sets the cookie."""
        response = self.client.get("/api/v1/auth/csrf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("csrftoken", response.cookies)

    def test_login_success_and_logout(self):
        """Verify login establishes session and logout clears it."""
        # Login
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "analyst@bncs.local", "password": "AnalystPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["user"]["role"], Role.COMMERCIAL_ANALYST)
        self.assertEqual(data["user"]["email"], "analyst@bncs.local")

        # Verify /me works when authenticated
        me_response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.json()["email"], "analyst@bncs.local")

        # Logout
        logout_response = self.client.post("/api/v1/auth/logout/")
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Verify /me is now rejected with 401
        me_after_logout = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me_after_logout.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(me_after_logout.json().get("code"), "not_authenticated")

    def test_login_invalid_credentials(self):
        """Verify invalid credentials return 400 with standard error format."""
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "analyst@bncs.local", "password": "WrongPassword!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data.get("code"), "validation_error")

    def test_registration_and_verification_flow(self):
        """Verify user registration issues a token, and verification activates the account."""
        register_payload = {
            "email": "newuser@bncs.local",
            "password": "SecurePassword123!",
            "first_name": "New",
            "last_name": "User",
            "role": Role.COMMERCIAL_ANALYST,
        }
        reg_response = self.client.post("/api/v1/auth/register/", register_payload, format="json")
        self.assertEqual(reg_response.status_code, status.HTTP_201_CREATED)
        reg_data = reg_response.json()
        token = reg_data.get("verification_token")
        self.assertIsNotNone(token)
        self.assertFalse(reg_data["user"]["is_verified"])

        # Check verification status before verify
        status_response = self.client.get("/api/v1/auth/verify/status/?email=newuser@bncs.local")
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertFalse(status_response.json()["is_verified"])

        # Perform verification
        verify_response = self.client.post(
            "/api/v1/auth/verify/",
            {"email": "newuser@bncs.local", "token": token},
            format="json",
        )
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.json()["user"]["is_verified"])

        # Now check verification status is True
        status_after = self.client.get("/api/v1/auth/verify/status/?email=newuser@bncs.local")
        self.assertTrue(status_after.json()["is_verified"])

    def test_rbac_user_management_access(self):
        """
        Verify only Platform Admin can access user management API.
        Commercial Analyst and unauthenticated users receive 403 or 401.
        """
        # Unauthenticated -> 401
        unauth_response = self.client.get("/api/v1/auth/users/")
        self.assertEqual(unauth_response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Login as Commercial Analyst
        self.client.force_login(self.analyst_user)
        analyst_response = self.client.get("/api/v1/auth/users/")
        # Commercial Analyst is denied user management access -> 403
        self.assertEqual(analyst_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(analyst_response.json().get("code"), "permission_denied")

        # Login as Platform Admin -> 200 OK
        self.client.force_login(self.admin_user)
        admin_response = self.client.get("/api/v1/auth/users/")
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(admin_response.json().get("results", [])), 3)

    def test_admin_cannot_deactivate_self(self):
        """Verify an admin cannot deactivate their own account."""
        self.client.force_login(self.admin_user)
        response = self.client.post(f"/api/v1/auth/users/{self.admin_user.id}/deactivate/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json().get("code"), "permission_denied")
