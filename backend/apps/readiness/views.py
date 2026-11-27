from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.permissions import RolePermission
from apps.audit.services import record_event
from apps.readiness.models import (
    ReadinessAssessment,
    AssessmentEvidence,
    WorkflowState,
    ReadinessOutcome,
    EvidenceCondition,
)
from apps.readiness.serializers import (
    ReadinessAssessmentSerializer,
    AssessmentEvidenceSerializer,
    AssessmentSubmitSerializer,
    AssessmentRequestInfoSerializer,
    AssessmentCompleteReviewSerializer,
)

# Reference definitions for the 18 China Readiness Criteria per Mentor Baseline v2.2 §6
CRITERIA_METADATA = [
    {
        "id": "CR-01",
        "category": "Corporate & Legal Identity",
        "title": "Indian Legal Entity Identity & Verification",
        "mandatory": True,
        "evidence_required": True,
        "description": "Verification of corporate identity, registered business name, and active incorporation.",
    },
    {
        "id": "CR-02",
        "category": "Corporate & Legal Identity",
        "title": "Corporate Identification Number (CIN) / Registration Details",
        "mandatory": True,
        "evidence_required": True,
        "description": "Registered CIN, ROC filing verification, and director identity verification.",
    },
    {
        "id": "CR-03",
        "category": "Tax & Export Identity",
        "title": "Goods & Services Tax Identification Number (GSTIN)",
        "mandatory": False,
        "evidence_required": False,
        "description": "Active GSTIN registration and tax compliance standing.",
    },
    {
        "id": "CR-04",
        "category": "Tax & Export Identity",
        "title": "Importer Exporter Code (IEC) Validity & Authorisation",
        "mandatory": True,
        "evidence_required": True,
        "description": "Active Directorate General of Foreign Trade (DGFT) Import-Export Code.",
    },
    {
        "id": "CR-05",
        "category": "Manufacturing & Capacity",
        "title": "Manufacturing Facility & Production Site Verification",
        "mandatory": False,
        "evidence_required": False,
        "description": "Verification of plant address, ownership status, and physical production infrastructure.",
    },
    {
        "id": "CR-06",
        "category": "China Customs & Sanitary Compliance",
        "title": "GACC Registration Status (Decree 248 / 249)",
        "mandatory": True,
        "evidence_required": True,
        "description": "General Administration of Customs of China (GACC) import registration or qualification track.",
    },
    {
        "id": "CR-07",
        "category": "China Customs & Sanitary Compliance",
        "title": "CIQ Inspection & Sanitary/Phytosanitary Protocol Compliance",
        "mandatory": True,
        "evidence_required": True,
        "description": "Compliance with China Inspection and Quarantine (CIQ) pest risk and phytosanitary clearance protocols.",
    },
    {
        "id": "CR-08",
        "category": "Packaging & Regulatory Standards",
        "title": "Chinese GB Standard Packaging & Labeling Compliance (GB 7718 / GB 5296)",
        "mandatory": True,
        "evidence_required": True,
        "description": "Simplified Chinese label layout, ingredient declarations, net quantity, and manufacturer address in Mandarin.",
    },
    {
        "id": "CR-09",
        "category": "Traceability & Quality Assurance",
        "title": "Lot Traceability, Batch Records & Recall Protocols",
        "mandatory": True,
        "evidence_required": False,
        "description": "Demonstrated digital or physical batch tracing capability from raw materials to export container.",
    },
    {
        "id": "CR-10",
        "category": "Quality & Food Safety Certifications",
        "title": "International Quality & Food Safety Accreditations",
        "mandatory": True,
        "evidence_required": True,
        "description": "Active accredited third-party certification: ISO 22000, HACCP, FSSC 22000, BRCGS, or GMP.",
    },
    {
        "id": "CR-11",
        "category": "Logistics & Cold-Chain Capacity",
        "title": "Export Cold-Chain & Temperature Integrity Infrastructure",
        "mandatory": True,
        "evidence_required": False,
        "description": "Continuous cold storage, Reefer container booking, and automated temperature data logging capabilities.",
    },
    {
        "id": "CR-12",
        "category": "Logistics & Cold-Chain Capacity",
        "title": "Shelf-Life Viability & Transit Window Feasibility",
        "mandatory": True,
        "evidence_required": False,
        "description": "Product shelf-life buffer exceeding ocean freight transit + customs clearance times to Chinese ports.",
    },
    {
        "id": "CR-13",
        "category": "Commercial & Market Experience",
        "title": "Export Experience to East Asia / Greater China Region",
        "mandatory": True,
        "evidence_required": False,
        "description": "Demonstrated historical trade track record, Bill of Lading history, or export experience.",
    },
    {
        "id": "CR-14",
        "category": "Commercial & Communication Readiness",
        "title": "Mandarin Commercial & Technical Communication Capability",
        "mandatory": True,
        "evidence_required": False,
        "description": "Mandarin product documentation, WeChat business interface, or designated bilingual trade coordinator.",
    },
    {
        "id": "CR-15",
        "category": "Banking, Currency & Settlement",
        "title": "Cross-Border Settlement & Payment Term Compatibility (L/C, RMB, USD)",
        "mandatory": True,
        "evidence_required": False,
        "description": "Capacity to transact via Irrevocable Documentary Letter of Credit (L/C), RMB cross-border CIPS, or USD.",
    },
    {
        "id": "CR-16",
        "category": "Legal & Risk Governance",
        "title": "Dispute Resolution & Trade Contract Jurisdiction",
        "mandatory": True,
        "evidence_required": False,
        "description": "Agreed contract clauses referencing neutral international arbitration (CIETAC, SIAC, or UNCITRAL).",
    },
    {
        "id": "CR-17",
        "category": "Legal & Risk Governance",
        "title": "Regulatory Sanctions, Blacklist & Compliance Declaration",
        "mandatory": True,
        "evidence_required": True,
        "description": "Absence of customs penalties, anti-dumping citations, or regulatory import bans.",
    },
    {
        "id": "CR-18",
        "category": "Legal & Risk Governance",
        "title": "China Readiness Assessment Limitation Confirmation",
        "mandatory": True,
        "evidence_required": False,
        "description": "Explicit declaration acknowledging assessment reflects documentary evaluation and does not guarantee customs clearance or commercial agreement.",
    },
]


class ReadinessAssessmentViewSet(viewsets.ModelViewSet):
    """
    M4: China Readiness Assessment ViewSet.
    Manages assessment questionnaires, submission gate validation,
    information requests, and reviewer dispositions with strict RBAC.
    """

    queryset = ReadinessAssessment.objects.all().select_related("supplier", "assigned_analyst", "submitted_by", "reviewer", "created_by").prefetch_related("linked_products", "evidence_items")
    serializer_class = ReadinessAssessmentSerializer
    permission_classes = [RolePermission]
    policy_resource = "assessment"

    filter_backends = [filters.SearchFilter]
    search_fields = [
        "supplier__legal_name",
        "supplier__trade_name",
        "submission_notes",
        "reviewer_notes",
    ]

    def initial(self, request, *args, **kwargs):
        # Map custom view actions to policy.py actions before check_permissions runs in super().initial()
        action_mapping = {
            "list_criteria": "list",
            "check_submission_gate": "retrieve",
            "complete_review": "review",
            "request_information": "request_info",
        }
        if getattr(self, "action", None) in action_mapping:
            self.action = action_mapping[self.action]
        super().initial(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        supplier_id = self.request.query_params.get("supplier")
        state_param = self.request.query_params.get("state") or self.request.query_params.get("workflow_state") or self.request.query_params.get("status")
        outcome_param = self.request.query_params.get("outcome") or self.request.query_params.get("readiness_outcome")

        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        if state_param:
            qs = qs.filter(workflow_state__iexact=state_param.strip().lower().replace(" ", "_"))
        if outcome_param:
            norm_outcome = outcome_param.strip().lower().replace("-", "_").replace(" ", "_")
            qs = qs.filter(readiness_outcome__iexact=norm_outcome)

        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        assessment = serializer.save(created_by=user, assigned_analyst=user)
        supplier_name = assessment.supplier.legal_name or assessment.supplier.trade_name or "Supplier"
        record_event(
            actor=user,
            action="create",
            obj=assessment,
            reason=f"Readiness assessment initialized for supplier {supplier_name}.",
            correlation_id=correlation_id,
        )

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        assessment = serializer.save()
        record_event(
            actor=user,
            action="update",
            obj=assessment,
            reason=f"Readiness assessment updated (Version {assessment.version}).",
            correlation_id=correlation_id,
        )

    @action(detail=False, methods=["get"], url_path="criteria")
    def list_criteria(self, request):
        """Returns the full 18-question criteria baseline per Mentor Baseline v2.2 §6."""
        return Response({"criteria": CRITERIA_METADATA})

    @action(detail=True, methods=["get"], url_path="submission-gate")
    def check_submission_gate(self, request, pk=None):
        """Evaluates whether the assessment meets all Section 6.1 submission requirements."""
        assessment = self.get_object()
        can_submit, reasons = assessment.evaluate_submission_gate()
        return Response(
            {
                "can_submit": can_submit,
                "blocking_reasons": reasons,
                "completeness": assessment.calculate_completion_percentage(),
                "workflow_state": assessment.workflow_state,
            }
        )

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        """
        Transitions assessment from Draft or Information Required to Submitted.
        Enforces Section 6.1 Submission Gate.
        """
        assessment = self.get_object()
        if assessment.workflow_state not in (WorkflowState.DRAFT, WorkflowState.INFORMATION_REQUIRED):
            return Response(
                {
                    "code": "invalid_transition",
                    "message": f"Cannot submit assessment in state '{assessment.get_workflow_state_display()}'.",
                    "field_errors": {},
                    "correlation_id": getattr(request, "correlation_id", ""),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        can_submit, reasons = assessment.evaluate_submission_gate()
        if not can_submit:
            return Response(
                {
                    "code": "submission_gate_failed",
                    "message": "Assessment failed Section 6.1 submission gate criteria.",
                    "blocking_reasons": reasons,
                    "field_errors": {"submission": reasons},
                    "correlation_id": getattr(request, "correlation_id", ""),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        submit_serializer = AssessmentSubmitSerializer(data=request.data)
        submit_serializer.is_valid(raise_exception=True)

        user = request.user if request.user.is_authenticated else None
        assessment.workflow_state = WorkflowState.SUBMITTED
        assessment.submitted_by = user
        if submit_serializer.validated_data.get("submission_notes"):
            assessment.submission_notes = submit_serializer.validated_data["submission_notes"]
        assessment.version += 1
        assessment.save()

        record_event(
            actor=user,
            action="submit",
            obj=assessment,
            reason=f"Readiness assessment submitted for reviewer evaluation.",
            correlation_id=getattr(request, "correlation_id", ""),
        )

        return Response(ReadinessAssessmentSerializer(assessment).data)

    @action(detail=True, methods=["post"], url_path="request-information")
    def request_information(self, request, pk=None):
        """
        Reviewer requests additional evidence or clarified questionnaire answers.
        Transitions state to Information Required.
        """
        assessment = self.get_object()
        if assessment.workflow_state != WorkflowState.UNDER_REVIEW:
            return Response(
                {
                    "code": "invalid_transition",
                    "message": f"Cannot request information in state '{assessment.get_workflow_state_display()}'. Assessment must be in 'Under Review'.",
                    "field_errors": {},
                    "correlation_id": getattr(request, "correlation_id", ""),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AssessmentRequestInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user if request.user.is_authenticated else None
        assessment.workflow_state = WorkflowState.INFORMATION_REQUIRED
        assessment.information_request_notes = serializer.validated_data["request_notes"]
        assessment.version += 1
        assessment.save()

        record_event(
            actor=user,
            action="request_info",
            obj=assessment,
            reason=f"Reviewer requested information: {assessment.information_request_notes}",
            correlation_id=getattr(request, "correlation_id", ""),
        )

        return Response(ReadinessAssessmentSerializer(assessment).data)

    @action(detail=True, methods=["post"], url_path="complete-review")
    def complete_review(self, request, pk=None):
        """
        Reviewer records final readiness outcome (Section 8.1).
        Enforces deny_self_review policy: reviewer cannot approve their own submitted assessment.
        """
        assessment = self.get_object()
        if assessment.workflow_state != WorkflowState.UNDER_REVIEW:
            return Response(
                {
                    "code": "invalid_transition",
                    "message": f"Cannot complete review in state '{assessment.get_workflow_state_display()}'. Assessment must be in 'Under Review'.",
                    "field_errors": {},
                    "correlation_id": getattr(request, "correlation_id", ""),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enforce Object-level authorization (deny_self_review)
        self.check_object_permissions(request, assessment)

        serializer = AssessmentCompleteReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user if request.user.is_authenticated else None
        assessment.workflow_state = WorkflowState.REVIEW_COMPLETE
        assessment.readiness_outcome = serializer.validated_data["readiness_outcome"]
        assessment.reviewer_notes = serializer.validated_data["reviewer_notes"]
        assessment.reviewer = user
        assessment.version += 1
        assessment.save()

        record_event(
            actor=user,
            action="review",
            obj=assessment,
            reason=f"Assessment review completed with outcome: {assessment.get_readiness_outcome_display()}.",
            correlation_id=getattr(request, "correlation_id", ""),
        )

        return Response(ReadinessAssessmentSerializer(assessment).data)


class AssessmentEvidenceViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for AssessmentEvidence items.
    """

    queryset = AssessmentEvidence.objects.all().order_by("criterion_id", "-created_at")
    serializer_class = AssessmentEvidenceSerializer
    permission_classes = [RolePermission]
    policy_resource = "evidence"

    def get_queryset(self):
        qs = super().get_queryset()
        assessment_id = self.request.query_params.get("assessment")
        criterion_id = self.request.query_params.get("criterion")
        if assessment_id:
            qs = qs.filter(assessment_id=assessment_id)
        if criterion_id:
            qs = qs.filter(criterion_id__iexact=criterion_id)
        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        evidence = serializer.save()
        record_event(
            actor=user,
            action="create",
            obj=evidence,
            reason=f"Evidence {evidence.document_name} attached to criterion {evidence.criterion_id}.",
            correlation_id=getattr(self.request, "correlation_id", ""),
        )
