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
