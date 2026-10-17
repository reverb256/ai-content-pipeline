#!/usr/bin/env python3
"""acestep_qa.py — the mastering + QC gate that runs after generation.

Why this exists: a raw ACE-Step take lands in ~/Music/acestep/ with no quality
control. Nothing measures it, nothing repairs it, nothing normalises it, and a
bad take sits there looking identical to a good one. This runs the ComfyUI
MusicTools chain over a finished track:

    LoadAudio
      -> Music_AudioRepair    invalid samples, DC offset, clicks, short clipping
      -> Music_Fix            genre-informed EQ / linked compression / stereo /
                              LUFS management / peak protection (200 labels -> 18 profiles)
      -> Music_LufsNormalizer integrated loudness to an exact target (ITU-R BS.1770)
      -> SaveAudio            <name>-mastered.flac

Order matters and follows the pack's own guidance: repair BEFORE spectral
processing, so impulsive defects are not spread by the denoiser/EQ.

The genre label is not decoration. Music_Fix maps 200 genre and subgenre labels
onto 18 maintained DSP profiles; pick the one the track was written for.

Usage (inside the pod):
    python3 acestep_qa.py planner-test-intimacy_00001.flac
    python3 acestep_qa.py song.flac --genre "General / Balanced" --lufs -14
"""

import argparse
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request

COMFY = "http://localhost:8188"
COMFY_ROOT = "/home/j_kro/StabilityMatrix/Packages/ComfyUI"
INPUT_DIR = os.path.join(COMFY_ROOT, "input")
# Inside the pod the host's ~/Music is mounted INSIDE ComfyUI's output dir (see
# helm/apps/comfyui-zephyr.yaml): ComfyUI realpaths a save target and refuses
# anything outside --output-directory, so the mount has to be genuinely interior.
# Hence the pod-visible path differs from the host path (~/Music/acestep).
MUSIC_DIR = "/home/j_kro/3d-out/music/acestep"
OUTPUT_PREFIX = "music/acestep"


def api(path, payload=None, timeout=30):
    url = f"{COMFY}{path}"
    if payload is None:
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} from {path}:\n{e.read().decode(errors='replace')}")


def main():
    ap = argparse.ArgumentParser(description="master + QC a generated track")
    ap.add_argument("audio", help="filename in ~/Music/acestep/, or an absolute path")
    ap.add_argument("--genre", default="General / Balanced",
                    help='Music_Fix profile label (default: "General / Balanced")')
    ap.add_argument("--lufs", type=float, default=-14.0,
                    help="integrated loudness target (default: -14, streaming)")
    ap.add_argument("--suffix", default="-mastered", help="output filename suffix")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    # Resolve the source and stage it into ComfyUI's input dir (LoadAudio only
    # sees files there).
    src = args.audio if os.path.isabs(args.audio) else os.path.join(MUSIC_DIR, args.audio)
    if not os.path.exists(src):
        raise SystemExit(f"no such file: {src}")
    staged = os.path.join(INPUT_DIR, os.path.basename(src))
    os.makedirs(INPUT_DIR, exist_ok=True)
    if os.path.abspath(src) != os.path.abspath(staged):
        shutil.copy2(src, staged)

    stem, ext = os.path.splitext(os.path.basename(src))
    out_stem = f"{stem}{args.suffix}"

    workflow = {
        "1": {"class_type": "LoadAudio",
              "inputs": {"audio": os.path.basename(staged)}},
        # repair first: impulsive defects must not be smeared by later EQ/dynamics
        "2": {"class_type": "Music_AudioRepair",
              "inputs": {"audio": ["1", 0], "mode": "Auto (All)",
                         "sensitivity": 0.5, "clip_threshold_dbfs": -0.1,
                         "max_click_ms": 3.0, "max_clip_ms": 3.0,
                         "output_ceiling_dbfs": -0.1}},
        "3": {"class_type": "Music_Fix",
              "inputs": {"audio": ["2", 0], "genre": args.genre}},
        "4": {"class_type": "Music_LufsNormalizer",
              "inputs": {"audio": ["3", 0], "target_lufs": args.lufs}},
        "5": {"class_type": "SaveAudio",
              "inputs": {"audio": ["4", 0],
                         "filename_prefix": f"{OUTPUT_PREFIX}/{out_stem}"}},
    }

    print(f"source   : {src}")
    print(f"chain    : AudioRepair(Auto) -> Music_Fix({args.genre}) -> LUFS({args.lufs})")
    queued = api("/prompt", {"prompt": workflow})
    pid = queued["prompt_id"]
    print(f"queued   : {pid}")

    start = time.time()
    while time.time() - start < args.timeout:
        time.sleep(10)
        hist = api(f"/history/{pid}")
        if hist and pid in hist:
            entry = hist[pid]
            status = entry.get("status", {})
            if status.get("completed") or status.get("status_str") in ("success", "error"):
                print(f"\nfinished in {time.time()-start:.0f}s — {status.get('status_str')}")
                if status.get("status_str") == "error":
                    for m in status.get("messages", []):
                        print("  ", str(m)[:500])
                    return 1
                # repair report is a STRING output on node 2
                for node_id, out in (entry.get("outputs") or {}).items():
                    for k, v in out.items():
                        if k == "text" or "report" in k.lower():
                            print(f"  report[{node_id}]: {str(v)[:300]}")
                        for a in (v if isinstance(v, list) else []):
                            if isinstance(a, dict) and "filename" in a:
                                print(f"  output: {a['filename']}")
                print(f"\n-> ~/Music/acestep/{out_stem}_00001{ext}")
                return 0
        print(f"  ...{int(time.time()-start)}s", flush=True)

    print(f"\nTIMEOUT after {args.timeout}s")
    return 1


if __name__ == "__main__":
    sys.exit(main())
