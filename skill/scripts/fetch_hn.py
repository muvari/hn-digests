#!/usr/bin/env python3
"""Fetch the top stories from a past day's Hacker News front page.

Scrapes https://news.ycombinator.com/front for the story list (rank, title,
url, points), then uses the Algolia HN API for full comment trees, and
fetches each article page for its text.

Writes one index file plus one JSON file per story so the caller can read
stories individually without loading everything into context at once.

Usage:
    python3 fetch_hn.py --out DIR [--day YYYY-MM-DD] [--top 20]

Output layout (inside --out):
    index.json      {date, stories: [{rank, id, title, url, points, ...}]}
    story_01.json   index entry + article_text + comment threads
    story_02.json   ...

Stdlib only; no pip installs needed.
"""

import argparse
import html
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Macintosh) hn-daily-digest/1.0"}

ARTICLE_TEXT_LIMIT = 6000       # chars of article text kept per story
ROOT_COMMENTS_KEPT = 6          # top-level comment threads per story
COMMENT_TEXT_LIMIT = 900        # chars kept per comment
REPLIES_PER_THREAD = 3          # direct replies kept per top-level comment


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        ctype = resp.headers.get("Content-Type", "")
        charset = "utf-8"
        m = re.search(r"charset=([\w-]+)", ctype)
        if m:
            charset = m.group(1)
        return resp.read().decode(charset, errors="replace"), ctype


def parse_front_page(page_html, top_n):
    """Pull rank/title/url/points/comment-count out of the /front HTML."""
    stories = []
    # Each story is a <tr class="athing submission" id="NNN"> row followed by
    # a subtext row. Split on the story rows and parse each chunk.
    chunks = re.split(r"<tr class=['\"]athing submission['\"] id=['\"](\d+)['\"]", page_html)
    # chunks: [preamble, id1, body1, id2, body2, ...]
    for i in range(1, len(chunks) - 1, 2):
        sid, body = chunks[i], chunks[i + 1]
        title_m = re.search(
            r"<span class=['\"]titleline['\"]>\s*<a href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", body
        )
        if not title_m:
            continue
        url, title = title_m.group(1), html.unescape(re.sub(r"<[^>]+>", "", title_m.group(2)))
        if url.startswith("item?id="):  # Ask HN / text posts link to themselves
            url = "https://news.ycombinator.com/" + url
        points_m = re.search(r"(\d+)\s*point", body)
        comments_m = re.search(r"(\d+)(?:&nbsp;|\s)comment", body)
        stories.append(
            {
                "rank": len(stories) + 1,
                "id": int(sid),
                "title": title,
                "url": url,
                "hn_url": f"https://news.ycombinator.com/item?id={sid}",
                "points": int(points_m.group(1)) if points_m else None,
                "num_comments": int(comments_m.group(1)) if comments_m else 0,
            }
        )
        if len(stories) >= top_n:
            break
    return stories


class TextExtractor(HTMLParser):
    """Crude readability: body text minus script/style/nav chrome."""

    SKIP = {"script", "style", "noscript", "svg", "header", "footer", "nav", "form", "iframe"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())


def extract_article_text(url):
    try:
        raw, ctype = get(url)
        if "html" not in ctype and "<html" not in raw[:2000].lower():
            return None, f"not html (content-type: {ctype.split(';')[0]})"
        p = TextExtractor()
        p.feed(raw)
        text = re.sub(r"\s+", " ", " ".join(p.parts)).strip()
        if len(text) < 200:
            return None, "extracted text too short (likely JS-rendered or paywalled)"
        return text[:ARTICLE_TEXT_LIMIT], None
    except Exception as e:  # noqa: BLE001 - report any fetch failure to caller
        return None, f"{type(e).__name__}: {e}"


def clean_comment_text(raw):
    if not raw:
        return ""
    text = re.sub(r"<p>", "\n", raw)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\n{2,}", "\n", text).strip()[:COMMENT_TEXT_LIMIT]


def fetch_comments(story_id):
    """Top comment threads from the Algolia items API (children come in HN rank order)."""
    raw, _ = get(f"https://hn.algolia.com/api/v1/items/{story_id}")
    item = json.loads(raw)
    threads = []
    for child in (item.get("children") or [])[:ROOT_COMMENTS_KEPT]:
        if not child.get("text"):
            continue
        thread = {
            "author": child.get("author"),
            "text": clean_comment_text(child["text"]),
            "replies": [
                {"author": r.get("author"), "text": clean_comment_text(r["text"])}
                for r in (child.get("children") or [])[:REPLIES_PER_THREAD]
                if r.get("text")
            ],
        }
        threads.append(thread)
    return threads


def enrich(story):
    if story["url"].startswith("https://news.ycombinator.com/item"):
        story["article_text"] = None
        story["article_fetch_error"] = "self post - the discussion IS the content"
    else:
        text, err = extract_article_text(story["url"])
        story["article_text"] = text
        story["article_fetch_error"] = err
    try:
        story["comment_threads"] = fetch_comments(story["id"])
    except Exception as e:  # noqa: BLE001
        story["comment_threads"] = []
        story["comments_fetch_error"] = f"{type(e).__name__}: {e}"
    return story


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--day", help="YYYY-MM-DD (default: HN's default = yesterday)")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    front_url = "https://news.ycombinator.com/front"
    if args.day:
        front_url += f"?day={args.day}"

    page, _ = get(front_url)
    date_m = re.search(r"front\?day=(\d{4}-\d{2}-\d{2})", page)
    # /front shows "day before" links; the shown date appears in the page title area
    shown_date_m = re.search(r"(\d{4}-\d{2}-\d{2})</font>", page) or date_m
    stories = parse_front_page(page, args.top)
    if not stories:
        sys.exit("ERROR: no stories parsed from /front - HN markup may have changed. "
                 "Fall back to fetching the page directly and parsing manually.")

    date = args.day or (shown_date_m.group(1) if shown_date_m else "unknown")

    with ThreadPoolExecutor(max_workers=8) as pool:
        stories = list(pool.map(enrich, stories))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    index = {
        "date": date,
        "front_url": front_url,
        "stories": [
            {k: s[k] for k in ("rank", "id", "title", "url", "hn_url", "points", "num_comments")}
            | {"article_ok": bool(s.get("article_text")), "story_file": f"story_{s['rank']:02d}.json"}
            for s in stories
        ],
    }
    (out / "index.json").write_text(json.dumps(index, indent=2))
    for s in stories:
        (out / f"story_{s['rank']:02d}.json").write_text(json.dumps(s, indent=2))

    print(f"Fetched {len(stories)} stories for {date} -> {out}/")
    for s in stories:
        flags = []
        if not s.get("article_text"):
            flags.append(f"NO ARTICLE TEXT ({s.get('article_fetch_error')})")
        if not s.get("comment_threads"):
            flags.append("NO COMMENTS")
        flag_str = ("  [" + "; ".join(flags) + "]") if flags else ""
        print(f"  {s['rank']:2d}. ({s['points']} pts, {s['num_comments']} comments) {s['title']}{flag_str}")


if __name__ == "__main__":
    main()
