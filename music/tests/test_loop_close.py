#!/usr/bin/env python3
"""loop_close — the render rail's loop check and the delivered-loop builder (card t_b21aeb51).

Run: /usr/bin/python3 -m unittest music.tests.test_loop_close
     (from the repo root; numpy+scipy are needed for the parity case only, ffmpeg
      must be locatable — see ffmpeg_dir())

WHY THIS TEST EXISTS (card t_b21aeb51, board music, 2026-10-16)
---------------------------------------------------------------
Every ACE render ends in 1.5-6.2 s of digital silence, the render rail
(`helm/charts/music-pipeline/templates/cronjob-render.yaml`) wrote its success
`.rendered` marker on `rc=0` alone, and so the rail certified a master that is
provably not loopable. Measured on the delivered master of t_28146d70
(elemental-fire "Emberfall", 120.000 s, sha256
ddc73523dca73bd756197cd83c75f5aa206bc97462a4707b10f4118455c9c67c, byte-identical
to what ComfyUI returned — nothing in the wrapper pads it):

  head-1s mean_volume -25.1 dB   tail-1s mean_volume -58.7 dB   delta 33.6 dB
  silencedetect noise=-50dB:d=0.5 -> silence 115.224063 -> 119.983896 (4.76 s)

A check that has never failed on real input is not a check. So this suite pins
three things:

  RED      the frozen real artifact — music/tests/fixtures/loop_silence_tail.wav
           (15.000 s: the first 10 s of that master + 5 s of digital silence,
           sha256 51473534c1075573248ddfab8e1a2db52921dd617013275af6cb0661366421f7)
           — must FAIL the level ruler, and must fail FOR THE LEVEL REASON.
  RED      a synthesized silence-tailed loop claim (no committed bytes) must
           FAIL the same way.
  GREEN    close mode must build a loop artifact from a silence-tailed render
           that PASSES the committed two-ruler gate_loop_points AND
           loop_seam_check, with neither end silent.

PARITY (the reason the port is allowed to exist)
------------------------------------------------
`music/scripts/loop_close.py` carries a port of `music/assets/pack.py`'s
`choose_loop_bars`, `crossfade_into_preroll` and `edge_fade`, because the rail's
image (`python:3.13-slim`) has no numpy/scipy. A second, differently-behaving
loop builder is worse than the defect, so TestParityWithPack imports BOTH and
requires identical constants, an identical bar count, and sample-identical
output (bitwise, float32). TestGenreReaderParity does the same for the registry
reader: loop_close parses music/genres.yaml with no PyYAML, PyYAML parses it
here, and the two {genre: video_shape} maps must be equal.
"""

import array
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
LOOP_CLOSE = REPO / "music" / "scripts" / "loop_close.py"
GATE = REPO / "music" / "gates" / "gate_loop_points.py"
SEAM = REPO / "music" / "scripts" / "loop_seam_check.py"
GENRES = REPO / "music" / "genres.yaml"
FIXTURE = HERE / "fixtures" / "loop_silence_tail.wav"

# The frozen fixture, measured with ffmpeg volumedetect (2026-10-16).
FIXTURE_SHA256 = ("51473534c1075573248ddfab8e1a2db52921dd617013275af6cb0661366421f7")
FIXTURE_DURATION = 15.000
FIXTURE_SILENCE_FROM = 10.0

BPM = 150.0                     # elemental-fire's anchor: one bar = 1.600 s
BAR_S = 4 * 60.0 / BPM
SR = 44100
LEVEL_MAX = 6.0                 # rubrics/gamer.json `loop_safety` ("~6 dB")
VOL_RE = re.compile(r"mean_volume:\s*(-?[\d.]+)\s*dB")


def ffmpeg_dir() -> pathlib.Path:
    """The lane's ffmpeg, resolved the way loop_seam_check.py resolves it."""
    env = os.environ.get("FFMPEG_BIN_DIR")
    cands = [pathlib.Path(env)] if env else []
    cands.append(pathlib.Path.home() / ".hermes" / "tools" /
                 "ffmpeg-9.0.1-linux-x64" / "bin")
    for c in cands:
        if (c / "ffmpeg").is_file():
            return c
    found = shutil.which("ffmpeg")
    if found:
        return pathlib.Path(found).parent
    return pathlib.Path("/usr/bin")


FF_DIR = ffmpeg_dir()


def run(cmd, **kw):
    env = dict(os.environ)
    env["FFMPEG_BIN_DIR"] = str(FF_DIR)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                          env=env, **kw)


def mean_volume_db(path, start=0.0, dur=None):
    """Independent measurement: ffmpeg volumedetect on a slice."""
    cmd = [str(FF_DIR / "ffmpeg"), "-v", "info", "-ss", f"{start:.4f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.4f}"]
    cmd += ["-i", str(path), "-af", "volumedetect", "-f", "null", "-"]
    m = VOL_RE.search(run(cmd).stderr or "")
    return float(m.group(1)) if m else None


def check_only(master):
    return run([sys.executable, str(LOOP_CLOSE), "--check-only",
                "--master", str(master)])


def build_tone_with_silence(out: pathlib.Path, music_s: float, silence_s: float,
                            freq: float = 220.0) -> pathlib.Path:
    """music_s of a 220 Hz tone, then silence_s of digital silence."""
    out.mkdir(parents=True, exist_ok=True)
    path = out / "source.wav"
    run([str(FF_DIR / "ffmpeg"), "-v", "error", "-y",
         "-f", "lavfi", "-i",
         f"sine=frequency={freq}:sample_rate={SR}:duration={music_s}",
         "-f", "lavfi", "-i",
         f"anullsrc=r={SR}:cl=mono",
         "-filter_complex",
         f"[0:a]aformat=channel_layouts=mono[a];"
         f"[1:a]atrim=0:{silence_s},asetpts=PTS-STARTPTS[b];"
         f"[a][b]concat=n=2:v=0:a=1[out]",
         "-map", "[out]", "-c:a", "pcm_s16le", str(path)])
    return path


class TestFrozenFixture(unittest.TestCase):
    """The RED case: the real pre-fix rail output must FAIL the check."""

    def test_fixture_is_the_frozen_artifact(self):
        self.assertTrue(FIXTURE.is_file(), f"missing frozen fixture {FIXTURE}")
        import hashlib
        sha = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        self.assertEqual(sha, FIXTURE_SHA256,
                         "the frozen fixture changed — it is evidence, not a "
                         "sample; regenerate it and update the card instead")
        proc = run([str(FF_DIR / "ffprobe"), "-v", "error", "-show_entries",
                    "format=duration", "-of",
                    "default=noprint_wrappers=1:nokey=1", str(FIXTURE)])
        self.assertAlmostEqual(float(proc.stdout.strip()), FIXTURE_DURATION, 3)

    def test_fixture_ends_in_silence(self):
        """Measured independently of loop_close: the defect is really there."""
        head = mean_volume_db(FIXTURE, 0.0, 1.0)
        tail = mean_volume_db(FIXTURE, FIXTURE_DURATION - 1.0, 1.0)
        self.assertIsNotNone(head)
        self.assertIsNotNone(tail)
        self.assertGreater(abs(tail - head), LEVEL_MAX + 30.0,
                           f"head {head} tail {tail}: the fixture no longer "
                           "reproduces the 4.76 s silence tail")

    def test_fixture_FAILS_the_check(self):
        res = check_only(FIXTURE)
        self.assertEqual(res.returncode, 1,
                         "the frozen pre-fix artifact PASSED the check — the "
                         f"hole is back:\n{res.stdout}\n{res.stderr}")
        self.assertIn("loop level drops", res.stderr)
        self.assertIn("max 6.0", res.stderr)


class TestSyntheticCases(unittest.TestCase):
    """RED and GREEN, synthesized with ffmpeg (nothing read from disk)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = pathlib.Path(tempfile.mkdtemp(prefix="loopclose-test-"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_silence_tailed_loop_claim_FAILS(self):
        """25.6 s of music + 5 s of silence: a loop claim that is not a loop."""
        src = build_tone_with_silence(self.tmp / "s1", 25.6, 5.0)
        res = check_only(src)
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("is silence", res.stderr)

    def test_seamless_tone_PASSES(self):
        src = self.tmp / "s2_seamless.wav"
        run([str(FF_DIR / "ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i",
             f"sine=frequency=220:sample_rate={SR}:duration=25.6",
             "-c:a", "pcm_s16le", str(src)])
        res = check_only(src)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("PASS loop_close --check-only", res.stdout)

    def test_close_BUILDS_a_loop_that_passes_BOTH_rulers(self):
        """GREEN: the rail's closer turns a silence-tailed render into a loop.

        The music ends at 25.2 s (15.75 bars at 150 BPM), so this also covers
        the bar-alignment rounding: the window must land on a bar boundary.
        """
        src = build_tone_with_silence(self.tmp / "s3", 25.2, 5.0)
        out = self.tmp / "s3_delivered" / "loop.wav"
        lp = self.tmp / "s3_delivered" / "loop_points.json"
        plan = self.tmp / "s3.plan.json"
        plan.write_text(json.dumps({"bpm": BPM, "_meta": {
            "genre": "elemental-fire"}}), encoding="utf-8")
        res = run([sys.executable, str(LOOP_CLOSE), "--master", str(src),
                   "--plan", str(plan), "--out", str(out),
                   "--loop-points-out", str(lp)])
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertTrue(out.is_file())
        self.assertTrue(lp.is_file())

        idx = json.loads(lp.read_text(encoding="utf-8"))
        self.assertEqual(idx["loop_start_s"], 0.0)
        span = idx["loop_end_s"]
        self.assertAlmostEqual(span, round(4 * BAR_S, 6), 6)
        self.assertTrue(idx["seamless"])

        # the artifact's own ends, measured independently
        head = mean_volume_db(out, 0.0, 1.0)
        tail = mean_volume_db(out, span - 1.0, 1.0)
        self.assertLessEqual(abs(tail - head), LEVEL_MAX,
                             f"artifact ends do not match: {head} / {tail}")

        # the committed gate, BOTH rulers, on the artifact
        g = run([sys.executable, str(GATE), "--master", str(out),
                 "--loop-points", str(lp)])
        self.assertEqual(g.returncode, 0, g.stdout + g.stderr)
        self.assertIn("PASS gate_loop_points", g.stdout)

        # and the second ruler as the lane runs it
        s = run([sys.executable, str(SEAM), "--master", str(out),
                 "--loop-points", str(lp)])
        self.assertEqual(s.returncode, 0, s.stdout + s.stderr)
        self.assertIn("PASS loop_seam_check", s.stdout)

        # the check the rail runs on what it is about to certify
        c = check_only(out)
        self.assertEqual(c.returncode, 0, c.stdout + c.stderr)

    def test_close_REFUSES_a_render_shorter_than_one_loop(self):
        """No artifact and a non-zero exit when nothing can carry the claim."""
        src = build_tone_with_silence(self.tmp / "s4", 3.0, 1.0)
        out = self.tmp / "s4_delivered" / "loop.wav"
        res = run([sys.executable, str(LOOP_CLOSE), "--master", str(src),
                   "--bpm", "10", "--out", str(out)])
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertFalse(out.exists(),
                         "a refused render must leave no loop artifact behind")
        self.assertIn("FAIL loop_close", res.stderr)


class TestLoopClaim(unittest.TestCase):
    """The loop claim comes from the genre registry, not from prose."""

    def _plan(self, name, genre):
        p = pathlib.Path(tempfile.mkdtemp(prefix="loopclaim-")) / f"{name}.json"
        p.write_text(json.dumps({"_meta": {"genre": genre}, "bpm": BPM}),
                     encoding="utf-8")
        return p

    def test_loop_shape_genres_are_claims(self):
        for genre in ("elemental-fire", "elemental-earth", "elemental-air",
                      "elemental-water", "chiptune-8bit"):
            res = run([sys.executable, str(LOOP_CLOSE), "--claims-loop",
                       "--plan", str(self._plan(genre, genre)), "--json"])
            self.assertEqual(res.returncode, 0, f"{genre}: {res.stdout}")
            self.assertTrue(json.loads(res.stdout)["claim"])

    def test_non_loop_shapes_are_not_claims(self):
        for genre in ("sentimental-piano", "chill-lounge", "trance"):
            res = run([sys.executable, str(LOOP_CLOSE), "--claims-loop",
                       "--plan", str(self._plan(genre, genre)), "--json"])
            self.assertEqual(res.returncode, 1, f"{genre}: {res.stdout}")
            self.assertFalse(json.loads(res.stdout)["claim"])

    def test_missing_genre_is_a_usage_error(self):
        p = pathlib.Path(tempfile.mkdtemp(prefix="loopclaim-")) / "n.json"
        p.write_text(json.dumps({"bpm": 120}), encoding="utf-8")
        res = run([sys.executable, str(LOOP_CLOSE), "--claims-loop",
                   "--plan", str(p), "--json"])
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)


class TestGenreReaderParity(unittest.TestCase):
    """loop_close's PyYAML-free registry reader must equal PyYAML's."""

    def test_video_shape_map_matches_pyyaml(self):
        try:
            import yaml
        except ImportError:  # pragma: no cover
            self.skipTest("PyYAML not importable")
        sys.path.insert(0, str(REPO / "music" / "scripts"))
        try:
            import loop_close
        finally:
            sys.path.pop(0)
        mine = loop_close.genre_video_shapes(GENRES)
        theirs = {g: e.get("video_shape")
                  for g, e in (yaml.safe_load(GENRES.read_text(
                      encoding="utf-8")) or {}).get("genres", {}).items()}
        self.assertEqual(mine, theirs,
                         "the stdlib registry reader drifted from PyYAML")


class TestParityWithPack(unittest.TestCase):
    """The ported loop builder must behave exactly like music/assets/pack.py."""

    @classmethod
    def setUpClass(cls):
        try:
            import numpy  # noqa: F401
            from scipy import signal  # noqa: F401
        except ImportError:
            raise unittest.SkipTest(
                "numpy+scipy are needed to compare against music/assets/pack.py")
        sys.path.insert(0, str(REPO / "music" / "scripts"))
        try:
            import loop_close
        finally:
            sys.path.pop(0)
        sys.path.insert(0, str(REPO))
        import importlib
        cls.pack = importlib.import_module("music.assets.pack")
        cls.lc = loop_close

    def test_constants_match_pack(self):
        import importlib
        gate = importlib.import_module("music.gates.gate_loop_points")
        self.assertEqual(self.lc.BARS_PREFERRED, self.pack.BARS_PREFERRED)
        self.assertEqual(self.lc.CROSSFADE_S, self.pack.CROSSFADE_S)
        self.assertEqual(self.lc.MIN_LOOP_SPAN_S, gate.MIN_LOOP_SPAN_S)
        self.assertEqual(self.lc.MIN_LOOP_SPAN_S,
                         self.pack.MIN_LOOP_SPAN_S)

    def test_choose_loop_bars_is_identical(self):
        for sr in (44100, 48000):
            for bpm in (50.0, 72.0, 88.0, 92.0, 120.0, 150.0, 184.0):
                for n in (0, sr, int(sr * 1.3), int(sr * 25.6), int(sr * 120),
                          int(sr * 600)):
                    self.assertEqual(
                        self.lc.choose_loop_bars(sr, bpm, n),
                        self.pack.choose_loop_bars(sr, bpm, n),
                        f"sr={sr} bpm={bpm} n={n}")

    def test_crossfade_into_preroll_is_bitwise_identical(self):
        import numpy as np
        rng = np.random.default_rng(20261016)
        for trial in range(6):
            n = 4410 + trial * 137
            sr = 44100
            seg = (rng.standard_normal(n) * 0.3).astype(np.float32)
            pre = (rng.standard_normal(882) * 0.3).astype(np.float32)
            cf = [0, 1, 20, 882][trial % 4]
            theirs, t_method = self.pack.crossfade_into_preroll(
                seg.copy(), pre.copy(), sr, cf)
            mine, m_method = self.lc.crossfade_into_preroll(
                array.array("f", seg.tobytes()), array.array("f", pre.tobytes()),
                sr, cf)
            self.assertEqual(m_method, t_method)
            self.assertEqual(list(mine),
                             [float(x) for x in theirs.astype(np.float32)],
                             f"trial {trial} (cf={cf}) diverged from pack.py")

    def test_edge_fade_is_bitwise_identical(self):
        import numpy as np
        rng = np.random.default_rng(7)
        seg = (rng.standard_normal(8820) * 0.4).astype(np.float32)
        theirs = self.pack.edge_fade(seg.copy(), 44100)
        mine = self.lc.edge_fade(array.array("f", seg.tobytes()), 44100)
        self.assertEqual(list(mine),
                         [float(x) for x in theirs.astype(np.float32)])


if __name__ == "__main__":
    unittest.main()
