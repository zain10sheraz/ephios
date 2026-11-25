# Weekly progress report 2 (project day 3: 2026-11-25)

Author: Zain Sheraz with Claude Code assistance. Status time: 2026-11-25 midday. Previous report: `PROGRESS_REPORT_1.md`.

## 1. Progress against plan
| Plan item | Owner | Status | Evidence |
|---|---|---|---|
| Setup, scope, requirements, risks | all | done | `SETUP.md`, `REQUIREMENTS.md`, `RISK_REGISTER.md` |
| Unit tests, coverage, MCC/MC-DC | Zain | **done**: 458 tests, all passing; 16 modules at 100 % statement+branch (1,343 statements, 174 branches) | `COVERAGE_SCOPE.md`, `MCC_MCDC.md` |
| SonarQube + complexity | Zain | **done**: final scan, 16/16 gate modules at 100 %, 14 upstream smells | `SONARQUBE.md`, `reports/sonar_metrics_final.txt` |
| Mutation + custom operators + survivor analysis | Zain | **done for 8 modules** (1,079 mutants, 78.2 % -> 97.7 %); all 235 round-1 survivors analysed (210 killed, 23 equivalent, 2 unresolved) | `MUTATION.md` |
| CI gate, fix PR, blocked PR | Zain | **done**; early check of the final merge (draft PR #9) passed everything, upstream workflows included | `CI_GATES.md`, `reports/evidence/github/` |
| Defects + RCA + Pareto | Zain (shared) | **done**: 4 defects, all closed | `RCA.md`, issues #1 #4 #6 #7 |
| API tests, OpenAPI, generator | Manan | **NOT STARTED** (branch `manan` has 0 commits ahead of the baseline) | `git rev-list --count d12e76cd..origin/manan` = 0 |
| Playwright use cases, usability, accessibility, security, performance | Sujawal | **NOT STARTED** (branch `sajawal` has 0 commits ahead of the baseline) | `git rev-list --count d12e76cd..origin/sajawal` = 0 |
| Test completion report, final PDF/ZIP | shared | not started (depends on the two areas above) | - |

## 2. GQM metrics (updated)
| Goal | Metric | Value |
|---|---|---|
| G1 white-box quality | statement / branch coverage of the 16 gate modules | 100 % / 100 % |
| | mutation kill rate, 8 modules, 1,079 mutants | 97.7 % (round 1: 78.2 %) |
| | survivors analysed | 235 (210 killable and killed, 23 equivalent, 2 unresolved) |
| G2 defects | defects found / closed | 4 / 4 (2 major, 2 minor) |
| | defect density | 4 / 5.01 KLOC (Sonar ncloc 5,010) = **0.80 per KLOC** |
| | reopen rate | 0 / 4 = **0 %** |
| G3 requirements | requirements with an executed passing test | **8 / 9 = 89 %** (only FR-04, REST read, has none) |
| Quality gate | PRs run through the gate | 6 (#2, #3, #5, #8, #9, plus the two Sonar blocks inside #2 and #5); all fix PRs green, the demo PR #3 BLOCKED |

## 3. Variances and control actions
| Variance | Cause | Control action |
|---|---|---|
| Areas 2 and 3 have produced no commits after two project days | not known to the author | **escalated to the group**: Manan and Sujawal must start immediately; interfaces are documented (`REQUIREMENTS.md`, `TEST_PLAN.md`, `RISK_REGISTER.md`, `SQE_PROJECT.md`); the author offers to pair on setup. If nothing is committed by the end of day 3 the missing activities are reported as NOT RUN with the reason in the completion report, and the release decision is HOLD |
| Mutation on 4 more modules took about 4 hours | 7.7 GB laptop, Windows; Docker/WSL memory | run in the background, one module at a time; finished; also found that Cosmic Ray mislabels kills as incompetent on non-UTF-8 output, corrected in the evaluation scripts |
| GitHub network timeouts (twice) | external | retried, commits kept locally |
| Lint errors on our `tools/` found only by the early draft PR to `main` | upstream's lint environment lacks our mutation tooling | fixed with targeted `ty: ignore`; early check re-run green |

## 4. Risk register changes
PR-01/PR-11/PR-12 are confirmed and fixed; EC-01, EC-02, EC-03 are met; EC-04 (performance) and EC-05 (role matrix) are **not run** because they belong to area 3. PJ-03 (teammates late) has **occurred**: likelihood raised to 5, impact 5 (score 25).

## 5. Plan for the rest of day 3 and day 4
1. Get area 2 and area 3 started (the only real schedule risk).
2. (done) remaining mutation runs finished and reported.
3. After the other branches land: refresh coverage, Sonar and mutation numbers, write the test completion report, compare estimates with actual effort, assemble the PDF and ZIP, and run the final merge to `main` (only when the group asks).

**Update 2026-11-25 evening:** Zain's area was merged into `main` by PR #11 (merge commit `520edca3`; required checks unit-tests, mutation-score and sonarqube-thresholds passed; all 20 checks completed, none failed). The baseline is preserved by the tag `baseline-upstream-d12e76cd`. Areas 2 and 3 are still not started.
