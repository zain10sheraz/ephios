"""
Tests written to kill surviving mutants of mutation round 1 (participant_validation.py).
Analysis table: docs/team/MUTATION.md. Mutant ids refer to line numbers of the baseline file.
"""

from datetime import timedelta

import pytest

from ephios.core.models import AbstractParticipation, LocalParticipation
from ephios.core.signup.flow.participant_validation import (
    check_conflicting_participations,
    get_conflicting_participations,
)

S = AbstractParticipation.States


@pytest.fixture
def shift(event):
    return event.shifts.get()


def validator(shift, user):
    return shift.signup_flow.signup_action_validator_class(shift, user.as_participant())


def configure(shift, **conf):
    shift.signup_flow_configuration = conf
    shift.save()
    shift.refresh_from_db()


def messages(errors):
    return " | ".join(str(e) for e in errors)


# ---- L55: `participation.state == CONFIRMED` mutated to >=, is not, <= (missing test)
@pytest.mark.parametrize("state", [S.REQUESTED, S.GETTING_DISPATCHED])
def test_only_confirmed_is_locked_when_decline_forbidden(shift, volunteer, state):
    configure(shift, user_can_decline_confirmed=False)
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=state)
    assert validator(shift, volunteer).can_decline()


def test_declined_state_reports_its_own_message_when_decline_forbidden(shift, volunteer):
    configure(shift, user_can_decline_confirmed=False)
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.USER_DECLINED)
    text = messages(validator(shift, volunteer).get_decline_errors())
    assert "already declined" in text
    assert "by yourself" not in text


def test_rejected_blocks_signup_even_when_decline_forbidden(shift, volunteer):
    configure(shift, user_can_decline_confirmed=False)
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.RESPONSIBLE_REJECTED)
    v = validator(shift, volunteer)
    assert not v.can_sign_up()
    assert "rejected" in messages(v.get_signup_errors())


# ---- L61: `state == USER_DECLINED` mutated to >= (weak assertion in old dispatched test)
def test_getting_dispatched_may_still_decline(shift, volunteer):
    configure(shift, user_can_decline_confirmed=True)
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.GETTING_DISPATCHED)
    v = validator(shift, volunteer)
    assert v.can_decline()
    assert not v.get_decline_errors()


# ---- L85 / L101 / L102 / L119: conflict query defaults (missing tests: only called with all args)
@pytest.fixture
def partially_conflicting(shift, volunteer, conflicting_event):
    other = conflicting_event.shifts.get()
    other.end_time = other.start_time + timedelta(hours=1)  # covers only the start of `shift`
    other.save()
    return other


def test_default_total_false_reports_partial_conflict(shift, volunteer, partially_conflicting):
    conflicts = get_conflicting_participations(volunteer.as_participant(), shift)
    assert [c.shift for c in conflicts] == [partially_conflicting]


def test_total_true_ignores_partial_conflict(shift, volunteer, partially_conflicting):
    assert not get_conflicting_participations(volunteer.as_participant(), shift, total=True)


def test_explicit_start_time_is_used_not_shift_start(shift, volunteer, conflicting_event):
    later = shift.end_time + timedelta(hours=1)
    assert not get_conflicting_participations(
        volunteer.as_participant(), shift, start_time=later, end_time=later + timedelta(hours=1)
    )


def test_explicit_end_time_is_used_not_shift_end(shift, volunteer, conflicting_event):
    before = shift.start_time - timedelta(hours=1)
    assert not get_conflicting_participations(volunteer.as_participant(), shift, end_time=before)


def test_explicit_start_only_is_used_not_shift_start(shift, volunteer, conflicting_event):
    later = shift.end_time + timedelta(hours=1)
    assert not get_conflicting_participations(volunteer.as_participant(), shift, start_time=later)


def test_missing_customize_flag_defaults_to_strict_conflicts(
    shift, volunteer, partially_conflicting
):
    """Defensive default False: without the flag any overlap blocks signup."""
    flow = shift.signup_flow
    del flow.configuration.user_can_customize_signup_times
    from ephios.core.signup.flow.participant_validation import SignupDisallowedError

    participant = volunteer.as_participant()
    with pytest.raises(SignupDisallowedError):
        check_conflicting_participations(shift, participant)
