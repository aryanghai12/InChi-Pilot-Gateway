"""
Application Configuration and Settings.

Reads FastAPI AI Matching Engine configuration from environment variables only
(ARCHITECTURE.md §5 "Configuration"). This module is the single place where the
embedding model name is read; no other module reads or hard-codes it.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2 foundation; Week 3 embedding settings.

Environment variables:
    MATCHING_ENGINE_HOST / MATCHING_ENGINE_PORT  bind address (default 127.0.0.1:8001)
    EMBEDDING_PROVIDER             "none" | "sentence_transformers" (default "none")
    EMBEDDING_MODEL_NAME           model identifier; NO default in code
    EMBEDDING_MODEL_CACHE_DIR      optional local directory for model weights
    EMBEDDING_LOCAL_FILES_ONLY     "true" (default): never download at request time
    MATCHING_CRITERIA_DIR          optional override of the versioned scoring-config directory
    MATCHING_ALLOW_UNAPPROVED_CONFIG  "false" (default): refuse unapproved scoring configs

NOTE ON ARCHITECTURE & DECISIONS:
# D-11: the model name comes only from EMBEDDING_MODEL_NAME. The C7 owner selected
#   sentence-transformers/all-MiniLM-L6-v2 on 2026-11-19; that selection must be
#   recorded in ARCHITECTURE.md §9 (Aryan) after Ajendra's review.
# D-04 / D-05: weights and criteria are NOT configured here; they come from the
#   versioned scoring configuration (core/scoring_config.py).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ai_matching.core.exceptions import ConfigurationError

# Values that mean "no model has been configured".
_UNSET_MODEL_MARKERS = {"", "tbd", "none", "tbd-d11-pending-approval"}

SUPPORTED_EMBEDDING_PROVIDERS = ("none", "sentence_transformers")

DEFAULT_CRITERIA_DIR = Path(__file__).resolve().parent.parent / "criteria"

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


@dataclass(frozen=True)
class EngineSettings:
    """Immutable engine settings resolved from the environment."""

    host: str
    port: int
    embedding_provider: str
    embedding_model_name: str | None
    embedding_model_cache_dir: str | None = None
    embedding_local_files_only: bool = True
    criteria_dir: Path = DEFAULT_CRITERIA_DIR
    allow_unapproved_config: bool = False

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


def _parse_bool(env: dict[str, str], name: str, default: bool) -> bool:
    raw = env.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise ConfigurationError(f"{name} must be true or false.")


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
    if provider != "none" and model_name is None:
        raise ConfigurationError(f"EMBEDDING_MODEL_NAME is required when EMBEDDING_PROVIDER={provider}.")

    criteria_dir_raw = env.get("MATCHING_CRITERIA_DIR", "").strip()

    return EngineSettings(
        # Default to loopback; containers set MATCHING_ENGINE_HOST explicitly.
        host=env.get("MATCHING_ENGINE_HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_parse_port(env.get("MATCHING_ENGINE_PORT", "8001").strip() or "8001"),
        embedding_provider=provider,
        embedding_model_name=model_name,
        embedding_model_cache_dir=env.get("EMBEDDING_MODEL_CACHE_DIR", "").strip() or None,
        embedding_local_files_only=_parse_bool(env, "EMBEDDING_LOCAL_FILES_ONLY", True),
        criteria_dir=Path(criteria_dir_raw) if criteria_dir_raw else DEFAULT_CRITERIA_DIR,
        allow_unapproved_config=_parse_bool(env, "MATCHING_ALLOW_UNAPPROVED_CONFIG", False),
    )


@lru_cache(maxsize=1)
def get_settings() -> EngineSettings:
    """Process-wide cached settings (FastAPI dependency)."""
    return load_settings()
