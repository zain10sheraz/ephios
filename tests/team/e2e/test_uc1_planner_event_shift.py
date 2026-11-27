"""UC1 - planner creates an event with a shift (docs/team/USE_CASES.md). One test per flow.

Each test asserts the result shown on screen and the post-conditions read back from the stored state
(REST API and, for rejections, the row counts of the database).
"""

from tests.team.e2e.pages import (
    alerts,
    create_event_in_ui,
    field_errors,
    fill_shift_form,
    save_shift,
    submit_without_browser_validation,
)


def shifts_of(api, event_id):
    return api.rest(f"/api/events/{event_id}/")["shifts"]


def test_uc1_main_planner_creates_event_and_shift(planner_page, planner_api, server):
    event_id = create_event_in_ui(planner_page, server.base, "UC1 main event")
    fill_shift_form(planner_page)
    save_shift(planner_page)
    assert any("UC1 main event has been saved" in text for text in alerts(planner_page))
    assert planner_page.inner_text("h1") == "UC1 main event"
    [shift] = shifts_of(planner_api, event_id)
    assert shift["signup_stats"]["max_count"] == 5
    assert (
        planner_api.get(f"/api/events/{event_id}/").status_code == 200
    )  # saving the shift activated the event


def test_uc1_a1_request_flow_makes_later_signups_requested(
    planner_page, planner_api, volunteer_api, server
):
    event_id = create_event_in_ui(planner_page, server.base, "UC1 request flow")
    fill_shift_form(planner_page, flow="request_confirm", date="2099-03-02")
    save_shift(planner_page)
    [shift] = shifts_of(planner_api, event_id)
    assert shift["signup_flow_slug"] == "request_confirm"
    volunteer_api.post(f"/shifts/{shift['id']}/signup/", {"signup_choice": "sign_up"})
    states = volunteer_api.rest("/api/users/me/participations/", shift=shift["id"])["results"]
    assert [participation["state"]["value"] for participation in states] == [0]


def test_uc1_a2_planner_raises_the_capacity_of_the_shift(planner_page, planner_api, server):
    event_id, shift_id = planner_api.new_shift(maximum_number_of_participants="5")
    planner_page.goto(f"{server.base}/shifts/{shift_id}/edit/")
    planner_page.fill("#id_maximum_number_of_participants", "8")
    save_shift(planner_page)
    assert any("has been saved" in text for text in alerts(planner_page))
    shifts = shifts_of(planner_api, event_id)
    assert [shift["signup_stats"]["max_count"] for shift in shifts] == [8]


def test_uc1_e1_empty_title_is_rejected_and_nothing_is_stored(planner_page, server):
    before = server.db_count("event")
    planner_page.goto(f"{server.base}/events/create/1/")
    planner_page.fill("#id_location", "Test hall")
    submit_without_browser_validation(planner_page)
    assert "This field is required." in field_errors(planner_page)
    assert planner_page.url.endswith("/events/create/1/")
    assert server.db_count("event") == before


def test_uc1_e2_meeting_after_start_is_rejected_with_an_error_naming_the_rule(planner_page, server):
    create_event_in_ui(planner_page, server.base, "UC1 bad times")
    before = server.db_count("shift")
    fill_shift_form(planner_page, meeting_time="11:00", start_time="10:00")
    save_shift(planner_page)
    assert "Meeting time must not be after start time!" in field_errors(planner_page)
    assert server.db_count("shift") == before


def test_uc1_e3_volunteer_cannot_open_the_create_event_page(volunteer_page, server):
    before = server.db_count("event")
    response = volunteer_page.goto(f"{server.base}/events/create/1/")
    assert response.status == 403
    assert volunteer_page.title().startswith("Permission denied")
    assert server.db_count("event") == before
