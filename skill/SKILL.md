---
name: hn-daily-digest
description: Generate an HTML digest of the top stories (20 by default) from the previous day's Hacker News front page — headline, category, article summary, and a summary of the top comment threads. Use this whenever the user asks for a Hacker News summary, HN digest, "what happened on Hacker News", yesterday's top HN stories/links, or a summary of HN discussions/comments — even if they don't say "digest" or specify a date. Also use for a specific past day's HN front page (it takes a date).
---

# Hacker News Daily Digest

Produce a polished, self-contained HTML page summarizing the top stories from a past day's HN front page (https://news.ycombinator.com/front — defaults to yesterday), including what each article says and what the HN commenters thought of it. Default to the top 20 stories; honor a different count if the user asks for one (pass `--top N` to the fetcher).

## Step 1: Fetch the data

Run the bundled fetcher (stdlib-only, no installs). Point `--out` at a scratch directory:

```bash
python3 <skill-dir>/scripts/fetch_hn.py --out <scratch>/hn-data [--day YYYY-MM-DD]
```

- Omit `--day` for the default (yesterday). Pass it only if the user asked for a specific date.
- It writes `index.json` (story list) plus one `story_NN.json` per story, each containing extracted `article_text` and `comment_threads` (top ~6 threads with top replies, in HN rank order).
- The stdout summary flags stories with `NO ARTICLE TEXT` or `NO COMMENTS` — note these for Step 2.
- If it errors with "no stories parsed", HN's markup changed: fetch the front page yourself (WebFetch or curl) and build equivalent per-story JSON before continuing.

## Step 2: Read and understand each story

Read the story files one at a time (they're sized to be context-friendly). For each story produce:

1. **Category** — a short label (1–3 words) for the *kind* of story, e.g. "AI & ML", "Databases", "Security", "Space", "Show HN", "Programming", "Business", "Science", "Policy". Invent an apt label when none of these fit; the goal is that a reader scanning badges gets the day's shape at a glance.
2. **Article summary** — 2–4 sentences on what the piece actually says (its argument, findings, or announcement), not a restatement of the headline. The extracted `article_text` is crude (nav chrome may leak in at the start); skip past boilerplate to the substance.
3. **Comment summary** — 3–5 bullets capturing the *shape of the conversation*: the dominant opinions, major disagreements, notable first-hand anecdotes or expert corrections. Attribute stances to "commenters" generally, not usernames, unless a specific comment is the story. Don't just summarize the first comment — synthesize across threads, and note when the room disagrees with the article.

**Fallbacks when `article_text` is missing:** use WebFetch on the story URL (handles JS-rendered pages; for PDFs, summarize from the title, domain, and what commenters say the paper contains). For self-posts (Ask HN/Tell HN), the discussion *is* the content — summarize the post text from the HN item and lean the summary on the threads.

## Step 3: Generate the HTML page

Use `<skill-dir>/assets/template.html`: copy it, replace the `{{...}}` placeholders (`{{TOP_N}}` is the story count), and emit one `<details class="card">` per story at `{{CARDS}}`, following the card structure documented in the template's comment exactly. Cards are collapsible: the `<summary>` holds the always-visible header (rank, category badge, linked headline, meta line with points/comment-count linked to the HN item) and the `<div class="card-body">` holds the article summary and comment bullets. Emit cards without the `open` attribute so the page starts collapsed for skimming.

- Preserve the headline text as it appeared on HN; link it to the article URL (for self-posts, the HN item).
- Meta line domain: bare hostname without `www.` (e.g. `clickhouse.com`).
- HTML-escape story titles and any text you quote.
- Save as `hn-digest-<YYYY-MM-DD>.html` in the current working directory unless the user asked for a different location.

## Step 4: Deliver

Tell the user where the file is and offer to open it. If an Artifact tool is available and the user wants a shareable page, publish it there too. End with a one-line TL;DR of the day (e.g. the biggest story and the overall theme).
