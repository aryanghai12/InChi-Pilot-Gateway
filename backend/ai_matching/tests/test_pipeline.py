"""
Unit Tests: Matching Pipeline Orchestration, Contract Schemas and Configuration.

End-to-end engine tests with a deterministic test embedder and a SYNTHETIC
approved scoring configuration: ranking, the hard-gate guarantee (M6-AC1),
unknown-is-not-a-pass (M6-AC2), honest zero results (M6-AC4), explicit failure
with no partial results (M6-AC5) and run metadata (M6-AC6).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
"""

import unittest

from pydantic import ValidationError

from ai_matching.core.config import load_settings
from ai_matching.core.constants import MAX_CANDIDATES_PER_REQUEST, EligibilityOutcome
from ai_matching.core.exceptions import (
    ConfigurationError,
    EmbeddingGenerationError,
    InvalidRequestError,
    StageNotAvailableError,
)
from ai_matching.providers.embedding_provider import NoneEmbeddingProvider
from ai_matching.schemas.matching import MatchRequest
from ai_matching.schemas.result import MatchResponse
from ai_matching.services.matching_pipeline import (
    UNAPPROVED_CONFIG_WARNING,
    prepare_inputs,
    run_pipeline,
)
from ai_matching.tests.factories import (
    TEST_CONFIG_VERSION,
    CriteriaDir,
    KeywordEmbedder,
    candidate_payload,
    match_request_payload,
    scoring_config,
    settings,
)

STRONG_TEXT = {"product_name": "Synthetic electronic component", "description": "Synthetic electronic components."}
WEAK_TEXT = {"product_name": "Synthetic item", "description": "Synthetic steel item.", "specifications": ""}


def _request(candidates, **overrides) -> MatchRequest:
    return MatchRequest(**match_request_payload(candidates=candidates, criteria_version=TEST_CONFIG_VERSION, **overrides))


class PipelineRunTests(unittest.TestCase):
    def setUp(self):
        self._dir = CriteriaDir()
        self.settings = settings(self._dir.__enter__())
        self.embedder = KeywordEmbedder()

    def tearDown(self):
        self._dir.__exit__(None, None, None)

    def _run(self, candidates, **kw):
        return run_pipeline(_request(candidates, **kw), self.settings, self.embedder)

    def test_completed_run_is_valid_and_traceable(self):
        response = self._run([candidate_payload(1, **STRONG_TEXT), candidate_payload(2, **WEAK_TEXT)])
        MatchResponse.model_validate(response.model_dump())
        self.assertEqual(response.status, "completed")
        self.assertEqual(response.criteria_version, TEST_CONFIG_VERSION)
        self.assertEqual(response.configuration_status, "approved")
        self.assertEqual(response.embedding_model_id, "keyword-test-double")
        self.assertEqual(response.requirement_version, 1)
        self.assertEqual(response.metrics.candidates_received, 2)
        self.assertEqual(response.run_warnings, [])

    def test_ranked_by_hybrid_score(self):
        response = self._run([candidate_payload(1, **WEAK_TEXT), candidate_payload(2, **STRONG_TEXT)])
        self.assertEqual([r.rank for r in response.ranked], [1, 2])
        self.assertEqual(response.ranked[0].candidate_id, candidate_payload(2)["candidate_id"])
        self.assertGreater(response.ranked[0].scores.hybrid_score, response.ranked[1].scores.hybrid_score)

    def test_mandatory_failure_never_ranked_despite_perfect_similarity(self):
        """M6-AC1 / SEC-TEST-09: similarity cannot override a hard-gate failure."""
        requirement_text = {"product_name": "Synthetic demand requirement 004",
                            "description": "Synthetic electronic components for test matching only."}
        failing = candidate_payload(1, origin="China", **requirement_text)
        passing = candidate_payload(2, **WEAK_TEXT)
        response = self._run([failing, passing])
        self.assertEqual([r.candidate_id for r in response.excluded], [failing["candidate_id"]])
        self.assertEqual([r.candidate_id for r in response.ranked], [passing["candidate_id"]])
        self.assertIsNone(response.excluded[0].rank)
        self.assertIsNone(response.excluded[0].scores)

    def test_unknown_mandatory_value_is_insufficient_not_ranked(self):
        """M6-AC2."""
        response = self._run([candidate_payload(1, origin="")])
        self.assertEqual(len(response.insufficient_data), 1)
        self.assertEqual(response.insufficient_data[0].eligibility, EligibilityOutcome.INSUFFICIENT_DATA)
        self.assertEqual(response.ranked, [])

    def test_zero_eligible_is_honest_and_skips_embedding(self):
        """M6-AC4: nothing is promoted to fill the list."""
        response = self._run([candidate_payload(1, origin="China")])
        self.assertEqual(response.ranked, [])
        self.assertEqual(self.embedder.calls, 0)
        self.assertTrue(any("No eligible candidates" in w for w in response.run_warnings))

    def test_explanations_and_warnings_present(self):
        response = self._run([candidate_payload(1, moq_value=None)])
        ranked = response.ranked[0]
        self.assertTrue(ranked.explanation[0].startswith("Ranked 1 of 1"))
        self.assertIn("moq_value", {w.field for w in ranked.warnings})
        self.assertEqual({c.criterion_key for c in ranked.criteria}, {"origin_country", "required_evidence"})

    def test_unscored_preference_reported(self):
        contributions = self._run([candidate_payload(1)]).ranked[0].scores.contributions
        outcomes = {c.preference_key: c.outcome for c in contributions}
        self.assertEqual(outcomes["lead_time"], "satisfied")
        self.assertEqual(outcomes["shorter_lead_time"], "not_scored")

    def test_deterministic(self):
        candidates = [candidate_payload(1, **STRONG_TEXT), candidate_payload(2, **WEAK_TEXT)]
        self.assertEqual(self._run(candidates).model_dump(), self._run(candidates).model_dump())


class PipelineFailureTests(unittest.TestCase):
    def test_embedding_failure_fails_whole_run(self):
        """M6-AC5: no silent rules-only fallback, no partial results."""
        with CriteriaDir() as path, self.assertRaises(EmbeddingGenerationError):
            run_pipeline(_request([candidate_payload(1)]), settings(path), KeywordEmbedder(fail=True))

    def test_no_provider_fails_before_any_work(self):
        with CriteriaDir() as path, self.assertRaises(StageNotAvailableError) as ctx:
            run_pipeline(_request([candidate_payload(1)]), settings(path), NoneEmbeddingProvider())
        self.assertEqual(ctx.exception.stage, "semantic")

    def test_unapproved_config_refused(self):
        with CriteriaDir(scoring_config(status="unapproved")) as path, self.assertRaises(StageNotAvailableError):
            run_pipeline(_request([candidate_payload(1)]), settings(path), KeywordEmbedder())

    def test_unapproved_config_allowed_is_labelled(self):
        with CriteriaDir(scoring_config(status="unapproved")) as path:
            response = run_pipeline(_request([candidate_payload(1)]), settings(path, allow_unapproved=True), KeywordEmbedder())
        self.assertEqual(response.configuration_status, "unapproved")
        self.assertIn(UNAPPROVED_CONFIG_WARNING, response.run_warnings)

    def test_repository_placeholder_config_refused(self):
        with self.assertRaises(StageNotAvailableError) as ctx:
            run_pipeline(MatchRequest(**match_request_payload(criteria_version="v0-UNAPPROVED")),
                         load_settings({}), KeywordEmbedder())
        self.assertEqual(ctx.exception.stage, "scoring")

    def test_invalid_criterion_fails_run(self):
        payload = match_request_payload(criteria_version=TEST_CONFIG_VERSION)
        payload["requirement"]["mandatory_criteria"] = [{"criterion_key": "colour", "operator": "equals", "value": {"value": "x"}}]
        with CriteriaDir() as path, self.assertRaises(InvalidRequestError):
            run_pipeline(MatchRequest(**payload), settings(path), KeywordEmbedder())

    def test_prepare_inputs_processes_every_candidate(self):
        prepared = prepare_inputs(MatchRequest(**match_request_payload()))
        self.assertEqual(len(prepared.candidates), 2)


class MatchRequestContractTests(unittest.TestCase):
    def test_wrong_contract_version_rejected(self):
        with self.assertRaises(ValidationError):
            MatchRequest(**match_request_payload(contract_version="9.9.9"))

    def test_unknown_field_rejected(self):
        payload = match_request_payload()
        payload["requirement"]["unexpected_field"] = "x"
        with self.assertRaises(ValidationError):
            MatchRequest(**payload)

    def test_duplicate_candidate_ids_rejected(self):
        with self.assertRaises(ValidationError):
            MatchRequest(**match_request_payload(candidates=[candidate_payload(1), candidate_payload(1)]))

    def test_non_positive_quantity_rejected(self):
        with self.assertRaises(ValidationError):
            MatchRequest(**match_request_payload(candidates=[candidate_payload(1, moq_value="0")]))

    def test_oversized_text_rejected(self):
        with self.assertRaises(ValidationError):
            MatchRequest(**match_request_payload(candidates=[candidate_payload(1, description="x" * 5001)]))

    def test_candidate_pool_is_bounded(self):
        too_many = [candidate_payload(i) for i in range(MAX_CANDIDATES_PER_REQUEST + 1)]
        with self.assertRaises(ValidationError):
            MatchRequest(**match_request_payload(candidates=too_many))


class ConfigurationTests(unittest.TestCase):
    def test_defaults_have_no_model(self):
        s = load_settings({})
        self.assertEqual(s.embedding_provider, "none")
        self.assertIsNone(s.embedding_model_name)
        self.assertTrue(s.embedding_local_files_only)
        self.assertFalse(s.allow_unapproved_config)
        self.assertEqual(s.host, "127.0.0.1")

    def test_model_name_and_options_read_from_environment(self):
        s = load_settings({
            "EMBEDDING_PROVIDER": "sentence_transformers",
            "EMBEDDING_MODEL_NAME": "sentence-transformers/all-MiniLM-L6-v2",
            "EMBEDDING_MODEL_CACHE_DIR": "/models",
            "EMBEDDING_LOCAL_FILES_ONLY": "false",
            "MATCHING_ALLOW_UNAPPROVED_CONFIG": "true",
        })
        self.assertEqual(s.embedding_model_name, "sentence-transformers/all-MiniLM-L6-v2")
        self.assertEqual(s.embedding_model_cache_dir, "/models")
        self.assertFalse(s.embedding_local_files_only)
        self.assertTrue(s.allow_unapproved_config)

    def test_provider_without_model_rejected(self):
        with self.assertRaises(ConfigurationError):
            load_settings({"EMBEDDING_PROVIDER": "sentence_transformers"})

    def test_placeholder_model_name_means_not_configured(self):
        self.assertIsNone(load_settings({"EMBEDDING_MODEL_NAME": "TBD-D11-PENDING-APPROVAL"}).embedding_model_name)

    def test_unsupported_provider_rejected(self):
        for provider in ("hosted-api", "fastembed"):
            with self.subTest(provider=provider), self.assertRaises(ConfigurationError):
                load_settings({"EMBEDDING_PROVIDER": provider})

    def test_invalid_boolean_rejected(self):
        with self.assertRaises(ConfigurationError):
            load_settings({"MATCHING_ALLOW_UNAPPROVED_CONFIG": "maybe"})

    def test_invalid_port_rejected(self):
        with self.assertRaises(ConfigurationError):
            load_settings({"MATCHING_ENGINE_PORT": "not-a-port"})


if __name__ == "__main__":
    unittest.main()
