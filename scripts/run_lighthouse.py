"""Run Lighthouse (accessibility, best practices, SEO) on the logged-in key screen of each use case.

Usage: python scripts/run_lighthouse.py <base_url|start> <phase>      e.g.  http://127.0.0.1:8001 before
       "start" launches a fresh seeded server from THIS source tree (used for the post-fix run).
Needs: Lighthouse installed in C:/sqe_tools (npm install lighthouse), a Chromium (CHROME_PATH), a running seeded server.
It logs in with the real login form's HTTP flow (session cookie), creates its own event/shift for the screens and writes
reports/accessibility/lighthouse_<screen>_<phase>.json (full report) and prints the scores.
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.team.api.support import PLANNER, VOLUNTEER, Browser, Server

LIGHTHOUSE = r"C:\sqe_tools\node_modules\.bin\lighthouse.cmd"
CHROME = os.environ.get(
    "CHROME_PATH",
    r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1255\chrome-win64\chrome.exe",
)
OUT = os.path.join(os.path.dirname(__file__), "..", "reports", "accessibility")


def cookie_header(browser):
    return "; ".join(f"{c.name}={c.value}" for c in browser.session.cookies)


def run(url, browser, name, phase):
    os.makedirs(OUT, exist_ok=True)
    out = os.path.abspath(os.path.join(OUT, f"lighthouse_{name}_{phase}.json"))
    headers = json.dumps({"Cookie": cookie_header(browser)})
    command = [
        LIGHTHOUSE,
        url,
        "--only-categories=accessibility,best-practices,seo",
        "--output=json",
        f"--output-path={out}",
        "--chrome-flags=--headless=new --no-sandbox",
        f"--extra-headers={headers}",
        "--quiet",
    ]
    subprocess.run(command, check=True, env={**os.environ, "CHROME_PATH": CHROME})
    with open(out, encoding="utf-8") as handle:
        report = json.load(handle)
    scores = {key: round(value["score"] * 100) for key, value in report["categories"].items()}
    print(name, phase, scores)


def main():
    base, phase = sys.argv[1], sys.argv[2]
    if base == "start":
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            server = Server(folder)
            server.start()
            try:
                audit(server.base, phase)
            finally:
                server.stop()
    else:
        audit(base, phase)


def audit(base, phase):
    planner, volunteer = Browser(base, PLANNER), Browser(base, VOLUNTEER)
    event_id, shift_id = planner.new_shift()
    run(f"{base}/shifts/{shift_id}/edit/", planner, "uc1_shift_form", phase)
    frontend = planner.rest(f"/api/events/{event_id}/")["frontend_url"]
    run(base + "/" + frontend.split("/", 3)[3], volunteer, "uc2_event_page", phase)


if __name__ == "__main__":
    main()
