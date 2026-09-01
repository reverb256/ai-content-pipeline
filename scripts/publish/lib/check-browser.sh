#!/usr/bin/env bash
# Publisher helper — verify media-browser (CDP) is up before publishing.
# All publish scripts source this. Exits 1 if the browser is down.
set -euo pipefail

BROWSER_PORT="${BROWSER_PORT:-9222}"
LOG_TAG="[publish]"

log() { echo "$LOG_TAG $(date +%H:%M:%S) $*"; }

# media-browser.service (or manual CDP Chromium) must be listening on :9222
if ! curl -s --max-time 3 "http://127.0.0.1:${BROWSER_PORT}/json/version" >/dev/null 2>&1; then
  log "ERROR: CDP browser not reachable on :${BROWSER_PORT}"
  log "Start it: systemctl --user start media-browser.service  (or launch chromium --remote-debugging-port=9222 --user-data-dir=~/.config/chromium)"
  exit 1
fi

log "CDP browser OK on :${BROWSER_PORT}"
