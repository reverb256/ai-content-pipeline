#!/bin/bash
# free-model-catalog.sh — list ALL free models available on every provider
set -uo pipefail
ENV_FILE="$HOME/.hermes/.env"
env_val() { grep "^$1=" "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"'; }
NOUS_KEY=$(env_val NOUS_API_KEY); OR_KEY=$(env_val OPENROUTER_API_KEY)
OC_KEY=$(env_val OPENCODE_API_KEY); CC_KEY=$(env_val COMMANDCODE_API_KEY); KILO_KEY=$(env_val KILOCODE_API_KEY)

echo "===== NOUS (inference-api.nousresearch.com) ====="
timeout 30 curl -s https://inference-api.nousresearch.com/v1/models -H "Authorization: Bearer $NOUS_KEY" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    for m in d.get('data',[]):
        if 'free' in m['id']: print(' ', m['id'])
except Exception as e: print('  ERR', e)
"

echo "===== OPENROUTER (openrouter.ai, :free only) ====="
timeout 30 curl -s https://openrouter.ai/api/v1/models -H "Authorization: Bearer $OR_KEY" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    for m in d.get('data',[]):
        if ':free' in m['id']: print(' ', m['id'])
except Exception as e: print('  ERR', e)
"

echo "===== OPENCODE-ZEN (opencode.ai/zen) ====="
timeout 30 curl -s https://opencode.ai/zen/v1/models -H "Authorization: Bearer $OC_KEY" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    for m in d.get('data',[]):
        if 'free' in m['id'] or '-free' in m['id']: print(' ', m['id'])
except Exception as e: print('  ERR', e)
"

echo "===== COMMANDCODE (api.commandcode.ai) ====="
timeout 30 curl -s https://api.commandcode.ai/provider/v1/models -H "Authorization: Bearer $CC_KEY" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    for m in d.get('data',[]):
        if 'free' in m['id']: print(' ', m['id'])
except Exception as e: print('  ERR', e)
"

echo "===== KILO (api.kilo.ai) ====="
timeout 30 curl -s https://api.kilo.ai/api/gateway/v1/models -H "Authorization: Bearer $KILO_KEY" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    for m in d.get('data',[]):
        if 'free' in m['id'].lower(): print(' ', m['id'])
    if not d.get('data'): print('  (no data — endpoint may differ)')
except Exception as e: print('  ERR', e)
"
