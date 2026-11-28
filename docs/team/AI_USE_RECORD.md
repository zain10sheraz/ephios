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
| B1 | 2026-11-26 | Manan `MannanJafferyyy` (prompted by Zain, see Prompts) | OpenAPI spec, EP/BVA generator, API harness and tests, API documents, issues #12-#14 | `prompts/ZAIN_PROMPTS.md`, prompts 57-76 | Full suite run against a real server (`reports/api/pytest_full_run.txt`); API coverage script |
| B2 | 2026-11-26 | Manan | 14 follow-up API tests (filters, concurrency, combined invalid values, transitions) and their documentation | `prompts/ZAIN_PROMPTS.md`, prompts 57-76 | Rerun of the full suite; the concurrency log was read and the assertion corrected |
| B3 | 2026-11-27 | Manan | UC3 and UC4: specification and 12 Playwright flows | `prompts/ZAIN_PROMPTS.md`, prompts 80-144 | Every expected message read from the real page; run and rerun (`reports/e2e/manan_uc3_uc4_run.txt`) |
| C1 | 2026-11-26 | Sajawal `sajawalkhanfake` (prompted by Zain, see Prompts) | Use cases, Playwright suite, axe and Lighthouse runs and the accessibility fix, k6 test, pip-audit, access matrix, recovery test, area 3 documents, issues #17-#23 | `prompts/ZAIN_PROMPTS.md`, prompts 79-100 | Browser and k6 runs on the real app; regression test fails before and passes after the fix |
| C2 | 2026-11-27 | Sajawal | Real `@axe-core/playwright`, ZAP passive scan, API-level recovery test, evidence | `prompts/ZAIN_PROMPTS.md`, prompts 80-144 | ZAP alerts fetched from ZAP's API and checked against `settings.py`; axe rerun |
| A10 | 2026-11-27 | Zain | UC5 and UC6: specification and 12 Playwright flows; test completion report | `prompts/ZAIN_PROMPTS.md` | Flows run in Chromium (`reports/e2e/zain_uc5_uc6_run.txt`); report figures taken from the reports |
| A11 | 2026-11-28 | Zain | Report corrections after the course review: table layout, risk matrix, CI required checks, GQM and Pareto update, EC-02 wording, AI-use record layout | `prompts/ZAIN_PROMPTS.md` | `scripts/check_tables.py` reports 0 broken tables; the PDF is rebuilt and checked |

## Prompts

The manual requires the prompts to be kept. `scripts/export_prompts.py` exports them unchanged from the Claude Code session
history. **Exported: `docs/team/prompts/ZAIN_PROMPTS.md`, 144 prompts (2026-11-23 to 2026-11-27)**, proof in screenshots
`EV-080` and `EV-080b`.

**Whose prompts these are (stated plainly):** this is the only Claude Code session of the project. Zain ran it, and the work
of all three areas was done in it, switching the git identity and the GitHub login per area. The log itself shows this
(for example prompt 57: "now that we are logged in as manan, go on and finish all manan work"; prompt 79: "for sajawal work
here is the github account ... i am logged in as this rn"). Consequently:

| Area | Prompted by | Where in `ZAIN_PROMPTS.md` (from the markers in the log, indicative) |
|---|---|---|
| Area 1 (Zain) | Zain | prompts 1-52 (23-25 Nov) |
| Area 2 (Manan, commits and issues made with the account `MannanJafferyyy`) | Zain | prompts 57-76 (25-26 Nov) |
| Area 3 (Sajawal, commits and issues made with the account `sajawalkhanfake`) | Zain | prompts 79 onward (26-27 Nov) |
| Use cases UC1-UC6, follow-ups, evidence, completion report, review fixes | Zain, for all three members | prompts 80-144 (mixed) |

There is therefore **no separate prompt log for Manan or for Sajawal**, and none was reconstructed or invented. If either of
them also used Claude Code or another AI tool on their own, they must export or list those prompts themselves and add them
here. Manan and Sajawal still have to read, rerun and be able to explain the work credited to them (viva).

## Sign-off (each member fills in their own row)

The AI wrote drafts. A row counts as reviewed only when the member has read the output, rerun the check in the last
column and initialled it here. Until then the status is **not yet signed off**. Nobody signs for another member.

| Member | Rows | Reviewed (initials) | Date | Can rerun and explain |
|---|---|---|---|---|
| Zain Sheraz | A1-A11 (prompt log exported, EV-080) | not yet signed off | | |
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

