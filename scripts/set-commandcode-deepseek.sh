#!/bin/bash
# set-commandcode-deepseek.sh — make commandcode ONLY deepseek-v4-flash + :free
# Hard constraint (j_kro 2026-09-01): commandcode = deepseek/deepseek-v4-flash
# + :free models. NO other paid models from this provider.
set -uo pipefail

# 1. Fix the provider def in global + all profiles: model -> deepseek-v4-flash
hermes config set providers.commandcode.model "deepseek/deepseek-v4-flash" >/dev/null 2>&1 && echo "global provider def -> deepseek/deepseek-v4-flash"
for p in /home/j_kro/.hermes/profiles/*/; do
  prof=$(basename "$p")
  if [ -f "$p/config.yaml" ]; then
    hermes config set -p "$prof" providers.commandcode.model "deepseek/deepseek-v4-flash" >/dev/null 2>&1 && echo "  $prof provider def -> deepseek-v4-flash"
  fi
done

# 2. Update fallback chains: replace any commandcode paid-model entry with deepseek-v4-flash
#    (only poolside/laguna-s-2.1-free was there, which is :free — keep it but ensure it's the free one)
for f in ~/.hermes/config.yaml /home/j_kro/.hermes/profiles/*/config.yaml; do
  python3 - "$f" <<'PY'
import sys, yaml, io
f = sys.argv[1]
with open(f) as fh: d = yaml.safe_load(fh)
chain = d.get('fallback_providers', [])
changed = False
for e in chain:
    if e.get('provider') == 'commandcode' and e.get('model') != 'poolside/laguna-s-2.1-free' and ':free' not in str(e.get('model','')):
        e['model'] = 'deepseek/deepseek-v4-flash'
        changed = True
if changed:
    with open(f, 'w') as fh: yaml.safe_dump(d, fh, default_flow_style=False, sort_keys=False)
    print('  updated chain:', f)
PY
done

echo
echo '=== verify global commandcode ==='
hermes config get providers.commandcode 2>&1
