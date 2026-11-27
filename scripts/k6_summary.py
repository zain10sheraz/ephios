"""Compute the k6 summary table (reports/performance/k6_summary.md) from the raw k6 exports.

Reads reports/performance/k6_vus*_run*.json (written by `k6 run --summary-export`) and prints, per run, the requests,
requests per second, average, p95 and maximum response time and the percentage of failed requests, and whether the limits
set before testing (p95 < 800 ms, failed requests < 1 %) were met.
"""

import glob
import json
import os

FOLDER = os.path.join(os.path.dirname(__file__), "..", "reports", "performance")
P95_LIMIT_MS = 800
FAILED_LIMIT = 0.01


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)["metrics"]


def main():
    lines = [
        "| VUs | run | requests | req/s | avg ms | p95 ms | max ms | failed % | threshold |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for path in sorted(glob.glob(os.path.join(FOLDER, "k6_vus*_run*.json"))):
        metrics = load(path)
        duration, requests_, failed = (
            metrics["http_req_duration"],
            metrics["http_reqs"],
            metrics["http_req_failed"],
        )
        name = os.path.basename(path)[:-5].split("_")
        met = duration["p(95)"] < P95_LIMIT_MS and failed["value"] < FAILED_LIMIT
        lines.append(
            f"| {name[1][3:]} | {name[2][3:]} | {requests_['count']} | {requests_['rate']:.1f} | {duration['avg']:.0f} "
            f"| {duration['p(95)']:.0f} | {duration['max']:.0f} | {failed['value'] * 100:.2f} | {'PASS' if met else 'FAIL'} |"
        )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
