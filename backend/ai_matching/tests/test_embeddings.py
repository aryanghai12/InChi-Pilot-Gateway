"""
Unit Tests: Embedding provider (sentence-transformers integration) — mocked model.

Proves the model is loaded lazily, exactly once, reused across calls, never with
trust_remote_code, and that load/inference failures fail explicitly. No real
model is used here; see test_real_model.py for an opt-in check with real weights.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
"""

import threading
import unittest

from ai_matching.core.config import load_settings
from ai_matching.core.exceptions import ConfigurationError, EmbeddingGenerationError
from ai_matching.providers.embedding_provider import (
    NoneEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    clear_model_cache,
    get_embedding_provider,
)

MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class _FakeModel:
    def __init__(self, dim=3, rows=None, fail=False):
        self.dim, self.rows, self.fail, self.encode_calls = dim, rows, fail, 0

    def get_embedding_dimension(self):
        return self.dim

    def encode(self, texts, **kwargs):
        self.encode_calls += 1
        self.kwargs = kwargs
        if self.fail:
            raise RuntimeError("internal model detail /secret/path")
        return self.rows if self.rows is not None else [[1.0, 0.0, 0.0] for _ in texts]


class _CountingLoader:
    def __init__(self, model=None, error=None):
        self.model, self.error, self.calls, self.args = model or _FakeModel(), error, 0, None

    def __call__(self, name, cache_dir, local_only):
        self.calls += 1
        self.args = (name, cache_dir, local_only)
        if self.error:
            raise self.error
        return self.model


class SentenceTransformerProviderTests(unittest.TestCase):
    def setUp(self):
        clear_model_cache()

    def tearDown(self):
        clear_model_cache()

    def test_creating_provider_does_not_load_model(self):
        loader = _CountingLoader()
        SentenceTransformerEmbeddingProvider(MODEL, loader=loader)
        self.assertEqual(loader.calls, 0)

    def test_model_loaded_once_and_reused_across_providers(self):
        loader = _CountingLoader()
        SentenceTransformerEmbeddingProvider(MODEL, loader=loader).embed(["a"])
        SentenceTransformerEmbeddingProvider(MODEL, loader=loader).embed(["b", "c"])
        self.assertEqual(loader.calls, 1)
        self.assertEqual(loader.model.encode_calls, 2)

    def test_concurrent_first_use_loads_once(self):
        loader = _CountingLoader()
        provider = SentenceTransformerEmbeddingProvider(MODEL, loader=loader)
        threads = [threading.Thread(target=provider.embed, args=(["x"],)) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(loader.calls, 1)

    def test_model_name_and_local_only_passed_to_loader(self):
        loader = _CountingLoader()
        SentenceTransformerEmbeddingProvider(MODEL, cache_dir="/cache", local_files_only=True, loader=loader).embed(["a"])
        self.assertEqual(loader.args, (MODEL, "/cache", True))

    def test_encode_normalises_and_hides_progress(self):
        loader = _CountingLoader()
        SentenceTransformerEmbeddingProvider(MODEL, loader=loader).embed(["a"])
        self.assertTrue(loader.model.kwargs["normalize_embeddings"])
        self.assertFalse(loader.model.kwargs["show_progress_bar"])

    def test_model_id_and_dimension(self):
        provider = SentenceTransformerEmbeddingProvider(MODEL, loader=_CountingLoader(_FakeModel(dim=384)))
        self.assertEqual(provider.model_id, MODEL)
        self.assertEqual(provider.dimension, 384)

    def test_load_failure_is_explicit_and_hides_internals(self):
        provider = SentenceTransformerEmbeddingProvider(MODEL, loader=_CountingLoader(error=OSError("/home/x/.cache")))
        with self.assertRaises(EmbeddingGenerationError) as ctx:
            provider.embed(["a"])
        self.assertNotIn("/home/x", ctx.exception.message)

    def test_failed_load_is_not_cached(self):
        failing = _CountingLoader(error=OSError("offline"))
        with self.assertRaises(EmbeddingGenerationError):
            SentenceTransformerEmbeddingProvider(MODEL, loader=failing).embed(["a"])
        working = _CountingLoader()
        SentenceTransformerEmbeddingProvider(MODEL, loader=working).embed(["a"])
        self.assertEqual(working.calls, 1)

    def test_inference_failure_is_explicit_and_hides_internals(self):
        provider = SentenceTransformerEmbeddingProvider(MODEL, loader=_CountingLoader(_FakeModel(fail=True)))
        with self.assertRaises(EmbeddingGenerationError) as ctx:
            provider.embed(["a"])
        self.assertNotIn("/secret/path", ctx.exception.message)

    def test_wrong_vector_count_rejected(self):
        provider = SentenceTransformerEmbeddingProvider(MODEL, loader=_CountingLoader(_FakeModel(rows=[[1.0, 0.0]])))
        with self.assertRaises(EmbeddingGenerationError):
            provider.embed(["a", "b"])

    def test_inconsistent_dimensions_rejected(self):
        provider = SentenceTransformerEmbeddingProvider(MODEL, loader=_CountingLoader(_FakeModel(rows=[[1.0], [1.0, 2.0]])))
        with self.assertRaises(EmbeddingGenerationError):
            provider.embed(["a", "b"])

    def test_non_finite_values_rejected(self):
        provider = SentenceTransformerEmbeddingProvider(MODEL, loader=_CountingLoader(_FakeModel(rows=[[float("nan")]])))
        with self.assertRaises(EmbeddingGenerationError):
            provider.embed(["a"])

    def test_empty_input_does_not_load_model(self):
        loader = _CountingLoader()
        self.assertEqual(SentenceTransformerEmbeddingProvider(MODEL, loader=loader).embed([]), [])
        self.assertEqual(loader.calls, 0)

    def test_empty_model_name_rejected(self):
        with self.assertRaises(ConfigurationError):
            SentenceTransformerEmbeddingProvider("")


class ProviderFactoryTests(unittest.TestCase):
    def test_none_by_default(self):
        self.assertIsInstance(get_embedding_provider(load_settings({})), NoneEmbeddingProvider)

    def test_model_name_read_from_environment(self):
        settings = load_settings({"EMBEDDING_PROVIDER": "sentence_transformers", "EMBEDDING_MODEL_NAME": MODEL})
        provider = get_embedding_provider(settings, loader=_CountingLoader())
        self.assertIsInstance(provider, SentenceTransformerEmbeddingProvider)
        self.assertEqual(provider.model_id, MODEL)

    def test_none_provider_fails_explicitly(self):
        with self.assertRaises(EmbeddingGenerationError):
            NoneEmbeddingProvider().embed(["a"])


if __name__ == "__main__":
    unittest.main()
