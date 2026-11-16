"""
HTTP Client for FastAPI AI Matching Engine Communication.

Responsible for sending matching requests from Django to the standalone FastAPI
AI Matching Engine and receiving validated results.

* Standard library only (urllib), so the Django process needs no new dependency.
* Every failure becomes a typed exception from apps.matching.exceptions; nothing
  is retried silently and no partial result is ever returned (M6-AC5).
* Request and response bodies are never logged.

Configuration (environment variables):
    FASTAPI_MATCHING_URL             engine base URL, e.g. http://backend:8001 (.env.example)
    MATCHING_ENGINE_TIMEOUT_SECONDS  per-request timeout in seconds (default 30)

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Week 2 implementation.

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: engine runtime/deployment arrangement (ARCHITECTURE.md §6.3).
# OPEN: service-to-service authentication (THREAT_MODEL Boundary 3, Ajendra review).
# Settings are read from the environment here; Abhishek (C5) may move them into
# config/settings.py, which he owns.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from apps.matching.exceptions.matching_exceptions import (
    InvalidMatchingPayloadError,
    MatchingEngineConnectionError,
    MatchingEngineResponseError,
    MatchingEngineTimeoutError,
)
from apps.matching.schemas.matching_request import MatchingRequestPayload
from apps.matching.schemas.matching_response import (
    EngineErrorPayload,
    MatchingResponsePayload,
)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # bound memory use on a misbehaving engine


class AIEngineClient:
    """Thin, synchronous client for the engine's /health and /match endpoints."""

    def __init__(self, base_url: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS):
        parsed = urllib.parse.urlparse(base_url or "")
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise MatchingEngineConnectionError("The matching engine URL is missing or invalid.")
        if parsed.username or parsed.password:
            raise MatchingEngineConnectionError("The matching engine URL must not contain credentials.")
        if timeout_seconds <= 0:
            raise MatchingEngineConnectionError("The matching engine timeout must be positive.")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_environment(cls, environ: dict[str, str] | None = None) -> AIEngineClient:
        env = os.environ if environ is None else environ
        raw_timeout = env.get("MATCHING_ENGINE_TIMEOUT_SECONDS", "").strip()
        try:
            timeout = float(raw_timeout) if raw_timeout else DEFAULT_TIMEOUT_SECONDS
        except ValueError as exc:
            raise MatchingEngineConnectionError("MATCHING_ENGINE_TIMEOUT_SECONDS must be a number.") from exc
        return cls(env.get("FASTAPI_MATCHING_URL", "").strip(), timeout)

    # ------------------------------------------------------------------ public

    def health(self, correlation_id: str = "") -> dict[str, Any]:
        status, body = self._request("GET", "/health", None, correlation_id)
        if status != 200 or not isinstance(body, dict):
            raise MatchingEngineConnectionError("The matching engine health check failed.")
        return body

    def match(self, payload: MatchingRequestPayload) -> MatchingResponsePayload:
        """POST /match. Returns a contract-validated response or raises."""
        status, body = self._request("POST", "/match", payload.to_dict(), payload.correlation_id)
        if status != 200:
            error = EngineErrorPayload.from_dict(body)
            raise MatchingEngineResponseError(status, error.code, error.message, error.field_errors)
        return MatchingResponsePayload.from_dict(body)

    # ----------------------------------------------------------------- private

    def _request(
        self, method: str, path: str, body: dict[str, Any] | None, correlation_id: str
    ) -> tuple[int, Any]:
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        request = urllib.request.Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        try:
            # Scheme is restricted to http/https in __init__.
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310
                return response.status, self._read_json(response)
        except urllib.error.HTTPError as exc:
            with exc:
                return exc.code, self._read_json(exc, tolerate_invalid=True)
        except TimeoutError as exc:
            logger.warning("matching_engine_timeout path=%s correlation_id=%s", path, correlation_id or "-")
            raise MatchingEngineTimeoutError() from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise MatchingEngineTimeoutError() from exc
            logger.warning("matching_engine_unreachable path=%s correlation_id=%s", path, correlation_id or "-")
            raise MatchingEngineConnectionError() from exc

    @staticmethod
    def _read_json(response, tolerate_invalid: bool = False) -> Any:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise InvalidMatchingPayloadError("The matching engine response is too large.")
        try:
            return json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            if tolerate_invalid:
                return None
            raise InvalidMatchingPayloadError("The matching engine returned invalid JSON.") from exc
