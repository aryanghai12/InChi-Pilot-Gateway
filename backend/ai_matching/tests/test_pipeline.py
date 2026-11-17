"""
Unit Tests: Matching Pipeline Orchestration, Contract Schemas and Configuration.

Tests Stage 1 orchestration, explicit failure at the first unapproved stage
(no partial results, M6-AC5), request contract validation, provider selection
and configuration parsing (no model default, D-11).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
"""

import unittest

from pydantic import ValidationError

from ai_matching.core.config import load_settings
from ai_matching.core.constants import MAX_CANDIDATES_PER_REQUEST
from ai_matching.core.exceptions import ConfigurationError, StageNotAvailableError
from ai_matching.providers.embedding_provider import (
    NoneEmbeddingProvider,
    get_embedding_provider,
)
from ai_matching.schemas.matching import MatchRequest
from ai_matching.services.matching_pipeline import prepare_inputs, run_pipeline
from ai_matching.tests.factories import candidate_payload, match_request_payload


class PipelineTests(unittest.TestCase):
    def test_prepare_inputs_processes_every_candidate(self):
        prepared = prepare_inputs(MatchRequest(**match_request_payload()))
        self.assertEqual(len(prepared.candidates), 2)
        self.assertEqual(prepared.criteria_version, "criteria-v1")
        self.assertEqual(prepared.requirement.requirement_version, 1)

    def test_run_fails_explicitly_at_eligibility(self):
        with self.assertRaises(StageNotAvailableError) as ctx:
            run_pipeline(MatchRequest(**match_request_payload()))
        self.assertEqual(ctx.exception.stage, "eligibility")
        self.assertIn("D-04", ctx.exception.reason)

    def test_empty_candidate_pool_still_reaches_eligibility_gate(self):
        with self.assertRaises(StageNotAvailableError):
            run_pipeline(MatchRequest(**match_request_payload(candidates=[])))


class MatchRequestContractTests(unittest.TestCase):
    def test_valid_request(self):
        request = MatchRequest(**match_request_payload())
        self.assertEqual(request.requirement.mandatory_criteria[0].criterion_key, "origin_country")

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

    def test_requirement_version_must_be_positive(self):
        payload = match_request_payload()
        payload["requirement"]["requirement_version"] = 0
        with self.assertRaises(ValidationError):
            MatchRequest(**payload)


class ConfigurationTests(unittest.TestCase):
    def test_defaults_have_no_model(self):
        settings = load_settings({})
        self.assertEqual(settings.embedding_provider, "none")
        self.assertIsNone(settings.embedding_model_name)
        self.assertFalse(settings.embedding_model_configured)
        self.assertEqual(settings.host, "127.0.0.1")

    def test_env_example_placeholder_means_not_configured(self):
        settings = load_settings({"EMBEDDING_MODEL_NAME": "TBD-D11-PENDING-APPROVAL"})
        self.assertIsNone(settings.embedding_model_name)

    def test_unknown_provider_rejected(self):
        with self.assertRaises(ConfigurationError):
            load_settings({"EMBEDDING_PROVIDER": "hosted-api"})

    def test_invalid_port_rejected(self):
        with self.assertRaises(ConfigurationError):
            load_settings({"MATCHING_ENGINE_PORT": "not-a-port"})

    def test_none_provider_selected_by_default(self):
        self.assertIsInstance(get_embedding_provider(load_settings({})), NoneEmbeddingProvider)

    def test_real_providers_refused_until_d11(self):
        for provider in ("sentence_transformers", "fastembed"):
            with self.subTest(provider=provider), self.assertRaises(ConfigurationError):
                get_embedding_provider(load_settings({"EMBEDDING_PROVIDER": provider}))


if __name__ == "__main__":
    unittest.main()
