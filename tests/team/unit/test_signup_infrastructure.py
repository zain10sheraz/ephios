"""
Unit tests for the signup-path infrastructure: participants (age rules), abstract flow contract,
BaseSignupFlow helpers and the participant helper functions used by the signup views.
"""

from datetime import date, timedelta

import pytest
from dateutil.relativedelta import relativedelta
from django.test import RequestFactory
from django.urls import resolve, reverse
from django.utils import timezone

from ephios.core.models import LocalParticipation
from ephios.core.signup.flow.abstract import AbstractSignupFlow
from ephios.core.signup.flow.base import BaseSignupFlow
from ephios.core.signup.flow.participant_validation import BaseSignupActionValidator
from ephios.core.signup.participants import (
    AbstractParticipant,
    PlaceholderParticipant,
    get_nonlocal_participant_from_request,
)
from ephios.core.views.signup import BaseShiftActionView, request_to_participant


@pytest.fixture
def shift_of_event(event):
    return event.shifts.get()


class DummyFlow(BaseSignupFlow):
    slug = "dummy"
    verbose_name = "Dummy"
    description = "A flow without behaviour, used to test the shared base class"


def abstract_participant(born):
    return AbstractParticipant(
        display_name="Test Person", qualifications=[], date_of_birth=born, email=None
    )


# ------------------------------------------------------------ age rules (3-point BVA at the birthday)
@pytest.mark.parametrize(
    "today, expected_age",
    [(date(2020, 6, 14), 19), (date(2020, 6, 15), 20), (date(2020, 6, 16), 20)],
    ids=["day_before_birthday", "on_birthday", "day_after_birthday"],
)
def test_age_changes_exactly_on_the_birthday(today, expected_age):
    assert abstract_participant(date(2000, 6, 15)).get_age(today) == expected_age


def test_age_is_unknown_without_birth_date():
    assert abstract_participant(None).get_age() is None
    assert abstract_participant(None).is_minor is False


@pytest.mark.parametrize(
    "days_after_18th_birthday, expected_minor",
    [(-1, True), (0, False), (1, False)],
    ids=["one_day_before_18", "on_18th_birthday", "one_day_after_18"],
)
def test_is_minor_boundary_at_18(days_after_18th_birthday, expected_minor):
    today = timezone.now().date()
    born = today - relativedelta(years=18) - timedelta(days=days_after_18th_birthday)
    assert abstract_participant(born).is_minor is expected_minor


@pytest.mark.xfail(
    strict=True,
    reason="DEFECT-003 (issue #6): is_minor uses `if age := get_age()`, so age 0 is treated like unknown",
)
def test_a_newborn_is_a_minor():
    assert abstract_participant(timezone.now().date()).is_minor is True


# ------------------------------------------------------------ participant contract
def test_abstract_participant_contract_is_not_implemented():
    participant = abstract_participant(date(2000, 1, 1))
    with pytest.raises(NotImplementedError):
        _ = participant.identifier
    for method in (
        participant.new_participation,
        participant.participation_for,
        participant.reverse_signup_action,
        participant.reverse_event_detail,
    ):
        with pytest.raises(NotImplementedError):
            method(None)
    with pytest.raises(NotImplementedError):
        participant.all_participations()
    assert str(participant) == "Test Person"
    assert "fa-user" in participant.icon


def test_abstract_participant_qualification_helpers(qualifications):
    participant = AbstractParticipant(
        display_name="Medic", qualifications=[qualifications.nfs], date_of_birth=None, email=None
    )
    assert qualifications.nfs in participant.collect_all_qualifications()
    assert participant.has_qualifications([qualifications.nfs])
    assert not participant.has_qualifications([qualifications.na])
    assert qualifications.nfs.uuid in participant.skill


def test_local_participant_helpers(shift_of_event, volunteer):
    participant = volunteer.as_participant()
    assert participant.identifier == f"user-{volunteer.pk}"
    assert participant.reverse_signup_action(shift_of_event).endswith(
        f"/shifts/{shift_of_event.pk}/signup/"
    )
    assert (
        participant.reverse_event_detail(shift_of_event.event)
        == shift_of_event.event.get_absolute_url()
    )
    assert participant.participation_for(shift_of_event) is None
    new = participant.new_participation(shift_of_event)
    assert isinstance(new, LocalParticipation)
    assert new.user == volunteer


def test_placeholder_participant_helpers(shift_of_event):
    placeholder = PlaceholderParticipant(
        display_name="Walk-in", qualifications=[], date_of_birth=None, email=None
    )
    assert placeholder.identifier.startswith("placeholder-")
    assert placeholder.participation_for(shift_of_event) is None
    new = placeholder.new_participation(shift_of_event)
    new.save()
    assert placeholder.participation_for(shift_of_event) == new
    assert placeholder.all_participations().count() == 0
    assert "Placeholder" in placeholder.icon
    with pytest.raises(NotImplementedError):
        placeholder.reverse_signup_action(shift_of_event)
    with pytest.raises(NotImplementedError):
        placeholder.reverse_event_detail(shift_of_event.event)


def test_nonlocal_participant_from_request_is_none_without_plugin_receivers():
    request = RequestFactory().get("/")
    request.resolver_match = resolve(reverse("core:event_list"))
    request.session = {}
    assert get_nonlocal_participant_from_request(request) is None


# ------------------------------------------------------------ view helpers
def test_request_to_participant_for_authenticated_and_anonymous_users(volunteer):
    from django.contrib.auth.models import AnonymousUser

    request = RequestFactory().get("/")
    request.resolver_match = resolve(reverse("core:event_list"))
    request.session = {}
    request.user = volunteer
    assert request_to_participant(request) == volunteer.as_participant()
    request.user = AnonymousUser()
    assert request_to_participant(request) is None


def test_base_shift_action_view_requires_a_participant_provider():
    view = BaseShiftActionView()
    with pytest.raises(NotImplementedError):
        view.get_participant()


# ------------------------------------------------------------ abstract signup flow contract
@pytest.mark.parametrize("name", ["slug", "verbose_name", "description"])
def test_abstract_flow_properties_must_be_overridden(name):
    getter = getattr(AbstractSignupFlow, name).fget
    with pytest.raises(NotImplementedError):
        getter(None)


@pytest.mark.parametrize(
    "name, args",
    [
        ("perform_signup", (None, None)),
        ("perform_decline", (None, None)),
        ("get_signup_info", ()),
        ("get_configuration_form", ()),
    ],
)
def test_abstract_flow_methods_must_be_overridden(name, args):
    method = getattr(AbstractSignupFlow, name)
    with pytest.raises(NotImplementedError):
        method(None, *args)


def test_abstract_flow_defaults():
    assert AbstractSignupFlow.uses_requested_state.fget(None) is True


def test_base_signup_flow_helpers(event):
    shift = event.shifts.get()
    flow = DummyFlow(None)
    assert flow.signup_action_validator_class is BaseSignupActionValidator
    with pytest.raises(NotImplementedError):
        flow._configure_participation(None)
    flow_with_shift = shift.signup_flow
    form = flow_with_shift.get_configuration_form(request=RequestFactory().get("/"))
    assert "signup_until" in form.fields
    assert (
        form.initial["user_can_decline_confirmed"] is True
    )  # from the shift's stored configuration
    detached_form = DummyFlow(None, event=event).get_configuration_form(
        request=RequestFactory().get("/"), shift=None
    )
    assert "signup_until" in detached_form.fields
