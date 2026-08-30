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

log() { echo "$(date -Is) $1" >> "$LOG"; }

# Get cards in a given stage. Kanban stages map to status; we use a label convention.
# Cards carry "stage: <stage>" in their body (the oracle sets this). We scan for
# ready cards and check their stage.
get_ready_cards() {
  hermes kanban --board "$BOARD" list 2>/dev/null | grep -E "^▶" | awk '{print $2}' || true
}

stage_of() {
  hermes kanban --board "$BOARD" show "$1" 2>/dev/null | grep -oE "stage: [a-z]+" | head -1 | awk '{print $2}'
}

# Dispatch the bot for a stage (async — each bot runs its own chat)
dispatch_stage() {
  local card="$1" stage="$2"
  case "$stage" in
    research)  bot="researcher";  prompt="Run the research stage. Read the opportunity card (kanban task $card), build the evidence package (3-7 verified claims with URLs), save to the campaign folder, comment on the kanban task with the result." ;;
    script)    bot="scriptwriter"; prompt="Run the script stage for kanban task $card. Read the evidence package, write the retention-optimized TTS-paced script with per-section visual notes. Save + comment." ;;
    voice)     bot="voicebot";    prompt="Run the voice stage for kanban task $card. Check pick-provider.sh voice, generate narration from the script. Save audio + log tier." ;;
    visuals)   bot="videobot";    prompt="Run the visuals stage for kanban task $card. Check pick-provider.sh video, render the video (manim or fallback). Save MP4 + log tier." ;;
    thumbnail) bot="thumbnailbot"; prompt="Run the thumbnail stage for kanban task $card. Generate 2-3 thumbnail variants. Save + comment." ;;
    seo)       bot="seobot";      prompt="Run the SEO stage for kanban task $card. Write title/description/tags/chapters from the script. Save metadata JSON." ;;
    upload)    bot="publishbot";  prompt="Run the upload stage for kanban task $card. Upload the finished video as PRIVATE (review gate). Do NOT make public without human approval. Report the video ID." ;;
    analyze)   bot="analyst";     prompt="Run the analyze stage for kanban task $card. Pull performance, produce keep/test/stop. Post to kanban." ;;
    story)     bot="storyteller"; prompt="Run the story/audio-drama stage for kanban task $card. Read the story script (or write one from the opportunity), run storyteller.py (scripts/audio/storyteller.py) to synthesize the audio drama with MiniMax TTS (fallback Chatterbox). Save the finished audio + comment with the output path." ;;
    *) log "unknown stage $stage for card $card"; return ;;
  esac
  log "dispatching $bot for card $card (stage $stage)"
  # Fire in background so the driver doesn't block on one bot
  nohup hermes -p "$bot" chat -q "$prompt" >> "$LOG" 2>&1 &
}

log "pipeline driver run start"
for card in $(get_ready_cards); do
  stage=$(stage_of "$card")
  if [ -z "$stage" ]; then
    log "card $card has no stage label — skipping (need oracle to set stage:)"
    continue
  fi
  log "card $card → stage $stage"
  dispatch_stage "$card" "$stage"
done
log "pipeline driver run complete"
