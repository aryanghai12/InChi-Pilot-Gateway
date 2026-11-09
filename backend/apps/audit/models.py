import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class AuditEvent(models.Model):
    """
    Append-only audit log for material actions and lifecycle events.
    Complies with M10 and build manual traceability requirements.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=50, db_index=True)
    object_type = models.CharField(max_length=50, db_index=True)
    object_id = models.CharField(max_length=50, db_index=True)
    outcome = models.CharField(max_length=20, default="success")
    reason = models.TextField(blank=True, default="")
    changes = models.JSONField(default=dict, blank=True)
    correlation_id = models.CharField(max_length=50, blank=True, default="")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Audit Event"
        verbose_name_plural = "Audit Events"
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        """Application-level immutability: Prevent updates to existing records (TD-03)."""
        if not self._state.adding and self.pk:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("AuditEvent records are append-only and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Application-level immutability: Prevent deletion of audit records (TD-03)."""
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("AuditEvent records are append-only and cannot be deleted.")

    def __str__(self):
        actor_email = self.actor.email if self.actor else "system"
        return f"[{self.timestamp}] {actor_email} -> {self.action} on {self.object_type}:{self.object_id} ({self.outcome})"
