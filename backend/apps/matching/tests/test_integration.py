"""
Integration Tests: Django -> FastAPI engine communication (mock engine over HTTP).

A local HTTP stub server stands in for the engine so the real urllib client is
exercised end to end: success parsing, error envelopes, invalid JSON, timeouts,
unreachable engine and correlation-ID propagation (M6-AC5 explicit failure).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
"""

from __future__ import annotations

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from django.test import SimpleTestCase

from apps.matching.exceptions.matching_exceptions import (
    InvalidMatchingPayloadError,
    MatchingEngineConnectionError,
    MatchingEngineResponseError,
    MatchingEngineTimeoutError,
)
from apps.matching.integrations.ai_engine_client import AIEngineClient
from apps.matching.schemas.matching_response import MatchingResponsePayload
from apps.matching.services.request_builder import build_matching_request
from apps.matching.tests.helpers import candidate, engine_success_response, requirement


class _StubEngine(BaseHTTPRequestHandler):
    """Responds with whatever the test configured on the server object."""

    def _respond(self):
        length = int(self.headers.get("Content-Length") or 0)
        self.server.received_body = json.loads(self.rfile.read(length)) if length else None
        self.server.received_correlation_id = self.headers.get("X-Correlation-ID")
        if self.server.delay:
            time.sleep(self.server.delay)
        status, raw = self.server.reply
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    do_GET = _respond
    do_POST = _respond

    def log_message(self, *args):  # keep test output clean
        pass


class AIEngineClientTests(SimpleTestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _StubEngine)
        self.server.delay = 0
        self.server.reply = (200, b"{}")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = AIEngineClient(f"http://127.0.0.1:{self.server.server_port}", timeout_seconds=2)
        self.payload = build_matching_request(requirement(), [candidate(1)], "criteria-v1", "corr-123")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def _reply(self, status: int, body):
        self.server.reply = (status, body if isinstance(body, bytes) else json.dumps(body).encode())

    def test_success_response_is_validated_and_parsed(self):
        self._reply(200, engine_success_response())
        result = self.client.match(self.payload)
        self.assertIsInstance(result, MatchingResponsePayload)
        self.assertEqual(result.ranked[0].rank, 1)
        self.assertEqual(self.server.received_body["criteria_version"], "criteria-v1")

    def test_correlation_id_is_forwarded(self):
        self._reply(200, engine_success_response())
        self.client.match(self.payload)
        self.assertEqual(self.server.received_correlation_id, "corr-123")

    def test_engine_error_envelope_raises_typed_error(self):
        self._reply(503, {"code": "stage_not_available", "message": "pending", "field_errors": {}, "correlation_id": "x"})
        with self.assertRaises(MatchingEngineResponseError) as ctx:
            self.client.match(self.payload)
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(ctx.exception.engine_code, "stage_not_available")

    def test_non_json_error_still_raises_response_error(self):
        self._reply(500, b"<html>gateway error</html>")
        with self.assertRaises(MatchingEngineResponseError) as ctx:
            self.client.match(self.payload)
        self.assertEqual(ctx.exception.engine_code, "matching_engine_error")

    def test_invalid_json_success_body_is_rejected(self):
        self._reply(200, b"not json")
        with self.assertRaises(InvalidMatchingPayloadError):
            self.client.match(self.payload)

    def test_contract_violating_success_body_is_rejected(self):
        self._reply(200, engine_success_response(contract_version="9.9.9"))
        with self.assertRaises(InvalidMatchingPayloadError):
            self.client.match(self.payload)

    def test_timeout_raises_timeout_error(self):
        self.server.delay = 1.0
        self._reply(200, engine_success_response())
        fast_client = AIEngineClient(f"http://127.0.0.1:{self.server.server_port}", timeout_seconds=0.2)
        with self.assertRaises(MatchingEngineTimeoutError):
            fast_client.match(self.payload)

    def test_health(self):
        self._reply(200, {"status": "ok"})
        self.assertEqual(self.client.health()["status"], "ok")


class AIEngineClientConfigurationTests(SimpleTestCase):
    def test_unreachable_engine_fails_explicitly(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            free_port = sock.getsockname()[1]
        client = AIEngineClient(f"http://127.0.0.1:{free_port}", timeout_seconds=1)
        # Linux refuses immediately (connection error); Windows retries the SYN until
        # the timeout. Either way the failure is explicit and typed.
        with self.assertRaises((MatchingEngineConnectionError, MatchingEngineTimeoutError)):
            client.health()

    def test_missing_url_rejected(self):
        with self.assertRaises(MatchingEngineConnectionError):
            AIEngineClient.from_environment({})

    def test_non_http_scheme_rejected(self):
        with self.assertRaises(MatchingEngineConnectionError):
            AIEngineClient("file:///etc/passwd")

    def test_credentials_in_url_rejected(self):
        with self.assertRaises(MatchingEngineConnectionError):
            AIEngineClient("http://user:secret@backend:8001")

    def test_environment_configuration(self):
        client = AIEngineClient.from_environment(
            {"FASTAPI_MATCHING_URL": "http://backend:8001/", "MATCHING_ENGINE_TIMEOUT_SECONDS": "5"}
        )
        self.assertEqual(client.base_url, "http://backend:8001")
        self.assertEqual(client.timeout_seconds, 5.0)

    def test_invalid_timeout_rejected(self):
        with self.assertRaises(MatchingEngineConnectionError):
            AIEngineClient.from_environment({"FASTAPI_MATCHING_URL": "http://backend:8001", "MATCHING_ENGINE_TIMEOUT_SECONDS": "x"})
