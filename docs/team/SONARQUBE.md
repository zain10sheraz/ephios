# SonarQube analysis (SonarQube Community 26.11, run 2026-11-23)

Scope (`sonar-project.properties`): `core/signup`, `core/models`, `core/views/event.py`, `core/views/signup.py`,
`plugins/basesignupflows`, `plugins/baseshiftstructures`, `api` (59 files, 4,747 ncloc) + our tests in `tests/team`.
Raw output: `reports/sonar_metrics_run1_core_profile.txt`, `reports/sonar_metrics_run2_comprehensive.txt`.

| Metric | Run 1 (Sonar way core, 232 rules) | Run 2 (Sonar way comprehensive, 407 rules) | What it shows |
|---|---|---|---|
| Code smells | 0 | **18** (5 critical, 9 major, 4 minor) | maintainability problems; run 1 was too lenient to be informative |
| Bugs / Vulnerabilities / Hotspots | 0 / 0 / 0 | 0 / 0 / 0 | no reliability or security findings in scope |
| Technical debt (sqale_index) | 0 min | **104 min** | estimated fix effort for the smells |
| Ratings (reliability/security/maintainability) | A/A/A | A/A/A | |
| Cyclomatic complexity | 707 | 707 | number of independent paths; higher = more tests needed |
| Cognitive complexity | 419 | 419 | how hard the code is to read |
| Duplication | 0.5 % (2 blocks, 30 lines) | same | copy-paste risk is low |
| Coverage (whole scope) | 9.5 % line / 100 % branch* | same | most of the scope is not unit tested by us (yet) |
| Coverage of the 3 tested modules | 100 % line, 100 % branch each | same | `participant_validation.py`, `structure/common.py`, `stats.py` |

*Sonar reports 100 % branch coverage next to 7.9 % line coverage; we did not investigate the reason, so do not quote the branch figure as scope-wide.
Highest-complexity files: `core/models/events.py` (66), `named_teams.py` (66), `core/views/event.py` (63).
Top smell rules: python:S9073 (5), S1192 duplicated string literal (4), S117 naming (3), S6553 (2).

## Honest notes
- The first scans failed (bind-mount file loss, Docker out of memory); only the final successful runs are reported.
- Whole-scope coverage of 9.5 % is **low**; the 100 % claim applies only to the three modules above.
- Quality profile choice matters (0 vs 18 smells); we report both.

## Quality gate (from Zain's screenshots EV-005a/b)
Default "Sonar way" gate: **FAILED**, 2 conditions: (1) 13 issues on new code (gate requires 0) and
(2) 9.5 % coverage on new code (required >= 80 %). On a first analysis all code counts as "new code".
Interpretation: the failure is genuine for the scoped modules - most of the scoped code is not unit tested by us yet.
The CI gate thresholds (see CI section) will be set from this evidence, not copied from the default.
Sonar also warns the embedded H2 database is for evaluation only (acceptable for a local course instance).

## Final scan (2026-11-24, after all unit/HTTP tests; `reports/sonar_metrics_final.txt`)
Scope grew to 148 files / 5,010 ncloc (adds `core/forms/events.py`; sources unchanged otherwise). Profile: Sonar way comprehensive. The first attempt of this scan failed
(`Fail to download plugin [python]`: the SonarQube server was starved of RAM while a 6-minute test run was active) and was repeated once the machine was quiet; only the successful scan is reported.

| Metric | First report (2026-11-23) | Final | Reading |
|---|---|---|---|
| Code smells | 18 | **14** | all 14 are upstream-owned code; our own code adds none |
| Bugs / vulnerabilities / hotspots | 0 / 0 / 0 | 0 / 0 / 0 | |
| Technical debt | 104 min | **81 min** | |
| Ratings (reliability / security / maintainability) | A / A / A | A / A / A | |
| Cyclomatic / cognitive complexity | 707 / 419 | 741 / 442 | grew because one more file joined the scope |
| Duplication | 0.5 % | 0.5 % (2 blocks) | |
| Coverage of the whole scope | 9.5 % | **48.3 %** (line 45.2 %, branch 100 % as reported by Sonar) | only code outside our 16 tested modules is uncovered (calendar/copy views, disposition, REST layer, alternative structures; see `COVERAGE_SCOPE.md`) |
| Coverage of the 16 gate modules | 3 modules at 100 % | **16 of 16 at 100 %** | `scripts/check_sonar_gate.py` exits 0 |

The default SonarQube "Sonar way" quality gate would still FAIL on coverage of new code (< 80 %) because the scope includes untested upstream code; our custom thresholds (`docs/team/CI_GATES.md`) are what CI enforces.
