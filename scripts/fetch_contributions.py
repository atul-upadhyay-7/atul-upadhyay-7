#!/usr/bin/env python3
"""
fetch_contributions.py
Scrape the public GitHub contribution calendar for atul-upadhyay-7.
No personal access token required — uses the same public endpoint the
profile page uses.
Output: data/contributions.json
"""

import json
import re
import os
from datetime import datetime, date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "atul-upadhyay-7"
URL = f"https://github.com/users/{USERNAME}/contributions"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_days() -> list[dict]:
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    # Each day cell is a <td data-date="YYYY-MM-DD" ...>
    for td in soup.select("td[data-date]"):
        date_str = td["data-date"]
        level = int(td.get("data-level", 0))

        # The contribution count lives in the sibling <tool-tip> text
        count = 0
        tip = td.find("tool-tip") or td.find_next_sibling("tool-tip")
        if tip:
            m = re.search(r"(\d[\d,]*)\s+contribution", tip.get_text())
            if m:
                count = int(m.group(1).replace(",", ""))

        days.append({"date": date_str, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    # Current streak (backwards from today)
    today = date.today().isoformat()
    streak = 0
    for d in reversed(days):
        if d["date"] > today:
            continue
        if d["count"] > 0:
            streak += 1
        else:
            break

    # Longest streak
    longest = cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0

    # Best day
    best = max(days, key=lambda d: d["count"], default={"date": "", "count": 0})

    # Monthly totals
    monthly: dict[str, int] = {}
    for d in days:
        month = d["date"][:7]
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "total": total,
        "current_streak": streak,
        "longest_streak": longest,
        "best_day": best,
        "monthly": monthly,
    }


def main():
    print(f"Fetching contributions for {USERNAME}…")
    days = fetch_days()
    stats = compute_stats(days)

    out = {
        "username": USERNAME,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "stats": stats,
        "days": days,
    }

    Path("data").mkdir(exist_ok=True)
    with open("data/contributions.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"  → {len(days)} days,  {stats['total']:,} total contributions")
    print(f"  → current streak {stats['current_streak']} days, "
          f"longest {stats['longest_streak']} days")
    print("  → written to data/contributions.json")


if __name__ == "__main__":
    main()
