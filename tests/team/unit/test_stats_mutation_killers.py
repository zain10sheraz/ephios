"""
Tests targeting the 40 surviving mutants of core/signup/stats.py (mutation round 1).
Root cause of the survivors: existing tests used zeros / small numbers where bitwise operators
coincide with addition (e.g. 1+2 == 1|2 == 1^2) and never combined None on one side only.
Operands 3 and 5 are used because 3+5=8 differs from 3|5=7, 3^5=6, 3&5=1, 3*5=15, 3//5=0, 3>>5=0, 3<<5=96.
Analysis: docs/team/MUTATION.md.
"""

import dataclasses

import pytest

from ephios.core.signup.stats import SignupStats


def make(**overrides):
    base = dict(requested_count=3, confirmed_count=3, missing=3, free=3, min_count=3, max_count=3)
    base.update(overrides)
    return SignupStats(**base)


# ---- L6: dataclass is frozen (immutable value object)
def test_signup_stats_is_frozen_and_hashable():
    stats = make()
    with pytest.raises(dataclasses.FrozenInstanceError):
        stats.free = 99
    assert hash(stats) == hash(make())


# ---- L67: has_free boundary (3-point BVA around 0, plus negative)
@pytest.mark.parametrize("free, expected", [(None, True), (-1, False), (0, False), (1, True)])
def test_has_free_boundary(free, expected):
    assert make(free=free).has_free() is expected


# ---- L78: full_count = confirmed + free
def test_full_count_adds_confirmed_and_free():
    assert make(confirmed_count=3, free=5).full_count == 8


# ---- additive fields with overlapping bits (L90, L102, L103)
@pytest.mark.parametrize("field", ["requested_count", "confirmed_count", "missing"])
def test_counts_are_added(field):
    total = make(**{field: 3}) + make(**{field: 5})
    assert getattr(total, field) == 8


# ---- decision table for the optional fields free / max_count (L89, L97, L98) and min_count (L92)
@pytest.mark.parametrize(
    "left, right, expected",
    [(3, 5, 8), (3, None, None), (None, 5, None), (None, None, None)],
    ids=["both_set", "right_none", "left_none", "both_none"],
)
@pytest.mark.parametrize("field", ["free", "max_count"])
def test_unbounded_when_either_side_unbounded(field, left, right, expected):
    total = make(**{field: left}) + make(**{field: right})
    assert getattr(total, field) == expected


@pytest.mark.parametrize(
    "left, right, expected",
    [(3, 5, 8), (3, None, 3), (None, 5, 5), (None, None, None), (0, 5, 5)],
    ids=["both_set", "right_none", "left_none", "both_none", "left_zero"],
)
def test_min_count_treats_none_as_zero_unless_both_none(left, right, expected):
    total = make(min_count=left) + make(min_count=right)
    assert total.min_count == expected
