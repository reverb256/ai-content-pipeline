#!/bin/bash
# task-rotation-v1.sh — per-task model rotation, live-verified 2026-09-01 18:32 CDT
# All entries below were confirmed working with real completions in this session
set -uo pipefail

# === ROTATION DEFINITIONS ===
# Each tier has 6-8 entries: top 3 working free models, then load-spread fallbacks
# Cross-provider spread avoids single-endpoint rate-limit cliffs

# GLOBAL/DEFAULT — broad, reliable
GLOBAL='[
  {"provider":"openrouter-free","model":"nvidia/nemotron-3-super-120b-a12b:free"},
  {"provider":"nous","model":"meituan/longcat-2.0:free"},
  {"provider":"openrouter-free","model":"inclusionai/ling-3.0-flash-fin:free"},
  {"provider":"openrouter-free","model":"nvidia/nemotron-3.5-lightning:free"},
  {"provider":"openrouter-free","model":"cohere/north-mini-code:free"},
  {"provider":"openrouter-free","model":"minimax/minimax-m3:free"},
  {"provider":"kilo","model":"kilo-auto/free"}
]'

# CODING — strong reasoning + code-specific models
CODING='[
  {"provider":"nous","model":"meituan/longcat-2.0:free"},
  {"provider":"openrouter-free","model":"nvidia/nemotron-3-super-120b-a12b:free"},
  {"provider":"opencode-zen","model":"laguna-s-2.1-free"},
  {"provider":"openrouter-free","model":"poolside/laguna-s-2.1:free"},
  {"provider":"openrouter-free","model":"minimax/minimax-m3:free"},
  {"provider":"openrouter-free","model":"cohere/north-mini-code:free"},
  {"provider":"opencode-zen","model":"nemotron-3.5-lightning-free"},
  {"provider":"kilo","model":"kilo-auto/free"}
]'

# REASONING — deep thinking, analytical
REASONING='[
  {"provider":"nous","model":"meituan/longcat-2.0:free"},
  {"provider":"openrouter-free","model":"nvidia/nemotron-3-super-120b-a12b:free"},
  {"provider":"openrouter-free","model":"minimax/minimax-m3:free"},
  {"provider":"openrouter-free","model":"nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"},
  {"provider":"openrouter-free","model":"inclusionai/ling-3.0-flash-fin:free"},
  {"provider":"openrouter-free","model":"cohere/north-mini-code:free"},
  {"provider":"openrouter-free","model":"dots-studio/dots-3-note-preview:free"},
  {"provider":"kilo","model":"kilo-auto/free"}
]'

# CONTENT — creative writing, narrative
CONTENT='[
  {"provider":"nous","model":"meituan/longcat-2.0:free"},
  {"provider":"openrouter-free","model":"minimax/minimax-m3:free"},
  {"provider":"openrouter-free","model":"inclusionai/ling-3.0-flash-fin:free"},
  {"provider":"openrouter-free","model":"nvidia/nemotron-3-super-120b-a12b:free"},
  {"provider":"openrouter-free","model":"cohere/north-mini-code:free"},
  {"provider":"openrouter-free","model":"mimo-v2.5-free"},
  {"provider":"kilo","model":"kilo-auto/free"}
]'

# COMMODITY — fast, cheap, volume bots
COMMODITY='[
  {"provider":"openrouter-free","model":"inclusionai/ling-3.0-flash-fin:free"},
  {"provider":"openrouter-free","model":"nvidia/nemotron-3.5-lightning:free"},
  {"provider":"openrouter-free","model":"poolside/laguna-xs-2.1:free"},
  {"provider":"nous","model":"poolside/laguna-xs-2.1:free"},
  {"provider":"openrouter-free","model":"liquid/lfm-2.5-2.6b:free"},
  {"provider":"kilo","model":"kilo-auto/free"}
]'

# === TIER ASSIGNMENTS ===
REASONING_PROFILES="cco coo cro analyst strategist researcher oracle caio maplespike-eng ops"
CONTENT_PROFILES="writer editor scriptwriter storyteller web-designer site-agency"
COMMODITY_PROFILES="distributor scout seobot thumbnailbot videobot voicebot publishbot"
CODING_PROFILES=""

apply() {
  local tier="$1" chain="$2"
  hermes config set -p "$1" fallback_providers "$chain" >/dev/null 2>&1
  [ $? -eq 0 ] && echo "$tier $1"
}

for prof in $(ls /home/j_kro/.hermes/profiles/); do
  if echo "$REASONING_PROFILES" | grep -qw "$prof"; then
    apply "$prof" "$REASONING"; echo "  tier=REASONING"
  elif echo "$CONTENT_PROFILES" | grep -qw "$prof"; then
    apply "$prof" "$CONTENT"; echo "  tier=CONTENT"
  elif echo "$COMMODITY_PROFILES" | grep -qw "$prof"; then
    apply "$prof" "$COMMODITY"; echo "  tier=COMMODITY"
  elif echo "$CODING_PROFILES" | grep -qw "$prof"; then
    apply "$prof" "$CODING"; echo "  tier=CODING"
  else
    apply "$prof" "$GLOBAL"; echo "  tier=GLOBAL"
  fi
done
hermes config set fallback_providers "$GLOBAL" >/dev/null 2>&1 && echo "GLOBAL  global"
