# Viva notes - Area 3 (use cases, Playwright, usability, accessibility, security, performance) - Sajawal

Re-run things yourself before the viva; do not rely on this page alone. You must be able to explain every test, number and decision below. Details: `E2E_AND_QUALITY_REPORT.md`.

## 1. One-minute story
Ephios has two workflows: a planner creates an event with a shift (WF1) and a volunteer signs up for it (WF2). I wrote two use cases with 12 flows, automated each flow in a real browser (Playwright) with checks of the screen and of the stored state, ran accessibility tools (axe-core, Lighthouse) and found and fixed two critical problems on one screen, checked who may do what (access matrix), audited the dependencies, measured performance with k6 against limits set beforehand, and tested that a storage failure leaves no half-written signup.

## 2. Component by component

| Component | What to say | Where |
|---|---|---|
| **Use cases** | UC1 planner creates event + shift, UC2 volunteer signs up; each: goal, actor, preconditions, main flow, 2 alternative, 3 exception flows, postconditions | `USE_CASES.md` |
| **Playwright suite** | logs in through the real login form; every flow asserts the banner/error shown **and** the stored state (REST read-back, DB row counts); rejection flows use a stale page; the empty-title flow switches off the browser's `required` check to test the server rule | `tests/team/e2e/` |
| **Usability tests** | WF1: reject (meeting after start), the error names the field and the rule, values are kept, correct, success. WF2: sign up, confirmation shown | `test_usability_keyboard.py` |
| **Keyboard test** | focus goes date -> meeting -> start -> end ... -> "Save event"; Enter submits | same file |
| **Accessibility** | axe-core 4.14.0 through `@axe-core/playwright` (`scripts/axe_scan.mjs`) + Lighthouse 13.6.0 on the shift form and the event page; merged by rule id so a finding of both tools counts once; fixed `select-name` and `label` (critical): Lighthouse 80 -> 89 on the shift form; regression test fails before, passes after | `ACCESSIBILITY.md`, `reports/accessibility/` |
| **Access matrix** | 7 role/action decisions in the browser (4 denied, 3 allowed) | `SECURITY.md`, `reports/e2e/access_matrix.md` |
| **Controls reviewed** | session cookie HttpOnly + SameSite=Lax, Secure only in non-debug settings; POST without CSRF token -> 403; CSP and other headers | `SECURITY.md` section 3 |
| **pip-audit** | 175 audited packages (2 local packages skipped); 4 advisories in soupsieve 2.9; not reachable (the app only calls `find_all("img")`) | `SECURITY.md` section 4 |
| **k6** | operation `GET /api/events/`; limits p95 < 800 ms, < 1 % failures set before; 1 and 5 users, 2 runs each, 60 s; p95 about 100 ms and 505 ms; throughput flat at about 15 req/s | `PERFORMANCE.md` |
| **Recovery** | database file made read-only during the signup click; nothing stored; restored; retry gives exactly one participation | `test_failure_recovery.py` |

## 3. Likely questions and honest answers
- *Why is the UC1-E1 test switching off `required`?* The browser blocks an empty required field before it reaches the server. The test is about the server-side rule, so I disable the browser check on purpose and say so in the test.
- *Why stale pages for the rejection flows?* A fresh page hides the button when the shift is full or you already signed up, so a user can only hit the rule from an old page (second tab, page left open). That is realistic and it showed a usability problem: the message "This action is not allowed." gives no reason (issue #22).
- *Why did the first browser run fail with Django errors?* Upstream marks every test as using Django's test database, which cannot start next to Playwright's event loop. These tests use a separate real server, so the conftest removes that marker for this folder only.
- *Is 505 ms a failure?* Not against my limit (800 ms, set before testing). But the risk register's EC-04 asks for p95 <= 500 ms at 5 users for **signup**; I measured the event list, not signup, so EC-04 is reported as not met as written and not comparable. I did not change the limit after seeing the result.
- *What does flat throughput mean?* About 15 requests/s whatever the number of users: the development server and SQLite handle requests essentially one at a time. Not a production figure.
- *What did ZAP find and how do you know it is real?* ZAP 2.17.0 ran in passive mode in Docker while the browser tests of both workflows went through it (22 of 22 passed, 166 URLs, 298 alerts of 10 types). I assessed each type against the source: the CSP lacks `frame-ancestors`, `form-action`, `base-uri` (`settings.py:344`, issue #25) and the language cookie has no SameSite (issue #26); the Server header and the missing nosniff on `/static/` come from the development server. Passive means nothing was attacked.
- *What did the accessibility fix change?* `aria-label` on the two selects and on the shared date/time widget (`core/forms/events.py`, `extra/widgets.py`). It does not fix colour contrast, positive tabindex or the Select2 name (issues #18-#20 stay open).
- *What would you do differently?* Run axe in CI from the start, test signup (a write) under load with several volunteers, run ZAP, and add Firefox/WebKit.
- *AI use?* Claude Code assisted (recorded in `AI_USE_RECORD.md`); I must explain every test myself. Screenshots must be taken by me.

## 4. Live-task rehearsal
Example: *"the signup deadline error must name the time"*: change the message in the form, rerun `test_uc1_e2_*` and `test_usability_wf1_*` (they assert the exact text) and see them fail until the expectation is updated.
Example 2: *"volunteers may open the edit-shift page"*: the access matrix rows `volunteer-open edit-shift page` expect 403 and fail; the CI job `e2e-browser-tests` goes red.

## 5. Commands cheat sheet
- Browser tests: `$env:PYTHONPATH="src"; .venv\Scripts\python.exe -m pytest tests/team/e2e -q -p no:cacheprovider` (needs `uv pip install playwright pytest-html` and `python -m playwright install chromium`)
- axe: start a seeded server `python scripts/serve_seeded.py`, then `node scripts/axe_scan.mjs <url> before|after` (`npm install playwright @axe-core/playwright` in `C:\sqe_tools`)
- ZAP passive scan: Docker running, then `python scripts/run_zap_passive.py` and `python scripts/zap_summary.py`
- Lighthouse: `python scripts/run_lighthouse.py start after` (Lighthouse in `C:\sqe_tools`), comparison: `python scripts/compare_accessibility.py`
- k6: `k6 run -e BASE=http://127.0.0.1:8001 -e VUS=5 -e DURATION=60s scripts/k6_events_list.js`
- pip-audit: `python -m pip_audit --local`
