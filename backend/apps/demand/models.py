import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings


class RequirementStatus(models.TextChoices):
    """
    Agreed M5 MVP Workflow Statuses.
    D-15 / v1.4 Dictionary: Strictly 3 statuses. No In-Review, On-Hold, or Archived.
    """
    DRAFT = "draft", "Draft"
    READY_FOR_MATCHING = "ready_for_matching", "Ready for matching"
    CLOSED = "closed", "Closed"


class OrderFrequency(models.TextChoices):
    ONE_OFF = "one_off", "One-off"
    MONTHLY = "monthly", "Monthly"
    QUARTERLY = "quarterly", "Quarterly"
    ANNUAL = "annual", "Annual"


class ProductCategory(models.TextChoices):
    """7 Top-Level Working Categories defined in Buyer Requirement Field Dictionary v1.4."""
    AGRICULTURE_AND_FOOD = "Agriculture and Food", "Agriculture and Food"
    TEXTILES = "Textiles", "Textiles"
    ENGINEERING_GOODS = "Engineering Goods", "Engineering Goods"
    ELECTRONIC_GOODS = "Electronic Goods", "Electronic Goods"
    CHEMICALS = "Chemicals", "Chemicals"
    MINERALS_AND_METALS = "Minerals & Metals", "Minerals & Metals"
    MARINE_PRODUCTS = "Marine Products", "Marine Products"


class BuyerRequirement(models.Model):
    """
    M5: Buyer Procurement Requirement Model (BUY-001 to BUY-032).
    Captures commercial buyer demand with hard mandatory criteria,
    preferred criteria, delivery windows, and matching readiness gates.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Core Organisation & Identity (BUY-002, BUY-003, BUY-004)
    # Stored directly against requirement per Decision D-13 (No separate BuyerProfile)
    buyer_organisation_name = models.CharField(max_length=255, db_index=True)
    buyer_reference = models.CharField(max_length=100, blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_requirements",
    )

    # Product & Categorisation (BUY-005, BUY-006, BUY-007, BUY-008)
    requirement_title = models.CharField(max_length=255, blank=True, default="", db_index=True)
    target_market = models.CharField(max_length=100, default="China")
    product_category = models.CharField(
        max_length=100,
        choices=ProductCategory.choices,
        db_index=True,
    )
    product_specifications = models.TextField(blank=True, default="")

    # Volume & Frequency (BUY-009, BUY-010, BUY-011)
    quantity_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    quantity_unit = models.CharField(max_length=50, blank=True, default="")
    order_frequency = models.CharField(
        max_length=50,
        choices=OrderFrequency.choices,
        default=OrderFrequency.ONE_OFF,
    )

    # Target Pricing (BUY-012, BUY-013, BUY-014, BUY-015)
    target_price_min = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    target_price_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency_code = models.CharField(max_length=10, default="USD")
    price_basis = models.CharField(max_length=50, blank=True, default="FOB")

    # Delivery & Logistics (BUY-017, BUY-018, BUY-019, BUY-020, BUY-021)
    delivery_location = models.CharField(max_length=255, blank=True, default="")
    delivery_window_start = models.DateField(null=True, blank=True)
    delivery_window_end = models.DateField(null=True, blank=True)
    required_lead_time_value = models.PositiveIntegerField(null=True, blank=True)
    required_lead_time_unit = models.CharField(max_length=30, blank=True, default="days")

    # Structured Eligibility & Preference Criteria (BUY-016, BUY-022, BUY-023, BUY-024, BUY-025)
    mandatory_criteria = models.JSONField(
        default=list,
        blank=True,
        help_text="Hard eligibility rules candidates must pass before scoring.",
    )
    preferred_criteria = models.JSONField(
        default=list,
        blank=True,
        help_text="Weighted preferences used for candidate ranking.",
    )
    required_evidence = models.JSONField(
        default=list,
        blank=True,
        help_text="Specific certificates or documents required from suppliers.",
    )
    priority_weights = models.JSONField(default=dict, blank=True)
    buyer_preferences = models.JSONField(default=dict, blank=True)
    requirement_notes = models.TextField(blank=True, default="")

    # Lifecycle & Concurrency (BUY-028, BUY-030)
    requirement_status = models.CharField(
        max_length=30,
        choices=RequirementStatus.choices,
        default=RequirementStatus.DRAFT,
        db_index=True,
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Optimistic concurrency tracking version.",
    )

    # Metadata & Auditing (BUY-031)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_requirements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Buyer Requirement"
        verbose_name_plural = "Buyer Requirements"

    def __str__(self):
        title = self.requirement_title or f"Requirement for {self.buyer_organisation_name}"
        return f"{title} [{self.get_requirement_status_display()}]"

    def evaluate_readiness(self):
        """
        Calculates matching readiness and blocking reasons per BUY-032.
        Returns: (is_ready: bool, blocking_reasons: list[str])
        """
        reasons = []

        if not self.buyer_organisation_name or not self.buyer_organisation_name.strip():
            reasons.append("Buyer organisation name is required.")

        if not self.target_market or not self.target_market.strip():
            reasons.append("Target destination market must be specified.")

        if not self.product_category or not self.product_category.strip():
            reasons.append("Product category classification is required.")

        if self.quantity_value is None or self.quantity_value <= Decimal("0"):
            reasons.append("Positive procurement quantity is required.")

        if not self.quantity_unit or not self.quantity_unit.strip():
            reasons.append("Approved quantity measurement unit is required.")

        if not self.delivery_location or not self.delivery_location.strip():
            reasons.append("Delivery destination port or city in China is required.")

        # Conditional Pricing Gate
        has_min = self.target_price_min is not None
        has_max = self.target_price_max is not None
        if has_min or has_max:
            if not self.currency_code or not self.currency_code.strip():
                reasons.append("Currency code is required when target pricing is specified.")
            if not self.price_basis or not self.price_basis.strip():
                reasons.append("Price basis (e.g., FOB, CIF) is required when target pricing is specified.")
            if has_min and self.target_price_min <= Decimal("0"):
                reasons.append("Minimum target price must be greater than zero.")
            if has_max and self.target_price_max <= Decimal("0"):
                reasons.append("Maximum target price must be greater than zero.")
            if has_min and has_max and self.target_price_min > self.target_price_max:
                reasons.append("Maximum target price cannot be less than minimum target price.")

        is_ready = len(reasons) == 0
        return is_ready, reasons
