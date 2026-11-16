"""
Mandatory Eligibility Evaluation Service.

Evaluates mandatory criteria against supplier capabilities.
Hard-gate rule: any supplier failing ANY mandatory criterion is excluded from final ranking.
Unknown or missing criteria must not pass by default.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Structural Scaffolding — Week 4 work, not started.

NOTE ON ARCHITECTURE & DECISIONS:
# PENDING DECISION: D-04 (Mandatory eligibility criteria and handling of unknown values;
# MVP_FEATURES §12. Earlier docs mislabelled this as D-03, which is readiness questions.)
# Needs Gate 2 approval and an agreed mapping from criterion_key/operator to candidate
# fields (docs/ai/MATCHING_CONTRACT.md §6). No evaluation algorithms implemented here.
"""

