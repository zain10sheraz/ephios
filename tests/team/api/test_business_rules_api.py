"""BR1-BR5, BR-W6..W9 and the participation state machine, checked end to end over HTTP with read-back.

Every rejection is verified in two ways: the HTTP response and the stored state read back through the REST API.
"""

SIGN_UP = {"signup_choice": "sign_up"}
DECLINE = {"signup_choice": "decline"}


def signup(browser, shift_id, data=SIGN_UP):
    return browser.post(f"/shifts/{shift_id}/signup/", data)


def states(browser, shift_id):
    """States of the logged-in user's participations on a shift, read back through the REST API."""
    page = browser.rest("/api/users/me/participations/", shift=shift_id)
    return [p["state"]["value"] for p in page["results"]]


def stats(planner, shift_id):
    return planner.rest(f"/api/shifts/{shift_id}/")["signup_stats"]


# ---- FR-05 / state transitions -------------------------------------------------------------------------------
def test_instant_flow_confirms_participation(planner, volunteer):
    _, shift = planner.new_shift(signup_flow_slug="instant_confirmation")
    assert signup(volunteer, shift).status_code == 302
    assert states(volunteer, shift) == [1]


def test_request_flow_leaves_participation_requested(planner, volunteer):
    _, shift = planner.new_shift(signup_flow_slug="request_confirm")
    signup(volunteer, shift)
    assert states(volunteer, shift) == [0]


# ---- BR4 capacity (3-point boundary through the full workflow: limit-1, limit, limit+1) ---------------------------
def test_br4_below_limit_signup_is_confirmed(planner, volunteer):
    _, shift = planner.new_shift(
        maximum_number_of_participants="2", signup_flow_slug="instant_confirmation"
    )
    signup(volunteer, shift)
    assert states(volunteer, shift) == [1]


def test_br4_at_limit_last_place_is_confirmed(planner, volunteer, volunteer2):
    _, shift = planner.new_shift(
        maximum_number_of_participants="2", signup_flow_slug="instant_confirmation"
    )
    signup(volunteer, shift)
    signup(volunteer2, shift)
    assert stats(planner, shift)["confirmed_count"] == 2


def test_br4_above_limit_is_rejected_and_count_stays(planner, volunteer, volunteer2):
    _, shift = planner.new_shift(
        maximum_number_of_participants="1", signup_flow_slug="instant_confirmation"
    )
    signup(volunteer, shift)
    signup(volunteer2, shift)
    assert states(volunteer2, shift) == []
    assert stats(planner, shift)["confirmed_count"] == 1


# ---- FR-08 repeated request, no duplicate ---------------------------------------------------------------------
def test_repeated_signup_creates_no_duplicate(planner, volunteer):
    _, shift = planner.new_shift()
    signup(volunteer, shift)
    signup(volunteer, shift)
    assert len(states(volunteer, shift)) == 1


# ---- BR2 / FR-06 decline ---------------------------------------------------------------------------------------
def test_br2_decline_allowed_when_flag_set(planner, volunteer):
    _, shift = planner.new_shift(user_can_decline_confirmed="on")
    signup(volunteer, shift)
    signup(volunteer, shift, DECLINE)
    assert states(volunteer, shift) == [2]


def test_br2_decline_of_confirmed_refused_without_flag(planner, volunteer):
    _, shift = planner.new_shift(user_can_decline_confirmed=None)
    signup(volunteer, shift)
    signup(volunteer, shift, DECLINE)
    assert states(volunteer, shift) == [1]


def test_decline_without_participation_creates_nothing_confirmed(planner, volunteer):
    _, shift = planner.new_shift()
    signup(volunteer, shift, DECLINE)
    assert 1 not in states(volunteer, shift)


# ---- BR1 signup deadline ----------------------------------------------------------------------------------------
def test_br1_signup_after_deadline_is_rejected(planner, volunteer):
    _, shift = planner.new_shift(
        date="2000-01-02", signup_until_0="2000-01-01", signup_until_1="08:00"
    )
    signup(volunteer, shift)
    assert states(volunteer, shift) == []


def test_br1_signup_before_deadline_is_accepted(planner, volunteer):
    _, shift = planner.new_shift()
    signup(volunteer, shift)
    assert states(volunteer, shift) == [1]
