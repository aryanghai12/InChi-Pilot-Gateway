# Source and Reference Documents

The original programme and specification documents for the InChi Pilot Gateway pilot. **Do not edit, rename, move or delete these files** (ARCHITECTURE.md §4.2). Add new versions alongside the old ones and record them here.

## Inventory

| File | What it is | Date / version | Governs |
|---|---|---|---|
| [`InChi_China_Readiness_Implementation_Baseline_v2.2.pdf`](InChi_China_Readiness_Implementation_Baseline_v2.2.pdf) | China Readiness Implementation Baseline, 26 pages. Closed product decisions, field dictionary (SUP, PRD, BYR, REQ, ASM, EVD, MCH, DSP, AUD), 18-question questionnaire, evidence conditions, workflows, deterministic matching rules, screens SCR-01 to SCR-07, worked examples, acceptance criteria AC-01 to AC-25, security tests SEC-01 to SEC-06, change control. | v2.2, 16 Nov 2026. Product Authority: Venture Build Director and Chief Product Officer (BNCS). Supersedes the China Readiness Framework v2.1. | **The China-readiness and supplier–demand matching portion of the MVP.** On conflict with any earlier document, v2.2 governs unless the VBD and CPO approve a change request. |
| [`InChi_Pilot_User_Delivery Ownership (revised).pdf`](InChi_Pilot_User_Delivery%20Ownership%20(revised).pdf) | Revised team roles and delivery ownership (page 4 of 6 of "User Journey and Build Ownership") | Effective 26 Oct 2026 | **People and roles** (Aryan coordination, Ajendra security; AGENTS.md §C). |
| [`InChi_Pilot_Build Sequence Timeline (revised).pdf`](InChi_Pilot_Build%20Sequence%20Timeline%20(revised).pdf) | Week-by-week product targets, named duties and Friday exit reviews (pages 5–6) | 26 Oct – 18 Dec 2026 | **Dates and weekly duties** (proposed; approval pending under D-19). |
| [`InChi_Pilot_User_Journey_Proposed.pdf`](InChi_Pilot_User_Journey_Proposed.pdf) | Eight-stage user journey and stage owners (pages 1–3) | Footer: "Current 26 October 2026" | Journey stages (see DS-14). |
| [`InChi_Pilot_Gateway_Build_Manual.pdf`](InChi_Pilot_Gateway_Build_Manual.pdf) | Original build manual | Original calendar 19 Oct – 11 Dec 2026 | Everything not covered above: scope, components, governance, AI and security rules, gates, severity. Roles and dates are superseded (DS-01, DS-02). |
| [`InChi_University_Collaboration_Internship_Program.pdf`](InChi_University_Collaboration_Internship_Program.pdf) | Internship programme brief | — | Programme objective, evaluation standards. |
| [`InChi_Mapped_Website_Feature_Blueprint.pdf`](InChi_Mapped_Website_Feature_Blueprint.pdf) | Feature blueprint | v1.0, 27 Oct 2026 | Audited in [MVP_FEATURES §9](../MVP_FEATURES.md#9-feature-blueprint-audit); not authoritative on its own. |

**Not in the repository:** `InChi_Internship_Role_Assignment_Brief.pdf` (DS-16). The "Buyer Requirement Field Dictionary v1.4" cited by the `demand` code is also not here (AUD-13).

## Precedence when documents disagree

1. **Baseline v2.2** for readiness, evidence, buyer requirements, matching, explanation, disposition, the five-role permission matrix, and its acceptance criteria.
2. **Revised ownership, timeline and journey** (26 Oct 2026) for people, duties and dates.
3. **Build manual** for everything else.

Recorded discrepancies are DS-01 to DS-16 in [MVP_FEATURES §11](../MVP_FEATURES.md#11-source-document-discrepancies) and DS-17 onward in [governance/REGISTERS.md §8](../governance/REGISTERS.md#8-source-discrepancy-register). Conflicts between v2.2 and what is already built are listed in the [audit gap analysis](../governance/AUDIT_2026-11-21.md#3-baseline-v22-gap-analysis) and escalated as D-21 to D-25.

## Reading v2.2 in this repository

- v2.2 §4.1 names generic intern functions. The people are mapped in DS-20: Project Manager → Aryan, Product UX → Adrika, Frontend → Priyanka, Backend → Abhishek (API) and Vishal (data model), Data and AI → Alok, Cybersecurity → Ajendra, QA and Integration → Harish.
- v2.2 acceptance criteria use `AC-01`–`AC-25`. The repository's module criteria use `M#-AC#`. Harish maps the two in `docs/qa/traceability.md` (AUD-12).
- v2.2 controlled values (e.g. `ENG_COMPONENT`, `ACCEPT_FOR_FOLLOW_UP`) are the decided codes. Code that uses other values is a gap until aligned or covered by an approved change request (D-23).
