"""Live-task rehearsal: change two constraints in a COPY of the spec and show which generated cases change.

Usage: python scripts/demo_regeneration.py
Changes: maximum_number_of_participants.minimum 1 -> 3 and event title maxLength 254 -> 100 (the real spec is untouched).
"""

import os
import tempfile

import generate_api_data as generator
import yaml


def show(value):
    text = str(value)
    return f"'x'*{len(text)}" if text and set(text) == {"x"} else repr(text)


def main():
    spec = generator.load_spec()
    before = generator.generate()
    spec["components"]["schemas"]["ShiftForm"]["properties"]["maximum_number_of_participants"][
        "minimum"
    ] = 3
    spec["paths"]["/events/create/{type}/"]["post"]["requestBody"]["content"][
        "application/x-www-form-urlencoded"
    ]["schema"]["properties"]["title"]["maxLength"] = 100
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "modified.yaml")
        with open(path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(spec, handle)
        after = generator.generate(path)
    changes = generator.diff(before, after)
    print(f"cases before: {before['summary']['cases']}, after: {after['summary']['cases']}")
    for key, change in sorted(changes.items()):
        print(f"\n{key}")
        for item in change["removed"]:
            print(f"  - removed {item[0]:<22} value={show(item[1]):<12} expected={item[2]}")
        for item in change["added"]:
            print(f"  + added   {item[0]:<22} value={show(item[1]):<12} expected={item[2]}")


if __name__ == "__main__":
    main()
