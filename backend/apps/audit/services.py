import logging
from apps.audit.models import AuditEvent

logger = logging.getLogger(__name__)


def record_event(actor, action, obj, outcome="success", reason="", changes=None, correlation_id=""):
    """
    Helper to record an append-only audit event in the database.
    """
    try:
        object_type = obj.__class__.__name__.lower() if hasattr(obj, "__class__") else str(obj)
        object_id = str(getattr(obj, "id", getattr(obj, "pk", "")))

        event = AuditEvent.objects.create(
            actor=actor if (actor and actor.is_authenticated) else None,
            action=action,
            object_type=object_type,
            object_id=object_id,
            outcome=outcome,
            reason=reason or "",
            changes=changes or {},
            correlation_id=correlation_id or "",
        )
        return event
    except Exception as e:
        logger.error(f"Failed to record audit event: {e}")
        return None
