# Scope, requirements, business rules, roles (test basis)

Application: Ephios (upstream https://github.com/ephios-dev/ephios, MIT, baseline `d12e76cd`).
Test basis: source code (validators in `participant_validation.py`, views in `core/views/`), upstream docs,
and justified assumptions marked **[A]**. Status: DRAFT for team review.

## Workflows (module: events and signup)

| | WF1 Event and Shift Management | WF2 Participant Signup |
|---|---|---|
| Starting condition | Planner is logged in with `core.add_event` | Volunteer is logged in; event is active and visible; shift exists |
| User action | Create event (`/events/create/<type>/`), add/edit shift (`/events/<id>/createshift/`, `/shifts/<id>/edit/`), set times, flow, max participants | POST `/shifts/<id>/signup/` with `signup_choice` (sign_up / decline / customize) |
| Expected outcome | Event and shift persisted; shown in list and `/api/events/`, `/api/shifts/` | Participation created in REQUESTED or CONFIRMED (flow dependent), or rejection message with no record |

**Shared record:** `Shift` (times, `signup_flow_configuration.signup_until`, `maximum_number_of_participants`)
and `Event.active`. WF1 changes them; WF2 reads them in `participant_validation`.

## Functional requirements
| ID | Workflow | Requirement |
|---|---|---|
| FR-01 | WF1 | A Planner with `add_event` can create an event with title, type, location and active flag. |
| FR-02 | WF1 | A Planner can add a shift with meeting, start and end time to an event. |
| FR-03 | WF1 | A Planner can configure the signup flow and structure (incl. maximum participants, minimum age) of a shift. |
| FR-04 | WF1 | Created events/shifts are readable via the REST API (`/api/events/`, `/api/shifts/`) by permitted users. |
| FR-05 | WF2 | A Volunteer can sign up for a shift; with instant confirmation the participation is CONFIRMED, with request flow REQUESTED. |
| FR-06 | WF2 | A Volunteer can decline a shift where permitted. |
| FR-07 | WF2 | Signup is rejected with an explanatory message when a rule is violated, and no participation is created. |
| FR-08 | WF2 | Repeating a signup does not create a duplicate participation. |
| FR-09 | Both | Signup availability reflects WF1 configuration changes (capacity, deadline, active flag). |

## Business rules
| ID | Rule | Type |
|---|---|---|
| BR1 | Signup closes when `now > min(shift.end_time, signup_until)` (equal instant is still open). | boundary/limit |
| BR2 | A CONFIRMED volunteer may decline only if `user_can_decline_confirmed` AND the signup window is open. | Boolean decision (2 conditions) |
| BR3 | Participation state changes: REJECTED blocks all actions; DECLINED cannot decline again but may sign up; REQUESTED/CONFIRMED cannot sign up again. | state change |
| BR4 | With instant confirmation, signup is rejected once confirmed participants ≥ maximum_number_of_participants. | boundary/limit |
| BR5 (extra) | Signup is rejected for inactive events. **Known defect DEFECT-001 (Issue #1).** | decision |
| BR6 (extra) | Overlapping CONFIRMED participation blocks signup; minimum age and required qualifications block signup. | decision |

## Roles and permissions (access matrix, to be verified by Playwright)
| Action | Planner (`planner@sqe.test`) | Volunteer (`volunteer@sqe.test`) |
|---|---|---|
| View event list / detail | allowed | allowed (events visible to Volunteers group) |
| Create event | allowed (`core.add_event`) | denied |
| Edit event / shift | allowed on own events (`change_event` object permission) **[A: confirm]** | denied |
| Sign up for shift | allowed (also in Volunteers group) | allowed |
| Read `/api/events/` | allowed with auth | allowed with auth; unauthenticated 403 (observed) |

## Open assumptions to verify before testing
- **[A]** Planner receives `change_event` on events they create (guardian object permission on create).
- **[A]** Instant-confirmation flow ignores `signup_until` only when unset.
- The REST API is read-only (`ReadOnlyModelViewSet`); all writes are HTML form POSTs with CSRF.
