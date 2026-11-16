"""
API Tests: FastAPI routes and error envelope.

Tests GET /health, POST /match validation (422 envelope, no echoed values) and
explicit failure (503 stage_not_available, no results), using FastAPI's
TestClient (no network).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
"""

import unittest

from fastapi.testclient import TestClient

from ai_matching.core.constants import CONTRACT_VERSION
from ai_matching.main import app
from ai_matching.tests.factories import candidate_payload, match_request_payload

ENVELOPE_KEYS = {"code", "message", "field_errors", "correlation_id"}


class HealthEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_reports_contract_and_no_model(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["contract_version"], CONTRACT_VERSION)
        self.assertIn("embedding_model_configured", body)

    def test_interactive_docs_disabled(self):
        self.assertEqual(self.client.get("/docs").status_code, 404)


class MatchEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_valid_request_fails_explicitly_with_stage_not_available(self):
        response = self.client.post(
            "/match", json=match_request_payload(), headers={"X-Correlation-ID": "abc-123"}
        )
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(set(body), ENVELOPE_KEYS)
        self.assertEqual(body["code"], "stage_not_available")
        self.assertEqual(body["correlation_id"], "abc-123")
        self.assertNotIn("ranked", body)

    def test_invalid_request_returns_validation_envelope_without_values(self):
        secret_like = "SYNTHETIC-SENSITIVE-VALUE"
        payload = match_request_payload(candidates=[candidate_payload(1, moq_value="-5", supplier_name=secret_like)])
        payload["candidates"][0]["unexpected"] = secret_like
        response = self.client.post("/match", json=payload)
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(set(body), ENVELOPE_KEYS)
        self.assertEqual(body["code"], "validation_error")
        self.assertIn("candidates.0.moq_value", body["field_errors"])
        self.assertNotIn(secret_like, response.text)

    def test_unsafe_correlation_id_is_replaced(self):
        response = self.client.post(
            "/match", json=match_request_payload(), headers={"X-Correlation-ID": "bad id;<script>"}
        )
        self.assertNotEqual(response.json()["correlation_id"], "bad id;<script>")


if __name__ == "__main__":
    unittest.main()
