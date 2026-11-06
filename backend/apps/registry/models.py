import uuid
from django.db import models
from django.conf import settings


class SupplierStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    COMPLETE = "complete", "Complete"
    ARCHIVED = "archived", "Archived"


class SupplierType(models.TextChoices):
    MANUFACTURER = "manufacturer", "Manufacturer"
    MERCHANT_EXPORTER = "merchant_exporter", "Merchant Exporter"
    TRADER = "trader", "Trader / Aggregator"


class TranslationStatus(models.TextChoices):
    NOT_PROVIDED = "not_provided", "Not provided"
    PROVIDED_UNREVIEWED = "provided_unreviewed", "Provided – unreviewed"
    REVIEWED = "reviewed", "Reviewed"


class QuantityUnit(models.TextChoices):
    MT = "MT", "Metric Tonnes"
    KG = "KG", "Kilograms"
    PIECES = "PIECES", "Pieces"
    BOXES = "BOXES", "Boxes"
    CONTAINERS = "CONTAINERS", "Containers"


class CapacityPeriod(models.TextChoices):
    MONTH = "MONTH", "Per Month"
    YEAR = "YEAR", "Per Year"
    QUARTER = "QUARTER", "Per Quarter"


class CurrencyCode(models.TextChoices):
    USD = "USD", "US Dollar"
    INR = "INR", "Indian Rupee"
    CNY = "CNY", "Chinese Yuan"
    EUR = "EUR", "Euro"


class LeadTimeUnit(models.TextChoices):
    DAYS = "DAYS", "Days"
    WEEKS = "WEEKS", "Weeks"
    MONTHS = "MONTHS", "Months"


class Supplier(models.Model):
    """
    M2: Supplier Registry Model.
    Lifecycle states: Draft, Complete, Archived.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_name = models.CharField(max_length=255, blank=True, default="", db_index=True)
    trade_name = models.CharField(max_length=255, blank=True, default="")
    country_of_registration = models.CharField(max_length=2, default="IN", db_index=True)
    supplier_type = models.CharField(
        max_length=30,
        choices=SupplierType.choices,
        blank=True,
        default="",
        db_index=True,
    )
    address = models.TextField(blank=True, default="")
    contact_name = models.CharField(max_length=150, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    contact_phone = models.CharField(max_length=50, blank=True, default="")
    industry_description = models.TextField(blank=True, default="")

    record_status = models.CharField(
        max_length=20,
        choices=SupplierStatus.choices,
        default=SupplierStatus.DRAFT,
        db_index=True,
    )

    version = models.PositiveIntegerField(
        default=1,
        help_text="Optimistic concurrency tracking version.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_suppliers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        ordering = ["-created_at"]

    def __str__(self):
        name = self.legal_name or self.trade_name or "Unnamed Supplier"
        return f"{name} ({self.get_record_status_display()})"


class Product(models.Model):
    """
    M3: Product Catalogue Model.
    Associated strictly with a Supplier.
    Supports Mandarin fields (M3-AC4) and optimistic concurrency.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="products",
    )
    product_name = models.CharField(max_length=255, db_index=True)
    product_category = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True, default="")

    # Mandarin fields (M3-AC4 / D-14)
    product_name_zh = models.CharField(max_length=255, blank=True, default="")
    short_description_zh = models.TextField(blank=True, default="")
    translation_status = models.CharField(
        max_length=30,
        choices=TranslationStatus.choices,
        default=TranslationStatus.NOT_PROVIDED,
    )

    origin = models.CharField(max_length=100, blank=True, default="India")
    specifications = models.TextField(blank=True, default="")

    # Minimum Order Quantity (MOQ)
    moq_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    moq_unit = models.CharField(max_length=30, choices=QuantityUnit.choices, blank=True, default="")

    # Indicative Price Range
    price_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CurrencyCode.choices, default=CurrencyCode.USD)
    price_basis = models.CharField(max_length=50, blank=True, default="")

    # Capacity
    capacity_quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    capacity_unit = models.CharField(max_length=30, choices=QuantityUnit.choices, blank=True, default="")
    capacity_period = models.CharField(max_length=30, choices=CapacityPeriod.choices, blank=True, default="")

    # Lead Time
    lead_time_value = models.PositiveIntegerField(null=True, blank=True)
    lead_time_unit = models.CharField(max_length=30, choices=LeadTimeUnit.choices, blank=True, default="")

    version = models.PositiveIntegerField(
        default=1,
        help_text="Optimistic concurrency tracking version.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_products",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product_name} - {self.supplier.legal_name or 'Supplier'}"


class EvidenceItem(models.Model):
    """
    Evidence metadata record (EVD-01 to EVD-10).
    References supporting documentation without binary file uploads.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name="evidence_items",
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="evidence_items",
        null=True,
        blank=True,
    )
    document_type = models.CharField(max_length=100)
    evidence_reference = models.CharField(max_length=255)
    document_name = models.CharField(max_length=255, blank=True, default="")
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    presence_status = models.CharField(max_length=50, default="provided")
    review_status = models.CharField(max_length=50, default="unreviewed")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evidence Item"
        verbose_name_plural = "Evidence Items"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.document_type} ({self.evidence_reference})"
