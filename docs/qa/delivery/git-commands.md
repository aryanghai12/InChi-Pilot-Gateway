# Proposed commands after review

Run in this separate delivery worktree. The original test checkout must remain untouched. This task stops before commit; none of the commands below authorizes publication.

```powershell
Set-Location -LiteralPath 'C:\Users\harry\InChi-Pilot-Gateway\.cache\qa-delivery-worktree'
git branch --show-current
git status --short --branch
git diff --cached --check
git diff --cached --name-only
git diff --cached --stat
```

Review the staged candidate and the exact file manifest. After explicit commit approval:

```powershell
git commit -F docs/qa/delivery/commit-message.txt
```

After separate push approval, publish only the clean delivery branch, not all branches/tags:

```powershell
git -c push.followTags=false push -u origin qa/week1-3-delivery
```

Do not run push in this task. Use the prepared Draft PR body targeting `main` only after separate PR approval. No rewrite, reset, rebase or merge of the original branch is needed or authorized. Do not force-add ignored artifacts.
