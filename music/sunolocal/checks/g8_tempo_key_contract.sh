#!/usr/bin/env bash
# G8: explicit tempo + key contract (t_25a6499c D1/D2).
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
# Neither was caught because no gate exercised the tempo or key at all: G3
# asserted only `60 <= bpm <= 240` and PINNED the D2 defect
# (`plan["key"] == "synthwave"`). This check is the one that would have failed
# on the pre-fix code. Negative control: run it with `key = req.style` restored
# and it fails on the caption assertion.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
python3 - <<'PY'
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
assert len(p["key"]) <= 32, f"D2: key is {len(p['key'])} chars: {p['key'][:60]!r}"
assert p["key"] == "C major", p["key"]

p = translate.suno_to_aceplan(SunoGenerateRequest(style=CAPTION, keyscale="C major"))
assert p["key"] == "C major", p["key"]
p = translate.suno_to_aceplan(SunoGenerateRequest(keyscale="D Phrygian"))
assert p["key"] == "D Phrygian", p["key"]

# --- the wire body carries both fields to the internal request --------------
body = GenerateBody(prompt="x", style=CAPTION, instrumental=True, bpm=150,
                    keyscale="D Phrygian", duration=120)
inner = _to_internal(body)
assert inner.bpm == 150, inner.bpm
assert inner.keyscale == "D Phrygian", inner.keyscale
plan = translate.suno_to_aceplan(inner)
assert plan["bpm"] == 150 and plan["key"] == "D Phrygian", plan
print("G8-OK: explicit bpm and keyscale reach the ACE plan; key is never the caption")
PY
