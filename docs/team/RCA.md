# Root cause analysis (5 Whys + fishbone) for the two major defects

Evidence for every "why" below is a real artefact from our runs; where a statement is an inference it is marked *(inference)*.

---
## DEFECT-001 - Inactive event still accepts signup (issue #1, severity major, priority high) - FIXED in PR #2

**Problem statement:** a volunteer's POST to `/shifts/<id>/signup/` creates a participation on a deactivated event.

### 5 Whys
1. **Why did signup succeed?** `check_event_is_active` *returns* `ActionDisallowedError(...)` instead of raising it, and `BaseSignupActionValidator._get_errors` only collects *raised* errors. (`participant_validation.py:48`; test `test_event_inactive_blocks_signup`.)
2. **Why was it returned and not raised?** The line differs from every other checker, which all `raise`. A one-word slip *(inference: no git blame review done)*.
3. **Why was the slip never caught?** Upstream's own tests never executed that line: the baseline coverage run of upstream tests reported line 48 as **missing** (`participant_validation.py 91 %, Missing 48, 60, 141...`, Day 1 run).
4. **Why was it untested?** Inactive events are normally hidden from users by other layers (`ActiveManager`), so the validator branch looked redundant defence-in-depth *(inference)*; nobody wrote a test for the "direct POST to a hidden event" case.
5. **Why did no process catch it?** The checker contract ("signal errors by raising") is not enforced by types, lint or a contract test, and the project does not run mutation testing (our mutation run later showed the line as a masked survivor).

**Root cause:** an unenforced error-signalling contract combined with an untested defensive branch.

**Corrective action:** change `return` to `raise` (PR #2, commit 810c3906); regression tests unit + integration (before: 2 failed, after: 2 passed).
**Preventive actions:** (a) 100 % statement+branch coverage gate in CI; (b) custom mutation operator `team/RaiseToReturn` that targets exactly this slip class (all 10 valid mutants killed); (c) mutation-score gate >= 90 %; (d) recommended to upstream: a contract test that every registered checker raises.

### Fishbone (Ishikawa)
| Category | Contributing causes |
|---|---|
| Code | `return` instead of `raise` in one checker; inconsistent with siblings |
| Tests | line never executed by upstream tests; no negative test for inactive events |
| Design | error signalling relies on convention (exceptions collected by a loop), not types |
| Process | no mutation testing, no contract test, coverage not gated on this file |
| Environment/data | inactive events hidden from UI hides the path from manual testing |
| People | defensive code written without a failing test first *(inference)* |

---
## DEFECT-002 - ShiftForm raises KeyError (HTTP 500) on missing/invalid date or start_time (issue #4, severity major, priority medium) - FIXED in PR #5

**Problem statement:** POSTing the create-shift form with an empty or malformed date/start time gives HTTP 500 instead of a form error (live probe: 500 x4; valid input 302).

### 5 Whys
1. **Why HTTP 500?** An unhandled `KeyError: 'date'` / `'start_time'` is raised in `ShiftForm.clean_meeting_time/clean_start_time/clean_end_time` (`forms/events.py`, traceback at line 244).
2. **Why the KeyError?** When the `date` or `start_time` field fails its own validation, Django leaves it out of `cleaned_data`; the `clean_*` methods index it directly.
3. **Why do they assume it exists?** The three time fields are combined with the separate `date` field inside the field-level `clean_<field>` hooks, which implicitly depends on field order and on earlier fields being valid.
4. **Why did that go unnoticed?** The UI widgets (date picker, time inputs) make invalid values hard to enter, and upstream's form tests submit valid data through WebTest forms *(inference)*.
5. **Why were invalid inputs never tested?** No equivalence-partitioning/negative testing of form inputs exists upstream; our own EP/BVA tests on `ShiftForm` found it on the first invalid-input probe.

**Root cause:** a cross-field dependency inside field-level cleaners without a guard, plus the absence of negative-input tests.

**Corrective action:** guard each cleaner with `_require_valid_date()` and a start-time check that raise `ValidationError` (PR #5); regression tests (before: 4 failed, after: all pass); live server 500 -> 200.
**Preventive actions:** (a) EP test with one invalid value per input group for every form field (API tests, generator-driven); (b) Playwright exception flows that submit invalid dates; (c) team review rule: cross-field logic belongs in `clean()`.

### Fishbone (Ishikawa)
| Category | Contributing causes |
|---|---|
| Code | direct `cleaned_data[...]` indexing; cross-field logic in `clean_<field>` |
| Tests | only valid-input form tests upstream; no invalid-partition tests |
| Design | date and time split into separate fields combined later |
| Process | no input-validation checklist/EP technique in upstream review |
| Environment/data | UI widgets prevent invalid input in manual use, so it never surfaced |
| People | happy-path bias *(inference)* |

---
---
## DEFECT-003 - `is_minor` treats age 0 as unknown (issue #6, severity minor, priority low) - FIXED in PR #8
**Problem:** `AbstractParticipant.is_minor` returns False for a participant aged 0.
1. **Why?** `if age := self.get_age():` is falsy for 0, so the "known age" branch is skipped.
2. **Why that form?** The walrus assigns and tests in one step; the intent was "is the age known?".
3. **Why wrong?** Python truthiness conflates `0` and `None` for an optional number.
4. **Why unseen?** No test used the partition "age = 0" (BVA/EP around 0 and 18); real volunteers are never 0 years old.
5. **Why no such test?** Derived values were not partitioned systematically; our BVA test at 17/18 passed, only the age-0 partition exposed it.
**Root cause:** truthiness test on an optional numeric value plus a missing zero partition. **Corrective:** `age is not None and age < 18`. **Preventive:** explicit `is None` checks for optional numbers (review rule), zero partition in EP tables.
Fishbone: Code (truthiness), Tests (no zero partition), Design (optional number overloaded), Process (no EP checklist), Environment (no real data at age 0), People (concise idiom).

## DEFECT-004 - config-form fragment endpoints return HTTP 500 (issue #7, severity minor, priority low) - FIXED in PR #8
**Problem:** unknown slug or non-numeric `shift_id` on the two fragment endpoints raise an unhandled `ValueError` (live probe: 500 x4).
1. **Why 500?** `ValueError` from `signup_flow_from_slug` / `shifts.get(pk="abc")` is not caught in `AbstractShiftConfigurationFormView.get`.
2. **Why not caught?** The view assumes its parameters are valid.
3. **Why assumed?** The URLs are generated by the shift form's JavaScript, so they were treated as trusted internal input.
4. **Why no validation?** Only permission checks were considered for a helper endpoint.
5. **Why unseen?** UI-driven manual testing never sends crafted URLs; no invalid-parameter tests per endpoint existed.
**Root cause:** trust in client-generated parameters on an internal endpoint. **Corrective:** unknown slug -> `Http404`, malformed `shift_id` -> treated as new shift. **Preventive:** EP tests with one invalid value per parameter for every endpoint (Manan's generator-driven API tests), validate path/query parameters in views.
Fishbone: Code (unguarded lookups), Tests (no invalid-parameter tests), Design (internal-only assumption), Process (no endpoint checklist), Environment (JS hides the problem), People (happy-path bias).

---
## DEFECT-005..007 - API weaknesses found by area 2 (issues #12, #13, #14; all minor, open, not fixed)
**5 Whys (DEFECT-005, rejection returns 302):** 1. clients cannot tell success from rejection -> 2. both answer 302 -> 3. rejections are shown as flash messages after a redirect -> 4. the endpoints were built for the HTML UI, not as an API -> 5. no API contract was specified. **Root cause class:** API contract not specified (framework defaults relied on). Same class for #13 (paginator/ordering defaults ignore invalid values) and #14 (permission check before method check; schema generated from code, not reviewed).
**Fishbone categories:** Method (no contract), Machine (framework defaults), Material (generated schema lists only 200). **Corrective:** document the behaviour (done: `test_specs/openapi.yaml`); optional product decision to change status codes. Not fixed in code because it is design-level behaviour of the upstream HTML application; the tests assert the observed behaviour and read state back.

## Pareto of the four defects
By **category label** (GitHub labels): business-logic 2 (50 %), validation 2 (50 %).
By **root-cause class** (more informative):
| Root-cause class | Defects | Count | Share | Cumulative |
|---|---|---|---|---|
| Input / partition not handled (missing value, malformed value, zero) | DEFECT-002, 003, 004 | 3 | 75 % | 75 % |
| Unenforced error-signalling contract (`return` instead of `raise`) | DEFECT-001 | 1 | 25 % | 100 % |
By **severity:** major 2 (001, 002), minor 2 (003, 004). By **detection technique:** all four were suspected while reading the source to design white-box tests, then confirmed by an executed test (DEFECT-002 and DEFECT-004 additionally against the live server).
One root-cause class (input partitions not handled) explains three of four defects, which is why equivalence partitioning and invalid-value tests are the recommended preventive action. With only four defects the 80/20 pattern is indicative, not statistically meaningful; API/E2E/security/performance defects from teammates will be added when they exist.
