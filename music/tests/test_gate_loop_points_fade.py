#!/usr/bin/env python3
"""gate_loop_points must refuse a fade-out tail — the level ruler (card t_bab8aa19).

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

Measured with the fixtures this test builds (real gate output, 2026-10-16):

  case        curvature          level (tail vs head)      verdict
  seamless    1.56x  (pass)      0.0 dB  (-21.1/-21.1)     PASS
  faded       2.21x  (pass)      8.8 dB  (-29.9/-21.1)     FAIL <- the level ruler
  phaseslip   5.99x  (FAIL)      0.0 dB  (-3.0/-3.0)       FAIL <- curvature (its hole
                                                                is the mirror one:
                                                                the level ruler is
                                                                blind to a click)
  truncated   33.80x (FAIL)      0.0 dB                    FAIL <- curvature
  silent      measured            measured                  FAIL <- silent region

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

# The rubric's own numbers (`loop_safety`), and the gate's defaults.
LEVEL_WINDOW_S = 1.0
LEVEL_DELTA_MAX_DB = 6.0
CURVATURE_MAX = 3.0

RATIO_RE = re.compile(r"curvature ratio ([\d.]+)x")
DELTA_RE = re.compile(r"delta ([\d.]+) dB")


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
        # both rulers must report their measurement on PASS
        self.assertIn("seam     : curvature ratio", proc.stdout)
        self.assertIn("level    : tail-1.0s", proc.stdout)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
