#!/usr/bin/env python3
"""Check that every `video_shape` a genre declares has a rendered artifact.

WHY THIS EXISTS (incident 2026-10-16, card t_ec378832): `music/genres.yaml`
gave the `activist` genre `video_shape: lyric-video`, and NO template
`music/visuals/lyric_video.mp4` existed. The registry validated clean anyway,
because `registry.py` checks that `lanes`, `prompt_template` and `visual_style`
resolve — it never checked `video_shape`. So the registry handed the visual
stage a shape name that no renderer owned, and nothing failed until a human
read the brief.

The template file name is DERIVED, not tabulated: the shape value with `-`
replaced by `_`, plus `.mp4`. That is exactly how the defect was found by hand
(`lyric-video` -> `lyric_video.mp4`), and it holds for all six registry values
today (album-30-60min, loop-10min, mix-60min, single-4min, lyric-video, none).
A hardcoded table would drift; the derivation cannot.

A second, softer check covers the sibling case: a genre whose `visual_style`
sheet (e.g. `visuals/element-fire.md`) has no rendered style clip
(`element_fire.mp4`). That is reported as a WARN because the style clips are
per-style, not per-genre, and two genres may share one style.

Run:  /usr/bin/python3 music/scripts/check_video_shapes.py [--musics PATH]
      /usr/bin/python3 music/scripts/check_video_shapes.py --selftest
Exit: 0 clean; 1 a declared video_shape has no artifact (or --strict WARN).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# A shape that deliberately has NO visual artifact. `none` is the registry
# value for a genre with no video at all (commentary-beds), so it is a
# resolved answer, not a missing file.
SHAPE_WITHOUT_ARTIFACT = {"none"}

MUSIC_DIR = Path(__file__).resolve().parents[1]
if str(MUSIC_DIR) not in sys.path:
    sys.path.insert(0, str(MUSIC_DIR))

import registry  # noqa: E402  (path must be set first)


def template_for(shape: str) -> str:
    """`lyric-video` -> `lyric_video.mp4`. Derived, never tabulated."""
    return f"{shape.strip().replace('-', '_')}.mp4"


def style_clip_for(visual_style: str) -> str:
    """`visuals/element-fire.md` -> `element_fire.mp4`."""
    return f"{Path(visual_style).stem.replace('-', '_')}.mp4"


def check(genres: dict, visuals: Path
          ) -> tuple[list[str], list[str], dict[str, list[str]]]:
    """Return (failures, warnings, shape -> genres) for a registry + visuals dir."""
    failures: list[str] = []
    warnings: list[str] = []
    shape_users: dict[str, list[str]] = {}

    for name in sorted(genres):
        spec = genres[name]

        shape = spec.get("video_shape")
        if not isinstance(shape, str) or not shape.strip():
            failures.append(f"{name}: video_shape is missing or not a string")
            continue
        shape_users.setdefault(shape, []).append(name)

        if shape in SHAPE_WITHOUT_ARTIFACT:
            continue
        template = visuals / template_for(shape)
        if not template.is_file():
            failures.append(
                f"{name}: video_shape '{shape}' -> {template} does not exist "
                f"-- no renderer owns this shape (card t_ec378832)")

        style = spec.get("visual_style")
        if isinstance(style, str) and style:
            clip = visuals / style_clip_for(style)
            if not clip.is_file():
                warnings.append(
                    f"{name}: visual_style '{style}' has no rendered clip "
                    f"{clip.name}")

    return failures, warnings, shape_users


def report(genres: dict, visuals: Path) -> int:
    failures, warnings, shape_users = check(genres, visuals)
    print(f"music/visuals : {visuals}")
    print(f"genres        : {len(genres)}")
    print()
    print(f"{'video_shape':<18}{'template':<22}{'exists':<8}genres")
    for shape in sorted(shape_users):
        if shape in SHAPE_WITHOUT_ARTIFACT:
            print(f"{shape:<18}{'(none by design)':<22}{'-':<8}"
                  f"{', '.join(shape_users[shape])}")
            continue
        template = template_for(shape)
        exists = (visuals / template).is_file()
        print(f"{shape:<18}{template:<22}{str(exists):<8}"
              f"{', '.join(shape_users[shape])}")
    print()
    for w in warnings:
        print(f"WARN  {w}")
    for f in failures:
        print(f"FAIL  {f}")
    if failures:
        print(f"\nFAIL check_video_shapes: {len(failures)} declared "
              f"video_shape(s) with no artifact")
        return 1
    print(f"PASS check_video_shapes ({len(warnings)} warning(s))")
    return 0


def selftest() -> int:
    """Prove the check FAILS on the incident shape, and passes when it exists."""
    visuals = Path("/nonexistent/visuals")
    incident = {"activist": {"video_shape": "lyric-video",
                             "visual_style": "visuals/documentary-grain.md"}}
    failures, _, _ = check(incident, visuals)
    if not failures:
        print("SELFTEST FAIL: the incident (a shape with no artifact) passed")
        return 1
    print(f"SELFTEST ok: incident detected -> {failures[0]}")

    clean = {"activist": {"video_shape": "none",
                          "visual_style": "visuals/documentary-grain.md"}}
    failures, _, _ = check(clean, visuals)
    if failures:
        print(f"SELFTEST FAIL: shape 'none' should be a resolved answer: "
              f"{failures}")
        return 1
    print("SELFTEST ok: video_shape 'none' is not a missing file")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Check that every declared video_shape has an artifact")
    ap.add_argument("--musics", default=str(MUSIC_DIR),
                    help="the music/ directory (default: beside this script)")
    ap.add_argument("--strict", action="store_true",
                    help="treat style-clip warnings as failures")
    ap.add_argument("--selftest", action="store_true",
                    help="prove the check can fail")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    music = Path(args.musics)
    try:
        lanes = registry.load_lanes()
        genres = registry.load_genres(lanes)
    except registry.RegistryError as exc:
        print(f"REGISTRY ERROR: {exc}", file=sys.stderr)
        return 2

    rc = report(genres, music / "visuals")
    if rc == 0 and args.strict:
        _, warnings, _ = check(genres, music / "visuals")
        if warnings:
            print(f"\n--strict: {len(warnings)} style clip(s) unrendered")
            return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
