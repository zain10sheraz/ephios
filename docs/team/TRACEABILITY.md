# Requirements traceability matrix (RTM) - status 2026-11-26

Legend: **P** = executed and passing, **-** = no test yet (honest gap), **partial** = only part of the requirement is checked.
Levels: U = unit/white-box (Zain, `tests/team/unit`), I = integration (`tests/team/integration`), A = API black-box over HTTP (Manan, `tests/team/api`, 476 tests all passing), E = browser E2E (Sujawal, `tests/team/e2e`, 26 browser tests passing).
Requirement text and rule definitions: `REQUIREMENTS.md`. Test names are real pytest names in this repository.

## Functional requirements
| ID | Requirement (short) | U | I | A | E | Main tests (examples) | Status |
|---|---|---|---|---|---|---|---|
| FR-01 | Planner creates an event | P | P | P | P | `test_planner_creates_an_event_and_is_sent_on_to_add_a_shift`, `test_creating_events_needs_the_add_event_permission`, `test_new_event_form_assigns_permissions`; API: `test_generated_inputs[createEvent.*]` (29 cases) | covered (unit + HTTP) |
| FR-02 | Planner adds a shift with times | P | P | P | P | `test_saving_the_first_shift_activates_the_event`, `test_meeting_time_boundary`, `test_end_time_rolls_over_to_next_day`, DEFECT-002 tests; API: `test_generated_inputs[createShift.*]` | covered (unit + HTTP) |
| FR-03 | Configure flow/structure (max participants, min age, qualifications) | P | P | P | P | `test_shift_is_stored_with_the_posted_configuration`, `test_maximum_participants_form_boundary`, `test_minimum_age_form_boundaries`; API: `test_generated_inputs[editShift.maximum_number_of_participants.*]` | covered (unit + HTTP) |
| FR-04 | Events/shifts readable via REST API | - | - | P | - | API: `test_rest_api.py` (13), `test_generated_inputs[list*/get*]` | covered (API level) |
| FR-05 | Volunteer signs up (instant -> CONFIRMED, request -> REQUESTED) | P | P | P | P | `test_request_flow_signup_creates_requested_participation`, `test_instant_flow_signup_creates_confirmed_participation`; API: `test_instant_flow_confirms_participation`, `test_generated_inputs[signup.*]` | covered (unit + HTTP) |
| FR-06 | Volunteer declines where permitted | P | P | P | P | `test_decline_of_confirmed_participation_when_allowed`, `test_br2_confirmed_decline_decision_table`; API: `test_br2_decline_*` (3) | covered (unit + HTTP) |
| FR-07 | Rule violation rejected with message, nothing created | P | P | P | P | `test_signup_after_deadline_is_rejected_and_leaves_no_participation`, `test_signup_beyond_capacity_is_rejected_and_count_stays`, `test_failing_flow_action_rolls_back_and_reports_the_error`; API: `test_br4_above_limit_is_rejected_and_count_stays`, `test_br1_signup_after_deadline_is_rejected` | covered (unit + HTTP) |
| FR-08 | Repeated signup creates no duplicate | - | P | P | P | `test_repeated_signup_creates_no_duplicate_and_is_rejected`, `test_signup_after_decline_reuses_the_same_participation`, `test_retry_after_failure_succeeds_without_duplicates`; API: `test_repeated_signup_creates_no_duplicate` | covered (HTTP) |
| FR-09 | WF1 configuration changes affect WF2 | P | P | P | P | `tests/team/integration/test_cross_workflow.py` (capacity raise/lower, deadline set/clear, flow switch, min age, volunteer cannot edit); API: `test_cross_workflow_api.py` (11) | covered (HTTP, shared record read back) |

**Requirements coverage (unit + HTTP integration + API levels):** **9 of 9 requirements** have executed passing tests; FR-04 (REST read) is covered by the API tests (area 2, 2026-11-26).
Requirements coverage = **9 / 9 = 100 %** (strict, no half credit); before the API tests it was 8 / 9 = 89 %.
Earlier today it was 61 % (4 full + 3 partial of 9); the HTTP tests closed FR-01, 05, 08 and 09.
E2E tests (Sujawal, area 3) are listed in the E column: FR-01/02/03 by UC1 flows, FR-05..09 by UC2 flows (`docs/team/USE_CASES.md`, `E2E_AND_QUALITY_REPORT.md`); FR-04 (REST read) has no browser test by design.

## Business rules
| ID | Rule | Tests (all executed, all passing on `zain`) | Techniques |
|---|---|---|---|
| BR1 | Signup window boundary | `test_br1_signup_until_boundary[just_before/exactly_at/just_after]`, `test_br1_end_time_is_limit_without_signup_until`, `test_br1_signup_until_after_end_time_is_capped_by_end_time` | 3-point BVA |
| BR2 | Decline: flag AND window open | `test_br2_confirmed_decline_decision_table[R1..R4]` | decision table |
| BR3 | State transitions | `test_br3_*` (6 tests), `test_only_confirmed_is_locked_when_decline_forbidden` | state transition |
| BR4 | Capacity limit | `test_br4_maximum_participants_instant_flow[max_minus_1/at_max/max_plus_1]`, `test_capacity_counts_only_confirmed` | 3-point BVA |
| BR5 | Inactive event rejects signup (DEFECT-001) | `test_event_inactive_blocks_signup`, `test_signup_post_on_inactive_event_creates_no_participation` | decision, integration |
| BR6 | Overlap / min age / qualification | `test_conflict_*`, `test_partial_overlap_depends_on_customizable_times`, `test_minimum_age_boundary`, `test_required_qualification_*` | decision table, BVA |
| BR-W1 | Meeting time <= start time | `test_meeting_time_boundary` | 3-point BVA |
| BR-W2 | End <= start rolls to next day | `test_end_time_rolls_over_to_next_day` | 3-point BVA |
| BR-W3 | Multi-day at >= 23 h | `test_is_multi_day_boundary[just_below/exactly/just_above]` | 3-point BVA |
| BR-W4 | Event save assigns/removes permissions | `test_new_event_form_assigns_permissions`, `test_edit_keeps_locked_groups_and_participants_visible`, `test_edit_removes_access_of_users_no_longer_responsible` | decision |
| BR-W5 | Event type colour #RRGGBB | `test_event_type_colour_validation` | EP |
| BR-V | Who sees participant data | `test_*_setting_*` in `test_wf1_models_visibility.py` (decision table, 7 tests) | decision table |
| BR-W6 | Saving a shift activates its event | `test_saving_the_first_shift_activates_the_event`, `test_planner_can_activate_an_inactive_event` | state change |
| BR-W7 | Last shift cannot be deleted | `test_last_shift_cannot_be_deleted`, `test_a_shift_can_be_deleted_when_the_event_has_two` | 2-point BVA (1 vs 2 shifts) |
| BR-W8 | Inactive events visible only to users who may add events | `test_volunteer_sees_an_active_event_but_not_an_inactive_one`, `test_planner_sees_inactive_events` | role decision |
| BR-W9 | Event delete needs delete AND change; create needs add | `test_deleting_needs_both_delete_and_change_permission`, `test_creating_events_needs_the_add_event_permission` | decision table / role matrix |
| BR-F | Event list filters (search, type, date direction, participation state) | `test_search_matches_*`, `test_date_filter_boundaries`, `test_participation_state_filter` | EP + 3-point BVA |

## Risks -> evidence
PR-01 -> DEFECT-001 tests + fix; PR-02 -> BR1 tests; PR-03 -> BR4 tests (concurrency untested); PR-04 -> BR3; PR-05 -> BR6; PR-11 (shift time input validation) -> DEFECT-002 tests.

## Structural and mutation evidence per module
| Module | Statement / branch coverage | Mutation kill rate (final) |
|---|---|---|
| `core/signup/flow/participant_validation.py` | 100 % / 100 % | 98.3 % (100 % in CI after DEFECT-001 fix) |
| `plugins/baseshiftstructures/structure/common.py` | 100 % / 100 % | 94.5 % |
| `core/signup/stats.py` | 100 % / 100 % | 100 % |
| `core/forms/events.py` | 100 % / 100 % | 98.5 % |
| `core/models/events.py` | 100 % / 100 % | 98.0 % |
| `core/signup/views.py`, `participants.py`, `forms.py` | 100 % / 100 % | 92.1 % / 98.9 % / 98.0 % |
| 6 further signup-path modules | 100 % / 100 % (see `COVERAGE_SCOPE.md`) | not run |
