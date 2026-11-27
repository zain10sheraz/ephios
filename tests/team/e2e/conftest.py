"""Browser end-to-end fixtures: a real Ephios process (temporary database, seeded accounts) and real Chromium.

Every page logs in through the real login form. No screenshots are taken or stored by these tests.
"""

import importlib
import os
from pathlib import Path

import pytest

from tests.team.api.support import PLANNER, VOLUNTEER, VOLUNTEER2, Browser, Server

try:  # loaded dynamically: the upstream test jobs and the lint job do not install the browser tooling
    sync_playwright = importlib.import_module("playwright.sync_api").sync_playwright
except ImportError:
    sync_playwright = None
    collect_ignore_glob = [
        "test_*.py"
    ]  # browser tests run in the job e2e-browser-tests, which installs Playwright

HERE = Path(__file__).parent


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    """The upstream conftest marks every test as django_db. These browser tests use a separate real server and never
    touch an in-process database, and Django's test database set-up cannot run next to Playwright's event loop."""
    for item in items:
        if HERE in Path(str(item.path)).parents:
            item.own_markers = [marker for marker in item.own_markers if marker.name != "django_db"]


@pytest.fixture(autouse=True)
def enable_plugins():
    """Override of the upstream autouse fixture of the same name, which needs the in-process database."""
    return


@pytest.fixture(scope="session")
def server(tmp_path_factory):
    srv = Server(tmp_path_factory.mktemp("ephios_e2e"))
    srv.start()
    yield srv
    srv.stop()


@pytest.fixture(scope="session")
def chromium():
    with sync_playwright() as playwright:
        proxy = os.environ.get(
            "E2E_PROXY"
        )  # e.g. the OWASP ZAP proxy for the passive security scan
        options = (
            {"proxy": {"server": proxy}, "args": ["--proxy-bypass-list=<-loopback>"]}
            if proxy
            else {}
        )
        browser = playwright.chromium.launch(**options)
        yield browser
        browser.close()


def login(page, base, credentials):
    page.goto(f"{base}/accounts/login/")
    page.fill("#id_username", credentials[0])
    page.fill("#id_password", credentials[1])
    page.click("button[type=submit]")
    page.wait_for_url(lambda url: "/accounts/login" not in url)


@pytest.fixture
def make_page(chromium, server):
    """Return a function that opens a new logged-in (or anonymous) page; all contexts are closed after the test."""
    contexts = []

    def factory(credentials=None):
        context = chromium.new_context()
        context.set_default_timeout(
            60000
        )  # generous: the laptop has 7.7 GB RAM and slows down under memory pressure
        context.set_default_navigation_timeout(60000)
        contexts.append(context)
        page = context.new_page()
        if credentials:
            login(page, server.base, credentials)
        return page

    yield factory
    for context in contexts:
        context.close()


@pytest.fixture
def planner_page(make_page):
    return make_page(PLANNER)


@pytest.fixture
def volunteer_page(make_page):
    return make_page(VOLUNTEER)


@pytest.fixture
def anonymous_page(make_page):
    return make_page()


@pytest.fixture(scope="session")
def planner_api(server):
    """HTTP session used only to prepare data and to read stored state back after a browser step."""
    return Browser(server.local_base, PLANNER)


@pytest.fixture(scope="session")
def volunteer_api(server):
    return Browser(server.local_base, VOLUNTEER)


@pytest.fixture(scope="session")
def volunteer2_api(server):
    return Browser(server.local_base, VOLUNTEER2)
