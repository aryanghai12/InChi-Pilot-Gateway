"""
Unit Tests: Text Preprocessing and Sanitization (Pipeline Stage 1).

Tests text normalisation, code/alias normalisation, unknown-stays-unknown
handling, quality flags and deterministic embedding-ready records.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
"""

import unittest
from decimal import Decimal

from ai_matching.core.constants import EMBEDDING_TEXT_TEMPLATE_VERSION, QualityFlag
from ai_matching.schemas.buyer import BuyerRequirementInput
from ai_matching.schemas.supplier import SupplierCandidateInput
from ai_matching.services import preprocessing as pp
from ai_matching.tests.factories import candidate_payload, requirement_payload


def _flags(prepared) -> set[tuple[QualityFlag, str]]:
    return {(issue.flag, issue.field) for issue in prepared.quality_issues}


class NormaliseTextTests(unittest.TestCase):
    def test_collapses_whitespace_and_strips(self):
        self.assertEqual(pp.normalise_text("  Synthetic \t\n  board  "), "Synthetic board")

    def test_removes_control_characters(self):
        self.assertEqual(pp.normalise_text("Board\x00\x07name"), "Board name")

    def test_applies_nfkc(self):
        # Full-width letters fold to ASCII under NFKC.
        self.assertEqual(pp.normalise_text("ＡＢＣ"), "ABC")

    def test_none_and_empty_return_empty_string(self):
        self.assertEqual(pp.normalise_text(None), "")
        self.assertEqual(pp.normalise_text(""), "")


class CodeNormalisationTests(unittest.TestCase):
    def test_quantity_unit_aliases(self):
        for raw, expected in [("kg", "KG"), ("Kilograms", "KG"), ("metric tonnes", "MT"), ("pcs", "PIECES")]:
            with self.subTest(raw=raw):
                self.assertEqual(pp.normalise_quantity_unit(raw).code, expected)

    def test_ambiguous_ton_is_not_guessed(self):
        result = pp.normalise_quantity_unit("ton")
        self.assertIsNone(result.code)
        self.assertEqual(result.raw, "ton")

    def test_lead_time_unit_matches_demand_seed_lowercase(self):
        self.assertEqual(pp.normalise_lead_time_unit("days").code, "DAYS")

    def test_country_names_map_to_iso_alpha2(self):
        self.assertEqual(pp.normalise_country("India").code, "IN")
        self.assertEqual(pp.normalise_country("CHN").code, "CN")
        self.assertIsNone(pp.normalise_country("Atlantis").code)

    def test_category_display_name_maps_to_reference_code(self):
        self.assertEqual(pp.normalise_category("Electronic Goods").code, "ELECTRONICS")
        self.assertEqual(pp.normalise_category("Minerals & Metals").code, "MINERALS")
        self.assertIsNone(pp.normalise_category("Spaceships").code)

    def test_currency_shape_only_no_conversion(self):
        self.assertEqual(pp.normalise_currency(" usd ").code, "USD")
        self.assertIsNone(pp.normalise_currency("US$").code)

    def test_empty_value_is_unknown_not_default(self):
        result = pp.normalise_quantity_unit("")
        self.assertIsNone(result.code)
        self.assertEqual(result.raw, "")


class PrepareCandidateTests(unittest.TestCase):
    def test_complete_candidate_is_normalised_without_issues(self):
        prepared = pp.prepare_candidate(SupplierCandidateInput(**candidate_payload()))
        self.assertEqual(prepared.quality_issues, ())
        self.assertEqual(prepared.values["product_category"], "ELECTRONICS")
        self.assertEqual(prepared.values["origin_country"], "IN")
        self.assertEqual(prepared.values["moq_unit"], "PIECES")
        self.assertEqual(prepared.values["moq_value"], Decimal(100))
        self.assertEqual(prepared.values["capacity_period"], "MONTH")
        self.assertEqual(prepared.values["lead_time_unit"], "DAYS")
        self.assertEqual(prepared.values["currency"], "USD")
        self.assertEqual(prepared.values["evidence_types"], ("QUALITY_CERTIFICATE",))

    def test_missing_numeric_value_stays_none_and_is_flagged(self):
        """M3-AC2: unknown values are never zero or a default."""
        prepared = pp.prepare_candidate(SupplierCandidateInput(**candidate_payload(moq_value=None)))
        self.assertIsNone(prepared.values["moq_value"])
        self.assertIn((QualityFlag.MISSING_VALUE, "moq_value"), _flags(prepared))

    def test_value_without_unit_is_flagged(self):
        prepared = pp.prepare_candidate(SupplierCandidateInput(**candidate_payload(moq_unit="")))
        self.assertIn((QualityFlag.MISSING_UNIT, "moq_unit"), _flags(prepared))

    def test_unrecognised_codes_are_flagged_not_guessed(self):
        prepared = pp.prepare_candidate(
            SupplierCandidateInput(**candidate_payload(origin="Atlantis", product_category="Spaceships"))
        )
        self.assertIsNone(prepared.values["origin_country"])
        self.assertIsNone(prepared.values["product_category"])
        self.assertIn((QualityFlag.UNRECOGNISED_COUNTRY, "origin"), _flags(prepared))
        self.assertIn((QualityFlag.UNRECOGNISED_CATEGORY, "product_category"), _flags(prepared))

    def test_single_price_bound_is_incomplete_range(self):
        prepared = pp.prepare_candidate(SupplierCandidateInput(**candidate_payload(price_max=None)))
        self.assertIn((QualityFlag.INCOMPLETE_RANGE, "price_range"), _flags(prepared))

    def test_no_descriptive_text_is_flagged(self):
        prepared = pp.prepare_candidate(
            SupplierCandidateInput(**candidate_payload(description="", specifications=""))
        )
        self.assertIn((QualityFlag.NO_DESCRIPTIVE_TEXT, "description"), _flags(prepared))


class PrepareRequirementTests(unittest.TestCase):
    def test_requirement_normalisation_and_evidence_split(self):
        prepared = pp.prepare_requirement(BuyerRequirementInput(**requirement_payload()))
        self.assertEqual(prepared.values["product_category"], "ELECTRONICS")
        self.assertEqual(prepared.values["required_lead_time_unit"], "DAYS")
        self.assertEqual(prepared.values["mandatory_evidence"], ("QUALITY_CERTIFICATE",))
        self.assertEqual(prepared.values["preferred_evidence"], ())
        self.assertEqual(prepared.quality_issues, ())

    def test_missing_quantity_is_flagged(self):
        prepared = pp.prepare_requirement(BuyerRequirementInput(**requirement_payload(quantity_value=None)))
        self.assertIsNone(prepared.values["quantity_value"])
        self.assertIn((QualityFlag.MISSING_VALUE, "quantity_value"), _flags(prepared))


class EmbeddingRecordTests(unittest.TestCase):
    def test_record_is_deterministic(self):
        first = pp.build_candidate_embedding_record(SupplierCandidateInput(**candidate_payload()))
        second = pp.build_candidate_embedding_record(SupplierCandidateInput(**candidate_payload()))
        self.assertEqual(first, second)
        self.assertEqual(first.template_version, EMBEDDING_TEXT_TEMPLATE_VERSION)
        self.assertEqual(len(first.source_hash), 64)

    def test_whitespace_only_changes_do_not_change_hash(self):
        base = pp.build_candidate_embedding_record(SupplierCandidateInput(**candidate_payload()))
        spaced = pp.build_candidate_embedding_record(
            SupplierCandidateInput(**candidate_payload(description="  Synthetic   printed circuit board for testing. "))
        )
        self.assertEqual(base.source_hash, spaced.source_hash)

    def test_content_change_changes_hash(self):
        base = pp.build_candidate_embedding_record(SupplierCandidateInput(**candidate_payload()))
        changed = pp.build_candidate_embedding_record(
            SupplierCandidateInput(**candidate_payload(description="Different synthetic text."))
        )
        self.assertNotEqual(base.source_hash, changed.source_hash)

    def test_text_excludes_numeric_commercial_fields(self):
        record = pp.build_candidate_embedding_record(SupplierCandidateInput(**candidate_payload()))
        self.assertIn("Category: ELECTRONICS", record.text)
        self.assertNotIn("USD", record.text)
        self.assertNotIn("100", record.text)

    def test_empty_fields_are_omitted_from_text(self):
        record = pp.build_requirement_embedding_record(
            BuyerRequirementInput(**requirement_payload(specification_text=""))
        )
        self.assertNotIn("Specification:", record.text)


if __name__ == "__main__":
    unittest.main()
