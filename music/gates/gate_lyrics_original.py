#!/usr/bin/env python3
"""gate_lyrics_original — PASS/FAIL gate for the lyrics stage.

Checks (architecture doc §5, row `gate_lyrics_original`):
  1. The lyric sheet exists and PARSES: real sections with real lines
     (we measure unique-word count and section structure — no grep).
  2. A human-authorship claim is recorded in the track manifest
     (named author, date, explicit AI-assist scope).
  3. The claim is bound to THIS text: the manifest's sha256 must match
     the lyric file on disk.
  4. The lyric text carries no marker of Suno's lyric generator
     ("Write with Suno", ReMi, provenance headers, known example
     outputs). See SUNO_FINGERPRINTS.md beside this gate.
  5. The claim asserts suno_generated_lyrics == False.

The gate EXECUTES the artifact: it parses the sheet, measures it, hashes
it, and compares against the manifest. A file that merely exists is not
evidence.

Usage:
  python3 music/gates/gate_lyrics_original.py --track-dir <lyrics track dir> [--strict]
  python3 music/gates/gate_lyrics_original.py --lyrics-file <file> [--strict]

Exit codes: 0 = PASS, 1 = FAIL (human-readable reasons on stderr), 2 = usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "music" / "lyrics"))

# The gate is the stage's validation logic — imported, never copied.
# (music/lyrics/lyrics.py is the single source of the parse/measure rules.)
from lyrics import (  # noqa: E402
    scan_suno_markers,
    parse_sections,
    unique_word_count,
    validate_sheet,
)

MIN_SECTIONS = 2
MIN_UNIQUE_WORDS = 25


def fail(msgs: list[str]) -> int:
    print("FAIL gate_lyrics_original", file=sys.stderr)
    for m in msgs:
        print(f"  - {m}", file=sys.stderr)
    return 1


def gate_track_dir(track_dir: Path, strict: bool) -> int:
    problems: list[str] = []

    manifest_path = track_dir / "manifest.json"
    lyrics_path = track_dir / "lyrics.suno.txt"
    if not manifest_path.is_file():
        return fail([f"no manifest.json in {track_dir} — "
                     "the human-authorship claim is the artifact this gate protects"])
    if not lyrics_path.is_file():
        return fail([f"no lyrics.suno.txt in {track_dir}"])

    import hashlib
    import json

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail([f"manifest.json is not valid JSON: {exc}"])

    # --- 1. Parse + measure the lyric sheet itself -----------------------
    raw = lyrics_path.read_text(encoding="utf-8")
    sections = parse_sections(raw)
    measured_words = unique_word_count(sections)
    if len(sections) < MIN_SECTIONS:
        problems.append(f"lyric sheet has {len(sections)} content section(s); "
                        f"{MIN_SECTIONS} required")
    if measured_words < MIN_UNIQUE_WORDS:
        problems.append(f"lyric sheet has {measured_words} unique words; "
                        f"{MIN_UNIQUE_WORDS} required")
    problems.extend(validate_sheet(sections, strict=strict))

    # --- 2. The human-authorship claim -----------------------------------
    auth = manifest.get("authorship")
    if not isinstance(auth, dict):
        return fail(problems + ["manifest has no authorship claim"])
    if auth.get("status") != "human-original":
        problems.append(f"authorship.status={auth.get('status')!r}; "
                        "expected 'human-original'")
    if not auth.get("authors"):
        problems.append("no named human author in authorship.authors")
    if not auth.get("written_at"):
        problems.append("authorship claim is undated")
    ai_scope = auth.get("ai_assist")
    if not ai_scope or not str(ai_scope).strip():
        problems.append("authorship.ai_assist is empty — the claim must state "
                        "what the AI did and did not do")
    if auth.get("suno_generated_lyrics") is not False:
        problems.append("authorship.suno_generated_lyrics must be False")

    # --- 3. Claim is bound to THIS text ----------------------------------
    files = manifest.get("files") or {}
    entry = files.get("lyrics.suno.txt")
    if not isinstance(entry, dict) or not entry.get("sha256"):
        problems.append("manifest.files['lyrics.suno.txt'] has no sha256 — "
                        "claim not recorded via 'lyrics.py claim'")
    else:
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if entry["sha256"] != digest:
            problems.append("manifest sha256 does not match lyrics.suno.txt — "
                            "the claim does not cover the text on disk")

    # --- 4. Suno-generator markers --------------------------------------
    markers = scan_suno_markers(raw)
    for marker, why in markers:
        problems.append(f"Suno-generated-lyric marker '{marker}' ({why})")

    if problems:
        return fail(problems)

    title = manifest.get("title", track_dir.name)
    authors = ", ".join(auth.get("authors", []))
    print("PASS gate_lyrics_original")
    print(f"  track        : {title} ({track_dir})")
    print(f"  sections     : {len(sections)}")
    print(f"  unique words : {measured_words}")
    print(f"  authorship   : {authors} @ {auth.get('written_at')}")
    print(f"  suno markers : none")
    return 0


def gate_lyrics_file(path: Path, strict: bool) -> int:
    """Bare-file mode: parse + measure + marker scan (no manifest).

    This mode exists so a reviewer can test ANY lyric sheet — e.g. a
    Suno-generated lyric — against the same executable rules. It cannot
    PASS a track (a pass requires the manifest claim); --lyrics-file is
    for interrogating text, --track-dir is for gating a track.
    """
    if not path.is_file():
        print(f"FAIL gate_lyrics_original: no such file {path}", file=sys.stderr)
        return 2
    raw = path.read_text(encoding="utf-8")
    problems: list[str] = []
    sections = parse_sections(raw)
    if len(sections) < MIN_SECTIONS:
        problems.append(f"lyric sheet has {len(sections)} content section(s); "
                        f"{MIN_SECTIONS} required")
    if unique_word_count(sections) < MIN_UNIQUE_WORDS:
        problems.append(f"only {unique_word_count(sections)} unique words; "
                        f"{MIN_UNIQUE_WORDS} required")
    problems.extend(validate_sheet(sections, strict=strict))
    for marker, why in scan_suno_markers(raw):
        problems.append(f"Suno-generated-lyric marker '{marker}' ({why})")
    if problems:
        return fail(problems)
    print("PASS gate_lyrics_original (sheet-level checks only — "
          "a track PASS requires --track-dir with a manifest claim)")
    print(f"  file         : {path}")
    print(f"  sections     : {len(sections)}")
    print(f"  unique words : {unique_word_count(sections)}")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_lyrics_original — lyrics-stage PASS/FAIL gate")
    parser.add_argument("--track-dir", default=None,
                        help="lyrics track directory (manifest + lyrics)")
    parser.add_argument("--lyrics-file", default=None,
                        help="bare lyric sheet to interrogate (cannot full-pass)")
    parser.add_argument("--strict", action="store_true",
                        help="also enforce known Suno section tags")
    args = parser.parse_args(argv)
    if bool(args.track_dir) == bool(args.lyrics_file):
        print("usage: gate_lyrics_original.py (--track-dir DIR | "
              "--lyrics-file FILE) [--strict]", file=sys.stderr)
        return 2
    if args.track_dir:
        return gate_track_dir(Path(args.track_dir), args.strict)
    return gate_lyrics_file(Path(args.lyrics_file), args.strict)


if __name__ == "__main__":
    sys.exit(main())
