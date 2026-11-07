# Weekly reports

Every team member records one concise progress report for each programme week. The reports give the team one place to see completed work, work in progress, blockers, validation, meeting and review activity, and the next step. They supply evidence for the sprint review and Aryan's weekly BNCS report.

The folder name remains `daily-reports` to preserve existing links, open branches and Git history. It now contains weekly reports only. The proposed revised timeline in `docs/MVP_FEATURES.md` section 13 defines Week 1 as 26-30 October 2026 and Week 2 as 2-6 November 2026; it remains pending D-19 approval.

| | |
|---|---|
| **Who writes** | Each member writes **only their own file**. Nobody writes or completes a report for someone else. |
| **When** | Once for each programme week, after that week's Friday sprint review or by the next working day. |
| **Where** | One file per member in this folder (links below). The newest report goes at the top. |
| **How it is submitted** | One focused pull request per member per week (see *Workflow*). |
| **Process owner** | Aryan maintains this README and follows up missing reports. |
| **Migration** | Existing daily entries remain historical evidence. From this change onward, members use the weekly template below. |

## Member files

| Member | Role | File |
|---|---|---|
| Aryan Ghai | Technical Project Coordinator, Product Operations and Integration Governance | [aryan-ghai.md](aryan-ghai.md) |
| Ajendra Nath Tripathi | Cybersecurity and DevSecOps Engineer | [ajendra-nath-tripathi.md](ajendra-nath-tripathi.md) |
| Adrika T Kumar | Product UX and Commercial Workflow Analyst | [adrika-t-kumar.md](adrika-t-kumar.md) |
| Priyanka Singh | Frontend Web and Client-Side Integration Engineer | [priyanka-singh.md](priyanka-singh.md) |
| Abhishek Kumar | Application Backend and Access-Control Engineer | [abhishek-kumar.md](abhishek-kumar.md) |
| Vishal Chauhan | Data and Platform Services Engineer | [vishal-chauhan.md](vishal-chauhan.md) |
| Alok Tiwari | AI Matching and Data Intelligence Engineer | [alok-tiwari.md](alok-tiwari.md) |
| Harish Pal | QA and Test Automation Engineer | [harish-pal.md](harish-pal.md) |

## Workflow

`main` is protected, so reports reach it through a pull request. Keep reports separate from work PRs: a report links to work and evidence, but does not contain that work.

1. **Start the week.** Update `main` and create a branch named `reports/<first-name>-week-<n>`, for example `reports/vishal-week-2`. Week numbers come from MVP_FEATURES section 13.
2. **Prepare one report.** By the Friday sprint review (or next working day), copy the template below into your own file directly under the marker line. Commit only that file, using `report: <first-name> week-<n>`.
3. **Open and review the PR.** Open one PR titled `Weekly report: <Full Name>, Week <n>`, label it `weekly-report`, and describe it as `Weekly report only.` Request a review from any other member. The reviewer checks only that the PR changes the member's file, follows the format, has usable evidence links, and contains no secrets, credentials, real personal data or confidential material. The reviewer does not vouch for factual accuracy.
4. **Merge promptly.** Merge after review by the end of the next working day. The author remains responsible for accuracy.

## How to read the log

- **This week, live:** filter GitHub pull requests by `is:pr is:open label:weekly-report`.
- **History:** read the member file on `main`, or run `git log -p -- docs/daily-reports/<file>.md`.
- **Blockers across the team:** scan the *Blocked, dependencies and decisions needed* section. A report does not replace raising a blocker in the team channel after 24 hours (AGENTS.md section B rule 14).

## Weekly report template

Copy this block. Keep every heading, and write `None.` under a heading with nothing to report.

```markdown
## Week N - DD Month-DD Month YYYY

**Completed**
- <what you finished> - <state: merged | in review | submitted | drafted> - <evidence: PR, issue, commit or file link>

**Meetings, reviews and coordination**
- <meeting, PR review, merge, decision follow-up or coordination activity> - <evidence or precise record>

**In progress**
- <task> - <M#-AC#, D-xx or issue link> - <what remains>

**Tests and validation**
- `<exact command or manual check>` -> <actual result, including failures>

**Blocked, dependencies and decisions needed**
- <what> - waiting on <person or BNCS> - since <YYYY-MM-DD> - raised in <issue, PR or channel>

**Next week**
- <next step> - <M#-AC#, D-xx or issue link>
```

**No update.** If you had no pilot work to report for the entire week, use the week's heading and `No update.` You need not give a personal reason.

## Accuracy and timing rules

1. **Completed means finished.** State whether the item is merged, in review, submitted or drafted. Planned work belongs under *Next week*.
2. **Link evidence where it exists.** Use a PR, issue, commit, file, review comment or test output. If no link exists, describe the artefact precisely enough to find it.
3. **Report only checks actually run.** Include the command and actual result, including failures. Write `None.` if no check was run.
4. **Do not invent or inflate.** Report only work, meetings, reviews and outcomes that happened.
5. **Late reports.** Add the report as soon as possible under its correct week, prefaced with `_Recorded late on YYYY-MM-DD._` Include only supported facts.
6. **Corrections.** Do not silently rewrite a merged report. Add `_Correction YYYY-MM-DD: ..._` below the relevant report.
7. **Keep it concise.** A weekly report should normally be no more than 15-20 lines plus links.
8. **Use synthetic and non-sensitive information only.** Never include secrets, passwords, tokens, real personal data or confidential BNCS material.

## Missing reports

- **Weekly check.** After the Friday sprint review, Aryan (or a delegate Aryan names while away) checks that every member has submitted a report for the week.
- **Reminder.** If a report is missing, Aryan reminds that member in the team channel. Only that member can add it.
- **Escalation.** If it is still missing at the next weekly check, Aryan lists the member and week in the BNCS weekly report. Nobody else fills it in.

## Using an AI coding agent

An agent may draft your report, but you check and commit it. You remain accountable for it (MVP_FEATURES section 8).

- An agent writes only in the active member's own file, as stated by the role supplied to it in AGENTS.md section D.
- The draft may use only facts from the session, `git log`, linked PRs and issues, and facts supplied by the member. Anything it cannot verify is left out or marked `None.`
- It must not report a test result it did not see run.
