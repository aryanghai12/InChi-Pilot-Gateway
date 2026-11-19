"""
Semantic Matching Coordinator.

Coordinates embedding generation and similarity computation.
Non-negotiable principle: semantic matching is mandatory; semantic processing failure
explicitly fails the run (no silent fallback to rules-only).

compute_semantic_similarities() embeds the requirement text and every candidate
text in one provider call, validates the provider output, and returns raw cosine
similarities in candidate order. Any provider or vector problem raises; there is
no partial or default result.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 3 foundation. Not yet wired into the pipeline: semantic matching runs
after mandatory eligibility (Stage 2), which is pending D-04.

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: D-11 (Embedding Model Selection).
# PENDING DECISION: rules-only fallback conflict (docs/ai/EVALUATION_AND_FALLBACK_DESIGN.md).
"""

from __future__ import annotations

from collections.abc import Sequence

from ai_matching.core.exceptions import EmbeddingGenerationError
from ai_matching.providers.base import EmbeddingProvider
from ai_matching.services.similarity import cosine_similarities


def compute_semantic_similarities(
    provider: EmbeddingProvider, requirement_text: str, candidate_texts: Sequence[str]
) -> list[float]:
    """Raw cosine similarity of the requirement against each candidate text, in order."""
    if not requirement_text:
        raise EmbeddingGenerationError("Requirement text for embedding is empty.")
    if not candidate_texts:
        return []

    texts = [requirement_text, *candidate_texts]
    try:
        vectors = provider.embed(texts)
    except EmbeddingGenerationError:
        raise
    except Exception as exc:  # provider internals must never leak or be swallowed
        raise EmbeddingGenerationError("The embedding provider raised an unexpected error.") from exc

    if len(vectors) != len(texts):
        raise EmbeddingGenerationError(
            f"Embedding provider returned {len(vectors)} vectors for {len(texts)} texts."
        )
    return cosine_similarities(vectors[0], vectors[1:])
