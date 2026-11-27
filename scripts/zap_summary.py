"""Summarise reports/security/zap_alerts.json (ZAP passive scan) into reports/security/zap_summary.md.

One row per distinct alert type, with the number of URLs, the evidence ZAP recorded and OUR assessment after checking the
source or configuration (the assessment column is written by hand in ASSESSMENT below; unknown alert types are flagged).
"""

import collections
import json
import os

FOLDER = os.path.join(os.path.dirname(__file__), "..", "reports", "security")
ASSESSMENT = {
    "CSP: Failure to Define Directive with No Fallback": "CONFIRMED in source: `CONTENT_SECURITY_POLICY` (`settings.py:344`) defines only default-src, style-src, img-src, frame-src, script-src; no frame-ancestors, form-action, base-uri. Framing is still blocked by `X-Frame-Options: DENY`. Reported (issue #25).",
    "Cookie No HttpOnly Flag": "csrftoken only. Django default (`CSRF_COOKIE_HTTPONLY` not set); the session cookie is HttpOnly and was not flagged. Accepted design, not reported.",
    "Cookie without SameSite Attribute": "django_language only. No `LANGUAGE_COOKIE_SAMESITE` in `settings.py`, so Django's default (none) applies. Low impact (language preference). Reported (issue #26).",
    'Server Leaks Version Information via "Server" HTTP Response Header Field': "`WSGIServer/0.2 CPython/3.12.10` is the Django development server used for the test; a production deployment sits behind another server. Not reported.",
    "X-Content-Type-Options Header Missing": "only on `/static/...` files served by the development static handler; pages carry `X-Content-Type-Options: nosniff` (SECURE_CONTENT_TYPE_NOSNIFF). Development-server effect. Not reported.",
    "Authentication Request Identified": "informational: the login form was recognised.",
    "Information Disclosure - Suspicious Comments": "informational: a `TODO` comment in a bundled JavaScript file; no secret.",
    "Modern Web Application": "informational.",
    "Session Management Response Identified": "informational: csrftoken/sessionid recognised as session tokens.",
    "User Controllable HTML Element Attribute (Potential XSS)": "informational: ZAP lists form fields whose submitted value is reflected; the application escapes output (Django templates). No XSS observed; not exploited (passive mode).",
}
ORDER = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}


def load(name):
    with open(os.path.join(FOLDER, name), encoding="utf-8") as handle:
        return json.load(handle)


data = load("zap_alerts.json")
groups = collections.defaultdict(lambda: {"risk": "", "cwe": "", "urls": set(), "evidence": ""})
for alert in data["alerts"]:
    group = groups[alert["alert"]]
    group.update(
        risk=alert["risk"], cwe=alert.get("cweid", ""), evidence=(alert.get("evidence") or "")[:70]
    )
    group["urls"].add(alert["url"].split("?")[0])
urls = load("zap_urls.json")
lines = [
    f"# ZAP passive scan summary (ZAP {data['zap_version']}, {len(urls)} URLs seen, {len(data['alerts'])} alerts, {len(groups)} alert types)",
    "",
    "| Risk | Alert | CWE | URLs | Evidence recorded by ZAP | Assessment after checking source/configuration |",
    "|---|---|---|---|---|---|",
]
for name, group in sorted(
    groups.items(), key=lambda item: (ORDER.get(item[1]["risk"], 9), item[0])
):
    note = ASSESSMENT.get(name, "NOT YET ASSESSED")
    lines.append(
        f"| {group['risk']} | {name} | {group['cwe']} | {len(group['urls'])} | `{group['evidence']}` | {note} |"
    )
with open(os.path.join(FOLDER, "zap_summary.md"), "w", encoding="utf-8", newline="\n") as handle:
    handle.write("\n".join(lines) + "\n")
print("\n".join(lines[:3]))
print("not yet assessed:", [name for name in groups if name not in ASSESSMENT])
