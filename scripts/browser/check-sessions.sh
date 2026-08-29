#!/usr/bin/env bash
# Check session status across all registered sites via the CDP browser.
# Reads the live media-browser (real reverb256 profile) and reports which
# sites are signed in. Updates the human-readable status; registry.md is the
# source of truth.
#
# Usage: bash scripts/browser/check-sessions.sh
set -euo pipefail

PORT="${MEDIA_BROWSER_PORT:-9222}"

if ! curl -s --max-time 3 "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
    echo "media-browser CDP not reachable on :${PORT} — start it:"
    echo "  systemctl --user start media-browser.service"
    exit 1
fi

echo "=== Session check via CDP (:${PORT}) ==="
echo "(Verification happens through the browser; see platforms/registry.md for the authoritative table.)"

# GitHub
GH=$(curl -s --max-time 5 "http://127.0.0.1:${PORT}/json" | python3 -c "
import sys, json
tabs = json.load(sys.stdin)
for t in tabs:
    if t.get('type') == 'page' and 'github.com' in t.get('url', ''):
        print('github-tab-found')
        break
")
echo "GitHub tab: ${GH:-no-github-tab}"

# X
X=$(curl -s --max-time 5 "http://127.0.0.1:${PORT}/json" | python3 -c "
import sys, json
tabs = json.load(sys.stdin)
for t in tabs:
    if t.get('type') == 'page' and 'x.com' in t.get('url', ''):
        print('x-tab-found')
        break
")
echo "X tab: ${X:-no-x-tab}"

echo ""
echo "Full DOM-level verification (signed-in state) runs through browser_exec."
echo "For an automated check across all sites, use the browser session check"
echo "pattern in docs/api-capture-procedure.md or add site-specific probes."
