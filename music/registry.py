#!/usr/bin/env python3
"""music/registry.py — genre + lane registry loader and validator.

The music pipeline is genre-generic: genres are DATA (genres.yaml),
never code. This module is the single read path for that data and the
guard that keeps the registry internally consistent.

Pattern basis (established implementations, researched 2026-10-08):
  - PyYAML docs / yaml/pyyaml#576: use yaml.safe_load (yaml.load
    without a Loader is deprecated and unsafe).
  - autowarefoundation/autoware-index scripts/registry_load.py: one
    load module every reader goes through; RegistryError raised on
    parse errors, non-mapping documents, missing keys, and dangling
    references (a reference to an id that is not live is a HARD
    failure — silent empty output is exactly the failure mode this
    loader exists to kill).

Validation rules (fail loudly, exit non-zero on any violation):
  1. Both YAMLs parse (via safe_load).
  2. Every genre block carries the required keys: family,
     prompt_template, visual_style, lanes, cadence, video_shape.
  3. Every `lanes:` entry in every genre exists as a lane in
     lanes.yaml (dangling lane reference = failure).
  4. Every `prompt_template` and `visual_style` path resolves to a
     real file relative to music/ (dangling path = failure).
  5. Every lane block carries the required keys: surface, bot, gate.

Usage:
    python3 music/registry.py validate    # exit 0 on a clean registry
    python3 music/registry.py show        # dump the resolved registries

Exit codes: 0 = valid, 2 = registry error (dangling reference or
malformed file). On success, prints the resolved genre + lane counts.
"""

import json
import sys
from pathlib import Path

import yaml

# music/ is the anchor for every template/visual path in genres.yaml.
MUSIC_DIR = Path(__file__).resolve().parent
GENRES_YAML = MUSIC_DIR / "genres.yaml"
LANES_YAML = MUSIC_DIR / "lanes.yaml"
QUOTA_LEDGER = MUSIC_DIR / "quota-ledger.json"

GENRE_REQUIRED_KEYS = (
    "family",
    "prompt_template",
    "visual_style",
    "lanes",
    "cadence",
    "video_shape",
)
LANE_REQUIRED_KEYS = ("surface", "bot", "gate")


class RegistryError(Exception):
    """A registry invariant is violated. Printed, exit code 2."""


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise RegistryError(f"missing registry file: {path}")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RegistryError(f"{path}: cannot parse: {exc}") from exc
    if not isinstance(doc, dict):
        raise RegistryError(
            f"{path}: expected a YAML mapping, got {type(doc).__name__}"
        )
    return doc


def load_lanes() -> dict:
    doc = load_yaml(LANES_YAML)
    lanes = doc.get("lanes")
    if not isinstance(lanes, dict) or not lanes:
        raise RegistryError(
            f"{LANES_YAML}: 'lanes:' must be a non-empty mapping of lane id -> spec"
        )
    problems = []
    for name, spec in lanes.items():
        if not isinstance(spec, dict):
            problems.append(f"{LANES_YAML}::{name}: lane spec must be a mapping")
            continue
        for key in LANE_REQUIRED_KEYS:
            value = spec.get(key)
            if not isinstance(value, str) or not value.strip():
                problems.append(
                    f"{LANES_YAML}::{name}: '{key}' must be a non-empty string"
                )
    if problems:
        raise RegistryError("lane registry errors:\n  " + "\n  ".join(problems))
    return lanes


def load_genres(lanes: dict) -> dict:
    doc = load_yaml(GENRES_YAML)
    genres = doc.get("genres")
    if not isinstance(genres, dict) or not genres:
        raise RegistryError(
            f"{GENRES_YAML}: 'genres:' must be a non-empty mapping of genre id -> spec"
        )

    problems = []
    for name, spec in genres.items():
        if not isinstance(spec, dict):
            problems.append(f"{GENRES_YAML}::{name}: genre spec must be a mapping")
            continue

        for key in GENRE_REQUIRED_KEYS:
            if key not in spec or spec[key] in (None, ""):
                problems.append(
                    f"{GENRES_YAML}::{name}: missing required key '{key}'"
                )

        # Lane references must exist in lanes.yaml (the crossover check).
        declared = spec.get("lanes")
        if isinstance(declared, str):
            declared = [declared]
        if isinstance(declared, list):
            for lane in declared:
                if not isinstance(lane, str) or lane not in lanes:
                    problems.append(
                        f"{GENRES_YAML}::{name}: lane {lane!r} has no entry in "
                        f"{LANES_YAML.name}"
                    )

        # Template + visual paths must resolve to real files. Enforce
        # string type: YAML types `1.2` as float, which would silently
        # mangle the path (autoware registry_load.py float trap).
        for key in ("prompt_template", "visual_style"):
            rel = spec.get(key)
            if not isinstance(rel, str) or not rel:
                continue
            target = MUSIC_DIR / rel
            if not target.is_file():
                problems.append(
                    f"{GENRES_YAML}::{name}: {key} '{rel}' does not resolve "
                    f"(expected {target})"
                )

    if problems:
        raise RegistryError("genre registry errors:\n  " + "\n  ".join(problems))
    return genres


def load_quota_ledger() -> dict:
    if not QUOTA_LEDGER.is_file():
        raise RegistryError(f"missing quota ledger: {QUOTA_LEDGER}")
    try:
        data = json.loads(QUOTA_LEDGER.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RegistryError(f"{QUOTA_LEDGER}: cannot parse: {exc}") from exc
    for key in ("standard_downloads_limit", "warn_at", "hard_stop_at"):
        if key not in data:
            raise RegistryError(f"{QUOTA_LEDGER}: missing '{key}'")
    if data["warn_at"] >= data["hard_stop_at"]:
        raise RegistryError(
            f"{QUOTA_LEDGER}: warn_at ({data['warn_at']}) must be < hard_stop_at "
            f"({data['hard_stop_at']})"
        )
    return data


def load_registry() -> dict:
    """Full registry: genres, lanes, defaults, quota. Raises RegistryError."""
    lanes = load_lanes()
    genres_doc = load_yaml(GENRES_YAML)
    genres = load_genres(lanes)
    return {
        "genres": genres,
        "lanes": lanes,
        "defaults": genres_doc.get("defaults", {}),
        "quota": load_quota_ledger(),
    }


def cmd_validate() -> int:
    registry = load_registry()
    genre_count = len(registry["genres"])
    lane_count = len(registry["lanes"])
    quota = registry["quota"]
    print(f"registry OK: {genre_count} genres, {lane_count} lanes")
    print("genres: " + ", ".join(sorted(registry["genres"])))
    print("lanes: " + ", ".join(sorted(registry["lanes"])))
    print(
        "quota ledger: period {period}, standard {standard_downloads_used}/"
        "{standard_downloads_limit} "
        "(warn_at {warn_at}, hard_stop_at {hard_stop_at})".format(**quota)
    )
    return 0


def cmd_show() -> int:
    registry = load_registry()
    print(yaml.safe_dump({"genres": registry["genres"], "lanes": registry["lanes"]}, sort_keys=False))
    return 0


def main(argv: list) -> int:
    command = argv[1] if len(argv) > 1 else "validate"
    try:
        if command == "validate":
            return cmd_validate()
        if command == "show":
            return cmd_show()
        print(f"usage: {Path(argv[0]).name} [validate|show]", file=sys.stderr)
        return 2
    except RegistryError as exc:
        print(f"REGISTRY ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
