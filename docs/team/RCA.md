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
## Pareto by category (all defects found so far)
| Category | Defects | Share |
|---|---|---|
| business-logic | 1 (DEFECT-001) | 50 % |
| validation | 1 (DEFECT-002) | 50 % |

Only 2 defects exist, so the Pareto "80/20" shape cannot be claimed yet; the table will be regenerated from GitHub issue labels when API/E2E/accessibility/security/performance defects are added. Defects found by area so far: white-box/unit (2).
