"""
Structured Logging Configuration.

Configures structured logging for pipeline stages, candidate counts, and execution metrics.
Strictly prohibits logging raw confidential data, credentials, or personal information:
log codes, counts, stage names and correlation IDs only — never payload text.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 foundation.
"""

import logging

LOGGER_NAME = "ai_matching"


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child of the engine logger. Handlers come from the host process."""
    return logging.getLogger(f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME)


def log_stage(logger: logging.Logger, stage: str, correlation_id: str, **counts: int) -> None:
    """Log a pipeline stage event with integer counts only (no payload content)."""
    details = " ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    logger.info("stage=%s correlation_id=%s %s", stage, correlation_id or "-", details)
