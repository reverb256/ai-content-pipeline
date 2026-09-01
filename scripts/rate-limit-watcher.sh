#!/bin/bash
# rate-limit-watcher.sh — scan logs for model/provider errors, alert + self-heal
# Run by cron (every 30 min). Dispatches COO when a provider is saturated.
set -uo pipefail

LOG_DIR="$HOME/.hermes/logs"
REPORT_DIR="$HOME/Projects/ai-content-pipeline/performance/rate-limits"
mkdir -p "$REPORT_DIR"
STAMP=$(date +%Y%m%d-%H%M%S)
REPORT="$REPORT_DIR/$STAMP.md"

# Count errors in the last 6 hours (approximate window via log tail)
WINDOW=2000  # lines to scan (recent activity)
ERRORS=$(tail -n $WINDOW "$LOG_DIR/agent.log" 2>/dev/null | grep -cE "RateLimitError|HTTP 429")
QUOTA=$(tail -n $WINDOW "$LOG_DIR/agent.log" 2>/dev/null | grep -cE "HTTP 402|Add credits|quota")
AUTH=$(tail -n $WINDOW "$LOG_DIR/agent.log" 2>/dev/null | grep -cE "HTTP 401|Invalid API key|AuthError")

# Which providers are erroring most
PROVIDER_HITS=$(tail -n $WINDOW "$LOG_DIR/agent.log" 2>/dev/null | grep -oE "provider=[a-z-]+" | sort | uniq -c | sort -rn | head -5)

{
  echo "# Rate-Limit Watch — $STAMP"
  echo
  echo "Window: last $WINDOW log lines"
  echo
  echo "| Error class | Count |"
  echo "|---|---|"
  echo "| HTTP 429 / RateLimit | $ERRORS |"
  echo "| HTTP 402 / Quota | $QUOTA |"
  echo "| HTTP 401 / Auth | $AUTH |"
  echo
  echo "## Top providers by error"
  echo "\`\`\`"
  echo "$PROVIDER_HITS"
  echo "\`\`\`"
} > "$REPORT"

# Threshold: if >5 rate-limit OR >2 quota OR >2 auth in window -> alert + dispatch COO
if [ "$ERRORS" -gt 5 ] || [ "$QUOTA" -gt 2 ] || [ "$AUTH" -gt 2 ]; then
  echo "ALERT: rate-limit anomalies detected (429=$ERRORS 402=$QUOTA 401=$AUTH)"
  # Circuit-breaker emulation: identify the worst provider from the hits, write a cooldown marker
  WORST=$(echo "$PROVIDER_HITS" | head -1 | awk '{print $2}' | sed 's/provider=//')
  if [ -n "$WORST" ]; then
    COOLDOWN_DIR="$HOME/.hermes/state/provider-cooldowns"
    mkdir -p "$COOLDOWN_DIR"
    echo "$(date +%s)" > "$COOLDOWN_DIR/$WORST"
    echo "CIRCUIT OPEN: $WORST (cooldown marker written)"
  fi
  # Dispatch COO to diagnose + self-heal (repin/switch providers)
  # Guard against nested-default-profile collision: COO is a dedicated profile
  timeout 240 hermes -p coo chat -q "Rate-limit watch alert. Scan $LOG_DIR/agent.log + errors.log for the error signatures in $REPORT. Diagnose which providers are saturated and fix the fallback chains or repin cron jobs per the standing directive (always deal with model/rate-limit errors). Reply with what you changed." --oneshot 2>&1 | tail -15
  exit 2  # alert fired
fi

echo "OK: no anomalies (429=$ERRORS 402=$QUOTA 401=$AUTH)"
exit 0
