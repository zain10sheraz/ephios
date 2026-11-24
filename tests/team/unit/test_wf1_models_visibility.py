"""
Team unit tests for the event/shift/participation model helpers used by WF1 and WF2.

Decision table (BR-V): who may see participant data of an event, by the event type's
`show_participant_data` setting and the viewer.
"""

import pytest
from django.urls import reverse

from ephios.core.models import (
    AbstractParticipation,
    EventType,
    LocalParticipation,
)
from ephios.core.models.events import ParticipationComment, PlaceholderParticipation
from ephios.core.signup.participants import PlaceholderParticipant

S = AbstractParticipation.States
SHOW = EventType.ShowParticipantDataChoices


@pytest.fixture
def shift(event):
    return event.shifts.get()


def visible_ids(viewer, participations):
    qs = AbstractParticipation.objects.filter(pk__in=[p.pk for p in participations])
    return set(qs.viewable_by(viewer.as_participant()).values_list("pk", flat=True))


def set_visibility(event, choice):
    event.type.show_participant_data = choice
    event.type.save()


@pytest.fixture
def two_participations(shift, volunteer, qualified_volunteer):
    mine = LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.REQUESTED)
    theirs = LocalParticipation.objects.create(
        shift=shift, user=qualified_volunteer, state=S.CONFIRMED
    )
    return mine, theirs


# ---- decision table: (setting, viewer) -> which of the two participations are visible
def test_instance_users_setting_shows_everything_to_logged_in_viewers(
    event, volunteer, two_participations
):
    set_visibility(event, SHOW.INSTANCE_USERS)
    mine, theirs = two_participations
    assert visible_ids(volunteer, two_participations) == {mine.pk, theirs.pk}


def test_confirmed_setting_hides_others_from_unconfirmed_viewer(
    event, volunteer, two_participations
):
    set_visibility(event, SHOW.CONFIRMED)
    mine, _ = two_participations
    assert visible_ids(volunteer, two_participations) == {mine.pk}  # only own


def test_confirmed_setting_shows_all_to_confirmed_participant(
    event, qualified_volunteer, two_participations
):
    set_visibility(event, SHOW.CONFIRMED)
    mine, theirs = two_participations
    assert visible_ids(qualified_volunteer, two_participations) == {mine.pk, theirs.pk}


def test_responsibles_setting_hides_others_from_volunteers(event, volunteer, two_participations):
    set_visibility(event, SHOW.RESPONSIBLES)
    mine, _ = two_participations
    assert visible_ids(volunteer, two_participations) == {mine.pk}


def test_responsibles_setting_shows_all_to_planner(event, planner, two_participations):
    set_visibility(event, SHOW.RESPONSIBLES)
    mine, theirs = two_participations
    assert visible_ids(planner, two_participations) == {mine.pk, theirs.pk}


def test_public_setting_shows_everything_to_non_local_participants(event, two_participations):
    set_visibility(event, SHOW.PUBLIC)
    guest = PlaceholderParticipant(
        display_name="Guest", qualifications=[], date_of_birth=None, email=None
    )
    qs = AbstractParticipation.objects.filter(pk__in=[p.pk for p in two_participations])
    assert qs.viewable_by(guest).count() == 2


def test_non_public_setting_hides_everything_from_non_local_participants(event, two_participations):
    set_visibility(event, SHOW.INSTANCE_USERS)
    guest = PlaceholderParticipant(
        display_name="Guest", qualifications=[], date_of_birth=None, email=None
    )
    qs = AbstractParticipation.objects.filter(pk__in=[p.pk for p in two_participations])
    assert qs.viewable_by(guest).count() == 0


def test_with_show_participant_data_to_annotates_each_row(event, volunteer, two_participations):
    set_visibility(event, SHOW.RESPONSIBLES)
    mine, theirs = two_participations
    rows = {
        p.pk: p.show_participant_data
        for p in AbstractParticipation.objects.all().with_show_participant_data_to(
            volunteer.as_participant()
        )
    }
    assert rows[mine.pk] is True
    assert rows[theirs.pk] is False


# ---- participation helpers
def test_participation_states_helpers():
    assert S.REQUESTED_AND_CONFIRMED == {0, 1}
    assert S.labels_dict()[S.CONFIRMED] == "confirmed"


@pytest.mark.parametrize(
    "state, positive",
    [
        (S.REQUESTED, True),
        (S.CONFIRMED, True),
        (S.USER_DECLINED, False),
        (S.RESPONSIBLE_REJECTED, False),
        (S.GETTING_DISPATCHED, False),
    ],
)
def test_is_in_positive_state(shift, volunteer, state, positive):
    participation = LocalParticipation.objects.create(shift=shift, user=volunteer, state=state)
    assert participation.is_in_positive_state() is positive


def test_hours_value_and_customized_signup(shift, volunteer):
    participation = LocalParticipation.objects.create(
        shift=shift, user=volunteer, state=S.CONFIRMED
    )
    assert participation.hours_value == pytest.approx(12.5)  # 08:00 - 20:30
    assert not participation.has_customized_signup()
    participation.individual_start_time = shift.start_time
    assert participation.has_customized_signup()


def test_abstract_participation_str_falls_back_without_participant(shift):
    participation = AbstractParticipation(shift=shift)
    assert str(participation)  # NotImplementedError of .participant is handled


def test_placeholder_participation_participant_and_str(shift):
    participation = PlaceholderParticipation.objects.create(
        shift=shift, display_name="Walk-in Helper", state=S.CONFIRMED
    )
    assert participation.participant.display_name == "Walk-in Helper"
    assert str(participation).startswith("Walk-in Helper @ ")
    assert list(shift.get_participants()) == [participation.participant]


def test_comment_author_is_responsible_or_participant(shift, volunteer, planner):
    participation = LocalParticipation.objects.create(
        shift=shift, user=volunteer, state=S.CONFIRMED
    )
    by_participant = ParticipationComment.objects.create(participation=participation, text="hi")
    by_planner = ParticipationComment.objects.create(
        participation=participation, text="ok", authored_by_responsible=planner
    )
    assert by_participant.author.display_name == volunteer.display_name
    assert by_planner.author == planner
    assert "hi" in str(by_participant)


# ---- shift helpers
def test_shift_str_and_url(shift, event):
    assert str(shift).startswith(event.title)
    shift.label = "Night"
    assert str(shift).startswith("Night (")
    assert shift.get_absolute_url().endswith(f"#shift-{shift.pk}")
    assert event.get_absolute_url() == reverse(
        "core:event_detail", kwargs={"pk": event.pk, "slug": event.get_canonical_slug()}
    )


def test_shift_signup_info_and_refresh_clears_cached_objects(shift):
    assert isinstance(shift.get_signup_info(), dict)
    assert shift.signup_flow.slug == "request_confirm"
    shift.signup_flow_slug = "instant_confirmation"
    shift.save()
    shift.refresh_from_db()
    assert shift.signup_flow.slug == "instant_confirmation"


def test_deleting_a_shift_cascades_to_its_participations(shift, volunteer, planner):
    LocalParticipation.objects.create(shift=shift, user=volunteer, state=S.CONFIRMED)
    PlaceholderParticipation.objects.create(shift=shift, display_name="Walk-in", state=S.CONFIRMED)
    shift_id = shift.pk
    shift.delete()
    assert AbstractParticipation.objects.filter(shift_id=shift_id).count() == 0


def test_signup_info_is_empty_without_flow_and_structure(shift):
    shift.signup_flow = None  # defensive branches: cached properties are normally always objects
    shift.structure = None
    assert shift.get_signup_info() == {}


def test_shift_with_uninstalled_flow_and_structure_uses_fallbacks(shift):
    shift.signup_flow_slug = "no-such-flow"
    shift.structure_slug = "no-such-structure"
    shift.save()
    shift.refresh_from_db()
    assert shift.signup_flow.slug != "request_confirm"
    assert shift.structure.slug != "uniform"
