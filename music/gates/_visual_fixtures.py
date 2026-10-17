#!/usr/bin/env python3
"""Build the visual fixtures for check_gate_suite.sh.

good_visual.mp4 — 5 distinct colored scenes (shot diversity).
prior_visual.mp4 — 3 different scenes (distinct from good).
raw_dump.mp4    — a static image looped (the raw-dump case).
upload_index.json — the prior-upload signature index.
"""

import hashlib
import json
import os
import subprocess
import sys


def make_scene(color, out, dur):
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i",
         f"color=c={color}:size=1280x720:d={dur}:r=30",
         "-pix_fmt", "yuv420p", out],
        check=True)


def list_path(out):
    """The concat demuxer's list file for `out`, NEXT TO its output.

    REGRESSION (2026-10-16, card t_7ab98781). This path used to be the bare
    relative name `concat_list.txt`, and `check_gate_suite.sh` cd's to the repo
    root before calling the builder, so EVERY matrix run overwrote the TRACKED
    repo file `concat_list.txt` at the repo root with that run's own fixture
    paths and left the shared checkout dirty - which is how a fixture byproduct
    gets swept into somebody's commit by `git add -A`. Per-output names also
    stop two concurrent runs racing on one list.
    """
    return f"{out}.concat_list.txt"


def write_list(files, out):
    """Write the list for `files` next to `out`; return the list path.

    REFUSES a relative path. A relative list lands in the CALLER's CWD, which is
    the repo root here - that is exactly the incident above, and it must fail
    loudly rather than dirty the tree in silence. `build_fixtures` in
    check_gate_suite.sh turns any failure into FATAL, so the matrix cannot pass
    with a relative list.
    """
    lst = list_path(out)
    if not os.path.isabs(lst):
        raise SystemExit(
            f"FATAL: the concat list must be an absolute path, got {lst!r} - a "
            f"relative list lands in the caller's CWD (t_7ab98781)")
    with open(lst, "w") as f:
        for p in files:
            f.write(f"file '{p}'\n")
    return lst


def concat(files, out):
    lst = write_list(files, out)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat",
         "-safe", "0", "-i", lst, "-c", "copy", out],
        check=True)


def frame_hashes(path, cadence, duration):
    hashes = []
    t = 0.0
    while t < duration:
        proc = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-ss",
             f"{t:.3f}", "-i", path, "-frames:v", "1",
             "-vf", "scale=64:64,format=gray",
             "-f", "rawvideo", "-"],
            capture_output=True, timeout=120)
        if proc.returncode == 0 and proc.stdout:
            h = hashlib.sha256(proc.stdout).hexdigest()[:16]
            if not hashes or hashes[-1] != h:
                hashes.append(h)
        t += cadence
    return hashes


def main(argv):
    out_dir = argv[1]

    scenes = []
    for i, color in enumerate(
            ["0x224488", "0x882244", "0x448822",
             "0x888822", "0x228888"]):
        p = f"{out_dir}/scene_{i}.mp4"
        make_scene(color, p, 6)
        scenes.append(p)
    concat(scenes, f"{out_dir}/good_visual.mp4")

    prior_scenes = []
    for i, color in enumerate(
            ["0x442288", "0x884422", "0x224488"]):
        p = f"{out_dir}/pscene_{i}.mp4"
        make_scene(color, p, 6)
        prior_scenes.append(p)
    concat(prior_scenes, f"{out_dir}/prior_visual.mp4")

    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-loop", "1",
         "-i", f"{out_dir}/artwork.jpg", "-t", "30",
         "-pix_fmt", "yuv420p",
         f"{out_dir}/raw_dump.mp4"],
        check=True)

    prior = frame_hashes(f"{out_dir}/prior_visual.mp4", 2.0, 18.0)
    index = {"ocean-drift-ep01": {
        "title": "Ocean Drift Ep01",
        "frame_hashes": prior}}
    with open(f"{out_dir}/upload_index.json", "w") as f:
        json.dump(index, f, indent=2)
    print("built good_visual.mp4 + prior_visual.mp4 + "
          "raw_dump.mp4 + upload_index.json")


if __name__ == "__main__":
    main(sys.argv)
