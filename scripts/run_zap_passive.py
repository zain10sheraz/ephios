"""OWASP ZAP in PASSIVE mode while the Playwright tests run both workflows.

What it does (nothing is attacked: ZAP only observes the traffic that the normal Playwright flows produce):
1. starts the ZAP container as a proxy (ghcr.io/zaproxy/zaproxy:stable, daemon mode, port 8090; passive scanners only);
2. runs the browser tests (use cases of both workflows, usability, access matrix) with every browser request sent
   through ZAP (E2E_PROXY); the application is reached through host.docker.internal so the container can see it;
3. waits until ZAP has finished its passive scan queue, then saves the alerts and the list of URLs ZAP saw to
   reports/security/zap_alerts.json and zap_urls.json, and stops the container.
Usage: python scripts/run_zap_passive.py            (Docker must be running)
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "reports", "security")
IMAGE = "ghcr.io/zaproxy/zaproxy:stable"
NAME = "sqe_zap"
API = "http://127.0.0.1:8090"


def zap(path):
    with urllib.request.urlopen(f"{API}/{path}", timeout=60) as response:
        return json.load(response)


def start_zap():
    subprocess.run(["docker", "rm", "-f", NAME], check=False, capture_output=True)
    subprocess.run(
        [
            "docker", "run", "-d", "--name", NAME, "-p", "8090:8090", IMAGE, "zap.sh", "-daemon",
            "-host", "0.0.0.0", "-port", "8090", "-config", "api.disablekey=true",
            "-config", "api.addrs.addr.name=.*", "-config", "api.addrs.addr.regex=true",
        ],
        check=True,
    )  # fmt: skip
    for _ in range(90):
        try:
            return zap("JSON/core/view/version/")["version"]
        except OSError:
            time.sleep(2)
    raise RuntimeError("ZAP did not start")


def main():
    os.makedirs(OUT, exist_ok=True)
    version = start_zap()
    print("ZAP version", version)
    env = {
        **os.environ,
        "E2E_PROXY": "http://127.0.0.1:8090",
        "E2E_BIND": "0.0.0.0",
        "E2E_PUBLIC_HOST": "host.docker.internal",
        "PYTHONPATH": os.path.join(ROOT, "src"),
    }
    tests = [
        "tests/team/e2e/test_uc1_planner_event_shift.py",
        "tests/team/e2e/test_uc2_volunteer_signup.py",
        "tests/team/e2e/test_access_matrix.py",
        "tests/team/e2e/test_usability_keyboard.py",
    ]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *tests, "-q", "-p", "no:cacheprovider"],
        check=False,
        cwd=ROOT,
        env=env,
    )
    print("browser tests through ZAP finished, exit code", result.returncode)
    for _ in range(120):  # wait for the passive scan queue
        if int(zap("JSON/pscan/view/recordsToScan/")["recordsToScan"]) == 0:
            break
        time.sleep(2)
    alerts = zap("JSON/alert/view/alerts/?start=0&count=500")["alerts"]
    urls = zap("JSON/core/view/urls/")["urls"]
    with open(os.path.join(OUT, "zap_alerts.json"), "w", encoding="utf-8") as handle:
        json.dump({"zap_version": version, "alerts": alerts}, handle, indent=1)
    with open(os.path.join(OUT, "zap_urls.json"), "w", encoding="utf-8") as handle:
        json.dump(urls, handle, indent=1)
    subprocess.run(["docker", "rm", "-f", NAME], check=False, capture_output=True)
    print(f"{len(urls)} URLs seen, {len(alerts)} alerts")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
