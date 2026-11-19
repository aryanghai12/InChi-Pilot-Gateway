"""
Abstract Base Class for Embedding Providers.

Defines the contract every local embedding provider implements, so the model
stays replaceable (AGENTS.md C7 rule 7). Providers run locally only: pilot data
never leaves the environment (ARCHITECTURE.md §1, THREAT_MODEL T-ID-03).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 3 foundation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class EmbeddingProvider(ABC):
    """A local text-embedding backend."""

    #: Provider identifier, matching EMBEDDING_PROVIDER (e.g. "none").
    name: str

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Model ID and version recorded on every run (M6-AC6), or "none"."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimension. Raises EmbeddingGenerationError if no model is loaded."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Embed texts in order. Must return exactly len(texts) vectors of equal
        dimension, or raise EmbeddingGenerationError. Never returns partial output.
        """
