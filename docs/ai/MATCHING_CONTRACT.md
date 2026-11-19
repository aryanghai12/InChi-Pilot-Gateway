# Django ↔ AI Matching Engine Contract

| | |
|---|---|
| **Contract version** | `0.1.0-proposed` |
| **Status** | **Proposed.** Needs review by Abhishek (C5, orchestration and API) and Vishal (C6, data fields) before it is treated as agreed. Recorded in the interface register by Aryan once agreed. |
| **Owner** | Alok Tiwari (C7) |
| **Code** | Engine: [`backend/ai_matching/schemas/`](../../backend/ai_matching/schemas/). Django: [`backend/apps/matching/schemas/`](../../backend/apps/matching/schemas/). Agreement is checked by [`apps/matching/tests/test_contract.py`](../../backend/apps/matching/tests/test_contract.py). |
| **Requirements** | MVP_FEATURES M6-AC1 to AC6, M5-AC1, M3-AC2; ARCHITECTURE.md §6 |

## 1. Boundary

- Django collects data, decides permissions and readiness, and persists results. The engine never reads or writes the database.
- Django sends **one self-contained request**: a requirement version, its criteria and the full candidate pool.
- The engine either returns a **complete** result or an **error envelope**. A partial result is never returned, so none can be stored (M6-AC5).

```
Django (apps/matching)                               FastAPI engine (ai_matching)
supplier_selector ─► request_builder ─► ai_engine_client ──POST /match──► schemas → pipeline
                                         ◄── 200 MatchResponse | non-2xx error envelope ──┘
```

## 2. Endpoints

| Method and path | Purpose | Success | Failure |
|---|---|---|---|
| `GET /health` | Liveness, contract version, whether a model is configured | 200 | n/a |
| `POST /match` | Run matching for one requirement version | 200 `MatchResponse` | Error envelope (§5) |

Headers: `Content-Type: application/json`. Optional `X-Correlation-ID` (letters, digits, `-_.`, at most 100 characters), which the engine echoes in errors. Django forwards the request's correlation ID.

There is no service-to-service authentication yet (open item O-3).

## 3. Request: `MatchRequest`

Unknown fields are rejected at every level. Decimal values travel as JSON strings or numbers. `null` means **unknown**, never zero (M3-AC2).

| Field | Type | Notes |
|---|---|---|
| `contract_version` | string | Must equal `0.1.0-proposed` |
| `correlation_id` | string ≤ 100 | Optional |
| `criteria_version` | string, required | Version of the matching configuration the criteria come from (M6-AC6) |
| `requirement` | `BuyerRequirementInput` | See below |
| `candidates` | list of `SupplierCandidateInput`, ≤ 1000 | `candidate_id` unique. An empty list is valid. |

**`BuyerRequirementInput`.** Field names follow `database/apps/demand/models.py`.

| Field | Type | Source (C6 demand schema) |
|---|---|---|
| `requirement_id` | string | `BuyerRequirement.requirement_id` |
| `requirement_version` | int ≥ 1 | `BuyerRequirementVersion.version` |
| `title`, `product_category`, `target_market` | string | `BuyerRequirement` |
| `specification_text` | string ≤ 5000 | **Open (O-4):** which stored field carries free-text specification |
| `quantity_value`, `quantity_unit` | decimal > 0 or null, string | `RequirementQuantity` |
| `target_price_min/max`, `currency_code`, `price_basis` | decimal or null, string | `RequirementCommercialTerms` |
| `delivery_country`, `required_lead_time_value/unit` | string, int > 0 or null | `RequirementDelivery` |
| `mandatory_criteria[]` | `{criterion_key, operator, value{}, unknown_policy}` | `RequirementEligibilityCriterion` |
| `preference_criteria[]` | `{preference_key, value{}, weight_key}` | `RequirementPreference`. **No weight values.** |
| `evidence_criteria[]` | `{evidence_type, classification}` | `RequirementEvidenceCriterion` |

Mandatory criteria and preferences are separate lists (M5-AC1). The engine does **not** define which `criterion_key` or `operator` values exist (open item O-1).

**`SupplierCandidateInput`.** One product with its supplier. Field names follow `backend/apps/registry/models.py`.

`candidate_id` (product ID), `supplier_id`, `supplier_name`, `supplier_country`, `supplier_record_status`, `supplier_industry_description`, `readiness_status` (null until M4 exists), `product_name`, `product_category`, `description`, `specifications`, `origin`, `moq_value`/`moq_unit`, `price_min`/`price_max`/`currency`/`price_basis`, `capacity_quantity`/`capacity_unit`/`capacity_period`, `lead_time_value`/`lead_time_unit`, `evidence[]` (`{document_type, presence_status, review_status, expiry_date}`).

Bounds: short text ≤ 255, long text ≤ 5000, codes ≤ 100, ≤ 50 criteria per list, ≤ 50 evidence items per candidate (THREAT_MODEL T-DS-01).

## 4. Success response: `MatchResponse` (HTTP 200)

| Field | Notes |
|---|---|
| `contract_version`, `status` | `status` is always `completed` on 200 |
| `mode` | `hybrid`. Whether a labelled rules-only mode exists is open (O-2). |
| `requirement_id`, `requirement_version`, `criteria_version` | Echoed for traceability (M6-AC6) |
| `embedding_model_id`, `embedding_text_template_version` | Model ID and version used (M6-AC6) |
| `ranked[]` | Eligible candidates only. Each has `rank ≥ 1` and `scores`. |
| `excluded[]` | Failed a mandatory criterion. No rank, no scores (M6-AC1). |
| `insufficient_data[]` | Unknown on a mandatory criterion. No rank (M6-AC2). |
| `metrics` | Counts only |

Each result: `candidate_id`, `supplier_id`, `eligibility` (`eligible` / `excluded` / `insufficient_data`), `rank`, `criteria[]` (`{criterion_key, outcome: pass|fail|insufficient_data, detail}`), `scores` (`rule_score`, `semantic_score`, `hybrid_score` in [0, 1], `contributions[]`), `explanation[]`, `warnings[]` (`{flag, field, message}`), `readiness_status`.

Zero eligible candidates is a valid response (M6-AC4). How scores are computed is **not** part of this contract; it depends on D-05.

Django rejects any 200 body that breaks these rules, for example an excluded candidate with a rank, as `invalid_matching_payload`.

## 5. Errors

Every non-2xx response uses the project envelope (ARCHITECTURE.md §5):

```json
{"code": "stage_not_available", "message": "…", "field_errors": {}, "correlation_id": "…"}
```

| HTTP | `code` | Meaning |
|---|---|---|
| 422 | `validation_error` | Contract violation. `field_errors` keys are paths such as `candidates.0.moq_value`. Submitted values are never echoed. |
| 503 | `stage_not_available` | A required stage has no approved rules or model. **Currently returned for every valid request** (eligibility, D-04). |
| 503 | `embedding_generation_failed` | Embedding provider unavailable or failed |
| 500 | `similarity_computation_failed`, `pipeline_execution_failed`, `engine_configuration_error`, `internal_error` | Engine fault |

Django maps these to typed exceptions in `apps/matching/exceptions/`:

| Django exception | `code` | Raised when |
|---|---|---|
| `MatchingEngineResponseError` | `matching_engine_rejected` | Any engine error envelope. Carries `status_code` and `engine_code`. |
| `MatchingEngineTimeoutError` | `matching_engine_timeout` | No answer within `MATCHING_ENGINE_TIMEOUT_SECONDS` |
| `MatchingEngineConnectionError` | `matching_engine_unavailable` | Unreachable or misconfigured URL |
| `InvalidMatchingPayloadError` | `invalid_matching_payload` | Bad request built, or a 200 body that breaks the contract |

Every one of these means the run failed and **no results** are stored (M6-AC5).

## 6. Open items

| ID | Item | Needs |
|---|---|---|
| O-1 | Mapping from `criterion_key` / `operator` to candidate fields, and how `unknown_policy` relates to "insufficient data". The seed uses `origin_country equals IN` with `unknown_policy=exclude`, but M6-AC2 requires unknown to give `insufficient_data`, not `excluded`. | Adrika drafts, BNCS approves (D-04, Gate 2) |
| O-2 | Rules-only fallback: the Build Manual requires one, MVP_FEATURES M6-AC5 forbids it | Aryan → mentor and BNCS ([EVALUATION_AND_FALLBACK_DESIGN.md](EVALUATION_AND_FALLBACK_DESIGN.md)) |
| O-3 | Django → engine authentication and network exposure | Ajendra, Abhishek |
| O-4 | Which demand field carries free-text specification (`requirement_notes`, `RequirementSpecification.attributes`, or a new field) | Vishal, Adrika |
| O-5 | Product certifications: no structured field exists, so they are only inferable from evidence metadata | Vishal, Adrika |
| O-6 | Engine deployment: same container as Django or separate (`FASTAPI_MATCHING_URL=http://backend:8001` assumes the same container) | Team and mentor. ARCHITECTURE.md §6.3 labels this "D-15", but D-15 is a different business decision. |

## 7. Change rule

Breaking changes bump `contract_version` on both sides in the same PR and are reviewed by Abhishek, and by Vishal when data fields change (ARCHITECTURE.md §4.3). `test_contract.py` must keep passing.
