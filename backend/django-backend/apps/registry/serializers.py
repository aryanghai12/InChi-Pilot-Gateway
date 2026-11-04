from decimal import Decimal
from rest_framework import serializers
from config.exceptions import ConflictError
from apps.registry.models import (
    Supplier,
    SupplierStatus,
    SupplierType,
    Product,
    TranslationStatus,
    EvidenceItem,
)


class SupplierSerializer(serializers.ModelSerializer):
    """
    M2: Serializer for Supplier Registry.
    Supports partial draft save, complete transition validation, and version concurrency.
    """

    class Meta:
        model = Supplier
        fields = [
            "id",
            "legal_name",
            "trade_name",
            "country_of_registration",
            "supplier_type",
            "address",
            "contact_name",
            "contact_email",
            "contact_phone",
            "industry_description",
            "record_status",
            "version",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        record_status = attrs.get("record_status", getattr(self.instance, "record_status", SupplierStatus.DRAFT))
        legal_name = attrs.get("legal_name", getattr(self.instance, "legal_name", "")).strip()
        country = attrs.get("country_of_registration", getattr(self.instance, "country_of_registration", "")).strip()
        supplier_type = attrs.get("supplier_type", getattr(self.instance, "supplier_type", "")).strip()

        # Validation gate for Complete status (D-01 / D-02)
        if record_status == SupplierStatus.COMPLETE:
            errors = {}
            if not legal_name:
                errors["legal_name"] = ["Legal / registered business name is required to mark supplier as Complete."]
            if not country:
                errors["country_of_registration"] = ["Country of registration is required to mark supplier as Complete."]
            if not supplier_type:
                errors["supplier_type"] = ["Supplier type classification is required to mark supplier as Complete."]
            if errors:
                raise serializers.ValidationError(errors)

        return attrs

    def update(self, instance, validated_data):
        # Concurrency check (M2-AC7)
        if "version" in self.initial_data:
            client_version = self.initial_data.get("version")
            if client_version != instance.version:
                raise ConflictError("This supplier record has been modified by another process. Please refresh.")

        # Increment version on update
        validated_data["version"] = instance.version + 1
        return super().update(instance, validated_data)


class ProductSerializer(serializers.ModelSerializer):
    """
    M3: Serializer for Product Catalogue.
    Enforces mandatory units, numeric bounds, Mandarin consistency, and version concurrency.
    """

    supplier_name = serializers.CharField(source="supplier.legal_name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "supplier",
            "supplier_name",
            "product_name",
            "product_category",
            "description",
            "product_name_zh",
            "short_description_zh",
            "translation_status",
            "origin",
            "specifications",
            "moq_value",
            "moq_unit",
            "price_min",
            "price_max",
            "currency",
            "price_basis",
            "capacity_quantity",
            "capacity_unit",
            "capacity_period",
            "lead_time_value",
            "lead_time_unit",
            "version",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "supplier_name", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        supplier = attrs.get("supplier", getattr(self.instance, "supplier", None))
        if supplier and supplier.record_status == SupplierStatus.ARCHIVED:
            raise serializers.ValidationError({"supplier": ["Cannot add or edit products for an archived supplier."]})

        errors = {}

        # MOQ validation
        moq_value = attrs.get("moq_value", getattr(self.instance, "moq_value", None))
        moq_unit = attrs.get("moq_unit", getattr(self.instance, "moq_unit", ""))
        if moq_value is not None:
            if moq_value <= Decimal("0"):
                errors["moq_value"] = ["Minimum order quantity must be greater than zero."]
            if not moq_unit:
                errors["moq_unit"] = ["Minimum order unit is required when MOQ is provided."]

        # Pricing validation
        price_min = attrs.get("price_min", getattr(self.instance, "price_min", None))
        price_max = attrs.get("price_max", getattr(self.instance, "price_max", None))
        if price_min is not None and price_min <= Decimal("0"):
            errors["price_min"] = ["Minimum price must be greater than zero."]
        if price_max is not None and price_max <= Decimal("0"):
            errors["price_max"] = ["Maximum price must be greater than zero."]
        if price_min is not None and price_max is not None and price_min > price_max:
            errors["price_max"] = ["Maximum price cannot be less than minimum price."]

        # Capacity validation
        cap_qty = attrs.get("capacity_quantity", getattr(self.instance, "capacity_quantity", None))
        cap_unit = attrs.get("capacity_unit", getattr(self.instance, "capacity_unit", ""))
        cap_period = attrs.get("capacity_period", getattr(self.instance, "capacity_period", ""))
        if cap_qty is not None:
            if cap_qty <= Decimal("0"):
                errors["capacity_quantity"] = ["Capacity quantity must be greater than zero."]
            if not cap_unit:
                errors["capacity_unit"] = ["Capacity unit is required when capacity is provided."]
            if not cap_period:
                errors["capacity_period"] = ["Capacity period is required when capacity is provided."]

        # Lead time validation
        lt_val = attrs.get("lead_time_value", getattr(self.instance, "lead_time_value", None))
        lt_unit = attrs.get("lead_time_unit", getattr(self.instance, "lead_time_unit", ""))
        if lt_val is not None:
            if lt_val <= 0:
                errors["lead_time_value"] = ["Lead time value must be greater than zero."]
            if not lt_unit:
                errors["lead_time_unit"] = ["Lead time unit is required when lead time is provided."]

        # Mandarin fields consistency (M3-AC4)
        name_zh = attrs.get("product_name_zh", getattr(self.instance, "product_name_zh", "")).strip()
        desc_zh = attrs.get("short_description_zh", getattr(self.instance, "short_description_zh", "")).strip()
        trans_status = attrs.get("translation_status", getattr(self.instance, "translation_status", TranslationStatus.NOT_PROVIDED))

        if not name_zh and not desc_zh:
            attrs["translation_status"] = TranslationStatus.NOT_PROVIDED
        elif (name_zh or desc_zh) and trans_status == TranslationStatus.NOT_PROVIDED:
            attrs["translation_status"] = TranslationStatus.PROVIDED_UNREVIEWED

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def update(self, instance, validated_data):
        # Concurrency check
        if "version" in self.initial_data:
            client_version = self.initial_data.get("version")
            if client_version != instance.version:
                raise ConflictError("This product record has been modified by another process. Please refresh.")

        # Increment version on update
        validated_data["version"] = instance.version + 1
        return super().update(instance, validated_data)


class EvidenceItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Evidence Metadata records (EVD-01 to EVD-10).
    """

    class Meta:
        model = EvidenceItem
        fields = [
            "id",
            "supplier",
            "product",
            "document_type",
            "evidence_reference",
            "document_name",
            "issue_date",
            "expiry_date",
            "presence_status",
            "review_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
