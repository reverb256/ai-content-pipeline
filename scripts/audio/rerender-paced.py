#!/usr/bin/env python3
"""Re-render Cartographer's Paradox with proper pacing (reuses raw VoxCPM segs).

One-shot fix runner for the 2026-09-02 pacing issue: the original render
concatenated raw TTS segments with ZERO added silence between scenes/lines.
This re-renders from the surviving /tmp workdir raw segments through
storyteller.py's new pacing functions (inter-line varied gaps + [pause:]
cues + SCENE_GAP fallback), then writes the fixed mp3.

Usage:
    python3 scripts/audio/rerender-paced.py <workdir> <out.mp3>
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import storyteller  # noqa: E402


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: rerender-paced.py <workdir> <out.mp3>")
        return 2
    workdir = Path(sys.argv[1])
    out_mp3 = Path(sys.argv[2])
    story_md = Path(__file__).resolve().parent.parent.parent / "campaigns" / "audio-drama-premiere" / "story.md"
    if not story_md.exists():
        print(f"story not found: {story_md}")
        return 2
    if not workdir.exists():
        print(f"workdir not found: {workdir}")
        return 2

    story = storyteller.parse_story(story_md)
    # attach raw segment paths by index
    for i, seg in enumerate(story.segments, start=1):
        raw = workdir / f"seg-{i:02d}-raw.mp3"
        if raw.exists():
            seg.audio_path = str(raw)
            seg.audio_duration = storyteller.ffprobe_duration(raw)

    missing = [seg for seg in story.segments if not seg.audio_path]
    if missing:
        print(f"missing raw audio for {len(missing)}/{len(story.segments)} segments")
        return 1

    work = Path(tempfile.mkdtemp(prefix="storyteller-rerender-"))
    try:
        scene_audio: list[Path] = []
        timeline = 0.0
        for sc in story.scenes:
            segs = [x for x in sc.segments if x.audio_path]
            if not segs:
                print(f"scene '{sc.title}': no segments, skipping")
                continue
            speech = storyteller._concat_with_pacing(segs, work)
            trailing = storyteller._scene_trailing_pause(sc)
            if trailing <= 0.0:
                trailing = storyteller.SCENE_GAP
            if trailing > 0.0:
                gapped = work / f"{storyteller._slug(sc.title)}-trail.wav"
                speech = storyteller._append_silence(speech, gapped, trailing, work)
            scene_path = work / f"{storyteller._slug(sc.title)}-scene.wav"
            out = storyteller._fade(speech, scene_path, duration=storyteller.ffprobe_duration(speech))
            sc.start_offset = timeline
            timeline += storyteller.ffprobe_duration(out)
            scene_audio.append(out)
            print(f"scene '{sc.title}': {storyteller.ffprobe_duration(out):.1f}s "
                  f"(trailing {trailing:.1f}s) cumulative {timeline:.1f}s")

        out_mp3.parent.mkdir(parents=True, exist_ok=True)
        duration = storyteller.concat_scenes(scene_audio, out_mp3)
        print(f"done: {out_mp3} ({duration:.1f}s)")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
