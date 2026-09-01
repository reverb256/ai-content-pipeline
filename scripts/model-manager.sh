#!/bin/bash
# model-manager.sh — dynamic free-model management layer
# 1. Fetch the daily-updated free-ai-models catalog (ClawLabsAI)
# 2. Cross-check against our live endpoints (nous, openrouter, opencode-zen, commandcode, kilo)
# 3. Live-verify candidates with a real 1-token completion
# 4. Emit the best rotation as a chain, log the result
#
# Design (j_kro 2026-09-01): rotate laguna-s-2.1:free across every endpoint,
# stagger the tail (kilo/free and openrouter/free separated), and use whatever
# free models are actually available RIGHT NOW.
set -uo pipefail

CATALOG_URL="https://raw.githubusercontent.com/ClawLabsAI/free-ai-models/main/data/models.json"
ENV_FILE="$HOME/.hermes/.env"
STATE_DIR="$HOME/.hermes/state/model-manager"
mkdir -p "$STATE_DIR"
STAMP=$(date +%Y%m%d-%H%M%S)

# Read a key from .env
env_val() { grep "^$1=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"'; }

NOUS_KEY=$(env_val NOUS_API_KEY)
OR_KEY=$(env_val OPENROUTER_API_KEY)
OC_KEY=$(env_val OPENCODE_API_KEY)
CC_KEY=$(env_val COMMANDCODE_API_KEY)
KILO_KEY=$(env_val KILOCODE_API_KEY)

# Live-test a model on an endpoint. args: label base_url key model
test_model() {
  local label="$1" base="$2" key="$3" model="$4"
  [ -z "$key" ] && { echo "$label|$model|NO_KEY"; return; }
  local out
  out=$(timeout 20 curl -s "$base/chat/completions" \
    -H "Authorization: Bearer $key" -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK\"}],\"max_tokens\":5}" 2>/dev/null)
  if echo "$out" | grep -q '"choices"'; then
    echo "$label|$model|OK"
  elif echo "$out" | grep -q "429"; then
    echo "$label|$model|429"
  elif echo "$out" | grep -q "402\|balance\|credits"; then
    echo "$label|$model|402"
  elif echo "$out" | grep -q "401\|Invalid\|AuthError"; then
    echo "$label|$model|401"
  elif echo "$out" | grep -q "503\|overloaded\|unavailable"; then
    echo "$label|$model|503"
  else
    echo "$label|$model|ERR"
  fi
}

{
  echo "# Model Manager Sweep — $STAMP"
  echo
  echo "## Catalog (free-ai-models, updated daily)"
  timeout 30 curl -s "$CATALOG_URL" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'{d.get(\"updated_at\",\"?\")} — {d.get(\"total_free_models\",\"?\")} models')
    for m in d.get('models', []):
        print(f'  {m[\"id\"]}')
except Exception as e:
    print(f'catalog parse error: {e}')
" || echo "catalog unreachable"

  echo
  echo "## Live verification (all endpoints)"
  # Core free models across our endpoints — rotate laguna everywhere
  echo "### nous"
  test_model "nous" "https://inference-api.nousresearch.com/v1" "$NOUS_KEY" "meituan/longcat-2.0:free"
  test_model "nous" "https://inference-api.nousresearch.com/v1" "$NOUS_KEY" "inclusionai/ling-3.0-flash-fin:free"
  test_model "nous" "https://inference-api.nousresearch.com/v1" "$NOUS_KEY" "poolside/laguna-s-2.1:free"
  test_model "nous" "https://inference-api.nousresearch.com/v1" "$NOUS_KEY" "poolside/laguna-xs-2.1:free"
  test_model "nous" "https://inference-api.nousresearch.com/v1" "$NOUS_KEY" "z-ai/glm-5.2:free"
  test_model "nous" "https://inference-api.nousresearch.com/v1" "$NOUS_KEY" "thinkingmachines/inkling:free"
  echo "### openrouter"
  test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "minimax/minimax-m3:free"
  test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "inclusionai/ling-3.0-flash-fin:free"
  test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "poolside/laguna-s-2.1:free"
  test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "poolside/laguna-xs-2.1:free"
  test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "z-ai/glm-5.2:free"
  test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "nvidia/nemotron-3-super-120b-a12b:free"
  test_model "openrouter" "https://openrouter.ai/api/v1" "$OR_KEY" "cohere/north-mini-code:free"
  echo "### opencode-zen"
  test_model "opencode-zen" "https://opencode.ai/zen/v1" "$OC_KEY" "laguna-s-2.1-free"
  test_model "opencode-zen" "https://opencode.ai/zen/v1" "$OC_KEY" "ling-3.0-flash-fin-free"
  echo "### commandcode"
  test_model "commandcode" "https://api.commandcode.ai/provider/v1" "$CC_KEY" "poolside/laguna-s-2.1-free"
  echo "### kilo"
  test_model "kilo" "https://api.kilo.ai/api/gateway" "$KILO_KEY" "kilo-auto/free"
} > "$STATE_DIR/sweep-$STAMP.md"

cat "$STATE_DIR/sweep-$STAMP.md" | head -60
echo
echo "Sweep saved: $STATE_DIR/sweep-$STAMP.md"
