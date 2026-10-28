# Daily reports

Every team member records their own progress here on every working day. The log gives the whole team one place to see what each person has completed, what is in progress and what is blocked. It also supplies the evidence for the Friday Sprint Review and Aryan's weekly report to BNCS.

The format follows the build manual's daily stand-up format (§6). Under the manual's rules, every update points to a working artefact, decision, test result, review record or documented blocker.

| | |
|---|---|
| **Who writes** | Each member writes **only their own file**. Nobody writes or completes an entry for someone else. Harish writes only his own. |
| **When** | Every working day (Monday to Friday), before you finish for the day. |
| **Where** | One file per member in this folder (links below). The newest entry goes at the top. |
| **How it is submitted** | One pull request per member per week, updated with one commit per day (see *Workflow*). |
| **Process owner** | Aryan maintains this README and follows up missing entries. |
| **Starts** | The first working day after this folder is merged to `main`. There are no earlier entries, and none should be back-filled. |

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

`main` is protected, so entries reach it through a pull request. To keep this light there is **one PR per member per week**, and you push to it each day.

1. **Monday: start the week.** Update `main` and create a branch named `reports/<first-name>-week-<n>`, for example `reports/vishal-week-2`. Week numbers come from MVP_FEATURES §13.
2. **Each working day: add the entry.**
   - Copy the template below into your own file, directly under the marker line, so the newest entry is first.
   - Commit only that file, with the message `report: <first-name> <YYYY-MM-DD>`, and push.
   - On Monday, open the PR after the first push:
     - title: `Daily reports: <Full Name>, Week <n>`;
     - label: `daily-report`;
     - description: "Daily report entries only."
3. **Friday: submit the week.**
   - After Friday's entry, request a review from any other member.
   - The reviewer checks only that:
     - the PR changes nothing but your file;
     - the format is followed and links work;
     - no secrets, credentials, real personal data or confidential material appear.
   - **The reviewer does not vouch for accuracy.** You remain responsible for that.
   - Merge by the end of Friday, or first thing Monday at the latest.

Keep report PRs separate from work PRs. A report links to your work. It never contains the work.

## How to read the log

- **This week, live:** on GitHub, go to *Pull requests* and filter `is:pr is:open label:daily-report`. Each open PR's *Files changed* tab shows that member's entries so far this week.
- **History:** the member files on `main`. Use `git log -p -- docs/daily-reports/<file>.md` to see when each entry was committed.
- **Blockers across the team:** each entry has a *Blocked, dependencies and decisions needed* section, so you can scan the open PRs for it. Raising a blocker in the report does **not** replace raising it in the team channel when it is older than 24 hours (AGENTS.md §B rule 14).

## Entry template

Copy this block. Keep every heading, and write `None.` under a heading that has nothing to report, so entries stay consistent and easy to scan.

```markdown
## YYYY-MM-DD · Ddd · Week N

**Completed**
- <what you finished> — <state: merged | in review | submitted | drafted> — <evidence: PR, issue, commit or file link>

**In progress**
- <task> — <M#-AC#, D-xx or issue link> — <what remains>

**Tests and validation**
- `<exact command or manual check>` → <actual result, e.g. "41 passed, 2 failed">

**Blocked, dependencies and decisions needed**
- <what> — waiting on <person or BNCS> — since <YYYY-MM-DD> — raised in <issue, PR or channel>

**Next**
- <the next step you plan to take> — <M#-AC#, D-xx or issue link>
```

**No update.** On a working day you did not work on the pilot (leave, illness, programme commitments), or worked without anything to report, write only the heading and one line. You do not have to give a reason or any personal detail.

```markdown
## YYYY-MM-DD · Ddd · Week N

No update.
```

## Accuracy rules

1. **Completed means finished, and its state says how finished.** A merged PR, a PR in review and a drafted document are all different. Say which. Planned work goes under *Next*, never under *Completed*.
2. **Link evidence wherever it exists:** PR, issue, commit, file, review comment or test output. If there is no link, describe the artefact precisely enough for someone to find it.
3. **Tests: report only what you ran and what actually happened.** Give the command and the real result, including failures. Write `None.` if you ran nothing. Never write "tests pass" for tests you did not run.
4. **Do not invent or inflate.** Describe work as it is. "Started the supplier serializer" is a useful entry; claiming the endpoint is "done" when it is not is a problem.
5. **Late entries.**
   - If you missed a day, add that day's entry as soon as you can, under its own date, with the line `_Recorded late on YYYY-MM-DD._`
   - Include only what you can still support with evidence. Otherwise write `No update.`
6. **Corrections.**
   - Do not silently rewrite an entry that has already been merged.
   - Add a line under it: `_Correction YYYY-MM-DD: …_`
7. **Keep it short:** a few bullets per heading, usually ten to fifteen lines per day.
8. **Synthetic data only.** No secrets, passwords, tokens, real personal data or confidential BNCS material, exactly as in the rest of the repository.

## Missing entries

- **Daily check.** Each working morning before stand-up, Aryan (or a delegate Aryan names while away) checks that every member's open report PR has an entry for the previous working day. On Monday, this covers Friday.
- **Reminder.** If an entry is missing, Aryan reminds that member in the team channel. Only the member can add their entry.
- **Escalation.** If an entry is still missing at the next working morning's check, Aryan lists it as missing in the weekly report (member, date). Nobody else fills it in.
- **Programme-wide non-working days** (for example a public holiday announced by Aryan) need no entries.

## Using an AI coding agent

An agent may draft your entry, but you check and commit it. You stay accountable for it (MVP_FEATURES §8).

- An agent writes only in **the active member's own file**, as stated by the role you gave it (AGENTS.md §D). It never edits another member's file.
- The draft may use only facts from the session, `git log`, linked PRs and issues, and what you tell it. Anything it cannot verify is left out or marked `None.`
- It must not report a test result it did not see run.
