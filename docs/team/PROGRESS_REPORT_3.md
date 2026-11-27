# Weekly progress report 3 (project day 4: 2026-11-26) - area 2

*Historical report: status on the date above; current status in `PROGRESS_REPORT_4.md` section 5.*

Author: Manan (GitHub MannanJafferyyy) with Claude Code assistance (recorded in `AI_USE_RECORD.md`). Previous: `PROGRESS_REPORT_2.md`.

## 1. Progress against plan
| Plan item | Owner | Status | Evidence |
|---|---|---|---|
| OpenAPI spec of events/signup API | Manan | **done** (14 operations, extensions documented) | `test_specs/openapi.yaml` |
| EP / 3-point BVA generator + regeneration demo | Manan | **done** (409 cases from 80 inputs) | `scripts/generate_api_data.py`, `reports/api/regeneration_demo.txt` |
| API / integration tests with post-conditions | Manan | **done**: 476 tests, 476 passed in one clean run (14 min 21 s) | `reports/api/pytest_full_run.txt`, `junit.xml` |
| Cross-workflow validation | Manan | **done** (11 tests) | `tests/team/api/test_cross_workflow_api.py` |
| API coverage criteria | Manan | **done**: operations 14/14, documented responses 46/46, inputs 80/80 | `reports/api/api_coverage.md` |
| Endpoint weaknesses reported | Manan | **done**: issues #12 #13 #14 (minor, open, not fixed) | `API_TESTING.md` section 5 |
| Playwright use cases, usability, accessibility, security, performance | Sajawal | not started (branch `sajawal` at baseline) | - |

## 2. Metrics
| Metric | Value |
|---|---|
| requirements with an executed passing test | **9 / 9 = 100 %** (FR-04 closed by the REST tests; was 8 / 9) |
| API tests | 476 (409 generated EP/BVA, 67 hand-written) |
| defects reported by area 2 | 3, all minor (design-level API weaknesses) |
| defects in the application proven by the generated cases | 0 (the 29 first-run failures were wrong assumptions in spec/generator/tests, corrected) |

## 3. Variances and control actions
| Variance | Cause | Control action |
|---|---|---|
| First generated run: 29 of 425 cases failed | cross-field rules, a limit that does not exist, overlapping shifts of one volunteer | spec, generator and test set-up corrected from observed behaviour; no assertion weakened (`API_TESTING.md` section 4) |
| Invalid signup cases passed for the wrong reason | overlap rejection masked the invalid value | post-condition checks (row counts, read-back) added to every generated write case |
| API suite needs a real server (8-15 min) | black-box requirement | separate CI job `api-tests-black-box`, excluded from the unit gate |

## 4. Open items
Area 3 (Sajawal) not started; final completion report, PDF and ZIP; `api-tests-black-box` is not a required check.

**Update 2026-11-26 evening:** area 2 was merged into `main` by PR #15 (merge commit `195a9eb5`); all 21 checks passed, including the three required ones and the new `api-tests-black-box` job. Area 3 (Sajawal) is the only area still not started.
