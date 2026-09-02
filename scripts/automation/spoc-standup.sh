#!/usr/bin/env bash
# SPOC standup — snapshot the boards for the SPOC cron agent.
# The cron agent (default profile) is the SPOC and does the reasoning itself;
# this script ONLY gathers the board state so the agent has fresh data.
# Run by cron (daily) before the standup prompt.
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
SNAP="$REPO/performance/standups/board-snapshot.md"
LOG="$REPO/performance/spoc-standup.log"
mkdir -p "$(dirname "$SNAP")" "$(dirname "$LOG")"

echo "$(date -Is) — standup start" >> "$LOG"

# Snapshot board state for the standup summary
{
  echo "# Board snapshot — $(date -Is)"
  echo
  for b in media faceless-youtube; do
    echo "=== board: $b ==="
    hermes kanban --board "$b" list 2>/dev/null | grep -E "^▶|^●" | head -8 || true
    echo
  done
} > "$SNAP"

echo "Board snapshot written to $SNAP" >> "$LOG"
echo "$(date -Is) — snapshot complete" >> "$LOG"
