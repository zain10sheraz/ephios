# Guided evidence run. YOU take every screenshot (course rule); this script only runs the commands, one at a time,
# shows the exact file name to use, and waits for you.
#
# Run from PowerShell (does not change git, only runs the project's own commands):
#   powershell -ExecutionPolicy Bypass -File C:\ephios_sajawal\scripts\evidence_walkthrough.ps1 -Phase A
# Phases: A = terminal (no server), B = browser pages, C = server needed (k6 and axe), D = Docker (ZAP).
# Screenshot: Windows key + Shift + S, drag around the whole PowerShell window, click the pop-up, Save as PNG into
#   C:\ephios_sajawal\reports\evidence\  with the file name shown on the screen.
param([ValidateSet("A", "B", "C", "D")][string]$Phase = "A")

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
}
Write-Host "Phase $Phase finished. Tell Claude which files you saved." -ForegroundColor Green
