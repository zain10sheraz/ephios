"""
Cross-workflow tests (FR-09): the planner changes the shared Shift record through WF1 (HTTP shift edit)
and volunteers act on it through WF2 (HTTP signup). The shared records are read back after every step.

Shared record: Shift (maximum participants, signup deadline); WF1 changes it, WF2 reads it.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils.timezone import localtime

from ephios.core.models import AbstractParticipation, LocalParticipation

S = AbstractParticipation.States

SHIFT_FORM = dict(
    date="2099-06-30",
    meeting_time="09:00",
    start_time="10:00",
    end_time="16:00",
    label="",
    signup_flow_slug="instant_confirmation",
    structure_slug="uniform",
)


@pytest.fixture
def shift(event):
    return event.shifts.get()


def planner_edits(client, planner, shift, **fields):
    client.force_login(planner)
    response = client.post(
        reverse("core:shift_edit", kwargs={"pk": shift.pk}), {**SHIFT_FORM, **fields}
    )
    assert response.status_code == 302, "the shift edit itself must succeed"
    shift.refresh_from_db()


def volunteer_signs_up(client, user, shift):
    client.force_login(user)
    return client.post(
        reverse("core:signup_action", kwargs={"pk": shift.pk}),
        {"quick_action": "1", "signup_choice": "sign_up"},
    )


def state_of(shift, user):
    participation = LocalParticipation.objects.filter(shift=shift, user=user).first()
    return participation.state if participation else None


def test_capacity_change_by_the_planner_is_enforced_for_the_next_volunteer(
    client, shift, planner, volunteer, qualified_volunteer
):
    planner_edits(client, planner, shift, maximum_number_of_participants="1")
    assert shift.structure_configuration["maximum_number_of_participants"] == 1

    volunteer_signs_up(client, volunteer, shift)
    assert state_of(shift, volunteer) == S.CONFIRMED

    volunteer_signs_up(client, qualified_volunteer, shift)
    assert state_of(shift, qualified_volunteer) is None  # rejected: capacity 1 is full

    planner_edits(client, planner, shift, maximum_number_of_participants="2")
    volunteer_signs_up(client, qualified_volunteer, shift)
    assert state_of(shift, qualified_volunteer) == S.CONFIRMED  # the raised capacity is honoured
    assert LocalParticipation.objects.filter(shift=shift, state=S.CONFIRMED).count() == 2


def test_lowering_capacity_below_current_signups_blocks_new_ones_but_keeps_existing(
    client, shift, planner, volunteer, qualified_volunteer
):
    planner_edits(client, planner, shift, maximum_number_of_participants="5")
    volunteer_signs_up(client, volunteer, shift)
    planner_edits(client, planner, shift, maximum_number_of_participants="1")
    assert state_of(shift, volunteer) == S.CONFIRMED  # existing participation untouched
    volunteer_signs_up(client, qualified_volunteer, shift)
    assert state_of(shift, qualified_volunteer) is None


def test_deadline_set_by_the_planner_closes_and_reopens_signup(client, shift, planner, volunteer):
    past = localtime(shift.start_time - timedelta(days=365 * 100))
    planner_edits(
        client,
        planner,
        shift,
        signup_until_0=past.strftime("%Y-%m-%d"),
        signup_until_1=past.strftime("%H:%M"),
    )
    assert shift.signup_flow_configuration["signup_until"] is not None
    volunteer_signs_up(client, volunteer, shift)
    assert state_of(shift, volunteer) is None  # signup period is over

    planner_edits(client, planner, shift, signup_until_0="", signup_until_1="")
    assert shift.signup_flow_configuration["signup_until"] is None
    volunteer_signs_up(client, volunteer, shift)
    assert state_of(shift, volunteer) == S.CONFIRMED


def test_switching_the_flow_to_request_changes_the_outcome_of_the_next_signup(
    client, shift, planner, volunteer, qualified_volunteer
):
    planner_edits(client, planner, shift)  # instant confirmation
    volunteer_signs_up(client, volunteer, shift)
    assert state_of(shift, volunteer) == S.CONFIRMED

    planner_edits(client, planner, shift, signup_flow_slug="request_confirm")
    volunteer_signs_up(client, qualified_volunteer, shift)
    assert state_of(shift, qualified_volunteer) == S.REQUESTED


def test_minimum_age_set_by_the_planner_blocks_a_younger_volunteer(
    client, shift, planner, volunteer
):
    planner_edits(
        client, planner, shift, minimum_age="120"
    )  # volunteer is about 109 at the shift date
    volunteer_signs_up(client, volunteer, shift)
    assert state_of(shift, volunteer) is None
    planner_edits(client, planner, shift, minimum_age="18")
    volunteer_signs_up(client, volunteer, shift)
    assert state_of(shift, volunteer) == S.CONFIRMED


def test_volunteer_cannot_change_the_shared_record_through_wf1(client, shift, volunteer):
    client.force_login(volunteer)
    before = dict(shift.structure_configuration)
    response = client.post(
        reverse("core:shift_edit", kwargs={"pk": shift.pk}),
        {**SHIFT_FORM, "maximum_number_of_participants": "99"},
    )
    assert response.status_code == 403
    shift.refresh_from_db()
    assert shift.structure_configuration == before
