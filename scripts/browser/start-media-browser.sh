#!/usr/bin/env bash
# Launch the headless CDP Chromium that the AI content pipeline uses.
# Runs the REAL reverb256 profile so bots browse/post as reverb256.
#
# Used by: systemd user unit media-browser.service
# Manual:   bash scripts/browser/start-media-browser.sh
#
# Flags:
#   --headless=new  modern headless: SAME profile + cookie store as headed
#   --remote-debugging-port=9222  CDP endpoint for browser_exec / API capture
#   --user-data-dir  the real Chromium profile (signed-in accounts)
#   --password-store=gnome-libsecret  real keyring so cookies decrypt
set -euo pipefail

PROFILE_DIR="${MEDIA_BROWSER_PROFILE:-$HOME/.config/chromium}"
PORT="${MEDIA_BROWSER_PORT:-9222}"
URL="${MEDIA_BROWSER_URL:-https://github.com/reverb256}"

# Sanity: is something already on the port?
if curl -s --max-time 2 "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
    echo "media-browser: CDP already listening on :${PORT} — nothing to do."
    exit 0
fi

echo "media-browser: launching headless Chromium (profile=${PROFILE_DIR}, port=${PORT})"
exec chromium \
    --headless=new \
    --remote-debugging-port="${PORT}" \
    --user-data-dir="${PROFILE_DIR}" \
    --password-store=gnome-libsecret \
    --no-first-run \
    --no-default-browser-check \
    --disable-background-networking \
    --disable-component-update \
    --disable-sync \
    "${URL}"
