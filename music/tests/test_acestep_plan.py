#!/usr/bin/env python3
"""Render-wrapper regression checks. Run: python3 music/tests/test_acestep_plan.py

Standalone (no pytest), same requirement as the wrapper itself: it must run
anywhere python3 does. Each check exists because the defect it pins reached the
live cluster.

WHY THIS FILE EXISTS (card t_25a6499c D3/D5, card t_8c5a6b91)
------------------------------------------------------------
The render rail is `music-pipeline-render` -> `acestep_plan.py`. Two defects
there were invisible because nothing exercised the wrapper's own decisions:

  * `build_suno_request` hardcoded `"instrumental": False` and dropped
    `plan["bpm"]` and `plan["key"]` entirely, so a queued instrumental rendered
    as a vocal track and the engine answered its hardcoded 120 BPM for every
    genre. Live proof: `/var/lib/music-plans/*.rendered` markers.
  * `check_lyrics` refused any plan whose sections are empty, which is every
    instrumental plan BY DESIGN — so the review of the refusal (card t_a14e5d52)
    was correct to keep it and the instrumental mode had to be a separate,
    explicitly declared path rather than a relaxation.
"""

import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
WRAPPER = REPO / "music" / "scripts" / "acestep_plan.py"

spec = importlib.util.spec_from_file_location("acestep_plan", WRAPPER)
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def plan(**over) -> dict:
    base = {
        "title": "t", "caption": "a genre caption, 72 BPM", "lyrics": "[Instrumental]\n",
        "bpm": 72, "key": "C minor", "duration": 180, "timesignature": "4",
        "instrumental": True,
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
print("1. tempo, key and the instrumental flag are CARRIED to the engine")

# REGRESSION (2026-10-16, t_25a6499c D1/D2/D5). The wrapper used to send
# `"instrumental": False`, no `bpm` and no `keyscale`; the body had no field for
# the last two, so the engine fell back to 120 BPM and to using the style
# caption as the key signature. Sentimental-piano measured 120 against its own
# 72 anchor, with a 674-character caption in the key field.
req = ap.build_suno_request(plan())
check("instrumental=true is carried", req["instrumental"] is True, repr(req.get("instrumental")))
check("the plan's bpm is carried", req["bpm"] == 72, repr(req.get("bpm")))
check("the plan's key is carried as keyscale", req["keyscale"] == "C minor", repr(req.get("keyscale")))

# A plan without the field is still a vocal plan: every plan already on disk
# lacks it, and silently flipping them to instrumental would be worse than the
# defect being fixed. A plan without bpm/key must send None, so the engine
# applies its own documented defaults instead of something invented here.
req = ap.build_suno_request({k: v for k, v in plan().items()
                             if k not in ("instrumental", "bpm", "key")})
check("a plan without the flag is treated as vocal", req["instrumental"] is False)
check("an absent bpm/key is sent as None, not guessed",
      req["bpm"] is None and req["keyscale"] is None,
      f"bpm={req['bpm']!r} keyscale={req['keyscale']!r}")

# The engine's explicit-bpm precedence must be reachable from a plan, which is
# what the 8 instrumental genres need (their anchors are 72..150, none of them
# 120).
for g_bpm in (72, 82, 88, 92, 120, 150):
    req = ap.build_suno_request(plan(bpm=g_bpm))
    check(f"bpm {g_bpm} survives the wrapper", req["bpm"] == g_bpm, repr(req["bpm"]))

# ---------------------------------------------------------------------------
print()
print("2. the DRAFT refusal is NOT relaxed")

# A draft plan: section tags with the template's craft notes and no singable
# lines. It has NO `instrumental` field. Rendering it ships a track whose vocal
# line is the craft notes, so it must still be refused.
DRAFT = {
    "title": "d", "caption": "c", "bpm": 120, "key": "C minor",
    "duration": 180, "timesignature": "4",
    "lyrics": "[Intro]\n(the motif, alone)\n\n[Chorus]\n(the bloom)\n",
}

try:
    ap.check_lyrics(DRAFT, allow_empty=False)
    check("a draft plan is refused", False, "check_lyrics returned instead of exiting")
except SystemExit:
    check("a draft plan is refused", True)

# The pre-fix hole, pinned: a scaffold is never COMPLETELY empty (it has tags),
# so a body-is-empty test passes it. This is why the check is section-level.
try:
    ap.check_lyrics({"lyrics": "[Verse]\n\n[Chorus]\n\n", "instrumental": False},
                    allow_empty=False)
    check("a scaffold with bare tags is refused", False, "returned instead of exiting")
except SystemExit:
    check("a scaffold with bare tags is refused", True)

# ---------------------------------------------------------------------------
print()
print("3. an INSTRUMENTAL plan is deliberately NOT refused")

# REGRESSION (2026-10-16, t_25a6499c D3). Every instrumental plan has bare
# section tags by design, so the draft refusal marked all 8 instrumental genres
# `.refused` forever and the queue could never render one. The plan's OWN
# `instrumental: true` field is the declaration - the exemption is NOT inferred
# from emptiness (that is the draft case above, which still refuses).
try:
    ap.check_lyrics(plan(lyrics="[Intro]\n[Verse]\n[Chorus]\n"), allow_empty=False)
    check("an instrumental plan with bare tags is accepted", True)
except SystemExit as e:
    check("an instrumental plan with bare tags is accepted", False, str(e))

try:
    ap.check_lyrics(plan(lyrics=""), allow_empty=False)
    check("an instrumental plan with an empty lyrics box is accepted", True)
except SystemExit as e:
    check("an instrumental plan with an empty lyrics box is accepted", False, str(e))

# A vocal plan that is merely EMPTY is still refused: the flag is the only way
# through, so `instrumental` cannot be set by accident downstream.
try:
    ap.check_lyrics({"lyrics": "", "instrumental": False}, allow_empty=False)
    check("an empty vocal plan is still refused", False, "returned instead of exiting")
except SystemExit:
    check("an empty vocal plan is still refused", True)

# ---------------------------------------------------------------------------
print()
print("4. the live plans on disk (read live state, not a fixture)")

PLANS = pathlib.Path("/var/lib/music-plans")
if PLANS.is_dir():
    for p in sorted(PLANS.glob("*.json")):
        try:
            d = json.loads(p.read_text())
        except json.JSONDecodeError:
            check(f"{p.name}: parses", False, "invalid JSON")
            continue
        inst = bool(d.get("instrumental"))
        mode = "instrumental" if inst else "vocal"
        # measured, not asserted: report what the live file actually says
        print(f"  INFO  {p.name}: {mode}, bpm={d.get('bpm')}, key={str(d.get('key'))[:28]!r}")
else:
    print(f"  SKIP  {PLANS} not present on this host")

# ---------------------------------------------------------------------------
print()
if fails:
    print(f"RESULT: FAIL ({len(fails)})")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS")
