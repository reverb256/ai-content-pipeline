#!/usr/bin/env python3
"""Lyric-sheet measurement and section-tag recognition, held to the repo's own data.

Run: /usr/bin/python3 -m unittest music.tests.test_lyrics_gate_language
     (from the repo root; needs PyYAML, so the bare interpreter will not do)

WHY THIS TEST EXISTS (card t_53da62e5, 2026-10-16). The lyrics stage was
unreachable for the anisong family, and both causes were in
music/lyrics/lyrics.py — the single source of the gate's rules:

  1. unique_word_count() counted only [a-z']+, so a Japanese-script sheet — the
     script music/genres.yaml REQUIRES for anime-opening and anime-ending, and
     which forbids romaji — measured 0. Measured on the complete draft sheet
     music/lyrics/anime-opening/becoming before the fix:
         $ /usr/bin/python3 music/gates/gate_lyrics_original.py \\
               --lyrics-file music/lyrics/anime-opening/becoming/lyrics.suno.txt --strict
         FAIL gate_lyrics_original
           - only 0 unique words; 25 required
           - only 0 unique words (minimum 25)
           - unknown section tag [Final Chorus — KEY CHANGE UP ONE SEMITONE/TONE] (not a Suno metatag)
     No author could fix that; the sheet was complete and correct.

  2. The strict section check compared tags for exact membership in
     KNOWN_SECTIONS, which held no composed tag. anime-opening's template makes
     "[Final Chorus — KEY CHANGE UP ONE SEMITONE/TONE]" the genre's defining
     section, and lyrics.py claim runs validate_sheet(strict=True) — so the
     human-authorship claim, the artifact this whole stage protects, could never
     be recorded for an in-genre anisong sheet. Measured on a COPY of the track
     dir before the fix:
         $ /usr/bin/python3 music/lyrics/lyrics.py claim --track-dir <copy> --author probe
         FAIL: cannot claim — lyric sheet incomplete:
           - only 0 unique words (minimum 25)
           - unknown section tag [Final Chorus — KEY CHANGE UP ONE SEMITONE/TONE] (not a Suno metatag)

Both are now fixed: the token measure is script-aware, the section check is
qualifier-aware, and KNOWN_SECTIONS was re-synced to the templates. The checks
below are the ones that would have caught each defect, and the two mitigations
that keep the fixes from widening the gate by accident: an English sheet's count
must be bit-identical to the old pattern's, and EVERY tag in EVERY template must
be recognised (the invariant that was silently false for six tags across eleven
of the fourteen templates).
"""

import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
LYRICS_PY = REPO / "music" / "lyrics" / "lyrics.py"
PLANNER_PY = REPO / "music" / "planner" / "planner.py"
GATE_PY = REPO / "music" / "gates" / "gate_lyrics_original.py"
REGISTRY = REPO / "music" / "genres.yaml"

ANISONG_SHEET = REPO / "music" / "lyrics" / "anime-opening" / "becoming" / "lyrics.suno.txt"
ANISONG_DIR = REPO / "music" / "lyrics" / "anime-opening" / "becoming"

# The three tracks that carry a recorded human claim, all English script. Their
# counts are the control group for the script-aware tokeniser.
ENGLISH_SHEETS = [
    REPO / "music" / "lyrics" / "chill-lounge" / "amber-hour" / "lyrics.suno.txt",
    REPO / "music" / "lyrics" / "trance" / "signal-before-dawn" / "lyrics.suno.txt",
    REPO / "music" / "lyrics" / "activist" / "what-runs-beneath" / "lyrics.suno.txt",
]

# The pattern as it stood before the fix, kept here verbatim to recompute the
# old number from the same text.
LEGACY_LATIN_RE = re.compile(r"[a-z']+")


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lyrics = _load(LYRICS_PY, "lyrics_under_test")
planner = _load(PLANNER_PY, "planner_under_test")


def _legacy_count(sections) -> int:
    words = set()
    for _, lines in sections:
        for line in lines:
            words.update(LEGACY_LATIN_RE.findall(line.lower()))
    return len(words)


class TemplateTagCorpus(unittest.TestCase):
    """Every [tag] a genre's template mandates must be a tag the writer may use."""

    def test_every_registry_genre_tag_is_known(self):
        genres = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["genres"]
        seen = 0
        unknown = []
        for genre in sorted(genres):
            for tag in planner.load_template(genre)["structure"]:
                seen += 1
                if not lyrics.is_known_section(tag):
                    unknown.append((genre, tag))
        self.assertGreater(seen, 50, "the scan found almost no template tags")
        self.assertEqual(
            unknown, [],
            "template section tags the strict check would reject, so 'claim' "
            f"could not record a claim for that sheet: {unknown}")


class ScriptAwareTokenMeasure(unittest.TestCase):
    def test_english_counts_are_bit_identical_to_the_legacy_pattern(self):
        for sheet in ENGLISH_SHEETS:
            sections = lyrics.parse_sections(sheet.read_text(encoding="utf-8"))
            with self.subTest(sheet=sheet.name):
                self.assertEqual(lyrics.unique_word_count(sections),
                                 _legacy_count(sections))
                self.assertGreaterEqual(lyrics.unique_word_count(sections),
                                        lyrics.MIN_UNIQUE_WORDS)

    def test_japanese_sheet_is_measured_not_zeroed(self):
        sections = lyrics.parse_sections(ANISONG_SHEET.read_text(encoding="utf-8"))
        self.assertEqual(len(sections), 10, "the anisong structure has 10 sections")
        self.assertGreaterEqual(lyrics.unique_word_count(sections),
                                lyrics.MIN_UNIQUE_WORDS,
                                "a kana/kanji sheet must clear the floor")


class QualifiedSectionTags(unittest.TestCase):
    KEY_CHANGE = "Final Chorus — KEY CHANGE UP ONE SEMITONE/TONE"

    def test_the_signature_tag_is_known(self):
        self.assertTrue(lyrics.is_known_section(self.KEY_CHANGE))
        self.assertTrue(lyrics.is_known_section("Final Chorus — KEY LIFT"))
        self.assertTrue(lyrics.is_known_section("Instrumental Break"))
        self.assertTrue(lyrics.is_known_section("Chorus"))

    def test_junk_is_still_unknown(self):
        for junk in ("Sausage", "Mic Drop Into Space", "(untagged)"):
            with self.subTest(tag=junk):
                self.assertFalse(lyrics.is_known_section(junk))

    def test_strict_validation_accepts_a_sheet_built_on_the_signature_tag(self):
        sheet = f"[Bridge]\n{chr(12371)}{chr(12371)}で息を吐く\n\n[{self.KEY_CHANGE}]\n夜を追い越して\n"
        problems = lyrics.validate_sheet(lyrics.parse_sections(sheet), strict=True)
        self.assertEqual([p for p in problems if "unknown section tag" in p], [])


class GateOnTheCommittedAnisongSheet(unittest.TestCase):
    """The artifact the generate stage is gated on, run through the real gate."""

    def test_sheet_level_checks_pass(self):
        proc = subprocess.run(
            [sys.executable, str(GATE_PY), "--lyrics-file", str(ANISONG_SHEET),
             "--strict"], capture_output=True, text=True, cwd=REPO)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("unique words : ", proc.stdout)

    def test_track_gate_refuses_it_only_for_the_missing_human_claim(self):
        """A draft must fail on authorship and on nothing else."""
        proc = subprocess.run(
            [sys.executable, str(GATE_PY), "--track-dir", str(ANISONG_DIR)],
            capture_output=True, text=True, cwd=REPO)
        self.assertEqual(proc.returncode, 1)
        reasons = "\n".join(
            ln for ln in (proc.stdout + proc.stderr).splitlines() if ln.strip())
        for authorship_reason in ("authorship.status", "human author",
                                  "undated", "ai_assist", "sha256"):
            self.assertIn(authorship_reason, reasons)
        for unrelated in ("unique words", "unknown section tag", "placeholder"):
            self.assertNotIn(unrelated, reasons,
                             f"the draft sheet is being refused for {unrelated!r}, "
                             "which is a sheet defect, not a missing claim")

    def test_claim_records_over_a_copy_and_leaves_the_real_dir_alone(self):
        real_manifest = (ANISONG_DIR / "manifest.json").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            copy = pathlib.Path(tmp) / "becoming"
            shutil.copytree(ANISONG_DIR, copy)
            proc = subprocess.run(
                [sys.executable, str(LYRICS_PY), "claim", "--track-dir", str(copy),
                 "--author", "regression-probe"], capture_output=True, text=True,
                cwd=REPO)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            manifest = json.loads((copy / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["authorship"]["status"], "human-original")
            self.assertTrue((copy / "lyrics.txt").is_file())
            digest = hashlib.sha256(
                (copy / "lyrics.suno.txt").read_bytes()).hexdigest()
            self.assertEqual(manifest["files"]["lyrics.suno.txt"]["sha256"], digest)
        self.assertEqual((ANISONG_DIR / "manifest.json").read_bytes(), real_manifest,
                         "the probe wrote to the real track dir")
        self.assertFalse((ANISONG_DIR / "lyrics.txt").exists(),
                         "a claim leaked into the real (unclaimed) track dir")


if __name__ == "__main__":
    unittest.main(verbosity=2)
