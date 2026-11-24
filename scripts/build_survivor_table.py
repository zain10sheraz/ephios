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
}

# (module, line) -> (killable rationale, equivalent rationale or None)
WHY = {
    ("participant_validation", 47): ("-", "Equivalent relative to DEFECT-001: checker returns instead of raising, so its outcome is discarded; killable once the defect is fixed"),
    ("participant_validation", 55): ("Missing test: only CONFIRMED was tested with decline forbidden -> test_only_confirmed_is_locked_when_decline_forbidden, test_declined_state_reports_its_own_message..., test_rejected_blocks_signup_even_when_decline_forbidden", None),
    ("participant_validation", 61): ("Weak assertion: GETTING_DISPATCHED only checked for sign-up, not decline -> test_getting_dispatched_may_still_decline", None),
    ("participant_validation", 85): ("Missing test: default total=False never used -> test_default_total_false_reports_partial_conflict", None),
    ("participant_validation", 101): ("Missing test: explicit start_time never passed -> test_explicit_start_time_is_used_not_shift_start", None),
    ("participant_validation", 102): ("Missing test: explicit end_time never passed -> test_explicit_end_time_is_used_not_shift_end", None),
    ("participant_validation", 119): ("Missing test: default of missing flag -> test_missing_customize_flag_defaults_to_strict_conflicts", None),
    ("structure_common", 14): ("-", "Equivalent: typing-only switch (TYPE_CHECKING); concrete classes inherit BaseShiftStructure anyway"),
    ("structure_common", 19): ("Missing test: minimum_age form limits and optionality -> test_minimum_age_form_boundaries, test_configuration_fields_are_optional", None),
    ("structure_common", 54): ("Missing test: capacity must count only CONFIRMED -> test_capacity_counts_only_confirmed", None),
    ("structure_common", 71): ("Missing test: minimum participants limits and optionality -> test_minimum_participants_form_boundary", None),
    ("structure_common", 74): ("Missing test: maximum participants limits and optionality -> test_maximum_participants_form_boundary", None),
    ("structure_common", 83): ("Weak assertion: empty_spots never asserted -> test_empty_spots", "Equivalent: -1 offset in max(0, x); range of a negative number is empty, same as 0"),
    ("structure_common", 84): ("Weak assertion: minimum None / set cases not asserted -> test_empty_spots", "Equivalent: -1 in `min or -1` gives a negative value that max(0, ...) clamps to 0"),
    ("structure_common", 85): ("Weak assertion: event-detail test only checked the title; XOR/arith coincidences -> test_empty_spots (min 5, 2 confirmed)", None),
    ("structure_common", 115): ("Missing test: qualification field is optional -> test_configuration_fields_are_optional", None),
    ("structure_common", 134): ("-", "Equivalent: @staticmethod removal; method is always called through the class, never bound"),
    ("structure_common", 176): ("Missing test: no placeholder rows when nothing configured -> test_export_rows", "Equivalent: -1 offset inside max(x or 0, y or 0); operands are >= 0 so result is unchanged"),
    ("structure_common", 177): ("-", "Equivalent: `list * n` with n <= 0 is an empty list, so <=, != and is-not give identical results"),
    ("structure_common", 184): ("Weak test data: 3-1 == 3^1 -> test_export_rows (4 rows, 1 confirmed)", None),
    ("stats", 6): ("Missing test: immutability -> test_signup_stats_is_frozen_and_hashable", None),
    ("stats", 67): ("Missing test: has_free boundary -> test_has_free_boundary", None),
    ("stats", 78): ("Weak test data: bitwise == add on tested numbers -> test_full_count_adds_confirmed_and_free", None),
    ("stats", 89): ("Missing decision table for free None/int -> test_unbounded_when_either_side_unbounded", None),
    ("stats", 90): ("Weak test data -> test_counts_are_added (3 + 5)", None),
    ("stats", 92): ("Missing asymmetric None cases -> test_min_count_treats_none_as_zero_unless_both_none", None),
    ("stats", 97): ("Weak test data -> test_unbounded_when_either_side_unbounded", None),
    ("stats", 98): ("Missing decision table for max_count -> test_unbounded_when_either_side_unbounded", None),
    ("stats", 102): ("Weak test data -> test_counts_are_added", None),
    ("stats", 103): ("Weak test data -> test_counts_are_added", None),
}


def load(name, rnd):
    out = {}
    with open(os.path.join(RAW, f"round{rnd}_{name}.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            work, result = json.loads(line)
            m = work["mutations"][0]
            out[(m["operator_name"], m["occurrence"])] = (m["start_pos"][0], result["test_outcome"] if result else None)
    return out


rows = []
for name, path in MODULES.items():
    src_lines = open(os.path.join(SRC, *path.split("/")), encoding="utf-8").read().splitlines()
    r1, r2 = load(name, 1), load(name, 2)
    for key, (line, outcome1) in r1.items():
        if outcome1 != "survived":
            continue
        outcome2 = r2[key][1]
        kill_why, equiv_why = WHY[(name, line)]
        if outcome2 == "killed":
            category, rationale = "killable (missing test / weak assertion)", kill_why
        else:
            category, rationale = "equivalent", equiv_why
            if rationale is None:
                sys.exit(f"UNEXPECTED survivor without equivalence justification: {name} {key} line {line}")
        rows.append([name, line, key[0].replace("core/", "").replace("team/", "team:"), key[1],
                     src_lines[line - 1].strip()[:80], "survived", outcome2, category, rationale])

rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
out_path = os.path.join(RAW, "survivor_analysis.csv")
with open(out_path, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["module", "line", "operator", "occurrence", "source", "round1", "round2", "category", "rationale"])
    w.writerows(rows)
cats = {}
for r in rows:
    cats[(r[0], r[7])] = cats.get((r[0], r[7]), 0) + 1
print("survivors analysed:", len(rows))
for k, v in sorted(cats.items()):
    print(" ", k, v)
