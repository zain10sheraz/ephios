"""Enforce the team's SonarQube thresholds (justified in docs/team/CI_GATES.md). Exit 1 on any violation.

Usage: python scripts/check_sonar_gate.py http://localhost:9000 <token> [project-key]
"""

import base64
import json
import os
import sys
import urllib.request

host, token = sys.argv[1], sys.argv[2]
key = sys.argv[3] if len(sys.argv) > 3 else "ephios-sqe"
AUTH = "Basic " + base64.b64encode(f"{token}:".encode()).decode()

THRESHOLDS = {  # metric: maximum allowed
    "bugs": 0,
    "vulnerabilities": 0,
    "security_hotspots": 0,
    "code_smells": 14,  # ratchet: 14 smells are all upstream-owned code in scope (13 + 1 when forms/events.py joined the scope); our own code must add none
    "duplicated_lines_density": 3.0,
}
with open(
    os.path.join(os.path.dirname(__file__), "gate_modules.txt"), encoding="utf-8"
) as modules_file:
    FULLY_COVERED = [
        line.strip() for line in modules_file if line.strip()
    ]  # files that must stay at 100 % coverage


def get(path):
    request = urllib.request.Request(f"{host}{path}", headers={"Authorization": AUTH})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


metrics = ",".join(THRESHOLDS)
measures = {
    m["metric"]: float(m["value"])
    for m in get(f"/api/measures/component?component={key}&metricKeys={metrics}")["component"][
        "measures"
    ]
}
failed = []
for metric, limit in THRESHOLDS.items():
    value = measures.get(metric)
    ok = value is not None and value <= limit
    print(f"{'OK  ' if ok else 'FAIL'} {metric} = {value} (max {limit})")
    if not ok:
        failed.append(metric)

if {"bugs", "vulnerabilities"} & set(
    failed
):  # name the offending lines so the failure can be acted upon
    found = get(
        f"/api/issues/search?componentKeys={key}&types=BUG,VULNERABILITY&resolved=false&ps=50"
    )
    for issue in found["issues"]:
        print(
            f"  {issue['type']} {issue['rule']} {issue['component']}:{issue.get('line')} {issue['message']}"
        )

tree = get(
    f"/api/measures/component_tree?component={key}&metricKeys=coverage&qualifiers=FIL&ps=500"
)
coverage = {
    c["path"]: float(c["measures"][0]["value"]) for c in tree["components"] if c["measures"]
}
for path in FULLY_COVERED:
    value = coverage.get(path)
    ok = value is not None and value >= 100.0
    print(f"{'OK  ' if ok else 'FAIL'} coverage {path} = {value} (required 100)")
    if not ok:
        failed.append(path)

sys.exit(1 if failed else 0)
