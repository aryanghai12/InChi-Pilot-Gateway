import csv
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

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
    "evidence_type": [
        ("QUALITY_CERTIFICATE", "Quality certificate"),
        ("ORIGIN_CERTIFICATE", "Certificate of origin"),
        ("PRODUCT_SPECIFICATION", "Product specification"),
    ],
}


class Command(BaseCommand):
    help = "Create repeatable synthetic buyer-demand reference and demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_reference_values()
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
                matching_ready = row["matching_ready"].lower() == "true"
                requirement, was_created = BuyerRequirement.objects.get_or_create(
                    buyer_reference=row["buyer_reference"],
                    defaults={
                        "requirement_id": row["requirement_id"],
                        "buyer_organisation_name": row["buyer_organisation_name"],
                        "target_market": row["target_market"],
                        "product_category_id": row["product_category_id"],
                        "requirement_title": row["requirement_title"],
                        "requirement_status": row["requirement_status"],
                        "completeness_status": row["completeness_status"],
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
                f"{BuyerRequirement.objects.count()} total."
            )
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
