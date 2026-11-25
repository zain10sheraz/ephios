# GitHub evidence exports (machine-generated, 2026-11-25)

Produced with `gh pr view / gh issue view / gh api ... --json` against https://github.com/zain10sheraz/ephios. They are GitHub's own records of
state at export time; they do not replace a screenshot a member took, and no member has verified them yet.

| File | What it shows |
|---|---|
| `pr_2.json`, `pr_5.json`, `pr_8.json` | fix PRs: state MERGED into `zain`; our 3 checks SUCCESS (statusCheckRollup) |
| `pr_3.json` | demo PR to `main`: state OPEN, `mergeStateStatus = BLOCKED`, our 3 checks FAILURE |
| `pr_9.json` | draft early-check PR zain -> main: our 3 checks, CodeQL and upstream `tests` (lint + 12 jobs) SUCCESS; closed unmerged |
| `issue_1.json`, `issue_4.json`, `issue_6.json`, `issue_7.json` | the four defects: CLOSED, with severity / priority / category labels |
| `branch_protection_main.json` | required checks (3), enforce_admins true, no force pushes |
| `workflow_runs.json` | the last 40 workflow runs with conclusions and timestamps |
| `pr_10.json` | second draft early-check PR zain -> main on the final commit: all checks SUCCESS; closed unmerged |
