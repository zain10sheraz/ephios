"""Cross-workflow validation over HTTP: a change made in WF1 (planner) must show up consistently in WF2 (volunteer),
and a signup made in WF2 must be visible to WF1. The shared records are Shift and Participation; each test reads
them back through the REST API, not from the response of the write.
"""

from tests.team.api.support import VALID_SHIFT, unique_day

SIGN_UP = {"signup_choice": "sign_up"}


def signup(browser, shift_id):
    return browser.post(f"/shifts/{shift_id}/signup/", SIGN_UP)


def my_states(browser, shift_id):
    page = browser.rest("/api/users/me/participations/", shift=shift_id)
    return [p["state"]["value"] for p in page["results"]]


def edit(planner, shift_id, **changes):
    """Edit a shift but keep its own (unique) day, so the volunteers' signups do not overlap with other tests."""
    day = planner.rest(f"/api/shifts/{shift_id}/")["start_time"][:10]
    same_day = {
        "date": day,
        "signup_until_0": f"{int(day[:4])}-{day[5:7]}-{int(day[8:]) - 1:02d}"
        if int(day[8:]) > 1
        else day,
    }
    response = planner.post(f"/shifts/{shift_id}/edit/", {**VALID_SHIFT, **same_day, **changes})
    assert response.status_code == 302, response.text[:200]


def test_xwf_signup_is_visible_to_planner_in_participation_list(planner, volunteer):
    _, shift = planner.new_shift()
    signup(volunteer, shift)
    listed = planner.rest("/api/participations/", shift=shift)["results"]
    assert len(listed) == 1


def test_xwf_signup_updates_event_and_shift_counts(planner, volunteer):
    event, shift = planner.new_shift()
    signup(volunteer, shift)
    assert planner.rest(f"/api/shifts/{shift}/")["signup_stats"]["confirmed_count"] == 1
    assert planner.rest(f"/api/events/{event}/")["signup_stats"]["confirmed_count"] == 1


def test_xwf_lowering_capacity_below_confirmed_blocks_further_signups(
    planner, volunteer, volunteer2
):
    _, shift = planner.new_shift(maximum_number_of_participants="2")
    signup(volunteer, shift)
    edit(planner, shift, maximum_number_of_participants="1")
    signup(volunteer2, shift)
    assert my_states(volunteer2, shift) == []
    assert my_states(volunteer, shift) == [1]  # existing confirmation is kept


def test_xwf_raising_capacity_allows_signup_that_was_rejected(planner, volunteer, volunteer2):
    _, shift = planner.new_shift(maximum_number_of_participants="1")
    signup(volunteer, shift)
    signup(volunteer2, shift)
    assert my_states(volunteer2, shift) == []
    edit(planner, shift, maximum_number_of_participants="2")
    signup(volunteer2, shift)
    assert my_states(volunteer2, shift) == [1]


def test_xwf_moving_deadline_into_the_past_blocks_signup(planner, volunteer):
    _, shift = planner.new_shift()
    edit(planner, shift, signup_until_0="2000-01-01", signup_until_1="08:00")
    signup(volunteer, shift)
    assert my_states(volunteer, shift) == []


def test_xwf_changing_flow_to_request_changes_new_signup_state(planner, volunteer):
    _, shift = planner.new_shift(signup_flow_slug="instant_confirmation")
    edit(planner, shift, signup_flow_slug="request_confirm")
    signup(volunteer, shift)
    assert my_states(volunteer, shift) == [0]


def test_xwf_last_shift_of_an_event_cannot_be_deleted(planner):
    event, shift = planner.new_shift()
    assert (
        planner.post(f"/shifts/{shift}/delete/", {}).status_code == 302
    )  # refusal is a redirect plus a message
    assert planner.get(f"/api/shifts/{shift}/").status_code == 200
    assert len(planner.rest(f"/api/events/{event}/")["shifts"]) == 1


def test_xwf_deleting_shift_removes_its_participations_and_blocks_signup(
    planner, volunteer, volunteer2
):
    event, shift = planner.new_shift()
    planner.create_shift(event, **unique_day())  # a second shift, so the first one may be deleted
    signup(volunteer, shift)
    assert planner.post(f"/shifts/{shift}/delete/", {}).status_code == 302
    assert planner.get(f"/api/shifts/{shift}/").status_code == 404
    assert signup(volunteer2, shift).status_code == 404
    assert shift not in {
        p["shift"] for p in volunteer.rest("/api/users/me/participations/", limit=1000)["results"]
    }


def test_xwf_deleting_event_removes_its_shifts(planner):
    event, shift = planner.new_shift()
    assert planner.post(f"/events/{event}/delete/", {}).status_code == 302
    assert planner.get(f"/api/events/{event}/").status_code == 404
    assert planner.get(f"/api/shifts/{shift}/").status_code == 404


def test_xwf_volunteer_cannot_edit_or_delete_planner_shift(planner, volunteer):
    event, shift = planner.new_shift()
    assert volunteer.post(f"/shifts/{shift}/edit/", dict(VALID_SHIFT)).status_code == 403
    assert volunteer.post(f"/shifts/{shift}/delete/", {}).status_code == 403
    assert volunteer.post(f"/events/{event}/delete/", {}).status_code == 403
    assert planner.get(f"/api/shifts/{shift}/").status_code == 200


def test_xwf_unauthenticated_signup_is_refused_and_nothing_is_stored(planner, anonymous):
    _, shift = planner.new_shift()
    assert anonymous.post_without_csrf(f"/shifts/{shift}/signup/", SIGN_UP).status_code in (
        302,
        403,
    )
    assert planner.rest(f"/api/shifts/{shift}/")["signup_stats"]["confirmed_count"] == 0
