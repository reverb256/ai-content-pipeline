#!/bin/bash
# assign-laguna-tiers.sh — assign Laguna S vs XS per bot tier
# Reasoning/coding bots → laguna S (stronger, 1M ctx) in chain
# Commodity bots → laguna XS (faster, 33B, open-weights) in chain
# Both keep the same structure; only the laguna entries differ.
set -uo pipefail

# Reasoning/coding tier — laguna S as their laguna entry
REASONING="analyst caio cco coo cro editor maplespike-eng ops oracle researcher scriptwriter site-agency storyteller strategist web-designer writer"
# Commodity tier — laguna XS as their laguna entry
COMMODITY="distributor scout seobot thumbnailbot videobot voicebot publishbot"

CHAIN_S='[
  {"provider": "nous", "model": "meituan/longcat-2.0:free"},
  {"provider": "nous", "model": "inclusionai/ling-3.0-flash-fin:free"},
  {"provider": "openrouter-free", "model": "minimax/minimax-m3:free"},
  {"provider": "openrouter-free", "model": "inclusionai/ling-3.0-flash-fin:free"},
  {"provider": "nous", "model": "poolside/laguna-s-2.1:free"},
  {"provider": "opencode-zen", "model": "laguna-s-2.1-free"},
  {"provider": "openrouter-free", "model": "poolside/laguna-s-2.1:free"},
  {"provider": "kilo", "model": "kilo-auto/free"},
  {"provider": "openrouter-free", "model": "openrouter/free"},
  {"provider": "openrouter-free", "model": "z-ai/glm-5.2:free"},
  {"provider": "commandcode", "model": "poolside/laguna-s-2.1-free"}
]'

CHAIN_XS='[
  {"provider": "nous", "model": "inclusionai/ling-3.0-flash-fin:free"},
  {"provider": "openrouter-free", "model": "inclusionai/ling-3.0-flash-fin:free"},
  {"provider": "nous", "model": "poolside/laguna-xs-2.1:free"},
  {"provider": "openrouter-free", "model": "poolside/laguna-xs-2.1:free"},
  {"provider": "kilo", "model": "kilo-auto/free"},
  {"provider": "openrouter-free", "model": "openrouter/free"}
]'

for p in $(ls /home/j_kro/.hermes/profiles/); do
  if echo "$REASONING" | grep -qw "$p"; then
    hermes config set -p "$p" fallback_providers "$CHAIN_S" >/dev/null 2>&1 && echo "S  $p"
  elif echo "$COMMODITY" | grep -qw "$p"; then
    hermes config set -p "$p" fallback_providers "$CHAIN_XS" >/dev/null 2>&1 && echo "XS $p"
  else
    echo "UNMAPPED $p"
  fi
done
hermes config set fallback_providers "$CHAIN_S" >/dev/null 2>&1 && echo "S  global"
