from rest_framework import serializers
from config.exceptions import ConflictError
from apps.readiness.models import (
    ReadinessAssessment,
    AssessmentEvidence,
    WorkflowState,
    ReadinessOutcome,
    EvidenceCondition,
)
from apps.registry.models import Supplier, Product


class AssessmentEvidenceSerializer(serializers.ModelSerializer):
    condition_display = serializers.CharField(source="get_evidence_condition_display", read_only=True)

    class Meta:
        model = AssessmentEvidence
        fields = [
            "id",
            "assessment",
            "criterion_id",
            "document_name",
            "evidence_condition",
            "condition_display",
            "issuer_source",
            "reference_number",
            "issue_date",
            "expiry_date",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ReadinessAssessmentSerializer(serializers.ModelSerializer):
    """
    Serializer for ReadinessAssessment with dual-aliasing for Priyanka's frontend
    (supports both 'workflow_state' / 'status' and 'readiness_outcome' / 'outcome'),
    optimistic concurrency, and nested relations.
    """

    supplier_name = serializers.CharField(source="supplier.legal_name", read_only=True)
    status = serializers.CharField(source="workflow_state", required=False)
    outcome = serializers.CharField(source="readiness_outcome", required=False, allow_null=True)
    state_display = serializers.CharField(source="get_workflow_state_display", read_only=True)
    outcome_display = serializers.CharField(source="get_readiness_outcome_display", read_only=True)
    completeness = serializers.SerializerMethodField()
    evidence_items = AssessmentEvidenceSerializer(many=True, read_only=True)
    linked_product_details = serializers.SerializerMethodField()

    class Meta:
        model = ReadinessAssessment
        fields = [
            "id",
            "supplier",
            "supplier_name",
            "linked_products",
            "linked_product_details",
            "questionnaire_version",
            "workflow_state",
            "status",
            "state_display",
            "readiness_outcome",
            "outcome",
            "outcome_display",
            "assigned_analyst",
            "submitted_by",
            "reviewer",
            "answers",
            "submission_notes",
            "reviewer_notes",
            "information_request_notes",
            "version",
            "completeness",
            "evidence_items",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "state_display",
            "outcome_display",
            "created_by",
            "created_at",
            "updated_at",
            "evidence_items",
        ]

    def get_completeness(self, obj) -> int:
        return obj.calculate_completion_percentage()

    def get_linked_product_details(self, obj) -> list[dict]:
        return [
            {
                "id": str(p.id),
                "product_name": p.product_name,
                "category": p.product_category,
            }
            for p in obj.linked_products.all()
        ]

    def validate(self, attrs):
        # Concurrency check
        if self.instance and "version" in self.initial_data:
            client_version = self.initial_data.get("version")
            if client_version is not None and int(client_version) != self.instance.version:
                raise ConflictError(
                    detail="Assessment has been modified by another transaction. Please reload.",
                    code="concurrency_conflict",
                )

        # Normalize frontend aliased fields
        if "status" in self.initial_data and "workflow_state" not in attrs:
            val = self.initial_data["status"].lower().replace(" ", "_")
            if val in dict(WorkflowState.choices):
                attrs["workflow_state"] = val

        if "outcome" in self.initial_data and "readiness_outcome" not in attrs:
            val = self.initial_data["outcome"]
            if val:
                val_norm = val.lower().replace("-", "_").replace(" ", "_")
                # Map frontend legacy strings if any
                mapping = {
                    "china_ready": ReadinessOutcome.READY_FOR_MATCHING,
                    "ready_for_matching": ReadinessOutcome.READY_FOR_MATCHING,
                    "more_information_required": ReadinessOutcome.INFORMATION_REQUIRED,
                    "information_required": ReadinessOutcome.INFORMATION_REQUIRED,
                    "not_ready": ReadinessOutcome.NOT_CURRENTLY_ELIGIBLE,
                    "not_currently_eligible": ReadinessOutcome.NOT_CURRENTLY_ELIGIBLE,
                }
                attrs["readiness_outcome"] = mapping.get(val_norm, val)

        return attrs

    def update(self, instance, validated_data):
        # Increment version for optimistic concurrency
        validated_data["version"] = instance.version + 1
        return super().update(instance, validated_data)


class AssessmentSubmitSerializer(serializers.Serializer):
    submission_notes = serializers.CharField(required=False, allow_blank=True, default="")


class AssessmentRequestInfoSerializer(serializers.Serializer):
    request_notes = serializers.CharField(required=True, allow_blank=False)


class AssessmentCompleteReviewSerializer(serializers.Serializer):
    readiness_outcome = serializers.ChoiceField(choices=ReadinessOutcome.choices, required=True)
    reviewer_notes = serializers.CharField(required=True, allow_blank=False)
