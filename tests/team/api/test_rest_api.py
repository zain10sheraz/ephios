"""FR-04: the read-only REST API, tested over real HTTP against the running application."""

import pytest


def test_unauthenticated_request_is_refused(anonymous):
    assert anonymous.get("/api/events/").status_code == 403


def test_event_list_has_pagination_envelope(planner):
    page = planner.rest("/api/events/")
    assert {"count", "results"} <= set(page)
    assert page["count"] >= len(page["results"])


def test_created_event_is_read_back_with_its_shift(planner):
    event_id, shift_id = planner.new_shift()
    event = planner.rest(f"/api/events/{event_id}/")
    assert event["id"] == event_id
    assert [shift["id"] for shift in event["shifts"]] == [shift_id]


def test_shift_detail_reflects_posted_capacity(planner):
    _, shift_id = planner.new_shift(maximum_number_of_participants="7")
    assert planner.rest(f"/api/shifts/{shift_id}/")["signup_stats"]["max_count"] == 7


def test_search_filter_finds_the_event_by_title(planner):
    title = "Zebra-crossing-unique-title"
    event_id = planner.create_event(title=title)
    planner.create_shift(event_id)  # an event without a shift is not listed
    found = planner.rest("/api/events/", search=title)
    assert [event["id"] for event in found["results"]] == [event_id]


@pytest.mark.parametrize("limit", ["1", "2"])
def test_limit_bounds_page_size(planner, limit):
    planner.new_shift()
    planner.new_shift()
    assert len(planner.rest("/api/events/", limit=limit)["results"]) == int(limit)


def test_own_participations_list_only_own_records(volunteer, volunteer2, planner):
    _, shift_id = planner.new_shift()
    volunteer.post(f"/shifts/{shift_id}/signup/", {"signup_choice": "sign_up"})
    own = {p["shift"] for p in volunteer.rest("/api/users/me/participations/")["results"]}
    other = {p["shift"] for p in volunteer2.rest("/api/users/me/participations/")["results"]}
    assert shift_id in own
    assert shift_id not in other


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_write_methods_are_refused_on_rest_api(planner, method):
    # observed: POST -> 405, DELETE -> 403 (permission check runs before the method check; inconsistent, see API_TESTING.md)
    assert planner.request(method, "/api/events/").status_code in (403, 405)


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
def test_put_and_patch_are_refused_on_rest_api(planner, method):
    event_id = planner.create_event()
    assert planner.request(method, f"/api/events/{event_id}/").status_code in (403, 405)


def test_post_without_csrf_token_is_refused(planner):
    assert (
        planner.post_without_csrf("/events/create/1/", {"title": "x", "location": "y"}).status_code
        == 403
    )
