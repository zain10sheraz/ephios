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

| 2026-11-26 | Manan (assisted by Claude Code) | OpenAPI spec, EP/BVA generator, API harness and 462 tests, API docs, issues #12-#14 | to be reviewed and understood by Manan before the viva |

AI mistakes caught by checking real output (2026-11-26): a spec that claimed a length limit on `search` the application does not have; a generator that produced a wrong-case class for integer enums and ignored cross-field time order; tests that reused one date so signups overlapped and invalid cases passed for the wrong reason; a wrong expectation that PUT on a create endpoint returns 405. Each was found by running against the real server and corrected from the observed behaviour, never by weakening an assertion.

| 2026-11-26 | Manan (assisted by Claude Code) | 14 follow-up API tests (filters, concurrency, combined invalid values, transitions) and their documentation | to be reviewed and understood by Manan before the viva |

Correction caught by running the real server: the first concurrency test assumed no HTTP 500 under simultaneous writes; the log showed `sqlite3.OperationalError: database is locked`, so the test now asserts the stored state and the limit is documented instead of the assertion being weakened silently.
