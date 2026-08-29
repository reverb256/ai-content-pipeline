#!/usr/bin/env bash
# Scout run: X search recipes → candidate signals → kanban discovery.
# Run by cron (daily). Requires the media-browser CDP Chromium to be up.
#
# Usage: bash scripts/automation/scout-run.sh
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
LOG="$REPO/performance/scout-runs.log"

cd "$REPO"

# Ensure the browser is up (the real reverb256 session)
systemctl --user start media-browser.service 2>/dev/null || true
sleep 2

echo "$(date -Is) — scout run start" >> "$LOG"

# The actual discovery happens in the scout profile (it has the x_search tool).
# This wrapper ensures preconditions, then hands off to the scout profile.
hermes -p scout chat -q \
  "Run today's signal discovery. Use queries/x-search-recipes.md, read brain/RULINGS.md first. Return 1-3 strong signals as kanban tasks on board 'media' stage 'discovery' (or append to campaigns/<name>/signal.md). Do not draft content."

echo "$(date -Is) — scout run complete" >> "$LOG"
