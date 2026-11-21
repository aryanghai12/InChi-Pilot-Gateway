"""
Contract Tests: Django payloads vs the FastAPI engine's Pydantic schemas.

Proves both sides of the proposed contract (docs/ai/MATCHING_CONTRACT.md) agree:
a request built by Django validates against the engine's MatchRequest, the
engine's real /match endpoint answers it with the error envelope Django parses,
and response validation rules on both sides match.

Skipped automatically when the engine dependencies (FastAPI/Pydantic) are not
installed in the Django test environment.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A + Component B
"""

import unittest

from django.test import SimpleTestCase

from apps.matching.exceptions.matching_exceptions import InvalidMatchingPayloadError
from apps.matching.schemas import matching_request
from apps.matching.schemas.matching_response import (
    EngineErrorPayload,
    MatchingResponsePayload,
)
from apps.matching.services import request_builder
from apps.matching.services.request_builder import build_matching_request
from apps.matching.tests.helpers import candidate, engine_success_response, requirement

try:
    from fastapi.testclient import TestClient

    from ai_matching.core import constants as engine_constants
    from ai_matching.main import app as engine_app
    from ai_matching.schemas.matching import MatchRequest
    from ai_matching.schemas.result import MatchResponse

    ENGINE_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on the environment
    ENGINE_AVAILABLE = False


@unittest.skipUnless(ENGINE_AVAILABLE, "FastAPI engine dependencies are not installed.")
class DjangoEngineContractTests(SimpleTestCase):
    def _request_body(self):
        return build_matching_request(requirement(), [candidate(1), candidate(2)], "criteria-v1", "corr-1").to_dict()

    def test_shared_constants_agree(self):
        self.assertEqual(matching_request.CONTRACT_VERSION, engine_constants.CONTRACT_VERSION)
        self.assertEqual(request_builder.MAX_CANDIDATES_PER_REQUEST, engine_constants.MAX_CANDIDATES_PER_REQUEST)
        self.assertEqual(request_builder.MAX_LONG_TEXT_LENGTH, engine_constants.MAX_LONG_TEXT_LENGTH)
        self.assertEqual(request_builder.MANUAL_REVIEW_OPERATOR, engine_constants.MANUAL_REVIEW_OPERATOR)

    def test_full_round_trip_through_real_engine_pipeline(self):
        """Django request -> real engine pipeline (test embedder, synthetic approved config) -> Django parse."""
        from ai_matching.api.dependencies import (
            embedding_provider_dependency,
            settings_dependency,
        )
        from ai_matching.tests.factories import (
            TEST_CONFIG_VERSION,
            CriteriaDir,
            KeywordEmbedder,
            settings,
        )

        body = build_matching_request(requirement(), [candidate(1), candidate(2, origin="China")],
                                      TEST_CONFIG_VERSION, "corr-rt").to_dict()
        with CriteriaDir() as path:
            engine_app.dependency_overrides[settings_dependency] = lambda: settings(path)
            engine_app.dependency_overrides[embedding_provider_dependency] = KeywordEmbedder
            try:
                response = TestClient(engine_app).post("/match", json=body)
            finally:
                engine_app.dependency_overrides.clear()
        self.assertEqual(response.status_code, 200, response.text)
        parsed = MatchingResponsePayload.from_dict(response.json())
        self.assertEqual([r.candidate_id for r in parsed.ranked], [candidate(1).candidate_id])
        self.assertEqual([r.candidate_id for r in parsed.excluded], [candidate(2).candidate_id])
        self.assertEqual(parsed.configuration_status, "approved")

    def test_django_request_validates_against_engine_schema(self):
        validated = MatchRequest.model_validate(self._request_body())
        self.assertEqual(len(validated.candidates), 2)
        self.assertEqual(validated.requirement.mandatory_criteria[0].operator, "equals")

    def test_engine_answers_django_request_with_parseable_failure_envelope(self):
        response = TestClient(engine_app).post(
            "/match", json=self._request_body(), headers={"X-Correlation-ID": "corr-1"}
        )
        self.assertEqual(response.status_code, 503)
        error = EngineErrorPayload.from_dict(response.json())
        self.assertEqual(error.code, "stage_not_available")
        self.assertEqual(error.correlation_id, "corr-1")

    def test_synthetic_success_body_is_valid_on_both_sides(self):
        body = engine_success_response()
        MatchResponse.model_validate(body)
        MatchingResponsePayload.from_dict(body)


class ResponseValidationTests(SimpleTestCase):
    def test_ranked_candidate_without_scores_rejected(self):
        body = engine_success_response()
        body["ranked"][0]["scores"] = None
        with self.assertRaises(InvalidMatchingPayloadError):
            MatchingResponsePayload.from_dict(body)

    def test_excluded_candidate_with_rank_rejected(self):
        body = engine_success_response()
        excluded = dict(body["ranked"][0], eligibility="excluded", scores=None)
        body["ranked"] = []
        body["excluded"] = [excluded]
        with self.assertRaises(InvalidMatchingPayloadError):
            MatchingResponsePayload.from_dict(body)

    def test_ineligible_candidate_in_ranked_list_rejected(self):
        body = engine_success_response()
        body["ranked"][0]["eligibility"] = "insufficient_data"
        with self.assertRaises(InvalidMatchingPayloadError):
            MatchingResponsePayload.from_dict(body)

    def test_score_outside_unit_interval_rejected(self):
        body = engine_success_response()
        body["ranked"][0]["scores"]["hybrid_score"] = 1.5
        with self.assertRaises(InvalidMatchingPayloadError):
            MatchingResponsePayload.from_dict(body)

    def test_failed_status_is_never_parsed_as_results(self):
        with self.assertRaises(InvalidMatchingPayloadError):
            MatchingResponsePayload.from_dict(engine_success_response(status="failed"))

    def test_zero_eligible_candidates_is_valid(self):
        """M6-AC4: an honest empty result is a valid response."""
        body = engine_success_response(ranked=[])
        self.assertEqual(MatchingResponsePayload.from_dict(body).ranked, ())
