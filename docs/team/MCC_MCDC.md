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

## Limitation to state in the viva
Unique-cause MC/DC for A and B cannot be shown for these decisions because of short-circuit
evaluation; masking MC/DC is used and justified above.
