#!/usr/bin/env bash
# Production pipeline driver — walks the faceless-youtube kanban board and
# advances each card through the stages by dispatching the right bot.
# Run by cron (e.g. every 30 min during the day).
#
# Stage → bot mapping:
#   opportunity → (oracle already created the card)
#   research → researcher
#   script   → scriptwriter
#   voice    → voicebot
#   visuals  → videobot
#   thumbnail→ thumbnailbot
#   seo      → seobot
#   upload   → publishbot (needs review gate + OAuth)
#   analyze  → analyst
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
BOARD="faceless-youtube"
LOG="$REPO/performance/pipeline-driver.log"
mkdir -p "$(dirname "$LOG")"

# Concurrency cap: how many bots may run at once. Default 1 (sequential) —
# j_kro's rule: never parallelize against quota-limited providers (xAI etc.).
# Raise via env: MAX_CONCURRENT_BOTS=2 bash pipeline-driver.sh
MAX_CONCURRENT="${MAX_CONCURRENT_BOTS:-1}"

# Rate-limit respect knobs
# MAX_DISPATCH_PER_TICK: how many cards to advance per run (default 2). Free-tier
#   providers can't sustain more without hitting 60/min caps. The pipeline is
#   throughput-limited by design — 2 cards/tick = 2 bots/call each = ~4-6 model
#   calls per 30min, well under any cap.
MAX_DISPATCH="${MAX_DISPATCH_PER_TICK:-2}"
# MIN_TICK_GAP: if the last run dispatched cards within this many seconds, skip
#   this tick (gives the model calls time to drain). Default 120s.
MIN_TICK_GAP="${MIN_TICK_GAP:-120}"
# COOLDOWN_FILE: when a 429 is detected, mark time so subsequent ticks back off.
COOLDOWN_FILE="$REPO/performance/.driver-cooldown"

log() { echo "$(date -Is) $1" >> "$LOG"; }

# Respect: skip this tick if the previous dispatch happened < MIN_TICK_GAP ago.
recent_dispatch() {
  local last
  last=$(grep "dispatch" "$LOG" 2>/dev/null | tail -1 | grep -oE "^[0-9T:.+-]+" || true)
  [ -z "$last" ] && return 1
  local last_epoch now_epoch
  last_epoch=$(date -d "$last" +%s 2>/dev/null || echo 0)
  now_epoch=$(date +%s)
  [ $((now_epoch - last_epoch)) -lt "$MIN_TICK_GAP" ]
}

# Work around: if we recently hit a 429 (cooldown marker), skip dispatch.
in_cooldown() {
  [ -f "$COOLDOWN_FILE" ] || return 1
  local marker now_epoch marker_epoch
  marker=$(cat "$COOLDOWN_FILE" 2>/dev/null || echo 0)
  now_epoch=$(date +%s)
  marker_epoch=$((marker))
  [ $((now_epoch - marker_epoch)) -lt 300 ]  # 5 min cooldown
}

# Count bots currently running (any hermes -p <bot> chat in the crew)
running_bots() {
  # Count crew bot processes. pgrep -fc returns exit 1 when no matches,
  # which would trigger || echo 0 and produce "0\n0" — capture instead.
  local count
  count=$(pgrep -fc "hermes.*-p (researcher|scriptwriter|voicebot|videobot|thumbnailbot|seobot|publishbot|analyst|storyteller|oracle).*chat" 2>/dev/null) || count=0
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
  s=$(echo "$body" | grep -oE "stage: [a-z]+" | tail -1 | awk '{print $2}' || true)
  if [ -z "$s" ]; then
    # No stage label yet → the oracle created it as an opportunity; treat as
    # opportunity stage so the driver picks it up and starts research.
    s="opportunity"
  fi
  echo "$s"
}

# Dispatch the bot for a stage (async — each bot runs its own chat)
dispatch_stage() {
  local card="$1" stage="$2"
  case "$stage" in
    opportunity) bot="researcher"; prompt="Run the research stage for kanban task $card. Read the opportunity card, build the evidence package (3-7 verified claims with URLs), save to the campaign folder, then advance the card: run scripts/automation/advance-stage.sh $card research." ;;
    research)  bot="researcher";  prompt="Run the research stage. Read the opportunity card (kanban task $card), build the evidence package (3-7 verified claims with URLs), save to the campaign folder, then advance the card: run scripts/automation/advance-stage.sh $card script. Comment on the kanban task with the result." ;;
    script)    bot="scriptwriter"; prompt="Run the script stage for kanban task $card. Read the evidence package, write the retention-optimized TTS-paced script with per-section visual notes. Save + comment." ;;
    voice)     bot="voicebot";    prompt="Run the voice stage for kanban task $card. Check pick-provider.sh voice, generate narration from the script. Save audio + log tier." ;;
    visuals)   bot="videobot";    prompt="Run the visuals stage for kanban task $card. Check pick-provider.sh video, render the video (manim or fallback). Save MP4 + log tier." ;;
    thumbnail) bot="thumbnailbot"; prompt="Run the thumbnail stage for kanban task $card. Generate 2-3 thumbnail variants. Save + comment." ;;
    seo)       bot="seobot";      prompt="Run the SEO stage for kanban task $card. Write title/description/tags/chapters from the script. Save metadata JSON." ;;
    upload)    bot="publishbot";  prompt="Run the upload stage for kanban task $card. Upload the finished video as PRIVATE (review gate). Do NOT make public without human approval. Report the video ID." ;;
    analyze)   bot="analyst";     prompt="Run the analyze stage for kanban task $card. Pull performance, produce keep/test/stop. Post to kanban." ;;
    review)    bot="default";     prompt="You are SPOC (chief of staff). Run the critic/review pass on kanban task $card (board $BOARD). Read the card's latest artifact (research/script/audio/video), judge it: does it meet the definition of done? Is it original (not template-slop)? Does it match the voice/brain rules? If it passes, advance it: run scripts/automation/advance-stage.sh $card <next-stage>. If it fails, comment with the specific critique and keep the card at its current stage (do NOT advance). You review; you do not redo the work." ;;
    story)     bot="storyteller"; prompt="Run the story/audio-drama stage for kanban task $card. Read the story script (or write one from the opportunity), run storyteller.py (scripts/audio/storyteller.py) to synthesize the audio drama with VoxCPM TTS (self-hosted). Save the finished audio + comment with the output path." ;;
    audio)     bot="storyteller"; prompt="Run the audio-drama stage for kanban task $card. Read the story script (or write one from the opportunity), run storyteller.py (scripts/audio/storyteller.py) to synthesize the audio drama with VoxCPM TTS (self-hosted). Save the finished audio + comment with the output path." ;;
    *) log "unknown stage $stage for card $card"; return ;;
  esac
  log "dispatching $bot for card $card (stage $stage)"
  # Fire in background so the driver doesn't block on one bot.
  # --oneshot -Q ensures the process exits after answering instead of
  # staying resident as an interactive session.
  nohup hermes -p "$bot" chat -q "$prompt" --oneshot -Q >> "$LOG" 2>&1 &
}

log "pipeline driver run start"
# Respect + work-around gates
if in_cooldown; then
  log "cooldown active (429 recently) — skipping tick"
  exit 0
fi
if recent_dispatch; then
  log "recent dispatch within ${MIN_TICK_GAP}s — skipping tick"
  exit 0
fi
dispatched=0
for card in $(get_ready_cards); do
  # Respect the concurrency cap: stop dispatching once we're at the limit.
  # This is the quota guard — never parallelize against xAI/quota providers.
  running=$(running_bots)
  if [ "$running" -ge "$MAX_CONCURRENT" ]; then
    log "concurrency cap reached ($running/$MAX_CONCURRENT) — stopping dispatch"
    break
  fi
  # Respect the per-tick dispatch cap (free-tier throughput limit)
  if [ "$dispatched" -ge "$MAX_DISPATCH" ]; then
    log "per-tick dispatch cap reached ($dispatched/$MAX_DISPATCH) — stopping dispatch"
    break
  fi
  stage=$(stage_of "$card")
  if [ -z "$stage" ]; then
    log "card $card has no stage label — skipping (need oracle to set stage:)"
    continue
  fi
  log "card $card → stage $stage"
  dispatch_stage "$card" "$stage"
  dispatched=$((dispatched+1))
done
log "pipeline driver run complete (dispatched $dispatched, running $(running_bots)/$MAX_CONCURRENT)"
