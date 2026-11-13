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
    Provides backward and dual compatibility with Next.js frontend contracts.
    """

    supplier_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Supplier
        fields = [
            "id",
            "supplier_id",
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
        read_only_fields = ["id", "supplier_id", "created_by", "created_at", "updated_at"]

    def to_internal_value(self, data):
        # Allow mutable copy
        data_copy = data.copy() if hasattr(data, "copy") else dict(data)

        # Map frontend address alias
        if "address_registration_reference" in data_copy and "address" not in data_copy:
            data_copy["address"] = data_copy.get("address_registration_reference")

        # Map nested contact_details structure
        if "contact_details" in data_copy and isinstance(data_copy["contact_details"], dict):
            cd = data_copy["contact_details"]
            if cd.get("contact_name") and "contact_name" not in data_copy:
                data_copy["contact_name"] = cd.get("contact_name")
            if cd.get("email") and "contact_email" not in data_copy:
                data_copy["contact_email"] = cd.get("email")
            if cd.get("phone") and "contact_phone" not in data_copy:
                data_copy["contact_phone"] = cd.get("phone")

        # Normalize enum casing (Title Case -> lowercase)
        if "supplier_type" in data_copy and isinstance(data_copy["supplier_type"], str):
            st = data_copy["supplier_type"].strip().lower()
            if "manufacturer" in st:
                data_copy["supplier_type"] = SupplierType.MANUFACTURER
            elif "trader" in st or "distributor" in st:
                data_copy["supplier_type"] = SupplierType.TRADER
            elif "merchant" in st or "exporter" in st:
                data_copy["supplier_type"] = SupplierType.MERCHANT_EXPORTER

        if "record_status" in data_copy and isinstance(data_copy["record_status"], str):
            rs = data_copy["record_status"].strip().lower()
            if rs in [choice.value for choice in SupplierStatus]:
                data_copy["record_status"] = rs

        # Map country names to 2-letter ISO
        if "country_of_registration" in data_copy and isinstance(data_copy["country_of_registration"], str):
            c = data_copy["country_of_registration"].strip().upper()
            if c in ("INDIA", "IND"):
                data_copy["country_of_registration"] = "IN"
            elif c in ("CHINA", "CHN"):
                data_copy["country_of_registration"] = "CN"
            elif len(c) == 2:
                data_copy["country_of_registration"] = c

        return super().to_internal_value(data_copy)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Expose friendly frontend properties
        ret["supplier_id"] = str(instance.id)
        ret["address_registration_reference"] = instance.address or ""
        ret["contact_details"] = {
            "contact_name": instance.contact_name or "",
            "email": instance.contact_email or "",
            "phone": instance.contact_phone or "",
        }
        return ret

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
    Supports dual contract compatibility with frontend field names.
    """

    product_id = serializers.UUIDField(source="id", read_only=True)
    supplier_name = serializers.CharField(source="supplier.legal_name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "product_id",
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
        read_only_fields = ["id", "product_id", "supplier_name", "created_by", "created_at", "updated_at"]

    def to_internal_value(self, data):
        data_copy = data.copy() if hasattr(data, "copy") else dict(data)

        # Map supplier_id -> supplier
        if "supplier_id" in data_copy and "supplier" not in data_copy:
            data_copy["supplier"] = data_copy.get("supplier_id")

        # Map MOQ aliases
        if "minimum_order_quantity" in data_copy and "moq_value" not in data_copy:
            data_copy["moq_value"] = data_copy.get("minimum_order_quantity")
        if "minimum_order_unit" in data_copy and "moq_unit" not in data_copy:
            data_copy["moq_unit"] = data_copy.get("minimum_order_unit")

        # Normalize quantity unit (MT, KG, PIECES, BOXES, CONTAINERS)
        if "moq_unit" in data_copy and isinstance(data_copy["moq_unit"], str):
            u = data_copy["moq_unit"].strip().upper()
            if "TONNE" in u or "MT" in u:
                data_copy["moq_unit"] = "MT"
            elif "KG" in u or "KILO" in u:
                data_copy["moq_unit"] = "KG"
            elif "PIECE" in u:
                data_copy["moq_unit"] = "PIECES"
            elif "BOX" in u:
                data_copy["moq_unit"] = "BOXES"
            elif "CONTAINER" in u:
                data_copy["moq_unit"] = "CONTAINERS"

        # Map capacity aliases and units
        if "capacity_unit" in data_copy and isinstance(data_copy["capacity_unit"], str):
            cu = data_copy["capacity_unit"].strip().upper()
            if "TONNE" in cu or "MT" in cu:
                data_copy["capacity_unit"] = "MT"
            elif "KG" in cu or "KILO" in cu:
                data_copy["capacity_unit"] = "KG"
            elif "PIECE" in cu:
                data_copy["capacity_unit"] = "PIECES"
            elif "BOX" in cu:
                data_copy["capacity_unit"] = "BOXES"
            elif "CONTAINER" in cu:
                data_copy["capacity_unit"] = "CONTAINERS"

        if "capacity_period" in data_copy and isinstance(data_copy["capacity_period"], str):
            cp = data_copy["capacity_period"].strip().upper()
            if "MONTH" in cp:
                data_copy["capacity_period"] = "MONTH"
            elif "YEAR" in cp:
                data_copy["capacity_period"] = "YEAR"
            elif "QUARTER" in cp:
                data_copy["capacity_period"] = "QUARTER"

        # Map lead time unit
        if "lead_time_unit" in data_copy and isinstance(data_copy["lead_time_unit"], str):
            ltu = data_copy["lead_time_unit"].strip().upper()
            if "DAY" in ltu:
                data_copy["lead_time_unit"] = "DAYS"
            elif "WEEK" in ltu:
                data_copy["lead_time_unit"] = "WEEKS"
            elif "MONTH" in ltu:
                data_copy["lead_time_unit"] = "MONTHS"

        # Map price aliases
        if "indicative_price_min" in data_copy and "price_min" not in data_copy:
            data_copy["price_min"] = data_copy.get("indicative_price_min")
        if "indicative_price_max" in data_copy and "price_max" not in data_copy:
            data_copy["price_max"] = data_copy.get("indicative_price_max")

        # Normalize translation status
        if "translation_status" in data_copy and isinstance(data_copy["translation_status"], str):
            ts = data_copy["translation_status"].strip().lower()
            if "not provided" in ts or "not_provided" in ts:
                data_copy["translation_status"] = TranslationStatus.NOT_PROVIDED
            elif "unreviewed" in ts or "provided" in ts:
                data_copy["translation_status"] = TranslationStatus.PROVIDED_UNREVIEWED
            elif "reviewed" in ts:
                data_copy["translation_status"] = TranslationStatus.REVIEWED

        return super().to_internal_value(data_copy)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Expose friendly frontend properties
        ret["product_id"] = str(instance.id)
        ret["supplier_id"] = str(instance.supplier_id)
        ret["minimum_order_quantity"] = float(instance.moq_value) if instance.moq_value is not None else None
        ret["minimum_order_unit"] = instance.moq_unit or ""
        ret["indicative_price_min"] = float(instance.price_min) if instance.price_min is not None else None
        ret["indicative_price_max"] = float(instance.price_max) if instance.price_max is not None else None
        return ret

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
    Dual compatible with frontend entity_type and entity_id format.
    """

    evidence_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = EvidenceItem
        fields = [
            "id",
            "evidence_id",
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
        read_only_fields = ["id", "evidence_id", "created_at", "updated_at"]

    def to_internal_value(self, data):
        data_copy = data.copy() if hasattr(data, "copy") else dict(data)

        # Map entity_type + entity_id
        entity_type = data_copy.get("entity_type")
        entity_id = data_copy.get("entity_id")
        if entity_type == "supplier" and entity_id and "supplier" not in data_copy:
            data_copy["supplier"] = entity_id
        elif entity_type == "product" and entity_id and "product" not in data_copy:
            data_copy["product"] = entity_id

        return super().to_internal_value(data_copy)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["evidence_id"] = str(instance.id)
        if instance.supplier_id:
            ret["entity_type"] = "supplier"
            ret["entity_id"] = str(instance.supplier_id)
        elif instance.product_id:
            ret["entity_type"] = "product"
            ret["entity_id"] = str(instance.product_id)
        return ret
