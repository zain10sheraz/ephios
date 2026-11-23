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
| EV-010 | Mutation round 1 raw data (3 modules) | `reports/mutation/round1_*.jsonl`, summary in `docs/team/MUTATION.md` | 2026-11-24 | captured (round 2 pending) |
| EV-011 | Risk register + exit criteria draft | `docs/team/RISK_REGISTER.md` | 2026-11-24 | draft - team review pending |
| EV-012 | CI workflow (not yet run on GitHub) | `.github/workflows/team-quality-gate.yml` | 2026-11-24 | written, UNTESTED on GitHub |
