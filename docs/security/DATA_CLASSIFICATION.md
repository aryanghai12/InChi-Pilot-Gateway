# Data Classification & Protection Policy — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Working Baseline (v0.1) |
| **Authority** | [`../MVP_FEATURES.md`](../MVP_FEATURES.md) §6, §8; [`../../AGENTS.md`](../../AGENTS.md) §B rule 7 |
| **Reviewers** | Vishal Chauhan (Data), Abhishek Kumar (Backend) |

---

## 1. Classification Tiers & Definitions

To guarantee least-privilege data handling and prevent data leakage, data handled by InChi Pilot Gateway is classified into four operational tiers:

| Classification Tier | Definition | Handling & Protection Rules |
|---|---|---|
| **Tier 1: Public** | Information intended for public distribution. | Not applicable to v0.1 pilot data. Only unauthenticated assets (system login page, favicon, static public logos) belong here. |
| **Tier 2: Internal** | Information for internal BNCS operational use. Available to authorized users according to their assigned roles. | Accessible only over authenticated sessions. Transmission protected by TLS in staging. Must never be exposed to unauthenticated endpoints. |
| **Tier 3: Confidential** | Sensitive internal data including authentication secrets, password hashes, session keys, and strategic commercial opportunity notes. | Strong hashing (PBKDF2 for passwords); `HttpOnly` and `SameSite` flags for session tokens; strict field-level redaction in logs and error responses. |
| **Tier 4: Prohibited** | Real personal identifiable information (PII), real passport/national IDs, proprietary trade secrets, live production credentials. | **STRICTLY PROHIBITED in the repository and pilot database.** Only synthetic, anonymized, or approved mock data may be ingested. |

---

## 2. Entity-Level Data Classification Matrix

Mapping of all 15 core entities defined in [`docs/MVP_FEATURES.md §6`](../MVP_FEATURES.md#6-core-data-entities):

| # | Entity | Description & Key Fields | Sensitivity Tier | Access Restrictions | Logging & Masking Rules |
|---|---|---|---|---|---|
| 1 | **User** | `id`, `email`, `role`, `password_hash`, `is_active` | **Tier 3 (Confidential)** | Platform Administrator only for edits; user self-view for role. | Passwords never logged. PBKDF2 with SHA-256 hashing. |
| 2 | **Supplier** | `id`, `name`, `country`, `status`, `synthetic_contact` | **Tier 2 (Internal)** | Commercial Analyst (create/edit), Reviewer (view), Admin (view). | Synthetic contacts only; never use real supplier personal details. |
| 3 | **Product** | `id`, `supplier_id`, `category`, `specifications`, `MOQ`, `price_range`, `embedding` | **Tier 2 (Internal)** | Commercial Analyst (create/edit), Reviewer (view). | Vectors stored in PostgreSQL pgvector. Model weights local. |
| 4 | **EvidenceItem** | `id`, `type`, `description_ref`, `status`, `expiry_date` | **Tier 2 (Internal)** | Commercial Analyst (create), Reviewer (verify). | **Metadata only (D-10).** No physical file uploads permitted in v0.1. |
| 5 | **ReadinessQuestionSet** | `version`, `questions_json`, `effective_date` | **Tier 2 (Internal)** | Read-only in application; updated via versioned configuration. | Unapproved questions tagged `UNAPPROVED - D-03`. |
| 6 | **ReadinessAssessment** | `supplier_id`, `question_set_version`, `answers`, `status`, `outcome`, `reviewer_notes` | **Tier 2 (Internal)** | Analyst (draft/submit), Reviewer (outcome/notes). | Outcome set exclusively by human reviewer. |
| 7 | **BuyerRequirement** | `buyer_name`, `category`, `specs`, `criteria`, `version`, `status` | **Tier 2 (Internal)** | Commercial Analyst (create/edit), Reviewer (view). | Synthetic buyer organizations (D-13). Versioned on change. |
| 8 | **Criterion** | `requirement_id`, `type` (`mandatory` / `preference`), `value`, `weight` | **Tier 2 (Internal)** | Commercial Analyst (configure within approved set). | Mandatory vs preference distinctly stored. |
| 9 | **CriteriaVersion** | `version`, `rules_json`, `weights_json`, `approver`, `date` | **Tier 2 (Internal)** | Read-only reference; updated via versioned configuration. | Version referenced by every MatchRun. |
| 10 | **MatchRun** | `run_id`, `requirement_id`, `criteria_version`, `model_id`, `status`, `actor` | **Tier 2 (Internal)** | All authorized roles. | Immutable run record. Explicit `Failed` status on AI error. |
| 11 | **MatchResult** | `run_id`, `product_id`, `eligibility`, `scores`, `explanation`, `warnings` | **Tier 2 (Internal)** | All authorized roles. | Explanations deterministic. No LLM prompts. |
| 12 | **MatchDisposition** | `result_id`, `outcome` (`Accepted`/`Rejected`/`On hold`), `reason`, `actor` | **Tier 2 (Internal)** | Reviewer/Approver only (M7-AC1). | Mandatory reason required; immutable history. |
| 13 | **Opportunity** | `disposition_id`, `stage`, `owner`, `notes`, `blocked_flag`, `outcome` | **Tier 2 (Internal)** | Commercial Analyst, Reviewer. | Created only from `Accepted` disposition. |
| 14 | **OpportunityActivity** | `opportunity_id`, `date`, `activity_type`, `summary`, `actor` | **Tier 2 (Internal)** | Opportunity owner, Reviewer. | Interaction notes; synthetic parties only. |
| 15 | **AuditEvent** | `id`, `actor`, `action`, `object_type`, `object_id`, `outcome`, `changes`, `correlation_id` | **Tier 2 (Internal)** / Append-Only | Read-only. Viewable by Admin & Reviewer; Analyst scoped to owned records. | **Never log passwords, tokens, or session IDs (M10-AC3).** |

---

## 3. Synthetic Data Mandate & Guardrails

1. **Synthetic Data Policy (Build Manual §2, AGENTS.md §B rule 7)**:
   - All supplier companies, product specifications, contact details, buyer names, and pricing ranges used in the application, test suites, and database seed scripts (`manage.py seed_demo`) must be entirely synthetic.
   - Any contributor discovering real personal or corporate data in the codebase must immediately notify the DevSecOps Engineer (Ajendra) and Technical Coordinator (Aryan) for removal.
2. **Zero-Secret Codebase Policy**:
   - Environment variables (`os.environ`) are the single authorized source for configuration secrets.
   - The repository tracks only [`.env.example`](../../.env.example) containing non-sensitive placeholder tokens.
   - All `.env` and `.env.*` files are blocked by the root [`.gitignore`](../../.gitignore) and monitored via continuous CI `gitleaks` checks.

---

## 4. Cryptographic & Data Protection Standards

* **Data in Transit**: Enforce TLS 1.3 (fallback TLS 1.2) for any hosted staging deployment. Single-origin proxy ensures browser traffic never traverses unsecured inter-service paths without encryption.
* **Passwords**: Django standard PBKDF2 algorithm with a SHA-256 hash and a minimum 600,000 iterations.
* **Database Immutability**: `AuditEvent` table is protected by application-level immutability and an explicit PostgreSQL database trigger preventing `UPDATE` and `DELETE` commands (TD-03).

