"""Build the final PDF report from the project documents (Markdown -> HTML -> PDF through Chromium).

Usage: python scripts/build_report_pdf.py [output.pdf]
Every repository path written in backticks (docs/..., reports/..., tests/..., scripts/..., src/...) becomes a link to the
file on GitHub, which provides the "evidence links" the brief asks for. The test completion report with the release or
hold decision is the last section, as required.
"""

import base64
import glob
import html
import importlib
import os
import re
import sys
from datetime import date

import markdown

ROOT = os.path.join(os.path.dirname(__file__), "..")
REPO = "https://github.com/zain10sheraz/ephios"
BASE = f"{REPO}/blob/main/"
TREE = f"{REPO}/tree/main/"
OUTPUT = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.path.join(ROOT, "reports", "Project_24I-3115_24K-3068_24I-3038_C.pdf")
)

SECTIONS = [
    ("1 Scope, requirements and test basis", ["docs/team/REQUIREMENTS.md", "docs/team/SETUP.md"]),
    ("2 Area ownership and AI-use record", ["docs/team/AI_USE_RECORD.md"]),
    (
        "3 Test plan, risk register and traceability",
        ["docs/team/TEST_PLAN.md", "docs/team/RISK_REGISTER.md", "docs/team/TRACEABILITY.md"],
    ),
    (
        "4 Results of the testing activities",
        [
            "docs/team/SONARQUBE.md",
            "docs/team/CYCLOMATIC_COMPLEXITY.md",
            "docs/team/COVERAGE_SCOPE.md",
            "docs/team/MCC_MCDC.md",
            "docs/team/MUTATION.md",
            "docs/team/CI_GATES.md",
            "docs/team/API_TESTING.md",
            "docs/team/USE_CASES.md",
            "docs/team/USE_CASES_MANAN.md",
            "docs/team/USE_CASES_ZAIN.md",
            "docs/team/E2E_AND_QUALITY_REPORT.md",
            "docs/team/ACCESSIBILITY.md",
            "docs/team/SECURITY.md",
            "docs/team/PERFORMANCE.md",
        ],
    ),
    (
        "5 Findings, defects and root cause analysis",
        ["docs/team/FINDINGS_REGISTER.md", "docs/team/RCA.md"],
    ),
    (
        "6 Monitoring: progress reports, GQM metrics and effort",
        [
            "docs/team/PROGRESS_REPORT_1.md",
            "docs/team/PROGRESS_REPORT_2.md",
            "docs/team/PROGRESS_REPORT_3.md",
            "docs/team/PROGRESS_REPORT_4.md",
            "docs/team/WORKLOG.md",
        ],
    ),
    (
        "7 Appendix: result tables and raw output",
        [
            "docs/team/DATA_SOURCES.md",
            "reports/api/api_coverage.md",
            "reports/accessibility/comparison.md",
            "reports/security/zap_summary.md",
            "reports/e2e/access_matrix.md",
            "reports/performance/k6_summary.md",
        ],
    ),
    ("8 Evidence links", ["docs/team/EVIDENCE_CHECKLIST.md"]),
    ("9 Test completion report, release or hold decision", ["docs/team/TEST_COMPLETION_REPORT.md"]),
]

COVER = f"""
<div class="cover">
<p class="small">SE3002 / SOFTWARE QUALITY ENGINEERING &nbsp;&middot;&nbsp; Section SE-C</p>
<h1>Software Quality Engineering Final Project</h1>
<h2>Automated testing of the open-source MIS Ephios<br/>(module: events and signup)</h2>
<table class="meta">
<tr><th>Group</th><td>Zain Sheraz (24I-3115), Sajawal Khan (24K-3068), Abdul Manan (24I-3038)</td></tr>
<tr><th>GitHub accounts</th><td>Zain: <b>zain10sheraz</b>; Manan: <b>MannanJafferyyy</b>; Sajawal: <b>sajawalkhanfake</b> (the accounts the commits were made with)</td></tr>
<tr><th>Area ownership</th><td>Zain: area 1, static analysis, white-box, mutation, CI (use cases UC5, UC6).
Manan: area 2, API testing and data generation (use cases UC3, UC4).
Sajawal: area 3, use cases, usability, accessibility, security, performance (use cases UC1, UC2).</td></tr>
<tr><th>Repository (public)</th><td><a href="{REPO}">{REPO}</a></td></tr>
<tr><th>Upstream</th><td><a href="https://github.com/ephios-dev/ephios">https://github.com/ephios-dev/ephios</a> (MIT licence)</td></tr>
<tr><th>Baseline commit</th><td>d12e76cd2b5b422177176506b0b6b9393dbc10e5 (tag <code>baseline-upstream-d12e76cd</code>)</td></tr>
<tr><th>Decision</th><td><b>HOLD</b> (see section 9)</td></tr>
<tr><th>Date</th><td>{date.today().isoformat()}</td></tr>
</table>
<p class="small">Evidence links: every repository path in backticks is a link to the file on GitHub (branch main). Screenshots in the evidence set were taken by the team members themselves.</p>
</div>
"""

CSS = """
@page { size: A4; margin: 18mm 15mm 18mm 15mm; }
body { font-family: Segoe UI, Arial, sans-serif; font-size: 9.5pt; line-height: 1.38; color: #1b1b1b; }
h1 { font-size: 20pt; margin: 0 0 6px 0; } h2 { font-size: 14pt; border-bottom: 1px solid #999; padding-bottom: 2px; margin-top: 18px; }
h3 { font-size: 11.5pt; margin-top: 14px; } h4 { font-size: 10.5pt; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px 0; font-size: 8.4pt; }
th, td { border: 1px solid #aaa; padding: 3px 5px; vertical-align: top; text-align: left; word-break: break-word; }
th { background: #eef1f5; }
code { font-family: Consolas, monospace; font-size: 8.4pt; background: #f3f3f3; padding: 0 2px; word-break: break-all; }
pre { background: #f6f6f6; padding: 6px; border: 1px solid #ddd; font-size: 8pt; white-space: pre-wrap; word-break: break-all; }
a { color: #0b4f9e; text-decoration: none; }
.cover { padding-top: 40mm; } .cover h1 { font-size: 26pt; } .cover h2 { border: none; font-size: 15pt; font-weight: normal; }
.cover table.meta th { width: 24%; } .small { color: #555; font-size: 9pt; }
.chapter { page-break-before: always; } .doc { margin-top: 12px; }
.docpath { color: #666; font-size: 8pt; margin-bottom: 2px; }
.toc li { margin: 2px 0; }
figure { margin: 10px 0; page-break-inside: avoid; } figure img { max-width: 100%; border: 1px solid #bbb; }
figcaption { font-size: 8.5pt; color: #333; margin-top: 2px; }
"""

PATH = re.compile(
    r"`((?:docs|reports|tests|scripts|src|test_specs|test_data|tools|mutation|\.github)/[A-Za-z0-9_./\-]+)`"
)


def link_paths(text):
    def replace(match):
        path = match.group(1)
        if "*" in path or "<" in path:
            return match.group(0)
        folder = path.endswith("/") or "." not in os.path.basename(path)
        return f"[`{path}`]({(TREE if folder else BASE) + path})"

    return PATH.sub(replace, text)


def render(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        text = handle.read()
    if relative.endswith(".txt"):
        body = f"<pre>{html.escape(text)}</pre>"
    else:
        body = markdown.markdown(
            link_paths(text), extensions=["tables", "fenced_code", "sane_lists"]
        )
    return f'<div class="doc"><div class="docpath">{html.escape(relative)}</div>{body}</div>'


def evidence_captions():
    """Map evidence ids (EV-005a, ...) to the description in the evidence checklist."""
    captions = {}
    with open(
        os.path.join(ROOT, "docs", "team", "EVIDENCE_CHECKLIST.md"), encoding="utf-8"
    ) as handle:
        for line in handle:
            cells = [cell.strip() for cell in line.split("|")]
            if len(cells) > 3 and re.fullmatch(r"EV-\d+[a-z]?", cells[1]):
                captions[cells[1]] = cells[2]
    return captions


def gallery():
    """All screenshots in reports/evidence, embedded as images with their evidence id and description."""
    captions = evidence_captions()
    figures = []
    for path in sorted(glob.glob(os.path.join(ROOT, "reports", "evidence", "*.png"))):
        name = os.path.basename(path)
        evidence_id = name.split("_")[0]
        with open(path, "rb") as handle:
            data = base64.b64encode(handle.read()).decode("ascii")
        caption = f"{evidence_id}: {captions.get(evidence_id, name)}"
        figures.append(
            f'<figure><img src="data:image/png;base64,{data}" alt="{html.escape(name)}"/>'
            f"<figcaption>{html.escape(caption)} <span class='docpath'>({html.escape(name)})</span></figcaption></figure>"
        )
    intro = (
        "<h3>Screenshots taken by the team members</h3><p>Each screenshot was taken by a team member from the real tool or "
        f"page (course rule). {len(figures)} screenshots are included; their files are in <code>reports/evidence/</code>.</p>"
    )
    return f'<div class="doc">{intro}{"".join(figures)}</div>'


def build_html():
    toc = "".join(f"<li>{html.escape(title)}</li>" for title, _ in SECTIONS)
    parts = [f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>", COVER]
    parts.append(f'<div class="chapter"><h2>Contents</h2><ol class="toc">{toc}</ol></div>')
    for title, files in SECTIONS:
        parts.append(f'<div class="chapter"><h2>{html.escape(title)}</h2>')
        parts.extend(render(name) for name in files)
        if title.startswith("8 "):
            parts.append(gallery())
        parts.append("</div>")
    parts.append("</body></html>")
    return "".join(parts)


def main():
    sync_playwright = importlib.import_module("playwright.sync_api").sync_playwright
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT)), exist_ok=True)
    document = build_html()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_content(document, wait_until="load")
        footer = (
            "<div style='font-size:8px;width:100%;text-align:center;color:#666'>"
            "SE3002 SQE Final Project - Ephios - <span class='pageNumber'></span> / <span class='totalPages'></span></div>"
        )
        page.pdf(
            path=OUTPUT,
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<span></span>",
            footer_template=footer,
            margin={"top": "18mm", "bottom": "18mm", "left": "15mm", "right": "15mm"},
        )
        browser.close()
    print("written", os.path.abspath(OUTPUT), os.path.getsize(OUTPUT), "bytes")


if __name__ == "__main__":
    main()
