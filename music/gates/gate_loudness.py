#!/usr/bin/env python3
"""gate_loudness — PASS/FAIL loudness gate, MEASURED with ffmpeg volumedetect.

Spec (music-lane-architecture.md §5, row `gate_loudness`):
  streaming target: -14 LUFS (volumedetect mean_volume, dB)
  sync target:      -16 LUFS
  tolerance:        +/- 1.0 dB

The gate EXECUTES the artifact: it runs `ffmpeg -i <master> -af
volumedetect -f null -`, parses the measured mean_volume line, and
compares it to the target. A loud master (mean -12 dB) fails honestly;
a quiet or absent master also fails. No file is trusted by name.

NOTE on units: volumedetect's mean_volume is a plain RMS mean in dB,
not a gated LUFS value (that needs ebur128 / BS.1770 metering). The
architecture pins volumedetect as the pipeline's measurement tool, so
this gate measures what the spec says to measure. Treat the numbers as
the pipeline's loudness dialect; a mastering-grade LUFS reading is a
separate tool (see FinalPass / sacrifunk-loudness patterns).

Usage:
  python3 music/gates/gate_loudness.py --master <wav> \
      [--target streaming|sync] [--tolerance 1.0] [--json]

Exit codes: 0 = PASS, 1 = FAIL (reasons on stderr), 2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TARGETS = {"streaming": -14.0, "sync": -16.0}
DEFAULT_TOLERANCE = 1.0
MEAN_RE = re.compile(r"mean_volume:\s*(-?[\d.]+)\s*dB")
MAX_RE = re.compile(r"max_volume:\s*(-?[\d.]+)\s*dB")


def measure(path: Path) -> dict:
    """Run ffmpeg volumedetect on the master; return the measured stats."""
    proc = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "volumedetect",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=600,
    )
    stderr = proc.stderr or ""
    mean = MEAN_RE.search(stderr)
    peak = MAX_RE.search(stderr)
    if not mean:
        return {"ok": False,
                "error": "ffmpeg volumedetect produced no mean_volume line "
                         "(file is not decodable audio, or ffmpeg failed)"}
    return {
        "ok": True,
        "mean_volume_db": float(mean.group(1)),
        "max_volume_db": float(peak.group(1)) if peak else None,
        "ffmpeg_stderr_tail": stderr.strip().splitlines()[-6:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_loudness — measured loudness gate (volumedetect)")
    parser.add_argument("--master", required=True,
                        help="the mastered audio file (wav/flac/mp3...)")
    parser.add_argument("--target", default="streaming",
                        choices=tuple(TARGETS),
                        help="loudness target: streaming (-14) or sync (-16)")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE,
                        help="+/- dB around the target (default 1.0)")
    parser.add_argument("--json", action="store_true",
                        help="emit the measurement as JSON")
    args = parser.parse_args(argv)

    master = Path(args.master)
    if not master.is_file():
        print(f"FAIL gate_loudness: no such file {master}", file=sys.stderr)
        return 2

    result = measure(master)
    if not result.get("ok"):
        print("FAIL gate_loudness", file=sys.stderr)
        print(f"  - {result['error']}", file=sys.stderr)
        if args.json:
            print(json.dumps({"ok": False, "error": result["error"]}))
        return 1

    target = TARGETS[args.target]
    measured = result["mean_volume_db"]
    deviation = measured - target
    passed = abs(deviation) <= args.tolerance

    if args.json:
        print(json.dumps({
            "ok": passed, "gate": "gate_loudness",
            "file": str(master), "target_lufs": target,
            "measured_mean_volume_db": measured,
            "max_volume_db": result["max_volume_db"],
            "deviation_db": round(deviation, 3),
            "tolerance_db": args.tolerance,
        }))
        return 0 if passed else 1

    if passed:
        print("PASS gate_loudness")
        print(f"  master    : {master}")
        print(f"  target    : {target} dB ({args.target} lane)")
        print(f"  measured  : mean_volume {measured:.2f} dB "
              f"(max {result['max_volume_db']:.2f} dB)")
        print(f"  deviation : {deviation:+.2f} dB "
              f"(tolerance +/-{args.tolerance:.1f} dB)")
        return 0

    print("FAIL gate_loudness", file=sys.stderr)
    print(f"  master    : {master}", file=sys.stderr)
    print(f"  target    : {target} dB ({args.target} lane, "
          f"tolerance +/-{args.tolerance:.1f} dB)", file=sys.stderr)
    print(f"  measured  : mean_volume {measured:.2f} dB "
          f"(max {result['max_volume_db']:.2f} dB)", file=sys.stderr)
    direction = "LOUD" if deviation > 0 else "QUIET"
    print(f"  deviation : {deviation:+.2f} dB — master is {direction} "
          f"for the {args.target} target; re-normalize and re-run "
          "the gate", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
