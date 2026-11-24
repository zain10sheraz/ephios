"""
HTTP tests of WF1 helper endpoints: the shift configuration-form fragments (used by the shift form's
JavaScript) and the event list filters (search, type, date direction with BVA, participation state).
DEFECT-004 (issue #7): crafted fragment URLs raise an unhandled ValueError (HTTP 500).
"""

import logging

import pytest
from django.test import Client
from django.urls import reverse

from ephios.core.models import AbstractParticipation, EventType, LocalParticipation

S = AbstractParticipation.States


def flow_fragment_url(event, slug="request_confirm", query=""):
    return (
        reverse("core:signup_flow_configuration_form", kwargs={"event_id": event.pk, "slug": slug})
        + query
    )


def structure_fragment_url(event, slug="uniform", query=""):
    return (
        reverse(
            "core:shift_structure_configuration_form", kwargs={"event_id": event.pk, "slug": slug}
        )
        + query
    )


def get_quietly(user, url):
    """GET without raising server exceptions into the test; the expected error log is muted."""
    client = Client(raise_request_exception=False)
    client.force_login(user)
    logging.disable(logging.CRITICAL)
    try:
        return client.get(url)
    finally:
        logging.disable(logging.NOTSET)


# ------------------------------------------------------------ fragments: valid use
def test_flow_fragment_returns_the_configuration_fields(client, planner, event):
    client.force_login(planner)
    response = client.get(flow_fragment_url(event))
    assert response.status_code == 200
    assert b"signup_until" in response.content
    assert b"user_can_decline_confirmed" in response.content


def test_structure_fragment_returns_the_configuration_fields(client, planner, event):
    client.force_login(planner)
    response = client.get(structure_fragment_url(event))
    assert response.status_code == 200
    assert b"maximum_number_of_participants" in response.content


def test_fragment_for_an_existing_shift_is_prefilled_from_its_configuration(client, planner, event):
    shift = event.shifts.get()
    client.force_login(planner)
    response = client.get(structure_fragment_url(event, query=f"?shift_id={shift.pk}"))
    assert response.status_code == 200
    assert b'value="1"' in response.content  # maximum_number_of_participants = 1 in the fixture


def test_fragment_for_a_shift_id_of_another_event_is_treated_as_new(client, planner, event):
    client.force_login(planner)
    response = client.get(flow_fragment_url(event, query="?shift_id=999999"))
    assert response.status_code == 200


def test_fragments_need_change_permission(client, volunteer, event):
    client.force_login(volunteer)
    assert client.get(flow_fragment_url(event)).status_code == 403
    assert client.get(structure_fragment_url(event)).status_code == 403


# ------------------------------------------------------------ fragments: DEFECT-004
@pytest.mark.parametrize(
    "builder, args",
    [
        (flow_fragment_url, {"slug": "no-such-flow"}),
        (flow_fragment_url, {"query": "?shift_id=abc"}),
        (structure_fragment_url, {"slug": "no-such-structure"}),
        (structure_fragment_url, {"query": "?shift_id=abc"}),
    ],
    ids=[
        "flow_unknown_slug",
        "flow_bad_shift_id",
        "structure_unknown_slug",
        "structure_bad_shift_id",
    ],
)
def test_crafted_fragment_urls_give_a_client_error_not_a_server_error(
    planner, event, builder, args
):
    response = get_quietly(planner, builder(event, **args))
    assert response.status_code < 500


# ------------------------------------------------------------ event list filters
def listing(client, user, **params):
    client.force_login(user)
    response = client.get(reverse("core:event_list"), params)
    assert response.status_code == 200
    return response.content.decode()


@pytest.mark.parametrize(
    "query, expected",
    [
        ("Fission", True),  # title
        ("fission", True),  # case-insensitive
        ("Lärz", True),  # location
        ("rescue", True),  # description
        ("nothing-matches-this", False),
    ],
    ids=["title", "case_insensitive", "location", "description", "no_match"],
)
def test_search_matches_title_location_and_description(client, volunteer, event, query, expected):
    page = listing(client, volunteer, query=query, direction="from", date="2099-01-01")
    assert ("Fission Festival" in page) is expected


@pytest.mark.parametrize(
    "direction, date, expected",
    [
        ("from", "2099-06-29", True),  # day before the event ends
        ("from", "2099-06-30", True),  # the day it ends
        ("from", "2099-07-01", False),  # day after it ended
        ("until", "2099-06-29", False),  # day before it starts
        ("until", "2099-06-30", True),  # the day it starts
        ("until", "2099-07-01", True),  # day after it started
    ],
    ids=[
        "from_before",
        "from_on_end_day",
        "from_after",
        "until_before",
        "until_on_start_day",
        "until_after",
    ],
)
def test_date_filter_boundaries(client, volunteer, event, direction, date, expected):
    page = listing(client, volunteer, direction=direction, date=date)
    assert ("Fission Festival" in page) is expected


def test_type_filter_includes_and_excludes(client, volunteer, event, training_event_type):
    included = listing(
        client, volunteer, types=[event.type.pk], direction="from", date="2099-01-01"
    )
    excluded = listing(
        client, volunteer, types=[training_event_type.pk], direction="from", date="2099-01-01"
    )
    assert "Fission Festival" in included
    assert "Fission Festival" not in excluded


@pytest.mark.parametrize(
    "participation_state, state_filter, expected",
    [
        (None, "no-response", True),
        (S.REQUESTED, "no-response", False),
        (S.CONFIRMED, "confirmed", True),
        (S.REQUESTED, "confirmed", False),
        (S.REQUESTED, "requested-confirmed", True),
        (S.USER_DECLINED, "requested-confirmed", False),
        (None, "confirmed", False),
        (None, "", True),
    ],
    ids=[
        "none_no_response",
        "requested_no_response",
        "confirmed_confirmed",
        "requested_confirmed_filter",
        "requested_requested_confirmed",
        "declined_requested_confirmed",
        "none_confirmed_filter",
        "none_all",
    ],
)
def test_participation_state_filter(
    client, volunteer, event, participation_state, state_filter, expected
):
    if participation_state is not None:
        LocalParticipation.objects.create(
            shift=event.shifts.get(), user=volunteer, state=participation_state
        )
    page = listing(client, volunteer, state=state_filter, direction="from", date="2099-01-01")
    assert ("Fission Festival" in page) is expected


def test_pending_filter_shows_events_with_requests_to_decide_for_responsibles(
    client, planner, volunteer, event
):
    LocalParticipation.objects.create(shift=event.shifts.get(), user=volunteer, state=S.REQUESTED)
    page = listing(client, planner, state="pending", direction="from", date="2099-01-01")
    assert "Fission Festival" in page


def test_pending_filter_hides_events_without_requests(client, planner, event):
    page = listing(client, planner, state="pending", direction="from", date="2099-01-01")
    assert "Fission Festival" not in page


def test_invalid_filter_values_do_not_break_the_list(client, volunteer, event):
    client.force_login(volunteer)
    response = client.get(
        reverse("core:event_list"), {"date": "not-a-date", "direction": "sideways"}
    )
    assert response.status_code == 200


def test_event_type_exists_for_the_filter(service_event_type):
    assert EventType.objects.filter(pk=service_event_type.pk).exists()
