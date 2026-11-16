"""
Core Domain Exceptions for FastAPI AI Matching Engine.

Every engine failure is an explicit, typed exception carrying a stable error
code. The API layer converts them into the project error envelope
{"code", "message", "field_errors", "correlation_id"} (ARCHITECTURE.md §5).
No exception message may contain request payload values or secrets.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 foundation.
"""


class MatchingEngineException(Exception):
    """Base class for all engine errors. Never raised directly."""

    code = "engine_error"
    http_status = 500
    default_message = "The matching engine failed to process the request."

    def __init__(self, message: str | None = None, field_errors: dict[str, list[str]] | None = None):
        self.message = message or self.default_message
        self.field_errors = field_errors or {}
        super().__init__(self.message)


class InvalidRequestError(MatchingEngineException):
    """The request is structurally valid JSON but violates the contract."""

    code = "validation_error"
    http_status = 422
    default_message = "The matching request failed validation."


class StageNotAvailableError(MatchingEngineException):
    """
    A pipeline stage cannot run because its approved rules, configuration or
    model do not exist yet (e.g. eligibility before D-04, semantic before D-11).

    This is an explicit failure: the run must be recorded as failed and no
    partial results may be returned (MVP_FEATURES M6-AC5).
    """

    code = "stage_not_available"
    http_status = 503
    default_message = "A required matching stage is not available."

    def __init__(self, stage: str, reason: str):
        self.stage = stage
        self.reason = reason
        super().__init__(f"Matching stage '{stage}' is not available: {reason}")


class EligibilityEvaluationError(MatchingEngineException):
    """Mandatory eligibility evaluation could not be completed."""

    code = "eligibility_evaluation_failed"
    http_status = 500
    default_message = "Mandatory eligibility evaluation failed."


class EmbeddingGenerationError(MatchingEngineException):
    """Embedding provider unavailable or embedding generation failed."""

    code = "embedding_generation_failed"
    http_status = 503
    default_message = "Embedding generation failed."


class SimilarityComputationError(MatchingEngineException):
    """Vectors cannot be compared (empty, dimension mismatch, zero norm, non-finite)."""

    code = "similarity_computation_failed"
    http_status = 500
    default_message = "Semantic similarity could not be computed."


class PipelineExecutionError(MatchingEngineException):
    """Unexpected failure while orchestrating the pipeline."""

    code = "pipeline_execution_failed"
    http_status = 500
    default_message = "The matching pipeline failed."


class ConfigurationError(MatchingEngineException):
    """Engine configuration (environment variables) is invalid."""

    code = "engine_configuration_error"
    http_status = 500
    default_message = "The matching engine is misconfigured."
