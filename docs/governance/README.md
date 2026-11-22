# Delivery Governance

**Owner:** Aryan Ghai, Technical Project Coordinator, Product Operations and Integration Governance (AGENTS.md §C1).
**Scope:** sprint cadence, backlog, registers, decisions, interface coordination, integration evidence and review packs.

## Documents

| Document | Purpose | Last updated |
|---|---|---|
| [`REGISTERS.md`](REGISTERS.md) | Decision register (business and technical, with the **pending-decision escalation list**), risks, issues, dependencies, interface contracts, change-request log (`CRQ-###`, v2.2 §15.3), gate register and source discrepancies DS-17+. | 21 Nov 2026 |
| [`INTEGRATION_PLAN.md`](INTEGRATION_PLAN.md) | Components, the eight interface contracts with their verified endpoints and wiring status, gate content, and the Week 5–6 integration sequence. | 21 Nov 2026 |
| [`AUDIT_2026-11-21.md`](AUDIT_2026-11-21.md) | End-of-Week-4 repository and documentation audit: checks run, Baseline v2.2 gap analysis, findings AUD-01 to AUD-15, document-by-document status, weekly-report verification. | 21 Nov 2026 |
| [`../daily-reports/README.md`](../daily-reports/README.md) | Weekly-report process, template and missing-report rules. | 21 Nov 2026 |

## How decisions are recorded

1. Business rules, scope and permissions are decided by BNCS. For the China-readiness and matching portion, Baseline v2.2 (16 Nov 2026) is the BNCS decision of record. Any deviation needs a change request approved by the Venture Build Director and CPO (v2.2 §15.3).
2. Technical decisions are recorded in [ARCHITECTURE.md §9](../ARCHITECTURE.md#9-technical-decision-record), and build-manual deviations awaiting approval in [§10](../ARCHITECTURE.md#10-build-manual-deviations-and-pending-approvals).
3. A decision is marked **Decided** or **Approved** only with an approver, a date and a pointer to the record. Everything else is **Proposed** or **Open**.

## Weekly cadence

| When | Ritual | Output |
|---|---|---|
| Monday | Sprint Start (chaired by Aryan) | Week target against the revised timeline, owners, blockers, decisions to escalate |
| Tuesday – Thursday | Integration check-ins | Contract changes agreed; blockers older than 24 hours raised (AGENTS.md §B rule 14) |
| Friday | Sprint Review and gate demo (chaired by Aryan) | Demo against the exit review; evidence linked; weekly reports submitted; review record added here |

## Still to add

- Gate 1 and Gate 2 review records (outcome, approver, conditions, evidence links).
- Weekly BNCS report copies or links.
