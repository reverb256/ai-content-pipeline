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
#
# LOUD FAILURE + CHANNEL GUIDANCE 2026-10-16 (t_5a93164a): this script used to
# pipe the CLI through `tail -1`, so a REFUSED mutation still printed a
# plausible line and the caller could not tell there was no advance. A
# dispatcher-spawned kanban worker cannot use this script at all: its terminal
# and every subprocess it starts are fenced (agent/delegation_context.py::
# kanban_path_is_fenced, hermes_cli/kanban.py::_is_delegated_child_cli_mutation),
# so `hermes kanban --board <b> comment` exits 1 with
#   kanban: delegate_task child contexts cannot mutate Kanban tasks via the CLI
# Such a worker must post the marker with the kanban_comment TOOL instead:
#   kanban_comment(task_id="<card>", body="stage: <next-stage>")
# This script stays for the callers the fence does NOT cover: the pipeline
# driver's `hermes -p <bot> chat`, cron jobs, and a human shell on the host.
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

# Update the card's stage. The marker convention (t_669bb02b,
# scripts/automation/stage_marker.py): a marker is a LINE that IS
# `stage: <stage>` — nothing before it and nothing after it on the line — and a
# reader takes it from the card body and from comment bodies ONLY, never from a
# run summary (`hermes kanban show` prints the run summary AFTER the comments, so
# prose in a summary used to capture the driver's last-match read — measured on
# t_92a09bdc, which resolved to the undeclared stage `advance-stage`). A comment
# is the append-only way to move a card forward without rewriting the body, and
# the comment posted below IS the marker line. Do not write a lone
# `stage: <word>` line anywhere else in the card.
RC=0
OUT=$(hermes kanban --board "$BOARD" comment "$CARD" "stage: $STAGE" 2>&1) || RC=$?

if [ "$RC" -ne 0 ]; then
  printf '%s\n' "$OUT" >&2
  echo "advance-stage: FAILED (rc=$RC) — card $CARD was NOT advanced to stage: $STAGE (board $BOARD)" >&2
  case "$OUT" in
    *"cannot mutate Kanban tasks"*)
      echo "advance-stage: this shell is a dispatcher-spawned kanban worker, or a descendant of one." >&2
      echo "  Its environment is fenced, so the 'hermes kanban' CLI cannot mutate the board (t_5a93164a)." >&2
      echo "  The flag order does not help — --board $BOARD was already passed." >&2
      echo "  Post the marker with the kanban_comment TOOL from the worker itself:" >&2
      echo "      kanban_comment(task_id=\"$CARD\", body=\"stage: $STAGE\")" >&2
      echo "  Non-delegated callers (the pipeline driver's 'hermes -p <bot> chat', cron," >&2
      echo "  a human shell) are unaffected and keep using this script." >&2
      ;;
    *)
      echo "advance-stage: the CLI refused or failed; do not report an advance." >&2
      ;;
  esac
  exit "$RC"
fi

printf '%s\n' "$OUT"
echo "card $CARD advanced to stage: $STAGE (board $BOARD)"
