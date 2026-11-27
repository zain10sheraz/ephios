# Findings register: API, accessibility, usability, security and performance

For each finding: root cause, severity, risk (linked to `RISK_REGISTER.md`) and fix. Defects have a GitHub issue (https://github.com/zain10sheraz/ephios/issues/N); observations that are not defects are marked so. Analysis (5 Whys, fishbone, Pareto): `RCA.md`. Severity: **major** = serious/critical effect on a core workflow or axe `critical`/`serious`; **minor** = hardening or consistency gap with a workaround.

## API (area 2, `API_TESTING.md`)
| Finding | Issue | Root cause | Severity | Risk (residual) | Fix / status |
|---|---|---|---|---|---|
| Business-rule rejections answer HTTP 302, the same status as success; only a read-back tells them apart | #12 DEFECT-005 | API contract not specified: the endpoints were built for the HTML UI (flash message after redirect) | minor | PR-04, PR-03 (low: rules are enforced, clients must read back) | documented in `test_specs/openapi.yaml`; changing status codes is a product decision; open |
| Invalid `limit`, `offset`, `ordering` silently ignored (200) while other invalid filters return 400 | #13 DEFECT-006 | framework defaults (DRF paginator and ordering filter) relied on without validation | minor | PR-12 (low) | validate or document; open |
| 403 vs 405 inconsistent (`DELETE` 403, `POST` 405), 403 instead of 401, schema of the project documents only 200 | #14 DEFECT-007 | permission check runs before the method check; schema generated from code and not reviewed | minor | PR-06 (low: no bypass found) | own spec written from observed behaviour; open |
| Observation (not a defect): a custom signup window that extends beyond the shift is accepted; the only rule is start before end | - | rule not specified in the documentation | - | PR-02 (needs a product decision) | recorded in `API_TESTING.md` |
| Observation (test environment): two truly simultaneous writes on SQLite can fail with `database is locked` (HTTP 500) | - | SQLite allows one writer; production uses PostgreSQL/MySQL (not tested here) | - | PR-03 (low-medium) | the concurrency tests assert the stored state; PostgreSQL run recommended |

## Accessibility and usability (area 3, `ACCESSIBILITY.md`)
| Finding | Issue | Root cause | Severity | Risk (residual) | Fix / status |
|---|---|---|---|---|---|
| Selects and signup-deadline inputs of the shift form have no accessible name (axe `select-name`, `label`: critical) | #17 DEFECT-008 | accessibility not part of the definition of done, no automated check; headings used instead of labels | major | PR-08 | **fixed and merged** (PR #24): `aria-label`s; regression test fails 4/4 before, passes 4/4 after; Lighthouse 80 -> 89 |
| Colour contrast of secondary text 3.47:1 / 3.73:1 (needs 4.5:1) on all key screens | #18 DEFECT-009 | theme grey chosen for looks, no contrast criterion | major | PR-08 (medium) | darken `text-body-secondary` to >= 4.5:1; open |
| Positive `tabindex="1"` on the signup button wrapper | #19 DEFECT-010 | legacy markup, no keyboard-order check upstream | major | PR-08 (medium) | remove the positive tabindex; open |
| Select2 qualification field has no accessible name (`aria-input-field-name`) | #20 DEFECT-011 | third-party widget not verified at integration | major | PR-08 (medium) | pass a name to the Select2 widget; open |
| Heading order, ARIA role of the Select2 search box, unnamed dialog | #21 DEFECT-012 | legacy markup, third-party widget | minor | PR-08 (low) | open |
| Rejected signup from an already open page shows only "This action is not allowed." without the reason | #22 DEFECT-013 | one catch-all message for all rejections | minor | PR-08 (usability, low) | state the reason in the message; open |

## Security (area 3, `SECURITY.md`)
| Finding | Issue | Root cause | Severity | Risk (residual) | Fix / status |
|---|---|---|---|---|---|
| `soupsieve 2.9` has 4 advisories (CVE-2026-126190 to -126193) | #23 DEFECT-014 | transitive dependency of `beautifulsoup4`; vulnerable CSS-selector code is not reachable (`find_all("img")` only) | minor | PR-13 (low) | upgrade `soupsieve` after a compatibility check; open |
| CSP lacks `frame-ancestors`, `form-action`, `base-uri` (ZAP medium, confirmed in `settings.py:344`) | #25 DEFECT-015 | CSP written with five directives only | minor | PR-07 (low: `X-Frame-Options: DENY` blocks framing) | add the three directives; open |
| `django_language` cookie without SameSite (ZAP low, confirmed: no `LANGUAGE_COOKIE_SAMESITE`) | #26 DEFECT-016 | Django default | minor | PR-07 (low) | `LANGUAGE_COOKIE_SAMESITE = "Lax"`; open |
| Verified controls with no finding: session cookie HttpOnly + SameSite=Lax, CSRF refusal (403), role checks (7 decisions), security headers | - | - | - | PR-06, PR-07 | documented as verified controls |

## Performance (area 3, `PERFORMANCE.md`)
| Finding | Issue | Root cause | Severity | Risk (residual) | Fix / status |
|---|---|---|---|---|---|
| Throughput stays at about 15 requests/s from 1 to 5 users; average time grows 4.3 times | observation | development server (one process) and SQLite handle requests one at a time | - (no limit broken) | PR-09 (medium: production capacity unknown) | measure on a production server; not a defect |
| p95 at 5 users is 505-506 ms: within the own limit (800 ms) but 5-6 ms above the 500 ms of the register's EC-04 row, which concerns signup (not measured) | observation | different operation and limit than the register's row | - | PR-09 / EC-04 (not comparable) | k6 test of signup recommended |
| Slow outliers of 3.7-5.1 s in every run (p95 stays below 0.5 s) | observation | not investigated (a cold first request after login is plausible, unverified) | - | PR-09 | investigate |
