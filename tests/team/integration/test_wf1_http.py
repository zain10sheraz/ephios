"""
HTTP integration tests of WF1 (Event and Shift Management) through the real views.

Rules covered:
BR-W6  Saving a shift activates its event.
BR-W7  The last shift of an event cannot be deleted (boundary: 1 shift refused, 2 shifts allowed).
BR-W8  Inactive events are visible only to users who may add events.
BR-W9  Deleting an event needs delete_event AND change_event; creating needs add_event.
Roles: Planner (add/change/delete) versus Volunteer (view only).
"""

from datetime import timedelta

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from guardian.shortcuts import assign_perm

from ephios.core.models import Event, LocalParticipation, Shift
from ephios.core.models.events import AbstractParticipation

SHIFT_DATA = dict(
    date="2099-06-30",
    meeting_time="09:00",
    start_time="10:00",
    end_time="16:00",
    label="",
    signup_flow_slug="request_confirm",
    structure_slug="uniform",
)


@pytest.fixture
def inactive_event(groups, service_event_type, planner):
    managers, planners, volunteers = groups
    event = Event.objects.create(
        title="Draft Event", type=service_event_type, location="x", active=False
    )
    assign_perm("view_event", [volunteers, planners], event)
    assign_perm("change_event", planners, event)
    return event


def messages_of(response):
    return " | ".join(str(m) for m in get_messages(response.wsgi_request))


def add_shift_url(event):
    return reverse("core:event_createshift", kwargs={"pk": event.pk})


def make_second_shift(event):
    first = event.shifts.get()
    return Shift.objects.create(
        event=event,
        meeting_time=first.meeting_time + timedelta(days=1),
        start_time=first.start_time + timedelta(days=1),
        end_time=first.end_time + timedelta(days=1),
        signup_flow_slug="request_confirm",
        structure_slug="uniform",
    )


# ------------------------------------------------------------ FR-01: create event
def test_planner_creates_an_event_and_is_sent_on_to_add_a_shift(
    client, planner, groups, service_event_type
):
    managers, planners, volunteers = groups
    client.force_login(planner)
    response = client.post(
        reverse("core:event_create", kwargs={"type": service_event_type.pk}),
        {
            "title": "Seeed Concert",
            "description": "Medical service",
            "location": "BOS ARENA",
            "visible_for": [volunteers.id],
            "responsible_groups": [planners.id],
            "responsible_users": [planner.id],
        },
    )
    event = Event.all_objects.get(title="Seeed Concert")
    assert response.status_code == 302
    assert response.url == add_shift_url(event)
    assert event.active is False  # becomes active when its first shift is saved
    assert event.shifts.count() == 0
    assert planner.has_perm("core.change_event", event)


def test_event_without_a_title_is_not_created(client, planner, groups, service_event_type):
    client.force_login(planner)
    response = client.post(
        reverse("core:event_create", kwargs={"type": service_event_type.pk}),
        {"title": "", "description": "d", "location": "x"},
    )
    assert response.status_code == 200
    assert Event.all_objects.count() == 0


def test_creating_events_needs_the_add_event_permission(
    client, volunteer, groups, service_event_type
):
    client.force_login(volunteer)
    response = client.post(
        reverse("core:event_create", kwargs={"type": service_event_type.pk}),
        {"title": "Sneaky", "description": "d", "location": "x"},
    )
    assert response.status_code == 403
    assert Event.all_objects.count() == 0


def test_event_creation_form_page_renders_for_planner(client, planner, groups, service_event_type):
    client.force_login(planner)
    response = client.get(reverse("core:event_create", kwargs={"type": service_event_type.pk}))
    assert response.status_code == 200


# ------------------------------------------------------------ FR-02 / FR-03 / BR-W6: add a shift
def test_saving_the_first_shift_activates_the_event(client, planner, inactive_event):
    client.force_login(planner)
    response = client.post(add_shift_url(inactive_event), SHIFT_DATA)
    assert response.status_code == 302
    shift = inactive_event.shifts.get()
    assert shift.signup_flow_slug == "request_confirm"
    assert shift.structure_slug == "uniform"
    assert shift.start_time.hour is not None
    inactive_event.refresh_from_db()
    assert inactive_event.active is True
    assert "has been saved" in messages_of(response)


def test_shift_is_stored_with_the_posted_configuration(client, planner, inactive_event):
    client.force_login(planner)
    client.post(
        add_shift_url(inactive_event),
        {
            **SHIFT_DATA,
            "maximum_number_of_participants": "7",
            "minimum_age": "18",
            "user_can_decline_confirmed": "on",
        },
    )
    shift = inactive_event.shifts.get()
    assert shift.structure_configuration["maximum_number_of_participants"] == 7
    assert shift.structure_configuration["minimum_age"] == 18
    assert shift.signup_flow_configuration["user_can_decline_confirmed"] is True


@pytest.mark.parametrize(
    "override",
    [
        {"meeting_time": "10:30"},  # after start (BR-W1)
        {"signup_flow_slug": "no-such-flow"},
        {"structure_slug": "no-such-structure"},
        {"signup_flow_slug": ""},
        {"maximum_number_of_participants": "0"},  # below the minimum of 1
    ],
    ids=[
        "meeting_after_start",
        "unknown_flow",
        "unknown_structure",
        "missing_flow",
        "maximum_zero",
    ],
)
def test_invalid_shift_data_is_rejected_and_nothing_is_stored(
    client, planner, inactive_event, override
):
    client.force_login(planner)
    response = client.post(add_shift_url(inactive_event), {**SHIFT_DATA, **override})
    assert response.status_code == 200
    assert inactive_event.shifts.count() == 0
    inactive_event.refresh_from_db()
    assert inactive_event.active is False


def test_add_another_redirects_back_to_the_shift_form(client, planner, inactive_event):
    client.force_login(planner)
    response = client.post(add_shift_url(inactive_event), {**SHIFT_DATA, "addAnother": "1"})
    assert response.status_code == 302
    assert response.url == add_shift_url(inactive_event)
    assert inactive_event.shifts.count() == 1


def test_adding_a_shift_needs_change_permission_on_the_event(client, volunteer, inactive_event):
    client.force_login(volunteer)
    response = client.post(add_shift_url(inactive_event), SHIFT_DATA)
    assert response.status_code == 403
    assert inactive_event.shifts.count() == 0


def test_shift_form_page_renders_for_planner(client, planner, inactive_event):
    client.force_login(planner)
    assert client.get(add_shift_url(inactive_event)).status_code == 200


# ------------------------------------------------------------ edit event and shift
def test_planner_edits_the_event(client, planner, groups, event):
    managers, planners, volunteers = groups
    client.force_login(planner)
    response = client.post(
        reverse("core:event_edit", kwargs={"pk": event.pk}),
        {
            "title": "Renamed Festival",
            "type": event.type.pk,
            "description": "new",
            "location": "Berlin",
            "visible_for": [volunteers.id],
            "responsible_groups": [planners.id],
            "responsible_users": [planner.id],
        },
    )
    assert response.status_code == 302
    event.refresh_from_db()
    assert event.title == "Renamed Festival"
    assert event.location == "Berlin"


def test_volunteer_cannot_edit_an_event(client, volunteer, event):
    client.force_login(volunteer)
    response = client.post(
        reverse("core:event_edit", kwargs={"pk": event.pk}),
        {"title": "Hacked", "type": event.type.pk, "description": "d", "location": "x"},
    )
    assert response.status_code == 403
    event.refresh_from_db()
    assert event.title == "Fission Festival"


def test_planner_edits_a_shift(client, planner, event):
    shift = event.shifts.get()
    client.force_login(planner)
    response = client.post(
        reverse("core:shift_edit", kwargs={"pk": shift.pk}),
        {**SHIFT_DATA, "label": "Night shift", "maximum_number_of_participants": "3"},
    )
    assert response.status_code == 302
    shift.refresh_from_db()
    assert shift.label == "Night shift"
    assert shift.structure_configuration["maximum_number_of_participants"] == 3


def test_shift_edit_with_invalid_time_is_rejected(client, planner, event):
    shift = event.shifts.get()
    client.force_login(planner)
    response = client.post(
        reverse("core:shift_edit", kwargs={"pk": shift.pk}), {**SHIFT_DATA, "meeting_time": "11:00"}
    )
    assert response.status_code == 200
    shift.refresh_from_db()
    assert shift.label == ""


def test_shift_edit_page_renders_for_planner(client, planner, event):
    client.force_login(planner)
    assert (
        client.get(reverse("core:shift_edit", kwargs={"pk": event.shifts.get().pk})).status_code
        == 200
    )


def test_volunteer_cannot_edit_a_shift(client, volunteer, event):
    shift = event.shifts.get()
    client.force_login(volunteer)
    response = client.post(
        reverse("core:shift_edit", kwargs={"pk": shift.pk}), {**SHIFT_DATA, "label": "x"}
    )
    assert response.status_code == 403


# ------------------------------------------------------------ activate
def test_planner_can_activate_an_inactive_event(client, planner, inactive_event):
    client.force_login(planner)
    response = client.post(reverse("core:event_activate", kwargs={"pk": inactive_event.pk}))
    assert response.status_code == 302
    inactive_event.refresh_from_db()
    assert inactive_event.active is True


def test_volunteer_cannot_activate_an_event(client, volunteer, inactive_event):
    client.force_login(volunteer)
    response = client.post(reverse("core:event_activate", kwargs={"pk": inactive_event.pk}))
    assert response.status_code == 403
    inactive_event.refresh_from_db()
    assert inactive_event.active is False


# ------------------------------------------------------------ BR-W7: last shift cannot be deleted
def test_last_shift_cannot_be_deleted(client, planner, event):
    shift = event.shifts.get()
    client.force_login(planner)
    response = client.post(reverse("core:shift_delete", kwargs={"pk": shift.pk}))
    assert response.status_code == 302
    assert "cannot delete the last shift" in messages_of(response)
    assert event.shifts.count() == 1


def test_a_shift_can_be_deleted_when_the_event_has_two(client, planner, event):
    second = make_second_shift(event)
    client.force_login(planner)
    response = client.post(reverse("core:shift_delete", kwargs={"pk": second.pk}))
    assert response.status_code == 302
    assert "has been deleted" in messages_of(response)
    assert event.shifts.count() == 1
    assert not Shift.objects.filter(pk=second.pk).exists()


def test_volunteer_cannot_delete_a_shift(client, volunteer, event):
    second = make_second_shift(event)
    client.force_login(volunteer)
    response = client.post(reverse("core:shift_delete", kwargs={"pk": second.pk}))
    assert response.status_code == 403
    assert Shift.objects.filter(pk=second.pk).exists()


# ------------------------------------------------------------ BR-W9: delete event
def test_planner_deletes_an_event_with_its_shifts_and_participations(
    client, planner, event, volunteer
):
    shift = event.shifts.get()
    LocalParticipation.objects.create(
        shift=shift, user=volunteer, state=AbstractParticipation.States.CONFIRMED
    )
    client.force_login(planner)
    response = client.post(reverse("core:event_delete", kwargs={"pk": event.pk}))
    assert response.status_code == 302
    assert not Event.all_objects.filter(pk=event.pk).exists()
    assert not Shift.objects.filter(pk=shift.pk).exists()
    assert LocalParticipation.objects.filter(shift_id=shift.pk).count() == 0


def test_volunteer_cannot_delete_an_event(client, volunteer, event):
    client.force_login(volunteer)
    response = client.post(reverse("core:event_delete", kwargs={"pk": event.pk}))
    assert response.status_code == 403
    assert Event.all_objects.filter(pk=event.pk).exists()


def test_deleting_needs_both_delete_and_change_permission(client, volunteer, groups, event):
    managers, planners, volunteers = groups
    assign_perm("core.delete_event", volunteers)  # delete without change permission on this event
    client.force_login(volunteer)
    response = client.post(reverse("core:event_delete", kwargs={"pk": event.pk}))
    assert response.status_code == 403
    assert Event.all_objects.filter(pk=event.pk).exists()


# ------------------------------------------------------------ BR-W8: visibility
def test_volunteer_sees_an_active_event_but_not_an_inactive_one(
    client, volunteer, event, inactive_event
):
    client.force_login(volunteer)
    assert client.get(event.get_absolute_url()).status_code == 200
    assert client.get(inactive_event.get_absolute_url()).status_code == 404


def test_planner_sees_inactive_events(client, planner, inactive_event):
    client.force_login(planner)
    assert client.get(inactive_event.get_absolute_url()).status_code == 200


def test_event_list_shows_active_events_to_a_volunteer(client, volunteer, event, inactive_event):
    client.force_login(volunteer)
    response = client.get(reverse("core:event_list"))
    assert response.status_code == 200
    assert b"Fission Festival" in response.content
    assert b"Draft Event" not in response.content


def test_anonymous_users_are_sent_to_login(client, event):
    response = client.get(reverse("core:event_list"))
    assert response.status_code == 302
    assert "login" in response.url
