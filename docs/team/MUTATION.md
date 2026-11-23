# Mutation testing (Cosmic Ray 8.9.0) - INTERIM, round 1 complete, round 2 not yet run

Tool: Cosmic Ray (mutmut needs `fork()`, not available on native Windows). Runs in an isolated copy (`scripts/setup_mutation_workdir.sh`).
Test command: `tests/team/unit` rules + coverage + MCC + killer tests, reusable on-disk test DB (`tests/team/settings_mutation.py`).
Operators: all core operators + 3 custom operators (`tools/team_mutation/`): `team/RaiseToReturn`, `team/StateConstantSwap`, `team/RuleBoundaryShift`.
Raw data (real): `reports/mutation/round1_*.jsonl|sqlite`.

## Round 1 results (before the killer tests)
Kill rate = killed / (killed + survived + timeout); "incompetent" (invalid mutant code) excluded.

| Module | Mutants | Killed | Survived | Incompetent | Kill rate |
|---|---|---|---|---|---|
| `core/signup/flow/participant_validation.py` | 117 | 106 | 10 | 1 | **91.4 %** |
| `plugins/baseshiftstructures/structure/common.py` | 165 | 119 | 42 | 4 | **73.9 %** |
| `core/signup/stats.py` | 133 | 93 | 40 | 0 | **69.9 %** |
| Total | 415 | 318 | 92 | 5 | 77.6 % |

All mutants produced by our three custom operators in `participant_validation.py` were killed (8 RaiseToReturn, 16 StateConstantSwap, 1 RuleBoundaryShift); they did not appear among the survivors.
Statement/branch coverage was already 100 % on all three modules, so these survivors show where 100 % coverage still left behaviour unchecked.

## Survivor analysis done so far (52 of 92 classified)
`participant_validation.py` (10) - 2 equivalent, 8 killable:
- L47 (2): `if not shift.event.active` negation. **Equivalent relative to DEFECT-001**: the checker `return`s instead of `raise`s, so its result is discarded; becomes killable once the defect is fixed.
- L55 (3), L61 (1): `state == X` comparison changed (>=, is not, <=). **Missing test / weak assertion**: no test with a state other than CONFIRMED while decline is forbidden; GETTING_DISPATCHED only asserted on sign-up, not decline.
- L85 (1), L101-102 (2), L119 (1): defaults of `get_conflicting_participations` / `user_can_customize_signup_times`. **Missing test**: only ever called with all arguments.
- Killer tests: `tests/team/unit/test_mutation_killers.py` (11 tests, pass on unmutated code).

`structure/common.py` (42): 15 + 27 analysed - 34 killable (missing tests, weak assertions, e.g. event-detail test only asserted the title; XOR coincidence 3^1 = 3-1), 8 expected equivalent:
- L14 `typing.TYPE_CHECKING` switch (typing-only), L134 `@staticmethod` removal (method always called via the class), L177 `<` -> `<=`/`!=`/`is not` (`list * n` with n <= 0 is empty), L83/L176 `-1` offsets (`range(-1)` / `max(-1, x)` behave like 0).
- Killer tests: `tests/team/unit/test_mutation_killers_structure.py` (29 tests, pass on unmutated code).
- "Expected equivalent" will be confirmed by round 2: if they still survive after targeted tests they are equivalent.

`stats.py` (40): **not analysed yet.**

## Round 2 plan (tomorrow)
1. Sync `tests/team` into `C:\mut_work`.
2. Copy each round-1 session, delete only the SURVIVED results, `cosmic-ray exec` reruns just those (valid because tests were only added, so killed mutants stay killed).
3. Report before/after kill rates; classify what still survives as equivalent with justification.
4. Add tests for `stats.py` survivors, analyse, rerun.
5. Commit final score; gate threshold in CI is 90 % on `participant_validation.py` (round 1 = 91.4 %).
