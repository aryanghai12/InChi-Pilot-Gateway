"""
Custom Exceptions for Django Matching Integration Layer.

Defines domain exceptions: MatchingEngineError, MatchingEngineConnectionError,
MatchingEngineTimeoutError, MatchingEngineResponseError and
InvalidMatchingPayloadError.

Every exception carries a stable `code`. The DRF view layer (Abhishek, C5) maps
them to the standard error envelope and records the run as failed (M6-AC5).
Messages never contain payload values, URLs with credentials or secrets.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component A (Django Integration Layer)
Status: Week 2 implementation.
"""


class MatchingEngineError(Exception):
    """Base class for all matching-integration failures."""

    code = "matching_engine_error"
    default_message = "The matching engine could not complete the request."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class MatchingEngineConnectionError(MatchingEngineError):
    """The engine is not configured or cannot be reached."""

    code = "matching_engine_unavailable"
    default_message = "The matching engine is not reachable."


class MatchingEngineTimeoutError(MatchingEngineError):
    """The engine did not answer within the configured timeout."""

    code = "matching_engine_timeout"
    default_message = "The matching engine did not respond in time."


class MatchingEngineResponseError(MatchingEngineError):
    """The engine answered with an error envelope (non-2xx)."""

    code = "matching_engine_rejected"

    def __init__(self, status_code: int, engine_code: str, message: str, field_errors: dict | None = None):
        self.status_code = status_code
        self.engine_code = engine_code
        self.field_errors = field_errors or {}
        super().__init__(message)


class InvalidMatchingPayloadError(MatchingEngineError):
    """A request could not be built, or a response does not satisfy the contract."""

    code = "invalid_matching_payload"
    default_message = "The matching payload does not satisfy the engine contract."
