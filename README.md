# HN Daily Digest

A daily archive of Hacker News front-page digests, generated automatically by a
Claude skill. Each `digests/hn-digest-YYYY-MM-DD.html` is a self-contained page
summarizing the top 20 stories from that day's HN front page
(https://news.ycombinator.com/front): headline, category, a short article
summary, and a synthesis of the top comment threads. Cards are collapsible —
skim the headers, expand what interests you. `index.html` is a clickable
calendar of the whole archive. Light/dark mode follows your system setting.

## What's in this repo

```
index.html                  calendar landing page (auto-rebuilt daily)
digests/                    the daily digests, one per day
skill/                      the Claude skill that generates them
├── SKILL.md                  instructions Claude follows
├── scripts/fetch_hn.py        fetcher (Python 3 stdlib only, no pip installs)
├── scripts/build_index.py     rebuilds the calendar index.html
└── assets/template.html       HTML template for the digest page
scheduled-task/SKILL.md     reference copy of the daily routine's prompt
.nojekyll                   tells GitHub Pages to serve files as-is
```

The live copies that actually run are in `~/.claude/` (see below); the copies
here are for backup and for setting up a new machine.

## GitHub Pages

With Pages enabled (repo Settings → Pages → Deploy from a branch → `main`,
`/ (root)`), the calendar is served at
`https://<username>.github.io/hn-digests/` and every push redeploys it
automatically. The daily routine pushes after committing, so the site updates
itself each morning. Note: Pages sites are public.

## Setting up on a new computer

Prerequisites: the Claude desktop app (or Claude Code) installed and signed in,
and `python3` available (`python3 --version` — the scripts need nothing beyond
the standard library).

1. **Clone this repo**:

   ```bash
   git clone https://github.com/muvari/hn-digests.git ~/hn-digests
   ```

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
   approval. Pushing requires git credentials for the repo on that machine
   (e.g. `gh auth login`).

4. Scheduled tasks run while the Claude app is open — keep it running on an
   always-on machine. If the app was closed when a run was due, it runs on the
   next launch.

## Running one manually

In any Claude session: *"give me yesterday's HN digest"* — or a specific date
(*"HN digest for 2026-07-04"*), or a different size (*"just the top 10"*).

## Keeping this repo in sync

The daily routine re-syncs `skill/` from `~/.claude/skills/hn-daily-digest/`,
rebuilds `index.html`, commits, and pushes to `origin` (when one is
configured). So: edit the skill in `~/.claude/skills/`, and the repo catches up
each morning. To sync immediately:

```bash
cp -r ~/.claude/skills/hn-daily-digest/* ~/hn-digests/skill/
python3 ~/hn-digests/skill/scripts/build_index.py --repo ~/hn-digests
cd ~/hn-digests && git add -A && git commit -m "Update skill" && git push
```
