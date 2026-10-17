#!/usr/bin/env python3
"""gate_loop_points — seamless-loop gate for the game-assets lane.

Spec (music-lane-architecture.md §3 `game-assets` requires:
[stems, loop_point, seamless_loop, metadata]; §5 row
`gate_loop_points`: "seamless loop verified").

The gate EXECUTES the artifact. It does not trust
loop_points.json — it renders the loop region with ffmpeg
and measures the SEAM itself.

Two rulers. A loop must pass BOTH.

Ruler 1 — junction curvature (click detection):
  1. Render the tail window [loop_end - W, loop_end]
     and the head window [loop_start, loop_start + W].
  2. Concatenate them: tail + head. This is the signal
     the ear hears at the wrap.
  3. Compute the discrete second difference |x[i+1] - 2x[i]
     + x[i-1]| (curvature) across the whole buffer.
  4. A seamless loop is smooth everywhere: the curvature
     at the junction is the same order as the curvature
     in the body. A broken loop has a derivative kink
     (a click) at the junction: the junction curvature
     spikes far above the body.
  5. Seamlessness = junction_curvature / body_curvature.
     PASS when the ratio <= CLICK_RATIO_MAX (3.0x).

Verified separation on synthetic loops: a clean 5 s-period
loop measures 1.6x; a half-period phase-slip loop measures
6.0x. The 3.0x ceiling sits between them.

Ruler 2 — level continuity (fade detection). Card t_bab8aa19:
curvature measures a derivative kink and says nothing about
LEVEL, so a smooth fade-out passes ruler 1. Measured on the
frozen 25.6 s probe artifacts (16 bars @ 150 BPM, card
t_6f0d261e / music/scripts/loop_seam_check.py --selftest):
a 1.6 s fade-out tail measures 2.21x curvature — UNDER the
3.0x ceiling while its tail-1s sits 8.9 dB below its head-1s
— where a real click measures 5.99x. No single click
threshold separates those two, so the gate needs a second
measurement, not a different number.
  1. Render [loop_start, loop_start + L] (head) and
     [loop_end - L, loop_end] (tail), L = level window
     (default 1.0 s).
  2. Measure each with `ffmpeg -af volumedetect` mean_volume
     — the ruler `music/rubrics/gamer.json` `loop_safety`
     names: "last-1s RMS within ~6 dB of first-1s RMS, no
     fade-to-silence on a loop claim".
  3. PASS when |tail_db - head_db| <= LEVEL_DELTA_MAX_DB
     (6.0 dB). The measured head level, tail level and delta
     are printed on PASS and on FAIL. A loop must pass ruler 1
     AND ruler 2; each ruler has one hole and they are
     different holes. This one is blind to a click: a
     half-period phase slip measures 0.0 dB (the level never
     changes), which is why the curvature ruler stays.
  4. What ruler 2 does NOT see (measured 2026-10-16, card
     t_8297d2c6): the window is 1.0 s and the ceiling is the
     rubric's own ~6 dB, so a fade SHORTER than ~1.15 s stays
     inside it. On the same 25.6 s tone a 1.0 s
     fade-to-silence measures a 4.7 dB delta and PASSES, a
     1.2 s fade measures 6.3 dB and fails, a 1.6 s fade 8.8 dB.
     Do not close that by lowering the ceiling: the rubric
     names the 6 dB tolerance, and the delta is a property of
     the fade length (a linear fade of length d >= L measures
     (L/d)/sqrt(3)). Ruler 3 below closes it with a second
     PROPERTY, not a moved number.

Ruler 3 — the ends must not ramp into silence (card t_8297d2c6,
successor of t_bab8aa19). Ruler 2 compares the level BETWEEN the
two ends. Ruler 3 measures the ENVELOPE INSIDE the end window,
which is a different measurement and sees a different thing:
  1. Take the rubric's own window L (the level window, 1.0 s) at
     the end of the loop and split it in half: render
     [loop_end - L, loop_end - L/2] and [loop_end - L/2,
     loop_end] — two 0.5 s halves.
  2. FAIL when the second half is more than
     --level-delta-max below the first: the loop END is ramping
     toward silence. A linear fade of any length >= L reads
     exactly 20*log10(3) = 9.5 dB between those halves (measured
     8.5 dB on the probe tone), while a level ending or a gentle
     musical decrescendo reads ~0 dB.
  3. PRECONDITION — a window that is itself silence is not
     evidence of level continuity: two silent ends match each
     other. The floor is the lane's own -50 dB (the
     `ffmpeg silencedetect=noise=-50dB` floor this pipeline
     already uses, and `music/scripts/loop_close.py`
     SILENCE_FLOOR_DB). FAIL when the first or the last L of the
     loop is at or below it, naming both levels. Measured on the
     elemental-air 334 s render: head-1s -59.5 dB, tail-1s
     -58.7 dB, delta 0.8 dB — ruler 2 PASSED it; ruler 3 refuses
     it.

No new numbers. The window is the rubric's 1 s, the tolerance is
the rubric's own ~6 dB (--level-delta-max — one dial, both
rulers), the floor is the lane's -50 dB. Measured separation
(2026-10-16, 25 real loops: 3 closed by `music/scripts/loop_close.py`
from real ACE masters and 22 written by `music/assets/pack.py`
from real masters): the largest half-to-half ramp on real
material is 5.3 dB, and every fade fixture from 0.6 s up reads
6.2 dB or more (0.6 s -> 6.2, 1.0 s -> 8.5, 1.6 s -> 8.5).
Boundary, measured: a 0.5 s fade still passes (4.7 dB), the
0.6 s fade is the first refusal (6.2 dB). A fade of 0.5 s or
less stays inside the measured real-material range (max 5.3 dB),
so it cannot be closed without a tolerance the rubric does not
name. Ruler 3 also does not guard the HEAD against a ramp
(a fade-in): on real generator output a head half-to-half ramp
of 9.4 dB occurs on a loop the rubric accepts, so a symmetric
head guard would be a false fail; only a silent head is refused.

Also verifies the loop points are inside the file
(0 <= loop_start < loop_end <= duration), the loop span
is musical (>= MIN_LOOP_SPAN_S), and the loop region is not
silent.

Two modes:

  single (default) — one loop in one file:
    --master <wav> --loop-points loop_points.json
    loop_points.json: {"loop_start_s": 0.0, "loop_end_s": 60.0,
                       "seamless": true}

  pack — every loop of an asset pack, in one run
  (card t_5ed495eb: "PASS on every loop in that pack"):
    --pack-dir <pack>
    <pack>/loop_points.json: {"loops": {"loops/loop_01.wav":
        {"loop_start_s": 0.0, "loop_end_s": 5.2, "seamless": true}, ...}}
    Each entry's master is resolved inside <pack>; every loop is run
    through the SAME measurement code as the single mode. The pack
    fails if any loop fails.

Usage:
  python3 music/gates/gate_loop_points.py --master <wav> \
      --loop-points loop_points.json [--window 3.0] \
      [--click-ratio-max 3.0] [--level-window 1.0] \
      [--level-delta-max 6.0] [--silence-floor -50.0]
  python3 music/gates/gate_loop_points.py --pack-dir <pack>

Exit codes: 0 = PASS, 1 = FAIL (reasons on stderr),
2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_WINDOW = 3.0
DEFAULT_CLICK_RATIO_MAX = 3.0
# Ruler 2 (card t_bab8aa19). The 1.0 s window and the ~6 dB ceiling are the
# rubric's own numbers — music/rubrics/gamer.json `loop_safety`: "last-1s RMS
# within ~6 dB of first-1s RMS, no fade-to-silence on a loop claim".
DEFAULT_LEVEL_WINDOW_S = 1.0
DEFAULT_LEVEL_DELTA_MAX_DB = 6.0
# Ruler 3 (card t_8297d2c6). The lane's own silence floor: the
# `ffmpeg silencedetect=noise=-50dB` floor this pipeline already uses, and
# SILENCE_FLOOR_DB in music/scripts/loop_close.py. A window that is itself
# silence is not evidence of level continuity.
DEFAULT_SILENCE_FLOOR_DB = -50.0
# The musical floor for a loop span. ONE definition, imported by
# gate_sync_ready (pack mode) and by music/assets/pack.py, so the
# generator and the gates cannot drift apart (card t_5ed495eb).
MIN_LOOP_SPAN_S = 2.0
POINTS_TOLERANCE_S = 0.001
VOL_RE = re.compile(r"mean_volume:\s*(-?[\d.]+)\s*dB")


def render_slice(master: Path, start: float, dur: float,
                 out: Path) -> bool:
    """Render [start, start+dur] of master to a mono WAV."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-ss", f"{max(start, 0.0):.6f}", "-t", f"{dur:.6f}",
         "-i", str(master),
         "-ac", "1", "-ar", "8000", str(out)],
        capture_output=True, text=True, timeout=300,
    )
    return proc.returncode == 0 and out.is_file()


def read_pcm(wav: Path) -> list[float]:
    """Decode a WAV to a list of float samples (via ffmpeg)."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(wav),
         "-f", "f32le", "-acodec", "pcm_f32le", "-"],
        capture_output=True, timeout=300,
    )
    if proc.returncode != 0 or len(proc.stdout) < 8:
        return []
    return list(struct.unpack(
        f"<{len(proc.stdout) // 4}f", proc.stdout))


def curvature(samples: list[float]) -> list[float]:
    """Discrete second difference |x[i+1]-2x[i]+x[i-1]|."""
    return [abs(samples[i + 1] - 2 * samples[i]
                + samples[i - 1])
            for i in range(1, len(samples) - 1)]


def mean_volume_db(path: Path) -> float | None:
    """ffmpeg volumedetect mean_volume of a rendered file, in dB."""
    proc = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "volumedetect",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=300,
    )
    m = VOL_RE.search(proc.stderr or "")
    if not m:
        return None
    return float(m.group(1))


def rms_from_wav(path: Path) -> float | None:
    """RMS (linear) of a WAV via volumedetect mean_volume."""
    mean_db = mean_volume_db(path)
    if mean_db is None:
        return None
    if mean_db <= -100.0:
        return 0.0
    return 10.0 ** (mean_db / 20.0)


def probe_duration(master: Path) -> float | None:
    proc = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries", "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", str(master)],
        capture_output=True, text=True, timeout=120,
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def fail(msgs: list[str]) -> int:
    print("FAIL gate_loop_points", file=sys.stderr)
    for m in msgs:
        print(f"  - {m}", file=sys.stderr)
    return 1


def check_loop(master: Path, loop_start: float, loop_end: float,
               seamless: bool, window: float, ratio_max: float,
               scratch: Path,
               level_window: float = DEFAULT_LEVEL_WINDOW_S,
               level_delta_max_db: float = DEFAULT_LEVEL_DELTA_MAX_DB,
               silence_floor_db: float = DEFAULT_SILENCE_FLOOR_DB,
               ) -> tuple[list[str], dict]:
    """Verify ONE loop by measurement. Returns (problems, info).

    info carries what the measurement found: duration, span, the
    junction/body curvature ratio, the head/tail level delta, the
    end-ramp (the level of the tail window's first half minus its
    second half), the end-window levels against the silence floor, and
    the region RMS. info["ratio"] is None when the seam could not be
    measured; info["level_delta_db"] is None when the level ruler could
    not run; info["ramp_db"] is None when the end ramp could not be
    measured.
    """
    problems: list[str] = []
    info: dict = {"master": str(master), "duration": None, "span": None,
                  "ratio": None, "region_rms": None, "head_db": None,
                  "tail_db": None, "level_delta_db": None,
                  "level_window_s": None, "level_max_db": level_delta_max_db,
                  "ramp_db": None, "tail_first_db": None,
                  "tail_second_db": None, "end_half_s": None,
                  "silence_floor_db": silence_floor_db}

    duration = probe_duration(master)
    if duration is None:
        return ([f"master {master} is not real audio "
                 "(ffprobe found no duration)"], info)
    info["duration"] = duration

    if not (0.0 <= loop_start < loop_end
            <= duration + POINTS_TOLERANCE_S):
        problems.append(f"loop points [{loop_start}s, "
                        f"{loop_end}s] are not within the "
                        f"master duration {duration:.3f}s "
                        "(or start >= end)")
    span = loop_end - loop_start
    info["span"] = span
    if span < MIN_LOOP_SPAN_S:
        problems.append(f"loop span is {span:.2f}s — too "
                        f"short to be musical (minimum "
                        f"{MIN_LOOP_SPAN_S:.0f}s)")
    if not seamless:
        problems.append("loop_points.json does not declare "
                        "'seamless': true")
    if problems:
        return problems, info

    # --- measure the seam (junction curvature) --------------
    scratch.mkdir(parents=True, exist_ok=True)

    tail_wav = scratch / "tail.wav"
    head_wav = scratch / "head.wav"

    # tail: [loop_end - W, loop_end]; head: [loop_start,
    # loop_start + W]
    tail_start = loop_end - window
    head_start = loop_start

    if not render_slice(master, tail_start, window, tail_wav):
        return ([f"ffmpeg could not render the tail "
                 f"window [{tail_start:.2f}s, "
                 f"{loop_end:.2f}s]"], info)
    if not render_slice(master, head_start, window, head_wav):
        return ([f"ffmpeg could not render the head "
                 f"window [{head_start:.2f}s, "
                 f"{head_start + window:.2f}s]"], info)

    tail_pcm = read_pcm(tail_wav)
    head_pcm = read_pcm(head_wav)
    if len(tail_pcm) < 10 or len(head_pcm) < 10:
        return (["could not decode the rendered "
                 "windows to PCM"], info)

    # The wrap: the ear hears tail immediately followed by head.
    joined = tail_pcm + head_pcm
    curv = curvature(joined)
    junction = len(tail_pcm) - 1   # index of the seam

    seam_lo = max(0, junction - 5)
    seam_hi = min(len(curv), junction + 6)
    seam_curv = (max(curv[seam_lo:seam_hi])
                 if curv[seam_lo:seam_hi] else 0.0)

    body_parts = (curv[:max(0, junction - 50)]
                  + curv[min(len(curv), junction + 50):])
    body_curv = max(body_parts) if body_parts else 0.0
    if body_curv <= 1e-9:
        body_curv = 1e-9

    ratio = seam_curv / body_curv
    info["ratio"] = ratio

    # --- the loop region must not be silent -----------------
    region_wav = scratch / "region.wav"
    if not render_slice(master, loop_start, span, region_wav):
        return (["ffmpeg could not render the loop "
                 "region"], info)
    region_rms = rms_from_wav(region_wav)
    if region_rms is None:
        return (["could not measure loop-region level"], info)
    info["region_rms"] = region_rms
    if region_rms <= 1e-4:
        problems.append("the loop region is silent — a "
                        "silent loop is not a usable game "
                        "asset")

    if ratio > ratio_max:
        problems.append(
            f"seam curvature ratio {ratio:.2f}x exceeds max "
            f"{ratio_max}x — a click (discontinuity) at the wrap "
            "point; the loop is NOT seamless")

    # --- ruler 2: level continuity across the wrap (card t_bab8aa19) ---
    # Curvature measures a kink and nothing about LEVEL. A linear fade-out is
    # perfectly smooth, so ruler 1 passes it (measured 2.21x on the frozen
    # 25.6 s probe artifact) while the wrap drops 8.9 dB. Compare the rubric's
    # own windows: the last L seconds against the first L seconds.
    lw = min(level_window, span / 2.0)
    info["level_window_s"] = lw
    level_head = scratch / "level_head.wav"
    level_tail = scratch / "level_tail.wav"
    if lw <= 0.0:
        problems.append("the loop span is too short to measure a level "
                        "window at each end of the loop")
    elif not render_slice(master, loop_start, lw, level_head):
        problems.append(f"ffmpeg could not render the head level "
                        f"window [{loop_start:.2f}s, "
                        f"{loop_start + lw:.2f}s]")
    elif not render_slice(master, loop_end - lw, lw, level_tail):
        problems.append(f"ffmpeg could not render the tail level "
                        f"window [{loop_end - lw:.2f}s, "
                        f"{loop_end:.2f}s]")
    else:
        head_db = mean_volume_db(level_head)
        tail_db = mean_volume_db(level_tail)
        if head_db is None or tail_db is None:
            problems.append("could not measure the loop's head/tail level "
                            "with ffmpeg volumedetect")
        else:
            info["head_db"] = head_db
            info["tail_db"] = tail_db
            delta = abs(tail_db - head_db)
            info["level_delta_db"] = delta
            if delta > level_delta_max_db:
                direction = "drops" if tail_db < head_db else "rises"
                problems.append(
                    f"loop level {direction} {delta:.1f} dB across the "
                    f"wrap: tail-{lw:.1f}s {tail_db:.1f} dB vs "
                    f"head-{lw:.1f}s {head_db:.1f} dB (max "
                    f"{level_delta_max_db:.1f} dB) — a fade or level ramp "
                    "at the loop end; the loop is NOT seamless")

    # --- ruler 3: the ends must not ramp into silence (card t_8297d2c6) ---
    # Ruler 2 compares the level BETWEEN the ends and its 1.0 s / 6 dB budget
    # hides a fade shorter than ~1.15 s (a 1.0 s fade reads 4.7 dB). Ruler 3
    # measures the ENVELOPE INSIDE the end window: the rubric's own window,
    # split in half. And a window that is itself silence is not evidence of
    # level continuity — two silent ends match each other.
    half = lw / 2.0
    info["end_half_s"] = half
    tail_first = scratch / "end_tail_first.wav"
    tail_second = scratch / "end_tail_second.wav"
    if half <= 0.0:
        problems.append("the loop span is too short to measure an end "
                        "window in halves")
    elif not render_slice(master, loop_end - lw, half, tail_first):
        problems.append(f"ffmpeg could not render the end window's first "
                        f"half [{loop_end - lw:.2f}s, "
                        f"{loop_end - half:.2f}s]")
    elif not render_slice(master, loop_end - half, half, tail_second):
        problems.append(f"ffmpeg could not render the end window's second "
                        f"half [{loop_end - half:.2f}s, "
                        f"{loop_end:.2f}s]")
    else:
        first_db = mean_volume_db(tail_first)
        second_db = mean_volume_db(tail_second)
        if first_db is None or second_db is None:
            problems.append("could not measure the loop end's halves with "
                            "ffmpeg volumedetect")
        else:
            info["tail_first_db"] = first_db
            info["tail_second_db"] = second_db
            ramp = first_db - second_db
            info["ramp_db"] = ramp
            if ramp > level_delta_max_db:
                problems.append(
                    f"the loop end ramps {ramp:.1f} dB toward silence "
                    f"inside its last {lw:.1f}s: first half {first_db:.1f} dB "
                    f"vs second half {second_db:.1f} dB (max "
                    f"{level_delta_max_db:.1f} dB) — a fade-out shorter "
                    "than the level window, which the level ruler cannot "
                    "see; the loop is NOT seamless")

    head_level = info["head_db"]
    tail_level = info["tail_db"]
    if head_level is not None and tail_level is not None:
        silent = [n for n, v in (("first", head_level), ("last", tail_level))
                  if v <= silence_floor_db]
        if silent:
            problems.append(
                f"the {' and '.join(silent)} {lw:.1f}s of the loop is "
                f"silence (head-{lw:.1f}s {head_level:.1f} dB, "
                f"tail-{lw:.1f}s {tail_level:.1f} dB, floor "
                f"{silence_floor_db:.1f} dB) — a window that is itself "
                "silence is not evidence of level continuity; two silent "
                "ends match each other and a loop cannot start or end in "
                "silence")
    return problems, info


def pack_index_loops(pack: Path) -> tuple[dict, list[str]]:
    """Read <pack>/loop_points.json. Returns (loops_map, problems)."""
    lp_path = pack / "loop_points.json"
    if not lp_path.is_file():
        return {}, [f"no {lp_path} — a game-assets pack carries its "
                    "per-loop loop points (see music/assets/pack.py)"]
    try:
        index = json.loads(lp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{lp_path} is corrupt JSON: {exc}"]
    if not isinstance(index, dict):
        return {}, [f"{lp_path} must hold a JSON object"]
    loops = index.get("loops")
    if not isinstance(loops, dict) or not loops:
        return {}, [f"{lp_path} must hold a 'loops' object mapping each "
                    "loop file to its own {loop_start_s, loop_end_s, "
                    "seamless} (a single pair cannot describe a "
                    "multi-loop pack)"]
    return loops, []


def run_pack(pack: Path, window: float, ratio_max: float,
             scratch_root: Path,
             level_window: float = DEFAULT_LEVEL_WINDOW_S,
             level_delta_max_db: float = DEFAULT_LEVEL_DELTA_MAX_DB,
             silence_floor_db: float = DEFAULT_SILENCE_FLOOR_DB) -> int:
    """Verify every loop in one asset pack with the single-loop method."""
    loops, problems = pack_index_loops(pack)
    if problems:
        return fail(problems)

    rows: list[tuple[str, dict]] = []
    for key in sorted(loops):
        entry = loops[key]
        rel = Path(key)
        if rel.is_absolute() or ".." in rel.parts:
            problems.append(f"{key} is not a path inside the pack")
            continue
        master = pack / rel
        if not master.is_file():
            problems.append(f"{key} is listed in loop_points.json but "
                            "the file is not in the pack")
            continue
        if not isinstance(entry, dict):
            problems.append(f"{key}: entry must be an object")
            continue
        start = entry.get("loop_start_s")
        end = entry.get("loop_end_s")
        if not isinstance(start, (int, float)) or \
                not isinstance(end, (int, float)):
            problems.append(f"{key}: loop_start_s and loop_end_s must be "
                            "numeric")
            continue
        sub, info = check_loop(master, float(start), float(end),
                               bool(entry.get("seamless")), window,
                               ratio_max, scratch_root / rel.stem,
                               level_window, level_delta_max_db,
                               silence_floor_db)
        problems += [f"{key}: {p}" for p in sub]
        info["key"] = key
        info["start"] = float(start)
        info["end"] = float(end)
        rows.append((key, info))

    if problems:
        return fail(problems)

    print("PASS gate_loop_points")
    print(f"  pack     : {pack} ({len(rows)} loops)")
    for i, (key, info) in enumerate(rows, 1):
        print(f"  loop {i}/{len(rows)}: {key}")
        print(f"            [{info['start']:.3f}s -> {info['end']:.3f}s] "
              f"span {info['span']:.3f}s  "
              f"seam {info['ratio']:.2f}x (max {ratio_max}x)  "
              f"level {info['level_delta_db']:.1f} dB "
              f"(tail {info['tail_db']:.1f} vs head {info['head_db']:.1f} dB, "
              f"max {level_delta_max_db:.1f})  "
              f"end ramp {info['ramp_db']:.1f} dB "
              f"({info['tail_first_db']:.1f} -> {info['tail_second_db']:.1f} dB, "
              f"max {level_delta_max_db:.1f})  "
              f"RMS {info['region_rms']:.5f}")
    print(f"  verdict  : all {len(rows)} loops seamless "
          f"(curvature <= {ratio_max}x, tail/head level delta "
          f"<= {level_delta_max_db:.1f} dB, end ramp "
          f"<= {level_delta_max_db:.1f} dB, neither end at/below "
          f"{silence_floor_db:.1f} dB)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_loop_points — seamless-loop "
                    "verification gate")
    parser.add_argument("--master", default=None,
                        help="the audio file the loop lives in "
                             "(single mode)")
    parser.add_argument("--loop-points", default=None,
                        help="loop_points.json with "
                             "loop_start_s / loop_end_s (single mode)")
    parser.add_argument("--pack-dir", default=None,
                        help="asset pack with loop_points.json carrying "
                             "a 'loops' map (pack mode: verify every "
                             "loop)")
    parser.add_argument("--window", type=float,
                        default=DEFAULT_WINDOW,
                        help="comparison window in seconds "
                             "(default 3.0)")
    parser.add_argument("--click-ratio-max", type=float,
                        default=DEFAULT_CLICK_RATIO_MAX,
                        help=f"max junction/body curvature "
                             f"ratio "
                             f"(default {DEFAULT_CLICK_RATIO_MAX})")
    parser.add_argument("--level-window", type=float,
                        default=DEFAULT_LEVEL_WINDOW_S,
                        help=f"level ruler: seconds rendered at each end of "
                             f"the loop "
                             f"(default {DEFAULT_LEVEL_WINDOW_S}; clamped "
                             f"to half the loop span)")
    parser.add_argument("--level-delta-max", type=float,
                        default=DEFAULT_LEVEL_DELTA_MAX_DB,
                        help=f"level ruler: max |tail - head| level delta in "
                             f"dB "
                             f"(default {DEFAULT_LEVEL_DELTA_MAX_DB}, the "
                             f"rubric's ~6 dB). ONE dial for both the "
                             f"between-ends delta and the end ramp")
    parser.add_argument("--silence-floor", type=float,
                        default=DEFAULT_SILENCE_FLOOR_DB,
                        help=f"end guard: a first/last level window at or "
                             f"below this is silence, not evidence "
                             f"(default {DEFAULT_SILENCE_FLOOR_DB} dB, the "
                             f"lane's silencedetect floor)")
    parser.add_argument("--scratch", default=None,
                        help="scratch dir for rendered slices")
    args = parser.parse_args(argv)

    scratch = Path(args.scratch) if args.scratch else \
        Path(tempfile.mkdtemp(prefix="loopgate-"))
    scratch.mkdir(parents=True, exist_ok=True)

    if args.pack_dir:
        if args.master or args.loop_points:
            parser.error("--pack-dir takes no --master/--loop-points")
        pack = Path(args.pack_dir)
        if not pack.is_dir():
            return fail([f"no such pack directory: {pack}"])
        return run_pack(pack, args.window, args.click_ratio_max, scratch,
                        args.level_window, args.level_delta_max,
                        args.silence_floor)

    if not args.master or not args.loop_points:
        parser.error("provide --master and --loop-points, or --pack-dir")

    master = Path(args.master)
    lp_path = Path(args.loop_points)
    if not master.is_file():
        return fail([f"no master file: {master}"])
    if not lp_path.is_file():
        return fail([f"no loop points file: {lp_path}"])

    try:
        lp = json.loads(lp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail([f"{lp_path} is corrupt JSON: {exc}"])

    if not isinstance(lp, dict):
        return fail([f"{lp_path} must hold a JSON object"])

    loop_start = lp.get("loop_start_s")
    loop_end = lp.get("loop_end_s")
    if not isinstance(loop_start, (int, float)) or \
            not isinstance(loop_end, (int, float)):
        if isinstance(lp.get("loops"), dict):
            return fail([f"{lp_path} is a pack index (it carries "
                         "'loops'); run it with --pack-dir <the pack> "
                         "instead"])
        return fail([f"{lp_path} must carry numeric "
                     "loop_start_s and loop_end_s"])

    problems, info = check_loop(master, float(loop_start),
                                float(loop_end), bool(lp.get("seamless")),
                                args.window, args.click_ratio_max, scratch,
                                args.level_window, args.level_delta_max,
                                args.silence_floor)
    if problems:
        print("FAIL gate_loop_points", file=sys.stderr)
        if info["duration"] is not None:
            print(f"  master   : {master} ({info['duration']:.3f}s)",
                  file=sys.stderr)
            print(f"  loop     : [{loop_start:.3f}s -> "
                  f"{loop_end:.3f}s]", file=sys.stderr)
        if info["ratio"] is not None:
            print(f"  seam     : curvature ratio {info['ratio']:.2f}x "
                  f"(max {args.click_ratio_max}x)", file=sys.stderr)
        if info["level_delta_db"] is not None:
            print(f"  level    : tail-{info['level_window_s']:.1f}s "
                  f"{info['tail_db']:.1f} dB vs head-"
                  f"{info['level_window_s']:.1f}s {info['head_db']:.1f} dB "
                  f"(delta {info['level_delta_db']:.1f} dB, max "
                  f"{args.level_delta_max:.1f})", file=sys.stderr)
        if info["ramp_db"] is not None:
            print(f"  end      : first half "
                  f"{info['tail_first_db']:.1f} dB vs second half "
                  f"{info['tail_second_db']:.1f} dB over the last "
                  f"{info['level_window_s']:.1f}s "
                  f"(ramp {info['ramp_db']:.1f} dB, max "
                  f"{args.level_delta_max:.1f}; silence floor "
                  f"{args.silence_floor:.1f} dB)", file=sys.stderr)
        for m in problems:
            print(f"  - {m}", file=sys.stderr)
        if info["ratio"] is not None and info["ratio"] > args.click_ratio_max:
            print("  fix: render the loop with a crossfade at the "
                  "seam, or pick loop points on a zero crossing, "
                  "then re-run the gate", file=sys.stderr)
        if (info["level_delta_db"] is not None
                and info["level_delta_db"] > args.level_delta_max) or \
                (info["ramp_db"] is not None
                 and info["ramp_db"] > args.level_delta_max):
            print("  fix: remove the fade-out / level ramp at the loop "
                  "end — a loop must end at the level it starts at, or "
                  "the wrap is audible; re-render and re-run the gate",
                  file=sys.stderr)
        return 1

    print("PASS gate_loop_points")
    print(f"  master   : {master} ({info['duration']:.3f}s)")
    print(f"  loop     : [{loop_start:.3f}s -> "
          f"{loop_end:.3f}s] (span {info['span']:.3f}s)")
    print(f"  seam     : curvature ratio {info['ratio']:.2f}x "
          f"(max {args.click_ratio_max}x) — seamless")
    print(f"  level    : tail-{info['level_window_s']:.1f}s "
          f"{info['tail_db']:.1f} dB vs head-"
          f"{info['level_window_s']:.1f}s {info['head_db']:.1f} dB "
          f"(delta {info['level_delta_db']:.1f} dB, max "
          f"{args.level_delta_max:.1f}) — no fade")
    print(f"  end      : first half {info['tail_first_db']:.1f} dB vs "
          f"second half {info['tail_second_db']:.1f} dB over the last "
          f"{info['level_window_s']:.1f}s "
          f"(ramp {info['ramp_db']:.1f} dB, max {args.level_delta_max:.1f}; "
          f"silence floor {args.silence_floor:.1f} dB) — no end ramp, "
          "neither end silent")
    print(f"  region   : RMS {info['region_rms']:.5f} "
          "(not silent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
