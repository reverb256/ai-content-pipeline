#!/bin/bash
# verify-profile-providers.sh — check every profile's primary provider+model is valid
echo '=== PROFILE PRIMARY PROVIDER/MODEL ==='
for p in /home/j_kro/.hermes/profiles/*/; do
  prof=$(basename "$p")
  provider=$(hermes -p "$prof" config get model.provider 2>/dev/null | head -1)
  model=$(hermes -p "$prof" config get model.default 2>/dev/null | head -1)
  # flag mismatches: provider nous but model not nous-compatible, or provider openrouter but model looks nous
  flag=""
  if [ "$provider" = "nous" ] && ! echo "$model" | grep -qE "longcat|ling-3.0|step-3.7|solar-pro4"; then
    flag=" ⚠️ model may not be on nous"
  fi
  if [ "$provider" = "openrouter-free" ] && echo "$model" | grep -qE "longcat-2.0:free$"; then
    flag=" ⚠️ longcat is a nous model, not openrouter"
  fi
  echo "$prof | provider=$provider | model=$model$flag"
done
