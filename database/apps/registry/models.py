import uuid

from django.core.validators import EmailValidator, MinValueValidator, RegexValidator
from django.db import models


class Supplier(models.Model):
    class SupplierType(models.TextChoices):
        MANUFACTURER = "MANUFACTURER", "Manufacturer"
        TRADER = "TRADER", "Trader"
        DISTRIBUTOR = "DISTRIBUTOR", "Distributor"
        AGENT = "AGENT", "Agent"
        HYBRID = "HYBRID", "Hybrid"

    class RecordStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    supplier_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    legal_name = models.CharField(max_length=255)
    trading_name = models.CharField(max_length=255, blank=True, default="")
    supplier_type = models.CharField(
        max_length=20,
        choices=SupplierType.choices,
    )
    registered_address = models.TextField()
    state_country = models.CharField(max_length=255, default="India")
    gstin = models.CharField(
        max_length=15,
        blank=True,
        default="",
        validators=[
            RegexValidator(
                regex=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$",
                message="Enter a valid 15-character GSTIN.",
            ),
        ],
    )
    iec = models.CharField(
        max_length=10,
        blank=True,
        default="",
        validators=[
            RegexValidator(
                regex=r"^[0-9]{10}$",
                message="IEC must contain exactly 10 digits.",
            ),
        ],
    )
    primary_contact = models.CharField(max_length=255)
    contact_email = models.EmailField(validators=[EmailValidator()])
    export_markets = models.JSONField(default=list, blank=True)
    record_status = models.CharField(
        max_length=20,
        choices=RecordStatus.choices,
        default=RecordStatus.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "supplier"
        indexes = [
            models.Index(fields=["legal_name"]),
            models.Index(fields=["supplier_type", "record_status"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self):
        return self.legal_name


class Product(models.Model):
    class CategoryCode(models.TextChoices):
        AGRICULTURE_FOOD = "AGRICULTURE_FOOD", "Agriculture and Food"
        MINERALS_METALS = "MINERALS_METALS", "Minerals and Metals"
        MARINE_PRODUCTS = "MARINE_PRODUCTS", "Marine Products"
        CHEMICALS = "CHEMICALS", "Chemicals"
        PETROLEUM_PRODUCTS = "PETROLEUM_PRODUCTS", "Petroleum Products"

    class UnitOfMeasure(models.TextChoices):
        PIECE = "PIECE", "Piece"
        KILOGRAM = "KILOGRAM", "Kilogram"
        METRIC_TONNE = "METRIC_TONNE", "Metric tonne"
        LITRE = "LITRE", "Litre"
        CARTON = "CARTON", "Carton"

    class CapacityPeriod(models.TextChoices):
        WEEK = "WEEK", "Week"
        MONTH = "MONTH", "Month"
        QUARTER = "QUARTER", "Quarter"

    class OriginCountry(models.TextChoices):
        INDIA = "IN", "India"

    product_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="products",
    )
    product_name_en = models.CharField(max_length=255)
    product_name_zh_draft = models.CharField(max_length=255, blank=True, default="")
    category_code = models.CharField(
        max_length=50,
        choices=CategoryCode.choices,
    )
    hs_code_declared = models.CharField(max_length=50, blank=True, default="")
    model_grade = models.CharField(max_length=255, blank=True, default="")
    technical_specification = models.TextField()
    unit_of_measure = models.CharField(
        max_length=30,
        choices=UnitOfMeasure.choices,
    )
    declared_capacity = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        validators=[MinValueValidator(0)],
    )
    capacity_period = models.CharField(
        max_length=20,
        choices=CapacityPeriod.choices,
    )
    moq = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        validators=[MinValueValidator(0)],
    )
    lead_time_days = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    price_amount = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    price_currency_basis = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    origin_country = models.CharField(
        max_length=2,
        choices=OriginCountry.choices,
        default=OriginCountry.INDIA,
    )
    packaging_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product"
        indexes = [
            models.Index(fields=["supplier", "category_code"]),
            models.Index(fields=["category_code", "unit_of_measure"]),
            models.Index(fields=["supplier", "-updated_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(declared_capacity__gt=0),
                name="product_declared_capacity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(moq__gt=0),
                name="product_moq_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(lead_time_days__gte=1),
                name="product_lead_time_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(price_amount__isnull=True)
                    | (
                        ~models.Q(price_currency_basis="")
                        & models.Q(price_amount__gt=0)
                    )
                ),
                name="product_price_requires_currency_basis",
            ),
        ]

    def __str__(self):
        return self.product_name_en
