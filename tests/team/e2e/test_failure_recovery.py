"""S11 failure-and-recovery: a dependency (the database file) fails before a write completes.

Scenario (real application, real browser):
1. volunteer opens the event page and is ready to sign up;
2. the database file is made read-only, so the application cannot write (storage failure);
3. volunteer clicks "sign up": the write fails, the stored state must not change (nothing half-written);
4. the database is restored;
5. volunteer retries: the signup succeeds and the final state has exactly one participation (no duplicate).
"""

import os
import stat

import pytest

from tests.team.e2e.pages import alerts, event_path, own_states, sign_up_button


@pytest.fixture
def read_only_database(server):
    database = server.workdir / "db.sqlite3"
    original_mode = database.stat().st_mode

    def fail():
        os.chmod(database, stat.S_IREAD)

    def restore():
        os.chmod(database, original_mode)

    yield fail, restore
    restore()  # never leave the database read-only for other tests


def test_signup_survives_a_storage_failure_and_a_retry_creates_no_duplicate(
    volunteer_page, planner_api, volunteer_api, server, read_only_database
):
    fail, restore = read_only_database
    event_id, shift_id = planner_api.new_shift(signup_flow_slug="instant_confirmation")
    volunteer_page.goto(server.base + event_path(planner_api, event_id))
    rows_before = server.db_count("abstractparticipation")

    fail()
    response = None
    try:
        sign_up_button(volunteer_page, shift_id).click()
        volunteer_page.wait_for_load_state()
        response = volunteer_page.title()
    finally:
        restore()
    assert (
        "success" not in " ".join(alerts(volunteer_page)).lower()
    )  # the user is not told it worked
    assert response is not None
    assert server.db_count("abstractparticipation") == rows_before  # nothing was persisted
    assert own_states(volunteer_api, shift_id) == []

    volunteer_page.goto(
        server.base + event_path(planner_api, event_id)
    )  # retry after the dependency is back
    sign_up_button(volunteer_page, shift_id).click()
    volunteer_page.wait_for_load_state()
    assert any("successfully signed up" in text for text in alerts(volunteer_page))
    assert own_states(volunteer_api, shift_id) == [1]
    assert server.db_count("abstractparticipation") == rows_before + 1
