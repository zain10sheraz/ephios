"""Report documents whose Markdown tables do not render (raw pipe rows left in paragraphs)."""

import glob
import os
import re
import sys

import markdown

ROOT = os.path.join(os.path.dirname(__file__), "..")
bad = 0
for f in sorted(
    glob.glob(os.path.join(ROOT, "docs", "team", "*.md"))
    + glob.glob(os.path.join(ROOT, "reports", "*", "*.md"))
):
    with open(f, encoding="utf-8") as handle:
        source = handle.read()
    html = markdown.markdown(source, extensions=["tables", "fenced_code", "sane_lists"])
    for p in re.findall(r"<p>(.*?)</p>", html, re.DOTALL):
        if "|---" in p.replace(" ", "") or p.count("|") >= 6:
            bad += 1
            print(os.path.relpath(f, ROOT), "->", p[:110].replace("\n", " "))
print("broken blocks:", bad)
sys.exit(1 if bad else 0)
