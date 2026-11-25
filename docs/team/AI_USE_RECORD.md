# AI-use record

Tool: Claude Code (Claude Sonnet 5.5) used as an assistant in the VS Code extension, run by Zain Sheraz.
Policy: all AI-generated code and text is reviewed by the owning member; test results come only from real
executions; the AI never commits as another member.

| Date | Who prompted | What AI produced | Human review status |
|---|---|---|---|
| 2026-11-23 | Zain | Repo inspection, plan, setup scripts (`scripts/`), seed data | to be reviewed |
| 2026-11-23 | Zain | Unit tests `tests/team/unit/*`, MCC/MC-DC tables, complexity doc | to be reviewed by Zain |
| 2026-11-23 | Zain | DEFECT-001 analysis and GitHub issue text | to be reviewed |
| 2026-11-23 | Zain | SonarQube setup/scans, `docs/team/SONARQUBE.md` | to be reviewed |
| 2026-11-23 | Zain | Mutation setup: Cosmic Ray config, custom operators `tools/team_mutation/` | to be reviewed |
| 2026-11-23 | Zain | `docs/team/REQUIREMENTS.md` draft (contains unverified assumptions marked [A]) | to be reviewed by all members |

| 2026-11-24 | Zain | WF1/WF2 HTTP integration tests, cross-workflow tests, complete MCC/MC-DC, 16-module gate, mutation on WF1 forms, survivor analysis and killer tests | to be reviewed by Zain |
| 2026-11-24 | Zain | CI workflow, gate scripts, fix PRs #2 #5 #8, demo PR #3, branch protection, RCA, test plan, RTM, progress report, viva notes | to be reviewed by Zain |
| 2026-11-24 | Zain | four defect reports (#1 #4 #6 #7) with live-server probes | to be reviewed by Zain |

Limitations observed: AI initially mis-specified a Sonar API parameter, a bind-mount scan that silently
skipped files, and an unverified explanation in the Sonar notes (corrected). Each was caught by checking real output.

Further corrections of AI mistakes caught by checking real output (2026-11-24): a regex replacement that silently corrupted the CI workflow YAML (caught by validating it); a wrong test-count figure written before verifying (333 vs real 367); a wrong GitHub username typed for a teammate (fixed); several predicted-equivalent mutants that were actually killable (recorded in MUTATION.md); a `pytest.raises` pattern that Sonar flags (found by a local scan). The AI also attempted `gh pr merge` on the deliberately-blocked demo PR and was correctly denied by the permission layer; verification was done with read-only queries instead.
