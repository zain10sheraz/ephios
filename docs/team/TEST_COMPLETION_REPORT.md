# Test completion report (2026-11-27)

Project: SE3002 final project on Ephios (upstream `ephios-dev/ephios`, baseline `d12e76cd2b5b422177176506b0b6b9393dbc10e5`, tag `baseline-upstream-d12e76cd`). Scope: module "events and signup", workflows **WF1** event and shift management and **WF2** participant signup (`REQUIREMENTS.md`). All numbers below come from real runs; the evidence is linked.

## 1. Area ownership (who is examined on what)

| Member | GitHub | Area | Browser use cases (two per member) |
|---|---|---|---|
| Zain Sheraz | zain10sheraz | 1: static analysis, white-box, mutation, CI | UC5, UC6 (`USE_CASES_ZAIN.md`) |
| Manan | MannanJafferyyy | 2: API testing, OpenAPI, EP/BVA generator, cross-workflow validation | UC3, UC4 (`USE_CASES_MANAN.md`) |
| Sajawal | sajawalkhanfake | 3: use cases, usability, accessibility, security, performance | UC1, UC2 (`USE_CASES.md`) |

Test management documents are shared. The AI-use record is `AI_USE_RECORD.md`.

## 2. What was tested (results)

| Activity | Result | Evidence |
|---|---|---|
| Unit and coverage | 458 tests; 16 modules at 100 % statement and branch coverage; MCC and MC/DC of the critical module | `COVERAGE_SCOPE.md`, `MCC_MCDC.md` |
| Static analysis | SonarQube: 0 bugs, 0 vulnerabilities, 0 hotspots, 14 smells (all upstream's), 0.5 % duplication | `SONARQUBE.md`, `reports/sonar_metrics_final.txt` |
| Mutation | Cosmic Ray, 8 modules, 1,079 mutants, 78.2 % -> 97.7 %; 235 survivors analysed; 3 custom operators | `MUTATION.md` |
| CI gate | three required checks (unit 100 %, mutation, SonarQube thresholds) plus API and browser jobs, which must also become required (`scripts/require_all_checks.ps1`, status in CI_GATES.md); a blocked demonstration PR (#3) and fix PRs | `CI_GATES.md`, PRs #2 #3 #5 #8 #11 |
| API and integration | OpenAPI of 14 operations, generator (409 EP/BVA cases), 477 black-box tests, operation coverage 14/14, documented responses 46/46, inputs 80/80, post-conditions read back | `API_TESTING.md`, `reports/api/` |
| Browser end to end | 6 use cases, 36 flows, plus usability, keyboard, access matrix, recovery, accessible-name regression: 51 Playwright tests in real Chromium | `USE_CASES*.md`, `reports/e2e/` |
| Usability and accessibility | axe-core (`@axe-core/playwright`) and Lighthouse on 4 key screens; 2 critical rules fixed on the shift form (Lighthouse 80 -> 89) | `ACCESSIBILITY.md`, `reports/accessibility/` |
| Security | access matrix 7 decisions; ZAP 2.17.0 passive scan while the browser tests ran (166 URLs, 298 alerts, 10 types); pip-audit 175 audited packages (2 local packages skipped) | `SECURITY.md`, `reports/security/` |
| Performance and recovery | k6: p95 99-104 ms (1 user), 505-506 ms (5 users), 0 % failures in the first runs; 17.8 ms and 115 ms in a second set on a quiet machine (limits met in both); recovery test (storage down, retry, no duplicate) at API and browser level | `PERFORMANCE.md`, `reports/performance/` |

## 3. What was not tested
Signup under load on PostgreSQL/MySQL (measured on SQLite only, see section 7 and `PERFORMANCE.md` 1c); capacity races on PostgreSQL/MySQL (only SQLite: a simultaneous write can fail with `database is locked`); Firefox and WebKit; manual screen-reader testing; ZAP active scanning (the brief asks for passive only); a production deployment (HTTPS, Secure cookies, HSTS); upstream modules outside the two workflows (calendar rendering, event copy, bulk delete, disposition, alternative structures); mutation testing outside 8 modules; BR5 over HTTP (not reachable: saving a shift activates its event, covered at integration level).

## 4. Deviations from the plan
* Estimates for area 1 were written after the work (retrospective, labelled in `TEST_PLAN.md`); area 2 and 3 efforts in `WORKLOG.md` are approximate.
* The unit scope is 16 business-logic modules, not every server-side file; the exclusions are justified in `COVERAGE_SCOPE.md`.
* k6 limits were set once for both workloads (p95 < 800 ms, < 1 % failures) before testing, not separately per workload. The register's EC-04 (signup p95 <= 500 ms at 5 users) concerns signup; the measured operation was the event list. Separate limits for the signup write (p95 < 500 ms, < 1 % failures) and the script `scripts/k6_signup.js` were added in the course review (`PERFORMANCE.md` section 1b); the signup run was done on 2026-11-28 and shows EC-04 not met on SQLite.
* The recovery failure is simulated with a read-only SQLite file, not with a test double of an external dependency.
* The use cases of Zain and Manan were added after the first areas were merged; they were not part of the first plan.
* SonarQube and ZAP were run through Docker as a convenience; the tools are the same as a local installation.

## 5. Defects (16 reported, 5 closed, 11 open)

| Area | Issues | Status |
|---|---|---|
| 1 | #1 #4 #6 #7 (DEFECT-001..004) | closed, fixed through PRs #2 #5 #8, with regression tests |
| 2 | #12 #13 #14 (DEFECT-005..007, API weaknesses, minor) | open, not fixed (design level, tests assert observed behaviour) |
| 3 | #17 (DEFECT-008, major, accessible names) | closed, fixed and merged (PR #24) |
| 3 | #18 #19 #20 (DEFECT-009..011, major, accessibility: contrast, positive tabindex, Select2 name) | **open** |
| 3 | #21 #22 #23 #25 #26 (minor: heading order, generic rejection message, soupsieve, CSP directives, language cookie) | open |

Root-cause analyses (5 Whys, fishbone, Pareto): `RCA.md`.

## 6. Residual risk per risk (`RISK_REGISTER.md`)

| Risk | Evidence | Residual |
|---|---|---|
| PR-01 inactive event accepts signup | DEFECT-001 fixed, unit and integration tests, mutation | Low |
| PR-02 deadline boundary | 3-point BVA unit, API, UC2-E2, UC4-E3 | Low |
| PR-03 capacity exceeded | BVA, API above-limit, simultaneous-signup tests (SQLite only) | Low-Medium (PostgreSQL untested) |
| PR-04 invalid state transitions | state tests unit and API, UC4 | Low |
| PR-05 overlapping shifts | decision-table unit tests, mutation | Low |
| PR-06 broken access control | 7 browser decisions, API access tests | Low |
| PR-07 session/CSRF | CSRF refusal, cookie review, ZAP (2 minor findings #25 #26) | Low |
| PR-08 inaccessible key screens | 2 critical rules fixed; contrast, tabindex, Select2 name still open | **Medium** |
| PR-09 slow signup | event list measured, signup not | **Medium (unknown)** |
| PR-10 WF1 change not reflected in WF2 | 11 cross-workflow API tests, UC3 | Low |
| PR-11 / PR-12 input crashes | DEFECT-002/003/004 fixed, EP/BVA suites | Low |
| PR-13 vulnerable dependency | soupsieve not reachable | Low |
| PJ-01 / PJ-02 / PJ-03 project risks | occurred (laptop memory, late start of areas 2 and 3); handled (heavy tools run one at a time, areas 2 and 3 completed) | closed |

## 7. Release criteria: actual versus target

| ID | Criterion | Target | Actual | Met |
|---|---|---|---|---|
| EC-01 | coverage of the business-logic modules | 100 % statement and branch | 100 % / 100 % on 16 modules | yes |
| EC-02 | open defects of severity major or critical | 0 | **3 open major** (#18 #19 #20) | **no** |
| EC-03 | mutation kill rate on business-rule modules | >= 90 % | 97.7 % overall (92.1-100 % per module) | yes |
| EC-04 | signup p95 and failure rate at 5 users | p95 <= 500 ms, < 1 % failures | signup at 5 users: p95 757 ms and 1,020 ms, **27-29 % failed** (HTTP 500 `database is locked`, SQLite); at 1 user p95 114-138 ms, 0 % failures; member's own quiet-machine run: p95 410 ms (met) but 22.33 % failed (not met) | **no (measured)** |
| EC-05 | denied actions actually denied (role matrix) | 100 % of >= 4 checks | 4 of 4 denied decisions (7 decisions in total) | yes |

## 8. Recommendation: **HOLD**
Three of five criteria are met. The release is held because EC-02 is not met (three major accessibility defects, #18 #19 #20, are open) and EC-04 is measured and not met for the signup operation (27-29 % HTTP 500 at 5 users on SQLite). Actions to reach a release decision: fix the colour contrast, the positive `tabindex` and the Select2 name (rerun axe and Lighthouse), rerun the signup load test on PostgreSQL (or accept the SQLite limit as a documented deployment constraint), and rerun the whole gate. No release blocker was found in the business rules, the access control or the dependencies.
