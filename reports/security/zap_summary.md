# ZAP passive scan summary (ZAP 2.17.0, 166 URLs seen, 298 alerts, 10 alert types)

| Risk | Alert | CWE | URLs | Evidence recorded by ZAP | Assessment after checking source/configuration |
|---|---|---|---|---|---|
| Medium | CSP: Failure to Define Directive with No Fallback | 693 | 43 | `style-src 'self' 'nonce-lUYaHJvGPLaFhKYnmgL86Q=='; default-src 'self';` | CONFIRMED in source: `CONTENT_SECURITY_POLICY` (`settings.py:344`) defines only default-src, style-src, img-src, frame-src, script-src; no frame-ancestors, form-action, base-uri. Framing is still blocked by `X-Frame-Options: DENY`. Reported (issue #25). |
| Low | Cookie No HttpOnly Flag | 1004 | 22 | `Set-Cookie: csrftoken` | csrftoken only. Django default (`CSRF_COOKIE_HTTPONLY` not set); the session cookie is HttpOnly and was not flagged. Accepted design, not reported. |
| Low | Cookie without SameSite Attribute | 1275 | 1 | `Set-Cookie: django_language` | django_language only. No `LANGUAGE_COOKIE_SAMESITE` in `settings.py`, so Django's default (none) applies. Low impact (language preference). Reported (issue #26). |
| Low | Server Leaks Version Information via "Server" HTTP Response Header Field | 497 | 59 | `WSGIServer/0.2 CPython/3.12.10` | `WSGIServer/0.2 CPython/3.12.10` is the Django development server used for the test; a production deployment sits behind another server. Not reported. |
| Low | X-Content-Type-Options Header Missing | 693 | 16 | `` | only on `/static/...` files served by the development static handler; pages carry `X-Content-Type-Options: nosniff` (SECURE_CONTENT_TYPE_NOSNIFF). Development-server effect. Not reported. |
| Informational | Authentication Request Identified | -1 | 1 | `password` | informational: the login form was recognised. |
| Informational | Information Disclosure - Suspicious Comments | 615 | 5 | `// TODO isolatedDeclaration` | informational: a `TODO` comment in a bundled JavaScript file; no secret. |
| Informational | Modern Web Application | -1 | 24 | `<a class="nav-link dropdown-toggle" href="#" id="navbarDropdownAccount` | informational. |
| Informational | Session Management Response Identified | -1 | 29 | `csrftoken` | informational: csrftoken/sessionid recognised as session tokens. |
| Informational | User Controllable HTML Element Attribute (Potential XSS) | 20 | 3 | `` | informational: ZAP lists form fields whose submitted value is reflected; the application escapes output (Django templates). No XSS observed; not exploited (passive mode). |
