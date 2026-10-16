#!/usr/bin/env python3
"""music/test_stage_state.py — the resume-stage rule (card t_6599927d).

REGRESSION UNDER TEST
---------------------
`music/oracle.py` wrote `stage: brief` into every card body, so a re-emitted
card re-entered the brief stage for a genre whose brief was already on disk
(measured 2026-10-16: all 14 genres; 13 cards of the 14:05 wave). The rule that
replaces it — `music/stage_state.py::resume_stage` — must:

  1. start at `brief` when the genre has no brief artifact,
  2. start at `genre-select` when the genre's brief artifact exists (either
     `music/briefs/<genre>.md` or `music/briefs/<genre>/<slug>/brief.md`),
  3. NEVER skip a stage it cannot prove — a genre with a brief AND a lyric sheet
     still resumes at `genre-select`, because `genre-select` declares no proof,
  4. take the stage ORDER from the file that declares it (stages.yaml), so a
     reordered or extended stage list moves the answer with it,
  5. fail loud (StageStateError) rather than fall back to a hard-coded stage.

Run:  /usr/bin/python3 music/test_stage_state.py
Exit: 0 = all pass, 1 = failure.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MUSIC_DIR = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location("stage_state", MUSIC_DIR / "stage_state.py")
if _spec is None or _spec.loader is None:  # pragma: no cover
    raise ImportError(f"cannot load {MUSIC_DIR / 'stage_state.py'}")
stage_state = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stage_state)

ORDER = ["brief", "genre-select", "lyrics", "generate"]


def stage_map(order: list[str], gates: tuple[str, ...] = ()) -> str:
    """A stages.yaml declaring `order`, with `gates` flagged human_gate."""
    lines = ["version: 1", "stages:"]
    for stage in order:
        lines.append(f"  - stage: {stage}")
        if stage in gates:
            lines.append("    human_gate: true")
    return "\n".join(lines) + "\n"


def fixture(files: tuple[str, ...] = (), order: list[str] | None = None,
            gates: tuple[str, ...] = ()) -> Path:
    """A throwaway repo holding `files` and a stage map declaring `order`."""
    root = Path(tempfile.mkdtemp(prefix="stage-state-test."))
    (root / "music").mkdir(parents=True, exist_ok=True)
    (root / "music" / "stages.yaml").write_text(
        stage_map(order or ORDER, gates), encoding="utf-8")
    for rel in files:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
    return root


def resolve(repo: Path, genre: str) -> tuple[str, dict]:
    """Call the rule against the fixture's own declared stage map."""
    return stage_state.resume_stage(repo, genre, stages_yaml=repo / "music" / "stages.yaml")


class ResumeStageTest(unittest.TestCase):

    def test_no_artifact_starts_at_brief(self):
        stage, ev = resolve(fixture(), "chill-lounge")
        self.assertEqual(stage, "brief")
        self.assertEqual(ev["proved"], {})
        self.assertEqual(ev["unproved"], "brief")

    def test_genre_keyed_brief_artifact_starts_at_genre_select(self):
        stage, ev = resolve(fixture(("music/briefs/chill-lounge.md",)), "chill-lounge")
        self.assertEqual(stage, "genre-select", ev)
        self.assertEqual(ev["proved"]["brief"], ["music/briefs/chill-lounge.md"])

    def test_subdir_brief_artifact_starts_at_genre_select(self):
        """The other half of the genre-keyed convention: briefs/<genre>/<slug>/brief.md."""
        repo = fixture(("music/briefs/trance/signal-before-dawn/brief.md",))
        stage, ev = resolve(repo, "trance")
        self.assertEqual(stage, "genre-select", ev)
        self.assertEqual(ev["proved"]["brief"],
                         ["music/briefs/trance/signal-before-dawn/brief.md"])

    def test_another_genres_brief_does_not_serve_this_genre(self):
        repo = fixture(("music/briefs/trance.md",))
        stage, ev = resolve(repo, "chill-lounge")
        self.assertEqual(stage, "brief", "briefs are keyed by genre — no cross-genre credit")
        self.assertEqual(ev["proved"], {})

    def test_never_skips_a_stage_with_no_declared_proof(self):
        """brief AND lyrics proved, but genre-select proves nothing -> stop there."""
        repo = fixture(("music/briefs/chill-lounge.md",
                        "music/lyrics/chill-lounge/amber-hour/lyrics.suno.txt"))
        stage, ev = resolve(repo, "chill-lounge")
        self.assertEqual(stage, "genre-select", ev)
        self.assertEqual(sorted(ev["proved"]), ["brief", "lyrics"])

    def test_lyric_sheet_is_the_proof_not_the_directory(self):
        repo = fixture(("music/lyrics/chill-lounge/amber-hour/notes.md",))
        stage, ev = resolve(repo, "chill-lounge")
        self.assertEqual(stage, "brief", ev)
        self.assertEqual(ev["proved"], {})

    def test_order_comes_from_the_declared_stage_list(self):
        """The walk follows the DECLARED order — no stage list is carried here.

        `generate` declares no proof, so a stage map that puts it first moves the
        resume point to `generate`, where the lane's own order answers
        `genre-select` for the same artifact set.
        """
        files = ("music/briefs/chill-lounge.md",
                 "music/lyrics/chill-lounge/amber-hour/lyrics.suno.txt")
        reordered = fixture(files, order=["generate", "brief", "genre-select", "lyrics"])
        stage, ev = resolve(reordered, "chill-lounge")
        self.assertEqual(ev["order"], ["generate", "brief", "genre-select", "lyrics"])
        self.assertEqual(stage, "generate", ev)

        lane_order = fixture(files, order=ORDER)
        stage_lane, _ = resolve(lane_order, "chill-lounge")
        self.assertEqual(stage_lane, "genre-select")

    def test_stage_map_path_is_reported(self):
        repo = fixture()
        _, ev = resolve(repo, "chill-lounge")
        self.assertEqual(ev["stages_yaml"], str(repo / "music" / "stages.yaml"))

    def test_a_delivered_chain_stops_at_the_human_gate(self):
        """A gate declares no proof, so a fully delivered chain stops there."""
        repo = fixture(("music/briefs/chill-lounge.md",
                        "music/lyrics/chill-lounge/amber-hour/lyrics.suno.txt"),
                       order=["brief", "lyrics", "human-approval"],
                       gates=("human-approval",))
        stage, ev = resolve(repo, "chill-lounge")
        self.assertEqual(stage, "human-approval")
        self.assertEqual(ev["unproved"], "human-approval")
        self.assertEqual(ev["gates"], ["human-approval"])
        self.assertFalse(ev["chain_complete"])
        note = stage_state.resume_note(stage, ev)
        self.assertIn("human gate", note)
        self.assertNotIn("stage: ", note)

    def test_a_chain_with_no_declared_gate_resumes_at_the_terminal_stage(self):
        repo = fixture(("music/briefs/chill-lounge.md",
                        "music/lyrics/chill-lounge/amber-hour/lyrics.suno.txt"),
                       order=["brief", "lyrics"])
        stage, ev = resolve(repo, "chill-lounge")
        self.assertEqual(stage, "lyrics")
        self.assertTrue(ev["chain_complete"])
        self.assertIsNone(ev["unproved"])
        self.assertIn("terminal stage", stage_state.resume_note(stage, ev))

    def test_empty_or_missing_stage_map_fails_loud(self):
        empty = fixture()
        (empty / "music" / "stages.yaml").write_text("version: 1\nstages: []\n", encoding="utf-8")
        with self.assertRaises(stage_state.StageStateError):
            resolve(empty, "chill-lounge")
        missing = fixture()
        (missing / "music" / "stages.yaml").unlink()
        with self.assertRaises(stage_state.StageStateError):
            resolve(missing, "chill-lounge")

    def test_bad_genre_name_fails_loud(self):
        repo = fixture()
        for bad in ("", "a/b", " chill-lounge", "chill lounge "):
            with self.assertRaises(stage_state.StageStateError, msg=bad):
                resolve(repo, bad)


class NoteTest(unittest.TestCase):

    def test_note_names_the_delivered_artifact_and_carries_no_second_marker(self):
        repo = fixture(("music/briefs/chill-lounge.md",))
        stage, ev = resolve(repo, "chill-lounge")
        note = stage_state.resume_note(stage, ev)
        self.assertIn("music/briefs/chill-lounge.md", note)
        self.assertIn("genre-select", note)
        self.assertIn("t_6599927d", note)
        # A card body must carry exactly ONE `stage: <x>` marker, the resume one —
        # the driver takes the LAST match in the whole card (t_92a09bdc).
        self.assertNotIn("stage: ", note)

    def test_note_for_an_unstarted_chain(self):
        stage, ev = resolve(fixture(), "fresh-genre")
        note = stage_state.resume_note(stage, ev)
        self.assertIn("brief", note)
        self.assertNotIn("stage: ", note)


class LiveLaneTest(unittest.TestCase):
    """The rule against the real lane: the incident class must stay closed."""

    def test_real_stage_map_declares_the_order_this_rule_walks(self):
        order = stage_state.load_stage_order()
        self.assertEqual(order[0], "brief")
        self.assertIn("genre-select", order)
        self.assertIn("track", order)
        self.assertEqual(len(order), len(set(order)), "a stage is declared twice")
        self.assertEqual(stage_state.human_gates(), {"human-approval", "escalate"})

    def test_real_genres_with_a_brief_do_not_resume_at_brief(self):
        """The incident, asserted against the live lane: every delivered brief
        must move its genre's resume point off `brief`."""
        repo = stage_state.REPO
        briefs = sorted(repo.glob("music/briefs/*.md")) + \
            sorted(repo.glob("music/briefs/*/*/brief.md"))
        genres = sorted({p.relative_to(repo / "music/briefs").parts[0].removesuffix(".md")
                         for p in briefs})
        self.assertTrue(genres, "no brief artifact found — this test cannot judge anything")
        for genre in genres:
            with self.subTest(genre=genre):
                stage, ev = stage_state.resume_stage(repo, genre)
                self.assertNotEqual(
                    stage, "brief",
                    f"{genre} has a brief on disk but would restart the brief stage")
                self.assertIn("brief", ev["proved"])


if __name__ == "__main__":
    if "yaml" not in sys.modules:
        try:
            import yaml  # noqa: F401
        except ModuleNotFoundError:
            raise SystemExit("this test needs PyYAML — run it with /usr/bin/python3")
    unittest.main(verbosity=2)
