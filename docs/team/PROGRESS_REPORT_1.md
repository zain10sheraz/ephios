# Weekly progress report 1 (project days 1-2: 2026-11-23 .. 2026-11-24)

Author: Zain Sheraz with Claude Code assistance (see AI-use record). Status date: 2026-11-24 evening.

## 1. Progress against plan
| Plan item (4-day plan) | Planned | Actual | Status |
|---|---|---|---|
| Day 1: setup, scope, requirements, risks | done by end Day 1 | environment, seed/reset, `REQUIREMENTS.md`, `RISK_REGISTER.md` draft | **done** (requirements not yet reviewed by Manan/Sujawal) |
| Day 2: unit tests + coverage + MCC/MC-DC | Zain | 197 team tests; 100 % statement and branch on 5 modules; 2 MCC/MC-DC tables | **done** |
| Day 2: API tests, OpenAPI, generator | Manan | nothing committed on branch `manan` | **NOT STARTED** |
| Day 2: Playwright use cases | Sujawal | nothing committed on branch `sajawal` | **NOT STARTED** |
| Day 3: SonarQube + complexity | Zain | two real scans (core / comprehensive profile); V(G) hand = 6 | **done early** |
| Day 3: mutation + 2 custom operators + 15 survivors | Zain | 415 mutants, 3 custom operators, 92 survivors analysed, 97.3 % kill rate | **done early** |
| Day 3: CI gate, fix PR, blocked PR | Zain | PR #2 (fix, green after a real Sonar block), PR #3 (blocked), PR #5 (DEFECT-002 fix, running) | **done** (PR #5 pending result) |
| Day 3: Lighthouse/axe, ZAP, pip-audit, k6, recovery | Sujawal | nothing | **NOT STARTED** |
| Day 4: defects, RCA, Pareto, reports | shared | 2 defects filed and RCA written; this report; PDF not started | in progress |

## 2. Defects (GitHub Issues)
| ID | Title | Severity | Priority | Status | Found by |
|---|---|---|---|---|---|
| #1 DEFECT-001 | inactive event still accepts signup | major | high | closed (fixed PR #2) | white-box unit test |
| #4 DEFECT-002 | ShiftForm KeyError / HTTP 500 on invalid date or start time | major | medium | fix in PR #5 (pending CI) | EP probe + live server |
Triage decisions: both confirmed, fixed with regression tests, no duplicates, none rejected. Root cause analysis: `RCA.md`.

## 3. GQM metrics
**Goal G1 - white-box quality of the business-logic modules.**
| Question | Metric | Value | Reading |
|---|---|---|---|
| Is the logic executed by tests? | statement / branch coverage (5 modules, 672 statements, 94 branches) | 100 % / 100 % | meets EC-01 |
| Do tests actually detect faults? | mutation kill rate (3 modules, 415 mutants) | round 1: 77.6 % -> final 97.3 % | coverage alone hid 92 gaps (81 killable, 11 equivalent) |
| Is the code simple enough to test? | cyclomatic complexity, scope total (Sonar) | 707 (cognitive 419) | highest files: `models/events.py` 66, `named_teams.py` 66, `views/event.py` 63 |

**Goal G2 - defects found and their handling.**
| Question | Metric | Value | Reading |
|---|---|---|---|
| How dense are defects? | defects per KLOC (2 / 4.747 ncloc in scope) | **0.42 per KLOC** | low absolute number; only white-box area tested so far |
| Are fixes stable? | reopen rate (reopened / closed) | 0 / 1 = **0 %** | one closed defect only, too early to conclude |
| Severity mix | major / minor | 2 / 0 | both major: unhandled error and unenforced rule |

**Goal G3 - requirement coverage.**
| Question | Metric | Value | Reading |
|---|---|---|---|
| How many requirements have an executed test? | requirements coverage | **61 %** (5.5 / 9; strict 44 %) | gaps FR-04 (REST), FR-08 (duplicates) need API tests |
| Are business rules covered? | rules with tests | 11 / 11 (BR1-BR6, BR-W1..W5) + BR-V | all executed and passing |

Quality-gate indicators: SonarQube comprehensive profile 18 smells initially, 13 after cleanup (upstream-owned); 0 bugs, 0 vulnerabilities; duplication 0.5 %; default Sonar gate FAILED (coverage 9.5 % of scope < 80 %, evidence EV-005a).

## 4. Variances, causes and control actions
| Variance | Cause | Control action |
|---|---|---|
| Teammates' areas (API, E2E, security, performance, usability) not started; branches at baseline | availability unknown to the author | ask Manan and Sujawal to start today; interfaces given in `REQUIREMENTS.md`, plan, risk register; if not started by Day 3 evening, report NOT RUN and cut scope |
| Docker/WSL froze twice, SonarQube scan failed twice | 7.7 GB RAM, SonarQube + Docker + mutation together | capped WSL memory, run heavy tools sequentially, narrowed Sonar scope, shut Docker down when idle |
| GitHub network outage during PR #5 | external | retried; commits kept locally |
| CI blocked PR #2 on first run (21 > 18 smells) | our own new tests added 3 smells | fixed the tests and tightened the ratchet to 13 (the gate worked as intended) |
| Our code failed upstream ruff rules (9 files, 16 findings) | not checked locally before | formatted and fixed; ruff now clean on our files |

## 5. Plan for the next period
1. Merge PR #5 after green CI; refresh coverage, Sonar and mutation numbers for the final report.
2. Chase the two teammates; review the shared documents together (all three are examined on them).
3. Start the final PDF skeleton; collect remaining screenshots (EV-008, EV-009, EV-015b, EV-016).
4. Update estimates versus actuals and the risk register once API/E2E/security/performance results exist.

---
## Update 2026-11-24 late evening (same reporting period, after the first version of this report)
| Item | Earlier today | Now |
|---|---|---|
| Team tests | 197 | **333** (unit + HTTP integration; run in CI) |
| Modules at 100 % statement+branch | 5 | **16** (1,344 statements, 176 branches; `COVERAGE_SCOPE.md`) |
| MCC / MC-DC | 2 decisions | **every compound decision of the critical module** (D1-D8 + error routing table) |
| Defects | 2 (1 fixed) | **4, all fixed and closed** (#1, #4, #6, #7), each through a PR with green CI |
| Requirements coverage | 61 % (5.5 / 9) | **89 % (8 / 9)**; only FR-04 (REST read) has no test |
| Mutation | 3 modules, 97.3 % | WF1 forms run in progress (136 mutants) |
| CI | PRs #2 (green after block), #3 (blocked), #5 | + PR #8 all green on the 16-module gate (unit 1m19, sonar 2m44, mutation 9m03) |

GQM update: defect density 4 / 4.747 KLOC = **0.84 per KLOC**; reopen rate 0 / 4 = **0 %**; severity mix 2 major / 2 minor.
Pareto by root cause: input/partition not handled 3 of 4 defects (75 %).
Remaining schedule risk unchanged: Manan's (API) and Sujawal's (E2E, usability, security, performance) areas not started.
