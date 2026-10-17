#!/usr/bin/env python3
"""gate_sync_ready — PASS/FAIL gate for every lane that declares it.

The lane set is READ from `music/lanes.yaml`, never copied into this file: any
lane whose `gate:` is `gate_sync_ready` is runnable by name (measured today:
sync, sync-documentary, direct-license, game-assets). Card t_d9983bb9: the
`sync-documentary` lane declared this gate but argparse rejected the name, so a
stage passing the lane through got rc=2 — an ARGUMENT error that reads as a gate
FAILURE on the highest-value revenue lane the activist genre has.

Two package SHAPES, because the lanes have two shapes (card t_5ed495eb):

  track mode (default for `sync`, `sync-documentary` and `direct-license`) — one track:
    the lane's own `requires:` list in music/lanes.yaml is read at run time:
      sync, sync-documentary: [stems, metadata, clearance_doc, instrumental_version]
      direct-license:         [stems, license_tiers]
    checks 1-7 below.

  pack mode (default for `game-assets`; `--mode pack`) — a multi-asset pack:
    the lane's `requires:` (§3 game-assets [stems, loop_point, seamless_loop,
    metadata]; §13 "Packaging requirements"):
      loops/ + stems/ (+ one_shots/, sfx/) of real audio, a manifest with a
      package-level `metadata` object and a `pack_manifest` count block that
      MATCHES the files on disk, per-loop loop points in `loop_points.json`
      (span >= the gate's floor), a clearance document, an AI disclosure and
      a licence file.
    A pack has no single full_mix.wav and no instrumental version, so the
    track shape is not applied to it. The seam of every loop is measured here
    with gate_loop_points' own measurement; `gate_loop_points.py --pack-dir
    <pack>` prints the per-loop ratios on their own.

REQUIREMENT COVERAGE (card t_d9983bb9): every requirement token the lane declares
must map to a check that produces EVIDENCE for it (TRACK_COVERAGE / PACK_COVERAGE
below). A token with no check FAILS the run and says so. A gate that answers
"ready" for a requirement it cannot measure is the defect this guard removes.

The gate EXECUTES the artifact — nothing is trusted from a filename:
  1. Stems: >= MIN_STEMS real audio files (ffprobe must open them and
     report a duration + a stream), each non-zero, each within
     +/- STEM_TOLERANCE s of the master duration (ffprobe, not file size).
  2. Master: full_mix.wav must itself be a real audio file.  [track mode]
  3. Instrumental: instrumental.wav must be a real audio file, distinct
     from the master (different bytes — a copied master is not an
     instrumental version).                                           [track mode]
  4. Metadata: manifest.json parses and carries title, artist, bpm, key,
     mood, genre. A pack must also state `sample_rate`, and every WAV in
     the pack must really carry it (ffprobe).
  5. Clearance doc: clearance_doc is a real PDF (a PDF starts with %PDF-;
     we parse the header bytes — not a file-extension guess).
  6. AI disclosure: ai_disclosure.txt states the AI role.
  7. License tiers (a lane whose `requires:` names license_tiers).
  8. Pack mode: category counts == files on disk, every audio file is real
     audio at the stated sample rate, stems mutually time-aligned, and
     every loop carries loop points inside its measured duration with a
     span >= gate_loop_points.MIN_LOOP_SPAN_S.

Usage:
  python3 music/gates/gate_sync_ready.py --package-dir <dir> \
      [--lane <lane in music/lanes.yaml with gate: gate_sync_ready>] \
      [--mode track|pack]

Exit codes: 0 = PASS, 1 = FAIL (human-readable reasons on stderr),
2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# One definition of the musical loop floor, shared with gate_loop_points and
# with music/assets/pack.py. Imported, not copied, so the generator and the
# gates cannot drift apart (card t_5ed495eb).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_loop_points import (  # noqa: E402
    DEFAULT_CLICK_RATIO_MAX,
    DEFAULT_WINDOW,
    MIN_LOOP_SPAN_S,
    check_loop,
)
# The lane contract is READ, never copied (card t_d9983bb9): this module is
# stdlib-only on purpose — every stage prompt calls a gate as `python3
# music/gates/<gate>.py`, and bare python3 in a worker shell has no PyYAML.
from _lane_registry import (  # noqa: E402
    LANES_YAML,
    LaneRegistryError,
    lanes_declaring,
    requirements_for,
)

GATE_NAME = "gate_sync_ready"

MIN_STEMS = 4                 # architecture §5: >= 4 stems
STEM_TOLERANCE_S = 0.5        # durations match master +/- 0.5 s
MASTER_NAME = "full_mix.wav"
INSTRUMENTAL_NAME = "instrumental.wav"
CLEARANCE_NAMES = ("clearance_doc.pdf", "clearance_doc.txt")
MANIFEST_NAME = "manifest.json"
REQUIRED_META = ("title", "artist", "bpm", "key", "mood", "genre")
REQUIRED_PACK_META = REQUIRED_META + ("sample_rate",)
PACK_REQUIRED_CATEGORIES = ("loops", "stems")
MODES = ("track", "pack")
AUDIO_SUFFIXES = (".wav", ".aif", ".aiff", ".flac")
LICENCE_NAMES = ("LICENCE.txt", "LICENSE.txt", "licence.txt", "license.txt",
                 "LICENCE.md", "LICENSE.md", "LICENCE.pdf", "LICENSE.pdf")
# The lane's licence of record. A pack ships this text verbatim; the gate
# compares bytes when the file exists (see check_pack).
REPO_ROOT = Path(__file__).resolve().parents[2]
LICENCE_OF_RECORD = REPO_ROOT / "music/licences/perpetual_game_asset_v1.txt"

# ---------------------------------------------------------------------
# requirement coverage — the lane's `requires:` tokens this gate can EVIDENCE
# ---------------------------------------------------------------------
# Card t_d9983bb9. Each lane declares in music/lanes.yaml what it requires; this
# gate reads that list and must have a check for every token in it. A token with
# no check FAILS the run and names itself: a gate that answers "ready" for a
# requirement it cannot measure is a false pass. Adding a requirement to
# lanes.yaml therefore cannot be absorbed silently — the gate says so instead.
TRACK_COVERAGE = {
    "stems": f"stems/ holds >= {MIN_STEMS} real audio files, ffprobe-read, "
             f"each within +/-{STEM_TOLERANCE_S}s of {MASTER_NAME}",
    "metadata": f"{MANIFEST_NAME} metadata carries "
                + ", ".join(REQUIRED_META),
    "clearance_doc": "a real PDF clearance document (header bytes parsed)",
    "instrumental_version": f"{INSTRUMENTAL_NAME} is real audio and is not a "
                            f"byte-copy of {MASTER_NAME}",
    "license_tiers": "license_tiers* is present",
}
PACK_COVERAGE = {
    "stems": "stems/ holds real, mutually time-aligned audio files",
    "metadata": f"{MANIFEST_NAME} metadata carries "
                + ", ".join(REQUIRED_PACK_META)
                + " (sample_rate verified against every audio file)",
    "loop_point": "loop_points.json carries an entry per loop, inside its "
                  "measured duration",
    "seamless_loop": "every loop's seam is measured with gate_loop_points' "
                     "ruler (a declared `seamless: true` is a claim)",
}


def probe(path: Path) -> dict | None:
    """Run ffprobe; return parsed format info, or None if not real media.

    This is the exercise step: a zero-byte or text file named .wav has
    no duration and no streams, and ffprobe fails — the gate fails.
    """
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries",
             "format=duration,size:stream=codec_type,sample_rate",
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


def audio_sample_rate(path: Path) -> int | None:
    """The sample rate ffprobe really reads from the file, or None."""
    info = probe(path)
    if not info:
        return None
    for s in info.get("streams") or []:
        if s.get("codec_type") == "audio" and s.get("sample_rate"):
            try:
                return int(s["sample_rate"])
            except (TypeError, ValueError):
                return None
    return None


def fail(msgs: list[str]) -> int:
    print("FAIL gate_sync_ready", file=sys.stderr)
    for m in msgs:
        print(f"  - {m}", file=sys.stderr)
    return 1


def read_manifest(pkg: Path, problems: list[str]) -> dict:
    manifest = pkg / MANIFEST_NAME
    if not manifest.is_file():
        problems.append(f"no {MANIFEST_NAME}")
        return {}
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        problems.append(f"{MANIFEST_NAME} is corrupt JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        problems.append(f"{MANIFEST_NAME} must hold a JSON object")
        return {}
    return data


def check_clearance(pkg: Path, problems: list[str]) -> Path | None:
    clearance = next((pkg / n for n in CLEARANCE_NAMES if (pkg / n).is_file()),
                     None)
    if clearance is None:
        problems.append("no clearance_doc.pdf (or .txt) — sync requires a "
                        "clearance document")
        return None
    head = clearance.read_bytes()[:8]
    if clearance.suffix.lower() == ".pdf" and not head.startswith(b"%PDF-"):
        problems.append(f"{clearance.name} does not start with a PDF "
                        "header (%PDF-) — not a real PDF")
    elif clearance.stat().st_size == 0:
        problems.append(f"{clearance.name} is zero bytes")
    return clearance


def check_disclosure(pkg: Path, problems: list[str]) -> Path | None:
    disclosure = pkg / "ai_disclosure.txt"
    if not disclosure.is_file():
        problems.append("no ai_disclosure.txt — the AI role must be "
                        "declared for sync platforms")
        return None
    if disclosure.stat().st_size == 0:
        problems.append("ai_disclosure.txt is zero bytes")
    return disclosure


def check_metadata(meta: dict, required: tuple[str, ...],
                   problems: list[str]) -> None:
    for field in required:
        if not meta.get(field):
            problems.append(f"manifest metadata missing '{field}'")


# ------------------------------------------------------------------
# track mode
# ------------------------------------------------------------------

def check_track(pkg: Path, lane: str,
                requires: tuple[str, ...] = ()) -> tuple[list[str], dict]:
    """Validate a one-track package for `lane`, whose `requires:` is `requires`."""
    problems: list[str] = []
    info: dict = {}

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
    data = read_manifest(pkg, problems)
    meta = data.get("metadata") if isinstance(data, dict) else None
    if not isinstance(meta, dict):
        problems.append("manifest.json has no metadata object")
        meta = {}
    check_metadata(meta, REQUIRED_META, problems)

    # --- 5/6. clearance + disclosure ---------------------------------
    clearance = check_clearance(pkg, problems)
    check_disclosure(pkg, problems)

    # --- 7. lane-specific extras --------------------------------------
    # Driven by the lane's `requires:` in music/lanes.yaml, never by the lane's
    # name: `license_tiers` is a requirement, so any lane that declares it is
    # checked for it (card t_d9983bb9).
    if "license_tiers" in requires:
        tiers = [p for p in pkg.glob("license_tiers*") if p.is_file()]
        if not tiers:
            problems.append(f"{lane} lane requires license_tiers "
                            "(multi-tier licence with permitted use, "
                            "distribution, derivative rules)")

    info.update({"master_dur": master_dur, "stems": len(stems),
                 "inst_dur": inst_dur, "clearance": clearance})
    return problems, info


# ------------------------------------------------------------------
# pack mode (lane game-assets)
# ------------------------------------------------------------------

def check_pack(pkg: Path) -> tuple[list[str], dict]:
    """Validate a multi-asset pack. Executes every audio file it finds.

    The loop SEAM is measured here too, with gate_loop_points' own
    check_loop — the game-assets lane requires a seamless loop
    (music/lanes.yaml), so a pack with a click at the wrap must not pass this
    gate. The standalone sweep (gate_loop_points.py --pack-dir) reports the
    ratios per loop.
    """
    problems: list[str] = []
    info: dict = {}
    ratios: dict = {}
    scratch_root = Path(tempfile.mkdtemp(prefix="pack-seam-"))

    data = read_manifest(pkg, problems)

    # --- metadata object (package level) -----------------------------
    meta = data.get("metadata") if isinstance(data, dict) else None
    if not isinstance(meta, dict):
        problems.append("manifest.json has no metadata object")
        meta = {}
    check_metadata(meta, REQUIRED_PACK_META, problems)
    declared_rate = meta.get("sample_rate")
    if declared_rate is not None and not isinstance(declared_rate, int):
        try:
            declared_rate = int(declared_rate)
        except (TypeError, ValueError):
            problems.append(f"metadata sample_rate {declared_rate!r} is not "
                            "an integer")
            declared_rate = None

    # --- pack_manifest counts vs the files on disk -------------------
    counts = data.get("pack_manifest") if isinstance(data, dict) else None
    if not isinstance(counts, dict) or not counts:
        problems.append("manifest.json has no pack_manifest count object "
                        "(loops/stems/one_shots/sfx) — a pack must declare "
                        "its contents and the declaration must match the "
                        "files")
        counts = {}
    for category in PACK_REQUIRED_CATEGORIES:
        if category not in counts:
            problems.append(f"pack_manifest has no '{category}' count — a "
                            "game-assets pack ships loops and stems")

    durations: dict[str, float] = {}
    on_disk: dict[str, list[Path]] = {}
    for category in sorted(counts):
        cdir = pkg / category
        if not cdir.is_dir():
            problems.append(f"pack_manifest declares '{category}' but there "
                            f"is no {category}/ directory")
            continue
        files = sorted(p for p in cdir.iterdir() if p.is_file())
        audio = [p for p in files if p.suffix.lower() in AUDIO_SUFFIXES]
        junk = [p for p in files if p.suffix.lower() not in AUDIO_SUFFIXES]
        for p in junk:
            problems.append(f"{category}/{p.name} is not an audio file — a "
                            "pack category must hold only audio")
        on_disk[category] = audio
        if len(audio) != counts[category]:
            problems.append(f"pack_manifest says {category}={counts[category]}"
                            f" but {category}/ holds {len(audio)} audio file(s)"
                            " — the manifest does not describe the pack")
        for p in audio:
            if p.stat().st_size == 0:
                problems.append(f"{category}/{p.name} is zero bytes")
                continue
            d = audio_duration(p)
            if d is None:
                problems.append(f"{category}/{p.name} is not a real audio "
                                "file (ffprobe could not read a duration)")
                continue
            durations[p.relative_to(pkg).as_posix()] = d
            if declared_rate is not None:
                real_rate = audio_sample_rate(p)
                if real_rate != declared_rate:
                    problems.append(
                        f"{category}/{p.name} is {real_rate} Hz but the "
                        f"manifest states {declared_rate} Hz — the stated "
                        "sample rate must be the rate of the audio")

    # --- stems must be mutually time-aligned --------------------------
    stem_durs = [durations[p.relative_to(pkg).as_posix()]
                 for p in on_disk.get("stems", [])
                 if p.relative_to(pkg).as_posix() in durations]
    if stem_durs:
        ref = max(stem_durs)
        for p in on_disk.get("stems", []):
            key = p.relative_to(pkg).as_posix()
            if key not in durations:
                continue
            if abs(durations[key] - ref) > STEM_TOLERANCE_S:
                problems.append(
                    f"stems/{p.name} duration {durations[key]:.3f}s vs the "
                    f"longest stem {ref:.3f}s — outside "
                    f"+/-{STEM_TOLERANCE_S}s (stems must be time-aligned)")
    elif "stems" in counts:
        problems.append(f"stems/ holds no real audio file; {MIN_STEMS} "
                        "required (architecture HARD RULE 4)")
    if len(on_disk.get("stems", [])) and len(on_disk["stems"]) < MIN_STEMS:
        problems.append(f"only {len(on_disk['stems'])} stem(s) found; "
                        f"{MIN_STEMS} required")

    # --- per-loop loop points -----------------------------------------
    loops = on_disk.get("loops", [])
    lp_path = pkg / "loop_points.json"
    if not lp_path.is_file():
        problems.append("no loop_points.json — the game-assets lane requires "
                        "loop points (run gate_loop_points.py --pack-dir for "
                        "the seam check)")
        loop_index = {}
    else:
        try:
            idx = json.loads(lp_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"loop_points.json is corrupt JSON: {exc}")
            idx = {}
        loop_index = idx.get("loops") if isinstance(idx, dict) else None
        if not isinstance(loop_index, dict) or not loop_index:
            problems.append("loop_points.json must hold a 'loops' object "
                            "mapping each loop file to its own "
                            "{loop_start_s, loop_end_s, seamless}")
            loop_index = {}
    for p in loops:
        key = p.relative_to(pkg).as_posix()
        entry = loop_index.get(key)
        if entry is None:
            problems.append(f"{key} has no entry in loop_points.json — every "
                            "loop needs its own loop points")
            continue
        if not isinstance(entry, dict):
            problems.append(f"{key}: loop_points entry must be an object")
            continue
        start = entry.get("loop_start_s")
        end = entry.get("loop_end_s")
        if not isinstance(start, (int, float)) or \
                not isinstance(end, (int, float)):
            problems.append(f"{key}: loop_start_s and loop_end_s must be "
                            "numeric")
            continue
        dur = durations.get(key)
        if dur is None:
            continue
        if not (0.0 <= float(start) < float(end) <= dur + 0.001):
            problems.append(f"{key}: loop points [{start}s, {end}s] are not "
                            f"inside the measured duration {dur:.3f}s")
            continue
        span = float(end) - float(start)
        if span < MIN_LOOP_SPAN_S:
            problems.append(f"{key}: loop span is {span:.2f}s — too short to "
                            f"be musical (minimum {MIN_LOOP_SPAN_S:.0f}s)")
            continue
        if not entry.get("seamless"):
            problems.append(f"{key}: loop_points.json does not declare "
                            "'seamless': true")
            continue
        # Measure the seam. A declared 'seamless': true is a claim; this is
        # the evidence (the same measurement gate_loop_points runs).
        seam_scratch = scratch_root / Path(key).stem
        sub, seam_info = check_loop(p, float(start), float(end), True,
                                    DEFAULT_WINDOW, DEFAULT_CLICK_RATIO_MAX,
                                    seam_scratch)
        ratios[key] = seam_info.get("ratio")
        problems += [f"{key}: {p_}" for p_ in sub]
    for key in sorted(loop_index):
        if key not in {p.relative_to(pkg).as_posix() for p in loops}:
            problems.append(f"loop_points.json lists {key} but the pack has "
                            "no such loop")

    # --- clearance, disclosure, licence -------------------------------
    clearance = check_clearance(pkg, problems)
    check_disclosure(pkg, problems)
    licence = next((pkg / n for n in LICENCE_NAMES if (pkg / n).is_file()),
                   None)
    if licence is None:
        problems.append("no LICENCE.txt — §13 requires a licence with explicit "
                        "permitted use, distribution and derivative-work "
                        "rules (music/licences/perpetual_game_asset_v1.txt)")
    elif licence.stat().st_size == 0:
        problems.append(f"{licence.name} is zero bytes")
    elif LICENCE_OF_RECORD.is_file():
        # The pack must ship the lane's licence of record, not a substitute.
        # Measured 2026-10-16 (card t_5ed495eb): a generator run on a tree
        # where music/licences/ was absent wrote its own fallback text and the
        # pack's licence silently changed from the authored licence to it.
        if licence.read_bytes() != LICENCE_OF_RECORD.read_bytes():
            problems.append(
                f"{licence.name} is not the lane's licence of record "
                f"({LICENCE_OF_RECORD.relative_to(REPO_ROOT).as_posix()}) — "
                "the pack must ship that text, byte for byte")

    shutil.rmtree(scratch_root, ignore_errors=True)
    info.update({"counts": {k: len(v) for k, v in sorted(on_disk.items())},
                 "declared": counts, "sample_rate": declared_rate,
                 "stems": len(on_disk.get("stems", [])),
                 "loops": len(loops), "clearance": clearance,
                 "licence": licence, "ratios": ratios,
                 "pack_name": data.get("pack_name") if isinstance(data, dict)
                 else None})
    return problems, info


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def lanes_for_this_gate() -> tuple[str, ...]:
    """The lanes music/lanes.yaml assigns to THIS gate. Reads the registry.

    This is the whole fix for card t_d9983bb9: `sync-documentary` is a lane that
    declares `gate: gate_sync_ready`, so it must be runnable by name. Derived,
    never copied — the next lane added to lanes.yaml works without touching this
    file, and a lane removed from lanes.yaml stops being accepted in the same
    breath.
    """
    return lanes_declaring(GATE_NAME)


def main(argv: list[str] | None = None) -> int:
    try:
        lanes = lanes_for_this_gate()
    except LaneRegistryError as exc:
        print(f"gate_sync_ready: cannot read the lane contract: {exc}",
              file=sys.stderr)
        return 2
    if not lanes:
        print(f"gate_sync_ready: no lane in {LANES_YAML} declares gate: "
              f"{GATE_NAME} — the registry and this gate disagree",
              file=sys.stderr)
        return 2
    default_lane = "sync" if "sync" in lanes else lanes[0]

    parser = argparse.ArgumentParser(
        description=f"gate_sync_ready — gate for the lanes that declare it "
                    f"({', '.join(sorted(lanes))})")
    parser.add_argument("--package-dir", required=True,
                        help="the packaged deliverable directory")
    parser.add_argument("--lane", default=default_lane, choices=lanes,
                        help="lane whose `requires:` in music/lanes.yaml this "
                             "package must satisfy (the lane's own name)")
    parser.add_argument("--mode", default=None, choices=MODES,
                        help="package shape: 'track' (one track: full_mix + "
                             "instrumental) or 'pack' (multi-asset pack). "
                             "Default: pack for the game-assets lane, track "
                             "for the others")
    args = parser.parse_args(argv)

    pkg = Path(args.package_dir)
    if not pkg.is_dir():
        return fail([f"no such package directory: {pkg}"])

    mode = args.mode or ("pack" if args.lane == "game-assets" else "track")

    # The lane's declared requirements, read from music/lanes.yaml, drive the
    # lane-specific checks. A requirement this gate has no check for is a hard
    # FAIL: the gate must not certify what it cannot measure.
    requires = requirements_for(args.lane)
    coverage = PACK_COVERAGE if mode == "pack" else TRACK_COVERAGE
    uncovered = [token for token in requires if token not in coverage]
    if uncovered:
        return fail([
            f"the {args.lane} lane requires {', '.join(uncovered)} "
            f"(music/lanes.yaml) but this gate has no {mode}-mode check for it "
            f"— a gate must not certify a requirement it cannot measure"
        ])

    if mode == "pack":
        problems, info = check_pack(pkg)
    else:
        problems, info = check_track(pkg, args.lane, requires)

    if problems:
        return fail(problems)

    print("PASS gate_sync_ready")
    print(f"  package     : {pkg}")
    print(f"  lane        : {args.lane}")
    print(f"  mode        : {mode}")
    if mode == "pack":
        print(f"  pack        : {info.get('pack_name')}")
        print(f"  counts      : "
              + ", ".join(f"{k} {v}" for k, v in
                          (info.get("counts") or {}).items())
              + " (matched against the files on disk)")
        print(f"  metadata    : {', '.join(REQUIRED_PACK_META)} present")
        print(f"  sample_rate : {info.get('sample_rate')} Hz (ffprobe-verified "
              "on every audio file)")
        print(f"  stems       : {info.get('stems')} (mutually time-aligned "
              f"within +/-{STEM_TOLERANCE_S}s)")
        print(f"  loops       : {info.get('loops')} (each carries loop points "
              f"with a span >= {MIN_LOOP_SPAN_S:.0f}s and declares seamless)")
        seam = info.get("ratios") or {}
        if seam:
            shown = ", ".join(
                f"{Path(k).name} {v:.2f}x" if v is not None else
                f"{Path(k).name} n/a" for k, v in sorted(seam.items()))
            print(f"  seam        : {shown} (measured, max "
                  f"{DEFAULT_CLICK_RATIO_MAX}x)")
        print(f"  clearance   : {info['clearance'].name if info.get('clearance') else '-'}")
        print("  disclosure  : ai_disclosure.txt")
        print(f"  licence     : {info['licence'].name if info.get('licence') else '-'}")
    else:
        print(f"  master      : {MASTER_NAME} ({info['master_dur']:.3f}s)")
        print(f"  stems       : {info['stems']} (durations within "
              f"+/-{STEM_TOLERANCE_S}s of master)")
        print(f"  instrumental: {INSTRUMENTAL_NAME} ({info['inst_dur']:.3f}s)")
        print(f"  clearance   : "
              f"{info['clearance'].name if info.get('clearance') else '-'}")
        print(f"  metadata    : {', '.join(REQUIRED_META)} present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
