#!/usr/bin/env bash
# Advance a faceless-youtube kanban card to the next stage.
# Usage: advance-stage.sh <card-id> <new-stage>
# The bot calls this when it finishes its stage, so the driver picks it up
# at the next stage.
set -euo pipefail

CARD="${1:?usage: advance-stage.sh <card-id> <new-stage>}"
STAGE="${2:?usage: advance-stage.sh <card-id> <new-stage>}"
BOARD="faceless-youtube"

# Update the card body's "stage:" line (the oracle set it; we rewrite it).
# Use kanban comment + a marker so the driver's stage_of finds the new stage.
# Simplest robust approach: comment with "stage: <new-stage>" — stage_of greps
# the most recent stage: line from the card body.
hermes kanban --board "$BOARD" comment "$CARD" "stage: $STAGE" 2>&1 | tail -1
echo "card $CARD advanced to stage: $STAGE"
