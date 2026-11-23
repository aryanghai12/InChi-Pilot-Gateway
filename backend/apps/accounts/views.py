import uuid
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
    UserCreateSerializer,
    UserAdminUpdateSerializer,
)
from apps.audit.services import record_event


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
    Emits audit events for successful and failed authentication attempts (AC-23, §14.1).
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
        correlation_id = getattr(request, "correlation_id", str(uuid.uuid4()))
        serializer = LoginSerializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Audit failed login attempt (NEVER log credentials or raw passwords)
            attempted_email = request.data.get("email", "").strip().lower() if isinstance(request.data, dict) else "unknown"
            record_event(
                actor=None,
                action="login",
                obj=attempted_email or "unknown",
                outcome="failure",
                reason=f"Failed login attempt: {str(e)}",
                correlation_id=correlation_id,
            )
            raise e

        user = serializer.validated_data["user"]
        login(request, user)  # Rotates session key and CSRF token

        # Audit successful login
        record_event(
            actor=user,
            action="login",
            obj=user,
            outcome="success",
            reason=f"User {user.email} authenticated successfully.",
            correlation_id=correlation_id,
        )

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


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Dedicated user management endpoints for Platform Administrators.
    Allows listing all users, provisioning new users, updating roles, and activating or deactivating accounts.
    Users cannot be deleted; DELETE returns HTTP 405 Method Not Allowed (ARCHITECTURE §5).
    """

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [IsPlatformAdmin, RolePermission]
    policy_resource = "user"
    serializer_class = UserSerializer
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserAdminUpdateSerializer
        return UserSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Hard deletion of user accounts is prohibited per ARCHITECTURE §5.
        Use POST /api/v1/auth/users/{id}/deactivate/ instead.
        """
        correlation_id = getattr(request, "correlation_id", str(uuid.uuid4()))
        return Response(
            {
                "code": "method_not_allowed",
                "message": "User accounts cannot be deleted. Use POST /deactivate/ to deactivate an account.",
                "field_errors": {},
                "correlation_id": correlation_id,
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def perform_create(self, serializer):
        user = serializer.save()
        correlation_id = getattr(self.request, "correlation_id", "")
        record_event(
            actor=self.request.user,
            action="create",
            obj=user,
            outcome="success",
            reason=f"User {user.email} provisioned with role {user.role}.",
            changes={
                "email": {"before": None, "after": user.email},
                "role": {"before": None, "after": user.role},
            },
            correlation_id=correlation_id,
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        old_data = {field: getattr(instance, field) for field in serializer.validated_data}
        user = serializer.save()
        changes = {}
        for field, old_val in old_data.items():
            new_val = getattr(user, field)
            if old_val != new_val:
                changes[field] = {"before": str(old_val), "after": str(new_val)}

        correlation_id = getattr(self.request, "correlation_id", "")
        record_event(
            actor=self.request.user,
            action="update",
            obj=user,
            outcome="success",
            reason=f"User {user.email} updated by administrator.",
            changes=changes,
            correlation_id=correlation_id,
        )

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

        old_active = user.is_active
        user.is_active = False
        user.version += 1
        user.save(update_fields=["is_active", "version", "updated_at"])

        record_event(
            actor=request.user,
            action="deactivate",
            obj=user,
            outcome="success",
            reason=f"User {user.email} deactivated by administrator.",
            changes={"is_active": {"before": old_active, "after": False}},
            correlation_id=getattr(request, "correlation_id", ""),
        )

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
        old_active = user.is_active
        user.is_active = True
        user.version += 1
        user.save(update_fields=["is_active", "version", "updated_at"])

        record_event(
            actor=request.user,
            action="activate",
            obj=user,
            outcome="success",
            reason=f"User {user.email} reactivated by administrator.",
            changes={"is_active": {"before": old_active, "after": True}},
            correlation_id=getattr(request, "correlation_id", ""),
        )

        return Response(
            {"message": f"User {user.email} has been activated.", "user": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )
