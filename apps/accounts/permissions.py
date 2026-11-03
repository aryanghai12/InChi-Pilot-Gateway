from rest_framework.permissions import BasePermission
from apps.accounts.models import Role
from apps.accounts.policy import is_role_allowed, OBJECT_RULES


class RolePermission(BasePermission):
    """
    Evaluates whether the authenticated user's role has permission to perform
    the given action on the specified resource, as defined in policy.py.

    Views using this permission must define:
        policy_resource = "supplier"  # or "assessment", "user", etc.
    """

    ACTION_MAP = {
        "GET": "list",
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "deactivate",
    }

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        resource = getattr(view, "policy_resource", None)
        if not resource:
            # Deny by default if policy_resource is omitted
            return False

        action = getattr(view, "action", None)
        if not action:
            # Fall back to HTTP method mapping
            if hasattr(view, "kwargs") and "pk" in view.kwargs and request.method == "GET":
                action = "retrieve"
            else:
                action = self.ACTION_MAP.get(request.method, "retrieve")

        return is_role_allowed(request.user.role, resource, action)

    def has_object_permission(self, request, view, obj):
        resource = getattr(view, "policy_resource", None)
        action = getattr(view, "action", None)
        rule_key = f"{resource}.{action}"

        rules = OBJECT_RULES.get(rule_key, {})

        # Self-review check
        if rules.get("deny_self_review"):
            if hasattr(obj, "submitted_by") and obj.submitted_by == request.user:
                return False

        # Self-deactivation check
        if rules.get("deny_self_deactivate"):
            if obj == request.user:
                return False

        return True


class IsPlatformAdmin(BasePermission):
    """Allows access only to Platform Administrators."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.PLATFORM_ADMIN
        )


class IsCommercialAnalyst(BasePermission):
    """Allows access only to Commercial Analysts."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.COMMERCIAL_ANALYST
        )


class IsReviewer(BasePermission):
    """Allows access only to Reviewer / Approvers."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.REVIEWER
        )
