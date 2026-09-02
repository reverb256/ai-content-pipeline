#!/bin/bash
# normalize-fallbacks-v2.sh — verified working chain, nous-first with ling as the reliable nous fallback
# Order: nous longcat (exec primary) → nous ling (RELIABLE nous) → openrouter minimax → openrouter ling → kilo router
set -uo pipefail

CHAIN='[
  {"provider": "nous", "model": "meituan/longcat-2.0:free"},
  {"provider": "nous", "model": "inclusionai/ling-3.0-flash-fin:free"},
  {"provider": "openrouter-free", "model": "minimax/minimax-m3:free"},
  {"provider": "openrouter-free", "model": "inclusionai/ling-3.0-flash-fin:free"},
  {"provider": "kilo", "model": "kilo-auto/free"}
]'

for p in $(ls /home/j_kro/.hermes/profiles/); do
  hermes config set -p "$p" fallback_providers "$CHAIN" >/dev/null 2>&1 && echo "set $p" || echo "FAIL $p"
done
hermes config set fallback_providers "$CHAIN" >/dev/null 2>&1 && echo "set global" || echo "FAIL global"
