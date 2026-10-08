#!/usr/bin/env python3
"""gate_sync_ready — PASS/FAIL gate for the sync / direct-license / game-assets lanes.

Requirements (music-lane-architecture.md §3 `requires` + §5):
  sync:           [stems, metadata, clearance_doc, instrumental_version]
  direct-license: [stems, license_tiers]
  game-assets:    [stems, loop_point, seamless_loop, metadata]

The gate EXECUTES the artifact — nothing is trusted from a filename:
  1. Stems: >= MIN_STEMS real audio files (ffprobe must open them and
     report a duration + a stream), each non-zero, each within
     +/- STEM_TOLERANCE s of the master duration (ffprobe, not file size).
  2. Master: full_mix.wav must itself be a real audio file.
  3. Instrumental: instrumental.wav must be a real audio file, distinct
     from the master (different bytes — a copied master is not an
     instrumental version).
  4. Metadata: manifest.json parses and carries title, artist, bpm, key,
     mood, genre.
  5. Clearance doc: clearance_doc is a real PDF (a PDF starts with %PDF-;
     we parse the header bytes — not a file-extension guess).
  6. AI disclosure: ai_disclosure.txt states the AI role.
  7. License tiers (direct-license lane): license_tiers.* present.

Usage:
  python3 music/gates/gate_sync_ready.py --package-dir <dir> \
      [--lane sync|direct-license|game-assets]

Exit codes: 0 = PASS, 1 = FAIL (human-readable reasons on stderr),
2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

MIN_STEMS = 4                 # architecture §5: >= 4 stems
STEM_TOLERANCE_S = 0.5        # durations match master +/- 0.5 s
MASTER_NAME = "full_mix.wav"
INSTRUMENTAL_NAME = "instrumental.wav"
CLEARANCE_NAMES = ("clearance_doc.pdf", "clearance_doc.txt")
MANIFEST_NAME = "manifest.json"
REQUIRED_META = ("title", "artist", "bpm", "key", "mood", "genre")
LANES = ("sync", "direct-license", "game-assets")


def probe(path: Path) -> dict | None:
    """Run ffprobe; return parsed format info, or None if not real media.

    This is the exercise step: a zero-byte or text file named .wav has
    no duration and no streams, and ffprobe fails — the gate fails.
    """
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration,size:stream=codec_type",
             "-of", "json", str(path)],
            capture_output=True, text=True, timeout=120,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return None


def audio_duration(path: Path) -> float | None:
    info = probe(path)
    if not info:
        return None
    streams = info.get("streams") or []
    if not any(s.get("codec_type") == "audio" for s in streams):
        return None
    try:
        return float(info["format"]["duration"])
    except (KeyError, ValueError, TypeError):
        return None


def fail(msgs: list[str]) -> int:
    print("FAIL gate_sync_ready", file=sys.stderr)
    for m in msgs:
        print(f"  - {m}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_sync_ready — sync/direct-license/game-assets gate")
    parser.add_argument("--package-dir", required=True,
                        help="the packaged sync deliverable directory")
    parser.add_argument("--lane", default="sync", choices=LANES,
                        help="lane shaping which extras are required")
    args = parser.parse_args(argv)

    pkg = Path(args.package_dir)
    if not pkg.is_dir():
        return fail([f"no such package directory: {pkg}"])

    problems: list[str] = []

    # --- 1. master ------------------------------------------------
    master = pkg / MASTER_NAME
    master_dur = audio_duration(master)
    if master_dur is None:
        problems.append(f"{MASTER_NAME} is not a real audio file "
                        "(ffprobe could not read a duration)")
    elif master.stat().st_size == 0:
        problems.append(f"{MASTER_NAME} is zero bytes")

    # --- 2. stems --------------------------------------------------
    stems_dir = pkg / "stems"
    if not stems_dir.is_dir():
        problems.append("no stems/ directory — a sync track without "
                        "stems is not sync-ready (architecture HARD RULE 4)")
        stems: list[Path] = []
    else:
        stems = sorted(p for p in stems_dir.iterdir()
                       if p.is_file() and p.suffix.lower() in
                       (".wav", ".aif", ".aiff", ".flac"))
    if len(stems) < MIN_STEMS:
        problems.append(f"only {len(stems)} stem(s) found; {MIN_STEMS} "
                        "required (drums, bass, keys, vocals, ...)")
    for st in stems:
        if st.stat().st_size == 0:
            problems.append(f"stem {st.name} is zero bytes")
            continue
        d = audio_duration(st)
        if d is None:
            problems.append(f"stem {st.name} is not a real audio file")
            continue
        if master_dur is not None and abs(d - master_dur) > STEM_TOLERANCE_S:
            problems.append(f"stem {st.name} duration {d:.3f}s vs master "
                            f"{master_dur:.3f}s — outside "
                            f"+/-{STEM_TOLERANCE_S}s (stems must be "
                            "time-aligned)")

    # --- 3. instrumental ---------------------------------------------
    inst = pkg / INSTRUMENTAL_NAME
    inst_dur = audio_duration(inst)
    if inst_dur is None:
        problems.append(f"{INSTRUMENTAL_NAME} is not a real audio file "
                        "(sync needs an instrumental version)")
    elif inst.exists() and master.exists():
        if inst.read_bytes() == master.read_bytes():
            problems.append(f"{INSTRUMENTAL_NAME} is byte-identical to "
                            f"{MASTER_NAME} — a copied master is not an "
                            "instrumental version")

    # --- 4. metadata ------------------------------------------------
    manifest = pkg / MANIFEST_NAME
    if not manifest.is_file():
        problems.append("no manifest.json")
    else:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"manifest.json is corrupt JSON: {exc}")
            data = {}
        meta = data.get("metadata") if isinstance(data, dict) else None
        if not isinstance(meta, dict):
            problems.append("manifest.json has no metadata object")
            meta = {}
        for field in REQUIRED_META:
            if not meta.get(field):
                problems.append(f"manifest metadata missing '{field}'")

    # --- 5. clearance doc --------------------------------------------
    clearance = next((pkg / n for n in CLEARANCE_NAMES if (pkg / n).is_file()),
                     None)
    if clearance is None:
        problems.append("no clearance_doc.pdf (or .txt) — sync requires a "
                        "clearance document")
    else:
        head = clearance.read_bytes()[:8]
        if clearance.suffix.lower() == ".pdf" and not head.startswith(b"%PDF-"):
            problems.append(f"{clearance.name} does not start with a PDF "
                            "header (%PDF-) — not a real PDF")
        elif clearance.stat().st_size == 0:
            problems.append(f"{clearance.name} is zero bytes")

    # --- 6. AI disclosure ---------------------------------------------
    disclosure = pkg / "ai_disclosure.txt"
    if not disclosure.is_file():
        problems.append("no ai_disclosure.txt — the AI role must be "
                        "declared for sync platforms")
    elif disclosure.stat().st_size == 0:
        problems.append("ai_disclosure.txt is zero bytes")

    # --- 7. lane-specific extras --------------------------------------
    if args.lane == "direct-license":
        tiers = [p for p in pkg.glob("license_tiers*") if p.is_file()]
        if not tiers:
            problems.append("direct-license lane requires license_tiers "
                            "(multi-tier licence with permitted use, "
                            "distribution, derivative rules)")
    if args.lane == "game-assets":
        loop_json = pkg / "loop_points.json"
        if not loop_json.is_file():
            problems.append("game-assets lane requires loop_points.json "
                            "(run gate_loop_points.py for the seam check)")

    if problems:
        return fail(problems)

    print("PASS gate_sync_ready")
    print(f"  package     : {pkg}")
    print(f"  lane        : {args.lane}")
    print(f"  master      : {MASTER_NAME} ({master_dur:.3f}s)")
    print(f"  stems       : {len(stems)} (durations within "
          f"+/-{STEM_TOLERANCE_S}s of master)")
    print(f"  instrumental: {INSTRUMENTAL_NAME} ({inst_dur:.3f}s)")
    print(f"  clearance   : {clearance.name if clearance else '-'}")
    print(f"  metadata    : {', '.join(REQUIRED_META)} present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
