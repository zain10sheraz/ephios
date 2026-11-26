"""Concurrent signups for the last free place: capacity (BR4) must hold when two requests arrive at the same moment.

Limit of the test environment: the application runs here on SQLite, which allows one writer at a time, so one of two
truly simultaneous writes may fail with "database is locked" (HTTP 500). That is a property of SQLite, not of the
capacity rule, so a 500 is tolerated; what must hold is the stored state: never more confirmed participants than
places, never two records for one volunteer.
"""

import threading

ROUNDS = 5
SIGN_UP = {"signup_choice": "sign_up"}


def simultaneous_signups(shift, *browsers):
    barrier = threading.Barrier(len(browsers))
    statuses = []

    def go(browser):
        barrier.wait()
        statuses.append(browser.post(f"/shifts/{shift}/signup/", SIGN_UP).status_code)

    threads = [threading.Thread(target=go, args=(browser,)) for browser in browsers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return statuses


def own_records(browser, shift):
    return browser.rest("/api/users/me/participations/", shift=shift)["results"]


def test_simultaneous_signups_for_one_place_never_exceed_capacity(planner, volunteer, volunteer2):
    for _ in range(ROUNDS):
        _, shift = planner.new_shift(
            maximum_number_of_participants="1", signup_flow_slug="instant_confirmation"
        )
        statuses = simultaneous_signups(shift, volunteer, volunteer2)
        assert set(statuses) <= {302, 500}, statuses
        assert planner.rest(f"/api/shifts/{shift}/")["signup_stats"]["confirmed_count"] <= 1
        assert len(own_records(volunteer, shift)) <= 1
        assert len(own_records(volunteer2, shift)) <= 1
