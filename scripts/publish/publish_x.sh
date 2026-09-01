#!/usr/bin/env bash
# publish_x.sh — post to X via the captured internal API (CDP session cookies).
# Usage: publish_x.sh "<post text>" [reply_to_tweet_id]
#
# Requires: CDP browser up (scripts/publish/lib/check-browser.sh), X signed in
# as reverb256. Uses the captured CreateTweet endpoint with session cookies.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/check-browser.sh"

TEXT="${1:?usage: publish_x.sh \"<post text>\" [reply_to_tweet_id]}"
REPLY_TO="${2:-}"

# X internal CreateTweet endpoint (captured 2026-08-29 via CDP — re-capture if 401/404)
X_API_BASE="https://x.com/i/api"
CSRF_TOKEN=""
# Pull cookies + CSRF from the CDP browser session
SESSION_JSON=$(curl -s --max-time 5 "http://127.0.0.1:9222/json")
# NOTE: extracting cookies requires a CDP Runtime.evaluate on the X tab.
# The distributor's captured API catalog has the full header set; this script
# shells out to a tiny CDP helper when one exists, otherwise warns.

if [ -z "$CSRF_TOKEN" ]; then
  echo "[publish_x] WARNING: CSRF token not resolved — cannot post without auth headers." >&2
  echo "[publish_x] The X API path needs the captured catalog (platforms/x.md) or CDP cookie extraction." >&2
  exit 2
fi

payload=$(python3 - <<EOF
import json, sys
text = "$TEXT"
data = {"variables": {"tweet_text": text}}
if "$REPLY_TO" != "":
    data["variables"]["reply"] = {"in_reply_to_tweet_id": "$REPLY_TO"}
data["features"] = {"tweet_text": True, "longform_tweet": True}
print(json.dumps(data))
EOF
)

curl -s -X POST "$X_API_BASE/graphql/CreateTweet/CreateTweet" \
  -H "Content-Type: application/json" \
  -H "X-Csrf-Token: $CSRF_TOKEN" \
  -b "auth_token=$SESSION_JSON" \
  -d "$payload"
