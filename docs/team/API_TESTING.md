# Area 2 - API testing, OpenAPI, EP/BVA generator, cross-workflow validation (Manan)

All numbers below come from real runs against a real application process (evidence in `reports/api/`). Nothing here was run against mocks.

## 1. What is tested and how
Ephios has a **read-only JSON REST API** (`/api/...`, DRF) and **write endpoints that are HTML form POSTs** (session cookie + CSRF token,
`application/x-www-form-urlencoded`). Both are API surface for WF1 (events and shifts) and WF2 (signup). The tests are black-box:

| Piece | Where |
|---|---|
| Test basis (OpenAPI 3.0.3, hand-written from observed behaviour; the project's own schema only lists 200 responses) | `test_specs/openapi.yaml` (14 operations, vendor extensions `x-identifier`, `x-lenient`, `x-paired`, `x-time-edges`) |
| EP and 3-point BVA generator | `scripts/generate_api_data.py` -> `test_data/api_cases.json` (80 inputs, 409 cases: 324 EP, 85 BVA, 182 invalid) |
| Regeneration for a changed specification | `scripts/demo_regeneration.py` -> `reports/api/regeneration_demo.txt` |
| Test harness: starts the real app (temporary SQLite DB, migrate, seed, `runserver`), logs in like a browser, sends CSRF token | `tests/team/api/support.py`, `conftest.py` |
| Tests | `tests/team/api/` (462 tests, below) |
| API coverage against the spec | `scripts/api_coverage.py` -> `reports/api/api_coverage.md` |
| CI | job `api-tests-black-box` in `team-quality-gate.yml` (excluded from the unit gate with `--ignore=tests/team/api` because it needs a server) |

| Test file | Tests | Purpose |
|---|---|---|
| `test_generated_inputs.py` | 409 | one case per generated EP/BVA class, **one invalid value per request**, status + stored-state post-conditions |
| `test_rest_api.py` | 13 | FR-04 REST read: envelope, detail, filters, pagination, own-records only, write methods refused, CSRF required |
| `test_business_rules_api.py` | 11 | BR1 deadline, BR2 decline, BR4 capacity (below / at / above), FR-08 no duplicate, instant vs request flow, read-back |
| `test_cross_workflow_api.py` | 11 | WF1 change -> WF2 effect, WF2 signup -> WF1 view (capacity raise/lower, deadline, flow switch, delete shift/event, last-shift rule, permissions) |
| `test_access_control_api.py` | 11 | anonymous / volunteer refused, nothing stored |
| `test_spec_and_generator.py` | 7 | spec refs resolve, operation ids unique, committed cases equal a fresh generation, 3-point BVA present, constraint change changes cases |

## 2. Techniques
* **EP**: every input has a valid class and one invalid class per way of being invalid (non-numeric, decimal, empty, unknown option, wrong type, non-existent id, ...).
  Exactly **one invalid value per request** so a rejection is attributable to that value.
* **3-point BVA** for every numeric limit (min and max: limit-1, limit, limit+1) and string length (253/254/255 for a 254 limit); time-of-day edges 00:00 and 23:59, plus 24:00 just above.
* **Cross-field rules** are not boundaries of one field: `meeting_time <= start_time <= end_time` (declared in the spec with `x-time-edges`), paired date/time halves (`x-paired`),
  signup window must start before it ends (observed; a window beyond the shift is accepted).
* **Post-conditions** (read back from stored state, not from the response of the write): the number of database rows changes by exactly the expected amount after a success
  (event +1, shift +1, delete -1, participation +1) and by **zero after a rejection**; a rejected edit leaves the shift unchanged; an accepted capacity is read back through the REST API
  (an empty capacity is stored as unlimited).
* **Invalid state transitions / rules**: signup beyond capacity, repeated signup, signup after the deadline, decline when the flag forbids it, delete of the last shift (BR-W7), volunteer editing a planner's shift.
* **Cross-workflow**: see the table above; each test changes something through WF1 and reads the effect on WF2 through the REST API and vice versa.

## 3. Results (one clean run, 2026-11-26)
`reports/api/pytest_full_run.txt`: **462 passed, 0 failed** in 7 min 39 s (`reports/api/junit.xml`).
`reports/api/api_coverage.md`: **operation coverage 14/14 = 100 %**, **documented-response coverage 46/46 = 100 %**, **input coverage 80/80**.

## 4. What the first runs found (honest account)
Running the generated cases the first time gave 29 failures out of 425. None was a defect of the application; each was a wrong assumption of mine, corrected from the real behaviour:
* generator ignored cross-field time ordering (4) -> `x-time-edges` in the spec;
* spec claimed a 254 character limit on `search` that the application does not enforce (2) -> spec corrected (no limit);
* a "wrong case" class was generated for integer enums (2) -> generator fixed;
* all shifts used the same day, so the same volunteer's signups overlapped and were rejected (21) -> unique day per shift; this also showed that the **invalid signup cases had been passing for the wrong reason**, which is why post-conditions were added;
* signup custom window beyond the shift is accepted (3) -> expectation changed to "start before end" (observation, not claimed as a defect);
* further corrections: participation state is an object `{value,label}`, the last shift of an event cannot be deleted (a rule, BR-W7), `PUT` on the create endpoint gives 403 not 405 (spec corrected).

## 5. Weaknesses of the API found and reported (all minor, not fixed: design decisions of the upstream HTML application)
| Issue | Weakness | Severity |
|---|---|---|
| #12 DEFECT-005 | business-rule rejections answer 302, the same status as success; only read-back tells them apart | minor |
| #13 DEFECT-006 | invalid `limit`/`offset`/`ordering` silently ignored (200) while other invalid filters return 400 | minor |
| #14 DEFECT-007 | 403 vs 405 inconsistent, 403 instead of 401, project schema documents only 200 | minor |
No source code of the application was changed in area 2. Root cause class for all three: **API contract not specified** (defaults of the framework relied on).

## 6. Limits and what was not done
* Business rule BR5 (inactive event rejects signup) cannot be reached over HTTP: saving a shift activates its event, and an event without a shift has nothing to sign up for. It stays covered by `tests/team/integration/test_inactive_event_signup.py` (DEFECT-001).
* No concurrency (race) test of capacity over HTTP; no load test (area 3).
* The generated tests send one value at a time; combinations of several invalid values are not covered.
* `api-tests-black-box` is not a required check on `main`; the three required checks are unchanged.

## 7. Re-run
    .venv\Scripts\python.exe scripts\generate_api_data.py
    $env:PYTHONPATH="src"; .venv\Scripts\python.exe -m pytest tests/team/api -q -p no:cacheprovider
    cd scripts; ..\.venv\Scripts\python.exe api_coverage.py; ..\.venv\Scripts\python.exe demo_regeneration.py
The first test starts a server (about 40 s); the whole suite takes 8-15 minutes on the 7.7 GB laptop.
