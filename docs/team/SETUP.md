# SQE Project – Setup (Windows, PowerShell)

Upstream: https://github.com/ephios-dev/ephios (MIT)
Baseline commit: d12e76cd2b5b422177176506b0b6b9393dbc10e5 (2026-11-09)
Tool versions: Python 3.12.10, uv, Node 24.15.0, Django 5.2.17

## Install
    uv sync --all-extras
    Copy-Item .env.example .env        # local only, git-ignored
    uv run python manage.py generate_vapid_key
    uv run python manage.py collectstatic --noinput
    uv run python manage.py compilejsi18n
(`compilemessages` needs GNU gettext `msgfmt`, not installed here; the UI falls back to English.)

## Seed / reset (fresh SQLite DB + synthetic accounts)
    powershell -File scripts/reset_env.ps1

## Run
    uv run python manage.py runserver 8000 --noreload   # http://localhost:8000

## Test accounts (synthetic)
| Role | Email | Password |
|---|---|---|
| Superuser (setup only) | admin@localhost | admin |
| Planner | planner@sqe.test | Planner#2026 |
| Volunteer | volunteer@sqe.test | Volunteer#2026 |
| Volunteer 2 | volunteer2@sqe.test | Volunteer#2026 |

## Verified on 2026-11-23
- migrate OK, reset_env.ps1 OK, /accounts/login/ 200, /api/events/ 403 unauthenticated, /api/schema/ 200

## Test tooling (added 2026-11-24)
Tool versions: pytest 9.0.3, pytest-django 4.14.0, coverage 7.17.2, Cosmic Ray 8.9.0, ruff (project dev dependency), SonarQube Community 26.11 (Docker `sonarqube:community`, scanner `sonarsource/sonar-scanner-cli`), GitHub Actions on ubuntu-latest.

    # install extras used by our tests (outside upstream's pyproject)
    uv pip install cosmic-ray -e tools/team_mutation
    # unit + HTTP tests, then the 100 % gate over scripts/gate_modules.txt
    .venv\Scripts\python.exe -m pytest tests/team -q -p no:cacheprovider
    powershell -File scripts/run_unit_coverage.ps1
    # mutation (isolated copy in C:\mut_work; real tree is never mutated)
    bash scripts/setup_mutation_workdir.sh
    #   then in /c/mut_work:  cosmic-ray init cosmic-ray.toml s.sqlite ; cosmic-ray exec cosmic-ray.toml s.sqlite ; cr-report s.sqlite
    # SonarQube (needs Docker, about 3-4 GB RAM; stop it afterwards)
    docker start sonarqube ; bash scripts/run_sonar.sh ; python scripts/check_sonar_gate.py http://127.0.0.1:9000 <token>
Secrets (`data/sonar.env`, `.env`) are git-ignored.
Live probes of defects against the running app: `scripts/probe_shift_form_live.py`, `scripts/probe_config_fragments_live.py` (run after `scripts/reset_env.ps1` and `manage.py runserver`).
