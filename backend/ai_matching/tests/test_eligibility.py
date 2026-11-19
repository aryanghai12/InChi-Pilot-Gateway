"""
Unit Tests: Mandatory Eligibility Evaluation (Stage 2).

Tests mandatory criteria hard gates: all criteria pass, single criterion failure,
missing criteria handling, and unverified data handling (M6-AC1, M6-AC2).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
"""

import unittest
from decimal import Decimal

from ai_matching.core.constants import CriterionOutcome, EligibilityOutcome
from ai_matching.core.exceptions import InvalidRequestError
from ai_matching.schemas.supplier import SupplierCandidateInput
from ai_matching.services.eligibility import (
    candidate_outcome,
    evaluate_candidate,
    evaluate_criterion,
    parse_criterion,
    parse_mandatory_criteria,
)
from ai_matching.services.preprocessing import prepare_candidate
from ai_matching.tests.factories import candidate_payload


def _values(**overrides) -> dict:
    return prepare_candidate(SupplierCandidateInput(**candidate_payload(**overrides))).values


def _outcome(key, op, value, **candidate):
    return evaluate_criterion(parse_criterion(key, op, value, "t"), _values(**candidate)).outcome


class CodeCriterionTests(unittest.TestCase):
    def test_equals_pass_uses_normalised_values(self):
        # Candidate origin "India" normalises to IN; criterion value given as display name.
        self.assertEqual(_outcome("origin_country", "equals", {"value": "india"}), CriterionOutcome.PASS)

    def test_equals_fail(self):
        self.assertEqual(_outcome("origin_country", "equals", {"value": "CN"}), CriterionOutcome.FAIL)

    def test_in_operator(self):
        self.assertEqual(
            _outcome("product_category", "in", {"value": ["Textiles", "Electronic Goods"]}), CriterionOutcome.PASS
        )

    def test_not_equals(self):
        self.assertEqual(
            _outcome("supplier_record_status", "not_equals", {"value": "archived"}), CriterionOutcome.PASS
        )

    def test_unknown_candidate_value_is_insufficient_not_pass(self):
        """M6-AC2."""
        self.assertEqual(
            _outcome("origin_country", "equals", {"value": "IN"}, origin=""), CriterionOutcome.INSUFFICIENT_DATA
        )

    def test_unrecognised_candidate_value_is_insufficient(self):
        self.assertEqual(
            _outcome("origin_country", "equals", {"value": "IN"}, origin="Atlantis"),
            CriterionOutcome.INSUFFICIENT_DATA,
        )


class MeasuredCriterionTests(unittest.TestCase):
    def test_lte_pass_and_fail(self):
        self.assertEqual(_outcome("moq", "lte", {"value": 200, "unit": "pieces"}), CriterionOutcome.PASS)
        self.assertEqual(_outcome("moq", "lte", {"value": 50, "unit": "PIECES"}), CriterionOutcome.FAIL)

    def test_gte(self):
        self.assertEqual(
            _outcome("capacity", "gte", {"value": "4000", "unit": "PIECES", "period": "month"}),
            CriterionOutcome.PASS,
        )

    def test_unit_mismatch_is_insufficient_no_conversion(self):
        self.assertEqual(_outcome("moq", "lte", {"value": 1, "unit": "KG"}), CriterionOutcome.INSUFFICIENT_DATA)

    def test_period_mismatch_is_insufficient(self):
        self.assertEqual(
            _outcome("capacity", "gte", {"value": 1, "unit": "PIECES", "period": "YEAR"}),
            CriterionOutcome.INSUFFICIENT_DATA,
        )

    def test_missing_candidate_value_is_insufficient(self):
        self.assertEqual(
            _outcome("lead_time", "lte", {"value": 45, "unit": "DAYS"}, lead_time_value=None),
            CriterionOutcome.INSUFFICIENT_DATA,
        )

    def test_currency_mismatch_is_insufficient(self):
        self.assertEqual(
            _outcome("price_max", "lte", {"value": 30, "currency": "CNY"}), CriterionOutcome.INSUFFICIENT_DATA
        )

    def test_price_comparison(self):
        self.assertEqual(_outcome("price_max", "lte", {"value": 25, "currency": "usd"}), CriterionOutcome.PASS)


class EvidenceAndManualTests(unittest.TestCase):
    def test_recorded_evidence_passes(self):
        criteria = parse_mandatory_criteria([], ["QUALITY_CERTIFICATE"])
        outcome, evaluations = evaluate_candidate(criteria, _values())
        self.assertEqual(outcome, EligibilityOutcome.ELIGIBLE)
        self.assertEqual(evaluations[0].criterion_key, "required_evidence")

    def test_unrecorded_evidence_is_insufficient_not_fail(self):
        criteria = parse_mandatory_criteria([], ["ORIGIN_CERTIFICATE"])
        outcome, _ = evaluate_candidate(criteria, _values())
        self.assertEqual(outcome, EligibilityOutcome.INSUFFICIENT_DATA)

    def test_free_text_criterion_never_passes(self):
        criterion = parse_criterion("manual_review_1", "manual_review", {"text": "ISO 9001 certified"}, "t")
        evaluation = evaluate_criterion(criterion, _values())
        self.assertEqual(evaluation.outcome, CriterionOutcome.INSUFFICIENT_DATA)
        self.assertIn("ISO 9001", evaluation.detail)


class CandidateOutcomeTests(unittest.TestCase):
    def _parsed(self, *specs):
        class _C:
            def __init__(self, key, op, value):
                self.criterion_key, self.operator, self.value = key, op, value
        return parse_mandatory_criteria([_C(*s) for s in specs], [])

    def test_any_fail_excludes_even_if_others_pass(self):
        criteria = self._parsed(("origin_country", "equals", {"value": "IN"}), ("moq", "lte", {"value": 1, "unit": "PIECES"}))
        self.assertEqual(evaluate_candidate(criteria, _values())[0], EligibilityOutcome.EXCLUDED)

    def test_fail_takes_precedence_over_insufficient(self):
        outcomes = [CriterionOutcome.INSUFFICIENT_DATA, CriterionOutcome.FAIL]
        evaluations = [type("E", (), {"outcome": o})() for o in outcomes]
        self.assertEqual(candidate_outcome(evaluations), EligibilityOutcome.EXCLUDED)

    def test_no_criteria_means_eligible(self):
        self.assertEqual(evaluate_candidate((), _values())[0], EligibilityOutcome.ELIGIBLE)

    def test_all_pass_is_eligible(self):
        criteria = self._parsed(("origin_country", "equals", {"value": "IN"}), ("moq", "lte", {"value": 500, "unit": "PIECES"}))
        self.assertEqual(evaluate_candidate(criteria, _values())[0], EligibilityOutcome.ELIGIBLE)


class CriterionValidationTests(unittest.TestCase):
    def test_unknown_key_rejected(self):
        with self.assertRaises(InvalidRequestError) as ctx:
            parse_criterion("favourite_colour", "equals", {"value": "blue"}, "requirement.mandatory_criteria.0")
        self.assertIn("requirement.mandatory_criteria.0", ctx.exception.field_errors)

    def test_unsupported_operator_rejected(self):
        with self.assertRaises(InvalidRequestError):
            parse_criterion("origin_country", "lte", {"value": "IN"}, "t")

    def test_measured_criterion_requires_unit(self):
        with self.assertRaises(InvalidRequestError):
            parse_criterion("moq", "lte", {"value": 10}, "t")

    def test_non_numeric_value_rejected(self):
        with self.assertRaises(InvalidRequestError):
            parse_criterion("moq", "lte", {"value": "ten", "unit": "KG"}, "t")

    def test_boolean_value_rejected(self):
        with self.assertRaises(InvalidRequestError):
            parse_criterion("moq", "lte", {"value": True, "unit": "KG"}, "t")

    def test_unrecognised_code_value_rejected(self):
        with self.assertRaises(InvalidRequestError):
            parse_criterion("origin_country", "equals", {"value": "Atlantis"}, "t")

    def test_missing_value_rejected(self):
        with self.assertRaises(InvalidRequestError):
            parse_criterion("origin_country", "equals", {}, "t")

    def test_decimal_target(self):
        parsed = parse_criterion("moq", "lte", {"value": "12.5", "unit": "kg"}, "t")
        self.assertEqual(parsed.target, Decimal("12.5"))
        self.assertEqual(parsed.unit, "KG")


if __name__ == "__main__":
    unittest.main()
