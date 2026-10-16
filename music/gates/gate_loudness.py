#!/usr/bin/env python3
"""gate_loudness — PASS/FAIL loudness gate, MEASURED with ffmpeg ebur128.

Spec (music-lane-architecture.md §5, row `gate_loudness`):
  streaming target: -14 LUFS integrated
  sync target:      -16 LUFS integrated
  tolerance:        +/- 1.0 LUFS

The gate EXECUTES the artifact: it runs `ffmpeg -i <master> -af
ebur128=peak=true -f null -`, parses the integrated loudness line and the
true-peak line from the filter's summary block, and compares the integrated
value to the target. A loud master fails honestly. A quiet master fails
too. A missing or silent master also fails. No file is trusted by name.

Ruler — EBU R128 integrated loudness (ITU-R BS.1770), decided 2026-10-16 on
card t_9546841b. LUFS is the unit the streaming platforms normalize on, and
the unit this pipeline's own `loudnorm=I=-14:TP=-1.0:LRA=11` normalization
already targets. Before that date the gate measured `volumedetect`
mean_volume instead — a plain RMS mean, with no K-weighting and no gating,
so not a LUFS reading at all. The two rulers disagreed by a
content-dependent amount: across the five Virtual Reflections masters the
gap ran 1.2 to 2.6 dB (worst `sincerely`: mean_volume -15.40 dB vs
integrated -12.80 LUFS). The RMS ruler failed three of the five
(-15.5 / -15.7 / -15.4 dB mean_volume) whose integrated loudness was
-13.6 / -13.3 / -12.8 LUFS; and it would PASS a tone whose RMS sits on
-14.1 dB while its integrated loudness is -11.8 LUFS. Both directions are
pinned by fixtures in `music/gates/check_gate_suite.sh` and
`music/tests/test_gate_loudness.py`.
One ruler, one unit. Do not mix them, and do not add a fallback to the
other.

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
RULER = "ebur128 integrated loudness (EBU R128 / ITU-R BS.1770), LUFS"
# ebur128 prints a running `I:` line per frame and repeats it in the final
# summary block, so the LAST match is the file's integrated loudness.
INTEGRATED_RE = re.compile(r"\bI:\s*(-?[\d.]+|-inf)\s*LUFS", re.IGNORECASE)
TRUE_PEAK_RE = re.compile(r"\bPeak:\s*(-?[\d.]+|-inf)\s*dBFS", re.IGNORECASE)


def measure(path: Path) -> dict:
    """Run ffmpeg ebur128 on the master; return the measured loudness."""
    proc = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "ebur128=peak=true",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=900,
    )
    stderr = proc.stderr or ""
    integrated = INTEGRATED_RE.findall(stderr)
    peaks = TRUE_PEAK_RE.findall(stderr)
    if not integrated:
        return {"ok": False,
                "error": "ffmpeg ebur128 produced no integrated loudness "
                         "(I:) line (file is not decodable audio, or ffmpeg "
                         "failed)"}
    raw = integrated[-1]
    if raw.lower() == "-inf":
        return {"ok": False,
                "error": "master is silent: ebur128 integrated loudness is "
                         "-inf LUFS"}
    peak = peaks[-1] if peaks else None
    return {
        "ok": True,
        "integrated_lufs": float(raw),
        "true_peak_dbfs": (None if peak is None or peak.lower() == "-inf"
                           else float(peak)),
        "ffmpeg_stderr_tail": stderr.strip().splitlines()[-6:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_loudness — measured loudness gate (ffmpeg ebur128)")
    parser.add_argument("--master", required=True,
                        help="the mastered audio file (wav/flac/mp3...)")
    parser.add_argument("--target", default="streaming",
                        choices=tuple(TARGETS),
                        help="loudness target: streaming (-14) or sync (-16)")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE,
                        help="+/- LUFS around the target (default 1.0)")
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
    measured = result["integrated_lufs"]
    deviation = measured - target
    passed = abs(deviation) <= args.tolerance
    peak = result["true_peak_dbfs"]
    peak_txt = "n/a" if peak is None else f"{peak:.2f} dBFS"

    if args.json:
        print(json.dumps({
            "ok": passed, "gate": "gate_loudness",
            "file": str(master), "target_lufs": target,
            "ruler": RULER,
            "measured_lufs": measured,
            "true_peak_dbfs": peak,
            "deviation_lufs": round(deviation, 3),
            "tolerance_lufs": args.tolerance,
        }))
        return 0 if passed else 1

    if passed:
        print("PASS gate_loudness")
        print(f"  master    : {master}")
        print(f"  target    : {target} LUFS ({args.target} lane)")
        print(f"  measured  : integrated {measured:.2f} LUFS "
              f"(true peak {peak_txt})")
        print(f"  deviation : {deviation:+.2f} LUFS "
              f"(tolerance +/-{args.tolerance:.1f} LUFS)")
        return 0

    print("FAIL gate_loudness", file=sys.stderr)
    print(f"  master    : {master}", file=sys.stderr)
    print(f"  target    : {target} LUFS ({args.target} lane, "
          f"tolerance +/-{args.tolerance:.1f} LUFS)", file=sys.stderr)
    print(f"  measured  : integrated {measured:.2f} LUFS "
          f"(true peak {peak_txt})", file=sys.stderr)
    direction = "LOUD" if deviation > 0 else "QUIET"
    print(f"  deviation : {deviation:+.2f} LUFS — master is {direction} "
          f"for the {args.target} target; re-normalize with a two-pass "
          "measured loudnorm (pass 1 measured_I/TP/LRA, pass 2 with "
          "the measured_* values and offset) and re-run the gate",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
