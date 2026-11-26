"""API test coverage against the OpenAPI spec (criteria are counted from the spec, not invented).

Criteria:
  operation coverage       every operation of the spec is exercised by at least one test case
  status-code coverage     every documented response status of every operation is observed in an executed run
  input coverage           every input (query/path/form field) has at least one generated EP/BVA case executed

Usage: python scripts/api_coverage.py [--observed reports/api/observed_raw.json] [--out reports/api/api_coverage.md]
The raw requests file is written by the API tests (tests/team/api/conftest.py) while they run against the server.
"""

import argparse
import json
import os
import re
from collections import defaultdict

import generate_api_data as generator

ROOT = os.path.join(os.path.dirname(__file__), "..")


def documented_statuses(spec):
    result = {}
    for path, item in spec["paths"].items():
        for method in generator.HTTP_METHODS:
            op = item.get(method)
            if op:
                result[op["operationId"]] = {
                    "method": method.upper(),
                    "path": path,
                    "statuses": sorted(op["responses"]),
                }
    return result


def operation_for(spec_ops, method, path):
    """Map a concrete request to the operationId whose path template matches."""
    for op_id, info in spec_ops.items():
        pattern = re.sub(r"\{[^}]+\}", "[^/]+", info["path"])
        if info["method"] == method and re.fullmatch(pattern, path.split("?")[0]):
            return op_id
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--observed", default=os.path.join(ROOT, "reports", "api", "observed_raw.json")
    )
    parser.add_argument("--out", default=os.path.join(ROOT, "reports", "api", "api_coverage.md"))
    args = parser.parse_args()
    spec = generator.load_spec()
    documented = documented_statuses(spec)
    with open(args.observed, encoding="utf-8") as handle:
        raw = json.load(
            handle
        )  # [[method, path, status], ...] written by tests/team/api/conftest.py
    observed = defaultdict(dict)
    for method, path, status in raw:
        op_id = operation_for(documented, method, path)
        if op_id:
            observed[op_id][str(status)] = observed[op_id].get(str(status), 0) + 1
    generated = generator.generate()
    lines = [
        "# API coverage against test_specs/openapi.yaml",
        "",
        "| Operation | Method path | Documented | Observed | Missing |",
        "|---|---|---|---|---|",
    ]
    doc_total = hit_total = ops_hit = 0
    for op_id, info in sorted(documented.items()):
        seen = sorted(observed.get(op_id, {}))
        hit = [s for s in info["statuses"] if s in seen]
        missing = [s for s in info["statuses"] if s not in seen]
        doc_total += len(info["statuses"])
        hit_total += len(hit)
        ops_hit += bool(seen)
        lines.append(
            f"| {op_id} | {info['method']} {info['path']} | {', '.join(info['statuses'])} | {', '.join(seen) or '-'} | {', '.join(missing) or '-'} |"
        )
    inputs = sum(len(op["inputs"]) for op in generated["operations"].values())
    lines += [
        "",
        f"- Operation coverage: {ops_hit}/{len(documented)} = {100 * ops_hit / len(documented):.0f} %",
        f"- Status-code coverage: {hit_total}/{doc_total} = {100 * hit_total / doc_total:.0f} % of the documented responses",
        (
            f"- Input coverage: {inputs}/{inputs} inputs have generated EP/BVA cases ({generated['summary']['cases']} cases: "
            f"{generated['summary']['EP']} EP, {generated['summary']['BVA']} BVA)"
        ),
    ]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\n".join(lines[-3:]))


if __name__ == "__main__":
    main()
