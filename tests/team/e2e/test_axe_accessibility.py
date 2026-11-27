"""Full axe-core scan of the key screen of each use case, in the real browser, logged in.

The scan results are saved as JSON (evidence) in reports/accessibility/. The test passes when the scan completes
and the saved report is readable; it does NOT hide findings: they are analysed in docs/team/ACCESSIBILITY.md.
Set AXE_PHASE=after to write the post-fix reports next to the pre-fix ones.
"""

import importlib
import json
import os

import pytest

from tests.team.api.support import ROOT
from tests.team.e2e.pages import event_path

Axe = importlib.import_module("axe_playwright_python.sync_playwright").Axe
PHASE = os.environ.get("AXE_PHASE", "before")
OUT = ROOT / "reports" / "accessibility"


def scan(page, label):
    results = Axe().run(page)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"axe_{label}_{PHASE}.json"
    path.write_text(json.dumps(results.response, indent=1, ensure_ascii=False), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def violation_ids(report):
    return sorted(violation["id"] for violation in report["violations"])


@pytest.mark.parametrize("screen", ["uc1_shift_form", "uc2_event_page"])
def test_axe_scan_of_the_key_screen(screen, planner_page, volunteer_page, planner_api, server):
    event_id, shift_id = planner_api.new_shift()
    if screen == "uc1_shift_form":
        planner_page.goto(f"{server.base}/shifts/{shift_id}/edit/")
        planner_page.wait_for_load_state("networkidle")
        report = scan(planner_page, screen)
    else:
        volunteer_page.goto(server.base + event_path(planner_api, event_id))
        volunteer_page.wait_for_load_state("networkidle")
        report = scan(volunteer_page, screen)
    assert report["passes"], "axe did not evaluate any rule"
    print(
        f"{screen} ({PHASE}): {len(report['violations'])} violated rules: {violation_ids(report)}"
    )


def test_shift_form_controls_have_accessible_names(planner_page, planner_api, server):
    """Regression test for DEFECT-A11Y-1: the two selects and the signup-deadline inputs of the shift form had no
    accessible name (axe rules `select-name` and `label`, both 'critical')."""
    _, shift_id = planner_api.new_shift()
    planner_page.goto(f"{server.base}/shifts/{shift_id}/edit/")
    planner_page.wait_for_load_state("networkidle")
    options = {"runOnly": {"type": "rule", "values": ["label", "select-name"]}}
    violations = Axe().run(planner_page, options=options).response["violations"]
    unnamed = [node["target"] for violation in violations for node in violation["nodes"]]
    assert unnamed == []
