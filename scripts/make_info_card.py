#!/usr/bin/env python3
"""
make_info_card.py
Generate a neofetch-style info-card SVG that fades in line by line.
Edit the DATA list below with your own details, then run:
    python scripts/make_info_card.py
Output: info-card.svg
"""

import os
import html as _html


def esc(s: str) -> str:
    """Escape XML special characters for safe embedding in SVG text nodes."""
    return _html.escape(str(s), quote=False)

# ── Personalise this ─────────────────────────────────────────────────────────
TITLE   = "atul-upadhyay-7@github"
DIVIDER = "─" * 22

DATA = [
    ("OS",        "Arch Linux (Cloud-Native Edition)"),
    ("Role",      "Full-Stack Developer · Cloud Engineer"),
    ("Now",       "Building Cloud-Native and DevOps solutions"),
    ("Prev",      "KubeEdge Contributor · Open-Source Dev"),
    ("Stack",     "Go · Python · TypeScript · React · K8s"),
    ("Infra",     "AWS · GCP · Docker · Terraform · CI/CD"),
    ("Interests", "Microservices · Serverless · 3D Gaming"),
    ("Contact",   "atulupadhyay192@gmail.com"),
    ("LinkedIn",  "linkedin.com/in/atulupadhyay192"),
    ("LeetCode",  "leetcode.com/atul_upadhyay"),
]
# ─────────────────────────────────────────────────────────────────────────────

W, H_LINE = 490, 18
PADDING_X, PADDING_Y = 16, 14
TITLE_H = 32
LINES = len(DATA) + 2          # +2 for title + divider
TOTAL_H = TITLE_H + PADDING_Y + LINES * H_LINE + PADDING_Y + 8

KEY_COLOR  = "#58a6ff"   # blue
VAL_COLOR  = "#e6edf3"   # near-white
TTL_COLOR  = "#39d353"   # green
DIV_COLOR  = "#30363d"   # muted
BG_COLOR   = "#0d1117"
BORDER_COL = "#30363d"

STATIC = os.environ.get("STATIC", "0") == "1"   # set STATIC=1 for frozen frame


def row_svg(index: int, key: str, value: str, y: int, delay: float) -> str:
    kx = PADDING_X
    vx = PADDING_X + 130
    if STATIC:
        return (
            f'  <g>\n'
            f'    <text x="{kx}" y="{y}" class="key">{key}</text>\n'
            f'    <text x="{vx}" y="{y}" class="val">{value}</text>\n'
            f'  </g>\n'
        )
    smil = (f'<animate attributeName="opacity" from="0" to="1" '
            f'dur="0.4s" begin="{delay:.2f}s" fill="freeze"/>')
    return (
        f'  <g opacity="0">\n'
        f'    {smil}\n'
        f'    <text x="{kx}" y="{y}" class="key">{esc(key)}</text>\n'
        f'    <text x="{vx}" y="{y}" class="val">{esc(value)}</text>\n'
        f'  </g>\n'
    )


def build_svg() -> str:
    lines: list[str] = []

    # NOTE: No @import – GitHub's CSP blocks external resources in img SVGs.
    # Animations use SMIL <animate> so they work on github.com.
    css = """
  <style>
    .root  { font-family: ui-monospace,'Cascadia Code','Source Code Pro',
              Menlo,Consolas,'DejaVu Sans Mono',monospace; font-size: 11px; }
    .title { font-size: 13px; font-weight: bold; fill: #39d353; }
    .div   { fill: #30363d; font-size: 10px; }
    .key   { fill: #58a6ff; font-weight: bold; }
    .val   { fill: #e6edf3; }
  </style>
"""
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{TOTAL_H}" '
        f'viewBox="0 0 {W} {TOTAL_H}" class="root">\n'
        f'  <rect width="100%" height="100%" fill="{BG_COLOR}" rx="8" '
        f'stroke="{BORDER_COL}" stroke-width="1"/>\n'
        + css
    )

    # Title bar
    ty = PADDING_Y + 14
    if STATIC:
        t_smil = ""
        t_opacity = ""
    else:
        t_smil = '<animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="0s" fill="freeze"/>'
        t_opacity = 'opacity="0"'
    lines.append(
        f'  <text x="{PADDING_X}" y="{ty}" class="title" {t_opacity}>{esc(TITLE)}{"" if STATIC else t_smil}</text>\n'
    )

    # Divider
    dy = ty + H_LINE
    if STATIC:
        d_smil = ""
        d_opacity = ""
    else:
        d_smil = '<animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="0.1s" fill="freeze"/>'
        d_opacity = 'opacity="0"'
    lines.append(
        f'  <text x="{PADDING_X}" y="{dy}" class="div" {d_opacity}>{esc(DIVIDER)}{"" if STATIC else d_smil}</text>\n'
    )

    # Data rows
    for i, (key, value) in enumerate(DATA):
        y     = dy + (i + 1) * H_LINE
        delay = 0.15 + i * 0.07
        lines.append(row_svg(i, key, value, y, delay))

    lines.append("</svg>")
    return "".join(lines)


def main():
    svg = build_svg()
    with open("info-card.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Written info-card.svg  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
