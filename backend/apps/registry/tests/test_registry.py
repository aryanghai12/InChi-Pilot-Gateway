from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, Role
from apps.registry.models import (
    Supplier,
    SupplierStatus,
    SupplierType,
    Product,
    TranslationStatus,
    EvidenceItem,
)
from apps.audit.models import AuditEvent


class SupplierRegistryTests(TestCase):
    """
    Test suite for Module M2: Supplier Registry.
    Covers Draft saving, Complete validation gate, Archiving, Concurrency, and RBAC.
    """

    def setUp(self):
        self.client = APIClient()

        # Analyst user (allowed to create/edit)
        self.analyst = User.objects.create_user(
            email="analyst@bncs.local",
            password="Password123!",
            role=Role.COMMERCIAL_ANALYST,
            is_verified=True,
        )

        # Reviewer user (read-only for supplier create/edit)
        self.reviewer = User.objects.create_user(
            email="reviewer@bncs.local",
            password="Password123!",
            role=Role.REVIEWER,
            is_verified=True,
        )

    def test_create_draft_supplier_success(self):
        """M2-AC1: Analyst can save a draft supplier with partial/draft-minimum fields."""
        self.client.force_login(self.analyst)

        payload = {
            "legal_name": "Agro Bharat Pvt Ltd",
            "country_of_registration": "IN",
        }
        response = self.client.post("/api/v1/suppliers/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["legal_name"], "Agro Bharat Pvt Ltd")
        self.assertEqual(data["record_status"], SupplierStatus.DRAFT)
        self.assertEqual(data["version"], 1)

        # Verify audit event emitted
        self.assertTrue(AuditEvent.objects.filter(object_id=data["id"], action="create").exists())

    def test_complete_supplier_validation_failure(self):
        """M2-AC2: Marking Complete fails with field errors if mandatory fields are missing."""
        self.client.force_login(self.analyst)

        # Create draft missing supplier_type
        supplier = Supplier.objects.create(
            legal_name="Partial Agro Ltd",
            country_of_registration="IN",
            supplier_type="",
            record_status=SupplierStatus.DRAFT,
            created_by=self.analyst,
        )

        # Attempt to mark complete
        response = self.client.post(f"/api/v1/suppliers/{supplier.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data["code"], "validation_error")
        self.assertIn("supplier_type", data["field_errors"])

    def test_complete_supplier_success(self):
        """M2-AC2: Marking Complete succeeds when all required fields are present."""
        self.client.force_login(self.analyst)

        supplier = Supplier.objects.create(
            legal_name="Complete Exports Ltd",
            country_of_registration="IN",
            supplier_type=SupplierType.MANUFACTURER,
            record_status=SupplierStatus.DRAFT,
            created_by=self.analyst,
        )

        response = self.client.post(f"/api/v1/suppliers/{supplier.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        supplier.refresh_from_db()
        self.assertEqual(supplier.record_status, SupplierStatus.COMPLETE)
        self.assertEqual(supplier.version, 2)

        # Verify audit event for complete
        self.assertTrue(AuditEvent.objects.filter(object_id=str(supplier.id), action="complete").exists())

    def test_archive_supplier_success(self):
        """Analyst can archive a supplier record."""
        self.client.force_login(self.analyst)

        supplier = Supplier.objects.create(
            legal_name="To Archive Ltd",
            country_of_registration="IN",
            supplier_type=SupplierType.TRADER,
            record_status=SupplierStatus.DRAFT,
            created_by=self.analyst,
        )

        response = self.client.post(f"/api/v1/suppliers/{supplier.id}/archive/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        supplier.refresh_from_db()
        self.assertEqual(supplier.record_status, SupplierStatus.ARCHIVED)

    def test_supplier_concurrency_conflict(self):
        """M2-AC7: Updating with a stale version returns HTTP 409 Conflict."""
        self.client.force_login(self.analyst)

        supplier = Supplier.objects.create(
            legal_name="Concurrency Corp",
            country_of_registration="IN",
            supplier_type=SupplierType.MERCHANT_EXPORTER,
            version=2,
            created_by=self.analyst,
        )

        # Send stale version=1
        update_payload = {
            "legal_name": "Concurrency Corp Updated",
            "version": 1,
        }
        response = self.client.patch(f"/api/v1/suppliers/{supplier.id}/", update_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        data = response.json()
        self.assertEqual(data["code"], "conflict")

    def test_supplier_rbac_reviewer_denied_create(self):
        """RBAC: Reviewer cannot create a supplier (403 Forbidden)."""
        self.client.force_login(self.reviewer)

        payload = {
            "legal_name": "Unauthorized Create",
            "country_of_registration": "IN",
        }
        response = self.client.post("/api/v1/suppliers/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["code"], "permission_denied")


class ProductCatalogueTests(TestCase):
    """
    Test suite for Module M3: Product Catalogue.
    Covers creation, supplier linkage, Mandarin fields, units/pricing validation, and concurrency.
    """

    def setUp(self):
        self.client = APIClient()

        self.analyst = User.objects.create_user(
            email="analyst@bncs.local",
            password="Password123!",
            role=Role.COMMERCIAL_ANALYST,
            is_verified=True,
        )

        self.supplier = Supplier.objects.create(
            legal_name="Bharat Rice Mills",
            country_of_registration="IN",
            supplier_type=SupplierType.MANUFACTURER,
            record_status=SupplierStatus.COMPLETE,
            created_by=self.analyst,
        )

        self.archived_supplier = Supplier.objects.create(
            legal_name="Old Mills",
            country_of_registration="IN",
            record_status=SupplierStatus.ARCHIVED,
            created_by=self.analyst,
        )

    def test_create_product_success(self):
        """M3-AC1: Commercial Analyst can create a product linked to an existing supplier."""
        self.client.force_login(self.analyst)

        payload = {
            "supplier": str(self.supplier.id),
            "product_name": "Basmati 1121 Steam Rice",
            "product_category": "rice",
            "description": "Extra long grain aromatic basmati rice.",
            "moq_value": "25.00",
            "moq_unit": "MT",
            "price_min": "900.00",
            "price_max": "1100.00",
            "currency": "USD",
            "capacity_quantity": "500.00",
            "capacity_unit": "MT",
            "capacity_period": "MONTH",
            "lead_time_value": 21,
            "lead_time_unit": "DAYS",
        }
        response = self.client.post("/api/v1/products/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["product_name"], "Basmati 1121 Steam Rice")
        self.assertEqual(data["supplier_name"], "Bharat Rice Mills")
        self.assertEqual(data["translation_status"], TranslationStatus.NOT_PROVIDED)

    def test_create_product_under_archived_supplier_rejected(self):
        """Cannot create products under an archived supplier."""
        self.client.force_login(self.analyst)

        payload = {
            "supplier": str(self.archived_supplier.id),
            "product_name": "Product for Archived",
            "product_category": "rice",
        }
        response = self.client.post("/api/v1/products/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supplier", response.json()["field_errors"])

    def test_product_mandarin_translation_status(self):
        """M3-AC4: Supplying Mandarin text updates translation_status to provided_unreviewed."""
        self.client.force_login(self.analyst)

        payload = {
            "supplier": str(self.supplier.id),
            "product_name": "Organic Black Pepper",
            "product_category": "spices",
            "product_name_zh": "有机黑胡椒",
            "short_description_zh": "高品质印度黑胡椒",
        }
        response = self.client.post("/api/v1/products/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["product_name_zh"], "有机黑胡椒")
        self.assertEqual(data["translation_status"], TranslationStatus.PROVIDED_UNREVIEWED)

    def test_product_validation_errors(self):
        """M3-AC2: Validate positive numeric values, units, and price bounds."""
        self.client.force_login(self.analyst)

        payload = {
            "supplier": str(self.supplier.id),
            "product_name": "Invalid Product",
            "product_category": "pulses",
            "moq_value": "-5.00",  # Negative MOQ
            "price_min": "1000.00",
            "price_max": "800.00",  # Max < Min
            "lead_time_value": 0,    # Zero lead time
        }
        response = self.client.post("/api/v1/products/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        field_errors = response.json()["field_errors"]
        self.assertIn("moq_value", field_errors)
        self.assertIn("price_max", field_errors)
        self.assertIn("lead_time_value", field_errors)

    def test_product_concurrency_conflict(self):
        """Product update with stale version returns 409 Conflict."""
        self.client.force_login(self.analyst)

        product = Product.objects.create(
            supplier=self.supplier,
            product_name="Concurrency Rice",
            product_category="rice",
            version=3,
            created_by=self.analyst,
        )

        update_payload = {
            "product_name": "Updated Concurrency Rice",
            "version": 1,  # Stale version
        }
        response = self.client.patch(f"/api/v1/products/{product.id}/", update_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.json()["code"], "conflict")

    def test_frontend_supplier_payload_compatibility(self):
        """Verify frontend-specific payload shape (nested contact_details, address alias, Title Case) works."""
        self.client.force_login(self.analyst)

        frontend_payload = {
            "legal_name": "Frontend Compatible Exporters",
            "country_of_registration": "India",
            "supplier_type": "Manufacturer",  # Title Case
            "address_registration_reference": "Plot 42, Export City",
            "contact_details": {
                "contact_name": "Priyanka Singh",
                "email": "priyanka@frontend.local",
                "phone": "+91 9876543210",
            },
            "industry_description": "Agricultural commodities",
            "record_status": "Draft",  # Title Case
        }
        response = self.client.post("/api/v1/suppliers/", frontend_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        # Check both id and supplier_id are exposed
        self.assertIn("id", data)
        self.assertIn("supplier_id", data)
        self.assertEqual(data["id"], data["supplier_id"])
        self.assertEqual(data["supplier_type"], "manufacturer")
        self.assertEqual(data["record_status"], "draft")
        self.assertEqual(data["address"], "Plot 42, Export City")
        self.assertEqual(data["contact_details"]["contact_name"], "Priyanka Singh")
        self.assertEqual(data["contact_details"]["email"], "priyanka@frontend.local")

    def test_frontend_product_payload_compatibility(self):
        """Verify frontend-specific product payload (supplier_id alias, minimum_order_quantity, indicative_price) works."""
        self.client.force_login(self.analyst)

        frontend_payload = {
            "supplier_id": str(self.supplier.id),
            "product_name": "Frontend Sourced Basmati",
            "product_category": "Agriculture and Food",
            "minimum_order_quantity": 25,
            "minimum_order_unit": "tonnes",
            "indicative_price_min": 750,
            "indicative_price_max": 850,
            "currency": "USD",
            "price_basis": "FOB",
            "translation_status": "Not provided",
        }
        response = self.client.post("/api/v1/products/", frontend_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        # Check both id and product_id are exposed
        self.assertIn("id", data)
        self.assertIn("product_id", data)
        self.assertEqual(data["id"], data["product_id"])
        self.assertEqual(data["supplier_id"], str(self.supplier.id))
        self.assertEqual(data["translation_status"], "not_provided")
        self.assertEqual(data["minimum_order_quantity"], 25.0)
        self.assertEqual(data["indicative_price_min"], 750.0)

