"""
Deliberate, one-off download of the configured embedding model weights.

Request handling never downloads (EMBEDDING_LOCAL_FILES_ONLY=true). Run this once
per environment, for example during image build or setup:

    cd backend
    EMBEDDING_PROVIDER=sentence_transformers \
    EMBEDDING_MODEL_NAME=<model from .env> \
    python -m ai_matching.providers.download_model

Only model weights are fetched from the model hub. No pilot data is sent. The
model name is read from EMBEDDING_MODEL_NAME; nothing is hard-coded here.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
"""

from __future__ import annotations

import sys

from ai_matching.core.config import load_settings
from ai_matching.core.exceptions import MatchingEngineException
from ai_matching.providers.embedding_provider import (
    SentenceTransformerEmbeddingProvider,
)


def main() -> int:
    try:
        settings = load_settings()
        if settings.embedding_provider != "sentence_transformers":
            print("EMBEDDING_PROVIDER must be 'sentence_transformers' to download a model.", file=sys.stderr)
            return 2
        provider = SentenceTransformerEmbeddingProvider(
            model_name=settings.embedding_model_name or "",
            cache_dir=settings.embedding_model_cache_dir,
            local_files_only=False,
        )
        dimension = provider.dimension
    except MatchingEngineException as exc:
        print(f"Download failed: {exc.message}", file=sys.stderr)
        return 1
    print(f"Model '{provider.model_id}' is available locally (dimension {dimension}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
