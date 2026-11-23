"""
Tests written to kill surviving mutants in structure/common.py (mutation round 1).
Analysis: docs/team/MUTATION.md. Line numbers refer to the baseline file.
"""

import pytest
from django.test import RequestFactory

from ephios.core.models import AbstractParticipation, LocalParticipation

S = AbstractParticipation.States


@pytest.fixture
def shift(event):
    return event.shifts.get()


def structure_conf(shift, flow=None, **conf):
    if flow:
        shift.signup_flow_slug = flow
    shift.structure_configuration = conf
    shift.save()
    shift.refresh_from_db()
    return shift


def form_errors(shift, **data):
    form = shift.structure.get_configuration_form(request=RequestFactory().get("/"), data=data)
    form.is_valid()
    return form.errors


def context_for(shift, user):
    request = RequestFactory().get("/")
    request.user = user
    return shift.structure.get_shift_state_context_data(request)


# ---- L54: capacity must count ONLY confirmed participations
def test_capacity_counts_only_confirmed(shift, volunteer, planner, manager, superuser):
    structure_conf(
        shift, flow="instant_confirmation",
        minimum_number_of_participants=0, maximum_number_of_participants=2,
    )
    LocalParticipation.objects.create(shift=shift, user=planner, state=S.CONFIRMED)
    LocalParticipation.objects.create(shift=shift, user=manager, state=S.USER_DECLINED)
    LocalParticipation.objects.create(shift=shift, user=superuser, state=S.RESPONSIBLE_REJECTED)
    errors = shift.signup_flow.signup_action_validator_class(
        shift, volunteer.as_participant()
    ).get_signup_errors()
    assert "maximum number of participants" not in " ".join(str(e) for e in errors)


# ---- L71 / L74: form limits, 3-point BVA
@pytest.mark.parametrize("value, valid", [("-1", False), ("0", True), ("1", True)])
def test_minimum_participants_form_boundary(shift, value, valid):
    assert ("minimum_number_of_participants" not in form_errors(
        shift, minimum_number_of_participants=value)) is valid


@pytest.mark.parametrize("value, valid", [("0", False), ("1", True), ("2", True)])
def test_maximum_participants_form_boundary(shift, value, valid):
    assert ("maximum_number_of_participants" not in form_errors(
        shift, maximum_number_of_participants=value)) is valid


# ---- L83 / L84 / L85: empty-spot computation in the shift state context
@pytest.mark.parametrize(
    "minimum, confirmed, expected_empty",
    [(None, 0, 0), (0, 0, 0), (0, 1, 0), (3, 1, 2), (3, 3, 0), (2, 0, 2)],
    ids=["min_none", "min0_none", "min0_one", "min3_one", "min3_full", "min2_none"],
)
def test_empty_spots(shift, planner, volunteer, manager, superuser, minimum, confirmed, expected_empty):
    structure_conf(shift, minimum_number_of_participants=minimum, maximum_number_of_participants=None)
    for user in [volunteer, manager, superuser][:confirmed]:
        LocalParticipation.objects.create(shift=shift, user=user, state=S.CONFIRMED)
    assert len(context_for(shift, planner)["empty_spots"]) == expected_empty


# ---- L176 / L184: export padding
@pytest.mark.parametrize(
    "minimum, maximum, confirmed, expected_rows",
    [
        (None, None, 0, 0),  # nothing configured -> no placeholder rows
        (None, 3, 0, 3),
        (3, None, 0, 3),
        (0, 4, 1, 4),  # 4 - 1 = 3 padding rows (XOR would give 5)
        (0, 1, 1, 1),
    ],
)
def test_export_rows(shift, volunteer, minimum, maximum, confirmed, expected_rows):
    structure_conf(
        shift, minimum_number_of_participants=minimum, maximum_number_of_participants=maximum
    )
    if confirmed:
        LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    assert len(shift.structure.get_list_export_data()) == expected_rows
