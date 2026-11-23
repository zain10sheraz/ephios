# Reset the local Ephios test environment: fresh SQLite DB + seed data.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
Remove-Item data\db.sqlite3 -ErrorAction SilentlyContinue
New-Item -ItemType Directory data -Force | Out-Null
uv run python manage.py migrate --noinput | Select-Object -Last 1
uv run python scripts/seed_test_data.py
