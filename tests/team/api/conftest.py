import json

import pytest

from tests.team.api.support import OBSERVED, PLANNER, ROOT, VOLUNTEER, VOLUNTEER2, Browser, Server


@pytest.fixture(scope="session")
def server(tmp_path_factory):
    srv = Server(tmp_path_factory.mktemp("ephios_api"))
    srv.start()
    yield srv
    srv.stop()
    out = ROOT / "reports" / "api"
    out.mkdir(parents=True, exist_ok=True)
    (out / "observed_raw.json").write_text(json.dumps(OBSERVED), encoding="utf-8")


@pytest.fixture(scope="session")
def planner(server):
    return Browser(server.base, PLANNER)


@pytest.fixture(scope="session")
def volunteer(server):
    return Browser(server.base, VOLUNTEER)


@pytest.fixture(scope="session")
def volunteer2(server):
    return Browser(server.base, VOLUNTEER2)


@pytest.fixture
def anonymous(server):
    return Browser(server.base)
