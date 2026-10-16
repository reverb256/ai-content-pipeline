#!/usr/bin/env python3
"""Build the loop fixtures for check_gate_suite.sh.

loop_seamless.wav — 220 Hz, 5 s loop region => 1100 whole
periods => clean wrap (junction curvature ~1.6x).
loop_broken.wav  — 220.5 Hz in the loop region => half-period
phase slip per loop => click at the wrap (~6.0x).
loop_faded.wav   — 220 Hz with a 1.6 s fade-out at the end. The
fade is SMOOTH, so the curvature ruler cannot see it (measured
2.21x with the loop points below, under the 3.0x ceiling), while
its last 1 s sits 8.8 dB below its first 1 s. Card t_bab8aa19:
the level ruler is the only one that refuses it.

Card t_8297d2c6 (successor of t_bab8aa19) adds three fixtures for
the third ruler — the end guard:

loop_faded_short.wav — 220 Hz with a 1.0 s fade-out at the end, the
  hole the level ruler could not see: with a 1.0 s / 6 dB budget the
  fade measures a 4.7 dB delta across the wrap and PASSED (theory:
  a linear fade of length d >= L reads (L/d)/sqrt(3)). Inside its
  last 1.0 s the first half sits 8.5 dB above the second, so the end
  guard refuses it and the refusal NAMES the ramp, not the level.
loop_quiet.wav — 220 Hz at -45.5 dB, constant: quiet but NOT
  silence, so it clears the -50 dB floor and stays level at both
  ends. The end guard must leave it alone (a quiet ending is not a
  fade).
loop_silent_ends.wav — 220 Hz only between 6.5 s and 8.5 s: the loop
  region [5, 10] is silent in its first AND last second, like the
  elemental-air 334 s render (head-1s -59.5 dB, tail-1s -58.7 dB,
  delta 0.8 dB) that the level ruler PASSED. Two silent ends match
  each other, so the end guard refuses it and names the silence.
"""

import math
import struct
import sys
import wave

SR = 44100
DUR = 10.0
N = int(SR * DUR)
FADE_S = 1.6          # the fade in loop_faded.wav (card t_bab8aa19's B)
FADE_SHORT_S = 1.0    # the fade in loop_faded_short.wav (t_8297d2c6)
QUIET_AMP = 0.06      # about -45.5 dB: quiet, above the -50 dB floor
SILENT_MUSIC = (6.5, 8.5)   # where the tone sounds in loop_silent_ends.wav


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

    def faded(t):
        # A linear fade over the last FADE_S seconds: no kink at the wrap,
        # 8.8 dB down across the last second (card t_bab8aa19).
        amp = max(0.0, min(1.0, (DUR - t) / FADE_S))
        return amp * math.sin(2 * math.pi * 220 * t)

    write_wav(f"{out_dir}/loop_faded.wav", faded)

    def faded_short(t):
        # A linear fade over the last 1.0 s: still smooth (curvature cannot
        # see it) and still inside the level ruler's 1.0 s / 6 dB budget
        # (4.7 dB), but the end window's halves differ by 8.5 dB
        # (card t_8297d2c6).
        amp = max(0.0, min(1.0, (DUR - t) / FADE_SHORT_S))
        return amp * math.sin(2 * math.pi * 220 * t)

    write_wav(f"{out_dir}/loop_faded_short.wav", faded_short)

    write_wav(f"{out_dir}/loop_quiet.wav",
              lambda t: QUIET_AMP * math.sin(2 * math.pi * 220 * t))

    def silent_ends(t):
        lo, hi = SILENT_MUSIC
        if lo <= t <= hi:
            return math.sin(2 * math.pi * 220 * t)
        return 0.0

    write_wav(f"{out_dir}/loop_silent_ends.wav", silent_ends)
    print("built loop_seamless.wav + loop_broken.wav + loop_faded.wav + "
          "loop_faded_short.wav + loop_quiet.wav + loop_silent_ends.wav")


if __name__ == "__main__":
    main(sys.argv)
