from decimal import Decimal
from rest_framework import serializers
from config.exceptions import ConflictError
from apps.demand.models import (
    BuyerRequirement,
    RequirementStatus,
    OrderFrequency,
    ProductCategory,
)


class BuyerRequirementSerializer(serializers.ModelSerializer):
    """
    M5: Serializer for Buyer Procurement Requirements.
    Supports partial draft save, complete ready-for-matching transition validation,
    version concurrency, and dual-compatibility with frontend types.
    """

    requirement_id = serializers.UUIDField(source="id", read_only=True)
    product_category_id = serializers.CharField(source="product_category", required=False)
    completeness_status = serializers.SerializerMethodField()
    matching_ready = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()

    class Meta:
        model = BuyerRequirement
        fields = [
            "id",
            "requirement_id",
            "buyer_organisation_name",
            "buyer_reference",
            "owner",
            "requirement_title",
            "target_market",
            "product_category",
            "product_category_id",
            "product_specifications",
            "quantity_value",
            "quantity_unit",
            "order_frequency",
            "target_price_min",
            "target_price_max",
            "currency_code",
            "price_basis",
            "delivery_location",
            "delivery_window_start",
            "delivery_window_end",
            "required_lead_time_value",
            "required_lead_time_unit",
            "mandatory_criteria",
            "preferred_criteria",
            "required_evidence",
            "priority_weights",
            "buyer_preferences",
            "requirement_notes",
            "requirement_status",
            "completeness_status",
            "matching_ready",
            "blocking_reasons",
            "version",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "requirement_id",
            "completeness_status",
            "matching_ready",
            "blocking_reasons",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def get_completeness_status(self, obj):
        is_ready, _ = obj.evaluate_readiness()
        return "Complete" if is_ready else "Incomplete"

    def get_matching_ready(self, obj):
        return obj.requirement_status == RequirementStatus.READY_FOR_MATCHING

    def get_blocking_reasons(self, obj):
        _, reasons = obj.evaluate_readiness()
        return reasons

    def to_internal_value(self, data):
        data_copy = data.copy() if hasattr(data, "copy") else dict(data)

        # Alias product_category_id -> product_category
        if "product_category_id" in data_copy and "product_category" not in data_copy:
            data_copy["product_category"] = data_copy.get("product_category_id")

        # Normalize Order Frequency
        if "order_frequency" in data_copy and isinstance(data_copy["order_frequency"], str):
            freq = data_copy["order_frequency"].strip().lower().replace("-", "_").replace(" ", "_")
            if "one_off" in freq:
                data_copy["order_frequency"] = OrderFrequency.ONE_OFF
            elif "month" in freq:
                data_copy["order_frequency"] = OrderFrequency.MONTHLY
            elif "quarter" in freq:
                data_copy["order_frequency"] = OrderFrequency.QUARTERLY
            elif "annual" in freq or "year" in freq:
                data_copy["order_frequency"] = OrderFrequency.ANNUAL

        # Normalize Requirement Status
        if "requirement_status" in data_copy and isinstance(data_copy["requirement_status"], str):
            st = data_copy["requirement_status"].strip().lower().replace(" ", "_").replace("-", "_")
            if "ready" in st:
                data_copy["requirement_status"] = RequirementStatus.READY_FOR_MATCHING
            elif "close" in st:
                data_copy["requirement_status"] = RequirementStatus.CLOSED
            elif "draft" in st:
                data_copy["requirement_status"] = RequirementStatus.DRAFT

        # Normalize Quantity Unit
        if "quantity_unit" in data_copy and isinstance(data_copy["quantity_unit"], str):
            qu = data_copy["quantity_unit"].strip().upper()
            if "TONNE" in qu or "MT" in qu:
                data_copy["quantity_unit"] = "MT"
            elif "KG" in qu or "KILO" in qu:
                data_copy["quantity_unit"] = "KG"
            elif "PIECE" in qu:
                data_copy["quantity_unit"] = "PIECES"
            elif "BOX" in qu:
                data_copy["quantity_unit"] = "BOXES"
            elif "CONTAINER" in qu:
                data_copy["quantity_unit"] = "CONTAINERS"

        return super().to_internal_value(data_copy)

    def validate(self, attrs):
        errors = {}

        # Minimum Draft Gate: Buyer organisation name
        buyer_org = attrs.get(
            "buyer_organisation_name",
            getattr(self.instance, "buyer_organisation_name", "")
        )
        if not buyer_org or not buyer_org.strip():
            errors["buyer_organisation_name"] = ["Buyer organisation name is required."]

        # Category validation
        category = attrs.get("product_category", getattr(self.instance, "product_category", ""))
        if not category:
            errors["product_category"] = ["Product category is required."]
        elif category not in [c.value for c in ProductCategory]:
            errors["product_category"] = [f"'{category}' is not an approved product category."]

        # Positive quantity validation if provided
        qty = attrs.get("quantity_value", getattr(self.instance, "quantity_value", None))
        if qty is not None and qty <= Decimal("0"):
            errors["quantity_value"] = ["Procurement quantity must be greater than zero."]

        # Target Pricing bounds
        price_min = attrs.get("target_price_min", getattr(self.instance, "target_price_min", None))
        price_max = attrs.get("target_price_max", getattr(self.instance, "target_price_max", None))
        if price_min is not None and price_min <= Decimal("0"):
            errors["target_price_min"] = ["Minimum target price must be greater than zero."]
        if price_max is not None and price_max <= Decimal("0"):
            errors["target_price_max"] = ["Maximum target price must be greater than zero."]
        if price_min is not None and price_max is not None and price_min > price_max:
            errors["target_price_max"] = ["Maximum target price cannot be less than minimum target price."]

        # Delivery window bounds
        w_start = attrs.get("delivery_window_start", getattr(self.instance, "delivery_window_start", None))
        w_end = attrs.get("delivery_window_end", getattr(self.instance, "delivery_window_end", None))
        if w_start and w_end and w_start > w_end:
            errors["delivery_window_end"] = ["Delivery window end date cannot precede start date."]

        # Full validation gate when target status is Ready for Matching
        status_val = attrs.get("requirement_status", getattr(self.instance, "requirement_status", RequirementStatus.DRAFT))
        if status_val == RequirementStatus.READY_FOR_MATCHING:
            target_mkt = attrs.get("target_market", getattr(self.instance, "target_market", "")).strip()
            deliv_loc = attrs.get("delivery_location", getattr(self.instance, "delivery_location", "")).strip()
            unit = attrs.get("quantity_unit", getattr(self.instance, "quantity_unit", "")).strip()

            if not target_mkt:
                errors["target_market"] = ["Target destination market must be specified."]
            if qty is None or qty <= Decimal("0"):
                errors["quantity_value"] = ["Positive procurement quantity is required for matching."]
            if not unit:
                errors["quantity_unit"] = ["Approved quantity unit is required for matching."]
            if not deliv_loc:
                errors["delivery_location"] = ["Delivery location in destination market is required for matching."]
            specs = attrs.get("product_specifications", getattr(self.instance, "product_specifications", ""))
            if not specs or not str(specs).strip():
                errors["product_specifications"] = ["Product specifications are required for matching."]

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def update(self, instance, validated_data):
        # Concurrency check (BUY-030)
        if "version" in self.initial_data:
            client_version = self.initial_data.get("version")
            if client_version != instance.version:
                raise ConflictError("This requirement record has been modified by another process. Please refresh.")

        validated_data["version"] = instance.version + 1
        return super().update(instance, validated_data)
