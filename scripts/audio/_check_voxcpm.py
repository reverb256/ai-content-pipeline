#!/usr/bin/env python3
"""Check voxcpm availability and test the sidechain/loudnorm chain."""
import sys
try:
    import voxcpm
    print("voxcpm: AVAILABLE")
except ImportError as e:
    print(f"voxcpm: NOT AVAILABLE ({e})")

try:
    import soundfile as sf
    print("soundfile: AVAILABLE")
except ImportError as e:
    print(f"soundfile: NOT AVAILABLE ({e})")
