#!/usr/bin/env python3
"""measure.py — MEASURED evidence extraction for the music review panel.

The panel judges cannot listen. This module EXECUTES the artifact with
ffmpeg/numpy and returns measured facts: duration, loudness (volumedetect
mean/max), sample rate, channels, silence map, onset-based BPM candidates,
spectral centroid, and dynamic range (RMS in 1s windows).

Research basis: Evaluation-Illusion (arXiv:2603.11027) — judges anchor on
surface heuristics when given only text. Feeding MEASURED numbers grounds
the review in the artifact itself.

Tempo (v2, card t_ed609eb0)
---------------------------
The tempo fields report a CANDIDATE SET with its evidence, never one bare
number:

  bpm                 the headline candidate (see the rule below)
  bpm_candidates      every candidate the autocorrelation supports, with the
                      band that supports it, the lag, and the ac value
  bpm_bands           per-band detail: argmax, median ac, top peaks
  bpm_pulse           "measurable" | "none"
  bpm_note            why the headline is not the obvious number, when it is not
  ac_at_anchor        the ac value AT the requested anchor (optional argument)

The onset envelope is measured in four bands (full, 20-500 Hz, 500-8000 Hz,
2000-8000 Hz). A whole-band envelope cannot see a percussion-free bed: the
low-frequency pad energy dominates the spectral flux and the weak transients
that carry the tempo are averaged away. The 2-8 kHz band sees them.

The headline is the candidate with the highest ac PROMINENCE (peak ac minus
that band's median ac — the salience of a peak against its own envelope), not
the raw argmax. Two artefacts of the old single-number estimate are removed:

  * a whole-band argmax that sits at the 60 BPM END of the lag search range is
    a cut, not a peak. When a non-edge candidate reaches at least
    BPM_EDGE_SUPPRESS_RATIO of that ac, the non-edge candidate wins and
    `bpm_note` names the artefact.
  * a candidate's confidence is read at its OWN lag, so a folded half/double
    reports the ac it actually has (the old code read the ac at
    int(60*fps/b), up to a lag away from the peak it claimed).

`bpm` is None and `bpm_pulse` is "none" when nothing reaches
BPM_PULSE_AC_FLOOR: the tool says it cannot measure a tempo instead of
reporting a number it cannot support.

Lag quantisation: the envelope frame rate is sr/HOP = 43.07 Hz, so the lag
grid steps by about 3 BPM at 92 BPM. `ac_at_anchor.lag_bpm` states the tempo
the grid can actually express near the anchor; `ac_at_anchor.near` reports the
best ac within +/-10 % of the anchor period, which is the honest answer to
"is there periodicity at the anchor".

Usage (library):
    from measure import measure_track
    ev = measure_track(Path("track.flac"), anchor_bpm=92)

CLI:
    python3 measure.py <audio> [--anchor-bpm N] [--json]
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

# --- tempo measurement constants -------------------------------------------
SR_DEFAULT = 22050        # decode rate; the band edges below assume it
N_FFT = 1024
HOP = 512
# name, low Hz (inclusive), high Hz (exclusive; None = the sample rate)
BPM_BANDS = (
    ("full", 0.0, None),
    ("bass", 20.0, 500.0),
    ("mid", 500.0, 8000.0),
    ("high", 2000.0, 8000.0),
)
BPM_MIN = 60.0            # candidate search range, BPM
BPM_MAX = 190.0
BPM_CAND_AC_FLOOR = 0.20  # peaks below this are noise, not candidates
BPM_PULSE_AC_FLOOR = 0.25  # nothing at or above this -> no measurable pulse
BPM_EDGE_SUPPRESS_RATIO = 0.75
BPM_MAX_CANDIDATES = 8
BPM_ANCHOR_TOL_BPM = 3.0
MEASURE_VERSION = "measure.py v2"


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


def _stft_mags(x: np.ndarray, n_fft: int = N_FFT,
               hop: int = HOP) -> np.ndarray:
    """Magnitude spectrogram (frames x n_fft//2), one windowed rFFT pass."""
    frames = 1 + (len(x) - n_fft) // hop
    win = np.hanning(n_fft)
    mags = np.empty((frames, n_fft // 2))
    for i in range(frames):
        seg = x[i * hop: i * hop + n_fft] * win
        mags[i] = np.abs(np.fft.rfft(seg))[: n_fft // 2]
    return mags


def _onset_flux(mags: np.ndarray, sr: int, lo_hz: float,
                hi_hz: float | None) -> np.ndarray:
    """Positive spectral flux inside [lo_hz, hi_hz): the onset envelope."""
    d = np.diff(mags, axis=0).clip(min=0)
    if lo_hz > 0.0 or hi_hz is not None:
        freqs = np.fft.rfftfreq(2 * mags.shape[1], 1 / sr)[: mags.shape[1]]
        hi = freqs[-1] + 1.0 if hi_hz is None else hi_hz
        sel = (freqs >= lo_hz) & (freqs < hi)
        if not sel.any():
            return np.zeros(d.shape[0])
        d = d[:, sel]
    flux = np.sum(d, axis=1)
    return flux - flux.mean()


def _ac_peaks(acn: np.ndarray, lag_min: int, lag_max: int) -> list:
    """Local maxima of the normalized autocorrelation inside the lag range.

    The lag_max boundary is included and flagged by the caller: an argmax that
    sits there is a CUT, not a located peak, and it must be visible rather than
    silently winning the headline.
    """
    out = []
    for i in range(max(1, lag_min), lag_max):
        v = acn[i]
        if v > acn[i - 1] and v >= acn[i + 1]:
            out.append((float(v), i))
    if lag_max > max(1, lag_min) and acn[lag_max] >= acn[lag_max - 1]:
        out.append((float(acn[lag_max]), lag_max))
    out.sort(reverse=True)
    return out


def _bpm(x: np.ndarray, sr: int, anchor_bpm: float | None = None) -> dict:
    """Onset-envelope autocorrelation tempo candidates, per band.

    Read the module docstring for the measurement rule. `bpm` is the headline
    candidate; `bpm_candidates` and `bpm_bands` carry the evidence behind it,
    and `bpm_note` explains a headline that is not the obvious number.
    """
    empty = {
        "bpm": None,
        "bpm_confidence": 0.0,
        "bpm_candidates": [],
        "bpm_bands": {},
        "bpm_pulse": "none",
        "bpm_note": "no measurable pulse: the artifact is shorter than 2 s or "
                    "the onset envelope has no variance",
    }
    if len(x) < sr * 2:
        return dict(empty)
    mags = _stft_mags(x)
    frames = mags.shape[0]
    if frames < 8:
        return dict(empty)
    fps = sr / HOP
    lag_min = int(fps * 60 / BPM_MAX)      # lag for 190 BPM
    lag_max = int(fps * 60 / BPM_MIN)      # lag for 60 BPM
    if lag_max >= (frames - 1) - 1:
        lag_max = (frames - 1) - 2
    if lag_min < 1 or lag_max <= lag_min:
        return dict(empty)

    bands: dict = {}
    acns: dict = {}
    cands: dict = {}
    for name, lo_hz, hi_hz in BPM_BANDS:
        flux = _onset_flux(mags, sr, lo_hz, hi_hz)
        if flux.std() < 1e-9:
            continue
        # flux has one sample fewer than the frame count (it is a difference)
        ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:][: lag_max + 1]
        if ac[0] <= 0:
            continue
        acn = ac / ac[0]
        acns[name] = acn
        seg = acn[lag_min: lag_max + 1]
        med = float(np.median(seg))
        peaks = _ac_peaks(acn, lag_min, lag_max)
        bands[name] = {
            "argmax_bpm": round(float(60.0 * fps / (int(np.argmax(seg)) + lag_min)), 1),
            "argmax_ac": round(float(seg.max()), 4),
            "median_ac": round(med, 4),
            "top_peaks": [{"bpm": round(float(60.0 * fps / lag), 1),
                           "lag": lag, "ac": round(float(v), 4),
                           "edge": lag == lag_max}
                          for v, lag in peaks[:4]],
        }
        # every ac peak, plus its folds (half/double tempo)
        for acv, lag in peaks:
            for factor in (1.0, 2.0, 0.5):
                l = int(round(lag * factor))
                if not lag_min <= l <= lag_max:
                    continue
                b = 60.0 * fps / l
                if not (BPM_MIN - 0.5) <= b <= (BPM_MAX + 0.5):
                    continue
                a = float(acn[l])
                if a < BPM_CAND_AC_FLOOR:
                    continue
                c = cands.setdefault(l, {
                    "lag": l, "bpm": b, "ac": a, "confidence": a,
                    "peak": False, "best_band": name, "prominence": 0.0,
                    "bands": {},
                })
                c["peak"] = c["peak"] or l == lag
                c["bands"][name] = round(a, 4)
                if a - med > c["prominence"]:
                    c["prominence"] = round(a - med, 4)
                    c["ac"] = a
                    c["confidence"] = a
                    c["best_band"] = name
    if not cands:
        out = dict(empty)
        out["bpm_bands"] = bands
        out["bpm_note"] = ("no measurable pulse: no autocorrelation peak in any "
                           f"band reaches ac {BPM_CAND_AC_FLOOR}")
        return out

    clist = sorted(cands.values(), key=lambda c: (-c["prominence"], -c["ac"]))
    for c in clist:
        c["bpm"] = round(float(c["bpm"]), 1)
        c["ac"] = round(float(c["ac"]), 4)
        c["confidence"] = c["ac"]
        c["lag_bpm"] = round(float(60.0 * fps / c["lag"]), 1)
        c["edge"] = c["lag"] == lag_max
        c["bands"] = sorted(c["bands"].keys())

    notes = []

    # --- the anchor block, and the candidate it supports -------------------
    anchor_block, anchor_cand = None, None
    if anchor_bpm:
        a = float(anchor_bpm)
        la = max(lag_min, min(lag_max, int(round(fps * 60 / a))))
        by_band = {n: round(float(acns[n][la]), 4) for n in acns
                   if la < len(acns[n])}
        best_band = max(by_band, key=lambda k: by_band[k]) if by_band else None
        near = None
        lo_lag = max(lag_min, int(round(la * 0.9)))
        hi_lag = min(lag_max, int(round(la * 1.1)))
        for n, acn in acns.items():
            if hi_lag >= len(acn):
                continue
            j = int(np.argmax(acn[lo_lag: hi_lag + 1])) + lo_lag
            v = float(acn[j])
            if near is None or v > near["ac"]:
                near = {"bpm": round(float(60.0 * fps / j), 1), "lag": j,
                        "ac": round(v, 4), "band": n}
        within = [c for c in clist if abs(c["bpm"] - a) <= BPM_ANCHOR_TOL_BPM]
        if within:
            anchor_cand = max(within, key=lambda c: c["ac"])
            if anchor_cand["ac"] < BPM_PULSE_AC_FLOOR:
                anchor_cand = None
        supported = (near is not None
                     and near["ac"] >= BPM_PULSE_AC_FLOOR
                     and abs(near["bpm"] - a) <= BPM_ANCHOR_TOL_BPM)
        anchor_block = {
            "anchor_bpm": a,
            "lag": la,
            "lag_bpm": round(float(60.0 * fps / la), 1),
            "ac": by_band.get(best_band),
            "ac_by_band": by_band,
            "best_band": best_band,
            "near": near,
            "candidate_within_3bpm": (
                {"bpm": anchor_cand["bpm"], "ac": anchor_cand["ac"],
                 "band": anchor_cand["best_band"]} if anchor_cand else None),
            "verdict": "supported" if supported else "not_supported",
        }

    clist = clist[:BPM_MAX_CANDIDATES]
    if anchor_cand is not None and anchor_cand not in clist:
        clist = clist[:BPM_MAX_CANDIDATES - 1] + [anchor_cand]

    # --- pick the headline -------------------------------------------------
    # Rule 1: an argmax at the lag_max boundary is a cut, not a peak. Report
    # the strongest located candidate when it is close in ac.
    head = clist[0]
    if head["edge"]:
        ne = next((c for c in clist if not c["edge"]), None)
        if ne is not None and ne["ac"] >= BPM_EDGE_SUPPRESS_RATIO * head["ac"]:
            notes.append(
                f"the argmax sits at the {BPM_MIN:g} BPM edge of the lag search "
                f"range ({head['bpm']} BPM, ac {head['ac']}, lag {head['lag']} = "
                "the longest lag searched): the autocorrelation is CUT there, it "
                f"does not peak there. Reported {ne['bpm']} BPM "
                f"(ac {ne['ac']}, {ne['best_band']} band) instead.")
            head = ne
        else:
            notes.append(
                f"the headline {head['bpm']} BPM sits at the {BPM_MIN:g} BPM edge "
                f"of the lag search range (ac {head['ac']}, lag {head['lag']}); "
                "no other candidate comes close, so it is reported as measured.")
    # Rule 2: with an anchor, a measured candidate at the anchor wins, and the
    # note names the candidate the ranking would have reported instead.
    if (anchor_cand is not None and anchor_block is not None
            and anchor_cand is not head):
        notes.append(
            f"the requested anchor {anchor_block['anchor_bpm']:g} BPM is "
            f"supported: candidate {anchor_cand['bpm']} BPM "
            f"(ac {anchor_cand['ac']}, {anchor_cand['best_band']} band, "
            f"{round(anchor_cand['bpm'] - anchor_block['anchor_bpm'], 1):+} BPM "
            f"off the anchor) is reported as the headline. The prominence "
            f"ranking alone would report {head['bpm']} BPM "
            f"(ac {head['ac']}, {head['prominence']} prominence) — an octave "
            "relation at this tempo is common, so both stay in "
            "bpm_candidates.")
        head = anchor_cand
    if head["ac"] < BPM_PULSE_AC_FLOOR:
        notes.append(
            f"no candidate reaches ac {BPM_PULSE_AC_FLOOR}: no measurable pulse. "
            "The tempo fields are advisory for this artifact.")
        out = dict(empty)
        out["bpm_candidates"] = clist
        out["bpm_bands"] = bands
        if anchor_block:
            out["ac_at_anchor"] = anchor_block
        out["bpm_note"] = " ".join(notes)
        return out

    out = {
        "bpm": head["bpm"],
        "bpm_confidence": head["ac"],
        "bpm_candidates": clist,
        "bpm_bands": bands,
        "bpm_pulse": "measurable",
    }
    if anchor_block:
        out["ac_at_anchor"] = anchor_block
        if anchor_block["verdict"] == "not_supported":
            near = anchor_block["near"]
            notes.append(
                f"the anchor {anchor_block['anchor_bpm']:g} BPM is NOT "
                "supported: the best autocorrelation within 10 % of its period "
                f"is {near['ac'] if near else None} at "
                f"{near['bpm'] if near else None} BPM. Use the ac_at_anchor "
                "block, not the headline, for this track.")
    out["bpm_note"] = " ".join(notes) if notes else None
    return out


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


def measure_track(path: Path, anchor_bpm: float | None = None) -> dict:
    """All measured evidence for one audio file. Raises on undecodable.

    anchor_bpm: the genre's tempo anchor. Adds the `ac_at_anchor` block, the
    measured autocorrelation AT the anchor, so a reviewer can see the anchor's
    own score instead of only the argmax.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    info = _ffprobe(path)
    if not info["duration_s"] or info["duration_s"] < 1.0:
        raise ValueError(f"{path}: not decodable audio "
                         f"(duration={info['duration_s']})")
    vol = _volumedetect(path)
    x = _load_mono(path, SR_DEFAULT)
    sr = SR_DEFAULT
    ev = {
        "file": str(path),
        "measured_at_version": MEASURE_VERSION,
        **info,
        **vol,
        "silences_ge_1s": _silence_map(path),
        **_bpm(x, sr, anchor_bpm),
        "pct_energy_above_8khz": _spectral_centroid_db(x, sr),
        **_dynamics_db(x, sr),
    }
    return ev


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="measure.py — measured evidence extraction for the "
                    "music review panel (ffmpeg + numpy)")
    ap.add_argument("audio")
    ap.add_argument("--anchor-bpm", type=float, default=None,
                    help="the genre's tempo anchor; adds ac_at_anchor")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    ev = measure_track(Path(args.audio), anchor_bpm=args.anchor_bpm)
    print(json.dumps(ev, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
