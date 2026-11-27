"""UC2 - volunteer signs up for a shift (docs/team/USE_CASES.md). One test per flow.

The rejection flows use a *stale page*: the volunteer opens the event page, something changes behind it (another
volunteer takes the last place, the planner closes the signup window, the volunteer signs up in a second tab) and then
the volunteer clicks. This is how a real user reaches the server-side rules, because a fresh page no longer offers the button.
"""

from tests.team.api.support import VALID_SHIFT
from tests.team.e2e.pages import (
    alerts,
    event_path,
    own_states,
    shift_box_text,
    sign_up_button,
)

NOT_ALLOWED = "This action is not allowed."


def open_event(page, server, api, event_id):
    page.goto(server.base + event_path(api, event_id))


def click_and_wait(page, button):
    button.click()
    page.wait_for_load_state()


def test_uc2_main_volunteer_requests_a_place(volunteer_page, planner_api, volunteer_api, server):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="request_confirm")
    before = server.db_count("abstractparticipation")
    open_event(volunteer_page, server, planner_api, event_id)
    click_and_wait(volunteer_page, sign_up_button(volunteer_page, shift_id))
    assert any("successfully requested a participation" in text for text in alerts(volunteer_page))
    assert own_states(volunteer_api, shift_id) == [0]
    assert server.db_count("abstractparticipation") == before + 1


def test_uc2_a1_instant_confirmation_confirms_at_once(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    open_event(volunteer_page, server, planner_api, event_id)
    click_and_wait(volunteer_page, sign_up_button(volunteer_page, shift_id))
    assert any("successfully signed up" in text for text in alerts(volunteer_page))
    assert "1/5" in shift_box_text(volunteer_page, shift_id)
    assert own_states(volunteer_api, shift_id) == [1]
    assert planner_api.rest(f"/api/shifts/{shift_id}/")["signup_stats"]["confirmed_count"] == 1


def test_uc2_a2_volunteer_declines_a_confirmed_place(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    open_event(volunteer_page, server, planner_api, event_id)
    click_and_wait(volunteer_page, sign_up_button(volunteer_page, shift_id))
    click_and_wait(volunteer_page, sign_up_button(volunteer_page, shift_id, "decline"))
    assert any("successfully declined" in text for text in alerts(volunteer_page))
    assert own_states(volunteer_api, shift_id) == [2]
    assert planner_api.rest(f"/api/shifts/{shift_id}/")["signup_stats"]["confirmed_count"] == 0


def test_uc2_e1_shift_filled_meanwhile_is_rejected(
    volunteer_page, planner_api, volunteer_api, volunteer2_api, server
):
    event_id, shift_id = planner_api.new_shift(maximum_number_of_participants="1")
    open_event(volunteer_page, server, planner_api, event_id)
    volunteer2_api.post(
        f"/shifts/{shift_id}/signup/", {"signup_choice": "sign_up"}
    )  # takes the only place
    click_and_wait(volunteer_page, sign_up_button(volunteer_page, shift_id))
    assert NOT_ALLOWED in alerts(volunteer_page)
    assert own_states(volunteer_api, shift_id) == []
    assert planner_api.rest(f"/api/shifts/{shift_id}/")["signup_stats"]["confirmed_count"] == 1
    open_event(volunteer_page, server, planner_api, event_id)  # a fresh page names the reason
    assert "The maximum number of participants is reached." in shift_box_text(
        volunteer_page, shift_id
    )


def test_uc2_e2_signup_window_closed_meanwhile_is_rejected(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift()
    open_event(volunteer_page, server, planner_api, event_id)
    day = planner_api.rest(f"/api/shifts/{shift_id}/")["start_time"][:10]
    closed = {**VALID_SHIFT, "date": day, "signup_until_0": "2000-01-01", "signup_until_1": "08:00"}
    assert planner_api.post(f"/shifts/{shift_id}/edit/", closed).status_code == 302
    click_and_wait(volunteer_page, sign_up_button(volunteer_page, shift_id))
    assert NOT_ALLOWED in alerts(volunteer_page)
    assert own_states(volunteer_api, shift_id) == []


def test_uc2_e3_second_signup_from_a_stale_tab_creates_no_duplicate(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    open_event(volunteer_page, server, planner_api, event_id)
    second_tab = volunteer_page.context.new_page()
    open_event(second_tab, server, planner_api, event_id)
    click_and_wait(volunteer_page, sign_up_button(volunteer_page, shift_id))
    click_and_wait(second_tab, sign_up_button(second_tab, shift_id))
    assert NOT_ALLOWED in alerts(second_tab)
    assert own_states(volunteer_api, shift_id) == [1]
