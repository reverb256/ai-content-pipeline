#!/usr/bin/env bash
# G9: instrumental mode end-to-end.
#
# Regression for t_82ed3b8a: 8 of the 14 genre templates are instrumental
# (their prompt templates say "leave the lyrics box empty"), but the
# generation path required a human lyric sheet for every run, so those
# templates could not be generated or validated. This gate exercises the
# fix at both layers:
#   1. translate.suno_to_aceplan carries instrumental=true and an empty
#      lyrics box (the spec/translate layer).
#   2. suno-gen.py's is_instrumental_template() reads the template and
#      load_track() accepts an instrumental track dir without a sheet.
# Prints G9-OK on success, exits nonzero on any failure.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

python3 - <<'PY'
import importlib.util
import json, sys, tempfile
from pathlib import Path

# suno-gen.py has a hyphen in its name and is not importable as a
# Python module. Load it explicitly via importlib so the gate can
# exercise its functions.
_spec = importlib.util.spec_from_file_location(
    "suno_gen", str(Path("music/suno-gen.py").resolve())
)
suno_gen = importlib.util.module_from_spec(_spec)
sys.modules["suno_gen"] = suno_gen
_spec.loader.exec_module(suno_gen)

from music.sunolocal import translate
from music.sunolocal.spec import SunoGenerateRequest

# --- 1. translate layer: instrumental flag survives the mapping -------------
# An instrumental request carries empty lyrics and instrumental=True.
r = SunoGenerateRequest(
    style="downtempo chill lounge, 75 BPM, 4/4, heavy swung hats",
    prompt="late-night room with rain outside, warm jazz chords on felt electric piano",
    lyrics="",
    instrumental=True,
    duration=30,
    style_weight=0.5,
)
plan = translate.suno_to_aceplan(r)
assert plan["instrumental"] is True, plan
# The renderer (acestep_plan.py) refuses an EMPTY lyrics string outright.
# Translate emits the canonical "[Instrumental]\n" header so the loader
# passes; --allow-empty then accepts the empty body. Caption still says
# "instrumental, no vocals" so the engine steers to no vocals.
assert plan["lyrics"] == "[Instrumental]\n", plan
assert "instrumental, no vocals" in plan["caption"], plan["caption"]
assert plan["duration"] == 30.0, plan
assert isinstance(plan["bpm"], int) and 60 <= plan["bpm"] <= 240, plan
assert plan["timesignature"] == "4", plan

# --- 2. translate layer: a vocal request is NOT flagged instrumental -------
v = translate.suno_to_aceplan(SunoGenerateRequest(
    style="uplifting trance", lyrics="[Chorus]\nshine on", instrumental=False))
assert v["instrumental"] is False, v
assert v["lyrics"] == "[Chorus]\nshine on", v
assert "instrumental, no vocals" not in v["caption"], v["caption"]

# --- 3. translate layer: instrumental with non-empty lyrics is honoured ---
# (a template that carries metatags only — the chill-lounge tag sheet)
m = translate.suno_to_aceplan(SunoGenerateRequest(
    style="chill", lyrics="[Instrumental]\n", instrumental=True))
assert m["instrumental"] is True, m
assert m["lyrics"] == "[Instrumental]\n", m

# --- 4. suno-gen.is_instrumental_template() reads the writer's template ----
# 8 instrumental templates, each declaring "leave the lyrics box empty"
instr = ["chill-lounge", "sentimental-piano", "commentary-beds",
         "elemental-fire", "elemental-water", "elemental-earth",
         "elemental-air", "chiptune-8bit"]
for g in instr:
    assert suno_gen.is_instrumental_template(g), f"{g} should be instrumental"
assert len(instr) == 8, f"expected 8 instrumental templates, got {len(instr)}"

# 6 vocal templates must NOT be flagged instrumental
# (epic-orchestral-boss has choir/chant vocals — it is NOT instrumental)
vocal = ["trance", "jungle-dnb", "activist", "anime-opening",
         "anime-ending", "epic-orchestral-boss"]
for g in vocal:
    assert not suno_gen.is_instrumental_template(g), f"{g} must NOT be instrumental"

# --- 5. suno-gen.load_track() accepts an instrumental track dir -----------
# without a lyrics.suno.txt, provided the dir is marked instrumental.
with tempfile.TemporaryDirectory() as td:
    tdir = Path(td) / "chill-lounge" / "amber-hour"
    tdir.mkdir(parents=True)
    (tdir / "title.txt").write_text("Amber Hour")
    (tdir / "manifest.json").write_text(json.dumps({"instrumental": True}))
    track = suno_gen.load_track(tdir, instrumental=True)
    assert track["title"] == "Amber Hour", track
    assert track["lyrics"] == "", track
    assert track["sheet"] == "", track

    # The marker file form also works
    tdir2 = Path(td) / "chiptune-8bit" / "pixel-run"
    tdir2.mkdir(parents=True)
    (tdir2 / "title.txt").write_text("Pixel Run")
    (tdir2 / "instrumental").write_text("x")
    track2 = suno_gen.load_track(tdir2, instrumental=True)
    assert track2["title"] == "Pixel Run", track2

    # A vocal track dir with no sheet still fails — the guard holds
    tdir3 = Path(td) / "trance" / "no-sheet"
    tdir3.mkdir(parents=True)
    (tdir3 / "title.txt").write_text("No Sheet")
    try:
        suno_gen.load_track(tdir3, instrumental=False)
    except SystemExit as e:
        assert "FATAL" in str(e), e
    else:
        raise AssertionError("load_track should have refused a vocal dir with no sheet")

# --- 6. suno-gen cmd_generate: --dry for an instrumental genre ----------------
# Exercises the full registry + template-decision + load_track path
# without touching the browser or spending a credit.
# Uses a tmp dir marked instrumental (amber-hour is a vocal track even
# though the chill-lounge template is instrumental — the wrong fixture).
import subprocess, tempfile, os
with tempfile.TemporaryDirectory() as td:
    tdir = Path(td) / "chill-lounge" / "dry-run-inst"
    tdir.mkdir(parents=True)
    (tdir / "title.txt").write_text("Dry Run Inst")
    (tdir / "manifest.json").write_text(json.dumps({"instrumental": True}))
    r = subprocess.run(
        [sys.executable, "music/suno-gen.py", "--genre", "chill-lounge",
         "--track-dir", str(tdir),
         "--dry"],
        capture_output=True, text=True, timeout=30,
    )
    print("  dry run stdout tail:", (r.stdout.strip().splitlines() or ["(empty)"])[-1])
    assert r.returncode == 0, f"dry run failed: {r.stderr}"
    assert "INSTRUMENTAL" in r.stdout, f"dry run did not report instrumental mode: {r.stdout}"
    assert "lyrics box empty" in r.stdout, f"dry run did not confirm empty lyrics box: {r.stdout}"

print("G9-OK")
PY