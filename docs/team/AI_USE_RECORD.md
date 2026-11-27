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

| 2026-11-26 | Sujawal (account `sajawalkhanfake`, assisted by Claude Code) | use cases, Playwright suite (26 tests), axe/Lighthouse runs and accessibility fix, k6 test, pip-audit, access matrix, recovery test, area 3 documents and issues #17-#23 | to be reviewed and understood by Sujawal before the viva; screenshots must be taken by the member |

Corrections of AI mistakes caught by running the real application (2026-11-26/27): selectors for the signup button were first written for the label "Sign up" but the request flow shows "Request" (found by dumping the real page; now selected by button value); the first browser run failed because upstream marks every test as using Django's test database (fixed in the e2e conftest, not by disabling tests); the first keyboard test checked the page before the keyboard-triggered navigation finished; the performance report first stated "about 50 events" from memory, the real figure was 16 events and 15 shifts (corrected in a separate commit); the exit criterion EC-04 was first at risk of being reported as met although it concerns signup and the measured operation was the event list (reported as not comparable).

| 2026-11-27 | Manan (account `MannanJafferyyy`, assisted by Claude Code) | UC3 and UC4: specification and 12 Playwright flows | to be reviewed and understood by Manan before the viva |
| 2026-11-27 | Zain (account `zain10sheraz`, assisted by Claude Code) | UC5 and UC6: specification and 12 Playwright flows; test completion report | to be reviewed and understood by Zain before the viva |
| 2026-11-27 | Sujawal (account `sajawalkhanfake`, assisted by Claude Code) | real `@axe-core/playwright`, ZAP passive scan, API-level recovery test, evidence | to be reviewed and understood by Sujawal before the viva |

Correction caught by re-reading the assignment text (2026-11-27): the first area 3 delivery substituted a Python port for `@axe-core/playwright` and marked ZAP "not run" although it could be installed; both were redone with the real tools, and the missing "two use cases per member" were added for the other two members.
