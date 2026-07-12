# HN Daily Digest

A daily archive of Hacker News front-page digests, generated automatically by a
Claude skill. Each `hn-digest-YYYY-MM-DD.html` is a self-contained page
summarizing the top 20 stories from that day's HN front page
(https://news.ycombinator.com/front): headline, category, a short article
summary, and a synthesis of the top comment threads. Cards are collapsible —
skim the headers, expand what interests you. Open any file in a browser;
light/dark mode follows your system setting.

## What's in this repo

```
hn-digest-YYYY-MM-DD.html   the daily digests (one per day)
skill/                      the Claude skill that generates them
├── SKILL.md                  instructions Claude follows
├── scripts/fetch_hn.py       fetcher (Python 3 stdlib only, no pip installs)
└── assets/template.html      HTML template for the digest page
scheduled-task/SKILL.md     reference copy of the daily routine's prompt
```

The live copies that actually run are in `~/.claude/` (see below); the copies
here are for backup and for setting up a new machine.

## Setting up on a new computer

Prerequisites: the Claude desktop app (or Claude Code) installed and signed in,
and `python3` available (`python3 --version` — the script needs nothing beyond
the standard library).

1. **Copy this repo** to the new machine, e.g. to `~/hn-digests`.

2. **Install the skill** — copy it to where Claude discovers personal skills:

   ```bash
   mkdir -p ~/.claude/skills
   cp -r ~/hn-digests/skill ~/.claude/skills/hn-daily-digest
   ```

3. **Recreate the daily routine** — scheduled tasks are per-machine, so in a
   new Claude session say something like:

   > Create a scheduled task that runs every morning at 7am using the prompt
   > in ~/hn-digests/scheduled-task/SKILL.md

   (That file contains the exact prompt the routine runs; Claude can copy it
   verbatim.) Then click **Run now** on the task once and approve its
   permission prompts, so future automatic runs never stall waiting for
   approval.

4. Scheduled tasks run while the Claude app is open — keep it running on an
   always-on machine. If the app was closed when a run was due, it runs on the
   next launch.

## Running one manually

In any Claude session: *"give me yesterday's HN digest"* — or a specific date
(*"HN digest for 2026-07-04"*), or a different size (*"just the top 10"*).

## Keeping this repo in sync

The daily routine commits each new digest after generating it, and re-syncs
`skill/` from `~/.claude/skills/hn-daily-digest/` first, so skill edits are
captured too. If you edit the skill and want it archived immediately:

```bash
cp -r ~/.claude/skills/hn-daily-digest/* ~/hn-digests/skill/
cd ~/hn-digests && git add -A && git commit -m "Update skill"
```
