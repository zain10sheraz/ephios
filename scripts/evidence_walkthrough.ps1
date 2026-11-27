# Guided evidence run. YOU take every screenshot (course rule); this script only runs the commands, one at a time,
# shows the exact file name to use, and waits for you.
#
# Run from PowerShell (does not change git, only runs the project's own commands):
#   powershell -ExecutionPolicy Bypass -File C:\ephios_sajawal\scripts\evidence_walkthrough.ps1 -Phase A
# Phases: A = terminal (no server), B = browser pages, C = server needed (k6 and axe), D = Docker (ZAP),
#         E = static analysis / unit / mutation / CI evidence, F = screenshots of the application itself.
# Screenshot: Windows key + Shift + S, drag around the whole PowerShell window, click the pop-up, Save as PNG into
#   C:\ephios_sajawal\reports\evidence\  with the file name shown on the screen.
param([ValidateSet("A", "B", "C", "D", "E", "F")][string]$Phase = "A")

$Repo = "C:\ephios_sajawal"
$Py = "C:\Users\Admin\OneDrive\Desktop\ephios\.venv\Scripts\python.exe"
$K6 = "C:\sqe_tools\k6-v2.4.0-windows-amd64\k6.exe"
$OutDir = Join-Path $Repo "reports\evidence"
New-Item -ItemType Directory -Force $OutDir | Out-Null
Set-Location $Repo
$env:PYTHONPATH = "src"

function Show-Task($file, $what) {
    Clear-Host
    Write-Host "SCREENSHOT TO TAKE:  $file" -ForegroundColor Cyan
    Write-Host "IT MUST SHOW:        $what"
    Write-Host "SAVE IN:             $OutDir"
    Write-Host ""
}

function Terminal-Step($file, $what, [scriptblock]$command) {
    Show-Task $file $what
    [void](Read-Host "Press Enter to run the command (the command line must be visible in your screenshot)")
    Clear-Host
    Write-Host ("PS " + $Repo + "> " + $command.ToString().Trim()) -ForegroundColor Green
    & $command
    Write-Host ""
    Write-Host ">>> NOW take the screenshot of this window and save it as: $file" -ForegroundColor Yellow
    [void](Read-Host "When it is saved, press Enter for the next step")
}

function Browser-Step($file, $what, $target) {
    Show-Task $file $what
    Write-Host "OPEN:  $target"
    Write-Host ""
    [void](Read-Host "Press Enter to open it in your browser")
    Start-Process $target
    Write-Host ""
    Write-Host ">>> Take the screenshot in the browser (include the address bar) and save it as: $file" -ForegroundColor Yellow
    [void](Read-Host "When it is saved, press Enter for the next step")
}

function Manual-Step($file, $what) {
    Show-Task $file $what
    Write-Host ">>> Do the actions in your browser now, then take the screenshot (include the address bar) and save it as: $file" -ForegroundColor Yellow
    [void](Read-Host "When it is saved, press Enter for the next step")
}

function Start-AuditServer {
    $log = Join-Path $env:TEMP "sqe_serve.log"
    Remove-Item $log, "$log.err" -ErrorAction SilentlyContinue
    Write-Host "Starting a seeded test server (about 1 minute) ..."
    $process = Start-Process -FilePath $Py -ArgumentList "scripts\serve_seeded.py" -WorkingDirectory $Repo `
        -RedirectStandardOutput $log -RedirectStandardError "$log.err" -PassThru -WindowStyle Hidden
    for ($i = 0; $i -lt 120; $i++) {
        Start-Sleep -Seconds 2
        if ((Test-Path $log) -and (Select-String -Path $log -Pattern "READY" -Quiet)) { break }
    }
    $line = (Select-String -Path $log -Pattern "READY" | Select-Object -First 1).Line
    if (-not $line) { throw "The test server did not start. Look at $log.err" }
    return @{ Process = $process; Url = ($line -split " ")[1] }
}

function Stop-AuditServer($server) {
    & taskkill /T /F /PID $server.Process.Id | Out-Null
}

switch ($Phase) {
    "A" {
        Terminal-Step "EV-036_api_tests.png" "the last line '477 passed' (takes 8 to 20 minutes)" { & $Py -m pytest tests/team/api -q -p no:cacheprovider }
        Terminal-Step "EV-037_api_coverage.png" "the three coverage lines (operations, status codes, inputs)" { & $Py scripts\api_coverage.py }
        Terminal-Step "EV-038_regeneration_demo.png" "the removed and added test cases after two constraints change" { & $Py scripts\demo_regeneration.py }
        Terminal-Step "EV-043_access_matrix.png" "'7 passed' and the matrix table with the Evidence column" {
            & $Py -m pytest tests/team/e2e/test_access_matrix.py -q -p no:cacheprovider
            Get-Content reports\e2e\access_matrix.md
        }
        Terminal-Step "EV-047_pip_audit.png" "the pip-audit result with the soupsieve findings" { & $Py -m pip_audit --local }
    }
    "B" {
        Browser-Step "EV-016_issues_closed.png" "the closed issues #1, #4, #6, #7" "https://github.com/zain10sheraz/ephios/issues?q=is%3Aissue+is%3Aclosed"
        Browser-Step "EV-039_issues_open.png" "the open issues (#12-#14, #18-#23, #25, #26) with their labels" "https://github.com/zain10sheraz/ephios/issues?q=is%3Aissue+is%3Aopen"
        Browser-Step "EV-032b_prs_merged.png" "the list of merged pull requests (top of the list)" "https://github.com/zain10sheraz/ephios/pulls?q=is%3Apr+is%3Amerged"
        Browser-Step "EV-041_pr30_checks.png" "the checks of PR #30 with api-tests-black-box and e2e-browser-tests green" "https://github.com/zain10sheraz/ephios/pull/30/checks"
        Browser-Step "EV-042_playwright_report.png" "the Playwright HTML report with '51 passed'" (Join-Path $Repo "reports\e2e\playwright_report.html")
        Write-Host "Optional: open https://googlechrome.github.io/lighthouse/viewer/ and drop in" -ForegroundColor DarkGray
        Write-Host "  reports\accessibility\lighthouse_uc1_shift_form_before.json  (score 80)  -> EV-044b_lighthouse_before.png" -ForegroundColor DarkGray
        Write-Host "  reports\accessibility\lighthouse_uc1_shift_form_after.json   (score 89)  -> EV-044c_lighthouse_after.png" -ForegroundColor DarkGray
        [void](Read-Host "Press Enter to finish phase B")
    }
    "C" {
        $server = Start-AuditServer
        try {
            $url = $server.Url
            Terminal-Step "EV-046_k6_1user.png" "the k6 summary: p95, http_req_failed and the passed thresholds (1 user, 60 s)" { & $K6 run -e BASE=$url -e VUS=1 -e DURATION=60s scripts\k6_events_list.js }
            Terminal-Step "EV-046b_k6_5users.png" "the k6 summary for 5 users (60 s)" { & $K6 run -e BASE=$url -e VUS=5 -e DURATION=60s scripts\k6_events_list.js }
            Terminal-Step "EV-044_axe_after.png" "the four lines 'violated rules' of the axe-core scan (after the fix)" { node scripts\axe_scan.mjs $url after }
        }
        finally { Stop-AuditServer $server }
    }
    "D" {
        Write-Host "Docker Desktop must be running. Checking ..."
        & docker version --format "{{.Server.Version}}"
        Terminal-Step "EV-049_zap_run.png" "'22 passed' and '166 URLs seen ... alerts' (takes about 10 minutes)" { & $Py scripts\run_zap_passive.py }
        Terminal-Step "EV-049b_zap_summary.png" "the ZAP summary table header with the alert types" { & $Py scripts\zap_summary.py }
    }
    "E" {
        $inc = (Get-Content scripts\gate_modules.txt | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join ","
        Terminal-Step "EV-066_unit_coverage.png" "the coverage table of the 16 gate modules, every line 100 %, and 'Required test coverage of 100% reached' (takes several minutes)" {
            & $Py -m coverage run --include=$inc -m pytest tests/team --ignore=tests/team/api --ignore=tests/team/e2e -q -p no:cacheprovider
            & $Py -m coverage report -m --fail-under=100
        }
        Terminal-Step "EV-067_mutation_summary.png" "the mutation table: 1079 mutants, 78.2 % -> 97.7 % overall" { & $Py scripts\mutation_summary.py }
        Browser-Step "EV-068_branch_protection.png" "the protection rule of branch main with the required status checks (you must be logged in as the repository owner)" "https://github.com/zain10sheraz/ephios/settings/branches"
        Browser-Step "EV-069_actions_runs.png" "the list of GitHub Actions workflow runs (team-quality-gate)" "https://github.com/zain10sheraz/ephios/actions"
        Write-Host "Optional: open https://googlechrome.github.io/lighthouse/viewer/ and drop in" -ForegroundColor DarkGray
        Write-Host "  reportsccessibility\lighthouse_uc1_shift_form_before.json  (score 80)  -> EV-044b_lighthouse_before.png" -ForegroundColor DarkGray
        Write-Host "  reportsccessibility\lighthouse_uc1_shift_form_after.json   (score 89)  -> EV-044c_lighthouse_after.png" -ForegroundColor DarkGray
        [void](Read-Host "Press Enter to finish phase E")
    }
    "F" {
        $server = Start-AuditServer
        try {
            $url = $server.Url
            Write-Host "App is running at $url  (synthetic accounts, local only)" -ForegroundColor Green
            Write-Host "  planner:   planner@sqe.test   / Planner#2026"
            Write-Host "  volunteer: volunteer@sqe.test / Volunteer#2026   (use a private/incognito window for the second user)"
            [void](Read-Host "Press Enter to start")
            Browser-Step "EV-070_app_login_page.png" "the login page of the application (before logging in)" "$url/accounts/login/"
            Manual-Step "EV-071_planner_home.png" "log in as planner@sqe.test; the page after login (home / events list)"
            Browser-Step "EV-072_create_event_form.png" "the Create event form (title, location, visible for, responsible groups)" "$url/events/create/1/"
            Manual-Step "EV-073_shift_form_empty.png" "fill title 'Demo event', location 'Hall', click Next: the empty 'Create new shift' form with the Signup mode section"
            Manual-Step "EV-074_shift_form_error.png" "fill date (a future date), meeting time 11:00, start 10:00, end 16:00, click Save: the red error 'Meeting time must not be after start time!'"
            Manual-Step "EV-075_event_page_saved.png" "set meeting time 09:00 and click Save: the event page with the green banner 'The event ... has been saved' and the shift"
            Manual-Step "EV-076_volunteer_event_page.png" "in a private window log in as volunteer@sqe.test and open the event: the shift with the Sign up / Request button"
            Manual-Step "EV-077_volunteer_signup_success.png" "click Sign up / Request: the green confirmation banner"
            Browser-Step "EV-078_volunteer_permission_denied.png" "as the volunteer (private window) open this page: 'Permission denied'" "$url/events/create/1/"
        }
        finally { Stop-AuditServer $server }
    }
}
Write-Host "Phase $Phase finished. Tell Claude which files you saved." -ForegroundColor Green
