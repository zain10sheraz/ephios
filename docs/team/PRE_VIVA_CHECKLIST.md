# Checklist before the viva (items the repository cannot prove by itself)

| # | Item | Who | How to check | Done |
|---|---|---|---|---|
| 1 | Commit identity: 56 commits carry the placeholder address `zain@test.com`, so GitHub does not link them to `zain10sheraz`. History is not rewritten (it is published and `main` is protected). `.mailmap` maps them for `git shortlog`; for new commits set `git config user.email` to the address verified on the GitHub account. | Zain | `git shortlog -sne` shows the three members; new commits show the avatar on GitHub | |
| 2 | Authorship: each member committed their own work and took the screenshots credited to them. | all | `git log --author=<account>` per member; screenshots listed in `EVIDENCE_CHECKLIST.md` | |
| 3 | Prompt logs exported and committed by each member (`docs/team/prompts/`, `scripts/export_prompts.py`) and the sign-off table of `AI_USE_RECORD.md` filled by each member. | all | three `*_PROMPTS.md` files exist; sign-off rows initialled | |
| 4 | Branch protection lists five required checks. Applied 2026-11-28 and exported; screenshots EV-068b, EV-068c and EV-078 taken by Zain. | Zain | `reports/evidence/github/branch_protection_main.json` shows five contexts | done |
| 5 | The signup load test was run (`scripts/k6_signup.js`, `PERFORMANCE.md` sections 1b and 1c): done 2026-11-28, EC-04 measured and not met on SQLite; screenshots EV-079 and EV-079b taken by Zain. | Zain | `reports/performance/k6_signup_*.json` exist | done |
| 6 | The repository is registered in our section's tab of the course Google Sheet. | all | open the sheet; this cannot be checked from the files | |
| 7 | Each member can rerun a test and explain their area. | each | commands in `SETUP.md` and the `VIVA_NOTES_*.md` of the member | |
