# Runs team tests with statement+branch coverage on the signup business-logic modules.
Set-Location (Split-Path $PSScriptRoot -Parent)
$inc = (Get-Content scripts/gate_modules.txt | Where-Object { $_.Trim() }) -join ","
uv run coverage run --include=$inc -m pytest tests/team --ignore=tests/team/api --ignore=tests/team/e2e -q -p no:cacheprovider
uv run coverage report -m
uv run coverage html -d reports/coverage_unit_html
