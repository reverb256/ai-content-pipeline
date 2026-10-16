#!/usr/bin/env python3
"""Regression test for the G4 ruler in campaigns/audio-pipeline-v2/GATES.md.

Standing rule (FAILURE -> TEST). Card t_0e1c409a (music lane) found G4
asserting on `ffmpeg volumedetect` mean_volume while carrying the comment
"loudnorm maps dBFS roughly 1:1 to LUFS for a steady tone". That claim is
false, and mean_volume is not a LUFS value: it is a plain RMS mean with no
K-weighting and no gating.

Measured on this host (ffmpeg 9.0.1, 2026-10-16) on G4's own fixture
(440 Hz sine -> `-af loudnorm=I=-16:TP=-1.5:LRA=11`):

    ebur128  integrated loudness  I    = -16.0 LUFS
    volumedetect                 mean = -15.3 dB

0.7 dB apart, with the RMS number reading LOUDER than the loudness number.
G4 now measures EBU R128 integrated loudness (`-af ebur128=peak=true`), the
unit loudnorm's own I= target uses.

These checks pin the ruler in BOTH directions, so a silent reversion to
volumedetect cannot pass:

  1. G4's entry names ebur128, mentions neither volumedetect nor mean_volume,
     and no longer claims a dBFS-to-LUFS 1:1 mapping.
  2. G4's own documented CHECK command runs and prints LOUDNORM_OK (exit 0) --
     the doc's command is exercised, not paraphrased.
  3. The rulers really do disagree: on G4's fixture integrated LUFS sits on the
     -16 target while mean_volume does not reproduce it (>= 0.5 dB apart).
  4. The G4 window is not a re-labelling of the old RMS window: a fixture
     normalized to -12 LUFS has mean_volume inside the OLD window (-22, -10)
     but integrated loudness OUTSIDE the new one (-17, -15), so the two rulers
     hand down different verdicts.

Usage:
    python3 scripts/gates/test_gate_g4_ruler_regression.py [--keep]
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
GATES = REPO / "campaigns" / "audio-pipeline-v2" / "GATES.md"
# G4's declared window, kept in sync with the CHECK command in GATES.md
G4_LO, G4_HI = -17.0, -15.0
# the window G4 used before the ruler was corrected
OLD_LO, OLD_HI = -22.0, -10.0


def g4_block() -> str:
    """Return G4's full entry (it spans several physical lines)."""
    lines = GATES.read_text().splitlines()
    out: list[str] = []
    started = False
    for ln in lines:
        if ln.startswith("G4:"):
            started = True
        if started:
            out.append(ln)
            if "|  EXPECT:" in ln and len(out) > 1:
                break
    return "\n".join(out)


def g4_command(block: str) -> str:
    """Extract the shell command after `CHECK: ` from G4's entry."""
    cmd = block.split("CHECK: ", 1)[1].rsplit("|  EXPECT:", 1)[0]
    return cmd.strip()


def measure(path: Path) -> dict:
    """Independent ffmpeg measurement: integrated LUFS + volumedetect mean."""
    r = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Integrated loudness:"):]
    m = re.search(r"I:\s+([-\d.]+) LUFS", tail)
    if not m:
        raise RuntimeError(f"no ebur128 integrated reading: {r.stderr[-300:]}")
    lufs = float(m.group(1))
    r2 = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True)
    m2 = re.search(r"mean_volume:\s*([-\d.]+) dB", r2.stderr)
    if not m2:
        raise RuntimeError(f"no volumedetect mean_volume: {r2.stderr[-300:]}")
    return {"lufs": lufs, "mean": float(m2.group(1))}


def synth(name: str, filters: str, work: Path) -> Path:
    out = work / name
    r = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-f", "lavfi",
         "-i", "sine=frequency=440:duration=2", "-af", filters, str(out)],
        capture_output=True, text=True)
    assert r.returncode == 0, f"fixture synth failed: {r.stderr[-300:]}"
    return out


def main() -> int:
    keep = "--keep" in sys.argv
    failures = 0

    def check(ok: bool, desc: str, detail: str = "") -> None:
        nonlocal failures
        print(f"{'ok ' if ok else 'BAD'}  {desc:<58} {detail}")
        if not ok:
            failures += 1

    # --- 1. the documented ruler -------------------------------------------
    # The entry's comment may NAME volumedetect (it explains why it is the
    # wrong ruler); the executable code must not USE it.
    block = g4_block()
    check(bool(block), "GATES.md has a G4 entry")
    check("ebur128" in block, "G4 names the ebur128 ruler")
    check(not re.search(r"dBFS\s+roughly\s+1:1", block),
          "G4 drops the false 1:1 dBFS->LUFS claim")

    cmd = g4_command(block)
    code = "\n".join(l for l in cmd.splitlines() if not l.strip().startswith("#"))
    check("ebur128=peak=true" in code, "G4 measures with ebur128 integrated LUFS")
    check("volumedetect" not in code, "G4's code never runs volumedetect")
    check("mean_volume" not in code, "G4's code asserts no mean_volume (RMS) value")
    check("LUFS" in code, "G4 asserts on a LUFS quantity")

    # --- 2. G4's own command runs ------------------------------------------
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
    check(r.returncode == 0 and "LOUDNORM_OK" in r.stdout,
          "G4's documented CHECK command passes",
          f"rc={r.returncode} out={r.stdout.strip()[-40:]!r} err={r.stderr.strip()[-80:]!r}")

    # --- 3./4. the rulers, and their disagreement --------------------------
    with tempfile.TemporaryDirectory(prefix="g4-ruler-test-") as td:
        work = Path(td)
        target = synth("target16.wav", "loudnorm=I=-16:TP=-1.5:LRA=11", work)
        quiet_but_off = synth("off12.wav", "loudnorm=I=-12:TP=-1.5:LRA=11", work)
        a = measure(target)
        b = measure(quiet_but_off)

        check(abs(a["lufs"] - (-16.0)) <= 0.5,
              "G4 fixture hits the -16 LUFS target",
              f"I={a['lufs']:.1f} LUFS")
        check(G4_LO < a["lufs"] < G4_HI,
              "G4 fixture passes the new window",
              f"{G4_LO} < {a['lufs']:.1f} < {G4_HI}")
        check(abs(a["lufs"] - a["mean"]) >= 0.5,
              "the two rulers disagree on G4's fixture",
              f"I={a['lufs']:.1f} LUFS vs mean={a['mean']:.1f} dB "
              f"(diff {abs(a['lufs'] - a['mean']):.1f} dB)")

        check(OLD_LO < b["mean"] < OLD_HI,
              "a -12 LUFS tone would PASS the old RMS window",
              f"mean={b['mean']:.1f} dB in ({OLD_LO}, {OLD_HI})")
        check(not (G4_LO < b["lufs"] < G4_HI),
              "the same tone FAILS the new LUFS window",
              f"I={b['lufs']:.1f} LUFS outside ({G4_LO}, {G4_HI})")

        if keep:
            print(f"\nfixtures kept in {work}")

    print()
    if failures:
        print(f"FAIL: {failures} case(s) failed")
        return 1
    print("PASS: gate G4 ruler regression")
    return 0


if __name__ == "__main__":
    sys.exit(main())
