# InChi Pilot Gateway — QA & Test Automation Pack

**Lead Engineer:** Harish Pal (QA and Test Automation Engineer)  
**Authority & Scope:** [`../../AGENTS.md §C8`](../../AGENTS.md#c8-harish-pal--qa-and-test-automation-engineer), [`../MVP_FEATURES.md M11`](../MVP_FEATURES.md#m11--quality-assurance-security-documentation-and-demonstration-setup)  
**Status:** Active QA Baseline & Traceability — Week 4 Delivery

---

## 1. Overview & Objectives

The QA and Test Automation workstream provides independent verification, test coverage design, requirements-to-test traceability, regression testing, and defect lifecycle management across the InChi Pilot Gateway platform.

Testing spans unit, API contract, integration, access control, and browser-based end-to-end automation.

---

## 2. QA Deliverables Index

| Document / Directory | Description | Status |
|---|---|---|
| **[`test-strategy.md`](test-strategy.md)** | Multi-level test strategy: smoke, functional, negative, API, integration, regression, and audit testing. | Active Baseline |
| **[`traceability.md`](traceability.md)** | Requirements-to-Test Traceability Matrix mapping user journey modules (`M1`–`M10`) to test case IDs and evidence. | Updated for Week 4 |
| **[`defects.md`](defects.md)** | Defect lifecycle ledger tracking discovered defects, severity, repro steps, owners, and closure evidence. | Active Register |
| **[`execution-2026-11-16-integrated.md`](execution-2026-11-16-integrated.md)** | Integrated test execution log for Week 3/4 baseline covering authentication, registry, and readiness gates. | Verified |
| **[`delivery/`](delivery/)** | QA delivery logs, verification reports, commit metadata, and public issue drafts. | Reference |
| **[`evidence/`](evidence/)** | Automated test run logs, Playwright trace outputs, and terminal execution logs. | Test Artifacts |

---

## 3. Automated Test Suites & Commands

### Backend Tests (pytest & Django Test Runner)
```bash
# Run all backend tests
docker compose exec backend python -m pytest

# Run specific app suites
docker compose exec backend python -m pytest apps/accounts/tests
docker compose exec backend python -m pytest apps/registry/tests
docker compose exec backend python -m pytest apps/readiness/tests
```

### AI Matching Engine Tests (FastAPI / pytest)
```bash
docker compose exec backend python -m pytest ai_matching/tests
```

### Frontend Tests (Vitest & TypeScript)
```bash
cd frontend
npm test          # Vitest unit & component suites
npm run typecheck # tsc --noEmit
npm run lint      # ESLint analysis
```

### End-to-End Automation (Playwright)
```bash
# Run cross-browser E2E suite
npx playwright test
```

