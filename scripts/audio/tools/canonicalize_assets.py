#!/usr/bin/env python3
"""canonicalize_assets.py — convert atmos/SFX assets to pipeline canonical format.

The storyteller pipeline mixes at CANONICAL_SAMPLE_RATE=48000, CANONICAL_BIT_DEPTH
"s24le", stereo (see scripts/audio/storyteller.py). MMAudio's text-to-audio
outputs 44.1 kHz / 16-bit / mono, and any user-supplied library files may be in
any format. Without canonicalization, every render re-samples on the fly and
introduces a tiny resampling artifact on every bed.

This script walks assets/{atmos,sfx,music}/, detects non-canonical files, and
emits a canonical twin at <stem>.canonical.wav (idempotent — skipped when the
twin is newer than the source). The originals are NOT modified, so a
downstream `--use-canonical` flag in storyteller.py can opt in.

Pattern: probe → threshold gate (skip when within 100 Hz) → resample with
linear filter → verify realized rate via post-probe (anti-pattern: trust exit
code; ffmpeg can stream-copy and report success without changing rate).
Reference: mediapipeline.org audio sample-rate normalization article.

Usage:
    python3 scripts/audio/tools/canonicalize_assets.py [--root DIR] [--apply]
    python3 scripts/audio/tools/canonicalize_assets.py --apply --in-place

Exit codes:
    0 — all canonical (or conversion succeeded)
    1 — ffmpeg failure or verification failure
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]  # scripts/audio/tools/ → repo root
TARGET_RATE = 48000
TARGET_CHANNELS = 2
TARGET_BIT_DEPTH = "pcm_s24le"
RATE_TOLERANCE_HZ = 100  # already-at-target bypass; mediapipeline.org pattern
KINDS = ("atmos", "sfx", "music")
MIN_BYTES = 1000  # below this it's almost certainly corrupt/truncated

# Atmos beds land under the fixed 0.22 per-bed gain in storyteller.py
# (≈ -13 dB). MMAudio source beds vary wildly (-17 to -33 dB RMS), so a
# fixed gain would make some beds inaudible and others loud. We normalize
# each atmos source toward ATMOS_RMS_TARGET dBFS mean RMS before the mix
# gain, so every bed reaches ~ -34 dB in a bed-only zone (above the -40 dB
# ambience gate floor) and ~ -37 dB under duck — audible texture, not noise.
ATMOS_RMS_TARGET = -22.0  # dBFS mean RMS the canonical bed should measure
_ATMOS_RMS_CACHE: dict[str, float] = {}


def _rms_db(path: Path) -> float:
    """Measure mean RMS dBFS via ffmpeg volumedetect (cached per path)."""
    key = str(path)
    if key in _ATMOS_RMS_CACHE:
        return _ATMOS_RMS_CACHE[key]
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=120,
    )
    mean = -99.0
    for line in r.stderr.splitlines():
        if "mean_volume" in line:
            try:
                mean = float(line.split(":", 1)[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
    _ATMOS_RMS_CACHE[key] = mean
    return mean


def _atmos_gain(src: Path) -> float:
    """Linear gain that lifts a bed's measured RMS to ATMOS_RMS_TARGET."""
    import math
    cur = _rms_db(src)
    if cur <= -99.0 or cur >= 0.0:
        return 1.0
    db = ATMOS_RMS_TARGET - cur
    return min(max(10.0 ** (db / 20.0), 0.02), 8.0)


def _ffprobe(path: Path) -> dict | None:
    r = subprocess.run(
        ["ffprobe", "-hide_banner", "-v", "error",
         "-select_streams", "a:0",
         "-show_entries", "format=duration:stream=sample_rate,channels,codec_name",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def _is_canonical(info: dict) -> bool:
    streams = info.get("streams", [])
    if not streams:
        return False
    s = streams[0]
    try:
        rate = int(s.get("sample_rate", 0))
        channels = int(s.get("channels", 0))
    except (TypeError, ValueError):
        return False
    codec = (s.get("codec_name") or "").lower()
    return (
        abs(rate - TARGET_RATE) <= RATE_TOLERANCE_HZ
        and channels == TARGET_CHANNELS
        and codec == "pcm_s24le"
    )


def _convert(src: Path, dst: Path, kind: str = "") -> tuple[bool, str]:
    """Resample + channel-upconvert to canonical PCM. Verify after write.

    kind='atmos' also applies a loudness anchor (normalize mean RMS toward
    ATMOS_RMS_TARGET dB) so MMAudio's wildly-varying bed levels (rain-on-window
    at -33 dB vs night-crickets at -18 dB) land consistently under the fixed
    0.22 atmos gain in the mix.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.parent / f".{dst.stem}.tmp.wav"
    af = (
        f"aresample={TARGET_RATE},"
        f"aformat=channel_layouts=stereo,"
        f"alimiter=limit=0.97"
    )
    if kind == "atmos":
        gain = _atmos_gain(src)
        af += f",volume={gain:.6f}"
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-y", "-i", str(src),
         "-af", af,
         "-ac", str(TARGET_CHANNELS),
         "-ar", str(TARGET_RATE),
         "-c:a", "pcm_s24le",
         str(tmp)],
        capture_output=True, text=True, timeout=180,
    )
    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        return False, f"ffmpeg rc={r.returncode}: {r.stderr.strip()[-200:]}"
    # Verify: file exists, non-trivial size, realized at target rate (anti-pattern:
    # trusting exit code alone — ffmpeg can stream-copy and skip the resample).
    if not tmp.exists() or tmp.stat().st_size < MIN_BYTES:
        tmp.unlink(missing_ok=True)
        return False, "output missing or truncated"
    post = _ffprobe(tmp)
    if post is None:
        tmp.unlink(missing_ok=True)
        return False, "post-ffprobe failed"
    s = post.get("streams", [{}])[0]
    try:
        rate = int(s.get("sample_rate", 0))
        channels = int(s.get("channels", 0))
    except (TypeError, ValueError):
        tmp.unlink(missing_ok=True)
        return False, "post-probe malformed"
    if abs(rate - TARGET_RATE) > RATE_TOLERANCE_HZ or channels != TARGET_CHANNELS:
        tmp.unlink(missing_ok=True)
        return False, f"verification: realized {rate}Hz/{channels}ch, expected {TARGET_RATE}Hz/{TARGET_CHANNELS}ch"
    tmp.replace(dst)
    return True, "ok"


def _walk(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir()
                  if p.is_file() and p.suffix.lower() in (".wav", ".mp3", ".flac", ".ogg"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=REPO / "assets",
                    help="assets root (with atmos/, sfx/, music/ subdirs)")
    ap.add_argument("--apply", action="store_true",
                    help="actually convert (default: dry-run report only)")
    ap.add_argument("--in-place", action="store_true",
                    help="overwrite originals with canonical versions")
    ap.add_argument("--re-anchor-atmos", action="store_true",
                    help="even canonical atmos beds: normalize RMS to target level")
    args = ap.parse_args(argv)

    report: dict[str, list[dict]] = {}
    rc = 0
    for kind in KINDS:
        d = args.root / kind
        files = _walk(d)
        report[kind] = []
        for f in files:
            if f.stat().st_size < MIN_BYTES:
                report[kind].append({"file": f.name, "status": "SKIP_TINY",
                                     "size": f.stat().st_size})
                continue
            info = _ffprobe(f)
            if info is None:
                report[kind].append({"file": f.name, "status": "FFPROBE_FAIL"})
                rc = 1
                continue
            if _is_canonical(info):
                # Atmos re-anchor: even canonical files may sit at the wrong
                # loudness (MMAudio output levels vary). --re-anchor-atmos
                # re-runs them through the volume normalization.
                if args.re_anchor_atmos and kind == "atmos" and "silence" not in f.stem:
                    gain = _atmos_gain(f)
                    if abs(gain - 1.0) > 0.02:
                        if args.apply:
                            ok, msg = _convert(f, f, kind=kind)
                            report[kind].append({
                                "file": f.name,
                                "status": "RE_ANCHORED" if ok else "CONVERT_FAIL",
                                "gain": round(gain, 3),
                                "msg": msg,
                            })
                            if not ok:
                                rc = 1
                        else:
                            report[kind].append({
                                "file": f.name,
                                "status": "NEEDS_RE_ANCHOR",
                                "gain": round(gain, 3),
                                "src_mean_rms": round(_rms_db(f), 1),
                            })
                        continue
                report[kind].append({"file": f.name, "status": "OK_CANONICAL",
                                     "duration": float(info["format"].get("duration", 0))})
                continue

            # non-canonical → convert
            kind_arg = kind
            if args.in_place:
                dst = f
            else:
                dst = f.with_name(f.stem + ".canonical.wav")
            if args.apply:
                ok, msg = _convert(f, dst, kind=kind_arg)
                report[kind].append({
                    "file": f.name,
                    "status": "CONVERTED" if ok else "CONVERT_FAIL",
                    "msg": msg,
                    "dst": str(dst) if ok else None,
                })
                if not ok:
                    rc = 1
            else:
                report[kind].append({
                    "file": f.name,
                    "status": "NEEDS_CONVERT",
                    "src_rate": info["streams"][0].get("sample_rate"),
                    "src_channels": info["streams"][0].get("channels"),
                    "src_codec": info["streams"][0].get("codec_name"),
                })

    print(json.dumps(report, indent=2))
    return rc


if __name__ == "__main__":
    sys.exit(main())