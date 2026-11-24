# Requirements traceability matrix (RTM) - status 2026-11-24

Legend: **P** = executed and passing, **-** = no test yet (honest gap), **partial** = only part of the requirement is checked.
Levels: U = unit/white-box (Zain, `tests/team/unit`), I = integration (`tests/team/integration`), A = API (Manan, not started), E = browser E2E (Sujawal, not started).
Requirement text and rule definitions: `REQUIREMENTS.md`. Test names are real pytest names in this repository.

## Functional requirements
| ID | Requirement (short) | U | I | A | E | Main tests (examples) | Status |
|---|---|---|---|---|---|---|---|
| FR-01 | Planner creates an event | P | - | - | - | `test_new_event_form_assigns_permissions`, `test_event_form_for_planner_without_publish_rights_disables_visibility` | partial (form level only) |
| FR-02 | Planner adds a shift with times | P | - | - | - | `test_meeting_time_boundary`, `test_end_time_rolls_over_to_next_day`, `test_missing_or_invalid_date_or_start_is_a_form_error_not_an_exception` (DEFECT-002) | covered at unit level |
| FR-03 | Configure flow/structure (max participants, min age, qualifications) | P | - | - | - | `test_maximum_participants_form_boundary`, `test_minimum_age_form_boundaries`, `test_configuration_fields_are_optional` | covered at unit level |
| FR-04 | Events/shifts readable via REST API | - | - | - | - | none yet (Manan) | **gap** |
| FR-05 | Volunteer signs up (instant -> CONFIRMED, request -> REQUESTED) | P | partial | - | - | `test_br4_*`, `test_br3_*`, `test_signup_post_on_inactive_event_creates_no_participation` | partial (validators; HTTP create path not asserted) |
| FR-06 | Volunteer declines where permitted | P | - | - | - | `test_br2_confirmed_decline_decision_table`, `test_getting_dispatched_may_still_decline` | covered at unit level |
| FR-07 | Rule violation rejected with message, nothing created | P | partial | - | - | `test_br1_signup_until_boundary`, `test_rejected_blocks_signup_even_when_decline_forbidden`, `test_conflict_with_confirmed_overlapping_shift_blocks` | covered at unit level |
| FR-08 | Repeated signup creates no duplicate | - | - | - | - | none yet | **gap** |
| FR-09 | WF1 configuration changes affect WF2 (capacity, deadline, active flag) | partial | partial | - | - | `test_br4_maximum_participants_instant_flow` (config -> validator), `test_event_inactive_blocks_signup` | partial |

**Requirements coverage (unit level only):** 4 requirements fully covered (FR-02, FR-03, FR-06, FR-07), 3 partially covered
(FR-01, FR-05, FR-09), 2 with no test (FR-04, FR-08). Counting a partial as half: (4 + 3 x 0.5) / 9 = 5.5 / 9 = **61 %**.
Strict count (only fully covered): 4 / 9 = 44 %. API and E2E tests by the other members are expected to close the gaps.

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

## Risks -> evidence
PR-01 -> DEFECT-001 tests + fix; PR-02 -> BR1 tests; PR-03 -> BR4 tests (concurrency untested); PR-04 -> BR3; PR-05 -> BR6; PR-11 (shift time input validation) -> DEFECT-002 tests.

## Structural and mutation evidence per module
| Module | Statement / branch coverage | Mutation kill rate (final) |
|---|---|---|
| `core/signup/flow/participant_validation.py` | 100 % / 100 % | 98.3 % (100 % in CI after DEFECT-001 fix) |
| `plugins/baseshiftstructures/structure/common.py` | 100 % / 100 % | 94.4 % |
| `core/signup/stats.py` | 100 % / 100 % | 100 % |
| `core/forms/events.py` | 100 % / 100 % | not run |
| `core/models/events.py` | 100 % / 100 % | not run |
