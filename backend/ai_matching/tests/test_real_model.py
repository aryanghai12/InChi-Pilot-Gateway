"""
Opt-in integration test with the REAL configured embedding model.

Skipped unless RUN_REAL_MODEL_TESTS=1, sentence-transformers is installed and
EMBEDDING_MODEL_NAME is set. It loads whatever model EMBEDDING_MODEL_NAME names
(no model name is hard-coded) and checks shape, normalisation and that related
synthetic texts are more similar than unrelated ones. It does not measure accuracy.

    RUN_REAL_MODEL_TESTS=1 EMBEDDING_PROVIDER=sentence_transformers \
    EMBEDDING_MODEL_NAME=<model> python -m pytest ai_matching/tests/test_real_model.py

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
"""

import importlib.util
import math
import os
import unittest

from ai_matching.core.config import load_settings
from ai_matching.providers.embedding_provider import get_embedding_provider
from ai_matching.services.semantic_matcher import compute_semantic_similarities

ENABLED = (
    os.environ.get("RUN_REAL_MODEL_TESTS") == "1"
    and importlib.util.find_spec("sentence_transformers") is not None
    and bool(os.environ.get("EMBEDDING_MODEL_NAME"))
)


@unittest.skipUnless(ENABLED, "Real-model test disabled (set RUN_REAL_MODEL_TESTS=1 and EMBEDDING_MODEL_NAME).")
class RealModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = get_embedding_provider(load_settings())

    def test_vectors_have_model_dimension_and_unit_norm(self):
        vectors = self.provider.embed(["Synthetic printed circuit boards", "Synthetic cotton yarn"])
        self.assertEqual(len(vectors[0]), self.provider.dimension)
        self.assertAlmostEqual(math.sqrt(sum(x * x for x in vectors[0])), 1.0, places=4)

    def test_related_text_scores_higher_than_unrelated(self):
        similarities = compute_semantic_similarities(
            self.provider,
            "Requirement: synthetic electronic circuit boards for assembly",
            ["Product: synthetic printed circuit board, two-layer", "Product: synthetic organic cotton textile yarn"],
        )
        self.assertGreater(similarities[0], similarities[1])
