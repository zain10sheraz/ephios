# Authorship evidence: commits, pull requests and issues per account

Counts from the repository on 2026-11-28 (commits since the upstream baseline `d12e76cd`; pull requests and issues of
`zain10sheraz/ephios`). Reproduce with the commands at the end.

| Member | GitHub account | Commits since baseline | Pull requests (merged / closed / open) | Issues opened |
|---|---|---|---|---|
| Zain Sheraz | `zain10sheraz` (10 commits) and the older placeholder identity `zain` (56 commits, see below) | **66** | 7 / 2 / 2 | 4 |
| Manan | `MannanJafferyyy` | **36** | 3 / 0 / 0 | 3 |
| Sajawal | `sajawalkhanfake` | **75** | 8 / 0 / 0 | 9 |

Pull requests: Zain's two closed ones are the early checks #9 and #10, his open ones are the deliberately blocked demonstration
#3 and the current review PR; every other pull request was merged only after the required checks passed.

## What these numbers prove and what they do not

- They prove which **account** made each commit, pull request and issue. The commits of each member are attributed to that
  member's own GitHub account.
- They do **not** show who typed the prompts. All of the work of the three areas was done in one Claude Code session on one
  laptop, with the git identity and the GitHub login switched per area (`docs/team/AI_USE_RECORD.md`, section Prompts). The
  prompts are therefore in the files of `docs/team/prompts/`, cut by area, and every prompt in them was typed by Zain.
- Each member must still be able to explain and rerun the work credited to them (`docs/team/PRE_VIVA_CHECKLIST.md`).

## The 56 commits of the placeholder identity

56 of Zain's commits carry the placeholder author `zain` with a non-GitHub address, so GitHub does not link them to
`zain10sheraz`. History is not rewritten (it is published, and `main` is protected). `.mailmap` maps them to `zain10sheraz`
for `git shortlog`; the commit counts above include them.

## Commands

```
git log --format='%an' d12e76cd..main | sort | uniq -c
git shortlog -sne d12e76cd..main
gh pr list --repo zain10sheraz/ephios --state all --limit 100 --json number,author,state
gh issue list --repo zain10sheraz/ephios --state all --limit 100 --json author
```
