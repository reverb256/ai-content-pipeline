#!/usr/bin/env bash
# Pick the best available provider tier for a stage of the content machine.
# Checks live health of each provider; falls back down the chain on failure.
#
# Usage:
#   pick-provider.sh video     → echoes: xai | manim | comfyui | stock
#   pick-provider.sh voice     → echoes: chatterbox | xai | edge | local
#   pick-provider.sh llm       → echoes: nous | opencode-zen | opencode-go | hy3
#   pick-provider.sh image     → echoes: comfyui | xai | ideogram
#
# Logs the pick to performance/model-routing.log
set -euo pipefail

REPO="${REPO:-$HOME/Projects/ai-content-pipeline}"
LOG="$REPO/performance/model-routing.log"
mkdir -p "$(dirname "$LOG")"

STAGE="${1:?usage: pick-provider.sh <video|voice|llm|image>}"

log() { echo "$(date -Is) [$STAGE] $1" >> "$LOG"; }

check_http() {
  local code=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" "$1" 2>/dev/null || true)
  # curl returns "000" on connection failure; anything 2xx/3xx/4xx = alive
  if [ "$code" = "000" ] || [ -z "$code" ]; then echo "down"; else echo "up"; fi
}

pick_video() {
  # Manim/ffmpeg: always local. ComfyUI on nexus: probe.
  local comfy=$(check_http "http://10.1.1.120:8188/system_stats" 2>/dev/null)
  if command -v manim >/dev/null 2>&1; then
    echo "manim"; log "manim (local, always available)"
  elif [ "$comfy" = "up" ]; then
    echo "comfyui"; log "comfyui (nexus up)"
  else
    echo "stock"; log "stock footage fallback (manim missing, comfyui $comfy)"
  fi
}

pick_voice() {
  # Chatterbox on forge (or wherever it runs): probe the API
  local cb=$(check_http "http://10.1.1.130:8004/get_reference_files" 2>/dev/null)
  if [ "$cb" = "up" ]; then
    echo "chatterbox"; log "chatterbox (local GPU, up)"
  else
    # Fall back to Hermes's configured TTS (xai currently)
    local tts_provider=$(hermes config get tts.provider 2>/dev/null | tr -d '"' || echo "xai")
    echo "$tts_provider"; log "tts fallback: $tts_provider (chatterbox $cb)"
  fi
}

pick_llm() {
  # The profile's fallback chain handles this; report the configured default
  local model=$(hermes config get -p oracle model.default 2>/dev/null | tr -d '"' || echo "longcat-2.0")
  echo "$model"; log "llm: $model (profile fallback chain handles quota)"
}

pick_image() {
  local comfy=$(check_http "http://10.1.1.120:8188/system_stats" 2>/dev/null)
  if [ "$comfy" = "up" ]; then
    echo "comfyui"; log "comfyui (nexus up)"
  else
    echo "xai"; log "xai image (comfyui $comfy)"
  fi
}

case "$STAGE" in
  video) pick_video ;;
  voice) pick_voice ;;
  llm)   pick_llm ;;
  image) pick_image ;;
  *) echo "unknown stage: $STAGE (video|voice|llm|image)" >&2; exit 1 ;;
esac
