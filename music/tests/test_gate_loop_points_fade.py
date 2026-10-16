#!/usr/bin/env python3
"""gate_loop_points must refuse a fade-out tail — the level ruler (t_bab8aa19)
and, for a short fade, the end guard (card t_8297d2c6).

Run: /usr/bin/python3 -m unittest music.tests.test_gate_loop_points_fade
     (from the repo root; ffmpeg must be locatable — see _ffmpeg_dir())

WHY THIS TEST EXISTS (card t_bab8aa19, 2026-10-16). `music/gates/gate_loop_points.py`
is the artifact-defining gate of the `game-assets` lane, and it measured ONE thing:
junction CURVATURE (the discrete second difference of the PCM across the wrap). That
catches a derivative kink — a click. It cannot see a LEVEL discontinuity, and a linear
fade-out is perfectly smooth, so the gate PASSED a track that cannot be looped in a
game. Measured on the frozen probe artifacts (card t_6f0d261e), before the fix:

  $ python3 music/gates/gate_loop_points.py --master B_faded.wav --loop-points lp.json
  PASS gate_loop_points
    seam     : curvature ratio 2.21x (max 3.0x) — seamless
  rc=0
      ... while its tail-1s measured -29.9 dB against a head-1s of -21.1 dB
      (delta 8.8 dB) — a hard reject on the rubric's own `reject_signals`
      ("fade-out or truncated ending on a game-loop claim").

`music/rubrics/gamer.json` `loop_safety` (weight 3 of 10) names the missing evidence:
"last-1s RMS within ~6 dB of first-1s RMS, no fade-to-silence on a loop claim". So the
gate now runs TWO rulers and a loop must pass BOTH. The fade fixture below is the RED
case: it used to exit 0, it must exit 1, and it must exit 1 FOR THE LEVEL REASON — the
same loop stays under the 3.0x curvature ceiling, which is why no value of
`--click-ratio-max` can separate it from the real click case (5.99x).

WHY THE THIRD RULER EXISTS (card t_8297d2c6, successor of t_bab8aa19). The level ruler
is honest about what it measures, but its window is the rubric's 1.0 s and its ceiling
the rubric's own ~6 dB, so a fade SHORTER than ~1.15 s hides inside that budget — by
arithmetic, not by accident: for a linear fade of length d >= L the last-L RMS ratio is
(L/d)/sqrt(3). Measured by executing the gate on the card's 25.6 s 220 Hz probe tone
(loop 0 -> 25.6 s), 2026-10-16:

  fade-out tail | curvature | level delta (tail-1s vs head-1s) | end ramp | verdict
  none          | 1.56x     | 0.0 dB                        | 0.0 dB   | PASS
  0.25 s        | 2.21x     | 0.8 dB                        | 1.7 dB   | PASS
  0.50 s        | 2.21x     | 1.7 dB                        | 4.7 dB   | PASS
  0.60 s        | ~2.21x    | 2.2 dB                        | 6.2 dB   | FAIL <- end guard
  1.00 s        | 2.21x     | 4.7 dB  (UNDER the ceiling)   | 8.5 dB   | FAIL <- end guard
  1.20 s        | 2.21x     | 6.3 dB                        | 8.5 dB   | FAIL <- level
  1.60 s        | 2.21x     | 8.8 dB                        | 8.5 dB   | FAIL <- level
  4.00 s        | 2.94x     | 16.8 dB                       | 8.4 dB   | FAIL <- level

So the gate now measures a THIRD, different property — the envelope INSIDE the end
window, not the level between the ends:
  * the rubric's own 1.0 s window at the loop end, split into two 0.5 s halves; FAIL
    when the second half is more than the rubric's own 6 dB below the first (one dial,
    `--level-delta-max`, for both rulers — no moved number);
  * a silence PRECONDITION: a window that is itself silence is not evidence of level
    continuity, so a first or last window at/below the lane's own -50 dB floor
    (`loop_close.py` SILENCE_FLOOR_DB, `silencedetect noise=-50dB`) is a FAIL naming
    both levels. This closes the SYMMETRIC hole: the elemental-air 334 s master is
    silent at BOTH ends (head-1s -59.5 dB, tail-1s -58.7 dB, delta 0.8 dB) and the
    level ruler PASSED it.
  * the end guard does NOT guard the head against a ramp (a fade-in): on real
    generator output a head half-to-half ramp of 9.4 dB occurs on a loop the rubric
    accepts, so a symmetric guard would be a false fail.
No new thresholds: the window is the rubric's 1 s, the tolerance the rubric's own ~6 dB,
the floor the lane's -50 dB. Measured separation on 25 real loops (3 closed by
`music/scripts/loop_close.py` from real ACE masters, 22 written by
`music/assets/pack.py` from real masters): the largest half-to-half end ramp on real
material is 5.3 dB, and every fade fixture from 0.6 s up reads 6.2 dB or more.

Measured with the fixtures this test builds (real gate output, 2026-10-16):

  case        curvature          level (tail vs head)      verdict
  seamless    1.56x  (pass)      0.0 dB  (-21.1/-21.1)     PASS
  faded       2.21x  (pass)      8.8 dB  (-29.9/-21.1)     FAIL <- the level ruler
  shortfade   2.21x  (pass)      4.7 dB  (UNDER 6.0)       FAIL <- the end guard
  quiet       measured           0.0 dB  (-45.5/-45.5)     PASS <- quiet is not silence
  silentends  measured           0.0 dB  (both ends -91)   FAIL <- the silence floor
  phaseslip   5.99x  (FAIL)      0.0 dB  (-3.0/-3.0)       FAIL <- curvature (its hole
                                                                is the mirror one:
                                                                the level ruler is
                                                                blind to a click)
  truncated   33.80x (FAIL)      0.0 dB                    FAIL <- curvature
  silent      measured           measured                  FAIL <- silent region

Every fixture is synthesized by ffmpeg `lavfi` in setUpClass — nothing is read from a
checked-in audio file, and no fixture is trusted by name: the gate re-renders and
re-measures each one.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
GATE = REPO / "music" / "gates" / "gate_loop_points.py"

# The lane's real loop shape: 16 bars of 4/4 at 150 BPM (elemental-fire's cutdown).
BPM = 150.0
BARS = 16
DUR = BARS * 4 * 60.0 / BPM            # 25.600 s
FREQ = 220.0                           # 220 Hz * 25.6 s = 5632 whole cycles
SR = 44100
QUARTER_CYCLE = 1.0 / (4 * FREQ)       # the truncation in case D
HALF_CYCLE = 1.0 / (2 * FREQ)          # the phase slip in case C
FADE_START = 24.0                      # afade out over the last 1.6 s (case B)
FADE_SHORT_S = 1.0                     # afade out over the last 1.0 s (case F)
QUIET_GAIN = 0.06                      # about -45.5 dB: quiet, not silence

# The rubric's own numbers (`loop_safety`), and the gate's defaults.
LEVEL_WINDOW_S = 1.0
LEVEL_DELTA_MAX_DB = 6.0
CURVATURE_MAX = 3.0
SILENCE_FLOOR_DB = -50.0               # the lane's own floor (loop_close.py)

RATIO_RE = re.compile(r"curvature ratio ([\d.]+)x")
DELTA_RE = re.compile(r"delta ([\d.]+) dB")
RAMP_RE = re.compile(r"ramp (-?[\d.]+) dB")
HALVES_RE = re.compile(r"first half (-?[\d.]+) dB vs second half "
                       r"(-?[\d.]+) dB")


def _ffmpeg_dir() -> pathlib.Path:
    """Locate the lane's ffmpeg. Refuse loudly — a silent skip proves nothing."""
    env = os.environ.get("FFMPEG_BIN_DIR")
    cands = [pathlib.Path(env)] if env else []
    cands.append(pathlib.Path.home() / ".hermes" / "tools" /
                 "ffmpeg-9.0.1-linux-x64" / "bin")
    for cand in cands:
        if (cand / "ffmpeg").is_file() and (cand / "ffprobe").is_file():
            return cand
    found = shutil.which("ffmpeg")
    if found:
        return pathlib.Path(found).parent
    raise RuntimeError(
        "ffmpeg/ffprobe not found — gate_loop_points measures the seam with them, "
        "so this test cannot run. Set FFMPEG_BIN_DIR to the directory holding "
        "ffmpeg + ffprobe (e.g. ~/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin).")


def _synth(ffbin: pathlib.Path, out: pathlib.Path, name: str,
           inargs: list[str], loop_end: float) -> dict:
    """Build one fixture with ffmpeg and write its loop_points.json."""
    wav = out / f"{name}.wav"
    proc = subprocess.run(
        [str(ffbin / "ffmpeg"), "-y", "-v", "error", *inargs,
         "-ac", "1", "-ar", str(SR), str(wav)],
        capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not wav.is_file() or wav.stat().st_size == 0:
        raise RuntimeError(f"ffmpeg could not build the {name} fixture: "
                           f"{proc.stderr.strip()[-400:]}")
    lp = out / f"{name}.loop_points.json"
    lp.write_text(json.dumps({"loop_start_s": 0.0, "loop_end_s": loop_end,
                              "seamless": True}), encoding="utf-8")
    return {"wav": wav, "loop_points": lp, "loop_end": loop_end}


def build_cases(out: pathlib.Path, ffbin: pathlib.Path) -> dict[str, dict]:
    """Synthesize all five fixtures. Returns {name: {wav, loop_points, ...}}."""
    sine = f"sine=frequency={FREQ}:duration={DUR}"
    return {
        # A. a real seamless loop: whole cycles, full level at both ends
        "seamless": _synth(ffbin, out, "seamless",
                           ["-f", "lavfi", "-i", sine], DUR),
        # B. a 1.6 s fade-out tail — smooth, so curvature passes it (THE RED CASE)
        "faded": _synth(ffbin, out, "faded",
                        ["-f", "lavfi", "-i", sine,
                         "-af", f"afade=t=out:st={FADE_START}:d={DUR - FADE_START}"],
                        DUR),
        # C. half-period phase slip at the wrap: flip the sign of the final half
        #    cycle (one tanh step, no commas to escape). A pure click.
        "phaseslip": _synth(
            ffbin, out, "phaseslip",
            ["-f", "lavfi", "-i",
             f"aevalsrc=sin(2*PI*{FREQ}*t)*tanh(-100000*(t-"
             f"{DUR - HALF_CYCLE:.7f})):s={SR}:d={DUR}"], DUR),
        # D. cut 1/4 cycle early: the file's own duration IS the loop end
        "truncated": _synth(ffbin, out, "truncated",
                            ["-f", "lavfi", "-i",
                             f"sine=frequency={FREQ}:duration={DUR - QUARTER_CYCLE:.7f}"],
                            DUR - QUARTER_CYCLE),
        # E. digital silence across the whole loop region
        "silent": _synth(ffbin, out, "silent",
                         ["-f", "lavfi", "-i",
                          f"anullsrc=r={SR}:cl=mono:d={DUR}"], DUR),
        # F. a 1.0 s fade-out tail — the level ruler cannot see it (t_8297d2c6):
        #    its 1.0 s / 6 dB delta is 4.7 dB, UNDER the ceiling, while the wrap
        #    still jumps from digital silence to full level.
        "shortfade": _synth(
            ffbin, out, "shortfade",
            ["-f", "lavfi", "-i", sine,
             "-af", f"afade=t=out:st={DUR - FADE_SHORT_S}:d={FADE_SHORT_S}"],
            DUR),
        # G. a quiet but NONZERO loop (-45.5 dB, above the -50 dB floor): the
        #    end guard must leave it alone — quiet is not silence (t_8297d2c6)
        "quiet": _synth(ffbin, out, "quiet",
                        ["-f", "lavfi", "-i", sine,
                         "-af", f"volume={QUIET_GAIN}"], DUR),
        # H. silent at BOTH ends, level in the middle: two silent ends match
        #    each other, so the LEVEL ruler passes it (delta 0.0 dB) and only
        #    the silence precondition refuses it (t_8297d2c6, the measured
        #    elemental-air hole). The tone sounds from 3.0 s to DUR - 3.0 s.
        "silentends": _synth(
            ffbin, out, "silentends",
            ["-f", "lavfi", "-i", sine,
             "-af", "volume=volume='if(between(t\\,3.0\\,"
                    f"{DUR - 3.0:.1f})\\,1\\,0)':eval=frame"], DUR),
    }


class LoopGateOnFadeOutTail(unittest.TestCase):
    """The five cases the card names, each run through the real gate."""

    @classmethod
    def setUpClass(cls):
        cls.ffbin = _ffmpeg_dir()
        cls._tmp = tempfile.TemporaryDirectory(prefix="loopgate-test-")
        cls.dir = pathlib.Path(cls._tmp.name)
        cls.cases = build_cases(cls.dir, cls.ffbin)
        cls.env = dict(os.environ)
        cls.env["PATH"] = f"{cls.ffbin}{os.pathsep}{cls.env.get('PATH', '')}"
        cls._runs = 0

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def run_gate(self, case: str, *extra: str) -> subprocess.CompletedProcess:
        """Run the real gate on one fixture. Each call gets its own scratch."""
        cls = type(self)
        cls._runs += 1
        case_data = cls.cases[case]
        return subprocess.run(
            [sys.executable, str(GATE),
             "--master", str(case_data["wav"]),
             "--loop-points", str(case_data["loop_points"]),
             "--scratch", str(cls.dir / f"scratch_{case}_{cls._runs}"),
             *extra],
            capture_output=True, text=True, cwd=REPO, env=cls.env, timeout=600)

    @staticmethod
    def ratio(output: str) -> float:
        m = RATIO_RE.search(output)
        assert m, f"the gate printed no curvature ratio:\n{output}"
        return float(m.group(1))

    @staticmethod
    def delta(output: str) -> float:
        m = DELTA_RE.search(output)
        assert m, f"the gate printed no level delta:\n{output}"
        return float(m.group(1))

    # --- 1. the control: a genuine loop still passes ---------------------
    def test_1_seamless_tone_passes_both_rulers(self):
        proc = self.run_gate("seamless")
        out = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, f"a seamless tone was refused:\n{out}")
        self.assertLess(self.ratio(out), CURVATURE_MAX)
        self.assertLessEqual(self.delta(out), LEVEL_DELTA_MAX_DB)
        # every ruler must report its measurement on PASS
        self.assertIn("seam     : curvature ratio", proc.stdout)
        self.assertIn("level    : tail-1.0s", proc.stdout)
        self.assertIn("end      : first half", proc.stdout)
        self.assertIn("not silent", proc.stdout)

    # --- 2. THE RED CASE: a smooth fade-out must be refused ---------------
    def test_2_fade_out_tail_fails_for_the_level_reason(self):
        """Before the fix this exited 0 (measured: PASS at 2.21x, tail 8.8 dB down)."""
        proc = self.run_gate("faded")
        out = proc.stdout + proc.stderr
        self.assertEqual(
            proc.returncode, 1,
            "the gate PASSED a fade-out tail — the false pass of card t_bab8aa19 "
            f"has returned:\n{out}")

        # ... and it must be refused for the LEVEL, not for the curvature. If the
        # fixture were clicky the test would prove nothing about the level ruler.
        ratio = self.ratio(out)
        self.assertLess(
            ratio, CURVATURE_MAX,
            f"the fade fixture measured {ratio:.2f}x curvature, over the "
            f"{CURVATURE_MAX}x ceiling — it is no longer the smooth fade the "
            "curvature ruler cannot see")
        self.assertNotIn("seam curvature ratio", out,
                         "the fade was refused by the curvature ruler, not the "
                         "level ruler")

        # the rubric's evidence, with the measured delta in the message
        self.assertIn("loop level drops", out)
        delta = self.delta(out)
        self.assertGreater(delta, LEVEL_DELTA_MAX_DB)
        self.assertIn(f"{delta:.1f} dB", out)
        self.assertIn("tail-1.0s", out)
        self.assertIn("head-1.0s", out)

    # --- 3. a pure click still fails on ruler 1 ---------------------------
    def test_3_phase_slip_fails_on_the_curvature_ruler(self):
        proc = self.run_gate("phaseslip")
        out = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 1, out)
        self.assertGreater(self.ratio(out), CURVATURE_MAX)
        self.assertIn("seam curvature ratio", out)
        # the mirror hole, documented so nobody "simplifies" the gate to one
        # ruler: the level ruler is blind to this break
        self.assertLessEqual(self.delta(out), LEVEL_DELTA_MAX_DB)

    # --- 4. a truncated ending fails ---------------------------------------
    def test_4_truncated_cycle_fails(self):
        proc = self.run_gate("truncated")
        out = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 1, out)
        self.assertGreater(self.ratio(out), CURVATURE_MAX)

    # --- 5. a silent loop region fails -------------------------------------
    def test_5_silent_loop_region_fails(self):
        proc = self.run_gate("silent")
        out = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("silent", out)

    # --- 6. control for the control: the level ruler IS the decider --------
    def test_6_the_level_ceiling_is_the_decider_and_is_overridable(self):
        """Re-run case B with the ceiling raised: the same loop passes again.

        This proves case 2 fails because of the measured level delta, and that the
        `--level-delta-max` dial moves that decision (the escape hatch a genre
        with a legitimate fade would use).
        """
        proc = self.run_gate("faded", "--level-delta-max", "20")
        out = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, out)
        self.assertGreater(self.delta(out), LEVEL_DELTA_MAX_DB)
        self.assertLess(self.ratio(out), CURVATURE_MAX)

    # --- 7. THE SECOND RED CASE: a 1.0 s fade-out (card t_8297d2c6) --------
    def test_7_short_fade_out_tail_fails_for_the_end_ramp(self):
        """Before ruler 3 this exited 0 (measured: PASS at 2.21x, 4.7 dB level).

        The level ruler cannot see a 1.0 s fade: for a linear fade of length
        d >= L the last-L RMS ratio is (L/d)/sqrt(3), so the 1.0 s window reads
        4.7 dB — inside the rubric's own 6 dB. The end guard measures the
        ENVELOPE inside that window and reads 8.5 dB between its halves.
        """
        proc = self.run_gate("shortfade")
        out = proc.stdout + proc.stderr
        self.assertEqual(
            proc.returncode, 1,
            "the gate PASSED a 1.0 s fade-to-silence tail — the false pass of "
            f"card t_8297d2c6 has returned:\n{out}")

        # the refusal must NAME the end ramp, and the split is what decided it
        self.assertIn("the loop end ramps", out)
        m = RAMP_RE.search(out)
        self.assertIsNotNone(m, f"the gate printed no end ramp:\n{out}")
        ramp = float(m.group(1))
        self.assertGreater(ramp, LEVEL_DELTA_MAX_DB)

        # the measured levels must be in the message (acceptance #1/#3): both
        # halves, and the level delta that stayed UNDER the ceiling
        halves = HALVES_RE.search(out)
        if halves is None:
            self.fail(f"the refusal did not print both halves' levels:\n{out}")
        self.assertIn(f"{float(halves.group(1)):.1f} dB", out)
        self.assertIn(f"{float(halves.group(2)):.1f} dB", out)
        self.assertLess(
            self.delta(out), LEVEL_DELTA_MAX_DB,
            "the 1.0 s fade now trips the LEVEL ruler too — it is no longer "
            "the short-fade case that only the end guard can see")
        self.assertLess(self.ratio(out), CURVATURE_MAX)
        self.assertNotIn("loop level drops", out)

    # --- 8. quiet is not silence: a nonzero quiet ending passes ------------
    def test_8_quiet_nonzero_loop_ending_passes(self):
        """-45.5 dB is quiet and above the lane's -50 dB floor: leave it alone."""
        proc = self.run_gate("quiet")
        out = proc.stdout + proc.stderr
        self.assertEqual(
            proc.returncode, 0,
            f"the end guard refused a loop that ENDS at level, above the "
            f"{SILENCE_FLOOR_DB} dB floor — quiet is not a fade:\n{out}")
        self.assertLessEqual(self.delta(out), LEVEL_DELTA_MAX_DB)
        ramp = RAMP_RE.search(out)
        if ramp is None:
            self.fail(f"the gate printed no end ramp on PASS:\n{out}")
        self.assertLessEqual(float(ramp.group(1)), LEVEL_DELTA_MAX_DB)
        # and the measured level really is quiet (the case is what it claims)
        self.assertLess(self.tail_level(out), SILENCE_FLOOR_DB + 6.0)

    # --- 9. THE SYMMETRIC HOLE: silent at both ends (card t_8297d2c6) ------
    def test_9_loop_silent_at_both_ends_fails_on_the_silence_floor(self):
        """Two silent ends match each other, so the LEVEL ruler passes it.

        Measured on the real elemental-air 334 s master: head-1s -59.5 dB,
        tail-1s -58.7 dB, delta 0.8 dB, `PASS gate_loop_points`. A window that
        is itself silence is not evidence of level continuity.
        """
        proc = self.run_gate("silentends")
        out = proc.stdout + proc.stderr
        self.assertEqual(
            proc.returncode, 1,
            "the gate PASSED a loop that is silent at both ends — the "
            f"symmetric false pass of card t_8297d2c6:\n{out}")
        self.assertIn("is silence", out)
        self.assertIn(f"floor {SILENCE_FLOOR_DB:.1f} dB", out)
        self.assertIn("the first and last 1.0s", out)
        # the level ruler is blind here — that is the whole point
        self.assertLessEqual(
            self.delta(out), LEVEL_DELTA_MAX_DB,
            "the symmetric-silence fixture tripped the LEVEL ruler, so it no "
            "longer proves the silence precondition decides")
        # and the region RMS guard did not decide it either
        self.assertNotIn("the loop region is silent", out)

    @staticmethod
    def tail_level(output: str) -> float:
        m = re.search(r"tail-1\.0s (-?[\d.]+) dB", output)
        assert m, f"the gate printed no tail level:\n{output}"
        return float(m.group(1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
