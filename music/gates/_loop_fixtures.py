#!/usr/bin/env python3
"""Build the loop fixtures for check_gate_suite.sh.

loop_seamless.wav — 220 Hz, 5 s loop region => 1100 whole
periods => clean wrap (junction curvature ~1.6x).
loop_broken.wav  — 220.5 Hz in the loop region => half-period
phase slip per loop => click at the wrap (~6.0x).
"""

import math
import struct
import sys
import wave

SR = 44100
DUR = 10.0
N = int(SR * DUR)


def write_wav(path, gen):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for i in range(N):
            t = i / SR
            frames += struct.pack("<h", int(gen(t) * 30000))
        w.writeframes(bytes(frames))


def main(argv):
    out_dir = argv[1]
    write_wav(f"{out_dir}/loop_seamless.wav",
              lambda t: math.sin(2 * math.pi * 220 * t))

    def broken(t):
        freq = 220.5 if 5.0 <= t < 10.0 else 220.0
        return math.sin(2 * math.pi * freq * t)

    write_wav(f"{out_dir}/loop_broken.wav", broken)
    print("built loop_seamless.wav + loop_broken.wav")


if __name__ == "__main__":
    main(sys.argv)
