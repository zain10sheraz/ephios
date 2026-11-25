# Mutation testing (Cosmic Ray 8.9.0) - final, eight modules, 1,079 mutants

Tool choice: Cosmic Ray. mutmut needs `fork()` and does not run on native Windows; Cosmic Ray runs here and supports custom operators.
Method: mutants run in an isolated copy of the repo (`scripts/setup_mutation_workdir.sh`) so the real tree is never mutated. Each module is mutated with the unit/HTTP tests that cover it
(`mutation/cosmic-ray-<module>.toml`), using a reusable on-disk test DB (`tests/team/settings_mutation.py`). Round 1 runs all mutants against the tests as they were; killer tests are then
written for every survivor and only the survivors are rerun (valid because tests were only added: a killed mutant stays killed).
Raw data (all real): `reports/mutation/round{1,2}_*.jsonl|sqlite`; per-mutant analysis of **every** round-1 survivor: `reports/mutation/survivor_analysis.csv`
(`scripts/build_survivor_table.py`); the tables below are produced by `scripts/mutation_summary.py`.

## A tool artefact that changes how "incompetent" must be read
Cosmic Ray labels a mutant INCOMPETENT when its worker crashes. In our runs **all 35 incompetent mutants** (every session) crashed in the same place: decoding the pytest output
of a test run that had **failed** (`UnicodeDecodeError`, a non-UTF-8 byte such as the umlaut in "Rettungssanitaeter" from the Windows console). The traceback lies on the
`TestOutcome.KILLED` line in all 35, and none was on the SURVIVED line. They are therefore real kills and are counted as killed
(`mutation_summary.py`, `check_mutation_score.py`, `build_survivor_table.py` all apply the same rule). Earlier interim figures in this project excluded them and were slightly too low;
this document supersedes them. CI runs on Linux with UTF-8 and is not affected. Kill rate = killed / (killed + survived + timeout).

## Results
| Module | Mutants | Round 1 (before killer tests) | Final (after killer tests) |
|---|---|---|---|
| `core/signup/flow/participant_validation.py` | 117 | 107 killed, 10 survived -> 91.5 % | 115 killed, 2 survived -> **98.3 %** |
| `plugins/baseshiftstructures/structure/common.py` | 165 | 123 killed, 42 survived -> 74.5 % | 156 killed, 9 survived -> **94.5 %** |
| `core/signup/stats.py` | 133 | 93 killed, 40 survived -> 69.9 % | 133 killed, 0 survived -> **100.0 %** |
| `core/forms/events.py` (WF1) | 136 | 115 killed, 21 survived -> 84.6 % | 134 killed, 2 survived -> **98.5 %** |
| `core/signup/views.py` | 38 | 24 killed, 14 survived -> 63.2 % | 35 killed, 3 survived -> **92.1 %** |
| `core/signup/participants.py` | 88 | 84 killed, 4 survived -> 95.5 % | 87 killed, 1 survived -> **98.9 %** |
| `core/signup/forms.py` | 101 | 70 killed, 31 survived -> 69.3 % | 99 killed, 2 survived -> **98.0 %** |
| `core/models/events.py` | 301 | 228 killed, 73 survived -> 75.7 % | 295 killed, 6 survived -> **98.0 %** |
| **Total** | **1,079** | 844 killed, 235 survived -> **78.2 %** | 1,054 killed, 25 survived -> **97.7 %** |

All eight modules were already at **100 % statement and branch coverage** before round 1. Even so, 235 behavioural gaps existed: coverage shows that a line ran, mutation shows whether a test would notice if it were wrong.
Final rounds took 2-3 passes for some modules (a first killer test sometimes used data on which the mutated and original code agree; the survivor was investigated and the test strengthened).

## Custom operators (`tools/team_mutation/`), 105 mutants over the eight modules
| Operator | Business rule | Mutants | Round 1 outcome |
|---|---|---|---|
| `team/RaiseToReturn` | error signalling (the DEFECT-001 class) | 27 | 25 killed, 2 survived (both killed after the tests were strengthened) |
| `team/StateConstantSwap` | BR3 participation states | 72 | 64 killed, 8 survived (the default `state` of a new participation, untested; killed afterwards) |
| `team/RuleBoundaryShift` | BR1/BR4/age boundaries | 6 | 6 killed |
The two `RaiseToReturn` survivors were `raise ValidationError` -> `return ValidationError` in `EventTypeForm.clean_color` (the model's `max_length` check still made the form invalid, so a test asserting only `is_valid()` could not tell; asserting the message killed it)
and `raise NotImplementedError` in `AbstractParticipation.participant` (a `str()` test only asserted a truthy value). Both are weak assertions of the same slip class as DEFECT-001, so the operator proved useful.
The operators are narrow (RuleBoundaryShift matched only 6 comparisons); most survivors came from generic core operators.

## Analysis of all 235 round-1 survivors (full per-mutant table: `survivor_analysis.csv`)
| Category | Count | Meaning |
|---|---|---|
| Killable - missing test or weak assertion | 210 | killed in the final rounds by the tests named in the CSV rationale |
| Equivalent | 23 | still alive after targeted tests; each justified below or in the CSV |
| Unresolved | 2 | still alive; **not proven equivalent** (see below) |

Root causes of the 210 (feeds the defect/RCA section): (1) tests used zeros and tiny numbers where bitwise operators equal addition (1+2 = 1|2 = 1^2) - all 40 `stats.py` survivors and several more;
(2) form and model fields never tested at their limits or empty (max_length, null, blank, defaults, persisted enum values) - the test database is built from migrations, so changes to model fields are invisible until `full_clean` or the field metadata is asserted;
(3) side effects never asserted (the customise notification to the responsibles: 9 survivors on one line; comment visibility; atomic saves; the rule that a participation grants event view access: 14 mutants);
(4) default parameters never exercised because callers pass every argument; (5) one participation state tested where the code distinguishes five; (6) assertions of validity or page title instead of the specific result;
(7) mutation test commands that did not include a unit test that already covered the behaviour (11 form survivors).

### Equivalent survivors (23)
| Module:line | Mutation | Why equivalent |
|---|---|---|
| participant_validation:47 (x2) | negate `if not shift.event.active` | **Masked by DEFECT-001** while the checker returned instead of raised; killed in CI after the fix (118/118) |
| structure_common:14, 83, 84, 134, 176 (x3), 177 (x3) | typing switch; `-1` offsets clamped by `max`/`range`; removing `@staticmethod`; `list * n` with n <= 0 | clamped / never bound / empty list either way (details in the CSV) |
| forms/events:168, 267 | `flat=False` inside a subquery; `<=` -> `<` on a key set | Django uses the single column either way; the sets are never equal |
| signup/views:81, 82 | `or` -> `and` on quick-action defaults | those individual times only reach plugin signal receivers and are ignored by the core flows |
| signup/views:142 | `==` -> `<=` | "customize" is the alphabetically smallest valid choice, so `<=` behaves like `==` |
| participants:115 | remove `@dataclass` on `PlaceholderParticipant` | it adds no fields; behaviour is inherited |
| signup/forms:61, 144 | unused `commit` default; `!=` -> `is not` | parameter is never used; CPython interns both strings |
| models/events:200, 203 | `\|` -> `^` between event-type conditions | one event type cannot be INSTANCE_USERS and PUBLIC (or PUBLIC and CONFIRMED) at once |
| models/events:542 (x2) | `!=` -> `is not` / `<` | small ints are interned; GETTING_DISPATCHED (4) is the largest state value |
Equivalence is argued by reading the code, not formally proven. Two earlier equivalence guesses were wrong and were corrected by evidence (forms/events lines 212 and 226 turned out killable).

### Unresolved survivors (2) - stated honestly
`models/events.py` lines 207 and 209: `|` -> `^` between the "responsible user" and "may view user profiles" terms of `Participation.viewable_by`. The targeted tests (a responsible planner and a user manager
viewing participants of an event whose setting already shows everything) pass even with the mutant. We did not establish why (Django's XOR over these joined query terms returned the same rows in our scenario). They are **neither killed nor proven equivalent** and are listed as residual risk.

## CI gate threshold (justified from this evidence)
Gate: kill rate on `participant_validation.py` >= **90 %** (`scripts/check_mutation_score.py --min 90`, job `mutation-score`). Local rounds gave 91.5 % then 98.3 %, and CI after the DEFECT-001 fix 100 % (118/118).
90 % blocks a real regression (deleting a killer test drops below) without failing on equivalent mutants; a 100 % gate would be impossible because equivalent mutants exist.

## Limitations
- Mutation covers 8 of the 16 modules under the coverage gate (1,079 mutants; about 1-3 minutes per mutant at worst on this 7.7 GB laptop). Not mutated: `core/signup/flow/base.py`, `flow/abstract.py`, `fallback.py`, `structure/base.py`, `structure/abstract.py`, `core/views/signup.py` and the two selected signup flows.
- Equivalence of the 23 survivors is argued, not proven; 2 are unresolved.
- Cosmic Ray core operators were used unfiltered; some mutants (e.g. bit-shift for `+`) are unrealistic.
- One tool artefact (decode crash) had to be worked around in the evaluation, as described above.
