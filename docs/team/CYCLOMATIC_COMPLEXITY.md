# Hand-calculated cyclomatic complexity

Function: `check_participation_state(shift, participant)` – `src/ephios/core/signup/flow/participant_validation.py:51-62`
(business rule BR3: state-change rule for participations).

## Source (line numbers relative to the function)
```
1  def check_participation_state(shift, participant):
2      participation = participant.participation_for(shift)
3      if participation is not None:                                   # D1
4          if (state == CONFIRMED                                      # D2
5              and not flow.user_can_decline_confirmed):               # D3 (short-circuit and)
6              raise DeclineDisallowedError
7          if state == RESPONSIBLE_REJECTED:                           # D4
8              raise ActionDisallowedError
9          if state == USER_DECLINED:                                  # D5
10             raise DeclineDisallowedError
11     (implicit return None)
```

## Control-flow graph (nodes = basic blocks)
- N1: lines 1-2 (entry, assignment)
- N2: `participation is not None`  (D1)
- N3: `state == CONFIRMED`  (D2)
- N4: `not user_can_decline_confirmed`  (D3)
- N5: raise Decline (line 6) → exit
- N6: `state == RESPONSIBLE_REJECTED`  (D4)
- N7: raise Action (line 8) → exit
- N8: `state == USER_DECLINED`  (D5)
- N9: raise Decline (line 10) → exit
- N10: exit / return None

Edges: N1→N2; N2→N3 (T), N2→N10 (F); N3→N4 (T), N3→N6 (F); N4→N5 (T), N4→N6 (F);
N5→N10; N6→N7 (T), N6→N8 (F); N7→N10; N8→N9 (T), N8→N10 (F); N9→N10.

E = 14 edges, N = 10 nodes, P = 1 component.

## Calculation
Formula 1: V(G) = E − N + 2P = 14 − 10 + 2 = **6**

Formula 2: predicate nodes + 1 = (N2, N3, N4, N6, N8) 5 + 1 = **6** ✔ (matches).

**Hand-calculated V(G) = 6**, i.e. 6 linearly independent paths:
1. participation None → return
2. not CONFIRMED, not REJECTED, not DECLINED → return (e.g. REQUESTED)
3. CONFIRMED and cannot decline → raise Decline
4. CONFIRMED and may decline → continue → return
5. REJECTED → raise Action
6. DECLINED → raise Decline

All six are exercised by `tests/team/unit/test_signup_rules.py` (BR2 decision table and BR3 tests).

## SonarQube comparison (real values, scan of 2026-11-23)
SonarQube reports cyclomatic complexity per **file**, not per function (no per-function value in its API).

| Check | Hand/AST value | SonarQube | Result |
|---|---|---|---|
| `check_participation_state` V(G) by CFG (E−N+2P) | **6** | n/a (file-level only) | – |
| Same function via `scripts/cyclomatic_ast.py` (Sonar-style counting) | **6** | n/a | equals hand value |
| `core/signup/stats.py` file total | 17 | **17** | exact match |
| `structure/common.py` file total | 36 | **34** | my count +2 |
| `participant_validation.py` file total | 45 | **42** | my count +3 |

Interpretation: the counting rule matches Sonar exactly on one file and over-counts by 2-3 on the others,
so Sonar evidently does not count some construct I count (not identified; likely nested/closure or
`not`-chain handling). The hand-calculated function value (6) is derived from the CFG independently of
either tool. We do not claim a per-function Sonar match because Sonar does not expose one.
