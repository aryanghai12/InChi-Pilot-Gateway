# Embedding Model Selection (D-11)

| | |
|---|---|
| **Decision** | D-11, embedding library and model |
| **Status** | **Open. No model is selected.** This document is the Week 3 shortlist and evaluation plan. It is a proposal, not a decision. |
| **Owner** | Alok Tiwari (C7), with Ajendra (security and licence review). Aryan records the outcome in ARCHITECTURE.md §9. |
| **Needed by** | Before Week 5 hybrid work, ideally Gate 2 (20 Nov 2026) |

Until D-11 is recorded, the code ships only the `none` provider. `sentence_transformers` and `fastembed` are refused by configuration, and no model name exists in code or configuration defaults.

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
