"""
Integration probe: can a volunteer sign up via the real signup endpoint (HTTP POST)
when the event has been deactivated? (Related: unit test test_event_inactive_blocks_signup.)
"""

import pytest
from django.urls import reverse

from ephios.core.models import AbstractParticipation, Event, LocalParticipation


@pytest.mark.django_db
def test_signup_post_on_inactive_event_creates_no_participation(client, event, volunteer):
    Event.all_objects.filter(pk=event.pk).update(active=False)
    shift = Event.all_objects.get(pk=event.pk).shifts.get()
    client.force_login(volunteer)
    response = client.post(
        reverse("core:signup_action", kwargs=dict(pk=shift.pk)),
        data={"signup_choice": "sign_up"},
    )
    print("HTTP status:", response.status_code)
    created = LocalParticipation.objects.filter(shift=shift, user=volunteer)
    print("participations created:", [(p.pk, p.state) for p in created])
    assert not created.filter(
        state__in=[AbstractParticipation.States.REQUESTED, AbstractParticipation.States.CONFIRMED]
    ).exists()
