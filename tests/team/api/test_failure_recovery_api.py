"""Controlled failure and recovery of a state-changing operation (signup), through HTTP requests.

The dependency is the database file: it is made read-only so a write cannot complete (a storage dependency becoming
unavailable before the write finishes). Steps: fail, send the signup, verify the persisted state, restore, retry, and
assert the final state with no duplicate record.
"""

import os
import stat

import pytest

SIGN_UP = {"signup_choice": "sign_up"}


@pytest.fixture
def database_failure(server):
    database = server.workdir / "db.sqlite3"
    original_mode = database.stat().st_mode

    def fail():
        os.chmod(database, stat.S_IREAD)

    def restore():
        os.chmod(database, original_mode)

    yield fail, restore
    restore()  # never leave the database read-only for other tests


def own_records(browser, shift):
    return browser.rest("/api/users/me/participations/", shift=shift)["results"]


def test_signup_fails_while_storage_is_down_and_the_retry_creates_exactly_one_record(
    planner, volunteer, server, database_failure
):
    fail, restore = database_failure
    _, shift = planner.new_shift(signup_flow_slug="instant_confirmation")
    rows_before = server.db_count("abstractparticipation")

    fail()
    try:
        failed = volunteer.post(f"/shifts/{shift}/signup/", SIGN_UP)
    finally:
        restore()
    assert failed.status_code >= 500  # the write could not complete and the client is told so
    assert server.db_count("abstractparticipation") == rows_before  # nothing persisted
    assert own_records(volunteer, shift) == []

    retry = volunteer.post(f"/shifts/{shift}/signup/", SIGN_UP)  # dependency restored
    assert retry.status_code == 302
    [record] = own_records(volunteer, shift)
    assert record["state"]["value"] == 1
    assert server.db_count("abstractparticipation") == rows_before + 1

    volunteer.post(f"/shifts/{shift}/signup/", SIGN_UP)  # a further retry must not duplicate
    assert len(own_records(volunteer, shift)) == 1
    assert server.db_count("abstractparticipation") == rows_before + 1
