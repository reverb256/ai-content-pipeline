#!/usr/bin/env bash
# Opportunity Oracle run: X-search arbitrage scan → scored production cards.
# Run by cron (daily). The oracle finds where demand outruns supply and routes
# the content machine.
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
LOG="$REPO/performance/oracle-runs.log"

cd "$REPO"

echo "$(date -Is) — oracle run start" >> "$LOG"

hermes -p oracle chat -q \
  "Run today's arbitrage scan. Read brain/playbooks/arbitrage.md and brain/RULINGS.md first. Use the x_search tool to run the demand and supply gap queries on candidate topics. Score opportunities with the rubric (demand × gap × monetization × automation × platform, policy safety as gate). Post scored production cards (score > 6) to kanban board 'faceless-youtube' stage 'opportunity'. Add score 4-6 items to the watchlist. Do NOT produce content — you are the gate, not the factory."

echo "$(date -Is) — oracle run complete" >> "$LOG"
