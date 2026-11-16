"""
Integration Tests: Matching request payload building (Component A).

Covers pre-flight validation, versioning metadata (M6-AC6), JSON serialisation
(Decimals as strings, unknown as null) and mandatory/preference separation (M5-AC1).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
"""

import json

from django.test import SimpleTestCase

from apps.matching.exceptions.matching_exceptions import InvalidMatchingPayloadError
from apps.matching.schemas.matching_request import CONTRACT_VERSION
from apps.matching.services.request_builder import (
    MAX_CANDIDATES_PER_REQUEST,
    build_matching_request,
)
from apps.matching.tests.helpers import candidate, requirement


class RequestBuilderTests(SimpleTestCase):
    def test_builds_versioned_request(self):
        payload = build_matching_request(requirement(), [candidate(1)], "criteria-v1", "corr-1")
        body = payload.to_dict()
        self.assertEqual(body["contract_version"], CONTRACT_VERSION)
        self.assertEqual(body["criteria_version"], "criteria-v1")
        self.assertEqual(body["correlation_id"], "corr-1")
        self.assertEqual(body["requirement"]["requirement_version"], 1)

    def test_body_is_json_serialisable_with_decimals_as_strings(self):
        body = build_matching_request(requirement(), [candidate(1)], "criteria-v1").to_dict()
        encoded = json.loads(json.dumps(body))
        self.assertEqual(encoded["candidates"][0]["moq_value"], "100.00")

    def test_unknown_values_stay_null(self):
        body = build_matching_request(requirement(), [candidate(1, moq_value=None)], "criteria-v1").to_dict()
        self.assertIsNone(body["candidates"][0]["moq_value"])

    def test_mandatory_and_preference_criteria_are_separate(self):
        body = build_matching_request(requirement(), [candidate(1)], "criteria-v1").to_dict()
        self.assertEqual(body["requirement"]["mandatory_criteria"][0]["criterion_key"], "origin_country")
        self.assertEqual(body["requirement"]["preference_criteria"][0]["preference_key"], "shorter_lead_time")

    def test_missing_criteria_version_rejected(self):
        with self.assertRaises(InvalidMatchingPayloadError):
            build_matching_request(requirement(), [candidate(1)], "  ")

    def test_invalid_requirement_version_rejected(self):
        with self.assertRaises(InvalidMatchingPayloadError):
            build_matching_request(requirement(requirement_version=0), [candidate(1)], "criteria-v1")

    def test_duplicate_candidates_rejected(self):
        with self.assertRaises(InvalidMatchingPayloadError):
            build_matching_request(requirement(), [candidate(1), candidate(1)], "criteria-v1")

    def test_candidate_pool_bounded(self):
        too_many = [candidate(i) for i in range(MAX_CANDIDATES_PER_REQUEST + 1)]
        with self.assertRaises(InvalidMatchingPayloadError):
            build_matching_request(requirement(), too_many, "criteria-v1")

    def test_empty_candidate_pool_allowed(self):
        """M6-AC4: zero candidates is a legitimate, honest outcome, not a builder error."""
        self.assertEqual(build_matching_request(requirement(), [], "criteria-v1").candidates, ())
