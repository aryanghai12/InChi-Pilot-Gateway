# InChi Pilot Gateway — Security & DevSecOps Pack

| Attribute | Specification |
|---|---|
| **Workstream Owner** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Active Working Baseline (v0.1 Pilot) |
| **Authority & Governance** | [`../../AGENTS.md`](../../AGENTS.md) §C2, [`../MVP_FEATURES.md`](../MVP_FEATURES.md) §8, M11, [`../ARCHITECTURE.md`](../ARCHITECTURE.md) §1, §8 |
| **Reviewers** | Aryan Ghai (Coordination), Abhishek Kumar (Backend), Vishal Chauhan (Data) |

---

## 1. Overview & Workstream Mandate

The Security & DevSecOps workstream provides independent verification, proactive threat modeling, automated CI security gates, and risk posture tracking for the **InChi Pilot Gateway**. 

The pilot operates under a strict principle:
> **"Security and privacy are designed in from Day 1. Technical owners implement fixes; Security identifies, validates, and tracks risk."** (AGENTS.md §B rule 7, §C2)

InChi Pilot Gateway is a **supervised, non-production internal pilot** (v0.1). It is not certified for production or public operation. It relies exclusively on synthetic data.

---

## 2. Security Pack Inventory

This directory comprises the mandatory **Security Handover Pack** defined in [`docs/MVP_FEATURES.md`](../MVP_FEATURES.md) §4 (M11-AC9) and Build Manual §10:

| Document | Purpose & Scope | Status |
|---|---|---|
| **[THREAT_MODEL.md](THREAT_MODEL.md)** | STRIDE Threat Model evaluating data flows, trust boundaries, IDOR, AI matching inputs, and session hijacking. | Baseline Complete |
| **[DATA_CLASSIFICATION.md](DATA_CLASSIFICATION.md)** | Sensitivity classification for all 15 core entities (MVP_FEATURES §6), synthetic data rules, and zero-secrets mandate. | Baseline Complete |
| **[ACCESS_CONTROL_MATRIX.md](ACCESS_CONTROL_MATRIX.md)** | Object-level RBAC matrix across Platform Admin, Commercial Analyst, and Reviewer (MVP_FEATURES §5; `UNAPPROVED - D-09`). | Baseline Complete |
| **[AUTH_THREAT_REVIEW.md](AUTH_THREAT_REVIEW.md)** | Threat review covering Django Session Auth, CSRF bootstrap, single-origin Next.js proxying (TD-09), and 401/403 semantics. | Baseline Complete |
| **[REMEDIATION_REGISTER.md](REMEDIATION_REGISTER.md)** | Central vulnerability ledger tracking issues, severity (Critical/High/Medium/Low), owners, fixes, and retest evidence. | Active Ledger |
| **[STAGING_CHECKLIST.md](STAGING_CHECKLIST.md)** | Pre-deployment verification checklist for optional hosted staging environments (pending D-16). | Pending D-16 |
| **[RESIDUAL_RISK_STATEMENT.md](RESIDUAL_RISK_STATEMENT.md)** | Explicit non-production risk boundary statement for final Gate 4/5 acceptance. | Formal Baseline |

---

## 3. DevSecOps CI Automation

Security gates are continuously enforced via GitHub Actions in [`.github/workflows/security.yml`](../../.github/workflows/security.yml):
1. **Secret Leak Detection**: Continuous scanning across repository history via `gitleaks` configured with [`.gitleaks.toml`](../../.gitleaks.toml).
2. **Frontend Dependency Auditing**: `npm audit --audit-level=high` on all Next.js packages.
3. **Backend Dependency Auditing**: `pip-audit` scanning for known CVEs in Python libraries.
4. **Static Application Security Testing (SAST)**: Automated Python SAST (`bandit`).
5. **Continuous Dependency Updates**: Automated monitoring via [`.github/dependabot.yml`](../../.github/dependabot.yml).

---

## 4. Workstream Boundaries & Rules of Engagement

Per **AGENTS.md §C2**:
* **No Direct Code Modifications**: Security does not rewrite application business logic or frontend code to fix findings. Security authors negative test cases, reproduction steps, and remediation guidance. Component owners (Abhishek, Priyanka, Vishal, Alok) implement the fixes.
* **No Unilateral Risk Acceptance**: Material residual security risk is accepted only by BNCS or the Senior Technical Mentor through Aryan.
* **Non-Intrusive Testing**: Security scans and negative tests execute only against local non-production containerized environments.
