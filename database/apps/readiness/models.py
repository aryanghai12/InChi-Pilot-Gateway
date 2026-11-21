import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ReadinessAssessment(models.Model):
    class WorkflowState(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        INFORMATION_REQUIRED = "INFORMATION_REQUIRED", "Information Required"
        REVIEW_COMPLETE = "REVIEW_COMPLETE", "Review Complete"
        ARCHIVED = "ARCHIVED", "Archived"

    class ReadinessOutcome(models.TextChoices):
        READY_FOR_MATCHING = "READY_FOR_MATCHING", "Ready for Matching"
        INFORMATION_REQUIRED = "INFORMATION_REQUIRED", "Information Required"
        NOT_CURRENTLY_ELIGIBLE = "NOT_CURRENTLY_ELIGIBLE", "Not Currently Eligible"

    assessment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(
        "registry.Supplier",
        on_delete=models.PROTECT,
        related_name="readiness_assessments",
    )
    products = models.ManyToManyField(
        "registry.Product",
        related_name="readiness_assessments",
    )
    assessment_version = models.PositiveIntegerField(default=1)
    questionnaire_version = models.CharField(max_length=20, default="2.2")
    workflow_state = models.CharField(
        max_length=30,
        choices=WorkflowState.choices,
        default=WorkflowState.DRAFT,
    )
    readiness_outcome = models.CharField(
        max_length=30,
        choices=ReadinessOutcome.choices,
        blank=True,
        default="",
    )
    readiness_outcome_reason = models.TextField(blank=True, default="")
    contributor_confirmed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_readiness_assessments",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_readiness_assessments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "readiness_assessment"
        constraints = [
            models.UniqueConstraint(
                fields=["supplier", "assessment_version"],
                name="uq_assessment_supplier_version",
            ),
        ]
        indexes = [
            models.Index(fields=["supplier", "workflow_state"]),
            models.Index(fields=["workflow_state", "readiness_outcome"]),
            models.Index(fields=["-updated_at"]),
        ]


class ReadinessResponse(models.Model):
    class ResponseState(models.TextChoices):
        UNKNOWN = "UNKNOWN", "Unknown"
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"
        NONE = "NONE", "No explicit special state"

    response_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        ReadinessAssessment,
        on_delete=models.PROTECT,
        related_name="responses",
    )
    criterion_id = models.CharField(max_length=20)
    response_value = models.JSONField(default=dict, blank=True)
    response_state = models.CharField(
        max_length=20,
        choices=ResponseState.choices,
        default=ResponseState.NONE,
    )
    state_reason = models.TextField(blank=True, default="")
    evidence_condition = models.CharField(max_length=80, blank=True, default="")
    reviewer_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "readiness_response"
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "criterion_id"],
                name="uq_readiness_assessment_criterion",
            ),
        ]
        indexes = [
            models.Index(fields=["assessment", "criterion_id"]),
            models.Index(fields=["response_state"]),
        ]

    def clean(self):
        super().clean()
        if (
            self.response_state == self.ResponseState.NOT_APPLICABLE
            and not self.state_reason.strip()
        ):
            raise ValidationError(
                {"state_reason": "A reason is required for Not Applicable responses."}
            )


class EvidenceRecord(models.Model):
    class EvidenceType(models.TextChoices):
        CERTIFICATE = "CERTIFICATE", "Certificate"
        TEST_REPORT = "TEST_REPORT", "Test Report"
        DECLARATION = "DECLARATION", "Declaration"
        REGISTRY_EXTRACT = "REGISTRY_EXTRACT", "Registry Extract"
        OTHER = "OTHER", "Other"

    class EvidenceCondition(models.TextChoices):
        NOT_PROVIDED = "NOT_PROVIDED", "Not Provided"
        SELF_DECLARED = "SELF_DECLARED", "Self Declared"
        DOCUMENT_RECEIVED_UNVERIFIED = "DOCUMENT_RECEIVED_UNVERIFIED", "Document Received Unverified"
        OFFICIAL_SOURCE_CHECKED = "OFFICIAL_SOURCE_CHECKED", "Official Source Checked"
        THIRD_PARTY_REPORT_RECEIVED_UNVERIFIED = "THIRD_PARTY_REPORT_RECEIVED_UNVERIFIED", "Third-Party Report Received Unverified"
        THIRD_PARTY_REPORT_SOURCE_CHECKED = "THIRD_PARTY_REPORT_SOURCE_CHECKED", "Third-Party Report Source Checked"
        EXPIRED = "EXPIRED", "Expired"
        DISCREPANCY = "DISCREPANCY", "Discrepancy"
        NOT_APPLICABLE = "NOT_APPLICABLE", "Not Applicable"

    evidence_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        ReadinessAssessment,
        on_delete=models.PROTECT,
        related_name="evidence_records",
    )
    criterion_id = models.CharField(max_length=20)
    evidence_type = models.CharField(
        max_length=30,
        choices=EvidenceType.choices,
    )
    evidence_condition = models.CharField(
        max_length=80,
        choices=EvidenceCondition.choices,
        default=EvidenceCondition.DOCUMENT_RECEIVED_UNVERIFIED,
    )
    issuer_source = models.CharField(max_length=255, blank=True, default="")
    reference_number = models.CharField(max_length=255, blank=True, default="")
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    storage_reference = models.CharField(max_length=500, blank=True, default="")
    reviewer_notes = models.TextField(blank=True, default="")
    condition_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="evidence_condition_changes",
    )
    condition_changed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "readiness_evidence"
        indexes = [
            models.Index(fields=["assessment", "criterion_id"]),
            models.Index(fields=["evidence_condition"]),
            models.Index(fields=["expiry_date"]),
        ]


class ReadinessBlocker(models.Model):
    blocker_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        ReadinessAssessment,
        on_delete=models.PROTECT,
        related_name="blockers",
    )
    criterion_id = models.CharField(max_length=20)
    reason_code = models.CharField(max_length=100)
    reason_detail = models.TextField(blank=True, default="")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "readiness_blocker"
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "criterion_id", "reason_code"],
                name="uq_readiness_blocker",
            ),
        ]
        indexes = [
            models.Index(fields=["assessment", "active"]),
        ]


class ReadinessSubmissionSnapshot(models.Model):
    snapshot_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.OneToOneField(
        ReadinessAssessment,
        on_delete=models.PROTECT,
        related_name="submission_snapshot",
    )
    questionnaire_version = models.CharField(max_length=20)
    snapshot = models.JSONField(default=dict)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="readiness_submission_snapshots",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "readiness_submission_snapshot"


class ReadinessAuditEvent(models.Model):
    audit_event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="readiness_audit_events",
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_version = models.PositiveIntegerField(null=True, blank=True)
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    change_summary = models.CharField(max_length=500)
    reason = models.TextField(blank=True, default="")
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "readiness_audit_event"
        indexes = [
            models.Index(fields=["object_type", "object_id"]),
            models.Index(fields=["-occurred_at"]),
        ]
