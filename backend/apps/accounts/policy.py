"""
apps/accounts/policy.py

InChi Pilot Gateway — Role-Based Access Control (RBAC) Policy Matrix.
Source of Truth: docs/MVP_FEATURES.md §5 and docs/ARCHITECTURE.md §5.

STATUS: UNAPPROVED — Awaiting formal BNCS confirmation (D-09).
All permission checks evaluate against this matrix.
"""

from apps.accounts.models import Role

UNAPPROVED = True

# Matrix defining allowed roles per resource and action
PERMISSIONS = {
    # User Management
    "user": {
        "list": [Role.PLATFORM_ADMIN],
        "create": [Role.PLATFORM_ADMIN],
        "retrieve": [Role.PLATFORM_ADMIN],
        "update": [Role.PLATFORM_ADMIN],
        "deactivate": [Role.PLATFORM_ADMIN],
    },

    # Supplier Registry (M2)
    "supplier": {
        "list": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "create": [Role.COMMERCIAL_ANALYST],
        "retrieve": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "update": [Role.COMMERCIAL_ANALYST],
        "complete": [Role.COMMERCIAL_ANALYST],
        "archive": [Role.COMMERCIAL_ANALYST],
    },

    # Product Catalogue (M3)
    "product": {
        "list": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "create": [Role.COMMERCIAL_ANALYST],
        "retrieve": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "update": [Role.COMMERCIAL_ANALYST],
    },

    # Evidence Metadata (M2 / M3)
    "evidence": {
        "list": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "create": [Role.COMMERCIAL_ANALYST],
        "retrieve": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "update": [Role.COMMERCIAL_ANALYST],
        "verify": [Role.REVIEWER],
    },

    # China Readiness Assessment (M4)
    "assessment": {
        "list": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "create": [Role.COMMERCIAL_ANALYST],
        "retrieve": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "update": [Role.COMMERCIAL_ANALYST],
        "submit": [Role.COMMERCIAL_ANALYST],
        "review": [Role.REVIEWER],
        "request_info": [Role.REVIEWER],
    },

    # Buyer Requirements (M5)
    "requirement": {
        "list": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "create": [Role.COMMERCIAL_ANALYST],
        "retrieve": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "update": [Role.COMMERCIAL_ANALYST],
        "mark_ready": [Role.COMMERCIAL_ANALYST],
        "close": [Role.COMMERCIAL_ANALYST],
    },

    # Matching Runs & Explanations (M6)
    "match_run": {
        "create": [Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "list": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "retrieve": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
    },

    # Dispositions (M7)
    "disposition": {
        "create": [Role.REVIEWER],
        "list": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "retrieve": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
    },

    # Opportunities Pipeline (M8)
    "opportunity": {
        "list": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "create": [Role.COMMERCIAL_ANALYST],
        "retrieve": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "update": [Role.COMMERCIAL_ANALYST],
        "transition": [Role.COMMERCIAL_ANALYST, Role.REVIEWER],
        "close": [Role.REVIEWER],
    },

    # Operational Dashboard (M9)
    "dashboard": {
        "view": [Role.PLATFORM_ADMIN, Role.COMMERCIAL_ANALYST, Role.REVIEWER],
    },

    # Audit Events (M10)
    "audit_event": {
        "list": [Role.PLATFORM_ADMIN, Role.REVIEWER],
        "retrieve": [Role.PLATFORM_ADMIN, Role.REVIEWER],
    },
}

# Object-Level Authorization Restrictions
OBJECT_RULES = {
    "assessment.review": {
        "deny_self_review": True,  # Reviewer cannot approve an assessment they submitted
    },
    "user.deactivate": {
        "deny_self_deactivate": True,  # Platform Admin cannot deactivate their own account
    },
}


def is_role_allowed(role: str, resource: str, action: str) -> bool:
    """Helper to check if a given role is allowed to perform action on resource."""
    allowed_roles = PERMISSIONS.get(resource, {}).get(action, [])
    return role in allowed_roles
