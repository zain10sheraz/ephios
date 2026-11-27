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

## Areas 2 and 3: tools, versions and commands (added 2026-11-27)
| Tool | Version | Installed how | Used for |
|---|---|---|---|
| Playwright (Python) | 1.65.2 | `uv pip install playwright pytest-html` then `python -m playwright install chromium` (Chromium 159.0.8154.6) | browser tests, `tests/team/e2e/` |
| Playwright (Node) and `@axe-core/playwright` | 1.65.1 / 4.14.1 (axe-core 4.14.0) | `npm install playwright @axe-core/playwright` in `C:\sqe_tools`, then `npx playwright install chromium` | full axe scan, `scripts/axe_scan.mjs` |
| Lighthouse | 13.6.0 | `npm install lighthouse` in `C:\sqe_tools` | `scripts/run_lighthouse.py` |
| Grafana k6 OSS | 2.4.0 | release zip from github.com/grafana/k6 (no installer) | `scripts/k6_events_list.js` |
| pip-audit | 2.10.1 | `uv pip install pip-audit` | `python -m pip_audit --local` |
| OWASP ZAP | 2.17.0 | Docker image `ghcr.io/zaproxy/zaproxy:stable` (the official image; a local ZAP installation would do the same) | passive scan, `scripts/run_zap_passive.py` |
| SonarQube Community | 26.11 | Docker image `sonarqube:community` (a local installation from the zip would do the same) | static analysis, `scripts/run_sonar.sh` |
| requests, pytest, coverage | 2.34.2, 9.0.3, 7.17.2 | project environment | API tests, runner, coverage |
Docker is only a way to run SonarQube and ZAP without installing Java and the tools on Windows; the tools and their results are the same as a local installation.

Commands (PowerShell/Git Bash from the repository root, `PYTHONPATH=src` set):
    # API tests (start their own server on a temporary database): about 8-15 minutes
    python -m pytest tests/team/api -q -p no:cacheprovider
    # browser tests with the Playwright report
    python -m pytest tests/team/e2e -q -p no:cacheprovider --html=reports/e2e/playwright_report.html --self-contained-html
    # seeded server for audits (prints READY <url>), then axe and Lighthouse
    python scripts/serve_seeded.py ; node scripts/axe_scan.mjs <url> before|after ; python scripts/run_lighthouse.py <url|start> before|after ; python scripts/compare_accessibility.py
    # ZAP passive scan while the browser tests of both workflows run (Docker must be running)
    docker pull ghcr.io/zaproxy/zaproxy:stable ; python scripts/run_zap_passive.py ; python scripts/zap_summary.py
    # k6: one user and five users, each twice, 60 s per run (server running on <url>)
    k6 run -e BASE=<url> -e VUS=1 -e DURATION=60s --summary-export=reports/performance/k6_vus1_run1.json scripts/k6_events_list.js
    # dependency audit
    python -m pip_audit --local --format json -o reports/security/pip_audit.json
    # test data generator and its regeneration demo
    python scripts/generate_api_data.py ; python scripts/demo_regeneration.py
