#!/usr/bin/env bash
# Set the verified-free fallback chain for a content-machine bot.
# commandcode = deepseek-v4-flash ONLY (verified working, active session).
# MiniMax-M3 / GLM-5.2 / longcat verified FREE on openrouter-free (live HTTP).
# kilo = longcat-2.0-free + hy3:free (verified free, router LAST).
# Usage: set-fallbacks.sh <bot>
set -euo pipefail

BOT="${1:?usage: set-fallbacks.sh <bot>}"

# Verified-free chain (commandcode = deepseek only; routers TRULY last; no slow):
#   commandcode deepseek-v4-flash (active, verified) →
#   openrouter-free minimax-m3:free (live-verified, fast + strong) →
#   openrouter-free ling-3.0-flash-fin:free (live-verified, fast) →
#   openrouter-free inkling:free (live-verified, fast) →
#   kilo longcat-2.0-free (live-verified free) →
#   openrouter-free openrouter/free (router, auto-selects free, LAST) →
#   kilo kilo-auto/free (router, auto-selects free, LAST)
hermes config set -p "$BOT" fallback_providers '[
  {"provider": "Api.commandcode.ai", "model": "deepseek/deepseek-v4-flash"},
  {"provider": "openrouter-free", "model": "minimax/minimax-m3:free"},
  {"provider": "openrouter-free", "model": "inclusionai/ling-3.0-flash-fin:free"},
  {"provider": "openrouter-free", "model": "thinkingmachines/inkling:free"},
  {"provider": "kilo", "model": "meituan/longcat-2.0-free"},
  {"provider": "openrouter-free", "model": "openrouter/free"},
  {"provider": "kilo", "model": "kilo-auto/free"}
]' 2>&1 | tail -1

echo "fallbacks set for $BOT"
