"""
Tests written to kill surviving mutants of core/models/events.py (mutation round 1).
The test database is built from migrations, so model-field changes only show up in validation
(`full_clean` / `clean_fields`) and in Python defaults: these tests assert exactly those.
Equivalent (not killable): `|` -> `^` between two mutually exclusive terms of Participation.viewable_by
(a type cannot be INSTANCE_USERS and PUBLIC, or PUBLIC and CONFIRMED, at once).
"""

import pytest
from django.core.exceptions import ValidationError
from guardian.models import UserObjectPermission

from ephios.core.models import (
    AbstractParticipation,
    Event,
    EventType,
    LocalParticipation,
    UserProfile,
)
from ephios.core.models.events import (
    EventTypePreference,
    ParticipationComment,
    PlaceholderParticipation,
    ShiftLogConfig,
)
from ephios.core.signup.participants import AbstractParticipant
from ephios.modellogging.log import LOGGED_MODELS

S = AbstractParticipation.States


@pytest.fixture
def shift(event):
    return event.shifts.get()


def field_errors(instance, *fields):
    """Validate only the given fields and return the names of the fields that failed."""
    exclude = [f.name for f in instance._meta.fields if f.name not in fields]
    try:
        instance.clean_fields(exclude=exclude)
    except ValidationError as error:
        return set(error.message_dict)
    return set()


# ------------------------------------------------------------ length limits (3-point BVA)
@pytest.mark.parametrize(
    "length, valid",
    [(253, True), (254, True), (255, False)],
    ids=["max_minus_1", "at_max", "max_plus_1"],
)
def test_event_title_and_location_length_limits(service_event_type, length, valid):
    event = Event(title="t" * length, location="l" * length, type=service_event_type)
    assert (field_errors(event, "title") == set()) is valid
    assert (field_errors(event, "location") == set()) is valid


@pytest.mark.parametrize(
    "length, valid",
    [(253, True), (254, True), (255, False)],
    ids=["max_minus_1", "at_max", "max_plus_1"],
)
def test_event_type_title_length_limit(length, valid):
    assert (field_errors(EventType(title="t" * length), "title") == set()) is valid


@pytest.mark.parametrize(
    "length, valid", [(6, True), (7, True), (8, False)], ids=["max_minus_1", "at_max", "max_plus_1"]
)
def test_event_type_color_length_limit(length, valid):
    assert (
        field_errors(EventType(title="t", color="#" + "a" * (length - 1)), "color") == set()
    ) is valid


@pytest.mark.parametrize(
    "length, valid",
    [(254, True), (255, True), (256, False)],
    ids=["max_minus_1", "at_max", "max_plus_1"],
)
def test_comment_text_and_shift_label_length_limits(shift, volunteer, length, valid):
    participation = LocalParticipation.objects.create(
        shift=shift, user=volunteer, state=S.CONFIRMED
    )
    comment = ParticipationComment(participation=participation, text="c" * length, visible_for=1)
    assert (field_errors(comment, "text") == set()) is valid
    shift.label = "s" * length
    assert (field_errors(shift, "label") == set()) is valid


@pytest.mark.parametrize(
    "length, valid",
    [(253, True), (254, True), (255, False)],
    ids=["max_minus_1", "at_max", "max_plus_1"],
)
def test_placeholder_display_name_length_limit(shift, length, valid):
    placeholder = PlaceholderParticipation(shift=shift, display_name="p" * length)
    assert (field_errors(placeholder, "display_name") == set()) is valid


# ------------------------------------------------------------ optional fields and defaults
def test_event_description_may_be_empty_or_missing(service_event_type):
    for value in ("", None):
        event = Event(title="t", location="l", type=service_event_type, description=value)
        assert field_errors(event, "description") == set()


def test_event_type_default_description_may_be_empty_or_missing():
    for value in ("", None):
        assert (
            field_errors(EventType(title="t", default_description=value), "default_description")
            == set()
        )


def test_comment_author_is_optional(shift, volunteer):
    participation = LocalParticipation.objects.create(
        shift=shift, user=volunteer, state=S.CONFIRMED
    )
    comment = ParticipationComment(participation=participation, text="x", visible_for=1)
    assert field_errors(comment, "authored_by_responsible") == set()


def test_individual_times_may_be_stored_as_null(shift, volunteer):
    """null=True (database level); blank is not set, so forms must treat the fields as optional themselves."""
    for name in ("individual_start_time", "individual_end_time"):
        assert LocalParticipation._meta.get_field(name).null is True
    participation = LocalParticipation.objects.create(
        shift=shift, user=volunteer, state=S.CONFIRMED
    )
    participation.refresh_from_db()
    assert participation.individual_start_time is None
    assert participation.individual_end_time is None


def test_new_objects_start_with_safe_defaults(service_event_type, shift, volunteer):
    assert Event(title="t", location="l", type=service_event_type).active is False
    participation = LocalParticipation(shift=shift, user=volunteer)
    assert participation.state == S.GETTING_DISPATCHED
    assert participation.finished is False
    assert EventType(title="t").color == "#343a40"
    assert (
        EventType(title="t").show_participant_data
        == EventType.ShowParticipantDataChoices.INSTANCE_USERS
    )


# ------------------------------------------------------------ persisted enum values are a contract
def test_stored_enum_values_never_change():
    assert {s.name: s.value for s in S} == {
        "REQUESTED": 0,
        "CONFIRMED": 1,
        "USER_DECLINED": 2,
        "RESPONSIBLE_REJECTED": 3,
        "GETTING_DISPATCHED": 4,
    }
    assert {v.name: v.value for v in EventType.ShowParticipantDataChoices} == {
        "INSTANCE_USERS": 0,
        "CONFIRMED": 1,
        "RESPONSIBLES": 2,
        "PUBLIC": 3,
    }
    assert {v.name: v.value for v in ParticipationComment.Visibility} == {
        "RESPONSIBLES_ONLY": 0,
        "PARTICIPANT": 1,
        "PUBLIC": 2,
    }
    assert S.REQUESTED_AND_CONFIRMED == {S.REQUESTED, S.CONFIRMED}


# ------------------------------------------------------------ logging registration
def test_models_are_registered_for_logging_or_explicitly_excluded():
    assert EventType in LOGGED_MODELS
    assert ParticipationComment in LOGGED_MODELS
    assert AbstractParticipation._ephios_dont_log is True
    assert EventTypePreference._ephios_dont_log is True


def test_shift_log_records_readable_flow_and_structure_names(shift):
    recorder = list(ShiftLogConfig().initial_log_recorders(shift))[-1]
    mapping = recorder.derive(shift)
    assert list(mapping.values()) == [
        str(shift.signup_flow.verbose_name),
        str(shift.structure.verbose_name),
    ]


def test_shift_log_names_are_none_for_unknown_slugs(shift):
    shift.signup_flow_slug = "ghost-flow"
    shift.structure_slug = "ghost-structure"
    recorder = list(ShiftLogConfig().initial_log_recorders(shift))[-1]
    assert list(recorder.derive(shift).values()) == [None, None]


# ------------------------------------------------------------ participation helpers
def test_abstract_participation_falls_back_to_django_default_string(shift):
    participation = AbstractParticipation(shift=shift)
    with pytest.raises(NotImplementedError):
        _ = participation.participant
    assert str(participation) == "AbstractParticipation object (None)"


@pytest.mark.parametrize(
    "start, end, structure_says, expected",
    [
        (True, False, False, True),
        (False, True, False, True),
        (False, False, True, True),
        (False, False, False, False),
    ],
    ids=["start_only", "end_only", "structure_only", "nothing"],
)
def test_has_customized_signup_decision_table(
    shift, volunteer, start, end, structure_says, expected
):
    participation = LocalParticipation(shift=shift, user=volunteer)
    if start:
        participation.individual_start_time = shift.start_time
    if end:
        participation.individual_end_time = shift.end_time
    shift.structure.has_customized_signup = lambda _participation: structure_says
    assert participation.has_customized_signup() is expected


# ------------------------------------------------------------ a participation grants view access to the event
@pytest.mark.parametrize("state", list(S), ids=[s.name for s in S])
def test_saving_a_participation_grants_event_view_access_except_when_dispatched(
    event, shift, state
):
    outsider = UserProfile.objects.create(
        display_name="Outside Olga",
        email="olga2@sqe.test",
        date_of_birth="1990-01-01",
        password="x",
    )
    assert not outsider.has_perm("core.view_event", event)
    LocalParticipation.objects.create(shift=shift, user=outsider, state=state)
    outsider = UserProfile.objects.get(pk=outsider.pk)  # drop guardian's permission cache
    assert outsider.has_perm("core.view_event", event) is (state != S.GETTING_DISPATCHED)


def test_no_extra_object_permission_when_the_user_may_already_view_the_event(
    event, shift, volunteer
):
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    assert UserObjectPermission.objects.filter(user=volunteer, object_pk=str(event.pk)).count() == 0


# ------------------------------------------------------------ viewable_by: conditions may overlap
class SeesNothingByItself(AbstractParticipant):
    """A non-local participant whose own participations are real rows (like a guest)."""

    def all_participations(self):
        return AbstractParticipation.objects.filter(pk__in=self._pks)

    _pks = ()


def visible(viewer_user, participations):
    qs = AbstractParticipation.objects.filter(pk__in=[p.pk for p in participations])
    return set(qs.viewable_by(viewer_user.as_participant()).values_list("pk", flat=True))


def make_visibility(event, choice):
    event.type.show_participant_data = choice
    event.type.save()


def test_responsible_planner_sees_all_even_when_the_setting_already_shows_everything(
    event, shift, planner, volunteer
):
    make_visibility(event, EventType.ShowParticipantDataChoices.INSTANCE_USERS)
    theirs = LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    assert visible(planner, [theirs]) == {
        theirs.pk
    }  # INSTANCE_USERS and change permission both apply


def test_responsible_planner_sees_own_participation_when_only_responsibles_may_see(
    event, shift, planner
):
    make_visibility(event, EventType.ShowParticipantDataChoices.RESPONSIBLES)
    own = LocalParticipation.objects.create(shift=shift, user=planner, state=S.CONFIRMED)
    assert visible(planner, [own]) == {own.pk}  # own participation and change permission both apply


def test_volunteer_sees_own_participation_when_the_setting_shows_everything(
    event, shift, volunteer
):
    make_visibility(event, EventType.ShowParticipantDataChoices.INSTANCE_USERS)
    own = LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    assert visible(volunteer, [own]) == {own.pk}


def test_user_managers_see_participants_even_when_the_setting_already_shows_everything(
    event, shift, manager, volunteer
):
    make_visibility(event, EventType.ShowParticipantDataChoices.INSTANCE_USERS)
    theirs = LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    assert visible(manager, [theirs]) == {
        theirs.pk
    }  # may view user profiles, and the setting applies


def test_public_event_shows_a_guests_own_participation_exactly_once(event, shift, volunteer):
    make_visibility(event, EventType.ShowParticipantDataChoices.PUBLIC)
    own = LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    guest = SeesNothingByItself(
        display_name="Guest", qualifications=[], date_of_birth=None, email=None
    )
    guest._pks = (own.pk,)
    qs = AbstractParticipation.objects.filter(pk=own.pk)
    assert qs.viewable_by(guest).count() == 1  # PUBLIC and "own participation" both apply


def test_optional_text_fields_may_be_stored_as_null():
    """full_clean skips blank-allowed fields, so the database-level null flag is asserted directly."""
    assert Event._meta.get_field("description").null is True
    assert EventType._meta.get_field("default_description").null is True
