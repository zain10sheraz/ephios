"""UC5 - planner deletes a shift or an event (docs/team/USE_CASES_ZAIN.md; BR-W7: the last shift cannot be deleted).

One test per flow. Each asserts the result shown on the screen and the post-conditions read back from stored state
(REST API and database row counts).
"""

from tests.team.api.support import unique_day
from tests.team.e2e.pages import alerts, event_path

SIGN_UP = {"signup_choice": "sign_up"}


def delete_in_ui(page, server, kind, object_id):
    """Open the confirmation page of a shift or an event and confirm the deletion."""
    page.goto(f"{server.base}/{kind}/{object_id}/delete/")
    page.click("form button[type=submit]")
    page.wait_for_load_state()


def event_with_two_shifts(planner_api):
    event_id, first = planner_api.new_shift()
    second = planner_api.create_shift(event_id, **unique_day())
    return event_id, first, second


def test_uc5_main_planner_deletes_the_second_shift_of_an_event(planner_page, planner_api, server):
    event_id, first, second = event_with_two_shifts(planner_api)
    delete_in_ui(planner_page, server, "shifts", second)
    assert "The shift has been deleted." in alerts(planner_page)
    assert [shift["id"] for shift in planner_api.rest(f"/api/events/{event_id}/")["shifts"]] == [
        first
    ]
    assert planner_api.get(f"/api/shifts/{second}/").status_code == 404


def test_uc5_a1_planner_deletes_the_whole_event_with_its_shifts(planner_page, planner_api, server):
    event_id, first, second = event_with_two_shifts(planner_api)
    shifts_before = server.db_count("shift")
    delete_in_ui(planner_page, server, "events", event_id)
    assert planner_page.url == f"{server.base}/events/"
    assert planner_api.get(f"/api/events/{event_id}/").status_code == 404
    assert planner_api.get(f"/api/shifts/{first}/").status_code == 404
    assert server.db_count("shift") == shifts_before - 2


def test_uc5_a2_deleting_a_shift_removes_the_participation_on_it(
    planner_page, planner_api, volunteer_api, server
):
    event_id, first, second = event_with_two_shifts(planner_api)
    volunteer_api.post(f"/shifts/{first}/signup/", SIGN_UP)
    participations_before = server.db_count("abstractparticipation")
    delete_in_ui(planner_page, server, "shifts", first)
    assert "The shift has been deleted." in alerts(planner_page)
    assert server.db_count("abstractparticipation") == participations_before - 1
    assert planner_api.get(f"/api/shifts/{first}/").status_code == 404


def test_uc5_e1_the_last_shift_cannot_be_deleted(planner_page, planner_api, server):
    event_id, shift_id = planner_api.new_shift()
    delete_in_ui(planner_page, server, "shifts", shift_id)
    assert "You cannot delete the last shift!" in alerts(planner_page)
    assert planner_page.url.startswith(f"{server.base}/events/{event_id}-")
    assert planner_api.get(f"/api/shifts/{shift_id}/").status_code == 200


def test_uc5_e2_volunteer_cannot_open_the_delete_page(volunteer_page, planner_api, server):
    event_id, first, second = event_with_two_shifts(planner_api)
    shifts_before = server.db_count("shift")
    response = volunteer_page.goto(f"{server.base}/shifts/{second}/delete/")
    assert response.status == 403
    assert volunteer_page.title().startswith("Permission denied")
    assert server.db_count("shift") == shifts_before


def test_uc5_e3_anonymous_user_is_sent_to_the_login_page_and_nothing_is_deleted(
    anonymous_page, planner_api, server
):
    event_id, first, second = event_with_two_shifts(planner_api)
    shifts_before = server.db_count("shift")
    anonymous_page.goto(f"{server.base}/shifts/{second}/delete/")
    assert f"/accounts/login/?next=/shifts/{second}/delete/" in anonymous_page.url
    assert server.db_count("shift") == shifts_before
    assert event_path(planner_api, event_id)  # the event is still readable
