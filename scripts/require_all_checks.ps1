# Make all five team-quality-gate jobs required checks on main (run by the repository owner, needs admin rights).
# Usage: powershell -File scripts/require_all_checks.ps1
# Afterwards save a screenshot of Settings > Branches > main and export the rule:
#   gh api repos/zain10sheraz/ephios/branches/main/protection > reports/evidence/github/branch_protection_main.json
$body = @'
{
  "required_status_checks": {
    "strict": false,
    "contexts": [
      "unit-tests-100pct-coverage",
      "mutation-score",
      "sonarqube-thresholds",
      "api-tests-black-box",
      "e2e-browser-tests"
    ]
  }
}
'@
# (a PATCH with a piped body did not take on Windows PowerShell; adding the contexts directly works)
gh api -X POST repos/zain10sheraz/ephios/branches/main/protection/required_status_checks/contexts -f 'contexts[]=api-tests-black-box' -f 'contexts[]=e2e-browser-tests' | Out-Null
gh api repos/zain10sheraz/ephios/branches/main/protection/required_status_checks --jq ".contexts"
