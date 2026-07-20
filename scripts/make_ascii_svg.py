#!/usr/bin/env python3
"""
make_ascii_svg.py [prepped-image.png]

Downsamples the prepped photo to a character grid, maps brightness to a
density ramp, and writes a monochrome SVG where each row "types" itself
in left-to-right, staggered top to bottom, then freezes.

Output: avi-ascii.svg  (rename inside this file if you want a different name)
"""
import sys
import numpy as np
from PIL import Image

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
COLS = 100
ROWS = 53
CHAR_W = 6.2
CHAR_H = 11
FONT_SIZE = 11
FILL = "#8fd3ff"          # single monochrome accent color
ROW_DURATION = 0.55       # seconds per row wipe
ROW_STAGGER = 0.045       # seconds between successive rows starting


def image_to_rows(path: str):
    img = Image.open(path).convert("L").resize((COLS, ROWS))
    arr = np.array(img, dtype=np.float32) / 255.0  # 0=black .. 1=white
    rows = []
    for r in range(ROWS):
        line = []
        for c in range(COLS):
            # brightness 1.0 (white) -> ramp start (space); 0.0 (black) -> ramp end
            idx = int((1.0 - arr[r, c]) * (len(RAMP) - 1))
            line.append(RAMP[idx])
        rows.append("".join(line))
    return rows


def escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(rows) -> str:
    width = COLS * CHAR_W + 20
    height = ROWS * CHAR_H + 20

    parts = [
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Menlo, Consolas, monospace" font-size="{FONT_SIZE}">',
        f'<rect width="100%" height="100%" fill="#0d1117"/>',
        "<style>",
        f"text {{ fill: {FILL}; white-space: pre; }}",
        "</style>",
    ]

    for r, text in enumerate(rows):
        y = 15 + r * CHAR_H
        row_width = len(text) * CHAR_W
        start = ROW_STAGGER * r
        clip_id = f"clip{r}"
        parts.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="10" y="{y - FONT_SIZE:.1f}" width="0" height="{CHAR_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{row_width:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            f"</rect>"
            f"</clipPath>"
        )
        parts.append(
            f'<text x="10" y="{y:.1f}" clip-path="url(#{clip_id})">{escape(text)}</text>'
        )
        # small block cursor riding the wipe edge
        parts.append(
            f'<rect x="10" y="{y - FONT_SIZE:.1f}" width="6" height="{CHAR_H:.1f}" fill="{FILL}" opacity="0.85">'
            f'<animate attributeName="x" from="10" to="{10 + row_width:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            f'<animate attributeName="opacity" from="0.85" to="0" '
            f'begin="{start + ROW_DURATION:.3f}s" dur="0.15s" fill="freeze"/>'
            f"</rect>"
        )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    rows = image_to_rows(src)
    svg = build_svg(rows)
    with open("avi-ascii.svg", "w") as f:
        f.write(svg)
    print("wrote avi-ascii.svg")
