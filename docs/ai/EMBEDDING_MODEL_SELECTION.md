# Embedding Model Selection (D-11)

| | |
|---|---|
| **Decision** | D-11, embedding library and model |
| **Status** | **Selected by the C7 owner on 19 Nov 2026: `sentence-transformers/all-MiniLM-L6-v2`** (library `sentence-transformers`). **Not yet recorded** in ARCHITECTURE.md §9. AGENTS.md requires Aryan to record it there after Ajendra's review (licence, offline loading, telemetry, dependency size). Until then, treat the selection as pending. |
| **Owner** | Alok Tiwari (C7), with Ajendra (security and licence review). Aryan records the outcome in ARCHITECTURE.md §9. |
| **Needed by** | Before Week 5 hybrid work, ideally Gate 2 (20 Nov 2026) |

## 0. Integration (implemented 19 Nov 2026)

| Aspect | Implementation |
|---|---|
| Where the name lives | Only in the environment variable `EMBEDDING_MODEL_NAME` (`.env.example`), read by `ai_matching/core/config.py`. No model name appears in code defaults. |
| Provider | `SentenceTransformerEmbeddingProvider` in `ai_matching/providers/embedding_provider.py`, selected with `EMBEDDING_PROVIDER=sentence_transformers` |
| Loading | Lazy: nothing is imported or loaded at application import or on `/health`. The model loads on the first `/match`, then is cached once per process behind a lock and reused. |
| Security | `trust_remote_code=False`, `device="cpu"`. `EMBEDDING_LOCAL_FILES_ONLY=true` (default) means the model is never downloaded at request time. Telemetry is off (`HF_HUB_DISABLE_TELEMETRY=1`) and the hub is offline (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`). |
| Weights download | Deliberate, one-off: `python -m ai_matching.providers.download_model`, run with the offline flags off. Only weights are fetched; no pilot data is sent. |
| Output | `encode(normalize_embeddings=True)`, then the vectors are validated (count, equal dimension, finite). Dimension 384, observed. |
| Failures | Library missing, model not cached, or inference error all raise `EmbeddingGenerationError`. **The run fails explicitly; there is no fallback** (M6-AC5). |
| Dependency | `ai_matching/requirements-semantic.txt`: `sentence-transformers==6.3.0`, verified with CPU `torch==2.15.0+cpu`. It's an optional install; the base engine image does not include it. |
| Replacement | Change `EMBEDDING_MODEL_NAME` (and Vishal's vector dimension if it differs). No code change is needed for another sentence-transformers model. |

**Verified 19 Nov 2026** in an isolated venv:
- A load with local files only failed explicitly before the download.
- The download command fetched the model (dimension 384).
- The opt-in real-model tests passed fully offline (`RUN_REAL_MODEL_TESTS=1`).
- In a live engine run, the model loaded once (≈19 s) and was reused on the next run (≈0.05 s).

No accuracy evaluation has been run yet (§3).

## 1. Selection criteria

| # | Criterion | Why | Check |
|---|---|---|---|
| 1 | Runs locally on CPU; weights downloaded once, then offline | Pilot data never leaves the environment (T-ID-03) | Run with `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1` |
| 2 | No `trust_remote_code` | No arbitrary code from the model repo | Loads with the flag off |
| 3 | Permissive licence (Apache-2.0 or MIT) on the weights | Reuse and handover | Ajendra verifies on the model card |
| 4 | English quality on short product text | MVP is English only (DS-11) | Evaluation set (§3) |
| 5 | Small: download size, RAM and latency at pilot volume | Compose demo machine, no GPU | Measure embedding 30–300 records |
| 6 | Fixed output dimension | Vishal's pgvector column needs it (TD-01) | Read from the model config |
| 7 | Maintained, widely used | Supportability | Release history |

## 2. Candidate shortlist

These are **candidates to evaluate, not recommendations**. Licences and sizes come from public model cards and must be re-verified by Ajendra at evaluation time.

| Candidate | Library | Dimension | Stated licence | Notes |
|---|---|---|---|---|
| `sentence-transformers/all-MiniLM-L6-v2` | sentence-transformers | 384 | Apache-2.0 | Very small and fast; widely used baseline |
| `BAAI/bge-small-en-v1.5` | sentence-transformers or FastEmbed | 384 | MIT | Strong retrieval quality for its size |
| `intfloat/e5-small-v2` | sentence-transformers | 384 | MIT | Needs `query:` / `passage:` prefixes |

The library choice (sentence-transformers needs PyTorch; FastEmbed uses ONNX Runtime) is part of D-11. ARCHITECTURE.md §1 records `sentence-transformers` as the evaluated library and FastEmbed as pending confirmation.

## 3. Evaluation plan

1. Build a synthetic set with Harish: requirement texts paired with product texts labelled relevant or irrelevant. It must include near-duplicates, synonyms and unrelated-but-same-category items. No real data.
2. For each candidate, embed with the Stage 1 template (`embedding-text-v0`). Record precision of the top results and how well relevant pairs separate from irrelevant ones, plus load time, RAM and latency.
3. Record model ID, revision and library versions in the results file (M6-AC7, M11-AC8). Report only what was observed on that set.
4. Ajendra reviews licence, offline loading, telemetry and dependency size. The proposal goes to Aryan for §9.

## 4. After the decision

- Add a provider class in `ai_matching/providers/embedding_provider.py` that reads `EMBEDDING_MODEL_NAME` (no default).
- Add `requirements-semantic.txt`.
- Vishal adds `Product.embedding` with the decided dimension.
