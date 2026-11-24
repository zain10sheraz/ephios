"""
Team unit tests for WF1 (Event and Shift Management) business logic.

BR-W1  Shift meeting time must not be after the start time (equal is allowed).
BR-W2  An end time at or before the start time means the next day.
BR-W3  An event is multi-day when its span is >= 23 hours.
BR-W4  Saving an event assigns view/change permissions to the chosen groups and users; locked
       visibility groups and users with participations keep their access.
BR-W5  Event type colour must be a #RRGGBB hex value.
Defect: DEFECT-002 (issue #4) - missing/invalid date or start_time raises KeyError.
"""

from datetime import datetime, timedelta

import pytest
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_users_with_perms

from ephios.core.forms.events import (
    BasePluginFormMixin,
    EventCopyForm,
    EventForm,
    EventTypeForm,
    ShiftCopyForm,
    ShiftForm,
)
from ephios.core.models import AbstractParticipation, Event, LocalParticipation, Shift
from ephios.extra.permissions import get_groups_with_perms

BASE = dict(
    date="2099-06-30",
    meeting_time="09:00",
    start_time="10:00",
    end_time="16:00",
    label="",
    signup_flow_slug="request_confirm",
    structure_slug="uniform",
)


def shift_form(**overrides):
    return ShiftForm(data={**BASE, **overrides})


# ------------------------------------------------------------ BR-W1: meeting <= start (3-point BVA)
@pytest.mark.parametrize(
    "meeting, valid",
    [("09:59", True), ("10:00", True), ("10:01", False)],
    ids=["one_minute_before", "equal", "one_minute_after"],
)
def test_meeting_time_boundary(meeting, valid):
    form = shift_form(meeting_time=meeting)
    assert form.is_valid() is valid
    if not valid:
        assert "must not be after start time" in str(form.errors["meeting_time"])


# ------------------------------------------------------------ BR-W2: end rollover (3-point BVA)
@pytest.mark.parametrize(
    "end, expected_delta",
    [
        ("09:59", timedelta(hours=23, minutes=59)),  # before start -> next day
        ("10:00", timedelta(hours=24)),  # equal to start -> next day
        ("10:01", timedelta(minutes=1)),  # after start -> same day
    ],
    ids=["one_minute_before_start", "equal_to_start", "one_minute_after_start"],
)
def test_end_time_rolls_over_to_next_day(end, expected_delta):
    form = shift_form(end_time=end)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["end_time"] - form.cleaned_data["start_time"] == expected_delta


def test_valid_shift_form_combines_date_with_times():
    form = shift_form()
    assert form.is_valid(), form.errors
    assert form.cleaned_data["meeting_time"].date().isoformat() == "2099-06-30"
    assert form.cleaned_data["start_time"].hour == 10


@pytest.mark.parametrize(
    "field, value",
    [("date", ""), ("date", "not-a-date"), ("start_time", ""), ("start_time", "25:99")],
    ids=["date_empty", "date_invalid", "start_empty", "start_invalid"],
)
@pytest.mark.xfail(
    strict=True,
    raises=KeyError,
    reason="DEFECT-002 (issue #4): clean_*_time read cleaned_data keys that may be missing",
)
def test_missing_or_invalid_date_or_start_is_a_form_error_not_an_exception(field, value):
    form = shift_form(**{field: value})
    assert form.is_valid() is False


@pytest.mark.parametrize(
    "field", ["meeting_time", "end_time", "signup_flow_slug", "structure_slug"]
)
def test_other_required_fields_give_form_errors(field):
    form = shift_form(**{field: ""})
    assert form.is_valid() is False
    assert field in form.errors


# ------------------------------------------------------------ Event model logic
def make_event(event_type, title="Concert"):
    return Event.objects.create(title=title, type=event_type, location="Hall", active=True)


def add_shift(event, start, hours):
    return Shift.objects.create(
        event=event,
        meeting_time=start,
        start_time=start,
        end_time=start + timedelta(hours=hours),
        signup_flow_slug="request_confirm",
        structure_slug="uniform",
        structure_configuration=dict(
            minimum_number_of_participants=2, maximum_number_of_participants=4
        ),
    )


def test_event_without_shifts_has_no_times(service_event_type):
    event = make_event(service_event_type)
    assert event.get_start_time() is None
    assert event.get_end_time() is None
    assert event.is_multi_day() is False


def test_event_times_span_all_shifts(service_event_type, tz):
    event = make_event(service_event_type)
    early = datetime(2099, 6, 30, 8, 0, tzinfo=tz)
    late = datetime(2099, 6, 30, 18, 0, tzinfo=tz)
    add_shift(event, late, 2)
    add_shift(event, early, 3)
    assert event.get_start_time() == early
    assert event.get_end_time() == late + timedelta(hours=2)


@pytest.mark.parametrize(
    "hours, minutes, multi_day",
    [(22, 59, False), (23, 0, True), (23, 1, True)],
    ids=["just_below_23h", "exactly_23h", "just_above_23h"],
)
def test_is_multi_day_boundary(service_event_type, tz, hours, minutes, multi_day):
    event = make_event(service_event_type)
    start = datetime(2099, 6, 30, 8, 0, tzinfo=tz)
    Shift.objects.create(
        event=event,
        meeting_time=start,
        start_time=start,
        end_time=start + timedelta(hours=hours, minutes=minutes),
        signup_flow_slug="request_confirm",
        structure_slug="uniform",
    )
    assert event.is_multi_day() is multi_day


@pytest.mark.parametrize(
    "title, expected_is_title_slug",
    [("Seeed Concert", True), ("!!!", False), ("", False)],
    ids=["normal", "only_symbols", "empty"],
)
def test_canonical_slug_falls_back_to_id(service_event_type, title, expected_is_title_slug):
    event = make_event(service_event_type, title=title)
    slug = event.get_canonical_slug()
    assert (slug == "seeed-concert") is expected_is_title_slug
    if not expected_is_title_slug:
        assert slug == str(event.id)


def test_event_signup_stats_aggregate_over_shifts(service_event_type, tz, volunteer, planner):
    event = make_event(service_event_type)
    first = add_shift(event, datetime(2099, 6, 30, 8, 0, tzinfo=tz), 2)
    add_shift(event, datetime(2099, 6, 30, 12, 0, tzinfo=tz), 2)
    LocalParticipation.objects.create(
        shift=first, user=volunteer, state=AbstractParticipation.States.CONFIRMED
    )
    stats = event.get_signup_stats()
    assert stats.confirmed_count == 1
    assert stats.min_count == 4
    assert stats.max_count == 8
    assert stats.missing == 3


def test_activate_is_idempotent_and_only_changes_inactive_events(service_event_type):
    event = Event.objects.create(title="Draft", type=service_event_type, location="x", active=False)
    event.activate()
    event.refresh_from_db()
    assert event.active is True
    event.activate()
    event.refresh_from_db()
    assert event.active is True


# ------------------------------------------------------------ BR-W4: EventForm permissions
def event_data(**overrides):
    return {"title": "Seeed Concert", "description": "d", "location": "BOS ARENA", **overrides}


def test_new_event_form_assigns_permissions(planner, groups, service_event_type):
    managers, planners, volunteers = groups
    form = EventForm(
        user=planner,
        eventtype=service_event_type,
        data=event_data(
            visible_for=[volunteers.id],
            responsible_groups=[planners.id],
            responsible_users=[planner.id],
        ),
    )
    assert form.is_valid(), form.errors
    event = form.save()
    assert event.type == service_event_type
    assert set(get_groups_with_perms(event, only_with_perms_in=["view_event"])) == {
        volunteers,
        planners,
        managers,
    }
    assert set(get_groups_with_perms(event, only_with_perms_in=["change_event"])) == {
        planners,
        managers,
    }
    responsible = get_users_with_perms(
        event, only_with_perms_in=["change_event"], with_group_users=False
    )
    assert set(responsible) == {planner}
    assert planner in get_users_with_perms(event, only_with_perms_in=["view_event"])


def test_event_form_for_planner_without_publish_rights_disables_visibility(
    volunteer, groups, service_event_type
):
    form = EventForm(user=volunteer, eventtype=service_event_type)
    assert form.fields["visible_for"].disabled is True
    assert form.fields["visible_for"].queryset.count() == 0


def test_edit_keeps_locked_groups_and_participants_visible(
    planner, groups, event, volunteer, manager
):
    managers, planners, volunteers = groups
    secret = Group.objects.create(name="Secret group")  # planner may not publish for it
    assign_perm("view_event", secret, event)
    LocalParticipation.objects.create(
        shift=event.shifts.get(), user=manager, state=AbstractParticipation.States.CONFIRMED
    )
    form = EventForm(
        user=planner,
        instance=event,
        data=event_data(
            title=event.title,
            type=event.type.pk,
            visible_for=[],
            responsible_groups=[planners.id],
            responsible_users=[planner.id],
        ),
    )
    assert "Secret group" in str(form.fields["visible_for"].help_text)
    assert form.is_valid(), form.errors
    saved = form.save()
    assert secret in get_groups_with_perms(saved, only_with_perms_in=["view_event"])
    assert volunteers not in get_groups_with_perms(saved, only_with_perms_in=["view_event"])
    assert manager in get_users_with_perms(
        saved, only_with_perms_in=["view_event"], with_group_users=False
    )


# ------------------------------------------------------------ BR-W5: event type colour
@pytest.mark.parametrize(
    "color, valid",
    [
        ("#12abEF", True),
        ("#000000", True),
        ("#12345", False),
        ("#12345g", False),
        ("123456", False),
    ],
)
def test_event_type_colour_validation(color, valid):
    form = EventTypeForm(
        data={
            "title": "Training",
            "color": color,
            "show_participant_data": 0,
            "default_description": "",
        }
    )
    assert form.is_valid() is valid
    if valid:
        assert form.save().color == color
    else:
        assert "valid color" in str(form.errors["color"]) or "color" in form.errors


# ------------------------------------------------------------ small form helpers
def test_copy_forms_remember_original_start():
    start = datetime(2099, 1, 1, 8, 0)
    assert EventCopyForm(original_start=start).fields["recurrence"].widget.original_start == start
    assert ShiftCopyForm(original_start=start).fields["recurrence"].widget.original_start == start


def test_base_plugin_form_mixin_defaults():
    mixin = BasePluginFormMixin()
    assert mixin.is_function_active() is False
    with pytest.raises(NotImplementedError):
        _ = mixin.heading


def test_edit_removes_access_of_users_no_longer_responsible(planner, groups, event, volunteer):
    managers, planners, volunteers = groups
    assign_perm("change_event", volunteer, event)  # volunteer was responsible before the edit
    assert volunteer.has_perm("core.change_event", event)
    form = EventForm(
        user=planner,
        instance=event,
        data=event_data(
            title=event.title,
            type=event.type.pk,
            visible_for=[volunteers.id],
            responsible_groups=[planners.id],
            responsible_users=[planner.id],
        ),
    )
    assert form.is_valid(), form.errors
    form.save()
    volunteer = type(volunteer).objects.get(pk=volunteer.pk)  # drop guardian's permission cache
    assert not volunteer.has_perm("core.change_event", event)


def test_shift_form_survives_shift_with_uninstalled_flow_and_structure(event):
    shift = event.shifts.get()
    shift.signup_flow_slug = "no-such-flow"
    shift.structure_slug = "no-such-structure"
    form = ShiftForm(instance=shift)
    flow_slugs = [slug for slug, _label in form.fields["signup_flow_slug"].widget.choices]
    structure_slugs = [slug for slug, _label in form.fields["structure_slug"].widget.choices]
    assert "no-such-flow" not in flow_slugs
    assert "no-such-structure" not in structure_slugs
    assert "request_confirm" in flow_slugs
    assert "uniform" in structure_slugs
