"""Tests of the test basis itself (no server needed): the OpenAPI spec is consistent and the generator output is
reproducible and contains the boundary points the technique requires."""

import importlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

generator = importlib.import_module("generate_api_data")

SPEC_PATH = ROOT / "test_specs" / "openapi.yaml"
CASES_PATH = ROOT / "test_data" / "api_cases.json"


def refs(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref":
                yield value
            else:
                yield from refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from refs(value)


def test_every_reference_in_spec_resolves():
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    for ref in refs(spec):
        target = spec
        for part in ref.lstrip("#/").split("/"):
            target = target[part]
        assert target is not None, ref


def test_operation_ids_are_unique():
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    ids = [
        op["operationId"]
        for item in spec["paths"].values()
        for op in item.values()
        if isinstance(op, dict)
    ]
    assert len(ids) == len(set(ids)) == 14


def test_committed_cases_match_a_fresh_generation():
    fresh = generator.generate(str(SPEC_PATH))
    committed = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    assert fresh == committed


def test_generator_is_deterministic():
    first_run = generator.generate(str(SPEC_PATH))
    second_run = generator.generate(str(SPEC_PATH))
    assert first_run == second_run


def test_three_point_bva_for_every_numeric_limit():
    document = generator.generate(str(SPEC_PATH))
    cases = document["operations"]["createShift"]["inputs"]["maximum_number_of_participants"][
        "cases"
    ]
    points = {
        (c["boundary"]["limit"], c["boundary"]["point"]): c["value"]
        for c in cases
        if "boundary" in c
    }
    assert points == {("minimum", "below"): "0", ("minimum", "at"): "1", ("minimum", "above"): "2"}


def test_three_point_bva_for_string_length():
    document = generator.generate(str(SPEC_PATH))
    cases = document["operations"]["createEvent"]["inputs"]["title"]["cases"]
    lengths = {c["boundary"]["point"]: len(c["value"]) for c in cases if "boundary" in c}
    assert lengths == {"below": 253, "at": 254, "above": 255}


def test_changing_a_constraint_changes_the_generated_cases():
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    before = generator.generate(str(SPEC_PATH))
    spec["components"]["schemas"]["ShiftForm"]["properties"]["maximum_number_of_participants"][
        "minimum"
    ] = 3
    modified = SPEC_PATH.parent / "_modified_for_test.yaml"
    modified.write_text(yaml.safe_dump(spec), encoding="utf-8")
    try:
        after = generator.generate(str(modified))
    finally:
        modified.unlink()
    changes = generator.diff(before, after)
    assert "createShift.maximum_number_of_participants" in changes
    assert "editShift.maximum_number_of_participants" in changes
