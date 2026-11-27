# Evidence checklist

Status values: `captured` (file exists, produced by a real run), `verified` (a group member looked at it and confirmed).
**Nothing is `verified` until a member confirms.** Date = execution date.

| ID | Related test / activity | File or location | Date | Status |
|---|---|---|---|---|
| EV-001 | Unit tests + 100 % coverage (3 modules) | `reports/coverage_unit.txt`; rerun `scripts/run_unit_coverage.ps1` | 2026-11-23 | captured (rerun by Claude, 73 passed / 2 xfailed) |
| EV-002 | DEFECT-001 GitHub Issue | https://github.com/zain10sheraz/ephios/issues/1 | 2026-11-23 | captured |
| EV-003 | SonarQube metrics run 1 (core profile) | `reports/sonar_metrics_run1_core_profile.txt` | 2026-11-23 | captured |
| EV-004 | SonarQube metrics run 2 (comprehensive) | `reports/sonar_metrics_run2_comprehensive.txt` | 2026-11-23 | captured |
| EV-005a | SonarQube Summary page: Quality Gate FAILED (2 conditions: 13 issues on new code, coverage 9.5 % < 80 %) | `reports/evidence/EV-005a_sonar_summary_quality_gate.png` | 2026-11-23 | captured by Zain (screenshot supplied in chat) |
| EV-005b | SonarQube Overview: 18 issues, 0.5 % duplication, 9.5 % coverage | `reports/evidence/EV-005b_sonar_overview.png` | 2026-11-23 | captured by Zain (screenshot supplied in chat) |
| EV-006 | MCC / MC/DC tables + 15 passing tests | `docs/team/MCC_MCDC.md`, `tests/team/unit/test_mcc_mcdc.py` | 2026-11-23 | captured |
| EV-007 | Hand-calculated V(G) vs tool | `docs/team/CYCLOMATIC_COMPLEXITY.md`, `scripts/cyclomatic_ast.py` | 2026-11-23 | captured |
| EV-008 | Login page, Planner view of event list (real app) | **TO TAKE by Zain**: http://localhost:8000/accounts/login/ then log in as planner@sqe.test -> `reports/evidence/EV-008_planner_event_list.png` | – | pending |
| EV-009 | Volunteer view of the same event | **TO TAKE by Zain**: log in as volunteer@sqe.test, open "Concert Medical Service" -> `reports/evidence/EV-009_volunteer_event.png` | – | pending |
| EV-010 | Mutation round 1 raw data (3 modules) | `reports/mutation/round1_*.jsonl`, summary in `docs/team/MUTATION.md` | 2026-11-24 | captured |
| EV-013 | Mutation round 2 raw data and survivor analysis CSV | `reports/mutation/round2_*.jsonl`, `reports/mutation/survivor_analysis.csv` | 2026-11-24 | captured |
| EV-011 | Risk register + exit criteria draft | `docs/team/RISK_REGISTER.md` | 2026-11-24 | written - members to confirm |
| EV-012 | CI workflow + gate scripts | `.github/workflows/team-quality-gate.yml`, `docs/team/CI_GATES.md` | 2026-11-24 | captured (ran on GitHub) |
| EV-014 | Fix PR #2 (red Sonar run -> green) | https://github.com/zain10sheraz/ephios/pull/2 | 2026-11-24 | captured by Zain: `reports/evidence/EV-014_pr2_checks_all_green.png` (PR #2 Checks tab, 3 jobs green, merged into zain). The earlier RED run is not in this image; its evidence is the CI log in docs/team/CI_GATES.md |
| EV-015 | Blocked PR #3 (merge blocked by required checks) | https://github.com/zain10sheraz/ephios/pull/3 | 2026-11-24 | PARTIAL: `reports/evidence/EV-015a_pr3_demo_description_commits.png` shows PR #3 description and commits only. STILL NEEDED: scroll down to the checks box showing 'Merging is blocked' / failing checks -> `EV-015b_pr3_blocked.png` |
| EV-016 | Issue #1 (DEFECT-001) closed with evidence | `reports/evidence/EV-016_issue1_closed_defect001.png`, https://github.com/zain10sheraz/ephios/issues/1 | 2026-11-28 | captured by the member (screenshot supplied) |
| EV-017 | DEFECT-001 before/after test output | `reports/defect001_before_fix.txt`, `reports/defect001_after_fix.txt` | 2026-11-24 | captured |

| EV-018 | DEFECT-002 live probe against the running app (HTTP 500 on invalid date/start_time; valid input 302) | `reports/defect002_live_probe_before_fix.txt`, `scripts/probe_shift_form_live.py`, issue https://github.com/zain10sheraz/ephios/issues/4 | 2026-11-24 | captured (real HTTP requests to localhost:8000) |
| EV-019 | WF1 unit tests: 100 % statement+branch on forms/events.py and models/events.py | rerun `scripts/run_unit_coverage.ps1` | 2026-11-24 | captured (rerun by Claude; not yet verified by a member) |
| EV-020 | PR #5 (DEFECT-002 fix): Merged into zain, description with before/after evidence | `reports/evidence/EV-020_pr5_merged_defect_002.png` | 2026-11-25 | captured by Zain (shows the PR page; its Checks tab is not in this image, see `reports/evidence/github/pr_5.json` for the check results) |
| EV-021 | Issue #4 (DEFECT-002) closed with evidence | `reports/evidence/EV-021_issue4_closed_defect002.png`, https://github.com/zain10sheraz/ephios/issues/4 | 2026-11-28 | captured by the member (screenshot supplied) |
| EV-022 | Live probe before/after DEFECT-002 | `reports/defect002_live_probe_before_fix.txt` (500 x4), `reports/defect002_live_probe_after_fix.txt` (200 x4) | 2026-11-24 | captured |
| EV-023 | RCA, test plan, RTM, progress report 1 | `docs/team/RCA.md`, `TEST_PLAN.md`, `TRACEABILITY.md`, `PROGRESS_REPORT_1.md` | 2026-11-24 | written - members to confirm |
| EV-024 | DEFECT-003/004 before/after tests and live probe | `reports/defect003_004_before_fix.txt` (5 failed), `reports/defect003_004_after_fix.txt` (57 passed), `reports/defect004_live_probe_before_fix.txt` (500 x4), `reports/defect004_live_probe_after_fix.txt` (404 x2, 200 x2), `reports/defect003_004_regression.txt` | 2026-11-24 | captured |
| EV-025 | PR #8 (DEFECT-003 + DEFECT-004 fix): Merged into zain, description with before/after evidence | `reports/evidence/EV-025_pr8_merged_defects_003_004.png` | 2026-11-25 | captured by Zain (check results in `reports/evidence/github/pr_8.json`) |
| EV-026 | Coverage scope + 16-module 100 % run | `docs/team/COVERAGE_SCOPE.md`, rerun `scripts/run_unit_coverage.ps1` | 2026-11-24 | captured (rerun by Claude; not yet verified by a member) |
| EV-027 | Complete MCC/MC-DC tables | `docs/team/MCC_MCDC.md`, `tests/team/unit/test_mcc_mcdc_validation.py` | 2026-11-24 | captured |
| EV-028 | WF1 forms mutation (136 mutants) rounds, survivor CSV with 113 rows | `reports/mutation/round{1,2}_wf1_forms.*`, `reports/mutation/survivor_analysis.csv` | 2026-11-24 | captured |
| EV-029 | GitHub API exports of PRs #2 #3 #5 #8 #9, issues #1 #4 #6 #7, branch protection, workflow runs | `reports/evidence/github/` (README there) | 2026-11-25 | captured (machine export; screenshots EV-015b, EV-016, EV-020, EV-021, EV-025 are still welcome and not yet supplied) |
| EV-015b | PR #3 page: Open, red 'Merge status' button, 21 commits into main, demo description | `reports/evidence/EV-015b_pr3_merge_status_red.png` | 2026-11-25 | captured by Zain (file saved) |
| EV-015c | PR #3 Checks tab: upstream `lint (3.14)` and all 12 `test` jobs failed (red cross) for demo commit e268535; our `team-quality-gate` group is listed below | `reports/evidence/EV-015c_pr3_checks_all_red.png` | 2026-11-25 | captured by Zain (file saved) |
| EV-030 | Second early check, final commit 1279249e: our 3 checks, CodeQL and upstream tests (lint + 12 jobs) all pass; PR #10 closed unmerged | `reports/evidence/github/pr_10.json`, https://github.com/zain10sheraz/ephios/pull/10 | 2026-11-25 | captured (machine export) |
| EV-031 | Final mutation results, 8 modules, 235 survivors analysed | `docs/team/MUTATION.md`, `reports/mutation/survivor_analysis.csv`, `scripts/mutation_summary.py` | 2026-11-25 | captured (rerun the summary script to reproduce) |
| EV-014b | PR #2 (DEFECT-001 fix): Merged into zain, description with before/after evidence | `reports/evidence/EV-014b_pr2_merged_defect_001.png` | 2026-11-25 | captured by Zain (its all-green Checks tab is EV-014) |
| EV-030b | PR #10 (second early check zain -> main): Closed (not merged), 50 commits, 20 checks | `reports/evidence/EV-030_pr10_early_check2_closed_unmerged.png` | 2026-11-25 | captured by Zain (check results in `reports/evidence/github/pr_10.json`) |
| EV-032 | Pull request list, closed: #10 and #9 draft early checks closed with 20/20 checks, #8, #5, #2 merged with 3/3 checks | `reports/evidence/EV-032_pr_list_closed_5_merged_and_drafts.png` | 2026-11-25 | captured by Zain |
| EV-033 | Pull request list, open: only #3 'Demo (blocked)' remains open, with a red cross and 4/20 checks passing | `reports/evidence/EV-033_pr_list_open_pr3_blocked_4of20.png` | 2026-11-25 | captured by Zain |

| EV-034 | PR #3 'Files changed' view of one commit inside it (810c390, the DEFECT-001 fix: `return` -> `raise` in `participant_validation.py`, commit status 2/3) | `reports/evidence/EV-034_pr3_files_changed_commit_810c390_fix_diff.png` | 2026-11-25 | captured by Zain. Note: PR #3's *last* commit (e268535) restores the buggy `return`, so the PR as a whole keeps the defect; this screenshot shows an intermediate commit of the branch, not the net diff |
| EV-035 | PR #11 zain -> main merged (merge commit 520edca3), 20 checks, none failed; baseline tag created | `reports/evidence/github/pr_11.json`, https://github.com/zain10sheraz/ephios/pull/11, tag `baseline-upstream-d12e76cd` | 2026-11-25 | captured (machine export; screenshot welcome) |
| EV-036 | API test suite, one clean run: 462 passed, 0 failed (7 min 39 s) | `reports/api/pytest_full_run.txt`, `reports/api/junit.xml` | 2026-11-26 | captured (machine output) |
| EV-037 | API coverage against the spec: 14/14 operations, 46/46 documented responses, 80/80 inputs | `reports/api/api_coverage.md`, `reports/api/observed_raw.json` | 2026-11-26 | captured (machine output) |
| EV-038 | Generator output and regeneration demo (constraint change -> changed cases) | `test_data/api_cases.json`, `reports/api/regeneration_demo.txt` | 2026-11-26 | captured (machine output) |
| EV-039 | Open issues list (Open 11 / Closed 5): DEFECT-005 to DEFECT-016 with their labels | `reports/evidence/EV-039_issues_open.png`, `reports/evidence/EV-039b_issues_open_list_bottom.png` (rest of the list) | 2026-11-28 | captured by the member (screenshot supplied) |
| EV-042 | Browser suite, final full run: 51 passed (6 use cases, usability, keyboard, access matrix, recovery, accessible-name regression), Playwright HTML report | `reports/e2e/pytest_full_run.txt`, `reports/e2e/junit.xml`, `reports/e2e/playwright_report.html` | 2026-11-27 | captured (machine output) |
| EV-043 | Access matrix, observed vs expected (7 decisions) | `reports/e2e/access_matrix.md` | 2026-11-27 | captured (machine output) |
| EV-044 | axe-core (`@axe-core/playwright`) and Lighthouse reports before/after the fix, merged comparison; axe scan of the four key screens run by the member | `reports/accessibility/` (`comparison.md`), `reports/evidence/EV-044_axe_after.png` | 2026-11-28 | captured (machine output) and by the member (screenshot) |
| EV-045 | Regression test failing before the fix | `reports/accessibility/regression_before_fix.txt` | 2026-11-26 | captured (machine output) |
| EV-046 | k6 runs: first set (1 and 5 users, 2 runs each, 60 s, raw JSON) and the member's second set on a quiet machine (screenshots of one 1-user and one 5-user run) | `reports/performance/` (raw), `reports/evidence/EV-046_k6_1user.png`, `EV-046c_k6_1user_summary_detail.png`, `EV-046b_k6_5users.png` | 2026-11-28 | captured (raw output) and by the member (screenshots) |
| EV-047 | pip-audit result | `reports/security/pip_audit.json` | 2026-11-26 | captured (machine output) |
| EV-048 | Issues #17-#23 (area 3 defects) | https://github.com/zain10sheraz/ephios/issues/17 (to 23) | 2026-11-27 | created; screenshot not yet taken |
| EV-049 | OWASP ZAP 2.17.0 passive scan while the browser tests ran both workflows (166 URLs, 298 alerts, 10 types; first run 299) | `reports/security/zap_summary.md`, `zap_alerts.json`, `zap_urls.json`, `zap_run.txt` (first run), `reports/evidence/EV-049_zap_run.png`, `EV-049b_zap_summary.png` | 2026-11-28 | captured (machine output) and by the member (screenshots) |
| EV-050 | pip-audit: packages and versions checked | `reports/security/pip_audit_packages.txt` | 2026-11-27 | captured (machine output) |
| EV-051 | axe-core via `@axe-core/playwright` before/after reports; regression test before (4 failed) and after (4 passed) | `reports/accessibility/axe_*_{before,after}.json`, `regression_before_fix.txt`, `regression_after_fix.txt` | 2026-11-27 | captured (machine output) |
| EV-052 | Run of Manan's UC3 and UC4 (11 passed, 1 login-timeout under memory pressure, rerun passed) | `reports/e2e/manan_uc3_uc4_run.txt` | 2026-11-27 | captured (machine output) |
| EV-053 | Run of Zain's UC5 and UC6 (same pattern) | `reports/e2e/zain_uc5_uc6_run.txt` | 2026-11-27 | captured (machine output) |
| EV-054 | Test completion report with release criteria actual vs target (HOLD) | `docs/team/TEST_COMPLETION_REPORT.md` | 2026-11-27 | written |
| EV-055 | Issue #6 (DEFECT-003) closed with evidence | `reports/evidence/EV-055_issue6_closed_defect003.png` | 2026-11-28 | captured by the member (screenshot supplied) |
| EV-056 | Issue #7 (DEFECT-004) closed with evidence | `reports/evidence/EV-056_issue7_closed_defect004.png` | 2026-11-28 | captured by the member (screenshot supplied) |
| EV-057 | Issue #17 (DEFECT-008, accessible names) closed by the merged fix PR #24 | `reports/evidence/EV-057_issue17_closed_defect008.png` | 2026-11-28 | captured by the member (screenshot supplied) |
| EV-058 | Closed issues list: #17, #7, #6, #4, #1 (Open 11 / Closed 5) | `reports/evidence/EV-058_issues_closed_list.png` | 2026-11-28 | captured by the member (screenshot supplied) |
| EV-059 | Issue #12 (DEFECT-005, API: rejections return 302 like success), open | `reports/evidence/EV-059_issue12_open_defect005.png` | 2026-11-28 | captured by the member |
| EV-060 | Issue #13 (DEFECT-006, API: invalid limit/offset/ordering ignored), open | `reports/evidence/EV-060_issue13_open_defect006.png` | 2026-11-28 | captured by the member |
| EV-061 | Issue #14 (DEFECT-007, API: inconsistent 403/405/401, schema only 200), open | `reports/evidence/EV-061_issue14_open_defect007.png` | 2026-11-28 | captured by the member |
| EV-062 | Issue #18 (DEFECT-009, colour contrast), open, with the follow-up comment about UC5 and UC6 | `reports/evidence/EV-062_issue18_open_defect009.png` | 2026-11-28 | captured by the member |
| EV-063 | Open pull requests: #33 (22/22 checks passed) and the blocked demonstration #3 (4/20) | `reports/evidence/EV-063_pr_list_open_pr33_and_pr3.png` | 2026-11-28 | captured by the member |
| EV-064 | Blocked demonstration PR #3: description and its 21 commits | `reports/evidence/EV-064_pr3_demo_blocked_page.png` | 2026-11-28 | captured by the member |
| EV-065 | PR #33: "All checks have passed, 22 successful checks", no conflicts | `reports/evidence/EV-065_pr33_all_checks_passed.png` | 2026-11-28 | captured by the member |
| EV-032b | Merged pull requests list (13 merged: #2, #5, #8, #11, #15, #16, #24, #27, #28, #29, #30, #31, #32), each with all checks passed | `reports/evidence/EV-032b_prs_merged.png` | 2026-11-28 | captured by the member |
| EV-041 | Checks tab of PR #33: CodeQL, upstream tests and team-quality-gate, 22 checks | `reports/evidence/EV-041_pr33_checks_tab.png` | 2026-11-28 | captured by the member |
| EV-042b | Playwright HTML report, screenshots of the summary (0 failed, 51 passed, 0 errors) and the list of all 51 tests | `reports/evidence/EV-042_playwright_report.png`, `EV-042b_playwright_report_tests_1.png`, `EV-042c_playwright_report_tests_2.png` | 2026-11-28 | captured by the member (the 04:30 duration of the first test is the laptop suspension described in `E2E_AND_QUALITY_REPORT.md`) |
