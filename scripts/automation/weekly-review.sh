#!/usr/bin/env bash
# Weekly performance review: pull analytics → keep/test/stop lists → kanban.
# Run by cron (weekly). Proposes playbook changes; j_kro approves before the
# brain updates.
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
LOG="$REPO/performance/weekly-reviews.log"

cd "$REPO"

systemctl --user start media-browser.service 2>/dev/null || true
sleep 2

echo "$(date -Is) — weekly review start" >> "$LOG"

hermes -p editor chat -q \
  "Run the weekly performance review. Read brain/RULINGS.md, brain/playbooks/performance.md, and the recent campaign records in campaigns/. Pull what analytics we can reach via the CDP browser. Return three lists (keep / test / stop) with the posts supporting each. Post to kanban board 'media' as a performance task. Do not update any playbook until j_kro approves."

echo "$(date -Is) — weekly review complete" >> "$LOG"
