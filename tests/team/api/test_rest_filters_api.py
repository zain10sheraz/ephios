"""FR-04 REST read: filters, ordering and paging checked against records the test created itself."""

from tests.team.api.support import unique_day


def titled_events(planner, token, titles, **shift_overrides):
    """Create one event per title (each with a shift) and return {title: event id}."""
    created = {}
    for title in titles:
        event_id = planner.create_event(title=f"{title}-{token}")
        planner.create_shift(event_id, **{**unique_day(), **shift_overrides.get(title, {})})
        created[title] = event_id
    return created


def listed_ids(planner, **params):
    return [event["id"] for event in planner.rest("/api/events/", limit=1000, **params)["results"]]


def test_participation_state_filter_separates_confirmed_from_requested(planner, volunteer):
    _, confirmed_shift = planner.new_shift(signup_flow_slug="instant_confirmation")
    _, requested_shift = planner.new_shift(signup_flow_slug="request_confirm")
    volunteer.post(f"/shifts/{confirmed_shift}/signup/", {"signup_choice": "sign_up"})
    volunteer.post(f"/shifts/{requested_shift}/signup/", {"signup_choice": "sign_up"})
    own = "/api/users/me/participations/"
    confirmed = {p["shift"] for p in volunteer.rest(own, state=1, limit=1000)["results"]}
    requested = {p["shift"] for p in volunteer.rest(own, state=0, limit=1000)["results"]}
    assert confirmed_shift in confirmed
    assert requested_shift in requested
    assert requested_shift not in confirmed
    assert confirmed_shift not in requested


def test_ordering_by_title_ascending_and_descending(planner):
    token = "ordtest"
    events = titled_events(planner, token, ["Aaa", "Mmm", "Zzz"])
    expected = [events["Aaa"], events["Mmm"], events["Zzz"]]
    assert listed_ids(planner, search=token, ordering="title") == expected
    assert listed_ids(planner, search=token, ordering="-title") == expected[::-1]


def test_start_time_filters_split_events_at_a_date(planner):
    token = "datetest"
    events = titled_events(
        planner,
        token,
        ["early", "late"],
        early={"date": "2085-01-10", "signup_until_0": "2085-01-09"},
        late={"date": "2086-01-10", "signup_until_0": "2086-01-09"},
    )
    cut = "2085-06-01T00:00:00Z"
    assert listed_ids(planner, search=token, start_time_after=cut) == [events["late"]]
    assert listed_ids(planner, search=token, start_time_before=cut) == [events["early"]]


def test_paging_with_limit_and_offset_walks_through_the_same_records(planner):
    token = "pagetest"
    events = titled_events(planner, token, ["p1", "p2", "p3"])
    first = planner.rest("/api/events/", search=token, ordering="title", limit=1, offset=0)
    second = planner.rest("/api/events/", search=token, ordering="title", limit=1, offset=1)
    assert first["count"] == second["count"] == 3
    assert [first["results"][0]["id"], second["results"][0]["id"]] == [events["p1"], events["p2"]]
