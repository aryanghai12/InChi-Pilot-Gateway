"""
Concrete Embedding Provider Implementations and Factory.

get_embedding_provider() maps EMBEDDING_PROVIDER to a provider:

* "none" (default): NoneEmbeddingProvider. Every embed call raises
  EmbeddingGenerationError, so semantic matching fails explicitly instead of
  silently producing a rules-only result (MVP_FEATURES M6-AC5).
* "sentence_transformers": SentenceTransformerEmbeddingProvider, a local CPU
  model whose name comes ONLY from EMBEDDING_MODEL_NAME (core/config.py).

Model lifecycle (SentenceTransformerEmbeddingProvider):
* Nothing is imported or loaded at module import time. The library is imported
  and the model loaded on the first embed() call.
* The loaded model is cached per (model name, cache dir) for the whole process
  and shared by every request; a lock prevents concurrent double loads.
* Security (THREAT_MODEL T-ID-03, AGENTS.md C2 week 5): trust_remote_code is
  always False; device is CPU; with EMBEDDING_LOCAL_FILES_ONLY=true (default) the
  model is read only from the local cache and never downloaded at request time.
  Weights are fetched deliberately with `python -m ai_matching.providers.download_model`.
* Any import, load or inference problem raises EmbeddingGenerationError with a
  generic message; library internals (paths, stack traces) are not exposed.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Implemented.

NOTE ON ARCHITECTURE & DECISIONS:
# D-11: model selected by the C7 owner on 2026-11-19
# (sentence-transformers/all-MiniLM-L6-v2, set via EMBEDDING_MODEL_NAME only).
# Must be recorded in ARCHITECTURE.md §9 by Aryan after Ajendra's review.
"""

from __future__ import annotations

import math
import threading
from collections.abc import Callable, Sequence
from typing import Any

from ai_matching.core.config import EngineSettings
from ai_matching.core.exceptions import ConfigurationError, EmbeddingGenerationError
from ai_matching.core.logging import get_logger
from ai_matching.providers.base import EmbeddingProvider

logger = get_logger("providers")

_MODEL_CACHE: dict[tuple[str, str | None, bool], Any] = {}
_MODEL_CACHE_LOCK = threading.Lock()

ModelLoader = Callable[[str, str | None, bool], Any]


class NoneEmbeddingProvider(EmbeddingProvider):
    """Used when no provider is configured. Always fails explicitly."""

    name = "none"

    @property
    def model_id(self) -> str:
        return "none"

    @property
    def dimension(self) -> int:
        raise EmbeddingGenerationError("No embedding provider is configured.")

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise EmbeddingGenerationError("No embedding provider is configured.")


def _load_sentence_transformer(model_name: str, cache_dir: str | None, local_files_only: bool) -> Any:
    """Default loader. Imports the library lazily so the engine starts without it."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise EmbeddingGenerationError(
            "The sentence-transformers library is not installed (see ai_matching/requirements-semantic.txt)."
        ) from exc
    return SentenceTransformer(
        model_name,
        device="cpu",
        cache_folder=cache_dir,
        trust_remote_code=False,
        local_files_only=local_files_only,
    )


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformers model, loaded once per process and reused."""

    name = "sentence_transformers"

    def __init__(
        self,
        model_name: str,
        cache_dir: str | None = None,
        local_files_only: bool = True,
        loader: ModelLoader | None = None,
    ):
        if not model_name:
            raise ConfigurationError("An embedding model name is required.")
        self._model_name = model_name
        self._cache_dir = cache_dir
        self._local_files_only = local_files_only
        self._loader = loader or _load_sentence_transformer

    @property
    def model_id(self) -> str:
        return self._model_name

    def _model(self) -> Any:
        key = (self._model_name, self._cache_dir, self._local_files_only)
        model = _MODEL_CACHE.get(key)
        if model is not None:
            return model
        with _MODEL_CACHE_LOCK:
            model = _MODEL_CACHE.get(key)
            if model is None:
                logger.info("embedding_model_loading provider=%s", self.name)
                try:
                    model = self._loader(self._model_name, self._cache_dir, self._local_files_only)
                except EmbeddingGenerationError:
                    raise
                except Exception as exc:
                    logger.warning("embedding_model_load_failed provider=%s error=%s", self.name, type(exc).__name__)
                    raise EmbeddingGenerationError(
                        "The embedding model could not be loaded. If EMBEDDING_LOCAL_FILES_ONLY is true, "
                        "download it first with: python -m ai_matching.providers.download_model"
                    ) from exc
                _MODEL_CACHE[key] = model
                logger.info("embedding_model_loaded provider=%s", self.name)
        return model

    @property
    def dimension(self) -> int:
        model = self._model()
        # Newer sentence-transformers names it get_embedding_dimension(); older ones
        # use get_sentence_embedding_dimension().
        getter = getattr(model, "get_embedding_dimension", None) or getattr(
            model, "get_sentence_embedding_dimension", None
        )
        try:
            dimension = int(getter())
        except EmbeddingGenerationError:
            raise
        except Exception as exc:
            raise EmbeddingGenerationError("The embedding model dimension is unavailable.") from exc
        if dimension <= 0:
            raise EmbeddingGenerationError("The embedding model reported an invalid dimension.")
        return dimension

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._model()
        try:
            raw = model.encode(
                list(texts),
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            vectors = [[float(x) for x in row] for row in raw]
        except Exception as exc:
            logger.warning("embedding_inference_failed provider=%s error=%s", self.name, type(exc).__name__)
            raise EmbeddingGenerationError("Embedding generation failed.") from exc

        if len(vectors) != len(texts):
            raise EmbeddingGenerationError("The embedding model returned the wrong number of vectors.")
        widths = {len(v) for v in vectors}
        if len(widths) != 1 or 0 in widths:
            raise EmbeddingGenerationError("The embedding model returned vectors of inconsistent dimension.")
        if not all(math.isfinite(x) for v in vectors for x in v):
            raise EmbeddingGenerationError("The embedding model returned non-finite values.")
        return vectors


def clear_model_cache() -> None:
    """Drop cached models (tests and controlled reloads only)."""
    with _MODEL_CACHE_LOCK:
        _MODEL_CACHE.clear()


def get_embedding_provider(settings: EngineSettings, loader: ModelLoader | None = None) -> EmbeddingProvider:
    """Return the configured provider. Creating it never loads the model."""
    if settings.embedding_provider == "none":
        return NoneEmbeddingProvider()
    if settings.embedding_provider == "sentence_transformers":
        return SentenceTransformerEmbeddingProvider(
            model_name=settings.embedding_model_name or "",
            cache_dir=settings.embedding_model_cache_dir,
            local_files_only=settings.embedding_local_files_only,
            loader=loader,
        )
    raise ConfigurationError(f"Embedding provider '{settings.embedding_provider}' is not supported.")
