"""
Application Configuration and Settings.

Reads FastAPI AI Matching Engine configuration from environment variables only
(ARCHITECTURE.md §5 "Configuration"). No secrets, model names, weights or
thresholds have defaults here.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 foundation.

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: D-11 (embedding model) — EMBEDDING_MODEL_NAME has NO default.
#   The placeholder value in .env.example ("TBD-D11-PENDING-APPROVAL") is
#   treated as "not configured".
# PENDING DECISION: D-05 (weights) — not configured here; weights will come from
#   versioned, approved matching configuration, never from code defaults.
# PENDING DECISION: engine deployment arrangement (ARCHITECTURE.md §6.3, labelled
#   "D-15" there but D-15 is a different business decision in MVP_FEATURES §12).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from ai_matching.core.exceptions import ConfigurationError

# Values that mean "the model has not been decided yet" (D-11).
_UNSET_MODEL_MARKERS = {"", "tbd", "none", "tbd-d11-pending-approval"}

SUPPORTED_EMBEDDING_PROVIDERS = ("none", "sentence_transformers", "fastembed")


@dataclass(frozen=True)
class EngineSettings:
    """Immutable engine settings resolved from the environment."""

    host: str
    port: int
    embedding_provider: str
    embedding_model_name: str | None

    @property
    def embedding_model_configured(self) -> bool:
        return self.embedding_model_name is not None


def _parse_port(raw: str) -> int:
    try:
        port = int(raw)
    except ValueError as exc:
        raise ConfigurationError("MATCHING_ENGINE_PORT must be an integer.") from exc
    if not 1 <= port <= 65535:
        raise ConfigurationError("MATCHING_ENGINE_PORT must be between 1 and 65535.")
    return port


def load_settings(environ: dict[str, str] | None = None) -> EngineSettings:
    """Build settings from an environment mapping (defaults to os.environ)."""
    env = os.environ if environ is None else environ

    provider = env.get("EMBEDDING_PROVIDER", "none").strip().lower() or "none"
    if provider not in SUPPORTED_EMBEDDING_PROVIDERS:
        raise ConfigurationError(
            f"EMBEDDING_PROVIDER must be one of: {', '.join(SUPPORTED_EMBEDDING_PROVIDERS)}."
        )

    model_raw = env.get("EMBEDDING_MODEL_NAME", "").strip()
    model_name = None if model_raw.lower() in _UNSET_MODEL_MARKERS else model_raw

    return EngineSettings(
        # Default to loopback; containers set MATCHING_ENGINE_HOST explicitly.
        host=env.get("MATCHING_ENGINE_HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_parse_port(env.get("MATCHING_ENGINE_PORT", "8001").strip() or "8001"),
        embedding_provider=provider,
        embedding_model_name=model_name,
    )


@lru_cache(maxsize=1)
def get_settings() -> EngineSettings:
    """Process-wide cached settings (FastAPI dependency)."""
    return load_settings()
