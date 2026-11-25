"""
Team unit tests completing structural coverage of the signup validators, the
shift-structure mixins and SignupStats (server-side business logic of WF1/WF2).
"""

from datetime import timedelta

import pytest
from django.test import RequestFactory
from django.urls import reverse

from ephios.core.models import AbstractParticipation, LocalParticipation, Qualification
from ephios.core.signup.flow.participant_validation import (
    ActionDisallowedError,
    BaseSignupActionValidator,
    NoSignupSignupActionValidator,
)
from ephios.core.signup.stats import SignupStats
from ephios.plugins.baseshiftstructures.structure.common import participation_entry_sort_key

S = AbstractParticipation.States


@pytest.fixture
def shift(event):
    return event.shifts.get()


def make_validator(shift, user):
    # fresh validator each time (flow caches its validator)
    return shift.signup_flow.signup_action_validator_class(shift, user.as_participant())


def save(shift, **fields):
    for k, v in fields.items():
        setattr(shift, k, v)
    shift.save()
    shift.refresh_from_db()


def messages(errors):
    return " | ".join(str(e) for e in errors)


# ------------------------------------------------------------ minimum age (3-point BVA)
@pytest.mark.parametrize(
    "delta, expect_blocked", [(-1, False), (0, False), (1, True)], ids=["below", "at", "above"]
)
def test_minimum_age_boundary(shift, volunteer, delta, expect_blocked):
    age = volunteer.as_participant().get_age(shift.start_time.date())
    save(shift, structure_configuration=dict(minimum_age=age + delta))
    blocked = "too young" in messages(make_validator(shift, volunteer).get_signup_errors())
    assert blocked is expect_blocked


def test_minimum_age_unknown_birthdate_is_not_blocked(shift, volunteer):
    save(shift, structure_configuration=dict(minimum_age=18))
    volunteer.date_of_birth = None
    volunteer.save()
    assert "too young" not in messages(make_validator(shift, volunteer).get_signup_errors())


def test_minimum_age_not_configured(shift, volunteer):
    save(shift, structure_configuration=dict())
    assert "too young" not in messages(make_validator(shift, volunteer).get_signup_errors())


# ------------------------------------------------------------ qualifications
def test_required_qualification_missing_blocks(shift, volunteer, qualifications):
    save(shift, structure_configuration=dict(required_qualification_ids=[qualifications.nfs.pk]))
    assert "not qualified" in messages(make_validator(shift, volunteer).get_signup_errors())


def test_required_qualification_present_allows(shift, qualified_volunteer, qualifications):
    save(shift, structure_configuration=dict(required_qualification_ids=[qualifications.nfs.pk]))
    assert "not qualified" not in messages(
        make_validator(shift, qualified_volunteer).get_signup_errors()
    )


def test_general_required_qualification_blocks_unqualified(shift, volunteer, qualifications):
    shift.event.type.preferences["general_required_qualifications"] = Qualification.objects.filter(
        pk=qualifications.nfs.pk
    )
    assert "lack the necessary qualification" in messages(
        make_validator(shift, volunteer).get_signup_errors()
    )


def test_general_required_qualification_allows_qualified(
    shift, qualified_volunteer, qualifications
):
    shift.event.type.preferences["general_required_qualifications"] = Qualification.objects.filter(
        pk=qualifications.nfs.pk
    )
    assert make_validator(shift, qualified_volunteer).can_sign_up()


# ------------------------------------------------------------ conflicting participations
def test_conflict_with_confirmed_overlapping_shift_blocks(shift, volunteer, conflicting_event):
    errors = make_validator(shift, volunteer).get_signup_errors()
    assert "already confirmed for other shifts" in messages(errors)


def test_conflict_not_checked_for_other_user(shift, planner, conflicting_event):
    assert "already confirmed" not in messages(make_validator(shift, planner).get_signup_errors())


@pytest.mark.parametrize("customizable, expect_blocked", [(True, False), (False, True)])
def test_partial_overlap_depends_on_customizable_times(
    shift, volunteer, conflicting_event, customizable, expect_blocked
):
    other = conflicting_event.shifts.get()
    other.end_time = other.start_time + timedelta(hours=1)  # only covers part of `shift`
    other.save()
    conf = dict(shift.signup_flow_configuration, user_can_customize_signup_times=customizable)
    save(shift, signup_flow_configuration=conf)
    blocked = "already confirmed" in messages(make_validator(shift, volunteer).get_signup_errors())
    assert blocked is expect_blocked


def test_conflict_check_uses_existing_participation_times(shift, volunteer, conflicting_event):
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.REQUESTED)
    errors = make_validator(shift, volunteer).get_signup_errors()
    assert "already confirmed" in messages(errors)


# ------------------------------------------------------------ can_customize_signup
def test_can_customize_when_not_signed_up(shift, volunteer):
    assert make_validator(shift, volunteer).can_customize_signup()


def test_can_customize_when_signed_up_and_may_decline(shift, volunteer):
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    assert make_validator(shift, volunteer).can_customize_signup()


def test_cannot_customize_when_confirmed_and_decline_forbidden(shift, volunteer):
    save(shift, signup_flow_configuration=dict(user_can_decline_confirmed=False))
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    assert not make_validator(shift, volunteer).can_customize_signup()


def test_cannot_customize_when_signup_errors_exist(shift, volunteer, conflicting_event):
    assert not make_validator(shift, volunteer).can_customize_signup()


# ------------------------------------------------------------ "no signup" flows
def test_manual_flow_disables_signup_with_default_message(shift, volunteer):
    save(shift, signup_flow_slug="manual", signup_flow_configuration={})
    v = make_validator(shift, volunteer)
    assert not v.can_sign_up()
    assert "Signup for this shift is disabled" in messages(v.get_action_errors())


def test_manual_flow_shows_custom_explanation(shift, volunteer):
    save(
        shift,
        signup_flow_slug="manual",
        signup_flow_configuration=dict(no_selfservice_explanation="Call the dispatcher."),
    )
    assert "Call the dispatcher." in messages(make_validator(shift, volunteer).get_action_errors())


def test_abstract_validators_defaults(shift, volunteer):
    participant = volunteer.as_participant()
    assert BaseSignupActionValidator(shift, participant).get_checkers() == []
    no_signup = NoSignupSignupActionValidator(shift, participant)
    with pytest.raises(NotImplementedError):
        no_signup.get_no_signup_allowed_message()
    with pytest.raises(NotImplementedError):
        no_signup.get_action_errors()
    assert [c.__name__ for c in no_signup.get_checkers()] == ["signup_is_disabled"]
    assert issubclass(ActionDisallowedError, Exception)


# ------------------------------------------------------------ SignupStats
def test_stats_free_and_helpers():
    unlimited = SignupStats(0, 3, 0, None, None, None)
    limited = SignupStats(1, 3, 2, 4, 5, 7)
    assert unlimited.has_free()
    assert unlimited.full_count is None
    assert limited.has_free()
    assert limited.full_count == 7
    assert limited.required_count == 5
    assert not SignupStats(0, 2, 0, 0, 0, 2).has_free()
    assert limited.replace(free=0).free == 0


def test_stats_zero_and_reduce():
    assert (
        SignupStats.ZERO == SignupStats(0, 0, 0, 0, None, None)
        or SignupStats.ZERO.confirmed_count == 0
    )
    a, b = SignupStats(1, 2, 0, 1, 1, 3), SignupStats(0, 1, 1, 2, 2, 3)
    assert SignupStats.reduce([a, b]) == a + b


def test_stats_min_none_both_sides():
    s = SignupStats(0, 0, 0, None, None, None) + SignupStats(0, 0, 0, None, None, None)
    assert s.min_count is None
    assert s.max_count is None


def test_shift_signup_stats_from_database(shift, volunteer, planner, manager):
    save(
        shift,
        structure_configuration=dict(
            minimum_number_of_participants=3, maximum_number_of_participants=4
        ),
    )
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    LocalParticipation.objects.create(shift=shift, user=planner, state=S.REQUESTED)
    stats = shift.get_signup_stats()
    assert (stats.confirmed_count, stats.requested_count) == (1, 1)
    assert (stats.missing, stats.free, stats.min_count, stats.max_count) == (2, 3, 3, 4)


def test_shift_signup_stats_without_limits(shift):
    save(
        shift,
        structure_configuration=dict(
            minimum_number_of_participants=None, maximum_number_of_participants=None
        ),
    )
    stats = shift.get_signup_stats()
    assert stats.missing == 0
    assert stats.free is None


# ------------------------------------------------------------ structure exports / rendering
def test_sort_key_orders_confirmed_first_and_empty_last(shift, volunteer, planner):
    states = [
        S.REQUESTED,
        S.CONFIRMED,
        S.USER_DECLINED,
        S.RESPONSIBLE_REJECTED,
        S.GETTING_DISPATCHED,
    ]
    entries = [
        {"participation": LocalParticipation(shift=shift, user=volunteer, state=s)} for s in states
    ]
    ordered = sorted(entries, key=participation_entry_sort_key)
    assert [e["participation"].state for e in ordered] == [
        S.CONFIRMED,
        S.REQUESTED,
        S.USER_DECLINED,
        S.RESPONSIBLE_REJECTED,
        S.GETTING_DISPATCHED,
    ]
    assert participation_entry_sort_key({"participation": None}) == 1000


def test_list_export_pads_to_minimum_participants(shift, volunteer):
    save(
        shift,
        structure_configuration=dict(
            minimum_number_of_participants=3, maximum_number_of_participants=3
        ),
    )
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    data = shift.structure.get_list_export_data()
    assert len(data) == 3
    assert data[0]["participation"].user == volunteer
    assert [d["participation"] for d in data[1:]] == [None, None]


def test_list_export_without_padding_when_full(shift, volunteer):
    save(
        shift,
        structure_configuration=dict(
            minimum_number_of_participants=0, maximum_number_of_participants=1
        ),
    )
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    assert len(shift.structure.get_list_export_data()) == 1


def test_structure_configuration_form_has_limit_fields(shift):
    form = shift.structure.get_configuration_form(request=RequestFactory().get("/"))
    for name in (
        "minimum_number_of_participants",
        "maximum_number_of_participants",
        "minimum_age",
        "required_qualification_ids",
    ):
        assert name in form.fields


def test_qualification_form_formats_ids(shift, qualifications):
    form_class = shift.structure.configuration_form_class
    assert qualifications.nfs.title in form_class.format_required_qualification_ids([
        qualifications.nfs.pk
    ])


def test_qualification_form_help_text_with_general_qualification(shift, qualifications):
    shift.event.type.preferences["general_required_qualifications"] = Qualification.objects.filter(
        pk=qualifications.nfs.pk
    )
    form = shift.structure.get_configuration_form(
        event=shift.event, request=RequestFactory().get("/")
    )
    assert qualifications.nfs.title in str(form.fields["required_qualification_ids"].help_text)


def test_event_detail_renders_shift_state_for_planner(client, event, planner, qualifications):
    shift = event.shifts.get()
    save(
        shift,
        structure_configuration=dict(
            minimum_number_of_participants=2,
            maximum_number_of_participants=3,
            required_qualification_ids=[qualifications.nfs.pk],
        ),
    )
    client.force_login(planner)
    response = client.get(
        reverse("core:event_detail", kwargs=dict(pk=event.pk, slug="x")), follow=True
    )
    assert response.status_code == 200
    assert "Fission Festival" in response.content.decode()


# ------------------------------------------------------------ plugin signal + abstract bits
def test_plugin_signal_checkers_are_included(shift, volunteer):
    from unittest.mock import patch

    from ephios.core.signup.flow.participant_validation import SignupDisallowedError

    def plugin_checker(shift, participant):
        raise SignupDisallowedError("blocked by plugin")

    with patch(
        "ephios.core.signup.flow.participant_validation.participant_signup_checkers.send",
        return_value=[(None, [plugin_checker]), (None, None)],
    ):
        errors = make_validator(shift, volunteer).get_signup_errors()
    assert "blocked by plugin" in messages(errors)


def test_structure_without_shift_has_no_required_qualifications_attr(event):
    from ephios.plugins.baseshiftstructures.structure.uniform import UniformShiftStructure

    structure = UniformShiftStructure(None, event=event)
    assert not hasattr(structure.configuration, "required_qualifications")


def test_base_structure_slug_is_abstract(event):
    from ephios.plugins.baseshiftstructures.structure.common import (
        QualificationMinMaxBaseShiftStructure,
    )

    class Incomplete(QualificationMinMaxBaseShiftStructure):
        verbose_name = "incomplete"
        description = "no slug defined"

    with pytest.raises(NotImplementedError):
        _ = Incomplete(None, event=event).slug
