# Weekly reports — Alok Tiwari



AI Matching and Data Intelligence Engineer · Process, template and rules: [README.md](README.md)



Only Alok Tiwari writes in this file. Newest entry first.



<!-- Add new entries directly below this line. -->

## Week 4 - 16-20 November 2026

_Draft prepared with an AI coding agent on 2026-11-16; to be checked and completed after the Friday sprint review._

**Completed**
- C7 Week 1–3 backlog: engine contract schemas, FastAPI app (`/health`, `/match`), config, exceptions, Stage 1 preprocessing/normalisation, quality flags, embedding-ready records, provider interface (`none` only), cosine similarity - drafted (uncommitted) - [backend/ai_matching/](../../backend/ai_matching/)
- Django integration layer: request/response schemas, request builder, candidate mapping, HTTP client, typed exceptions - drafted (uncommitted) - [backend/apps/matching/](../../backend/apps/matching/)
- Contract v0.1.0-proposed, preprocessing rules, D-11 shortlist, evaluation and fallback design; corrected decision IDs in docs/ai - drafted (uncommitted) - [docs/ai/](../ai/)

**Meetings, reviews and coordination**
- None.

**In progress**
- Contract review with Abhishek (orchestration/API) and Vishal (data fields) - M6-AC6 - [MATCHING_CONTRACT.md](../ai/MATCHING_CONTRACT.md) not yet reviewed

**Tests and validation**
- `python -m pytest ai_matching/tests` (from `backend/`) -> 63 passed
- `python manage.py test apps` (from `backend/`) -> 60 tests, OK (22 existing + 38 new matching tests)
- `bandit -r ai_matching apps/matching -ll -ii` -> no issues reported
- Manual smoke test: engine under uvicorn, called by the Django client -> `/health` ok; `/match` returned 503 `stage_not_available` (expected until D-04)

**Blocked, dependencies and decisions needed**
- D-04 eligibility criteria / D-05 weights - waiting on BNCS (Gate 2) - since 2026-10-26 - tracked in decision register
- D-11 embedding model - waiting on Ajendra review and decision - since 2026-10-26 - shortlist in docs/ai
- Rules-only fallback conflict (Build Manual vs M6-AC5) - waiting on Aryan → mentor/BNCS - since 2026-11-16 - [EVALUATION_AND_FALLBACK_DESIGN.md](../ai/EVALUATION_AND_FALLBACK_DESIGN.md)
- MatchRun/MatchResult models and demand-schema merge into backend - waiting on Vishal - since 2026-11-16 - not yet raised in channel

**Next week**
- Eligibility engine and weighted-score baseline once D-04/D-05 are approved - M6-AC1, M6-AC2



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
