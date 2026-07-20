#!/usr/bin/env python3
"""
make_info_card.py
Generate a neofetch-style info-card SVG that fades in line by line.
Edit the DATA list below with your own details, then run:
    python scripts/make_info_card.py
Output: info-card.svg
"""

import os

# ── Personalise this ─────────────────────────────────────────────────────────
TITLE   = "atul-upadhyay-7@github"
DIVIDER = "─" * 22

DATA = [
    ("OS",        "Arch Linux (Cloud-Native Edition)"),
    ("Role",      "Full-Stack Developer · Cloud Engineer"),
    ("Now",       "Building Cloud-Native & DevOps solutions"),
    ("Prev",      "KubeEdge Contributor · Open-Source Dev"),
    ("Stack",     "Go · Python · TypeScript · React · K8s"),
    ("Infra",     "AWS · GCP · Docker · Terraform · CI/CD"),
    ("Interests", "Microservices · Serverless · 3D Gaming 🎮"),
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
    anim = (
        ""
        if STATIC
        else f'style="animation: fadeSlide 0.4s ease both {delay:.2f}s"'
    )
    kx = PADDING_X
    vx = PADDING_X + 130
    return (
        f'  <g {anim}>\n'
        f'    <text x="{kx}" y="{y}" class="key">{key}</text>\n'
        f'    <text x="{vx}" y="{y}" class="val">{value}</text>\n'
        f'  </g>\n'
    )


def build_svg() -> str:
    lines: list[str] = []

    css = """
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .root { font-family: 'JetBrains Mono', monospace; font-size: 11px; }
    .title { font-size: 13px; font-weight: 700; fill: #39d353; }
    .div   { fill: #30363d; font-size: 10px; }
    .key   { fill: #58a6ff; font-weight: 700; }
    .val   { fill: #e6edf3; }
    @keyframes fadeSlide {
      0%   { opacity: 0; transform: translateX(-6px); }
      100% { opacity: 1; transform: translateX(0); }
    }
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
    t_anim = "" if STATIC else 'style="animation: fadeSlide 0.4s ease both 0s"'
    lines.append(
        f'  <text x="{PADDING_X}" y="{ty}" class="title" {t_anim}>{TITLE}</text>\n'
    )

    # Divider
    dy = ty + H_LINE
    d_anim = "" if STATIC else 'style="animation: fadeSlide 0.4s ease both 0.1s"'
    lines.append(
        f'  <text x="{PADDING_X}" y="{dy}" class="div" {d_anim}>{DIVIDER}</text>\n'
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
