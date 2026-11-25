"""Summarise the Cosmic Ray rounds stored in reports/mutation/ (round1_*.jsonl and round2_*.jsonl).

Normalisation: Cosmic Ray 8.9.0 records a mutant as INCOMPETENT when decoding the pytest output raises
UnicodeDecodeError, even if the traceback shows the mutant was in the KILLED branch (the output contains a
non-UTF-8 byte from a Windows console, e.g. the 'a' umlaut in "Rettungssanitaeter"). We counted all 35 such
cases across every session: none was in the SURVIVED branch. They are therefore counted as killed here.
Kill rate = killed / (killed + survived + timeout).
"""

import collections
import json
import os
import sys

RAW = os.path.join(os.path.dirname(__file__), "..", "reports", "mutation")
MODULES = [
    ("core/signup/flow/participant_validation.py", "participant_validation"),
    ("plugins/baseshiftstructures/structure/common.py", "structure_common"),
    ("core/signup/stats.py", "stats"),
    ("core/forms/events.py", "wf1_forms"),
    ("core/signup/views.py", "signup_views"),
    ("core/signup/participants.py", "participants"),
    ("core/signup/forms.py", "signup_forms"),
    ("core/models/events.py", "models_events"),
]


def outcome(result):
    if not result:
        return None
    kind = result["test_outcome"]
    output = result.get("output") or ""
    if kind == "incompetent" and "UnicodeDecodeError" in output and "TestOutcome.KILLED" in output:
        return "killed"  # artefact of the tool, see module docstring
    return kind


def load(name, rnd):
    path = os.path.join(RAW, f"round{rnd}_{name}.jsonl")
    counts = collections.Counter()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            _work, result = json.loads(line)
            kind = outcome(result)
            if kind:
                counts[kind] += 1
    return counts


def rate(counts):
    valid = counts["killed"] + counts["survived"] + counts["timeout"]
    return 100.0 * counts["killed"] / valid if valid else float("nan")


if __name__ == "__main__":
    total1, total2 = collections.Counter(), collections.Counter()
    print("| Module | Mutants | Round 1 | Final |\n|---|---|---|---|")
    for label, name in MODULES:
        c1, c2 = load(name, 1), load(name, 2)
        total1.update(c1)
        total2.update(c2)
        print(
            f"| `{label}` | {sum(c1.values())} | {c1['killed']} killed, {c1['survived']} survived -> {rate(c1):.1f} % "
            f"| {c2['killed']} killed, {c2['survived']} survived -> **{rate(c2):.1f} %** |"
        )
    print(
        f"| **Total** | {sum(total1.values())} | {total1['killed']} killed, {total1['survived']} survived -> {rate(total1):.1f} % "
        f"| {total2['killed']} killed, {total2['survived']} survived -> **{rate(total2):.1f} %** |"
    )
    sys.exit(0)
