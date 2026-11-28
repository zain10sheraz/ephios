# Scope of the 100 % white-box coverage claim, and justification of everything outside it

Rubric: "100 % statement and branch coverage of all server-side business logic; justify any uncovered code."
Measured with coverage.py (statement + branch) running only `tests/team` (our tests; upstream tests are never counted).
Module list that CI enforces: `scripts/gate_modules.txt` (single source for the workflow, the Sonar gate and the local script).

## 1. What "server-side business logic" means here
The code that implements the rules of our two workflows (WF1 event/shift management, WF2 participant signup):
validators and state rules, forms and their validation, models and their query/decision methods, the signup
view and signup flows, participants (age rules), and shift structures used by the selected `uniform` structure.

## 2. Inside the 100 % gate: 16 modules, 1,343 statements, 174 branches (re-measured 2026-11-25 with 458 tests, after the defect fixes), **100 % statement and 100 % branch**

| Module | Role | Statements | Branches |
|---|---|---|---|
| `core/signup/flow/participant_validation.py` | critical module: all signup rules (BR1-BR5) | 98 | 30 |
| `plugins/baseshiftstructures/structure/common.py` | capacity, min age, qualifications | 84 | 16 |
| `core/signup/stats.py` | SignupStats arithmetic | 34 | 2 |
| `core/forms/events.py` | WF1 event/shift forms and validation | 159 | 26 |
| `core/models/events.py` | Event/Shift/Participation models and visibility | 306 | 24 |
| `core/signup/views.py` | WF2 signup view (HTTP) | 109 | 24 |
| `core/signup/forms.py` | WF2 signup form | 112 | 28 |
| `core/signup/flow/base.py`, `flow/abstract.py` | flow contract and base behaviour | 63 + 44 | 10 + 0 |
| `core/signup/participants.py` | participants, age rules | 102 | 8 |
| `core/signup/fallback.py` | fallbacks for uninstalled plugins | 41 | 0 |
| `core/signup/structure/base.py`, `structure/abstract.py` | structure contract | 65 + 54 | 6 + 0 |
| `core/views/signup.py` | signup entry view | 22 | 2 |
| `plugins/basesignupflows/flow/participant.py`, `flow/manual.py` | the selected signup flows | 31 + 20 | 0 |

Evidence: `scripts/run_unit_coverage.ps1` output; CI job `unit-tests-100pct-coverage`; SonarQube per-file coverage check.

## 3. Outside the 100 % gate (measured with `tests/team`, 2026-11-24) and why

| Module | Measured | Why it is outside the gate | Residual risk |
|---|---|---|---|
| `core/views/event.py` (WF1 views) | 46 % stmt (create/edit/activate/delete covered by 32 HTTP tests in `test_wf1_http.py`) | Uncovered: the event **list/calendar rendering** (month grid, day view, CSS context) and **event copy with recurrence** (`EventCopyView`). Neither is among our requirements FR-01..FR-09; rendering is presentation logic best checked by browser tests | medium: calendar/copy bugs would not be caught; E2E tests (Sajawal) cover the list only |
| `core/views/shift.py` | 74 % (create/edit/delete, fragments covered) | Uncovered: **shift copy with recurrence** (`ShiftCopyView`) and a plugin-less error branch of shift creation (needs all signup-flow plugins disabled) | low |
| `core/views/bulk.py` | 39 % | bulk delete of events; outside the selected requirements | low |
| `core/signup/disposition.py` | 37 % | the responsible's **disposition** UI (assigning participants) is not WF2 self-service signup | medium: separate workflow |
| `plugins/baseshiftstructures/structure/named_teams.py`, `qualification_mix.py`, `group_common.py` | 45 % / 24 % / 49 % | alternative shift structures not selected (we use `uniform`); `named_teams` is exercised only through the signup form it adds | low for our scope |
| `plugins/basesignupflows/flow/coupled.py` | 52 % | "coupled" flow type, not selected | low |
| `api/filters.py`, `api/serializers.py`, `api/views/events.py`, `api/permissions.py` | 74 % / 87 % / 100 % / 91 % | REST layer is exercised by Manan's API tests (area 2), counted at the API level, not by our unit gate | to be re-measured when API tests exist |
| everything else (notifications, PDF, consequences, federation, guests, questionnaires, ...) | not measured here | outside the two workflows; upstream owns their tests | accepted |

## 4. Lines inside the gate modules that needed special treatment (none uncovered)
Defensive or plugin-only branches were reached with real tests, not excluded:
- abstract-method `raise NotImplementedError` lines: tested by calling the unbound methods;
- fallback/plugin-missing paths: tested by saving a shift with an uninstalled flow/structure slug;
- non-local participants (guests/federation): tested on `SignupView` internals and `request_to_participant`;
- "required signup field" quick-action branch: tested with the `named_teams` structure's required team choice;
- `-1` offsets etc. are not coverage issues (see `MUTATION.md` for equivalent mutants).
No `# pragma: no cover` or coverage exclusions were added to any file.

## 5. Honest limits
- 100 % coverage is a statement about executed lines and branches, not about correctness: mutation testing showed 92 gaps behind 100 % coverage (`MUTATION.md`).
- The WF1 list/calendar and copy features are untested by us; this is stated as a risk, not hidden.
- Four defects were found by the tests written for this scope (`RCA.md`, issues #1, #4, #6, #7).
