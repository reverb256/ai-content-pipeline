#!/bin/bash
# align-all-to-nous.sh — make nous the PRIMARY provider on every profile
# Reasoning/coding tier → nous/longcat (verified reasoning model)
# Commodity tier → nous/ling-3.0-flash-fin (verified, reliable)
set -uo pipefail

# Commodity tier: cheap fast models (scout, distributor, thumbnailbot, videobot, voicebot, seobot, publishbot)
COMMODITY="distributor scout seobot thumbnailbot videobot voicebot publishbot"

for p in $(ls /home/j_kro/.hermes/profiles/); do
  if echo "$COMMODITY" | grep -qw "$p"; then
    hermes config set -p "$p" model.provider nous >/dev/null 2>&1
    hermes config set -p "$p" model.default inclusionai/ling-3.0-flash-fin:free >/dev/null 2>&1
    echo "$p → nous/ling-3.0-flash-fin"
  else
    hermes config set -p "$p" model.provider nous >/dev/null 2>&1
    hermes config set -p "$p" model.default meituan/longcat-2.0:free >/dev/null 2>&1
    echo "$p → nous/longcat-2.0"
  fi
done
