# InChi Pilot Gateway — Delivery Registers

**Maintained by:** Aryan Ghai (Technical Project Coordinator)  
**Status:** Updated for Week 4 (Workflow & Rule Approval Gate) — 21 November 2026

---

## 1. Decision Register

Authoritative register consolidating technical decisions from [`ARCHITECTURE.md §9`](../ARCHITECTURE.md#9-technical-decision-record) and business decisions from [`MVP_FEATURES.md §12`](../MVP_FEATURES.md#12-open-decisions).

### 1.1 Technical Decisions

| ID | Title | Owner | Approver | Resolution / Current State | Status |
|---|---|---|---|---|---|
| **D-01** | Technology Stack | Abhishek / Vishal / Priyanka / Alok | BNCS + Mentor | Next.js (App Router), Django 5.2 LTS + DRF, PostgreSQL 17 + pgvector, two-component matching (Django integration + FastAPI AI engine), Docker Compose. | **Selected** (Deviation pending formal sign-off) |
| **D-10** | Evidence Document Storage | Abhishek / Vishal | BNCS | Metadata-only for v0.1 (`EvidenceItem` tracking references, hashes, verification status; no binary storage). | **Resolved** |
| **D-11** | Local Embedding Model | Alok / Ajendra | BNCS + Mentor | Library: `sentence-transformers` interface running locally on CPU. Offline operation. Model selection shortlist in `docs/ai/EMBEDDING_MODEL_SELECTION.md`. | **Model Open** (Pre-Week 5) |
| **D-12** | Authentication & Provisioning | Abhishek | Ajendra | Django session auth with PBKDF2 hashing, CSRF rotation, and `create_platform_admin` command. No external SSO/self-registration. | **Resolved** |
| **D-15** | Matching Engine Deployment | Alok / Abhishek | Mentor | Two-component architecture: FastAPI matching engine containerized on internal port 8001; Django talks via HTTP client. | **Resolved** |
| **D-16** | Staging Environment | Aryan / Ajendra | BNCS | Docker Compose reference environment serves as primary demo and UAT platform; hosted staging optional. | **Selected** (Deviation pending formal sign-off) |
| **D-17** | Immutability of Match Runs | Alok / Abhishek | BNCS | Match runs and scores are immutable records tied to specific criteria versions. UI flags if underlying records change. | **Resolved** |
| **D-18** | Issue & Project Tracking | Aryan | Team | GitHub Issues with module (`M#`), severity, and role labels; GitHub Projects board. | **Resolved** |
| **D-20** | LLM Provider and Model | Aryan / Alok / Ajendra | BNCS | No LLM in v0.1 MVP. Deterministic rule-based and template explainability only. Zero external AI API transmission. | **Resolved for v0.1** |
| **TD-01** | Vector Storage Architecture | Vishal | Mentor | pgvector extension in PostgreSQL 17, schema managed by Django migrations. Cosine distance calculated via SQL. | **Resolved** |
| **TD-02** | Matching Boundary | Alok / Abhishek | Mentor | Clean separation: Django handles persistence/state; FastAPI handles AI computation/scoring. | **Resolved** |
| **TD-03** | Audit Trail Immutability | Abhishek / Vishal | Ajendra | Append-only database records via `apps/audit/models.py`. Update and delete actions prohibited. | **Resolved** |
| **TD-04** | Login Throttling | Abhishek / Ajendra | Ajendra | Evaluated in Week 2 security review; baseline Django throttling applied. | **Resolved** |
| **TD-05** | Login CSRF & Bootstrap | Abhishek / Priyanka | Ajendra | Explicit `GET /api/v1/auth/csrf/` endpoint providing token bootstrap for Next.js client. | **Resolved** |
| **TD-06** | Auth Error Semantics | Abhishek / Priyanka | Harish | Unauthenticated requests return structured JSON 401 (`not_authenticated`). Access-denied returns JSON 403. | **Resolved** |
| **TD-07** | SPA Catch-All Routing | Abhishek | Team | Superseded by TD-09 single-origin proxy. | **Superseded** |
| **TD-08** | Initial Platform Admin | Abhishek | Ajendra | Provisioned via `manage.py create_platform_admin` (or auto-provisioned via `.env` in Compose). | **Resolved** |
| **TD-09** | Single-Origin Proxy | Abhishek / Priyanka | Ajendra | Next.js rewrites `/api/:path*`, `/admin/:path*`, and `/static/:path*` to Django backend on `:8000`. No CORS or token storage. | **Resolved** |
| **TD-10** | Next.js Rendering Boundary | Priyanka | Abhishek | Client components use `apiFetch` and TanStack Query. No business logic, auth checks, or DB credentials in Next.js. | **Resolved** |

### 1.2 Business Decisions (Awaiting or Confirmed by BNCS)

| ID | Title | Owner | Approver | Current Working Assumption | Status |
|---|---|---|---|---|---|
| **D-02** | Target Industry Sectors | Adrika | BNCS | Agribusiness, food & beverage, and manufactured consumer goods. | **Approved for Pilot** |
| **D-03** | China Readiness Questionnaire & Criteria | Adrika / Abhishek | BNCS / Mentor | *China Readiness Implementation Baseline v2.2* adopted: 18 compliance criteria (`CR-01` to `CR-18`), 9 evidence conditions, 3 categorical qualitative outcomes. | **Resolved (Baseline v2.2)** |
| **D-04** | Mandatory Eligibility Criteria | Adrika / Alok | BNCS | Strict hard filters: China market readiness status, export certification status, minimum capacity. | **Open** (Gate 2 formal sign-off) |
| **D-05** | Weighted Preference Criteria | Adrika / Alok | BNCS | Working weights: pricing/commercial (30%), technical capability (30%), logistics/lead-time (20%), readiness depth (20%). | **Open** (Gate 2 formal sign-off) |
| **D-06** | Match Review Disposition Vocabulary | Adrika / Abhishek | BNCS | Three human disposition states: `Accepted`, `Rejected`, `On Hold` with mandatory justification notes. | **Approved for Pilot** |
| **D-07** | Commercial Opportunity Stages | Adrika / Abhishek | BNCS | 4 pipeline stages: `Initiated`, `Discovery`, `Negotiation`, `Closed`. Conversion only from accepted matches. | **Proposed for Week 5** |
| **D-08** | Dashboard Summary Metric Definitions | Adrika / Vishal | BNCS | Total registered suppliers, total products, readiness distribution, open buyer requirements. | **Proposed for Week 5** |
| **D-09** | Role Permission Matrix | Aryan / Abhishek | BNCS | Three roles: `Platform Admin`, `Commercial Analyst`, `Reviewer`. Reviewers cannot review their own submissions (`deny_self_review`). | **Resolved** |
| **D-13** | Buyer Verification Meaning | Adrika | BNCS | Verification metadata excluded from MVP eligibility logic; internal note only. | **Resolved** |
| **D-14** | Mandarin-Ready Product Fields | Adrika / Vishal | BNCS | `product_name_zh`, `short_description_zh`, and `translation_status` supported. | **Resolved** |
| **D-19** | Formal Revised Timeline Approval | Aryan | BNCS / Univ | 26 Oct – 18 Dec 2026 timeline operating across all teams. Formal ratification pending. | **Working Baseline (Pending Sign-off)** |

### 1.3 Source Discrepancies Register (DS-01 to DS-16)

| ID | Topic | Discrepancy Description | Resolution / Precedence |
|---|---|---|---|
| **DS-01** | Team Roles | Build manual swapped Aryan and Ajendra. | Revised ownership PDF governs (Aryan = Governance, Ajendra = Security). |
| **DS-02** | Timeline Dates | Manual had 19 Oct start; revised has 26 Oct start. | Revised timeline PDF governs (26 Oct – 18 Dec 2026). |
| **DS-03** | User Journey Stages | Manual had 7 stages; revised journey specifies 8 stages. | Revised 8-stage journey PDF governs. |
| **DS-04** | Module Count | Brief had M1-M12; manual condensed into M1-M11. | Manual M1-M11 module structure governs. |
| **DS-05** | Vector DB | Manual suggested external vector DB; team selected pgvector. | PostgreSQL + pgvector governed by ARCHITECTURE.md. |
| **DS-06** | Staging Requirement | Manual implied dedicated hosted staging; team made it optional. | Docker Compose reference environment serves as baseline. |
| **DS-07** | LLM Integration | Brief suggested LLM-generated summaries; v0.1 excludes LLM. | Deterministic templated output governs (D-20). |
| **DS-08** | Mandarin UI | Blueprint suggested bilingual UI; scope is English UI with Mandarin data fields. | English-first UI with Mandarin-ready fields governs. |
| **DS-09** | Evidence Uploads | Blueprint showed file upload widget; v0.1 uses metadata only. | Metadata-only tracking governs (D-10). |
| **DS-10** | External Accounts | Brief mentioned buyer self-service; v0.1 is internal BNCS users only. | Internal-only access governs. |
| **DS-11** | Scoring Mechanism | Brief suggested percentage scores; Baseline v2.2 enforces categorical outcomes for readiness. | Categorical qualitative outcomes govern. |
| **DS-12** | Commercial Contracts | Brief mentioned contract generation; excluded from v0.1. | Contract drafting is strictly out of scope. |
| **DS-13** | Opportunity Creation | Blueprint showed manual opportunity button; must originate from accepted match. | Strict match-acceptance dependency governs. |
| **DS-14** | Mobile Support | Blueprint responsive layout; desktop-optimized web app prioritized. | Desktop web application governs. |
| **DS-15** | Stack Approval | Build manual stack deviation (Django vs Spring Boot). | Pending formal sign-off in Week 1 review. |
| **DS-16** | Role Assignment Brief | Original role PDF not present in repo. | Revised ownership document governs. |

---

## 2. Risk Register

| Risk ID | Category | Description | Impact | Likelihood | Mitigation Strategy | Status |
|---|---|---|---|---|---|---|
| **RSK-01** | Governance | Delayed formal approval of revised timeline (D-19). | High | Low | Continue delivery against revised sequence; review at each sprint gate with BNCS. | Monitoring |
| **RSK-02** | AI / Data | Late selection of embedding model (D-11) blocks hybrid scoring. | High | Medium | Shortlist evaluated in `docs/ai/`; rules-based baseline works independently of embeddings. | Mitigated |
| **RSK-03** | Security | Insecure Direct Object Reference (IDOR) on readiness reviews. | Critical | Low | Enforced server-side `deny_self_review` in DRF permissions and automated E2E tests. | Resolved |
| **RSK-04** | Architecture | Cross-origin CSRF/CORS breakage during local or staging demos. | High | Low | Single-origin proxy architecture via Next.js rewrites; tested with Playwright E2E. | Resolved |
| **RSK-05** | Quality | Regression across multi-service boundaries prior to feature freeze. | High | Medium | Full-stack CI pipeline running backend, frontend, matching, and E2E checks on every PR. | Active |

---

## 3. Issue Register

| Issue ID | Module | Title & Description | Owner | Discovered | Resolved In | Status |
|---|---|---|---|---|---|---|
| **QA-001** | M1 Auth | Unauthenticated route redirects allowed empty shell render before redirecting. | Priyanka | Week 3 | PR #75 (`middleware.ts` 307 redirect) | **Closed** |
| **QA-003** | M3 Registry | Product price specified without mandatory currency code. | Abhishek | Week 3 | PR #70 (Serializer currency validation) | **Closed** |
| **QA-005** | M1 Auth | CSRF failure returned HTML error page instead of structured JSON. | Abhishek | Week 4 | PR #70 (`csrf_failure` handler returning 403) | **Closed** |
| **QA-006** | API Core | Unmatched `/api/` routes returned HTML 404 instead of JSON error envelope. | Abhishek | Week 4 | PR #70 (Custom 404 JSON catch-all) | **Closed** |
| **QA-007** | M4 Readiness | Frontend Dual-Aliasing needed for `workflow_state` and `status`. | Abhishek / Priyanka | Week 4 | PR #77 (Dual-aliasing serializer) | **Closed** |
| **QA-008** | Matching | Engine `/match` returns 503 until eligibility criteria (D-04) activated. | Alok | Week 4 | Tracking for Week 5 | **Open** |

---

## 4. Interface Contract Register

| Contract | Consumer | Provider | Specification | Protocol | Status |
|---|---|---|---|---|---|
| **IF-01: Auth & User** | Frontend | Django Backend | `/api/v1/auth/*` | HTTP Session / CSRF | Active & Locked |
| **IF-02: Supplier & Product** | Frontend | Django Backend | `/api/v1/suppliers/*`, `/api/v1/products/*` | DRF REST / JSON | Active & Locked |
| **IF-03: China Readiness** | Frontend | Django Backend | `/api/v1/assessments/*` | DRF REST / Baseline v2.2 | Active & Locked |
| **IF-04: Buyer Demand** | Frontend | Django Backend | `/api/v1/requirements/*` | DRF REST / Field Dict v1.4 | Active & Locked |
| **IF-05: AI Matching** | Django Backend | FastAPI Engine | `/api/v1/match/`, `/health` | HTTP Client / Pydantic | Active (Engine draft) |
| **IF-06: Audit Logging** | Django Apps | Audit Service | `record_event()` internal API | Python / ORM | Active & Locked |

