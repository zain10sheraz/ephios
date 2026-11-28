# AI-use record

Tool: Claude Code (Claude Sonnet 5.5) used as an assistant in the VS Code extension. Policy: all AI-generated code and
text is reviewed by the owning member; test results come only from real executions; the AI never commits as another member.

| ID | Date | Member and account | What the AI produced | Prompt log | Verification done by the member (real run or check) |
|---|---|---|---|---|---|
| A1 | 2026-11-23 | Zain `zain10sheraz` | Repo inspection, plan, setup scripts (`scripts/`), seed data | `prompts/ZAIN_PROMPTS.md` | Ran the setup and reset scripts, logged in with the seeded accounts, checked `/api/events/` 403 and `/accounts/login/` 200 |
| A2 | 2026-11-23 | Zain | Unit tests `tests/team/unit/*`, MCC/MC-DC tables, complexity document | `prompts/ZAIN_PROMPTS.md` | Ran pytest and coverage (100 % on the modules); recounted V(G) by hand against the control-flow graph |
| A3 | 2026-11-23 | Zain | DEFECT-001 analysis and GitHub issue text | `prompts/ZAIN_PROMPTS.md` | Reproduced with a failing test before the fix and a passing test after (`reports/defect001_*`) |
| A4 | 2026-11-23 | Zain | SonarQube setup and scans, `docs/team/SONARQUBE.md` | `prompts/ZAIN_PROMPTS.md` | Queried the metrics through the Sonar API and compared them with the screenshots |
| A5 | 2026-11-23 | Zain | Mutation setup: Cosmic Ray configuration, custom operators `tools/team_mutation/` | `prompts/ZAIN_PROMPTS.md` | Ran the sessions on an isolated copy; counted results from the session databases |
| A6 | 2026-11-23 | Zain | `docs/team/REQUIREMENTS.md` draft (assumptions marked [A]) | `prompts/ZAIN_PROMPTS.md` | Assumptions checked against the running app and the source; the other members review it |
| A7 | 2026-11-24 | Zain | WF1/WF2 HTTP integration tests, cross-workflow tests, complete MCC/MC-DC, 16-module gate, mutation on WF1 forms, survivor analysis and killer tests | `prompts/ZAIN_PROMPTS.md` | pytest and coverage rerun (458 tests, 16 modules at 100 %); every survivor classified from the mutant source |
| A8 | 2026-11-24 | Zain | CI workflow, gate scripts, fix PRs #2 #5 #8, demo PR #3, branch protection, RCA, test plan, RTM, progress report | `prompts/ZAIN_PROMPTS.md` | Workflow YAML validated; real GitHub runs (green, blocked) read back through the API |
| A9 | 2026-11-24 | Zain | Four defect reports (#1 #4 #6 #7) with live-server probes | `prompts/ZAIN_PROMPTS.md` | Probes run against the live server before and after each fix |
| B1 | 2026-11-26 | Manan `MannanJafferyyy` | OpenAPI spec, EP/BVA generator, API harness and tests, API documents, issues #12-#14 | `prompts/MANAN_PROMPTS.md` | Full suite run against a real server (`reports/api/pytest_full_run.txt`); API coverage script |
| B2 | 2026-11-26 | Manan | 14 follow-up API tests (filters, concurrency, combined invalid values, transitions) and their documentation | `prompts/MANAN_PROMPTS.md` | Rerun of the full suite; the concurrency log was read and the assertion corrected |
| B3 | 2026-11-27 | Manan | UC3 and UC4: specification and 12 Playwright flows | `prompts/MANAN_PROMPTS.md` | Every expected message read from the real page; run and rerun (`reports/e2e/manan_uc3_uc4_run.txt`) |
| C1 | 2026-11-26 | Sajawal `sajawalkhanfake` | Use cases, Playwright suite, axe and Lighthouse runs and the accessibility fix, k6 test, pip-audit, access matrix, recovery test, area 3 documents, issues #17-#23 | `prompts/SAJAWAL_PROMPTS.md` | Browser and k6 runs on the real app; regression test fails before and passes after the fix |
| C2 | 2026-11-27 | Sajawal | Real `@axe-core/playwright`, ZAP passive scan, API-level recovery test, evidence | `prompts/SAJAWAL_PROMPTS.md` | ZAP alerts fetched from ZAP's API and checked against `settings.py`; axe rerun |
| A10 | 2026-11-27 | Zain | UC5 and UC6: specification and 12 Playwright flows; test completion report | `prompts/ZAIN_PROMPTS.md` | Flows run in Chromium (`reports/e2e/zain_uc5_uc6_run.txt`); report figures taken from the reports |
| A11 | 2026-11-28 | Zain | Report corrections after the course review: table layout, risk matrix, CI required checks, GQM and Pareto update, EC-02 wording, AI-use record layout | `prompts/ZAIN_PROMPTS.md` | `scripts/check_tables.py` reports 0 broken tables; the PDF is rebuilt and checked |

## Prompts

The manual requires the prompts to be kept. They are exported unchanged from each member's own Claude Code session
history by `scripts/export_prompts.py` (see `docs/team/prompts/README.md`). Each member runs it on the machine where they
worked and commits the result under their own account: `docs/team/prompts/ZAIN_PROMPTS.md`, `MANAN_PROMPTS.md`,
`SAJAWAL_PROMPTS.md`. A member's prompt log is missing until that member has done this; the AI did not write or
reconstruct prompts for anyone.

## Sign-off (each member fills in their own row)

The AI wrote drafts. A row counts as reviewed only when the member has read the output, rerun the check in the last
column and initialled it here. Until then the status is **not yet signed off**. Nobody signs for another member.

| Member | Rows | Reviewed (initials) | Date | Can rerun and explain |
|---|---|---|---|---|
| Zain Sheraz | A1-A11 | not yet signed off | | |
| Manan | B1-B3 | not yet signed off | | |
| Sajawal | C1-C2 | not yet signed off | | |

## Corrections of AI mistakes (caught by checking real output)

Limitations observed: AI initially mis-specified a Sonar API parameter, a bind-mount scan that silently
skipped files, and an unverified explanation in the Sonar notes (corrected). Each was caught by checking real output.

Further corrections of AI mistakes caught by checking real output (2026-11-24): a regex replacement that silently corrupted the CI workflow YAML (caught by validating it); a wrong test-count figure written before verifying (333 vs real 367); a wrong GitHub username typed for a teammate (fixed); several predicted-equivalent mutants that were actually killable (recorded in MUTATION.md); a `pytest.raises` pattern that Sonar flags (found by a local scan). The AI also attempted `gh pr merge` on the deliberately-blocked demo PR and was correctly denied by the permission layer; verification was done with read-only queries instead.

AI mistakes caught by checking real output (2026-11-26): a spec that claimed a length limit on `search` the application does not have; a generator that produced a wrong-case class for integer enums and ignored cross-field time order; tests that reused one date so signups overlapped and invalid cases passed for the wrong reason; a wrong expectation that PUT on a create endpoint returns 405. Each was found by running against the real server and corrected from the observed behaviour, never by weakening an assertion.

Correction caught by running the real server: the first concurrency test assumed no HTTP 500 under simultaneous writes; the log showed `sqlite3.OperationalError: database is locked`, so the test now asserts the stored state and the limit is documented instead of the assertion being weakened silently.

Corrections of AI mistakes caught by running the real application (2026-11-26/27): selectors for the signup button were first written for the label "Sign up" but the request flow shows "Request" (found by dumping the real page; now selected by button value); the first browser run failed because upstream marks every test as using Django's test database (fixed in the e2e conftest, not by disabling tests); the first keyboard test checked the page before the keyboard-triggered navigation finished; the performance report first stated "about 50 events" from memory, the real figure was 16 events and 15 shifts (corrected in a separate commit); the exit criterion EC-04 was first at risk of being reported as met although it concerns signup and the measured operation was the event list (reported as not comparable).

Correction caught by re-reading the assignment text (2026-11-27): the first area 3 delivery substituted a Python port for `@axe-core/playwright` and marked ZAP "not run" although it could be installed; both were redone with the real tools, and the missing "two use cases per member" were added for the other two members.

