"""Live probe of DEFECT-004 against the running Ephios (http://localhost:8000).
Logs in via the real login form, then requests the shift configuration-form fragment endpoints with
valid and crafted parameters. Prints the actual HTTP status codes. No mocks."""
import re
import sys

import requests

BASE = "http://localhost:8000"
EMAIL, PASSWORD = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("admin@localhost", "admin")

s = requests.Session()
html = s.get(f"{BASE}/accounts/login/").text
token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
r = s.post(f"{BASE}/accounts/login/", data={"username": EMAIL, "password": PASSWORD, "csrfmiddlewaretoken": token},
           headers={"Referer": f"{BASE}/accounts/login/"}, allow_redirects=False)
print("login:", r.status_code, "session cookie:", "sessionid" in s.cookies)

event_id = 1
cases = [
    ("flow fragment, valid slug (control)", f"/events/{event_id}/form/signup-flow-config/request_confirm/"),
    ("flow fragment, unknown slug", f"/events/{event_id}/form/signup-flow-config/no-such-flow/"),
    ("flow fragment, shift_id=abc", f"/events/{event_id}/form/signup-flow-config/request_confirm/?shift_id=abc"),
    ("structure fragment, valid slug (control)", f"/events/{event_id}/form/shift-structure-config/uniform/"),
    ("structure fragment, unknown slug", f"/events/{event_id}/form/shift-structure-config/no-such-structure/"),
    ("structure fragment, shift_id=abc", f"/events/{event_id}/form/shift-structure-config/uniform/?shift_id=abc"),
]
for name, path in cases:
    print(f"{name:42s} -> HTTP {s.get(BASE + path).status_code}")
