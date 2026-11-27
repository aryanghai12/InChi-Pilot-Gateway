from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.permissions import RolePermission
from apps.audit.services import record_event
from apps.registry.models import (
    Supplier,
    SupplierStatus,
    Product,
    EvidenceItem,
)
from apps.registry.serializers import (
    SupplierSerializer,
    ProductSerializer,
    EvidenceItemSerializer,
)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    M2: Supplier Registry ViewSet.
    Handles CRUD operations, Draft saving, Complete status transitions, and Archiving.
    Strictly protected by central RBAC policy (RolePermission).
    """

    queryset = Supplier.objects.all().order_by("-created_at")
    serializer_class = SupplierSerializer
    permission_classes = [RolePermission]
    policy_resource = "supplier"

    filter_backends = [filters.SearchFilter]
    search_fields = ["legal_name", "trade_name", "contact_name", "industry_description"]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        country_param = self.request.query_params.get("country")
        type_param = self.request.query_params.get("type")

        if status_param:
            qs = qs.filter(record_status=status_param.lower().strip())
        if country_param:
            qs = qs.filter(country_of_registration=country_param.upper().strip())
        if type_param:
            qs = qs.filter(supplier_type=type_param.lower().strip())

        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        supplier = serializer.save(created_by=user)
        record_event(
            actor=user,
            action="create",
            obj=supplier,
            reason="Supplier record created.",
            correlation_id=correlation_id,
        )

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        instance = serializer.instance
        old_data = {field: getattr(instance, field) for field in serializer.validated_data}
        supplier = serializer.save()
        changes = {}
        for field, old_val in old_data.items():
            new_val = getattr(supplier, field)
            if old_val != new_val:
                changes[field] = {"before": str(old_val), "after": str(new_val)}

        record_event(
            actor=user,
            action="update",
            obj=supplier,
            reason="Supplier record updated.",
            changes=changes,
            correlation_id=correlation_id,
        )

    @extend_schema(
        summary="Mark Supplier Complete",
        description="Transitions a supplier from Draft to Complete after verifying all mandatory fields.",
        request=None,
        responses={200: SupplierSerializer, 400: OpenApiResponse(description="Validation failed.")},
    )
    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        supplier = self.get_object()

        # Validate complete gate fields
        errors = {}
        if not supplier.legal_name or not supplier.legal_name.strip():
            errors["legal_name"] = ["Legal / registered business name is required to mark supplier as Complete."]
        if not supplier.country_of_registration or not supplier.country_of_registration.strip():
            errors["country_of_registration"] = ["Country of registration is required to mark supplier as Complete."]
        if not supplier.supplier_type or not supplier.supplier_type.strip():
            errors["supplier_type"] = ["Supplier type classification is required to mark supplier as Complete."]

        if errors:
            return Response(
                {
                    "code": "validation_error",
                    "message": "Supplier cannot be marked Complete due to missing mandatory fields.",
                    "field_errors": errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        supplier.record_status = SupplierStatus.COMPLETE
        supplier.version += 1
        supplier.save(update_fields=["record_status", "version", "updated_at"])

        correlation_id = getattr(request, "correlation_id", "")
        record_event(
            actor=request.user,
            action="complete",
            obj=supplier,
            reason="Supplier transitioned to Complete.",
            correlation_id=correlation_id,
        )

        return Response(
            {
                "message": f"Supplier {supplier.legal_name} successfully marked as Complete.",
                "supplier": SupplierSerializer(supplier).data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Archive Supplier",
        description="Soft-archives a supplier record. Associated products are preserved but blocked from new actions.",
        request=None,
        responses={200: SupplierSerializer},
    )
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        supplier = self.get_object()
        supplier.record_status = SupplierStatus.ARCHIVED
        supplier.version += 1
        supplier.save(update_fields=["record_status", "version", "updated_at"])

        correlation_id = getattr(request, "correlation_id", "")
        record_event(
            actor=request.user,
            action="archive",
            obj=supplier,
            reason="Supplier record archived.",
            correlation_id=correlation_id,
        )

        return Response(
            {
                "message": f"Supplier {supplier.legal_name or supplier.id} has been archived.",
                "supplier": SupplierSerializer(supplier).data,
            },
            status=status.HTTP_200_OK,
        )


class ProductViewSet(viewsets.ModelViewSet):
    """
    M3: Product Catalogue ViewSet.
    Handles product creation linked to suppliers, Mandarin attributes, and technical/commercial parameters.
    """

    queryset = Product.objects.select_related("supplier").all().order_by("-created_at")
    serializer_class = ProductSerializer
    permission_classes = [RolePermission]
    policy_resource = "product"

    filter_backends = [filters.SearchFilter]
    search_fields = ["product_name", "product_category", "description", "product_name_zh"]

    def get_queryset(self):
        qs = super().get_queryset()
        supplier_id = self.request.query_params.get("supplier_id")
        category = self.request.query_params.get("category")
        translation_status = self.request.query_params.get("translation_status")

        if supplier_id:
            qs = qs.filter(supplier__id=supplier_id)
        if category:
            qs = qs.filter(product_category__iexact=category.strip())
        if translation_status:
            qs = qs.filter(translation_status=translation_status.strip())

        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        product = serializer.save(created_by=user)
        record_event(
            actor=user,
            action="create",
            obj=product,
            reason=f"Product {product.product_name} created under supplier {product.supplier_id}.",
            correlation_id=correlation_id,
        )

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        instance = serializer.instance
        old_data = {field: getattr(instance, field) for field in serializer.validated_data}
        product = serializer.save()
        changes = {}
        for field, old_val in old_data.items():
            new_val = getattr(product, field)
            if old_val != new_val:
                changes[field] = {"before": str(old_val), "after": str(new_val)}

        record_event(
            actor=user,
            action="update",
            obj=product,
            reason=f"Product {product.product_name} updated.",
            changes=changes,
            correlation_id=correlation_id,
        )


class EvidenceItemViewSet(viewsets.ModelViewSet):
    """
    Evidence metadata viewset (EVD-01 to EVD-10).
    Allows linking supporting evidence references to suppliers or products.
    Restricts verification to Reviewers with mandatory reason and audit event logging (v2.2 §7.1, AC-06).
    """

    queryset = EvidenceItem.objects.all().order_by("-created_at")
    serializer_class = EvidenceItemSerializer
    permission_classes = [RolePermission]
    policy_resource = "evidence"

    def get_queryset(self):
        qs = super().get_queryset()
        supplier_id = self.request.query_params.get("supplier_id")
        product_id = self.request.query_params.get("product_id")

        if supplier_id:
            qs = qs.filter(supplier__id=supplier_id)
        if product_id:
            qs = qs.filter(product__id=product_id)

        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        evidence = serializer.save()
        record_event(
            actor=user,
            action="create",
            obj=evidence,
            outcome="success",
            reason=f"Evidence item {evidence.document_name} created.",
            changes={"document_type": {"before": None, "after": evidence.document_type}},
            correlation_id=correlation_id,
        )

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        correlation_id = getattr(self.request, "correlation_id", "")
        instance = serializer.instance
        old_data = {field: getattr(instance, field) for field in serializer.validated_data}
        evidence = serializer.save()
        changes = {}
        for field, old_val in old_data.items():
            new_val = getattr(evidence, field)
            if old_val != new_val:
                changes[field] = {"before": str(old_val), "after": str(new_val)}

        record_event(
            actor=user,
            action="update",
            obj=evidence,
            outcome="success",
            reason=f"Evidence item {evidence.document_name} updated.",
            changes=changes,
            correlation_id=correlation_id,
        )

    @extend_schema(
        summary="Verify Evidence Item",
        description="Restricted action for Reviewers to record evidence verification per v2.2 §7.1 and AC-06.",
        responses={200: EvidenceItemSerializer, 400: OpenApiResponse(description="Validation error.")},
    )
    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        evidence = self.get_object()

        reason = request.data.get("reason", "").strip() if isinstance(request.data, dict) else ""
        if not reason:
            return Response(
                {
                    "code": "validation_error",
                    "message": "A verification reason is required.",
                    "field_errors": {"reason": ["Verification reason is mandatory."]},
                    "correlation_id": getattr(request, "correlation_id", ""),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        condition = request.data.get("condition") or request.data.get("evidence_condition") or "verified"
        old_status = evidence.review_status
        evidence.review_status = condition
        evidence.save()

        user = request.user if request.user.is_authenticated else None
        record_event(
            actor=user,
            action="verify",
            obj=evidence,
            outcome="success",
            reason=reason,
            changes={"review_status": {"before": old_status, "after": condition}},
            correlation_id=getattr(request, "correlation_id", ""),
        )

        return Response(EvidenceItemSerializer(evidence).data)
