#!/usr/bin/env python3
"""Lyrics stage for the genre-generic music pipeline.

WRITER PROFILE ONLY. This module is the only sanctioned producer of track
lyrics in the pipeline. It never calls Suno's "Write with Suno" / ReMi /
classic lyric generator; lyrics written here are ORIGINAL, human-directed
works. The generator bot consumes the .suno.txt files it emits as the
Custom-mode lyric payload — Suno renders the vocals, it never authors the
words.

Design contract (brain/playbooks/music-lane-architecture.md):
  - GENRE-GENERIC: genres are DATA in music/genres.yaml. This file never
    names a genre. Add a genre = add a registry block + a lyric blueprints
    file under music/lyrics/blueprints/. Zero code edits.
  - LYRIC BLUEPRINTS are data too: music/lyrics/blueprints/<genre>.yaml
    carries theme, structure (with [metatags]), rhyme/meter guidance and
    title candidates per genre. The writer writes the actual lyrics from
    a blueprint by hand; this module only scaffolds + records.

Layout produced:
  music/lyrics/<genre>/<song-slug>/
      lyrics.suno.txt      — section-tagged lyric sheet ([Verse] etc.)
      lyrics.txt           — plain-text lyric sheet (no tags), human reading
      manifest.json        — human-authorship claim + AI-assist disclosure
      title.txt            — working title

Usage:
  python3 music/lyrics/lyrics.py scaffold --genre trance --theme "..."
  python3 music/lyrics/lyrics.py claim --track-dir music/lyrics/trance/<slug> \
      --author "j_kro" [--ai-assisted "suno rendered the vocals from ..."]
  python3 music/lyrics/lyrics.py validate --track-dir <dir> [--strict]
  python3 music/lyrics/lyrics.py validate --lyrics-file <file> [--strict]

Exit codes: 0 pass, 1 validation/gate failure, 2 usage/registry error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("FATAL: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise

REPO = Path(__file__).resolve().parents[2]
GENRES_YAML = REPO / "music" / "genres.yaml"
BLUEPRINT_DIR = REPO / "music" / "lyrics" / "blueprints"

# --- Suno section metatags (structure tags Suno's Custom mode understands).
# Kept in sync with music/prompts/<genre>.md templates. Re-synced 2026-10-16
# (card t_53da62e5): a scan of every template's Lyrics-guidance tag sheet found
# six distinct tags the list was missing — "Break" (elemental-fire, jungle-dnb)
# and "Choir" (epic-orchestral-boss) are plain metatags and are added here; the
# composed ones ("Final Chorus — KEY CHANGE UP ONE SEMITONE/TONE",
# "Final Chorus — KEY LIFT", "Instrumental Break") are handled by
# is_known_section() below, not by listing every genre's phrasing.
KNOWN_SECTIONS = [
    "Intro", "Verse", "Verse 1", "Verse 2", "Verse 3", "Verse 4", "Pre-Chorus",
    "Chorus", "Post-Chorus", "Bridge", "Refrain", "Hook", "Breakdown", "Break",
    "Drop", "Build", "Rise", "Interlude", "Solo", "Instrumental", "Vamp",
    "Choir", "Outro", "Fadeout", "End", "Spoken Word", "Ad-Lib",
]

# A genre may qualify a known metatag, and those tags are mandatory in the
# genre's own template: anime-opening's structure is not in genre without
# "[Final Chorus — KEY CHANGE UP ONE SEMITONE/TONE]" (music/prompts/anime-opening.md).
# The strict check must accept them WITHOUT this file naming a genre — the design
# contract above is "add a genre = add data, zero code edits" — so the rule is
# structural: a tag is known when it IS a metatag, or when the head before an
# em/en dash is a metatag carrying a qualifier at one EDGE ("final chorus",
# "instrumental break"). Edge-only on purpose: a known word buried in the middle
# of a label ("Mic Drop Into Space") is not a section, and a guard that accepts it
# stops guarding anything.
_QUALIFIER_SPLIT_RE = re.compile(r"\s*[—–]\s*")


def _is_metatag_at_an_edge(head: str, known: set[str]) -> bool:
    if head in known:
        return True
    return any(head.startswith(k + " ") or head.endswith(" " + k) for k in known)


def is_known_section(tag: str) -> bool:
    """True when `tag` is a Suno metatag this pipeline uses, qualifiers allowed."""
    t = " ".join(tag.strip().lower().split())
    known = {s.lower() for s in KNOWN_SECTIONS}
    if t in known:
        return True
    head = _QUALIFIER_SPLIT_RE.split(t, maxsplit=1)[0].strip()
    return _is_metatag_at_an_edge(head, known)

# --- AI-generated-lyric markers (detection layer, see gate_lyrics_original).
# The pipeline must never ship a lyric that Suno's generator authored.
# Markers are ordered; each is documented in music/gates/SUNO_FINGERPRINTS.md.
SUNO_GEN_MARKERS: list[tuple[str, str]] = [
    # writers put provenance directly in the file (honest recording)
    ("provenance:suno", "explicit provenance header naming Suno generation"),
    ("write with suno", "UI artefact pasted from Suno's lyric generator"),
    ("remi", "Suno ReMi lyric-model mention"),
    # reference examples verified 2026-10-08: outputs of Suno's classic model
    # (Full Song) and ReMi. See music/gates/SUNO_FINGERPRINTS.md for each
    # example, its source URL, and why the marker discriminates.
    ("umbrellas in space", "known Suno 'Full Song' example lyric"),
    ("intergalactic traveler", "known Suno 'Full Song' example lyric"),
    ("walking on the stars with my umbrella", "known Suno example lyric"),
    ("asteroids may stumble", "known Suno example lyric"),
    ("dancing in zero-g", "known Suno example lyric"),
    ("milky way confetti", "known Suno example lyric"),
    ("umbrella twirling magic", "known Suno example lyric"),
    ("aliens wave like friends", "known Suno example lyric"),
    ("gravity can't catch me", "known Suno example lyric"),
    ("dance beneath the nebula", "known Suno example lyric"),
    ("astral winds can't touch", "known Suno example lyric"),
    ("moon beams and dreams", "known Suno example lyric (spacing variants)"),
    ("craft a constellation with a sparkle", "known Suno example lyric"),
]

# Generation-quality heuristics — a lyric sheet Suno's Custom mode can sing
# and a court would recognize as an original human work.
MIN_UNIQUE_WORDS = 25
MIN_SECTIONS = 2
MAX_TITLE_LEN = 64

# What counts as one token in the unique-word measure. The Latin alternative is
# the original pattern, character for character, so an English sheet's count is
# identical before and after the script-aware extension (proved in
# music/tests/test_lyrics_gate_language.py, which recomputes both).
#
# The CJK alternative exists because two registry genres (anisong: anime-opening,
# anime-ending) REQUIRE kana/kanji and forbid romaji, and the Latin-only pattern
# measures such a sheet as 0 unique words — the gate then refuses a complete,
# in-genre sheet no matter who wrote it (measured 2026-10-16, card t_53da62e5).
# A maximal run of kana/kanji counts as one token: an approximation, since no
# morphological segmenter is available here, but the floor's job is to prove a
# sheet is a lyric rather than a stub, and both readings are honest about scale.
WORD_TOKEN_RE = re.compile(
    r"[a-z']+"                                                     # Latin words
    r"|[\u3005\u3041-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
    r"\uff66-\uff9d]+"                                             # kana / kanji
)

SLUG_RE = re.compile(r"[^a-z0-9]+")


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_genres() -> dict:
    """Load + minimally validate the genre registry (data layer)."""
    if not GENRES_YAML.is_file():
        print(f"FATAL: genre registry not found: {GENRES_YAML}",
              file=sys.stderr)
        print("FATAL: this file is owned by the registries card "
              "(music/genres.yaml). scaffold needs it; claim/validate/gate "
              "do not.", file=sys.stderr)
        sys.exit(2)
    with open(GENRES_YAML, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    genres = data.get("genres")
    if not isinstance(genres, dict) or not genres:
        print(f"FATAL: no genres in {GENRES_YAML}", file=sys.stderr)
        sys.exit(2)
    return data


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = SLUG_RE.sub("-", text.lower()).strip("-")
    return slug or "untitled"


def parse_sections(raw: str) -> list[tuple[str, list[str]]]:
    """Split a lyric sheet into ([Section], lines) pairs.

    Only well-formed [Tag] headers count as sections. Works for both
    lyrics.suno.txt (tagged) and lyrics.txt (plain) — an untagged sheet
    parses as one implicit section, which validation treats as a defect.
    """
    sections: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for line in raw.splitlines():
        if line.strip().startswith("#"):
            # file-level comment/provenance header — never sung, never gated
            continue
        header = re.fullmatch(r"\[([^\]]+)\]", line.strip())
        if header:
            if current:
                sections.append(current)
            current = (header.group(1), [])
        else:
            if current is None:
                current = ("(untagged)", [])
            current[1].append(line)
    if current:
        sections.append(current)
    # keep only sections that have at least one non-empty line
    return [(tag, [ln for ln in lines if ln.strip()]) for tag, lines in sections
            if any(ln.strip() for ln in lines)]


def lyric_text_of(sections: list[tuple[str, list[str]]]) -> str:
    return "\n".join("\n".join(lines) for _, lines in sections).strip()


def unique_word_count(sections: list[tuple[str, list[str]]]) -> int:
    """Distinct tokens in the sung lines, script-aware (see WORD_TOKEN_RE)."""
    words: set[str] = set()
    for _, lines in sections:
        for line in lines:
            for token in WORD_TOKEN_RE.findall(line.lower()):
                words.add(token)
    return len(words)


# ------------------------------------------------------------------------------------------------------------------------------------------------
# Scaffold: build the per-genre working directory from the blueprint.
# ---------------------------------------------------------------------------

def cmd_scaffold(args: argparse.Namespace) -> int:
    registry = load_genres()
    genre_key = args.genre
    if genre_key not in registry["genres"]:
        print(f"FAIL: genre '{genre_key}' is not in {GENRES_YAML}", file=sys.stderr)
        print("      known genres: " + ", ".join(sorted(registry["genres"])), file=sys.stderr)
        return 2

    bp_path = BLUEPRINT_DIR / f"{genre_key}.yaml"
    if not bp_path.is_file():
        print(f"FAIL: no lyric blueprint for '{genre_key}' at {bp_path}", file=sys.stderr)
        return 2
    with open(bp_path, encoding="utf-8") as fh:
        bp = yaml.safe_load(fh) or {}
    for field in ("family", "theme", "title_candidates", "structure"):
        if field not in bp:
            print(f"FAIL: blueprint {bp_path} is missing field '{field}'", file=sys.stderr)
            return 2

    title = args.title or bp["title_candidates"][0]
    theme = args.theme or bp["theme"]
    slug = slugify(title)

    track_dir = REPO / "music" / "lyrics" / genre_key / slug
    if track_dir.exists() and not args.force:
        print(f"FAIL: {track_dir} already exists (use --force to overwrite scaffolding)",
              file=sys.stderr)
        return 2
    track_dir.mkdir(parents=True, exist_ok=True)

    structure = bp["structure"]  # list of {tag, guidance} or bare strings
    tagged = []
    for entry in structure:
        if isinstance(entry, dict):
            tag = str(entry.get("tag", "Verse")).strip()
            guidance = str(entry.get("guidance", "")).strip()
        else:
            tag, guidance = str(entry).strip(), ""
        tagged.append((f"[{tag}]", guidance))

    # lyrics.suno.txt — scaffold headers + empty guidance. The writer
    # writes every sung line. Empty scaffold sections are placeholders and
    # validate() must reject them (no half-written track ever advances).
    suno_lines: list[str] = [
        f"# genre: {genre_key}",
        f"# title: {title}",
        f"# theme: {theme}",
        "# provenance: human-original (writer profile) — do not paste Suno-generated lyrics here",
        "",
    ]
    for header, guidance in tagged:
        suno_lines.append(header)
        if guidance:
            suno_lines.append(f"({guidance})")
        suno_lines.append("")
    (track_dir / "lyrics.suno.txt").write_text("\n".join(suno_lines), encoding="utf-8")

    (track_dir / "title.txt").write_text(title + "\n", encoding="utf-8")

    # manifest.json — the human-authorship claim is RECORDED here, not in prose.
    manifest = {
        "schema": "music/track-lyrics-manifest v1",
        "track_slug": slug,
        "title": title,
        "genre": genre_key,
        "genre_family": bp.get("family"),
        "theme": theme,
        "authorship": {
            "status": "incomplete",  # scaffold: writer has not claimed yet
            "authors": [],          # human writers of the words
            "written_at": None,     # UTC ISO-8601 when the claim is recorded
            "ai_assist": None,      # what the AI did / did not do
            "suno_generated_lyrics": False,  # must stay False for SOCAN path
        },
        "files": {
            "lyrics.suno.txt": None,
            "lyrics.txt": None,
        },
        "notes": bp.get("notes", ""),
    }
    (track_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"scaffolded {track_dir}")
    print(f"  blueprint : {bp_path}")
    print(f"  next      : write the lyrics into lyrics.suno.txt, then run")
    print(f"              python3 music/lyrics/lyrics.py claim --track-dir {track_dir} "
          f"--author 'j_kro'")
    return 0


# ---------------------------------------------------------------------------
# Claim: record the human-authorship claim after the writer finishes writing.
# ---------------------------------------------------------------------------

def cmd_claim(args: argparse.Namespace) -> int:
    track_dir = Path(args.track_dir).resolve()
    manifest_path = track_dir / "manifest.json"
    suno_file = track_dir / "lyrics.suno.txt"
    plain_file = track_dir / "lyrics.txt"
    if not manifest_path.is_file() or not suno_file.is_file():
        print(f"FAIL: {track_dir} is not a scaffolded lyric track "
              "(missing manifest.json or lyrics.suno.txt)", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw = suno_file.read_text(encoding="utf-8")
    sections = parse_sections(raw)

    # Never record a claim over an empty, clearly broken, or Suno-generated sheet.
    problems = validate_sheet(sections, strict=True)
    problems += [f"Suno-generated-lyric marker '{m}' present ({w})"
                 for m, w in scan_suno_markers(raw)]
    if problems:
        print("FAIL: cannot claim — lyric sheet incomplete:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    # Derive the plain reading copy from the tagged sheet (single source).
    plain_lines = []
    for tag, lines in sections:
        plain_lines.extend(lines)
    plain = "\n".join(ln for ln in plain_lines if ln.strip()).strip() + "\n"
    plain_file.write_text(plain, encoding="utf-8")

    authors = [a.strip() for a in args.author.split(",") if a.strip()]
    manifest["authorship"] = {
        "status": "human-original",
        "authors": authors,
        "written_at": utc_now_iso(),
        "ai_assist": args.ai_assisted or (
            "None for the lyric text. Lyrics were written by the named human "
            "author(s). Suno is used only to render vocals from this text; it "
            "did not write or edit any line."
        ),
        "suno_generated_lyrics": False,
    }
    manifest["files"] = {
        "lyrics.suno.txt": {
            "sha256": sha256_of(suno_file),
            "bytes": suno_file.stat().st_size,
        },
        "lyrics.txt": {
            "sha256": sha256_of(plain_file),
            "bytes": plain_file.stat().st_size,
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"human-authorship claim recorded for '{manifest.get('title', slug_of(track_dir))}'")
    print(f"  track dir : {track_dir}")
    print(f"  authors   : {', '.join(authors)}")
    print(f"  written_at: {manifest['authorship']['written_at']}")
    print(f"  ai_assist : {manifest['authorship']['ai_assist']}")
    print(f"  sha256(lyrics.suno.txt): {manifest['files']['lyrics.suno.txt']['sha256']}")
    return 0


def slug_of(track_dir: Path) -> str:
    return track_dir.name


# ---------------------------------------------------------------------------
# Shared validation: EXECUTES the artifact (parses the sheet, measures it).
# gate_lyrics_original.py imports these functions — the gate is this logic,
# not a copy of it.
# ---------------------------------------------------------------------------

def sung_lines(lines: list[str]) -> list[str]:
    """The section's lines that are meant to be SUNG, not direction text.

    A parenthetical note is guidance for the composer — "(low male chant
    murmurs, no drums)" — and a `#` line is provenance. Neither is sung. A note
    can WRAP: it opens a parenthesis on one line and closes it on the next, so
    the continuation line does not itself start with "(" — and the previous rule,
    which rejected a line only when it began AND ended with a parenthesis,
    counted that continuation as lyric text. Measured 2026-10-16 on the
    epic-orchestral-boss tag sheet (card t_bc6a0c00): 11 of its 14 direction
    lines were counted as words, carrying 54 of the sheet's 71 unique words.
    A draft scaffold therefore cleared the word floor on its craft notes alone.

    The renderer refuses the same sheet with the same rule
    (`singable_lines()` in music/scripts/acestep_plan.py). One rule, two
    implementations: music/tests/test_acestep_sheet_guard.py asserts that the two
    agree line for line on the real sheet, because their drift is what let this
    through in the first place.
    """
    kept: list[str] = []
    depth = 0
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if depth:
            # still inside a direction opened on an earlier line
            depth = max(depth + line.count("(") - line.count(")"), 0)
            continue
        if line.startswith(("#", "(")):
            depth = max(depth + line.count("(") - line.count(")"), 0)
            continue
        kept.append(line)
    return kept


def validate_sheet(sections: list[tuple[str, list[str]]], strict: bool) -> list[str]:
    """Parse-level checks. Returns a list of problems (empty = pass)."""
    problems: list[str] = []
    if len(sections) < MIN_SECTIONS:
        problems.append(f"fewer than {MIN_SECTIONS} sections with content "
                        f"({len(sections)} found)")
    unique_words = unique_word_count(sections)
    if unique_words < MIN_UNIQUE_WORDS:
        problems.append(f"only {unique_words} unique words (minimum {MIN_UNIQUE_WORDS})")
    body_lines = [ln for _, lines in sections for ln in lines if ln.strip()]
    if not body_lines:
        problems.append("no lyric lines")
        return problems
    for tag, lines in sections:
        if tag == "(untagged)":
            problems.append("untagged lines outside any [Section] header")
        # scaffold placeholder lines must be replaced by real lyrics
        nonempty = [ln for ln in lines if ln.strip()]
        if not nonempty:
            problems.append(f"[{tag}] section has no lines")
        sung = set(sung_lines(lines))
        for ln in nonempty:
            s = ln.strip()
            if s.startswith("#"):
                problems.append(f"[{tag}] comment/meta line inside lyric body: '{s[:60]}'")
            elif s not in sung:
                # Parentheses mark direction text, and a direction can WRAP onto
                # the next line. The previous rule rejected a line only when it
                # began AND ended with a parenthesis, so every continuation line
                # was read as lyric text (card t_bc6a0c00: 11 lines, 54 of the
                # sheet's 71 words). `sung` is the same rule the renderer refuses
                # on, so this gate and that refusal cannot disagree.
                problems.append(f"[{tag}] placeholder guidance left in: '{s[:60]}'")
    if strict:
        for tag, _ in sections:
            if not is_known_section(tag):
                problems.append(f"unknown section tag [{tag}] (not a Suno metatag)")
    return problems


def scan_suno_markers(raw: str) -> list[tuple[str, str]]:
    """Return every Suno-generated-lyric marker present in the text."""
    found: list[tuple[str, str]] = []
    lowered = raw.lower()
    for marker, why in SUNO_GEN_MARKERS:
        if marker in lowered:
            found.append((marker, why))
    return found


def validate_track_dir(track_dir: Path, strict: bool = True) -> tuple[list[str], dict]:
    """Full gate logic: parse + measure + provenance + manifest claim."""
    problems: list[str] = []
    context: dict = {"track_dir": str(track_dir)}

    manifest_path = track_dir / "manifest.json"
    suno_file = track_dir / "lyrics.suno.txt"
    if not manifest_path.is_file():
        problems.append(f"missing manifest.json (no human-authorship claim) in {track_dir}")
        return problems, context
    if not suno_file.is_file():
        problems.append("missing lyrics.suno.txt")
        return problems, context

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        problems.append(f"manifest.json is not valid JSON: {exc}")
        return problems, context

    auth = manifest.get("authorship")
    if not isinstance(auth, dict):
        problems.append("manifest has no 'authorship' claim")
        auth = {}
    else:
        if auth.get("status") != "human-original":
            problems.append(f"authorship.status is {auth.get('status')!r}, "
                            "expected 'human-original'")
        if not auth.get("authors"):
            problems.append("authorship.authors is empty (no named human writer)")
        if not auth.get("written_at"):
            problems.append("authorship.written_at missing (undated claim)")
        if auth.get("suno_generated_lyrics") is not False:
            problems.append("authorship.suno_generated_lyrics is not False")

    raw = suno_file.read_text(encoding="utf-8")
    context["sha256_lyrics_suno_txt"] = sha256_of(suno_file)
    sections = parse_sections(raw)
    context["sections"] = len(sections)
    context["unique_words"] = unique_word_count(sections)
    problems.extend(validate_sheet(sections, strict=strict))

    markers = scan_suno_markers(raw)
    context["suno_markers"] = [m for m, _ in markers]
    for marker, why in markers:
        problems.append(f"Suno-generated-lyric marker '{marker}' present ({why})")

    # files block must match reality (hashes prove the claim covers THIS text)
    files = manifest.get("files") or {}
    claimed = files.get("lyrics.suno.txt") or {}
    if isinstance(claimed, dict) and claimed.get("sha256"):
        if claimed["sha256"] != context["sha256_lyrics_suno_txt"]:
            problems.append("manifest hash for lyrics.suno.txt does not match the file — "
                            "the claim does not cover the text on disk")
    else:
        problems.append("manifest.files['lyrics.suno.txt'] has no sha256 "
                        "(claim never recorded via 'lyrics.py claim')")

    return problems, context


def cmd_validate(args: argparse.Namespace) -> int:
    if bool(args.track_dir) == bool(args.lyrics_file):
        print("FAIL: give exactly one of --track-dir or --lyrics-file", file=sys.stderr)
        return 2
    if args.lyrics_file:
        path = Path(args.lyrics_file)
        if not path.is_file():
            print(f"FAIL: no such file: {path}", file=sys.stderr)
            return 2
        raw = path.read_text(encoding="utf-8")
        markers = scan_suno_markers(raw)
        problems = validate_sheet(parse_sections(raw), strict=args.strict)
        problems += [f"Suno-generated-lyric marker '{m}' present ({w})"
                      for m, w in markers]
        context = {"lyrics_file": str(path), "suno_markers": [m for m, _ in markers]}
    else:
        track_dir = Path(args.track_dir)
        if not track_dir.is_dir():
            print(f"FAIL: no such track dir: {track_dir}", file=sys.stderr)
            return 2
        problems, context = validate_track_dir(track_dir, strict=args.strict)

    print(json.dumps({"ok": not problems, "problems": problems, "context": context},
                     indent=2, ensure_ascii=False))
    return 0 if not problems else 1


def main(argv: "list[str] | None" = None) -> int:
    doc_first_line = (__doc__ or "").splitlines()[0] if __doc__ else "music lyrics stage"
    parser = argparse.ArgumentParser(description=doc_first_line)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sc = sub.add_parser("scaffold", help="scaffold a lyric track from a genre blueprint")
    p_sc.add_argument("--genre", required=True)
    p_sc.add_argument("--theme", default=None, help="override blueprint theme")
    p_sc.add_argument("--title", default=None, help="override blueprint title candidate")
    p_sc.add_argument("--force", action="store_true")

    p_cl = sub.add_parser("claim", help="record the human-authorship claim")
    p_cl.add_argument("--track-dir", required=True)
    p_cl.add_argument("--author", required=True,
                      help="human author name(s), comma-separated")
    p_cl.add_argument("--ai-assisted", default=None,
                      help="what AI assisted with (defaults to an honest 'none for text')")

    p_va = sub.add_parser("validate", help="parse + measure + provenance check")
    p_va.add_argument("--track-dir", default=None)
    p_va.add_argument("--lyrics-file", default=None)
    p_va.add_argument("--strict", action="store_true",
                      help="also enforce known Suno section tags")

    args = parser.parse_args(argv)
    if args.cmd == "scaffold":
        return cmd_scaffold(args)
    if args.cmd == "claim":
        return cmd_claim(args)
    if args.cmd == "validate":
        return cmd_validate(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
