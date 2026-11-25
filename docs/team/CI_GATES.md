# CI quality gate (GitHub Actions) - thresholds, justification and real run history

Workflow: `.github/workflows/team-quality-gate.yml`, trigger: every `pull_request`. No `continue-on-error`, no `|| true`.
Branch protection on `main` (set 2026-11-24): required checks `unit-tests-100pct-coverage`, `mutation-score`,
`sonarqube-thresholds`; **enforced for admins**; force pushes and deletions disallowed.
`zain`, `manan`, `sajawal` are deliberately unprotected working branches (protecting them would reject direct pushes from members);
the final merge into `main` must pass the gate.

## Gates and why these thresholds
| Job | Gate | Threshold | Justification (from our own evidence) |
|---|---|---|---|
| unit-tests-100pct-coverage | team tests pass; statement+branch coverage of 16 business-logic modules listed in `scripts/gate_modules.txt` (rationale: `COVERAGE_SCOPE.md`) | 100 % | We reached 100 % (EV-001); the assignment targets 100 % of business logic; anything lower means untested rule code |
| mutation-score | Cosmic Ray kill rate on `participant_validation.py` | >= 90 % | Local rounds 91.5 % then 98.3 %, CI after the fix = 100 % (118/118). 90 % blocks a real regression (deleting a killer test drops below) but tolerates equivalent mutants; 100 % would be unachievable in general |
| sonarqube-thresholds | bugs, vulnerabilities, hotspots | 0 | none exist in scope |
| | code smells | <= 14 | all 14 smells are upstream-owned code in scope; our own code must add none (ratchet). History: 18 -> 13 after we fixed our own smells -> 14 when `forms/events.py` joined the Sonar scope (its one smell, `not a <= b` at line 267, is upstream's, confirmed with `git blame` and a local scan) |
| | duplicated lines | <= 3 % | measured 0.5 % |
| | line coverage of the 16 modules | 100 % each | same as the unit gate, measured independently by Sonar |

## Real run history (all on https://github.com/zain10sheraz/ephios)
| When (UTC, 2026-11-24) | PR | Result | What it shows |
|---|---|---|---|
| 13:40 | #2 fix (base `zain`), run 45405890738 | unit **pass** (50 s), mutation **pass** (8m27s, 118/118 killed), sonar **FAIL**: `code_smells = 21 (max 18)` | **The gate blocked a real problem**: the killer tests I added had 3 more Sonar smells (composite assertions). Fixed by splitting the assertions (commit 84d59b33), threshold tightened to 13 |
| 14:04-14:09 | #2 after fix | all three **pass** (unit 54 s, mutation 7m09s, sonar 1m47s) | PR #2 merged into `zain` (merge commit d78cb5a7) |
| 14:00-14:10 | #3 demo (base `main`) | all three **FAIL**; GitHub `mergeStateStatus = BLOCKED` | Same tests, fix withheld: 2 tests fail (`2 failed, 135 passed`); mutation job fails at `cosmic-ray baseline` (tests must pass on unmutated code); sonar job fails at its coverage step. PR #3 is intentionally left open and unmerged |

### "Fails before, passes after" for the documented fix (DEFECT-001, issue #1)
- Before: `reports/defect001_before_fix.txt` -> 2 failed (also CI on PR #3).
- After: `reports/defect001_after_fix.txt` -> 2 passed; PR #2 all green; issue #1 closed with the evidence.
- Mutation side-effect confirming the root cause: the 2 equivalent-looking survivors on line 47 (`if not shift.event.active`) were killed in CI once the defect was fixed (118/118), as predicted in docs/team/MUTATION.md.

## Observations / limitations
- Upstream's own workflows (`lint`, a 12-job `test` matrix, CodeQL) also run on PRs to `main` and are NOT required checks. On PR #3 they failed (tests: because our new tests fail; `lint`: our files broke upstream's ruff rules - 9 files to reformat, 16 findings). **We fixed the ruff findings afterwards** (commit following 84d59b33) so the final PR to `main` is not red for style.
- The 100 % gate covers 16 modules (WF2 signup validation, view, form, flows, participants; WF1 event/shift forms and models). WF1 list/calendar and copy views, REST serializers and alternative plugins are outside it and justified in `COVERAGE_SCOPE.md`.
- CI timings: unit 50-54 s, sonar 1m47-2m20, mutation 7-8.5 min (runner is faster than the local machine).
- The Sonar gate script (`scripts/check_sonar_gate.py`) is custom because a SonarQube Community server in CI starts with the default gate, which fails on first analysis (as seen locally: coverage 9.5 % < 80 %).

## PR #5 run history (DEFECT-002 fix)
| Run | Result | Cause |
|---|---|---|
| 1 | sonar FAIL: `coverage forms/events.py = None` | gate required coverage of a file that was not in `sonar.sources` (our configuration slip, caught by the gate) |
| 2 | sonar FAIL: `code_smells = 14 (max 13)` | scope now included upstream `forms/events.py` with 1 upstream smell; ratchet raised to 14 with the justification above |
Unit tests passed (1m) and mutation passed (10m39s) in both runs.

## PR #8 run (DEFECT-003 + DEFECT-004 fix, first run on the 16-module gate)
All three checks passed on the first run: unit-tests 1m19 (16 modules at 100 %), sonarqube-thresholds 2m44 (smells still <= 14: the new test files added none after the pre-emptive cleanup), mutation-score 9m03. PR #8 merged into `zain`; issues #6 and #7 closed. The coverage list now lives in one file (`scripts/gate_modules.txt`) read by the workflow, the Sonar gate script, `sonar-project.properties` and the local script, so they cannot drift apart.
