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
| EV-011 | Risk register + exit criteria draft | `docs/team/RISK_REGISTER.md` | 2026-11-24 | draft - team review pending |
| EV-012 | CI workflow + gate scripts | `.github/workflows/team-quality-gate.yml`, `docs/team/CI_GATES.md` | 2026-11-24 | captured (ran on GitHub) |
| EV-014 | Fix PR #2 (red Sonar run -> green) | https://github.com/zain10sheraz/ephios/pull/2 | 2026-11-24 | captured by Zain: `reports/evidence/EV-014_pr2_checks_all_green.png` (PR #2 Checks tab, 3 jobs green, merged into zain). The earlier RED run is not in this image; its evidence is the CI log in docs/team/CI_GATES.md |
| EV-015 | Blocked PR #3 (merge blocked by required checks) | https://github.com/zain10sheraz/ephios/pull/3 | 2026-11-24 | PARTIAL: `reports/evidence/EV-015a_pr3_demo_description_commits.png` shows PR #3 description and commits only. STILL NEEDED: scroll down to the checks box showing 'Merging is blocked' / failing checks -> `EV-015b_pr3_blocked.png` |
| EV-016 | Issue #1 closed with evidence | https://github.com/zain10sheraz/ephios/issues/1 | 2026-11-24 | **TO SCREENSHOT by Zain** |
| EV-017 | DEFECT-001 before/after test output | `reports/defect001_before_fix.txt`, `reports/defect001_after_fix.txt` | 2026-11-24 | captured |

| EV-018 | DEFECT-002 live probe against the running app (HTTP 500 on invalid date/start_time; valid input 302) | `reports/defect002_live_probe_before_fix.txt`, `scripts/probe_shift_form_live.py`, issue https://github.com/zain10sheraz/ephios/issues/4 | 2026-11-24 | captured (real HTTP requests to localhost:8000) |
| EV-019 | WF1 unit tests: 100 % statement+branch on forms/events.py and models/events.py | rerun `scripts/run_unit_coverage.ps1` | 2026-11-24 | captured (rerun by Claude; not yet verified by a member) |
| EV-020 | PR #5 (DEFECT-002 fix), all checks green after two real Sonar blocks | https://github.com/zain10sheraz/ephios/pull/5 ; CI run 45425449929 | 2026-11-24 | captured; **TO SCREENSHOT by Zain**: PR #5 Checks tab |
| EV-021 | Issue #4 closed with evidence | https://github.com/zain10sheraz/ephios/issues/4 | 2026-11-24 | **TO SCREENSHOT by Zain** |
| EV-022 | Live probe before/after DEFECT-002 | `reports/defect002_live_probe_before_fix.txt` (500 x4), `reports/defect002_live_probe_after_fix.txt` (200 x4) | 2026-11-24 | captured |
| EV-023 | RCA, test plan, RTM, progress report 1 | `docs/team/RCA.md`, `TEST_PLAN.md`, `TRACEABILITY.md`, `PROGRESS_REPORT_1.md` | 2026-11-24 | draft - team review pending |
