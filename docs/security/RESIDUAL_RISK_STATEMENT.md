# Formal Residual Risk Statement — InChi Pilot Gateway v0.1

| Attribute | Specification |
|---|---|
| **Author** | **Ajendra Nath Tripathi** (Cybersecurity and DevSecOps Engineer) |
| **Status** | Formal Baseline for Gate 4 / Gate 5 Handover |
| **Authority** | [`../MVP_FEATURES.md`](../MVP_FEATURES.md) §4 (M11-AC9), §15; Build Manual §9, §10 |
| **Sign-Off Authority** | BNCS Programme Sponsor & Senior Technical Mentor (via Aryan Ghai) |

---

## 1. Context & Purpose of Statement

This statement sets out the known residual security, architectural, and operational risks associated with **InChi Pilot Gateway v0.1**. 

InChi Pilot Gateway is an **internship pilot project** developed for supervised internal decision-support demonstration. In accordance with **Build Manual §9** and **AGENTS.md §B rule 12**, neither the DevSecOps Engineer nor the development team has the authority to unilaterally accept material residual security risks or certify the system as production-secure. Final risk acceptance belongs exclusively to BNCS and the Senior Technical Mentor.

---

## 2. Documented Non-Production Limitations & Residual Risks

### Risk 1: Non-Production Software Baseline (No External Penetration Certification)
* **Risk Nature**: The application has undergone internal static analysis, threat modeling, dependency scanning, and functional negative testing. However, it has **not** undergone third-party penetration testing or regulatory security certification (e.g. SOC 2, ISO 27001).
* **Residual Impact**: Potential undetected vulnerabilities in underlying third-party framework dependencies or network edge configurations.
* **Compensating Guardrail**: The platform is restricted to internal authorized BNCS staff behind authenticated sessions. Public registration, external supplier portals, and buyer access are strictly out of scope.

---

### Risk 2: Synthetic Data & Model Confidence Boundary
* **Risk Nature**: AI matching scores and cosine similarity metrics are evaluated exclusively against a synthetic dataset of $\ge 15$ suppliers and $\ge 30$ products.
* **Residual Impact**: Recommendations on synthetic data cannot guarantee commercial fit, legal compliance, or customs clearance in real-world China market operations.
* **Compensating Guardrail**: **Human-in-the-Loop mandate (M7)**: The platform operates solely as decision support. No match result can autonomously approve a supplier, sign a contract, or trigger commercial commitments. Authorised human reviewers must manually record dispositions.

---

### Risk 3: Unratified Permission Matrix (`UNAPPROVED – D-09`)
* **Risk Nature**: The permission matrix in [`ACCESS_CONTROL_MATRIX.md`](ACCESS_CONTROL_MATRIX.md) represents a recommended engineering baseline that is currently awaiting formal BNCS ratification.
* **Residual Impact**: Role boundaries (e.g., whether Commercial Analysts may recommend dispositions or view global audit logs) may change upon business sign-off.
* **Compensating Guardrail**: All permissions are implemented using the most restrictive baseline and isolated in `backend/apps/accounts/policy.py`. When BNCS ratifies D-09, adjustments require updating only a single configuration file without altering application endpoints.

---

### Risk 4: Local Embedding Resource Utilization (D-11 Pending Confirmation)
* **Risk Nature**: Embedding generation via local libraries (`sentence-transformers` on CPU) consumes significant memory and processing power during cold starts or bulk vectorization.
* **Residual Impact**: Local processing latency during high concurrent matching requests.
* **Compensating Guardrail**: The matching architecture executes synchronously in a two-component design with hard eligibility filters executed in PostgreSQL before vector embeddings are evaluated, minimizing unnecessary computation.

---

## 3. Formal Statement of Residual Risk Acceptance

```
To be executed at Gate 4 (Week 7) & Gate 5 (Week 8 Handover):

[ ] The undersigned BNCS Programme Sponsor and Senior Technical Mentor acknowledge the 
    residual risks and limitations documented above.
[ ] It is agreed that InChi Pilot Gateway v0.1 is accepted strictly as an internal, 
    supervised pilot and will not be operated as a production commercial marketplace 
    without independent security certification and production hardening.

Signed: _____________________________________   Date: ________________________
        BNCS Programme Sponsor

Signed: _____________________________________   Date: ________________________
        Senior Technical Mentor
```
