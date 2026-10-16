#!/usr/bin/env python3
"""check_loop_tiling — a `loop_bars` in the registry must TILE its video shape.

WHY THIS EXISTS (incident 2026-10-16, card t_b75ccb4a, measured on nexus)
------------------------------------------------------------------------
`video_shape: loop-10min` is a 600.000 s video built by REPEATING the delivered
loop, so the loop's length must divide the shape exactly or the video's last
seam is a jump cut. Nothing checked that, and the first loop this lane ever
delivered was 4 bars:

    bar at 150 BPM in 4/4 = 4 x 60 / 150 = exactly 1.600 s
    the 600.000 s shape    = exactly 375 bars
    delivered loop         = 4 bars = 6.400 s  ->  375 / 4 = 93.75 tiles
                                                     ^ FRACTIONAL

`music/scripts/loop_close.py` closed that loop at `BARS_PREFERRED = 4`, the
pack lane's default in `music/assets/pack.py` — legal for a pack cutdown (a
game engine loops any length it is handed) and illegal for the video tile. The
two contracts disagreed and no check could see it, because the tiling arithmetic
lived in one brief's prose. This is that check.

THE ARITHMETIC (integer/Fraction exact; a float here would hide a 93.75)
------------------------------------------------------------------------
    bar_s      = 240 / bpm            a 4/4 bar
    shape_bars = shape_s / bar_s      = shape_s x bpm / 240
    loop_bars  must DIVIDE shape_bars
    span       = loop_bars x bar_s    must be <= --ceiling-s (120.0 s: the
                                      master-loop length the briefs locked) and
                                      >= --floor-s (24.0 s: below that a loop is
                                      a fragment, not a phrase)
    tiles      = shape_s / span       must be an INTEGER

The shape's bar count depends on the GENRE'S OWN TEMPO, not on the shape alone:
375 bars at 150 BPM, but 205 at 82, 220 at 88, 230 at 92. That is why the loop
length is a per-genre field. Where a value lies is shown by the table this check
prints: the legal set for `elemental-fire` is {15, 25, 75, 125, 375} bars, and
75 (120.000 s, the ceiling) is REFUSED by the render — the ACE engine emits
1.5-6.2 s of digital silence inside every requested window, so a loop as long as
the render can never be closed (`loop_close.py`, measured: "the musical region
(115.197s) is shorter than one 120.000s loop — nothing to close"), which leaves
25 bars = 40.000 s = 15 exact tiles. A render that is to carry a loop must be
longer than that loop. Delivery is the rail's measurement; the invariant here is
declarative and must hold before any render exists.

WHAT THIS CHECK DOES NOT DO: it does not decide the value (that is the registry
field's, card t_b75ccb4a) and it does not measure a rendered artifact (that is
`loop_close.py` at the rail, and the two rulers in `gate_loop_points.py`). It
recomputes the declared value's legality from the genre's tempo and the shape
artifact's own duration, and FAILS when the declaration cannot tile.

PROVENANCE OF THE TWO INPUTS: the shape's duration is ffprobe's reading of
`music/visuals/<shape>.mp4`, the rendered shape artifact (600.000000 s for
`loop-10min`) — the same derivation `music/scripts/check_video_shapes.py` uses to
find the template. The tempo is the planner's OWN resolution order, reused, not
re-implemented: `planner.bpm_anchor_for()` over the genre's blueprint
(`music/lyrics/blueprints/<genre>.yaml` `bpm_anchor`) and then the template's
caption (`planner.bpm_in_caption()`). Where neither exists the check FAILS: a
tempo it invented would validate itself.

Usage:
  /usr/bin/python3 music/scripts/check_loop_tiling.py [--repo DIR]
      [--bpm GENRE=N] [--ceiling-s 120.0] [--floor-s 24.0] [--quiet]
  /usr/bin/python3 music/scripts/check_loop_tiling.py --selftest

Exit codes: 0 = every declared loop_bars tiles its shape, 1 = at least one
violation, 2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

# Shapes that are built by REPEATING a loop, so a loop_bars declared for one of
# them must tile it. A shape not in this set is not built by tiling: `none` has
# no video at all, and an album/mix/lyric-video/single shape is a programme, not
# a tile. A `loop_bars` on a non-tiling shape is reported as a violation rather
# than ignored — a field that cannot mean anything is a defect (fail loudly).
TILING_SHAPES = ("loop-10min",)

GENRES_YAML = "music/genres.yaml"
VISUALS_DIR = "music/visuals"
BLUEPRINTS_DIR = "music/lyrics/blueprints"

# The band a delivered loop must fall in, in seconds. The ceiling is the
# master-loop length the genre briefs locked (elemental-fire §4: "the master loop
# is 120.0 s"); the floor is the shortest span that is a phrase rather than a
# fragment (card t_b75ccb4a).
CEILING_S = 120.0
FLOOR_S = 24.0


def find_ffprobe() -> Path:
    """The lane's pinned ffprobe, then $PATH — one convention (see loop_close.py)."""
    import os
    cands = []
    env = os.environ.get("FFMPEG_BIN_DIR")
    if env:
        cands.append(Path(env))
    cands.append(Path.home() / ".hermes" / "tools" /
                 "ffmpeg-9.0.1-linux-x64" / "bin")
    for c in cands:
        if (c / "ffprobe").is_file():
            return c / "ffprobe"
    found = shutil.which("ffprobe")
    return Path(found) if found else Path("/usr/bin/ffprobe")


def shape_template(shape: str) -> str:
    """`loop-10min` -> `loop_10min.mp4`, the derivation check_video_shapes.py uses."""
    return f"{shape.strip().replace('-', '_')}.mp4"


def probe_duration_s(path: Path) -> Fraction | None:
    """The artifact's own duration, exactly, as a Fraction of its printed decimal."""
    proc = subprocess.run(
        [str(find_ffprobe()), "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=120)
    raw = (proc.stdout or "").strip()
    if proc.returncode != 0 or not re.fullmatch(r"\d+(\.\d+)?", raw):
        return None
    return Fraction(raw)


def divisors(n: int) -> list[int]:
    return [d for d in range(1, n + 1) if n % d == 0]


def audit(genre: str, spec: dict, shape_s: Fraction | None,
          bpm: int | None, shape: str | None = None,
          ceiling_s: float = CEILING_S, floor_s: float = FLOOR_S,
          ) -> tuple[list[str], dict]:
    """Recompute the declared loop_bars' legality. Returns (problems, info).

    Pure: every input is passed in, so --selftest exercises the same code path
    the real registry goes through (no fixture registry to drift from the real
    one).
    """
    problems: list[str] = []
    declared = spec.get("loop_bars")
    shape = shape if shape is not None else spec.get("video_shape")
    info: dict = {"genre": genre, "video_shape": shape, "loop_bars": declared,
                  "bpm": bpm, "shape_s": None if shape_s is None else float(shape_s),
                  "span_s": None, "tiles": None, "shape_bars": None,
                  "legal": [], "problems": problems}

    if declared is None:
        if shape in TILING_SHAPES:
            problems.append(
                f"{genre}: video_shape '{shape}' is built by repeating a loop but "
                f"no `loop_bars` is declared — the loop's length cannot be "
                f"checked, and an unchecked length is how a 4-bar loop (93.75 "
                f"tiles) reached the rail (card t_b75ccb4a). Declare `loop_bars` "
                f"in {GENRES_YAML}.")
        return problems, info

    if isinstance(declared, bool) or not isinstance(declared, int) or declared <= 0:
        problems.append(f"{genre}: `loop_bars` must be a positive integer, got "
                        f"{declared!r}")
        return problems, info

    if shape not in TILING_SHAPES:
        problems.append(
            f"{genre}: `loop_bars: {declared}` is declared for video_shape "
            f"{shape!r}, which is not a tiled loop shape "
            f"({', '.join(TILING_SHAPES)}) — the field cannot mean anything here")
        return problems, info

    if shape_s is None or shape_s <= 0:
        problems.append(f"{genre}: the shape artifact for '{shape}' "
                        f"({VISUALS_DIR}/{shape_template(str(shape))}) has no "
                        f"readable duration — the tiling cannot be checked, and a "
                        f"shape duration this check GUESSED would be a fabricated "
                        f"contract")
        return problems, info

    if not bpm or bpm <= 0:
        problems.append(f"{genre}: no tempo resolves (blueprint "
                        f"`{BLUEPRINTS_DIR}/{genre}.yaml` `bpm_anchor`, then the "
                        f"template caption) — the tiling is a function of tempo "
                        f"(shape_bars = shape_s x bpm / 240), so it cannot be "
                        f"checked without one")
        return problems, info

    bar_s = Fraction(240, bpm)
    shape_bars_exact = shape_s / bar_s
    info["bar_s"] = float(bar_s)
    if shape_bars_exact.denominator != 1:
        problems.append(
            f"{genre}: the {float(shape_s):.6f} s shape is {shape_bars_exact} bars "
            f"at {bpm} BPM — NOT a whole number of bars, so no whole-bar loop can "
            f"tile it")
        return problems, info
    shape_bars = int(shape_bars_exact)
    span = declared * bar_s
    tiles = shape_s / span
    info.update(shape_bars=shape_bars, span_s=float(span),
                tiles=float(tiles))

    # The legal set, so a reader sees WHY the declared value is the one it is.
    for d in divisors(shape_bars):
        s = d * bar_s
        if FLOOR_S <= float(s) <= ceiling_s:
            info["legal"].append({"bars": d, "span_s": float(s),
                                  "tiles": float(shape_s / s)})

    if shape_bars % declared != 0 or tiles.denominator != 1:
        problems.append(
            f"{genre}: `loop_bars: {declared}` is {float(span):.6f} s and tiles "
            f"{float(tiles)} times into the {float(shape_s):.3f} s '{shape}' video "
            f"— FRACTIONAL. {shape_bars} bars / {declared} is not a whole number, "
            f"so the video's last seam is a jump cut. Legal values in "
            f"[{floor_s:.1f}, {ceiling_s:.1f}] s: "
            + ", ".join(f"{e['bars']} bars ({e['span_s']:.3f} s, "
                        f"{e['tiles']:.0f} tiles)" for e in info["legal"]))

    if float(span) > ceiling_s:
        problems.append(
            f"{genre}: `loop_bars: {declared}` is {float(span):.3f} s — above the "
            f"{ceiling_s:.1f} s ceiling (the master-loop length the genre briefs "
            f"locked). A longer tile is no longer the loop the briefs spec.")
    if float(span) < floor_s:
        problems.append(
            f"{genre}: `loop_bars: {declared}` is {float(span):.3f} s — below the "
            f"{floor_s:.1f} s floor: that is a fragment, not a phrase "
            f"(card t_b75ccb4a).")

    return problems, info


def resolve_tempo(genre: str, music_dir: Path, override: int | None = None
                  ) -> tuple[int | None, str]:
    """The planner's OWN resolution order: blueprint bpm_anchor, then caption."""
    if override is not None:
        return override, "--bpm override"
    planner_dir = music_dir / "planner"
    if str(planner_dir) not in sys.path:
        sys.path.insert(0, str(planner_dir))
    try:
        import planner  # the lane's own parser + resolution order, not a copy
    except Exception as exc:  # pragma: no cover - environment failure
        return None, f"planner import failed: {exc!r}"
    import yaml
    bp_path = music_dir / "lyrics" / "blueprints" / f"{genre}.yaml"
    blueprint: dict = {}
    source = "template caption"
    if bp_path.is_file():
        try:
            doc = yaml.safe_load(bp_path.read_text(encoding="utf-8"))
            if isinstance(doc, dict):
                blueprint = doc
                if doc.get("bpm_anchor") is not None:
                    source = f"blueprint {bp_path.name} bpm_anchor"
        except Exception:
            blueprint = {}
    body = planner.load_template(genre)
    bpm = planner.bpm_anchor_for(
        {"blueprint": blueprint,
         "template_bpm": planner.bpm_in_caption(body.get("caption") or "")})
    return (int(bpm) if bpm else None), source


def run(repo: Path, overrides: dict, ceiling_s: float, floor_s: float,
        quiet: bool) -> int:
    import yaml
    music_dir = repo / "music"
    doc = yaml.safe_load((repo / GENRES_YAML).read_text(encoding="utf-8"))
    genres = doc.get("genres") or {}
    visuals = music_dir / "visuals"

    print(f"repo          : {repo}")
    print(f"registry      : {GENRES_YAML} ({len(genres)} genres)")
    print(f"band          : {floor_s:.1f} s .. {ceiling_s:.1f} s per loop")
    print()
    header = (f"{'genre':<20}{'shape':<14}{'bpm':>5}{'shape_bars':>12}"
              f"{'loop_bars':>11}{'span_s':>10}{'tiles':>8}  verdict")
    print(header)
    print("-" * len(header))

    failures: list[str] = []
    rows: list[dict] = []
    for genre in sorted(genres):
        spec = genres[genre]
        shape = spec.get("video_shape")
        if spec.get("loop_bars") is None and shape not in TILING_SHAPES:
            continue
        shape_s = None
        if isinstance(shape, str) and shape in TILING_SHAPES:
            art = visuals / shape_template(shape)
            shape_s = probe_duration_s(art) if art.is_file() else None
        bpm, source = resolve_tempo(genre, music_dir, overrides.get(genre))
        problems, info = audit(genre, spec, shape_s, bpm, shape, ceiling_s,
                               floor_s)
        info["tempo_source"] = source
        rows.append(info)
        failures.extend(problems)
        span = "" if info["span_s"] is None else f"{info['span_s']:.3f}"
        tiles = "" if info["tiles"] is None else f"{info['tiles']:.2f}"
        bars = "" if info["shape_bars"] is None else str(info["shape_bars"])
        verdict = "OK" if not problems else f"FAIL ({len(problems)})"
        print(f"{genre:<20}{str(shape):<14}{str(bpm or '-'):>5}{bars:>12}"
              f"{str(info['loop_bars']):>11}{span:>10}{tiles:>8}  {verdict}")
        if problems and not quiet:
            for p in problems:
                print(f"    - {p}")
        if info["legal"]:
            print(f"    legal: " + ", ".join(
                f"{e['bars']} ({e['span_s']:.3f}s/{e['tiles']:.0f}x)"
                for e in info["legal"])
                + f"   [tempo: {source}]")

    print()
    if failures:
        print(f"FAIL check_loop_tiling: {len(failures)} problem(s) — a declared "
              f"loop length that does not tile its shape leaves a jump cut at the "
              f"video's last seam")
        for p in failures:
            print(f"  - {p}")
        return 1
    print(f"PASS check_loop_tiling ({len(rows)} loop-claiming genre(s): every "
          f"declared loop_bars divides its shape's bar count exactly)")
    return 0


def selftest() -> int:
    """Prove the check FAILS on the incident and PASSES on the shipped values."""
    shape_s = Fraction(600)
    checks: list[tuple[str, bool, str]] = []

    # 1. THE INCIDENT: 4 bars at 150 BPM = 6.400 s -> 93.75 tiles.
    probs, info = audit("elemental-fire", {"video_shape": "loop-10min",
                                           "loop_bars": 4}, shape_s, 150)
    ok = (bool(probs) and info["tiles"] == 93.75
          and any("FRACTIONAL" in p for p in probs))
    checks.append(("incident 4 bars @150 BPM -> 93.75 tiles FAILS",
                   ok, f"tiles={info['tiles']} problems={len(probs)}"))

    # 2. The shipped value for the same genre tiles exactly (15 tiles).
    probs, info = audit("elemental-fire", {"video_shape": "loop-10min",
                                           "loop_bars": 25}, shape_s, 150)
    ok = (not probs and info["tiles"] == 15.0 and info["span_s"] == 40.0)
    checks.append(("shipped 25 bars @150 BPM -> 15 tiles PASSES",
                   ok, f"tiles={info['tiles']} span={info['span_s']} "
                       f"problems={probs}"))

    # 3. A legal-but-longer value also passes: the check guards the INVARIANT,
    #    not one blessed number (15 tiles is the value, 5 tiles is legal).
    probs, _ = audit("elemental-fire", {"video_shape": "loop-10min",
                                        "loop_bars": 75}, shape_s, 150)
    checks.append(("75 bars @150 BPM (the ceiling) is legal-but-not-chosen",
                   not probs, f"problems={probs}"))

    # 4. Every shipped sibling value, at its own tempo.
    for genre, bpm, bars, tiles in (("elemental-water", 82, 41, 5),
                                    ("elemental-earth", 88, 44, 5),
                                    ("elemental-air", 92, 46, 5),
                                    ("chiptune-8bit", 150, 75, 5)):
        probs, info = audit(genre, {"video_shape": "loop-10min",
                                    "loop_bars": bars}, shape_s, bpm)
        checks.append((f"{genre}: {bars} bars @{bpm} BPM -> {tiles} tiles",
                       not probs and info["tiles"] == float(tiles),
                       f"tiles={info['tiles']} problems={probs}"))

    # 5. The same tempo-derived defect on another genre's tempo: 4 bars at 88 BPM
    #    is 10.909 s and DOES tile (55x) but is below the phrase floor.
    probs, info = audit("elemental-earth", {"video_shape": "loop-10min",
                                            "loop_bars": 4}, shape_s, 88)
    ok = (info["tiles"] == 55.0 and bool(probs)
          and any("floor" in p for p in probs))
    checks.append(("4 bars @88 BPM tiles 55x yet FAILS the phrase floor",
                   ok, f"tiles={info['tiles']} problems={probs}"))

    # 6. Fail closed: a tiled shape with no declared length.
    probs, _ = audit("elemental-fire", {"video_shape": "loop-10min"}, shape_s, 150)
    checks.append(("no loop_bars on a tiled shape FAILS",
                   bool(probs), f"problems={probs}"))

    # 7. Fail closed: no tempo resolves, and no shape duration is readable.
    probs, _ = audit("elemental-fire", {"video_shape": "loop-10min",
                                        "loop_bars": 25}, shape_s, None)
    checks.append(("no tempo FAILS (the check never invents one)",
                   any("no tempo resolves" in p for p in probs), f"{probs}"))
    probs, _ = audit("elemental-fire", {"video_shape": "loop-10min",
                                        "loop_bars": 25}, None, 150)
    checks.append(("unreadable shape artifact FAILS (never guessed)",
                   any("no readable duration" in p for p in probs), f"{probs}"))

    # 8. A loop_bars on a shape that is not tiled.
    probs, _ = audit("chill-lounge", {"video_shape": "album-30-60min",
                                      "loop_bars": 8}, shape_s, 150)
    checks.append(("loop_bars on a non-tiling shape FAILS",
                   any("not a tiled loop shape" in p for p in probs), f"{probs}"))

    width = max(len(name) for name, _, _ in checks)
    bad = 0
    for name, ok, detail in checks:
        print(f"{name:<{width}}  {'PASS' if ok else 'FAIL'}   {detail}")
        bad += 0 if ok else 1
    if bad:
        print(f"\nFAIL check_loop_tiling --selftest: {bad} case(s) did not "
              f"reproduce")
        return 1
    print(f"\nPASS check_loop_tiling --selftest: {len(checks)} cases "
          f"(the incident, the shipped values, and the fail-closed paths)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="check_loop_tiling — every declared loop_bars must tile its "
                    "video shape exactly")
    ap.add_argument("--repo", default=None,
                    help="repo root (default: two levels above this script)")
    ap.add_argument("--bpm", action="append", default=[],
                    metavar="GENRE=N", help="override a genre's tempo")
    ap.add_argument("--ceiling-s", type=float, default=CEILING_S)
    ap.add_argument("--floor-s", type=float, default=FLOOR_S)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    repo = Path(args.repo).resolve() if args.repo else \
        Path(__file__).resolve().parents[2]
    overrides: dict = {}
    for item in args.bpm:
        if "=" not in item:
            print(f"usage: --bpm GENRE=N (got {item!r})", file=sys.stderr)
            return 2
        g, v = item.split("=", 1)
        try:
            overrides[g] = int(v)
        except ValueError:
            print(f"usage: --bpm GENRE=N — {v!r} is not an integer",
                  file=sys.stderr)
            return 2

    if args.json:
        import yaml  # noqa: F401
        doc = yaml.safe_load((repo / GENRES_YAML).read_text(encoding="utf-8"))
        music_dir = repo / "music"
        out = []
        rc = 0
        for genre in sorted((doc.get("genres") or {})):
            spec = (doc.get("genres") or {})[genre]
            shape = spec.get("video_shape")
            if spec.get("loop_bars") is None and shape not in TILING_SHAPES:
                continue
            shape_s = None
            if isinstance(shape, str) and shape in TILING_SHAPES:
                art = music_dir / "visuals" / shape_template(shape)
                shape_s = probe_duration_s(art) if art.is_file() else None
            bpm, source = resolve_tempo(genre, music_dir, overrides.get(genre))
            problems, info = audit(genre, spec, shape_s, bpm, shape,
                                   args.ceiling_s, args.floor_s)
            info["tempo_source"] = source
            rc = rc or (1 if problems else 0)
            out.append(info)
        print(json.dumps(out, indent=2))
        return rc

    return run(repo, overrides, args.ceiling_s, args.floor_s, args.quiet)


if __name__ == "__main__":
    sys.exit(main())
