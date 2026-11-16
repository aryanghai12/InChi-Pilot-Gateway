"""
Concrete Embedding Provider Implementation and Factory.

get_embedding_provider() maps EMBEDDING_PROVIDER to a provider:

* "none" (default): NoneEmbeddingProvider. Every embed call raises
  EmbeddingGenerationError, so semantic matching fails explicitly instead of
  silently producing a rules-only result (MVP_FEATURES M6-AC5).
* "sentence_transformers" / "fastembed": refused with ConfigurationError until
  the library and model are decided under D-11. No ML library is imported.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 3 foundation.

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: D-11 (Embedding Model Selection) — model is TBD and is NOT
# selected, defaulted or hard-coded anywhere. When D-11 is recorded in
# ARCHITECTURE.md §9, add a provider class here that reads the model name from
# EMBEDDING_MODEL_NAME, with trust_remote_code disabled, offline weights only
# and Hub telemetry off (Ajendra review).
"""

from __future__ import annotations

from collections.abc import Sequence

from ai_matching.core.config import EngineSettings
from ai_matching.core.exceptions import ConfigurationError, EmbeddingGenerationError
from ai_matching.providers.base import EmbeddingProvider


class NoneEmbeddingProvider(EmbeddingProvider):
    """Placeholder provider used until D-11 is decided. Always fails explicitly."""

    name = "none"

    @property
    def model_id(self) -> str:
        return "none"

    @property
    def dimension(self) -> int:
        raise EmbeddingGenerationError("No embedding model is configured (D-11 pending).")

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise EmbeddingGenerationError("No embedding model is configured (D-11 pending).")


def get_embedding_provider(settings: EngineSettings) -> EmbeddingProvider:
    """Return the configured provider, or raise ConfigurationError if it cannot be used."""
    if settings.embedding_provider == "none":
        return NoneEmbeddingProvider()
    raise ConfigurationError(
        f"Embedding provider '{settings.embedding_provider}' is not available: "
        "the embedding library and model are pending decision D-11."
    )
