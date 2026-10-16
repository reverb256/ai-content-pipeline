#!/usr/bin/env python3
"""Planner regression checks. Run: python3 music/tests/test_planner.py

These exist because each one caught a real defect that shipped. They are
deliberately standalone (no pytest) so they run anywhere python3 does, which is
the same requirement the planner itself has.
"""

import ast
import atexit
import importlib.util
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
PLANNER = REPO / "music" / "planner" / "planner.py"

# ---------------------------------------------------------------------------
# The suite's scratch is PRIVATE to the run (card t_7ab98781)
# ---------------------------------------------------------------------------
# REGRESSION (2026-10-16). Every intermediate plan used to be written to a FIXED
# name in the SHARED temp directory: `/tmp/_tp-<genre>.json`,
# `/tmp/_tp-rail-16.json`, `/tmp/_tp-kit-bed.json`, and so on. That directory is
# world-writable but STICKY, so what decides who may replace a file there is its
# OWNER, not its mode. A sibling card ran THIS suite from a root shell at
# 17:52-17:53 and left `/tmp/_tp-activist.json` behind as root:root 644. From
# then on every j_kro run died on it:
#     FAIL  activist: plans  [PermissionError: [Errno 13] Permission denied]
#     PermissionError: [Errno 1] Operation not permitted: '/tmp/_tp-rail-16.json'
# (EACCES opening a foreign file for write, EPERM unlinking in a sticky
# directory). The scheduled matrix read the unhandled exception as a gate that
# misbehaved:
#     BROKEN: 1 check(s) misbehaved      # 19 PASS / 26 expected FAILS / 1 BAD
# with every gate green - a gate regression that was not one. ONE run by ANY
# other user broke this suite for EVERY other user, permanently.
#
# The failure needs the PATH to be shared, so the path is not shared any more:
# one private directory per run, made by mkdtemp (mode 0700, unique name, so no
# other user can place a file in it and two runs cannot collide), removed at
# exit. Section 8 is the check that keeps it that way.
SCRATCH = pathlib.Path(tempfile.mkdtemp(prefix=f"_tp-suite-{os.getuid()}-"))
atexit.register(shutil.rmtree, SCRATCH, True)


def scratch(name: str) -> pathlib.Path:
    """A path in THIS run's private scratch directory.

    Every file the suite writes goes through here, so no assertion can depend on
    a path another user may create. A stale file owned by someone else was the
    whole incident; inside a mkdtemp directory the only possible author is this
    process, and the directory does not outlive the run.
    """
    return SCRATCH / name

spec = importlib.util.spec_from_file_location("planner", PLANNER)
pl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pl)

BRIEF = "a scene about the moment before something important begins"

fails: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        fails.append(name)


# A KIT genre carries TWO style fields, and WHICH one a plan uses is stated by
# the queue ENTRY, never by the template's block order (card t_3497b627). The
# planner REFUSES to guess - that refusal is the point - so a test that plans
# commentary-beds must name a field exactly as the queue entry does. The sweeps
# below use the sting; section 7 exercises both names and the refusals.
KIT_STYLE_FIELD = {"commentary-beds": "INTRO STING"}


def ctx_g(genre: str, **kw):
    return pl.context_for(genre, KIT_STYLE_FIELD.get(genre), **kw)


def style_args(genre: str) -> list[str]:
    f = KIT_STYLE_FIELD.get(genre)
    return ["--style-field", f] if f else []


def genres() -> list[str]:
    reg = pl.load_registry()
    return sorted(reg["genres"])


# ---------------------------------------------------------------------------
print("1. every genre plans, and gets a tempo from its own research")

# REGRESSION (2026-10-09). The draft path resolved bpm as
# `blueprint.bpm_anchor or 100`. The 7 of 14 genres with no blueprint fell back
# to a flat 100 BPM while their own template captions stated the real tempo:
# jungle-dnb came out 100 against a stated 168, anime-opening 100 against 160.
# A generic tempo is not a neutral default - it is a wrong answer that
# validation then could not catch, because validation read the same anchor and
# found nothing to disagree with.
for g in genres():
    out = scratch(f"plan-{g}.json")
    r = subprocess.run(
        [sys.executable, str(PLANNER), "plan", "--brief", BRIEF,
         "--genre", g, "--lyrics-mode", "draft", *style_args(g),
         "--out", str(out)],
        capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        check(f"{g}: plans", False, tail[-1] if tail else "no output")
        continue
    plan = json.loads(out.read_text())
    ctx = ctx_g(g)
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
ctx = ctx_g("anime-opening")
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
cl = ctx_g("chill-lounge")
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
    out = scratch(f"inst-{g}.json")
    r = subprocess.run(
        [sys.executable, str(PLANNER), "plan", "--brief", BRIEF,
         "--genre", g, "--lyrics-mode", "instrumental", *style_args(g),
         "--out", str(out)],
        capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        check(f"{g}: instrumental plans", False, tail[-1] if tail else "no output")
        continue
    plan = json.loads(out.read_text())
    ctxg = ctx_g(g)
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
         "--lyrics-mode", "instrumental", "--out", str(scratch(f"instvocal-{g}.json"))],
        capture_output=True, text=True)
    check(f"{g}: instrumental mode refused (rc={r.returncode})", r.returncode == 2,
          (r.stdout + r.stderr)[:140])

# The refusal must NOT be relaxed: a draft plan still carries no `instrumental`
# flag, which is what keeps acestep_plan.py refusing it.
out = scratch("draftflag.json")
subprocess.run([sys.executable, str(PLANNER), "plan", "--brief", BRIEF,
                "--genre", "sentimental-piano", "--lyrics-mode", "draft",
                "--out", str(out)], capture_output=True, text=True)
draft = json.loads(out.read_text())
check("a draft plan is not marked instrumental", draft.get("instrumental") is False)

# An instrumental plan is STRUCTURE, never words: that is what makes it
# acceptable to the renderer without relaxing the draft refusal.
esc = json.loads(scratch("inst-sentimental-piano.json").read_text())
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
    out = scratch(f"key-{g}.json")
    r = subprocess.run(
        [sys.executable, str(PLANNER), "plan", "--brief", BRIEF,
         "--genre", g, "--lyrics-mode", "draft", *style_args(g),
         "--out", str(out)],
        capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        check(f"{g}: draft plans", False, tail[-1] if tail else "no output")
        continue
    plan = json.loads(out.read_text())
    stated = pl.key_in_caption(ctx_g(g)["template"]["caption"] or "")
    check(f"{g}: key {plan['key']!r} is the key its caption states ({stated!r})",
          plan.get("key") == stated, f"planned {plan['key']!r}, caption {stated!r}")

# The census is measured here, not assumed. 3 of 14 captions state a key, and
# naming them is what makes a template that GAINS or LOSES a key visible.
stated_genres = sorted(
    g for g in genres()
    if pl.key_in_caption(ctx_g(g)["template"]["caption"] or ""))
check(f"3 of {len(genres())} genre captions state a key",
      len(stated_genres) == 3, str(stated_genres))
check("the three are elemental-water, epic-orchestral-boss, trance",
      stated_genres == ["elemental-water", "epic-orchestral-boss", "trance"],
      str(stated_genres))

# The exact case the incident was found on (card t_791b48f7), and the case that
# proves no default replaced the fabrication.
trance = json.loads(scratch("key-trance.json").read_text())
check("trance states 'A minor', not the old 'C minor'",
      trance["key"] == "A minor", repr(trance["key"]))
cl = json.loads(scratch("key-chill-lounge.json").read_text())
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
                  if ctx_g(g)["blueprint"].get("key_anchor")
                  or ctx_g(g)["blueprint"].get("key"))
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
      pl.key_in_caption(ctx_g("elemental-water")["template"]["caption"]) == "C minor",
      repr(pl.key_in_caption(ctx_g("elemental-water")["template"]["caption"])))
check("epic-orchestral-boss's caption reads 'C minor' from '150 BPM in C minor'",
      pl.key_in_caption(ctx_g("epic-orchestral-boss")["template"]["caption"])
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
if scratch("inst-chill-lounge.json").is_file():
    env = dict(os.environ, SUNOLOCAL_HOST="http://127.0.0.1:9")
    rr = subprocess.run(
        [sys.executable, str(REPO / "music" / "scripts" / "acestep_plan.py"),
         str(scratch("inst-chill-lounge.json")), "--name", "tf-key-cl"],
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
print("6. the duration rail admits the registry's shortest shape (t_96dfc521)")

# REGRESSION (2026-10-16, card t_96dfc521). MIN_DURATION_S was 30 - a round
# number with no artifact behind it - while the registry's own commentary-beds
# kit is SHORTER than that rail: the intro sting is 8 bars at 120 BPM = 16.0 s
# (`music/briefs/commentary-beds.md` §2 product table and §4 bar math), and its
# live queue entry carries `duration: 16` in BOTH queue lists
# (`helm/charts/music-pipeline/values.yaml` + `helm/apps/music-pipeline.yaml`,
# mining-k8s fb03105). Measured consequence: the planner WROTE the sting plan and
# then exited 1 with `duration 16s outside 30-600s`, so every scheduled run
# bought one red pod and one `VALIDATION FAILED` line, while the render rail -
# which does not run this check - rendered the plan anyway. The engine has no
# such floor: that artifact measures 16.000000 s (engine job
# c27fc133641540259517cb235af10207, `duration: 16`).
#
# The floor is now the SHORTEST shape the registry actually names, the same way
# MAX_DURATION_S became 600 for elemental-earth's documented 600 s `loop-10min`
# shape (card t_909069f0). "The shortest shape the registry names" is a measured
# census, not a guess: over the live queue's ten entries the shortest is the
# 16 s sting, and over `music/briefs/**` the shortest PLANNER product named is
# the same 16.0 s sting - the sub-16 s shapes the briefs name (elemental-earth's
# 4-bar 10.909 s pack loops) are built by `music/assets/pack.py` from a render,
# never planned, so they are not this rail's business.
#
# The check is run on a SINGLE-style-field instrumental genre (chill-lounge,
# ceiling: elemental-earth) on purpose. commentary-beds carries TWO style fields
# and WHICH one a plan uses is card t_3497b627's decision, so a CLI case on that
# genre would go red for a reason this card does not own. The sting entry's own
# genre is still covered, at the rail: case (d) below calls validate() with
# commentary-beds' own context.
STING_BRIEF = ("the audio sting for an interview podcast's brand kit: one 4-6 note "
               "bell-pluck motif stated twice over warm electric-piano chords, 8 bars, "
               "ends on a clean decisive hit then one beat of silence")


def plan_instrumental(genre, duration, tag):
    # No stale-file step is needed: the scratch is fresh and private, so this
    # name cannot already exist (and an unlink of a foreign file in a sticky
    # directory was the crash this card fixed).
    out = scratch(f"rail-{tag}.json")
    r = subprocess.run(
        [sys.executable, str(PLANNER), "plan", "--brief", STING_BRIEF,
         "--genre", genre, "--lyrics-mode", "instrumental",
         "--duration", str(duration), "--out", str(out)],
        capture_output=True, text=True)
    return r, (json.loads(out.read_text()) if out.is_file() else None)


# (a) the 16.0 s shape plans, exit 0, and prints no refusal.
r16, p16 = plan_instrumental("chill-lounge", 16, "16")
tail16 = (r16.stdout + r16.stderr).strip().splitlines()
check(f"a 16 s plan is accepted (rc={r16.returncode})", r16.returncode == 0,
      tail16[-1] if tail16 else "no output")
check("the 16 s plan keeps duration 16 and stays instrumental",
      bool(p16) and p16.get("duration") == 16 and p16.get("instrumental") is True,
      json.dumps(p16)[:160] if p16 else "no plan written")
check("the planner prints no VALIDATION FAILED for 16 s",
      "VALIDATION FAILED" not in (r16.stdout + r16.stderr),
      (r16.stdout + r16.stderr).strip()[-160:])

# (b) the ceiling regression from t_909069f0 still passes: elemental-earth's
# documented `loop-10min` shape is 220 whole bars at its own 88 BPM = 600.0 s.
r600, p600 = plan_instrumental("elemental-earth", 600, "600")
tail600 = (r600.stdout + r600.stderr).strip().splitlines()
check(f"the 600 s loop-10min shape still plans (rc={r600.returncode})",
      r600.returncode == 0, tail600[-1] if tail600 else "no output")
check("the 600 s plan keeps duration 600",
      bool(p600) and p600.get("duration") == 600,
      json.dumps(p600)[:120] if p600 else "no plan written")

# (c) a duration BELOW the shortest named shape is still refused, so the rail is
# a guard and not a no-op. 15 s is the commentary-beds template's own off-grid
# cutdown - 7.5 bars at its 2.00 s bar - which §4 of its brief rejects in favour
# of 16 s ("Do not silently ship a 15 s file and call the kit bar-aligned").
r15, p15 = plan_instrumental("chill-lounge", 15, "15")
check(f"15 s (the off-grid 7.5-bar cutdown) is still refused (rc={r15.returncode})",
      r15.returncode == 1 and "VALIDATION FAILED" in (r15.stdout + r15.stderr),
      (r15.stdout + r15.stderr).strip()[-200:])
# ...and NOT written. The plan file IS the render rail's queue and the render
# stage does not run this check, so a refused plan that is still written is a
# plan the render stage renders anyway. That is precisely what happened to the
# 16 s sting before this card: plan on disk, pod red, artifact 16.000 s.
check("a refused duration writes NO plan for the render rail to pick up",
      p15 is None and "REFUSED: no plan written" in (r15.stdout + r15.stderr),
      f"plan={'written' if p15 else 'absent'} "
      f"{(r15.stdout + r15.stderr).strip()[-160:]}")

# (d) the sting entry's OWN genre, at the rail. A 16 s plan for commentary-beds
# must carry no duration problem - the exact plan the queue writes today
# (`duration: 16`, `bpm: 120`, `keyscale: C minor`, instrumental).
ctx_cb = ctx_g("commentary-beds")
sting_plan = {
    "title": "Commentary Kit - Intro Sting (warm lo-fi jazz)",
    "caption": ctx_cb["template"]["caption"], "bpm": 120, "key": "C minor",
    "duration": 16, "timesignature": "4", "language": "en",
    "lyrics": pl.instrumental_lyrics(ctx_cb), "instrumental": True,
}
sting_problems = pl.validate(sting_plan, ctx_cb, STING_BRIEF, "en", instrumental=True)
check("validate() reports no duration problem for the sting entry's 16 s plan",
      not [p for p in sting_problems if "duration" in p], str(sting_problems))
check("the rail is the shortest shape the registry names (MIN_DURATION_S == 16)",
      pl.MIN_DURATION_S == 16, f"MIN_DURATION_S={pl.MIN_DURATION_S}, MAX={pl.MAX_DURATION_S}")

# ---------------------------------------------------------------------------
print()
print("7. a kit genre's caption is the style field the ENTRY names (t_3497b627)")

# REGRESSION (2026-10-16, card t_3497b627, found while queueing the kit on card
# t_640cc2a1). The template reader took the first fenced block after the first
# "## Style field" heading:
#     m = re.search(r"##\s*Style field.*?```(?:text)?\n(.*?)```", raw, re.S | re.I)
# music/prompts/commentary-beds.md carries TWO style fields - `## Style field —
# INTRO STING` (line 8) and `## Style field — LOOPABLE TALK BED` (line 14) - and
# says why in its own prose: "Two separate generations — never one". So BOTH kit
# plans carried the sting's caption, and the 32 s artifact on disk was the sting
# rather than the anti-melody bed the kit sells. Measured in the engine record
# for the bed job 0e3fb7b2728747ce816c3e6a760c3c69 ("Commentary Kit — Talk Bed",
# duration 32): its `prompt` was the sting's text, byte for byte, and the two kit
# plans' `caption` fields were identical.
#
# The decision: the ENTRY states which field is the caption (`styleField:` in the
# queue, `--style-field` to the planner). Nothing is inferred, an unknown name is
# a hard failure, and there is NO fallback to the first block.
KIT = "commentary-beds"
kit_tmpl = pl.load_template(KIT)
kit_fields = kit_tmpl["style_fields"]
check("commentary-beds declares two style fields",
      [f["name"] for f in kit_fields] == ["INTRO STING", "LOOPABLE TALK BED"],
      str([f["name"] for f in kit_fields]))
check("the template's own `caption` does NOT pick one of them",
      kit_tmpl["caption"] == "", repr(kit_tmpl["caption"]))
check("the two fields are different texts",
      kit_fields[0]["caption"] != kit_fields[1]["caption"])

BED_BRIEF = ("the loopable talk bed for an interview podcast: same warm lo-fi jazz "
             "palette, muted chords and soft bass on the loop's chord roots, rimshot "
             "ticks on 2 and 4, no melody, no fills, no builds, 16 bars that end on the "
             "chord that leads back to bar 1")


def plan_kit(style_field, tag, duration=None):
    # Same as plan_instrumental: the private scratch makes a stale file
    # impossible, and the unlink that a stale file used to require was the
    # crash site (t_7ab98781).
    out = scratch(f"kit-{tag}.json")
    cmd = [sys.executable, str(PLANNER), "plan", "--brief", BED_BRIEF,
           "--genre", KIT, "--lyrics-mode", "instrumental",
           "--bpm", "120", "--keyscale", "C minor"]
    if style_field is not None:
        cmd += ["--style-field", style_field]
    if duration is not None:
        cmd += ["--duration", str(duration)]
    cmd += ["--out", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r, (json.loads(out.read_text()) if out.is_file() else None), out


# The SECOND field, named exactly as the queue names it. THIS is the assertion
# that fails on the pre-fix reader: it returned block #1 whatever name was given
# (and had no such flag at all, so it also fails on argparse).
rbed, bed, bed_out = plan_kit("LOOPABLE TALK BED", "bed", 32)
check(f"naming 'LOOPABLE TALK BED' plans (rc={rbed.returncode})",
      rbed.returncode == 0 and bed is not None,
      (rbed.stdout + rbed.stderr).strip()[-200:])
check("its caption IS the second style field and is NOT the first",
      bool(bed) and bed["caption"] == kit_fields[1]["caption"]
      and bed["caption"] != kit_fields[0]["caption"],
      repr((bed or {}).get("caption", "")[:70]))
check("the plan records which field its caption came from",
      bool(bed) and bed["_meta"].get("style_field") == "LOOPABLE TALK BED",
      repr((bed or {}).get("_meta", {}).get("style_field")))
check("the bed's caption starts with the bed's own text",
      bool(bed) and bed["caption"].startswith("minimal instrumental podcast talk bed"),
      repr((bed or {}).get("caption", "")[:60]))

# The kit's other half is still reachable, and the two plans now differ.
rst, sting, sting_out = plan_kit("INTRO STING", "sting", 16)
check("naming 'INTRO STING' resolves the first field",
      bool(sting) and sting["caption"] == kit_fields[0]["caption"],
      repr((sting or {}).get("caption", "")[:70]))
check("the two kit plans no longer share a caption",
      bool(sting) and bool(bed) and sting["caption"] != bed["caption"])

# NEGATIVE CONTROLS. Neither is a fallback: each must FAIL LOUDLY - rc != 0,
# nothing written - for an unknown name and for an omission on a two-field genre.
r_bad, bad_plan, bad_out = plan_kit("LOOPABLE BED", "unknown")
check(f"an unknown style field is a hard failure (rc={r_bad.returncode}, "
      f"no plan={not bad_out.is_file()})",
      r_bad.returncode != 0 and not bad_out.is_file()
      and "unknown styleField" in (r_bad.stdout + r_bad.stderr),
      (r_bad.stdout + r_bad.stderr).strip()[:160])
r_omit, omit_plan, omit_out = plan_kit(None, "omit")
check(f"omitting it on a two-field genre is a hard failure (rc={r_omit.returncode}, "
      f"no plan={not omit_out.is_file()})",
      r_omit.returncode != 0 and not omit_out.is_file()
      and "carries 2 style fields" in (r_omit.stdout + r_omit.stderr),
      (r_omit.stdout + r_omit.stderr).strip()[:160])

# The RESOLVER is genre-AGNOSTIC on purpose (the card forbids special-casing
# commentary-beds by name, because any kit genre has this shape): a synthetic
# two-field template resolves by the named section under any genre name, and a
# single-field template is untouched.
two = {"path": str(scratch("two.md")),
       "style_fields": [{"name": "ALPHA", "caption": "alpha caption"},
                        {"name": "BETA", "caption": "beta caption"}]}
check("the resolver picks the SECOND field by name, whatever the genre is called",
      pl.resolve_style_caption(two, "BETA", "any-genre") == ("BETA", "beta caption"),
      repr(pl.resolve_style_caption(two, "BETA", "any-genre")))
chip = pl.load_template("chiptune-8bit")
check("a single-style-field genre still needs no selector",
      pl.resolve_style_caption(chip, None, "chiptune-8bit")[1] == chip["caption"] != "",
      repr(pl.resolve_style_caption(chip, None, "chiptune-8bit")[1][:40]))


def exits_loudly(fn, *a) -> bool:
    try:
        fn(*a)
    except SystemExit:
        return True
    return False


check("naming an unknown field on a single-field genre is a hard failure",
      exits_loudly(pl.resolve_style_caption, chip, "NOPE", "chiptune-8bit"))
check("naming a field on a genre whose template declares none is a hard failure",
      exits_loudly(pl.resolve_style_caption,
                   {"path": str(scratch("none.md")), "style_fields": []},
                   "ALPHA", "no-template-genre"))

# ---------------------------------------------------------------------------
print()
print("8. the suite's scratch is private to the run, and no path is shared (t_7ab98781)")

# REGRESSION (2026-10-16). A foreign file must never be able to collide with
# this suite's scratch, and the suite must never name a path under the SHARED
# temp directory. Both are asserted here rather than assumed: the incident was a
# root-run sibling's leftover at a fixed shared path, and the fix holds only as
# long as neither property is given back.

# (a) The home: per-run, owned by the runner, closed to everyone else.
st = SCRATCH.stat()
check("the scratch is a directory owned by this run's user",
      SCRATCH.is_dir() and st.st_uid == os.getuid(),
      f"uid={st.st_uid} runner={os.getuid()} path={SCRATCH}")
check("the scratch is closed to every other user (mode 0700)",
      stat.S_IMODE(st.st_mode) == 0o700, oct(stat.S_IMODE(st.st_mode)))
check("the scratch is a fresh entry IN the temp dir, not the temp dir itself",
      SCRATCH.parent == pathlib.Path(tempfile.gettempdir()),
      f"{SCRATCH} (temp dir {tempfile.gettempdir()})")
check("the scratch name carries the uid and a per-run suffix",
      re.fullmatch(rf"_tp-suite-{os.getuid()}-\S+", SCRATCH.name) is not None
      and SCRATCH.name != f"_tp-suite-{os.getuid()}-",
      SCRATCH.name)

# (b) The evidence of the files this run actually wrote: they are all in the
# scratch, and not one belongs to another user - the incident itself, inverted.
made = sorted(p.name for p in SCRATCH.glob("*.json"))
check("the plans this run wrote live in the private scratch",
      {"plan-activist.json", "key-trance.json", "inst-chill-lounge.json",
       "rail-16.json", "kit-bed.json"} <= set(made), str(made[:8]))
check("every swept genre planned into it, on all three sweeps",
      len(made) >= 2 * len(genres()) + len(INST), f"{len(made)} files")
foreign = [p.name for p in SCRATCH.iterdir() if p.stat().st_uid != os.getuid()]
check("no file in the scratch belongs to another user", not foreign, str(foreign))


# (c) The CLASS of defect, not just this instance. The pre-fix file was full of
# fixed paths under the shared temp dir; this reads the file's own source and
# fails if one comes back. Comments are not AST string literals, so the incident
# record above cannot trip it - only code can.
SHARED_TEMPS = {"/tmp", "/var/tmp", tempfile.gettempdir()}


def fixed_shared_temp_literals(source: str) -> list[str]:
    """Literals in `source` that name a FIXED path under a shared temp dir.

    Fixed means the path's own directory IS the shared temp dir. A plan written
    to a name in the shared dir is a violation; a file under a per-run mkdtemp
    directory is not, whatever the shared dir is on this host.
    """
    hits: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            parts = [node.value]
        elif isinstance(node, ast.JoinedStr):
            # Only the LEADING literal of an f-string can name a directory.
            parts = [v.value for v in node.values
                     if isinstance(v, ast.Constant) and isinstance(v.value, str)][:1]
        else:
            continue
        for part in parts:
            if part.startswith("/") and \
                    str(pathlib.PurePosixPath(part).parent) in SHARED_TEMPS:
                hits.append(part)
    return sorted(set(hits))


offenders = fixed_shared_temp_literals(
    pathlib.Path(__file__).read_text(encoding="utf-8"))
check("the suite's own source names no fixed path under a shared temp dir",
      not offenders, str(offenders))
# Positive control, taken from the incident: the PRE-FIX line. The reader must
# call it a violation, or it is not testing anything. The expected hit is cut
# OUT of that line rather than written as its own literal - this check reads the
# file it lives in, so a literal `/tmp/_tp-` expectation would flag itself (it
# did, on the first run of this section).
PREFIX_LINE = 'out = pathlib.Path(f"/tmp/_tp-{g}.json")'
EXPECTED_HIT = PREFIX_LINE.split('f"')[1].split("{")[0]
check("...and it flags the pre-fix line that caused the incident",
      fixed_shared_temp_literals(PREFIX_LINE) == [EXPECTED_HIT],
      str(fixed_shared_temp_literals(PREFIX_LINE)))
# Negative control: the form that replaced it must NOT read as a violation, or
# the check would forbid the very fix it exists to protect.
FIXED_LINE = 'out = scratch(f"plan-{g}.json")'
check("...and it does not flag the private-scratch form that replaced it",
      fixed_shared_temp_literals(FIXED_LINE) == [],
      str(fixed_shared_temp_literals(FIXED_LINE)))

# ---------------------------------------------------------------------------
print()
if fails:
    print(f"RESULT: FAIL ({len(fails)})")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("RESULT: PASS")
