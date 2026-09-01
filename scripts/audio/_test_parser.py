#!/usr/bin/env python3
"""Quick parser test for storyteller.py."""
from pathlib import Path
import sys
sys.path.insert(0, "scripts/audio")
from storyteller import parse_story

s = parse_story(Path("scripts/audio/example-story.md"))
print(f"scenes: {len(s.scenes)}, segments: {len(s.segments)}")
print(f"speakers: {{x.speaker for x in s.segments}}")
print(f"cast: {list(s.cast.keys())}")
for sc in s.scenes:
    print(f"  scene '{sc.title}': {len(sc.segments)} segs, {len(sc.cues)} cues")
    for seg in sc.segments:
        print(f"    [{seg.speaker}|{seg.emotion}] {seg.text[:60]!r}")
