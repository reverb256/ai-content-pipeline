#!/usr/bin/env python3
"""Planner regression checks. Run: python3 music/tests/test_planner.py

These exist because each one caught a real defect that shipped. They are
deliberately standalone (no pytest) so they run anywhere python3 does, which is
the same requirement the planner itself has.
"""

import importlib.util
import json
import os
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
print("4. instrumental mode (t_25a6499c D3)")

# REGRESSION (2026-10-16). The planner queue could not express an instrumental
# track AT ALL: --lyrics-mode accepted only `draft|ai`, `draft` is refused by
# acestep_plan.py (exit 1, a `.refused` marker) and `ai` writes lyrics a genre
# that must have none cannot carry - and which void the authorship claim. So
# 8 of the 14 genres had no supported entry point into the queue, and the
# `sunolocal/translate.py` inline comment even named NINE of them by wrongly
# including epic-orchestral-boss (whose template has 0 instrumental markers and
# says "Choir only - no solo lyrical singing").
#
# The decision itself was never in doubt: suno-gen.py has decided it since
# ba28f55 from the genre's own template. The planner had no third mode.
INST = ["chill-lounge", "chiptune-8bit", "commentary-beds", "elemental-air",
        "elemental-earth", "elemental-fire", "elemental-water", "sentimental-piano"]
VOCAL = ["activist", "anime-ending", "anime-opening", "epic-orchestral-boss",
         "jungle-dnb", "trance"]

for g in INST:
    out = pathlib.Path(f"/tmp/_tp-inst-{g}.json")
    r = subprocess.run(
        [sys.executable, str(PLANNER), "plan", "--brief", BRIEF,
         "--genre", g, "--lyrics-mode", "instrumental", "--out", str(out)],
        capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        check(f"{g}: instrumental plans", False, tail[-1] if tail else "no output")
        continue
    plan = json.loads(out.read_text())
    ctxg = pl.context_for(g)
    want = pl.bpm_anchor_for(ctxg)
    want_key = pl.key_anchor_for(ctxg)
    # `key` is NOT part of the instrumental contract: it is whatever an artifact
    # states, and null for the 11 genres whose caption states none. What must
    # hold is that the plan claims no key that no artifact states (t_f65b0f4c).
    check(f"{g}: plan is instrumental, bpm {plan['bpm']} == anchor {want}, "
          f"key is stated-or-null",
          plan.get("instrumental") is True and plan["bpm"] == want
          and plan.get("key") == want_key,
          f"instrumental={plan.get('instrumental')} bpm={plan['bpm']} "
          f"key={plan['key']!r} want_key={want_key!r}")

# A vocal genre must NOT be forced down the instrumental path: that would strip
# the element that defines it. epic-orchestral-boss is the measured case.
for g in VOCAL:
    r = subprocess.run(
        [sys.executable, str(PLANNER), "plan", "--brief", BRIEF, "--genre", g,
         "--lyrics-mode", "instrumental", "--out", f"/tmp/_tp-instvocal-{g}.json"],
        capture_output=True, text=True)
    check(f"{g}: instrumental mode refused (rc={r.returncode})", r.returncode == 2,
          (r.stdout + r.stderr)[:140])

# The refusal must NOT be relaxed: a draft plan still carries no `instrumental`
# flag, which is what keeps acestep_plan.py refusing it.
out = pathlib.Path("/tmp/_tp-draftflag.json")
subprocess.run([sys.executable, str(PLANNER), "plan", "--brief", BRIEF,
                "--genre", "sentimental-piano", "--lyrics-mode", "draft",
                "--out", str(out)], capture_output=True, text=True)
draft = json.loads(out.read_text())
check("a draft plan is not marked instrumental", draft.get("instrumental") is False)

# An instrumental plan is STRUCTURE, never words: that is what makes it
# acceptable to the renderer without relaxing the draft refusal.
esc = json.loads(pathlib.Path("/tmp/_tp-inst-sentimental-piano.json").read_text())
check("an instrumental plan carries no singable lines",
      not [ln for ln in esc["lyrics"].splitlines()
           if ln.strip() and not ln.strip().startswith(("[", "#", "("))],
      repr(esc["lyrics"]))

# The registry's own loop-10min video shape is 600 s and used to be outside the
# guard (MAX_DURATION_S was 420), so elemental-earth's documented entry could
# not be planned at all.
check("the 600 s loop-10min shape is inside the duration guard",
      pl.MIN_DURATION_S <= 600 <= pl.MAX_DURATION_S, f"MAX={pl.MAX_DURATION_S}")

# The predicate is a COPY of suno-gen.py's, and a copy drifts. Pin the two
# together over every genre: if the CDP rail and the planner ever disagree, a
# genre is queued as one thing and generated as the other.
sg_spec = importlib.util.spec_from_file_location("suno_gen", REPO / "music" / "suno-gen.py")
sg = importlib.util.module_from_spec(sg_spec)
sg_spec.loader.exec_module(sg)
for g in genres():
    a, b = pl.is_instrumental_template(g), sg.is_instrumental_template(g)
    check(f"{g}: planner and suno-gen agree on instrumental ({a})", a == b,
          f"planner={a} suno-gen={b}")

inst = [g for g in genres() if pl.is_instrumental_template(g)]
check(f"the instrumental census is 8 of {len(genres())} genres", len(inst) == 8,
      f"got {len(inst)}: {inst}")
check("epic-orchestral-boss is NOT in the instrumental census",
      "epic-orchestral-boss" not in inst)

# ---------------------------------------------------------------------------
print()
print("5. the plan's key is what an artifact states, never a default (t_f65b0f4c)")

# REGRESSION (2026-10-16, cards t_f65b0f4c and t_791b48f7). The draft and
# instrumental paths resolved the key as `args.key or "C minor"`, and the
# scheduled CronJob passes no --key, so EVERY plan the pipeline produced claimed
# "C minor" whatever the genre: the four live plans in /var/lib/music-plans
# (chill-lounge 72 BPM, anime-ending 92, epic-orchestral-boss 150, trance 138)
# all said C minor on 2026-10-16. For trance that contradicted the plan's own
# caption ("hall reverb, A minor, extended club arrangement") and the queued
# brief ("Uplifting trance at 138 BPM in A minor"). `bpm` had the same defect
# and was fixed against the caption; `key` was left behind - and since card
# t_25a6499c D2 the plan's key is ALSO carried to the engine as `keyscale`, so a
# fabricated value is no longer only a reading-surface problem.
#
# The invariant, over every genre in genres.yaml: the plan's key is the key its
# own caption states, and is null when the caption states none. The caption is
# the only key claim backed by an artifact (the genre template) and the only
# text the engine receives.
for g in genres():
    out = pathlib.Path(f"/tmp/_tp-key-{g}.json")
    r = subprocess.run(
        [sys.executable, str(PLANNER), "plan", "--brief", BRIEF,
         "--genre", g, "--lyrics-mode", "draft", "--out", str(out)],
        capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        check(f"{g}: draft plans", False, tail[-1] if tail else "no output")
        continue
    plan = json.loads(out.read_text())
    stated = pl.key_in_caption(pl.context_for(g)["template"]["caption"] or "")
    check(f"{g}: key {plan['key']!r} is the key its caption states ({stated!r})",
          plan.get("key") == stated, f"planned {plan['key']!r}, caption {stated!r}")

# The census is measured here, not assumed. 3 of 14 captions state a key, and
# naming them is what makes a template that GAINS or LOSES a key visible.
stated_genres = sorted(
    g for g in genres()
    if pl.key_in_caption(pl.context_for(g)["template"]["caption"] or ""))
check(f"3 of {len(genres())} genre captions state a key",
      len(stated_genres) == 3, str(stated_genres))
check("the three are elemental-water, epic-orchestral-boss, trance",
      stated_genres == ["elemental-water", "epic-orchestral-boss", "trance"],
      str(stated_genres))

# The exact case the incident was found on (card t_791b48f7), and the case that
# proves no default replaced the fabrication.
trance = json.loads(pathlib.Path("/tmp/_tp-key-trance.json").read_text())
check("trance states 'A minor', not the old 'C minor'",
      trance["key"] == "A minor", repr(trance["key"]))
cl = json.loads(pathlib.Path("/tmp/_tp-key-chill-lounge.json").read_text())
check("chill-lounge (no key in its caption) emits null, not an invention",
      cl["key"] is None, repr(cl["key"]))

# The resolution order mirrors bpm's: explicit request, blueprint decision,
# caption, and then NOTHING.
check("an explicit key wins over a blueprint decision",
      pl.key_anchor_for({"blueprint": {"key_anchor": "D Phrygian"},
                         "template_key": "A minor"}) == "D Phrygian")
check("a blueprint key_anchor wins over the caption",
      pl.key_anchor_for({"blueprint": {"key_anchor": "F# minor"},
                         "template_key": "A minor"}) == "F# minor")
check("a blueprint plain `key` is accepted too (card t_f65b0f4c step 3)",
      pl.key_anchor_for({"blueprint": {"key": "Bb major"},
                         "template_key": "A minor"}) == "Bb major")
check("no artifact states a key -> None, never a default",
      pl.key_anchor_for({"blueprint": {}, "template_key": None}) is None)
# No live blueprint pins a key yet, so the caption is what the live plans use.
# Pin that fact: if a blueprint gains a key_anchor, this tells the reader why a
# plan's key stops matching its caption.
anchored = sorted(g for g in genres()
                  if pl.context_for(g)["blueprint"].get("key_anchor")
                  or pl.context_for(g)["blueprint"].get("key"))
check("no live blueprint pins a key yet (the caption is the only live source)",
      anchored == [], str(anchored))

# NEGATIVE CONTROL for the caption reader. elemental-water's caption says BOTH
# "a minor key with add9 color" (lowercase - a description of modality) and
# ", C minor" (the signature). A case-INsensitive note name reads the first and
# returns the wrong key, so the pattern is case-sensitive on the note name and
# this is the case that caught it.
check("'a minor key' is not a signature (case-sensitive note name)",
      pl.key_in_caption("slow melancholic melody in a minor key with add9 color") is None,
      repr(pl.key_in_caption("slow melancholic melody in a minor key with add9 color")))
check("elemental-water's caption reads 'C minor', not 'a minor'",
      pl.key_in_caption(pl.context_for("elemental-water")["template"]["caption"]) == "C minor",
      repr(pl.key_in_caption(pl.context_for("elemental-water")["template"]["caption"])))
check("epic-orchestral-boss's caption reads 'C minor' from '150 BPM in C minor'",
      pl.key_in_caption(pl.context_for("epic-orchestral-boss")["template"]["caption"])
      == "C minor")
# Every non-key phrase is lifted from a live template. None may read as a key.
for phrase in ("FINAL CHORUS JUMPS UP ONE KEY - the defining anison gesture",
               "gentle key lift in the last chorus",
               "audible pedal and key mechanism noise",
               "simple key-triggered echo instead of reverb",
               "minor key with flat-2 Phrygian color",
               "pop vocals, EDM drop, trap, happy major key",
               "the key-change moment as metatags"):
    check(f"not a key: {phrase[:36]!r}", pl.key_in_caption(phrase) is None,
          repr(pl.key_in_caption(phrase)))

# End to end, through the render wrapper. SUNOLOCAL_HOST points at a closed
# port, so the submit fails fast - but `build_suno_request()` and the params
# print both run BEFORE it, so reaching the failure proves the wrapper carried
# `keyscale: null` without raising, and the print must not present that null as
# a key.
if pathlib.Path("/tmp/_tp-inst-chill-lounge.json").is_file():
    env = dict(os.environ, SUNOLOCAL_HOST="http://127.0.0.1:9")
    rr = subprocess.run(
        [sys.executable, str(REPO / "music" / "scripts" / "acestep_plan.py"),
         "/tmp/_tp-inst-chill-lounge.json", "--name", "tf-key-cl"],
        capture_output=True, text=True, env=env, timeout=120)
    check("acestep_plan.py renders a null-key plan without raising (no 'missing key')",
          "missing 'key'" not in (rr.stdout + rr.stderr), repr((rr.stdout + rr.stderr)[-200:]))
    check("acestep_plan.py prints key=unknown for a plan that states no key",
          "key=unknown" in rr.stdout, repr(rr.stdout[-200:]))
    check("acestep_plan.py never prints a bare None where a key belongs",
          "· None ·" not in rr.stdout, repr(rr.stdout[-200:]))
else:
    print("  SKIP  the instrumental chill-lounge plan was not produced above")

# ---------------------------------------------------------------------------
print()
if fails:
    print(f"RESULT: FAIL ({len(fails)})")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS")
