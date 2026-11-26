# Risk register and exit criteria (DRAFT for team review)

Scoring: Likelihood (L) and Impact (I) 1-5; score = L x I. Level: 1-6 low, 8-12 medium, 15-25 high.
Level decides technique and depth. Evidence column cites real findings from runs so far; rows without evidence
are plain expectations and are labelled so.

## Product risks
| ID | Risk | L | I | Score | Level | Technique / depth | Evidence so far |
|---|---|---|---|---|---|---|---|
| PR-01 | Signup accepted for a deactivated event (rule not enforced) | 4 | 4 | 16 | High | Unit (decision), integration POST, E2E; fix + regression test | **Confirmed and fixed: DEFECT-001 (Issue #1, PR #2)** |
| PR-02 | Signup accepted after the signup deadline (boundary error, BR1) | 3 | 5 | 15 | High | 3-point BVA unit + API at deadline +-1 s; mutation on comparison | BVA tests pass (test_signup_rules) |
| PR-03 | Capacity exceeded: more confirmed participants than maximum (BR4, race/duplicate) | 3 | 5 | 15 | High | 3-point BVA, repeated-request test, concurrent k6 load | unit BVA pass; concurrency not yet tested |
| PR-04 | Invalid state transitions allowed (rejected user signs up again, BR3) | 3 | 4 | 12 | Medium | State-transition tests (all allowed + 1 disallowed per state) | unit tests pass |
| PR-05 | Overlapping shifts both confirmed for one volunteer | 3 | 4 | 12 | Medium | Decision table + partial-overlap tests | unit tests pass; mutation survivors found and killed (see MUTATION.md) |
| PR-06 | Volunteer can perform Planner actions (broken access control) | 2 | 5 | 10 | Medium | Playwright role matrix (4+ decisions), source review of permission mixins | not yet run |
| PR-07 | Session/CSRF weaknesses on state-changing POSTs | 2 | 4 | 8 | Medium | ZAP passive scan, cookie attribute review | one CSRF error seen on first login in a normal browser (stale cookie suspected, not reproduced in incognito) |
| PR-08 | Key screens inaccessible (missing labels, contrast, keyboard) | 3 | 3 | 9 | Medium | Lighthouse + axe-core, keyboard test | not yet run |
| PR-09 | Slow signup under concurrent users | 2 | 3 | 6 | Low | k6 1 vs 5 VUs, p95 target | not yet run |
| PR-10 | WF1 changes (capacity/deadline) not reflected in WF2 (shared-record inconsistency) | 3 | 4 | 12 | Medium | Cross-workflow integration tests with read-back | **Covered 2026-11-26**: 11 cross-workflow API tests over HTTP, all pass; no inconsistency found (`API_TESTING.md`) |
| PR-11 | Invalid shift date/time input crashes the form (HTTP 500) instead of showing an error | 3 | 3 | 9 | Medium | EP with one invalid value per field, live-server probe | **Confirmed and fixed: DEFECT-002 (Issue #4, PR #5)**; live probe 500 -> 200 |
| PR-12 | Helper endpoints and derived values mishandle unusual input (HTTP 500, wrong age rule) | 3 | 2 | 6 | Low | EP with invalid values per parameter; live-server probes | **Confirmed and fixed: DEFECT-003 (#6), DEFECT-004 (#7), PR #8** |

## Project risks
| ID | Risk | L | I | Score | Level | Mitigation | Evidence so far |
|---|---|---|---|---|---|---|---|
| PJ-01 | Tooling overloads the 7.7 GB laptop (SonarQube + Docker + mutation) | 5 | 3 | 15 | High | WSL memory cap, run heavy tools sequentially, scope scans, record effort | **Occurred**: Docker engine hung twice; SonarQube scan failed twice before success |
| PJ-02 | Four-day deadline: not all rubric items finish | 4 | 4 | 16 | High | Daily plan, report NOT RUN honestly, cut scope on 100 % "all logic" claim first | tracked in WORKLOG.md |
| PJ-03 | Teammates' areas (API, E2E, security, performance) not started yet, integration late | 5 | 5 | 25 | High | Branches created; interface = docs/team/REQUIREMENTS.md | **Occurred**: manan and sajawal have 0 commits after two project days (checked 2026-11-25) |

## Exit criteria (measurable; tied to highest risks)
| ID | Criterion | Target | Tied to | Actual (to fill from runs) |
|---|---|---|---|---|
| EC-01 | Statement and branch coverage of signup validation modules | 100 % | PR-01, PR-02, PR-04 | 100 % / 100 % on 16 modules (`docs/team/COVERAGE_SCOPE.md`) |
| EC-02 | No open defect of severity major or critical | 0 open | PR-01, PR-02, PR-03 | DEFECT-001 (PR #2), DEFECT-002 (PR #5), DEFECT-003/004 (PR #8) fixed, issues #1, #4, #6, #7 closed; 0 open defects of any severity at this moment -> MET (re-check at the end) |
| EC-03 | Mutation kill rate on business-rule modules | >= 90 % | PR-02, PR-03, PR-05 | 98.3 % / 94.5 % / 100 % / 98.5 % / 92.1 % / 98.9 % / 98.0 % / 98.0 % on 8 modules after killer tests (97.7 % overall, 1,079 mutants); MET |
| EC-04 | Performance: signup p95 and failure rate at 5 users | p95 <= 500 ms, < 1 % failures | PR-09 | not run |
| EC-05 | Role matrix: denied actions actually denied | 100 % of >= 4 checks | PR-06 | not run |

Release decision will be made from the Actual column at the end. EC-04 and EC-05 are not yet run, so no release decision is possible yet.
