# Decision Boundary, Evaluation and Fallback Design

| | |
|---|---|
| **Status** | Week 1 design. **Fallback policy: OPEN conflict, needs a decision.** |
| **Owner** | Alok Tiwari (C7). Evaluation cases are built with Harish (C8). |
| **Requirements** | MVP_FEATURES §7, M6-AC5, M6-AC7, M11-AC8; Build Manual Component 2 DoD |

## 1. Decision boundary

| The engine may | The engine must not |
|---|---|
| Normalise data, flag missing information | Approve, reject or hold a supplier (M7-AC4) |
| Mark candidates eligible, excluded or insufficient data against **approved** criteria | Treat unknown mandatory data as a pass (M6-AC2) |
| Score and rank eligible candidates with **approved** weights | Let similarity override a mandatory failure (M6-AC1) |
| Explain each result deterministically | Create opportunities, interpret law or regulation, present scores as certainty |
| Fail explicitly | Return partial or silently degraded results |

Authorised humans record every disposition in M7.

## 2. Fallback policy: open conflict

| Source | Says |
|---|---|
| Build Manual, Component 2 Definition of Done | "A deterministic rules-only fallback remains available and documented." Week 5 exit: "including the rules-only fallback." |
| Revised ownership PDF (Alok's role) | "…evaluation cases, **fallback** and model limitations." Week 6: "fallback telemetry." |
| MVP_FEATURES M11-AC8 | Evidence must cover "deterministic rules-only fallback" |
| MVP_FEATURES M6-AC5, §7; ARCHITECTURE.md §1, §6; AGENTS.md C7 | "Semantic matching is mandatory… No silent fallback to rules-only matching is permitted." |
| ARCHITECTURE.md §1 runtime notes, §2, D-11 | "The default build runs rules-only… which is the required fallback." |

**Current implementation:** semantic failure fails the run explicitly. This follows M6-AC5 as written today. The `MatchingMode` enum has only `hybrid`.

**Options for the decision.** These are not chosen.

| Option | Behaviour | Fits |
|---|---|---|
| A. No fallback (current) | Any semantic failure gives a failed run | M6-AC5 as written; conflicts with the Build Manual and M11-AC8 |
| B. Explicit, labelled rules-only mode | Semantic failure still fails a `hybrid` run. A user or config may *request* `rules_only`, which is recorded as `mode=rules_only` and shown in the UI. Never automatic, never silent. | The Build Manual ("available and documented") and M6-AC5's "no **silent** fallback" |
| C. Automatic labelled fallback | Semantic failure switches to `rules_only` with a visible label | The Build Manual, but contradicts M6-AC5 |

**Needed:** Aryan takes this to the mentor and BNCS. Then update MVP_FEATURES M6-AC5, ARCHITECTURE.md §6 and this file together. Option B can be added later as a contract extension, since adding an enum value is backward-compatible.

## 3. Evaluation design (M6-AC7, M11-AC8)

The synthetic evaluation set is built with Harish. Expected outcomes are written **before** a run and can't be changed after it.

| Case type | Purpose | Expected outcome source |
|---|---|---|
| Expected match | Correct candidate ranks in the expected band | Approved criteria and weights (D-04, D-05) |
| False match | Semantically similar but fails a mandatory criterion | `excluded`, never ranked |
| Missed match | Relevant candidate with different wording | Ranked; tests the semantic signal |
| Missing data | Unknown mandatory value | `insufficient_data` with a warning |
| Manipulated input | Keyword stuffing, oversized text, unknown fields, out-of-range numbers | Rejected (422) or no unfair gain |
| Service failure | Provider or engine down, timeout | Failed run, no results (already tested) |
| Fallback | Per the §2 decision | TBD |

Results record the engine contract version, criteria version, embedding model ID and template version. No accuracy claim goes beyond the set.

**Already covered by tests:** contract validation and manipulated-input rejection (422, no echoed values), service failure (timeout, unreachable, error envelope, invalid JSON), and explicit failure at the unapproved eligibility stage.
