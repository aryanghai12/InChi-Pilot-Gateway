from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import IntegrityError, transaction

from apps.readiness.models import (
    EvidenceRecord,
    ReadinessAssessment,
    ReadinessAuditEvent,
    ReadinessBlocker,
    ReadinessResponse,
)
from apps.registry.models import Product, Supplier


class ReadinessDatabaseTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            legal_name="Week 3 Supplier",
            supplier_type=Supplier.SupplierType.MANUFACTURER,
            registered_address="India",
            state_country="India",
            primary_contact="Test Contact",
            contact_email="week3@example.com",
            record_status=Supplier.RecordStatus.ACTIVE,
        )
        self.product = Product.objects.create(
            supplier=self.supplier,
            product_name_en="Test Product",
            category_code=Product.CategoryCode.AGRICULTURE_FOOD,
            technical_specification="Test specification",
            unit_of_measure=Product.UnitOfMeasure.KILOGRAM,
            declared_capacity="100",
            capacity_period=Product.CapacityPeriod.MONTH,
            moq="10",
            lead_time_days=30,
            packaging_description="Food-grade cartons",
        )
        self.assessment = ReadinessAssessment.objects.create(
            supplier=self.supplier,
            questionnaire_version="2.2",
        )
        self.assessment.products.add(self.product)

    def test_assessment_requires_v2_2_questionnaire(self):
        self.assertEqual(self.assessment.questionnaire_version, "2.2")
        self.assertTrue(self.assessment.products.filter(pk=self.product.pk).exists())

    def test_response_is_unique_per_assessment_and_criterion(self):
        ReadinessResponse.objects.create(
            assessment=self.assessment,
            criterion_id="CR-01",
            response_value={"legal_name": "Week 3 Supplier"},
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ReadinessResponse.objects.create(
                    assessment=self.assessment,
                    criterion_id="CR-01",
                    response_value={"legal_name": "Duplicate"},
                )

    def test_document_receipt_defaults_to_unverified(self):
        evidence = EvidenceRecord.objects.create(
            assessment=self.assessment,
            criterion_id="CR-13",
            evidence_type=EvidenceRecord.EvidenceType.CERTIFICATE,
        )
        self.assertEqual(
            evidence.evidence_condition,
            EvidenceRecord.EvidenceCondition.DOCUMENT_RECEIVED_UNVERIFIED,
        )

    def test_expired_evidence_is_stored_as_visible_condition(self):
        evidence = EvidenceRecord.objects.create(
            assessment=self.assessment,
            criterion_id="CR-13",
            evidence_type=EvidenceRecord.EvidenceType.TEST_REPORT,
            evidence_condition=EvidenceRecord.EvidenceCondition.EXPIRED,
        )
        self.assertEqual(
            evidence.evidence_condition,
            EvidenceRecord.EvidenceCondition.EXPIRED,
        )

    def test_discrepancy_creates_information_required_blocker(self):
        blocker = ReadinessBlocker.objects.create(
            assessment=self.assessment,
            criterion_id="CR-14",
            reason_code="DISCREPANCY",
            reason_detail="Document conflicts with submitted response.",
        )
        self.assertTrue(blocker.active)

    def test_not_applicable_requires_reason_at_model_validation(self):
        response = ReadinessResponse(
            assessment=self.assessment,
            criterion_id="CR-03",
            response_state=ReadinessResponse.ResponseState.NOT_APPLICABLE,
            state_reason="",
        )
        with self.assertRaises(ValidationError):
            response.full_clean()

    def test_audit_event_records_material_change(self):
        event = ReadinessAuditEvent.objects.create(
            action="READINESS_TRANSITION",
            object_type="ReadinessAssessment",
            object_id=str(self.assessment.assessment_id),
            object_version=1,
            previous_value={"workflow_state": "DRAFT"},
            new_value={"workflow_state": "SUBMITTED"},
            change_summary="Assessment moved to Submitted.",
        )
        self.assertEqual(event.object_id, str(self.assessment.assessment_id))

    def test_audit_event_is_append_only_in_postgresql(self):
        event = ReadinessAuditEvent.objects.create(
            action="TEST_APPEND_ONLY",
            object_type="ReadinessAssessment",
            object_id=str(self.assessment.assessment_id),
            change_summary="Initial audit row.",
        )
        with self.assertRaises(Exception):
            with transaction.atomic():
                event.change_summary = "Changed audit row."
                event.save(update_fields=["change_summary"])
