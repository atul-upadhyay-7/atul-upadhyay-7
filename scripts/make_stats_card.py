#!/usr/bin/env python3
"""
make_stats_card.py
Generate a self-hosted GitHub stats SVG using the GitHub REST API (no token
needed for public data — uses the unauthenticated public API, rate-limited
to 60 req/hr per IP, which is fine for a daily cron).
Output: stats-card.svg
"""

import json
import os
import math
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

USERNAME = "atul-upadhyay-7"
API_BASE = "https://api.github.com"
HEADERS  = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "profile-stats-card/1.0",
}

# ── dimensions ──────────────────────────────────────────────────────────────
W, H = 860, 160
PAD  = 20

# colours
BG      = "#0d1117"
BORDER  = "#30363d"
GREEN   = "#39d353"
BLUE    = "#58a6ff"
MUTED   = "#8b949e"
WHITE   = "#e6edf3"
ORANGE  = "#f0883e"
PURPLE  = "#bc8cff"

FONT = ("ui-monospace,'Cascadia Code','Source Code Pro',"
        "Menlo,Consolas,'DejaVu Sans Mono',monospace")


def fetch_user() -> dict:
    r = requests.get(f"{API_BASE}/users/{USERNAME}", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_repos() -> list:
    repos, page = [], 1
    while True:
        r = requests.get(
            f"{API_BASE}/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def load_contributions() -> int:
    try:
        with open("data/contributions.json") as f:
            return json.load(f)["stats"]["total"]
    except Exception:
        return 0


def lang_bar(langs: dict[str, int], bar_w: int = 820, bar_h: int = 8) -> tuple[str, list]:
    """Return (bar SVG string, sorted_langs list)."""
    total = sum(langs.values()) or 1
    parts = []
    legend = []
    LANG_COLORS = {
        "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#2b7489",
        "Go": "#00ADD8",     "Java": "#b07219",       "C++": "#f34b7d",
        "HTML": "#e34c26",   "CSS": "#563d7c",         "Shell": "#89e051",
        "Rust": "#dea584",   "Ruby": "#701516",        "Swift": "#F05138",
    }
    x = 0
    sorted_l = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:6]
    for lang, count in sorted_l:
        pct = count / total
        w   = math.floor(pct * bar_w)
        color = LANG_COLORS.get(lang, "#8b949e")
        parts.append(
            f'<rect x="{x}" y="0" width="{w}" height="{bar_h}" '
            f'rx="2" fill="{color}"/>'
        )
        x += w
        legend.append((lang, color, f"{pct*100:.1f}%"))
    return "\n".join(parts), legend


def make_svg(user: dict, repos: list, contributions: int) -> str:
    # aggregate
    stars  = sum(r.get("stargazers_count", 0) for r in repos)
    forks  = sum(r.get("forks_count", 0)      for r in repos)
    pub    = user.get("public_repos", 0)
    followers = user.get("followers", 0)

    # language totals
    langs: dict[str, int] = {}
    for r in repos:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1

    bar_svg, legend = lang_bar(langs, bar_w=W - 2 * PAD)

    # ── metrics row ─────────────────────────────────────────────────────────
    metrics = [
        ("⭐", f"{stars:,}", "Stars"),
        ("🍴", f"{forks:,}", "Forks"),
        ("📦", f"{pub}",    "Repos"),
        ("👥", f"{followers}", "Followers"),
        ("🔥", f"{contributions:,}", "Contributions"),
    ]
    col_w  = (W - 2 * PAD) // len(metrics)
    metric_rows = []
    for i, (icon, val, lbl) in enumerate(metrics):
        cx = PAD + (i + 0.5) * col_w
        metric_rows.append(
            f'<text x="{cx:.0f}" y="50" text-anchor="middle" '
            f'font-size="18" font-weight="bold" fill="{WHITE}">{val}</text>\n'
            f'<text x="{cx:.0f}" y="67" text-anchor="middle" '
            f'font-size="9" fill="{MUTED}">{lbl}</text>'
        )

    # ── legend row ──────────────────────────────────────────────────────────
    leg_parts = []
    lx = PAD
    for lang, color, pct in legend:
        leg_parts.append(
            f'<rect x="{lx}" y="110" width="8" height="8" rx="2" fill="{color}"/>'
            f'<text x="{lx+11}" y="118" font-size="9" fill="{MUTED}">'
            f'{lang} {pct}</text>'
        )
        lx += 12 + len(lang) * 6 + 40

    updated = datetime.utcnow().strftime("%Y-%m-%d")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="100%" height="100%" fill="{BG}" rx="8"
        stroke="{BORDER}" stroke-width="1"/>
  <style>
    text {{ font-family: {FONT}; }}
  </style>

  <!-- title -->
  <text x="{PAD}" y="25" font-size="11" fill="{BLUE}" letter-spacing="1">
    atul@github ~ $ git stats --overview</text>

  <!-- metrics -->
  {"".join(f'<g>{m}</g>' for m in metric_rows)}

  <!-- language bar -->
  <g transform="translate({PAD}, 80)">
    {bar_svg}
  </g>

  <!-- legend -->
  {"".join(leg_parts)}

  <!-- updated stamp -->
  <text x="{W - PAD}" y="{H - 6}" text-anchor="end"
        font-size="8" fill="{BORDER}">updated {updated}</text>
</svg>"""
    return svg


def main():
    print(f"Fetching GitHub stats for {USERNAME}…")
    user  = fetch_user()
    repos = fetch_repos()
    contributions = load_contributions()

    print(f"  → {user.get('public_repos')} repos, "
          f"{sum(r.get('stargazers_count',0) for r in repos)} stars, "
          f"{contributions:,} contributions")

    svg = make_svg(user, repos, contributions)
    Path("stats-card.svg").write_text(svg, encoding="utf-8")
    print(f"  → written stats-card.svg ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
