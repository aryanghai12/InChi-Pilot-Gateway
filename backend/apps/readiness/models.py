import uuid
from django.db import models
from django.conf import settings
from apps.registry.models import Supplier, Product


class WorkflowState(models.TextChoices):
    """
    Agreed M4 Workflow States per Mentor Baseline v2.2 §4.
    """
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under Review"
    INFORMATION_REQUIRED = "information_required", "Information Required"
    REVIEW_COMPLETE = "review_complete", "Review Complete"
    ARCHIVED = "archived", "Archived"


class ReadinessOutcome(models.TextChoices):
    """
    Agreed M4 Final Readiness Outcomes per Mentor Baseline v2.2 §8.1.
    Strictly qualitative categorical outcomes — NO percentage or point scores.
    """
    READY_FOR_MATCHING = "ready_for_matching", "Ready for matching"
    INFORMATION_REQUIRED = "information_required", "Information required"
    NOT_CURRENTLY_ELIGIBLE = "not_currently_eligible", "Not currently eligible"


class EvidenceCondition(models.TextChoices):
    """
    9 Categorical Evidence Conditions per Mentor Baseline v2.2 §7.
    """
    NOT_PROVIDED = "not_provided", "Not Provided"
    SELF_DECLARED = "self_declared", "Self Declared"
    DOCUMENT_RECEIVED_UNVERIFIED = "document_received_unverified", "Document Received (Unverified)"
    OFFICIAL_SOURCE_CHECKED = "official_source_checked", "Official Source Checked"
    THIRD_PARTY_REPORT_RECEIVED_UNVERIFIED = "third_party_report_received_unverified", "Third Party Report Received (Unverified)"
    THIRD_PARTY_REPORT_SOURCE_CHECKED = "third_party_report_source_checked", "Third Party Report Source Checked"
    EXPIRED = "expired", "Expired"
    DISCREPANCY = "discrepancy", "Discrepancy"
    NOT_APPLICABLE = "not_applicable", "Not Applicable"


class ReadinessAssessment(models.Model):
    """
    M4: China Readiness Assessment Model.
    Captures compliance evaluation, 18-criterion questionnaire (CR-01 to CR-18),
    linked evidence records, and reviewer disposition.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core Associations (Linked Supplier & Products per Baseline v2.2 §5 & §6.1)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="readiness_assessments",
        db_index=True,
    )
    linked_products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="readiness_assessments",
    )

    questionnaire_version = models.CharField(max_length=20, default="2.2")

    # Workflow & Disposition
    workflow_state = models.CharField(
        max_length=30,
        choices=WorkflowState.choices,
        default=WorkflowState.DRAFT,
        db_index=True,
    )
    readiness_outcome = models.CharField(
        max_length=30,
        choices=ReadinessOutcome.choices,
        null=True,
        blank=True,
        db_index=True,
    )

    # Roles & Ownership
    assigned_analyst = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_assessments",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submitted_assessments",
        help_text="Tracked to enforce deny_self_review (reviewer cannot approve own submission).",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_assessments",
    )

    # Assessment Content & Audit Trails
    answers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Responses for CR-01 through CR-18 stored as key-value pairs or structured list.",
    )
    submission_notes = models.TextField(blank=True, default="")
    reviewer_notes = models.TextField(blank=True, default="")
    information_request_notes = models.TextField(blank=True, default="")

    # Optimistic Concurrency Control
    version = models.PositiveIntegerField(
        default=1,
        help_text="Optimistic concurrency tracking version.",
    )

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_assessments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Readiness Assessment"
        verbose_name_plural = "Readiness Assessments"

    def __str__(self):
        supplier_name = self.supplier.legal_name if self.supplier else "Unknown"
        return f"Assessment for {supplier_name} [{self.get_workflow_state_display()}]"

    def get_normalized_answers(self) -> dict:
        """Helper to return answers as a {criterion_id: response_dict} dictionary."""
        if isinstance(self.answers, dict):
            return self.answers
        if isinstance(self.answers, list):
            norm = {}
            for item in self.answers:
                if isinstance(item, dict) and "question_id" in item:
                    norm[item["question_id"]] = item
            return norm
        return {}

    def calculate_completion_percentage(self) -> int:
        """Calculates percentage of the 18 criteria answered."""
        norm = self.get_normalized_answers()
        total_questions = 18
        if not norm:
            return 0
        answered_count = 0
        for i in range(1, total_questions + 1):
            qid = f"CR-{i:02d}"
            val = norm.get(qid)
            if val is not None:
                if isinstance(val, dict):
                    resp = val.get("response") or val.get("value")
                    if resp and str(resp).strip():
                        answered_count += 1
                elif str(val).strip():
                    answered_count += 1
        return int((answered_count / total_questions) * 100)

    def evaluate_submission_gate(self) -> tuple[bool, list[str]]:
        """
        Validates Section 6.1 Submission Gate criteria before transitioning to Submitted:
        - Supplier linked
        - At least 1 linked product
        - Mandatory criteria answered: CR-01, CR-02, CR-04, CR-06 to CR-18
        - CR-18 limitation confirmation explicitly acknowledged
        """
        reasons = []

        if not self.supplier_id:
            reasons.append("Supplier must be linked to the assessment.")

        if not self.linked_products.exists():
            reasons.append("At least one product must be linked to the assessment.")

        norm = self.get_normalized_answers()
        mandatory_criteria = [
            "CR-01", "CR-02", "CR-04",
            "CR-06", "CR-07", "CR-08", "CR-09", "CR-10",
            "CR-11", "CR-12", "CR-13", "CR-14", "CR-15",
            "CR-16", "CR-17", "CR-18"
        ]

        for qid in mandatory_criteria:
            val = norm.get(qid)
            is_answered = False
            if val is not None:
                if isinstance(val, dict):
                    resp = val.get("response") or val.get("value")
                    is_answered = bool(resp and str(resp).strip())
                else:
                    is_answered = bool(str(val).strip())

            if not is_answered:
                reasons.append(f"Mandatory criterion {qid} must be answered.")

        # CR-18 explicit check
        cr18 = norm.get("CR-18")
        cr18_confirmed = False
        if cr18:
            resp = cr18.get("response") or cr18.get("value") if isinstance(cr18, dict) else cr18
            if str(resp).lower().strip() in ("confirmed", "yes", "true", "acknowledged"):
                cr18_confirmed = True

        if not cr18_confirmed:
            reasons.append("CR-18 China Readiness Assessment Limitation Confirmation must be explicitly confirmed.")

        can_submit = len(reasons) == 0
        return can_submit, reasons


class AssessmentEvidence(models.Model):
    """
    M4: Evidence records linked directly to an assessment and specific criterion.
    Per Mentor Baseline v2.2 §7.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        ReadinessAssessment,
        on_delete=models.CASCADE,
        related_name="evidence_items",
        db_index=True,
    )
    criterion_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Criterion code, e.g. CR-06, CR-08, CR-10.",
    )
    document_name = models.CharField(max_length=255)
    evidence_condition = models.CharField(
        max_length=50,
        choices=EvidenceCondition.choices,
        default=EvidenceCondition.DOCUMENT_RECEIVED_UNVERIFIED,
        db_index=True,
    )
    issuer_source = models.CharField(max_length=255, blank=True, default="")
    reference_number = models.CharField(max_length=150, blank=True, default="")
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["criterion_id", "-created_at"]
        verbose_name = "Assessment Evidence"
        verbose_name_plural = "Assessment Evidence Items"

    def __str__(self):
        return f"{self.criterion_id} - {self.document_name} [{self.get_evidence_condition_display()}]"
