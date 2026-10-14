#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
python3 - <<'PY'
from music.sunolocal import translate
from music.sunolocal.spec import SunoGenerateRequest

r = SunoGenerateRequest(style="synthwave", prompt="dreamy neon", lyrics="[Chorus]\nshine", duration=42, style_weight=0.5)
plan = translate.suno_to_aceplan(r)
assert plan["caption"] == "dreamy neon synthwave", plan
assert plan["lyrics"] == "[Chorus]\nshine", plan
assert plan["duration"] == 42.0, plan
assert isinstance(plan["bpm"], int) and 60 <= plan["bpm"] <= 240, plan
assert plan["timesignature"] == "4", plan
assert plan["key"] == "synthwave", plan

d = translate.suno_to_aceplan(SunoGenerateRequest())
assert d["caption"] == "music", d
assert d["duration"] == 30.0, d
assert d["bpm"] == 120, d
assert d["lyrics"] == "", d

y = translate.suno_to_yue2(SunoGenerateRequest(style="ambient", lyrics="la", seed=7, style_weight=0.25))
assert y["style"] == "ambient" and y["lyrics"] == "la" and y["seed"] == 7, y
assert abs(y["cfg_scale"] - 3.25) < 1e-9, y
assert y["cot"] == "full", y
print("G3-OK")
PY
