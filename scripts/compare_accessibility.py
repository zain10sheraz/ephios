"""Merge the axe-core and Lighthouse reports (before/after) into reports/accessibility/comparison.md.

An issue found by both tools is counted once: Lighthouse's accessibility audits use axe-core rule ids, so issues are
merged by rule id. Reads reports/accessibility/{axe,lighthouse}_<screen>_<phase>.json written by the test suite and by
scripts/run_lighthouse.py.
"""

import json
import os

FOLDER = os.path.join(os.path.dirname(__file__), "..", "reports", "accessibility")
SCREENS = ["uc1_shift_form", "uc2_event_page", "uc5_shift_delete", "uc6_customize_page"]
FIXED_SCREENS = {
    "uc1_shift_form"
}  # the screens that were fixed have a before and an after run; the others one measurement


def load(name):
    with open(os.path.join(FOLDER, name), encoding="utf-8") as handle:
        return json.load(handle)


def axe_rules(screen, phase):
    report = load(f"axe_{screen}_{phase}.json")
    return {
        v["id"]: {
            "impact": v["impact"],
            "nodes": len(v["nodes"]),
            "help": v["help"],
            "first": v["nodes"][0]["target"],
        }
        for v in report["violations"]
    }


def lighthouse(screen, phase):
    report = load(f"lighthouse_{screen}_{phase}.json")
    scores = {key: round(value["score"] * 100) for key, value in report["categories"].items()}
    failing = {}
    for ref in report["categories"]["accessibility"]["auditRefs"]:
        audit = report["audits"][ref["id"]]
        if (
            audit["score"] is not None
            and audit["score"] < 1
            and audit["scoreDisplayMode"] != "notApplicable"
        ):
            failing[ref["id"]] = len(audit.get("details", {}).get("items", []))
    return scores, failing


def main():
    lines = [
        "# Accessibility: before and after (axe-core + Lighthouse, issues found by both counted once)",
        "",
    ]
    for screen in SCREENS:
        lines += [
            f"## {screen}",
            "",
            "| Tool | Phase | Accessibility | Best practices | SEO |",
            "|---|---|---|---|---|",
        ]
        merged = {}
        phases = ("before", "after") if screen in FIXED_SCREENS else ("after",)
        for phase in phases:
            scores, failing = lighthouse(screen, phase)
            lines.append(
                f"| Lighthouse | {phase} | {scores['accessibility']} | {scores['best-practices']} | {scores['seo']} |"
            )
            for rule, nodes in failing.items():
                merged.setdefault(rule, {})[f"lh_{phase}"] = nodes
            for rule, info in axe_rules(screen, phase).items():
                merged.setdefault(rule, {})[f"axe_{phase}"] = info["nodes"]
                merged[rule]["impact"] = info["impact"]
                merged[rule]["first"] = info["first"]
        lines += [
            "",
            "| Rule | Impact | Found by | Elements before | Elements after | Example element |",
            "|---|---|---|---|---|---|",
        ]
        for rule, info in sorted(merged.items()):
            tools = [
                name
                for key, name in ((f"axe_{phases[0]}", "axe"), (f"lh_{phases[0]}", "Lighthouse"))
                if key in info
            ]
            before = (
                max(info.get("axe_before", 0), info.get("lh_before", 0))
                if len(phases) == 2
                else "- (not fixed, single measurement)"
            )
            after = max(info.get("axe_after", 0), info.get("lh_after", 0))
            lines.append(
                f"| {rule} | {info.get('impact', '-')} | {' + '.join(tools) or 'after only'} | {before} | {after} | `{info.get('first', '-')}` |"
            )
        lines.append("")
    path = os.path.join(FOLDER, "comparison.md")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
