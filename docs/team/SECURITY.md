# Security (area 3): access matrix, controls reviewed, dependency audit, ZAP

Scope: the two workflows (WF1 event and shift management, WF2 signup) on a local copy with synthetic data and test accounts. No other system was tested.

## 1. Routes and data of the two workflows

| Route | Method | Workflow | Data read or changed | Required permission (source) |
|---|---|---|---|---|
| `/accounts/login/` | GET, POST | both | session cookie, CSRF cookie | none |
| `/events/create/<type>/` | GET, POST | WF1 | creates `Event` | `core.add_event` |
| `/events/<id>/createshift/`, `/shifts/<id>/edit/` | GET, POST | WF1 | creates/changes `Shift` (shared record), activates `Event` | `core.change_event` on the event |
| `/shifts/<id>/delete/`, `/events/<id>/delete/` | POST | WF1 | deletes `Shift` / `Event` | `change_event` (shift), `delete_event` + `change_event` (event) (`ShiftDeleteView`, `src/ephios/core/views/shift.py`) |
| `/events/<id>-<slug>/` and `/events/` | GET | WF2 | reads `Event`, `Shift`, own participations | login, event visible to the user's groups |
| `/shifts/<id>/signup/` | POST | WF2 | creates/changes `LocalParticipation` | login, event visible |
| `/api/events/`, `/api/shifts/`, `/api/participations/`, `/api/users/me/participations/` | GET | both | reads the shared records | login (403 otherwise) |

## 2. Access matrix (Playwright, `tests/team/e2e/test_access_matrix.py`; role, action, expected, observed, result **and evidence** of every check are written to `reports/e2e/access_matrix.md` by the test run; the table below shows role, action, expected and observed)

| Role | Action | Expected | Observed | Result |
|---|---|---|---|---|
| anonymous | open create-event page | login page (HTTP 200 after redirect) | 200, URL is `/accounts/login/` | pass (denied) |
| volunteer | open create-event page | 403 | 403 | pass (denied) |
| planner | open create-event page | 200 | 200 | pass (allowed) |
| volunteer | open edit-shift page | 403 | 403 | pass (denied) |
| planner | open edit-shift page | 200 | 200 | pass (allowed) |
| volunteer | open delete-shift page | 403 | 403 | pass (denied) |
| volunteer | open the event list | 200 | 200 | pass (allowed) |

Seven decisions (3 allowed, 4 denied). Further decisions checked over HTTP in the API tests: anonymous REST access is 403 for every REST route (7 routes), a volunteer cannot add a shift, activate or create an event (`tests/team/api/test_access_control_api.py`).

## 3. Controls reviewed (observed on the running app and backed by source/configuration)

| Control | Observation (real response headers, `data` of this session) | Source / configuration | Assessment |
|---|---|---|---|
| **Session cookie** | `sessionid`: `HttpOnly`, `SameSite=Lax`, `Max-Age=1209600`; no `Secure` flag in the local run | `src/ephios/settings.py:447-449`: `SESSION_COOKIE_SECURE = True` and `CSRF_COOKIE_SECURE = True` **only when `DEBUG` is off** | acceptable: the local run uses `DEBUG=True` over HTTP; production configuration sets `Secure`. Not verified on a production deployment. |
| **CSRF protection** | `POST /accounts/login/` without the token -> **403**; every state-changing POST in the API tests without token -> 403 (`test_post_without_csrf_token_is_refused`); `csrftoken` cookie is `SameSite=Lax` and not `HttpOnly` (Django default, needed by the page scripts) | Django `CsrfViewMiddleware` (enabled in `settings.py` middleware list) | effective |
| **Role checks** | table in section 2; delete/edit/create decisions come from permission mixins, not from hiding buttons | `CustomPermissionRequiredMixin` with `permission_required` and `get_permission_object` (`views/shift.py`, `views/event.py`) | effective for the 7 decisions tested |
| **Browser security headers** | `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-src 'none'`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `Cross-Origin-Opener-Policy: same-origin` | `CONTENT_SECURITY_POLICY` (`settings.py:344`), `SECURE_*` settings | strong; `Strict-Transport-Security` is absent locally and set only in the non-debug configuration (`settings.py:455`) |
| Information disclosure | `Server: WSGIServer/0.2 CPython/3.12.10` | development server | applies to `runserver` only, not a production setup |

No defect was found in these controls, so none was reported.

## 4. Dependency audit (pip-audit 2.10.1, `reports/security/pip_audit.json`)
Checked: **175 packages** audited (177 installed; `ephios`, the application itself, and `team-mutation`, our own tool package, are not on PyPI and were **skipped** by pip-audit, as the tool's output states) of the project environment (installed versions of the locked dependencies and the tools used for this project). Found: **4 advisories in 1 package**.

| Component | Advisory (aliases) | Evidence | Impact | Correction |
|---|---|---|---|---|
| `soupsieve 2.9` (transitive: `ephios -> beautifulsoup4 -> soupsieve`; also `webtest`) | CVE-2026-126190 (descendant combinator, polynomial time), CVE-2026-126191 (regex backtracking), CVE-2026-126192 (`:has()` sibling combinator), CVE-2026-126193 (recursion on nested pseudo-classes) | `pip_audit.json`; `uv pip show soupsieve` (required by beautifulsoup4, ephios, webtest) | denial of service (CPU/recursion) **when attacker-controlled CSS selectors or documents are matched**. The application uses BeautifulSoup only as `email.find_all("img")` (`src/ephios/core/services/mail/cid.py:46`), never the CSS selector API, so the vulnerable code paths are **not reachable** from the application. Severity for this project: **low**. | upgrade `soupsieve` to the fixed versions named in the advisories (2.10.0 / 3.0.2 / 4.0.0) after checking compatibility with `beautifulsoup4` (`uv lock --upgrade-package soupsieve`); not applied here because the lock file is upstream's and the path is unreachable. |

No other package had a known vulnerability at the time of the run (2026-11-26); the audit depends on the vulnerability database available at that time.

## 5. OWASP ZAP passive scan (ZAP 2.17.0, `reports/security/zap_summary.md`, `zap_alerts.json`, `zap_urls.json`)
How: `scripts/run_zap_passive.py` starts ZAP in Docker as a proxy (passive scanners only, nothing is attacked), then runs the browser tests of **both workflows** (use cases UC1 and UC2, access matrix, usability and keyboard tests) with every browser request routed through ZAP. All **22 browser tests passed** through the proxy; ZAP saw **166 URLs** and raised **298 alerts of 10 types** (the member's rerun on 2026-11-28, screenshots `EV-049`, `EV-049b`; the first run on 2026-11-27 raised 299: the only difference is one informational alert of type 'Session Management Response Identified', 40 against 39) (1 medium, 4 low, 5 informational), assessed one by one against the source in `zap_summary.md`:

| Risk | Alert | Our assessment |
|---|---|---|
| Medium | CSP: failure to define directive with no fallback (`frame-ancestors`, `form-action`, `base-uri`) | **confirmed** in `settings.py:344`; mitigated by `X-Frame-Options: DENY`; reported as issue #25 (DEFECT-015, minor) |
| Low | `django_language` cookie without SameSite | **confirmed** (no `LANGUAGE_COOKIE_SAMESITE`); issue #26 (DEFECT-016, minor) |
| Low | `csrftoken` cookie without HttpOnly | Django default; the session cookie is HttpOnly and was not flagged; accepted |
| Low | Server header leaks version; X-Content-Type-Options missing on `/static/` files | development server only; pages carry `nosniff`; not reported |
| Informational (5) | authentication request, modern web application, session management, suspicious comment (`TODO` in a JS file), potential XSS attribute | no action; ZAP's "user-controllable attribute" lists reflected form fields, no XSS was observed (passive mode, nothing exploited) |

Controls reviewed with the ZAP evidence: **session cookie attributes** (ZAP did not flag `sessionid`, which is HttpOnly + SameSite=Lax, and did flag the two other cookies) and **role checks** (the access matrix ran through ZAP; ZAP does not test authorisation, the matrix does).

## 6. Limits
Authentication brute force, session fixation on a production deployment, file upload and the webhook/federation features were not tested; only the two workflows were in scope. The security tests use the development server over HTTP. ZAP ran in passive mode only (no active scan, as the brief requires).
