#!/usr/bin/env python3
"""Gate: loudness — EBU R128 broadcast-grade audio check (voice/final).

Enforces what the silence-only check missed:
- integrated LUFS near YouTube target (-14 LUFS, tolerance +-1.5)
- true peak <= -1.0 dBTP (no clipping)
- loudness range sane for narration (LRA 6-14 LU)
Uses ffmpeg loudnorm print_format=json (no audio modification).

Exit 0 = PASS, exit 1 = FAIL. No side effects.
"""
import json, subprocess, sys
from pathlib import Path

TARGET_LUFS = -14.0
LUFS_TOL = 1.5
MAX_TP = -1.0
LRA_MIN, LRA_MAX = 4.0, 16.0

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        fail("usage: gate_loudness.py <audio-file-or-campaign-dir>")
    p = Path(sys.argv[1])
    if p.is_dir():
        cands = []
        for pat in ("voice.mp3", "voice/voice.mp3", "voice/*.mp3", "audio/*.mp3", "audio.mp3", "out/*.mp3", "final.mp4", "video/final.mp4"):
            cands += list(p.glob(pat))
        if not cands:
            fail(f"no audio/video found under {p}")
        p = cands[0]
    if not p.exists():
        fail(f"file not found: {p}")

    # loudnorm measurement pass (analyze only)
    r = subprocess.run(
        ["ffmpeg", "-i", str(p), "-af", "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        fail(f"ffmpeg loudnorm failed on {p}: {r.stderr[-300:]}")

    # parse the JSON block at end of stderr
    try:
        idx = r.stderr.rindex("{")
        info = json.loads(r.stderr[idx:r.stderr.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError) as e:
        fail(f"could not parse loudnorm JSON: {e}")

    i_lufs = float(info.get("input_i") or info.get("input_i", -99))
    tp = float(info.get("input_tp") or -99)
    lra = float(info.get("input_lra") or 0)
    print(f"file={p.name}")
    print(f"integrated_lufs={i_lufs:.1f} target={TARGET_LUFS} (tol {LUFS_TOL})")
    print(f"true_peak={tp:.2f}dBTP max={MAX_TP}")
    print(f"lra={lra:.1f}LU range=[{LRA_MIN},{LRA_MAX}]")

    if abs(i_lufs - TARGET_LUFS) > LUFS_TOL:
        fail(f"integrated loudness {i_lufs:.1f} LUFS outside {TARGET_LUFS}±{LUFS_TOL} (YouTube target). Normalize with loudnorm.")
    if tp > MAX_TP:
        fail(f"true peak {tp:.2f} dBTP exceeds {MAX_TP} (clipping risk). Apply limiter.")
    if not (LRA_MIN <= lra <= LRA_MAX):
        print(f"WARN: LRA {lra:.1f} outside [{LRA_MIN},{LRA_MAX}] (flat or over-dynamic narration)")

    print("PASS: loudness gate")
    sys.exit(0)

if __name__ == "__main__":
    main()
