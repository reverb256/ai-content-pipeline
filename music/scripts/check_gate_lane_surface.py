#!/usr/bin/env python3
"""Check that every gate accepts the lanes `music/lanes.yaml` assigns to it.

WHY THIS EXISTS — the incident (card t_d9983bb9, measured 2026-10-16)
--------------------------------------------------------------------
`music/lanes.yaml` gives the `sync-documentary` lane `gate: gate_sync_ready`.
`gate_sync_ready.py` kept its own hardcoded lane list, argparse rejected the name
and the gate exited 2:

    $ /usr/bin/python3 music/gates/gate_sync_ready.py \
          --package-dir <empty> --lane sync-documentary
    gate_sync_ready.py: error: argument --lane: invalid choice: 'sync-documentary'
    rc=2

`2` is a USAGE error, but a stage reads any non-zero as a gate FAILURE — so the
lane's own gate could never be run, on the lane the activist genre's whole
revenue_potential (songtradr 800 + audiosparx 800) depends on. The same card
found the twin defect in the stage machine: `music/stages.yaml` ran
`gate_youtube_authentic` for every genre, including genres with no YouTube lane.
One root cause: gate selection was hardcoded per script, so the registry and the
gate could disagree and nothing noticed.

WHAT THIS CHECK ASSERTS (all of it measured, none of it grepped from a file):
  A. The lane registry read by the gates (stdlib scanner, `_lane_registry.py`)
     agrees with the authoritative PyYAML read (`music/registry.py`), lane by
     lane: same `gate`, same `requires`.
  B. Every lane's declared gate has a script, and every gate script's argparse
     surface is reachable (`--help` exits 0).
  C. Every gate that takes a `--lane` option accepts EVERY lane that declares it
     by name: exit 0 or 1, never 2, and never "invalid choice". The
     `sync-documentary` case above is the reference incident.
  D. `gate_sync_ready` really checks what each of its lanes requires: every
     `requires:` token in lanes.yaml must map to a check the gate can produce
     evidence with (its TRACK_COVERAGE / PACK_COVERAGE maps), and a pack-only
     requirement must be refused in track mode.
  E. Acceptance for the incident: a real sync fixture (built here with ffmpeg)
     PASSES `--lane sync-documentary`, and an empty directory FAILS with exit 1
     and output byte-identical to the `--lane sync` path.
  F. The `visual` stage's gate is derived from the genre's lanes, not hardcoded:
     every genre resolves through `registry.py gate-for-stage`, the resolved
     gate has a script, and the stage prompt names the resolver instead of a
     gate script.

Run:  /usr/bin/python3 music/scripts/check_gate_lane_surface.py
Exit: 0 = every lane surface holds, 1 = a violation, 2 = cannot run (no PyYAML
      or no ffmpeg — refusing rather than reporting a false PASS).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[2]
MUSIC = REPO / "music"
GATES = MUSIC / "gates"

sys.path.insert(0, str(GATES))
sys.path.insert(0, str(MUSIC))

INCIDENT = "card t_d9983bb9"


def ffmpeg_dir() -> Path:
    """Locate ffmpeg/ffprobe. Refuse loudly — a silent skip proves nothing."""
    env = os.environ.get("FFMPEG_BIN_DIR")
    cands = [Path(env)] if env else []
    cands.append(Path.home() / ".hermes" / "tools" /
                 "ffmpeg-9.0.1-linux-x64" / "bin")
    for cand in cands:
        if (cand / "ffmpeg").is_file() and (cand / "ffprobe").is_file():
            return cand
    found = shutil.which("ffmpeg")
    if found:
        return Path(found).parent
    raise RuntimeError(
        "ffmpeg/ffprobe not found. These gates measure real audio, so this "
        "check cannot run. Set FFMPEG_BIN_DIR to the directory holding ffmpeg + "
        "ffprobe (e.g. ~/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin).")


def run(cmd: list[str], env: dict | None = None) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env,
                          timeout=600)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def required_options(source: str, option: str) -> bool:
    """True when `add_argument("<option>", ... required=True ...)`."""
    match = re.search(
        r"add_argument\(\s*[\"']" + re.escape(option) + r"[\"'](.*?)\)",
        source, re.S)
    return bool(match) and "required=True" in match.group(1)


def help_options(text: str) -> set[str]:
    return set(re.findall(r"^\s+(--[A-Za-z0-9-]+)", text, re.M))


def build_sync_fixture(root: Path, ff: Path) -> Path:
    """A package that satisfies the sync lanes' requires, built by ffmpeg."""
    pkg = root / "good_sync"
    (pkg / "stems").mkdir(parents=True, exist_ok=True)
    ffmpeg = str(ff / "ffmpeg")

    def tone(path: Path, volume: str = "") -> None:
        cmd = [ffmpeg, "-y", "-v", "error", "-f", "lavfi",
               "-i", "sine=frequency=440:duration=10"]
        if volume:
            cmd += ["-af", f"volume={volume}"]
        cmd += ["-ar", "44100", "-ac", "2", str(path)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)

    tone(pkg / "full_mix.wav")
    tone(pkg / "instrumental.wav", "6dB")            # different bytes = real
    for stem in ("drums", "bass", "keys", "vox"):
        tone(pkg / "stems" / f"stem_{stem}.wav")
    (pkg / "manifest.json").write_text(json.dumps({
        "metadata": {"title": "Lane Surface Check", "artist": "music-producer",
                     "bpm": 120, "key": "A minor", "mood": "calm",
                     "genre": "activist"}}), encoding="utf-8")
    (pkg / "clearance_doc.pdf").write_bytes(b"%PDF-1.4\nfixture clearance\n")
    (pkg / "ai_disclosure.txt").write_text(
        "AI disclosure: music generated with Suno AI, human-directed.\n",
        encoding="utf-8")
    return pkg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Check the gate<->lane contract in music/lanes.yaml "
                    f"(repo root: {REPO}).")
    ap.parse_args(argv)

    try:
        import registry                      # needs PyYAML
        import _lane_registry                # stdlib-only scanner
    except ImportError as exc:
        print(f"CANNOT RUN check_gate_lane_surface: {exc} — the registry needs "
              "PyYAML. Use /usr/bin/python3.")
        return 2

    try:
        ff = ffmpeg_dir()
    except RuntimeError as exc:
        print(f"CANNOT RUN check_gate_lane_surface: {exc}")
        return 2

    env = dict(os.environ)
    env["PATH"] = f"{ff}:{env.get('PATH', '')}"

    failures: list[str] = []
    notes: list[str] = []

    def ok(msg: str) -> None:
        print(f"  OK   {msg}")

    def bad(msg: str) -> None:
        print(f"  FAIL {msg}")
        failures.append(msg)

    # ---------------------------------------------------------------- A
    print("A. the gate's lane view matches the authoritative registry read")
    scanned = _lane_registry.load_lanes()
    authoritative = registry.load_lanes()
    if set(scanned) != set(authoritative):
        bad(f"lane ids differ: scanner {sorted(scanned)} vs registry.py "
            f"{sorted(authoritative)}")
    for lane in sorted(set(scanned) & set(authoritative)):
        s, a = scanned[lane], authoritative[lane]
        if s.get("gate") != a.get("gate") or \
                tuple(s.get("requires") or ()) != tuple(a.get("requires") or ()):
            bad(f"{lane}: scanner says gate={s.get('gate')} "
                f"requires={list(s.get('requires') or ())}; registry.py says "
                f"gate={a.get('gate')} requires={list(a.get('requires') or ())}")
    if not failures:
        ok(f"{len(scanned)} lane(s): gate + requires identical in both reads "
           f"({MUSIC / 'lanes.yaml'})")

    # ---------------------------------------------------------------- B
    print("B. every lane's gate exists and its argparse surface is reachable")
    gate_scripts = sorted(GATES.glob("gate_*.py"))
    if not gate_scripts:
        bad(f"no gate scripts under {GATES}")
    declared_gates = {spec.get("gate") for spec in authoritative.values()
                      if spec.get("gate")}
    for name in sorted(declared_gates):
        if not (GATES / f"{name}.py").is_file():
            bad(f"{name}: no script music/gates/{name}.py, but lanes.yaml "
                "assigns it a lane")
    gate_help: dict[str, str] = {}
    help_ok = 0
    for script in gate_scripts:
        rc, out = run([sys.executable, str(script), "--help"])
        gate_help[script.name] = out
        if rc != 0:
            bad(f"{script.name} --help exited {rc} (argparse surface "
                f"unreachable): {' '.join(out.strip().splitlines()[:1])}")
        else:
            help_ok += 1
    if gate_scripts:
        ok(f"{help_ok}/{len(gate_scripts)} gate script(s): --help exits 0; "
           f"{len(declared_gates)} gate name(s) referenced by lanes.yaml all "
           "have a script")

    # ---------------------------------------------------------------- C
    print("C. a gate accepts every lane that declares it (0/1, never 2)")
    tmp = Path(tempfile.mkdtemp(prefix="lane-surface-"))
    empty = tmp / "empty"
    empty.mkdir()
    checked = 0
    for script in gate_scripts:
        source = script.read_text(encoding="utf-8")
        options = help_options(gate_help.get(script.name, ""))
        if "--lane" not in options:
            continue
        lanes_here = sorted(lane for lane, spec in authoritative.items()
                            if spec.get("gate") == script.stem)
        if not lanes_here:
            bad(f"{script.name}: takes --lane but no lane in lanes.yaml "
                f"declares gate: {script.stem} — the option is dead surface")
            continue
        required = [opt for opt in sorted(options)
                    if opt != "--lane" and required_options(source, opt)]
        for lane in lanes_here:
            cmd = [sys.executable, str(script)]
            for opt in required:
                cmd += [opt, str(empty)]
            cmd += ["--lane", lane]
            rc, out = run(cmd, env=env)
            checked += 1
            if rc not in (0, 1):
                bad(f"{script.name} --lane {lane} exited {rc} — a stage reads "
                    f"non-zero as a gate FAILURE. Output: "
                    f"{' / '.join(out.strip().splitlines()[:3])}")
            elif "invalid choice" in out:
                bad(f"{script.name} --lane {lane}: argparse still rejects the "
                    "lane name its registry assigns it")
            else:
                ok(f"{script.name} --lane {lane} -> exit {rc} (gate verdict)")
    if checked == 0:
        bad("no gate/lane pair was exercised — this check asserted nothing")
    else:
        notes.append(f"{checked} lane name(s) passed to their own gate")

    # ---------------------------------------------------------------- D
    print("D. gate_sync_ready checks the requirements its lanes declare")
    sync_gate = load_module(GATES / "gate_sync_ready.py")
    track_cov = set(getattr(sync_gate, "TRACK_COVERAGE", {}) or {})
    pack_cov = set(getattr(sync_gate, "PACK_COVERAGE", {}) or {})
    if not track_cov or not pack_cov:
        bad("gate_sync_ready no longer exposes TRACK_COVERAGE/PACK_COVERAGE — "
            "this check cannot prove the lane's requires are the ones checked")
    lanes_declaring = sorted(lane for lane, spec in authoritative.items()
                             if spec.get("gate") == "gate_sync_ready")
    if not lanes_declaring:
        bad("no lane declares gate: gate_sync_ready")
    for lane in lanes_declaring:
        requires = tuple(authoritative[lane].get("requires") or ())
        mode = "pack" if lane == "game-assets" else "track"
        coverage = pack_cov if mode == "pack" else track_cov
        uncovered = [token for token in requires if token not in coverage]
        if uncovered:
            bad(f"{lane}: requires {uncovered} but the gate's {mode} coverage "
                f"has no check for them")
        else:
            ok(f"{lane}: requires {list(requires)} all covered in {mode} mode")
    rc, out = run([sys.executable, str(GATES / "gate_sync_ready.py"),
                   "--package-dir", str(empty), "--lane", "game-assets",
                   "--mode", "track"], env=env)
    if "loop_point" in out and rc == 1:
        ok("track mode refuses the pack-only requirement `loop_point` "
           "(a gate must not certify what it cannot measure)")
    else:
        bad(f"--lane game-assets --mode track must refuse `loop_point` "
            f"(exit 1, naming it); got exit {rc}: "
            f"{' / '.join(out.strip().splitlines()[:3])}")

    # ---------------------------------------------------------------- E
    print("E. the incident: --lane sync-documentary runs the sync checks")
    pkg = build_sync_fixture(tmp, ff)
    gate = str(GATES / "gate_sync_ready.py")
    rc_doc, out_doc = run([sys.executable, gate, "--package-dir", str(pkg),
                           "--lane", "sync-documentary"], env=env)
    rc_sync, out_sync = run([sys.executable, gate, "--package-dir", str(pkg),
                             "--lane", "sync"], env=env)
    def checks_only(text: str) -> list[str]:
        """The reported checks, minus the line naming the lane (which differs)."""
        return [line for line in text.strip().splitlines()
                if not line.strip().startswith("lane ")]

    if rc_doc == 0 and rc_sync == 0:
        ok("sync-documentary PASSES the sync fixture (exit 0), same as "
           "--lane sync")
    else:
        bad(f"sync fixture: --lane sync-documentary exited {rc_doc}, "
            f"--lane sync exited {rc_sync}; both must PASS (0). Output: "
            f"{' / '.join(out_doc.strip().splitlines()[:4])}")
    if checks_only(out_doc) != checks_only(out_sync):
        bad("sync-documentary and sync report different checks on the same "
            "package — lanes.yaml gives them the same requires. "
            f"sync-documentary: {checks_only(out_doc)}; "
            f"sync: {checks_only(out_sync)}")
    rc_doc_e, out_doc_e = run([sys.executable, gate, "--package-dir", str(empty),
                               "--lane", "sync-documentary"], env=env)
    rc_sync_e, out_sync_e = run([sys.executable, gate, "--package-dir", str(empty),
                                 "--lane", "sync"], env=env)
    if rc_doc_e != 1:
        bad(f"empty package --lane sync-documentary exited {rc_doc_e}; the "
            "incident exit was 2 (usage error read as a gate FAILURE) — it must "
            "now be 1 (a real FAIL)")
    elif out_doc_e != out_sync_e:
        bad("empty package: --lane sync-documentary and --lane sync print "
            "different requirement lines")
    else:
        lines = len(out_doc_e.strip().splitlines())
        ok(f"empty package: exit 1 for both lanes, byte-identical output "
           f"({lines} requirement line(s)), never the incident's rc=2")

    # ---------------------------------------------------------------- F
    print("F. the visual stage's gate comes from the genre's lanes")
    rules = registry.load_stage_gates(authoritative)
    rule = rules.get("visual")
    if not rule:
        bad("no stage_gates rule for the visual stage in lanes.yaml")
    prompt = ""
    for entry in (registry.load_yaml(MUSIC / "stages.yaml").get("stages") or []):
        if isinstance(entry, dict) and entry.get("stage") == "visual":
            prompt = str(entry.get("prompt") or "")
    if "gate-for-stage" not in prompt or "registry.py" not in prompt:
        bad("the visual stage prompt does not resolve its gate through "
            "music/registry.py gate-for-stage")
    elif re.search(r"music/gates/gate_[a-z_]+\.py", prompt):
        bad("the visual stage prompt still names a gate SCRIPT directly — the "
            "gate must come from the genre's lanes")
    else:
        ok("visual stage prompt resolves its gate; no gate script hardcoded")
    if rule:
        for genre in sorted(registry.load_genres(authoritative)):
            resolved = registry.gate_for_stage("visual", genre)
            lanes_here = resolved["lanes"]
            selecting = [lane for lane in lanes_here
                         if authoritative.get(lane, {}).get("gate")
                         == resolved["declared_gate"]]
            if resolved["gate"] is None:
                if selecting:
                    bad(f"{genre}: resolver said 'none' but "
                        f"{selecting} declares {resolved['declared_gate']}")
                else:
                    ok(f"{genre}: no lane declares "
                       f"{resolved['declared_gate']} -> gate: none (stated "
                       f"explicitly, lanes: {', '.join(lanes_here)})")
            else:
                if not resolved["script"].is_file():
                    bad(f"{genre}: resolved gate {resolved['gate']} has no "
                        f"script {resolved['script']}")
                elif not selecting:
                    bad(f"{genre}: resolved gate {resolved['gate']} but no "
                        "lane of this genre declares it")
                else:
                    ok(f"{genre}: {resolved['gate']} via lane "
                       f"'{resolved['lane']}'")

    shutil.rmtree(tmp, ignore_errors=True)
    for note in notes:
        print(f"  note: {note}")

    if failures:
        print(f"\nFAIL check_gate_lane_surface: {len(failures)} violation(s) "
              f"of the gate<->lane contract")
        print(f"  cited: {INCIDENT} (sync-documentary rc=2; the visual stage's "
              "YouTube gate for a genre with no YouTube lane)")
        return 1
    print("\nPASS check_gate_lane_surface: every gate accepts the lanes "
          "lanes.yaml gives it, and the visual stage's gate follows the genre")
    print(f"  cited: {INCIDENT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
