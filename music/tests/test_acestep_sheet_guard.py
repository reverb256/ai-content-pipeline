#!/usr/bin/env python3
"""The two lyric guards must refuse the epic-orchestral-boss tag sheet.

Run: /usr/bin/python3 -m unittest music.tests.test_acestep_sheet_guard
     (from the repo root; the sibling suites are music.test_acestep_guard and
      music.tests.test_lyrics_gate_language)

WHY THIS TEST EXISTS (card t_bc6a0c00, 2026-10-16)
--------------------------------------------------
Genre templates ship a tag sheet: the section tags with the composer's direction
for each one in parentheses, and no lyrics. Rendering that sheet unedited is the
failure both guards exist to prevent — the engine sings the craft notes.

A direction WRAPS. `[Intro]` on the epic-orchestral-boss sheet reads

    [Intro]
    (sub-drone, distant metallic echoes, whispered choir breaths,
    heartbeat pulse)

The continuation line, `heartbeat pulse)`, does not start with "(" — so every rule
that asked "does this line OPEN a parenthesis?" read it as a lyric:

  * the renderer's section-emptiness test counted 5 of the 8 sections as full
    and rendered the sheet (music/scripts/acestep_plan.py, fixed in the lane by
    bdcef9e and in the chart payload by e9d27f5);
  * the gate's placeholder test rejected a line only when it began AND ended
    with a parenthesis, so it reported 3 problems instead of 14 and the sheet
    cleared `gate_lyrics_original` (music/lyrics/lyrics.py, the fix this card
    carries).

The sheet is read from the template at run time, not pasted here, so the test
follows the genre's own data. The structure assertions below are the tripwire:
if the template's sheet changes shape, this test says so instead of passing on a
sheet nobody measured.

EVERY NUMBER IN THIS FILE WAS MEASURED on the sheet it reads:
    8 sections, 14 direction lines, 0 singable lines, 71 unique words (54 of
    them carried by direction lines under the old rule).
"""

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

TEMPLATE = REPO / "music" / "prompts" / "epic-orchestral-boss.md"
RENDERER = REPO / "music" / "scripts" / "acestep_plan.py"
LYRICS_PY = REPO / "music" / "lyrics" / "lyrics.py"


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


acestep = _load(RENDERER, "acestep_plan_under_test")
lyrics = _load(LYRICS_PY, "lyrics_under_test")


def lyrics_block(template: pathlib.Path) -> str:
    """The genre's tag sheet: the first fenced block under '## Lyrics guidance'."""
    if not template.is_file():
        raise AssertionError(f"missing genre template {template}")
    text = template.read_text(encoding="utf-8")
    if "## Lyrics guidance" not in text:
        raise AssertionError(
            f"{template.name} lost its '## Lyrics guidance' heading: this test "
            "reads the tag sheet from there, so re-point it at the new heading")
    blocks = re.findall(r"```text\n(.*?)```", text.split("## Lyrics guidance", 1)[1],
                        re.S)
    if not blocks or "[Intro]" not in blocks[0]:
        raise AssertionError(
            f"the first fenced block under '## Lyrics guidance' in "
            f"{template.name} is not the tag sheet any more")
    return blocks[0]


SHEET = lyrics_block(TEMPLATE)

SECTION_RE = re.compile(r"^\[([^\]]+)\][ \t]*\n(.*?)(?=\n\[|\Z)", re.M | re.S)
SECTIONS = SECTION_RE.findall(SHEET)

# The genre's structure, as the template writes it (card t_2a798908 §8c: the
# boss form is three-act, and [Choir] carries the vocal).
EXPECTED_TAGS = ["Intro", "Choir", "Build", "Instrumental", "Choir",
                 "Breakdown", "Chorus", "Outro"]

CONTROLS = {
    # a one-line direction, never wrapped
    "single parenthetical": ("(the bloom)", []),
    # the card's own case: the paren opens on line 1 and closes on line 2
    "wrapped direction": ("(a direction that\nwraps)", []),
    # a real chant, as the template's rules ask the human to write it
    "real chant lines": ("Fortis, Astra, Dominus\nas-tra, do-mi-nus",
                         ["Fortis, Astra, Dominus", "as-tra, do-mi-nus"]),
    # DELIBERATE, and the conservative direction: a line that OPENS a direction
    # is direction text to its end, even with a remainder on the same line. The
    # guard then refuses the section and a human writes the line as a lyric —
    # loud and recoverable. The alternative (strip the span and count the
    # remainder) would let a scaffold through on a note that happens to share its
    # line with a stray word, which is the silent failure this guard prevents.
    "direction with an inline remainder": ("(direction) real lyric here", []),
}


def plan(lyrics_text: str, **over) -> dict:
    body = {"title": "epic-orchestral-boss", "caption": "c", "bpm": 150,
            "key": "C minor", "duration": 240, "timesignature": "4",
            "lyrics": lyrics_text}
    body.update(over)
    return body


class TheRealSheetIsWhatWeMeasured(unittest.TestCase):
    """The tripwire: the sheet's shape, pinned, so the rest is not vacuous."""

    def test_the_template_sheet_has_the_genres_eight_sections(self):
        self.assertEqual([tag for tag, _ in SECTIONS], EXPECTED_TAGS)
        self.assertGreaterEqual(len(SHEET.splitlines()), 20,
                                "the sheet is shorter than the measured one")

    def test_the_directions_really_do_wrap(self):
        """Without a wrapped direction this file tests nothing."""
        wrapped = [ln.strip() for _, content in SECTIONS
                   for ln in content.splitlines()
                   if ln.strip() and not ln.strip().startswith("(")]
        self.assertTrue(wrapped, "no continuation line found in the sheet")
        self.assertIn("heartbeat pulse)", wrapped)


class TheRendererRefusesEverySection(unittest.TestCase):
    """Card t_bc6a0c00, the required assertion: ALL sections report empty."""

    def test_no_section_has_a_singable_line(self):
        for tag, content in SECTIONS:
            with self.subTest(section=tag):
                self.assertEqual(acestep.singable_lines(content), [],
                                 f"[{tag}] 'sings' direction text")

    def test_check_lyrics_refuses_the_sheet(self):
        with self.assertRaises(SystemExit) as raised:
            acestep.check_lyrics(plan(SHEET), allow_empty=False)
        message = str(raised.exception)
        self.assertIn("8 section(s) have no lyrics", message)
        for tag in ("Intro", "Build", "Breakdown", "Chorus", "Outro"):
            # the five sections the unwrapped rule read as FULL
            self.assertIn(tag, message)

    def test_allow_empty_still_overrides(self):
        acestep.check_lyrics(plan(SHEET), allow_empty=True)   # must not raise


class TheDeployedRendererRefusesItEndToEnd(unittest.TestCase):
    """rc=4 is the contract cronjob-render.yaml records as `.refused`.

    Card t_69cab80b split the two codes: 1 is an operational failure (the rail
    must retry it, so it writes NO marker) and 4 is a refusal that needs a human
    (recorded with the plan's fingerprint, so an edit opens it again).
    """

    def test_the_script_exits_4_as_a_refusal_not_1_as_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "plan.json"
            p.write_text(json.dumps(plan(SHEET)), encoding="utf-8")
            env = dict(os.environ, SUNOLOCAL_HOST="http://127.0.0.1:9")
            proc = subprocess.run(
                [sys.executable, str(RENDERER), str(p), "--name", "epic"],
                capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(proc.returncode, 4, proc.stdout + proc.stderr)
        self.assertNotEqual(proc.returncode, 1,
                            "1 means the submit failed, and the rail would then "
                            "record a network blip as 'a human must edit the sheet'")
        self.assertIn("section(s) have no lyrics", proc.stdout + proc.stderr)
        self.assertNotIn("Failed to submit", proc.stdout + proc.stderr,
                         "the guard let the draft reach the network")


class TheGateRefusesItToo(unittest.TestCase):
    """The second hole on this card: music/lyrics/lyrics.py:validate_sheet."""

    def test_validate_sheet_flags_every_direction_line(self):
        sections = lyrics.parse_sections(SHEET)
        problems = lyrics.validate_sheet(sections, strict=False)
        placeholders = [p for p in problems if "placeholder guidance left in" in p]
        # 14 direction lines, none of them a lyric: measured 14, from 3 before
        # the fix (the three single-line directions only).
        self.assertEqual(len(placeholders), 14, "\n".join(problems))
        flagged = set()
        for p in placeholders:
            m = re.match(r"\[([^\]]+)\]", p)
            if m is None:
                self.fail(f"unparseable problem line: {p!r}")
                continue
            flagged.add(m.group(1))
        self.assertEqual(flagged, set(EXPECTED_TAGS),
                         "a section's direction text went unflagged")

    def test_no_section_records_a_singable_line(self):
        for tag, lines in lyrics.parse_sections(SHEET):
            with self.subTest(section=tag):
                self.assertEqual(lyrics.sung_lines(lines), [])

    def test_the_two_guards_agree_on_the_same_sheet(self):
        """Their drift is what let the sheet through: assert they cannot differ."""
        for tag, content in SECTIONS:
            lines = [ln for ln in content.splitlines() if ln.strip()]
            with self.subTest(section=tag):
                self.assertEqual(lyrics.sung_lines(lines),
                                 acestep.singable_lines("\n".join(lines)),
                                 f"the gate and the renderer disagree on [{tag}]")


class TheControlsStillBehave(unittest.TestCase):
    def test_singable_line_rules(self):
        for name, (content, expected) in CONTROLS.items():
            with self.subTest(case=name):
                self.assertEqual(acestep.singable_lines(content), expected)

    def test_a_chant_sheet_is_not_refused(self):
        """The fix must not widen the refusal to real lyrics."""
        chant = "[Intro]\nFortis, Astra, Dominus\n\n[Choir]\nas-tra, do-mi-nus\n"
        acestep.check_lyrics(plan(chant), allow_empty=False)   # must not raise
        problems = lyrics.validate_sheet(lyrics.parse_sections(chant), strict=False)
        self.assertEqual([p for p in problems if "placeholder" in p], [],
                         "a real chant line is being read as direction text")

    def test_a_single_parenthetical_section_is_still_refused(self):
        with self.assertRaises(SystemExit):
            acestep.check_lyrics(plan("[Intro]\n(the motif, alone)\n"), False)

    def test_the_committed_sheets_still_pass_the_gate(self):
        """The corpus is the negative control for the widened placeholder rule."""
        sheets = sorted(REPO.glob("music/lyrics/*/*/lyrics.suno.txt"))
        self.assertGreaterEqual(len(sheets), 3, "no committed sheets found")
        for sheet in sheets:
            sections = lyrics.parse_sections(sheet.read_text(encoding="utf-8"))
            problems = lyrics.validate_sheet(sections, strict=False)
            with self.subTest(sheet=str(sheet.relative_to(REPO))):
                self.assertEqual([p for p in problems if "placeholder" in p], [],
                                 "a human-authored sheet now fails the gate")


if __name__ == "__main__":
    unittest.main(verbosity=2)
