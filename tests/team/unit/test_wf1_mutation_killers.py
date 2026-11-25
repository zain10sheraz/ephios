"""
Tests written to kill surviving mutants of core/forms/events.py (mutation round 1, WF1 forms).
Analysis: docs/team/MUTATION.md. Equivalent mutants (not killable): values_list(flat=...) inside a
subquery, `and`->`or` in the two plugin-fallback conditions (the swallowed ValueError gives the same
result), and `<=` -> `<` on a field set that can never be equal to the cleaned_data key set.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group
from django.test import RequestFactory
from guardian.shortcuts import assign_perm, get_users_with_perms

from ephios.core.forms.events import (
    EventCopyForm,
    EventForm,
    EventTypeForm,
    ShiftCopyForm,
    ShiftForm,
)
from ephios.core.models import AbstractParticipation, Event, EventType, LocalParticipation
from ephios.extra.permissions import get_groups_with_perms


def data(**overrides):
    return {"title": "Concert", "description": "d", "location": "Hall", **overrides}


def ids(queryset_or_list):
    return {obj.pk for obj in queryset_or_list}


# ---- required=False on the optional person/group fields
def test_event_can_be_saved_without_any_optional_selection(planner, groups, service_event_type):
    form = EventForm(user=planner, eventtype=service_event_type, data=data())
    assert form.is_valid(), form.errors
    event = form.save()
    assert event.pk is not None


@pytest.mark.parametrize("field", ["visible_for", "responsible_users", "responsible_groups"])
def test_each_optional_selection_may_be_left_empty(planner, groups, service_event_type, field):
    form = EventForm(user=planner, eventtype=service_event_type, data=data())
    form.is_valid()
    assert field not in form.errors


# ---- initial values when editing: direct users only, object-level groups only
def test_edit_form_initial_values_exclude_group_members_and_global_permissions(
    planner, manager, groups, event
):
    managers, planners, volunteers = groups
    assign_perm("change_event", manager, event)  # directly responsible user
    auditors = Group.objects.create(name="Auditors")
    assign_perm("core.view_event", auditors)  # global permission only, must not count
    form = EventForm(user=planner, instance=event)
    assert ids(form.initial["responsible_users"]) == {manager.pk}  # not the planners' members
    assert ids(form.initial["responsible_groups"]) == {planners.pk}  # not global-permission groups
    assert ids(form.initial["visible_for"]) == {volunteers.pk}
    assert "Auditors" not in str(form.fields["visible_for"].help_text)


# ---- initial values for a new event
def test_new_event_initial_visible_for_falls_back_to_publishable_groups(
    planner, groups, service_event_type
):
    managers, planners, volunteers = groups
    form = EventForm(user=planner, eventtype=service_event_type)
    assert ids(form.initial["visible_for"]) == {volunteers.pk}  # the event type has no preference


def test_new_event_initial_visible_for_uses_the_event_type_preference(
    planner, groups, service_event_type
):
    managers, planners, volunteers = groups
    assign_perm("publish_event_for_group", planners, managers)  # two publishable groups now
    service_event_type.preferences["visible_for"] = Group.objects.filter(pk=volunteers.pk)
    form = EventForm(user=planner, eventtype=service_event_type)
    # the preference (volunteers) wins over "all publishable groups" (volunteers + managers)
    assert ids(form.initial["visible_for"]) == {volunteers.pk}


def test_new_event_initial_responsible_users_combine_preference_and_creator(
    planner, manager, groups, service_event_type
):
    service_event_type.preferences["responsible_users"] = type(planner).objects.filter(
        pk=manager.pk
    )
    form = EventForm(user=planner, eventtype=service_event_type)
    assert ids(form.initial["responsible_users"]) == {manager.pk, planner.pk}


def test_new_event_creator_stays_responsible_when_already_in_the_preference(
    planner, groups, service_event_type
):
    service_event_type.preferences["responsible_users"] = type(planner).objects.filter(
        pk=planner.pk
    )
    form = EventForm(user=planner, eventtype=service_event_type)
    assert ids(form.initial["responsible_users"]) == {planner.pk}


# ---- save() is atomic
def test_failure_while_assigning_permissions_rolls_back_the_event(
    planner, groups, service_event_type
):
    form = EventForm(
        user=planner,
        eventtype=service_event_type,
        data=data(responsible_users=[planner.pk]),
    )
    assert form.is_valid(), form.errors
    with (
        patch("ephios.core.forms.events.assign_perm", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError),
    ):
        form.save()
    assert Event.all_objects.filter(title="Concert").count() == 0


# ---- permissions are the union (OR), never the symmetric difference
def test_group_that_is_visible_and_responsible_gets_both_permissions(
    planner, groups, service_event_type
):
    managers, planners, volunteers = groups
    assign_perm(
        "publish_event_for_group", planners, planners
    )  # planners may publish for themselves too
    form = EventForm(
        user=planner,
        eventtype=service_event_type,
        data=data(visible_for=[planners.id], responsible_groups=[planners.id]),
    )
    assert form.is_valid(), form.errors
    event = form.save()
    assert planners in get_groups_with_perms(event, only_with_perms_in=["view_event"])
    assert planners in get_groups_with_perms(event, only_with_perms_in=["change_event"])


def test_locked_group_that_is_also_made_responsible_keeps_view_access(planner, groups, event):
    managers, planners, volunteers = groups
    secret = Group.objects.create(name="Secret group")  # planner may not publish for it
    assign_perm("view_event", secret, event)
    form = EventForm(
        user=planner,
        instance=event,
        data=data(
            title=event.title,
            type=event.type.pk,
            responsible_groups=[planners.id, secret.id],
            responsible_users=[planner.id],
        ),
    )
    assert form.is_valid(), form.errors
    saved = form.save()
    assert secret in get_groups_with_perms(saved, only_with_perms_in=["view_event"])
    assert secret in get_groups_with_perms(saved, only_with_perms_in=["change_event"])


def test_user_that_is_responsible_and_participating_gets_direct_view_access(
    planner, volunteer, groups, event
):
    managers, planners, volunteers = groups
    LocalParticipation.objects.create(
        shift=event.shifts.get(), user=volunteer, state=AbstractParticipation.States.CONFIRMED
    )
    form = EventForm(
        user=planner,
        instance=event,
        data=data(
            title=event.title,
            type=event.type.pk,
            responsible_groups=[planners.id],
            responsible_users=[volunteer.pk],
        ),
    )
    assert form.is_valid(), form.errors
    saved = form.save()
    direct_viewers = get_users_with_perms(
        saved, only_with_perms_in=["view_event"], with_group_users=False
    )
    assert volunteer in direct_viewers


# ---- shift form: each installed flow/structure is offered exactly once
def test_shift_form_offers_each_enabled_flow_and_structure_exactly_once(event):
    form = ShiftForm(instance=event.shifts.get())
    flow_slugs = [slug for slug, _label in form.fields["signup_flow_slug"].widget.choices]
    structure_slugs = [slug for slug, _label in form.fields["structure_slug"].widget.choices]
    assert flow_slugs.count("request_confirm") == 1
    assert flow_slugs.count("instant_confirmation") == 1
    assert structure_slugs.count("uniform") == 1


# ---- copy forms
def test_shift_copy_form_lets_the_user_pick_the_hour_but_event_copy_does_not():
    assert ShiftCopyForm().fields["recurrence"].widget.pick_hour is True
    assert EventCopyForm().fields["recurrence"].widget.pick_hour is False


# ---- event type form
def test_invalid_colour_reports_the_specific_message():
    form = EventTypeForm(
        data={
            "title": "Training",
            "color": "#12345",
            "show_participant_data": 0,
            "default_description": "",
        }
    )
    assert form.is_valid() is False
    assert form.errors["color"] == ["You need to enter a valid color"]


def test_event_type_form_save_persists_by_default():
    form = EventTypeForm(
        data={
            "title": "Rescue drill",
            "color": "#00ff00",
            "show_participant_data": 0,
            "default_description": "",
        }
    )
    assert form.is_valid(), form.errors
    form.save()
    assert EventType.objects.filter(title="Rescue drill").exists()


def test_event_request_factory_is_available_for_forms():
    assert RequestFactory().get("/").path == "/"
