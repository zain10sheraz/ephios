"""Participation state changes over HTTP (BR3 / BR2): allowed changes work, a disallowed change leaves the state alone."""

from tests.team.api.support import VALID_SHIFT

SIGN_UP = {"signup_choice": "sign_up"}
DECLINE = {"signup_choice": "decline"}


def mine(browser, shift):
    page = browser.rest("/api/users/me/participations/", shift=shift)
    return [(p["id"], p["state"]["value"]) for p in page["results"]]


def test_decline_then_sign_up_again_reuses_the_same_participation(planner, volunteer):
    _, shift = planner.new_shift()
    volunteer.post(f"/shifts/{shift}/signup/", SIGN_UP)
    [(participation, _)] = mine(volunteer, shift)
    volunteer.post(f"/shifts/{shift}/signup/", DECLINE)
    assert mine(volunteer, shift) == [(participation, 2)]
    volunteer.post(f"/shifts/{shift}/signup/", SIGN_UP)
    assert mine(volunteer, shift) == [(participation, 1)]
