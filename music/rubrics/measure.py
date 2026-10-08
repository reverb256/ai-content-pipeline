#!/usr/bin/env python3
"""measure.py — MEASURED evidence extraction for the music review panel.

The panel judges cannot listen. This module EXECUTES the artifact with
ffmpeg/numpy and returns measured facts: duration, loudness (volumedetect
mean/max), sample rate, channels, silence map, onset-based BPM estimate,
spectral centroid, and dynamic range (RMS in 1s windows).

Research basis: Evaluation-Illusion (arXiv:2603.11027) — judges anchor on
surface heuristics when given only text. Feeding MEASURED numbers grounds
the review in the artifact itself.

Usage (library):
    from measure import measure_track
    ev = measure_track(Path("track.flac"))

CLI:
    python3 measure.py <audio> [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

MEAN_RE = re.compile(r"mean_volume:\s*(-?[\d.]+)\s*dB")
MAX_RE = re.compile(r"max_volume:\s*(-?[\d.]+)\s*dB")
SIL_RE = re.compile(
    r"silence_(start|end):\s*(-?[\d.]+)")


def _ffprobe(path: Path) -> dict:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size,bit_rate:stream=codec_name,sample_rate,channels",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=300)
    data = json.loads(proc.stdout or "{}")
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    st = streams[0] if streams else {}
    return {
        "codec": st.get("codec_name"),
        "sample_rate_hz": int(st.get("sample_rate", 0) or 0),
        "channels": int(st.get("channels", 0) or 0),
        "duration_s": float(fmt.get("duration", 0) or 0),
        "file_bytes": int(fmt.get("size", 0) or 0),
    }


def _volumedetect(path: Path) -> dict:
    proc = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "volumedetect",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=600)
    err = proc.stderr or ""
    mean = MEAN_RE.search(err)
    peak = MAX_RE.search(err)
    return {
        "mean_volume_db": float(mean.group(1)) if mean else None,
        "max_volume_db": float(peak.group(1)) if peak else None,
    }


def _silence_map(path: Path, noise_db: float = -45.0,
                 min_dur: float = 1.0) -> list:
    """Long silences (>= min_dur s) — evidence of breakdowns/structure gaps."""
    proc = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af",
         f"silencedetect=noise={noise_db}dB:d={min_dur}",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=600)
    events, starts, ends = [], [], []
    for kind, val in SIL_RE.findall(proc.stderr or ""):
        (starts if kind == "start" else ends).append(float(val))
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        events.append({"start_s": round(s, 2),
                       "end_s": round(e, 2) if e is not None else None})
    return events


def _load_mono(path: Path, sr: int = 22050) -> np.ndarray:
    """Decode to float32 mono numpy array at sr via ffmpeg pipe."""
    proc = subprocess.run(
        ["ffmpeg", "-i", str(path), "-ac", "1", "-ar", str(sr),
         "-f", "f32le", "-"],
        capture_output=True, timeout=600)
    return np.frombuffer(proc.stdout, dtype=np.float32)


def _bpm(x: np.ndarray, sr: int) -> dict:
    """Onset-envelope autocorrelation BPM over 60-190 BPM candidates."""
    if len(x) < sr * 2:
        return {"bpm": None, "bpm_confidence": 0.0}
    # onset envelope: positive spectral flux via STFT magnitude diff
    n_fft, hop = 1024, 512
    frames = 1 + (len(x) - n_fft) // hop
    if frames < 8:
        return {"bpm": None, "bpm_confidence": 0.0}
    win = np.hanning(n_fft)
    mags = np.empty((frames, n_fft // 2))
    for i in range(frames):
        seg = x[i * hop: i * hop + n_fft] * win
        mags[i] = np.abs(np.fft.rfft(seg))[: n_fft // 2]
    flux = np.sum(np.diff(mags, axis=0).clip(min=0), axis=1)
    flux = flux - flux.mean()
    if flux.std() < 1e-9:
        return {"bpm": None, "bpm_confidence": 0.0}
    # autocorrelation lag range for 60-190 BPM
    fps = sr / hop
    lag_min = int(fps * 60 / 190)     # lag for 190 BPM
    lag_max = int(fps * 60 / 60)     # lag for 60 BPM
    if lag_max >= len(flux) - 1:
        lag_max = len(flux) - 2
    if lag_min < 1 or lag_max <= lag_min:
        return {"bpm": None, "bpm_confidence": 0.0}
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    ac = ac[: lag_max + 1]
    if ac[0] <= 0:
        return {"bpm": None, "bpm_confidence": 0.0}
    ac_n = ac / ac[0]
    band = ac_n[lag_min: lag_max + 1]
    if band.size == 0:
        return {"bpm": None, "bpm_confidence": 0.0}
    best = int(np.argmax(band)) + lag_min
    bpm = 60.0 * fps / best
    # prefer the folded tempo: map doubles/halves into 60-190 and pick the
    # candidate whose lag has the highest normalized autocorrelation
    cands = []
    for mult in (0.5, 1.0, 2.0):
        b = bpm * mult
        if 60.0 <= b <= 190.0:
            lag = int(fps * 60 / b)
            if lag < len(ac_n):
                cands.append((ac_n[lag], b))
    if not cands:
        cands = [(ac_n[best], bpm)]
    conf, bpm_best = max(cands)
    # report the full candidate set — a half/double ambiguity is common
    # (e.g. 72 BPM ballad read at 144). Judges see every candidate.
    seen, cand_list = set(), []
    for c, b in sorted(cands, reverse=True):
        b = round(float(b), 1)
        if b not in seen:
            seen.add(b)
            cand_list.append({"bpm": b, "confidence": round(float(c), 3)})
    return {"bpm": round(float(bpm_best), 1),
            "bpm_confidence": round(float(conf), 3),
            "bpm_candidates": cand_list}


def _spectral_centroid_db(x: np.ndarray, sr: int) -> float:
    """Broadband brightness proxy: fraction of energy above 8 kHz."""
    n_fft = 2048
    seg = x[: sr * 30]  # first 30 s
    if len(seg) < n_fft:
        return 0.0
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    freqs = np.fft.rfftfreq(len(seg), 1 / sr)
    total = spec.sum() + 1e-12
    hi = spec[freqs >= 8000].sum()
    return round(float(100 * hi / total), 2)


def _dynamics_db(x: np.ndarray, sr: int) -> dict:
    """Crest + windowed RMS spread: loudness-war / squash evidence."""
    win = sr  # 1 s
    n = len(x) // win
    if n < 2:
        return {}
    rms = np.sqrt(np.mean(
        x[: n * win].reshape(n, win) ** 2, axis=1))
    peak = np.abs(x).max() + 1e-12
    rms_all = np.sqrt(np.mean(x ** 2)) + 1e-12
    return {
        "crest_factor_db": round(float(20 * np.log10(peak / rms_all)), 1),
        "rms_1s_min_db": round(float(20 * np.log10(rms.min() + 1e-12)), 1),
        "rms_1s_max_db": round(float(20 * np.log10(rms.max() + 1e-12)), 1),
        "rms_1s_spread_db": round(float(20 * np.log10(
            (rms.max() + 1e-12) / (rms.min() + 1e-12))), 1),
    }


def measure_track(path: Path) -> dict:
    """All measured evidence for one audio file. Raises on undecodable."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    info = _ffprobe(path)
    if not info["duration_s"] or info["duration_s"] < 1.0:
        raise ValueError(f"{path}: not decodable audio "
                         f"(duration={info['duration_s']})")
    vol = _volumedetect(path)
    x = _load_mono(path)
    sr = 22050
    ev = {
        "file": str(path),
        "measured_at_version": "measure.py v1",
        **info,
        **vol,
        "silences_ge_1s": _silence_map(path),
        **_bpm(x, sr),
        "pct_energy_above_8khz": _spectral_centroid_db(x, sr),
        **_dynamics_db(x, sr),
    }
    return ev


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="measure.py — measured evidence extraction for the "
                    "music review panel (ffmpeg + numpy)")
    ap.add_argument("audio")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    ev = measure_track(Path(args.audio))
    print(json.dumps(ev, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
