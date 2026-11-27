# Weekly progress report 4 (project day 5: 2026-11-27) - area 3

Author: Sujawal (committed through the account `sajawalkhanfake`) with Claude Code assistance (recorded in `AI_USE_RECORD.md`). Previous: `PROGRESS_REPORT_3.md`.

## 1. Progress against plan
| Plan item | Owner | Status | Evidence |
|---|---|---|---|
| S1 use cases (2 use cases, 12 flows; team total 6 use cases, 36 flows) | Sujawal | **done** (UC3-UC6 of Manan and Zain: `USE_CASES_MANAN.md`, `USE_CASES_ZAIN.md`) | `USE_CASES.md` |
| S2 Playwright automation of every flow, post-conditions | Sujawal | **done**: 12 flow tests (36 for the team) | `tests/team/e2e/`, `reports/e2e/` |
| S3 usability tests (2) | Sujawal | **done** | `test_usability_keyboard.py` |
| S4 keyboard test | Sujawal | **done** | same file |
| S5 Lighthouse + axe-core | Sujawal | **done** (2 screens, both tools) | `reports/accessibility/`, `ACCESSIBILITY.md` |
| S6 fix one screen, before/after | Sujawal | **done** (shift form 80 -> 89, 2 critical rules 0) | `reports/accessibility/comparison.md` |
| S7 access matrix + role checks | Sujawal | **done** (7 decisions) | `SECURITY.md`, `reports/e2e/access_matrix.md` |
| S8 OWASP ZAP passive scan | Sujawal | **done** (ZAP 2.17.0 in Docker, 22 browser tests through the proxy, 166 URLs, 299 alerts; issues #25 and #26) | `SECURITY.md` section 5, `reports/security/zap_summary.md` |
| S9 dependency audit | Sujawal | **done** (177 packages, 4 advisories, not reachable) | `reports/security/pip_audit.json`, `pip_audit_packages.txt` |
| S10 performance k6 | Sujawal | **done** (limits met; EC-04 as written not met/not comparable) | `PERFORMANCE.md` |
| S11 failure and recovery | Sujawal | **done** (API/integration test with HTTP requests, as the brief asks, and the same scenario in the browser) | `tests/team/api/test_failure_recovery_api.py`, `tests/team/e2e/test_failure_recovery.py` |
| S12 management items | Sujawal | **done**: issues #17-#23, RCA, risk register, traceability | `RCA.md`, `RISK_REGISTER.md`, `TRACEABILITY.md` |

## 2. GQM metrics (updated)
| Goal | Metric | Value |
|---|---|---|
| G3 requirements | requirements with an executed passing test | 9 / 9 = 100 % (unchanged); E-level (browser) coverage 8 of 9 (FR-04 by design not) |
| G4 accessibility | Lighthouse accessibility score of the fixed screen | 80 -> 89 |
| | axe critical rules on the shift form | 2 -> 0 |
| G5 security | access decisions as expected | 7 / 7 |
| | dependency advisories reachable from the app | 0 of 4 |
| G6 performance | p95 at 5 users, GET /api/events/ | 505-506 ms (limit 800 ms met; EC-04 row 500 ms not comparable) |
| Defects | total in the project | 16 (area 1: 4 closed; area 2: 3 open minor; area 3: 9, 1 fixed and merged) |

## 3. Variances and control actions
| Variance | Cause | Control action |
|---|---|---|
| ZAP first run: 17 tests errored through the proxy | the host-side helpers tried to resolve the Docker-only name `host.docker.internal` | helpers use 127.0.0.1, only the browser uses the proxy name; rerun: 22 of 22 passed through ZAP |
| First browser run failed (Django test database vs Playwright event loop) | upstream marks every test `django_db` | conftest removes the marker for `tests/team/e2e` only |
| EC-04 not met as written | the register's row concerns signup, the measured operation was the event list | reported as not comparable; the limit was not changed after seeing the result |
| Release decision | open defects #18-#20 (major accessibility) | **HOLD** until fixed or accepted (`RISK_REGISTER.md`) |

## 4. Open items
Pull requests for the follow-up work (real `@axe-core/playwright`, ZAP, API-level recovery test, use cases of the other two members); screenshots by the team members (course rule); final completion report, PDF and ZIP.
