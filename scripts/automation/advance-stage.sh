#!/usr/bin/env bash
# Advance a kanban card to the next stage.
# Usage: advance-stage.sh <card-id> <new-stage> [--board <slug>]
#   BOARD=<slug> in the env also works. Default: faceless-youtube (unchanged).
#
# The bot calls this when it finishes its stage, so the driver picks it up
# at the next stage. On the music board (stage map: music/stages.yaml) the
# stages are: brief -> genre-select -> lyrics -> generate -> curate -> stems
# -> master -> gate -> package -> visual -> human-approval -> publish -> track.
#
# BOARD-PARAMETERIZED 2026-10-16 (t_38e84953): this script previously
# hardcoded BOARD="faceless-youtube", so every music stage advance was
# written to the WRONG board — the music card's stage marker never moved and
# the driver would re-dispatch the same stage forever. Same fix shape as
# pipeline-driver.sh got in t_b17ddffc.
set -euo pipefail

CARD="${1:?usage: advance-stage.sh <card-id> <new-stage> [--board <slug>]}"
STAGE="${2:?usage: advance-stage.sh <card-id> <new-stage> [--board <slug>]}"
shift 2

BOARD="${BOARD:-faceless-youtube}"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --board)
      if [ -z "${2:-}" ]; then
        echo "advance-stage: --board needs a slug" >&2
        exit 2
      fi
      BOARD="$2"
      shift 2
      ;;
    *)
      echo "advance-stage: unknown argument '$1'" >&2
      exit 2
      ;;
  esac
done

# Update the card's stage. The driver's stage_of greps the LAST "stage: <x>"
# marker it finds for the card (body first, then comments), so a comment is
# the append-only way to move a card forward without rewriting the body.
hermes kanban --board "$BOARD" comment "$CARD" "stage: $STAGE" 2>&1 | tail -1
echo "card $CARD advanced to stage: $STAGE (board $BOARD)"
