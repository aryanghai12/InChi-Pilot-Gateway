from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase

from apps.demand.models import (
    BuyerRequirement,
    BuyerRequirementVersion,
    MatchingReadinessBlocker,
    RequirementCommercialTerms,
    RequirementDelivery,
    RequirementQuantity,
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
            15,
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
