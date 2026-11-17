from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.permissions import RolePermission
from apps.audit.services import record_event
from apps.demand.models import (
    BuyerRequirement,
    RequirementStatus,
)
from apps.demand.serializers import BuyerRequirementSerializer


class BuyerRequirementViewSet(viewsets.ModelViewSet):
    """
    M5: Buyer Demand ViewSet.
    Handles CRUD for procurement requirements, minimum draft saving,
    hard readiness gate validation, and closed status transition.
    Protected strictly by central RBAC policy (RolePermission).
    """

    queryset = BuyerRequirement.objects.all().order_by("-created_at")
    serializer_class = BuyerRequirementSerializer
    permission_classes = [RolePermission]
    policy_resource = "requirement"

    filter_backends = [filters.SearchFilter]
    search_fields = [
        "buyer_organisation_name",
        "requirement_title",
        "buyer_reference",
        "delivery_location",
        "product_category",
    ]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        category_param = self.request.query_params.get("category")
        market_param = self.request.query_params.get("market")

        if status_param:
            qs = qs.filter(requirement_status=status_param.lower().strip())
        if category_param:
            qs = qs.filter(product_category__iexact=category_param.strip())
        if market_param:
            qs = qs.filter(target_market__iexact=market_param.strip())

        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        req = serializer.save(created_by=user, owner=user)
        record_event(
            actor=user,
            action="create",
            obj=req,
            reason=f"Buyer requirement {req.requirement_title or req.id} recorded for {req.buyer_organisation_name}.",
            correlation_id=correlation_id,
        )

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        req = serializer.save()
        record_event(
            actor=user,
            action="update",
            obj=req,
            reason=f"Buyer requirement {req.requirement_title or req.id} updated.",
            correlation_id=correlation_id,
        )

    @extend_schema(
        summary="Mark Requirement Ready for Matching",
        description="Validates all mandatory eligibility criteria (BUY-032) and transitions requirement to Ready for Matching.",
        request=None,
        responses={
            200: BuyerRequirementSerializer,
            400: OpenApiResponse(description="Requirement missing mandatory matching fields."),
        },
    )
    @action(detail=True, methods=["post"], url_path="mark-ready")
    def mark_ready(self, request, pk=None):
        req = self.get_object()

        if req.requirement_status == RequirementStatus.CLOSED:
            return Response(
                {
                    "code": "validation_error",
                    "message": "Cannot mark a closed requirement as ready for matching.",
                    "field_errors": {"requirement_status": ["Closed requirements cannot be reopened without administrative review."]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_ready, blocking_reasons = req.evaluate_readiness()
        if not is_ready:
            return Response(
                {
                    "code": "validation_error",
                    "message": "Requirement cannot be marked ready for matching due to missing mandatory criteria.",
                    "field_errors": {"blocking_reasons": blocking_reasons},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        req.requirement_status = RequirementStatus.READY_FOR_MATCHING
        req.version += 1
        req.save(update_fields=["requirement_status", "version", "updated_at"])

        correlation_id = getattr(request, "correlation_id", "")
        record_event(
            actor=request.user,
            action="mark_ready",
            obj=req,
            reason=f"Requirement {req.requirement_title or req.id} transitioned to Ready for Matching.",
            correlation_id=correlation_id,
        )

        return Response(
            {
                "message": f"Requirement '{req.requirement_title or req.id}' successfully marked as Ready for Matching.",
                "requirement": BuyerRequirementSerializer(req).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Close Requirement",
        description="Closes an active requirement, removing it from candidate matching runs.",
        request=None,
        responses={200: BuyerRequirementSerializer},
    )
    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        req = self.get_object()
        req.requirement_status = RequirementStatus.CLOSED
        req.version += 1
        req.save(update_fields=["requirement_status", "version", "updated_at"])

        correlation_id = getattr(request, "correlation_id", "")
        record_event(
            actor=request.user,
            action="close",
            obj=req,
            reason=f"Requirement {req.requirement_title or req.id} closed.",
            correlation_id=correlation_id,
        )

        return Response(
            {
                "message": f"Requirement '{req.requirement_title or req.id}' has been closed.",
                "requirement": BuyerRequirementSerializer(req).data,
            },
            status=status.HTTP_200_OK,
        )
