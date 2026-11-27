"""UC3 - planner changes the signup configuration of a shift and a volunteer sees the effect (docs/team/USE_CASES_MANAN.md).

One test per flow. Each asserts the result shown on the screen and the post-conditions read back from the stored state.
"""

from tests.team.e2e.pages import (
    alerts,
    event_path,
    field_errors,
    own_states,
    save_shift,
    shift_box_text,
    sign_up_button,
)

SIGN_UP = {"signup_choice": "sign_up"}


def shift_stats(api, shift_id):
    return api.rest(f"/api/shifts/{shift_id}/")["signup_stats"]


def edit_page(page, server, shift_id):
    page.goto(f"{server.base}/shifts/{shift_id}/edit/")


def submit_to_the_server(page):
    """Switch off the browser's own checks (required, min) so that the server-side rule is exercised, then save."""
    page.evaluate("document.getElementById('id_date').form.setAttribute('novalidate', '')")
    save_shift(page)


def open_event(page, server, api, event_id):
    page.goto(server.base + event_path(api, event_id))


def test_uc3_main_lowering_the_capacity_to_the_confirmed_count_closes_the_shift(
    planner_page, volunteer_page, planner_api, volunteer_api, volunteer2_api, server
):
    event_id, shift_id = planner_api.new_shift(maximum_number_of_participants="3")
    volunteer2_api.post(f"/shifts/{shift_id}/signup/", SIGN_UP)  # one place is taken
    edit_page(planner_page, server, shift_id)
    planner_page.fill("#id_maximum_number_of_participants", "1")
    save_shift(planner_page)
    assert any("has been saved" in text for text in alerts(planner_page))
    open_event(volunteer_page, server, planner_api, event_id)
    box = shift_box_text(volunteer_page, shift_id)
    assert "1/1" in box
    assert "The maximum number of participants is reached." in box
    assert sign_up_button(volunteer_page, shift_id).count() == 0
    assert own_states(volunteer_api, shift_id) == []
    stats = shift_stats(planner_api, shift_id)
    assert (stats["max_count"], stats["confirmed_count"]) == (1, 1)


def test_uc3_a1_raising_the_capacity_again_lets_the_volunteer_sign_up(
    planner_page, volunteer_page, planner_api, volunteer_api, volunteer2_api, server
):
    event_id, shift_id = planner_api.new_shift(maximum_number_of_participants="1")
    volunteer2_api.post(f"/shifts/{shift_id}/signup/", SIGN_UP)  # the shift is full
    edit_page(planner_page, server, shift_id)
    planner_page.fill("#id_maximum_number_of_participants", "3")
    save_shift(planner_page)
    open_event(volunteer_page, server, planner_api, event_id)
    sign_up_button(volunteer_page, shift_id).click()
    volunteer_page.wait_for_load_state()
    assert any("successfully signed up" in text for text in alerts(volunteer_page))
    assert own_states(volunteer_api, shift_id) == [1]
    assert shift_stats(planner_api, shift_id)["confirmed_count"] == 2


def test_uc3_a2_changing_the_flow_to_request_and_confirm_makes_signups_requested(
    planner_page, volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    edit_page(planner_page, server, shift_id)
    planner_page.select_option("#id_signup_flow_slug", "request_confirm")
    planner_page.wait_for_load_state("networkidle")
    save_shift(planner_page)
    assert any("has been saved" in text for text in alerts(planner_page))
    open_event(volunteer_page, server, planner_api, event_id)
    assert sign_up_button(volunteer_page, shift_id).inner_text().strip() == "Request"
    sign_up_button(volunteer_page, shift_id).click()
    volunteer_page.wait_for_load_state()
    assert any("successfully requested a participation" in text for text in alerts(volunteer_page))
    assert own_states(volunteer_api, shift_id) == [0]


def test_uc3_e1_capacity_zero_is_rejected_and_the_shift_is_unchanged(
    planner_page, planner_api, server
):
    _, shift_id = planner_api.new_shift(maximum_number_of_participants="5")
    edit_page(planner_page, server, shift_id)
    planner_page.fill("#id_maximum_number_of_participants", "0")
    submit_to_the_server(planner_page)
    assert "Ensure this value is greater than or equal to 1." in field_errors(planner_page)
    assert shift_stats(planner_api, shift_id)["max_count"] == 5


def test_uc3_e2_empty_date_is_rejected_and_the_shift_is_unchanged(
    planner_page, planner_api, server
):
    _, shift_id = planner_api.new_shift()
    before = planner_api.rest(f"/api/shifts/{shift_id}/")["start_time"]
    edit_page(planner_page, server, shift_id)
    planner_page.fill("#id_date", "")
    submit_to_the_server(planner_page)
    assert "This field is required." in field_errors(planner_page)
    assert planner_api.rest(f"/api/shifts/{shift_id}/")["start_time"] == before


def test_uc3_e3_volunteer_cannot_open_the_edit_page_and_the_shift_is_unchanged(
    volunteer_page, planner_api, server
):
    _, shift_id = planner_api.new_shift(maximum_number_of_participants="5")
    response = volunteer_page.goto(f"{server.base}/shifts/{shift_id}/edit/")
    assert response.status == 403
    assert volunteer_page.title().startswith("Permission denied")
    assert shift_stats(planner_api, shift_id)["max_count"] == 5
