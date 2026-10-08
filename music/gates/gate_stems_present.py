#!/usr/bin/env python3
"""gate_stems_present — PASS/FAIL gate for the stems stage.

Spec (music-lane-architecture.md §5, row `gate_stems_present`):
  >= 4 stems, non-zero bytes, durations match the master
  within +/- 0.5 s — measured with ffprobe, never guessed
  from file size.

The gate EXECUTES the artifact:
  - every stem must be a real audio file (ffprobe opens it,
    reports a duration AND an audio stream);
  - every stem must be non-zero bytes;
  - every stem duration must be within +/- STEM_TOLERANCE s of
    the master duration;
  - the master itself must be a real audio file.

Usage:
  python3 music/gates/gate_stems_present.py --master <wav> \
      --stems-dir <dir> [--min-stems 4] [--tolerance 0.5]

Exit codes: 0 = PASS, 1 = FAIL (reasons on stderr), 2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_MIN_STEMS = 4
DEFAULT_TOLERANCE = 0.5


def ffprobe_duration(path: Path) -> float | None:
    """Duration in seconds, or None if the file is not real audio."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration:stream=codec_type",
             "-of", "json", str(path)],
            capture_output=True, text=True, timeout=120,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if out.returncode != 0:
        return None
    try:
        info = json.loads(out.stdout)
    except json.JSONDecodeError:
        return None
    streams = info.get("streams") or []
    if not any(s.get("codec_type") == "audio" for s in streams):
        return None
    try:
        return float(info["format"]["duration"])
    except (KeyError, ValueError, TypeError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_stems_present — stem-count/size/duration gate")
    parser.add_argument("--master", required=True,
                        help="the mastered audio file (duration reference)")
    parser.add_argument("--stems-dir", required=True,
                        help="directory holding the stems")
    parser.add_argument("--min-stems", type=int,
                        default=DEFAULT_MIN_STEMS)
    parser.add_argument("--tolerance", type=float,
                        default=DEFAULT_TOLERANCE,
                        help="+/- s stem duration may differ from master")
    args = parser.parse_args(argv)

    master = Path(args.master)
    stems_dir = Path(args.stems_dir)

    problems: list[str] = []
    if not master.is_file():
        problems.append(f"no master file: {master}")
        master_dur = None
    else:
        master_dur = ffprobe_duration(master)
        if master_dur is None:
            problems.append(f"master {master} is not a real audio file")
        elif master.stat().st_size == 0:
            problems.append("master is zero bytes")

    if not stems_dir.is_dir():
        problems.append(f"no stems directory: {stems_dir}")
        stems: list[Path] = []
    else:
        stems = sorted(p for p in stems_dir.iterdir()
                       if p.is_file() and p.suffix.lower() in
                       (".wav", ".aif", ".aiff", ".flac"))

    if len(stems) < args.min_stems:
        problems.append(f"only {len(stems)} stem(s) in {stems_dir}; "
                        f"{args.min_stems} required")

    durations: dict[str, float] = {}
    for st in stems:
        if st.stat().st_size == 0:
            problems.append(f"stem {st.name} is zero bytes")
            continue
        d = ffprobe_duration(st)
        if d is None:
            problems.append(f"stem {st.name} is not a real audio file "
                            "(ffprobe found no audio stream)")
            continue
        durations[st.name] = d
        if master_dur is not None and abs(d - master_dur) > args.tolerance:
            problems.append(f"stem {st.name} is {d:.3f}s; master is "
                            f"{master_dur:.3f}s — outside "
                            f"+/-{args.tolerance}s (stems must be "
                            "time-aligned to the master)")

    if problems:
        print("FAIL gate_stems_present", file=sys.stderr)
        for m in problems:
            print(f"  - {m}", file=sys.stderr)
        return 1

    # an empty problems list proves master_dur was measured
    assert master_dur is not None
    print("PASS gate_stems_present")
    print(f"  master    : {master} ({master_dur:.3f}s)")
    print(f"  stems     : {len(stems)} in {stems_dir} "
          f"(>= {args.min_stems} required)")
    print(f"  durations : all within +/-{args.tolerance}s of master")
    for name, d in sorted(durations.items()):
        delta = d - master_dur
        print(f"      {name}: {d:.3f}s (delta {delta:+.3f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
