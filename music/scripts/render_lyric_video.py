#!/usr/bin/env python3
"""render_lyric_video.py — render the `lyric-video` video shape.

The `lyric-video` shape is the activist genre's platform-native visual
(`music/genres.yaml` -> `activist: video_shape: lyric-video`). This script is
the renderer that shape was missing: it DRIVES the shape from a track's
`lyrics.suno.txt` plus section timing, and it is the only producer of
`music/visuals/lyric_video.mp4`.

It renders exactly what `music/visuals/documentary-grain.md` specifies:

  palette      #232019 shadow / #6b6257 dust / #9c8f7a skin-and-paper,
               ONE accent colour per video, used sparingly
  medium       16 mm look: handheld sway, gate weave, occasional focus hunt,
               a 4:3 letterboxed archival insert that VARYS its medium
               (newsprint / chalk / protest wood / paper) from section to
               section -- steadicam polish reads as an ad
  texture      grain 6-8%, slight halation on highlights
  lyrics       typewriter face, appearing ON the phrase, never after it
  chorus       the line swaps to a crowd of hands writing the same line:
               many staggered hands, one text
  never        glossy kinetic-type effects; the light. No word-by-word
               karaoke bounce, no drop shadow, no glow.

Usage
-----
  render_lyric_video.py --lyrics music/lyrics/activist/what-runs-beneath/lyrics.suno.txt \
      --out music/visuals/lyric_video.mp4

  # section timing is explicit, per section in sheet order:
  render_lyric_video.py --lyrics <sheet> --out <mp4> --sections-file bars.json

  # fast check of the look before the full 4-minute render:
  render_lyric_video.py --lyrics <sheet> --out /tmp/preview.mp4 --preview 12

  # no audio bed (a template with no reference click):
  render_lyric_video.py --lyrics <sheet> --out <mp4> --bed none

Exit codes: 0 = rendered, 1 = render/encode failed, 2 = usage/bad input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# PIL moved the resampling enums under Image.Resampling in 10.x; keep working
# on either (this host runs 12.3).
_RESAMPLE = getattr(getattr(Image, "Resampling", Image), "BICUBIC")

# --- documentary-grain.md palette -----------------------------------------
SHADOW = (0x23, 0x20, 0x19)
DUST = (0x6b, 0x62, 0x57)
SKIN_PAPER = (0x9c, 0x8f, 0x7a)
ACCENT_DEFAULT = "c2542e"          # the movement's colour, used sparingly
INK = (0xef, 0xe8, 0xda)           # lyric type: aged paper, not white

TYPEWRITER_FONT = Path("/usr/share/fonts/gsfonts/NimbusMonoPS-Regular.ttf")
TYPEWRITER_FALLBACK = Path("/usr/share/fonts/liberation/LiberationMono-Regular.ttf")

# Bars per section tag. DATA, not a structure baked into code: a different
# sheet with different tags re-weights, and --sections-file overrides it.
TAG_BARS = {
    "intro": 8, "verse": 16, "pre-chorus": 8, "chorus": 8,
    "bridge": 12, "outro": 12, "refrain": 8,
}
BAR_BEATS = 4                       # 4/4

# Archival insert media, cycled per section so no two sections share one
# texture (documentary-grain: "vary the medium").
MEDIA = ("newsprint", "chalk", "wood", "paper")

# The archival insert must read as a DIFFERENT piece of media from the wall it
# is cut into; without a bias every medium sits in the same palette band and
# the panel looks like an empty framing guide.
MEDIA_BIAS = {"newsprint": 0.50, "paper": 0.42, "wood": -0.18, "chalk": -0.22}


def build_insert(name: str, h: int, w: int,
                 rng: np.random.Generator) -> np.ndarray:
    """An archival INSERT: a different medium, stretched and biased.

    A panel built from the same palette band as the wall it is cut into reads
    as an empty framing guide (measured: first pass at a 0.34 bias came back
    "essentially empty"). The bias lifts it off the wall; the stretch gives it
    its own contrast so it reads as a separate piece of paper/chalk/wood.
    """
    lum = build_medium(name, h, w, rng)
    lum = np.clip((lum - 0.5) * 1.30 + 0.5, 0.0, 1.0)
    return np.clip(lum + MEDIA_BIAS[name], 0.0, 1.0)


# --------------------------------------------------------------------------
# 1. the lyric sheet
# --------------------------------------------------------------------------
class SheetError(Exception):
    """The sheet cannot be rendered. Printed, exit 2."""


def parse_lyric_sheet(path: Path) -> tuple[str, list[dict]]:
    """Parse a `lyrics.suno.txt` sheet into (title, ordered sections).

    Sections are OCCURRENCE-SENSITIVE: a sheet that repeats `[Chorus]` yields
    two chorus sections at their real positions, because the second chorus
    starts later in time than the first. Collapsing them by tag would lose
    that. Returns sections as dicts: index, tag, occurrence, lines.
    """
    if not path.is_file():
        raise SheetError(f"no lyric sheet: {path}")
    text = path.read_text(encoding="utf-8")

    title = ""
    sections: list[dict] = []
    current: dict | None = None
    seen: dict[str, int] = {}

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line.lower().startswith("# title:") and not title:
                title = line.split(":", 1)[1].strip()
            continue
        if line.startswith("[") and line.endswith("]"):
            tag = line[1:-1].strip()
            seen[tag] = seen.get(tag, 0) + 1
            current = {"index": len(sections), "tag": tag,
                       "occurrence": seen[tag], "lines": []}
            sections.append(current)
            continue
        if current is None:
            raise SheetError(
                f"{path}: lyric line before any [section] tag: {line!r}")
        current["lines"].append(line)

    if not sections:
        raise SheetError(f"{path}: no [section] tags found")
    for sec in sections:
        if not sec["lines"]:
            raise SheetError(f"{path}: section [{sec['tag']}] has no lines")
    return title, sections


# --------------------------------------------------------------------------
# 2. section timing
# --------------------------------------------------------------------------
def _bars_for_tag(tag: str) -> int:
    key = tag.strip().lower()
    if key in TAG_BARS:
        return TAG_BARS[key]
    for known, bars in TAG_BARS.items():       # "Verse 1" -> verse
        if key.startswith(known):
            return bars
    return 12                                   # unknown tag: a fair default


def _largest_remainder(weights: list[float], total: int) -> list[int]:
    """Scale weights to exactly `total` integer bars (deterministic)."""
    scaled = [w * total / sum(weights) for w in weights]
    base = [int(math.floor(v)) for v in scaled]
    short = total - sum(base)
    order = sorted(range(len(scaled)), key=lambda i: (-(scaled[i] - base[i]), i))
    for i in order[:short]:
        base[i] += 1
    return base


def resolve_bars(sections: list[dict], bpm: float, duration: float,
                 sections_file: Path | None) -> list[int]:
    """Bars for each section.

    Precedence: an explicit --sections-file (the sheet carries no timing), else
    the tag weights scaled so the bars fill `duration` exactly at `bpm`.
    """
    bar_seconds = BAR_BEATS * 60.0 / bpm
    total_bars = max(len(sections), round(duration / bar_seconds))

    if sections_file is not None:
        data = json.loads(sections_file.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "bars" in data:
            bars = [int(b) for b in data["bars"]]
            if len(bars) != len(sections):
                raise SheetError(
                    f"{sections_file}: {len(bars)} bar counts for "
                    f"{len(sections)} sections in the sheet")
            return bars
        if isinstance(data, dict) and "bars_by_tag" in data:
            weights = [float(data["bars_by_tag"].get(s["tag"], _bars_for_tag(s["tag"])))
                       for s in sections]
            return _largest_remainder(weights, total_bars)
        raise SheetError(
            f"{sections_file}: expected {{'bars': [...]}} or "
            "{'bars_by_tag': {...}}")

    weights = [float(_bars_for_tag(s["tag"])) for s in sections]
    return _largest_remainder(weights, total_bars)


def build_timeline(sections: list[dict], bars: list[int], bpm: float) -> list[dict]:
    """Attach start/end (seconds) to every section and every line.

    Line slots are equal inside a section; a line's reveal is 45% of its slot,
    so the phrase is written while it is sung and holds after it lands.
    """
    bar_seconds = BAR_BEATS * 60.0 / bpm
    out = []
    clock = 0.0
    for sec, n_bars in zip(sections, bars):
        span = n_bars * bar_seconds
        lines = []
        slot = span / len(sec["lines"])
        for i, text in enumerate(sec["lines"]):
            start = clock + i * slot
            reveal = min(slot * 0.45, 0.055 * max(len(text), 1))
            lines.append({"text": text, "start": start, "end": start + slot,
                          "reveal": max(reveal, 0.12)})
        out.append({**sec, "start": clock, "end": clock + span,
                    "bars": n_bars, "line_times": lines})
        clock += span
    return out


# --------------------------------------------------------------------------
# 3. background media
# --------------------------------------------------------------------------
def value_noise(h: int, w: int, cells: int, rng: np.random.Generator) -> np.ndarray:
    """Multi-cell value noise upsampled bilinearly (one octave)."""
    grid = rng.random((cells + 1, cells + 1)).astype(np.float32)
    ys = np.linspace(0, cells, h, dtype=np.float32)
    xs = np.linspace(0, cells, w, dtype=np.float32)
    y0 = np.clip(np.floor(ys).astype(int), 0, cells - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, cells - 1)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    a = grid[np.ix_(y0, x0)]
    b = grid[np.ix_(y0, x0 + 1)]
    c = grid[np.ix_(y0 + 1, x0)]
    d = grid[np.ix_(y0 + 1, x0 + 1)]
    top = a + (b - a) * fx
    bot = c + (d - c) * fx
    return top + (bot - top) * fy


def fbm(h: int, w: int, cells: int, octaves: int,
        rng: np.random.Generator) -> np.ndarray:
    acc = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        acc += amp * value_noise(h, w, cells * (2 ** o), rng)
        total += amp
        amp *= 0.5
    acc /= total
    acc -= acc.min()
    peak = acc.max()
    return acc / peak if peak > 0 else acc


def build_medium(name: str, h: int, w: int,
                 rng: np.random.Generator) -> np.ndarray:
    """One archival medium as a 0..1 luminance field."""
    if name == "newsprint":
        base = fbm(h, w, 90, 4, rng)
        base = 0.35 + 0.5 * base
        # halftone dots, 3x3 blocks: real newsprint is dotty but not
        # per-pixel noise — per-pixel speckle is incompressible once the
        # frame starts weaving (card t_ec378832 measured 6.4 Mbit/s).
        dh, dw = h // 3 + 1, w // 3 + 1
        dots = (rng.random((dh, dw)) > 0.72).astype(np.float32)
        dots = np.repeat(np.repeat(dots, 3, axis=0), 3, axis=1)[:h, :w]
        return np.clip(base + 0.18 * dots, 0, 1)
    if name == "chalk":
        # Chalk: sparse BRIGHT scrawl on a dark pavement, not a mid-grey wash.
        base = 0.10 + 0.22 * fbm(h, w, 6, 4, rng)
        marks = (fbm(h, w, 16, 4, rng) > 0.60).astype(np.float32)
        marks = np.asarray(Image.fromarray((marks * 255).astype(np.uint8), "L")
                           .filter(ImageFilter.GaussianBlur(1)), np.float32) / 255.0
        return np.clip(base + 0.85 * marks, 0, 1)
    if name == "wood":
        grain = np.sin(np.linspace(0, 34, w, dtype=np.float32))[None, :]
        grain = np.repeat(grain, h, axis=0) * 0.5 + 0.5
        knots = fbm(h, w, 4, 3, rng)
        return np.clip(0.3 + 0.45 * grain * (0.5 + 0.5 * knots) + 0.2 * knots, 0, 1)
    base = fbm(h, w, 7, 5, rng)                 # paper
    fibre = fbm(h, w, 60, 2, rng)
    return np.clip(0.55 + 0.32 * base + 0.16 * fibre, 0, 1)


def to_palette(lum: np.ndarray, accent: tuple[int, int, int],
               accent_amount: np.ndarray | None = None) -> np.ndarray:
    """Map 0..1 luminance into the documentary-grain palette (uint8 RGB)."""
    stops = np.array([0.0, 0.5, 1.0], np.float32)
    chan = []
    for lo, mid, hi in zip(SHADOW, DUST, SKIN_PAPER):
        chan.append(np.interp(lum, stops, [lo, mid, hi]).astype(np.float32))
    rgb = np.stack(chan, axis=-1)
    if accent_amount is not None:
        a = np.clip(accent_amount, 0, 1)[..., None].astype(np.float32)
        rgb = rgb * (1 - a) + np.array(accent, np.float32) * a
    return np.clip(rgb, 0, 255).astype(np.uint8)


def print_dirt_field(height: int, width: int, rng: np.random.Generator,
                     amount: float) -> np.ndarray:
    """Static print dirt: specks and a couple of hair scratches.

    documentary-grain.md asks for "deliberate imperfection = credibility", and
    a frame with only grain and no print artifacts reads as a digital filter.
    The field is FIXED for the whole render, exactly as dirt is fixed on a
    print, so it costs the encoder almost nothing.
    """
    dirt = np.zeros((height, width), np.float32)
    specks = max(1, int(height * width / 1200))
    ys = rng.integers(0, height, specks)
    xs = rng.integers(0, width, specks)
    dirt[ys, xs] = 1.0
    for _ in range(3):                       # hair scratches
        x = int(rng.integers(4, max(5, width - 4)))
        y0 = int(rng.integers(0, height // 2))
        length = int(rng.integers(height // 4, height))
        dirt[y0:y0 + length, x] = 1.0
    smoothed = Image.fromarray((dirt * 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(0.6))
    return (np.asarray(smoothed, np.float32) / 255.0) * amount


def soft_band_image(width: int, height: int, top: int, bottom: int,
                    peak_alpha: int) -> Image.Image:
    """A full-frame RGBA overlay that darkens one band with soft edges.

    Type over a raw 16 mm texture is not readable at 720p. A raised-cosine
    alpha ramp darkens the lyric band without a hard lower-third bar, which
    documentary-grain.md rules out as "glossy kinetic type".
    """
    alpha = np.zeros(height, np.float32)
    if bottom > top:
        t = (np.arange(height, dtype=np.float32) - top) / float(bottom - top)
        inside = (t >= 0.0) & (t <= 1.0)
        alpha[inside] = peak_alpha * 0.5 * (1.0 - np.cos(2 * np.pi * t[inside]))
    rgba = np.zeros((height, width, 4), np.uint8)
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = 0x10, 0x0e, 0x0b
    rgba[..., 3] = np.clip(alpha, 0, 255).astype(np.uint8)[:, None]
    return Image.fromarray(rgba, "RGBA")


# --------------------------------------------------------------------------
# 4. type layer
# --------------------------------------------------------------------------
class Type:
    """Caches typewriter text rasters (lead lines and chorus hands)."""

    def __init__(self, size: int) -> None:
        font = TYPEWRITER_FONT if TYPEWRITER_FONT.is_file() else TYPEWRITER_FALLBACK
        self.font = ImageFont.truetype(str(font), size)
        self._cache: dict[tuple, Image.Image] = {}

    def line(self, text: str, chars: int) -> Image.Image:
        key = ("lead", text, chars)
        img = self._cache.get(key)
        if img is None:
            img = Image.new("RGBA", (1400, 120), (0, 0, 0, 0))
            ImageDraw.Draw(img).text((6, 6), text[:chars], font=self.font,
                                     fill=(*INK, 255))
            img = img.crop(img.getbbox() or (0, 0, 1, 1))
            self._cache[key] = img
        return img

    def hand(self, text: str, angle: float) -> Image.Image:
        key = ("hand", text, round(angle, 1))
        img = self._cache.get(key)
        if img is None:
            full = self.line(text, len(text)).copy()
            img = full.rotate(angle, resample=_RESAMPLE, expand=True)
            self._cache[key] = img
        return img

    def label(self, text: str) -> Image.Image:
        key = ("label", text)
        img = self._cache.get(key)
        if img is None:
            f = ImageFont.truetype(str(self.font.path), 26)
            img = Image.new("RGBA", (600, 44), (0, 0, 0, 0))
            ImageDraw.Draw(img).text((2, 2), text.upper(), font=f,
                                     fill=(*INK, 255))
            img = img.crop(img.getbbox() or (0, 0, 1, 1))
            self._cache[key] = img
        return img


def hex_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    if len(v) != 6:
        raise SheetError(f"--accent must be RRGGBB, got {value!r}")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))       # type: ignore[return-value]


# --------------------------------------------------------------------------
# 5. the audio bed
# --------------------------------------------------------------------------
def write_click_bed(path: Path, bpm: float, duration: float,
                    sample_rate: int = 48000) -> None:
    """A 96 BPM reference click bed (downbeat accented). Not music: a slate."""
    n = int(round(duration * sample_rate))
    t = np.arange(n, dtype=np.float32) / sample_rate
    beat = 60.0 / bpm
    bar = beat * BAR_BEATS
    phase_beat = np.mod(t, beat)
    phase_bar = np.mod(t, bar)
    click = (0.22 * np.exp(-45.0 * phase_beat)
             * np.sin(2 * np.pi * 1400.0 * t))
    down = (0.45 * np.exp(-30.0 * phase_bar)
            * np.sin(2 * np.pi * 900.0 * t))
    sig = np.clip(click + down, -1.0, 1.0)
    pcm = (sig * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())


# --------------------------------------------------------------------------
# 6. the render
# --------------------------------------------------------------------------
def focus_hunt_sigma(t: float, moments: list[float]) -> float:
    """Occasional focus hunt: a short defocus that settles (16 mm credibility)."""
    worst = 0.0
    for m in moments:
        if -0.35 < t - m < 0.55:
            worst = max(worst, 2.4 * math.exp(-abs(t - m) * 6.0))
    return worst


def render(args: argparse.Namespace) -> int:
    lyrics = Path(args.lyrics)
    out = Path(args.out)
    title, sections = parse_lyric_sheet(lyrics)
    bpm = float(args.bpm)
    duration = float(args.duration)
    width, height = (int(v) for v in args.size.lower().split("x"))
    fps = int(args.fps)
    accent = hex_rgb(args.accent)
    rng = np.random.default_rng(args.seed)
    full_frames = int(round(duration * fps))
    start_frame = max(0, int(round(float(args.preview_start) * fps)))
    n_frames = full_frames - start_frame
    if args.preview:
        n_frames = min(n_frames, int(round(float(args.preview) * fps)))
    if n_frames <= 0:
        raise SheetError("--preview-start is past the end of the track")
    window = n_frames / fps

    bars = resolve_bars(sections, bpm, duration,
                        Path(args.sections_file) if args.sections_file else None)
    timeline = build_timeline(sections, bars, bpm)

    typer = Type(int(height * 0.055))

    # --- sources ---------------------------------------------------------
    pad = 96
    tex_h, tex_w = height + pad * 2, width + pad * 2
    backgrounds = {m: build_medium(m, tex_h, tex_w, rng) for m in MEDIA}

    # Archival insert: a TRUE 4:3 panel. documentary-grain.md asks for "4:3 or
    # 16:9 letterboxed archival inserts"; sizing the box from width alone gave
    # a 2.37:1 rectangle that read as a framing guide, not an archival frame.
    ins_h = int(height * 0.56)
    ins_w = int(round(ins_h * 4 / 3))
    ins_x, ins_y = (width - ins_w) // 2, int(height * 0.05)
    inserts = {m: build_insert(m, ins_h, ins_w, rng) for m in MEDIA}

    # The lyric band: a soft dark falloff behind the type, so a typewriter
    # face stays readable at 720p without a hard, glossy lower-third bar.
    ly_line_y = int(height * 0.70)
    soft_band = soft_band_image(width, height,
                               ly_line_y - int(height * 0.085),
                               ly_line_y + int(height * 0.085), 150)

    moments = sorted(rng.uniform(8.0, max(9.0, duration - 8.0), 5).tolist())
    # "Grain 6-8%" (documentary-grain.md) has no unit anywhere in this repo —
    # other styles give 2% ("the lightest of all visuals") up to 8-10%, and no
    # file defines the scale. Interpreted as PROPORTIONAL modulation: the field
    # is 6.5% OF EACH PIXEL's value, so the wall texture survives the grain.
    # Measured: an additive field of 6.5% of FULL SCALE flattened the frame to
    # "no visible scene detail anywhere" and cost 5-7x the bitrate.
    grain_rel = float(args.grain_pct) / 100.0
    dirt = print_dirt_field(height, width, rng, float(args.dirt))
    flicker = float(args.flicker)

    # Grain: a chunky field (documentary-grain: 6-8%) refreshed every
    # --grain-hold frames instead of every frame. Two reasons. Measured: a
    # fresh noise field per frame is the ENTIRE encode cost (3866 kbit/s vs
    # 587 kbit/s with grain off at crf 30), because an uncorrelated residual
    # defeats every prediction. And real grain is fixed to the film frame, so
    # holding it for ~3 frames reads as film rather than video noise.
    gblock = max(1, int(args.grain_block))
    ghold = max(1, int(args.grain_hold))
    grain_field: np.ndarray | None = None
    grain_shapes = (max(2, height // gblock + 1), max(2, width // gblock + 1), 1)
    # --- encoder ---------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
        ]
        if args.bed == "click":
            bed = Path(tmp) / "bed.wav"
            write_click_bed(bed, bpm, duration)
            if start_frame:
                cmd += ["-ss", f"{start_frame / fps:.3f}"]
            cmd += ["-i", str(bed)]
        cmd += [
            "-t", f"{window:.3f}",
            "-c:v", "libx264", "-preset", args.preset,
            "-crf", str(args.crf), "-pix_fmt", "yuv420p",
            "-x264-params", "keyint=50:min-keyint=25",
        ]
        if args.bed == "click":
            cmd += ["-c:a", "aac", "-b:a", "128k", "-shortest"]
        cmd += [
            "-movflags", "+faststart",
            "-metadata", f"title={args.meta_title or ('lyric-video template' + (': ' + title if title else ''))}",
            "-metadata", f"comment={args.comment}",
            str(out),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        if proc.stdin is None:                    # cannot happen with stdin=PIPE
            raise RuntimeError("ffmpeg stdin unavailable")

        # --- frame loop --------------------------------------------------
        for i in range(n_frames):
            f = start_frame + i
            t = f / fps
            sec = next((s for s in timeline if s["start"] <= t < s["end"]),
                       timeline[-1])
            sec_i = sec["index"]
            local = t - sec["start"]

            # slow zoom + handheld sway + gate weave (integer pixels)
            zoom = 1.0 + 0.045 * (local / max(sec["end"] - sec["start"], 1e-6))
            win_h = int(height * zoom)
            win_w = int(width * zoom)
            sway_x = int(round(10 * math.sin(t * 0.37) + 4 * math.sin(t * 1.7)))
            sway_y = int(round(6 * math.sin(t * 0.53 + 1.1) + 3 * math.sin(t * 2.3)))
            weave_x = int(rng.integers(-2, 3))
            weave_y = int(rng.integers(-2, 3))
            ox = pad + (tex_w - win_w) // 2 + weave_x
            oy = pad + (tex_h - win_h) // 2 + weave_y
            ox += sway_x
            oy += sway_y
            ox = max(0, min(tex_w - win_w, ox))
            oy = max(0, min(tex_h - win_h, oy))

            med = MEDIA[sec_i % len(MEDIA)]
            bg = backgrounds[med][oy:oy + win_h, ox:ox + win_w]
            if (win_h, win_w) != (height, width):
                bg = bg[:height, :width]
            world = Image.fromarray(to_palette(bg, accent), "RGB")

            is_chorus = "chorus" in sec["tag"].lower()

            # --- world layer: the camera's layer ---------------------------
            # Archival 4:3 insert, letterboxed, one hairline in the accent
            # colour. The insert is cut from a DIFFERENT medium than the wall
            # it sits on, so it reads as an archival frame, not an empty guide
            # (documentary-grain: "vary the medium").
            if not is_chorus:
                med_ins = MEDIA[(sec_i + 1) % len(MEDIA)]
                panel = Image.fromarray(to_palette(inserts[med_ins], accent),
                                        "RGB")
                world.paste(panel, (ins_x, ins_y))
                d = ImageDraw.Draw(world)
                d.rectangle(
                    [ins_x - 2, ins_y - 2, ins_x + ins_w + 1, ins_y + ins_h + 1],
                    outline=accent, width=2)
                d.rectangle([ins_x + 1, ins_y + 1, ins_x + ins_w - 2,
                             ins_y + ins_h - 2], outline=(0x6a, 0x60, 0x52),
                            width=1)

            # the camera hunts focus on the WORLD, never on the type: blur
            # before the type is composited, or the lyric becomes unreadable.
            sigma = focus_hunt_sigma(t, moments)
            if sigma > 0.05:
                world = world.filter(ImageFilter.GaussianBlur(sigma))

            arr = np.asarray(world, dtype=np.float32)

            # halation: a light bleed on the highlights (world only)
            if args.halation > 0:
                lum = arr.mean(axis=2)
                bright = np.clip((lum - 150.0) / 105.0, 0, 1)
                if bright.max() > 0.02:
                    blur = np.asarray(
                        Image.fromarray((bright * 255).astype(np.uint8), "L")
                        .filter(ImageFilter.GaussianBlur(6)), dtype=np.float32)
                    arr = arr + ((blur[..., None] / 255.0) * args.halation
                                 * np.array([255, 240, 220], np.float32))

            # exposure flicker: a slow lamp/print instability, smooth and cheap
            if flicker > 0:
                arr = arr * (1.0 + flicker * (0.65 * math.sin(2 * math.pi * 0.31 * t)
                                              + 0.35 * math.sin(2 * math.pi * 1.7 * t)))

            # grain 6-8% (proportional): the film frame's own grain,
            # refreshed at ghold Hz
            if grain_field is None or i % ghold == 0:
                fld = rng.normal(0.0, 1.0, grain_shapes).astype(np.float32)
                fld = np.repeat(np.repeat(fld, gblock, axis=0), gblock, axis=1)
                grain_field = fld[:height, :width] * grain_rel
            arr = np.clip(arr * (1.0 + grain_field) * (1.0 - dirt[..., None]),
                          0, 255).astype(np.uint8)
            frame = Image.fromarray(arr, "RGB")

            # --- type layer: the graphic, composited over the world --------
            # A soft dark falloff behind the lyric keeps a typewriter face
            # readable at 720p without a hard, glossy lower-third bar.
            for lt in sec["line_times"]:
                if t < lt["start"] or t >= lt["end"]:
                    continue
                # soft darkening across the lyric band
                frame.paste(soft_band, (0, 0), soft_band)

                prog = min(1.0, (t - lt["start"]) / lt["reveal"])
                chars = max(1, int(round(len(lt["text"]) * prog)))
                lead = typer.line(lt["text"], chars)
                lx = (width - lead.width) // 2 + int(
                    round(3 * math.sin(lt["start"] * 7)))
                frame.paste(lead, (lx, ly_line_y), lead)

                if is_chorus:
                    # the chorus swaps to a crowd of hands writing the same
                    # line: many staggered hands, one text
                    for gidx in range(args.hands):
                        gstart = lt["start"] + 0.10 * gidx
                        if t < gstart:
                            continue
                        gprog = min(1.0, (t - gstart) / max(lt["reveal"], 0.12))
                        if gprog <= 0.0:
                            continue
                        hand = typer.hand(lt["text"],
                                          -8.0 + 16.0 * ((gidx * 37 % 11) / 10.0))
                        cut = hand.crop((0, 0, max(1, int(hand.width * gprog)),
                                         hand.height))
                        gx = int(40 + ((gidx * 211) % max(1, width - 380)))
                        gy = int(70 + ((gidx * 97) % max(1, int(height * 0.36))))
                        alpha = cut.getchannel("A").point(
                            lambda p, o=0.15 + 0.025 * gidx:
                            int(p * min(o, 0.34)))
                        cut.putalpha(alpha)
                        frame.paste(cut, (gx, gy), cut)

            # section label: accent, small, sparing
            if local < 2.4:
                lab = typer.label(f"{sec['tag']}")
                frame.paste(lab, (64, height - 74), lab)

            try:
                proc.stdin.write(frame.tobytes())
            except BrokenPipeError:
                print("ffmpeg closed the pipe early — see its stderr above",
                      file=sys.stderr)
                return 1
            if i % (fps * 20) == 0 and i:
                print(f"  {i}/{n_frames} frames ({t:.0f}s)", file=sys.stderr)

        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            print(f"ffmpeg failed with rc={rc}", file=sys.stderr)
            return 1

    return 0


# --------------------------------------------------------------------------
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Render the lyric-video shape from a lyrics.suno.txt sheet")
    p.add_argument("--lyrics", required=True, help="the track's lyrics.suno.txt")
    p.add_argument("--out", required=True, help="output mp4")
    p.add_argument("--bpm", default=96.0, type=float,
                   help="bpm anchor from the track's lyric blueprint")
    p.add_argument("--duration", default=240.0, type=float,
                   help="target duration in seconds (single-4min = 240)")
    p.add_argument("--sections-file", default=None,
                   help="JSON {'bars': [...]} or {'bars_by_tag': {...}}")
    p.add_argument("--size", default="1280x720")
    p.add_argument("--fps", default=25, type=int)
    p.add_argument("--accent", default=ACCENT_DEFAULT,
                   help="the movement's colour, RRGGBB (used sparingly)")
    p.add_argument("--grain-pct", default=6.5, type=float,
                   help="grain strength as a percent of full scale (6-8)")
    p.add_argument("--grain-block", default=4, type=int,
                   help="grain cell size in pixels. 16 mm grain is chunky, and "
                        "chunky grain also survives the encoder (a per-pixel "
                        "noise field pushes a 4-minute render past 1 GB)")
    p.add_argument("--grain-hold", default=3, type=int,
                   help="refresh the grain field every N frames (measured: a "
                        "fresh field per frame is the whole encode cost)")
    p.add_argument("--halation", default=26.0, type=float)
    p.add_argument("--dirt", default=0.16, type=float,
                   help="static print dirt/speck strength (fixed field: "
                        "free to encode, and it kills the 'digital filter' read)")
    p.add_argument("--flicker", default=0.030, type=float,
                   help="exposure flicker depth (0 disables)")
    p.add_argument("--hands", default=7, type=int,
                   help="chorus: hands writing the same line")
    p.add_argument("--bed", default="click", choices=("click", "none"),
                   help="audio bed. 'click' = a bpm reference slate, NOT music")
    p.add_argument("--seed", default=20261016, type=int)
    p.add_argument("--crf", default=26, type=int)
    p.add_argument("--preset", default="medium")
    p.add_argument("--preview", default=0.0, type=float,
                   help="render only the first N seconds, to check the look")
    p.add_argument("--preview-start", default=0.0, type=float,
                   help="start the preview window at this absolute second "
                        "(use it to inspect a chorus)")
    p.add_argument("--comment", default="", help="container 'comment' metadata")
    p.add_argument("--meta-title", default="")
    args = p.parse_args(argv)

    try:
        rc = render(args)
    except SheetError as exc:
        print(f"SHEET ERROR: {exc}", file=sys.stderr)
        return 2
    if rc != 0:
        return rc

    out = Path(args.out)
    size = out.stat().st_size
    print(f"rendered {out}  ({size} bytes)")
    if not args.comment:
        print("NOTE: pass --comment so the container states what the audio bed "
              "is (a reference click, not a master).")
    print(f"sheet sha256: {sha256(Path(args.lyrics))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
