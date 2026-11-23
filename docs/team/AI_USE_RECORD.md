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

Limitations observed: AI initially mis-specified a Sonar API parameter, a bind-mount scan that silently
skipped files, and an unverified explanation in the Sonar notes (corrected). Each was caught by checking real output.
