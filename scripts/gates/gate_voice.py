#!/usr/bin/env python3
"""Gate: voice stage — enforce narration audio contract.

Blocks advance if:
- narration audio missing (voice.mp3 / audio/*.mp3)
- duration doesn't match word budget: expected = words/160wpm minutes, +/-10%
- audio is silent / near-silent (volumedetect mean below threshold)
Exit 0 = PASS, exit 1 = FAIL (with reasons). No side effects.
"""
import json, os, subprocess, sys
from pathlib import Path

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def ffprobe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)

def volumedetect(path):
    r = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, timeout=60)
    mean = None
    for line in r.stderr.splitlines():
        if "mean_volume" in line:
            try:
                mean = float(line.split(":")[1].strip().replace(" dB", ""))
            except ValueError:
                pass
    return mean

def main():
    if len(sys.argv) < 2:
        fail("usage: gate_voice.py <campaign-dir>")
    camp = Path(sys.argv[1])

    # find narration audio
    candidates = []
    for pat in ("voice.mp3", "voice/voice.mp3", "voice/*.mp3", "audio/*.mp3", "audio.mp3", "out/*.mp3"):
        candidates += list(camp.glob(pat))
    if not candidates:
        fail(f"no narration audio found under {camp} (looked for voice.mp3, audio/*.mp3, out/*.mp3)")
    audio = candidates[0]
    print(f"audio={audio}")

    info = ffprobe(audio)
    if not info:
        fail(f"ffprobe failed on {audio}")
    dur = float(info.get("format", {}).get("duration", 0))
    print(f"duration={dur:.1f}s")

    # word budget from script.md
    script = camp / "script.md"
    words = 0
    if script.exists():
        for line in script.read_text().splitlines():
            s = line.strip()
            if not s or s.startswith('#') or s.startswith('**') or s.startswith('<!--'):
                continue
            if s.startswith('Visual:') or s.startswith('TTS') or s.startswith('Source') or s.startswith('>'):
                continue
            words += len(s.split())
    print(f"script_words={words}")
    if words:
        expected = words / 160 * 60  # seconds at 160wpm
        lo, hi = expected * 0.85, expected * 1.20
        if not (lo <= dur <= hi):
            fail(f"duration {dur:.0f}s outside expected {expected:.0f}s +/- 20% (words={words} @160wpm)")

    # silence check
    mean = volumedetect(audio)
    print(f"mean_volume={mean}dB")
    if mean is not None and mean < -45:
        fail(f"audio near-silent (mean {mean}dB < -45dB)")

    print("PASS: voice gate")
    sys.exit(0)

if __name__ == "__main__":
    main()
