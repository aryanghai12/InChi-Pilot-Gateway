# Preprocessing, Normalisation and Embedding-Ready Records (Stage 1)

| | |
|---|---|
| **Status** | Implemented (Week 3). Rules are technical normalisation only, not business rules. |
| **Owner** | Alok Tiwari (C7) |
| **Code** | [`backend/ai_matching/services/preprocessing.py`](../../backend/ai_matching/services/preprocessing.py), tests in [`test_preprocessing.py`](../../backend/ai_matching/tests/test_preprocessing.py) |

## 1. Principles

1. **Unknown stays unknown.** A missing value is `None`, never zero or a default (M3-AC2). An unrecognised code becomes `None` with a quality flag. Nothing is guessed.
2. **No conversion.** Quantity units are never converted (BUY-D05), and neither are currencies (BUY-D07).
3. **Flags inform; they never decide.** Quality flags feed missing-information warnings (M6-AC3). Eligibility is decided only in Stage 2, after D-04.
4. **Deterministic.** The same input always gives the same output and the same hash.

## 2. Text

`normalise_text`: Unicode NFKC, control and format characters replaced by spaces, whitespace collapsed, trimmed. Lengths are bounded by the request schema, so text is rejected rather than silently truncated.

## 3. Codes

Matching is case- and separator-insensitive (`"metric tonnes"`, `"Metric-Tonnes"` and `"METRIC_TONNES"` are all the same token).

| Field | Canonical codes | Source of codes |
|---|---|---|
| Quantity unit (MOQ, capacity, requirement quantity) | `MT`, `KG`, `PIECES`, `BOXES`, `CONTAINERS` | `registry.QuantityUnit` and the `ProductSerializer` aliases |
| Lead-time unit | `DAYS`, `WEEKS`, `MONTHS` | `registry.LeadTimeUnit`. The demand seed's lowercase `days` maps to `DAYS`. |
| Capacity period | `MONTH`, `QUARTER`, `YEAR` | `registry.CapacityPeriod` |
| Country (origin, supplier, market, delivery) | `IN`, `CN`, `AE` | Registry serializer (India, China) and the demand seed markets |
| Category | `AGRI_FOOD`, `TEXTILES`, `ENGINEERING`, `ELECTRONICS`, `CHEMICALS`, `MINERALS`, `MARINE` | **Provisional.** Mirrors the demand seed `ReferenceValue` (BUY-D04, D-02 open). Accepts the codes and the display names, including the frontend spelling "Minerals & Metals". |
| Currency | Any three-letter alphabetic code | ISO 4217 shape only |
| Evidence type | Upper-case token, e.g. `QUALITY_CERTIFICATE` | Demand seed `evidence_type` |

`ton` is deliberately **not** mapped, because it is ambiguous between metric and short tons.

**Known cross-module mismatches this resolves:**
- Registry `Product.origin` holds free text (default `"India"`), while the demand criteria use `IN`.
- Registry `product_category` is free text, while the demand schema uses codes.
- Registry lead-time units are `DAYS`, while the demand seed uses `days`.

The lasting fix is controlled values at the source (Vishal and Adrika).

## 4. Quality flags

| Flag | Raised when |
|---|---|
| `missing_value` | A matched field is absent (category, origin, supplier country, MOQ, capacity, lead time, price range, requirement quantity) |
| `missing_unit` | A numeric value has no unit |
| `unrecognised_unit` / `unrecognised_country` / `unrecognised_category` / `unrecognised_currency` | A value is present but not a known code |
| `incomplete_range` | Only one price bound is given |
| `no_descriptive_text` | No description or specifications (candidate), or no title or specification (requirement) |

Optional requirement fields (target market, delivery country, lead time) are flagged only when present but unrecognised.

## 5. Embedding-ready records

Template `embedding-text-v0`: labelled lines, empty fields omitted, joined by newlines.

| Record | Lines, in order |
|---|---|
| Candidate | `Product`, `Category` (code if recognised, else raw), `Description`, `Specifications`, `Supplier capability` (supplier industry description) |
| Requirement | `Requirement` (title), `Category`, `Specification` |

Numeric and commercial fields (MOQ, price, currency, capacity, lead time) are excluded. Those are matched by rules, not by semantic similarity.

`source_hash = SHA-256("embedding-text-v0\n" + text)`. It matches TD-01's `embedding_source_hash`: Vishal's stored embedding can be reused while the hash is unchanged and must be regenerated when it changes. Whitespace-only edits don't change the hash. Changing the template means bumping the version, which changes every hash.

English only; multilingual is Phase 2 (DS-11). Mandarin fields are not embedded.

## 6. Open

- Which demand field holds the free-text specification ([MATCHING_CONTRACT.md](MATCHING_CONTRACT.md) O-4).
- The final category list (D-02, BUY-D04). When Vishal's `ReferenceValue` becomes authoritative in the backend, the alias table should be replaced by values passed in or loaded from it.
- Readiness-rule inputs (Week 3 timeline duty) can't be normalised yet: the readiness module (M4) and its questions (D-03) don't exist. `readiness_status` travels as an opaque value.
