#!/usr/bin/env python3
"""gate_loop_points — seamless-loop gate for the game-assets lane.

Spec (music-lane-architecture.md §3 `game-assets` requires:
[stems, loop_point, seamless_loop, metadata]; §5 row
`gate_loop_points`: "seamless loop verified").

The gate EXECUTES the artifact. It does not trust
loop_points.json — it renders the loop region with ffmpeg
and measures the SEAM itself.

Method — junction curvature (click detection):
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
      [--click-ratio-max 3.0]
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


def rms_from_wav(path: Path) -> float | None:
    """RMS (linear) of a WAV via volumedetect mean_volume."""
    proc = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "volumedetect",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=300,
    )
    m = VOL_RE.search(proc.stderr or "")
    if not m:
        return None
    mean_db = float(m.group(1))
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
               scratch: Path) -> tuple[list[str], dict]:
    """Verify ONE loop by measurement. Returns (problems, info).

    info carries what the measurement found: duration, span, the
    junction/body curvature ratio, and the region RMS. info["ratio"]
    is None when the seam could not be measured.
    """
    problems: list[str] = []
    info: dict = {"master": str(master), "duration": None, "span": None,
                  "ratio": None, "region_rms": None}

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
             scratch_root: Path) -> int:
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
                               ratio_max, scratch_root / rel.stem)
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
              f"seam {info['ratio']:.2f}x (max {ratio_max}x) — seamless  "
              f"RMS {info['region_rms']:.5f}")
    print(f"  verdict  : all {len(rows)} loops seamless "
          f"(junction/body curvature <= {ratio_max}x)")
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
        return run_pack(pack, args.window, args.click_ratio_max, scratch)

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
                                args.window, args.click_ratio_max, scratch)
    if problems:
        print("FAIL gate_loop_points", file=sys.stderr)
        if info["duration"] is not None:
            print(f"  master   : {master} ({info['duration']:.3f}s)",
                  file=sys.stderr)
            print(f"  loop     : [{loop_start:.3f}s -> "
                  f"{loop_end:.3f}s]", file=sys.stderr)
        for m in problems:
            print(f"  - {m}", file=sys.stderr)
        if info["ratio"] is not None and info["ratio"] > args.click_ratio_max:
            print("  fix: render the loop with a crossfade at the "
                  "seam, or pick loop points on a zero crossing, "
                  "then re-run the gate", file=sys.stderr)
        return 1

    print("PASS gate_loop_points")
    print(f"  master   : {master} ({info['duration']:.3f}s)")
    print(f"  loop     : [{loop_start:.3f}s -> "
          f"{loop_end:.3f}s] (span {info['span']:.3f}s)")
    print(f"  seam     : curvature ratio {info['ratio']:.2f}x "
          f"(max {args.click_ratio_max}x) — seamless")
    print(f"  region   : RMS {info['region_rms']:.5f} "
          "(not silent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
