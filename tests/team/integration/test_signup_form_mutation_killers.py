"""
Tests written to kill surviving mutants of core/signup/forms.py (mutation round 1, signup form).
Equivalent (not killable): the unused `commit` default of `save()`, and `name is not "signup_choice"`
(CPython interns both strings, so `is not` behaves like `!=`). Analysis: docs/team/MUTATION.md.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django import forms

from ephios.core.models import AbstractParticipation, LocalParticipation
from ephios.core.models.events import ParticipationComment
from ephios.core.signup.forms import SignupForm
from tests.team.integration.test_signup_http import (
    NOTIFICATION,
    configure,
    confirmed_customizable,
    form_times,
    narrow_conflicting_shift,
    participations,
    quick,
    url,
)

S = AbstractParticipation.States


@pytest.fixture
def shift(event):
    return event.shifts.get()


def post_signup(client, shift, user, choice="sign_up", **extra):
    client.force_login(user)
    return client.post(
        url(shift),
        {"signup_choice": choice, **form_times(shift.start_time, shift.end_time), **extra},
    )


def direct_form(shift, user, data=None, **kwargs):
    participant = user.as_participant()
    participation = participant.participation_for(shift) or participant.new_participation(shift)
    return SignupForm(
        shift=shift, participant=participant, instance=participation, data=data, **kwargs
    )


# ---- comment length: 3-point BVA around max_length=255
@pytest.mark.parametrize(
    "length, valid",
    [(254, True), (255, True), (256, False)],
    ids=["max_minus_1", "at_max", "max_plus_1"],
)
def test_comment_length_boundary(client, shift, volunteer, length, valid):
    response = post_signup(client, shift, volunteer, comment="x" * length)
    assert (response.status_code == 302) is valid
    assert (participations(shift, volunteer).count() == 1) is valid


# ---- comment visibility
@pytest.mark.parametrize(
    "extra, expected",
    [
        ({"comment_is_public": "on"}, ParticipationComment.Visibility.PUBLIC),
        ({}, ParticipationComment.Visibility.PARTICIPANT),
    ],
    ids=["public", "participant_only"],
)
def test_comment_visibility_follows_the_checkbox(client, shift, volunteer, extra, expected):
    post_signup(client, shift, volunteer, comment="I bring a car", **extra)
    comment = participations(shift, volunteer).get().comments.get()
    assert comment.visible_for == expected


# ---- save is atomic when used directly (not through the view's own transaction)
def test_form_save_rolls_back_the_participation_when_the_comment_cannot_be_stored(shift, volunteer):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    participation = LocalParticipation.objects.create(
        shift=shift, user=volunteer, state=S.REQUESTED
    )
    start = shift.start_time + timedelta(hours=1)
    data = {
        "signup_choice": "customize",
        **form_times(start, shift.end_time),
        "comment": "will fail",
    }
    form = direct_form(shift, volunteer, data=data)
    assert form.is_valid(), form.errors
    with (
        patch(
            "ephios.core.signup.forms.ParticipationComment.objects.create",
            side_effect=RuntimeError("boom"),
        ),
        pytest.raises(RuntimeError),
    ):
        form.save()
    participation.refresh_from_db()
    assert participation.individual_start_time is None


# ---- previous comments are shown but never required
def test_a_participant_with_earlier_comments_can_submit_again(client, shift, volunteer):
    confirmed_customizable(client, shift, volunteer)
    participation = participations(shift, volunteer).get()
    ParticipationComment.objects.create(
        participation=participation,
        text="earlier",
        visible_for=ParticipationComment.Visibility.PUBLIC,
    )
    new_start = shift.start_time + timedelta(hours=1)
    response = client.post(
        url(shift), {"signup_choice": "customize", **form_times(new_start, shift.end_time)}
    )
    assert response.status_code == 302


# ---- the hidden signup_choice field is required, and not rendered as a visible field
def test_posting_without_a_signup_choice_is_invalid(client, shift, volunteer):
    client.force_login(volunteer)
    response = client.post(url(shift), form_times(shift.start_time, shift.end_time))
    assert response.status_code == 200
    assert participations(shift, volunteer).count() == 0


def test_field_layout_renders_every_field_except_signup_choice(shift, volunteer):
    form = direct_form(shift, volunteer)
    form.fields["zz_extra_plugin_field"] = forms.CharField(
        required=False
    )  # sorts after "signup_choice"
    names = [field.fields[0] for field in form._get_field_layout().fields]
    assert "zz_extra_plugin_field" in names
    assert "individual_start_time" in names
    assert "signup_choice" not in names


# ---- decline button only when declining is possible
def test_decline_button_is_shown_only_when_declining_is_possible(client, shift, volunteer):
    client.force_login(volunteer)
    assert b'value="decline"' in client.get(url(shift)).content
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.USER_DECLINED)
    assert b'value="decline"' not in client.get(url(shift)).content


# ---- customisation of times can be locked
def test_both_time_fields_are_disabled_when_customising_is_not_allowed(shift, volunteer):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=False))
    form = direct_form(shift, volunteer)
    assert form.fields["individual_start_time"].disabled is True
    assert form.fields["individual_end_time"].disabled is True


def test_times_are_locked_when_the_flow_does_not_define_the_setting(shift, volunteer):
    del shift.signup_flow.configuration.user_can_customize_signup_times
    form = direct_form(shift, volunteer)
    assert form.fields["individual_start_time"].disabled is True


def test_a_forged_end_time_is_ignored_when_times_are_locked(client, shift, volunteer):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=False))
    forged_end = shift.end_time - timedelta(hours=3)
    client.force_login(volunteer)
    client.post(
        url(shift), {"signup_choice": "sign_up", **form_times(shift.start_time, forged_end)}
    )
    assert participations(shift, volunteer).get().individual_end_time is None


# ---- notification text for changed times
def test_customising_back_to_the_default_end_time_reports_the_end_time_change(
    client, shift, volunteer
):
    confirmed_customizable(client, shift, volunteer)
    start = shift.start_time + timedelta(hours=2)
    client.post(
        url(shift),
        {"signup_choice": "customize", **form_times(start, shift.end_time - timedelta(hours=1))},
    )
    with patch(NOTIFICATION) as notification:
        client.post(url(shift), {"signup_choice": "customize", **form_times(start, shift.end_time)})
    assert notification.send.call_count == 1
    claims = notification.send.call_args.args[1]
    assert len(claims) == 1
    assert "Individual end time was changed" in claims[0]


# ---- overlap rules inside the form
def test_customising_into_an_overlap_with_another_confirmed_shift_is_rejected(
    client, shift, volunteer, conflicting_event
):
    configure(
        shift,
        flow="instant_confirmation",
        flow_conf=dict(user_can_customize_signup_times=True, user_can_decline_confirmed=True),
        structure_conf=dict(minimum_number_of_participants=0, maximum_number_of_participants=5),
    )
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    client.force_login(volunteer)
    new_start = shift.start_time + timedelta(hours=1)
    response = client.post(
        url(shift), {"signup_choice": "customize", **form_times(new_start, shift.end_time)}
    )
    assert response.status_code == 200
    assert b"already confirmed for other shifts" in response.content
    assert participations(shift, volunteer).get().individual_start_time is None


def test_partial_overlap_is_rejected_by_the_form(client, shift, volunteer, conflicting_event):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    narrow_conflicting_shift(conflicting_event)  # overlaps only the first hour of the shift
    response = post_signup(client, shift, volunteer)
    assert response.status_code == 200
    assert b"already confirmed for other shifts" in response.content
    assert participations(shift, volunteer).count() == 0


def test_chosen_start_after_the_conflict_avoids_the_overlap(
    client, shift, volunteer, conflicting_event
):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    narrow_conflicting_shift(conflicting_event)  # conflict covers only the first hour
    start = shift.start_time + timedelta(hours=2)
    client.force_login(volunteer)
    response = client.post(
        url(shift), {"signup_choice": "sign_up", **form_times(start, shift.end_time)}
    )
    assert response.status_code == 302
    assert participations(shift, volunteer).count() == 1


def test_chosen_end_before_the_conflict_avoids_the_overlap(
    client, shift, volunteer, conflicting_event
):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    other = conflicting_event.shifts.get()
    other.meeting_time = other.start_time = shift.end_time - timedelta(hours=1)
    other.end_time = shift.end_time + timedelta(hours=1)  # conflict covers only the last hour
    other.save()
    end = shift.end_time - timedelta(hours=2)
    client.force_login(volunteer)
    response = client.post(
        url(shift), {"signup_choice": "sign_up", **form_times(shift.start_time, end)}
    )
    assert response.status_code == 302
    assert participations(shift, volunteer).count() == 1


def test_quick_action_helper_is_available_for_the_killer_tests(client, shift, volunteer):
    client.force_login(volunteer)
    assert quick(client, shift, "sign_up").status_code == 302
