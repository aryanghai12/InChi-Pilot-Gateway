"""
Unit Tests: Vector Similarity Computation and Semantic Coordinator.

Tests cosine similarity math, orthogonal vectors, identical vectors,
negative similarity, and dimension mismatch errors, plus explicit failure of
the semantic coordinator when the provider fails (MVP_FEATURES M6-AC5).

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
"""

import math
import unittest

from ai_matching.core.exceptions import (
    EmbeddingGenerationError,
    SimilarityComputationError,
)
from ai_matching.providers.base import EmbeddingProvider
from ai_matching.providers.embedding_provider import NoneEmbeddingProvider
from ai_matching.services.semantic_matcher import compute_semantic_similarities
from ai_matching.services.similarity import cosine_similarities, cosine_similarity


class CosineSimilarityTests(unittest.TestCase):
    def test_identical_vectors(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 1.0)

    def test_orthogonal_vectors(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)

    def test_opposite_vectors(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 1.0], [-1.0, -1.0]), -1.0)

    def test_scale_invariance(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 2.0], [10.0, 20.0]), 1.0)

    def test_known_value(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [1.0, 1.0]), 1 / math.sqrt(2))

    def test_result_is_clamped(self):
        value = cosine_similarity([0.1] * 50, [0.1] * 50)
        self.assertLessEqual(value, 1.0)

    def test_dimension_mismatch_raises(self):
        with self.assertRaises(SimilarityComputationError):
            cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])

    def test_empty_vector_raises(self):
        with self.assertRaises(SimilarityComputationError):
            cosine_similarity([], [])

    def test_zero_vector_raises_instead_of_returning_zero(self):
        with self.assertRaises(SimilarityComputationError):
            cosine_similarity([0.0, 0.0], [1.0, 1.0])

    def test_non_finite_raises(self):
        with self.assertRaises(SimilarityComputationError):
            cosine_similarity([float("nan"), 1.0], [1.0, 1.0])

    def test_batch_preserves_order(self):
        values = cosine_similarities([1.0, 0.0], [[1.0, 0.0], [0.0, 1.0]])
        self.assertAlmostEqual(values[0], 1.0)
        self.assertAlmostEqual(values[1], 0.0)


class _FakeProvider(EmbeddingProvider):
    """Deterministic test double: never a real model."""

    name = "fake"

    def __init__(self, vectors=None, error: Exception | None = None):
        self._vectors = vectors
        self._error = error

    @property
    def model_id(self) -> str:
        return "fake-test-double"

    @property
    def dimension(self) -> int:
        return 2

    def embed(self, texts):
        if self._error:
            raise self._error
        return self._vectors if self._vectors is not None else [[1.0, 0.0] for _ in texts]


class SemanticMatcherTests(unittest.TestCase):
    def test_similarities_in_candidate_order(self):
        provider = _FakeProvider(vectors=[[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
        values = compute_semantic_similarities(provider, "requirement", ["a", "b"])
        self.assertAlmostEqual(values[0], 1.0)
        self.assertAlmostEqual(values[1], 0.0)

    def test_none_provider_fails_explicitly(self):
        with self.assertRaises(EmbeddingGenerationError):
            compute_semantic_similarities(NoneEmbeddingProvider(), "requirement", ["a"])

    def test_unexpected_provider_error_is_wrapped(self):
        provider = _FakeProvider(error=RuntimeError("internal detail"))
        with self.assertRaises(EmbeddingGenerationError) as ctx:
            compute_semantic_similarities(provider, "requirement", ["a"])
        self.assertNotIn("internal detail", ctx.exception.message)

    def test_wrong_vector_count_fails(self):
        provider = _FakeProvider(vectors=[[1.0, 0.0]])
        with self.assertRaises(EmbeddingGenerationError):
            compute_semantic_similarities(provider, "requirement", ["a", "b"])

    def test_empty_requirement_text_fails(self):
        with self.assertRaises(EmbeddingGenerationError):
            compute_semantic_similarities(_FakeProvider(), "", ["a"])

    def test_no_candidates_returns_empty(self):
        self.assertEqual(compute_semantic_similarities(_FakeProvider(), "requirement", []), [])


if __name__ == "__main__":
    unittest.main()
