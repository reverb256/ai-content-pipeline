#!/usr/bin/env python3
"""check_pack_manifest_paths — every asset a pack manifest declares must RESOLVE,
and the generator must read its one-shot source from the path it declared.

WHY THIS EXISTS (incident 2026-10-16, card t_5f814f2f)
------------------------------------------------------
`music/assets/pack.py` writes two locations for one artifact: `path`
(pack-relative) and `file` (relative to the PACK TREE ROOT — the directory that
holds the pack's own parent; the repository root for every pack that ships, which
is why the committed manifest reads
`packages/welcome-asset-pack/stems/02_drums.wav`). The one-shot cutter read that
field against the WRONG base:

    drum_stem_path = Path(__file__).resolve().parents[1] / s["file"]   # music/!
    if drum_stem_path.exists():        # ... never true, and never said so
        d, _ = load_wav(str(drum_stem_path))
        drum_stem = d
        break

Measured on nexus the same day, against the committed pack:

    music/packages/welcome-asset-pack/stems/02_drums.wav   exists=False
    <repo>/packages/welcome-asset-pack/stems/02_drums.wav  exists=True

Two defects in one line: a field with two meanings, and a guard whose miss was
SILENT. The one-shots came from a SECOND `hpss(x, sr)` computed in `main()`
instead of from the saved stem, and that bus happened to be the same audio —
which is exactly why no check caught it. The day the declared drum stem stops
being the raw percussive bus, the pack would ship one-shots nobody declared.

Rules enforced (FAIL)
---------------------
1. RESOLUTION — for every entry of `loops` / `stems` / `one_shots` / `sfx` that
   declares a `path`, the `file` field must be present, must resolve under the
   pack tree, the `path` must resolve under the pack directory, and both must
   name the SAME file. Resolved by the generator's own
   `resolve_manifest_file()` — imported, never re-implemented, so this check and
   the generator cannot drift apart.
2. DECLARED SOURCE — the one-shots' drum bus must come from the DECLARED stem.
   The check writes a marker signal into a fixture's declared drum stem and
   requires the generator's loader to return THAT signal; on a real pack it
   requires the declared stem to load and to be as long as the manifest says.
   A reader that recomputes a bus, or resolves the field elsewhere, fails here.
   This is the rule that would have caught the incident.
3. LOUD MISS — a declared path that does not resolve (missing file, `file` and
   `path` disagreeing, no `file` at all) must make the generator's loader RAISE.
   A loader that returns a fallback instead is the silent guard; it fails.
4. OUT-OF-TREE BUILD — the REAL generator is run on a synthesized master into a
   directory OUTSIDE the repository, and its freshly written manifest must pass
   rules 1-3. `file` is tree-root-relative, not repo-root-relative: a writer that
   hardcodes the repository root cannot make this leg resolve (and cannot build
   out-of-tree at all, which is how the gate fixtures build packs).
5. IN-TREE PACKS — every pack already in the repository
   (`packages/*/manifest.json`, plus any `--pack-dir`) passes rules 1-3.

cited: t_5f814f2f (this incident) · t_5ed495eb (the manifest/gate contract this
       field must keep saying) · t_eb079b91 (the stage that builds packs) ·
       t_4906bc6e (the same generator, another fabricated field)

Usage:
  /usr/bin/python3 music/scripts/check_pack_manifest_paths.py [--repo DIR]
      [--pack-dir DIR ...] [--no-build] [--json]
  /usr/bin/python3 music/scripts/check_pack_manifest_paths.py --selftest

Exit codes: 0 = every rule holds, 1 = at least one violation, 2 = cannot read the
inputs (generator not importable under this interpreter, no manifest to read).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

DEFAULT_REPO = Path(__file__).resolve().parents[2]
GENERATOR = "music/assets/pack.py"
CATEGORIES = ("loops", "stems", "one_shots", "sfx")
# The build leg: the lane's own default genre, which the generator validates
# against music/genres.yaml, at a tempo/key the manifest then declares.
BUILD_GENRE = "chill-lounge"
BUILD_BPM = 120.0
BUILD_KEY = "A minor"
BUILD_SECONDS = 30.0
FIXTURE_RATE = 44100
FIXTURE_SECONDS = 0.05
MARKER = 0.5                  # the peak a marker stem carries
MARKER_TOL = 1e-3             # the 16-bit round trip is ~3e-5; a wrong bus is ~0.5
LENGTH_TOL_MS = 2             # manifest durations are rounded to 3 decimals


class CheckError(RuntimeError):
    """The inputs cannot be read. Never report a PASS on unreadable inputs."""


# ── the generator, imported (not re-implemented) ────────────────────────────
def load_generator(repo: Path):
    """Import `music/assets/pack.py` so this check resolves manifest paths with
    the SAME code that writes and reads them."""
    path = repo / GENERATOR
    if not path.is_file():
        raise CheckError(f"no generator at {path}")
    spec = importlib.util.spec_from_file_location("packgen_under_check", path)
    if spec is None or spec.loader is None:
        raise CheckError(f"{path} is not importable")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod      # dataclasses needs the module registered
    try:
        spec.loader.exec_module(mod)
    except ImportError as exc:
        raise CheckError(
            f"this interpreter cannot import {GENERATOR} ({exc}); it needs "
            f"numpy + scipy — re-run it with the lane's pinned /usr/bin/python3"
        ) from exc
    return mod


def require_generator_api(gen) -> list[str]:
    """The single definition of the manifest's `file` field must exist in the
    generator. A revision that loses it has lost the fix (card t_5f814f2f)."""
    required = ("DRUM_STEM", "manifest_tree_root", "manifest_file",
                "resolve_manifest_file", "declared_drum_bus",
                "ManifestPathError")
    return [n for n in required if not hasattr(gen, n)]


def pre_fix_reader(gen, repo: Path):
    """The one-shot loader as it was BEFORE this card, reconstructed so the
    selftest can prove rule 2 catches it: resolve `file` against `music/`,
    swallow the miss, fall back to a recomputed bus (here: silence)."""
    def reader(stems, out_dir, sr):
        for s in stems:
            name = str(s.get("name", ""))
            if "drum" in name.lower() or name.startswith("02_"):
                candidate = repo / "music" / str(s.get("file", ""))
                if candidate.exists():
                    return gen.load_wav(str(candidate))[0]
                break
        return gen.np.zeros(int(sr), dtype=gen.np.float32)   # the silent fallback
    return reader


def repo_root_reader(gen, repo: Path):
    """A reader that assumes `file` is relative to the REPOSITORY ROOT. Right for
    the packs that ship, wrong for a pack built outside the tree — the confusion
    this card is about."""
    def reader(stems, out_dir, sr):
        for s in stems:
            if str(s.get("name")) == gen.DRUM_STEM:
                return gen.load_wav(str(repo / str(s["file"])))[0]
        raise LookupError("no drum stem")
    return reader


# ── fixture: a pack written the way the generator writes one ────────────────
def _tiny_wav(path: Path, value: float, seconds: float = FIXTURE_SECONDS,
              rate: int = FIXTURE_RATE) -> None:
    """A deterministic WAV: `value` on even samples, -value on odd."""
    n = int(rate * seconds)
    frames = bytearray()
    for i in range(n):
        v = value if i % 2 == 0 else -value
        frames += int(v * 32767).to_bytes(2, "little", signed=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


def build_fixture(gen, tree: Path, pack_name: str = "fixture-pack",
                  marker: float = MARKER, drums: bool = True,
                  dress=None) -> Path:
    """Write a minimal pack under `tree`, its `file` fields produced by the
    generator's own `manifest_file()`. `dress(manifest)` may mutate the manifest
    before it is written — that is how the selftest builds failure shapes."""
    pack_dir = tree / pack_name
    entries: dict[str, list[dict]] = {}
    for category, name, value in (
            ("loops", "loop_01_bpm120_key-Aminor.wav", 0.4),
            ("stems", "01_bass.wav", 0.3),
            ("one_shots", "oneshot_kick_01.wav", 0.2),
            ("sfx", "fire_whoosh_01.wav", 0.1)):
        p = pack_dir / category / name
        _tiny_wav(p, value)
        entries[category] = [{
            "path": f"{category}/{name}",
            "file": gen.manifest_file(p, pack_dir),
            "name": name,
            "duration_sec": round(FIXTURE_SECONDS, 3),
            "rms_db": -20.0,
        }]
    if drums:
        p = pack_dir / "stems" / f"{gen.DRUM_STEM}.wav"
        _tiny_wav(p, marker)
        entries["stems"].append({
            "path": f"stems/{gen.DRUM_STEM}.wav",
            "file": gen.manifest_file(p, pack_dir),
            "name": gen.DRUM_STEM,
            "duration_sec": round(FIXTURE_SECONDS, 3),
            "rms_db": -20.0,
        })
    manifest: dict = {
        "schema": "music/asset-pack/v1",
        "pack_name": pack_name,
        "metadata": {"sample_rate": FIXTURE_RATE},
        "counts": {c: len(entries[c]) for c in CATEGORIES},
    }
    manifest.update(entries)
    if dress is not None:
        dress(manifest)
    (pack_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                            encoding="utf-8")
    return pack_dir


# ── the rules ───────────────────────────────────────────────────────────────
def check_pack(pack_dir: Path, gen, reader=None,
               marker: float | None = None) -> list[str]:
    """Rules 1-3 for one pack directory. Returns problem strings (empty = OK).

    `reader` is the generator's one-shot loader (injectable so the selftest can
    run the PRE-FIX reader through these rules). `marker` is the peak the
    declared drum stem is known to carry; None means the stem is real audio and
    only its declared length is checked.
    """
    reader = reader or gen.declared_drum_bus
    problems: list[str] = []
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.is_file():
        return [f"{pack_dir}: no manifest.json"]
    try:
        man = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{manifest_path}: cannot read: {exc}"]

    # --- rule 1: every declared asset resolves, both fields, same file ------
    for category in CATEGORIES:
        for entry in man.get(category) or []:
            if not entry.get("path") and not entry.get("file"):
                continue
            try:
                gen.resolve_manifest_file(entry, pack_dir)
            except Exception as exc:                       # noqa: BLE001
                label = (entry.get("name") or entry.get("label")
                         or entry.get("path") or "?")
                problems.append(f"{category}/{label}: {exc}")

    # --- rule 2: the one-shots' source is the DECLARED stem -----------------
    stems = man.get("stems") or []
    names = [str(s.get("name")) for s in stems]
    rate = int((man.get("metadata") or {}).get("sample_rate") or FIXTURE_RATE)
    if gen.DRUM_STEM not in names:
        problems.append(
            f"stems: no {gen.DRUM_STEM!r} entry ({', '.join(names) or 'none'}) — "
            f"the one-shots have no declared source")
    else:
        entry = next(s for s in stems if str(s.get("name")) == gen.DRUM_STEM)
        try:
            bus = reader(stems, pack_dir, rate)
            peak = float(gen.np.max(gen.np.abs(bus))) if len(bus) else 0.0
            if marker is not None and abs(peak - marker) > MARKER_TOL:
                problems.append(
                    f"one-shot source: the declared stem carries markers at "
                    f"{marker} but the loader returned peak {peak:.4f} — the "
                    f"one-shots are NOT cut from the stem the manifest declares")
            want = float(entry.get("duration_sec") or 0.0) * rate
            if want and abs(len(bus) - want) > rate * LENGTH_TOL_MS / 1000.0:
                problems.append(
                    f"one-shot source: the declared stem is {len(bus)} samples "
                    f"but the manifest declares {entry.get('duration_sec')}s "
                    f"({want:.0f} samples) — the manifest and the audio disagree")
        except Exception as exc:                            # noqa: BLE001
            problems.append(f"one-shot source: the declared stem did not load: "
                            f"{exc}")

    # --- rule 3: a miss is LOUD --------------------------------------------
    for entry in stems:
        if not entry.get("path"):
            continue
        name = str(entry.get("name", ""))
        if name != gen.DRUM_STEM and "drum" not in name.lower():
            continue        # the loader only ever reads the drum stem
        variants = []
        e = dict(entry, file="does/not/exist.wav")
        variants.append(("`file` does not resolve", e))
        e = dict(entry)
        e.pop("file", None)
        variants.append(("no `file` is declared", e))
        e = dict(entry, file=str(entry.get("file", "")) + ".gone")
        variants.append(("`file` names a file that is not there", e))
        for label, broken in variants:
            try:
                reader([broken], pack_dir, rate)
                problems.append(
                    f"loud miss: the loader RETURNED for a stem whose {label} — "
                    f"an unresolved manifest path must raise, never fall back")
            except Exception:                               # noqa: BLE001
                pass
    return problems


def in_tree_packs(repo: Path, extra: list[Path]) -> list[Path]:
    packs = sorted(p.parent for p in (repo / "packages").glob("*/manifest.json"))
    for d in extra:
        if d not in packs:
            packs.append(d)
    return packs


# ── rule 4: the real generator, building OUTSIDE the repository ─────────────
def _synthesize_master(path: Path, seconds: float, bpm: float,
                       rate: int = FIXTURE_RATE) -> None:
    n = int(rate * seconds)
    spb = 60.0 / bpm
    frames = bytearray()
    for i in range(n):
        t = i / rate
        kick = math.exp(-((t % spb) / 0.06)) * math.sin(2 * math.pi * 55 * t)
        tone = 0.35 * math.sin(2 * math.pi * 220 * t) \
            + 0.2 * math.sin(2 * math.pi * 330 * t)
        s = max(-1.0, min(1.0, kick + tone * 0.5))
        frames += int(s * 30000).to_bytes(2, "little", signed=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


def built_pack(repo: Path) -> tuple[Path | None, list[str], str]:
    """Run the generator into a temp tree OUTSIDE the repository."""
    tmp = Path(tempfile.mkdtemp(prefix="check-pack-tree-"))
    master = tmp / "master.wav"
    _synthesize_master(master, BUILD_SECONDS, BUILD_BPM)
    pack_dir = tmp / "pack"
    proc = subprocess.run(
        [sys.executable, str(repo / GENERATOR), str(master),
         "--out", str(pack_dir), "--pack-name", "check-pack",
         "--genre", BUILD_GENRE, "--bpm", str(BUILD_BPM), "--key", BUILD_KEY,
         "--title", "Manifest Path Check", "--mood", "neutral"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr.strip() or proc.stdout.strip())[-300:]
        return None, [f"the generator exited {proc.returncode} building "
                      f"out-of-tree: {tail}"], f"rc={proc.returncode}"
    return pack_dir, [], (f"built {pack_dir.name} out-of-tree "
                          f"(tree root {tmp.name}) rc=0")


# ── selftest ────────────────────────────────────────────────────────────────
def selftest(repo: Path) -> tuple[int, list[str]]:
    gen = load_generator(repo)
    tmp = Path(tempfile.mkdtemp(prefix="check-pack-selftest-"))
    shapes: list[tuple[str, bool, list[str]]] = []
    try:
        # control: what the writer produces → PASS
        shapes.append(("a pack written the way the generator writes one "
                       "(control)", False,
                       check_pack(build_fixture(gen, tmp / "good"), gen,
                                  marker=MARKER)))

        # the incident's wrong base: `file` resolved under music/ → FAIL rule 1
        def pre_fix_base(man):
            for cat in CATEGORIES:
                for e in man[cat]:
                    e["file"] = "music/" + e["file"]
        shapes.append(("`file` rewritten to the pre-fix base (music/<file>)", True,
                       check_pack(build_fixture(gen, tmp / "s2", dress=pre_fix_base),
                                  gen, marker=MARKER)))

        # `file` naming a stem that is not on disk → FAIL rule 1
        def missing(man):
            for e in man["stems"]:
                e["file"] = str(Path(e["file"]).with_name("02_drums_GONE.wav"))
        shapes.append(("`file` names a stem that is not on disk", True,
                       check_pack(build_fixture(gen, tmp / "s3", dress=missing),
                                  gen, marker=MARKER)))

        # `file` and `path` naming different files → FAIL rule 1
        def disagree(man):
            man["stems"][1]["file"] = man["stems"][0]["file"]
        shapes.append(("`file` and `path` name different files", True,
                       check_pack(build_fixture(gen, tmp / "s4", dress=disagree),
                                  gen, marker=MARKER)))

        # no `file` at all → FAIL rule 1
        def no_file(man):
            man["stems"][1].pop("file", None)
        shapes.append(("an asset entry declares no `file`", True,
                       check_pack(build_fixture(gen, tmp / "s5", dress=no_file),
                                  gen, marker=MARKER)))

        # no declared drum stem → FAIL rule 2
        shapes.append(("the stems declare no drum bus", True,
                       check_pack(build_fixture(gen, tmp / "s6", drums=False),
                                  gen, marker=MARKER)))

        # the declared stem deleted from disk → FAIL (rule 1, and rule 3 loudly)
        s7 = build_fixture(gen, tmp / "s7")
        (s7 / "stems" / f"{gen.DRUM_STEM}.wav").unlink()
        shapes.append(("the declared drum stem was deleted from disk", True,
                       check_pack(s7, gen, marker=MARKER)))

        # THE INCIDENT: the pre-fix reader (wrong base + silent fallback)
        shapes.append(("the pre-fix reader cannot see the declared stem (the "
                       "incident)", True,
                       check_pack(build_fixture(gen, tmp / "s8"), gen,
                                  reader=pre_fix_reader(gen, repo), marker=MARKER)))

        # the other wrong base: repository root assumed, pack built outside → FAIL
        shapes.append(("a reader that assumes the repository root, on a pack "
                       "built outside it", True,
                       check_pack(build_fixture(gen, tmp / "s9"), gen,
                                  reader=repo_root_reader(gen, repo),
                                  marker=MARKER)))

        # a real pack (no marker) whose declared stem is the wrong length → FAIL
        s10 = build_fixture(gen, tmp / "s10")
        man = json.loads((s10 / "manifest.json").read_text())
        for e in man["stems"]:
            if e["name"] == gen.DRUM_STEM:
                e["duration_sec"] = 9.999
        (s10 / "manifest.json").write_text(json.dumps(man, indent=2))
        shapes.append(("the declared stem's length disagrees with its manifest "
                       "entry", True, check_pack(s10, gen)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = [name for name, should_fail, probs in shapes
           if bool(probs) != should_fail]
    notes = []
    for name, should_fail, probs in shapes:
        mark = "ok " if bool(probs) == should_fail else "BAD"
        notes.append(f"  {mark} {'FAIL' if probs else 'PASS'} "
                     f"(expected {'FAIL' if should_fail else 'PASS'}): {name}"
                     + (f"\n        {probs[0][:150]}" if probs else ""))
    return (1 if bad else 0), notes


# ── main ────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(
        description="check_pack_manifest_paths — every asset a pack manifest "
                    "declares must resolve (card t_5f814f2f)")
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--pack-dir", action="append", default=[],
                    help="an extra pack directory to check (repeatable)")
    ap.add_argument("--no-build", action="store_true",
                    help="skip the out-of-tree generator build (rule 4)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    if args.selftest:
        code, notes = selftest(repo)
        print("\n".join(notes))
        print(("PASS" if code == 0 else "FAIL")
              + f" check_pack_manifest_paths --selftest: {len(notes)} failure "
                f"shape(s) + 1 control")
        return code

    try:
        gen = load_generator(repo)
    except CheckError as exc:
        print(f"FAIL check_pack_manifest_paths: {exc}")
        return 2

    missing = require_generator_api(gen)
    if missing:
        print("FAIL check_pack_manifest_paths: "
              f"{GENERATOR} does not define {', '.join(missing)} — the ONE "
              f"definition of the manifest's `file` field and its loader is gone "
              f"from this revision (card t_5f814f2f)")
        return 1

    problems: list[str] = []
    notes: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="check-pack-marker-"))
    packs = in_tree_packs(repo, [Path(p).resolve() for p in args.pack_dir])
    if not packs and args.no_build:
        print("FAIL check_pack_manifest_paths: no pack manifest under "
              f"{repo / 'packages'}, no --pack-dir, and --no-build was given")
        return 2
    try:
        # the marker fixture: proof the declared stem IS the one-shot source
        marker_pack = build_fixture(gen, tmp, marker=MARKER)
        probs = check_pack(marker_pack, gen, marker=MARKER)
        notes.append("marker fixture (the declared stem is the source): "
                     + ("OK" if not probs else f"{len(probs)} problem(s)"))
        problems += [f"marker fixture: {p}" for p in probs]

        for pack_dir in packs:
            probs = check_pack(pack_dir, gen)
            rel = (pack_dir.relative_to(repo)
                   if str(pack_dir).startswith(str(repo)) else pack_dir)
            notes.append(f"in-tree pack {rel}: "
                         + ("OK" if not probs else f"{len(probs)} problem(s)"))
            problems += [f"{rel}: {p}" for p in probs]

        if not args.no_build:
            pack_dir, probs, note = built_pack(repo)
            notes.append(f"out-of-tree build: {note}")
            if pack_dir is not None:
                probs = probs + check_pack(pack_dir, gen)
            notes.append("out-of-tree pack manifest: "
                         + ("OK" if not probs else f"{len(probs)} problem(s)"))
            problems += probs
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if args.json:
        print(json.dumps({"packs": [str(p) for p in packs],
                          "problems": problems, "notes": notes}, indent=2))
    else:
        for n in notes:
            print(f"  {n}")
        for p in problems:
            print(f"  FAIL {p}")
    if problems:
        print(f"FAIL check_pack_manifest_paths: {len(problems)} unresolved "
              f"manifest path(s) across {len(packs)} in-tree pack(s)"
              + ("" if args.no_build else " + 1 built pack"))
        return 1
    print(f"PASS check_pack_manifest_paths: every declared path resolves "
          f"({len(packs)} in-tree pack(s)"
          + (", no build" if args.no_build else " + 1 out-of-tree build")
          + "); the one-shot source is the declared stem")
    return 0


if __name__ == "__main__":
    sys.exit(main())
