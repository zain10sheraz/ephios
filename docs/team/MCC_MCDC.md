# MCC and MC/DC – critical module (signup validation)

Module: `src/ephios/plugins/baseshiftstructures/structure/common.py` (+ `participant_validation.py`).
Executable tests: `tests/team/unit/test_mcc_mcdc.py` (15 tests, all pass on 2026-11-23).

## D1 – `check_participant_age`  (raise ⇔ A ∧ B ∧ C)
A = `minimum_age is not None`, B = `age is not None`, C = `age < minimum_age`

Full MCC has 2³ = 8 combinations. Python short-circuits `∧`, so C is only evaluated when A and B are
true. When A is false, C cannot even be formed (`age < None` raises `TypeError`, verified in
`test_d1_infeasible_mcc_rows_are_really_not_formable`). The 8 combinations therefore collapse to
4 executable rows (the other 4 are infeasible / equivalent to a row below):

| Row | A | B | C | Outcome | Test input (minimum_age, age) |
|---|---|---|---|---|---|
| D1-1 | F | – | – | no error | (None, 30)  — covers FFF, FFT, FTF, FTT |
| D1-2 | T | F | – | no error | (18, None)  — covers TFF, TFT |
| D1-3 | T | T | F | no error | (18, 18) |
| D1-4 | T | T | T | **raise** | (18, 17) |

MC/DC (masking form; unique-cause pairs for A and B are infeasible because of short-circuit/undefined C):

| Condition | Pair (rows) | Differs in | Outcome flips |
|---|---|---|---|
| A | D1-1 vs D1-4 | A (B, C masked in D1-1) | no error → raise |
| B | D1-2 vs D1-4 | B (C masked in D1-2) | no error → raise |
| C | D1-3 vs D1-4 | C only (unique-cause) | no error → raise |

Minimum test set for MC/DC = n + 1 = 4 rows (= D1-1..D1-4).

## D2 – `check_maximum_number_of_participants`  (raise ⇔ A ∧ B ∧ C)
A = `not signup_flow.uses_requested_state`, B = `maximum_number_of_participants is not None`,
C = `confirmed_count >= maximum_number_of_participants`  (A∧B is the outer `if`, C the nested `if`).

| Row | A | B | C | Outcome | Test input (uses_requested, maximum, confirmed) |
|---|---|---|---|---|---|
| D2-1 | F | – | – | no error | (True, 2, 5) |
| D2-2 | T | F | – | no error | (False, None, 5) |
| D2-3 | T | T | F | no error | (False, 2, 1) |
| D2-4 | T | T | T | **raise** | (False, 2, 2) |

Pairs: A = D2-1/D2-4, B = D2-2/D2-4, C = D2-3/D2-4 (same structure as D1).

## Complete coverage of the critical module `participant_validation.py`
Every compound decision of the module (found by listing all `and`/`or`/`not`/`if` in the source) is tabulated below.
Executable tests: `tests/team/unit/test_mcc_mcdc_validation.py` (17 tests, pass). Rows that differ only in a condition that
short-circuiting never evaluates are one input and are marked `-`.

### D3 `check_participation_state` (L54-56): raise Decline  <=>  A and B
A = `state == CONFIRMED`, B = `not user_can_decline_confirmed`. Full MCC (4 rows, all feasible):

| Row | A | B | Input (state, flag) | Outcome |
|---|---|---|---|---|
| D3-TT | T | T | CONFIRMED, False | **raise** |
| D3-TF | T | F | CONFIRMED, True | ok |
| D3-FT | F | T | REQUESTED, False | ok |
| D3-FF | F | F | REQUESTED, True | ok |

MC/DC (unique cause): A = D3-FT/D3-TT, B = D3-TF/D3-TT.

### D4 `can_sign_up` signupable state (L182): A or B
A = `participation is None`, B = `not participation.is_in_positive_state()`. (T,-) fixes B (no participation to inspect), so the 4 MCC rows reduce to 3.

| Row | A | B | Input | Outcome |
|---|---|---|---|---|
| D4-T- | T | - | no participation | True |
| D4-FF | F | F | positive state (REQUESTED/CONFIRMED) | False |
| D4-FT | F | T | non-positive state | True |

MC/DC: A = D4-FF/D4-T- (masking), B = D4-FF/D4-FT (unique cause).

### D5 `can_sign_up` result (L184): C and D
C = signupable_state, D = `not get_signup_errors()`.

| Row | C | D | Outcome |
|---|---|---|---|
| D5-TT | T | T | True |
| D5-TF | T | F | False |
| D5-F- | F | - | False (errors not evaluated) |

MC/DC: C = D5-F-/D5-TT, D = D5-TF/D5-TT (unique cause).

### D6 `can_customize_signup` positive state (L197): A and B
A = `participation is not None`, B = `is_in_positive_state()`. Observed through the branch taken (can_decline False, no errors: positive branch gives False, the other True).

| Row | A | B | Input | Outcome |
|---|---|---|---|---|
| D6-F- | F | - | no participation | True |
| D6-TF | T | F | non-positive | True |
| D6-TT | T | T | positive | False |

MC/DC: A = D6-F-/D6-TT (masking), B = D6-TF/D6-TT (unique cause).

### D7 `can_customize_signup` result in the positive branch (L202): X and Y
X = `can_decline()`, Y = `not get_signup_errors()`.

| Row | X | Y | Outcome |
|---|---|---|---|
| D7-TT | T | T | True |
| D7-TF | T | F | False |
| D7-F- | F | - | False |

MC/DC: X = D7-F-/D7-TT, Y = D7-TF/D7-TT.

### D8 default expressions `start_time or shift.start_time`, `end_time or shift.end_time` (L101-102)
Value-level `or` with two feasible inputs each (argument given / None); covered by `test_explicit_start_time_is_used_not_shift_start`, `test_explicit_end_time_is_used_not_shift_end` and the default-argument test (mutation survivors killed).

### Error-class routing (decision table, 6 classes x 3 queries)
| Error class | in signup errors | in decline errors | in action errors |
|---|---|---|---|
| SignupDisallowedError | yes | no | yes |
| ParticipantUnfitError | yes | no | yes |
| DeclineDisallowedError | no | yes | yes |
| ActionDisallowedError | yes | yes | yes |
| ImproperlyConfiguredError | yes | yes | yes |
| BaseSignupError | no | no | yes |

All 18 cells asserted in `test_error_class_routing_decision_table`.

### Summary of the critical module
D1/D2 (common.py: age, capacity) and D3-D8 (participant_validation.py) = every compound decision has a full or feasibility-reduced MCC table with executable tests, and MC/DC pairs for every condition.
Where a condition could not be varied independently, the table says so.

## Limitation to state in the viva
Unique-cause MC/DC for A and B cannot be shown for these decisions because of short-circuit
evaluation; masking MC/DC is used and justified above.
