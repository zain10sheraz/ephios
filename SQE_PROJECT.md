# SE3002 Software Quality Engineering project - Ephios (team repository guide)

This repository is a fork of the open-source application **Ephios**. The upstream `README.md` is unchanged. All our own work is additive and lives in the
folders listed below; upstream source is modified only where a documented defect fix required it (see "Source changes").

## Upstream reference and baseline
| | |
|---|---|
| Application | Ephios, shift management for medical services (Python / Django) |
| Upstream | https://github.com/ephios-dev/ephios |
| Licence | MIT (`LICENSE`) |
| **Baseline commit** | `d12e76cd2b5b422177176506b0b6b9393dbc10e5` (2026-11-09), permanently referenced by the tag `baseline-upstream-d12e76cd` and by the history of `main` (`git merge-base --is-ancestor d12e76cd main`) |
| Fork (public) | https://github.com/zain10sheraz/ephios |
| Selected scope | module "events and signup": WF1 Event and Shift Management, WF2 Participant Signup (details: `docs/team/REQUIREMENTS.md`) |

## Team and branches
| Member | GitHub | Area | Branch |
|---|---|---|---|
| Zain Sheraz | zain10sheraz | 1: static analysis, white-box, mutation, CI | `zain` |
| Manan | MannanJafferyyy | 2: API testing, integration, OpenAPI, EP/BVA generator, cross-workflow validation | `manan` |
| Sujawal | sajawalkhan01 | 3: use cases, usability, accessibility, security, performance | `sajawal` |
Test management documents are shared. Branches are merged into `main` only through a pull request that must pass the quality gate.

**Merge status of `main` (2026-11-27):** all three areas are merged through pull requests that passed the required checks: Zain's area by PR #11, Manan's by #15, #16 and #28, Sujawal's by #24, #27 and #30, Zain's use cases and the completion report by #29. Pull request #3 is the deliberately blocked demonstration.

## Where things are
| Path | Content |
|---|---|
| `tests/team/` | **our tests** (`unit/`, `integration/`, `api/`, `e2e/`); upstream tests in `tests/` are not ours and earn no marks |
| `docs/team/` | requirements, test plan, risk register, traceability, RCA, MCC/MC-DC, mutation, coverage scope, CI gates, progress report, viva notes, AI-use record, evidence checklist |
| `scripts/` | seed/reset, coverage, Sonar, mutation workdir, complexity, live probes, gate checks (`gate_modules.txt` = modules under the 100 % gate) |
| `tools/team_mutation/` | custom Cosmic Ray operators based on our business rules |
| `mutation/` | Cosmic Ray configurations |
| `reports/` | real tool output: coverage, Sonar metrics, mutation data, defect before/after runs, evidence (`reports/evidence/`) |
| `.github/workflows/team-quality-gate.yml` | CI gate on every pull request |
| `sonar-project.properties` | SonarQube scope |

## Run it (Windows, PowerShell; Python 3.12, uv, Node 24)
    uv sync --all-extras
    Copy-Item .env.example .env                       # local, git-ignored
    uv run python manage.py generate_vapid_key
    uv run python manage.py collectstatic --noinput
    uv run python manage.py compilejsi18n             # compilemessages needs GNU gettext; UI falls back to English
    powershell -File scripts/reset_env.ps1            # fresh SQLite DB + synthetic test accounts (see docs/team/SETUP.md)
    .venv\Scripts\python.exe manage.py runserver 8000 --noreload

Test accounts (synthetic, local only): `planner@sqe.test` / `Planner#2026`, `volunteer@sqe.test` / `Volunteer#2026`, `volunteer2@sqe.test`, `admin@localhost` (superuser, setup only).

## Test, measure, mutate, gate
    .venv\Scripts\python.exe -m pytest tests/team -q -p no:cacheprovider      # all of our tests
    powershell -File scripts/run_unit_coverage.ps1                              # statement + branch coverage of the gate modules (must be 100 %)
    uv pip install cosmic-ray -e tools/team_mutation                            # mutation tooling (once)
    bash scripts/setup_mutation_workdir.sh                                      # isolated copy; the real tree is never mutated
    docker start sonarqube ; bash scripts/run_sonar.sh                          # SonarQube (needs about 3-4 GB RAM)
Full instructions and tool versions: `docs/team/SETUP.md`. Reset between runs: `powershell -File scripts/reset_env.ps1`.

## CI quality gate
On every pull request (`team-quality-gate`): (1) all team tests with 100 % statement+branch coverage of the modules in `scripts/gate_modules.txt`,
(2) Cosmic Ray kill rate >= 90 % on the critical module, (3) SonarQube thresholds (0 bugs/vulnerabilities/hotspots, <= 14 smells, <= 3 % duplication,
100 % coverage per gated file). No `continue-on-error` and no `|| true`. `main` is protected: the three checks are required, also for admins.
Thresholds and the real run history (including the pull requests the gate blocked): `docs/team/CI_GATES.md`.

## Source changes to upstream code (all via pull requests with failing-then-passing tests)
| Defect | Issue | PR | File |
|---|---|---|---|
| inactive event accepts signup | #1 | #2 | `src/ephios/core/signup/flow/participant_validation.py` |
| ShiftForm KeyError (HTTP 500) | #4 | #5 | `src/ephios/core/forms/events.py` |
| `is_minor` treats age 0 as unknown | #6 | #8 | `src/ephios/core/signup/participants.py` |
| config-form fragments return HTTP 500 | #7 | #8 | `src/ephios/core/views/shift.py` |
Pull request #3 is a deliberately blocked demonstration (the same tests without the fix) and is intentionally left unmerged.

## Honest status
See `docs/team/PROGRESS_REPORT_1.md`. Area 1 is complete; areas 2 and 3 (API, E2E, usability, security, performance) are tracked in the same report.
