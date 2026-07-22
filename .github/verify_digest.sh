#!/usr/bin/env bash
# Assert that today's run actually produced a valid digest.
#
# This exists because the "Commit and push" step treats "no changes to commit"
# as exit 0, so a run where Claude generated nothing would still be reported as
# a green success. This script makes that case fail LOUDLY instead: the daily
# job calls it as a hard gate before committing (and as a soft check to decide
# whether to retry generation).
#
# Contract: a digest file for yesterday (UTC) must exist, be the newest digest
# present, and contain a plausible number of story cards. Run from the repo root.
set -euo pipefail

EXPECTED=$(date -u -d 'yesterday' +%F)   # the front-page day this run covers
FILE="digests/hn-digest-${EXPECTED}.html"
NEWEST=$(ls digests/hn-digest-*.html 2>/dev/null \
           | sed -E 's:.*/hn-digest-(.*)\.html:\1:' | sort | tail -1)

if [ ! -f "$FILE" ]; then
  echo "::error::expected digest $FILE was not created (newest present: ${NEWEST:-none})"
  exit 1
fi

# If the newest digest isn't today's, generation almost certainly did nothing
# (the classic ~2-minute no-op run).
if [ "$NEWEST" != "$EXPECTED" ]; then
  echo "::error::newest digest is $NEWEST but expected $EXPECTED — generation produced no fresh digest"
  exit 1
fi

# Catch truncated output (a partial run that wrote only a handful of cards).
# Real digests have 30; the template's example card can add 1, so 25 is a safe
# lower bound that still flags anything clearly incomplete.
CARDS=$(grep -c '<details class="card">' "$FILE" || true)
if [ "$CARDS" -lt 25 ]; then
  echo "::error::digest $FILE has only $CARDS story cards (<25) — likely truncated"
  exit 1
fi

echo "verified $FILE: $CARDS story cards"
