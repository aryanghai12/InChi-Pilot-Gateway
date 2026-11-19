"""
Vector Similarity Computation Service.

Computes cosine similarity between requirement and supplier capability embedding vectors.
Invalid input raises SimilarityComputationError; it never returns a silent 0.0,
because a fabricated similarity would be indistinguishable from a real one.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 3 foundation (pure mathematics; no business rule involved).

NOTE ON ARCHITECTURE & DECISIONS:
# Returns raw cosine in [-1, 1]. How that is bounded or mapped into the semantic
# score, and its weight in the hybrid score, are D-05 decisions and are NOT
# implemented here.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from ai_matching.core.exceptions import SimilarityComputationError


def _validated(vector: Sequence[float], name: str) -> list[float]:
    if len(vector) == 0:
        raise SimilarityComputationError(f"Vector '{name}' is empty.")
    values = [float(x) for x in vector]
    if not all(math.isfinite(x) for x in values):
        raise SimilarityComputationError(f"Vector '{name}' contains non-finite values.")
    return values


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two equal-length, non-zero, finite vectors, clamped to [-1, 1]."""
    left = _validated(a, "a")
    right = _validated(b, "b")
    if len(left) != len(right):
        raise SimilarityComputationError(
            f"Vector dimensions differ ({len(left)} vs {len(right)})."
        )
    norm_left = math.sqrt(math.fsum(x * x for x in left))
    norm_right = math.sqrt(math.fsum(y * y for y in right))
    if norm_left == 0.0 or norm_right == 0.0:
        raise SimilarityComputationError("Cannot compute cosine similarity of a zero vector.")
    dot = math.fsum(x * y for x, y in zip(left, right))
    return max(-1.0, min(1.0, dot / (norm_left * norm_right)))


def cosine_similarities(query: Sequence[float], candidates: Sequence[Sequence[float]]) -> list[float]:
    """Cosine similarity of one query vector against many candidate vectors, in order."""
    return [cosine_similarity(query, candidate) for candidate in candidates]
