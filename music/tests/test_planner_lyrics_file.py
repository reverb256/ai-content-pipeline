#!/usr/bin/env python3
"""A plan BUILT FROM A HUMAN SHEET must pass the render rail's own guard.

Run: /usr/bin/python3 -m unittest music.tests.test_planner_lyrics_file
     (from the repo root; the sibling suites are music.test_acestep_guard,
      music.tests.test_acestep_sheet_guard and music.tests.test_planner)

WHY THIS TEST EXISTS (cards t_e69368ff, t_a7a7d998; 2026-10-16)
--------------------------------------------------------------
The brief queue carries `lyricsMode: draft` entries, and `draft` writes a
SCAFFOLD: the section tags plus the template's per-section craft notes in
parentheses, and no singable line. The render rail refuses a scaffold on
purpose (`music/scripts/acestep_plan.py::check_lyrics`, exit 4, a `.refused`
marker) - so every draft entry reaches the rail and stops there.

Measured on the queued trance entry (card t_a7a7d998): the plan at
``/var/lib/music-plans/trance-signal-before-dawn.json`` carried the scaffold,
1011 B, nine section tags, 0 singable lines, and the rail refused it -

    FATAL: 9 section(s) have no lyrics: Intro, Verse 1, Pre-Chorus, Chorus,
           Verse 2, Chorus, Bridge, Chorus, Outro.

while the human-authored sheet for that same track already existed, was already
claimed (`music/lyrics/trance/signal-before-dawn/lyrics.suno.txt`, authors
j_kro, gate `gate_lyrics_original` PASS) and had no way into the plan:
`planner.py` had no `--lyrics-file` input. `--lyrics-mode ai` is not the fix -
AI-written words void the human-authorship claim this lane registers.

So the planner grew `--lyrics-file`, and THIS is its acceptance: the plan it
writes carries the sheet verbatim (byte for byte, so its sha256 IS the one the
sheet's own manifest.json claims), the rail's guard accepts it, and the same
guard still refuses a scaffold-only plan. The last assertion is the control -
without it this file would pass if the guard were simply disabled.

The sheet is read from the repo at run time, not pasted here, so the test
follows the lane's own data. The structure/count assertions are the tripwire: if
the sheet changes shape, this file says so instead of passing on words nobody
measured.

EVERY NUMBER HERE WAS MEASURED on the artifacts it reads (2026-10-16):
    sheet 1219 B, 9 sections, 84 unique words, sha256 e667e248...
    (the suite compares that hash against the manifest, not against a literal,
     because `lyrics.py claim` re-records it when j_kro edits the sheet)
"""

import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent

PLANNER = REPO / "music" / "planner" / "planner.py"
RENDERER = REPO / "music" / "scripts" / "acestep_plan.py"

TRACK_DIR = REPO / "music" / "lyrics" / "trance" / "signal-before-dawn"
SHEET_REL = "music/lyrics/trance/signal-before-dawn/lyrics.suno.txt"
SHEET = REPO / SHEET_REL
MANIFEST = TRACK_DIR / "manifest.json"

# The genre the sheet belongs to, and a VOCAL genre it does not belong to (used
# only to prove the genre cross-check; every instrumental genre is refused
# earlier and by a different rule, so it could not prove this one).
SHEET_GENRE = "trance"
OTHER_VOCAL_GENRE = "anime-opening"
# A genre whose own template declares the lyrics box stays empty: a sheet has no
# sung line to author there (card t_25a6499c D3).
INSTRUMENTAL_GENRE = "chill-lounge"

BRIEF = ("Signal Before Dawn. Holding on through the long stretch before dawn. "
         "Not a party song: a 3am promise, one voice against a big sky. Uplifting "
         "trance at 138 BPM in A minor. The breakdown is the emotional centre and "
         "the drop is the earned payoff.")


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


acestep = _load(RENDERER, "acestep_plan")


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def sheet_text() -> str:
    return SHEET.read_text(encoding="utf-8")


def claimed_sha() -> str:
    return manifest()["files"]["lyrics.suno.txt"]["sha256"]


def plan_via_cli(*extra, genre=SHEET_GENRE, cwd=REPO, timeout=120):
    """Run `planner.py plan` and return (rc, output, plan-or-None).

    The plan is written to a fresh temp file per call, so a refusal that writes
    NOTHING (the contract for a sheet-carrying plan) is distinguishable from a
    refusal that wrote a plan anyway.
    """
    out = pathlib.Path(tempfile.mkdtemp()) / "plan.json"
    cmd = [sys.executable, str(PLANNER), "plan", "--brief", BRIEF,
           "--genre", genre, "--out", str(out), *extra]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd),
                          timeout=timeout)
    plan = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else None
    return proc.returncode, proc.stdout + proc.stderr, plan


def fixture_track_dir(manifest_overrides: dict | None = None,
                      sheet_body: str | None = None) -> pathlib.Path:
    """A copy of the real sheet + manifest, with fields overridden.

    Built from the committed artifacts rather than hand-written, so the fixture
    keeps the schema of `music/track-lyrics-manifest v1`.
    """
    d = pathlib.Path(tempfile.mkdtemp())
    body = sheet_body if sheet_body is not None else sheet_text()
    (d / "lyrics.suno.txt").write_text(body, encoding="utf-8")
    m = manifest()
    if manifest_overrides:
        m = {**m, **manifest_overrides}
    (d / "manifest.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
    return d


class TheSheetIsWhatWeMeasured(unittest.TestCase):
    """Read the sheet's real shape first: the tests below rest on it."""

    def test_the_sheet_is_non_empty_and_tagged(self):
        tags = re.findall(r"^\[([^\]]+)\]", sheet_text(), re.M)
        self.assertEqual(len(tags), 9, f"sheet tags: {tags}")
        self.assertEqual(tags[0], "Intro")

    def test_the_manifest_claim_covers_the_file_on_disk(self):
        on_disk = hashlib.sha256(SHEET.read_bytes()).hexdigest()
        self.assertEqual(on_disk, claimed_sha(),
                         "the sheet changed without `lyrics.py claim` re-recording it")
        self.assertEqual(manifest()["authorship"]["status"], "human-original")
        self.assertEqual(manifest()["authorship"]["authors"], ["j_kro"])
        self.assertIs(manifest()["authorship"]["suno_generated_lyrics"], False)


class ThePlanCarriesTheSheet(unittest.TestCase):
    """THE CARD'S THREE ASSERTIONS (t_a69368ff FAILURE -> TEST)."""

    @classmethod
    def setUpClass(cls):
        cls.rc, cls.output, cls.plan = plan_via_cli(
            "--lyrics-mode", "draft", "--lyrics-file", SHEET_REL,
            "--bpm", "138", "--keyscale", "A minor", "--duration", "417",
            "--title", "Signal Before Dawn")

    def test_a_the_plan_is_written_and_carries_the_sheets_first_line(self):
        self.assertEqual(self.rc, 0, self.output)
        self.assertIsNotNone(self.plan, self.output)
        first_line = [ln for ln in sheet_text().splitlines()
                      if ln.strip() and not ln.strip().startswith(("#", "["))][0]
        self.assertIn(first_line, self.plan["lyrics"])

    def test_a_the_carried_text_hashes_to_the_manifests_hash(self):
        self.assertEqual(hashlib.sha256(self.plan["lyrics"].encode("utf-8")).hexdigest(),
                         claimed_sha())
        self.assertEqual(len(self.plan["lyrics"].encode("utf-8")),
                         manifest()["files"]["lyrics.suno.txt"]["bytes"])

    def test_a_it_is_not_the_scaffold(self):
        # the scaffold's own header: if it is here, the sheet did not replace it
        self.assertNotIn("write every sung line yourself", self.plan["lyrics"])
        self.assertNotIn("(Japanese:", self.plan["lyrics"])

    def test_b_the_render_rails_own_guard_accepts_it(self):
        # `allow_empty=False` is the rail's call (cronjob-render.yaml runs the
        # script WITHOUT --allow-empty); it must not raise.
        acestep.check_lyrics(self.plan, False)
        self.assertFalse(self.plan.get("instrumental"))

    def test_the_authorship_line_is_bound_to_the_sheet(self):
        line = self.plan["authorship"]
        self.assertIn("human-original", line)
        self.assertIn("j_kro", line)
        self.assertIn(SHEET_REL, line)
        self.assertIn(claimed_sha(), line)
        self.assertIn("manifest.json", line)

    def test_the_plan_says_its_lyrics_came_from_a_sheet(self):
        self.assertEqual(self.plan["_meta"]["lyrics_mode"], "sheet")
        src = self.plan["_meta"]["lyrics_source"]
        self.assertEqual(src["sha256"], claimed_sha())
        self.assertEqual(src["authors"], ["j_kro"])
        self.assertEqual(src["status"], "human-original")
        self.assertEqual(src["path"], SHEET_REL)

    def test_the_sheet_plan_is_validated_against_the_blueprint(self):
        # unlike a scaffold, a sheet has words, so the lane's own validation ran
        # and passed: the sheet's structure IS the blueprint's.
        plan = _load(PLANNER, "planner")
        bp = plan.load_blueprint(SHEET_GENRE)
        want = [s.get("tag") if isinstance(s, dict) else str(s)
                for s in (bp.get("structure") or [])]
        got = re.findall(r"^\[([^\]]+)\]", self.plan["lyrics"], re.M)
        self.assertEqual(got, want)


class TheGuardStillRefusesAScaffold(unittest.TestCase):
    """(c) the control: without the sheet, the plan is refused as before."""

    def test_the_guard_refuses_a_scaffold_only_plan(self):
        rc, out, plan = plan_via_cli("--lyrics-mode", "draft", "--bpm", "138",
                                     "--duration", "417")
        self.assertEqual(rc, 0, out)             # planning a scaffold still works
        self.assertEqual(plan["_meta"]["lyrics_mode"], "draft")
        self.assertNotIn(SHEET_REL, json.dumps(plan))
        with self.assertRaises(SystemExit):
            acestep.check_lyrics(plan, False)

    def test_the_deployed_renderer_refuses_it_end_to_end_with_rc_4(self):
        """rc 4 is the refusal the rail records as `.refused` (card t_69cab80b).

        SUNOLOCAL_HOST points at a closed port, so a plan that got PAST the guard
        fails with a submit error instead - which is how this test tells "the
        guard refused it" from "the guard let it through".
        """
        _rc, _out, scaffold = plan_via_cli("--lyrics-mode", "draft", "--bpm", "138",
                                           "--duration", "417")
        d = pathlib.Path(tempfile.mkdtemp())
        p = d / "scaffold-plan.json"
        p.write_text(json.dumps(scaffold), encoding="utf-8")
        env = dict(os.environ, SUNOLOCAL_HOST="http://127.0.0.1:9")
        proc = subprocess.run([sys.executable, str(RENDERER), str(p), "--name", "t"],
                              capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertIn("section(s) have no lyrics", proc.stdout + proc.stderr)
        self.assertNotIn("Failed to submit", proc.stdout + proc.stderr)

    def test_the_sheet_plan_reaches_the_network_instead(self):
        """The same runner, the same closed port, and the plan is NOT refused."""
        _rc, _out, plan = plan_via_cli("--lyrics-mode", "draft",
                                       "--lyrics-file", SHEET_REL, "--bpm", "138",
                                       "--duration", "417")
        d = pathlib.Path(tempfile.mkdtemp())
        p = d / "sheet-plan.json"
        p.write_text(json.dumps(plan), encoding="utf-8")
        env = dict(os.environ, SUNOLOCAL_HOST="http://127.0.0.1:9")
        proc = subprocess.run([sys.executable, str(RENDERER), str(p), "--name", "t"],
                              capture_output=True, text=True, env=env, timeout=120)
        out = proc.stdout + proc.stderr
        self.assertNotIn("section(s) have no lyrics", out)
        self.assertIn("Failed to submit", out)   # past the guard, engine unreachable
        self.assertEqual(proc.returncode, 1, out)


class ASheetThatCannotBeClaimedIsRefused(unittest.TestCase):
    """A sheet is carried only with the claim that makes it usable."""

    def assertRefused(self, *extra, genre=SHEET_GENRE, expect="FAIL: --lyrics-file"):
        rc, out, plan = plan_via_cli(*extra, genre=genre)
        self.assertEqual(rc, 2, out)
        self.assertIn(expect, out)
        self.assertIsNone(plan, "a refused sheet must not write a plan")

    def test_a_missing_file_is_refused(self):
        self.assertRefused("--lyrics-file", "music/lyrics/trance/no-such-track/x.txt")

    def test_a_sheet_without_a_manifest_is_refused(self):
        d = fixture_track_dir()
        (d / "manifest.json").unlink()
        self.assertRefused("--lyrics-file", str(d / "lyrics.suno.txt"),
                           expect="no manifest.json beside it")

    def test_a_claim_that_does_not_cover_the_text_is_refused(self):
        # the sheet is edited after the claim: the hash no longer matches, which
        # is exactly the check `lyrics.py::validate_track_dir` makes.
        d = fixture_track_dir(sheet_body=sheet_text() + "\n[Chorus]\nOne more line\n")
        self.assertRefused("--lyrics-file", str(d / "lyrics.suno.txt"),
                           expect="does not cover THIS text")

    def test_an_ai_authored_claim_is_refused(self):
        d = fixture_track_dir({"authorship": {**manifest()["authorship"],
                                              "status": "ai-assisted"}})
        self.assertRefused("--lyrics-file", str(d / "lyrics.suno.txt"),
                           expect="human-original")

    def test_a_suno_generated_sheet_is_refused(self):
        d = fixture_track_dir({"authorship": {**manifest()["authorship"],
                                              "suno_generated_lyrics": True}})
        self.assertRefused("--lyrics-file", str(d / "lyrics.suno.txt"),
                           expect="suno_generated_lyrics")

    def test_an_unnamed_author_is_refused(self):
        d = fixture_track_dir({"authorship": {**manifest()["authorship"], "authors": []}})
        self.assertRefused("--lyrics-file", str(d / "lyrics.suno.txt"),
                           expect="names no human author")

    def test_an_empty_sheet_is_refused(self):
        d = fixture_track_dir(sheet_body="\n\n")
        self.assertRefused("--lyrics-file", str(d / "lyrics.suno.txt"),
                           expect="the sheet is empty")

    def test_a_sheet_for_another_genre_is_refused(self):
        # the words and the sound would be two different tracks
        self.assertRefused("--lyrics-file", SHEET_REL, genre=OTHER_VOCAL_GENRE,
                           expect="the words and the sound would be two different tracks")

    def test_a_sheet_with_ai_mode_is_refused_before_any_model_call(self):
        # `ai` mode's words are the model's; a sheet there would contradict the
        # plan's own stamp. Refused before any endpoint call - this test would
        # otherwise try to reach the default planner endpoint.
        self.assertRefused("--lyrics-mode", "ai", "--lyrics-file", SHEET_REL,
                           expect="refused with --lyrics-mode ai")

    def test_a_sheet_with_instrumental_mode_is_refused(self):
        # reached only on an INSTRUMENTAL genre: on a vocal genre the mode/genre
        # agreement check refuses this combination first, one rule earlier.
        self.assertRefused("--lyrics-mode", "instrumental", "--lyrics-file", SHEET_REL,
                           genre=INSTRUMENTAL_GENRE,
                           expect="refused with --lyrics-mode instrumental")

    def test_a_sheet_on_an_instrumental_genre_is_refused(self):
        self.assertRefused("--lyrics-file", SHEET_REL, genre=INSTRUMENTAL_GENRE,
                           expect="is an instrumental genre")


class TheDeployedCopyIsNotStale(unittest.TestCase):
    """The CronJob mounts a COPY of the planner; a stale copy is a dead flag."""

    def test_the_chart_payload_planner_accepts_lyrics_file(self):
        chart = pathlib.Path(os.environ.get("MINING_K8S",
                                            str(REPO.parent / "mining-k8s")))
        payload = chart / "helm/charts/music-pipeline/files/music/planner/planner.py"
        if not payload.is_file():
            self.skipTest(f"the chart payload is not at {payload}")
        text = payload.read_text(encoding="utf-8")
        for needle in ("--lyrics-file", "def load_sheet", "sheet_authorship_line"):
            self.assertTrue(needle in text,
                            f"{payload} is stale: it lacks {needle}. Run "
                            f"helm/charts/music-pipeline/sync-payload.sh (SRC=<lane>)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
