import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
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
    class RequirementStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        READY_FOR_MATCHING = "READY_FOR_MATCHING", "Ready for Matching"
        CLOSED = "CLOSED", "Closed"

    class CompletenessStatus(models.TextChoices):
        INCOMPLETE = "INCOMPLETE", "Incomplete"
        COMPLETE = "COMPLETE", "Complete"

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
    requirement_status = models.CharField(
        max_length=50,
        choices=RequirementStatus.choices,
        default=RequirementStatus.DRAFT,
    )
    completeness_status = models.CharField(
        max_length=50,
        choices=CompletenessStatus.choices,
        default=CompletenessStatus.INCOMPLETE,
    )
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
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(requirement_status="READY_FOR_MATCHING")
                        & models.Q(matching_ready=True)
                    )
                    | ~models.Q(requirement_status="READY_FOR_MATCHING")
                ),
                name="buyer_ready_status_requires_matching_ready",
            ),
        ]
        indexes = [
            models.Index(fields=["requirement_status"]),
            models.Index(fields=["completeness_status"]),
            models.Index(fields=["matching_ready"]),
            models.Index(fields=["owner_user"]),
            models.Index(fields=["target_market"]),
            models.Index(fields=["product_category_id"]),
            models.Index(fields=["-updated_at"]),
            models.Index(
                fields=["requirement_status", "matching_ready", "-updated_at"],
                name="buyer_status_ready_upd_idx",
            ),
        ]

    def __str__(self):
        return self.requirement_title or str(self.requirement_id)

    def evaluate_readiness_gate(self, version):
        blockers = []

        if not self.buyer_organisation_name.strip():
            blockers.append(("BUY-002", "BUYER_ORGANISATION_REQUIRED"))
        if not self.product_category_id.strip():
            blockers.append(("BUY-006", "PRODUCT_CATEGORY_REQUIRED"))
        if not self.owner_user_id:
            blockers.append(("BUY-004", "INTERNAL_OWNER_REQUIRED"))

        specification = getattr(version, "specification", None)
        if specification is None or not specification.attributes:
            blockers.append(("BUY-008", "SPECIFICATION_REQUIRED"))

        quantity = getattr(version, "quantity", None)
        if (
            quantity is None
            or quantity.quantity_value is None
            or quantity.quantity_value <= 0
            or not quantity.quantity_unit.strip()
        ):
            blockers.append(("BUY-009/BUY-010", "QUANTITY_AND_UNIT_REQUIRED"))

        delivery = getattr(version, "delivery", None)
        if (
            delivery is None
            or not delivery.delivery_location
            or not str(delivery.delivery_location.get("country", "")).strip()
            or not str(delivery.delivery_location.get("city", "")).strip()
        ):
            blockers.append(("BUY-017", "DELIVERY_LOCATION_REQUIRED"))

        if not version.eligibility_criteria.exists():
            blockers.append(("BUY-022", "MANDATORY_CRITERION_REQUIRED"))

        commercial = getattr(version, "commercial_terms", None)
        if commercial is not None:
            price_supplied = (
                commercial.target_price_min is not None
                or commercial.target_price_max is not None
            )
            if price_supplied:
                if not commercial.currency_code.strip():
                    blockers.append(("BUY-014", "CURRENCY_REQUIRED"))
                if not commercial.price_basis.strip():
                    blockers.append(("BUY-015", "PRICE_BASIS_REQUIRED"))

        MatchingReadinessBlocker.objects.filter(
            requirement_version=version,
            active=True,
        ).exclude(
            field_id__in=[field_id for field_id, _ in blockers],
        ).update(active=False)

        for field_id, reason_code in blockers:
            blocker, created = MatchingReadinessBlocker.objects.get_or_create(
                requirement_version=version,
                field_id=field_id,
                reason_code=reason_code,
                defaults={
                    "reason_detail": "Required for Ready for Matching.",
                    "active": True,
                },
            )
            if not created and not blocker.active:
                blocker.active = True
                blocker.reason_detail = "Required for Ready for Matching."
                blocker.save(update_fields=["active", "reason_detail"])

        active_blockers = MatchingReadinessBlocker.objects.filter(
            requirement_version=version,
            active=True,
        )
        if active_blockers.exists():
            self.matching_ready = False
            self.completeness_status = self.CompletenessStatus.INCOMPLETE
            self.requirement_status = self.RequirementStatus.DRAFT
            self.save(update_fields=[
                "matching_ready",
                "completeness_status",
                "requirement_status",
                "updated_at",
            ])
            return False, blockers

        self.matching_ready = True
        self.completeness_status = self.CompletenessStatus.COMPLETE
        return True, []

    def mark_ready_for_matching(self, version):
        ready, blockers = self.evaluate_readiness_gate(version)
        if not ready:
            raise ValidationError(
                "The buyer requirement cannot become Ready for Matching.",
                code="matching_readiness_blocked",
            )
        self.requirement_status = self.RequirementStatus.READY_FOR_MATCHING
        self.save(update_fields=[
            "matching_ready",
            "completeness_status",
            "requirement_status",
            "updated_at",
        ])

    def close(self):
        self.requirement_status = self.RequirementStatus.CLOSED
        self.matching_ready = False
        self.save(update_fields=[
            "requirement_status",
            "matching_ready",
            "updated_at",
        ])


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

    def save(self, *args, **kwargs):
        if self.pk:
            previous = BuyerRequirementVersion.objects.filter(pk=self.pk).first()
            if previous is not None:
                raise ValidationError(
                    "Buyer requirement versions are immutable.",
                    code="immutable_requirement_version",
                )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Buyer requirement versions cannot be deleted.",
            code="immutable_requirement_version",
        )


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
            models.CheckConstraint(
                condition=(
                    models.Q(quantity_value__isnull=True)
                    | (
                        ~models.Q(quantity_unit="")
                        & models.Q(quantity_value__gt=0)
                    )
                ),
                name="quantity_unit_required_with_value",
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
            models.CheckConstraint(
                condition=(
                    models.Q(target_price_min__isnull=True, target_price_max__isnull=True)
                    | (
                        ~models.Q(currency_code="")
                        & ~models.Q(price_basis="")
                    )
                ),
                name="price_requires_currency_and_basis",
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
