# Weekly reports — Alok Tiwari



AI Matching and Data Intelligence Engineer · Process, template and rules: [README.md](README.md)



Only Alok Tiwari writes in this file. Newest entry first.



<!-- Add new entries directly below this line. -->

## Week 4 - 16-20 November 2026

_Draft prepared with an AI coding agent on 2026-11-16, updated 2026-11-19; to be checked and completed after the Friday sprint review._

**Completed**
- C7 Week 1–3 foundation (contract, FastAPI app, preprocessing, Django client) - merged 2026-11-17 - PR #67
- Full engine pipeline: eligibility, hybrid scoring from versioned config, ranking, Python explainability; contract 0.2.0-proposed - drafted (uncommitted) - [backend/ai_matching/](../../backend/ai_matching/)
- Embedding provider for `sentence-transformers/all-MiniLM-L6-v2` (env-configured, lazy single load, offline-only by default) - drafted (uncommitted)
- Django `run_matching` service, result records + atomic persist/audit hand-off, weekly matching summary, BuyerRequirement adapter - drafted (uncommitted) - [backend/apps/matching/](../../backend/apps/matching/)

**Meetings, reviews and coordination**
- None.

**In progress**
- Contract review with Abhishek and Vishal - M6-AC6 - [MATCHING_CONTRACT.md](../ai/MATCHING_CONTRACT.md) not yet reviewed

**Tests and validation**
- `python -m pytest ai_matching/tests` -> 144 passed, 2 skipped (opt-in real-model tests)
- `RUN_REAL_MODEL_TESTS=1 … pytest ai_matching/tests/test_real_model.py` (offline, all-MiniLM-L6-v2) -> 2 passed
- `python manage.py test apps` -> 81 tests, OK
- `bandit -r ai_matching apps/matching -ll -ii` -> no issues reported
- Live smoke test, real model + synthetic test-only config: excluded candidate never ranked; model loaded once (~19 s), reused (~0.05 s)

**Blocked, dependencies and decisions needed**
- D-04 criteria / D-05 weights - waiting on BNCS (Gate 2, 20 Nov) - since 2026-10-26 - decision register
- D-11 model selected by me 2026-11-19 - needs Ajendra review and Aryan's ARCHITECTURE.md §9 record - since 2026-11-19
- Rules-only fallback conflict - waiting on Aryan → mentor/BNCS - since 2026-11-16 - [EVALUATION_AND_FALLBACK_DESIGN.md](../ai/EVALUATION_AND_FALLBACK_DESIGN.md)
- MatchRun/MatchResult models + persister - waiting on Vishal - since 2026-11-16 - not yet raised in channel

**Next week**
- Evaluation set with Harish; DRF matching endpoints with Abhishek - M6-AC7



## 2026-11-04 · Wed · Week 2



**Completed**

- Aligned C7 AI Matching architecture and documentation across the repository — drafted — [AGENTS.md](../../AGENTS.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [MVP_FEATURES.md](../MVP_FEATURES.md), [README.md](../../README.md), and [docs/ai/README.md](../ai/README.md)

- Formalized C7 two-component architecture (Django integration layer `backend/apps/matching/` + FastAPI AI matching engine `backend/ai_matching/`) and target folder structure

- Documented 9-step matching pipeline, mandatory eligibility hard gates, mandatory semantic matching, and explicit failure policy (no silent fallback)



**In progress**

- Scaffolding of Component A (`apps/matching/`) and Component B (`ai_matching/`) — M6 / M7 — awaiting phase start



**Tests and validation**

- `git diff --stat` → documentation updates verified with zero unrelated modifications



**Blocked, dependencies and decisions needed**

- D-11 (Embedding model selection) — waiting on mentor and team review — since 2026-10-26 — tracked in decision register

- D-15 (Matching engine deployment arrangement) — waiting on team confirmation — since 2026-10-26 — tracked in decision register

- D-03 / D-05 / D-06 (Mandatory eligibility criteria & scoring weights) — waiting on BNCS — since 2026-10-26 — tracked in decision register



**Next**

- Begin implementation scaffolding of `backend/apps/matching/` and `backend/ai_matching/` once authorized — M6, M7
