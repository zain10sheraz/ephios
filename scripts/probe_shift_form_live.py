"""Live probe of DEFECT-002 against the running Ephios (http://localhost:8000).
Logs in as the seeded Planner/admin via the real login form, then POSTs the create-shift form
with a missing / invalid date. Prints the actual HTTP status codes. No mocks."""

import re
import sys

import requests

BASE = "http://localhost:8000"
EMAIL, PASSWORD = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("admin@localhost", "admin")


def csrf(session, url):
    html = session.get(url).text
    return re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)


s = requests.Session()
token = csrf(s, f"{BASE}/accounts/login/")
r = s.post(
    f"{BASE}/accounts/login/",
    data={"username": EMAIL, "password": PASSWORD, "csrfmiddlewaretoken": token},
    headers={"Referer": f"{BASE}/accounts/login/"},
    allow_redirects=False,
)
print("login:", r.status_code, "sessionid cookie set:", "sessionid" in s.cookies)

event_id = 1
url = f"{BASE}/events/{event_id}/createshift/"
token = csrf(s, url)
good = dict(
    date="2099-06-30",
    meeting_time="09:00",
    start_time="10:00",
    end_time="16:00",
    label="",
    signup_flow_slug="request_confirm",
    structure_slug="uniform",
    csrfmiddlewaretoken=token,
)
for name, patch in [
    ("valid input (control)", {}),
    ("date empty", {"date": ""}),
    ("date invalid text", {"date": "not-a-date"}),
    ("start_time empty", {"start_time": ""}),
    ("start_time invalid 25:99", {"start_time": "25:99"}),
]:
    resp = s.post(url, data={**good, **patch}, headers={"Referer": url}, allow_redirects=False)
    print(f"{name:28s} -> HTTP {resp.status_code}")
