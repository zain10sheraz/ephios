"""UC6 - volunteer signs up with her own times ("Customize") (docs/team/USE_CASES_ZAIN.md).

One test per flow. Each asserts the result shown on the screen and the participation read back through the REST API.
The shifts run 10:00-16:00; the volunteer's own window lies inside it.
"""

from tests.team.api.support import VALID_SHIFT
from tests.team.e2e.pages import alerts, event_path, field_errors, own_states

NOT_ALLOWED = "This action is not allowed."


def open_customize_page(page, server, api, event_id, shift_id):
    """Open the event page and follow the Customize link, as a volunteer does."""
    page.goto(server.base + event_path(api, event_id))
    page.locator(f"#shift-{shift_id} a:has-text('Customize')").click()
    page.wait_for_url(f"**/shifts/{shift_id}/signup/")


def fill_times(page, start="11:00", end="15:00"):
    page.fill("#id_individual_start_time_1", start)
    page.fill("#id_individual_end_time_1", end)


def submit(page, choice="sign_up"):
    page.click(f"button[name=signup_choice][value={choice}]")
    page.wait_for_load_state()


def records(api, shift_id):
    results = api.rest("/api/users/me/participations/", shift=shift_id)["results"]
    return [
        (r["id"], r["state"]["value"], r["start_time"][11:16], r["end_time"][11:16], r["comments"])
        for r in results
    ]


def test_uc6_main_volunteer_signs_up_with_her_own_times_and_a_comment(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    open_customize_page(volunteer_page, server, planner_api, event_id, shift_id)
    fill_times(volunteer_page, "11:00", "15:00")
    volunteer_page.fill("#id_comment", "I bring a car")
    submit(volunteer_page)
    assert any("successfully signed up" in text for text in alerts(volunteer_page))
    [(_, state, start, end, comments)] = records(volunteer_api, shift_id)
    assert (state, start, end) == (1, "11:00", "15:00")
    assert [comment["text"] for comment in comments] == ["I bring a car"]


def test_uc6_a1_customized_signup_on_a_request_flow_shift_is_requested(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="request_confirm")
    open_customize_page(volunteer_page, server, planner_api, event_id, shift_id)
    fill_times(volunteer_page)
    submit(volunteer_page)
    assert any("successfully requested a participation" in text for text in alerts(volunteer_page))
    [(_, state, start, end, _)] = records(volunteer_api, shift_id)
    assert (state, start, end) == (0, "11:00", "15:00")


def test_uc6_a2_changing_the_times_again_updates_the_same_participation(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    open_customize_page(volunteer_page, server, planner_api, event_id, shift_id)
    fill_times(volunteer_page, "11:00", "15:00")
    submit(volunteer_page)
    [(first_id, *_)] = records(volunteer_api, shift_id)
    open_customize_page(volunteer_page, server, planner_api, event_id, shift_id)
    fill_times(volunteer_page, "12:00", "14:00")
    submit(volunteer_page, "customize")
    assert "Your participation was saved." in alerts(volunteer_page)
    [(second_id, state, start, end, _)] = records(volunteer_api, shift_id)
    assert (second_id, state, start, end) == (first_id, 1, "12:00", "14:00")


def test_uc6_e1_end_before_start_is_rejected_and_nothing_is_stored(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift()
    open_customize_page(volunteer_page, server, planner_api, event_id, shift_id)
    fill_times(volunteer_page, "15:00", "11:00")
    submit(volunteer_page)
    assert "End time must not be before start time." in field_errors(volunteer_page)
    assert own_states(volunteer_api, shift_id) == []


def test_uc6_e2_signup_window_closed_meanwhile_is_rejected(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift()
    open_customize_page(volunteer_page, server, planner_api, event_id, shift_id)
    day = planner_api.rest(f"/api/shifts/{shift_id}/")["start_time"][:10]
    closed = {**VALID_SHIFT, "date": day, "signup_until_0": "2000-01-01", "signup_until_1": "08:00"}
    assert planner_api.post(f"/shifts/{shift_id}/edit/", closed).status_code == 302
    fill_times(volunteer_page)
    submit(volunteer_page)
    assert NOT_ALLOWED in alerts(volunteer_page)
    assert own_states(volunteer_api, shift_id) == []


def test_uc6_e3_empty_start_time_is_rejected_and_nothing_is_stored(
    volunteer_page, planner_api, volunteer_api, server
):
    event_id, shift_id = planner_api.new_shift()
    open_customize_page(volunteer_page, server, planner_api, event_id, shift_id)
    volunteer_page.evaluate(
        "document.getElementById('id_comment').form.setAttribute('novalidate', '')"
    )
    volunteer_page.fill("#id_individual_start_time_1", "")
    submit(volunteer_page)
    assert "Enter a valid time." in field_errors(volunteer_page)
    assert own_states(volunteer_api, shift_id) == []
