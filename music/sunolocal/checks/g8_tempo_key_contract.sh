#!/usr/bin/env bash
# G8: explicit tempo + key contract (t_25a6499c D1/D2, t_1578cc47).
#
# REGRESSION FOR THE t_25a6499c INCIDENT (2026-10-16). Three defects were
# measured in the deployed engine, two of them here:
#
#   D1  translate.py hardcoded `bpm = 120`, and the only override repurposed
#       Suno's style-ADHERENCE dial as a tempo control. Measured: a
#       sentimental-piano request (674-char caption, genre anchor 72 BPM)
#       planned at 120 — 1.67x fast — and 72 was reachable only at
#       style_weight 0.1, i.e. by telling the engine to barely follow the
#       style. Every one of the 8 instrumental genres was affected.
#   D2  `key = req.style or "C major"` put the WHOLE style caption into the
#       key field, and acestep_plan.py passes it to the ACE node as
#       `keyscale`. Measured: 674 characters where a key signature belongs.
#
# AND A SECOND INCIDENT, t_1578cc47 (2026-10-16): the D2 fix kept a default,
# `key = req.keyscale or "C major"`. That default is a key NO INPUT STATES, and
# it is not cosmetic: measured against the ACE node's own source in the live pod,
# a NON-empty `keyscale` is injected token-by-token into the language model's
# constrained decode (acestep/constrained_logits_processor.py:1913), so it
# OVERRIDES whatever mode the caption asks for. The planner now emits the key an
# artifact states and null for the other 11 of 14 genres (t_f65b0f4c), which had
# just made this branch reachable for the first time. The contract pinned below:
#   * a plan that states no key carries `key = None`;
#   * the ACE wire carries "" for it — NOT None, because ComfyUI's own validation
#     stringifies a STRING input (`val = str(val)`) and a JSON null therefore
#     reaches the node as the key "None" (measured live, section 3);
#   * "" is the node's documented "leave empty for auto-detection".
#
# Neither D1/D2 was caught because no gate exercised the tempo or key at all: G3
# asserted only `60 <= bpm <= 240` and PINNED the D2 defect
# (`plan["key"] == "synthwave"`). This check is the one that would have failed
# on the pre-fix code. Negative control: run it with `key = req.style` restored
# and it fails on the caption assertion; run it with `key = req.keyscale or
# "C major"` restored and it fails on the no-fabricated-key assertion.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
G8_ROOT="$ROOT" python3 - <<'PY'
from music.sunolocal.spec import SunoGenerateRequest
from music.sunolocal import translate
from music.sunolocal.studio import GenerateBody, _to_internal

# The real shape: a 674-character genre caption that states the anchor tempo.
CAPTION = ("neoclassical sentimental piano, 72 BPM, intimate felt piano "
           "close-mic'd with soft hammers and audible pedal and key mechanism "
           "noise, one singable 4-6 note motif repeated with tiny variations, "
           "simple diatonic harmony with add9 sus2 and sixth color tones, "
           "chord changes every 2-4 bars, broken-chord left hand ostinato, "
           "gentle rubato pacing, small chamber cello and upper strings "
           "entering only at the emotional peak, one soft reversed swell "
           "before phrases, dark spacious reverb around the piano but the "
           "piano itself stays close and dry, mid-register focus, low "
           "velocities, no virtuosic runs, one emotional bloom then a gentle "
           "return to solo piano, nostalgic and hopeful at once")

# --- D1: the anchor is expressible explicitly, and it WINS ------------------
p = translate.suno_to_aceplan(SunoGenerateRequest(
    style=CAPTION, lyrics="", instrumental=True, duration=180, bpm=72))
assert p["bpm"] == 72, f"D1: explicit bpm=72 became {p['bpm']}"

# ...and it beats the style_weight fallback rather than being ignored by it.
p = translate.suno_to_aceplan(SunoGenerateRequest(
    style=CAPTION, bpm=72, style_weight=0.8))
assert p["bpm"] == 72, f"D1: style_weight overrode an explicit bpm: {p['bpm']}"

# The defect itself, pinned: with no explicit tempo the old value was 120.
p = translate.suno_to_aceplan(SunoGenerateRequest(style=CAPTION))
assert p["bpm"] == 120, f"D1: undocumented default changed to {p['bpm']}"

# the style_weight fallback still maps, but is not the documented interface
p = translate.suno_to_aceplan(SunoGenerateRequest(style=CAPTION, style_weight=0.1))
assert p["bpm"] == 72, p["bpm"]

# --- D2: the key is a key signature, never the caption ----------------------
p = translate.suno_to_aceplan(SunoGenerateRequest(style=CAPTION))
assert p["key"] != CAPTION, "D2 REGRESSED: the caption is in the key field"
assert len(p["key"] or "") <= 32, f"D2: key is {len(p['key'])} chars: {p['key'][:60]!r}"
# t_1578cc47: it is not a key signature either. A request that states no key
# produces a plan that states no key. The old `or "C major"` filled a field no
# input filled, and the ACE node injects a non-empty keyscale into its
# constrained decode, so the fabrication OVERRODE the caption's own mode.
assert p["key"] is None, f"t_1578cc47 REGRESSED: fabricated key {p['key']!r}"

p = translate.suno_to_aceplan(SunoGenerateRequest(style=CAPTION, keyscale="C major"))
assert p["key"] == "C major", p["key"]
p = translate.suno_to_aceplan(SunoGenerateRequest(keyscale="D Phrygian"))
assert p["key"] == "D Phrygian", p["key"]

# A key is stated when, and only when, an input states it: the same request with
# and without `keyscale` must differ in exactly that field.
_a = translate.suno_to_aceplan(SunoGenerateRequest(style=CAPTION))
_b = translate.suno_to_aceplan(SunoGenerateRequest(style=CAPTION, keyscale="E minor"))
assert (_a["key"], _b["key"]) == (None, "E minor"), (_a["key"], _b["key"])

# --- the wire body carries both fields to the internal request --------------
body = GenerateBody(prompt="x", style=CAPTION, instrumental=True, bpm=150,
                    keyscale="D Phrygian", duration=120)
inner = _to_internal(body)
assert inner.bpm == 150, inner.bpm
assert inner.keyscale == "D Phrygian", inner.keyscale
plan = translate.suno_to_aceplan(inner)
assert plan["bpm"] == 150 and plan["key"] == "D Phrygian", plan

# --- the renderer, and the value the ACE NODE actually receives -------------
# REGRESSION (t_1578cc47). The composer is acestep_plan_direct.py: it reads the
# plan, builds the ComfyUI workflow and posts it. Two measured facts pin the
# contract here:
#   * it must ACCEPT a plan whose key is null. It used to exit FATAL on one
#     ("plan is missing 'key'") — measured — which is why the engine's
#     fabricated "C major" could not simply be deleted: the two had to move
#     together. A null key is a normal plan (11 of 14 genres), not a malformed
#     one.
#   * it must send "" for it, never None, because ComfyUI's own input validation
#     stringifies a STRING input. Measured on the LIVE node 2026-10-16 with a
#     GenerationParams -> PreviewAny probe: keyscale=None arrived as the key
#     "None" (a value in neither the 70-entry VALID_KEYSCALES nor the caption);
#     keyscale="" arrived as ''. "" is the node's documented auto-detection.
import importlib.util
import json
import os
import pathlib
import tempfile

ROOT = pathlib.Path(os.environ["G8_ROOT"])
_spec = importlib.util.spec_from_file_location(
    "g8_acestep_plan_direct", ROOT / "music" / "scripts" / "acestep_plan_direct.py")
direct = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(direct)

NO_KEY = {"caption": "jungle dnb, 168 BPM, rolling amen break",
          "lyrics": "[Instrumental]\n", "bpm": 168, "key": None,
          "duration": 16, "timesignature": "4", "instrumental": True}


def _write(plan: dict):
    td = tempfile.TemporaryDirectory()
    p = pathlib.Path(td.name) / "plan.json"
    p.write_text(json.dumps(plan), encoding="utf-8")
    return td, p


_td, _p = _write(NO_KEY)
loaded = direct.load_plan(str(_p))          # must NOT exit
assert loaded["key"] is None, loaded["key"]
_td.cleanup()

wf = direct.build(NO_KEY, seed=1, filename="g8")
got = wf["2"]["inputs"]["keyscale"]
assert isinstance(got, str), f"keyscale must be a STRING on the wire, got {got!r}"
assert got == "", f"t_1578cc47 REGRESSED: a plan with no key sent {got!r} to the ACE node"
wf = direct.build({**NO_KEY, "key": "A minor"}, seed=1, filename="g8")
assert wf["2"]["inputs"]["keyscale"] == "A minor", wf["2"]["inputs"]["keyscale"]

# The exemption is `key` ONLY: the other five fields are still required, so a
# truncated plan cannot reach the node through this door.
for _missing in ("caption", "lyrics", "bpm", "duration", "timesignature"):
    _td, _p = _write({k: v for k, v in NO_KEY.items() if k != _missing})
    try:
        direct.load_plan(str(_p))
        raise AssertionError(f"load_plan accepted a plan with no {_missing!r}")
    except SystemExit:
        pass
    finally:
        _td.cleanup()

print("G8-OK: explicit bpm and keyscale reach the ACE plan; a plan that states "
      "no key states none, and the node is told so with \"\"")
PY
