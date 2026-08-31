#!/usr/bin/env bash
# SPOC standup — the chief-of-staff rhythm. Reviews the boards, summarizes
# what moved, identifies blockers, and decides the next move.
# Run by cron (daily). Invokes the default (SPOC) profile.
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
LOG="$REPO/performance/spoc-standup.log"
mkdir -p "$(dirname "$LOG")"

echo "$(date -Is) — standup start" >> "$LOG"

# Snapshot board state for the standup summary
BOARDS=$(cd "$REPO" && for b in media faceless-youtube; do
  echo "=== board: $b ==="
  hermes kanban --board "$b" list 2>/dev/null | grep -E "^▶|^●" | head -8 || true
done)

# SPOC reviews and posts the standup
hermes -p default chat -q \
"Run the daily standup for the content machine (you are the chief of staff / SPOC).

Board state:
$BOARDS

For each board: what moved since yesterday (cards completed/advanced), what is stuck (cards with no progress), and the ONE next move you recommend. Post this as a kanban comment on the highest-priority stuck/ready card, or create a summary task on the 'media' board titled 'standup: <date>' with the full summary.

Rules:
- You are the orchestrator, not the doer. Do NOT do the work yourself — route it.
- If a card is stuck (e.g. no stage label, failed bot), decide: reassign, retry, or escalate to j_kro.
- Keep it short: done / stuck / one next move per board.
- Save the summary to $REPO/performance/standups/<date>.md"

echo "$(date -Is) — standup complete" >> "$LOG"
