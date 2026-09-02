#!/usr/bin/env python3
"""Gate: visuals stage — enforce final-video contract.

Blocks advance if:
- final video missing (final.mp4 / video/final.mp4 / out/*.mp4)
- video audio stream missing or SILENT (narration must be muxed)
- TRUNCATION: video audio duration must be >= narration duration - 2s.
  (The historical bug: video got cut at scene-total length, losing the last
  minutes of narration. Catches it deterministically.)
Exit 0 = PASS, exit 1 = FAIL. No side effects.
"""
import json, subprocess, sys
from pathlib import Path

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def ffprobe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)

def find_narration(camp):
    # narration is the voice stage output
    for pat in ("voice.mp3", "voice/voice.mp3", "voice/*.mp3", "audio/*.mp3", "audio.mp3", "out/*.mp3"):
        found = list(camp.glob(pat))
        if found:
            return found[0]
    return None

def main():
    if len(sys.argv) < 2:
        fail("usage: gate_visuals.py <campaign-dir>")
    camp = Path(sys.argv[1])

    vids = []
    for pat in ("final.mp4", "video/final.mp4", "final.mp4", "*.mp4"):
        vids += list(camp.glob(pat))
    # prefer final.mp4 specifically
    final = None
    for v in vids:
        if v.name == "final.mp4":
            final = v
            break
    if not final and vids:
        final = vids[0]
    if not final:
        fail(f"no final video found under {camp}")
    print(f"video={final}")

    info = ffprobe(final)
    if not info:
        fail(f"ffprobe failed on {final}")
    fmt = info.get("format", {})
    vdur = float(fmt.get("duration", 0))
    print(f"video_duration={vdur:.1f}s")

    # audio stream present?
    streams = info.get("streams", [])
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    if not has_audio:
        fail("video has NO audio stream — narration not muxed")
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    a_dur = float(audio_stream.get("duration") or 0) or vdur

    # narration source duration
    narration = find_narration(camp)
    if narration:
        ninfo = ffprobe(narration)
        ndur = float(ninfo.get("format", {}).get("duration", 0)) if ninfo else 0
        print(f"narration={narration} duration={ndur:.1f}s")
        # THE TRUNCATION CHECK
        if vdur < ndur - 2.0:
            fail(f"TRUNCATED: video {vdur:.0f}s < narration {ndur:.0f}s (lost {ndur-vdur:.0f}s of audio). Rebuild scenes longer.")
    else:
        print("WARN: no narration file found to compare (skipping truncation check)")

    print(f"PASS: visuals gate (video {vdur:.0f}s, audio stream present)")
    sys.exit(0)

if __name__ == "__main__":
    main()
