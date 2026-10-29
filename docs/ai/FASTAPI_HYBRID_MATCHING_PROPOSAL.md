# Proposal: FastAPI Microservice for Hybrid AI Matching

## Objective
Propose a separate FastAPI microservice for the AI matching component owned by C7 – AI Matching and Data Intelligence Engineer.

This is an architecture proposal only. It does not change the existing implementation or project requirements.

## Proposed Changes

### 1. Dedicated Matching Service
Run the matching engine as an independent FastAPI service instead of keeping it inside the Django backend.

### 2. Hybrid Matching
Combine two approaches:
- **Rule-based matching:** Apply mandatory eligibility filters and business rules.
- **Semantic matching:** Use embedding-based similarity as an additional ranking signal to identify semantically relevant matches.

### 3. Explainable Results
Return match scores, matched criteria, unmet requirements, and reasons supporting the ranking.

### 4. Rules-Only Fallback
Allow matching to run without semantic similarity if the semantic component is disabled or unavailable. Clearly identify when fallback is used.

### 5. Django–FastAPI Integration
Define a clear API contract between the Django backend and the FastAPI matching service, including request/response formats, timeouts, and error handling.

### 6. Evaluation
Evaluate matching quality before enabling semantic matching by default. The embedding model and evaluation criteria remain subject to a separate technical decision.

## Important Constraints
- Mandatory eligibility failures must never be overridden by semantic scores.
- Unknown mandatory information must not be treated as a pass.
- Final decisions remain with authorized human reviewers.
- No external LLM or hosted embedding dependency is proposed as part of this change.

## Expected Benefits
- Separation of backend orchestration and matching logic.
- Independent testing and deployment of the matching service.
- Easier experimentation with matching strategies.
- Improved explainability and maintainability.

## Open for Review
This proposal requires review and approval from the relevant project owners before implementation. Existing architecture and business rules remain unchanged until approval.
