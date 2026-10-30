from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.models import User
from apps.accounts.permissions import IsPlatformAdmin, RolePermission
from apps.accounts.serializers import (
    UserSerializer,
    LoginSerializer,
    RegisterSerializer,
    VerifyAccountSerializer,
    UserAdminUpdateSerializer,
)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfCookieView(APIView):
    """
    Bootstrap endpoint to set the CSRF cookie on initial frontend load.
    The client reads the csrftoken cookie and sends it as X-CSRFToken.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Set CSRF Cookie",
        description="Bootstraps the CSRF cookie so the frontend can send X-CSRFToken headers on subsequent requests.",
        responses={200: OpenApiResponse(description="CSRF cookie set successfully.")},
    )
    def get(self, request):
        return Response({"detail": "CSRF cookie set."})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    """
    Authenticate internal user, establish session, and rotate CSRF token.
    Enforces explicit CSRF protection on login.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Internal User Login",
        description="Authenticates the user using email and password, creates an active session and rotates the CSRF token.",
        request=LoginSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Invalid credentials or inactive account."),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        login(request, user)  # Rotates session key and CSRF token

        return Response(
            {
                "message": "Login successful.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Terminate session and clear session cookies.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="User Logout",
        description="Terminates the user's current session and flushes session data.",
        request=None,
        responses={200: OpenApiResponse(description="Logged out successfully.")},
    )
    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    Retrieve current authenticated user details and active role.
    Used by the frontend for role-aware routing and navigation shells.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Current Authenticated User",
        description="Returns the profile and role details of the currently signed-in user.",
        responses={200: UserSerializer},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    Register or onboard a new internal user account with assigned role.
    Account is set to unverified with an activation/verification token generated.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Internal User Registration",
        description="Registers a new user record with role assignment and issues a verification token.",
        request=RegisterSerializer,
        responses={201: UserSerializer},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully. Please complete verification.",
                "user": UserSerializer(user).data,
                "verification_token": user.verification_token,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyAccountView(APIView):
    """
    Verify internal user account using the generated verification token.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify Account Token",
        description="Validates the verification token for a registered account and marks the account as verified.",
        request=VerifyAccountSerializer,
        responses={
            200: OpenApiResponse(description="Account verified successfully."),
            400: OpenApiResponse(description="Invalid or expired token."),
        },
    )
    def post(self, request):
        serializer = VerifyAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user.is_verified = True
        user.verification_token = None
        user.version += 1
        user.save(update_fields=["is_verified", "verification_token", "version", "updated_at"])

        return Response(
            {
                "message": "Account successfully verified. You may now log in.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Check Verification Status",
        description="Check whether a specific email account has already been verified.",
        request=None,
        responses={200: OpenApiResponse(description="Returns verification status.")},
    )
    def get(self, request):
        email = request.query_params.get("email", "").strip().lower()
        if not email:
            return Response(
                {"code": "validation_error", "message": "Email query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            return Response({"email": user.email, "is_verified": user.is_verified, "is_active": user.is_active})
        except User.DoesNotExist:
            return Response(
                {"code": "not_found", "message": "No account found with this email."},
                status=status.HTTP_404_NOT_FOUND,
            )


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Dedicated user management endpoints for Platform Administrators.
    Allows listing all users, updating roles, and activating or deactivating accounts.
    """

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [IsPlatformAdmin, RolePermission]
    policy_resource = "user"
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return UserAdminUpdateSerializer
        return UserSerializer

    @extend_schema(
        summary="Deactivate User Account",
        description="Deactivates an internal user account immediately revoking access. A user cannot deactivate themselves.",
    )
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        user = self.get_object()

        # Prevent admin from deactivating their own account
        if user == request.user:
            return Response(
                {"code": "permission_denied", "message": "You cannot deactivate your own account."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.is_active = False
        user.version += 1
        user.save(update_fields=["is_active", "version", "updated_at"])

        return Response(
            {"message": f"User {user.email} has been deactivated.", "user": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Activate User Account",
        description="Reactivates a previously deactivated user account.",
    )
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.version += 1
        user.save(update_fields=["is_active", "version", "updated_at"])

        return Response(
            {"message": f"User {user.email} has been activated.", "user": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )
