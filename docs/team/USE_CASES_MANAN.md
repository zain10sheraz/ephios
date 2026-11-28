# Use cases of Manan (browser end-to-end, area 2 member)

The brief asks for two use cases **per member**. Manan's two use cases extend the two workflows of `REQUIREMENTS.md` (WF1 event and shift management, WF2 signup) and are written from the requirements and from the behaviour of the running application. Each has a main flow, 2 alternative flows and 3 exception flows; every flow is a Playwright test (real Chromium, real login form) that asserts the **result shown on the screen** and the **post-conditions** read back from stored state (REST API).
Tests: `tests/team/e2e/test_uc3_planner_changes_shift.py`, `tests/team/e2e/test_uc4_volunteer_declines.py`. Sajawal's use cases UC1 and UC2: `USE_CASES.md`.

## UC3 - Planner changes the signup configuration of a shift and a volunteer sees the effect (FR-03, FR-09, BR4)

| | |
|---|---|
| Goal | the planner adapts capacity or signup flow after publishing; volunteers see the new rule at once |
| Actor | Planner (needs `change_event` on the event); Volunteer |
| Preconditions | planner and volunteers logged in through the login form; an active event with a shift that has a signup window open |
| Trigger | planner opens the edit-shift page |

**Main flow (UC3-M):** 1. one place of a 3-place shift is already confirmed (another volunteer). 2. Planner opens the shift edit page, sets the maximum participants to 1 and saves. 3. System shows "The shift ... has been saved". 4. A second volunteer opens the event page: the shift shows 1/1, the text "The maximum number of participants is reached." and **no sign-up button**.
*Post-conditions:* capacity 1, confirmed 1, the second volunteer has no participation.

| ID | Flow | Expected result and post-conditions |
|---|---|---|
| UC3-A1 | planner raises the capacity again (1 -> 3) | the volunteer's page offers the sign-up button again; signup succeeds, CONFIRMED; confirmed count 2 |
| UC3-A2 | planner changes the signup flow to "request and confirm" | the volunteer's button reads "Request"; the signup is REQUESTED ("successfully requested a participation") |
| UC3-E1 | planner enters capacity 0 | "Ensure this value is greater than or equal to 1."; shift unchanged (capacity still 5) |
| UC3-E2 | planner clears the date | "This field is required."; start time unchanged |
| UC3-E3 | a volunteer opens the edit page | HTTP 403 "Permission denied"; shift unchanged |

(UC3-E1 and UC3-E2 switch off the browser's own `required`/`min` checks to exercise the server-side rule; the tests say so.)

## UC4 - Volunteer declines a place (FR-06, BR2, BR3)

| | |
|---|---|
| Goal | a volunteer gives a place back |
| Actor | Volunteer |
| Preconditions | volunteer logged in; shift with an open signup window; the volunteer has a place (REQUESTED or CONFIRMED) |
| Trigger | volunteer clicks "Decline" on the event page |

**Main flow (UC4-M):** 1. Volunteer signs up (instant confirmation) and sees "successfully signed up". 2. Volunteer clicks Decline. 3. System shows "You have successfully declined ...".
*Post-conditions:* exactly one participation, state DECLINED (2); the shift's confirmed count is 0.

| ID | Flow | Expected result and post-conditions |
|---|---|---|
| UC4-A1 | after declining the volunteer signs up again | "successfully signed up"; the **same** participation record is reused (same id), state CONFIRMED |
| UC4-A2 | request-and-confirm shift: Request, then Decline | state REQUESTED, then DECLINED |
| UC4-E1 | the shift forbids declining (flag off) | after signing up the page says "You cannot decline by yourself." and offers no Decline button; state stays CONFIRMED |
| UC4-E2 | the page is open, the planner forbids declining meanwhile, the volunteer clicks Decline | "This action is not allowed."; state stays CONFIRMED |
| UC4-E3 | the signup window is closed meanwhile (BR2: the window must be open), the volunteer clicks Decline | "This action is not allowed."; state stays CONFIRMED |

UC4-E2 and UC4-E3 use a stale page (the button was visible when the page was loaded), the way a real user reaches the server-side rule.

## Flow inventory
12 flows: UC3-M, A1, A2, E1, E2, E3 and UC4-M, A1, A2, E1, E2, E3. Results: `reports/e2e/` (run of the whole browser suite).
