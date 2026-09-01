#!/usr/bin/env python3
"""Short VoxCPM smoke test: generate one tiny utterance."""
import sys
import time
from pathlib import Path

sys.path.insert(0, "scripts/audio")
from storyteller import voxcpm_tts, voxcpm_available

print(f"voxcpm_available() = {voxcpm_available()}")

tmp = Path("/tmp/_voxcpm_smoke.wav")
start = time.time()
try:
    result = voxcpm_tts(
        "Hello world, this is a test.",
        tmp,
        voice_desc="a clear, expressive narrator",
        quality="f16",
        timeout=120.0,
    )
    dur = time.time() - start
    size = result.stat().st_size
    print(f"OK: {result} ({size} bytes) in {dur:.1f}s")
except RuntimeError as e:
    print(f"FAILED: {e}")
except Exception as e:
    print(f"UNEXPECTED: {type(e).__name__}: {e}")
