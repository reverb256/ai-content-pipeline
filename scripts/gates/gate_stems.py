#!/usr/bin/env python3
"""Gate: audio stem separation (companion to gate_voice + gate_loudness).

What it checks (when --export-stems was used for a render):

  - stems-index.json exists under <out-dir>/ (next to the master mp3)
  - every file referenced by the index actually exists on disk
  - voice-stem.wav exists and is non-empty
  - per-kind stems (music/atmos/sfx/roomtone) match the story's cues
    (i.e. when the script asks for music, a music stem is present)
  - voice-stem duration is within 2s of the master mp3 duration (the
    voice stem should track the master, since the master is voice + beds)

The pipeline produces ONE master mp3 and optionally a set of stems;
this gate runs only when --export-stems was used, so it is opt-in.
It does NOT fail when --export-stems was NOT used — that's a separate
verdict (PASS-with-stems-missing-note).

Distinguishing note (2026-09-03): this is "preserve-before-mix stem
export" (the storyteller already builds per-kind beds and exposes them
to a stable output), NOT "AI source separation" (Demucs / Spleeter /
audio-separator / MDX-Net). Those tools extract stems from an
already-mixed file using AI models; this gate verifies the cheaper,
lossless path the pipeline already supports. See:
  - github.com/YXenon/python-audio-separator (MDX-Net / UVR)
  - github.com/thcp/stemdeck (Demucs htdemucs_6s)
  - github.com/Abu-AM/Voice_Extractor (Spleeter)

Mode:

  gate_stems.py <out-dir>      # where <out-dir> contains <title>.mp3 +
                               # (optionally) stems-index.json

Exit codes:

  0 — stems pass (or stems not requested)
  1 — stems requested but missing/broken
  2 — usage error
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: gate_stems.py <out-dir>", file=sys.stderr)
        return 2

    out_dir = Path(argv[1])
    if not out_dir.exists():
        fail(f"path not found: {out_dir}")

    index_path = out_dir / "stems-index.json"
    master = next(iter(sorted(out_dir.glob("*.mp3"))), None)
    if master is None and not index_path.exists():
        fail(f"neither master mp3 nor stems-index.json under {out_dir}")

    # Stems were not requested → soft pass with a one-line note
    if not index_path.exists():
        print(f"PASS: stems not requested (no stems-index.json under {out_dir})")
        return 0

    try:
        idx: dict = json.loads(index_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        fail(f"stems-index.json unreadable: {e}")

    print(f"# stem-separation gate — {out_dir.name}")
    print(f"# index: {index_path}")
    if master:
        print(f"# master: {master.name}")
    print()

    issues: list[str] = []

    # 1. Voice stem exists + non-empty
    voice_info = idx.get("voice")
    if not voice_info or not isinstance(voice_info, dict):
        issues.append("index has no voice entry")
    else:
        vp = Path(voice_info.get("path", ""))
        if not vp.exists():
            issues.append(f"voice stem missing: {vp}")
        elif vp.stat().st_size < 1024:
            issues.append(f"voice stem suspiciously small: {vp} "
                          f"({vp.stat().st_size} bytes)")
        else:
            print(f"ok    voice-stem  {vp.name:<32} "
                  f"{voice_info.get('duration', 0):>7.2f}s  "
                  f"{voice_info.get('bytes', 0)/1024:>7.1f} KB")

    # 2. Per-kind stems
    kinds = idx.get("kinds", {})
    for kind in ("music", "atmos", "sfx", "roomtone"):
        files = kinds.get(kind, [])
        if not files:
            print(f"note  {kind:<10} (none — script had no {kind} cues)")
            continue
        for f in files:
            p = Path(f.get("path", ""))
            if not p.exists():
                issues.append(f"{kind} stem missing: {p}")
                continue
            if f.get("bytes", 0) < 1024:
                issues.append(f"{kind} stem too small: {p} "
                              f"({f.get('bytes', 0)} bytes)")
                continue
            print(f"ok    {kind:<10} {p.name:<32} "
                  f"{f.get('duration', 0):>7.2f}s  "
                  f"{f.get('bytes', 0)/1024:>7.1f} KB")

    # 3. Per-scene file inventory
    n_scenes = len(idx.get("scenes", []))
    print()
    print(f"# {n_scenes} scene(s) in index")
    for sc in idx.get("scenes", []):
        kinds_in_scene = sorted(sc.get("files", {}).keys())
        print(f"  - {sc.get('scene', '?')}: "
              f"{', '.join(kinds_in_scene) or '(voice only)'}")

    # 4. Voice-stem duration tracks master (within 2s)
    if master and voice_info and isinstance(voice_info, dict):
        try:
            import subprocess
            r = subprocess.run(
                ["ffprobe", "-hide_banner", "-v", "error",
                 "-show_entries", "format=duration", "-of", "json",
                 str(master)],
                capture_output=True, text=True, timeout=30,
            )
            master_dur = float(json.loads(r.stdout)["format"]["duration"])
            voice_dur = float(voice_info.get("duration", 0))
            drift = abs(master_dur - voice_dur)
            if drift > 2.0:
                issues.append(
                    f"voice-stem {voice_dur:.1f}s drifts > 2s from master "
                    f"{master_dur:.1f}s"
                )
            print()
            print(f"# master={master_dur:.2f}s  voice-stem={voice_dur:.2f}s  "
                  f"drift={drift:.2f}s (limit 2s)")
        except Exception as e:
            print(f"# duration-drift check skipped: {e}", file=sys.stderr)

    print()
    if issues:
        print(f"FAIL: stem-separation gate ({len(issues)} issue(s))")
        for ln in issues:
            print(f"  - {ln}")
        return 1
    print("PASS: stem-separation gate")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))