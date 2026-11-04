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
        supplier = serializer.save()
        record_event(
            actor=user,
            action="update",
            obj=supplier,
            reason="Supplier record updated.",
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
        product = serializer.save()
        record_event(
            actor=user,
            action="update",
            obj=product,
            reason=f"Product {product.product_name} updated.",
            correlation_id=correlation_id,
        )


class EvidenceItemViewSet(viewsets.ModelViewSet):
    """
    Evidence metadata viewset (EVD-01 to EVD-10).
    Allows linking supporting evidence references to suppliers or products.
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
