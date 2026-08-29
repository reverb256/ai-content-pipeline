#!/usr/bin/env bash
# Deploy the canonical role contracts to ~/.hermes/profiles/<name>/SOUL.md
#
# Usage: bash scripts/deploy-profiles.sh [bot...]
#   (no args = deploy all six)
#
# The repo profiles/<name>/role.md is the canonical source of truth.
# This script copies it to the profile SOUL.md location.
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
BOTS=(scout researcher strategist writer distributor editor)

if [ $# -gt 0 ]; then
    BOTS=("$@")
fi

for bot in "${BOTS[@]}"; do
    SRC="$REPO/profiles/$bot/role.md"
    DEST="$HOME/.hermes/profiles/$bot/SOUL.md"
    if [ ! -f "$SRC" ]; then
        echo "[deploy] MISSING $SRC — skipping $bot"
        continue
    fi
    mkdir -p "$HOME/.hermes/profiles/$bot"
    cp "$SRC" "$DEST"
    chmod 600 "$DEST"
    echo "[deploy] $bot → SOUL.md ($(wc -l < "$DEST") lines)"
done

echo "[deploy] done. Verify:"
for bot in "${BOTS[@]}"; do
    [ -f "$HOME/.hermes/profiles/$bot/SOUL.md" ] && echo "  ✓ $bot"
done
