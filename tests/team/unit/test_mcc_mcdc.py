"""
Multiple Condition Coverage (MCC) and MC/DC tests for two 3-condition decisions in the
critical signup-validation module. Tables and pair derivation: docs/team/MCC_MCDC.md.

D1  check_participant_age (structure/common.py, MinimumAgeMixin):
        raise  <=>  A and B and C
        A = minimum_age is not None
        B = age is not None
        C = age < minimum_age

D2  check_maximum_number_of_participants (structure/common.py, MinMaxParticipantsMixin):
        raise  <=>  A and B and C
        A = not shift.signup_flow.uses_requested_state
        B = maximum_number_of_participants is not None
        C = confirmed_count >= maximum_number_of_participants
    (A and B form the `if`; C is the nested `if`; the combined effect is a 3-condition AND.)

Python short-circuits `and`, so rows whose later conditions are not evaluated are marked
'-' (don't care). Where a later condition cannot even be formed (C needs both a minimum and
an age), the full-MCC row is infeasible and the table says so.
"""

from datetime import date
from types import SimpleNamespace

import pytest

from ephios.core.models import AbstractParticipation
from ephios.core.signup.flow.participant_validation import (
    ParticipantUnfitError,
    SignupDisallowedError,
)
from ephios.plugins.baseshiftstructures.structure.uniform import UniformShiftStructure


def get_checker(event, name):
    structure = UniformShiftStructure(None, event=event)
    return next(c for c in structure.get_checkers() if c.__name__ == name)


# ----------------------------------------------------------------------------- D1
class StubParticipant:
    def __init__(self, age):
        self._age = age

    def get_age(self, day):
        assert isinstance(day, date)
        return self._age


def age_case(minimum_age, age):
    shift = SimpleNamespace(
        start_time=SimpleNamespace(date=lambda: date(2099, 6, 30)),
        structure=SimpleNamespace(configuration=SimpleNamespace(minimum_age=minimum_age)),
    )
    return shift, StubParticipant(age)


# (id, A, B, C, minimum_age, age, raises)   -- MCC rows executable under short-circuit
D1_ROWS = [
    ("D1-1 F,-,-", False, None, None, None, 30, False),
    ("D1-2 T,F,-", True, False, None, 18, None, False),
    ("D1-3 T,T,F", True, True, False, 18, 18, False),
    ("D1-4 T,T,T", True, True, True, 18, 17, True),
]


@pytest.mark.parametrize("row", D1_ROWS, ids=[r[0] for r in D1_ROWS])
def test_d1_age_mcc_rows(event, row):
    *_, minimum_age, age, raises = row
    checker = get_checker(event, "check_participant_age")
    shift, participant = age_case(minimum_age, age)
    if raises:
        with pytest.raises(ParticipantUnfitError):
            checker(shift, participant)
    else:
        assert checker(shift, participant) is None


def test_d1_infeasible_mcc_rows_are_really_not_formable(event):
    """Rows (F,T,*) with A false: C = age < None is not evaluable (TypeError in Python)."""
    age, minimum_age = 30, None
    with pytest.raises(TypeError):
        _ = age < minimum_age


# MC/DC independence pairs (masking MC/DC): rows that differ in one condition flip outcome.
D1_MCDC_PAIRS = {
    "A": ("D1-1 F,-,-", "D1-4 T,T,T"),
    "B": ("D1-2 T,F,-", "D1-4 T,T,T"),
    "C": ("D1-3 T,T,F", "D1-4 T,T,T"),
}


@pytest.mark.parametrize("cond", ["A", "B", "C"])
def test_d1_mcdc_pair_flips_outcome(event, cond):
    checker = get_checker(event, "check_participant_age")
    by_id = {r[0]: r for r in D1_ROWS}
    outcomes = []
    for rid in D1_MCDC_PAIRS[cond]:
        *_, minimum_age, age, _raises = by_id[rid]
        shift, participant = age_case(minimum_age, age)
        try:
            checker(shift, participant)
            outcomes.append(False)
        except ParticipantUnfitError:
            outcomes.append(True)
    assert outcomes == [False, True]


# ----------------------------------------------------------------------------- D2
S = AbstractParticipation.States


def capacity_case(uses_requested, maximum, confirmed):
    participations = [SimpleNamespace(state=S.CONFIRMED) for _ in range(confirmed)]
    shift = SimpleNamespace(
        signup_flow=SimpleNamespace(uses_requested_state=uses_requested),
        structure=SimpleNamespace(
            configuration=SimpleNamespace(maximum_number_of_participants=maximum)
        ),
        participations=SimpleNamespace(all=lambda: participations),
    )
    return shift


# (id, uses_requested, maximum, confirmed, raises)
D2_ROWS = [
    ("D2-1 F,-,-", True, 2, 5, False),  # A false (flow uses requested state)
    ("D2-2 T,F,-", False, None, 5, False),  # A true, B false (no maximum)
    ("D2-3 T,T,F", False, 2, 1, False),  # A,B true, C false
    ("D2-4 T,T,T", False, 2, 2, True),  # A,B,C true
]


@pytest.mark.parametrize("row", D2_ROWS, ids=[r[0] for r in D2_ROWS])
def test_d2_capacity_mcc_rows(event, row):
    _, uses_requested, maximum, confirmed, raises = row
    checker = get_checker(event, "check_maximum_number_of_participants")
    shift = capacity_case(uses_requested, maximum, confirmed)
    if raises:
        with pytest.raises(SignupDisallowedError):
            checker(shift, None)
    else:
        assert checker(shift, None) is None


D2_MCDC_PAIRS = {
    "A": ("D2-1 F,-,-", "D2-4 T,T,T"),
    "B": ("D2-2 T,F,-", "D2-4 T,T,T"),
    "C": ("D2-3 T,T,F", "D2-4 T,T,T"),
}


@pytest.mark.parametrize("cond", ["A", "B", "C"])
def test_d2_mcdc_pair_flips_outcome(event, cond):
    checker = get_checker(event, "check_maximum_number_of_participants")
    by_id = {r[0]: r for r in D2_ROWS}
    outcomes = []
    for rid in D2_MCDC_PAIRS[cond]:
        _, uses_requested, maximum, confirmed, _ = by_id[rid]
        try:
            checker(capacity_case(uses_requested, maximum, confirmed), None)
            outcomes.append(False)
        except SignupDisallowedError:
            outcomes.append(True)
    assert outcomes == [False, True]
