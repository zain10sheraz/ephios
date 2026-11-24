"""Enforce the team's SonarQube thresholds (justified in docs/team/CI_GATES.md). Exit 1 on any violation.

Usage: python scripts/check_sonar_gate.py http://localhost:9000 <token> [project-key]
"""

import base64
import json
import sys
import urllib.request

host, token = sys.argv[1], sys.argv[2]
key = sys.argv[3] if len(sys.argv) > 3 else "ephios-sqe"
AUTH = "Basic " + base64.b64encode(f"{token}:".encode()).decode()

THRESHOLDS = {  # metric: maximum allowed
    "bugs": 0,
    "vulnerabilities": 0,
    "security_hotspots": 0,
    "code_smells": 13,  # ratchet: 13 smells are upstream-owned code in scope; our own code must add none
    "duplicated_lines_density": 3.0,
}
FULLY_COVERED = [  # files that must stay at 100 % line coverage
    "src/ephios/core/signup/flow/participant_validation.py",
    "src/ephios/core/signup/stats.py",
    "src/ephios/plugins/baseshiftstructures/structure/common.py",
]


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
