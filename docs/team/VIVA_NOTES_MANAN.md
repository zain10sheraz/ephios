# Viva notes - Area 2 (API testing, integration, OpenAPI, EP/BVA generator, cross-workflow) - Manan

Re-run things yourself before the viva; do not rely on this page alone. Everything is backed by files in the repository.
Details: `API_TESTING.md`.

## 1. One-minute story
Ephios has a read-only JSON REST API and form endpoints for writing (login cookie + CSRF token). I wrote an OpenAPI specification of 14 operations from the behaviour I observed
(the project's own schema only lists 200 responses), a generator that derives equivalence classes and 3-point boundary values from that specification, and 477 black-box tests (476 plus the recovery test)
that start the real application, log in, send real HTTP requests and read the stored state back. Nothing is mocked.

## 2. Component by component

| Component | What to say | Where |
|---|---|---|
| **OpenAPI spec** | 14 operations (7 REST reads, 7 form writes); constraints (min, max, maxLength, enum, format) drive the generator; vendor extensions mark ids (`x-identifier`), parameters the app ignores when invalid (`x-lenient`), split date/time fields (`x-paired`), valid time edges (`x-time-edges`) | `test_specs/openapi.yaml` |
| **Generator** | EP: one valid class and one invalid class per way of failing; BVA: limit-1, limit, limit+1 for numbers and lengths. 80 inputs -> 409 cases (324 EP, 85 BVA). Output committed as JSON and checked equal to a fresh generation by a test | `scripts/generate_api_data.py`, `test_data/api_cases.json` |
| **Regeneration** | Changing `minimum` of capacity 1 -> 3 and title `maxLength` 254 -> 100 changes exactly those inputs' cases (0/1/2 -> 2/3/4; 253/254/255 -> 99/100/101) | `scripts/demo_regeneration.py`, `reports/api/regeneration_demo.txt` |
| **Harness** | Starts the app in a subprocess with a temporary SQLite DB, migrates, seeds, collects static, logs in through the real login form, sends the CSRF token from the cookie; reads the database directly (read-only) for post-conditions | `tests/team/api/support.py` |
| **Post-conditions** | After success: row counts change by exactly the expected amount; after rejection: unchanged; accepted capacity read back via REST | `test_generated_inputs.py` |
| **Business-rule and cross-workflow tests** | BR1, BR2, BR4 (below/at/above), no duplicate; WF1 changes show up in WF2 and the reverse (capacity, deadline, flow, delete, permissions) | `test_business_rules_api.py`, `test_cross_workflow_api.py` |
| **API coverage** | Counted from the spec: 14/14 operations, 46/46 documented responses, 80/80 inputs | `scripts/api_coverage.py`, `reports/api/api_coverage.md` |
| **Defects** | #12 rejections return 302 like success; #13 invalid limit/offset/ordering ignored; #14 inconsistent 403/405/401 and schema only 200. All minor, not fixed, tests assert the observed behaviour | issues #12 #13 #14 |

## 3. Likely questions and honest answers
- *Why one invalid value per request?* Otherwise a rejection cannot be attributed to a value; two invalid values can mask each other.
- *Why does a rejected signup return 302?* The application uses the Django messages framework: rule rejection redirects with a flash message. That is why the tests read the stored state back instead of trusting the status (issue #12).
- *Your first run had 29 failures. Were they defects?* No. They were my wrong assumptions (cross-field time order, a limit the app does not have, overlapping shifts of one volunteer, a wrong-case class for integers). I corrected spec, generator and tests from the real behaviour (`API_TESTING.md` section 4). I did not weaken any assertion to make a test pass.
- *Why are post-conditions needed?* After fixing the overlap problem I noticed invalid signup cases had passed for the wrong reason (they were rejected by the overlap rule, not by the invalid value). Counting stored rows before and after makes such mistakes visible.
- *Why not test BR5 over HTTP?* Not reachable: saving a shift activates its event, and an event without a shift has no signup. Covered at integration level (DEFECT-001).
- *Why is `search` unlimited in your spec?* My first spec said 254; the test failed, the application accepts any length; I corrected the spec (a wrong specification is a test-basis defect, not an application defect).
- *What does the lenient class mean?* `limit`, `offset`, `ordering` are ignored when invalid (200). The tests assert that as observed and issue #13 reports the inconsistency.
- *Is the custom signup window beyond the shift a defect?* Not claimed: the application accepts it; the only rule I could observe is start before end. It would need the product owner's decision.
- *What happens when two volunteers take the last place at the same moment?* `test_concurrency_api.py` sends both requests together five times. The stored state never exceeded the capacity. In the first run one request returned 500 with `database is locked`: SQLite has one writer at a time. I treat that as a limit of the test environment, say so in the test and the docs, and assert the stored state instead of hiding it.
- *What would you do differently?* Estimate effort beforehand, test concurrency on PostgreSQL, generate pairwise combinations of fields, and make `api-tests-black-box` a required check.
- *AI use?* Claude Code assisted; recorded in `AI_USE_RECORD.md`. Every test and document must be understood and defendable by the member (see section 4).

## 4. Live-task rehearsal
Example: *"maximum capacity must be at least 3"*: change `minimum` in `ShiftForm.maximum_number_of_participants` in `openapi.yaml`, run `generate_api_data.py` (cases become 2/3/4), run the tests: `test_committed_cases_match_a_fresh_generation` fails until the JSON is regenerated; against the unchanged application the new BVA case `2` expecting rejection fails (the app accepts 2), which is exactly the signal that the application or the spec has to change.
Example 2: *"decline never allowed"*: change `test_br2_decline_allowed_when_flag_set` expectation; the app still allows decline when the flag is set, so the test fails.

## 5. Commands cheat sheet
- Generate: `.venv\Scripts\python.exe scripts\generate_api_data.py`
- Tests: `$env:PYTHONPATH="src"; .venv\Scripts\python.exe -m pytest tests/team/api -q -p no:cacheprovider`
- Single file: add the file name; spec tests need no server (`test_spec_and_generator.py`)
- Coverage: `cd scripts; ..\.venv\Scripts\python.exe api_coverage.py`
- Demo: `cd scripts; ..\.venv\Scripts\python.exe demo_regeneration.py`
