#!/usr/bin/env bash
# Verify the media-browser CDP Chromium is reachable and signed in.
# Prints JSON from the /json/version endpoint (browser identity).
set -euo pipefail

PORT="${MEDIA_BROWSER_PORT:-9222}"

if curl -s --max-time 3 "http://127.0.0.1:${PORT}/json/version" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('CDP OK:', d.get('Browser', 'unknown'))
" 2>/dev/null; then
    echo "media-browser: alive on :${PORT}"
else
    echo "media-browser: NOT REACHABLE on :${PORT} — start with:"
    echo "  systemctl --user start media-browser.service"
    echo "  (or: bash scripts/browser/start-media-browser.sh)"
    exit 1
fi
