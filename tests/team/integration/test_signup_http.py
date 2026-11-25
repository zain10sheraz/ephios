"""
HTTP integration tests of WF2 (participant signup) through the real view
`POST /shifts/<id>/signup/` (Django test client, real database, real views).

Covers FR-05 (sign up), FR-06 (decline), FR-07 (rejection leaves no record), FR-08 (repeated request, no duplicate)
and the read-back of the shared records (Shift, Participation) after success and after rejection.
"""

from datetime import timedelta

import pytest
from django.contrib.messages import get_messages
from django.test import RequestFactory
from django.urls import reverse
from django.utils.timezone import localtime
from guardian.shortcuts import assign_perm

from ephios.core.models import AbstractParticipation, LocalParticipation, UserProfile
from ephios.core.signup.views import prevent_getting_participant_from_request_user

S = AbstractParticipation.States


@pytest.fixture
def shift(event):
    return event.shifts.get()


def url(shift):
    return reverse("core:signup_action", kwargs={"pk": shift.pk})


def configure(shift, flow=None, flow_conf=None, structure_conf=None):
    if flow:
        shift.signup_flow_slug = flow
    if flow_conf is not None:
        shift.signup_flow_configuration = flow_conf
    if structure_conf is not None:
        shift.structure_configuration = structure_conf
    shift.save()
    shift.refresh_from_db()


def participations(shift, user):
    return LocalParticipation.objects.filter(shift=shift, user=user)


def messages_of(response):
    return " | ".join(str(m) for m in get_messages(response.wsgi_request))


def quick(client, shift, choice):
    return client.post(url(shift), {"quick_action": "1", "signup_choice": choice})


# ------------------------------------------------------------ FR-05: successful signup
def test_request_flow_signup_creates_requested_participation(client, shift, volunteer):
    client.force_login(volunteer)
    response = quick(client, shift, "sign_up")
    assert response.status_code == 302
    assert participations(shift, volunteer).get().state == S.REQUESTED
    assert "successfully requested a participation" in messages_of(response)


def test_instant_flow_signup_creates_confirmed_participation(client, shift, volunteer):
    configure(shift, flow="instant_confirmation", flow_conf={})
    client.force_login(volunteer)
    quick(client, shift, "sign_up")
    assert participations(shift, volunteer).get().state == S.CONFIRMED


# ------------------------------------------------------------ FR-08: repeated request, no duplicate
def test_repeated_signup_creates_no_duplicate_and_is_rejected(client, shift, volunteer):
    client.force_login(volunteer)
    quick(client, shift, "sign_up")
    second = quick(client, shift, "sign_up")
    assert second.status_code == 302
    assert participations(shift, volunteer).count() == 1
    assert participations(shift, volunteer).get().state == S.REQUESTED
    assert "not allowed" in messages_of(second).lower()


def test_signup_after_decline_reuses_the_same_participation(client, shift, volunteer):
    client.force_login(volunteer)
    quick(client, shift, "sign_up")
    first_pk = participations(shift, volunteer).get().pk
    quick(client, shift, "decline")
    assert participations(shift, volunteer).get().state == S.USER_DECLINED
    quick(client, shift, "sign_up")
    assert participations(shift, volunteer).count() == 1
    assert participations(shift, volunteer).get().pk == first_pk
    assert participations(shift, volunteer).get().state == S.REQUESTED


# ------------------------------------------------------------ FR-06: decline
def test_decline_of_confirmed_participation_when_allowed(client, shift, volunteer):
    configure(shift, flow="instant_confirmation", flow_conf=dict(user_can_decline_confirmed=True))
    client.force_login(volunteer)
    quick(client, shift, "sign_up")
    quick(client, shift, "decline")
    assert participations(shift, volunteer).get().state == S.USER_DECLINED


def test_decline_of_confirmed_participation_is_refused_when_forbidden(client, shift, volunteer):
    configure(shift, flow="instant_confirmation", flow_conf=dict(user_can_decline_confirmed=False))
    client.force_login(volunteer)
    quick(client, shift, "sign_up")
    response = quick(client, shift, "decline")
    assert participations(shift, volunteer).get().state == S.CONFIRMED  # unchanged
    assert "not allowed" in messages_of(response).lower()


# ------------------------------------------------------------ FR-07: rejections leave nothing behind
def test_signup_after_deadline_is_rejected_and_leaves_no_participation(client, shift, volunteer):
    configure(shift, flow_conf=dict(signup_until=shift.start_time - timedelta(days=365 * 200)))
    client.force_login(volunteer)
    response = quick(client, shift, "sign_up")
    assert response.status_code == 302
    assert participations(shift, volunteer).count() == 0


def test_signup_beyond_capacity_is_rejected_and_count_stays(client, shift, volunteer, planner):
    configure(
        shift,
        flow="instant_confirmation",
        flow_conf={},
        structure_conf=dict(minimum_number_of_participants=0, maximum_number_of_participants=1),
    )
    client.force_login(planner)
    quick(client, shift, "sign_up")
    client.force_login(volunteer)
    quick(client, shift, "sign_up")
    confirmed = LocalParticipation.objects.filter(shift=shift, state=S.CONFIRMED)
    assert confirmed.count() == 1
    assert confirmed.get().user == planner
    assert participations(shift, volunteer).count() == 0


def test_signup_for_inactive_event_creates_nothing(client, shift, volunteer):
    shift.event.active = False
    shift.event.save()
    client.force_login(volunteer)
    quick(client, shift, "sign_up")
    assert participations(shift, volunteer).count() == 0


def test_unknown_signup_choice_is_not_allowed(client, shift, volunteer):
    client.force_login(volunteer)
    response = quick(client, shift, "bogus")
    assert participations(shift, volunteer).count() == 0
    assert "This action is not allowed." in messages_of(response)


# ------------------------------------------------------------ permissions
def test_anonymous_post_is_redirected_to_login(client, shift):
    response = quick(client, shift, "sign_up")
    assert response.status_code == 302
    assert "login" in response.url


def test_user_without_view_permission_cannot_sign_up(client, shift):
    outsider = UserProfile.objects.create(
        display_name="Outside Olga", email="olga@sqe.test", date_of_birth="1990-01-01", password="x"
    )
    client.force_login(outsider)
    response = quick(client, shift, "sign_up")
    assert response.status_code in (302, 403)
    assert LocalParticipation.objects.filter(shift=shift, user=outsider).count() == 0


# ------------------------------------------------------------ conflicts and the regular form
def test_quick_signup_with_conflicting_participation_redirects_to_form(
    client, shift, volunteer, conflicting_event
):
    client.force_login(volunteer)
    response = quick(client, shift, "sign_up")
    assert response.status_code == 302
    assert response.url == url(shift)  # acts like a click on the customize button
    assert "overlap" in messages_of(response).lower()


def test_signup_form_page_renders_for_volunteer(client, shift, volunteer):
    client.force_login(volunteer)
    response = client.get(url(shift))
    assert response.status_code == 200
    assert b"signup_choice" in response.content


def test_regular_form_signup_with_individual_times(client, shift, volunteer):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    start = shift.start_time + timedelta(hours=1)
    end = shift.end_time - timedelta(hours=1)
    client.force_login(volunteer)
    response = client.post(
        url(shift),
        {
            "signup_choice": "sign_up",
            "individual_start_time_0": localtime(start).strftime("%Y-%m-%d"),
            "individual_start_time_1": localtime(start).strftime("%H:%M"),
            "individual_end_time_0": localtime(end).strftime("%Y-%m-%d"),
            "individual_end_time_1": localtime(end).strftime("%H:%M"),
            "comment": "",
        },
    )
    assert response.status_code == 302
    participation = participations(shift, volunteer).get()
    assert participation.state == S.REQUESTED
    assert participation.individual_start_time is not None


def test_regular_form_invalid_data_shows_the_form_again(client, shift, volunteer):
    client.force_login(volunteer)
    response = client.post(
        url(shift), {"signup_choice": "sign_up", "individual_start_time_0": "garbage"}
    )
    assert response.status_code == 200
    assert participations(shift, volunteer).count() == 0


# ------------------------------------------------------------ helper behaviour
def test_request_user_cannot_be_turned_into_a_participant_inside_signup_views(volunteer):
    request = RequestFactory().post("/")
    request.user = volunteer
    prevent_getting_participant_from_request_user(request)
    with pytest.raises(AttributeError):
        request.user.as_participant()


def test_planner_with_change_permission_can_still_sign_up_like_a_volunteer(client, shift, planner):
    assign_perm("change_event", planner, shift.event)
    client.force_login(planner)
    quick(client, shift, "sign_up")
    assert participations(shift, planner).get().state == S.REQUESTED


# ------------------------------------------------------------ customise and failure/rollback
def form_times(start, end):
    return {
        "individual_start_time_0": localtime(start).strftime("%Y-%m-%d"),
        "individual_start_time_1": localtime(start).strftime("%H:%M"),
        "individual_end_time_0": localtime(end).strftime("%Y-%m-%d"),
        "individual_end_time_1": localtime(end).strftime("%H:%M"),
        "comment": "",
    }


def test_customize_changes_times_of_existing_participation(client, shift, volunteer):
    configure(
        shift,
        flow="instant_confirmation",
        flow_conf=dict(user_can_customize_signup_times=True, user_can_decline_confirmed=True),
        structure_conf=dict(minimum_number_of_participants=0, maximum_number_of_participants=5),
    )
    client.force_login(volunteer)
    quick(client, shift, "sign_up")
    new_start = shift.start_time + timedelta(hours=2)
    new_end = shift.end_time - timedelta(hours=2)
    response = client.post(
        url(shift), {"signup_choice": "customize", **form_times(new_start, new_end)}
    )
    assert response.status_code == 302
    participation = participations(shift, volunteer).get()
    assert participation.state == S.CONFIRMED  # customising does not change the state
    assert participation.individual_start_time is not None
    assert participation.individual_start_time.replace(
        second=0, microsecond=0
    ) == new_start.replace(second=0, microsecond=0)
    assert participations(shift, volunteer).count() == 1


def test_failing_flow_action_rolls_back_and_reports_the_error(
    client, shift, volunteer, monkeypatch
):
    from ephios.core.signup.flow.participant_validation import BaseSignupError
    from ephios.plugins.basesignupflows.flow.participant import RequestConfirmSignupFlow

    def failing_signup(self, **kwargs):
        raise BaseSignupError("storage unavailable")

    monkeypatch.setattr(RequestConfirmSignupFlow, "perform_signup", failing_signup)
    client.force_login(volunteer)
    response = quick(client, shift, "sign_up")
    assert response.status_code == 302
    assert "storage unavailable" in messages_of(response)
    assert (
        participations(shift, volunteer).count() == 0
    )  # transaction rolled back, nothing persisted


def test_retry_after_failure_succeeds_without_duplicates(client, shift, volunteer, monkeypatch):
    from ephios.core.signup.flow.participant_validation import BaseSignupError
    from ephios.plugins.basesignupflows.flow.participant import RequestConfirmSignupFlow

    original = RequestConfirmSignupFlow.perform_signup

    def failing_signup(self, **kwargs):
        raise BaseSignupError("temporarily down")

    client.force_login(volunteer)
    with monkeypatch.context() as patch:
        patch.setattr(RequestConfirmSignupFlow, "perform_signup", failing_signup)
        quick(client, shift, "sign_up")
    assert participations(shift, volunteer).count() == 0
    monkeypatch.setattr(RequestConfirmSignupFlow, "perform_signup", original)
    quick(client, shift, "sign_up")
    assert participations(shift, volunteer).count() == 1
    assert participations(shift, volunteer).get().state == S.REQUESTED


def test_customize_is_refused_when_confirmed_user_may_not_decline(client, shift, volunteer):
    """Decision D7: customising a confirmed participation needs can_decline() (the rule behind the refusal)."""
    configure(
        shift,
        flow="instant_confirmation",
        flow_conf=dict(user_can_customize_signup_times=True, user_can_decline_confirmed=False),
    )
    client.force_login(volunteer)
    quick(client, shift, "sign_up")
    new_start = shift.start_time + timedelta(hours=2)
    response = client.post(
        url(shift), {"signup_choice": "customize", **form_times(new_start, shift.end_time)}
    )
    assert response.status_code == 302
    assert "This action is not allowed." in messages_of(response)
    assert participations(shift, volunteer).get().individual_start_time is None


# ------------------------------------------------------------ signup form rules (times and comments)
@pytest.mark.parametrize(
    "end_offset_minutes, valid",
    [(-1, False), (0, True), (1, True)],
    ids=["end_one_minute_before_start", "end_equals_start", "end_one_minute_after_start"],
)
def test_individual_end_time_must_not_be_before_start_time(
    client, shift, volunteer, end_offset_minutes, valid
):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    start = shift.start_time + timedelta(hours=1)
    end = start + timedelta(minutes=end_offset_minutes)
    client.force_login(volunteer)
    response = client.post(url(shift), {"signup_choice": "sign_up", **form_times(start, end)})
    assert (response.status_code == 302) is valid
    assert (participations(shift, volunteer).count() == 1) is valid
    if not valid:
        assert b"End time must not be before start time" in response.content


def test_individual_start_equal_to_shift_start_is_stored_as_unset(client, shift, volunteer):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    client.force_login(volunteer)
    client.post(
        url(shift), {"signup_choice": "sign_up", **form_times(shift.start_time, shift.end_time)}
    )
    participation = participations(shift, volunteer).get()
    assert participation.individual_start_time is None
    assert participation.individual_end_time is None


def test_comment_is_stored_and_shown_again_on_the_next_visit(client, shift, volunteer):
    configure(
        shift, flow_conf=dict(user_can_customize_signup_times=True, user_can_decline_confirmed=True)
    )
    client.force_login(volunteer)
    client.post(
        url(shift),
        {
            "signup_choice": "sign_up",
            **form_times(shift.start_time, shift.end_time),
            "comment": "I bring a car",
        },
    )
    participation = participations(shift, volunteer).get()
    assert [c.text for c in participation.comments.all()] == ["I bring a car"]
    page = client.get(url(shift))
    assert b"I bring a car" in page.content


# ------------------------------------------------------------ locked times and form-level conflict rule
def test_times_are_locked_when_users_may_not_customize_them(client, shift, volunteer):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=False))
    client.force_login(volunteer)
    forged_start = shift.start_time + timedelta(hours=3)
    client.post(
        url(shift), {"signup_choice": "sign_up", **form_times(forged_start, shift.end_time)}
    )
    participation = participations(shift, volunteer).get()
    assert (
        participation.individual_start_time is None
    )  # the posted time was ignored (field disabled)


def test_form_rejects_individual_times_overlapping_a_confirmed_shift(
    client, shift, volunteer, conflicting_event
):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    client.force_login(volunteer)
    response = client.post(
        url(shift), {"signup_choice": "sign_up", **form_times(shift.start_time, shift.end_time)}
    )
    assert response.status_code == 200
    assert b"already confirmed for other shifts" in response.content
    assert participations(shift, volunteer).count() == 0


def test_decline_is_allowed_even_when_shifts_overlap(client, shift, volunteer, conflicting_event):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    client.force_login(volunteer)
    response = client.post(
        url(shift), {"signup_choice": "decline", **form_times(shift.start_time, shift.end_time)}
    )
    assert response.status_code == 302
    assert participations(shift, volunteer).get().state == S.USER_DECLINED


# ------------------------------------------------------------ structure with a required signup field (named teams)
TEAM_UUID = "11111111-1111-1111-1111-111111111111"
TEAM_FIELD = "baseshiftstructures_named_teams_preferred_team_uuid"


@pytest.fixture
def named_teams_shift(shift, qualifications):
    shift.structure_slug = "named_teams"
    shift.structure_configuration = {
        "minimum_age": None,
        "signup_until": None,
        "user_can_decline_confirmed": False,
        "choose_preferred_team": True,
        "teams": [
            {"title": "KTW", "qualification": qualifications.rs, "min_count": 1, "uuid": TEAM_UUID}
        ],
    }
    shift.save()
    shift.refresh_from_db()
    return shift


def test_quick_signup_asks_for_more_information_when_a_field_is_required(
    client, named_teams_shift, qualified_volunteer
):
    client.force_login(qualified_volunteer)
    response = quick(client, named_teams_shift, "sign_up")
    assert response.status_code == 302
    assert response.url == url(named_teams_shift)
    assert "additional information" in messages_of(response)
    assert participations(named_teams_shift, qualified_volunteer).count() == 0


def test_regular_form_stores_the_chosen_team(client, named_teams_shift, qualified_volunteer):
    client.force_login(qualified_volunteer)
    response = client.post(
        url(named_teams_shift),
        {"signup_choice": "sign_up", "comment": "", TEAM_FIELD: TEAM_UUID},
    )
    assert response.status_code == 302
    participation = participations(named_teams_shift, qualified_volunteer).get()
    assert participation.state == S.REQUESTED
    assert participation.structure_data["preferred_team_uuid"] == TEAM_UUID


def test_regular_form_without_the_required_team_is_invalid(
    client, named_teams_shift, qualified_volunteer
):
    client.force_login(qualified_volunteer)
    response = client.post(url(named_teams_shift), {"signup_choice": "sign_up", "comment": ""})
    assert response.status_code == 200
    assert participations(named_teams_shift, qualified_volunteer).count() == 0


# ------------------------------------------------------------ view internals for non-local participants
def test_locked_validator_for_a_non_local_participant_locks_only_the_shift(shift):
    from django.db import transaction

    from ephios.core.signup.participants import PlaceholderParticipant
    from ephios.core.signup.views import SignupView

    view = SignupView()
    view.shift = shift
    view.participant = PlaceholderParticipant(
        display_name="Walk-in", qualifications=[], date_of_birth=None, email=None
    )
    with transaction.atomic():
        validator = view._get_shift_participant_locked_validator()
    assert validator.participant is view.participant
    assert validator.shift.pk == shift.pk


def test_acting_user_is_none_for_anonymous_requests(shift, volunteer):
    from django.contrib.auth.models import AnonymousUser

    from ephios.core.signup.views import SignupView

    view = SignupView()
    view.request = RequestFactory().get("/")
    view.request.user = AnonymousUser()
    assert view._acting_user is None
    view.request.user = volunteer
    assert view._acting_user == volunteer


def test_quick_signup_reuses_the_previously_chosen_team(
    client, named_teams_shift, qualified_volunteer
):
    LocalParticipation.objects.create(
        shift=named_teams_shift,
        user=qualified_volunteer,
        state=S.USER_DECLINED,
        structure_data={"preferred_team_uuid": TEAM_UUID},
    )
    client.force_login(qualified_volunteer)
    response = quick(client, named_teams_shift, "sign_up")
    assert response.status_code == 302
    assert response.url != url(named_teams_shift)  # signed up directly, no detour through the form
    participation = participations(named_teams_shift, qualified_volunteer).get()
    assert participation.state == S.REQUESTED
    assert participation.structure_data["preferred_team_uuid"] == TEAM_UUID


# ------------------------------------------------------------ killers for surviving mutants of signup/views.py
def narrow_conflicting_shift(conflicting_event):
    other = conflicting_event.shifts.get()
    other.end_time = other.start_time + timedelta(hours=1)  # overlaps only the start of `shift`
    other.save()


def test_quick_decline_is_allowed_even_when_shifts_overlap(
    client, shift, volunteer, conflicting_event
):
    client.force_login(volunteer)
    quick(client, shift, "decline")
    assert participations(shift, volunteer).get().state == S.USER_DECLINED


def test_quick_customize_with_an_overlapping_shift_redirects_to_the_form(
    client, shift, volunteer, conflicting_event
):
    client.force_login(volunteer)
    response = quick(client, shift, "customize")
    assert response.status_code == 302
    assert response.url == url(shift)
    assert "overlap" in messages_of(response).lower()


def test_quick_signup_with_a_partial_overlap_is_not_done_silently(
    client, shift, volunteer, conflicting_event
):
    narrow_conflicting_shift(conflicting_event)
    client.force_login(volunteer)
    response = quick(client, shift, "sign_up")
    assert response.url == url(shift)  # partial overlaps must be checked by the participant
    assert "overlap" in messages_of(response).lower()
    assert participations(shift, volunteer).count() == 0


def test_quick_resignup_keeps_the_previously_customized_times(client, shift, volunteer):
    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    start = shift.start_time + timedelta(hours=1)
    end = shift.end_time - timedelta(hours=1)
    client.force_login(volunteer)
    client.post(url(shift), {"signup_choice": "sign_up", **form_times(start, end)})
    quick(client, shift, "decline")
    quick(client, shift, "sign_up")
    participation = participations(shift, volunteer).get()
    assert participation.state == S.REQUESTED
    assert participation.individual_start_time.replace(second=0, microsecond=0) == start.replace(
        second=0, microsecond=0
    )
    assert participation.individual_end_time.replace(second=0, microsecond=0) == end.replace(
        second=0, microsecond=0
    )


NOTIFICATION = "ephios.core.signup.views.ResponsibleConfirmedParticipationCustomizedNotification"


def confirmed_customizable(client, shift, volunteer):
    configure(
        shift,
        flow="instant_confirmation",
        flow_conf=dict(user_can_customize_signup_times=True, user_can_decline_confirmed=True),
        structure_conf=dict(minimum_number_of_participants=0, maximum_number_of_participants=5),
    )
    client.force_login(volunteer)
    quick(client, shift, "sign_up")


def test_customizing_times_notifies_the_responsibles_with_the_changes(client, shift, volunteer):
    from unittest.mock import patch

    confirmed_customizable(client, shift, volunteer)
    new_start = shift.start_time + timedelta(hours=2)
    with patch(NOTIFICATION) as notification:
        client.post(
            url(shift), {"signup_choice": "customize", **form_times(new_start, shift.end_time)}
        )
    assert notification.send.call_count == 1
    participation, claims = notification.send.call_args.args
    assert participation.pk == participations(shift, volunteer).get().pk
    assert len(claims) == 1
    assert "was changed" in claims[0]


def test_customizing_without_changing_times_sends_no_notification(client, shift, volunteer):
    from unittest.mock import patch

    confirmed_customizable(client, shift, volunteer)
    with patch(NOTIFICATION) as notification:
        client.post(
            url(shift),
            {"signup_choice": "customize", **form_times(shift.start_time, shift.end_time)},
        )
    assert notification.send.call_count == 0


def test_signing_up_with_changed_times_sends_no_customize_notification(client, shift, volunteer):
    from unittest.mock import patch

    configure(shift, flow_conf=dict(user_can_customize_signup_times=True))
    client.force_login(volunteer)
    new_start = shift.start_time + timedelta(hours=2)
    with patch(NOTIFICATION) as notification:
        client.post(
            url(shift), {"signup_choice": "sign_up", **form_times(new_start, shift.end_time)}
        )
    assert notification.send.call_count == 0
    assert participations(shift, volunteer).count() == 1
