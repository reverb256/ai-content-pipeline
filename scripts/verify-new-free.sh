#!/bin/bash
# verify-new-free.sh — live-test the new/untested free models across providers
set -uo pipefail
ENV_FILE="$HOME/.hermes/.env"
env_val() { grep "^$1=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"'; }
NOUS_KEY=$(env_val NOUS_API_KEY); OR_KEY=$(env_val OPENROUTER_API_KEY)
OC_KEY=$(env_val OPENCODE_API_KEY); CC_KEY=$(env_val COMMANDCODE_API_KEY); KILO_KEY=$(env_val KILOCODE_API_KEY)

test_model() {
  local label="$1" base="$2" key="$3" model="$4"
  [ -z "$key" ] && { echo "$label | $model | NO_KEY"; return; }
  local out
  out=$(timeout 20 curl -s "$base/chat/completions" \
    -H "Authorization: Bearer $key" -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"max_tokens\":5}" 2>/dev/null)
  if echo "$out" | grep -q '"choices"'; then echo "$label | $model | ✅ WORKS"
  elif echo "$out" | grep -q "429"; then echo "$label | $model | ⏳ 429 (capped)"
  elif echo "$out" | grep -q "402\|balance\|credits"; then echo "$label | $model | 💰 402 (paid)"
  elif echo "$out" | grep -q "401\|Invalid\|AuthError"; then echo "$label | $model | 🔑 401"
  elif echo "$out" | grep -q "503\|overloaded\|unavailable"; then echo "$label | $model | 🔧 503 (upstream)"
  elif echo "$out" | grep -q "not supported\|not found\|does not exist\|unsupported"; then echo "$label | $model | ❌ unsupported"
  else echo "$label | $model | ❓ $(echo "$out" | head -c 80)"; fi
}

echo "=== NEW MODELS ON NOUS ==="
test_model "nous" "https://inference-api.nousresearch.com/v1" "$NOUS_KEY" "stepfun/step-3.7-flash:free"
test_model "nous" "https://inference-api.nousresearch.com/v1" "$NOUS_KEY" "upstage/solar-pro4:free"
echo "=== NEW MODELS ON OPENROUTER ==="
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "thinkingmachines/inkling:free"
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "thinkingmachines/inkling-small:free"
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "nvidia/nemotron-3.5-lightning:free"
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "google/gemma-4-31b-it:free"
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "google/gemma-4-26b-a4b-it:free"
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "minimax/minimax-m2.7:free"
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "nvidia/nemotron-3.5-content-safety:free"
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "dots-studio/dots-3-note-preview:free"
test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "liquid/lfm-2.5-2.6b:free"
echo "=== NEW MODELS ON OPENCODE-ZEN ==="
test_model "opencode-zen" "https://opencode.ai/zen/v1" "$OC_KEY" "mimo-v2.5-free"
test_model "opencode-zen" "https://opencode.ai/zen/v1" "$OC_KEY" "deepseek-v4-flash-free"
test_model "opencode-zen" "https://opencode.ai/zen/v1" "$OC_KEY" "muse-spark-1.2-contributor-free"
test_model "opencode-zen" "https://opencode.ai/zen/v1" "$OC_KEY" "nemotron-3.5-lightning-free"
test_model "opencode-zen" "https://opencode.ai/zen/v1" "$OC_KEY" "nemotron-3-ultra-free"
