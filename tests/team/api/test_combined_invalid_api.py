"""Several invalid values in ONE request (the generated cases send one at a time): the form is shown again and nothing is stored."""

from tests.team.api.support import VALID_EVENT, VALID_SHIFT


def test_event_with_empty_title_and_empty_location_is_rejected_and_not_stored(planner, server):
    before = server.db_count("event")
    response = planner.post("/events/create/1/", {**VALID_EVENT, "title": "", "location": ""})
    assert response.status_code == 200
    assert server.db_count("event") == before


def test_shift_with_bad_date_and_bad_capacity_is_rejected_and_not_stored(planner, server):
    event_id, _ = planner.new_shift()
    before = server.db_count("shift")
    response = planner.post(
        f"/events/{event_id}/createshift/",
        {**VALID_SHIFT, "date": "not-a-date", "maximum_number_of_participants": "0"},
    )
    assert response.status_code == 200
    assert server.db_count("shift") == before
