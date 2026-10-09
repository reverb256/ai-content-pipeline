#!/usr/bin/env bash
# Production pipeline driver — walks a kanban board and advances
# each card through the stages by dispatching the right bot.
# Run by cron (e.g. every 30 min during the day).
#
# BOARD-PARAMETERIZED (t_b17ddffc): the board and the stage→bot
# map are DATA, not code.
#   BOARD  from env (BOARD) or --board <slug>; default
#          faceless-youtube so the existing lane keeps working
#          byte-for-byte.
#   The stage→bot map is read from a per-board config file:
#     faceless-youtube -> scripts/automation/stages/faceless-youtube.yaml
#     music            -> music/stages.yaml
#   Add a lane = add a yaml file. Never edit this driver.
#
# Stage→bot map format (yaml):
#   stages:
#     - stage: <label>
#       bot: <hermes profile>        # dispatch `hermes -p <bot> chat`
#       prompt: "..."                # {card} and {board} are substituted
#     - stage: <label>
#       human_gate: true             # NEVER auto-dispatch (parked)
#
# Run by cron (e.g. every 30 min during the day).
set -euo pipefail

# REPO is auto-resolved: if the script is inside a git worktree, use the
# git root; otherwise fall back to $HOME/Projects/ai-content-pipeline so the
# local dev path still works byte-for-byte. Override via env REPO= explicitly.
if [ -z "${REPO:-}" ]; then
  git_root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || true)
  if [ -n "$git_root" ]; then
    REPO="$git_root"
  else
    REPO="$HOME/Projects/ai-content-pipeline"
  fi
fi
LOG="$REPO/performance/pipeline-driver.log"

# ---- Board selection: env BOARD or --board <slug>, default unchanged ----
# Env var BOARD (exported, non-empty) wins over the default; an explicit
# --board <slug> wins over both. Default is faceless-youtube so the
# existing lane keeps working byte-for-byte when neither is given.
BOARD="${BOARD:-faceless-youtube}"
if [ "${1:-}" = "--board" ] && [ -n "${2:-}" ]; then
  BOARD="$2"
  shift 2
fi

mkdir -p "$(dirname "$LOG")"

# Concurrency cap: how many bots may run at once. Default 1 (sequential) —
# j_kro's rule: never parallelize against quota-limited providers (xAI etc.).
# Raise via env: MAX_CONCURRENT_BOTS=2 bash pipeline-driver.sh
MAX_CONCURRENT="${MAX_CONCURRENT_BOTS:-1}"

log() { echo "$(date -Is) $1" >> "$LOG"; }

# ---- Stage→bot map: per-board config file (yaml) ----
# Resolve the config file for the board. Convention: a board named X maps
# to scripts/automation/stages/X.yaml; the music board maps to music/stages.yaml.
stage_config_file() {
  local board="$1"
  if [ "$board" = "music" ] && [ -f "$REPO/music/stages.yaml" ]; then
    echo "$REPO/music/stages.yaml"
  elif [ -f "$REPO/scripts/automation/stages/$board.yaml" ]; then
    echo "$REPO/scripts/automation/stages/$board.yaml"
  else
    return 1
  fi
}

STAGES_FILE="$(stage_config_file "$BOARD" || true)"
if [ -z "$STAGES_FILE" ]; then
  log "ERROR: no stage config file for board '$BOARD' (looked for scripts/automation/stages/$BOARD.yaml or music/stages.yaml)"
  echo "pipeline-driver: no stage config for board '$BOARD'" >&2
  exit 2
fi

# Parse the yaml config once into a temp file of "stage<TAB>bot<TAB>human_gate"
# rows plus a prompt file per stage. Uses python3 + PyYAML (present in the
# hermes runtime; validated at boot of every run).
CONFIG_PARSE="$(mktemp "${TMPDIR:-/tmp}/pipeline-driver.XXXXXX")"
if ! python3 - "$STAGES_FILE" "$CONFIG_PARSE" <<'PYEOF'
import sys, os
import yaml

cfg_path, out_path = sys.argv[1], sys.argv[2]
with open(cfg_path) as f:
    cfg = yaml.safe_load(f) or {}

stages = cfg.get("stages") or []
rows = []
for entry in stages:
    if not isinstance(entry, dict) or "stage" not in entry:
        continue
    stage = str(entry["stage"])
    bot = entry.get("bot")
    human_gate = bool(entry.get("human_gate", False))
    prompt = entry.get("prompt", "")
    rows.append("\t".join([stage, str(bot) if bot else "", "1" if human_gate else "0"]))
    # Write the prompt to a sidecar file: <out>.prompts/<stage>
    pdir = out_path + ".prompts"
    os.makedirs(pdir, exist_ok=True)
    with open(os.path.join(pdir, stage), "w") as pf:
        pf.write(str(prompt))

# The board's default stage (faceless-youtube: opportunity,
# music: brief). stage_of uses it when a card carries no
# "stage:" marker yet.
default_stage = str(cfg.get("default_stage", "opportunity"))
# stash the default stage name in its own sidecar file
with open(out_path + ".default", "w") as f:
    f.write(default_stage + "\n")

with open(out_path, "w") as f:
    f.write("\n".join(rows) + "\n")
PYEOF
then
  log "ERROR: failed to parse stage config $STAGES_FILE"
  rm -f "$CONFIG_PARSE"
  exit 2
fi

PROMPTS_DIR="$CONFIG_PARSE.prompts"

# Look up a stage's row. Echoes "bot" or "HUMAN_GATE" or "" (unknown).
# NOTE: called as `bot=$(lookup_stage ...)` — a command substitution runs
# in a SUBSHELL, so nothing assigned here survives to the caller. This
# function only echoes the routing token; the prompt is read separately
# in dispatch_stage (in the parent shell) from the sidecar files.
lookup_stage() {
  local stage="$1"
  local row
  row=$(awk -F'\t' -v s="$stage" '$1 == s {print; exit}' "$CONFIG_PARSE")
  if [ -z "$row" ]; then
    return 1
  fi
  local bot human
  bot=$(echo "$row" | cut -f2)
  human=$(echo "$row" | cut -f3)
  if [ "$human" = "1" ]; then
    echo "HUMAN_GATE"
    return 0
  fi
  if [ -z "$bot" ]; then
    return 1
  fi
  echo "$bot"
  return 0
}

# Count bots currently running (any hermes -p <bot> chat in the crew).
# Covers BOTH lanes' bots: the faceless-youtube crew AND the music crew
# (producer, writer, reviewer-deepseek, distributor), so the concurrency
# cap sees every bot the driver might dispatch, whichever board it walks.
running_bots() {
  # Count crew bot processes. pgrep -fc returns exit 1 when no matches,
  # which would trigger || echo 0 and produce "0\n0" — capture instead.
  local count
  count=$(pgrep -fc "hermes.*-p (researcher|scriptwriter|voicebot|videobot|thumbnailbot|seobot|publishbot|analyst|storyteller|oracle|producer|writer|reviewer-deepseek|distributor|socialbot).*chat" 2>/dev/null) || count=0
  echo "$count"
}

# Get cards in a given stage. Kanban stages map to status; we use a label convention.
# Cards carry "stage: <stage>" in their body (the oracle sets this). We scan for
# ready cards and check their stage.
get_ready_cards() {
  hermes kanban --board "$BOARD" list 2>/dev/null | grep -E "^▶" | awk '{print $2}' || true
}

stage_of() {
  # Check the card body first, then comments, then default to opportunity
  local body
  body=$(hermes kanban --board "$BOARD" show "$1" 2>/dev/null)
  local s
  # Read the LAST (most recent) stage marker — the first one is stale.
  # Stage names may contain hyphens (music lane: genre-select,
  # human-approval), so the class is [a-z-]+, not [a-z]+.
  s=$(echo "$body" | grep -oE "stage: [a-z-]+" | tail -1 | awk '{print $2}' || true)
  if [ -z "$s" ]; then
    # No stage label yet → the oracle created it; treat as the
    # board's default stage (faceless-youtube: opportunity,
    # music: brief).
    s=$(cat "$CONFIG_PARSE.default" 2>/dev/null || true)
    s="${s:-opportunity}"
  fi
  echo "$s"
}

# Dispatch the bot for a stage (async — each bot runs its own chat)
dispatch_stage() {
  local card="$1" stage="$2"
  local bot
  bot=$(lookup_stage "$stage" || true)
  if [ -z "$bot" ]; then
    log "unknown stage $stage for card $card (board $BOARD, config $STAGES_FILE)"
    return
  fi
  if [ "$bot" = "HUMAN_GATE" ]; then
    # Human gate: the card is parked awaiting j_kro. Never dispatch it,
    # never log-loop it (pre-fix this hit the *) branch every 30 min —
    # 198 lines of "unknown stage escalate" in the surviving log).
    log "card $card stage $stage is a HUMAN GATE — parked (board $BOARD)"
    return 1
  fi
  # Read the prompt from the per-stage sidecar file (the config parser
  # wrote it). {card} and {board} tokens are substituted here, in the
  # parent shell, so the substitution survives.
  local prompt
  prompt=$(cat "$PROMPTS_DIR/$stage" 2>/dev/null || true)
  if [ -z "$prompt" ]; then
    log "stage $stage (card $card, board $BOARD) has an empty prompt — skipping"
    return
  fi
  prompt="${prompt//\{card\}/$card}"
  prompt="${prompt//\{board\}/$BOARD}"
  log "dispatching $bot for card $card (stage $stage, board $BOARD)"
  # DRY_RUN=1 proves routing without launching a bot (used by the D6 test).
  if [ "${DRY_RUN:-0}" = "1" ]; then
    log "[dry-run] would dispatch $bot"
    return 0
  fi
  # Fire in background so the driver doesn't block on one bot.
  # --oneshot -Q ensures the process exits after answering instead of
  # staying resident as an interactive session.
  nohup hermes -p "$bot" chat -q "$prompt" --oneshot -Q >> "$LOG" 2>&1 &
}

log "pipeline driver run start (board $BOARD)"
dispatched=0
for card in $(get_ready_cards); do
  # Respect the concurrency cap: stop dispatching once we're at the limit.
  # This is the quota guard — never parallelize against xAI/quota providers.
  running=$(running_bots)
  if [ "$running" -ge "$MAX_CONCURRENT" ]; then
    log "concurrency cap reached ($running/$MAX_CONCURRENT) — stopping dispatch"
    break
  fi
  stage=$(stage_of "$card")
  if [ -z "$stage" ]; then
    log "card $card has no stage label — skipping (need oracle to set stage:)"
    continue
  fi
  log "card $card → stage $stage"
  if dispatch_stage "$card" "$stage"; then
    dispatched=$((dispatched+1))
  fi
done
log "pipeline driver run complete (board $BOARD, dispatched $dispatched, running $(running_bots)/$MAX_CONCURRENT)"

# Cleanup the parsed-config temp files.
rm -rf "$CONFIG_PARSE" "$PROMPTS_DIR"
