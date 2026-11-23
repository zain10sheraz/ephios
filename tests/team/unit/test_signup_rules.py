"""
Team unit tests for the signup business rules (WF2: participant signup).

BR1  Signup window boundary: signup is closed once now > min(shift.end_time, signup_until).
BR2  Decline decision: a CONFIRMED participant may decline only if user_can_decline_confirmed
     AND the signup window is still open (two Boolean conditions).
BR3  State change: REJECTED may do nothing; DECLINED may not decline again but may sign up;
     REQUESTED/CONFIRMED may not sign up again.
BR4  Capacity limit: with an instant-confirmation flow, signup is blocked once confirmed
     participants >= maximum_number_of_participants.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest

from ephios.core.models import AbstractParticipation, LocalParticipation

S = AbstractParticipation.States
VALIDATOR_MODULE = "ephios.core.signup.flow.participant_validation"


class FrozenClock:
    """Replacement for the `timezone` name inside participant_validation."""

    def __init__(self, now):
        self._now = now

    def now(self):
        return self._now


@pytest.fixture
def shift(event):
    return event.shifts.get()


def configure(shift, flow=None, flow_conf=None, structure_conf=None):
    if flow:
        shift.signup_flow_slug = flow
    if flow_conf is not None:
        shift.signup_flow_configuration = flow_conf
    if structure_conf is not None:
        shift.structure_configuration = structure_conf
    shift.save()
    shift.refresh_from_db()
    return shift


def validator(shift, user):
    return shift.signup_flow.get_validator(user.as_participant())


def put_in_state(shift, user, state):
    return LocalParticipation.objects.create(shift=shift, user=user, state=state)


# ------------------------------------------------------------ BR1: boundary (3-point BVA)
@pytest.mark.parametrize(
    "offset_s, expect_closed",
    [(-1, False), (0, False), (1, True)],  # just below, exactly at, just above the limit
    ids=["just_before", "exactly_at", "just_after"],
)
def test_br1_signup_until_boundary(shift, volunteer, offset_s, expect_closed):
    limit = shift.start_time
    configure(shift, flow_conf=dict(signup_until=limit))
    clock = FrozenClock(limit + timedelta(seconds=offset_s))
    with patch(f"{VALIDATOR_MODULE}.timezone", clock):
        errors = validator(shift, volunteer).get_signup_errors()
    assert any("signup period is over" in str(e) for e in errors) is expect_closed


@pytest.mark.parametrize(
    "offset_s, expect_closed",
    [(-1, False), (0, False), (1, True)],
    ids=["just_before", "exactly_at", "just_after"],
)
def test_br1_end_time_is_limit_without_signup_until(shift, volunteer, offset_s, expect_closed):
    configure(shift, flow_conf=dict(signup_until=None))
    clock = FrozenClock(shift.end_time + timedelta(seconds=offset_s))
    with patch(f"{VALIDATOR_MODULE}.timezone", clock):
        errors = validator(shift, volunteer).get_signup_errors()
    assert any("signup period is over" in str(e) for e in errors) is expect_closed


def test_br1_signup_until_after_end_time_is_capped_by_end_time(shift, volunteer):
    configure(shift, flow_conf=dict(signup_until=shift.end_time + timedelta(days=5)))
    clock = FrozenClock(shift.end_time + timedelta(seconds=1))
    with patch(f"{VALIDATOR_MODULE}.timezone", clock):
        assert not validator(shift, volunteer).can_sign_up()


# ------------------------------------------------------------ BR2: decision table
@pytest.mark.parametrize(
    "can_decline_flag, window_open, expect_can_decline",
    [
        (True, True, True),  # R1
        (True, False, False),  # R2
        (False, True, False),  # R3
        (False, False, False),  # R4
    ],
    ids=["R1_T_T", "R2_T_F", "R3_F_T", "R4_F_F"],
)
def test_br2_confirmed_decline_decision_table(
    shift, volunteer, can_decline_flag, window_open, expect_can_decline
):
    configure(shift, flow_conf=dict(user_can_decline_confirmed=can_decline_flag, signup_until=None))
    put_in_state(shift, volunteer, S.CONFIRMED)
    now = shift.start_time if window_open else shift.end_time + timedelta(minutes=1)
    with patch(f"{VALIDATOR_MODULE}.timezone", FrozenClock(now)):
        assert validator(shift, volunteer).can_decline() is expect_can_decline


# ------------------------------------------------------------ BR3: state transitions
def test_br3_no_participation_can_sign_up_and_decline(shift, volunteer):
    v = validator(shift, volunteer)
    assert v.can_sign_up() and v.can_decline()


def test_br3_requested_cannot_sign_up_again_but_may_decline(shift, volunteer):
    put_in_state(shift, volunteer, S.REQUESTED)
    v = validator(shift, volunteer)
    assert not v.can_sign_up()
    assert v.can_decline()


def test_br3_confirmed_cannot_sign_up_again(shift, volunteer):
    put_in_state(shift, volunteer, S.CONFIRMED)
    assert not validator(shift, volunteer).can_sign_up()


def test_br3_user_declined_cannot_decline_again_but_can_sign_up(shift, volunteer):
    put_in_state(shift, volunteer, S.USER_DECLINED)
    v = validator(shift, volunteer)
    assert not v.can_decline()
    assert v.can_sign_up()
    assert any("already declined" in str(e) for e in v.get_decline_errors())


def test_br3_rejected_is_blocked_for_every_action(shift, volunteer):
    put_in_state(shift, volunteer, S.RESPONSIBLE_REJECTED)
    v = validator(shift, volunteer)
    assert not v.can_sign_up()
    assert not v.can_decline()
    assert any("rejected" in str(e) for e in v.get_action_errors())


def test_br3_getting_dispatched_is_neutral(shift, volunteer):
    put_in_state(shift, volunteer, S.GETTING_DISPATCHED)
    assert validator(shift, volunteer).can_sign_up()


# ------------------------------------------------------------ BR4: capacity (3-point BVA)
@pytest.mark.parametrize(
    "confirmed, expect_full",
    [(1, False), (2, True), (3, True)],  # maximum=2: below, at, above
    ids=["max_minus_1", "at_max", "max_plus_1"],
)
def test_br4_maximum_participants_instant_flow(
    shift, volunteer, planner, manager, superuser, confirmed, expect_full
):
    configure(
        shift,
        flow="instant_confirmation",
        flow_conf=dict(signup_until=None),
        structure_conf=dict(minimum_number_of_participants=0, maximum_number_of_participants=2),
    )
    for other in [planner, manager, superuser][:confirmed]:
        put_in_state(shift, other, S.CONFIRMED)
    errors = validator(shift, volunteer).get_signup_errors()
    assert any("maximum number of participants" in str(e) for e in errors) is expect_full


def test_br4_capacity_ignored_for_request_flow(shift, volunteer, planner):
    configure(
        shift,
        flow="request_confirm",
        structure_conf=dict(minimum_number_of_participants=0, maximum_number_of_participants=1),
    )
    put_in_state(shift, planner, S.CONFIRMED)
    assert validator(shift, volunteer).can_sign_up()


def test_br4_no_maximum_means_unlimited(shift, volunteer, planner):
    configure(
        shift,
        flow="instant_confirmation",
        structure_conf=dict(minimum_number_of_participants=0, maximum_number_of_participants=None),
    )
    put_in_state(shift, planner, S.CONFIRMED)
    assert validator(shift, volunteer).can_sign_up()


# ------------------------------------------------------------ other checkers
@pytest.mark.xfail(strict=True, reason="DEFECT-001: check_event_is_active returns instead of raises")
def test_event_inactive_blocks_signup(shift, volunteer):
    """Expectation from the checker's own error text: 'The event is not active.'"""
    shift.event.active = False
    shift.event.save()
    shift.refresh_from_db()
    assert not validator(shift, volunteer).can_sign_up()
