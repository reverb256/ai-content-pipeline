#!/usr/bin/env python3
"""The renderer must refuse a DRAFT plan before it touches the network.

WHY THIS TEST EXISTS (card t_a14e5d52, 2026-10-16). The brief queue was extended
with draft entries, which is safe ONLY because acestep_plan.py refuses a scaffold
and music-pipeline-render records that refusal as a `.refused` marker instead of
retrying. Measured on the deployed copy before this test existed: its check_lyrics
refused only lyrics that were COMPLETELY empty, and a scaffold is never completely
empty - it carries the section tags - so a queued draft went straight to the
sunolocal engine, where the "lyrics" it would have sung are the template's craft
notes. Nothing caught that: the guard's own caller assumed it worked.

Run: /usr/bin/python3 -m unittest music.test_acestep_guard
     (from the repo root; the sibling suite for the tag sheet itself is
      music.tests.test_acestep_sheet_guard, which reads the template at run time)
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "music" / "scripts" / "acestep_plan.py"

spec = importlib.util.spec_from_file_location("acestep_plan", SCRIPT)
assert spec and spec.loader, f"cannot load {SCRIPT}"
acestep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acestep)


# A scaffold, as planner.py --lyrics-mode draft writes one: tags plus the
# template's per-section guidance in parentheses, no lyrics anywhere. Two of the
# direction notes WRAP onto a second line, which is the shape that defeated the
# first version of the section test (card t_bc6a0c00).
SCAFFOLD = """# brief: an anison ballad for the close of the arc
# provenance: human-original — write every sung line yourself

[Intro]
(Japanese: 2 lines, sparse. Piano alone, one string
sustain. The hook melody arrives in fragment)

[Verse 1]
(Japanese: 4-8 lines. Intimate, first-person. The memory or the person the
episode left behind)

[Outro]
(Japanese: 1-2 lines. The final line hangs on a single held piano note)
"""

REAL = """[Intro]
Silent snow on the window glass

[Verse 1]
I kept the light on
"""

BARE_TAGS = "[Intro]\n\n[Verse 1]\n\n"


def plan(lyrics):
    return {"title": "t", "caption": "c", "bpm": 92, "key": "C minor",
            "duration": 300, "timesignature": "4", "language": "ja",
            "lyrics": lyrics}


class TestSingableLines(unittest.TestCase):
    def test_scaffold_section_has_no_singable_lines(self):
        self.assertEqual(acestep.singable_lines(
            "(Japanese: 2 lines, sparse. Piano alone, one string\n"
            "sustain. The hook melody arrives in fragment)"), [])

    def test_wrapped_direction_does_not_leak_into_the_lyrics(self):
        # the continuation line "wraps)" does not start with "(" and the
        # unwrapped test counted it as a lyric (t_bc6a0c00)
        self.assertEqual(acestep.singable_lines("(a direction that\nwraps)"), [])

    def test_real_lines_survive(self):
        self.assertEqual(acestep.singable_lines("I kept the light on\n\nI waited"),
                         ["I kept the light on", "I waited"])


class TestCheckLyrics(unittest.TestCase):
    def assertRefused(self, lyrics, allow_empty=False):
        with self.assertRaises(SystemExit):
            acestep.check_lyrics(plan(lyrics), allow_empty)

    def test_draft_scaffold_is_refused(self):
        self.assertRefused(SCAFFOLD)

    def test_bare_tags_are_refused(self):
        self.assertRefused(BARE_TAGS)

    def test_no_section_headers_is_refused(self):
        self.assertRefused("words with no tags at all\n")

    def test_empty_lyrics_is_refused(self):
        self.assertRefused("")

    def test_real_lyrics_pass(self):
        acestep.check_lyrics(plan(REAL), False)   # must not raise

    def test_allow_empty_overrides_every_refusal(self):
        for lyrics in (SCAFFOLD, BARE_TAGS, "", "no tags\n"):
            acestep.check_lyrics(plan(lyrics), True)   # must not raise


class TestRefusalContract(unittest.TestCase):
    """The CronJob's side of the contract: rc == REFUSED_EXIT (4), and no network call.

    templates/cronjob-render.yaml calls this script WITHOUT --allow-empty and
    records the refusal (`.refused`, with the plan's fingerprint) when the exit
    code is that script's own REFUSED_EXIT = 4 - rc 1 is an OPERATIONAL failure
    and writes no marker, so the next run retries it (card t_69cab80b, which
    raised the refusal from 1 to 4 after a network blip was recorded as "a human
    must edit the sheet"). SUNOLOCAL_HOST points at a closed port, so a plan that
    got PAST the guard fails at submit with a different message - which is how
    these tests tell "the guard refused it" from "the guard let it through".
    """

    def run_script(self, lyrics, *extra):
        d = Path(tempfile.mkdtemp())
        p = d / "plan.json"
        p.write_text(json.dumps(plan(lyrics)), encoding="utf-8")
        env = dict(os.environ, SUNOLOCAL_HOST="http://127.0.0.1:9")
        proc = subprocess.run([sys.executable, str(SCRIPT), str(p), "--name", "t", *extra],
                              capture_output=True, text=True, env=env, timeout=60)
        return proc.returncode, proc.stdout + proc.stderr

    def test_scaffold_exits_4_with_the_draft_message(self):
        rc, out = self.run_script(SCAFFOLD)
        self.assertEqual(rc, acestep.REFUSED_EXIT)
        self.assertIn("section(s) have no lyrics", out)
        self.assertIn("DRAFT plan", out)
        self.assertNotIn("Failed to submit", out)   # nothing reached the network

    def test_allow_empty_reaches_the_network_instead(self):
        rc, out = self.run_script(SCAFFOLD, "--allow-empty")
        self.assertNotIn("have no lyrics", out)
        self.assertIn("Failed to submit", out)

    def test_real_lyrics_reach_the_network(self):
        rc, out = self.run_script(REAL)
        self.assertNotIn("have no lyrics", out)
        self.assertIn("Failed to submit", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
