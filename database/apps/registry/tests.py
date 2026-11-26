from django.db import IntegrityError, transaction
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import TestCase
from io import StringIO
from decimal import Decimal

from apps.registry.models import Product, Supplier


class SupplierProductModelTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            legal_name="Bharat Precision Components Pvt Ltd",
            supplier_type=Supplier.SupplierType.MANUFACTURER,
            registered_address="Pune, Maharashtra, India",
            state_country="Maharashtra, India",
            gstin="27ABCDE1234F1Z5",
            iec="1234567890",
            primary_contact="Approved Contact",
            contact_email="contact@example.com",
            export_markets=["China"],
            record_status=Supplier.RecordStatus.ACTIVE,
        )

    def test_approved_category_codes_are_available(self):
        self.assertEqual(
            set(dict(Product.CategoryCode.choices)),
            {
                "AGRICULTURE_FOOD",
                "MINERALS_METALS",
                "MARINE_PRODUCTS",
                "CHEMICALS",
                "PETROLEUM_PRODUCTS",
            },
        )

    def create_product(self, **overrides):
        values = {
            "supplier": self.supplier,
            "product_name_en": "Stainless Steel Valve Body VB-40",
            "category_code": Product.CategoryCode.AGRICULTURE_FOOD,
            "technical_specification": "Stainless steel valve body, 40 mm specification",
            "unit_of_measure": Product.UnitOfMeasure.PIECE,
            "declared_capacity": "10000",
            "capacity_period": Product.CapacityPeriod.MONTH,
            "moq": "1000",
            "lead_time_days": 28,
            "packaging_description": "Cartons with 100 pieces per pack",
        }
        values.update(overrides)
        return Product.objects.create(**values)

    def test_product_is_linked_to_supplier(self):
        product = self.create_product()
        self.assertEqual(product.supplier, self.supplier)
        self.assertEqual(self.supplier.products.count(), 1)

    def test_zero_capacity_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_product(declared_capacity="0")

    def test_zero_moq_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_product(moq="0")

    def test_negative_lead_time_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_product(lead_time_days=-1)

    def test_priced_product_requires_currency_and_basis(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_product(
                    price_amount="125",
                    price_currency_basis="",
                )

    def test_priced_product_accepts_explicit_currency_and_basis(self):
        product = self.create_product(
            price_amount="125",
            price_currency_basis="USD per piece",
        )
        self.assertEqual(Decimal(str(product.price_amount)), Decimal("125"))

    def test_week2_seed_is_repeatable(self):
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(Supplier.objects.count(), 4)
        self.assertEqual(Product.objects.count(), 6)

    def test_gstin_and_iec_syntax_is_validated(self):
        invalid_supplier = Supplier(
            legal_name="Invalid Identifier Supplier",
            supplier_type=Supplier.SupplierType.TRADER,
            registered_address="India",
            state_country="India",
            gstin="INVALID",
            iec="ABC",
            primary_contact="Contact",
            contact_email="contact@example.com",
            record_status=Supplier.RecordStatus.DRAFT,
        )
        with self.assertRaises(ValidationError):
            invalid_supplier.full_clean()

        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(Supplier.objects.count(), 4)
        self.assertEqual(Product.objects.count(), 6)
