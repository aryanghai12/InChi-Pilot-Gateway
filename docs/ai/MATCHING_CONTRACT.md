# Django ↔ AI Matching Engine Contract

| | |
|---|---|
| **Contract version** | `0.2.0-proposed` (change log in §8) |
| **Status** | **Proposed.** Needs review by Abhishek (C5, orchestration and API) and Vishal (C6, data fields) before it is treated as agreed. Aryan records it in the interface register once agreed. |
| **Owner** | Alok Tiwari (C7) |
| **Code** | Engine: [`backend/ai_matching/schemas/`](../../backend/ai_matching/schemas/). Django: [`backend/apps/matching/schemas/`](../../backend/apps/matching/schemas/). Agreement is checked by [`apps/matching/tests/test_contract.py`](../../backend/apps/matching/tests/test_contract.py), including a full round trip through the real engine pipeline. |
| **Requirements** | MVP_FEATURES M6-AC1 to AC6, M5-AC1, M3-AC2; ARCHITECTURE.md §6 |

## 1. Boundary

- Django collects data, decides permissions and readiness, and persists results. The engine never reads or writes the database.
- Django sends **one self-contained request**: a requirement version, its criteria, the full candidate pool and the name of the scoring configuration (`criteria_version`).
- The engine returns either a **complete** result or an **error envelope**. A partial result is never returned, so none can be stored (M6-AC5).

```
Django (apps/matching)                                         FastAPI engine (ai_matching)
matching_service.run_matching
  ├─ request_builder.requirement_payload_from_model (BuyerRequirement, read-only)
  ├─ supplier_selector.build_candidate_payloads   (Products from C6's query)
  ├─ request_builder.build_matching_request
  ├─ ai_engine_client.match ──────── POST /match ───────────► config → prepare → eligibility
  │                          ◄── 200 MatchResponse | error ──┘   → embeddings → score → rank → explain
  └─ result_handler.persist_outcome (persister from C6 + audit event, one transaction)
```

## 2. Endpoints

| Method and path | Purpose | Success | Failure |
|---|---|---|---|
| `GET /health` | Liveness, contract version, provider, whether a model is configured. The model is **not** loaded by this call. | 200 | n/a |
| `POST /match` | Run matching for one requirement version | 200 `MatchResponse` | Error envelope (§5) |

Headers: `Content-Type: application/json`. Optional `X-Correlation-ID` (letters, digits, `-_.`, at most 100 characters), echoed in errors. There is no service-to-service authentication yet (O-3).

## 3. Request: `MatchRequest`

Unknown fields are rejected at every level. Decimals travel as strings or numbers. `null` means **unknown**, never zero (M3-AC2).

| Field | Type | Notes |
|---|---|---|
| `contract_version` | string | Must equal `0.2.0-proposed` |
| `correlation_id` | string ≤ 100 | Optional |
| `criteria_version` | string, required | Names the scoring configuration file `ai_matching/criteria/<criteria_version>.json` (§7). Django reads it from `MATCHING_CRITERIA_VERSION`. |
| `requirement` | `BuyerRequirementInput` | See below |
| `candidates` | list of `SupplierCandidateInput`, ≤ 1000 | `candidate_id` unique. An empty list is valid. |

**`BuyerRequirementInput`**, as mapped from `apps.demand.models.BuyerRequirement` by `requirement_payload_from_model`:

| Field | Source | Notes |
|---|---|---|
| `requirement_id`, `requirement_version` | `id`, `version` | |
| `title`, `product_category`, `target_market` | `requirement_title`, `product_category`, `target_market` | Normalised by the engine (e.g. `China` → `CN`) |
| `specification_text` | `product_specifications` | ≤ 5000 characters, otherwise refused before sending |
| `quantity_*`, `target_price_*`, `currency_code`, `price_basis`, `required_lead_time_*` | same names | |
| `delivery_country` | always `""` | `delivery_location` is free text; no country is derived from it |
| `mandatory_criteria[]` | `mandatory_criteria` | Structured entries pass through; free-text entries become `manual_review` (§6) |
| `preference_criteria[]` | `preferred_criteria` | Structured entries pass through; free-text entries are carried but never scored |
| `evidence_criteria[]` | `required_evidence` | `document_name`/`evidence_type`; `is_mandatory: false` → `preferred` |

**`SupplierCandidateInput`**: one product with its supplier (`backend/apps/registry/models.py` field names). The fields are `candidate_id` (the product ID), `supplier_id`, `supplier_name`, `supplier_country`, `supplier_record_status`, `supplier_industry_description` and `readiness_status` (null until M4). Then `product_name`, `product_category`, `description`, `specifications`, `origin`, the MOQ, price, capacity and lead-time values with their units, and `evidence[]`.

Bounds: short text ≤ 255, long text ≤ 5000, codes ≤ 100, ≤ 50 criteria per list, ≤ 50 evidence items per candidate (THREAT_MODEL T-DS-01).

## 4. Success response: `MatchResponse` (HTTP 200)

| Field | Notes |
|---|---|
| `contract_version`, `status` | `status` is always `completed` on 200 |
| `mode` | `hybrid` (the only mode; see O-2) |
| `requirement_id`, `requirement_version`, `criteria_version` | Traceability (M6-AC6) |
| `configuration_status` | `approved`, or `unapproved` (only when the engine runs with `MATCHING_ALLOW_UNAPPROVED_CONFIG=true`) |
| `embedding_model_id` | Model actually used, e.g. the value of `EMBEDDING_MODEL_NAME` (M6-AC6) |
| `embedding_text_template_version` | `embedding-text-v0` ([PREPROCESSING.md](PREPROCESSING.md)) |
| `ranked[]` | Eligible only. Ranks 1..n in order, each with `scores`. |
| `excluded[]` | Failed a mandatory criterion. No rank, no scores (M6-AC1). |
| `insufficient_data[]` | A mandatory criterion could not be confirmed. No rank, no scores (M6-AC2). |
| `run_warnings[]` | E.g. the unapproved-configuration label, or "no eligible candidates" (M6-AC4) |
| `metrics` | Counts only |

Each result has:
- `candidate_id`, `supplier_id`, `eligibility`, `rank` and `readiness_status`.
- `criteria[]`: `{criterion_key, operator, outcome: pass|fail|insufficient_data, detail}`.
- `scores` (ranked only):
  - `rule_score`: in [0, 1], or `null` when no preference could be scored.
  - `semantic_cosine` in [−1, 1]; `semantic_score`, `hybrid_score`, `rule_weight` and `semantic_weight` in [0, 1].
  - `contributions[]`: `{preference_key, weight_key, weight, outcome: satisfied|not_satisfied|insufficient_data|not_scored, contribution, detail}`.
- `explanation[]`: deterministic sentences ending with the decision-support note.
- `warnings[]`: `{flag, field, message}`.

Ranking is `hybrid_score` DESC, then `rule_score` DESC, `supplier_id` ASC, `candidate_id` ASC. There is no minimum-score threshold.

Django rejects any 200 body that breaks these rules (an ineligible candidate with a rank or scores, ranks that aren't 1..n, out-of-range scores, an unknown outcome or status) as `invalid_matching_payload`.

## 5. Errors

Every non-2xx response uses the project envelope `{"code", "message", "field_errors", "correlation_id"}` (ARCHITECTURE.md §5).

| HTTP | `code` | When |
|---|---|---|
| 422 | `validation_error` | Contract violation, or an invalid structured criterion or preference. `field_errors` keys are paths such as `requirement.mandatory_criteria.0`. Values are never echoed. |
| 503 | `stage_not_available` | Stage `scoring`: the configuration is missing, unapproved, or has no weights or mapping. Stage `semantic`: `EMBEDDING_PROVIDER=none`. **With the committed `v0-UNAPPROVED` configuration every request ends here.** |
| 503 | `embedding_generation_failed` | Library missing, model not available locally, or inference failed |
| 500 | `similarity_computation_failed`, `engine_configuration_error`, `pipeline_execution_failed`, `internal_error` | Engine or configuration fault |

On the Django side, `run_matching()` turns every engine-side failure into a **failed `MatchRunOutcome` with no results**. The failure types are `MatchingEngineResponseError`, `MatchingEngineTimeoutError`, `MatchingEngineConnectionError` and a contract-violating `InvalidMatchingPayloadError`. Caller errors raise `InvalidMatchingPayloadError` and never become a run: a requirement that isn't ready or has blockers (M5-AC2), or a missing criteria version.

## 6. Comparison vocabulary (PROPOSED, needs D-04 approval of its use)

This defines **how** a criterion is evaluated, not **which** criteria apply. Criteria come from the requirement.

| `criterion_key` | Candidate field (normalised) | Operators | `value` object |
|---|---|---|---|
| `product_category`, `origin_country`, `supplier_country`, `supplier_record_status` | coded value | `equals`, `not_equals`, `in` | `{"value": "IN"}` or `{"value": ["IN", "AE"]}` |
| `moq`, `lead_time` | value + unit | `equals`, `lte`, `gte` | `{"value": 500, "unit": "KG"}` |
| `capacity` | value + unit (+ period) | `equals`, `lte`, `gte` | `{"value": 5000, "unit": "PIECES", "period": "MONTH"}` |
| `price_min`, `price_max` | price + currency | `equals`, `lte`, `gte` | `{"value": 20, "currency": "USD"}` |
| `required_evidence` (generated from `evidence_criteria` with `classification=mandatory`) | recorded evidence types | `includes_all` | n/a |
| any `manual_review_N` | none | `manual_review` | `{"text": "<free text>"}` |

The comparison is `candidate_field <operator> value`. Outcomes:
- **Unknown candidate value**, unit or currency mismatch (no conversion), capacity-period mismatch, unrecorded evidence, or a `manual_review` criterion → `insufficient_data`. **Never a pass.**
- **False comparison** → `fail`.
- **Per candidate:** any `fail` → `excluded`; otherwise any `insufficient_data` → `insufficient_data`; otherwise `eligible`.

A structured criterion with an unknown key, an unsupported operator or a bad value fails the run with 422, rather than being guessed.

**Preferences** use the same vocabulary, with the operator inside `value`: `{"preference_key": "lead_time", "value": {"operator": "lte", "value": 45, "unit": "DAYS"}, "weight_key": "lead_time"}`. A preference without an operator, or whose `weight_key` has no approved weight, is `not_scored` and never affects the result.

## 7. Scoring configuration (D-05)

`ai_matching/criteria/<version>.json`:

```json
{"version": "…", "status": "approved|unapproved", "approved_by": "", "approved_at": "", "decision_refs": [],
 "hybrid_weights": {"rule": 0.0, "semantic": 0.0}, "preference_weights": {"<weight_key>": 0.0},
 "semantic_score_mapping": "clamp_negative_to_zero | linear_rescale"}
```

- `rule_score = Σ(weightᵢ × satisfiedᵢ) / Σ weightᵢ` over scorable preferences. If no preference is scorable, `rule_score = null` and `hybrid = semantic_score`. That's ranking-equivalent, because it applies to every candidate equally.
- `hybrid = w_rule × rule_score + w_semantic × semantic_score`. The two weights must sum to 1.
- The engine refuses (503) a configuration that is unapproved, unless `MATCHING_ALLOW_UNAPPROVED_CONFIG=true` (then every response is labelled), or that lacks weights or a mapping.
- **The committed `v0-UNAPPROVED.json` deliberately has no weights.** BNCS-approved values go in through a reviewed PR (MVP_FEATURES §5).

## 8. Change log

| Version | Change |
|---|---|
| 0.1.0-proposed | Initial contract (Weeks 1–3) |
| 0.2.0-proposed (19 Nov 2026) | `rule_score` nullable. Added `semantic_cosine`, `rule_weight` and `semantic_weight`; typed `contributions` (weight, outcome, detail); `criteria[].operator`; `configuration_status`; `run_warnings`. `criteria_version` now names the engine scoring-configuration file. |

Breaking changes bump `contract_version` on both sides in the same PR, reviewed by Abhishek (and by Vishal for data fields). `test_contract.py` must keep passing.

## 9. Open items

| ID | Item | Needs |
|---|---|---|
| O-1 | Approval to use the §6 vocabulary for real criteria; how the UI stores structured criteria. The frontend currently saves free-text `{id, name, type}` entries, which can only become `manual_review`, so **no real requirement can make a candidate eligible on a free-text criterion.** | Adrika drafts the criteria; BNCS approves (D-04, Gate 2); Priyanka and Abhishek store structured entries |
| O-2 | Rules-only fallback conflict (Build Manual vs M6-AC5). The current implementation has no fallback. | Aryan → mentor and BNCS ([EVALUATION_AND_FALLBACK_DESIGN.md](EVALUATION_AND_FALLBACK_DESIGN.md)) |
| O-3 | Django → engine authentication and network exposure | Ajendra, Abhishek |
| O-4 | **Resolved for the backend model:** the specification text is `BuyerRequirement.product_specifications` | n/a |
| O-5 | Product certifications: no structured field; only inferable from evidence metadata | Vishal, Adrika |
| O-6 | Engine deployment (open PR #71 runs it as its own `matching` Compose service). Needs a correctly numbered §9 entry (ARCHITECTURE.md §6.3 says "D-15"). | Team and mentor; Aryan records |
| O-7 | `MatchRun` / `MatchResult` models and a `MatchRunPersister` implementation for `result_handler.persist_outcome()` | Vishal |
| O-8 | `audit.services.record_event` swallows its own exceptions, so an audit failure doesn't roll back the run transaction | Abhishek, Ajendra |
| O-9 | D-11 model recorded in ARCHITECTURE.md §9, and the semantic image/dependency (PyTorch size, licences) reviewed | Aryan, Ajendra |
