#!/usr/bin/env python3
"""_pack_fixtures.py — build the asset-pack fixtures for check_gate_suite.sh.

Card t_5ed495eb. The suite needs:

  pack/                 a pack built by the REAL generator (music/assets/pack.py)
                        from synthesized audio — proves the generator's output
                        satisfies both gates, which is the drift this card fixes.
  pack_synth/           a hand-built CONFORMING pack — proves the gate accepts a
                        conforming pack that the generator did not write.
  pack_bad_span/        one loop declares a 1.0 s span (below the 2 s floor)
  pack_bad_seam/        one loop is the phase-slip fixture (6x curvature)
  pack_bad_fade/        one loop is the fade-out fixture (level ruler, card
                        t_bab8aa19: smooth, so the curvature ruler cannot see it)
  pack_bad_count/       loops/ holds one more file than the manifest declares
  pack_bad_meta/        metadata object has no sample_rate
  pack_bad_noloops/     no loop_points.json
  pack_bad_noclear/     no clearance_doc.pdf

Usage: python3 music/gates/_pack_fixtures.py <fixture-dir>
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATES = REPO / "music" / "gates"
GEN_SECONDS = 32          # >= 5 loop candidates at 4 bars each
LOOP_SECONDS = 10.0       # the loop fixtures are 10 s
STEM_SECONDS = 10.0


def synth(path: Path, seconds: float, freq: float = 220.0,
          af: str | None = None, channels: int = 1) -> None:
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
           "-i", f"sine=frequency={freq}:duration={seconds}"]
    if af:
        cmd += ["-af", af]
    cmd += ["-ar", "44100", "-ac", str(channels), str(path)]
    subprocess.run(cmd, check=True)


LICENCE_OF_RECORD = REPO / "music/licences/perpetual_game_asset_v1.txt"


def licence_bytes() -> bytes:
    """The lane's licence of record — a pack ships this text verbatim."""
    if LICENCE_OF_RECORD.is_file():
        return LICENCE_OF_RECORD.read_bytes()
    return b"PERPETUAL-GAME-ASSET-V1 fixture licence\n"


def write_docs(pack: Path, meta: dict, counts: dict, loops: list[dict],
               with_loops_json: bool = True, with_clearance: bool = True,
               with_disclosure: bool = True, with_licence: bool = True,
               licence_text: bytes | None = None,
               pack_name: str = "suite-synth-pack") -> None:
    if with_loops_json:
        (pack / "loop_points.json").write_text(json.dumps({
            "schema": "music/pack-loop-points/v1",
            "pack_name": pack_name,
            "loops": {l["path"]: {"loop_start_s": l.get("loop_start_s", 0.0),
                                  "loop_end_s": l.get("loop_end_s",
                                                      l["duration_sec"]),
                                  "seamless": l.get("seamless", True)}
                      for l in loops}}, indent=2), encoding="utf-8")
    if with_clearance:
        (pack / "clearance_doc.pdf").write_bytes(b"%PDF-1.4\nfake fixture\n")
    if with_disclosure:
        (pack / "ai_disclosure.txt").write_text(
            "AI disclosure: generated with an AI music model.\n",
            encoding="utf-8")
    if with_licence:
        (pack / "LICENCE.txt").write_bytes(licence_text or licence_bytes())
    (pack / "manifest.json").write_text(json.dumps({
        "schema": "music/asset-pack/v1",
        "pack_name": pack_name,
        "metadata": meta,
        "pack_manifest": counts,
        "counts": counts,
    }, indent=2), encoding="utf-8")
    (pack / "README.md").write_text("# fixture pack\n", encoding="utf-8")


def build_synth_pack(out: Path, meta: dict, loops: list[dict], counts: dict,
                     loop_src: Path | None = None, **kwargs) -> None:
    for sub in ("loops", "stems"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    for loop in loops:
        dst = out / loop["path"]
        if loop_src:
            shutil.copy(loop_src, dst)
        else:
            synth(dst, LOOP_SECONDS, 220.0)
    for i in range(counts["stems"]):
        synth(out / "stems" / f"{i + 1:02d}_stem.wav", STEM_SECONDS, 330.0)
    write_docs(out, meta, counts, loops, **kwargs)


def main() -> int:
    out_root = Path(sys.argv[1])
    out_root.mkdir(parents=True, exist_ok=True)

    # --- 1. the generator's own output ---------------------------------
    gen_pack = out_root / "pack"
    if gen_pack.exists():
        shutil.rmtree(gen_pack)
    master = out_root / "pack_master.wav"
    synth(master, GEN_SECONDS, 220.0, af="tremolo=f=2:d=0.9")
    proc = subprocess.run(
        [sys.executable, str(REPO / "music/assets/pack.py"), str(master),
         "--out", str(gen_pack), "--pack-name", "suite-generated-pack",
         "--genre", "chill-lounge", "--title", "Suite Generated Pack",
         "--mood", "neutral", "--bpm", "120", "--key", "A minor"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        print("pack.py failed:", file=sys.stderr)
        print(proc.stdout[-2000:], file=sys.stderr)
        print(proc.stderr[-2000:], file=sys.stderr)
        return 1
    print(f"built {gen_pack} with music/assets/pack.py")

    # --- 2. a conforming hand-built pack -------------------------------
    meta = {"title": "Suite Synth Pack", "artist": "fixture", "bpm": 120,
            "key": "A minor", "mood": "neutral", "genre": "chill-lounge",
            "sample_rate": 44100}
    loops = [{"path": f"loops/loop_{i:02d}.wav",
              "duration_sec": LOOP_SECONDS} for i in (1, 2)]
    counts = {"loops": len(loops), "stems": 4}
    synth_pack = out_root / "pack_synth"
    if synth_pack.exists():
        shutil.rmtree(synth_pack)
    seamless = out_root / "loop_seamless.wav"
    broken = out_root / "loop_broken.wav"
    subprocess.run([sys.executable, str(GATES / "_loop_fixtures.py"),
                    str(out_root)], check=True)
    build_synth_pack(synth_pack, meta, loops, counts, loop_src=seamless)
    print(f"built {synth_pack} (conforming, hand-built)")

    # --- 3. broken variants --------------------------------------------
    bad_span_loops = [{"path": "loops/loop_01.wav", "duration_sec": 1.0},
                      {"path": "loops/loop_02.wav",
                       "duration_sec": LOOP_SECONDS}]
    # The loop-broken fixture's phase slip is at the half period (5 s), so its
    # loop points must span 5 s -> 10 s for the wrap to be the broken one. A
    # 0 -> 10 s window of that file wraps smoothly (measured 1.57x) — which is
    # exactly the kind of fixture mistake that makes a check pass vacuously.
    bad_seam_loops = [{"path": "loops/loop_01.wav", "duration_sec": LOOP_SECONDS,
                       "loop_start_s": 5.0, "loop_end_s": 10.0}]
    no_rate_meta = {k: v for k, v in meta.items() if k != "sample_rate"}

    def rebuild(name: str, meta_: dict, loops_: list, counts_: dict,
                src: Path | None = None, **kwargs) -> Path:
        d = out_root / name
        if d.exists():
            shutil.rmtree(d)
        build_synth_pack(d, meta_, loops_, counts_, loop_src=src, **kwargs)
        print(f"built {d}")
        return d

    rebuild("pack_bad_span", dict(meta), bad_span_loops, dict(counts),
            src=seamless)
    rebuild("pack_bad_seam", dict(meta), bad_seam_loops,
            {"loops": 1, "stems": counts["stems"]}, src=broken)
    # The level ruler (card t_bab8aa19). The loop source is the fade-out
    # fixture: with the default 0 -> 10 s window its last 1 s sits 8.8 dB below
    # its first 1 s (measured), while its curvature stays under the 3.0x
    # ceiling — so ONLY the level ruler can refuse this pack.
    rebuild("pack_bad_fade", dict(meta),
            [{"path": "loops/loop_01.wav", "duration_sec": LOOP_SECONDS}],
            {"loops": 1, "stems": counts["stems"]},
            src=out_root / "loop_faded.wav")
    rebuild("pack_bad_meta", no_rate_meta, [dict(l) for l in loops],
            dict(counts), src=seamless)
    rebuild("pack_bad_noloops", dict(meta), [dict(l) for l in loops],
            dict(counts), src=seamless, with_loops_json=False)
    rebuild("pack_bad_noclear", dict(meta), [dict(l) for l in loops],
            dict(counts), src=seamless, with_clearance=False)
    # The licence substitution incident (card t_5ed495eb): a generator run on a
    # tree with no music/licences/ wrote its own fallback text into the pack.
    rebuild("pack_bad_licence", dict(meta), [dict(l) for l in loops],
            dict(counts), src=seamless,
            licence_text=b"# Perpetual Game Asset Licence (v1.0)\n"
                         b"# Multi-Tier: PERSONAL / COMMERCIAL / EXCLUSIVE\n")

    # count mismatch: an extra file in loops/ that the manifest does not count
    d = rebuild("pack_bad_count", dict(meta), [dict(l) for l in loops],
                dict(counts), src=seamless)
    shutil.copy(seamless, d / "loops" / "loop_99_extra.wav")
    print(f"added an uncounted loops/loop_99_extra.wav to {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
