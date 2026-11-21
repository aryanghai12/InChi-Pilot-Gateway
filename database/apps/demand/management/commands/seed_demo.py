import csv
import json
import os
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured

from apps.demand.models import (
    BuyerRequirement,
    BuyerRequirementVersion,
    MatchingReadinessBlocker,
    ReferenceValue,
    RequirementCommercialTerms,
    RequirementDelivery,
    RequirementEligibilityCriterion,
    RequirementEvidenceCriterion,
    RequirementPreference,
    RequirementQuantity,
    RequirementSpecification,
    MatchingConfiguration,
)
from apps.registry.models import Product, Supplier
from apps.readiness.models import (
    EvidenceRecord,
    ReadinessAssessment,
    ReadinessBlocker,
    ReadinessResponse,
    ReadinessSubmissionSnapshot,
)


REFERENCE_VALUES = {
    "market": [("IN", "India"), ("CN", "China"), ("AE", "United Arab Emirates")],
    "product_category": [
        ("AGRI_FOOD", "Agriculture and Food"),
        ("TEXTILES", "Textiles"),
        ("ENGINEERING", "Engineering Goods"),
        ("ELECTRONICS", "Electronic Goods"),
        ("CHEMICALS", "Chemicals"),
        ("MINERALS", "Minerals and Metals"),
        ("MARINE", "Marine Products"),
    ],
    "quantity_unit": [("KG", "Kilograms"), ("MT", "Metric Tonnes"), ("PIECES", "Pieces")],
    "currency": [("USD", "US Dollar"), ("INR", "Indian Rupee"), ("CNY", "Chinese Yuan")],
    "price_basis": [("PER_KG", "Per kilogram"), ("PER_MT", "Per metric tonne"), ("PER_PIECE", "Per piece")],
    "supplier_type": [
        ("MANUFACTURER", "Manufacturer"),
        ("TRADER", "Trader"),
        ("DISTRIBUTOR", "Distributor"),
        ("AGENT", "Agent"),
        ("HYBRID", "Hybrid"),
    ],
    "unit_of_measure": [
        ("PIECE", "Piece"),
        ("KILOGRAM", "Kilogram"),
        ("METRIC_TONNE", "Metric tonne"),
        ("LITRE", "Litre"),
        ("CARTON", "Carton"),
    ],
    "capacity_period": [
        ("WEEK", "Week"),
        ("MONTH", "Month"),
        ("QUARTER", "Quarter"),
    ],
    "category_code": [
        ("AGRICULTURE_FOOD", "Agriculture and Food"),
        ("MINERALS_METALS", "Minerals and Metals"),
        ("MARINE_PRODUCTS", "Marine Products"),
        ("CHEMICALS", "Chemicals"),
        ("PETROLEUM_PRODUCTS", "Petroleum Products"),
    ],
    "evidence_type": [
        ("QUALITY_CERTIFICATE", "Quality certificate"),
        ("ORIGIN_CERTIFICATE", "Certificate of origin"),
        ("PRODUCT_SPECIFICATION", "Product specification"),
    ],
}

CATEGORY_CODE_MAP = {
    "AGRI_FOOD": "AGRICULTURE_FOOD",
    "TEXTILES": "AGRICULTURE_FOOD",
    "ENGINEERING": "MINERALS_METALS",
    "ELECTRONICS": "CHEMICALS",
    "CHEMICALS": "CHEMICALS",
    "MINERALS": "MINERALS_METALS",
    "MARINE": "MARINE_PRODUCTS",
}


class Command(BaseCommand):
    help = "Create repeatable synthetic buyer-demand reference and demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_reference_values()
        self._seed_registry()
        self._seed_readiness()
        users_created = self._seed_demo_users()
        MatchingConfiguration.objects.update_or_create(
            configuration_key="buyer-demand-demo",
            version=1,
            defaults={
                "status": MatchingConfiguration.Status.DRAFT,
                "configuration": {
                    "weights": {},
                    "thresholds": {},
                    "note": "Synthetic configuration only; approval required before matching.",
                },
            },
        )

        created = 0
        fixture_path = Path(settings.BASE_DIR) / "seed" / "synthetic_buyer_requirements.csv"
        with fixture_path.open(newline="", encoding="utf-8") as fixture:
            rows = csv.DictReader(fixture)
            for row in rows:
                number = int(row["buyer_reference"].split("-")[-1])
                raw_status = row["requirement_status"].lower()
                requirement_status = (
                    "READY_FOR_MATCHING"
                    if raw_status in {"ready_for_matching", "complete"}
                    else "CLOSED"
                    if raw_status == "closed"
                    else "DRAFT"
                )
                matching_ready = row["matching_ready"].lower() == "true"
                matching_ready = matching_ready and requirement_status == "READY_FOR_MATCHING"
                completeness_status = (
                    "COMPLETE"
                    if row["completeness_status"].lower() == "complete"
                    else "INCOMPLETE"
                )
                product_category_id = CATEGORY_CODE_MAP.get(
                    row["product_category_id"],
                    row["product_category_id"],
                )
                requirement, was_created = BuyerRequirement.objects.get_or_create(
                    buyer_reference=row["buyer_reference"],
                    defaults={
                        "requirement_id": row["requirement_id"],
                        "buyer_organisation_name": row["buyer_organisation_name"],
                        "target_market": row["target_market"],
                        "product_category_id": product_category_id,
                        "requirement_title": row["requirement_title"],
                        "requirement_status": requirement_status,
                        "completeness_status": completeness_status,
                        "matching_ready": matching_ready,
                    },
                )
                if not was_created:
                    continue

                created += 1
                version = BuyerRequirementVersion.objects.create(
                    requirement=requirement,
                    version=1,
                    requirement_notes=row["notes"],
                    schema_version="buyer-requirement-v1",
                    change_reason="Initial demo seed",
                )
                RequirementSpecification.objects.create(
                    requirement_version=version,
                    attributes={"material": "synthetic", "grade": f"G-{number:02d}"},
                )
                RequirementQuantity.objects.create(
                    requirement_version=version,
                    quantity_value=Decimal(row["quantity_value"]),
                    quantity_unit=row["quantity_unit"],
                    order_frequency=row["order_frequency"],
                    recurrence_interval=None if row["order_frequency"] == "one_off" else 1,
                    recurrence_period="" if row["order_frequency"] == "one_off" else "month",
                )
                RequirementCommercialTerms.objects.create(
                    requirement_version=version,
                    target_price_min=Decimal(row["target_price_min"]),
                    target_price_max=Decimal(row["target_price_max"]),
                    currency_code=row["currency_code"],
                    price_basis=row["price_basis"],
                )
                RequirementDelivery.objects.create(
                    requirement_version=version,
                    delivery_location={
                        "city": row["delivery_city"],
                        "country": row["delivery_country"],
                    },
                    required_lead_time_value=int(row["required_lead_time_value"]),
                    required_lead_time_unit=row["required_lead_time_unit"],
                )
                RequirementEvidenceCriterion.objects.create(
                    requirement_version=version,
                    evidence_type=row["mandatory_evidence"],
                    criterion_value={"status": "required"},
                    classification=RequirementEvidenceCriterion.MANDATORY,
                    taxonomy_version="evidence-v1",
                )
                RequirementEligibilityCriterion.objects.create(
                    requirement_version=version,
                    criterion_key="origin_country",
                    operator="equals",
                    criterion_value={"value": "IN"},
                    unknown_policy="exclude",
                    criteria_version="criteria-v1",
                )
                RequirementPreference.objects.create(
                    requirement_version=version,
                    preference_key=row["preferred_criteria"],
                    preference_value={"preferred_max_days": 45},
                    priority_weight_key="lead_time",
                    criteria_version="criteria-v1",
                )
                if not matching_ready:
                    MatchingReadinessBlocker.objects.create(
                        requirement_version=version,
                        field_id="BUY-032",
                        reason_code="INCOMPLETE_REQUIREMENT",
                        reason_detail="Synthetic record requires approved completeness inputs.",
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {created} new synthetic buyer requirements created; "
                f"{BuyerRequirement.objects.count()} total; "
                f"{users_created} synthetic role account(s) available."
            )
        )

    def _seed_demo_users(self):
        password = os.getenv("DEMO_USER_PASSWORD", "").strip()
        if not password:
            return 0

        User = get_user_model()
        user_fields = {field.name for field in User._meta.fields}
        if "role" not in user_fields:
            return 0

        valid_roles = {
            "platform_admin",
            "commercial_analyst",
            "reviewer",
        }
        fixture_path = Path(settings.BASE_DIR) / "seed" / "synthetic_demo_accounts.csv"
        created_count = 0

        with fixture_path.open(newline="", encoding="utf-8") as fixture:
            for row in csv.DictReader(fixture):
                role = row["role"].strip()
                email = row["email"].strip().lower()
                if role not in valid_roles:
                    raise ImproperlyConfigured(
                        f"Unsupported synthetic demo role: {role}"
                    )

                defaults = {
                    "role": role,
                    "is_active": True,
                    "is_verified": True,
                    "is_staff": role == "platform_admin",
                    "is_superuser": False,
                }

                if hasattr(User.objects, "create_user"):
                    user, was_created = User.objects.get_or_create(
                        email=email,
                        defaults=defaults,
                    )
                else:
                    user, was_created = User.objects.get_or_create(
                        username=email,
                        defaults=defaults,
                    )

                if was_created:
                    created_count += 1

                user.role = role
                user.is_active = True
                user.is_verified = True
                user.is_staff = role == "platform_admin"
                user.is_superuser = False
                user.set_password(password)
                user.save()

        return created_count

    def _seed_registry(self):
        suppliers_path = Path(settings.BASE_DIR) / "seed" / "synthetic_suppliers.csv"
        with suppliers_path.open(newline="", encoding="utf-8") as fixture:
            for row in csv.DictReader(fixture):
                Supplier.objects.update_or_create(
                    supplier_id=row["supplier_id"],
                    defaults={
                        "legal_name": row["legal_name"],
                        "trading_name": row["trading_name"],
                        "supplier_type": row["supplier_type"],
                        "registered_address": row["registered_address"],
                        "state_country": row["state_country"],
                        "gstin": row["gstin"],
                        "iec": row["iec"],
                        "primary_contact": row["primary_contact"],
                        "contact_email": row["contact_email"],
                        "export_markets": json.loads(row["export_markets"]),
                        "record_status": row["record_status"],
                    },
                )

    def _seed_readiness(self):
        supplier_product_pairs = [
            (
                "10000000-0000-0000-0000-000000000001",
                "20000000-0000-0000-0000-000000000001",
                ReadinessAssessment.WorkflowState.REVIEW_COMPLETE,
                ReadinessAssessment.ReadinessOutcome.READY_FOR_MATCHING,
                [],
            ),
            (
                "10000000-0000-0000-0000-000000000002",
                "20000000-0000-0000-0000-000000000003",
                ReadinessAssessment.WorkflowState.INFORMATION_REQUIRED,
                ReadinessAssessment.ReadinessOutcome.INFORMATION_REQUIRED,
                ["DISCREPANCY"],
            ),
            (
                "10000000-0000-0000-0000-000000000003",
                "20000000-0000-0000-0000-000000000005",
                ReadinessAssessment.WorkflowState.REVIEW_COMPLETE,
                ReadinessAssessment.ReadinessOutcome.NOT_CURRENTLY_ELIGIBLE,
                ["MANDATORY_BASELINE_FAILURE"],
            ),
        ]
        for index, (supplier_id, product_id, state, outcome, blocker_codes) in enumerate(
            supplier_product_pairs,
            start=1,
        ):
            supplier = Supplier.objects.get(pk=supplier_id)
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                product = Product.objects.filter(supplier=supplier).first()
                if product is None:
                    continue
            assessment_id = f"30000000-0000-0000-0000-{index:012d}"
            assessment, created = ReadinessAssessment.objects.update_or_create(
                assessment_id=assessment_id,
                defaults={
                    "supplier": supplier,
                    "assessment_version": 1,
                    "questionnaire_version": "2.2",
                    "workflow_state": state,
                    "readiness_outcome": outcome,
                    "readiness_outcome_reason": "Synthetic Week 3 demonstration record.",
                    "contributor_confirmed": True,
                },
            )
            assessment.products.set([product])
            if not created:
                assessment.responses.all().delete()
                assessment.blockers.all().delete()
                assessment.evidence_records.all().delete()

            for criterion_id in (
                "CR-01",
                "CR-02",
                "CR-04",
                "CR-06",
                "CR-07",
                "CR-08",
                "CR-09",
                "CR-10",
                "CR-12",
                "CR-13",
                "CR-14",
                "CR-15",
                "CR-16",
                "CR-17",
                "CR-18",
            ):
                ReadinessResponse.objects.create(
                    assessment=assessment,
                    criterion_id=criterion_id,
                    response_value={"synthetic": True, "record": index},
                    evidence_condition=(
                        EvidenceRecord.EvidenceCondition.SELF_DECLARED
                        if criterion_id in {"CR-01", "CR-02", "CR-15"}
                        else ""
                    ),
                )

            evidence_condition = EvidenceRecord.EvidenceCondition.DOCUMENT_RECEIVED_UNVERIFIED
            if index == 2:
                evidence_condition = EvidenceRecord.EvidenceCondition.DISCREPANCY
            elif index == 3:
                evidence_condition = EvidenceRecord.EvidenceCondition.EXPIRED

            EvidenceRecord.objects.create(
                assessment=assessment,
                criterion_id="CR-13",
                evidence_type=EvidenceRecord.EvidenceType.TEST_REPORT,
                evidence_condition=evidence_condition,
                issuer_source="Synthetic approved evidence source",
                reference_number=f"SYN-CR13-{index}",
                reviewer_notes="Synthetic database demonstration only.",
            )

            for blocker_code in blocker_codes:
                ReadinessBlocker.objects.create(
                    assessment=assessment,
                    criterion_id="CR-14",
                    reason_code=blocker_code,
                    reason_detail="Synthetic readiness blocker for database validation.",
                    active=True,
                )

            ReadinessSubmissionSnapshot.objects.update_or_create(
                assessment=assessment,
                defaults={
                    "questionnaire_version": "2.2",
                    "snapshot": {
                        "assessment_version": 1,
                        "supplier_id": supplier_id,
                        "product_ids": [product_id],
                        "synthetic": True,
                    },
                },
            )

        products_path = Path(settings.BASE_DIR) / "seed" / "synthetic_products.csv"
        with products_path.open(newline="", encoding="utf-8") as fixture:
            for row in csv.DictReader(fixture):
                supplier = Supplier.objects.get(pk=row["supplier_id"])
                Product.objects.update_or_create(
                    product_id=row["product_id"],
                    defaults={
                        "supplier": supplier,
                        "product_name_en": row["product_name_en"],
                        "product_name_zh_draft": row["product_name_zh_draft"],
                        "category_code": row["category_code"],
                        "hs_code_declared": row["hs_code_declared"],
                        "model_grade": row["model_grade"],
                        "technical_specification": row["technical_specification"],
                        "unit_of_measure": row["unit_of_measure"],
                        "declared_capacity": Decimal(row["declared_capacity"]),
                        "capacity_period": row["capacity_period"],
                        "moq": Decimal(row["moq"]),
                        "lead_time_days": int(row["lead_time_days"]),
                        "price_amount": Decimal(row["price_amount"]) if row["price_amount"] else None,
                        "price_currency_basis": row["price_currency_basis"],
                        "origin_country": row["origin_country"],
                        "packaging_description": row["packaging_description"],
                    },
                )

    def _seed_reference_values(self):
        for reference_type, values in REFERENCE_VALUES.items():
            for code, display_name in values:
                ReferenceValue.objects.update_or_create(
                    reference_type=reference_type,
                    code=code,
                    version=1,
                    defaults={
                        "display_name": display_name,
                        "status": ReferenceValue.Status.ACTIVE,
                        "metadata": {"source": "synthetic-demo-seed"},
                    },
                )
