#!/usr/bin/env bash
# Advance a faceless-youtube kanban card to the next stage.
# Usage: advance-stage.sh <card-id> <new-stage> [campaign-dir]
# The bot calls this when it finishes its stage, so the driver picks it up
# at the next stage.
#
# ENTERPRISE GATE: before advancing, run the mechanical gate for the CURRENT
# stage (the stage being left). If the gate FAILS, the card does NOT advance
# and the failure is commented on the card. This is the enforcement layer that
# makes "meticulous" real: garbage cannot move forward.
set -euo pipefail

CARD="${1:?usage: advance-stage.sh <card-id> <new-stage> [campaign-dir]}"
STAGE="${2:?usage: advance-stage.sh <card-id> <new-stage> [campaign-dir]}"
BOARD="faceless-youtube"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATES="$ROOT/scripts/gates"

# Derive campaign dir from the card body if not given
CAMPAIGN="${3:-}"
if [ -z "$CAMPAIGN" ]; then
  # try to find the campaign from the card (grep title/body on the kanban card)
  CAMPAIGN_DIR=""
  # default heuristic: latest campaign dir is the in-flight one
  CAMPAIGN="$(ls -dt "$ROOT"/campaigns/*/ 2>/dev/null | head -1 | sed 's#/$##')"
  echo "gate: auto-detected campaign dir: $CAMPAIGN"
fi

# Map the stage being LEFT to its gate script. If no gate for a stage, it's
# a pass-through (no artifact to validate).
run_gate() {
  local stage="$1" camp="$2"
  case "$stage" in
    script)    [ -x "$GATES/gate_script.py" ]    && python3 "$GATES/gate_script.py" "$camp" ;;
    research)  [ -x "$GATES/gate_evidence.py" ]  && python3 "$GATES/gate_evidence.py" "$camp" ;;
    voice)     [ -x "$GATES/gate_voice.py" ]     && python3 "$GATES/gate_voice.py" "$camp"
               [ -x "$GATES/gate_loudness.py" ]  && python3 "$GATES/gate_loudness.py" "$camp" ;;
    visuals)   [ -x "$GATES/gate_visuals.py" ]   && python3 "$GATES/gate_visuals.py" "$camp" ;;
    analyze)   [ -x "$GATES/gate_analyze.py" ]   && python3 "$GATES/gate_analyze.py" "$camp" ;;
    review)    # Review gate: determine which producing stage's artifact is being reviewed
               local review_stage=""
               for rs in script visuals voice thumbnail seo angle research; do
                 if [ -f "$camp/review/${rs}.review.json" ]; then
                   review_stage="$rs"
                   break
                 fi
               done
               if [ -n "$review_stage" ]; then
                 [ -x "$GATES/gate_review.py" ] && python3 "$GATES/gate_review.py" "$camp" "$review_stage"
               else
                 echo "gate: no review artifact found in $camp/review/"
                 return 1
               fi ;;
    *)         echo "gate: no mechanical gate for stage '$stage' (pass-through)" ;;
  esac
}

# Determine the stage being left = previous stage. The caller passes the NEW
# stage; the gate that applies is the one for the artifact just produced.
# We infer: advance script -> voice means voice gate checks the new voice.
# But the artifact for gate checks is the CURRENT stage's output. The driver
# calls advance with the NEXT stage. So the gate that should run is the one
# for the CURRENT stage the card is on. We get that from the card body's
# most recent "stage:" line.
CURRENT_STAGE="$(hermes kanban --board "$BOARD" show "$CARD" 2>/dev/null | grep -oE 'stage: [a-z-]+' | tail -1 | awk '{print $2}')"
CURRENT_STAGE="${CURRENT_STAGE:-$STAGE}"

echo "=== ENTERPRISE GATE: stage '$CURRENT_STAGE' → '$STAGE' ==="
if ! gate_output="$(run_gate "$CURRENT_STAGE" "$CAMPAIGN" 2>&1)"; then
  echo "GATE FAILED for stage '$CURRENT_STAGE'"
  echo "$gate_output"
  hermes kanban --board "$BOARD" comment "$CARD" "GATE FAILED ($CURRENT_STAGE): $(echo "$gate_output" | grep FAIL | head -1)" >/dev/null 2>&1 || true
  echo "card $CARD BLOCKED at $CURRENT_STAGE (gate failed — not advancing)"
  exit 1
fi
echo "$gate_output"
echo "GATE PASSED — advancing $CARD to $STAGE"

# Update the card body's stage
hermes kanban --board "$BOARD" comment "$CARD" "stage: $STAGE" 2>&1 | tail -1
echo "card $CARD advanced to stage: $STAGE"