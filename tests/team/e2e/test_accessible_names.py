"""Regression test for DEFECT-008 (issue #17): the controls of the shift form must have accessible names.

axe-core reported `select-name` and `label` (both critical) for these four controls. The check here uses Playwright's own
accessible-name assertion, so the test fails on the unfixed code and passes after the fix.
"""

import importlib

import pytest

expect = importlib.import_module("playwright.sync_api").expect

CONTROLS = [
    ("#id_signup_flow_slug", "Signup mode"),
    ("#id_structure_slug", "Structure"),
    ("#id_signup_until_0", "Date"),
    ("#id_signup_until_1", "Time"),
]


@pytest.mark.parametrize(("selector", "name"), CONTROLS, ids=[selector for selector, _ in CONTROLS])
def test_shift_form_control_has_an_accessible_name(
    selector, name, planner_page, planner_api, server
):
    _, shift_id = planner_api.new_shift()
    planner_page.goto(f"{server.base}/shifts/{shift_id}/edit/")
    expect(planner_page.locator(selector)).to_have_accessible_name(name)
