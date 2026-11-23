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

*Branch figure covers only the branches Sonar could attribute in the reported files; do not quote it as scope-wide.
Highest-complexity files: `core/models/events.py` (66), `named_teams.py` (66), `core/views/event.py` (63).
Top smell rules: python:S9073 (5), S1192 duplicated string literal (4), S117 naming (3), S6553 (2).

## Honest notes
- The first scans failed (bind-mount file loss, Docker out of memory); only the final successful runs are reported.
- Whole-scope coverage of 9.5 % is **low**; the 100 % claim applies only to the three modules above.
- Quality profile choice matters (0 vs 18 smells); we report both.
