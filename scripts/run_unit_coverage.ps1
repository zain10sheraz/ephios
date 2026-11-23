# Runs team tests with statement+branch coverage on the signup business-logic modules.
Set-Location (Split-Path $PSScriptRoot -Parent)
$inc = "src/ephios/core/signup/flow/participant_validation.py,src/ephios/plugins/baseshiftstructures/structure/common.py,src/ephios/core/signup/stats.py"
uv run coverage run --include=$inc -m pytest tests/team -q -p no:cacheprovider
uv run coverage report -m
uv run coverage html -d reports/coverage_unit_html
