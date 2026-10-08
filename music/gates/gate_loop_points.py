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
is musical (>= 2 s), and the loop region is not silent.

Usage:
  python3 music/gates/gate_loop_points.py --master <wav> \
      --loop-points loop_points.json [--window 3.0] \
      [--click-ratio-max 3.0]

loop_points.json:
  {"loop_start_s": 0.0, "loop_end_s": 60.0, "seamless": true}

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_loop_points — seamless-loop "
                    "verification gate")
    parser.add_argument("--master", required=True)
    parser.add_argument("--loop-points", required=True,
                        help="loop_points.json with "
                             "loop_start_s / loop_end_s")
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

    problems: list[str] = []

    loop_start = lp.get("loop_start_s")
    loop_end = lp.get("loop_end_s")
    if not isinstance(loop_start, (int, float)) or \
            not isinstance(loop_end, (int, float)):
        return fail([f"{lp_path} must carry numeric "
                     "loop_start_s and loop_end_s"])

    # --- 1. loop points inside the file ------------------------
    duration = probe_duration(master)
    if duration is None:
        return fail([f"master {master} is not real audio "
                     "(ffprobe found no duration)"])
    if not (0.0 <= loop_start < loop_end
            <= duration + 0.001):
        problems.append(f"loop points [{loop_start}s, "
                        f"{loop_end}s] are not within the "
                        f"master duration {duration:.3f}s "
                        "(or start >= end)")
    span = loop_end - loop_start
    if span < 2.0:
        problems.append(f"loop span is {span:.2f}s — too "
                        "short to be musical (minimum 2s)")
    if not lp.get("seamless"):
        problems.append("loop_points.json does not declare "
                        "'seamless': true")
    if problems:
        return fail(problems)

    # --- 2. measure the seam (junction curvature) --------------
    scratch = Path(args.scratch) if args.scratch else \
        Path(tempfile.mkdtemp(prefix="loopgate-"))
    scratch.mkdir(parents=True, exist_ok=True)

    tail_wav = scratch / "tail.wav"
    head_wav = scratch / "head.wav"

    # tail: [loop_end - W, loop_end]; head: [loop_start,
    # loop_start + W]
    tail_start = loop_end - args.window
    head_start = loop_start

    if not render_slice(master, tail_start, args.window,
                        tail_wav):
        return fail([f"ffmpeg could not render the tail "
                     f"window [{tail_start:.2f}s, "
                     f"{loop_end:.2f}s]"])
    if not render_slice(master, head_start, args.window,
                        head_wav):
        return fail([f"ffmpeg could not render the head "
                     f"window [{head_start:.2f}s, "
                     f"{head_start + args.window:.2f}s]"])

    tail_pcm = read_pcm(tail_wav)
    head_pcm = read_pcm(head_wav)
    if len(tail_pcm) < 10 or len(head_pcm) < 10:
        return fail(["could not decode the rendered "
                     "windows to PCM"])

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

    # --- 3. the loop region must not be silent -----------------
    region_wav = scratch / "region.wav"
    if not render_slice(master, loop_start, span,
                        region_wav):
        return fail(["ffmpeg could not render the loop "
                     "region"])
    region_rms = rms_from_wav(region_wav)
    if region_rms is None:
        return fail(["could not measure loop-region level"])
    if region_rms <= 1e-4:
        problems.append("the loop region is silent — a "
                        "silent loop is not a usable game "
                        "asset")
    if problems:
        return fail(problems)

    passed = ratio <= args.click_ratio_max

    if passed:
        print("PASS gate_loop_points")
        print(f"  master   : {master} ({duration:.3f}s)")
        print(f"  loop     : [{loop_start:.3f}s -> "
              f"{loop_end:.3f}s] (span {span:.3f}s)")
        print(f"  seam     : curvature ratio {ratio:.2f}x "
              f"(max {args.click_ratio_max}x) — seamless")
        print(f"  region   : RMS {region_rms:.5f} "
              "(not silent)")
        return 0

    print("FAIL gate_loop_points", file=sys.stderr)
    print(f"  master   : {master} ({duration:.3f}s)",
          file=sys.stderr)
    print(f"  loop     : [{loop_start:.3f}s -> "
          f"{loop_end:.3f}s]", file=sys.stderr)
    print(f"  seam     : curvature ratio {ratio:.2f}x "
          f"exceeds max {args.click_ratio_max}x — a click "
          "(discontinuity) at the wrap point; the loop is "
          "NOT seamless", file=sys.stderr)
    print("  fix: render the loop with a crossfade at the "
          "seam, or pick loop points on a zero crossing, "
          "then re-run the gate", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
