#!/usr/bin/env python3
"""Build index.html for an HN digest archive repo.

The landing page mirrors the LATEST digest (its styles and story cards are
extracted straight from the newest file in <repo>/digests/, so the index never
drifts from the digest design), plus an "Archive" button in the toolbar that
unfolds a clickable calendar of every archived day.

Scans <repo>/digests/ for files named hn-digest-YYYY-MM-DD.html and writes
<repo>/index.html. Stdlib only.

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
<title>Hacker News Daily Digest</title>
<style>
{{DIGEST_STYLE}}
  /* --- archive calendar (index-only) --- */
  #archive-panel { margin: 0 0 20px; }
  .archive-note { color: var(--muted); font-size: 13px; margin: 0 0 10px; }
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
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Hacker News Daily Digest</h1>
    <div class="sub">{{SUB}} · <a href="digests/hn-digest-{{LATEST}}.html">permalink</a></div>
  </header>

  <div class="controls">
    <button onclick="setAll(true)">Expand all</button>
    <button onclick="setAll(false)">Collapse all</button>
    <button onclick="toggleArchive()" id="archive-btn">&#128197; Archive</button>
  </div>

  <div id="archive-panel" hidden>
    <p class="archive-note">{{COUNT}} archived {{DIGEST_WORD}} · highlighted days are clickable</p>
    <div class="months">
{{MONTHS}}
    </div>
  </div>

{{CARDS}}

  <footer>latest digest shown · summaries by Claude · source: news.ycombinator.com</footer>
</div>
<script>
function setAll(open) {
  document.querySelectorAll('details.card').forEach(d => d.open = open);
}
function toggleArchive() {
  const p = document.getElementById('archive-panel');
  p.hidden = !p.hidden;
}
</script>
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
        f'      <section class="month">\n        <h2>{name}</h2>\n'
        f'        <div class="grid">{"".join(cells)}</div>\n      </section>'
    )


def extract(pattern, text, what, path):
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        raise SystemExit(f"could not extract {what} from {path} - "
                         "digest markup may have drifted from the template")
    return m.group(1)


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

    latest = max(dates)
    latest_path = repo / "digests" / f"hn-digest-{latest.isoformat()}.html"
    digest = latest_path.read_text()
    # strip HTML comments first so a leftover template comment (which contains
    # example card markup) can't pollute the extraction
    digest = re.sub(r"<!--.*?-->", "", digest, flags=re.DOTALL)

    style = extract(r"<style>(.*?)</style>", digest, "stylesheet", latest_path)
    sub = extract(r'<div class="sub">(.*?)</div>', digest, "subtitle", latest_path)
    cards = extract(r'(<details class="card">.*</details>)', digest, "story cards", latest_path)

    today = datetime.date.today()
    months = sorted({(d.year, d.month) for d in dates}, reverse=True)
    sections = "\n".join(month_section(y, m, dates, today) for y, m in months)

    out = (
        PAGE.replace("{{DIGEST_STYLE}}", style)
        .replace("{{SUB}}", sub)
        .replace("{{LATEST}}", latest.isoformat())
        .replace("{{MONTHS}}", sections)
        .replace("{{COUNT}}", str(len(dates)))
        .replace("{{DIGEST_WORD}}", "digest" if len(dates) == 1 else "digests")
        .replace("{{CARDS}}", cards)
    )
    (repo / "index.html").write_text(out)
    print(f"wrote {repo / 'index.html'}: mirrors {latest.isoformat()}, "
          f"{len(dates)} digests across {len(months)} month(s)")


if __name__ == "__main__":
    main()
