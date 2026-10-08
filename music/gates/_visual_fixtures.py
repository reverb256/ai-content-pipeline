#!/usr/bin/env python3
"""Build the visual fixtures for check_gate_suite.sh.

good_visual.mp4 — 5 distinct colored scenes (shot diversity).
prior_visual.mp4 — 3 different scenes (distinct from good).
raw_dump.mp4    — a static image looped (the raw-dump case).
upload_index.json — the prior-upload signature index.
"""

import hashlib
import json
import subprocess
import sys


def make_scene(color, out, dur):
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i",
         f"color=c={color}:size=1280x720:d={dur}:r=30",
         "-pix_fmt", "yuv420p", out],
        check=True)


def concat(files, out):
    lst = "concat_list.txt"
    with open(lst, "w") as f:
        for p in files:
            f.write(f"file '{p}'\n")
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
