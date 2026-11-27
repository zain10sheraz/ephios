# Where the data in the report comes from

Every number, table and result in this report was produced by a tool run or read from a recorded source in this repository; none was typed in from memory without a source. This page names the source of each kind of data, how it was produced, and which parts are **judgement** (made by the team, with Claude Code assistance as recorded in `AI_USE_RECORD.md`) and not measurement. Each member should be able to open the raw file behind any number in the viva.

## 1. Measured data (raw output is committed)
| Data in the report | Raw source in the repository | How it was produced |
|---|---|---|
| Unit tests, statement and branch coverage of the 16 gate modules | `reports/coverage_unit.txt`; `scripts/run_unit_coverage.ps1` | coverage.py run of `tests/team` (`scripts/gate_modules.txt` lists the modules) |
| Mutation scores, 1,079 mutants, survivors | `reports/mutation/*.jsonl`, `reports/mutation/*.sqlite`, `reports/mutation/survivor_analysis.csv`; `scripts/mutation_summary.py`, `scripts/build_survivor_table.py` | Cosmic Ray sessions on an isolated copy of the code; the scripts count results from the session databases |
| SonarQube metrics (bugs, smells, duplication, coverage, ratings) | `reports/sonar_metrics*.txt`; the gate verdict of every pull request in the GitHub Actions log (`scripts/check_sonar_gate.py`) | SonarQube Community queried through its web API after each scan |
| Cyclomatic complexity (hand calculation vs tool) | `docs/team/CYCLOMATIC_COMPLEXITY.md`, `scripts/cyclomatic_ast.py` | CFG counted by hand and by an AST counter, compared with SonarQube |
| Defect before/after runs | `reports/defect00*_before_fix.txt`, `reports/defect00*_after_fix.txt`, live probes | the same tests/probes run on the unfixed and the fixed code |
| API results: 477 tests, 409 generated cases, coverage 14/14, 46/46, 80/80 | `reports/api/pytest_full_run.txt`, `reports/api/junit.xml`, `reports/api/api_coverage.md`, `reports/api/observed_raw.json`, `test_data/api_cases.json`, `reports/api/regeneration_demo.txt` | pytest against a real server process; the harness records every real HTTP request (`observed_raw.json`) and `scripts/api_coverage.py` compares it with the OpenAPI spec; the generator `scripts/generate_api_data.py` reads `test_specs/openapi.yaml` |
| Browser tests: 51 passed, access matrix | `reports/e2e/pytest_full_run.txt`, `reports/e2e/junit.xml`, `reports/e2e/playwright_report.html`, `reports/e2e/access_matrix.md` | Playwright (Chromium) against a real server; the access-matrix file is written by the test itself, including the observed status and the final URL |
| Accessibility: axe and Lighthouse findings, before/after scores | `reports/accessibility/axe_*.json`, `reports/accessibility/lighthouse_*.json`, `reports/accessibility/comparison.md`, `regression_before_fix.txt`, `regression_after_fix.txt` | `@axe-core/playwright` (`scripts/axe_scan.mjs`) and Lighthouse (`scripts/run_lighthouse.py`) on a running app; `scripts/compare_accessibility.py` merges them by rule id; the contrast ratios (3.47:1, 3.73:1) are read from the axe result field `contrastRatio` |
| ZAP passive scan: 166 URLs, 299 alerts, 10 types | `reports/security/zap_alerts.json`, `reports/security/zap_urls.json`, `reports/security/zap_run.txt` | OWASP ZAP 2.17.0 as a proxy while the browser tests ran; alerts fetched from ZAP's API by `scripts/run_zap_passive.py` |
| Dependency audit: 177 packages, 4 advisories | `reports/security/pip_audit.json`, `reports/security/pip_audit_packages.txt` | `pip-audit` on the project environment |
| Performance: p95, requests per second, failure % | `reports/performance/k6_vus*_run*.json` and `.txt` | k6 `--summary-export`; the table `reports/performance/k6_summary.md` is recomputed from the JSON by `scripts/k6_summary.py` |
| Recovery tests | `reports/api/recovery_api_run.txt`, `tests/team/api/test_failure_recovery_api.py`, `tests/team/e2e/test_failure_recovery.py` | read-only database file during a signup, state read back, restore, retry |
| Defect list, severity/priority labels, status | GitHub Issues #1-#26; exports in `reports/evidence/github/` | issues created and labelled through the GitHub API |
| Pull requests, checks, merge commits | GitHub; exports in `reports/evidence/github/` (for example `pr_11.json`) | GitHub API |
| Commit counts per member | the Git history in the zip (`git shortlog`, `git log --author`) | counted from the repository |
| Request/response facts (cookie attributes, headers, CSRF refusal) | quoted in `docs/team/SECURITY.md` from real responses of the running app | HTTP requests to a local server; confirmed against `src/ephios/settings.py` |

## 2. Judgement (not measurement)
| Data | What it is |
|---|---|
| Likelihood and impact scores, risk levels (`RISK_REGISTER.md`) | the team's estimate on a 1-5 scale; the evidence column cites the runs |
| Severity and priority of defects, "major" and "minor" | triage decisions by the rules stated in `FINDINGS_REGISTER.md` |
| Residual risk and the HOLD decision (`TEST_COMPLETION_REPORT.md`) | evidence-based judgement from the measured results above |
| ZAP "assessment" column, root causes, 5 Whys, fishbone | written by the team after reading the source; the evidence (file and line) is quoted where it exists |
| Three-point estimates (`TEST_PLAN.md`) | prospective for areas 2 and 3, written retrospectively for area 1 (stated there) |
| **Effort hours** (`WORKLOG.md`, actuals in `TEST_PLAN.md`) | **approximate**, reconstructed from session activity, **not** timer measurements |
| Use-case flows and their expected results (`USE_CASES*.md`) | written from the requirements and from the behaviour of the running application; each expected message was read from the real page before it was asserted |

## 3. Corrections of wrong data (kept as record)
Data that was first written from memory or assumed and then corrected after checking the source: the test-data size of the performance run (first "about 50 events", real value 16 events and 15 shifts); the search-length limit in the OpenAPI spec (the application has none); the HTTP status of `PUT` on the create endpoint (403, not 405); the substitution of a Python port for `@axe-core/playwright` and the "ZAP not run" statement (both redone with the real tools); the exit criterion EC-04 (reported as not comparable, not as met). The AI-use record lists these corrections.

## 4. How to check a number yourself
Open the raw file in the first table, or rerun the command in `SETUP.md`. Example: the k6 table is recomputed by `python scripts/k6_summary.py` and is identical to `reports/performance/k6_summary.md`.
