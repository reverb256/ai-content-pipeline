#!/usr/bin/env bash
# G3: Suno -> engine mappings and defaults.
#
# UPDATED for t_25a6499c. Two pinned assertions had to change with the fix, and
# each now pins the FIXED contract instead of the defect:
#   * `key` was pinned to `req.style` ("synthwave"). That is D2: the style field
#     is the genre's whole caption (674 chars measured for sentimental-piano) and
#     acestep_plan.py hands this value to the ACE node as `keyscale`.
#   * `bpm` had no explicit-field assertion at all, which is how D1 (hardcoded
#     120) went unnoticed. The explicit field and the precedence order are
#     pinned here and exercised end-to-end by g8.
#
# UPDATED AGAIN for t_1578cc47. Those two lines pinned "C major" as the key of a
# request that states no key — a key no input states. Measured against the ACE
# node's own source in the live pod, a non-empty `keyscale` is injected into the
# LM's constrained decode, so that default OVERRODE the caption's mode for the 11
# of 14 genres whose caption states no key. A request with no key now plans to
# `key = None`, and the renderer sends "" (the node's auto-detect) on the wire;
# g8 owns the wire half and the negative controls.
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
# style_weight is only a FALLBACK now (0.5 -> 120); the key is NEVER the style,
# and a request that states no key does not acquire one (t_1578cc47).
assert plan["key"] is None, plan

d = translate.suno_to_aceplan(SunoGenerateRequest())
assert d["caption"] == "music", d
assert d["duration"] == 30.0, d
assert d["bpm"] == 120, d
assert d["lyrics"] == "", d
assert d["key"] is None, d

# t_25a6499c D1: an explicit tempo wins over the style_weight fallback.
assert translate.suno_to_aceplan(
    SunoGenerateRequest(bpm=72, style_weight=0.8))["bpm"] == 72
# t_25a6499c D2: an explicit key signature wins, and never becomes the caption.
assert translate.suno_to_aceplan(
    SunoGenerateRequest(keyscale="D Phrygian", style="a 600 char caption"))["key"] == "D Phrygian"
# ...including when style IS set and no key is given (the old defect): the
# caption does NOT become the key (D2), and no key is invented either (t_1578cc47).
assert translate.suno_to_aceplan(
    SunoGenerateRequest(style="a 600 char caption"))["key"] is None
# The clamp still applies to an explicit value.
assert translate.suno_to_aceplan(SunoGenerateRequest(bpm=999))["bpm"] == 240

y = translate.suno_to_yue2(SunoGenerateRequest(style="ambient", lyrics="la", seed=7, style_weight=0.25))
assert y["style"] == "ambient" and y["lyrics"] == "la" and y["seed"] == 7, y
assert abs(y["cfg_scale"] - 3.25) < 1e-9, y
assert y["cot"] == "full", y
print("G3-OK")
PY
