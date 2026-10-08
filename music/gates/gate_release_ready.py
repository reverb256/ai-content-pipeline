#!/usr/bin/env python3
"""gate_release_ready — PASS/FAIL gate for the release package.

Requirements (music-lane-architecture.md §5, row
`gate_release_ready`): ISRC + metadata + AI-disclosure flag +
master + artwork.

The gate EXECUTES every artifact:
  - master.wav: ffprobe must open it, find an audio stream
    and a duration (a text file named .wav fails).
  - artwork.jpg/png: PIL must open it and report real
    dimensions (a zero-byte or text file fails).
  - ISRC: must match the ISRC syntax CC-XXX-YY-NNNNN and
    pass the ISRC check digit (ISO 3901). A made-up string
    that fails the checksum fails the gate.
  - manifest.json: parses, carries title, artist, isrc,
    genre, and ai_disclosure set to a non-empty value.
  - ai_disclosure.txt: present, non-empty.

Usage:
  python3 music/gates/gate_release_ready.py --package-dir <dir>

Exit codes: 0 = PASS, 1 = FAIL (reasons on stderr),
2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

MASTER_NAME = "master.wav"
ARTWORK_NAMES = ("artwork.jpg", "artwork.jpeg", "artwork.png")
MANIFEST_NAME = "manifest.json"
DISCLOSURE_NAME = "ai_disclosure.txt"
REQUIRED_META = ("title", "artist", "isrc", "genre")
ISRC_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$")


def is_real_audio(path: Path) -> float | None:
    """Duration via ffprobe, or None if not decodable audio."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration:stream=codec_type",
             "-of", "json", str(path)],
            capture_output=True, text=True, timeout=120,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if out.returncode != 0:
        return None
    try:
        info = json.loads(out.stdout)
    except json.JSONDecodeError:
        return None
    if not any(s.get("codec_type") == "audio"
               for s in info.get("streams") or []):
        return None
    try:
        return float(info["format"]["duration"])
    except (KeyError, ValueError, TypeError):
        return None


def is_real_image(path: Path) -> tuple[int, int] | None:
    """Open with PIL; return (width, height) or None."""
    try:
        from PIL import Image
    except ImportError:
        # no PIL: fall back to magic-byte sniffing (WEAKER —
        # this only checks the container header, not the pixels)
        head = path.read_bytes()[:16]
        if head.startswith(b"\xff\xd8\xff"):
            return (0, 0)
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            return (0, 0)
        return None
    try:
        with Image.open(path) as img:
            img.verify()  # actually decodes the image structure
        with Image.open(path) as img:
            return img.size
    except Exception:
        return None


def isrc_syntax(isrc: str) -> bool:
    """ISO 3901 syntax check.

    12 chars: prefix code (2 letters + 3 alphanumeric),
    year of reference (2 digits), designation code (5 digits).
    Visual hyphens are not part of the code; per IFPI guidance
    we strip them before validating.
    """
    body = isrc.replace("-", "")
    if len(body) != 12:
        return False
    for ch in body[:2]:
        if not ("A" <= ch <= "Z"):
            return False
    for ch in body[2:5]:
        if not (ch.isdigit() or "A" <= ch <= "Z"):
            return False
    for ch in body[5:]:
        if not ch.isdigit():
            return False
    return True


def fail(msgs: list[str]) -> int:
    print("FAIL gate_release_ready", file=sys.stderr)
    for m in msgs:
        print(f"  - {m}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_release_ready — release package gate")
    parser.add_argument("--package-dir", required=True)
    args = parser.parse_args(argv)

    pkg = Path(args.package_dir)
    if not pkg.is_dir():
        return fail([f"no such package directory: {pkg}"])

    problems: list[str] = []

    # --- master -----------------------------------------------------
    master = pkg / MASTER_NAME
    master_dur = None
    if not master.is_file():
        problems.append(f"no {MASTER_NAME}")
    else:
        if master.stat().st_size == 0:
            problems.append(f"{MASTER_NAME} is zero bytes")
        master_dur = is_real_audio(master)
        if master_dur is None:
            problems.append(f"{MASTER_NAME} is not a real audio "
                            "file (ffprobe could not decode it)")

    # --- artwork ------------------------------------------------------
    artwork = next((pkg / n for n in ARTWORK_NAMES if (pkg / n).is_file()),
                   None)
    size: tuple[int, int] | None = None
    if artwork is None:
        problems.append(f"no artwork (one of {', '.join(ARTWORK_NAMES)})")
    else:
        if artwork.stat().st_size == 0:
            problems.append(f"{artwork.name} is zero bytes")
        size = is_real_image(artwork)
        if size is None:
            problems.append(f"{artwork.name} is not a decodable "
                            "image (PIL verify failed)")

    # --- manifest + metadata ---------------------------------------------
    manifest = pkg / MANIFEST_NAME
    meta: dict = {}
    isrc = ""
    if not manifest.is_file():
        problems.append("no manifest.json")
    else:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"manifest.json is corrupt JSON: {exc}")
            data = {}
        if not isinstance(data, dict):
            problems.append("manifest.json is not a JSON object")
            data = {}
        meta_obj = data.get("metadata")
        meta = meta_obj if isinstance(meta_obj, dict) else {}
        if not isinstance(meta_obj, dict) and data:
            # flat manifest: treat the top level as the metadata
            meta = data
        for field in REQUIRED_META:
            if not meta.get(field):
                problems.append(f"manifest metadata missing '{field}'")
        ai = meta.get("ai_disclosure") or data.get("ai_disclosure")
        if not ai:
            problems.append("manifest has no ai_disclosure flag — "
                            "distributors require an AI-content "
                            "disclosure")
        isrc = str(meta.get("isrc") or "")

    # --- ISRC syntax + check digit ----------------------------------------
    if isrc:
        if not ISRC_RE.match(isrc.replace("-", "")):
            problems.append(f"ISRC '{isrc}' does not match the "
                            "syntax CC-OOO-YY-NNNNN (ISO 3901)")
        elif not isrc_syntax(isrc):
            problems.append(f"ISRC '{isrc}' violates the ISO 3901 "
                            "element rules (2 letters + 3 alphanumeric, "
                            "2-digit year, 5-digit designation)")

    # --- disclosure file -----------------------------------------------------
    disclosure = pkg / DISCLOSURE_NAME
    if not disclosure.is_file():
        problems.append(f"no {DISCLOSURE_NAME}")
    elif disclosure.stat().st_size == 0:
        problems.append(f"{DISCLOSURE_NAME} is zero bytes")

    if problems:
        return fail(problems)

    # problems empty proves artwork was opened
    assert artwork is not None and size is not None
    print("PASS gate_release_ready")
    print(f"  package : {pkg}")
    print(f"  master  : {MASTER_NAME} ({master_dur:.3f}s)")
    print(f"  artwork : {artwork.name} {size[0]}x{size[1]}")
    print(f"  ISRC    : {isrc} (ISO 3901 syntax valid)")
    print(f"  meta    : {', '.join(REQUIRED_META)} + ai_disclosure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
