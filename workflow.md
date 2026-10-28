# Workflow and Approach: Vishal Chauhan

**Project:** InChi Pilot Gateway (BNCS internal pilot)
**Role:** Data and Platform Services Engineer

---

## 1. Role

I own the data layer of the platform: schema, migrations, constraints, search, analytics queries, audit storage, data contracts and recovery evidence.

**Boundary:** I own platform data services. I do not define commercial meaning alone. Field meaning and rules come from Adrika and BNCS; I implement and protect them.

---

## 2. Involvement in the user journey

| Stage | Journey step | My part |
|---|---|---|
| 2 | Register supplier and product | Primary co-owner: schema, evidence metadata, search, audit events |
| 3 | Assess China readiness | Store readiness answers, evidence and status history |
| 4 | Capture buyer requirement | Own data contracts: versioned requirements, criteria, weights |
| 5 | Generate match | Retrieval and storage of inputs, results, explanations, rule/model versions |
| 6 | Review and decide | Record inputs, explanations and human decisions |
| 7 | Manage opportunity | Primary co-owner: opportunity, stage, owner, due date, decision history |
| 8 | Monitor and audit | Primary co-lead: dashboard queries, audit history, reconciliation with source records |

---

## 3. Approach

1. **Contract first.** Agree field names, types, required/optional and versioning with Adrika (meaning), Abhishek (API) and Alok (match inputs) before writing migrations.
2. **Migrations only.** Every schema change is a migration file. No manual changes to shared databases.
3. **Integrity in the database.** Use keys, NOT NULL, unique and check constraints rather than relying on the UI or API alone.
4. **Audit by design.** Every material create, update and decision writes an append-only audit event: who, what, when.
5. **Versioning over overwriting.** Requirements, rules, weights and rule/model versions are versioned so every match result is traceable.
6. **Least privilege.** Separate database roles for app, reporting and migration. No secrets in the repo.
7. **Evidence every Friday** for Aryan's review pack.

---

## 4. Collaboration

| With | Exchange |
|---|---|
| Aryan | Status, blockers, dependencies, interface decisions |
| Adrika | I need: field dictionary, workflow states, acceptance criteria |
| Abhishek | Table and constraint contracts; query access patterns |
| Priyanka | Data shapes for forms, lists and dashboards |
| Alok | Match inputs; storage of results and explanations |
| Ajendra | Data classification, access review, secrets handling |
| Harish | Seed and test data; migration and integrity checks |

---

## 5. Definition of done

- [ ] Migration applies on a clean database and on the previous version
- [ ] Rollback or recovery path noted
- [ ] Constraints and indexes in place
- [ ] Audit events cover the new data
- [ ] Seed/test data updated
- [ ] Data dictionary updated
- [ ] Contract changes communicated to affected owners
- [ ] No secrets or real data committed
- [ ] PR reviewed by at least one teammate

---

## 6. Risks and escalation

| Risk | Mitigation |
|---|---|
| Field meaning changes after schema is built | Adrika signs off the field dictionary first; versioned migrations |
| API and schema drift | Written data contract; review each other's PRs |
| Match results not reproducible | Store inputs, weights, rule and model versions with every result |
| Dashboard disagrees with source records | Reconciliation queries; Harish verifies in Weeks 6-7 |
| Failed migration or data loss | Clean-DB migration test; backup/restore drill by Week 6-7 |

Escalate dependency blockers to Aryan, security questions to Ajendra, and commercial or policy meaning to Adrika/BNCS.