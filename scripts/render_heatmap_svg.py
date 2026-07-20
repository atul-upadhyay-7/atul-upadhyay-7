#!/usr/bin/env python3
"""
render_heatmap_svg.py
Read data/contributions.json and write contrib-heatmap.svg.
The SVG is a 53-week × 7-day contribution calendar with:
 - GitHub-green colour ramp
 - diagonal slide-in reveal animation (CSS keyframes, plays once on load)
 - stats footer (total / streak / best day)
 - Less → More legend
"""

import json
import math
from datetime import datetime
from pathlib import Path

DATA_FILE  = "data/contributions.json"
OUT_FILE   = "contrib-heatmap.svg"

# Colour ramp: 0 = no contributions → 5 = maximum
PALETTE = [
    "#161b22",  # 0 – background/none
    "#0e4429",  # 1
    "#006d32",  # 2
    "#26a641",  # 3
    "#39d353",  # 4
    "#69f0a0",  # 5 – brightest (neon top)
]

BOX   = 11   # px per cell (square)
GAP   = 2    # px gap between cells
COLS  = 53   # weeks
ROWS  = 7    # days per week (Mon-Sun)

LABEL_LEFT  = 28   # space for day labels (Mon/Wed/Fri)
LABEL_TOP   = 20   # space for month labels

TOTAL_W = LABEL_LEFT + COLS * (BOX + GAP) + 20
TOTAL_H = LABEL_TOP  + ROWS * (BOX + GAP) + 60  # extra for footer

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def level_from_count(count: int, max_count: int) -> int:
    if count == 0:
        return 0
    if max_count == 0:
        return 1
    ratio = count / max_count
    if ratio < 0.15:
        return 1
    if ratio < 0.35:
        return 2
    if ratio < 0.60:
        return 3
    if ratio < 0.80:
        return 4
    return 5


def build_grid(days: list[dict]) -> list[list[dict | None]]:
    """Build a [col][row] grid of day dicts (None = padding)."""
    if not days:
        return []

    from datetime import date as dt_date
    first = datetime.fromisoformat(days[0]["date"]).date()
    # Align to Monday of that week
    start = first - __import__("datetime").timedelta(days=first.weekday())

    grid: list[list[dict | None]] = []
    col: list[dict | None] = []
    day_map = {d["date"]: d for d in days}

    cursor = start
    while True:
        date_str = cursor.isoformat()
        col.append(day_map.get(date_str, None))
        if len(col) == 7:
            grid.append(col)
            col = []
        if len(grid) >= COLS:
            break
        cursor += __import__("datetime").timedelta(days=1)

    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)

    return grid[:COLS]


def month_labels(grid: list[list[dict | None]]) -> list[tuple[int, str]]:
    """Return (col_index, month_name) for month transitions."""
    labels = []
    seen = set()
    for ci, col in enumerate(grid):
        for cell in col:
            if cell:
                month = cell["date"][5:7]
                if month not in seen:
                    seen.add(month)
                    m_name = MONTHS[int(month) - 1]
                    labels.append((ci, m_name))
                break
    return labels


def make_svg(data: dict) -> str:
    days  = data["days"]
    stats = data["stats"]

    max_count = max((d["count"] for d in days), default=1)
    grid = build_grid(days)

    # Pre-compute diagonal order for animation (diagonal = col + row)
    max_diag = (COLS - 1) + (ROWS - 1)
    anim_dur  = 1.8   # seconds total reveal
    anim_delay_per_diag = anim_dur / max_diag

    parts: list[str] = []

    # ── CSS ─────────────────────────────────────────────────────────────────
    # NOTE: No @import – GitHub's CSP blocks external URLs in img-embedded SVGs.
    # Font: system monospace stack; animations: SMIL <animate> only.
    css = """
    <style>
      .hm-root { font-family: ui-monospace,'Cascadia Code','Source Code Pro',
                  Menlo,Consolas,'DejaVu Sans Mono',monospace; }
      .label      { font-size: 9px;  fill: #8b949e; }
      .stat-val   { font-size: 12px; fill: #e6edf3; font-weight: bold; }
      .stat-lbl   { font-size: 9px;  fill: #8b949e; }
      .title      { font-size: 11px; fill: #58a6ff; letter-spacing: 1px; }
      .legend-lbl { font-size: 9px;  fill: #8b949e; }
    </style>
"""
    parts.append(f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{TOTAL_W}" height="{TOTAL_H}"
     viewBox="0 0 {TOTAL_W} {TOTAL_H}"
     class="hm-root">
  <rect width="100%" height="100%" fill="#0d1117" rx="8"/>
{css}
""")

    # ── Title ────────────────────────────────────────────────────────────────
    parts.append(f'  <text x="{LABEL_LEFT}" y="13" class="title">'
                 f'atul@github ~ $ ./contributions.sh</text>\n')

    # ── Month labels ─────────────────────────────────────────────────────────
    for ci, mname in month_labels(grid):
        x = LABEL_LEFT + ci * (BOX + GAP)
        parts.append(f'  <text x="{x}" y="{LABEL_TOP - 4}" class="label">{mname}</text>\n')

    # ── Day labels ───────────────────────────────────────────────────────────
    for row_i, lbl in DAY_LABELS.items():
        y = LABEL_TOP + row_i * (BOX + GAP) + BOX - 1
        parts.append(f'  <text x="0" y="{y}" class="label">{lbl}</text>\n')

    # ── Cells ────────────────────────────────────────────────────────────────
    for ci, col in enumerate(grid):
        for ri, cell in enumerate(col):
            x = LABEL_LEFT + ci * (BOX + GAP)
            y = LABEL_TOP  + ri * (BOX + GAP)
            if cell is None:
                color = "#0d1117"
                tip   = ""
                cnt   = 0
            else:
                cnt   = cell["count"]
                lv    = cell.get("level") or level_from_count(cnt, max_count)
                color = PALETTE[min(lv, 5)]
                tip   = f'{cnt} contribution{"s" if cnt != 1 else ""} on {cell["date"]}'

            diag  = ci + ri
            delay = round(diag * anim_delay_per_diag, 3)

            # SMIL animate: GitHub renders these in <img>-embedded SVGs
            smil = (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'dur="0.3s" begin="{delay}s" fill="freeze"/>'
                if cell is not None else ""
            )
            opacity_attr = 'opacity="0"' if cell is not None else ""

            parts.append(
                f'  <rect x="{x}" y="{y}" rx="2" ry="2" '
                f'width="{BOX}" height="{BOX}" fill="{color}" {opacity_attr}>'
                + (f'<title>{tip}</title>' if tip else "")
                + smil
                + '</rect>\n'
            )

    # ── Legend ───────────────────────────────────────────────────────────────
    legend_y  = LABEL_TOP + ROWS * (BOX + GAP) + 10
    legend_x0 = TOTAL_W - (len(PALETTE) * (BOX + GAP)) - 50
    parts.append(f'  <text x="{legend_x0 - 4}" y="{legend_y + BOX - 1}" '
                 f'class="legend-lbl">Less</text>\n')
    for i, col in enumerate(PALETTE):
        lx = legend_x0 + i * (BOX + GAP)
        parts.append(f'  <rect class="cell" x="{lx}" y="{legend_y}" '
                     f'width="{BOX}" height="{BOX}" fill="{col}"/>\n')
    parts.append(f'  <text x="{legend_x0 + len(PALETTE) * (BOX + GAP) + 2}" '
                 f'y="{legend_y + BOX - 1}" class="legend-lbl">More</text>\n')

    # ── Stats footer ─────────────────────────────────────────────────────────
    footer_y = legend_y + BOX + 18
    stat_items = [
        (f'{stats["total"]:,}',         "contributions"),
        (f'{stats["current_streak"]}d',  "current streak"),
        (f'{stats["longest_streak"]}d',  "longest streak"),
        (f'{stats["best_day"]["count"]}', f'best day ({stats["best_day"]["date"]})'),
    ]
    col_w = TOTAL_W // len(stat_items)
    for i, (val, lbl) in enumerate(stat_items):
        cx = (i + 0.5) * col_w
        parts.append(f'  <text x="{cx:.0f}" y="{footer_y}" '
                     f'text-anchor="middle" class="stat-val">{val}</text>\n')
        parts.append(f'  <text x="{cx:.0f}" y="{footer_y + 13}" '
                     f'text-anchor="middle" class="stat-lbl">{lbl}</text>\n')

    parts.append("</svg>")
    return "".join(parts)


def main():
    with open(DATA_FILE) as f:
        data = json.load(f)

    svg = make_svg(data)
    Path(OUT_FILE).write_text(svg, encoding="utf-8")
    print(f"Written {OUT_FILE}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
