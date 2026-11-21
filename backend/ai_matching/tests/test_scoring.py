"""
Unit Tests: Scoring configuration, hybrid scoring, ranking and explainability.

Weights used here are SYNTHETIC test values (tests/factories.py), not proposals.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
"""

import unittest
from types import SimpleNamespace

from ai_matching.core.constants import (
    CriterionOutcome,
    EligibilityOutcome,
    PreferenceOutcome,
)
from ai_matching.core.exceptions import (
    ConfigurationError,
    InvalidRequestError,
    StageNotAvailableError,
)
from ai_matching.core.scoring_config import (
    ScoringConfiguration,
    load_scoring_config,
    require_usable,
)
from ai_matching.schemas.supplier import SupplierCandidateInput
from ai_matching.services.eligibility import CriterionEvaluation
from ai_matching.services.explainability import (
    DECISION_SUPPORT_NOTE,
    explain_ineligible,
    explain_ranked,
)
from ai_matching.services.hybrid_scorer import (
    map_semantic_score,
    parse_preferences,
    score_candidate,
)
from ai_matching.services.preprocessing import prepare_candidate
from ai_matching.services.ranking import rank_candidates
from ai_matching.tests.factories import (
    CriteriaDir,
    candidate_payload,
    scoring_config,
    settings,
)


def _config(**overrides) -> ScoringConfiguration:
    return ScoringConfiguration.model_validate(scoring_config(**overrides))


def _pref(key, value, weight_key="lead_time"):
    return SimpleNamespace(preference_key=key, value=value, weight_key=weight_key)


def _values(**overrides):
    return prepare_candidate(SupplierCandidateInput(**candidate_payload(**overrides))).values


LEAD_TIME_PREF = _pref("lead_time", {"operator": "lte", "value": 45, "unit": "DAYS"})


class ScoringConfigTests(unittest.TestCase):
    def test_committed_placeholder_is_refused(self):
        """The repository's v0-UNAPPROVED.json must never be usable for scoring."""
        from ai_matching.core.config import load_settings

        real = load_settings({})
        config = load_scoring_config("v0-UNAPPROVED", real)
        with self.assertRaises(StageNotAvailableError):
            require_usable(config, real)

    def test_placeholder_refused_even_when_unapproved_allowed(self):
        from dataclasses import replace

        from ai_matching.core.config import load_settings

        real = replace(load_settings({}), allow_unapproved_config=True)
        with self.assertRaises(StageNotAvailableError):  # no weights
            require_usable(load_scoring_config("v0-UNAPPROVED", real), real)

    def test_approved_config_loads(self):
        with CriteriaDir() as path:
            s = settings(path)
            config = require_usable(load_scoring_config("test-approved-v1", s), s)
        self.assertEqual(config.hybrid_weights.rule, 0.5)

    def test_unapproved_refused_unless_allowed(self):
        cfg = scoring_config(version="demo-v1", status="unapproved")
        with CriteriaDir(cfg) as path:
            with self.assertRaises(StageNotAvailableError):
                require_usable(load_scoring_config("demo-v1", settings(path)), settings(path))
            allowed = settings(path, allow_unapproved=True)
            self.assertEqual(require_usable(load_scoring_config("demo-v1", allowed), allowed).version, "demo-v1")

    def test_missing_version_is_stage_not_available(self):
        with CriteriaDir() as path, self.assertRaises(StageNotAvailableError):
            load_scoring_config("does-not-exist", settings(path))

    def test_path_traversal_rejected(self):
        with CriteriaDir() as path, self.assertRaises(ConfigurationError):
            load_scoring_config("../secrets", settings(path))

    def test_weights_must_sum_to_one(self):
        cfg = scoring_config(hybrid_weights={"rule": 0.7, "semantic": 0.7})
        with CriteriaDir(cfg) as path, self.assertRaises(ConfigurationError):
            require_usable(load_scoring_config("test-approved-v1", settings(path)), settings(path))

    def test_missing_semantic_mapping_refused(self):
        cfg = scoring_config(semantic_score_mapping=None)
        with CriteriaDir(cfg) as path, self.assertRaises(StageNotAvailableError):
            require_usable(load_scoring_config("test-approved-v1", settings(path)), settings(path))

    def test_version_mismatch_inside_file_rejected(self):
        cfg = scoring_config()
        with CriteriaDir(cfg) as path:
            (path / "other.json").write_text((path / "test-approved-v1.json").read_text(), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_scoring_config("other", settings(path))


class HybridScoringTests(unittest.TestCase):
    def test_satisfied_preference_full_rule_score(self):
        score = score_candidate(parse_preferences([LEAD_TIME_PREF], _config()), _values(), 0.6, _config())
        self.assertEqual(score.rule_score, 1.0)
        self.assertAlmostEqual(score.hybrid_score, 0.5 * 1.0 + 0.5 * 0.6)

    def test_unsatisfied_preference(self):
        score = score_candidate(parse_preferences([LEAD_TIME_PREF], _config()), _values(lead_time_value=60), 0.6, _config())
        self.assertEqual(score.rule_score, 0.0)
        self.assertEqual(score.preferences[0].outcome, PreferenceOutcome.NOT_SATISFIED)

    def test_unknown_preference_data_earns_no_credit(self):
        score = score_candidate(parse_preferences([LEAD_TIME_PREF], _config()), _values(lead_time_value=None), 0.6, _config())
        self.assertEqual(score.rule_score, 0.0)
        self.assertEqual(score.preferences[0].outcome, PreferenceOutcome.INSUFFICIENT_DATA)

    def test_weighted_average_across_preferences(self):
        config = _config(preference_weights={"lead_time": 3.0, "moq": 1.0})
        prefs = parse_preferences(
            [LEAD_TIME_PREF, _pref("moq", {"operator": "lte", "value": 1, "unit": "PIECES"}, "moq")], config
        )
        score = score_candidate(prefs, _values(), 0.0, config)
        self.assertAlmostEqual(score.rule_score, 0.75)
        self.assertAlmostEqual(sum(p.contribution for p in score.preferences), 0.75)

    def test_unstructured_or_unweighted_preferences_not_scored(self):
        prefs = parse_preferences(
            [_pref("shorter_lead_time", {"preferred_max_days": 45}),
             _pref("lead_time", {"operator": "lte", "value": 45, "unit": "DAYS"}, "no_such_weight")],
            _config(),
        )
        score = score_candidate(prefs, _values(), 0.8, _config())
        self.assertIsNone(score.rule_score)
        self.assertEqual({p.outcome for p in score.preferences}, {PreferenceOutcome.NOT_SCORED})
        self.assertAlmostEqual(score.hybrid_score, 0.8)

    def test_invalid_structured_preference_fails_run(self):
        with self.assertRaises(InvalidRequestError):
            parse_preferences([_pref("lead_time", {"operator": "between", "value": 1, "unit": "DAYS"})], _config())

    def test_semantic_mappings(self):
        self.assertEqual(map_semantic_score(-0.4, "clamp_negative_to_zero"), 0.0)
        self.assertAlmostEqual(map_semantic_score(0.4, "clamp_negative_to_zero"), 0.4)
        self.assertAlmostEqual(map_semantic_score(-1.0, "linear_rescale"), 0.0)
        self.assertAlmostEqual(map_semantic_score(0.0, "linear_rescale"), 0.5)

    def test_scores_stay_in_unit_interval(self):
        score = score_candidate((), _values(), 1.0000001, _config())
        self.assertLessEqual(score.hybrid_score, 1.0)
        self.assertLessEqual(score.semantic_cosine, 1.0)


class RankingTests(unittest.TestCase):
    @staticmethod
    def _rank(items):
        return [r.item["id"] for r in rank_candidates(
            items, hybrid_score=lambda i: i["h"], rule_score=lambda i: i["r"],
            supplier_id=lambda i: i["s"], candidate_id=lambda i: i["id"],
        )]

    def test_orders_by_hybrid_descending(self):
        self.assertEqual(self._rank([{"id": "a", "h": 0.2, "r": 0.1, "s": "1"}, {"id": "b", "h": 0.9, "r": 0.1, "s": "1"}]), ["b", "a"])

    def test_tie_breaks_rule_then_supplier_then_candidate(self):
        items = [
            {"id": "c3", "h": 0.5, "r": 0.2, "s": "s2"},
            {"id": "c2", "h": 0.5, "r": 0.9, "s": "s9"},
            {"id": "c1", "h": 0.5, "r": 0.2, "s": "s1"},
            {"id": "c0", "h": 0.5, "r": 0.2, "s": "s1"},
        ]
        self.assertEqual(self._rank(items), ["c2", "c0", "c1", "c3"])

    def test_ranks_are_consecutive_from_one(self):
        ranked = rank_candidates([1, 2, 3], hybrid_score=float, rule_score=lambda _: None,
                                 supplier_id=str, candidate_id=str)
        self.assertEqual([r.rank for r in ranked], [1, 2, 3])

    def test_empty(self):
        self.assertEqual(self._rank([]), [])


class ExplainabilityTests(unittest.TestCase):
    def test_excluded_explanation_names_failed_criterion(self):
        evaluation = CriterionEvaluation("moq", "lte", CriterionOutcome.FAIL, "moq lte 50 PIECES: candidate value 100.")
        lines = explain_ineligible(EligibilityOutcome.EXCLUDED, [evaluation], ())
        self.assertIn("cannot override", lines[0])
        self.assertTrue(any("Failed — moq" in line for line in lines))
        self.assertEqual(lines[-1], DECISION_SUPPORT_NOTE)

    def test_ranked_explanation_reports_actual_numbers(self):
        config = _config()
        score = score_candidate(parse_preferences([LEAD_TIME_PREF], config), _values(), 0.6, config)
        lines = explain_ranked(1, 2, [], score, (0.5, 0.5), ())
        text = " ".join(lines)
        self.assertIn("Ranked 1 of 2", text)
        self.assertIn(f"{score.hybrid_score:.2f}", text)
        self.assertIn("1 of 1 weighted preference(s) satisfied", text)
        self.assertIn("not a verified capability", text)
        self.assertTrue(all(len(line) <= 255 for line in lines))

    def test_rule_not_applicable_is_explained(self):
        score = score_candidate((), _values(), 0.3, _config())
        self.assertTrue(any("Rule score not applicable" in line for line in explain_ranked(1, 1, [], score, (0.5, 0.5), ())))

    def test_quality_issues_flagged_as_uncertain(self):
        prepared = prepare_candidate(SupplierCandidateInput(**candidate_payload(moq_value=None)))
        score = score_candidate((), prepared.values, 0.3, _config())
        lines = explain_ranked(1, 1, [], score, (0.5, 0.5), prepared.quality_issues)
        self.assertTrue(any("Incomplete or uncertain information: moq_value" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
