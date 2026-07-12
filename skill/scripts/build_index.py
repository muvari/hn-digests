#!/usr/bin/env python3
"""Build a calendar-view index.html for an HN digest archive repo.

Scans <repo>/digests/ for files named hn-digest-YYYY-MM-DD.html and writes
<repo>/index.html: one calendar grid per month (newest first), where each day
that has a digest is a clickable link. Self-contained output, styled to match
the digest pages, light/dark aware. Stdlib only.

Usage:
    python3 build_index.py --repo /path/to/archive-repo
"""

import argparse
import calendar
import datetime
import re
from pathlib import Path

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hacker News Daily Digest — Archive</title>
<style>
  :root {
    --bg: #f6f6ef; --card: #ffffff; --text: #1a1a1a; --muted: #666;
    --accent: #ff6600; --border: #e2e0d5; --badge-bg: #fff3ea; --badge-text: #b34700;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #16161a; --card: #1f1f26; --text: #e8e8e6; --muted: #9a9aa3;
      --accent: #ff7a26; --border: #2e2e38; --badge-bg: #33251b; --badge-text: #ffab70;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  .wrap { max-width: 980px; margin: 0 auto; padding: 32px 20px 64px; }
  header { border-bottom: 3px solid var(--accent); padding-bottom: 16px; margin-bottom: 28px; }
  header h1 { margin: 0 0 4px; font-size: 26px; }
  header .sub { color: var(--muted); font-size: 14px; }
  .months { display: flex; flex-wrap: wrap; gap: 18px; }
  .month {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 18px; width: 296px; flex-grow: 0;
  }
  .month h2 { margin: 0 0 12px; font-size: 16px; }
  .grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
  .dow {
    text-align: center; font-size: 11px; font-weight: 600; color: var(--muted);
    text-transform: uppercase; padding-bottom: 2px;
  }
  .day {
    aspect-ratio: 1; display: flex; align-items: center; justify-content: center;
    border-radius: 8px; font-size: 14px; color: var(--muted);
  }
  a.day {
    background: var(--badge-bg); color: var(--badge-text); font-weight: 700;
    text-decoration: none; border: 1px solid transparent;
  }
  a.day:hover { background: var(--accent); color: #fff; }
  .day.today { border: 1px solid var(--accent); }
  footer { margin-top: 40px; color: var(--muted); font-size: 13px; text-align: center; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Hacker News Daily Digest</h1>
    <div class="sub">{{COUNT}} archived digests · highlighted days are clickable · updated {{UPDATED}}</div>
  </header>
  <div class="months">
{{MONTHS}}
  </div>
  <footer>summaries by Claude · source: news.ycombinator.com</footer>
</div>
</body>
</html>
"""


def month_section(year, month, dates, today):
    cal = calendar.Calendar(firstweekday=6)  # Sunday-first
    cells = [f'<div class="dow">{d}</div>' for d in ("S", "M", "T", "W", "T", "F", "S")]
    for week in cal.monthdayscalendar(year, month):
        for day in week:
            if day == 0:
                cells.append('<div class="day"></div>')
                continue
            date = datetime.date(year, month, day)
            today_cls = " today" if date == today else ""
            if date in dates:
                cells.append(
                    f'<a class="day{today_cls}" href="digests/hn-digest-{date.isoformat()}.html" '
                    f'title="Digest for {date.isoformat()}">{day}</a>'
                )
            else:
                cells.append(f'<div class="day{today_cls}">{day}</div>')
    name = f"{calendar.month_name[month]} {year}"
    return (
        f'    <section class="month">\n      <h2>{name}</h2>\n'
        f'      <div class="grid">{"".join(cells)}</div>\n    </section>'
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="archive repo root (contains digests/)")
    args = ap.parse_args()
    repo = Path(args.repo)

    dates = set()
    for f in (repo / "digests").glob("hn-digest-*.html"):
        m = re.fullmatch(r"hn-digest-(\d{4}-\d{2}-\d{2})\.html", f.name)
        if m:
            dates.add(datetime.date.fromisoformat(m.group(1)))
    if not dates:
        raise SystemExit(f"no digest files found in {repo / 'digests'}")

    today = datetime.date.today()
    months = sorted({(d.year, d.month) for d in dates}, reverse=True)
    sections = "\n".join(month_section(y, m, dates, today) for y, m in months)

    out = (
        PAGE.replace("{{MONTHS}}", sections)
        .replace("{{COUNT}}", str(len(dates)))
        .replace("{{UPDATED}}", today.isoformat())
    )
    (repo / "index.html").write_text(out)
    print(f"wrote {repo / 'index.html'}: {len(dates)} digests across {len(months)} month(s)")


if __name__ == "__main__":
    main()
