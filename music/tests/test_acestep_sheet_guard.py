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

THE COMMITTED CORPUS IS TWO CONTROLS, MEASURED (card t_450e7f39, 2026-10-16)
---------------------------------------------------------------------------
The corpus check below first assumed that EVERY committed sheet is made of
singable lines, and used the whole `music/lyrics/*/*/lyrics.suno.txt` glob as the
negative control for the widened rule. Three direction-only sheets landed the
same day (commit ce845f6, card t_9682a610) for genres whose own template says the
lyrics box stays empty — so every line in them IS direction text, the gate flags
all of them, and it is right to. The glob reported

    FAILED (failures=3)   in   music.tests.test_acestep_sheet_guard

and `music/gates/check_gate_lyrics_original.sh` reported "BROKEN: 1 of 14
check(s) misbehaved" for sheets that are correct.

MEASURED 2026-10-16 — 9 committed sheets, and the sheet's own `# genre:` header
equals the directory it sits in for 9 of 9:

    vocal        (>=1 sung line, 0 placeholder problems each)         6 sheets
      activist/what-runs-beneath, anime-ending/reflections,
      anime-opening/becoming, anime-opening/opening-theme,
      chill-lounge/amber-hour, trance/signal-before-dawn
    direction-only (0 sung lines, every line flagged as direction)    3 sheets
      commentary-beds/warm-jazz-bed (3 lines), elemental-fire/molten-blaze
      (7), sentimental-piano/first-snow (7)

So the corpus is split by the STATE the shipped rule measures, one control each:

  * a sheet WITH a sung line is the NEGATIVE control: no line of it may be read
    as direction text (a rule that widens too far, or that flags everything);
  * a sheet with NO sung line is the POSITIVE control: every line of it must be
    read as direction text, and its genre's template must declare the empty
    lyrics box — that is what makes it a finished instrumental sheet rather than
    a scaffold.

WHY THE SPLIT IS NOT KEYED ON THE GENRE MARKER. The card that filed this
(t_450e7f39) offered "skip the sheets whose genre template leaves the lyrics box
empty" and "assert the placeholder rule fires on all of them". The marker cannot
carry that decision: music/prompts/chill-lounge.md:14 says "Leave the **lyrics
box empty**", music/planner/planner.py:is_instrumental_template reads
chill-lounge as instrumental (it is one of the census of 8 that
music/tests/test_planner.py pins), and yet music/lyrics/chill-lounge/amber-hour
is a finished, human-claimed VOCAL sheet that the gate's own acceptance matrix
requires to PASS (music/gates/check_gate_suite.sh:354). The marker is therefore a
ONE-WAY condition — a direction-only sheet implies an instrumental genre, never
the converse — and the sheet's own measured state is what selects its control.
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


# --- the committed corpus (card t_450e7f39, 2026-10-16) ---------------------
# The sheets this repo has committed, the genre each one declares in its own
# header, and the predicate that decides whether a genre's template leaves the
# lyrics box empty. The predicate is the SHIPPED one: the same predicate
# music/planner/planner.py gates `--lyrics-mode` on, which
# music/tests/test_planner.py pins against the CDP rail's copy
# (music/suno-gen.py:is_instrumental_template) over every genre. No genre list
# lives in this file — the genre comes from the sheet, the marker from the
# genre's own template.
PLANNER = REPO / "music" / "planner" / "planner.py"
planner = _load(PLANNER, "planner_under_test")

SHEET_GLOB = "music/lyrics/*/*/lyrics.suno.txt"
GENRE_HEADER_RE = re.compile(r"^#\s*genre:\s*(\S+)\s*$", re.M)


def committed_sheets() -> list:
    return sorted(REPO.glob(SHEET_GLOB))


def sheet_genre(sheet: pathlib.Path) -> str:
    """The genre the sheet declares about itself (`# genre:` in its header).

    music/lyrics/lyrics.py scaffold writes that line, and parse_sections skips
    `#` lines, so it is never lyric body. The directory is NOT read as a
    fallback: a sheet that does not say what genre it is cannot be asked the
    right question about its template (the corpus test asserts the two agree).
    """
    m = GENRE_HEADER_RE.search(sheet.read_text(encoding="utf-8"))
    if m is None:
        raise AssertionError(
            f"{sheet.relative_to(REPO)} has no '# genre: <genre>' header line")
    return m.group(1)


def sheet_problems(sheet: pathlib.Path) -> list:
    sections = lyrics.parse_sections(sheet.read_text(encoding="utf-8"))
    return lyrics.validate_sheet(sections, strict=False)


def is_direction_only(sheet: pathlib.Path) -> bool:
    """True when the shipped rule finds no sung line anywhere in the sheet."""
    sections = lyrics.parse_sections(sheet.read_text(encoding="utf-8"))
    return not any(lyrics.sung_lines(lines) for _, lines in sections)


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


class TheCommittedCorpusIsTwoControls(unittest.TestCase):
    """Card t_450e7f39: the committed sheets pin BOTH halves of the widened rule.

    The first version of this check used the whole `music/lyrics/*/*/lyrics.suno.txt`
    glob as the negative control, i.e. it assumed every committed sheet is made of
    singable lines. Three direction-only sheets landed (commit ce845f6, card
    t_9682a610) for genres whose template says the lyrics box stays empty, so every
    line in them IS direction text and the gate flags all of them — correctly. The
    glob then reported FAILED (failures=3) and the lyrics stage's own runner read
    "BROKEN: 1 of 14 check(s) misbehaved" for sheets that are right.

    The split is by the state the shipped rule MEASURES, not by genre. The module
    docstring records why the genre marker cannot be the key: chill-lounge declares
    the empty lyrics box and still ships a finished human-claimed vocal sheet.
    """

    def test_every_committed_sheet_declares_the_genre_it_sits_in(self):
        """The genre asked about the template must be the sheet's own genre."""
        sheets = committed_sheets()
        self.assertGreaterEqual(len(sheets), 3, "no committed sheets found")
        for sheet in sheets:
            with self.subTest(sheet=str(sheet.relative_to(REPO))):
                self.assertEqual(
                    sheet_genre(sheet), sheet.parent.parent.name,
                    "the sheet's own '# genre:' header and the directory it sits "
                    "in disagree: one of them is wrong, and every check below asks "
                    "the genre's template a question about this sheet")

    def test_the_committed_sheets_still_pass_the_gate(self):
        """A sheet WITH a sung line: the negative control. Nothing is direction."""
        sheets = [s for s in committed_sheets() if not is_direction_only(s)]
        self.assertGreaterEqual(len(sheets), 1,
                                "no committed sheet carries a sung line any more, "
                                "so the negative control is empty (see "
                                "test_the_corpus_holds_both_controls)")
        for sheet in sheets:
            problems = sheet_problems(sheet)
            with self.subTest(sheet=str(sheet.relative_to(REPO))):
                self.assertEqual(
                    [p for p in problems if "placeholder" in p], [],
                    "a human-authored sheet now fails the gate. If the flagged line "
                    "is the CONTINUATION of a wrapped direction, that is the "
                    "t_bc6a0c00 bug (a continuation line the rule read as a lyric), "
                    "not a defect in the sheet.")

    def test_a_direction_only_sheet_is_flagged_line_for_line(self):
        """A sheet with NO sung line: the positive control. Every line is direction.

        Two ways to fail here, both real:
          * the genre's template does not declare an empty lyrics box, so the sheet
            is a scaffold (or a genre whose template lost its marker) — a sheet
            nobody finished, which is not evidence about the widened rule;
          * a line of the sheet is NOT read as direction text. That is the t_bc6a0c00
            bug (a direction that WRAPS: its continuation line opens no parenthesis,
            so the rule saw it as a lyric). No committed sheet wraps a direction yet
            — measured 2026-10-16 — so the template-sheet tests above are what cover
            the wrapped case; this one covers every line on the real beds.
        """
        sheets = [s for s in committed_sheets() if is_direction_only(s)]
        self.assertGreaterEqual(len(sheets), 1,
                                "no direction-only sheet is committed any more, so "
                                "this positive control is gone (see "
                                "test_the_corpus_holds_both_controls)")
        for sheet in sheets:
            rel = str(sheet.relative_to(REPO))
            sections = lyrics.parse_sections(sheet.read_text(encoding="utf-8"))
            body = [ln.strip() for _, lines in sections for ln in lines if ln.strip()]
            genre = sheet_genre(sheet)
            problems = sheet_problems(sheet)
            flagged = [p for p in problems if "placeholder" in p]
            with self.subTest(sheet=rel):
                self.assertTrue(
                    planner.is_instrumental_template(genre),
                    f"{rel} carries no sung line, and '{genre}' is not an "
                    f"instrumental genre: music/prompts/{genre}.md does not say the "
                    "lyrics box stays empty. A sheet like this is a scaffold — a "
                    "half-written sheet, not a control: finish it, or re-point this "
                    "test if the state is deliberate")
                self.assertEqual(
                    len(flagged), len(body),
                    f"{rel}: {len(body)} line(s) in the sheet, {len(flagged)} read as "
                    "direction text — a direction line the rule did not see:\n"
                    + "\n".join(problems))
                seen = "\n".join(flagged)
                for line in body:
                    self.assertIn(line[:60], seen,
                                  f"{rel}: only a direction line can be here, and "
                                  f"this one is not flagged: {line!r}")

    def test_the_corpus_holds_both_controls(self):
        """Both controls must stay populated, or the rule can collapse unnoticed.

        A rule that flagged every line would leave the negative control EMPTY —
        every sheet would look direction-only and test_the_committed_sheets_still_
        pass_the_gate would pass over an empty list. So the census is asserted, and
        printed when it fails.
        """
        sheets = committed_sheets()
        vocal = [s for s in sheets if not is_direction_only(s)]
        beds = [s for s in sheets if is_direction_only(s)]
        census = "\n".join(
            [f"  vocal ({len(vocal)}):"] + [f"    {s.relative_to(REPO)}" for s in vocal]
            + [f"  direction-only ({len(beds)}):"]
            + [f"    {s.relative_to(REPO)}" for s in beds])
        self.assertEqual(len(vocal) + len(beds), len(sheets),
                         "a sheet was classified into two states at once")
        self.assertGreaterEqual(len(vocal), 1,
                                "no committed sheet carries a sung line any more: a "
                                "rule that flags every line empties the negative "
                                "control instead of failing it\n" + census)
        self.assertGreaterEqual(len(beds), 1,
                                "no direction-only sheet is committed any more: the "
                                "positive control (every direction line is seen) is "
                                "gone\n" + census)


if __name__ == "__main__":
    unittest.main(verbosity=2)
