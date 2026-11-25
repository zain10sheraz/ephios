"""
Complete MCC / MC-DC for every compound decision of the critical module
`src/ephios/core/signup/flow/participant_validation.py` (tables: docs/team/MCC_MCDC.md).

D3  check_participation_state   A and B     A = state == CONFIRMED, B = not user_can_decline_confirmed
D4  can_sign_up (signupable)    A or  B     A = participation is None, B = not participation.is_in_positive_state()
D5  can_sign_up (result)        C and D     C = signupable_state, D = not get_signup_errors()
D6  can_customize (positive)    A and B     A = participation is not None, B = participation.is_in_positive_state()
D7  can_customize (result)      X and Y     X = can_decline(), Y = not get_signup_errors()
D8  L101/L102 `x or shift.x`    value-level default, covered by test_mutation_killers.py

D1/D2 (age, capacity) are in test_mcc_mcdc.py. Python short-circuits and/or: a condition that is not
evaluated is '-' in the row. Rows that differ only in an unevaluated condition are the same input.
"""

from types import SimpleNamespace

import pytest

from ephios.core.models import AbstractParticipation
from ephios.core.signup.flow.participant_validation import (
    ActionDisallowedError,
    BaseSignupActionValidator,
    BaseSignupError,
    DeclineDisallowedError,
    ImproperlyConfiguredError,
    ParticipantUnfitError,
    SignupDisallowedError,
    check_participation_state,
)

S = AbstractParticipation.States


class StubParticipation:
    def __init__(self, positive):
        self._positive = positive

    def is_in_positive_state(self):
        return self._positive


def stub_validator(participation=None, signup_errors=(), can_decline=True):
    """A validator whose collaborators are fixed, so only the decision under test varies."""
    validator = BaseSignupActionValidator.__new__(BaseSignupActionValidator)
    validator.participation = participation
    validator.get_signup_errors = lambda: list(signup_errors)
    validator.can_decline = lambda: can_decline
    return validator


def outcomes(rows, run):
    return {row_id: run(*args) for row_id, args, _expected in rows}


def assert_rows(rows, run):
    for row_id, args, expected in rows:
        assert run(*args) == expected, row_id


def assert_mcdc_pairs(pairs, rows, run):
    """Each pair differs in exactly one condition and must flip the outcome."""
    result = outcomes(rows, run)
    for condition, (first, second) in pairs.items():
        assert result[first] != result[second], f"condition {condition}: {first} vs {second}"


# ------------------------------------------------------------------ D3
def d3_run(state, flag):
    shift = SimpleNamespace(
        signup_flow=SimpleNamespace(configuration=SimpleNamespace(user_can_decline_confirmed=flag))
    )
    participation = SimpleNamespace(state=state)
    participant = SimpleNamespace(participation_for=lambda _shift: participation)
    try:
        check_participation_state(shift, participant)
    except DeclineDisallowedError:
        return "raise"
    return "ok"


# (id, (state, user_can_decline_confirmed), expected)  A = state is CONFIRMED, B = flag is False
D3_ROWS = [
    ("D3-TT", (S.CONFIRMED, False), "raise"),
    ("D3-TF", (S.CONFIRMED, True), "ok"),
    ("D3-FT", (S.REQUESTED, False), "ok"),
    ("D3-FF", (S.REQUESTED, True), "ok"),
]
D3_PAIRS = {"A": ("D3-FT", "D3-TT"), "B": ("D3-TF", "D3-TT")}


def test_d3_mcc_all_four_rows():
    assert_rows(D3_ROWS, d3_run)


def test_d3_mcdc_pairs():
    assert_mcdc_pairs(D3_PAIRS, D3_ROWS, d3_run)


# ------------------------------------------------------------------ D4
def d4_run(participation):
    return stub_validator(participation).can_sign_up()


# A = participation is None, B = not positive.   (T,-) cannot vary B: participation is None.
D4_ROWS = [
    ("D4-T-", (None,), True),
    ("D4-FF", (StubParticipation(positive=True),), False),
    ("D4-FT", (StubParticipation(positive=False),), True),
]
D4_PAIRS = {"A": ("D4-FF", "D4-T-"), "B": ("D4-FF", "D4-FT")}


def test_d4_mcc_feasible_rows():
    assert_rows(D4_ROWS, d4_run)


def test_d4_mcdc_pairs():
    assert_mcdc_pairs(D4_PAIRS, D4_ROWS, d4_run)


# ------------------------------------------------------------------ D5
def d5_run(participation, errors):
    return stub_validator(participation, signup_errors=errors).can_sign_up()


# C = signupable_state, D = no signup errors.   (F,-): D is not evaluated.
D5_ROWS = [
    ("D5-TT", (None, []), True),
    ("D5-TF", (None, [SignupDisallowedError("x")]), False),
    ("D5-F-", (StubParticipation(positive=True), []), False),
]
D5_PAIRS = {"C": ("D5-F-", "D5-TT"), "D": ("D5-TF", "D5-TT")}


def test_d5_mcc_feasible_rows():
    assert_rows(D5_ROWS, d5_run)


def test_d5_mcdc_pairs():
    assert_mcdc_pairs(D5_PAIRS, D5_ROWS, d5_run)


def test_d5_errors_do_not_matter_when_state_is_not_signupable():
    row_with_errors = d5_run(StubParticipation(positive=True), [SignupDisallowedError("x")])
    row_without_errors = d5_run(StubParticipation(positive=True), [])
    assert row_with_errors is False
    assert row_without_errors is False


# ------------------------------------------------------------------ D6
def d6_run(participation):
    # can_decline is False and there are no signup errors, so the result exposes which branch ran:
    # positive branch -> can_decline() and ... = False; other branch -> not errors = True
    return stub_validator(participation, can_decline=False).can_customize_signup()


# A = participation is not None, B = positive.   (F,-): None cannot vary B.
D6_ROWS = [
    ("D6-F-", (None,), True),
    ("D6-TF", (StubParticipation(positive=False),), True),
    ("D6-TT", (StubParticipation(positive=True),), False),
]
D6_PAIRS = {"A": ("D6-F-", "D6-TT"), "B": ("D6-TF", "D6-TT")}


def test_d6_mcc_feasible_rows():
    assert_rows(D6_ROWS, d6_run)


def test_d6_mcdc_pairs():
    assert_mcdc_pairs(D6_PAIRS, D6_ROWS, d6_run)


# ------------------------------------------------------------------ D7
def d7_run(can_decline, errors):
    positive = StubParticipation(positive=True)
    return stub_validator(
        positive, signup_errors=errors, can_decline=can_decline
    ).can_customize_signup()


# X = can_decline(), Y = no signup errors.   (F,-): Y is not evaluated.
D7_ROWS = [
    ("D7-TT", (True, []), True),
    ("D7-TF", (True, [SignupDisallowedError("x")]), False),
    ("D7-F-", (False, []), False),
]
D7_PAIRS = {"X": ("D7-F-", "D7-TT"), "Y": ("D7-TF", "D7-TT")}


def test_d7_mcc_feasible_rows():
    assert_rows(D7_ROWS, d7_run)


def test_d7_mcdc_pairs():
    assert_mcdc_pairs(D7_PAIRS, D7_ROWS, d7_run)


# ------------------------------------------------------------------ error-class routing
# Decision table: which error class shows up in which query (signup / decline / action).
ROUTING = [
    # error class,               in signup errors, in decline errors, in action errors
    (SignupDisallowedError, True, False, True),
    (ParticipantUnfitError, True, False, True),
    (DeclineDisallowedError, False, True, True),
    (ActionDisallowedError, True, True, True),
    (ImproperlyConfiguredError, True, True, True),
    (BaseSignupError, False, False, True),
]


@pytest.mark.parametrize(
    "error_class, in_signup, in_decline, in_action",
    ROUTING,
    ids=[row[0].__name__ for row in ROUTING],
)
def test_error_class_routing_decision_table(error_class, in_signup, in_decline, in_action):
    def checker(_shift, _participant):
        raise error_class("boom")

    class Probe(BaseSignupActionValidator):
        def get_checkers(self):
            return [checker]

    probe = Probe.__new__(Probe)
    probe.shift = None
    probe.participant = None
    probe.participation = None
    assert bool(probe.get_signup_errors()) is in_signup
    assert bool(probe.get_decline_errors()) is in_decline
    assert bool(probe.get_action_errors()) is in_action
