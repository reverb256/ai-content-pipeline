#!/usr/bin/env python3
"""Executable validator for music/prompts/<genre>.md templates.

Gates must EXECUTE the artifact. This parses every template file, extracts the
Style field block(s), measures them against the 1000-char limit, and checks the
four required sections exist with real content. A failure here means the
template is broken, regardless of how it reads.

Usage:
    python3 music/prompts/validate_templates.py [genre ...]

Exit 0 = all pass. Exit 1 = any failure (prints each one).
"""
import re
import sys
from pathlib import Path

import yaml

PROMPTS_DIR = Path(__file__).resolve().parent
GENRES_YAML = PROMPTS_DIR.parent / "genres.yaml"
MAX_STYLE_CHARS = 1000


def registry_genres() -> list[str]:
    """The genre list is DATA (music/genres.yaml), never a hardcoded
    list here: adding a genre to the registry must require zero edits
    to this validator. A missing/unparsable registry is a hard error —
    silent empty output is the failure mode this kills."""
    if not GENRES_YAML.exists():
        raise SystemExit(f"FATAL: genre registry missing: {GENRES_YAML}")
    with open(GENRES_YAML) as f:
        registry = yaml.safe_load(f)
    genres = sorted((registry or {}).get("genres") or {})
    if not genres:
        raise SystemExit(f"FATAL: no genres in {GENRES_YAML}")
    return genres

REQUIRED_SECTIONS = ["Style field", "Lyrics guidance", "More Options", "Craft notes"]


def split_sections(text: str) -> dict[str, str]:
    """Split a template into {'Heading': body} at every '## ' heading."""
    sections: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*)$", line)
        if m:
            current = m.group(1).strip()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def find_sections(sections: dict[str, str], needle: str) -> list[tuple[str, str]]:
    """Return [(heading, body)] for every heading containing needle."""
    out = []
    for heading, body in sections.items():
        if needle.lower() in heading.lower():
            out.append((heading, body))
    return out


def extract_fenced_blocks(body: str) -> list[str]:
    """Return the contents of every ```text fence inside a section body."""
    return [m.strip() for m in re.findall(r"```text\n(.*?)```", body, re.DOTALL)]


def validate(genre: str) -> tuple[list[str], list[int]]:
    """Return (errors, measured style-block sizes)."""
    errors: list[str] = []
    style_sizes: list[int] = []
    path = PROMPTS_DIR / f"{genre}.md"
    if not path.exists():
        return [f"MISSING FILE: {path}"], style_sizes
    text = path.read_text(encoding="utf-8")
    sections = split_sections(text)

    # 1. Four required sections, each with real content.
    for section in REQUIRED_SECTIONS:
        found = find_sections(sections, section)
        if not any(body.strip() for _, body in found):
            errors.append(f"missing or empty section: '## {section}'")

    # 2. Style field block(s): present, fenced, and <= 1000 chars measured.
    #    A template may carry several style fields (e.g. sting + bed) — read all.
    style_secs = find_sections(sections, "style field")
    style_blocks = [b for _, body in style_secs for b in extract_fenced_blocks(body)]
    if not style_blocks:
        errors.append("no fenced ```text style block found under a Style field heading")
    for i, block in enumerate(style_blocks, 1):
        n = len(block)
        style_sizes.append(n)
        label = f"style block {i}" if len(style_blocks) > 1 else "style block"
        if n > MAX_STYLE_CHARS:
            errors.append(f"{label} is {n} chars (limit {MAX_STYLE_CHARS})")

    # 3. Lyrics guidance must carry [metatag] structure.
    for _, body in find_sections(sections, "lyrics guidance"):
        if not re.search(r"\[[A-Za-z][^\]]*\]", body):
            errors.append("lyrics guidance has no [metatag] structure")

    # 4. More Options must set weirdness, style influence, and exclusions.
    for _, body in find_sections(sections, "more options"):
        for needle, what in [("weirdness", "weirdness"), ("influence", "style influence"),
                             ("exclude", "exclusions")]:
            if needle not in body.lower():
                errors.append(f"More Options missing {what}")


    # 5. Header char-count claim must match measured reality (no stale claims).
    claims = re.findall(r"(\d+)\s*/\s*1000\s*chars?", text)
    for claim in claims:
        if int(claim) not in style_sizes:
            errors.append(
                f"header claims {claim}/1000 chars but measured style blocks are {style_sizes}"
            )
    return errors, style_sizes


def main() -> int:
    targets = sys.argv[1:] or registry_genres()
    failures = 0
    print(f"Validating {len(targets)} prompt template(s) in {PROMPTS_DIR}\n")
    for genre in targets:
        errs, sizes = validate(genre)
        if errs:
            failures += 1
            print(f"FAIL {genre}  (measured style blocks: {sizes})")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"PASS {genre}  (style block: {sizes} chars)")
    print(f"\n{len(targets) - failures}/{len(targets)} templates valid")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
