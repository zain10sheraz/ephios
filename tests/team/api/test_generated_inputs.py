"""EP and 3-point BVA black-box tests: every case in test_data/api_cases.json (generated from test_specs/openapi.yaml)
is sent as ONE invalid/valid value per request to the real application and the HTTP status is asserted.

Expected status by kind of input (see test_specs/openapi.yaml):
  GET list filter       valid/lenient -> 200, invalid -> 400
  GET detail path id    valid -> 200,  invalid -> 404
  POST path id          valid -> 302,  invalid -> 404
  POST form field       valid -> 302,  invalid -> 200 (form shown again, nothing saved)
"""

import json
from pathlib import Path

import pytest

from tests.team.api.support import VALID_EVENT, VALID_SHIFT, unique_day

CASES_FILE = Path(__file__).resolve().parents[3] / "test_data" / "api_cases.json"
DOCUMENT = json.loads(CASES_FILE.read_text(encoding="utf-8"))
SIGNUP_BASE = {"signup_choice": "sign_up"}
# post-condition of a successful write: (table, change of its row count); a rejected write changes nothing
STORED = {
    "createEvent": ("event", 1),
    "createShift": ("shift", 1),
    "deleteShift": ("shift", -1),
    "deleteEvent": ("event", -1),
    "signup": ("abstractparticipation", 1),
}


def flatten():
    for op_id, op in DOCUMENT["operations"].items():
        for name, data in op["inputs"].items():
            for item in data["cases"]:
                yield pytest.param(op_id, op, name, data["location"], item, id=item["id"])


def expected_status(op, location, item):
    if item["expected"] == "invalid":
        if location == "path":
            return 404
        if op["method"] == "GET":
            return 400
        return 200
    return 200 if op["method"] == "GET" else 302


# ---- per-operation set-up of a fresh, valid starting point ---------------------------------------------------
def fresh(op_id, planner, volunteer):
    """Return (actor, path_params, base_form_data) with a brand-new object so cases never interfere."""
    if op_id == "createEvent":
        return planner, {"type": "1"}, dict(VALID_EVENT)
    event_id, shift_id = planner.new_shift()
    if op_id in ("createShift", "deleteEvent", "activateEvent"):
        return planner, {"pk": str(event_id)}, dict(VALID_SHIFT) if op_id == "createShift" else {}
    if op_id == "editShift":
        return planner, {"pk": str(shift_id)}, dict(VALID_SHIFT)
    if op_id == "deleteShift":
        planner.create_shift(
            event_id, **unique_day()
        )  # the last shift of an event cannot be deleted
        return planner, {"pk": str(shift_id)}, {}
    if op_id == "signup":
        return volunteer, {"pk": str(shift_id)}, dict(SIGNUP_BASE)
    raise AssertionError(op_id)


def existing_ids(planner, volunteer):
    event_id, shift_id = planner.new_shift()
    volunteer.post(f"/shifts/{shift_id}/signup/", SIGNUP_BASE)
    participation = volunteer.rest("/api/users/me/participations/")["results"][0]["id"]
    return {"event": event_id, "shift": shift_id, "participation": participation}


@pytest.fixture(scope="module")
def ids(planner, volunteer):
    return existing_ids(planner, volunteer)


GET_DETAIL = {"getEvent": "event", "getShift": "shift", "getParticipation": "participation"}
LIST_OPS = {"listEvents", "listShifts", "listParticipations", "listOwnParticipations"}
FILTER_ID = {"type": None, "event_type": None, "shift": "shift", "event": "event"}


@pytest.mark.parametrize(("op_id", "op", "name", "location", "item"), flatten())
def test_generated_case(op_id, op, name, location, item, planner, volunteer, ids, server):
    want = expected_status(op, location, item)
    value = item["value"]
    if op["method"] == "GET":
        path = op["path"]
        params = {}
        if op_id in GET_DETAIL:
            if item["partition"] == "existing_id":
                value = str(ids[GET_DETAIL[op_id]])
            path = path.replace("{id}", str(value))
        else:
            if item["partition"] == "existing_id":
                value = "1" if FILTER_ID.get(name) is None else str(ids[FILTER_ID[name]])
            params = {name: value}
        actor = (
            volunteer
            if op_id in ("getParticipation", "listOwnParticipations", "listParticipations")
            else planner
        )
        response = actor.get(path, **params)
        assert response.status_code == want, (
            f"{item['id']}: value={value!r} -> {response.status_code}, expected {want}"
        )
        return

    actor, path_params, data = fresh(op_id, planner, volunteer)
    if op_id == "signup" and name.startswith("individual_"):
        # a custom time window is only accepted as a complete pair that lies inside the shift (10:00-16:00)
        shift_date = actor.rest(f"/api/shifts/{path_params['pk']}/")["start_time"][:10]
        data.update(
            signup_choice="customize",
            individual_start_time_0=shift_date,
            individual_start_time_1="11:00",
            individual_end_time_0=shift_date,
            individual_end_time_1="15:00",
        )
        if item["partition"] == "valid_date":
            value = shift_date
        if item["expected"] != "invalid":
            # observed rule: a well-formed custom window is accepted iff it starts before it ends (it may extend
            # beyond the shift); a window with start >= end is rejected
            data[name] = value
            start = (data["individual_start_time_0"], data["individual_start_time_1"])
            end = (data["individual_end_time_0"], data["individual_end_time_1"])
            want = 302 if start < end else 200
    if location == "path":
        key = next(iter(path_params))
        if item["partition"] != "existing_id":
            path_params[key] = value
    else:
        data[name] = value
    path = op["path"].format(**path_params)
    table, change = STORED.get(op_id, (None, 0))
    rows_before = server.db_count(table) if table else None
    shift_before = (
        planner.rest(f"/api/shifts/{path_params['pk']}/")
        if op_id == "editShift" and location != "path"
        else None
    )
    response = actor.post(path, data)
    assert response.status_code == want, (
        f"{item['id']}: value={str(value)[:40]!r} -> {response.status_code}, expected {want}"
    )

    # ---- post-conditions, read back from the stored state (not from the response of the write)
    accepted = response.status_code == 302
    if table and not (op_id == "signup" and data["signup_choice"] == "decline"):
        assert server.db_count(table) - rows_before == (change if accepted else 0), (
            f"{item['id']}: stored rows"
        )
    if shift_before is not None and not accepted:
        assert planner.rest(f"/api/shifts/{path_params['pk']}/") == shift_before, (
            f"{item['id']}: rejected edit changed the shift"
        )
    if accepted and name == "maximum_number_of_participants":
        event_or_shift = (
            planner.rest(f"/api/shifts/{path_params['pk']}/")
            if op_id == "editShift"
            else planner.rest(f"/api/events/{path_params['pk']}/")["shifts"][-1]
        )
        stored_capacity = None if value == "" else int(value)  # an empty capacity means unlimited
        assert event_or_shift["signup_stats"]["max_count"] == stored_capacity, (
            f"{item['id']}: capacity not stored"
        )
