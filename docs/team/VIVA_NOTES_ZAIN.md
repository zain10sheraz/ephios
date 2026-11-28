# Viva notes - Area 1 (static analysis, white-box, mutation, CI) - Zain Sheraz

These notes help you explain and defend the work. Re-run things yourself before the viva; do not rely on this page alone.
Everything below is backed by files in the repository; none of it is invented.

## 1. One-minute story
Ephios = shift management for medical services. WF1: planners create events and shifts. WF2: volunteers sign up. They share the **Shift** record
(capacity, deadline, flow type). I wrote white-box unit and HTTP tests for both workflows, measured structural coverage, found four real defects,
checked test strength with mutation testing, and built a GitHub Actions gate that blocks bad pull requests.

## 2. Component by component

| Component | What to say | Where / how to rerun |
|---|---|---|
| **SonarQube** | Community 26.11 in Docker, scope = business-logic folders (the whole app froze this 7.7 GB laptop). Two runs: default profile found 0 issues, "comprehensive" profile 18 smells (13 are upstream's, 1 more joined with `forms/events.py`). Default quality gate FAILED (coverage 9.5 % of scope < 80 %): honest result, because only 16 modules are unit-tested | `docs/team/SONARQUBE.md`, `scripts/run_sonar.sh`, screenshots EV-005a/b |
| **Cyclomatic complexity** | V(G) = E - N + 2P = 14 - 10 + 2 = **6** for `check_participation_state`; also predicates + 1 = 5 + 1. SonarQube reports per file only (42 for the module), my AST counter matches Sonar exactly on `stats.py` (17) and is off by 2-3 on two files, reason unknown | `docs/team/CYCLOMATIC_COMPLEXITY.md`, `scripts/cyclomatic_ast.py` |
| **Unit tests and coverage** | 16 modules at 100 % statement AND branch (1,343 statements, 174 branches; 458 tests); no `pragma: no cover`; techniques: 3-point BVA (deadline, capacity, age, shift times), decision tables (decline rule, error routing), state transitions (participation states), EP | `docs/team/COVERAGE_SCOPE.md`, `powershell -File scripts/run_unit_coverage.ps1` |
| **MCC and MC/DC** | critical module `participant_validation.py`, every compound decision D1-D8. MCC = all condition combinations; MC/DC = pairs where one condition flips the outcome. Python short-circuits `and/or`, so some rows are unreachable: masking MC/DC used and stated | `docs/team/MCC_MCDC.md`, `tests/team/unit/test_mcc_mcdc*.py` |
| **Mutation** | Cosmic Ray (mutmut cannot fork on Windows). 1,079 mutants, 8 modules: 78.2 % -> 97.7 %. 235 survivors analysed: 210 killable (missing test / weak assertion), 23 equivalent, 2 unresolved. 3 custom operators (105 mutants). Key lessons: 100 % coverage still hid 235 gaps; Cosmic Ray labelled 35 real kills as 'incompetent' because of a Windows output-decoding crash, which I detected and corrected for | `docs/team/MUTATION.md`, `reports/mutation/survivor_analysis.csv` |
| **CI gate** | `.github/workflows/team-quality-gate.yml`, every PR: unit tests with 100 % coverage on the module list, Cosmic Ray kill rate >= 90 %, SonarQube thresholds (0 bugs/vulnerabilities/hotspots, <= 14 smells, <= 3 % duplication, 100 % coverage per file). No `continue-on-error`, no `|| true`; branch protection on `main` enforced for admins | `docs/team/CI_GATES.md` |
| **Blocked and fix PRs** | #3 blocked (tests fail without the fix; GitHub says BLOCKED). #2, #5, #8 fix PRs, each fails before / passes after. #2 and #5 were also blocked once by the Sonar threshold for real reasons (3 extra smells; file not in the Sonar scope) | PRs #2 #3 #5 #8, issues #1 #4 #6 #7 |
| **Defects** | #1 inactive event accepts signup (`return` instead of `raise`), major; #4 ShiftForm KeyError -> HTTP 500, major; #6 `is_minor` age 0 (falsy), minor; #7 fragment endpoints 500, minor. Root-cause class: input partition not handled (3 of 4) | `docs/team/RCA.md` (5 Whys, fishbone, Pareto) |

## 3. Likely questions and honest answers
- *Why is the mutation score not 100 %?* An equivalent mutant changes code but not behaviour, so no test can kill it; 23 are listed with reasons, and 2 more are honestly unresolved.
- *What is the 'incompetent' count?* Cosmic Ray crashed decoding the output of failed test runs (non-UTF-8 byte); all 35 crashes sat on the KILLED branch, so they are kills (`docs/team/MUTATION.md`).
- *Why not 100 % coverage of every file?* Scope is the business logic of two workflows; the rest (calendar rendering, event copy, bulk delete, disposition, alternative structures, REST layer) is justified in `COVERAGE_SCOPE.md`; I do not claim it.
- *What does MC/DC prove over MCC?* Each condition independently affects the outcome, with n + 1 tests instead of 2^n.
- *Why did the Sonar gate fail locally but pass in CI?* Different gates: the default gate needs 80 % coverage on new code; CI uses our custom thresholds (`check_sonar_gate.py`) justified from our measured evidence.
- *What would you do differently?* Estimate effort before starting (our estimates for area 1 are retrospective), run the heavy tools one at a time, and ask teammates to start earlier.
- *Are estimates and AI use honest?* Yes: estimates are labelled retrospective in `TEST_PLAN.md`; AI assistance (Claude Code) is recorded in `AI_USE_RECORD.md` and each test/doc must be understood and defendable by the member.

## 4. Live-task rehearsal (business-rule change)
Example: *"signup deadline is inclusive"* i.e. change `timezone.now() > last_time` to `>=` in `check_inside_signup_timeframe`.
Prediction: `test_br1_signup_until_boundary[exactly_at]` and `test_br1_end_time_is_limit_without_signup_until[exactly_at]` fail; the CI job
`unit-tests-100pct-coverage` fails first; `mutation-score` fails at its baseline step (tests must pass on unmutated code); `sonarqube-thresholds` fails at its coverage step.
To adapt: change the two boundary tests and the MC/DC/BVA table rows for BR1, rerun.
Example 2: *"capacity is exclusive"* (`>=` to `>` in `check_maximum_number_of_participants`): predicted failures `test_br4_*[at_max]`, D2 row tests in `test_mcc_mcdc.py`, `test_signup_beyond_capacity_is_rejected_and_count_stays`, cross-workflow capacity tests.
Practise: make the change on a branch, run `uv run pytest tests/team -q`, compare with your prediction, open a PR and read which job fails.

## 5. Commands cheat sheet (from the repo root, PowerShell/Git Bash)
- App: `powershell -File scripts/reset_env.ps1` then `.venv\Scripts\python.exe manage.py runserver 8000 --noreload`
- Tests: `.venv\Scripts\python.exe -m pytest tests/team -q -p no:cacheprovider`
- Coverage gate: `powershell -File scripts/run_unit_coverage.ps1`
- Mutation: `bash scripts/setup_mutation_workdir.sh`, then in `/c/mut_work`: `cosmic-ray init cosmic-ray.toml s.sqlite`, `cosmic-ray exec cosmic-ray.toml s.sqlite`, `cr-report s.sqlite`
- Sonar: `docker start sonarqube`, wait for UP, `bash scripts/run_sonar.sh`
