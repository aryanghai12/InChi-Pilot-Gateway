"""
Integration Tests: Candidate payload mapping from registry records (Component A).

Uses real registry models (synthetic records) to prove the Product -> candidate
payload mapping is field-for-field, keeps unknown values unknown (M3-AC2) and
does not filter candidates (eligibility is the engine's job).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
"""

from decimal import Decimal

from django.test import TestCase

from apps.matching.services.supplier_selector import (
    build_candidate_payloads,
    candidate_from_product,
)
from apps.registry.models import EvidenceItem, Product, Supplier, SupplierStatus


class SupplierSelectorTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            legal_name="Synthetic Supplier Pvt Ltd",
            country_of_registration="IN",
            supplier_type="manufacturer",
            industry_description="Synthetic electronics assembly.",
            record_status=SupplierStatus.COMPLETE,
        )
        self.product = Product.objects.create(
            supplier=self.supplier,
            product_name="Synthetic Circuit Board",
            product_category="Electronic Goods",
            description="Synthetic board.",
            origin="India",
            moq_value=Decimal("100.00"),
            moq_unit="PIECES",
            lead_time_value=30,
            lead_time_unit="DAYS",
        )
        EvidenceItem.objects.create(
            product=self.product, document_type="QUALITY_CERTIFICATE", evidence_reference="SYN-001"
        )
        EvidenceItem.objects.create(
            supplier=self.supplier, document_type="ORIGIN_CERTIFICATE", evidence_reference="SYN-002"
        )

    def test_maps_product_and_supplier_fields(self):
        payload = candidate_from_product(self.product)
        self.assertEqual(payload.candidate_id, str(self.product.id))
        self.assertEqual(payload.supplier_id, str(self.supplier.id))
        self.assertEqual(payload.supplier_country, "IN")
        self.assertEqual(payload.supplier_record_status, "complete")
        self.assertEqual(payload.moq_value, Decimal("100.00"))
        self.assertEqual(payload.origin, "India")  # raw; the engine normalises

    def test_includes_product_and_supplier_evidence(self):
        payload = candidate_from_product(self.product)
        self.assertEqual(
            sorted(item.document_type for item in payload.evidence),
            ["ORIGIN_CERTIFICATE", "QUALITY_CERTIFICATE"],
        )
        self.assertTrue(all(item.review_status == "unreviewed" for item in payload.evidence))

    def test_unknown_values_stay_unknown(self):
        payload = candidate_from_product(self.product)
        self.assertIsNone(payload.capacity_quantity)
        self.assertIsNone(payload.price_min)
        self.assertIsNone(payload.readiness_status)

    def test_does_not_filter_archived_suppliers(self):
        self.supplier.record_status = SupplierStatus.ARCHIVED
        self.supplier.save()
        payloads = build_candidate_payloads(Product.objects.select_related("supplier"))
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0].supplier_record_status, "archived")

    def test_readiness_lookup_by_supplier(self):
        payloads = build_candidate_payloads([self.product], {str(self.supplier.id): "reviewed-outcome"})
        self.assertEqual(payloads[0].readiness_status, "reviewed-outcome")
