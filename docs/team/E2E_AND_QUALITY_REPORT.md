# Area 3 report: browser end-to-end tests, usability, accessibility, security, performance and recovery

All results come from real runs against a real Ephios process (temporary SQLite database, seeded synthetic accounts) driven by real Chromium through Playwright. Nothing is mocked. Screenshots are not produced by the test suite; the team member takes any screenshot himself (course rule).

## 1. Flow inventory and results (`docs/team/USE_CASES.md`)
Each use case has a main flow, 2 alternative and 3 exception flows. Every flow is one Playwright test that logs in through the real login form, asserts the **result shown on the screen** and the **post-conditions** read back from stored state (REST API and database row counts).
| Flow | Test | Screen result asserted | Post-condition asserted |
|---|---|---|---|
| UC1-M | `test_uc1_main_planner_creates_event_and_shift` | banner "... has been saved", event heading | one shift stored, `max_count` 5, event active and readable |
| UC1-A1 | `test_uc1_a1_request_flow_makes_later_signups_requested` | - | flow `request_confirm` stored; a later signup is REQUESTED (0) |
| UC1-A2 | `test_uc1_a2_planner_raises_the_capacity_of_the_shift` | banner "... has been saved" | capacity 8, still one shift |
| UC1-E1 | `test_uc1_e1_empty_title_is_rejected_and_nothing_is_stored` | "This field is required." next to the title, form shown again | event row count unchanged |
| UC1-E2 | `test_uc1_e2_meeting_after_start_is_rejected_with_an_error_naming_the_rule` | "Meeting time must not be after start time!" | shift row count unchanged |
| UC1-E3 | `test_uc1_e3_volunteer_cannot_open_the_create_event_page` | HTTP 403, "Permission denied" page | event row count unchanged |
| UC2-M | `test_uc2_main_volunteer_requests_a_place` | "successfully requested a participation" | REQUESTED, participation rows +1 |
| UC2-A1 | `test_uc2_a1_instant_confirmation_confirms_at_once` | "successfully signed up", counter 1/5 | CONFIRMED, confirmed count 1 |
| UC2-A2 | `test_uc2_a2_volunteer_declines_a_confirmed_place` | "successfully declined" | DECLINED, still one record, confirmed count 0 |
| UC2-E1 | `test_uc2_e1_shift_filled_meanwhile_is_rejected` | "This action is not allowed."; a fresh page says "The maximum number of participants is reached." | no participation for the volunteer, confirmed count stays 1 |
| UC2-E2 | `test_uc2_e2_signup_window_closed_meanwhile_is_rejected` | "This action is not allowed." | no participation |
| UC2-E3 | `test_uc2_e3_second_signup_from_a_stale_tab_creates_no_duplicate` | "This action is not allowed." | exactly one CONFIRMED participation |
The UC2 rejection flows use a **stale page** (the page was opened before something changed behind it) because a fresh page no longer offers the button: this is how a real user reaches the server-side rules. The empty-title flow (UC1-E1) switches off the browser's own `required` check (`novalidate`) to exercise the server rule; this is stated in the test.

## 2. Further tests of area 3
| Requirement of the brief | Test / document | Result |
|---|---|---|
| Two usability tests (one per workflow; one first submits a rejected value, checks the error, corrects, succeeds) | `test_usability_keyboard.py` | pass (details `ACCESSIBILITY.md` section 1) |
| Keyboard navigation test (focus order to the required fields and submit button, keyboard submit) | `test_keyboard_navigation_reaches_required_fields_and_submits` | pass |
| Lighthouse + axe-core, issues counted once, element/impact/fix, one screen fixed, before/after | `ACCESSIBILITY.md`, `reports/accessibility/comparison.md` | UC1 shift form accessibility 80 -> 89, 2 critical rules fixed |
| Access matrix (>= 4 decisions, allowed and denied) | `test_access_matrix.py`, `SECURITY.md` | 7 decisions pass |
| OWASP ZAP passive scan | `SECURITY.md` section 5 | **NOT RUN** (needs Docker, not available) |
| Dependency audit | `SECURITY.md` section 4, `reports/security/pip_audit.json` | 177 packages, 4 advisories in soupsieve, not reachable |
| Performance (k6) with limits set before testing, 1 and 5 users twice, >= 60 s | `PERFORMANCE.md`, `reports/performance/` | limits met; throughput flat at about 15 req/s |
| Failure and recovery | `test_failure_recovery.py`, `PERFORMANCE.md` section 5 | pass, no duplicate after retry |
| Management: issues, 5 Whys + fishbone, risk register, traceability, progress report, evidence checklist, AI-use record | issues #17-#23, `RCA.md`, `RISK_REGISTER.md`, `TRACEABILITY.md`, `PROGRESS_REPORT_4.md`, `EVIDENCE_CHECKLIST.md`, `AI_USE_RECORD.md` | done |

## 3. Defects found in area 3
#17 (fixed on branch), #18, #19, #20 (major, accessibility, open), #21 (minor), #22 (usability), #23 (dependency, minor). Analysis: `RCA.md`.

## 4. Limits and what was not done
* ZAP was not run. The use cases were written for the two workflows chosen in `REQUIREMENTS.md`; the brief asks for two use cases **per member**, so the other members' own use cases are outside this report.
* The browser tests run Chromium only, on the development server over HTTP.
* Automated accessibility tools find only a part of the problems; no manual screen-reader test was done.
