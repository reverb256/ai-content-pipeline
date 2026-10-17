#!/usr/bin/env python3
"""gate_youtube_authentic — inauthentic-content gate for YouTube lanes.

YouTube's inauthentic-content policy (2026) penalizes mass-produced,
visually repetitive uploads. The gate EXECUTES the visual artifact:

  1. The visual is a real, decodable video (ffprobe: video stream +
     duration + resolution).
  2. The visual is NOT a raw dump: it must carry a real edit —
     measured as scene/shot diversity. The gate samples frames at
     a fixed cadence, hashes each sampled frame's luminance
     signature, and requires >= MIN_DISTINCT_FRAMES distinct
     signatures across the video (a static image dumped with audio
     has 1 distinct frame signature — it fails).
  3. The visual VARIES vs prior uploads: the gate compares the
     video's frame-signature SET against a prior-upload index
     (upload_index.json: {slug: {frame_hashes: [...], title: ...}}).
     Jaccard similarity above SIM_MAX means the upload is a
     near-duplicate of a prior upload — it fails.
  4. Disclosure: disclosure.txt (or the manifest's disclosure
     field) states the AI role for the video.

Usage:
  python3 music/gates/gate_youtube_authentic.py \
      --visual <video> [--upload-index upload_index.json] \
      [--prior-slug <slug>] [--sample-cadence 2.0] \
      [--min-distinct-frames 10] [--sim-max 0.85]

Exit codes: 0 = PASS, 1 = FAIL (reasons on stderr),
2 = usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_CADENCE = 2.0        # sample a frame every N seconds
DEFAULT_MIN_DISTINCT = 10    # distinct frame signatures required
DEFAULT_SIM_MAX = 0.85       # Jaccard ceiling vs prior uploads
DISCLOSURE_NAMES = ("disclosure.txt", "ai_disclosure.txt")


def probe_video(path: Path) -> dict | None:
    """ffprobe the video; return stream info or None."""
    proc = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries", "format=duration:stream=codec_type,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def sample_frame_hashes(path: Path, cadence: float,
                        duration: float) -> list[str]:
    """Hash luminance signatures of frames sampled every cadence s.

    A raw dump (one static image + audio) yields one signature.
    An edited visual yields many. The hash is over a downscaled
    grayscale frame, so it is robust to encode noise but catches
    identical visuals.
    """
    hashes: list[str] = []
    t = 0.0
    while t < duration:
        proc = subprocess.run(
            ["ffmpeg", "-v", "error", "-y",
             "-ss", f"{t:.3f}", "-i", str(path),
             "-frames:v", "1", "-vf", "scale=64:64,format=gray",
             "-f", "rawvideo", "-"],
            capture_output=True, timeout=120,
        )
        if proc.returncode == 0 and proc.stdout:
            digest = hashlib.sha256(proc.stdout).hexdigest()[:16]
            if not hashes or hashes[-1] != digest:
                hashes.append(digest)
        t += cadence
    return hashes


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def fail(msgs: list[str]) -> int:
    print("FAIL gate_youtube_authentic", file=sys.stderr)
    for m in msgs:
        print(f"  - {m}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="gate_youtube_authentic — inauthentic-content gate")
    parser.add_argument("--visual", required=True,
                        help="the rendered video (mp4/mov/webm)")
    parser.add_argument("--upload-index", default=None,
                        help="upload_index.json of prior uploads "
                             "(frame-signature sets per slug)")
    parser.add_argument("--prior-slug", default=None,
                        help="compare against this specific prior "
                             "upload slug")
    parser.add_argument("--cadence", type=float, default=DEFAULT_CADENCE)
    parser.add_argument("--min-distinct-frames", type=int,
                        default=DEFAULT_MIN_DISTINCT)
    parser.add_argument("--sim-max", type=float, default=DEFAULT_SIM_MAX)
    args = parser.parse_args(argv)

    visual = Path(args.visual)
    if not visual.is_file():
        return fail([f"no visual file: {visual}"])

    problems: list[str] = []

    # --- 1. the visual is real video -------------------------------------
    info = probe_video(visual)
    if info is None:
        return fail([f"{visual} is not a decodable video "
                     "(ffprobe failed)"])
    streams = info.get("streams") or []
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    if not video_streams:
        problems.append(f"{visual} has no video stream — an audio-only "
                        "file is a raw dump, not a visual")
        return fail(problems)
    try:
        duration = float(info["format"]["duration"])
    except (KeyError, ValueError, TypeError):
        problems.append("visual has no readable duration")
        return fail(problems)
    width = video_streams[0].get("width", 0)
    height = video_streams[0].get("height", 0)
    if width < 640 or height < 360:
        problems.append(f"visual is {width}x{height} — below the "
                        "640x360 floor for a platform-native visual")

    # --- 2. not a raw dump: shot diversity -------------------------------
    hashes = sample_frame_hashes(visual, args.cadence, duration)
    distinct = len(set(hashes))
    if distinct < args.min_distinct_frames:
        problems.append(f"visual has only {distinct} distinct frame "
                        f"signature(s) across {duration:.1f}s "
                        f"(sampled every {args.cadence}s; "
                        f"{args.min_distinct_frames} required) — this "
                        "is a raw dump (static image + audio), which "
                        "YouTube's inauthentic-content policy penalizes")

    # --- 3. varies vs prior uploads ----------------------------------------
    index_path = Path(args.upload_index) if args.upload_index else None
    prior: dict = {}
    if index_path is not None:
        if not index_path.is_file():
            problems.append(f"upload index {index_path} not found")
        else:
            try:
                prior = json.loads(index_path.read_text(
                    encoding="utf-8"))
            except json.JSONDecodeError as exc:
                problems.append(f"upload index is corrupt JSON: {exc}")

    if prior:
        current = set(hashes)
        comparisons = ([args.prior_slug] if args.prior_slug
                       else list(prior.keys()))
        worst_sim = 0.0
        worst_slug = ""
        for slug in comparisons:
            entry = prior.get(slug) or {}
            prior_hashes = entry.get("frame_hashes") or \
                           entry.get("frame_signatures") or []
            sim = jaccard(current, set(prior_hashes))
            if sim > worst_sim:
                worst_sim, worst_slug = sim, slug
        if worst_sim > args.sim_max:
            problems.append(f"visual is {worst_sim:.2f} similar to prior "
                            f"upload '{worst_slug}' (ceiling "
                            f"{args.sim_max}) — the upload does not vary "
                            "from prior content")
        prior_summary = (worst_sim, worst_slug)
    else:
        prior_summary = (0.0, "")

    # --- 4. disclosure ------------------------------------------------------
    disclosure = next((p for p in (visual.parent / n
                     for n in DISCLOSURE_NAMES) if p.is_file()), None)
    if disclosure is None:
        problems.append(f"no disclosure file (one of "
                        f"{', '.join(DISCLOSURE_NAMES)}) beside the "
                        "visual — the AI role in the video must be "
                        "disclosed")
    elif disclosure.stat().st_size == 0:
        problems.append(f"{disclosure.name} is zero bytes")

    if problems:
        return fail(problems)

    print("PASS gate_youtube_authentic")
    print(f"  visual        : {visual} ({width}x{height}, "
          f"{duration:.1f}s)")
    print(f"  frame samples : {len(hashes)} taken, {distinct} distinct")
    print(f"  raw dump      : no — visual has real shot diversity")
    if prior:
        print(f"  vs prior      : max similarity {prior_summary[0]:.2f} "
              f"('{prior_summary[1]}'), ceiling {args.sim_max}")
    print(f"  disclosure    : {disclosure.name if disclosure else '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
