"""UC4 - volunteer declines a place (docs/team/USE_CASES_MANAN.md; BR2: decline needs the flag AND an open signup window).

One test per flow. The rejection flows use a stale page: the Decline button is visible, then the planner changes the rule
behind it, then the volunteer clicks.
"""

from datetime import date, timedelta

from tests.team.api.support import VALID_SHIFT
from tests.team.e2e.pages import alerts, event_path, own_states, shift_box_text, sign_up_button

NOT_ALLOWED = "This action is not allowed."


def open_event(page, server, api, event_id):
    page.goto(server.base + event_path(api, event_id))


def click(page, shift_id, choice):
    sign_up_button(page, shift_id, choice).click()
    page.wait_for_load_state()


def change_shift(planner_api, shift_id, **changes):
    """Edit a shift over HTTP but keep its own day (the volunteers' signups must not overlap other tests)."""
    day = planner_api.rest(f"/api/shifts/{shift_id}/")["start_time"][:10]
    day_before = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
    data = {**VALID_SHIFT, "date": day, "signup_until_0": day_before, **changes}
    assert planner_api.post(f"/shifts/{shift_id}/edit/", data).status_code == 302


def participation_ids(api, shift_id):
    return [p["id"] for p in api.rest("/api/users/me/participations/", shift=shift_id)["results"]]


def test_uc4_main_volunteer_declines_a_confirmed_place(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    open_event(volunteer_page, server, planner_api, event_id)
    click(volunteer_page, shift_id, "sign_up")
    click(volunteer_page, shift_id, "decline")
    assert any("successfully declined" in text for text in alerts(volunteer_page))
    assert own_states(volunteer_api, shift_id) == [2]
    assert planner_api.rest(f"/api/shifts/{shift_id}/")["signup_stats"]["confirmed_count"] == 0


def test_uc4_a1_signing_up_again_after_declining_reuses_the_same_record(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    open_event(volunteer_page, server, planner_api, event_id)
    click(volunteer_page, shift_id, "sign_up")
    [first] = participation_ids(volunteer_api, shift_id)
    click(volunteer_page, shift_id, "decline")
    click(volunteer_page, shift_id, "sign_up")
    assert any("successfully signed up" in text for text in alerts(volunteer_page))
    assert participation_ids(volunteer_api, shift_id) == [first]
    assert own_states(volunteer_api, shift_id) == [1]


def test_uc4_a2_volunteer_declines_a_requested_place(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="request_confirm")
    open_event(volunteer_page, server, planner_api, event_id)
    click(volunteer_page, shift_id, "sign_up")
    assert own_states(volunteer_api, shift_id) == [0]
    click(volunteer_page, shift_id, "decline")
    assert any("successfully declined" in text for text in alerts(volunteer_page))
    assert own_states(volunteer_api, shift_id) == [2]


def test_uc4_e1_shift_that_forbids_declining_offers_no_decline_button(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(
        signup_flow_slug="instant_confirmation", user_can_decline_confirmed=None
    )
    open_event(volunteer_page, server, planner_api, event_id)
    click(volunteer_page, shift_id, "sign_up")
    assert "You cannot decline by yourself." in shift_box_text(volunteer_page, shift_id)
    assert sign_up_button(volunteer_page, shift_id, "decline").count() == 0
    assert own_states(volunteer_api, shift_id) == [1]


def test_uc4_e2_decline_forbidden_meanwhile_is_rejected_and_the_place_is_kept(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    open_event(volunteer_page, server, planner_api, event_id)
    click(volunteer_page, shift_id, "sign_up")  # the page now offers Decline
    change_shift(planner_api, shift_id, user_can_decline_confirmed=None)  # the planner forbids it
    click(volunteer_page, shift_id, "decline")
    assert NOT_ALLOWED in alerts(volunteer_page)
    assert own_states(volunteer_api, shift_id) == [1]


def test_uc4_e3_decline_after_the_signup_window_closed_is_rejected_and_the_place_is_kept(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    open_event(volunteer_page, server, planner_api, event_id)
    click(volunteer_page, shift_id, "sign_up")
    change_shift(planner_api, shift_id, signup_until_0="2000-01-01", signup_until_1="08:00")
    click(volunteer_page, shift_id, "decline")
    assert NOT_ALLOWED in alerts(volunteer_page)
    assert own_states(volunteer_api, shift_id) == [1]
