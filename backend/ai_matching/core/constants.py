"""
Engine Constants and Status Enumerations.

Shared, non-business constants for the FastAPI AI Matching Engine: the contract
version, status vocabularies, quality-flag codes and technical payload bounds.

Author: Alok Tiwari (C7 — AI Matching and Data Intelligence Engineer)
Architecture: Component B (FastAPI AI Matching Engine)
Status: Week 2–3 foundation. Contract is PROPOSED (docs/ai/MATCHING_CONTRACT.md).

NOTE ON ARCHITECTURE & DECISIONS:
# Nothing in this module is a business rule. Eligibility criteria (D-04),
# preference weights and the semantic weight (D-05) are NOT defined here.
# The payload bounds below are technical limits (THREAT_MODEL T-DS-01), not
# commercial policy, and can be changed by the C7 owner with Ajendra's review.
"""

from enum import Enum

# Django <-> engine contract version. Bump on any breaking change and record it
# in docs/ai/MATCHING_CONTRACT.md. "-proposed" until Abhishek (C5) agrees it.
CONTRACT_VERSION = "0.1.0-proposed"

# Version of the deterministic text template used to build embedding-ready
# records (docs/ai/PREPROCESSING.md). Stored with every embedding hash.
EMBEDDING_TEXT_TEMPLATE_VERSION = "embedding-text-v0"

SERVICE_NAME = "inchi-ai-matching"


class RunStatus(str, Enum):
    """Match run status (MVP_FEATURES M6 simplifications)."""

    COMPLETED = "completed"
    FAILED = "failed"


class EligibilityOutcome(str, Enum):
    """Per-candidate eligibility outcome (M6-AC1, M6-AC2)."""

    ELIGIBLE = "eligible"
    EXCLUDED = "excluded"
    INSUFFICIENT_DATA = "insufficient_data"


class CriterionOutcome(str, Enum):
    """Per-criterion outcome. Unknown is never a pass (M6-AC2)."""

    PASS = "pass"
    FAIL = "fail"
    INSUFFICIENT_DATA = "insufficient_data"


class MatchingMode(str, Enum):
    """
    Matching mode recorded on every run (M6-AC6).

    Only HYBRID is defined. Whether a labelled rules-only mode is allowed is an
    open conflict between the Build Manual and MVP_FEATURES M6-AC5
    (docs/ai/EVALUATION_AND_FALLBACK_DESIGN.md). Do not add a value until decided.
    """

    HYBRID = "hybrid"


class QualityFlag(str, Enum):
    """
    Data-quality flags raised during preprocessing (Stage 1).

    Flags are informational. They never decide eligibility; they feed the
    missing-information warnings shown to reviewers (M6-AC3).
    """

    MISSING_VALUE = "missing_value"
    MISSING_UNIT = "missing_unit"
    UNRECOGNISED_UNIT = "unrecognised_unit"
    UNRECOGNISED_CURRENCY = "unrecognised_currency"
    UNRECOGNISED_COUNTRY = "unrecognised_country"
    UNRECOGNISED_CATEGORY = "unrecognised_category"
    INCOMPLETE_RANGE = "incomplete_range"
    NO_DESCRIPTIVE_TEXT = "no_descriptive_text"


# ---------------------------------------------------------------------------
# Technical payload bounds (THREAT_MODEL T-DS-01: AI processing exhaustion).
# Pilot volume is >=30 products, "at most hundreds" (ARCHITECTURE.md §2).
# ---------------------------------------------------------------------------
MAX_CANDIDATES_PER_REQUEST = 1000
MAX_SHORT_TEXT_LENGTH = 255
MAX_LONG_TEXT_LENGTH = 5000
MAX_CODE_LENGTH = 100
MAX_CRITERIA_PER_REQUIREMENT = 50
MAX_EVIDENCE_ITEMS_PER_CANDIDATE = 50
