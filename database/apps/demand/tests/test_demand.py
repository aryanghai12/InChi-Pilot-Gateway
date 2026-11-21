from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.demand.models import (
    BuyerRequirement,
    BuyerRequirementVersion,
    MatchingReadinessBlocker,
    RequirementCommercialTerms,
    RequirementDelivery,
    RequirementQuantity,
    RequirementSpecification,
    RequirementEligibilityCriterion,
)


class BuyerRequirementModelTests(TestCase):
    def test_seed_command_loads_twenty_rows_and_is_repeatable(self):
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(BuyerRequirement.objects.count(), 20)
        self.assertEqual(
            BuyerRequirementVersion.objects.count(),
            20,
        )
        self.assertEqual(
            MatchingReadinessBlocker.objects.count(),
            20,
        )

        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(BuyerRequirement.objects.count(), 20)
        self.assertEqual(BuyerRequirementVersion.objects.count(), 20)

    def test_version_number_is_unique_per_requirement(self):
        requirement = BuyerRequirement.objects.create()
        BuyerRequirementVersion.objects.create(requirement=requirement, version=1)

        with self.assertRaises(IntegrityError):
            BuyerRequirementVersion.objects.create(requirement=requirement, version=1)

    def test_invalid_price_range_is_rejected_by_database(self):
        requirement = BuyerRequirement.objects.create()
        version = BuyerRequirementVersion.objects.create(requirement=requirement, version=1)

        with self.assertRaises(IntegrityError):
            RequirementCommercialTerms.objects.create(
                requirement_version=version,
                target_price_min=Decimal("20"),
                target_price_max=Decimal("10"),
            )

    def test_invalid_delivery_window_is_rejected_by_database(self):
        requirement = BuyerRequirement.objects.create()
        version = BuyerRequirementVersion.objects.create(requirement=requirement, version=1)

        with self.assertRaises(IntegrityError):
            RequirementDelivery.objects.create(
                requirement_version=version,
                delivery_window_start="2027-02-01",
                delivery_window_end="2027-01-01",
            )

    def test_negative_quantity_is_rejected_by_database(self):
        requirement = BuyerRequirement.objects.create()
        version = BuyerRequirementVersion.objects.create(requirement=requirement, version=1)

        with self.assertRaises(IntegrityError):
            RequirementQuantity.objects.create(
                requirement_version=version,
                quantity_value=Decimal("-1"),
            )

    def test_quantity_requires_unit(self):
        requirement = BuyerRequirement.objects.create()
        version = BuyerRequirementVersion.objects.create(requirement=requirement, version=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RequirementQuantity.objects.create(
                    requirement_version=version,
                    quantity_value=Decimal("10"),
                    quantity_unit="",
                )

    def test_price_requires_currency_and_basis(self):
        requirement = BuyerRequirement.objects.create()
        version = BuyerRequirementVersion.objects.create(requirement=requirement, version=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                RequirementCommercialTerms.objects.create(
                    requirement_version=version,
                    target_price_min=Decimal("10"),
                    target_price_max=Decimal("20"),
                    currency_code="",
                    price_basis="",
                )

    def test_ready_for_matching_gate_accepts_complete_requirement(self):
        owner = get_user_model().objects.create_user(
            username="week4-owner",
            password="not-used",
        )
        requirement = BuyerRequirement.objects.create(
            buyer_organisation_name="China Buyer Co",
            product_category_id="AGRICULTURE_FOOD",
            owner_user=owner,
        )
        version = BuyerRequirementVersion.objects.create(requirement=requirement, version=1)
        RequirementSpecification.objects.create(
            requirement_version=version,
            attributes={"product": "approved synthetic specification"},
        )
        RequirementQuantity.objects.create(
            requirement_version=version,
            quantity_value=Decimal("100"),
            quantity_unit="KILOGRAM",
        )
        RequirementDelivery.objects.create(
            requirement_version=version,
            delivery_location={"city": "Shanghai", "country": "China"},
        )
        RequirementEligibilityCriterion.objects.create(
            requirement_version=version,
            criterion_key="category",
            operator="equals",
            criterion_value={"value": "AGRICULTURE_FOOD"},
        )

        requirement.mark_ready_for_matching(version)

    def test_ready_for_matching_gate_blocks_missing_owner(self):
        requirement = BuyerRequirement.objects.create(
            buyer_organisation_name="China Buyer Co",
            product_category_id="AGRICULTURE_FOOD",
        )
        version = BuyerRequirementVersion.objects.create(requirement=requirement, version=1)
        with self.assertRaises(ValidationError):
            requirement.mark_ready_for_matching(version)

    def test_requirement_version_is_immutable(self):
        requirement = BuyerRequirement.objects.create()
        version = BuyerRequirementVersion.objects.create(requirement=requirement, version=1)
        version.change_reason = "Attempted material edit"
        with self.assertRaises(ValidationError):
            version.save()

    def test_close_changes_status_and_disables_matching_ready(self):
        requirement = BuyerRequirement.objects.create(
            buyer_organisation_name="China Buyer",
            matching_ready=True,
            requirement_status="READY_FOR_MATCHING",
        )
        requirement.close()
        requirement.refresh_from_db()
        self.assertEqual(
            requirement.requirement_status,
            BuyerRequirement.RequirementStatus.CLOSED,
        )
        self.assertFalse(requirement.matching_ready)
