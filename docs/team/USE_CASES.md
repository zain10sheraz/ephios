# Use cases (area 3) - derived from `REQUIREMENTS.md`

Two use cases, one per workflow, each with the main flow, at least 2 alternative flows and at least 2 exception flows
(here 2 alternative + 3 exception). Every flow is automated in Playwright (`tests/team/e2e/`) through the real browser UI;
each automated test asserts the result **shown on the screen** and the **postconditions** (stored state read back after the browser step).
Test account names: see `SETUP.md` (synthetic, local only).

## UC1 - Planner creates an event with a shift (WF1; FR-01, FR-02, FR-03, FR-04, BR-W6, BR-W7)
| | |
|---|---|
| Goal | A planner publishes an event with one shift that volunteers can sign up for |
| Actor | Planner (permission `add_event`) |
| Preconditions | Application running; planner account exists and is logged in through the login form; at least one event type exists |
| Trigger | Planner opens "Create event" |

**Main flow (UC1-M)**
1. Planner opens the create-event page for an event type.
2. Planner enters title, location and description and submits.
3. System creates the event (not yet active) and shows the add-shift form.
4. Planner enters date, meeting time, start time, end time, flow "instant confirmation", maximum participants 5, and saves.
5. System creates the shift, activates the event and shows the event page with the shift.

*Postconditions:* event and shift persisted; event active; event page shows the title and the shift; `/api/events/<id>/` lists the shift with `max_count` 5; planner stays logged in.

**Alternative flows**
| ID | Branch at step | Flow | Expected result and postconditions |
|---|---|---|---|
| UC1-A1 | 4 | Planner chooses the flow "request and confirm" instead of instant confirmation | Shift saved with that flow; a later signup is REQUESTED, not CONFIRMED (checked through WF2 afterwards) |
| UC1-A2 | after 5 | Planner edits the shift and raises the maximum from 5 to 8 | Event page shows the new capacity; REST read-back shows `max_count` 8; no second shift is created |

**Exception flows**
| ID | Branch at step | Condition | Expected result and postconditions |
|---|---|---|---|
| UC1-E1 | 2 | Title is empty | Form shown again with a "required" error next to the field; no event stored |
| UC1-E2 | 4 | Meeting time is after the start time (rule BR-W1) | Form shown again with an error that names the field; no shift stored; event stays inactive |
| UC1-E3 | 1 | A volunteer without `add_event` opens the create-event page | "Permission denied" page (HTTP 403); nothing stored |

## UC2 - Volunteer signs up for a shift (WF2; FR-05, FR-06, FR-07, FR-08, FR-09, BR1-BR4)
| | |
|---|---|
| Goal | A volunteer takes a place on a shift |
| Actor | Volunteer |
| Preconditions | Volunteer logged in through the login form; event active; shift exists with free capacity and an open signup window |
| Trigger | Volunteer opens the event page |

**Main flow (UC2-M)**
1. Volunteer opens the event page and sees the shift with a sign-up button.
2. Volunteer chooses "sign up" and confirms.
3. System creates the participation and shows a confirmation message.

*Postconditions:* exactly one participation of the volunteer for the shift, state REQUESTED (request flow) or CONFIRMED (instant flow) as configured; the confirmation message names that outcome; `/api/users/me/participations/` lists it.

**Alternative flows**
| ID | Branch at step | Flow | Expected result and postconditions |
|---|---|---|---|
| UC2-A1 | 2 | Shift uses instant confirmation | Participation is CONFIRMED at once; the shift's confirmed count increases by 1 |
| UC2-A2 | after 3 | Volunteer declines a confirmed participation where the shift allows it (BR2) | State DECLINED by the user; still one record; the confirmed count decreases by 1 |

**Exception flows**
| ID | Branch at step | Condition | Expected result and postconditions |
|---|---|---|---|
| UC2-E1 | 2 | Shift is full (BR4) | Rejection message; no participation stored for this volunteer; confirmed count unchanged |
| UC2-E2 | 2 | Signup deadline has passed (BR1) | Rejection message; no participation stored |
| UC2-E3 | 2 | Volunteer signs up a second time (FR-08) | Message that the action is not allowed; still exactly one participation, state unchanged |

## Flow inventory (what the Playwright suite must cover)
12 flows: UC1-M, UC1-A1, UC1-A2, UC1-E1, UC1-E2, UC1-E3, UC2-M, UC2-A1, UC2-A2, UC2-E1, UC2-E2, UC2-E3 (>= 5 flows per use case as required).
Mapping of flows to tests and results: `E2E_AND_QUALITY_REPORT.md`.
