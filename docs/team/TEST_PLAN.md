# Test plan - Ephios (events and signup), SE3002 final project

Version 0.2 - 2026-11-24 - owners: all members (shared document). Updated as work proceeds; see "Plan changes" at the end.

## 1. Scope
- **Application under test:** Ephios, upstream https://github.com/ephios-dev/ephios (MIT), baseline commit `d12e76cd2b5b422177176506b0b6b9393dbc10e5`; fork https://github.com/zain10sheraz/ephios.
- **Workflows:** WF1 Event and Shift Management; WF2 Participant Signup (see `REQUIREMENTS.md`, FR-01..FR-09, BR1-BR6, BR-W1..W5).
- **Shared record:** `Shift` (times, signup_until, maximum participants) and `Event.active`; changed by WF1, read by WF2.
- **Roles:** Planner (`planner@sqe.test`) and Volunteer (`volunteer@sqe.test`).
- **In scope:** unit/white-box, API/integration (forms + read-only REST), browser E2E, usability/accessibility, security (access matrix, ZAP passive, dependency audit), performance and recovery, static analysis, mutation, CI.
- **Out of scope:** federation, guests, questionnaires, notifications delivery, PDF export, mobile PWA, upstream's own test suite (earns no marks), external identity providers.
- **Not testable here (stated honestly):** translations (no `msgfmt` installed; UI runs in English); MySQL/Postgres back-ends (we use SQLite).

## 2. Approach by risk level (from `RISK_REGISTER.md`)
| Risk level | Risks | Technique and depth |
|---|---|---|
| High (>= 15) | PR-01 inactive event, PR-02 deadline boundary, PR-03 capacity, PJ-01, PJ-02 | Complete decision/boundary/state coverage; unit + integration + E2E; 100 % statement+branch; MCC and MC/DC on critical decisions; mutation >= 90 %; fix with regression test |
| Medium (8-12) | PR-04..PR-07, PR-10, PR-11 | EP + 3-point BVA, state-transition and decision-table tests; at least unit + one higher level |
| Low (<= 6) | PR-09 | Single measured check (k6) against stated limit |

Techniques applied wherever they fit: equivalence partitioning (one invalid value per test), 3-point boundary value analysis at every limit, decision tables for every rule with 2+ conditions, state-transition tests (every allowed transition plus at least one disallowed per state), use-case testing for E2E.

## 3. Roles and ownership (examined in the viva)
| Member | Area | Deliverables |
|---|---|---|
| Zain Sheraz (zain10sheraz) | 1: static analysis, white-box, mutation, CI | SonarQube, complexity, unit tests, MCC/MC-DC, Cosmic Ray, CI gate, defects #1 #4 |
| Manan (MannanJafferyyy) | 2: API testing and data generation | OpenAPI spec, EP/BVA generator, API + integration tests, cross-workflow checks |
| Sujawal (sajawalkhan01; branch `sajawal`) | 3: use cases, usability, accessibility, security, performance | 4 use cases with 2 alt + 2 exception flows, Playwright, Lighthouse/axe, ZAP, pip-audit, k6, recovery test |
Shared: requirements, test plan, estimates, risks, traceability, reports, RCA, final PDF/ZIP.

## 4. Environment
Windows 11, 7.7 GB RAM; Python 3.12.10, Django 5.2.17, uv, Node 24.15.0; SQLite database; pytest 9.0.3, pytest-django 4.14.0, coverage 7.17.2, Cosmic Ray 8.9.0, SonarQube Community 26.11 (Docker), ruff. Setup, seed and reset: `docs/team/SETUP.md`, `scripts/reset_env.ps1`. CI: GitHub Actions on `ubuntu-latest`.

## 5. Test data
Synthetic only: accounts in `scripts/seed_test_data.py` (admin, planner, two volunteers, `*@sqe.test`), upstream sample event "Concert Medical Service", pytest fixtures for events/shifts/groups. Reset between runs with `scripts/reset_env.ps1`. API/BVA data will come from the generator reading the OpenAPI spec.

## 6. Schedule (4 days: 2026-11-23 .. 2026-11-26)
| Day | Planned | Status on 2026-11-24 evening |
|---|---|---|
| 1 Setup/planning | install, seed, scope, requirements, risks | done (setup, requirements, risk register draft) |
| 2 Core testing | unit + coverage + MCC, API tests, generator, Playwright | Zain part done; API/generator/Playwright NOT STARTED by teammates |
| 3 Advanced | Sonar, mutation, CI, Lighthouse/axe, ZAP, audit, k6, recovery | Zain part done early; others not started |
| 4 Defects/final | issues, RCA, Pareto, reports, PDF, ZIP | defects/RCA drafted; PDF not started |

## 7. Entry, exit, suspension and resumption criteria
- **Entry:** app runs from a clean checkout; seed/reset scripts work; test accounts log in.
- **Exit (measurable, see `RISK_REGISTER.md`):** EC-01 100 % coverage of 5 business-logic modules; EC-02 no open major defect; EC-03 mutation kill rate >= 90 %; EC-04 p95 <= 500 ms and < 1 % failures at 5 users; EC-05 all >= 4 role checks as expected.
- **Suspension:** environment unusable (e.g. Docker/RAM exhaustion), baseline tests failing on unmutated code, or GitHub unavailable for CI evidence.
- **Resumption:** environment restored and baseline test run green.

## 8. Risks
See `RISK_REGISTER.md` (10 product, 3 project). Project risks that already occurred: PJ-01 (RAM exhaustion froze Docker twice; scans failed twice) and a GitHub network outage on 2026-11-24 delayed PR #5.

## 9. Estimation (three-point, hours; E = (O + 4M + P) / 6)
Honesty note: estimates for Zain's areas below were written **after** the work (retrospective, from the worklog) because no estimates existed on Day 1; they are labelled so and the report must say that. Remaining areas are prospective.

| Area | O | M | P | E | Actual so far | Basis |
|---|---|---|---|---|---|---|
| Setup and environment | 1 | 2 | 4 | 2.2 | 1.0 (+ ~3 h Docker/RAM trouble) | worklog (retrospective) |
| White-box unit tests + coverage + MCC/MC-DC (+ HTTP tests added later) | 3 | 5 | 9 | 5.3 | **~13.5** (scope grew from 5 to 16 modules and from unit to HTTP tests) | worklog (retrospective) |
| SonarQube + complexity | 1 | 2 | 4 | 2.2 | ~2.5 | worklog (retrospective) |
| Mutation testing + analysis | 3 | 5 | 8 | 5.2 | ~8.5 (4 modules, 113 survivors analysed) | worklog (retrospective) |
| CI gate + PRs | 2 | 4 | 7 | 4.2 | ~8 (four PR cycles incl. real blocks and a GitHub outage) | worklog (retrospective) |
| API tests + generator + OpenAPI (Manan) | 5 | 8 | 14 | 8.5 | **~13.5** = 8.5 (suite) + 2.0 (follow-up tests) + 3.0 (use cases UC3, UC4); 1.6 times the estimate | prospective estimate, actual from `WORKLOG.md` (approximate) |
| E2E + use cases (Sujawal) | 5 | 8 | 12 | 8.2 | area 3 rows together: see the total below | prospective |
| Usability/accessibility | 2 | 3 | 5 | 3.2 | in the area 3 total | prospective |
| Security | 2 | 3 | 5 | 3.2 | in the area 3 total | prospective |
| Performance + recovery | 2 | 4 | 6 | 4.0 | in the area 3 total | prospective |
| Documents + PDF | 4 | 6 | 10 | 6.3 | ~6 so far, PDF not started | prospective |
Area 3 total (rows E2E, usability, security, performance): three-point E = 18.6 h, actual **about 14.0 h** (4.0 use cases and browser tests + 2.5 accessibility + 2.0 performance and security + 2.0 management items + 3.5 follow-up with the real axe, ZAP and API-level recovery; approximate, from `WORKLOG.md`), 0.75 times the estimate. Zain's use cases UC5 and UC6 and the completion report took about 3.5 h that no estimate covered. All effort figures after area 1 are approximate and reconstructed from session activity.
Reading: for Zain's area the actual effort (about 38 h, approximate and reconstructed from session activity) is well above the retrospective three-point total (about 17 h) because the scope grew during the work (more modules, HTTP tests, four defect cycles) and because machine stalls from RAM pressure cost hours. The final actual-versus-estimate comparison, including the other members' areas, belongs in the test completion report.

## 10. Plan changes
- 2026-11-24: SonarQube scope narrowed from the whole app to the business-logic folders (the whole app froze the machine); mutmut replaced by Cosmic Ray (needs fork(), no Windows support); upstream's CI workflows also run on PRs to `main` and are not required checks.
