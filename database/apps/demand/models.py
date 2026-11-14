import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class ReferenceValue(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        RETIRED = "retired", "Retired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_type = models.CharField(max_length=50)
    code = models.CharField(max_length=100)
    display_name = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    metadata = models.JSONField(default=dict, blank=True)
    approved_by = models.CharField(max_length=255, blank=True, default="")
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "demand_reference_value"
        constraints = [
            models.UniqueConstraint(
                fields=["reference_type", "code", "version"],
                name="uq_demand_reference_value_version",
            ),
        ]
        indexes = [
            models.Index(fields=["reference_type", "status"]),
            models.Index(fields=["reference_type", "code"]),
        ]


class MatchingConfiguration(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        RETIRED = "retired", "Retired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    configuration_key = models.CharField(max_length=100)
    version = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    configuration = models.JSONField(default=dict)
    approved_by = models.CharField(max_length=255, blank=True, default="")
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "matching_configuration"
        constraints = [
            models.UniqueConstraint(
                fields=["configuration_key", "version"],
                name="uq_matching_configuration_version",
            ),
        ]
        indexes = [
            models.Index(fields=["configuration_key", "status"]),
        ]


class BuyerRequirement(models.Model):
    requirement_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    buyer_organisation_name = models.CharField(max_length=255, blank=True, default="")
    buyer_reference = models.CharField(max_length=100, blank=True, default="")
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="owned_buyer_requirements",
    )
    target_market = models.CharField(max_length=100, blank=True, default="")
    product_category_id = models.CharField(max_length=100, blank=True, default="")
    requirement_title = models.CharField(max_length=255, blank=True, default="")
    requirement_status = models.CharField(max_length=50, default="draft")
    completeness_status = models.CharField(max_length=50, default="incomplete")
    matching_ready = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_buyer_requirements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="updated_buyer_requirements",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "buyer_requirement"
        indexes = [
            models.Index(fields=["requirement_status"]),
            models.Index(fields=["completeness_status"]),
            models.Index(fields=["matching_ready"]),
            models.Index(fields=["owner_user"]),
            models.Index(fields=["target_market"]),
            models.Index(fields=["product_category_id"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self):
        return self.requirement_title or str(self.requirement_id)


class BuyerRequirementVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement = models.ForeignKey(
        BuyerRequirement,
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version = models.PositiveIntegerField()
    requirement_notes = models.TextField(blank=True, default="")
    schema_version = models.CharField(max_length=50, default="buyer-requirement-v1")
    matching_configuration_version = models.CharField(max_length=100, blank=True, default="")
    change_reason = models.CharField(max_length=255, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_requirement_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "buyer_requirement_version"
        constraints = [
            models.UniqueConstraint(
                fields=["requirement", "version"],
                name="uq_buyer_requirement_version",
            ),
        ]
        indexes = [
            models.Index(fields=["requirement", "version"]),
            models.Index(fields=["-created_at"]),
        ]


class RequirementSpecification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_version = models.OneToOneField(
        BuyerRequirementVersion,
        on_delete=models.PROTECT,
        related_name="specification",
    )
    attributes = models.JSONField(default=dict, blank=True)
    schema_version = models.CharField(max_length=50, default="category-schema-v1")

    class Meta:
        db_table = "requirement_specification"


class RequirementQuantity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_version = models.OneToOneField(
        BuyerRequirementVersion,
        on_delete=models.PROTECT,
        related_name="quantity",
    )
    quantity_value = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    quantity_unit = models.CharField(max_length=50, blank=True, default="")
    order_frequency = models.CharField(max_length=50, blank=True, default="")
    recurrence_interval = models.PositiveIntegerField(null=True, blank=True)
    recurrence_period = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        db_table = "requirement_quantity"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(quantity_value__isnull=True)
                    | models.Q(quantity_value__gt=0)
                ),
                name="quantity_value_positive_when_supplied",
            ),
        ]


class RequirementCommercialTerms(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_version = models.OneToOneField(
        BuyerRequirementVersion,
        on_delete=models.PROTECT,
        related_name="commercial_terms",
    )
    target_price_min = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    target_price_max = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    currency_code = models.CharField(max_length=3, blank=True, default="")
    price_basis = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        db_table = "requirement_commercial_terms"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(target_price_min__isnull=True)
                    | models.Q(target_price_min__gt=0)
                ),
                name="target_price_min_positive_when_supplied",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(target_price_max__isnull=True)
                    | models.Q(target_price_max__gt=0)
                ),
                name="target_price_max_positive_when_supplied",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(target_price_min__isnull=True)
                    | models.Q(target_price_max__isnull=True)
                    | models.Q(target_price_min__lte=models.F("target_price_max"))
                ),
                name="target_price_min_lte_max",
            ),
        ]


class RequirementDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_version = models.OneToOneField(
        BuyerRequirementVersion,
        on_delete=models.PROTECT,
        related_name="delivery",
    )
    delivery_location = models.JSONField(default=dict, blank=True)
    delivery_window_start = models.DateField(null=True, blank=True)
    delivery_window_end = models.DateField(null=True, blank=True)
    required_lead_time_value = models.PositiveIntegerField(null=True, blank=True)
    required_lead_time_unit = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        db_table = "requirement_delivery"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(delivery_window_start__isnull=True)
                    | models.Q(delivery_window_end__isnull=True)
                    | models.Q(delivery_window_start__lte=models.F("delivery_window_end"))
                ),
                name="delivery_window_start_lte_end",
            ),
        ]


class RequirementEvidenceCriterion(models.Model):
    MANDATORY = "mandatory"
    PREFERRED = "preferred"
    CLASSIFICATION_CHOICES = (
        (MANDATORY, "Mandatory"),
        (PREFERRED, "Preferred"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_version = models.ForeignKey(
        BuyerRequirementVersion,
        on_delete=models.PROTECT,
        related_name="evidence_criteria",
    )
    evidence_type = models.CharField(max_length=100)
    criterion_value = models.JSONField(default=dict, blank=True)
    classification = models.CharField(
        max_length=20,
        choices=CLASSIFICATION_CHOICES,
    )
    taxonomy_version = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        db_table = "requirement_evidence_criterion"
        indexes = [
            models.Index(fields=["requirement_version", "classification"]),
        ]


class RequirementEligibilityCriterion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_version = models.ForeignKey(
        BuyerRequirementVersion,
        on_delete=models.PROTECT,
        related_name="eligibility_criteria",
    )
    criterion_key = models.CharField(max_length=100)
    operator = models.CharField(max_length=50)
    criterion_value = models.JSONField(default=dict)
    unknown_policy = models.CharField(max_length=50, blank=True, default="")
    criteria_version = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        db_table = "requirement_eligibility_criterion"
        constraints = [
            models.UniqueConstraint(
                fields=["requirement_version", "criterion_key"],
                name="uq_requirement_eligibility_key",
            ),
        ]


class RequirementPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_version = models.ForeignKey(
        BuyerRequirementVersion,
        on_delete=models.PROTECT,
        related_name="preferences",
    )
    preference_key = models.CharField(max_length=100)
    preference_value = models.JSONField(default=dict)
    priority_weight_key = models.CharField(max_length=100, blank=True, default="")
    criteria_version = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        db_table = "requirement_preference"
        constraints = [
            models.UniqueConstraint(
                fields=["requirement_version", "preference_key"],
                name="uq_requirement_preference_key",
            ),
        ]


class MatchingReadinessBlocker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement_version = models.ForeignKey(
        BuyerRequirementVersion,
        on_delete=models.PROTECT,
        related_name="matching_readiness_blockers",
    )
    field_id = models.CharField(max_length=20)
    reason_code = models.CharField(max_length=100)
    reason_detail = models.TextField(blank=True, default="")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "matching_readiness_blocker"
        constraints = [
            models.UniqueConstraint(
                fields=["requirement_version", "field_id", "reason_code"],
                name="uq_matching_readiness_blocker",
            ),
        ]
        indexes = [
            models.Index(fields=["requirement_version", "active"]),
        ]
