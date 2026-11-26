"""Access control over HTTP: unauthenticated and unauthorised requests are refused and change nothing (FR-09)."""

import pytest

REST_PATHS = [
    "/api/events/",
    "/api/events/1/",
    "/api/shifts/",
    "/api/shifts/1/",
    "/api/participations/",
    "/api/participations/1/",
    "/api/users/me/participations/",
]


@pytest.mark.parametrize("path", REST_PATHS)
def test_rest_endpoint_refuses_anonymous_requests(anonymous, path):
    assert anonymous.get(path).status_code == 403


def test_volunteer_cannot_add_a_shift_to_an_event(planner, volunteer):
    event = planner.create_event()
    assert (
        volunteer.post(f"/events/{event}/createshift/", {"date": "2099-01-01"}).status_code == 403
    )
    assert (
        planner.get(f"/api/events/{event}/").status_code == 404
    )  # still no shift, so still inactive and unlisted


def test_volunteer_cannot_activate_an_event(planner, volunteer):
    event = planner.create_event()
    assert volunteer.post(f"/events/{event}/activate/", {}).status_code == 403


def test_volunteer_cannot_create_an_event(volunteer):
    assert volunteer.post("/events/create/1/", {"title": "x", "location": "y"}).status_code == 403


def test_create_event_endpoint_refuses_put(planner):
    # observed: 403, not 405 - the permission check runs before the method check (documented as a weakness)
    assert planner.request("PUT", "/events/create/1/").status_code == 403
