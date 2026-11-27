"""Access matrix of the two workflows: role x action -> expected and observed decision, checked in the real browser.

The observed results are written to reports/e2e/access_matrix.md (role, action, expected, observed) as evidence.
"""

import pytest

from tests.team.api.support import ROOT

RESULTS = []

# (role, action, path template, expected HTTP status, meaning)
MATRIX = [
    ("anonymous", "open create-event page", "/events/create/1/", 200, "redirected to login"),
    ("volunteer", "open create-event page", "/events/create/1/", 403, "denied"),
    ("planner", "open create-event page", "/events/create/1/", 200, "allowed"),
    ("volunteer", "open edit-shift page", "/shifts/{shift}/edit/", 403, "denied"),
    ("planner", "open edit-shift page", "/shifts/{shift}/edit/", 200, "allowed"),
    ("volunteer", "open delete-shift page", "/shifts/{shift}/delete/", 403, "denied"),
    ("volunteer", "open the event list", "/events/", 200, "allowed"),
]


@pytest.fixture(scope="module", autouse=True)
def write_matrix():
    yield
    out = ROOT / "reports" / "e2e"
    out.mkdir(parents=True, exist_ok=True)
    lines = [
        "| Role | Action | Expected | Observed | Result | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    lines += [
        f"| {role} | {action} | {expected} | {observed} | {'PASS' if expected == observed else 'FAIL'} | {evidence} |"
        for role, action, expected, observed, evidence in RESULTS
    ]
    (out / "access_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    ("role", "action", "path", "expected", "meaning"),
    MATRIX,
    ids=[f"{m[0]}-{m[1]}" for m in MATRIX],
)
def test_access_decision(role, action, path, expected, meaning, make_page, planner_api, server):
    from tests.team.api.support import PLANNER, VOLUNTEER

    _, shift_id = planner_api.new_shift()
    credentials = {"anonymous": None, "volunteer": VOLUNTEER, "planner": PLANNER}[role]
    page = make_page(credentials)
    response = page.goto(server.base + path.format(shift=shift_id))
    observed_status = response.status
    if role == "anonymous":
        assert "/accounts/login/" in page.url  # the login page replaced the protected page
    evidence = f"`test_access_decision[{role}-{action}]`, HTTP {observed_status}, final URL `{page.url.replace(server.base, '')}`"
    RESULTS.append((role, f"{action} ({meaning})", expected, observed_status, evidence))
    assert observed_status == expected
