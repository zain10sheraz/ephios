"""Helpers for black-box HTTP tests against a real, separately started Ephios process.

The write API of Ephios consists of HTML form endpoints (session cookie + CSRF token, urlencoded body); only the REST
API under /api/ is JSON and read-only. These helpers log in like a browser does and send real HTTP requests.
"""

import itertools
import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
TIMEOUT = 120

PLANNER = ("planner@sqe.test", "Planner#2026")
VOLUNTEER = ("volunteer@sqe.test", "Volunteer#2026")
VOLUNTEER2 = ("volunteer2@sqe.test", "Volunteer#2026")

VALID_SHIFT = {
    "date": "2099-06-30",
    "meeting_time": "09:00",
    "start_time": "10:00",
    "end_time": "16:00",
    "label": "Night shift",
    "signup_flow_slug": "instant_confirmation",
    "structure_slug": "uniform",
    "maximum_number_of_participants": "5",
    "minimum_number_of_participants": "0",
    "minimum_age": "18",
    "signup_until_0": "2099-06-29",
    "signup_until_1": "08:00",
    "user_can_decline_confirmed": "on",
    "user_can_customize_signup_times": "on",
}
VALID_EVENT = {
    "title": "API created event",
    "description": "Created by API tests",
    "location": "Test hall",
    "visible_for": "1",
    "responsible_groups": "2",
}


_DAYS = itertools.count(1)


def unique_day():
    """Shift date fields for a day nobody used yet, so signups of the same volunteer never overlap in time."""
    day = date(2090, 1, 1) + timedelta(days=next(_DAYS))
    return {"date": day.isoformat(), "signup_until_0": (day - timedelta(days=1)).isoformat()}


OBSERVED = []  # (method, path, status) of every request, used by scripts/api_coverage.py


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Server:
    """A real Ephios process on a temporary SQLite database, seeded with the synthetic accounts."""

    def __init__(self, workdir):
        self.workdir = Path(workdir)
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.process = None
        self.env = {
            **os.environ,
            "PYTHONPATH": str(SRC),
            "DJANGO_SETTINGS_MODULE": "ephios.settings",
            "DEBUG": "True",
            "SECRET_KEY": "api-test-secret-key-not-used-anywhere-else",
            "ALLOWED_HOSTS": "*",
            "SITE_URL": self.base,
            "DATABASE_URL": f"sqlite:///{(self.workdir / 'db.sqlite3').as_posix()}",
            "DATA_DIR": str(self.workdir),
            "EMAIL_URL": "consolemail://",
            "PYTHONIOENCODING": "utf-8",
        }

    def db_count(self, table):
        """Number of rows in a table of the application database, read directly (read-only) for post-condition checks."""
        connection = sqlite3.connect(
            f"file:{(self.workdir / 'db.sqlite3').as_posix()}?mode=ro", uri=True
        )
        try:
            return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        finally:
            connection.close()

    def run(self, *args):
        subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            env=self.env,
            check=True,
            capture_output=True,
            timeout=600,
        )

    def start(self):
        self.run("manage.py", "migrate", "--noinput")
        self.run("manage.py", "collectstatic", "--noinput")
        self.run("manage.py", "compilejsi18n")
        self.run("scripts/seed_test_data.py")
        log = open(self.workdir / "server.log", "wb")  # noqa: SIM115 - closed by stop()
        self.log = log
        self.process = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", f"127.0.0.1:{self.port}", "--noreload"],
            cwd=ROOT,
            env=self.env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        deadline = time.time() + 120
        while time.time() < deadline:
            try:
                status = requests.get(self.base + "/accounts/login/", timeout=60).status_code
            except (requests.ConnectionError, requests.Timeout):
                status = None
            if status == 200:
                return
            if status is not None:
                raise RuntimeError(
                    f"login page returned HTTP {status}; see {self.workdir / 'server.log'}"
                )
            time.sleep(1)
        raise RuntimeError("server did not start")

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=30)
        self.log.close()


class Browser:
    """One logged-in (or anonymous) HTTP session; sends CSRF token like a browser does."""

    def __init__(self, base, credentials=None):
        self.base = base
        self.session = requests.Session()
        self.session.headers["Referer"] = base + "/"
        if credentials:
            self.login(*credentials)

    def login(self, email, password):
        self.session.get(self.base + "/accounts/login/", timeout=TIMEOUT)
        response = self.session.post(
            self.base + "/accounts/login/",
            data={"username": email, "password": password, "csrfmiddlewaretoken": self.csrf()},
            allow_redirects=False,
            timeout=TIMEOUT,
        )
        assert response.status_code == 302, f"login failed for {email}: {response.status_code}"

    def csrf(self):
        return self.session.cookies.get("csrftoken", "")

    def get(self, path, **params):
        response = self.session.get(
            self.base + path, params=params, allow_redirects=False, timeout=TIMEOUT
        )
        OBSERVED.append(("GET", path, response.status_code))
        return response

    def post(self, path, data=None):
        body = {**(data or {}), "csrfmiddlewaretoken": self.csrf()}
        body = {key: value for key, value in body.items() if value is not None}
        response = self.session.post(
            self.base + path, data=body, allow_redirects=False, timeout=TIMEOUT
        )
        OBSERVED.append(("POST", path, response.status_code))
        return response

    def post_without_csrf(self, path, data=None):
        response = self.session.post(
            self.base + path, data=data or {}, allow_redirects=False, timeout=TIMEOUT
        )
        OBSERVED.append(("POST", path, response.status_code))
        return response

    def request(self, method, path, data=None):
        body = {**(data or {}), "csrfmiddlewaretoken": self.csrf()}
        response = self.session.request(
            method, self.base + path, data=body, allow_redirects=False, timeout=TIMEOUT
        )
        OBSERVED.append((method, path, response.status_code))
        return response

    # ---- convenience used by many tests
    def create_event(self, **overrides):
        """Create an event as planner; return its id (read back from the redirect target)."""
        response = self.post("/events/create/1/", {**VALID_EVENT, **overrides})
        assert response.status_code == 302, response.text[:300]
        match = re.search(r"/events/(\d+)/createshift/", response.headers["Location"])
        assert match, response.headers["Location"]
        return int(match.group(1))

    def create_shift(self, event_id, **overrides):
        """Add a shift to an event; return the id of the new shift (read back through the REST API)."""
        response = self.post(f"/events/{event_id}/createshift/", {**VALID_SHIFT, **overrides})
        assert response.status_code == 302, response.text[:300]
        shifts = self.get(f"/api/events/{event_id}/").json()["shifts"]
        return max(shift["id"] for shift in shifts)

    def new_shift(self, **overrides):
        event_id = self.create_event()
        return event_id, self.create_shift(event_id, **{**unique_day(), **overrides})

    def rest(self, path, **params):
        response = self.get(path, **params)
        assert response.status_code == 200, (path, response.status_code, response.text[:200])
        return response.json()
