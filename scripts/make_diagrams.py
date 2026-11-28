"""Generate the SVG diagrams used in the report (reports/diagrams/*.svg): control-flow graph, fishbones, Pareto, risk matrix.

Usage: python scripts/make_diagrams.py
The numbers of the Pareto come from DEFECTS below, which mirrors docs/team/RCA.md (16 defects, root-cause class of each).
"""

import html
import os
import textwrap

OUT = os.path.join(os.path.dirname(__file__), "..", "reports", "diagrams")
FONT = "font-family='Segoe UI, Arial, sans-serif'"
INK, MUTED, LINE, ACCENT, WARN = "#1b1b1b", "#555", "#7a8794", "#0b4f9e", "#b3261e"


def svg(width, height, body, title):
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {height}' width='100%' role='img' "
        f"aria-label='{html.escape(title)}' {FONT}><title>{html.escape(title)}</title>"
        f"<rect width='{width}' height='{height}' fill='#ffffff'/>"
        "<defs><marker id='a' markerWidth='8' markerHeight='8' refX='7' refY='4' orient='auto'>"
        f"<path d='M0,0 L8,4 L0,8 z' fill='{LINE}'/></marker></defs>{body}</svg>"
    )


def text(x, y, s, size=11, anchor="middle", weight="normal", fill=INK):
    return (
        f"<text x='{x}' y='{y}' font-size='{size}' text-anchor='{anchor}' font-weight='{weight}' "
        f"fill='{fill}'>{html.escape(s)}</text>"
    )


def box(cx, cy, w, h, lines, fill="#eef1f5", stroke=LINE):
    parts = [
        f"<rect x='{cx - w / 2}' y='{cy - h / 2}' width='{w}' height='{h}' rx='5' fill='{fill}' stroke='{stroke}'/>"
    ]
    start = cy - (len(lines) - 1) * 7 + 4
    for i, line in enumerate(lines):
        parts.append(text(cx, start + i * 14, line, 11, weight="bold" if i == 0 else "normal"))
    return "".join(parts)


def edge(points, label=None, lx=0, ly=0, color=LINE):
    d = " ".join(f"{x},{y}" for x, y in points)
    out = f"<polyline points='{d}' fill='none' stroke='{color}' stroke-width='1.5' marker-end='url(#a)'/>"
    if label:
        out += text(lx, ly, label, 11, weight="bold", fill=ACCENT)
    return out


def cfg():
    b = []
    cx, rx, ex = 140, 400, 640
    chain = {1: 40, 2: 120, 3: 200, 4: 280, 6: 360, 8: 440}
    b.append(box(cx, chain[1], 200, 40, ["N1", "entry: participation = ..."], "#e3ecf7"))
    b.append(box(cx, chain[2], 200, 40, ["N2 (D1)", "participation is not None"]))
    b.append(box(cx, chain[3], 200, 40, ["N3 (D2)", "state == CONFIRMED"]))
    b.append(box(cx, chain[4], 200, 40, ["N4 (D3)", "not user_can_decline_confirmed"]))
    b.append(box(cx, chain[6], 200, 40, ["N6 (D4)", "state == RESPONSIBLE_REJECTED"]))
    b.append(box(cx, chain[8], 200, 40, ["N8 (D5)", "state == USER_DECLINED"]))
    b.append(box(rx, chain[4], 150, 40, ["N5", "raise DeclineDisallowed"], "#fbe9e7", WARN))
    b.append(box(rx, chain[6], 150, 40, ["N7", "raise ActionDisallowed"], "#fbe9e7", WARN))
    b.append(box(rx, chain[8], 150, 40, ["N9", "raise DeclineDisallowed"], "#fbe9e7", WARN))
    b.append(box(ex, 330, 160, 260, ["N10", "exit / return None"], "#e3f3e6", "#2e7d32"))
    for a, c in ((1, 2), (2, 3), (3, 4), (4, 6), (6, 8)):
        label = None if a == 1 else ("F" if a == 4 or a == 6 else "T")
        # N2->N3 T, N3->N4 T, N4->N6 F, N6->N8 F
        b.append(edge([(cx, chain[a] + 20), (cx, chain[c] - 20)], label, cx + 12, (chain[a] + chain[c]) / 2 + 4))
    b.append(edge([(cx + 100, chain[4]), (rx - 75, chain[4])], "T", 255, chain[4] - 6))
    b.append(edge([(cx + 100, chain[6]), (rx - 75, chain[6])], "T", 255, chain[6] - 6))
    b.append(edge([(cx + 100, chain[8]), (rx - 75, chain[8])], "T", 255, chain[8] - 6))
    for y in (280, 360, 440):
        b.append(edge([(rx + 75, y), (ex - 80, y)]))
    b.append(edge([(cx + 100, chain[2]), (ex, chain[2]), (ex, 200)], "F", 250, chain[2] - 6))
    b.append(edge([(cx - 100, chain[3]), (20, chain[3]), (20, chain[6]), (cx - 100, chain[6])], "F", 30, chain[3] + 16))
    b.append(edge([(cx, chain[8] + 20), (cx, 500), (ex, 500), (ex, 460)], "F", cx + 12, 492))
    b.append(text(370, 534, "V(G) = E - N + 2P = 14 - 10 + 2 = 6 (5 decision nodes + 1). T = condition true, F = false.", 11, fill=MUTED))
    return svg(740, 546, "".join(b), "Control-flow graph of check_participation_state, V(G) = 6")


def fishbone(title, effect, causes):
    """causes: list of (category, text); the first half is drawn above the spine, the rest below."""
    w, h, spine = 920, 470, 235
    b = [f"<line x1='30' y1='{spine}' x2='700' y2='{spine}' stroke='{INK}' stroke-width='3' marker-end='url(#a)'/>"]
    b.append(box(810, spine, 190, 110, effect, "#fbe9e7", WARN))
    half = (len(causes) + 1) // 2
    for idx, (cat, cause) in enumerate(causes):
        top = idx < half
        col = idx if top else idx - half
        x = 190 + col * 215
        y_label = 28 if top else h - 20
        y_bone = 95 if top else h - 85
        b.append(f"<line x1='{x - 30}' y1='{y_bone}' x2='{x + 40}' y2='{spine}' stroke='{LINE}' stroke-width='2'/>")
        b.append(text(x - 30, y_label, cat, 13, "middle", "bold", ACCENT))
        lines = textwrap.wrap(cause, 30)
        base = 60 if top else h - 150
        for i, line in enumerate(lines[:6]):
            b.append(text(x - 130, base + i * 13, line, 10.5, "start", fill=INK))
    return svg(w, h, "".join(b), title)


DEFECTS = {  # id: (root-cause class, severity, status)
    "001": ("Unenforced error-signalling contract", "major", "closed"),
    "002": ("Input / partition not handled", "major", "closed"),
    "003": ("Input / partition not handled", "minor", "closed"),
    "004": ("Input / partition not handled", "minor", "closed"),
    "005": ("Framework defaults / contract not specified or hardened", "minor", "open"),
    "006": ("Framework defaults / contract not specified or hardened", "minor", "open"),
    "007": ("Framework defaults / contract not specified or hardened", "minor", "open"),
    "008": ("Accessibility not part of the definition of done", "major", "closed"),
    "009": ("Accessibility not part of the definition of done", "major", "open"),
    "010": ("Accessibility not part of the definition of done", "major", "open"),
    "011": ("Third-party component not verified", "major", "open"),
    "012": ("Accessibility not part of the definition of done", "minor", "open"),
    "013": ("Error-message design (one generic message)", "minor", "open"),
    "014": ("Third-party component not verified", "minor", "open"),
    "015": ("Framework defaults / contract not specified or hardened", "minor", "open"),
    "016": ("Framework defaults / contract not specified or hardened", "minor", "open"),
}


def pareto():
    counts = {}
    for cls, _, _ in DEFECTS.values():
        counts[cls] = counts.get(cls, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: -kv[1])
    total = sum(counts.values())
    w, h, left, top, plot_w, plot_h = 860, 350, 60, 30, 740, 240
    b = []
    for k in range(0, total + 1, 4):
        y = top + plot_h - k / total * plot_h
        b.append(f"<line x1='{left}' y1='{y}' x2='{left + plot_w}' y2='{y}' stroke='#e3e6ea'/>")
        b.append(text(left - 8, y + 4, str(k), 10, "end", fill=MUTED))
        b.append(text(left + plot_w + 8, y + 4, f"{round(k / total * 100)} %", 10, "start", fill=MUTED))
    y80 = top + plot_h - 0.8 * plot_h
    b.append(f"<line x1='{left}' y1='{y80}' x2='{left + plot_w}' y2='{y80}' stroke='{WARN}' stroke-dasharray='5 4'/>")
    b.append(text(left + plot_w - 4, y80 - 4, "80 %", 10, "end", fill=WARN))
    slot = plot_w / len(ordered)
    cum, pts = 0, []
    for i, (cls, n) in enumerate(ordered):
        cum += n
        bw = slot * 0.6
        x = left + i * slot + (slot - bw) / 2
        bh = n / total * plot_h
        b.append(f"<rect x='{x}' y='{top + plot_h - bh}' width='{bw}' height='{bh}' fill='#9db8d6' stroke='{ACCENT}'/>")
        inside = bh >= 30
        b.append(text(x + bw / 2, top + plot_h - bh + (16 if inside else -5), str(n), 11, weight="bold"))
        pts.append((x + bw / 2, top + plot_h - cum / total * plot_h, cum))
        for j, line in enumerate(textwrap.wrap(cls, 24)[:4]):
            b.append(text(x + bw / 2, top + plot_h + 16 + j * 12, line, 10))
    b.append(f"<polyline points='{' '.join(f'{x},{y}' for x, y, _ in pts)}' fill='none' stroke='{WARN}' stroke-width='2'/>")
    for x, y, c in pts:
        b.append(f"<circle cx='{x}' cy='{y}' r='3.5' fill='{WARN}'/>")
        b.append(text(x, y - 8, f"{round(c / total * 100)} %", 10, fill=WARN))
    b.append(text(left, 16, f"Pareto of the {total} defects by root-cause class (bars: count, line: cumulative share)", 12, "start", "bold"))
    return svg(w, h, "".join(b), f"Pareto chart of {total} defects by root-cause class"), counts, total


def main():
    os.makedirs(OUT, exist_ok=True)
    f1 = [
        ("Code", "return instead of raise in one checker; inconsistent with siblings"),
        ("Tests", "line never executed by upstream tests; no negative test for inactive events"),
        ("Design", "error signalling relies on convention (exceptions collected by a loop), not types"),
        ("Process", "no mutation testing, no contract test, coverage not gated on this file"),
        ("Environment / data", "inactive events hidden in the UI hide the path from manual testing"),
        ("People", "defensive code written without a failing test first (inference)"),
    ]
    f2 = [
        ("Code", "direct cleaned_data[...] indexing; cross-field logic in clean_<field>"),
        ("Tests", "only valid-input form tests upstream; no invalid-partition tests"),
        ("Design", "date and time split into separate fields combined later"),
        ("Process", "no input-validation checklist or EP technique in upstream review"),
        ("Environment / data", "UI widgets prevent invalid input in manual use, so it never surfaced"),
        ("People", "happy-path bias (inference)"),
    ]
    files = {
        "cfg_check_participation_state.svg": cfg(),
        "fishbone_defect001.svg": fishbone("Fishbone DEFECT-001", ["DEFECT-001", "inactive event", "still accepts", "signup"], f1),
        "fishbone_defect002.svg": fishbone("Fishbone DEFECT-002", ["DEFECT-002", "ShiftForm KeyError", "(HTTP 500) on", "invalid date/time"], f2),
    }
    pareto_svg, counts, total = pareto()
    files["pareto_defects.svg"] = pareto_svg
    for name, content in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        print("wrote", name, len(content), "bytes")
    print({k: v for k, v in sorted(counts.items(), key=lambda kv: -kv[1])}, "total", total)


if __name__ == "__main__":
    main()
