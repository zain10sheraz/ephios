"""Generate equivalence-partitioning (EP) classes and 3-point boundary-value (BVA) cases from the OpenAPI spec.

Usage:  python scripts/generate_api_data.py [--spec test_specs/openapi.yaml] [--out test_data/api_cases.json]

For every input of every operation (query parameters, path parameters and form-body fields) the generator derives test
values from the constraints written in the spec:

* integer minimum / maximum -> BVA values just below, at and just above each limit (limit-1, limit, limit+1)
* string maxLength / minLength -> BVA lengths just below, at and just above each limit
* enum -> one valid class per value, plus an invalid value
* format date / time / date-time -> valid and invalid classes
* boolean -> every accepted representation (the application accepts any string)
* x-identifier (an id of an existing object) -> existing, non-existent, zero, negative and non-numeric classes
* x-lenient (the application ignores invalid values) -> all classes are expected to be accepted
* x-paired (one half of a split date/time field) -> a lone empty half is invalid

Every case carries the expectation `expected`: valid | invalid | lenient. The tests decide which HTTP status each
expectation means for the endpoint, send ONE invalid value per request and assert it.
"""

import argparse
import json
import os

import yaml

SPEC_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "test_specs", "openapi.yaml")
OUT_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "test_data", "api_cases.json")
HTTP_METHODS = ("get", "post", "put", "patch", "delete")
BIG_ID = "999999999"


def load_spec(path=SPEC_DEFAULT):
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(spec, node):
    """Follow a local $ref chain."""
    while isinstance(node, dict) and "$ref" in node:
        target = spec
        for part in node["$ref"].lstrip("#/").split("/"):
            target = target[part]
        node = target
    return node


def iter_inputs(spec):
    """Yield every input of every operation as a dict."""
    for path, item in sorted(spec["paths"].items()):
        for method in HTTP_METHODS:
            operation = item.get(method)
            if not operation:
                continue
            base = {
                "operation_id": operation["operationId"],
                "method": method.upper(),
                "path": path,
            }
            for parameter in operation.get("parameters", []):
                parameter = resolve(spec, parameter)
                yield {
                    **base,
                    "location": parameter["in"],
                    "name": parameter["name"],
                    "required": bool(parameter.get("required")),
                    "schema": resolve(spec, parameter["schema"]),
                }
            body = (
                operation
                .get("requestBody", {})
                .get("content", {})
                .get("application/x-www-form-urlencoded")
            )
            if body:
                schema = resolve(spec, body["schema"])
                required = set(schema.get("required", []))
                for name, prop in sorted(schema["properties"].items()):
                    yield {
                        **base,
                        "location": "body",
                        "name": name,
                        "required": name in required,
                        "schema": resolve(spec, prop),
                    }


def case(technique, partition, value, expected, **extra):
    return {
        "technique": technique,
        "partition": partition,
        "value": value,
        "expected": expected,
        **extra,
    }


def integer_cases(schema, required, lenient):
    cases = [case("EP", "valid_in_range", str(schema.get("example", 1)), "valid")]
    cases.extend((
        case("EP", "invalid_non_numeric", "abc", "invalid"),
        case("EP", "invalid_decimal", "1.5", "invalid"),
        case("EP", "empty", "", "invalid" if required else "valid"),
    ))
    for limit_name in ("minimum", "maximum"):
        if limit_name not in schema:
            continue
        limit = schema[limit_name]
        below_ok, above_ok = (False, True) if limit_name == "minimum" else (True, False)
        for point, value, ok in (
            ("below", limit - 1, below_ok),
            ("at", limit, True),
            ("above", limit + 1, above_ok),
        ):
            cases.append(
                case(
                    "BVA",
                    f"{limit_name}_{point}",
                    str(value),
                    "valid" if ok else "invalid",
                    boundary={"limit": limit_name, "value": limit, "point": point},
                )
            )
    return mark_lenient(cases, lenient)


def identifier_cases(schema):
    return [
        case("EP", "existing_id", str(schema.get("example", 1)), "valid"),
        case("EP", "nonexistent_id", BIG_ID, "invalid"),
        case("EP", "zero_id", "0", "invalid"),
        case("EP", "negative_id", "-1", "invalid"),
        case("EP", "non_numeric_id", "abc", "invalid"),
    ]


def string_cases(schema, required, wrong_case=True):
    example = str(schema.get("example", "x"))
    fmt = schema.get("format")
    if fmt == "date":
        return [
            case("EP", "valid_date", example, "valid"),
            case("EP", "valid_leap_day", "2096-02-29", "valid"),
            case("EP", "invalid_text", "not-a-date", "invalid"),
            case("EP", "invalid_month_13", "2099-13-45", "invalid"),
            case("EP", "invalid_leap_day_in_common_year", "2099-02-29", "invalid"),
        ]
    if fmt == "time":
        # x-time-edges lists the day edges that are valid on their own; the others would break the cross-field rule
        # meeting_time <= start_time <= end_time and are therefore not a boundary of this field alone
        edges = schema.get("x-time-edges", ["lower", "upper"])
        cases = [case("EP", "valid_time", example, "valid")]
        if "lower" in edges:
            cases.append(case("BVA", "time_lower_edge", "00:00", "valid"))
        if "upper" in edges:
            cases.append(case("BVA", "time_upper_edge", "23:59", "valid"))
        return cases + [
            case("BVA", "time_just_above_upper_edge", "24:00", "invalid"),
            case("EP", "invalid_minutes", "12:60", "invalid"),
            case("EP", "invalid_text", "abc", "invalid"),
        ]
    if fmt == "date-time":
        return [
            case("EP", "valid_datetime", example, "valid"),
            case("EP", "invalid_text", "garbage", "invalid"),
            case("EP", "invalid_date_part", "2099-13-45T00:00:00Z", "invalid"),
        ]
    if "enum" in schema:
        cases = [case("EP", f"valid_enum_{value}", str(value), "valid") for value in schema["enum"]]
        cases.append(case("EP", "invalid_not_an_option", "not-an-option", "invalid"))
        cases.append(case("EP", "empty", "", "invalid" if required else "valid"))
        if wrong_case and isinstance(schema["enum"][0], str):
            cases.append(
                case("EP", "invalid_wrong_case", str(schema["enum"][0]).upper(), "invalid")
            )
        return cases
    cases = [case("EP", "valid_text", example, "valid")]
    min_length = schema.get("minLength", 1 if required else 0)
    cases.append(case("EP", "empty", "", "invalid" if min_length >= 1 else "valid"))
    if required:
        cases.append(case("EP", "invalid_whitespace_only", "   ", "invalid"))
    if "maxLength" in schema:
        limit = schema["maxLength"]
        for point, length in (("below", limit - 1), ("at", limit), ("above", limit + 1)):
            cases.append(
                case(
                    "BVA",
                    f"maxLength_{point}",
                    "x" * length,
                    "invalid" if point == "above" else "valid",
                    boundary={"limit": "maxLength", "value": limit, "point": point},
                )
            )
    return cases


def boolean_cases():
    return [
        case("EP", "checked_on", "on", "valid"),
        case("EP", "explicit_true", "true", "valid"),
        case("EP", "explicit_false", "false", "valid"),
        case("EP", "absent", None, "valid"),
    ]


def mark_lenient(cases, lenient):
    if not lenient:
        return cases
    return [{**item, "expected": "lenient"} for item in cases]


def cases_for(inp):
    schema = inp["schema"]
    lenient = bool(schema.get("x-lenient"))
    if schema.get("x-identifier"):
        cases = identifier_cases(schema)
    elif schema.get("type") == "integer" and "enum" not in schema:
        cases = integer_cases(schema, inp["required"], lenient)
    elif schema.get("type") == "integer":
        cases = string_cases(
            {**schema, "enum": [str(v) for v in schema["enum"]], "example": str(schema["example"])},
            inp["required"],
            wrong_case=False,
        )
    elif schema.get("type") == "boolean":
        cases = boolean_cases()
    else:
        cases = mark_lenient(string_cases(schema, inp["required"]), lenient)
    if schema.get(
        "x-paired"
    ):  # half of a split date/time field: an empty half makes the pair incomplete
        for item in cases:
            if item["partition"] == "empty":
                item["expected"] = "invalid"
    return cases


def generate(spec_path=SPEC_DEFAULT):
    spec = load_spec(spec_path)
    operations = {}
    for inp in iter_inputs(spec):
        op = operations.setdefault(
            inp["operation_id"], {"method": inp["method"], "path": inp["path"], "inputs": {}}
        )
        cases = cases_for(inp)
        for number, item in enumerate(cases, start=1):
            item["id"] = f"{inp['operation_id']}.{inp['name']}.{number:02d}.{item['partition']}"
        op["inputs"][inp["name"]] = {
            "location": inp["location"],
            "required": inp["required"],
            "baseline": inp["schema"].get("example"),
            "cases": cases,
        }
    summary = {
        "operations": len(operations),
        "inputs": 0,
        "cases": 0,
        "EP": 0,
        "BVA": 0,
        "invalid": 0,
    }
    for op in operations.values():
        for data in op["inputs"].values():
            summary["inputs"] += 1
            for item in data["cases"]:
                summary["cases"] += 1
                summary[item["technique"]] += 1
                summary["invalid"] += item["expected"] == "invalid"
    return {"spec": os.path.basename(spec_path), "summary": summary, "operations": operations}


def diff(old, new):
    """Return {operation.input: {'added': [...], 'removed': [...]}} between two generated documents."""
    changes = {}
    for op_id, op in new["operations"].items():
        for name, data in op["inputs"].items():
            before = {
                (c["partition"], c["value"], c["expected"])
                for c in old["operations"]
                .get(op_id, {})
                .get("inputs", {})
                .get(name, {})
                .get("cases", [])
            }
            after = {(c["partition"], c["value"], c["expected"]) for c in data["cases"]}
            if before != after:
                changes[f"{op_id}.{name}"] = {
                    "added": sorted(map(list, after - before)),
                    "removed": sorted(map(list, before - after)),
                }
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--spec", default=SPEC_DEFAULT)
    parser.add_argument("--out", default=OUT_DEFAULT)
    args = parser.parse_args()
    document = generate(args.spec)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=1, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    print(json.dumps(document["summary"]))


if __name__ == "__main__":
    main()
