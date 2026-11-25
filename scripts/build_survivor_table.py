"""Build reports/mutation/survivor_analysis.csv from the raw Cosmic Ray dumps (round 1 and round 2).

Category rule (evidence based, not guessed):
  - survived in round 1 and KILLED in round 2   -> killable (missing test / weak assertion); the
    killing test is named in the rationale
  - survived in round 1 and STILL SURVIVING in round 2 -> equivalent mutant, with a justification
The rationale text per (module, line) was written by hand from reading the code.
"""

import csv
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "reports", "mutation")
SRC = os.environ.get("MUT_SRC", r"C:\mut_work\src\ephios")

MODULES = {
    "participant_validation": "core/signup/flow/participant_validation.py",
    "structure_common": "plugins/baseshiftstructures/structure/common.py",
    "stats": "core/signup/stats.py",
    "wf1_forms": "core/forms/events.py",
    "signup_views": "core/signup/views.py",
    "participants": "core/signup/participants.py",
    "signup_forms": "core/signup/forms.py",
    "models_events": "core/models/events.py",
}

# (module, line) -> (killable rationale, equivalent rationale or None)
WHY = {
    ("participant_validation", 47): (
        "-",
        "Equivalent relative to DEFECT-001: checker returns instead of raising, so its outcome is discarded; killable once the defect is fixed",
    ),
    ("participant_validation", 55): (
        "Missing test: only CONFIRMED was tested with decline forbidden -> test_only_confirmed_is_locked_when_decline_forbidden, test_declined_state_reports_its_own_message..., test_rejected_blocks_signup_even_when_decline_forbidden",
        None,
    ),
    ("participant_validation", 61): (
        "Weak assertion: GETTING_DISPATCHED only checked for sign-up, not decline -> test_getting_dispatched_may_still_decline",
        None,
    ),
    ("participant_validation", 85): (
        "Missing test: default total=False never used -> test_default_total_false_reports_partial_conflict",
        None,
    ),
    ("participant_validation", 101): (
        "Missing test: explicit start_time never passed -> test_explicit_start_time_is_used_not_shift_start",
        None,
    ),
    ("participant_validation", 102): (
        "Missing test: explicit end_time never passed -> test_explicit_end_time_is_used_not_shift_end",
        None,
    ),
    ("participant_validation", 119): (
        "Missing test: default of missing flag -> test_missing_customize_flag_defaults_to_strict_conflicts",
        None,
    ),
    ("structure_common", 14): (
        "-",
        "Equivalent: typing-only switch (TYPE_CHECKING); concrete classes inherit BaseShiftStructure anyway",
    ),
    ("structure_common", 19): (
        "Missing test: minimum_age form limits and optionality -> test_minimum_age_form_boundaries, test_configuration_fields_are_optional",
        None,
    ),
    ("structure_common", 54): (
        "Missing test: capacity must count only CONFIRMED -> test_capacity_counts_only_confirmed",
        None,
    ),
    ("structure_common", 71): (
        "Missing test: minimum participants limits and optionality -> test_minimum_participants_form_boundary",
        None,
    ),
    ("structure_common", 74): (
        "Missing test: maximum participants limits and optionality -> test_maximum_participants_form_boundary",
        None,
    ),
    ("structure_common", 83): (
        "Weak assertion: empty_spots never asserted -> test_empty_spots",
        "Equivalent: -1 offset in max(0, x); range of a negative number is empty, same as 0",
    ),
    ("structure_common", 84): (
        "Weak assertion: minimum None / set cases not asserted -> test_empty_spots",
        "Equivalent: -1 in `min or -1` gives a negative value that max(0, ...) clamps to 0",
    ),
    ("structure_common", 85): (
        "Weak assertion: event-detail test only checked the title; XOR/arith coincidences -> test_empty_spots (min 5, 2 confirmed)",
        None,
    ),
    ("structure_common", 115): (
        "Missing test: qualification field is optional -> test_configuration_fields_are_optional",
        None,
    ),
    ("structure_common", 134): (
        "-",
        "Equivalent: @staticmethod removal; method is always called through the class, never bound",
    ),
    ("structure_common", 176): (
        "Missing test: no placeholder rows when nothing configured -> test_export_rows",
        "Equivalent: -1 offset inside max(x or 0, y or 0); operands are >= 0 so result is unchanged",
    ),
    ("structure_common", 177): (
        "-",
        "Equivalent: `list * n` with n <= 0 is an empty list, so <=, != and is-not give identical results",
    ),
    ("structure_common", 184): (
        "Weak test data: 3-1 == 3^1 -> test_export_rows (4 rows, 1 confirmed)",
        None,
    ),
    ("stats", 6): ("Missing test: immutability -> test_signup_stats_is_frozen_and_hashable", None),
    ("stats", 67): ("Missing test: has_free boundary -> test_has_free_boundary", None),
    ("stats", 78): (
        "Weak test data: bitwise == add on tested numbers -> test_full_count_adds_confirmed_and_free",
        None,
    ),
    ("stats", 89): (
        "Missing decision table for free None/int -> test_unbounded_when_either_side_unbounded",
        None,
    ),
    ("stats", 90): ("Weak test data -> test_counts_are_added (3 + 5)", None),
    ("stats", 92): (
        "Missing asymmetric None cases -> test_min_count_treats_none_as_zero_unless_both_none",
        None,
    ),
    ("stats", 97): ("Weak test data -> test_unbounded_when_either_side_unbounded", None),
    ("stats", 98): (
        "Missing decision table for max_count -> test_unbounded_when_either_side_unbounded",
        None,
    ),
    ("stats", 102): ("Weak test data -> test_counts_are_added", None),
    ("stats", 103): ("Weak test data -> test_counts_are_added", None),
    ("wf1_forms", 48): (
        "Missing test: optional responsible users -> test_each_optional_selection_may_be_left_empty",
        None,
    ),
    ("wf1_forms", 55): (
        "Missing test: optional responsible groups -> test_each_optional_selection_may_be_left_empty",
        None,
    ),
    ("wf1_forms", 71): (
        "Missing test: initial responsible users are direct users only -> test_edit_form_initial_values_exclude_group_members_and_global_permissions",
        None,
    ),
    ("wf1_forms", 74): (
        "Missing test: initial responsible groups exclude global permissions -> same test",
        None,
    ),
    ("wf1_forms", 77): (
        "Missing test: initial visible groups exclude global permissions -> same test",
        None,
    ),
    ("wf1_forms", 92): (
        "Weak test data: preference and publishable group coincided -> test_new_event_initial_visible_for_uses_the_event_type_preference (two publishable groups)",
        None,
    ),
    ("wf1_forms", 96): (
        "Missing test: preference users united with the creator -> test_new_event_initial_responsible_users_combine_preference_and_creator, test_new_event_creator_stays_responsible_when_already_in_the_preference",
        None,
    ),
    ("wf1_forms", 123): (
        "Missing test: save is atomic -> test_failure_while_assigning_permissions_rolls_back_the_event",
        None,
    ),
    ("wf1_forms", 148): (
        "Missing test: union not symmetric difference -> test_group_that_is_visible_and_responsible_gets_both_permissions",
        None,
    ),
    ("wf1_forms", 149): (
        "Missing test -> test_locked_group_that_is_also_made_responsible_keeps_view_access",
        None,
    ),
    ("wf1_forms", 165): (
        "Missing test -> test_user_that_is_responsible_and_participating_gets_direct_view_access",
        None,
    ),
    ("wf1_forms", 168): (
        "-",
        "Equivalent: values_list(flat=...) inside a subquery; Django uses the single column either way",
    ),
    ("wf1_forms", 209): (
        "Weak assertion: normal flows offered once -> test_shift_form_offers_each_enabled_flow_and_structure_exactly_once",
        None,
    ),
    ("wf1_forms", 212): (
        "Weak assertion: same uniqueness test (predicted equivalent, was actually killable)",
        None,
    ),
    ("wf1_forms", 223): ("Weak assertion: structures offered once -> same test", None),
    ("wf1_forms", 226): (
        "Weak assertion: same uniqueness test (predicted equivalent, was actually killable)",
        None,
    ),
    ("wf1_forms", 267): (
        "-",
        "Equivalent: `<=` vs `<` on a field-name set; cleaned_data always has more keys than the two tested, so the sets are never equal",
    ),
    ("wf1_forms", 284): (
        "Missing test: shift copy picks the hour, event copy does not -> test_shift_copy_form_lets_the_user_pick_the_hour_but_event_copy_does_not",
        None,
    ),
    ("wf1_forms", 301): (
        "Weak assertion: only validity was asserted; the message differs -> test_invalid_colour_reports_the_specific_message (custom operator RaiseToReturn survivor)",
        None,
    ),
    ("wf1_forms", 304): (
        "Missing test: save() persists by default -> test_event_type_form_save_persists_by_default",
        None,
    ),
    # ---- signup/views.py
    ("signup_views", 81): (
        "Missing test of re-signup after customising -> test_quick_resignup_keeps_the_previously_customized_times",
        "Equivalent: the quick-action data is only passed to plugin signal receivers; the core flows ignore the individual times in it",
    ),
    ("signup_views", 82): ("Same as line 81 (end time)", "Equivalent: same reason as line 81"),
    ("signup_views", 84): (
        "Missing tests: quick decline/customize with an overlap -> test_quick_decline_is_allowed_even_when_shifts_overlap, test_quick_customize_with_an_overlapping_shift_redirects_to_the_form",
        None,
    ),
    ("signup_views", 92): (
        "Missing test: partial overlap in the quick action -> test_quick_signup_with_a_partial_overlap_is_not_done_silently",
        None,
    ),
    ("signup_views", 142): (
        "Missing tests: customise notification sent/not sent -> test_customizing_times_notifies_the_responsibles_with_the_changes and two siblings",
        "Equivalent (<= only): 'customize' is the alphabetically smallest valid choice, so <= behaves like ==",
    ),
    # ---- participants.py
    ("participants", 42): (
        "Weak test data: year - year equals year % year for realistic dates -> test_age_arithmetic_is_correct_for_very_old_birth_dates",
        None,
    ),
    ("participants", 47): (
        "Missing test: adults over 18 -> test_adults_over_18_are_not_minors",
        None,
    ),
    ("participants", 75): (
        "Missing test: exact qualification set -> test_exact_qualification_set_satisfies_the_requirement, test_no_requirement_is_satisfied_by_a_participant_without_qualifications",
        None,
    ),
    ("participants", 115): (
        "-",
        "Equivalent: PlaceholderParticipant adds no fields, so the dataclass decorator is redundant (inherits the parent's)",
    ),
    # ---- signup/forms.py
    ("signup_forms", 28): (
        "Missing test: comment length BVA -> test_comment_length_boundary",
        None,
    ),
    ("signup_forms", 46): (
        "Missing test: comment visibility -> test_comment_visibility_follows_the_checkbox",
        None,
    ),
    ("signup_forms", 60): (
        "Missing test: direct save is atomic -> test_form_save_rolls_back_the_participation_when_the_comment_cannot_be_stored",
        None,
    ),
    ("signup_forms", 61): (
        "-",
        "Equivalent: the commit parameter of save() is never used (super().save() is called without it)",
    ),
    ("signup_forms", 102): (
        "Missing test: previous comments are not required -> test_a_participant_with_earlier_comments_can_submit_again",
        None,
    ),
    ("signup_forms", 112): (
        "Weak coverage of the notification text (test command lacked the view tests) -> test_customizing_times_notifies_the_responsibles_with_the_changes",
        None,
    ),
    ("signup_forms", 113): ("Same as line 112", None),
    ("signup_forms", 121): (
        "Missing test: customising back to the default end time -> test_customising_back_to_the_default_end_time_reports_the_end_time_change",
        None,
    ),
    ("signup_forms", 140): (
        "Missing test: signup_choice is required -> test_posting_without_a_signup_choice_is_invalid",
        None,
    ),
    ("signup_forms", 144): (
        "Missing test: layout excludes only signup_choice -> test_field_layout_renders_every_field_except_signup_choice",
        "Equivalent (is not): CPython interns both strings, so `is not` behaves like `!=`",
    ),
    ("signup_forms", 166): (
        "Missing test: decline button only when possible -> test_decline_button_is_shown_only_when_declining_is_possible",
        None,
    ),
    ("signup_forms", 186): (
        "Missing test: flow without the setting -> test_times_are_locked_when_the_flow_does_not_define_the_setting",
        None,
    ),
    ("signup_forms", 189): (
        "Missing test: end time locked too -> test_both_time_fields_are_disabled_when_customising_is_not_allowed, test_a_forged_end_time_is_ignored_when_times_are_locked",
        None,
    ),
    ("signup_forms", 203): (
        "Missing test: customise into an overlap -> test_customising_into_an_overlap_with_another_confirmed_shift_is_rejected",
        "Equivalent (<= only): 'decline' compared with itself; other choices are rejected earlier",
    ),
    ("signup_forms", 207): (
        "Missing test: chosen start avoids the overlap -> test_chosen_start_after_the_conflict_avoids_the_overlap",
        None,
    ),
    ("signup_forms", 208): (
        "Missing test: chosen end avoids the overlap -> test_chosen_end_before_the_conflict_avoids_the_overlap",
        None,
    ),
    ("signup_forms", 210): (
        "Missing test: partial overlap via the form -> test_partial_overlap_is_rejected_by_the_form",
        None,
    ),
    ("signup_forms", 236): (
        "Test command lacked the unit test of the form context -> test_configuration_form_context_exposes_request_event_and_shift",
        None,
    ),
    # ---- models/events.py
    ("models_events", 55): (
        "Missing test: EventType registered for logging -> tests/team/unit/test_models_events_mutation_killers.py::test_models_are_registered_for_logging_or_explicitly_excluded",
        None,
    ),
    ("models_events", 61): (
        "Missing test: persisted enum values -> test_stored_enum_values_never_change",
        None,
    ),
    ("models_events", 63): (
        "Missing test: title length BVA -> test_event_type_title_length_limit, test_event_title_and_location_length_limits",
        None,
    ),
    ("models_events", 64): (
        "Missing test: colour length BVA -> test_event_type_color_length_limit",
        None,
    ),
    ("models_events", 76): (
        "Missing test: default description optional -> test_event_type_default_description_may_be_empty_or_missing",
        None,
    ),
    ("models_events", 90): (
        "Missing test: event title length BVA -> test_event_title_and_location_length_limits",
        None,
    ),
    ("models_events", 91): (
        "Missing test: event description optional -> test_event_description_may_be_empty_or_missing",
        None,
    ),
    ("models_events", 92): (
        "Missing test: location length BVA -> test_event_title_and_location_length_limits",
        None,
    ),
    ("models_events", 94): (
        "Missing test: new events are inactive -> test_new_objects_start_with_safe_defaults",
        None,
    ),
    ("models_events", 184): (
        "Missing test: PUBLIC and own participation both apply -> test_public_event_shows_a_guests_own_participation_exactly_once",
        None,
    ),
    ("models_events", 200): (
        "Missing test only if two terms can both be true",
        "Equivalent: `|` -> `^` between INSTANCE_USERS and PUBLIC; one event type cannot have both values",
    ),
    ("models_events", 203): (
        "Missing test only if two terms can both be true",
        "Equivalent: `|` -> `^` between PUBLIC and CONFIRMED-with-participation; one event type cannot have both values",
    ),
    ("models_events", 207): (
        "Missing test: responsible and setting both apply -> test_responsible_planner_sees_all_even_when_the_setting_already_shows_everything",
        None,
    ),
    ("models_events", 208): (
        "Missing test: own participation and another condition apply -> test_responsible_planner_sees_own_participation_when_only_responsibles_may_see, test_volunteer_sees_own_participation_when_the_setting_shows_everything",
        None,
    ),
    ("models_events", 209): (
        "Missing test: user-profile permission and setting both apply -> test_user_managers_see_participants_even_when_the_setting_already_shows_everything",
        None,
    ),
    ("models_events", 250): (
        "Missing test: AbstractParticipation explicitly excluded from logging -> test_models_are_registered_for_logging_or_explicitly_excluded",
        None,
    ),
    ("models_events", 253): (
        "Missing test: persisted enum values -> test_stored_enum_values_never_change",
        None,
    ),
    ("models_events", 257): (
        "Missing test: persisted enum values -> test_stored_enum_values_never_change",
        None,
    ),
    ("models_events", 273): (
        "Missing test: default state of a new participation -> test_new_objects_start_with_safe_defaults",
        None,
    ),
    ("models_events", 282): (
        "Missing test: individual start may be NULL -> test_individual_times_may_be_stored_as_null",
        None,
    ),
    ("models_events", 283): (
        "Missing test: individual end may be NULL -> test_individual_times_may_be_stored_as_null",
        None,
    ),
    ("models_events", 289): (
        "Missing test: finished defaults to False -> test_new_objects_start_with_safe_defaults",
        None,
    ),
    ("models_events", 297): (
        "Missing test: decision table of has_customized_signup -> test_has_customized_signup_decision_table",
        None,
    ),
    ("models_events", 307): (
        "Weak assertion (custom operator RaiseToReturn survivor): str() only asserted truthy -> test_abstract_participation_falls_back_to_django_default_string",
        None,
    ),
    ("models_events", 328): (
        "Missing test: ParticipationComment registered for logging -> test_models_are_registered_for_logging_or_explicitly_excluded",
        None,
    ),
    ("models_events", 338): (
        "Missing test: persisted enum values -> test_stored_enum_values_never_change",
        None,
    ),
    ("models_events", 340): (
        "Missing test: persisted enum values -> test_stored_enum_values_never_change",
        None,
    ),
    ("models_events", 351): (
        "Missing test: comment author optional -> test_comment_author_is_optional",
        None,
    ),
    ("models_events", 359): (
        "Missing test: comment length BVA -> test_comment_text_and_shift_label_length_limits",
        None,
    ),
    ("models_events", 385): (
        "Missing test: shift label length BVA -> test_comment_text_and_shift_label_length_limits",
        None,
    ),
    ("models_events", 513): (
        "Missing test: readable flow name in the shift log -> test_shift_log_records_readable_flow_and_structure_names",
        None,
    ),
    ("models_events", 514): (
        "Missing test: flow name lookup incl. unknown slug -> test_shift_log_records_readable_flow_and_structure_names, test_shift_log_names_are_none_for_unknown_slugs",
        None,
    ),
    ("models_events", 516): (
        "Missing test: readable structure name in the shift log -> test_shift_log_records_readable_flow_and_structure_names",
        None,
    ),
    ("models_events", 517): (
        "Missing test: structure name lookup incl. unknown slug -> same tests",
        None,
    ),
    ("models_events", 540): (
        "Missing test: view permission granted by a participation -> test_saving_a_participation_grants_event_view_access_except_when_dispatched",
        None,
    ),
    ("models_events", 541): (
        "Missing test: users who already may view get no extra permission -> test_no_extra_object_permission_when_the_user_may_already_view_the_event",
        None,
    ),
    ("models_events", 542): (
        "Missing test: no grant for GETTING_DISPATCHED, grant for the other four states -> test_saving_a_participation_grants_event_view_access_except_when_dispatched",
        None,
    ),
    ("models_events", 564): (
        "Missing test: display name length BVA -> test_placeholder_display_name_length_limit",
        None,
    ),
    ("models_events", 589): (
        "Missing test: EventTypePreference explicitly excluded from logging -> test_models_are_registered_for_logging_or_explicitly_excluded",
        None,
    ),
}

WHY[("models_events", 207)] = (
    WHY[("models_events", 207)][0],
    "UNRESOLVED (not proven equivalent): the targeted test passes even with the XOR mutant; Django's XOR over these joined Q terms returned the same rows in our scenario, for a reason that was not established",
)
WHY[("models_events", 209)] = (
    WHY[("models_events", 209)][0],
    "UNRESOLVED (not proven equivalent): same as line 207",
)
WHY[("models_events", 542)] = (
    WHY[("models_events", 542)][0],
    "Equivalent (is not / <): small ints are interned and GETTING_DISPATCHED (4) is the largest state value, so both behave like !=",
)


def load(name, rnd):
    out = {}
    with open(os.path.join(RAW, f"round{rnd}_{name}.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            work, result = json.loads(line)
            m = work["mutations"][0]
            kind = result["test_outcome"] if result else None
            output = (result.get("output") or "") if result else ""
            if (
                kind == "incompetent"
                and "UnicodeDecodeError" in output
                and "TestOutcome.KILLED" in output
            ):
                kind = "killed"  # tool artefact: decoding crashed on the output of a run that had failed
            out[(m["operator_name"], m["occurrence"])] = (m["start_pos"][0], kind)
    return out


rows = []
for name, path in MODULES.items():
    with open(os.path.join(SRC, *path.split("/")), encoding="utf-8") as source_file:
        src_lines = source_file.read().splitlines()
    r1, r2 = load(name, 1), load(name, 2)
    for key, (line, outcome1) in r1.items():
        if outcome1 != "survived":
            continue
        outcome2 = r2[key][1]
        kill_why, equiv_why = WHY[(name, line)]
        if outcome2 == "killed":
            category, rationale = "killable (missing test / weak assertion)", kill_why
        else:
            category = (
                "unresolved (not killed, not proven equivalent)"
                if str(equiv_why).startswith("UNRESOLVED")
                else "equivalent"
            )
            rationale = equiv_why
            if rationale is None:
                sys.exit(
                    f"UNEXPECTED survivor without equivalence justification: {name} {key} line {line}"
                )
        rows.append([
            name,
            line,
            key[0].replace("core/", "").replace("team/", "team:"),
            key[1],
            src_lines[line - 1].strip()[:80],
            "survived",
            outcome2,
            category,
            rationale,
        ])

rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
out_path = os.path.join(RAW, "survivor_analysis.csv")
with open(out_path, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow([
        "module",
        "line",
        "operator",
        "occurrence",
        "source",
        "round1",
        "round2",
        "category",
        "rationale",
    ])
    w.writerows(rows)
cats = {}
for r in rows:
    cats[(r[0], r[7])] = cats.get((r[0], r[7]), 0) + 1
print("survivors analysed:", len(rows))
for k, v in sorted(cats.items()):
    print(" ", k, v)
