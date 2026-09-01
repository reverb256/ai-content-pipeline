#!/usr/bin/env python3
"""Sidechain + loudnorm filter chain test with 2-clip sample."""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "scripts/audio")
from storyteller import gen_tone, sidechain_mix, concat_scenes, _copy_audio

work = Path(tempfile.mkdtemp(prefix="storyteller-chain-"))
print(f"workdir: {work}")

# Generate 2 short "speech" clips (tones at different freqs) and a music bed
print("generating test clips...")
speech1 = work / "speech1.wav"
speech2 = work / "speech2.wav"
bed = work / "bed.wav"

# Two "speech" tones (simulate speech)
gen_tone(speech1, 2.0, freq=350.0, kind="sine", volume=0.5)
gen_tone(speech2, 2.0, freq=450.0, kind="sine", volume=0.5)
print(f"  speech1: {speech1.stat().st_size} bytes")
print(f"  speech2: {speech2.stat().st_size} bytes")

# Music bed: a chord-like tone
gen_tone(bed, 5.0, freq=220.0, kind="sine", volume=0.3)
print(f"  bed: {bed.stat().st_size} bytes")

# Concat the two speech clips into one "scene"
print("concatenating speech clips...")
concat_list = work / "concat_list.txt"
concat_list.write_text(f"file '{speech1}'\nfile '{speech2}'\n")
speech_combined = work / "speech_combined.wav"
subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
     "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(speech_combined)],
    check=True, capture_output=True, text=True,
)
print(f"  combined speech: {speech_combined.stat().st_size} bytes")

# Run sidechain mix
print("running sidechain mix...")
t0 = time.time()
mixed = work / "mixed.wav"
sidechain_mix(speech_combined, bed, mixed, duck_db=12.0)
print(f"  mixed: {mixed.stat().st_size} bytes ({time.time() - t0:.2f}s)")

# Run loudnorm (simulating concat_scenes step)
print("running loudnorm...")
t0 = time.time()
final = work / "final.mp3"
subprocess.run(
    ["ffmpeg", "-y", "-i", str(mixed),
     "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
     "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-q:a", "2",
     str(final)],
    check=True, capture_output=True, text=True,
)
print(f"  final mp3: {final.stat().st_size} bytes ({time.time() - t0:.2f}s)")

print("\nCHAIN TEST OK — all filters ran successfully")
