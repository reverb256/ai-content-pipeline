#!/usr/bin/env bash
# Create a new campaign: copy the template, create the kanban task.
# Usage: bash scripts/new-campaign.sh "<campaign name>"
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
NAME="${1:?usage: new-campaign.sh '<campaign name>'}"

SLUG=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | tr ' /' '--' | tr -cd 'a-z0-9-')
DIR="$REPO/campaigns/$SLUG"

mkdir -p "$DIR"
cp "$REPO/campaigns/_TEMPLATE.md" "$DIR/campaign.md"
sed -i "s/^# Campaign: .*/# Campaign: $NAME/" "$DIR/campaign.md"
echo "[campaign] created $DIR/campaign.md"

# Create the kanban task on board 'media'
if hermes kanban boards list 2>/dev/null | grep -q media; then
    hermes kanban boards switch media 2>/dev/null || true
fi
hermes kanban create "campaign: $NAME" 2>&1 | tail -2 || echo "[campaign] (kanban task creation skipped — board may need creating)"

echo "[campaign] next: scout fills signal.md, then the pipeline runs."
