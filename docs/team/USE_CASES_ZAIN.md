# Use cases of Zain (browser end-to-end, area 1 member)

The brief asks for two use cases **per member**. Zain's two use cases extend the two workflows of `REQUIREMENTS.md` and are written from the requirements and from the behaviour of the running application. Each has a main flow, 2 alternative flows and 3 exception flows; every flow is a Playwright test (real Chromium, real login form) that asserts the **result shown on the screen** and the **post-conditions** read back from stored state (REST API and database row counts).
Tests: `tests/team/e2e/test_uc5_planner_deletes.py`, `tests/team/e2e/test_uc6_volunteer_customizes.py`. Other use cases: `USE_CASES.md` (Sajawal, UC1-UC2) and `USE_CASES_MANAN.md` (Manan, UC3-UC4).

## UC5 - Planner deletes a shift or an event (FR-02, BR-W7 last shift cannot be deleted, BR-W9 delete permission)

| | |
|---|---|
| Goal | the planner removes a shift or a whole event that is no longer needed |
| Actor | Planner (needs `change_event`; deleting an event also needs `delete_event`) |
| Preconditions | planner logged in through the login form; an event with two shifts |
| Trigger | planner opens the delete page of a shift |

**Main flow (UC5-M):** 1. Planner opens the delete page of the second shift ("Are you sure you want to delete the shift ...?", buttons Back / Delete). 2. Planner confirms. 3. System shows "The shift has been deleted." on the event page.
*Post-conditions:* the event has exactly one shift left; the deleted shift answers 404 on the REST API.

| ID | Flow | Expected result and post-conditions |
|---|---|---|
| UC5-A1 | planner deletes the whole event (confirmation page "Delete event") | redirected to the event list; event and shifts answer 404; two shift rows fewer |
| UC5-A2 | the shift has a volunteer's participation | "The shift has been deleted."; the participation row is gone too (one row fewer) |
| UC5-E1 | planner deletes the only shift of an event (BR-W7) | "You cannot delete the last shift!"; shift still readable |
| UC5-E2 | a volunteer opens the delete page | HTTP 403 "Permission denied"; no shift row removed |
| UC5-E3 | an anonymous user opens the delete page | redirected to `/accounts/login/?next=/shifts/<id>/delete/`; no shift row removed |

## UC6 - Volunteer signs up with her own times ("Customize") (FR-05, BR1, BR3)

| | |
|---|---|
| Goal | a volunteer takes part for only a part of the shift |
| Actor | Volunteer |
| Preconditions | volunteer logged in; shift (10:00-16:00) with an open signup window and free capacity |
| Trigger | volunteer follows the "Customize" link on the event page |

**Main flow (UC6-M):** 1. Volunteer opens the customize page, enters start 11:00 and end 15:00 and a comment, and presses "Sign up". 2. System shows "You have successfully signed up for ...".
*Post-conditions:* one participation, CONFIRMED, with start 11:00, end 15:00 and the comment.

| ID | Flow | Expected result and post-conditions |
|---|---|---|
| UC6-A1 | the shift uses "request and confirm" | "successfully requested a participation"; state REQUESTED with the chosen times |
| UC6-A2 | the volunteer opens the customize page again and changes the times to 12:00-14:00 ("customize" button) | "Your participation was saved."; the **same** participation (same id) now has 12:00-14:00 |
| UC6-E1 | end time before start time | "End time must not be before start time."; no participation |
| UC6-E2 | the planner closes the signup window while the customize page is open | "This action is not allowed."; no participation |
| UC6-E3 | the start time is empty | "Enter a valid time."; no participation |

UC6-E2 uses a stale page and UC6-E3 switches off the browser's own checks (`novalidate`) so that the server-side rule is exercised; the tests say so.

## Flow inventory
12 flows: UC5-M, A1, A2, E1, E2, E3 and UC6-M, A1, A2, E1, E2, E3. Results: `reports/e2e/`.
