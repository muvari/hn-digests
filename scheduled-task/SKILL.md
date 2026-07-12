---
name: hn-daily-digest
description: Generate the daily Hacker News digest and archive it in ~/hn-digests/
---

Use the hn-daily-digest skill (installed at ~/.claude/skills/hn-daily-digest/) to generate the daily Hacker News digest.

Follow the skill's instructions exactly:
1. Run its bundled fetcher script (scripts/fetch_hn.py) with no --day argument, so it picks up the previous day's front page from https://news.ycombinator.com/front. Point --out at a scratch directory. Use the script's default story count (top 20).
2. Read each story file it produces and write the digest per the skill: category badge, 2-4 sentence article summary, and 3-5 bullets synthesizing the top comment threads, rendered with the skill's assets/template.html (collapsible cards, collapsed by default).
3. Save the finished page as /Users/mark/hn-digests/hn-digest-<YYYY-MM-DD>.html, where the date is the front-page day the digest covers (i.e., yesterday's date). If a file for that date already exists, overwrite it — a rerun should refresh the same day's digest, not create duplicates.

Success criteria: the HTML file exists in /Users/mark/hn-digests/ with 20 story cards. Finish by reporting the file path and a one-line TL;DR of the day's biggest story.