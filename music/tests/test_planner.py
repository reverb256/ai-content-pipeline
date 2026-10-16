#!/usr/bin/env python3
"""Planner regression checks. Run: python3 music/tests/test_planner.py

These exist because each one caught a real defect that shipped. They are
deliberately standalone (no pytest) so they run anywhere python3 does, which is
the same requirement the planner itself has.
"""

import importlib.util
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
PLANNER = REPO / "music" / "planner" / "planner.py"

spec = importlib.util.spec_from_file_location("planner", PLANNER)
pl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pl)

BRIEF = "a scene about the moment before something important begins"

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


def genres() -> list[str]:
    reg = pl.load_registry()
    return sorted(reg["genres"])


# ---------------------------------------------------------------------------
print("1. every genre plans, and gets a tempo from its own research")

# REGRESSION (2026-10-09). The draft path resolved bpm as
# `blueprint.bpm_anchor or 100`. Only 3 of 14 genres have a blueprint, so 11
# genres were planned at a flat 100 BPM while their own template captions
# stated the real tempo: jungle-dnb came out 100 against a stated 168,
# anime-opening 100 against 160. A generic tempo is not a neutral default - it
# is a wrong answer that validation then could not catch, because validation
# read the same anchor and found nothing to disagree with.
for g in genres():
    out = pathlib.Path(f"/tmp/_tp-{g}.json")
    r = subprocess.run(
        [sys.executable, str(PLANNER), "plan", "--brief", BRIEF,
         "--genre", g, "--lyrics-mode", "draft", "--out", str(out)],
        capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        check(f"{g}: plans", False, tail[-1] if tail else "no output")
        continue
    plan = json.loads(out.read_text())
    ctx = pl.context_for(g)
    want = pl.bpm_anchor_for(ctx)
    check(f"{g}: bpm {plan['bpm']} matches its source ({want})",
          want is not None and plan["bpm"] == want,
          f"planned {plan['bpm']}, source says {want}")

# ---------------------------------------------------------------------------
print()
print("2. the empty-section check fires on an empty section")

# REGRESSION (2026-10-09). The first version of this check used `\\s*\\n` as the
# tag separator. `\\s` matches newlines, so an empty section swallowed the blank
# lines AND the next section's tag, inherited the following section's lyrics,
# and reported as full - so the check passed a plan whose Intro and Outro were
# bare tags. It is `[ \\t]*\\n` now, and this is the negative control that
# caught it.
ctx = pl.context_for("anime-opening")
good = {"lyrics": "[Intro]\nline one\n\n[Chorus]\nline two\n\n[Outro]\nline three\n",
        "bpm": pl.bpm_anchor_for(ctx), "key": "C minor", "duration": 90,
        "timesignature": "4", "caption": ctx["template"]["caption"]}
ok_clean = not [p for p in pl.validate(good, ctx, BRIEF, "en") if "no lyrics" in p]
check("a full plan reports no empty sections", ok_clean)

for tag in ("Intro", "Chorus", "Outro"):
    bad = json.loads(json.dumps(good))
    bad["lyrics"] = re.sub(rf"(\[{re.escape(tag)}\])\n[^\n]*\n", r"\1\n", bad["lyrics"])
    hits = [p for p in pl.validate(bad, ctx, BRIEF, "en") if "no lyrics" in p]
    check(f"emptying [{tag}] is reported", bool(hits) and tag in hits[0], "check did not fire")

# ---------------------------------------------------------------------------
print()
print("3. the bpm source order is blueprint, then caption")

# chill-lounge has both and they differ (blueprint 72, caption 75). The
# blueprint is the hand-researched decision and must win.
cl = pl.context_for("chill-lounge")
check("blueprint wins over the caption when both exist",
      cl["blueprint"].get("bpm_anchor") == 72 and cl["template_bpm"] == 75
      and pl.bpm_anchor_for(cl) == 72,
      f"blueprint={cl['blueprint'].get('bpm_anchor')} caption={cl['template_bpm']}")

# ---------------------------------------------------------------------------
print()
if fails:
    print(f"RESULT: FAIL ({len(fails)})")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS")
