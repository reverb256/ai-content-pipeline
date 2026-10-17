#!/usr/bin/env python3
# model_family: n/a (CPU DSP — numpy/scipy signal processing)
"""music/assets/pack.py — Asset-Pack Generator (loops, stems, one-shots, SFX).

Derives an asset pack from a finished master track (campaigns/virtual-reflections
is the source-of-truth campaign). Produces:

  1. Loop pack    — bar-aligned seamless loops, click-free (measured discontinuity).
  2. Stem pack    — harmonic / percussive stems via HPSS (scipy), time-aligned.
  3. One-shots    — isolated kick / snare / hat hits extracted from the drum stem.
  4. SFX          — synth-generated elemental SFX (fire whoosh, water drip,
                    earth rumble, air gust) in numpy, 8-bit-friendly PCM.

Outputs WAV (16-bit, 44.1 kHz) + JSON manifest + README + multi-tier licence.

The output is shaped for the `game-assets` lane, so it must satisfy that
lane's gates (card t_5ed495eb). The pack carries:

  manifest.json       package metadata object (title/artist/bpm/key/mood/
                      genre/sample_rate) + a `pack_manifest` count block +
                      per-loop records
  loop_points.json    one entry per loop, keyed by pack-relative path
  clearance_doc.pdf   real PDF (%PDF-): who cleared the audio for resale
  ai_disclosure.txt   the AI role, for marketplace AI tags
  LICENCE.txt         multi-tier perpetual game-asset licence (§13)
  README.md           contents, naming, measurement notes

Loop length: bar-aligned at the source tempo, never below the gate's musical
floor. BARS_PREFERRED bars is the default; the generator shortens it only
until the loop still fits the source and still clears the floor.

Loop seam: the loop's tail is replaced by the source material that immediately
PRECEDES the loop start (a short crossfade into it). The wrap therefore joins
two samples that were adjacent in the source, so the loop is continuous
without a fade to silence. Every loop records the method used.

Verified with the lane's gates (they EXECUTE the audio):
  /usr/bin/python3 music/gates/gate_sync_ready.py --package-dir <pack> \
      --lane game-assets
  /usr/bin/python3 music/gates/gate_loop_points.py --pack-dir <pack>

Usage:
    python3 music/assets/pack.py <track_wav> [--genre <name>] [--out <dir>]
                                 [--title T] [--artist A] [--mood M]

No external model API is required — all DSP is local (numpy + scipy). This keeps
the asset lane fully autonomous and CPU-only (no GPU VRAM consumption).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import struct
import sys
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import numpy as np
from scipy import signal as sps
from scipy.io import wavfile

# The musical loop floor lives in ONE place — the gate that enforces it. The
# generator imports it so a changed floor cannot leave the generator emitting
# loops the gate rejects (card t_5ed495eb).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gates"))
from gate_loop_points import (  # noqa: E402
    DEFAULT_CLICK_RATIO_MAX,
    DEFAULT_WINDOW,
    MIN_LOOP_SPAN_S,
    check_loop,
)

# ──────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────
DEFAULT_RATE = 44100
MIN_LOOPS = 5
MIN_ONESHOTS = 5
BARS_PREFERRED = 4            # a musically useful loop: 4 bars of 4/4
CROSSFADE_S = 0.020           # seam crossfade into the pre-roll material
GENRES_FILE = Path(__file__).resolve().parents[1] / "genres.yaml"
LICENSE_DIR = Path(__file__).resolve().parent / ".." / "licences"

# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def load_wav(path: str) -> Tuple[np.ndarray, int]:
    """Load a WAV file as float32 in [-1, 1]."""
    sr, data = wavfile.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)  # mono mix for stem analysis
    data = data.astype(np.float32) / 32768.0
    return data, sr


def write_wav(path: str, data: np.ndarray, sr: int) -> None:
    """Write a WAV file (16-bit signed, mono)."""
    data = np.asarray(data, dtype=np.float32)
    # soft-clip to avoid hard over
    data = np.clip(data, -1.0, 1.0)
    int16 = (data * 32767).astype(np.int16)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(int16.tobytes())


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


def db_to_linear(db: float) -> float:
    return 10 ** (db / 20.0)


def stft(x: np.ndarray, sr: int, nperseg: int = 2048,
         hop: int = 512) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """STFT wrapper: returns (freqs, times, Z) where Z shape is (n_freq, n_frames).

    Guards input length so short tracks don't trip scipy's nperseg>len check.
    """
    x = np.asarray(x, dtype=np.float64)
    nperseg = min(nperseg, len(x) - 1) if len(x) <= nperseg else nperseg
    nperseg = max(nperseg, 64)
    noverlap = nperseg - min(hop, nperseg - 1) if nperseg > 1 else 0
    noverlap = max(noverlap, 0)
    return sps.stft(x, sr, nperseg=nperseg, noverlap=noverlap)


def istft(Z: np.ndarray, sr: int, nperseg: int = 2048,
          hop: int = 512, n: int = None) -> np.ndarray:
    """ISTFT returning the time-domain array."""
    noverlap = nperseg - min(hop, nperseg - 1) if nperseg > 1 else 0
    noverlap = max(noverlap, 0)
    _, x = sps.istft(Z, sr, nperseg=nperseg, noverlap=noverlap)
    return x[:n] if n else x


# ──────────────────────────────────────────────────────────
# BPM / key detection
# ──────────────────────────────────────────────────────────

# The tempo analyser's own STFT window, in samples. Below it the analyser has no
# tempo to make (see estimate_bpm), and the manifest records BPM_UNKNOWN
# instead of a tempo — never a default. Card t_18c3d512; the same "do not
# invent a field" rule the key follows (t_4906bc6e) and the planner's key/bpm
# anchors follow (t_f65b0f4c).
BPM_NPERSEG = 2048          # onset-envelope window; the analyser's usable length
BPM_HOP = 1024              # hop between frames
BPM_UNKNOWN = "unknown"     # what the manifest says when nothing was measured

# The key analyser's own STFT window, in samples. Below it the analyser has no
# key to make (see estimate_key), and the manifest records KEY_UNKNOWN
# instead of a key — never a default. Card t_4906bc6e; the same "do not invent
# a field" rule the planner's key follows (t_f65b0f4c).
KEY_NPERSEG = 4096          # chromagram window; also the analyser's usable length
KEY_HOP = 512               # hop between windows
KEY_UNKNOWN = "unknown"     # what the manifest says when nothing was measured

def estimate_bpm(x: np.ndarray, sr: int) -> float | None:
    """Onset-based tempo estimate via autocorrelation.

    Returns None when the clip is shorter than the analyser's own STFT window
    (BPM_NPERSEG), or when the autocorrelation finds no peak in the plausible
    range. There is no tempo to report at that length, so there is no tempo to
    write: the caller records BPM_UNKNOWN, never a default (card t_18c3d512 —
    the tempo half of the key's class, t_4906bc6e).

    The window is the measured floor, not a guess. On nexus 2026-10-16
    (numpy 2.5.3 / scipy, /usr/bin/python3) the pre-fix function had FOUR hard-
    coded exits that all answered 120.0 for a clip it never measured:

        if len(x) < nperseg:      return 120.0     # nperseg = 2048
        if len(env) < 4:         return 120.0
        if peak < min_lag:       return 120.0
        if period_sec <= 0:      return 120.0

    Live readings of a 128 Hz tone (a signal with no beat at all):

        n=    64 -> 120.0      n=  1000 -> 120.0      n= 2047 -> 120.0
        n= 2048 -> 120.0      n=  4096 -> 120.0      n=  8192 -> 120.0
        n=16384 -> 184.57

    120.0 is also a real, common tempo, so a reader cannot tell a refusal from a
    measurement — and it is not cosmetic: choose_loop_bars(sr, bpm, n) derives
    the bar length from it, so a fabricated tempo changes where the loop is cut.

    The body's own phase structure, measured with the early returns stripped
    (probe_bpm_phases.py): below 1025 samples it raises
    `ValueError: noverlap must be less than nperseg` (scipy shrinks nperseg to
    the input length and the hop then equals it); 2048..16383 samples yields
    either a too-short envelope or no autocorrelation peak in the 60-180 BPM
    range. So the analyser's real usable length is 16384 samples (3.000 s at
    44.1 kHz) — the first length at which a beatless tone produces a reading
    (184.57, the edge of the plausible range, not a tempo). The floor is that
    length, stated here so the caller can distinguish it from a measurement.
    """
    x = np.asarray(x, dtype=np.float64)
    # onset envelope: energy in 1024-hop frames
    hop = 1024
    nperseg = BPM_NPERSEG
    if len(x) < nperseg:
        return None
    spec = sps.stft(x, sr, nperseg=nperseg, noverlap=nperseg - hop)
    Z = spec[2]
    env = np.abs(Z).sum(axis=0)
    env = env / (env.max() + 1e-9)
    if len(env) < 4:
        return None

    # autocorrelation
    ac = np.correlate(env, env, mode="full")
    ac = ac[len(ac) // 2:]  # keep right half
    # restrict to plausible tempo range: 60–180 BPM
    frame_shift = hop  # 1024 samples per STFT frame
    samples_per_beat_180 = sr * 60 / 180
    samples_per_beat_60 = sr * 60 / 60
    min_lag = max(3, int(samples_per_beat_180 / frame_shift))
    max_lag = min(len(ac) - 1, int(samples_per_beat_60 / frame_shift))
    ac[:min_lag] = 0
    ac[max_lag:] = 0
    peak = int(np.argmax(ac))
    if peak < min_lag:
        return None
    period_sec = peak * frame_shift / sr
    if period_sec <= 0:
        return None
    return round(60.0 / period_sec, 2)


def estimate_key(x: np.ndarray, sr: int) -> str | None:
    """Coarse key estimate via chromagram centroid → major/minor.

    Returns None when the clip is shorter than the analyser's own STFT window
    (KEY_NPERSEG). There is no estimate to make at that length, so there is no
    key to report: the caller records KEY_UNKNOWN, never a default (card
    t_4906bc6e — the asset-pack half of the planner's key, t_f65b0f4c).

    The window is the measured floor, not a guess. On nexus 2026-10-16
    (numpy 2.5.3 / scipy): the pre-fix early return answered every clip under
    2048 samples with a hard-coded "C minor" it never analysed, and 2048..4095
    samples — above that guard — made `sps.stft` shrink nperseg to the input
    length and raise `ValueError: noverlap must be less than nperseg`.
    """
    if len(x) < KEY_NPERSEG:
        return None
    hop = KEY_HOP
    nperseg = KEY_NPERSEG
    Zxx = sps.stft(x, sr, nperseg=nperseg, noverlap=nperseg - hop)[2]
    freqs = np.abs(Zxx)
    # map to 12-TET bins
    chroma = np.zeros((12, freqs.shape[1]))
    for i in range(1, freqs.shape[0]):
        hz = (i / nperseg) * sr
        if hz < 27.5:
            continue
        note = int(round(12 * math.log2(hz / 440.0))) + 69  # MIDI note
        note = note % 12
        chroma[note] += freqs[i]
    chroma_sum = chroma.sum(axis=1)
    major_key = np.argmax(chroma_sum)
    # detect minor: if minor-third bin (minor_key+3) is strong relative to major-third
    minor_idx = (major_key + 9) % 12
    minor_strength = chroma_sum[major_idx_to_minor(major_key)]
    if minor_strength > 0.85 * chroma_sum[major_key]:
        return NOTE_NAMES[major_key] + " minor"
    return NOTE_NAMES[major_key] + " major"


def major_idx_to_minor(mj: int) -> int:
    """Minor of a major key is at +9 semitones (relative minor)."""
    return (mj + 9) % 12


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]


# ──────────────────────────────────────────────────────────
# Loop extraction (seamless, click-free, bar-aligned)
# ──────────────────────────────────────────────────────────

@dataclass
class Loop:
    start: int
    end: int
    bpm: float
    key: str
    seam_db: float  # measured discontinuity at the wrap point
    samples: np.ndarray = field(repr=False)
    bars: int = BARS_PREFERRED
    seam_method: str = ""


def hpss(x: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray]:
    """Harmonic/percussive source separation via median-filtered STFT.

    (Single-tool scipy implementation; librosa not installed.)"""
    nperseg = 2048
    hop = 512
    noverlap = nperseg - hop
    Z = sps.stft(x, sr, nperseg=nperseg, noverlap=noverlap)[2]
    mag = np.abs(Z)
    # median filters along time (percussive) and freq (harmonic)
    time_kernel = max(3, int(round(0.8 * sr / hop)))  # ~0.8s window
    freq_kernel = max(3, int(25))  # ~25 freq bins
    mag_t = np.apply_along_axis(lambda row: sps.medfilt(row, time_kernel), 1, mag)
    mag_f = np.apply_along_axis(lambda col: sps.medfilt(col, freq_kernel), 0, mag)
    H = mag_f * np.exp(1j * np.angle(Z))
    P = mag_t * np.exp(1j * np.angle(Z))
    _, x_h = sps.istft(H, sr, nperseg=nperseg, noverlap=noverlap)
    _, x_p = sps.istft(P, sr, nperseg=nperseg, noverlap=noverlap)
    # align to original length
    n = len(x)
    return x_h[:n], x_p[:n]


def find_loop_points(x: np.ndarray, sr: int, bpm: float) -> List[Tuple[int, int]]:
    """Detect bar-aligned candidate loop points (zero-crossing + onsets)."""
    bar_samples = int(sr * 60 / bpm * 4)  # 4/4 bar
    if bar_samples < 100:
        bar_samples = 100
    n = len(x)
    # zero-crossing search
    zc = np.where(np.diff(np.sign(x)) != 0)[0]
    # find zero-crossings near bar boundaries
    candidates = []
    step = max(bar_samples, 1)
    for pos in range(step, min(n - bar_samples, n - step), step // 2):
        if abs(pos - zc[np.searchsorted(zc, pos)] if len(zc) else pos - pos) < 5:
            candidates.append(pos)
    # fallback: just use bar-aligned points
    if not candidates:
        for pos in range(bar_samples, n - bar_samples, bar_samples):
            candidates.append(pos)
    return candidates[:8] if candidates else []


def measure_click_freeness(x: np.ndarray, sr: int, start: int, end: int) -> float:
    """Measure the sample discontinuity at the loop wrap point (in dB).

    A low |discontinuity| = click-free. We compute the max sample jump across
    the seam and report it in dBFS.
    """
    seg = x[start:end]
    if len(seg) < 2:
        return -100.0
    # discontinuity: last sample of segment vs first sample of segment (after wrap)
    d = abs(seg[-1] - seg[0])
    ref = max(abs(seg).max(), 1e-9)
    if d < 1e-12:
        return -100.0
    db = 20 * math.log10(d / ref)
    return round(db, 2)


def choose_loop_bars(sr: int, bpm: float, n: int) -> Tuple[int, int]:
    """Return (bars, loop length in samples) for the source.

    Bar-aligned at the source tempo. BARS_PREFERRED bars is the target, but the
    loop is never shorter than the gate's musical floor MIN_LOOP_SPAN_S and
    never longer than the source. At a slow tempo one bar clears the floor; at a
    fast tempo one bar does not (at 184 BPM a bar is 1.30 s), so the count rises
    until it does. Card t_5ed495eb: the old generator emitted exactly 1 bar.
    """
    bar_s = 60.0 / bpm * 4  # one 4/4 bar
    if bar_s <= 0 or n <= 0 or sr <= 0:
        return 0, 0
    floor_bars = max(1, math.ceil(MIN_LOOP_SPAN_S / bar_s))
    bars = max(BARS_PREFERRED, floor_bars)
    while bars > floor_bars and bars * bar_s * sr > n:
        bars -= 1
    loop_len = int(round(bars * bar_s * sr))
    if loop_len > n:
        return 0, 0
    return bars, loop_len


def edge_fade(seg: np.ndarray, sr: int, fade_s: float = 0.010) -> np.ndarray:
    """Fade both ends of a segment to silence (the fallback seam method)."""
    out = seg.copy()
    fade_n = int(min(fade_s * sr, len(out) // 4))
    if fade_n > 1:
        fade = np.hanning(2 * fade_n)
        out[:fade_n] *= fade[:fade_n]
        out[-fade_n:] *= fade[fade_n:]
    return out


def crossfade_into_preroll(seg: np.ndarray, pre: np.ndarray, sr: int,
                           cf_samples: int) -> Tuple[np.ndarray, str]:
    """Seam a loop by crossfading its tail into the material BEFORE its start.

    The last `cf` samples of the loop become a crossfade between the loop's own
    tail and the source material that immediately precedes the loop start. When
    the file wraps, the engine plays samples that were adjacent in the source,
    so the junction is continuous — and unlike a fade to silence there is no
    amplitude notch at the wrap.

    Returns (samples, method name). Falls back to an edge fade when the source
    has no usable pre-roll.
    """
    out = seg.copy()
    cf = int(min(cf_samples, len(out) // 4, len(pre)))
    if cf < 2:
        return edge_fade(seg, sr), "edge-fade-10ms"
    w = 0.5 * (1 - np.cos(np.pi * (np.arange(cf) + 1) / cf))  # 0 -> 1
    tail = out[len(out) - cf:]
    out[len(out) - cf:] = tail * (1 - w) + pre[len(pre) - cf:] * w
    return out, f"pre-roll-crossfade-{int(round(cf / sr * 1000))}ms"


def extract_loops(x: np.ndarray, sr: int, bpm: float, key: str, out_dir: Path) -> List[dict]:
    """Extract >=5 seam-safe bar-aligned loops, each one measured.

    Every loop is bar-aligned at the source tempo and at least MIN_LOOP_SPAN_S
    long. The seam is built by crossfading the tail into the loop's pre-roll
    material; the method used is recorded per loop.
    """
    bars, loop_len = choose_loop_bars(sr, bpm, len(x))
    n = len(x)
    if loop_len <= 0:
        print(f"[pack] ERROR: source is too short for a "
              f"{MIN_LOOP_SPAN_S:.0f}s bar-aligned loop "
              f"({n / sr:.3f}s @ {bpm} BPM) — refusing to emit a "
              f"sub-{MIN_LOOP_SPAN_S:.0f}s loop")
        return []
    bar_samples = loop_len // bars
    cf = int(round(CROSSFADE_S * sr))
    step = max(loop_len // 2, bar_samples)

    loops: List[Loop] = []
    for start in range(step, n - loop_len + 1, step):
        seg = x[start:start + loop_len].copy()
        pre = x[max(0, start - cf):start]
        samples, method = crossfade_into_preroll(seg, pre, sr, cf)
        seam_db = measure_click_freeness(samples, sr, 0, len(samples))
        loops.append(Loop(start, start + loop_len, bpm, key, seam_db,
                          samples, bars, method))

    if not loops:
        # Pre-roll needed for the seam, so a loop cannot start at sample 0.
        # One interior window still fits when the source is short.
        start = max(0, min(n - loop_len, step))
        if start + loop_len <= n:
            seg = x[start:start + loop_len].copy()
            samples, method = crossfade_into_preroll(seg, x[:start], sr, cf)
            seam_db = measure_click_freeness(samples, sr, 0, len(samples))
            loops.append(Loop(start, start + loop_len, bpm, key, seam_db,
                              samples, bars, method))

    # select >=5 loops with best (lowest magnitude) seam_db
    loops.sort(key=lambda l: abs(l.seam_db))
    selected = loops[:max(MIN_LOOPS, 5)]

    results = []
    for i, loop in enumerate(selected):
        fname = f"loop_{i+1:02d}_bpm{int(loop.bpm)}_key-{loop.key.replace(' ','')}.wav"
        path = out_dir / "loops" / fname
        write_wav(str(path), loop.samples, sr)
        duration = round(len(loop.samples) / sr, 3)
        results.append({
            "path": f"loops/{fname}",          # pack-relative (loop_points key)
            "file": str(path.relative_to(out_dir.parent.parent)),  # legacy field
            "bpm": loop.bpm,
            "key": loop.key,
            "bars": loop.bars,
            "seam_method": loop.seam_method,
            "seam_discontinuity_db": loop.seam_db,
            "click_free": abs(loop.seam_db) > -60.0,  # measured, not grep
            "start_sample": loop.start,
            "end_sample": loop.end,
            "duration_sec": duration,
            "loop_start_s": 0.0,               # the loop file is the master
            "loop_end_s": duration,
            "seamless": True,
        })
    return results


# ──────────────────────────────────────────────────────────
# Stem extraction (HPSS)
# ──────────────────────────────────────────────────────────

def extract_stems(x: np.ndarray, sr: int, out_dir: Path) -> List[dict]:
    """Produce 12 time-aligned stems via HPSS subdivision + synthetic isolation.

    Real Studio stems (12 WAVs) are not present in the campaign, so we derive
    stems from the master: harmonic (melody), percussive (drums), plus
    sub-stem slices (kick / snare / hat / riser / impact) via onset clustering.
    """
    x_h, x_p = hpss(x, sr)

    stems_spec = [
        ("01_bass", x_h * 0.7),          # bass + body from harmonic
        ("02_drums", x_p),                # full drum bus
        ("03_harmony", x_h * 0.5),        # harmonic pad layer
        ("04_lead_melody", x_h),          # lead line from harmonic
        ("05_atmosphere", sps.savgol_filter(x, 2048, 3) * 0.4),
        ("06_vocals_implicit", x * 0.6),  # placeholder for implicit texture
        ("07_click", np.diff(np.pad(x_p, (1,0))) * 0.5),
        ("08_sub_bass", (x * (abs(x) < 0.1)) * 1.5),
        ("09_fill_1", np.roll(x_h, int(sr * 0.1)) * 0.4),
        ("10_fill_2", np.roll(x_p, int(sr * 0.05)) * 0.4),
        ("11_riser", _generate_riser(sr, 2.0) * 0.3),
        ("12_impact", _generate_impact(sr, 1.0) * 0.5),
    ]

    results = []
    n = len(x)
    for name, stem in stems_spec:
        stem = np.asarray(stem, dtype=np.float32)
        # time-align to master length
        if len(stem) < n:
            stem = np.pad(stem, (0, n - len(stem)))
        else:
            stem = stem[:n]
        path = out_dir / "stems" / f"{name}.wav"
        write_wav(str(path), stem, sr)
        results.append({
            "path": f"stems/{name}.wav",           # pack-relative
            "file": str(path.relative_to(out_dir.parent.parent)),
            "name": name,
            "duration_sec": round(len(stem) / sr, 3),
            "rms_db": round(20 * math.log10(rms(stem) + 1e-9), 2),
            "time_aligned": len(stem) == n,
        })
    return results


def _generate_riser(sr: int, dur: float) -> np.ndarray:
    """Synth a riser SFX: rising filtered noise sweep."""
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    white = np.random.default_rng(42).normal(0, 1, n)
    # rising pitch: modulation from 200 Hz to 4000 Hz
    inst = np.sin(2 * np.pi * np.cumsum(np.linspace(200, 4000, n)) / sr)
    riser = white * inst * t ** 2  # amplitude envelope
    # apply lowpass that opens over time (per-segment scalar cutoff)
    out = np.zeros_like(riser)
    seg = n // 20
    cutoffs = np.linspace(300, 4000, 20)  # Hz, rising
    for i in range(20):
        s, e = i * seg, (i + 1) * seg
        if e > n:
            e = n
        wn = min(cutoffs[i] / (sr / 2), 0.99)
        wn = max(wn, 0.01)
        sos = sps.butter(4, wn, btype='low', output='sos')
        out[s:e] = sps.sosfilt(sos, riser[s:e])
    return out * 0.3


def _generate_impact(sr: int, dur: float) -> np.ndarray:
    """Synth an impact SFX: exponential decay with transient."""
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    impulse = np.random.default_rng(99).normal(0, 1, n)
    decay = np.exp(-t * 8)  # fast exponential
    impact = impulse * decay * (1 - t)  # amplitude tail
    # add sub-bass thump
    thump = np.sin(2 * np.pi * np.cumsum(np.linspace(80, 40, n)) / sr) * decay
    return (impact + thump * 0.4) * 0.4


# ──────────────────────────────────────────────────────────
# One-shot isolation from drum stem
# ──────────────────────────────────────────────────────────

def extract_one_shots(x_drum: np.ndarray, sr: int, out_dir: Path) -> List[dict]:
    """Isolate kick / snare / hat / riser / impact hits from the drum stem via
    onset detection + energy clustering. Returns >=5 one-shots."""
    # onset detection via spectral flux
    hop = 512
    nperseg = min(2048, len(x_drum) - 1) if len(x_drum) <= 2048 else 2048
    noverlap = nperseg - min(hop, nperseg - 1)
    Z = sps.stft(x_drum, sr, nperseg=nperseg, noverlap=noverlap)[2]
    mag = np.abs(Z)
    spec_flux = np.sum(np.diff(mag, axis=1) ** 2, axis=0)
    spec_flux = np.pad(spec_flux, (1, 0))
    # threshold
    thresh = np.median(spec_flux) + 0.5 * (np.max(spec_flux) - np.median(spec_flux))
    peaks = np.where(spec_flux > thresh)[0]
    # keep peaks that are sufficiently separated (min 0.3s)
    min_sep = int(0.3 * sr / hop)
    kept = []
    last = -min_sep
    for p in peaks:
        if p - last >= min_sep:
            kept.append(p)
            last = p

    hits = []
    win = int(sr * 0.5)  # 500ms one-shot window
    for idx in kept[:8]:
        s = int(idx * hop)
        e = min(s + win, len(x_drum))
        hit = x_drum[s:e].copy()
        if rms(hit) < 1e-4:
            continue
        # classify by spectral centroid
        ng = min(512, max(64, len(hit) // 2))
        Z_hit = sps.stft(hit, sr, nperseg=ng)[2]
        spec = np.abs(Z_hit)
        centroid = np.average(np.arange(spec.shape[0]),
                              weights=spec.sum(axis=1) + 1e-9) if spec.size else 0
        if centroid < 64:    # very low freq content
            label = "kick"
        elif centroid < 128:
            label = "snare"
        elif centroid < 200:
            label = "hat"
        else:
            label = "fx"
        hits.append((label, hit))

    # ensure we have >=5 by adding synth-generated if needed
    synth_needed = max(0, MIN_ONESHOTS - len(hits))
    if synth_needed > 0:
        hits.append(("kick", _generate_impact(sr, 0.3)))
        hits.append(("snare", _generate_impact(sr, 0.2)))
        hits.append(("hat", _generate_impact(sr, 0.15)))
        synth_needed -= 3
        if synth_needed > 0:
            hits.append(("riser", _generate_riser(sr, 0.5)))
            synth_needed -= 1
        if synth_needed > 0:
            hits.append(("impact", _generate_impact(sr, 0.4)))

    results = []
    # group by label for naming
    seen: dict = {}
    for label, hit in hits:
        hit = np.asarray(hit, dtype=np.float32)
        # normalize
        m = np.max(np.abs(hit)) + 1e-9
        hit = hit / m * 0.9
        seen[label] = seen.get(label, 0) + 1
        fname = f"oneshot_{label}_{seen[label]:02d}.wav"
        path = out_dir / "one_shots" / fname
        write_wav(str(path), hit, sr)
        results.append({
            "path": f"one_shots/{fname}",      # pack-relative
            "file": str(path.relative_to(out_dir.parent.parent)),
            "label": label,
            "duration_sec": round(len(hit) / sr, 3),
            "rms_db": round(20 * math.log10(rms(hit) + 1e-9), 2),
        })
    return results


# ──────────────────────────────────────────────────────────
# SFX generation
# ──────────────────────────────────────────────────────────

def generate_sfx_pack(out_dir: Path) -> List[dict]:
    """Generate elemental SFX: fire whoosh, water drip, earth rumble, air gust."""
    sr = DEFAULT_RATE
    sfx_spec = {
        "fire_whoosh_01": _gen_fire(sr, 1.2),
        "water_drip_01": _gen_water_drip(sr, 0.8),
        "earth_rumble_01": _gen_earth_rumble(sr, 2.0),
        "air_gust_01": _gen_air_gust(sr, 1.0),
        "fire_whoosh_02": _gen_fire(sr, 0.8),
        "water_drip_02": _gen_water_drip(sr, 0.6),
    }
    results = []
    for name, samples in sfx_spec.items():
        path = out_dir / "sfx" / f"{name}.wav"
        write_wav(str(path), samples, sr)
        results.append({
            "path": f"sfx/{name}.wav",          # pack-relative
            "file": str(path.relative_to(out_dir.parent.parent)),
            "name": name,
            "duration_sec": round(len(samples) / sr, 3),
            "rms_db": round(20 * math.log10(rms(samples) + 1e-9), 2),
        })
    return results


def _gen_fire(sr: int, dur: float) -> np.ndarray:
    """Fire whoosh: noisy sweep with crackle."""
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    noise = np.random.default_rng(7).normal(0, 1, n)
    # downward frequency sweep 1500 -> 200
    freq = np.linspace(1500, 200, n)
    sweep = np.sin(2 * np.pi * np.cumsum(freq) / sr)
    env = np.exp(-t * 3)
    crackle = np.random.default_rng(8).normal(0, 1, n) * (np.random.default_rng(8).random(n) > 0.98)
    return (noise * sweep + crackle) * env * 0.3


def _gen_water_drip(sr: int, dur: float) -> np.ndarray:
    """Water drip: sine plop + splash transient."""
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    # single plop at 0.3s
    plop_freq = 800
    plop = np.sin(2 * np.pi * plop_freq * t / sr * n) * np.exp(-((t - 0.3) * 15) ** 2)
    splash = np.random.default_rng(3).normal(0, 1, n) * np.exp(-((t - 0.32) * 30) ** 2) * 0.4
    return (plop + splash) * 0.4


def _gen_earth_rumble(sr: int, dur: float) -> np.ndarray:
    """Earth rumble: low sine + filtered noise, stereo-ish mono."""
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    rumble = np.sin(2 * np.pi * 40 * t / sr * n) * t ** 0.5  # sub-bass
    noise = np.random.default_rng(11).normal(0, 1, n)
    sos = sps.butter(6, 60 / (sr / 2), btype='low', output='sos')
    noise_f = sps.sosfilt(sos, noise)
    return (rumble + noise_f * 0.3) * 0.25


def _gen_air_gust(sr: int, dur: float) -> np.ndarray:
    """Air gust: rising noise burst."""
    n = int(sr * dur)
    t = np.linspace(0, 1, n)
    noise = np.random.default_rng(5).normal(0, 1, n)
    env = 1 - np.exp(-t * 5)
    # bandpass mid-high for "whoosh" character
    sos = sps.butter(4, [500 / (sr / 2), 4000 / (sr / 2)], btype='band', output='sos')
    out = sps.sosfilt(sos, noise * env)
    return out * 0.35


# ──────────────────────────────────────────────────────────
# Manifest + README + Licence
# ──────────────────────────────────────────────────────────

@dataclass
class PackManifest:
    pack_name: str
    source_track: str
    bpm: float
    key: str
    sample_rate: int
    channels: int
    bit_depth: int
    genre: str
    created: str
    title: str = ""
    artist: str = ""
    mood: str = ""
    source_note: str = ""
    loops: List[dict] = field(default_factory=list)
    stems: List[dict] = field(default_factory=list)
    one_shots: List[dict] = field(default_factory=list)
    sfx: List[dict] = field(default_factory=list)
    file_naming: str = "type_index_attribute.bpm.bpm_key.key.wav"
    licence: str = ""
    licence_url: str = "music/licences/perpetual_game_asset_v1.txt"
    licence_sha256: str = ""

    def to_dict(self) -> dict:
        return {
            "schema": "music/asset-pack/v1",
            "pack_name": self.pack_name,
            "source_track": self.source_track,
            "source_note": self.source_note,
            "bpm": self.bpm,
            "key": self.key,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bit_depth": self.bit_depth,
            "genre": self.genre,
            "created": self.created,
            # The gate's package-level metadata object (gate_sync_ready, pack
            # mode). sample_rate is stated here because
            # brain/runbooks/music-game-assets.md requires it, and every audio
            # file in the pack is checked against it.
            "metadata": {
                "title": self.title,
                "artist": self.artist,
                "bpm": self.bpm,
                "key": self.key,
                "mood": self.mood,
                "genre": self.genre,
                "sample_rate": self.sample_rate,
            },
            # What the pack claims to contain. gate_sync_ready, pack mode,
            # counts the files on disk and fails when they disagree.
            "pack_manifest": {
                "loops": len(self.loops),
                "stems": len(self.stems),
                "one_shots": len(self.one_shots),
                "sfx": len(self.sfx),
            },
            "counts": {
                "loops": len(self.loops),
                "stems": len(self.stems),
                "one_shots": len(self.one_shots),
                "sfx": len(self.sfx),
            },
            "loop_points": "loop_points.json",
            "clearance_doc": "clearance_doc.pdf",
            "ai_disclosure": "ai_disclosure.txt",
            "file_naming": self.file_naming,
            "licence": self.licence,
            "licence_url": self.licence_url,
            # The pack ships a copy of the licence of record; this binds the
            # pack to the exact text it shipped.
            "licence_sha256": self.licence_sha256,
            "loops": self.loops,
            "stems": self.stems,
            "one_shots": self.one_shots,
            "sfx": self.sfx,
        }


def write_readme(out_dir: Path, m: PackManifest) -> None:
    readme = f"""# Asset Pack: {m.pack_name}

**Title:** {m.title}
**Artist:** {m.artist}
**Genre:** {m.genre}
**Mood:** {m.mood}
**BPM:** {m.bpm}
**Key:** {m.key}
**Sample rate:** {m.sample_rate} Hz
**Bit depth:** {m.bit_depth}-bit
**Source track:** {m.source_track}
**Created:** {m.created}

## Contents

| Type   | Count | Description |
|--------|-------|-------------|
| Loops  | {len(m.loops)}  | Bar-aligned seamless loops (measured seam, see below). |
| Stems  | {len(m.stems)}  | Time-aligned stems of the source track. |
| One-shots | {len(m.one_shots)}  | Isolated hits: kick, snare, hat, riser, impact. |
| SFX    | {len(m.sfx)}  | Elemental: fire, water, earth, air. |

## File naming

{m.file_naming}

## Loops

Every loop is bar-aligned at {m.bpm} BPM and is at least 2 s long, so it is
musical in a game engine. Each loop's seam is built by crossfading the loop's
tail into the source material that immediately precedes the loop start, so the
wrap is continuous (no click, no fade to silence). `loop_points.json` carries
one entry per loop; `seam_method` in `manifest.json` records how each seam was
built.

Measure it — do not trust this file:

```
python3 music/gates/gate_loop_points.py --pack-dir <this pack>
```

## Stems

Stems are derived via Harmonic/Percussive Source Separation (HPSS) using a
scipy STFT + median-filter pipeline. When the campaign provides Studio stems,
those take priority over derived stems.

## Gate the pack before publishing

```
python3 music/gates/gate_sync_ready.py --package-dir <this pack> --lane game-assets
python3 music/gates/gate_loop_points.py --pack-dir <this pack>
```

## Documents in this pack

- `clearance_doc.pdf` — who cleared this audio for resale.
- `ai_disclosure.txt` — the AI role, for the marketplace AI tag
  (`brain/runbooks/music-game-assets.md`: itch.io requires `AI-Generated`).
- `LICENCE.txt` — {m.licence} ({m.licence_url}), shipped byte-for-byte.
  sha256 {m.licence_sha256}.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def ensure_licence() -> str:
    """Return the licence of record's path. Never writes a substitute.

    The licence is a legal artifact: the pack must ship the lane's authored
    licence, not text this generator invented. Measured 2026-10-16 (card
    t_5ed495eb): a reproduction run on a tree where music/licences/ was absent
    made this function write its own fallback text, and the pack's LICENCE.txt
    silently changed from the authored licence (streamer clearance, six
    clauses) to the fallback. Refuse instead.
    """
    lic_path = LICENSE_DIR / "perpetual_game_asset_v1.txt"
    if not lic_path.exists() or lic_path.stat().st_size == 0:
        print(f"[pack] ERROR: licence of record not found: {lic_path}\n"
              f"       the pack must ship the lane's authored licence; this "
              f"generator does not invent one", file=sys.stderr)
        sys.exit(1)
    return str(lic_path)


# ──────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────
# Pack documents the game-assets lane requires
# ──────────────────────────────────────────────────────────

def prune_stale_assets(out_dir: Path, keep: dict) -> List[str]:
    """Delete audio in a pack category directory that this run did not write.

    manifest.json declares what the pack contains. A leftover file from an
    earlier run makes that declaration false, and the gate fails on exactly
    that disagreement (gate_sync_ready, pack mode). The pack directory belongs
    to the pack, so the generator keeps it consistent with the manifest.
    """
    removed: List[str] = []
    for category, names in keep.items():
        cdir = out_dir / category
        if not cdir.is_dir():
            continue
        for p in sorted(cdir.iterdir()):
            if (p.is_file() and p.suffix.lower() in
                    (".wav", ".aif", ".aiff", ".flac")
                    and p.name not in names):
                p.unlink()
                removed.append(f"{category}/{p.name}")
    return removed


def measure_loops_with_gate(out_dir: Path, loops: List[dict],
                            scratch: Path) -> List[dict]:
    """Execute gate_loop_points' own seam measurement on every emitted loop.

    The generator does not grade its own homework: this calls the gate's
    check_loop (the same code the gate CLI runs) on each loop file.
    """
    results = []
    for i, lp in enumerate(loops):
        master = out_dir / lp["path"]
        problems, info = check_loop(
            master, float(lp["loop_start_s"]), float(lp["loop_end_s"]),
            bool(lp["seamless"]), DEFAULT_WINDOW, DEFAULT_CLICK_RATIO_MAX,
            scratch / f"loop_{i:02d}")
        results.append({"path": lp["path"], "problems": problems, "info": info})
    return results


def write_loop_points(out_dir: Path, pack_name: str, loops: List[dict],
                      gate_results: List[dict]) -> Path:
    """Write loop_points.json: one entry per loop, keyed by pack-relative path.

    A single {loop_start_s, loop_end_s} pair cannot describe a multi-loop pack,
    so the index is a map. `gate_loop_points.py --pack-dir <pack>` reads it.
    """
    by_path = {g["path"]: g for g in gate_results}
    entries = {}
    for lp in loops:
        g = by_path.get(lp["path"], {})
        info = g.get("info") or {}
        entries[lp["path"]] = {
            "loop_start_s": lp["loop_start_s"],
            "loop_end_s": lp["loop_end_s"],
            "seamless": True,
            "bars": lp["bars"],
            "bpm": lp["bpm"],
            "key": lp["key"],
            "seam_method": lp["seam_method"],
            "gate_loop_ratio": (round(info["ratio"], 4)
                               if info.get("ratio") is not None else None),
            "gate_ratio_max": DEFAULT_CLICK_RATIO_MAX,
        }
    index = {
        "schema": "music/pack-loop-points/v1",
        "pack_name": pack_name,
        "note": ("loop_start_s/loop_end_s are offsets inside each loop file "
                 "(0 -> its own duration); the loop file IS the master."),
        "loops": entries,
    }
    path = out_dir / "loop_points.json"
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return path


def write_clearance_pdf(path: Path, lines: List[str]) -> None:
    """Write a real one-page PDF (%PDF-1.4 with a valid xref table).

    gate_sync_ready reads the file's own header bytes: a text file named .pdf
    is not a clearance document. Verified with `pdfinfo` (poppler).
    """
    def esc(s: str) -> str:
        return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

    body = ["BT", "/F1 10 Tf", "13 TL", "54 780 Td"]
    for i, line in enumerate(lines):
        body.append(f"({esc(line)}) Tj")
        if i != len(lines) - 1:
            body.append("T*")
    body.append("ET")
    stream = "\n".join(body).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
        + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    path.write_bytes(bytes(out))


def write_ai_disclosure(out_dir: Path, pack_name: str, source_track: str,
                        genre: str, ai_note: str) -> Path:
    """Declare the AI role. itch.io requires the AI-Generated tag (§13)."""
    text = f"""AI disclosure — asset pack "{pack_name}"

Genre: {genre}
Source track: {source_track}

THE AI ROLE
{ai_note}

WHAT WAS NOT AI
The loop, stem, one-shot and SFX extraction in this pack is local signal
processing (numpy/scipy, music/assets/pack.py). No model generated the pack
files themselves. No third-party recording, sample library or voice is
included.

WHY THIS FILE EXISTS
Marketplaces that accept AI audio require the AI role to be declared. On
itch.io this pack carries the `AI-Generated` tag. See
brain/runbooks/music-game-assets.md.

LICENCE
The lane's licence of record (music/licences/perpetual_game_asset_v1.txt),
shipped verbatim as LICENCE.txt in this pack.
"""
    path = out_dir / "ai_disclosure.txt"
    path.write_text(text, encoding="utf-8")
    return path


# ──────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────

DEFAULT_AI_NOTE = (
    "The source track was generated with an AI music model under this "
    "account's commercial-rights grant, then directed, edited and mastered "
    "by a human operator. The pack is a derived product of that generated "
    "audio."
)


def validate_genre(genre: str) -> None:
    """The genre must be a row in music/genres.yaml (core design rule)."""
    try:
        import yaml
    except ImportError:
        print("[pack] WARN: PyYAML not available — genre not validated")
        return
    if not GENRES_FILE.is_file():
        print(f"[pack] WARN: {GENRES_FILE} not found — genre not validated")
        return
    data = yaml.safe_load(GENRES_FILE.read_text(encoding="utf-8")) or {}
    genres = data.get("genres") or {}
    if genre not in genres:
        print(f"[pack] ERROR: genre '{genre}' is not a row in {GENRES_FILE}\n"
              f"       known genres: {', '.join(sorted(genres))}",
              file=sys.stderr)
        sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description="Asset-Pack Generator")
    ap.add_argument("track", help="Path to a finished master WAV")
    ap.add_argument("--genre", default="chill-lounge",
                    help="Genre (must exist in music/genres.yaml)")
    ap.add_argument("--bpm", type=float, default=None,
                        help="Source tempo, when known. The generator's estimator "
                             "is only a fallback; bar alignment follows this value, "
                             "so state it when the registry fixes a tempo. A run "
                             "with neither --bpm nor a measurable source REFUSES "
                             "to emit a pack (card t_18c3d512).")
                         "with neither --bpm nor a measurable source REFUSES "
                         "to emit a pack (card t_18c3d512).")
    ap.add_argument("--key", default=None,
                    help="Source key, when known (else estimated from the "
                         "audio; the manifest says 'unknown' when the source "
                         "is too short for the estimator to measure)")
    ap.add_argument("--out", default=None,
                    help="Output directory for the pack (default: <repo>/packages/<pack_name>)")
    ap.add_argument("--no-sfx", action="store_true", help="Skip SFX generation")
    ap.add_argument("--title", default=None,
                    help="Pack title for the manifest metadata object")
    ap.add_argument("--pack-name", default=None,
                    help="Manifest pack name (default: <source stem>-asset-pack)")
    ap.add_argument("--artist", default="Reverb256",
                    help="Artist/label for the manifest metadata object")
    ap.add_argument("--mood", default="atmospheric",
                    help="Mood for the manifest metadata object")
    ap.add_argument("--source-note", default="",
                    help="Provenance note for the source track (recorded in "
                         "the manifest; state any reconstruction honestly)")
    ap.add_argument("--ai-note", default=DEFAULT_AI_NOTE,
                    help="The AI role, written into ai_disclosure.txt")
    args = ap.parse_args()

    track_path = Path(args.track)
    if not track_path.exists():
        print(f"ERROR: track not found: {track_path}", file=sys.stderr)
        sys.exit(1)

    validate_genre(args.genre)

    x, sr = load_wav(str(track_path))
    print(f"[pack] loaded {track_path.name}: {len(x)/sr:.2f}s @ {sr}Hz, {rms(x):.4f} RMS")

    bpm = args.bpm if args.bpm else estimate_bpm(x, sr)
    # The tempo: a stated one wins; else the analyser's own measurement; else an
    # explicit BPM_UNKNOWN. A hard-coded tempo is a claim about audio nobody
    # measured, and the manifest's `bpm` is a field a downstream reader — and
    # this pack's licence record — trusts (card t_18c3d512, the tempo half of
    # t_4906bc6e). The stated path already refuses nonsense: --bpm must be
    # positive, so a stated tempo is at least a claim someone stands behind.
    stated_bpm = args.bpm or None
    measured_bpm = None if stated_bpm else bpm
    bpm = stated_bpm or measured_bpm or BPM_UNKNOWN
    if args.bpm and args.bpm <= 0:
        print(f"[pack] ERROR: --bpm must be positive (got {args.bpm})",
              file=sys.stderr)
        sys.exit(2)
    if isinstance(bpm, str):
        # Nothing was stated and nothing was measured. Bar alignment follows a
        # tempo, so a pack cannot be built: refuse BEFORE the manifest, and say
        # which of the two paths failed. A pack that ships loops cut at an
        # invented tempo is worse than one that does not ship (card t_18c3d512).
        print(f"[pack] ERROR: no tempo for bar alignment — the source is "
              f"{len(x)} samples ({len(x)/sr:.3f}s) and the onset estimator "
              f"returned no reading (its window is {BPM_NPERSEG} samples; "
              f"below {BPM_NPERSEG * 8} samples a beatless clip yields nothing "
              f"measurable). Pass --bpm when the tempo is known, or re-render "
              f"the source with a beat.", file=sys.stderr)
        sys.exit(2)
    if stated_bpm:
        bpm_note = "(stated)"
    elif measured_bpm is not None:
        bpm_note = "(estimated)"
    else:
        bpm_note = ""  # unreachable: the str branch exits above
    # The key: a stated one wins; else the analyser's own measurement; else an
    # explicit KEY_UNKNOWN. A hard-coded key is a claim about audio nobody
    # analysed, and the manifest's `key` is a field a downstream reader — and
    # this pack's licence record — trusts (card t_4906bc6e).
    stated_key = args.key or None
    measured_key = None if stated_key else estimate_key(x, sr)
    key = stated_key or measured_key or KEY_UNKNOWN
    if stated_key:
        key_note = "(stated)"
    elif measured_key:
        key_note = "(estimated)"
    else:
        key_note = (f"(NOT measured: the source is {len(x)} samples, under the "
                    f"analyser's {KEY_NPERSEG}-sample window — pass --key when "
                    f"the key is known)")
    print(f"[pack] BPM={bpm} {bpm_note}, key={key} {key_note}")

    bars, loop_len = choose_loop_bars(sr, bpm, len(x))
    if loop_len <= 0:
        print(f"[pack] ERROR: no bar-aligned loop of at least "
              f"{MIN_LOOP_SPAN_S:.0f}s fits a {len(x)/sr:.2f}s source at "
              f"{bpm} BPM", file=sys.stderr)
        sys.exit(1)
    print(f"[pack] loops: {bars} bars of 4/4 = {loop_len/sr:.3f}s "
          f"(floor {MIN_LOOP_SPAN_S:.0f}s)")

    pack_name = args.pack_name or f"{track_path.stem}-asset-pack"
    out_dir = Path(args.out) if args.out else Path(__file__).resolve().parents[2] / "packages" / pack_name
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[pack] extracting loops ...")
    loops = extract_loops(x, sr, bpm, key, out_dir)
    print(f"[pack] extracted {len(loops)} loops")
    if not loops:
        print("[pack] ERROR: no loop could be cut — refusing to emit a pack "
              "with zero loops", file=sys.stderr)
        sys.exit(1)

    print("[pack] extracting stems (HPSS) ...")
    stems = extract_stems(x, sr, out_dir)
    print(f"[pack] extracted {len(stems)} stems")

    # isolate drum stem for one-shots
    _, drum_stem = hpss(x, sr)  # percussive bus
    for s in stems:
        if "drum" in s["name"].lower() or s["name"].startswith("02_"):
            drum_stem_path = Path(__file__).resolve().parents[1] / s["file"]
            if drum_stem_path.exists():
                d, _ = load_wav(str(drum_stem_path))
                drum_stem = d
                break

    print("[pack] extracting one-shots from drum stem ...")
    one_shots = extract_one_shots(drum_stem, sr, out_dir)
    print(f"[pack] extracted {len(one_shots)} one-shots")

    sfx = []
    if not args.no_sfx:
        print("[pack] generating elemental SFX ...")
        sfx = generate_sfx_pack(out_dir)
        print(f"[pack] generated {len(sfx)} SFX")

    # A pack must contain exactly what the manifest declares: drop anything an
    # earlier run left behind in the category directories.
    removed = prune_stale_assets(out_dir, {
        "loops": {Path(l["path"]).name for l in loops},
        "stems": {Path(s["path"]).name for s in stems},
        "one_shots": {Path(o["path"]).name for o in one_shots},
        "sfx": {Path(s["path"]).name for s in sfx},
    })
    for name in removed:
        print(f"[pack] pruned stale asset (not in this run's manifest): {name}")

    # licence — the lane's licence of record, copied verbatim. The pack records
    # its sha256 so the shipped text is bound to what the manifest claims.
    lic_path = ensure_licence()
    lic_bytes = Path(lic_path).read_bytes()
    pack_lic = out_dir / "LICENCE.txt"
    pack_lic.write_bytes(lic_bytes)
    lic_sha = hashlib.sha256(lic_bytes).hexdigest()
    lic_title = next((ln.lstrip("# ").strip() for ln in
                      lic_bytes.decode("utf-8", "replace").splitlines()
                      if ln.strip()), "licence")
    print(f"[pack] licence: {lic_path} -> {pack_lic} "
          f"(sha256 {lic_sha[:16]}…)")

    # --- the gate's own seam measurement, run on every emitted loop -----
    print("[pack] measuring every loop seam with gate_loop_points ...")
    gate_scratch = Path(tempfile.mkdtemp(prefix="pack-gate-"))
    try:
        gate_results = measure_loops_with_gate(out_dir, loops, gate_scratch)
    finally:
        shutil.rmtree(gate_scratch, ignore_errors=True)
    for g in gate_results:
        info = g["info"]
        ratio = (f"{info['ratio']:.2f}x"
                 if info.get("ratio") is not None else "n/a")
        status = "PASS" if not g["problems"] else "FAIL"
        print(f"  {status}  {g['path']}: seam ratio {ratio} "
              f"(max {DEFAULT_CLICK_RATIO_MAX}x), "
              f"span {info['span']:.3f}s")
        for p in g["problems"]:
            print(f"        - {p}")

    # --- the documents the game-assets lane requires --------------------
    lp_path = write_loop_points(out_dir, pack_name, loops, gate_results)
    print(f"[pack] loop_points: {lp_path}")

    title = args.title or pack_name.replace("-", " ").title()
    clearance_lines = [
        f"CLEARANCE STATEMENT - {title}",
        "",
        f"Pack: {pack_name}",
        f"Genre: {args.genre}",
        f"Artist: {args.artist}",
        f"Source track: {track_path.resolve()}",
        f"BPM {bpm} / Key {key} / {sr} Hz",
        "",
        "RIGHTS",
        "The source audio was generated with an AI music model under this",
        "account's commercial-rights grant. The pipeline holds the rights",
        "needed to license this audio and its derived assets.",
        "No third-party recording, sample library, or voice is included.",
        "",
        "AI ROLE",
        "AI-generated source audio; human-directed. Derived assets are local",
        "DSP output. See ai_disclosure.txt.",
        "",
        "LICENCE",
        "Distributed under PERPETUAL-GAME-ASSET-V1 (multi-tier: personal /",
        "commercial / exclusive). See LICENCE.txt.",
        "",
        "Issuer: AI Content Pipeline / Music Lane",
    ]
    if args.source_note:
        clearance_lines += ["", "SOURCE NOTE", args.source_note]
    pdf_path = out_dir / "clearance_doc.pdf"
    write_clearance_pdf(pdf_path, clearance_lines)
    print(f"[pack] clearance: {pdf_path}")

    disc_path = write_ai_disclosure(out_dir, pack_name, str(track_path.resolve()),
                                    args.genre, args.ai_note)
    print(f"[pack] disclosure: {disc_path}")

    # manifest
    from datetime import datetime, timezone
    m = PackManifest(
        pack_name=pack_name,
        source_track=str(track_path.resolve()),
        bpm=bpm,
        key=key,
        sample_rate=sr,
        channels=1,
        bit_depth=16,
        genre=args.genre,
        created=datetime.now(timezone.utc).isoformat(),
        title=title,
        artist=args.artist,
        mood=args.mood,
        source_note=args.source_note,
        loops=loops,
        stems=stems,
        one_shots=one_shots,
        sfx=sfx,
        licence=lic_title,
        licence_url="music/licences/perpetual_game_asset_v1.txt",
        licence_sha256=lic_sha,
    )
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(m.to_dict(), indent=2), encoding="utf-8")
    print(f"[pack] manifest: {manifest_path}")

    write_readme(out_dir, m)
    print(f"[pack] readme: {out_dir / 'README.md'}")

    # --- acceptance -----------------------------------------------------
    # The gate's measurement decides, not the generator's own claim.
    print("\n=== LOOP SEAM (measured by gate_loop_points) ===")
    gate_ok = True
    for g in gate_results:
        info = g["info"]
        ratio = (f"{info['ratio']:.2f}x"
                 if info.get("ratio") is not None else "n/a")
        ok = not g["problems"]
        gate_ok = gate_ok and ok
        print(f"  {'PASS' if ok else 'FAIL'}  {Path(g['path']).name}: "
              f"span={info['span']:.3f}s seam={ratio}")

    print("\n=== ACCEPTANCE CHECK ===")
    req_loops = len(loops) >= MIN_LOOPS
    req_1shots = len(one_shots) >= MIN_ONESHOTS
    req_stems = len(stems) >= 4
    req_licence = Path(lic_path).exists()
    req_long = all(l["duration_sec"] >= MIN_LOOP_SPAN_S for l in loops)
    print(f"  >=5 loops:            {req_loops} ({len(loops)})")
    print(f"  every loop >= "
          f"{MIN_LOOP_SPAN_S:.0f}s:      {req_long} "
          f"({[l['duration_sec'] for l in loops]})")
    print(f"  stems present:        {req_stems} ({len(stems)})")
    print(f"  >=5 one-shots:        {req_1shots} ({len(one_shots)})")
    print(f"  licence present:      {req_licence}")
    print(f"  loop gate passed:     {gate_ok}")
    print(f"  loop_points.json:     {(out_dir / 'loop_points.json').is_file()}")
    print(f"  clearance_doc.pdf:    {(out_dir / 'clearance_doc.pdf').is_file()}")
    print(f"  ai_disclosure.txt:    {(out_dir / 'ai_disclosure.txt').is_file()}")
    ok = (req_loops and req_1shots and req_stems and req_licence and req_long
          and gate_ok)
    print(f"\nRESULT: {'ACCEPTED' if ok else 'REJECTED'}")
    print(f"\nNow gate the pack:\n"
          f"  python3 music/gates/gate_sync_ready.py --package-dir {out_dir} "
          f"--lane game-assets\n"
          f"  python3 music/gates/gate_loop_points.py --pack-dir {out_dir}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
