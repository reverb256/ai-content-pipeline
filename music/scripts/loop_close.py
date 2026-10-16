#!/usr/bin/env python3
"""loop_close — make the DELIVERED loop out of a render, and refuse one that is not a loop.

WHY THIS EXISTS (card t_b21aeb51, board music, measured 2026-10-16)
-----------------------------------------------------------------
Every ACE render ends in 1.5-6.2 s of digital silence and the render rail
(`helm/charts/music-pipeline/templates/cronjob-render.yaml`) wrote its success
`.rendered` marker on `rc=0` alone. So the rail certified a master that is
provably not loopable:

  elemental-fire "Emberfall", 120.000 s, sha256 ddc73523dca73bd756197cd83c75f5aa206bc97462a4707b10f4118455c9c67c
    head-1s mean_volume  -25.1 dB     tail-1s mean_volume  -58.7 dB   delta 33.6 dB
    silencedetect noise=-50dB:d=0.5 -> silence 115.224 -> 119.984 (4.76 s of a 120 s file)

That figure is the RAW render, byte-identical to what ComfyUI returned (the
engine stored the same bytes; nothing in the wrapper pads). The generator stops
writing music inside the requested window and its own tail is silence, so
`duration: 120` does not yield a 120 s loop.

MEASURED, so the fix is not a guess
-----------------------------------
The same render, run through this repo's own loop builder
(`music/assets/pack.py`: `choose_loop_bars()` bar-aligns, `crossfade_into_preroll()`
crossfades the tail into the material just before the loop start), yields loops
that PASS the committed three-ruler `gate_loop_points` on the SAME audio:

  loops/loop_01..05 (6.400 s each, 4 bars at 150 BPM)
    seam 0.00-0.06x (max 3.0x)   level delta 0.0-1.6 dB (max 6.0)   rc=0
  and `music/scripts/loop_seam_check.py` on loop_05: curvature 0.00x, level 0.0 dB, rc=0

So the loop artifact is the BUILT loop, never the raw render. This tool is that
step, at the render rail, right after the render: it builds the loop artifact
from the render, verifies it with the rubric's own ruler, and refuses the plan
when no bar-aligned loop of the render can carry the seamless claim.

TECHNIQUE — REUSED, NOT REINVENTED
----------------------------------
The bar alignment and the seam crossfade are `music/assets/pack.py`'s
`choose_loop_bars()` and `crossfade_into_preroll()` / `edge_fade()`, ported
here because the render rail's image (`docker.io/library/python:3.13-slim`)
carries neither numpy nor scipy, which is what pack.py imports. The port is
bound to the original by `music/tests/test_loop_close.py`, which imports BOTH
and asserts, for the same inputs:

  * identical constants (BARS_PREFERRED, CROSSFADE_S, MIN_LOOP_SPAN_S),
  * an identical bar count and loop length from `choose_loop_bars()`,
  * sample-identical output from `crossfade_into_preroll()` and `edge_fade()`
    (bitwise equal float32).

A second, differently-behaving loop builder is worse than the defect (card
t_b21aeb51). If `music/assets/pack.py` changes, that parity test fails.

THE RULER IS THE RUBRIC'S OWN
-----------------------------
`music/rubrics/gamer.json` `loop_safety`: "last-1s RMS within ~6 dB of
first-1s RMS, no fade-to-silence on a loop claim". Both windows are measured
with `ffmpeg -af volumedetect` (`mean_volume`, plain RMS in dB) — the same
ruler `music/gates/gate_loop_points.py` (ruler 2) and
`music/scripts/loop_seam_check.py` use. No threshold here is new: the ceiling
is 6.0 dB, the window is 1.0 s.

MODES
-----
  --check-only
      Measure ONE artifact and nothing else. FAIL (exit 1) when
      |mean_volume(last 1 s) - mean_volume(first 1 s)| > --level-delta-max, or
      when either window is at or below the silence floor while the other is
      not. This is the check the rail runs on the artifact it is about to
      certify. On the pre-fix rail output (the raw render above, or the frozen
      fixture music/tests/fixtures/loop_silence_tail.wav) it FAILs.

  --claims-loop
      Exit 0 when the plan is a loop claim, 1 when it is not, 2 on usage error.
      The claim is the genre's own `video_shape` in `music/genres.yaml`
      (`loop-10min`), read out of the plan's `_meta.genre`. Reading it from the
      registry, not from the brief's prose, keeps one definition of "a loop
      claim" — a gate that greps is not a gate.

  default (close)
      Build the loop artifact from the render:
        1. bar-align at the plan's bpm (`choose_loop_bars`, ported);
        2. walk bar-aligned windows from the end of the musical region
           backwards (the tail is where a song resolves, so the latest full
           window is the first candidate);
        3. seam each candidate with the pack method (tail crossfaded into the
           pre-roll material) and measure the artifact with ffmpeg volumedetect;
        4. write the first candidate that PASSES --level-delta-max with neither
           end silent, as --out, plus its --loop-points-out
           (`{"loop_start_s": 0.0, "loop_end_s": <duration>, "seamless": true}`
           — the loop file IS the master, so the span is 0 -> its duration);
        5. exit 1 with the measured reasons when no candidate passes, so the
           rail writes no success marker.

Usage:
  python3 music/scripts/loop_close.py --check-only --master M.wav \
      [--loop-points LP.json] [--level-window 1.0] [--level-delta-max 6.0] [--json]
  python3 music/scripts/loop_close.py --master M.wav --plan plan.json \
      --out loop.wav [--loop-points-out loop_points.json] [--json]
  python3 music/scripts/loop_close.py --claims-loop --plan plan.json

Exit codes: 0 = PASS / closed / is a loop claim, 1 = FAIL / refused / not a
loop claim, 2 = usage error.
"""

from __future__ import annotations

import argparse
import array
import json
import math
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

# ── the source of the ported behaviour, named so it cannot be lost ──────────
# music/assets/pack.py (loop builder) and music/gates/gate_loop_points.py
# (MIN_LOOP_SPAN_S). Every constant below is asserted equal to those modules by
# music/tests/test_loop_close.py::TestParityWithPack.
BARS_PREFERRED = 4            # pack.py BARS_PREFERRED: 4 bars of 4/4
CROSSFADE_S = 0.020           # pack.py CROSSFADE_S: seam crossfade into the pre-roll
MIN_LOOP_SPAN_S = 2.0         # gate_loop_points MIN_LOOP_SPAN_S (pack.py imports it)
EDGE_FADE_S = 0.010           # pack.py edge_fade default
DEFAULT_LEVEL_WINDOW_S = 1.0  # gate_loop_points DEFAULT_LEVEL_WINDOW_S
DEFAULT_LEVEL_DELTA_MAX_DB = 6.0   # rubrics/gamer.json loop_safety ("~6 dB")
# The floor `ffmpeg silencedetect=noise=-50dB` and the curvature test already
# use in this pipeline. A window that is itself silence is not evidence of
# level continuity: two silent ends match each other (measured on the
# elemental-air 334 s render, card t_8297d2c6), so a silent end is a refusal.
SILENCE_FLOOR_DB = -50.0
GENRES_FILE_NAME = "genres.yaml"
VOL_RE = re.compile(r"mean_volume:\s*(-?[\d.]+)\s*dB")
SILENCE_START_RE = re.compile(r"silence_start:\s*(-?[\d.]+)")


def find_ffmpeg() -> Path:
    """Locate ffmpeg. Prefer the lane's pinned build, then $PATH.

    Same resolution order as music/scripts/loop_seam_check.py (FFMPEG_BIN_DIR,
    then ~/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin, then $PATH): one
    convention for "where is the lane's ffmpeg".
    """
    cands = []
    env = os.environ.get("FFMPEG_BIN_DIR")
    if env:
        cands.append(Path(env))
    cands.append(Path.home() / ".hermes" / "tools" /
                 "ffmpeg-9.0.1-linux-x64" / "bin")
    for c in cands:
        if (c / "ffmpeg").is_file():
            return c
    found = shutil.which("ffmpeg")
    return Path(found).parent if found else Path("/usr/bin")


FF_BIN = find_ffmpeg()


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600)


# ── measurement: the rubric's own ruler (ffmpeg volumedetect) ───────────────

def mean_volume_db(master: Path, start: float = 0.0,
                   dur: float | None = None) -> float | None:
    """ffmpeg volumedetect mean_volume (dB) of [start, start+dur) of master."""
    cmd = [str(FF_BIN / "ffmpeg"), "-v", "info", "-ss", f"{max(start, 0.0):.4f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.4f}"]
    cmd += ["-i", str(master), "-af", "volumedetect", "-f", "null", "-"]
    proc = run(cmd)
    m = VOL_RE.search(proc.stderr or "")
    return float(m.group(1)) if m else None


def probe_duration(master: Path) -> float | None:
    proc = run([str(FF_BIN / "ffprobe"), "-v", "error", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                str(master)])
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def trailing_silence_start(master: Path) -> float | None:
    """Where the file's TRAILING silence begins, or None when it has none.

    `silencedetect noise=-50dB:d=0.5` — the same probe the card's evidence used.
    Only the LAST detected silence counts: the question is where music stops.
    """
    proc = run([str(FF_BIN / "ffmpeg"), "-v", "info", "-i", str(master),
                "-af", "silencedetect=noise=-50dB:d=0.5", "-f", "null", "-"])
    starts = [float(m.group(1))
              for m in SILENCE_START_RE.finditer(proc.stderr or "")]
    return starts[-1] if starts else None


# ── the ported loop builder (parity-tested against music/assets/pack.py) ────

def choose_loop_bars(sr: int, bpm: float, n: int) -> tuple[int, int]:
    """pack.py::choose_loop_bars — bar-aligned (bars, loop length in samples)."""
    bar_s = 60.0 / bpm * 4          # one 4/4 bar
    if bar_s <= 0 or n <= 0 or sr <= 0:
        return 0, 0
    floor_bars = max(1, math.ceil(MIN_LOOP_SPAN_S / bar_s))
    bars = max(BARS_PREFERRED, floor_bars)
    while bars > floor_bars and bars * bar_s * sr > n:
        bars -= 1
    loop_len = int(round(bars * bar_s * sr))
    if loop_len > n:
        return 0, 0
    return bars, loop_len


def edge_fade(seg: array.array, sr: int,
              fade_s: float = EDGE_FADE_S) -> array.array:
    """pack.py::edge_fade — fade both ends of a segment (the fallback seam).

    pack.py applies numpy.hanning(2 * fade_n) to the two ends, so the window
    used here is the same one: 0.5 - 0.5 * cos(2*pi*k / (2*n - 1)) for
    k = 0 .. 2n-1, the head taking k = 0 .. n-1 and the tail k = n .. 2n-1.
    """
    out = array.array("f", seg)
    fade_n = int(min(fade_s * sr, len(out) // 4))
    if fade_n > 1:
        denom = 2 * fade_n - 1
        for i in range(fade_n):
            head = 0.5 - 0.5 * math.cos(2 * math.pi * i / denom)
            tail = 0.5 - 0.5 * math.cos(2 * math.pi * (fade_n + i) / denom)
            out[i] *= head
            out[len(out) - fade_n + i] *= tail
    return out


def crossfade_into_preroll(seg: array.array, pre: array.array, sr: int,
                           cf_samples: int) -> tuple[array.array, str]:
    """pack.py::crossfade_into_preroll — seam by crossfading the tail into pre.

    The last `cf` samples of the loop become a crossfade between the loop's own
    tail and the source material that immediately precedes the loop start, so
    the wrap plays samples that were adjacent in the source. Falls back to an
    edge fade when the source has no usable pre-roll.
    """
    out = array.array("f", seg)
    cf = int(min(cf_samples, len(out) // 4, len(pre)))
    if cf < 2:
        return edge_fade(seg, sr), "edge-fade-10ms"
    tail = out[len(out) - cf:]
    for i in range(cf):
        w = 0.5 * (1 - math.cos(math.pi * (i + 1) / cf))   # 0 -> 1
        out[len(out) - cf + i] = tail[i] * (1 - w) + pre[len(pre) - cf + i] * w
    return out, f"pre-roll-crossfade-{int(round(cf / sr * 1000))}ms"


# ── audio io (ffmpeg, so a .flac render needs no decoder in python) ─────────

def read_pcm(master: Path, sr_target: int | None = None) -> tuple[array.array, int]:
    """Decode master to mono float32 PCM. Returns (samples, sample rate)."""
    sr = sr_target or probe_sample_rate(master)
    cmd = [str(FF_BIN / "ffmpeg"), "-v", "error", "-i", str(master),
           "-ac", "1", "-ar", str(sr), "-f", "f32le",
           "-acodec", "pcm_f32le", "-"]
    proc = subprocess.run(cmd, capture_output=True, timeout=600)
    if proc.returncode != 0 or len(proc.stdout) < 8:
        return array.array("f"), sr
    pcm = array.array("f")
    pcm.frombytes(proc.stdout[: (len(proc.stdout) // 4) * 4])
    return pcm, sr


def probe_sample_rate(master: Path) -> int:
    proc = run([str(FF_BIN / "ffprobe"), "-v", "error", "-select_streams", "a:0",
                "-show_entries", "stream=sample_rate",
                "-of", "default=noprint_wrappers=1:nokey=1", str(master)])
    try:
        return int(proc.stdout.strip())
    except ValueError:
        return 44100


def write_wav_pcm(path: Path, samples: array.array, sr: int) -> None:
    """Write mono float samples as a 16-bit PCM WAV (no numpy needed)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = array.array("h", bytes(2 * len(samples)))
    for i, s in enumerate(samples):
        frames[i] = int(max(-1.0, min(1.0, s)) * 32767)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(frames.tobytes())


# ── the plan's loop claim, from the genre registry (one definition) ─────────

def genre_video_shapes(genres_yaml: Path) -> dict:
    """Parse {genre: video_shape} out of music/genres.yaml with no PyYAML.

    The render rail's image carries no yaml module. This reader is bound to the
    registry by music/tests/test_loop_close.py, which parses the same file with
    PyYAML and requires the two maps to be identical — so it cannot drift.
    Structure read: a top-level `genres:` block, each genre at 2 spaces, its
    keys at 4 spaces.
    """
    shapes: dict = {}
    in_genres = False
    genre = None
    for raw in genres_yaml.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if indent == 0:
            in_genres = line.startswith("genres:")
            genre = None
            continue
        if not in_genres:
            continue
        if indent == 2 and line.endswith(":"):
            genre = line[:-1].strip()
            continue
        if indent == 4 and genre and line.startswith("video_shape:"):
            shapes[genre] = line.split(":", 1)[1].strip()
    return shapes


def loop_claim_of_plan(plan_path: Path, genres_yaml: Path,
                       loop_shapes: tuple[str, ...] = ("loop-10min",)) -> dict:
    """Is this plan a loop claim? Returns the evidence, not just a bool."""
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"claim": None, "error": f"{plan_path}: {exc}"}
    if not isinstance(plan, dict):
        return {"claim": None, "error": f"{plan_path} is not a JSON object"}
    meta = plan.get("_meta") or {}
    genre = meta.get("genre")
    # An explicit field on the plan wins when a planner stamps one.
    for key in ("loop_claim", "loop"):
        if isinstance(plan.get(key), bool):
            return {"claim": plan[key], "genre": genre,
                    "source": f"plan.{key}"}
        if isinstance(meta.get(key), bool):
            return {"claim": meta[key], "genre": genre,
                    "source": f"plan._meta.{key}"}
    if not genre:
        return {"claim": None,
                "error": f"{plan_path} has no _meta.genre — cannot resolve a "
                         "loop claim"}
    shape = genre_video_shapes(genres_yaml).get(genre)
    return {"claim": shape in loop_shapes, "genre": genre,
            "video_shape": shape, "source": "genres.yaml"}


# ── the check (what the rail runs on the artifact it will certify) ─────────

def check_artifact(master: Path, level_window: float = DEFAULT_LEVEL_WINDOW_S,
                   level_delta_max: float = DEFAULT_LEVEL_DELTA_MAX_DB,
                   ) -> tuple[list[str], dict]:
    """The rubric's level ruler on the artifact. Returns (problems, info)."""
    problems: list[str] = []
    info: dict = {"master": str(master), "duration": None, "head_db": None,
                  "tail_db": None, "level_delta_db": None,
                  "level_window_s": level_window,
                  "level_max_db": level_delta_max, "silence_floor_db":
                      SILENCE_FLOOR_DB, "head_silent": None, "tail_silent": None}
    duration = probe_duration(master)
    if duration is None:
        return ([f"{master} is not real audio (ffprobe found no duration)"],
                info)
    info["duration"] = duration
    lw = min(level_window, duration / 2.0)
    if lw <= 0.0:
        return ([f"{master} is too short ({duration:.3f}s) to measure a "
                 f"{level_window:.1f}s window at each end"], info)
    info["level_window_s"] = lw
    head = mean_volume_db(master, 0.0, lw)
    tail = mean_volume_db(master, duration - lw, lw)
    if head is None or tail is None:
        return ([f"ffmpeg volumedetect produced no mean_volume for {master}"],
                info)
    info["head_db"], info["tail_db"] = head, tail
    info["head_silent"] = head <= SILENCE_FLOOR_DB
    info["tail_silent"] = tail <= SILENCE_FLOOR_DB
    if info["head_silent"] or info["tail_silent"]:
        which = [n for n, s in (("first", info["head_silent"]),
                                ("last", info["tail_silent"])) if s]
        problems.append(
            f"the {' and '.join(which)} {lw:.1f}s of {master.name} is silence "
            f"(head {head:.1f} dB, tail {tail:.1f} dB, floor "
            f"{SILENCE_FLOOR_DB:.1f} dB) — a window that is itself silence is "
            "not evidence of level continuity")
    delta = abs(tail - head)
    info["level_delta_db"] = delta
    if delta > level_delta_max:
        direction = "drops" if tail < head else "rises"
        problems.append(
            f"loop level {direction} {delta:.1f} dB across the wrap: "
            f"tail-{lw:.1f}s {tail:.1f} dB vs head-{lw:.1f}s {head:.1f} dB "
            f"(max {level_delta_max:.1f} dB) — a fade or silent tail at the "
            "loop end; the artifact is NOT a loop")
    return problems, info


# ── the closer ─────────────────────────────────────────────────────────────

def close_loop(master: Path, bpm: float, out: Path, loop_points_out: Path,
               level_window: float = DEFAULT_LEVEL_WINDOW_S,
               level_delta_max: float = DEFAULT_LEVEL_DELTA_MAX_DB,
               max_candidates: int = 12) -> tuple[int, dict]:
    """Build a bar-aligned, seam-crossfaded loop from master. (rc, record)."""
    record: dict = {"master": str(master), "out": str(out), "bpm": bpm,
                    "candidates": [], "method": None, "start_s": None,
                    "bars": None, "span_s": None, "level_delta_db": None,
                    "head_db": None, "tail_db": None, "problems": []}
    duration = probe_duration(master)
    if duration is None:
        record["problems"].append(f"{master} is not real audio")
        return 1, record
    record["duration_s"] = duration

    silence_at = trailing_silence_start(master)
    musical_end = silence_at if silence_at is not None else duration
    record["trailing_silence_from_s"] = silence_at
    record["musical_end_s"] = musical_end

    pcm, sr = read_pcm(master)
    if len(pcm) < sr:
        record["problems"].append(f"could not decode {master} to PCM")
        return 1, record

    bars, loop_len = choose_loop_bars(sr, bpm, len(pcm))
    if loop_len <= 0:
        record["problems"].append(
            f"no bar-aligned loop of at least {MIN_LOOP_SPAN_S:.0f}s fits a "
            f"{duration:.2f}s render at {bpm} BPM")
        return 1, record
    bar_samples = loop_len // bars
    record["bars"] = bars
    record["span_s"] = loop_len / sr

    # Windows, latest first: the end of the musical region is where a song
    # resolves back toward its opening, per the briefs this lane writes.
    last_start = int(musical_end * sr) - loop_len
    k_max = last_start // bar_samples if bar_samples else 0
    starts = [k * bar_samples for k in range(k_max, -1, -1)][:max_candidates]
    if not starts:
        record["problems"].append(
            f"the musical region ({musical_end:.3f}s) is shorter than one "
            f"{loop_len / sr:.3f}s loop — nothing to close")
        return 1, record

    cf = int(round(CROSSFADE_S * sr))
    measured: list[tuple[float, int, str, array.array, dict]] = []
    for start in starts:
        seg = array.array("f", pcm[start:start + loop_len])
        pre = array.array("f", pcm[max(0, start - cf):start])
        samples, method = crossfade_into_preroll(seg, pre, sr, cf)
        write_wav_pcm(out, samples, sr)
        problems, info = check_artifact(out, level_window, level_delta_max)
        measured.append((info["level_delta_db"] if info["level_delta_db"]
                         is not None else float("inf"), start, method,
                         samples, {"start_s": round(start / sr, 6),
                                   "method": method,
                                   "head_db": info["head_db"],
                                   "tail_db": info["tail_db"],
                                   "level_delta_db": info["level_delta_db"],
                                   "problems": problems}))
        record["candidates"].append(measured[-1][4])

    # Select by the rubric's own property: the smallest |tail - head| level
    # delta, ties going to the LATER window (the end of a song resolves back
    # toward its opening, which is the shape the briefs in this lane ask for).
    # pack.py::extract_loops selects by measurement too (lowest seam
    # discontinuity); the builder is identical, only the ranked property
    # differs, because the rail's duty is the level ruler.
    ok = [m for m in measured if not m[4]["problems"]]
    if ok:
        best = min(ok, key=lambda m: (round(m[0], 2), -m[1]))
        delta, start, method, samples, info = best
        write_wav_pcm(out, samples, sr)
        record["method"] = method
        record["start_s"] = info["start_s"]
        record["head_db"] = info["head_db"]
        record["tail_db"] = info["tail_db"]
        record["level_delta_db"] = info["level_delta_db"]
        span = len(samples) / sr
        loop_points_out.parent.mkdir(parents=True, exist_ok=True)
        loop_points_out.write_text(json.dumps(
            {"loop_start_s": 0.0, "loop_end_s": round(span, 6),
             "seamless": True,
             "source_master": str(master),
             "source_start_s": record["start_s"],
             "seam_method": method, "bars": bars, "bpm": bpm,
             "level_head_db": info["head_db"],
             "level_tail_db": info["tail_db"],
             "level_delta_db": info["level_delta_db"]},
            indent=2) + "\n", encoding="utf-8")
        record["loop_points"] = str(loop_points_out)
        return 0, record

    out.unlink(missing_ok=True)
    record["problems"].append(
        f"no bar-aligned {loop_len / sr:.3f}s window of the {duration:.3f}s "
        f"render at {bpm} BPM meets |tail-1s - head-1s| <= "
        f"{level_delta_max:.1f} dB with neither end silent "
        f"({len(record['candidates'])} candidates measured)")
    return 1, record


# ── cli ────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="loop_close — build the delivered loop from a render, or "
                    "refuse one that is not a loop")
    p.add_argument("--master")
    p.add_argument("--plan", help="the plan that was rendered (loop claim)")
    p.add_argument("--out", help="where to write the loop artifact")
    p.add_argument("--loop-points-out", help="where to write its loop_points.json")
    p.add_argument("--loop-points", help="existing loop_points.json (--check-only)")
    p.add_argument("--check-only", action="store_true",
                   help="measure --master with the level ruler and nothing else")
    p.add_argument("--claims-loop", action="store_true",
                   help="exit 0 only when --plan is a loop claim")
    p.add_argument("--bpm", type=float, default=None,
                   help="source tempo (else the plan's bpm)")
    p.add_argument("--level-window", type=float, default=DEFAULT_LEVEL_WINDOW_S)
    p.add_argument("--level-delta-max", type=float,
                   default=DEFAULT_LEVEL_DELTA_MAX_DB,
                   help="max |tail - head| in dB (default 6.0, the rubric's)")
    p.add_argument("--max-candidates", type=int, default=12)
    p.add_argument("--genres-yaml", default=None,
                   help="path to music/genres.yaml (default: beside this repo)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    here = Path(__file__).resolve()
    genres = Path(args.genres_yaml) if args.genres_yaml else None
    if genres is None:
        for cand in (here.parents[1] / GENRES_FILE_NAME,
                     Path.cwd() / GENRES_FILE_NAME,
                     Path("/payload/music") / GENRES_FILE_NAME):
            if cand.is_file():
                genres = cand
                break
    if genres is None:
        genres = here.parents[1] / GENRES_FILE_NAME

    if args.claims_loop:
        if not args.plan:
            p.error("--claims-loop needs --plan")
        res = loop_claim_of_plan(Path(args.plan), genres)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(json.dumps(res))
        if res.get("claim") is None:
            return 2
        return 0 if res["claim"] else 1

    if not args.master:
        p.error("--master is required")
    master = Path(args.master)
    if not master.is_file():
        print(f"FAIL loop_close\n  - no master file: {master}", file=sys.stderr)
        return 1

    if args.check_only:
        problems, info = check_artifact(master, args.level_window,
                                        args.level_delta_max)
        if args.json:
            print(json.dumps({"info": info, "problems": problems}, indent=2))
        if problems:
            if not args.json:
                print("FAIL loop_close --check-only", file=sys.stderr)
                print(f"  master   : {master} "
                      f"({info['duration']:.3f}s)", file=sys.stderr)
                if info["level_delta_db"] is not None:
                    print(f"  level    : tail-{info['level_window_s']:.1f}s "
                          f"{info['tail_db']:.1f} dB vs head-"
                          f"{info['level_window_s']:.1f}s "
                          f"{info['head_db']:.1f} dB (delta "
                          f"{info['level_delta_db']:.1f} dB, max "
                          f"{info['level_max_db']:.1f})", file=sys.stderr)
                for m in problems:
                    print(f"  - {m}", file=sys.stderr)
            return 1
        if not args.json:
            print("PASS loop_close --check-only")
            print(f"  master   : {master} ({info['duration']:.3f}s)")
            print(f"  level    : tail-{info['level_window_s']:.1f}s "
                  f"{info['tail_db']:.1f} dB vs head-"
                  f"{info['level_window_s']:.1f}s {info['head_db']:.1f} dB "
                  f"(delta {info['level_delta_db']:.1f} dB, max "
                  f"{info['level_max_db']:.1f}) — no fade, neither end silent")
        return 0

    # close mode
    bpm = args.bpm
    if bpm is None and args.plan:
        try:
            bpm = json.loads(Path(args.plan).read_text(encoding="utf-8")).get("bpm")
        except (OSError, json.JSONDecodeError):
            bpm = None
    if not bpm:
        p.error("close mode needs a tempo: --bpm or a --plan carrying 'bpm'")
    if not args.out:
        p.error("close mode needs --out")
    out = Path(args.out)
    lp_out = Path(args.loop_points_out) if args.loop_points_out else \
        out.with_suffix(".loop_points.json")
    rc, record = close_loop(master, float(bpm), out, lp_out,
                            args.level_window, args.level_delta_max,
                            args.max_candidates)
    if args.json:
        print(json.dumps(record, indent=2))
    if rc == 0:
        if not args.json:
            print("PASS loop_close — delivered loop built from the render")
            print(f"  master   : {master} ({record['duration_s']:.3f}s)")
            print(f"  loop     : {out} ({record['span_s']:.3f}s, "
                  f"{record['bars']} bars at {record['bpm']:g} BPM, "
                  f"from {record['start_s']:.3f}s)")
            print(f"  seam     : {record['method']}")
            print(f"  level    : tail-1.0s {record['tail_db']:.1f} dB vs "
                  f"head-1.0s {record['head_db']:.1f} dB (delta "
                  f"{record['level_delta_db']:.1f} dB, max "
                  f"{args.level_delta_max:.1f})")
            print(f"  measured with ffmpeg volumedetect (music/rubrics/gamer.json "
                  f"loop_safety); the raw render's trailing silence "
                  f"({record['trailing_silence_from_s']} s) is outside the loop")
        return 0
    if not args.json:
        print("FAIL loop_close — the render cannot carry a seamless-loop claim",
              file=sys.stderr)
        print(f"  master   : {master}", file=sys.stderr)
        for m in record["problems"]:
            print(f"  - {m}", file=sys.stderr)
        for c in record["candidates"]:
            print(f"  candidate start {c['start_s']:.3f}s: "
                  f"tail {c['tail_db']} vs head {c['head_db']} dB "
                  f"({c['method']})", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
