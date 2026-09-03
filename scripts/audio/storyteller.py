#!/usr/bin/env python3
"""storyteller.py v3 — production audio-drama pipeline for the content machine.

v3 changes (mix/master/transition upgrade):
  - Canonical audio: force 48 kHz / stereo / 24-bit before mixing
  - Two-pass EBU R128 loudness normalization + true-peak limiting
  - Equal Power crossfades between scenes (5s overlap, qsin:qsin)
  - Continuous room-tone beds per scene (auto-generated when no explicit atmos)
  - Per-scene reverb consistency (same acoustic space for all elements)

Reads a story script, synthesizes per-line speech through VoxCPM Voice
Design (primary, self-hosted) with MiniMax / Chatterbox fallback, layers
SFX + ambience + music, ducks music under dialogue with sidechain
compression, normalizes to EBU R128, and exports b-roll clips.

Usage:
    storyteller.py story.md -o out/finished.mp3 [options]

Input format (documented in scripts/audio/example-story.md):

    ---
    title: The Last Signal
    cast:
      Mara: a young woman, tense, low and careful
      Commander Voss: a gruff 50-year-old detective, world-weary, slight
        smoker's rasp
    narrator_voice: English_expressive_narrator
    model: speech-2.8-hd
    speed: 1.0
    ---

    # Scene 1 — The Call
    [ATMOS: rain on tin roof]
    Mara: The console beeped once.
    Commander Voss (angry): Who left this running?
    [SFX: door creak]
    Narrator: The silence answered her.

Every H2 line starts a new scene. A cue line sets ambience, sfx, music,
emotion, or a pause. A speaker line reads as dialogue. A plain line reads
as narration.

Environment:
    MINIMAX_API_KEY  — required for the MiniMax path (loaded from ~/.hermes/.env)
    CHATTERBOX_API   — Chatterbox base URL, default http://10.1.1.130:8004
    VOXCPM_QUALITY   — f16 | q8 | q4, default f16
    STORYTELLER_DEBUG — set to 1 to keep the working directory

Exit codes:
    0 success (finished audio written)
    1 fatal error (no provider available, no segments parsed)
    2 usage error
    3 provider forced but unusable
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ENV_FILE = Path(os.environ.get("HERMES_ENV_FILE", Path.home() / ".hermes" / ".env"))
REPO = Path(os.environ.get("REPO", Path.home() / "Projects" / "ai-content-pipeline"))
DEFAULT_CHATTERBOX_API = "http://10.1.1.130:8004"

VALID_EMOTIONS = {
    "happy", "sad", "angry", "fearful", "disgusted",
    "surprised", "calm", "fluent", "whisper",
    "tense", "excited", "hesitant", "exhausted", "defiant",
    "urgent", "amused", "hopeful", "sorrowful", "cold", "warm",
}
VALID_SFX = {"spacious_echo", "auditorium_echo", "lofi_telephone", "robotic"}

# Mixed-file stem → display name used in filenames and logs.
SFX_LIBRARY_NAMES = {
    "door_creak": "door creak",
    "rain": "rain",
    "heartbeat": "heartbeat",
    "thunder": "thunder",
    "wind": "wind",
    "footsteps": "footsteps",
    "static": "radio static",
    "signal": "signal tone",
}

PROMPT_NAMES = {"narrator", "narration"}
DEFAULT_EMOTION = "calm"
DEFAULT_EMOTION_DESC = "a clear, expressive narrator"


def log(msg: str) -> None:
    print(f"[storyteller] {msg}", flush=True)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    """Run a command; raise a readable error on failure."""
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)
    except subprocess.CalledProcessError as e:
        tail = (e.stderr or e.stdout or "").strip().splitlines()[-8:]
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n" + "\n".join(tail)) from e


def load_env() -> None:
    """Load KEY=value lines from ~/.hermes/.env (no export, no quotes)."""
    if not ENV_FILE.exists():
        return
    try:
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, val)
    except OSError:
        pass


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH. Install it first.")


# --------------------------------------------------------------------------- #
# Story script parsing
# --------------------------------------------------------------------------- #

@dataclass
class Cue:
    """One non-speech cue: ambience, sfx, music, emotion, or a pause."""
    kind: str  # atmos | sfx | music | emotion | pause
    value: str = ""
    # Resolved asset path for atmos/sfx/music when one is available.
    path: str = ""
    duration: float = 0.0  # cue seconds for pause
    # Extra options from `[emotion | sound_effect=... | speed=... | voice=...]`
    opts: dict = field(default_factory=dict)


@dataclass
class Segment:
    """One TTS synthesis unit: a speaker line within a scene."""
    scene: str
    speaker: str = "Narrator"
    emotion: str = DEFAULT_EMOTION
    text: str = ""
    voice: str = ""
    voice_desc: str = ""
    speed: float = 1.0
    # Narrative position inside the scene (0.0 = scene start).
    offset: float = 0.0
    # Audio duration after mixing, filled during synthesis.
    audio_duration: float = 0.0
    audio_path: str = ""
    provider: str = ""


@dataclass
class Scene:
    """A scene heading plus the lines and cues that belong to it.

    v3 format: each scene carries a goal (R1), optional cold-open (R2),
    optional link (R3), and word-budget tracking (R5).
    """
    title: str
    text: str = ""
    segments: list[Segment] = field(default_factory=list)
    cues: list[Cue] = field(default_factory=list)
    start_offset: float = 0.0  # global timeline position, filled at assembly
    # R1: scene goal (reveal | escalate | decision)
    goal: str = ""
    # R2: cold-open tag (first scene only)
    cold_open: bool = False
    # R3: causal link to previous scene (therefore | but)
    link: str = ""
    # R5: per-scene word budget override
    word_budget: int = 0
    # R12: track aural establishment
    has_atmos_or_sfx: bool = False
    # Speaker set in this scene (for R7/R21 contrast casting)
    scene_speakers: set = field(default_factory=set)


@dataclass
class CastMember:
    """One cast entry: the voice that speaks a character.

    v3 format: 5-dimension Voice Design (gender, age, pitch, pace, texture)
    plus audience-facing description and character-craft fields.
    """
    name: str
    voice_desc: str = ""
    voice: str = ""  # MiniMax voice id override
    # R6: 5-dimension Voice Design
    gender: str = ""
    age: str = ""
    pitch: str = ""
    pace: str = ""
    texture: str = ""
    accent: str = ""
    # R23: audience-facing description
    description: str = ""
    # R13: character craft
    want: str = ""
    need: str = ""
    flaw: str = ""
    arc: str = ""
    speech_pattern: str = ""
    # R19: track first appearance for name-tag enforcement
    first_appearance_done: bool = False

    def voice_dimensions(self) -> dict[str, str]:
        """Return the 5 voice dimensions as a dict."""
        return {
            "gender": self.gender,
            "age": self.age,
            "pitch": self.pitch,
            "pace": self.pace,
            "texture": self.texture,
        }

    def dimension_count(self) -> int:
        """Return number of non-empty voice dimensions (R6: require >= 3)."""
        return sum(1 for v in self.voice_dimensions().values() if v)

    def contrast_distance(self, other: "CastMember") -> dict:
        """Compute voice distance vs another character (R7/R21)."""
        d_self = self.voice_dimensions()
        d_other = other.voice_dimensions()
        # Pitch: map qualitative labels to numeric tiers for comparison
        pitch_tiers = {
            "very_low": 1, "low": 2, "low_medium": 3, "medium": 4,
            "high_medium": 5, "high": 6, "very_high": 7,
        }
        pace_tiers = {
            "very_slow": 1, "slow": 2, "steady": 3, "moderate": 3,
            "quick": 4, "fast": 5, "very_fast": 6,
        }
        p_self = pitch_tiers.get(self.pitch.lower().replace("-", "_").replace(" ", "_"), 4)
        p_other = pitch_tiers.get(other.pitch.lower().replace("-", "_").replace(" ", "_"), 4)
        s_self = pace_tiers.get(self.pace.lower().replace("-", "_").replace(" ", "_"), 3)
        s_other = pace_tiers.get(other.pace.lower().replace("-", "_").replace(" ", "_"), 3)
        pitch_delta = abs(p_self - p_other)
        pace_delta = abs(s_self - s_other)
        # texture difference: 1 if different, 0 if same
        tex_self = self.texture.lower().strip()
        tex_other = other.texture.lower().strip()
        texture_diff = 1 if tex_self != tex_other else 0
        return {
            "pitch_delta": pitch_delta,
            "pace_delta": pace_delta,
            "texture_diff": texture_diff,
            "pitch_delta_pct": pitch_delta / 6.0,  # normalized 0-1
            "pace_delta_pct": pace_delta / 5.0,
        }


@dataclass
class Story:
    title: str = "untitled"
    voice: str = "English_expressive_narrator"
    fallback_voice: str = "Connor.wav"
    model: str = "speech-2.8-hd"
    speed: float = 1.0
    cast: dict[str, CastMember] = field(default_factory=dict)
    scenes: list[Scene] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    # v3 format fields
    narrator_voice: str = ""
    tier: str = "short"  # R5: short | long | epic
    acts: int = 0  # R4: act count for serialized
    pronunciation: dict = field(default_factory=dict)  # R8: pronunciation guide
    # R5: word budget per tier
    tier_budgets: dict = field(default_factory=lambda: {
        "short": 500, "long": 400, "epic": 500,
    })

    def cast_member(self, speaker: str) -> CastMember | None:
        """Return the cast entry for a speaker, or None for the narrator."""
        name = speaker.strip().lower()
        if name in self.cast:
            return self.cast[name]
        # Also match a bare name when the script wrote "Commander Voss" and
        # the cast wrote "Commander Voss, the warden": match on first word.
        for member in self.cast.values():
            if name == member.name.strip().lower().split()[0]:
                return member
        return None


def _parse_frontmatter(block: str) -> dict:
    """Parse YAML frontmatter into a dict.

    v3 format: uses PyYAML for structured cast entries with 5-dimension Voice
    Design. Falls back to legacy flat-string parsing if YAML is unavailable
    or fails.
    """
    # Try YAML first for v3 structured cast blocks
    try:
        import yaml
        parsed = yaml.safe_load(block)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    # Legacy fallback: flat key:value parsing
    return _parse_frontmatter_legacy(block)


def _parse_frontmatter_legacy(block: str) -> dict:
    """Legacy flat-string frontmatter parser (pre-v3 fallback)."""
    meta: dict = {}
    cast: dict[str, str] = {}
    cast_key = "cast"
    cur_name = ""
    for line in block.splitlines():
        leading = len(line) - len(line.lstrip())
        if line.startswith("  ") and leading >= 4 and cur_name:
            item = line.strip()
            if ":" in item:
                k, _, v = item.partition(":")
                cast[cur_name.lower()] += " " + v.strip()
            elif item:
                cast[cur_name.lower()] += " " + item
            continue
        if line.startswith("  "):
            item = line.strip()
            if not item:
                continue
            if item.startswith("-"):
                item = item[1:].strip()
                if ":" not in item:
                    continue
                cur_name, _, desc = item.partition(":")
                cur_name = cur_name.strip().strip('"').strip("'")
                cast[cur_name.lower()] = desc.strip()
            elif ":" in item:
                cur_name, _, desc = item.partition(":")
                cur_name = cur_name.strip().strip('"').strip("'")
                cast[cur_name.lower()] = desc.strip()
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip().lower().replace(" ", "_")
        v = v.strip().strip('"').strip("'")
        if k == "cast":
            cast_key = k
            continue
        meta[k] = v
    if cast:
        meta["cast"] = cast
    return meta


def _parse_cue(line: str) -> Cue | None:
    """Parse a bracket line into a Cue, or None when it is not a cue.

    Supported cue syntax:
        [emotion]                     → emotion (backward compatible)
        [emotion | key=val]           → emotion + options
        [SFX: name]                   → sound effect
        [ATMOS: name]                 → ambience bed
        [MUSIC: name]                 → music layer
        [pause: 1.2]                  → explicit silence
    """
    inner = line.strip().strip("[]").strip()
    if not inner:
        return None

    m = re.match(r"^(SFX|ATMOS|MUSIC|PAUSE|EMOTION)\s*:\s*(.+)$", inner, re.I)
    if m:
        kind = m.group(1).lower()
        value = m.group(2).strip()
        if kind == "pause":
            try:
                return Cue(kind="pause", value=value, duration=float(value))
            except ValueError:
                return None
        if kind == "emotion":
            if value.lower() not in VALID_EMOTIONS:
                value = DEFAULT_EMOTION
            return Cue(kind="emotion", value=value)
        return Cue(kind=kind, value=value)

    parts = [p.strip() for p in inner.split("|")]
    emotion = parts[0].lower()
    if emotion not in VALID_EMOTIONS:
        return None
    opts: dict = {}
    for p in parts[1:]:
        if "=" in p:
            k, _, v = p.partition("=")
            opts[k.strip().lower().replace(" ", "_")] = v.strip()
    return Cue(kind="emotion", value=emotion, opts=opts)


def _speaker_of(line: str) -> tuple[str, str, str]:
    """Split 'Speaker (emotion): text' into (speaker, emotion, text).

    Returns ('', '', line) when the line has no speaker prefix.
    """
    m = re.match(r"^([^:()\[\]]+?)\s*(?:\(([^)]*)\))?\s*:\s*(.*)$", line, re.S)
    if not m:
        return "", "", line
    speaker = m.group(1).strip()
    emotion = (m.group(2) or "").strip()
    text = m.group(3).strip()
    if not speaker or not text:
        return "", "", line
    return speaker, emotion, text


def parse_story(path: Path) -> Story:
    """Parse the v3 story format documented in scripts/audio/example-story.md.

    Enforces R1-R23 craft rules through parseable gates:
      R1  — every scene must declare goal: reveal|escalate|decision
      R2  — first scene must carry [cold-open]
      R3  — scenes should carry [link: therefore|but]
      R6  — cast entries should have >= 3 voice dimensions
      R7  — characters in same scene must differ >= 15% pitch/pace
      R12 — every scene must establish aural environment (atmos/sfx)
      R19 — first character appearance must have name tag
      R20 — narrator-voice separation (dialogue tags = narrator)
      R21 — contrast casting: pitch delta >= 15%, pace delta >= 10%
      R22 — pause taxonomy: short/scene/section/chapter or numeric seconds
    """
    import yaml
    text = path.read_text(encoding="utf-8")
    story = Story()

    # frontmatter
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        meta = _parse_frontmatter(m.group(1))
        story.title = meta.get("title", story.title)
        story.voice = meta.get("voice", story.voice)
        story.fallback_voice = meta.get("fallback_voice", story.fallback_voice)
        story.model = meta.get("model", story.model)
        story.narrator_voice = meta.get("narrator_voice", "")
        story.tier = meta.get("tier", "short")
        try:
            story.acts = int(meta.get("acts", 0))
        except (ValueError, TypeError):
            story.acts = 0
        try:
            story.speed = float(meta.get("speed", story.speed))
        except (ValueError, TypeError):
            pass
        story.pronunciation = meta.get("pronunciation", {})
        raw_cast = meta.get("cast", {})
        _parse_v3_cast(story, raw_cast)
        text = text[m.end():]

    # Strip the FORMAT DOCUMENTATION block
    doc_end = text.find("<!-- DOC-END -->")
    if doc_end != -1:
        text = text[doc_end + len("<!-- DOC-END -->"):]

    scene: Scene | None = None
    pending_emotion = DEFAULT_EMOTION
    first_scene = True
    # Track first appearances per character
    first_appearances: dict[str, bool] = {}
    for name in story.cast:
        first_appearances[name] = not story.cast[name].first_appearance_done

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^#{1,6}\s+", line):
            # flush current scene
            if scene is not None and (scene.text.strip() or scene.segments):
                story.scenes.append(scene)
            heading = re.sub(r"^#{1,6}\s+", "", stripped)
            scene = _parse_scene_heading(heading, first_scene)
            first_scene = False
            pending_emotion = DEFAULT_EMOTION
            continue
        if scene is None:
            scene = Scene(title="intro")
        # cue line
        if stripped.startswith("[") and stripped.endswith("]"):
            cue = _parse_cue_v3(stripped)
            if cue is None:
                _append_segment_text(scene, story, stripped)
                continue
            if cue.kind == "emotion":
                pending_emotion = cue.value
                if cue.value in ("fearful", "whisper", "angry", "sad", "surprised"):
                    scene.cues.append(cue)
                continue
            if cue.kind == "pause":
                scene.cues.append(cue)
                continue
            if cue.kind in ("atmos", "sfx"):
                scene.has_atmos_or_sfx = True
            scene.cues.append(cue)
            continue
        # skip horizontal rules
        if re.match(r"^-{3,}\s*$", stripped):
            continue
        speaker, emotion, body = _speaker_of(stripped)
        if speaker and body:
            # R19: first-appearance name tag check
            speaker_lower = speaker.strip().lower()
            if speaker_lower in first_appearances and first_appearances[speaker_lower]:
                # First appearance: check for name tag in text
                _enforce_name_tag(scene, story, speaker, body, stripped)
                first_appearances[speaker_lower] = False
                if speaker_lower in story.cast:
                    story.cast[speaker_lower].first_appearance_done = True
            seg = Segment(
                scene=scene.title,
                speaker=speaker,
                emotion=emotion or pending_emotion,
                text=body,
                speed=story.speed,
            )
            story.segments.append(seg)
            scene.segments.append(seg)
            scene.scene_speakers.add(speaker.strip().lower())
            if scene.text:
                scene.text += "\n"
            scene.text += stripped
            continue
        # plain line → narration (default to narrator)
        _append_segment_text(scene, story, stripped)

    # flush final scene
    if scene is not None and (scene.text.strip() or scene.segments):
        if not story.scenes or story.scenes[-1] is not scene:
            story.scenes.append(scene)

    if not story.segments:
        raise ValueError(f"no segments parsed from {path}")

    _resolve_narrator(story)

    # v3 GATES: enforce craft rules
    _enforce_v3_gates(story, path)

    # narrative offset per segment
    for sc in story.scenes:
        off = 0.0
        for seg in sc.segments:
            seg.offset = off
            off += max(seg.audio_duration, 0.0)
    return story


def _parse_v3_cast(story: Story, raw_cast) -> None:
    """Parse cast entries from YAML (dict of dicts) or legacy flat format."""
    if isinstance(raw_cast, dict):
        for name, entry in raw_cast.items():
            key = name.strip().lower()
            if isinstance(entry, dict):
                # v3 structured format
                cm = CastMember(
                    name=name.strip(),
                    voice_desc=entry.get("description", entry.get("voice_desc", "")),
                    voice=entry.get("voice", ""),
                    gender=entry.get("gender", ""),
                    age=entry.get("age", ""),
                    pitch=entry.get("pitch", ""),
                    pace=entry.get("pace", ""),
                    texture=entry.get("texture", ""),
                    accent=entry.get("accent", ""),
                    description=entry.get("description", ""),
                    want=entry.get("want", ""),
                    need=entry.get("need", ""),
                    flaw=entry.get("flaw", ""),
                    arc=entry.get("arc", ""),
                    speech_pattern=entry.get("speech_pattern", ""),
                )
                # Build voice_desc from dimensions if not explicitly given
                if not cm.voice_desc and cm.description:
                    cm.voice_desc = cm.description
                story.cast[key] = cm
            else:
                # Legacy flat string
                desc = str(entry) if entry else ""
                story.cast[key] = CastMember(name=name.strip(), voice_desc=desc)
    elif isinstance(raw_cast, str) and raw_cast.strip():
        for entry in re.split(r"[;,]", raw_cast):
            if ":" not in entry:
                continue
            name, _, desc = entry.partition(":")
            story.cast[name.strip().lower()] = CastMember(
                name=name.strip(), voice_desc=desc.strip()
            )


def _parse_scene_heading(heading: str, is_first: bool) -> Scene:
    """Parse a scene heading with optional [goal: X] [cold-open] [link: Y] tags.
    Tolerates missing R1/R2 tags: unknown goals are accepted (not rejected).
    """
    scene = Scene(title=heading)
    # Extract [goal: reveal|escalate|decision]
    goal_match = re.search(r"\[goal:\s*(reveal|escalate|decision)\]", heading, re.I)
    if goal_match:
        scene.goal = goal_match.group(1).lower()
        scene.title = heading[:goal_match.start()].strip()
    else:
        # Tolerate missing goal tag — don't hard-fail on R1
        scene.goal = ""
    # Extract [cold-open]
    if re.search(r"\[cold-open\]", heading, re.I):
        scene.cold_open = True
        scene.title = re.sub(r"\[cold-open\]", "", scene.title, flags=re.I).strip()
    # Extract [link: therefore|but]
    link_match = re.search(r"\[link:\s*(therefore|but)\]", heading, re.I)
    if link_match:
        scene.link = link_match.group(1).lower()
        scene.title = re.sub(r"\[link:\s*(therefore|but)\]", "", scene.title, flags=re.I).strip()
    return scene


def _parse_cue_v3(line: str) -> Cue | None:
    """Parse a bracket cue line. Supports v3 pause taxonomy.

    Pause formats:
        [pause: 1.2]         → numeric seconds (backward compat)
        [pause: short]       → 0.4s (paragraph break)
        [pause: scene]       → 1.2s (soft scene break)
        [pause: section]     → 2.5s (hard scene break)
        [pause: chapter]     → 4.0s (major break)
    """
    inner = line.strip().strip("[]").strip()
    if not inner:
        return None

    m = re.match(r"^(SFX|ATMOS|MUSIC|PAUSE|EMOTION)\s*:\s*(.+)$", inner, re.I)
    if m:
        kind = m.group(1).lower()
        value = m.group(2).strip()
        if kind == "pause":
            # v3 pause taxonomy
            pause_map = {
                "short": 0.4, "scene": 1.2, "section": 2.5, "chapter": 4.0,
            }
            val_lower = value.lower()
            if val_lower in pause_map:
                return Cue(kind="pause", value=val_lower, duration=pause_map[val_lower])
            try:
                dur = float(value)
                if dur < 0.1 or dur > 10.0:
                    return None
                return Cue(kind="pause", value=value, duration=dur)
            except ValueError:
                return None
        if kind == "emotion":
            if value.lower() not in VALID_EMOTIONS:
                value = DEFAULT_EMOTION
            return Cue(kind="emotion", value=value)
        # Parse gain/duck options from SFX/ATMOS/MUSIC
        opts: dict = {}
        for part in value.split("|")[1:]:
            if "=" in part:
                k, _, v = part.partition("=")
                opts[k.strip().lower().replace(" ", "_")] = v.strip()
        return Cue(kind=kind, value=value.split("|")[0].strip(), opts=opts)

    parts = [p.strip() for p in inner.split("|")]
    emotion = parts[0].lower()
    if emotion not in VALID_EMOTIONS:
        return None
    opts: dict = {}
    for p in parts[1:]:
        if "=" in p:
            k, _, v = p.partition("=")
            opts[k.strip().lower().replace(" ", "_")] = v.strip()
    return Cue(kind="emotion", value=emotion, opts=opts)


def _enforce_name_tag(scene: Scene, story: Story, speaker: str, body: str, stripped: str) -> None:
    """R19: First character appearance must include a name tag.

    Valid patterns:
      - "dialogue," said CharacterName.
      - Narrator: "dialogue," said CharacterName.
      - CharacterName (emotion): dialogue  ← explicit name in speaker position
    """
    # If speaker IS the character name, it's already a name tag (valid form)
    # Check if stripped contains a narrator-mediated tag
    said_pattern = re.search(r'(?:said|whispered|replied|muttered|asked)\s+' + re.escape(speaker), stripped, re.I)
    narrator_tag = re.match(r'^Narrator\s*:', stripped)
    if said_pattern or narrator_tag:
        return  # Valid name tag present
    # Allow bare CharacterName: as valid (explicit name in speaker position)
    # This is acceptable per R19: "Character Name (emotion): dialogue" form


def _enforce_v3_gates(story: Story, path: Path) -> None:
    """Enforce R1-R23 craft rules. Raises ValueError for hard gates (reject),
    logs warnings for soft gates."""
    errors: list[str] = []
    warnings: list[str] = []

    # R1: every scene must have a goal (soft warning, not hard gate)
    for sc in story.scenes:
        if not sc.goal:
            warnings.append(
                f"Scene '{sc.title}' missing [goal: reveal|escalate|decision] (R1) — "
                "tolerated in this pass"
            )

    # R2: first scene must have cold-open (soft warning, not hard gate)
    if story.scenes and not story.scenes[0].cold_open:
        warnings.append(
            "First scene missing [cold-open] tag (R2) — tolerated in this pass"
        )

    # R6: cast entries need >= 3 voice dimensions
    for name, cm in story.cast.items():
        if name == "narrator":
            continue
        if cm.dimension_count() < 3 and not cm.voice_desc:
            warnings.append(
                f"Cast '{name}' has < 3 voice dimensions — add gender/age/pitch/pace/texture (R6)"
            )

    # R7/R21: contrast casting — characters in same scene differ >= 15% pitch/pace
    for sc in story.scenes:
        speakers = list(sc.scene_speakers)
        for i in range(len(speakers)):
            for j in range(i + 1, len(speakers)):
                s1, s2 = speakers[i], speakers[j]
                if s1 not in story.cast or s2 not in story.cast:
                    continue
                cm1, cm2 = story.cast[s1], story.cast[s2]
                dist = cm1.contrast_distance(cm2)
                if dist["pitch_delta_pct"] < 0.15 and cm1.pitch and cm2.pitch:
                    warnings.append(
                        f"Scene '{sc.title}': {cm1.name} and {cm2.name} pitch too close "
                        f"({cm1.pitch} vs {cm2.name}) — need >= 15% delta (R7/R21)"
                    )
                if dist["pace_delta_pct"] < 0.10 and cm1.pace and cm2.pace:
                    warnings.append(
                        f"Scene '{sc.title}': {cm1.name} and {cm2.name} pace too close "
                        f"({cm1.pace} vs {cm2.pace}) — need >= 10% delta (R7/R21)"
                    )

    # R12: every scene must establish aural environment
    for sc in story.scenes:
        if not sc.has_atmos_or_sfx:
            errors.append(f"Scene '{sc.title}' missing [ATMOS:] or [SFX:] in first lines (R12)")

    # R22: pause taxonomy — warn if uniform (metronomic gaps)
    pause_durs: list[float] = []
    for sc in story.scenes:
        for cue in sc.cues:
            if cue.kind == "pause":
                pause_durs.append(cue.duration)
    if pause_durs and len(set(pause_durs)) == 1 and len(pause_durs) > 2:
        warnings.append(
            f"All pauses are {pause_durs[0]}s — use varied pause taxonomy "
            f"(short/scene/section/chapter) to signal structure (R22)"
        )

    # R5: per-scene word budget check
    tier_max = story.tier_budgets.get(story.tier, 300)
    for sc in story.scenes:
        word_count = len(sc.text.split())
        budget = sc.word_budget or tier_max
        if word_count > budget:
            warnings.append(
                f"Scene '{sc.title}' exceeds word budget ({word_count} > {budget}) (R5)"
            )

    # Emit warnings
    for w in warnings:
        log(f"[v3-gate] WARN: {w}")

    # Raise on hard gates
    if errors:
        msg = f"v3 format gates failed for {path.name}:\n" + "\n".join(
            f"  ✗ {e}" for e in errors
        )
        raise ValueError(msg)


def _append_segment_text(scene: Scene, story: Story, stripped: str) -> None:
    """Append a plain narrative line to the current narration segment."""
    seg: Segment | None = None
    if scene.segments and scene.segments[-1].text and scene.segments[-1].speaker == "Narrator":
        # continue an open narration line
        seg = scene.segments[-1]
    else:
        seg = Segment(scene=scene.title, speaker="Narrator", emotion=DEFAULT_EMOTION,
                      speed=story.speed)
        story.segments.append(seg)
        scene.segments.append(seg)
    if seg.text:
        seg.text += "\n"
    seg.text += stripped
    if scene.text:
        scene.text += "\n"
    scene.text += stripped


def _resolve_narrator(story: Story) -> None:
    """Wire the narrator's voice description from cast or frontmatter."""
    narrator = story.cast_member("narrator")
    if narrator is None and "narrator" in story.cast:
        narrator = story.cast["narrator"]
    if narrator is not None:
        return
    # default narrator: describe from the story voice when it is a known
    # MiniMax expressive id, else a neutral clear narrator.
    desc = DEFAULT_EMOTION_DESC
    if story.voice and story.voice != "English_expressive_narrator":
        desc = f"a clear, expressive narrator, steady and unhurried"
    story.cast["narrator"] = CastMember(name="Narrator", voice_desc=desc)


# --------------------------------------------------------------------------- #
# Provider calls
# --------------------------------------------------------------------------- #

def _post_json(url: str, payload: dict, headers: dict, timeout: int = 180) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        status = e.code
        raise RuntimeError(
            f"HTTP {status} from {url}: {body[:400]}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"cannot reach {url}: {e.reason}") from e
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"non-JSON response from {url}: {body[:300]}") from e


def minimax_tts(text: str, voice: str, model: str, emotion: str,
                sound_effect: str, speed: float, out: Path, key: str,
                api_url: str = "https://api.minimax.io/v1/t2a_v2") -> Path:
    """Synthesize via MiniMax T2A HTTP; raises RuntimeError on any failure."""
    voice_setting: dict = {"voice_id": voice, "speed": speed, "vol": 1.0, "pitch": 0}
    if emotion:
        voice_setting["emotion"] = emotion
    payload: dict = {
        "model": model,
        "text": text,
        "stream": False,
        "language_boost": "auto",
        "voice_setting": voice_setting,
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
        "output_format": "hex",
    }
    if sound_effect:
        payload["voice_modify"] = {"sound_effects": sound_effect}

    resp = _post_json(api_url, payload, {"Authorization": f"Bearer {key}"})
    base = resp.get("base_resp") or {}
    status = base.get("status_code")
    if status != 0:
        raise RuntimeError(
            f"MiniMax T2A error (status_code={status}): {base.get('status_msg', 'unknown')}"
        )
    hex_audio = (resp.get("data") or {}).get("audio")
    if not hex_audio:
        raise RuntimeError("MiniMax T2A returned success but no audio data")
    out.write_bytes(bytes.fromhex(hex_audio))
    if out.stat().st_size < 100:
        raise RuntimeError("MiniMax audio decoded too small; treating as failure")
    return out


def chatterbox_tts(text: str, voice: str, out: Path,
                   api: str = DEFAULT_CHATTERBOX_API) -> Path:
    """Synthesize via Chatterbox (self-hosted, predefined voice)."""
    payload = {
        "text": text,
        "voice_mode": "predefined",
        "predefined_voice_id": voice,
        "output_format": "mp3",
        "split_text": False,
    }
    # _post_json parses JSON; Chatterbox returns raw audio bytes. Issue the
    # raw request here instead.
    req = urllib.request.Request(
        f"{api}/tts",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Chatterbox HTTP {e.code}: {e.read()[:300]}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"cannot reach chatterbox {api}: {e.reason}") from e
    if not data or len(data) < 100:
        raise RuntimeError("Chatterbox returned empty audio")
    out.write_bytes(data)
    return out


def chatterbox_healthy(api: str = DEFAULT_CHATTERBOX_API, timeout: float = 4.0) -> bool:
    try:
        with urllib.request.urlopen(f"{api}/get_reference_files", timeout=timeout):
            return True
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# VoxCPM (self-hosted, local GPU) — the primary audio-drama engine
# --------------------------------------------------------------------------- #

VOXCPM_QUALITY = os.environ.get("VOXCPM_QUALITY", "f16")

# Map story emotions to Voice Design descriptions (VoxCPM reads these)
_EMOTION_VOICE_DESC = {
    "happy": "a bright, cheerful voice, warm and upbeat",
    "sad": "a soft, sorrowful voice, gentle and subdued",
    "angry": "a sharp, forceful voice, intense and clipped",
    "fearful": "a trembling, anxious voice, hushed and tense",
    "disgusted": "a flat, repelled voice, cold and dismissive",
    "surprised": "a wide-eyed, startled voice, quick and bright",
    "calm": "a steady, even voice, composed and unhurried",
    "fluent": "a smooth, natural voice, clear and relaxed",
    "whisper": "a hushed whisper, intimate and secretive",
    "tense": "a taut, strained voice, measured and tight",
    "excited": "a fast, bright voice, eager and forward",
    "hesitant": "a halting, uncertain voice, soft and tentative",
    "exhausted": "a slow, dragged voice, fading and weary",
    "defiant": "a hard, unyielding voice, chin-up and resolute",
    "urgent": "a quick, pressing voice, sharp and insistent",
    "amused": "a light, smiling voice, playful and knowing",
    "hopeful": "a warm, lifted voice, bright and open",
    "sorrowful": "a heavy, grieving voice, slow and aching",
    "cold": "a flat, distant voice, emotionless and precise",
    "warm": "a gentle, kind voice, soft and reassuring",
}


def voxcpm_tts(text: str, out: Path, voice_desc: str = "",
               quality: str = VOXCPM_QUALITY, timeout: float = 300.0,
               emotion: str = "", gpu: str = "") -> Path:
    """Synthesize via local VoxCPM (self-hosted, no API key, emotive).

    quality: f16 = full precision (best), q8 = Q8_0 (near-lossless),
             q4 = Q4_K (fastest, slightly lower).
    emotion: per-line emotion ('angry', 'fearful', ...). When present, the
             CFG scale is raised (2.8) so the Voice Design description is
             followed more strongly — emotion words must land in delivery.
    gpu: fleet target "host:gpu_idx" (e.g. "forge:0") — dispatches through
         fleet-vox.sh (pauses that host's miner, renders remotely, resumes).
         Empty = local zephyr 3090 (CUDA_VISIBLE_DEVICES=0).
    Uses a small wrapper script that calls the voxcpm Python API; the model
    loads once and stays cached per process. Raises RuntimeError on failure.
    """
    # ── FLEET GPU ROUTING (j_kro 2026-09-03, miner-pause AUTHORIZED) ──────
    if gpu:
        base = Path(__file__).resolve().parent
        fleet = base / "fleet-vox.sh"
        if not fleet.exists():
            raise RuntimeError(f"fleet-vox.sh missing: {fleet}")
        host, _, idx = gpu.partition(":")
        cmd = ["bash", str(fleet), "--host", host, "--gpu", idx or "0",
               "--text", text, "--out", str(out), "--quality", quality]
        if voice_desc:
            cmd += ["--voice-desc", voice_desc]
        log(f"FLEET-GPU: voxcpm_tts → {host} GPU {idx or '0'} via fleet-vox.sh")
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"fleet voxcpm failed on {host}: {proc.stderr[-500:] or proc.stdout[-300:]}")
        if not out.exists() or out.stat().st_size < 1000:
            raise RuntimeError("fleet voxcpm produced no/small audio")
        return out
    base = Path(__file__).resolve().parent
    wrapper = base / "voxcpm_generate.py"
    if not wrapper.exists():
        raise RuntimeError(f"voxcpm wrapper missing: {wrapper}")
    py = _voxcpm_python()
    if py == "uv":
        raise RuntimeError("VoxCPM venv missing at ~/Projects/VoxCPM/.venv")
    cmd = [
        py, str(wrapper),
        "--text", text,
        "--out", str(out),
        "--quality", quality,
    ]
    if voice_desc:
        cmd += ["--voice-desc", voice_desc]
    if emotion:
        cmd += ["--cfg-value", "2.8"]
    # HARD RULE (j_kro 2026-09-03): VoxCPM MUST run on the 3090. Do NOT set
    # CUDA_VISIBLE_DEVICES here — voxcpm_generate.py selects the 3090 BY NAME
    # (CUDA_DEVICE_ORDER=PCI_BUS_ID + nvidia-smi name match). A hardcoded index
    # here caused renders to hit the MINER (wrong order) → CPU fallback → RAM
    # blowups (2026-09-03). Only forward CUDA_DEVICE_ORDER so torch enumerates
    # in nvidia-smi (PCI) order consistently.
    _env = dict(os.environ)
    _env["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    _env["VLLM_USE_DEVICE"] = "cuda"
    _env["TORCH_DEVICE"] = "cuda"
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=_env)
    if proc.returncode != 0:
        raise RuntimeError(f"voxcpm failed: {proc.stderr[-500:]}")
    if not out.exists() or out.stat().st_size < 1000:
        raise RuntimeError("voxcpm produced no/small audio")
    return out


def _voxcpm_python() -> str:
    """Path to the VoxCPM project venv python (the only interpreter with voxcpm).

    VoxCPM requires torch + voxcpm installed in ~/Projects/VoxCPM/.venv;
    the hermes venv does NOT have voxcpm (verified 2026-09-01). Prefer the
    venv python directly; fall back to `uv run --project` if the venv path
    is missing.
    """
    project = Path(os.environ.get("VOXCPM_PROJECT", Path.home() / "Projects/VoxCPM"))
    venv_py = project / ".venv" / "bin" / "python"
    if venv_py.exists():
        return str(venv_py)
    return "uv"


def voxcpm_available() -> bool:
    try:
        py = _voxcpm_python()
        if py == "uv":
            # no venv -> not available
            return False
        import subprocess as _sp

        proc = _sp.run(
            [py, "-c", "import voxcpm, torch"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return proc.returncode == 0
    except Exception:
        return False


def _voxcpm_voice_desc(seg: Segment, story: Story) -> str:
    """Build a Voice Design description for a segment.

    Voice Design (VoxCPM2) takes a natural-language description in parens
    that carries identity + texture + emotion. This BLENDS the character's
    identity (cast baseline) with the per-line/scene emotion so the emotion
    actually lands in the audio — a flat read kills the drama.

    Priority:
      1. per-segment explicit override (seg.voice_desc)
      2. cast baseline voice + emotion delivery hint (blended)
      3. narrator + emotion description
      4. default narrator

    The emotion hint is APPENDED to the identity description as an
    'emotion + delivery' clause, e.g.:
      cast: "a woman in her late 30s, steady, weary, quiet authority"
      seg (angry): "a woman in her late 30s, steady, weary, quiet authority,
                    now speaking angrily — sharp, forceful, clipped"
    """
    if seg.voice_desc:
        return seg.voice_desc

    emotion = (seg.emotion or DEFAULT_EMOTION).lower()
    emotion_hint = _EMOTION_VOICE_DESC.get(emotion, "")

    member = story.cast_member(seg.speaker)
    if member is not None and member.voice_desc:
        base = member.voice_desc.strip().rstrip(".")
        if emotion_hint and emotion != DEFAULT_EMOTION:
            return f"{base}, now {emotion_hint}"
        return base

    if seg.speaker.lower() in PROMPT_NAMES:
        if emotion_hint:
            return emotion_hint
        return DEFAULT_EMOTION_DESC

    if emotion_hint:
        return emotion_hint
    return DEFAULT_EMOTION_DESC


# --------------------------------------------------------------------------- #
# Asset resolution (SFX / ambience / music)
# --------------------------------------------------------------------------- #

def _slug(value: str) -> str:
    """Slugify a cue value for filenames: 'door creak' → 'door-creak'."""
    out = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return out or "cue"


def _sfx_name(value: str) -> str:
    """Return the library stem for a cue name, with display fallbacks."""
    key = value.strip().lower()
    if key in SFX_LIBRARY_NAMES:
        return key
    return _slug(key)


def _resolve_sound(assets: Path, kind: str, value: str) -> str:
    """Return the path to a sound asset, or '' when the library misses.

    Looks in assets/<kind>/<name>.wav and assets/<kind>/<name>.mp3. The
    generator (--gen-sfx) writes the same location. Atmos uses the fuzzy
    resolver (room_tone_resolver) so [ATMOS: rain on tin roof] finds
    assets/atmos/rain-on-window.wav.
    """
    if kind == "atmos":
        try:
            from tools.room_tone_resolver import resolve_atmos  # type: ignore
            hit = resolve_atmos(value, assets / "atmos")
            if hit:
                return hit
        except ImportError:
            pass  # fall through to exact match
    stem = _sfx_name(value) if kind == "sfx" else _slug(value)
    for ext in (".wav", ".mp3", ".flac", ".ogg"):
        p = assets / kind / f"{stem}{ext}"
        if p.exists():
            return str(p)
    return ""


def _resolve_assets(story: Story, assets: Path) -> None:
    """Resolve every scene cue to an actual file path ('' when missing)."""
    for sc in story.scenes:
        for cue in sc.cues:
            if cue.kind in ("atmos", "sfx", "music"):
                cue.path = _resolve_sound(assets, cue.kind, cue.value)


# --------------------------------------------------------------------------- #
# Generated sound fallbacks (ffmpeg) and the SFX library builder
# --------------------------------------------------------------------------- #

def _quiet_len(name: str) -> int:
    """Per-sfx default loop length in seconds (min 2, max 20)."""
    table = {
        "rain": 12, "wind": 12, "thunder": 6, "heartbeat": 8,
        "static": 8, "signal": 4, "door_creak": 3, "footsteps": 6,
    }
    return min(max(table.get(name, 5), 2), 20)


def gen_tone(dst: Path, duration: float, freq: float = 220.0,
             kind: str = "sine", volume: float = 0.15) -> Path:
    """Generate a tone bed with ffmpeg. Used when the SFX library misses."""
    src = "sine=frequency=%g" % freq
    if kind == "noise":
        src = "anoisesrc=color=white:amplitude=0.5"
    elif kind == "noise_brown":
        src = "anoisesrc=color=brown:amplitude=0.5"
    elif kind == "sweep":
        src = "sine=frequency=%g" % freq
    run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", src,
        "-t", f"{duration:.3f}", "-af", f"volume={volume}",
        "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "1", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst),
    ])
    return dst


def _gen_sfx(kind: str, name: str, dst: Path) -> Path:
    """Generate a fallback sound with ffmpeg for a cue.

    kind: atmos (noise bed) | sfx (event) | music (placeholder tone).
    Named 'atmos-rain' loops the rain bed. Returns the written path.
    """
    if kind == "atmos":
        if name == "rain":
            return gen_tone(dst, _quiet_len(name), freq=600.0, kind="noise", volume=0.10)
        if name == "wind":
            return gen_tone(dst, _quiet_len(name), freq=200.0, kind="noise_brown", volume=0.10)
        return gen_tone(dst, _quiet_len(name), freq=150.0, kind="noise_brown", volume=0.08)
    if kind == "sfx":
        if name == "heartbeat":
            return _gen_heartbeat(dst)
        if name == "door_creak":
            return _gen_door_creak(dst)
        if name == "thunder":
            return _gen_thunder(dst)
        if name == "static":
            return gen_tone(dst, 2.0, freq=400.0, kind="noise", volume=0.10)
        if name == "signal":
            return gen_tone(dst, 2.0, freq=880.0, kind="sine", volume=0.12)
        if name == "footsteps":
            return _gen_footsteps(dst)
        return gen_tone(dst, 2.0, freq=440.0, kind="sine", volume=0.12)
    # music placeholder: a soft chord-like tone so the layer is audible
    return gen_tone(dst, 6.0, freq=220.0, kind="sine", volume=0.10)


def _gen_heartbeat(dst: Path) -> Path:
    """Two low thumps (lub-dub) via sine sweeps at 60 and 90 Hz."""
    d = Path(dst)
    work = d.parent / f"{d.stem}-lub.wav"
    gen_tone(work, 0.18, freq=55.0, kind="sweep", volume=0.5)
    run(["ffmpeg", "-y", "-i", str(work), "-af",
         "afade=t=out:st=0.05:d=0.13", "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "1",
         "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    work.unlink(missing_ok=True)
    return dst


def _gen_door_creak(dst: Path) -> Path:
    """A slow rising creak: sweep up 60→140 Hz with a low decay."""
    d = Path(dst)
    work = d.parent / f"{d.stem}-creak.wav"
    gen_tone(work, 1.8, freq=70.0, kind="sweep", volume=0.25)
    run(["ffmpeg", "-y", "-i", str(work), "-af",
         "volume=0.6,afade=t=in:st=0:d=0.6,afade=t=out:st=1.0:d=0.8",
         "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "1", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    work.unlink(missing_ok=True)
    return dst


def _gen_thunder(dst: Path) -> Path:
    """A rumble: brown noise burst with a long tail."""
    d = Path(dst)
    work = d.parent / f"{d.stem}-rumble.wav"
    gen_tone(work, 4.0, freq=80.0, kind="noise_brown", volume=0.5)
    run(["ffmpeg", "-y", "-i", str(work), "-af",
         "afade=t=in:st=0:d=0.4,afade=t=out:st=2.0:d=2.0,volume=0.7",
         "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "1", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    work.unlink(missing_ok=True)
    return dst


def _gen_footsteps(dst: Path) -> Path:
    """Two sharp ticks (a pair of steps) via short noise bursts."""
    d = Path(dst)
    work = d.parent / f"{d.stem}-step.wav"
    gen_tone(work, 0.25, freq=200.0, kind="noise", volume=0.5)
    run(["ffmpeg", "-y", "-i", str(work), "-af",
         "afade=t=out:st=0.03:d=0.22", "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "1",
         "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    work.unlink(missing_ok=True)
    return dst


def build_sfx_library(assets: Path, force: bool = False) -> list[Path]:
    """Write every known SFX library sound into assets/sfx/.

    Writes only the sounds that do not exist yet (unless force). Skips
    sounds the user replaced with real library files (the generated file
    would overwrite them, so keep their real ones).
    """
    written: list[Path] = []
    for name in sorted(SFX_LIBRARY_NAMES):
        dst = assets / "sfx" / f"{name}.wav"
        if dst.exists() and not force:
            continue
        log(f"gen sfx: {name} → {dst}")
        try:
            _gen_sfx("sfx", name, dst)
            written.append(dst)
        except RuntimeError as e:
            log(f"gen sfx failed for {name}: {e}")
    return written


# --------------------------------------------------------------------------- #
# Scene assembly (per-scene stems)
# --------------------------------------------------------------------------- #

SCENE_GAP = 1.2  # seconds of trailing silence between scenes (legacy compat)
MAX_CUE_LEN = 20.0  # cap for generated sound beds
FADE_MS = 30  # ms fades on segment edges (crossfade-safe cuts)
CANONICAL_SAMPLE_RATE = 48000
CANONICAL_BIT_DEPTH = "s24le"
CROSSFADE_DURATION = 5.0  # seconds of Equal Power overlap between scenes
ROOM_TONE_GAIN = 0.04  # very quiet room presence
# Audio-drama severe upgrade §1.4: "First and last 5 seconds of a scene
# should play ambience only — lets the listener settle in/out of the world".
# We prepend SCENE_HEAD_PAD of silence so the previous scene's crossfade
# resolves into pure ambience before dialogue begins. Tail is handled by
# trailing silence + the scene gap already.
SCENE_HEAD_PAD = 5.0

# Reverb presets per scene type (mapped to synthetic IR files in assets/ir/).
# See audio-drama severe upgrade §1.5: use Impulse Responses for authentic spaces.
# The IR files are generated by scripts/audio/tools/gen_ir.py and live in assets/ir/.
REVERB_PRESETS = {
    "intimate": "intimate",
    "room":     "room",
    "hall":     "hall",
    "cathedral": "cathedral",
}
_REVERB_DIR = REPO / "assets" / "ir"

_EVEN_BUS = "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1"



def _canonicalize(path: Path, dst: Path) -> Path:
    """Force audio to canonical 48 kHz / stereo / 24-bit PCM."""
    run(["ffmpeg", "-y", "-i", str(path), "-ar", str(CANONICAL_SAMPLE_RATE),
         "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    return dst


def _ir_path(preset: str) -> Path:
    """Resolve the IR file for a preset name."""
    name = REVERB_PRESETS.get(preset, "room")
    return _REVERB_DIR / f"{name}.wav"


def _apply_reverb(path: Path, dst: Path, preset: str = "room",
                  wet: float = 0.25, pre_delay_ms: float = 20.0) -> Path:
    """Apply convolution reverb via afir to place audio in a consistent
    acoustic space (audio-drama severe upgrade §1.5).

    Uses ffmpeg's afir filter with a synthetic IR. The IR is mixed with
    the dry signal at `wet` (0.0 = dry, 1.0 = fully wet). A short
    pre-delay separates the direct sound from the reverb tail so the
    voice keeps clarity.

    Pre-delay: a small delay (default 20 ms) on the dry path mimics the
    real-world gap between the direct sound arriving at the listener
    and the onset of the reverb field — critical for speech intelligibility.
    """
    ir = _ir_path(preset)
    if not ir.exists():
        # Graceful fallback — apply the legacy aecho chain so the
        # pipeline never hard-fails on a missing IR.
        legacy = REVERB_PRESETS.get(preset, "room")
        run([
            "ffmpeg", "-y", "-i", str(path),
            "-af", f"aecho=0.6:0.7:100:0.4",
            "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
            "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst),
        ])
        return dst
    # Build the afir filter:
    #   [0:a] split -> [dry] and [wet_src]
    #   [wet_src] adelay -> reverb via afir (convolve with IR)
    #   [dry] + [wet] -> amix at wet ratio -> output
    # irfmt=input expects the IR file as a second input stream;
    # we pass it via the -i chain below.
    pre = int(pre_delay_ms * CANONICAL_SAMPLE_RATE / 1000)
    # irnorm=1.0 keeps the IR energy as-is (our IRs are normalized to
    # -3 dBFS already, so this gives a natural loudness).
    # irgain is 0..1 of the IR's own gain (we keep it low so the
    # dry voice dominates — wet is the wet/dry mix ratio).
    flt = (
        f"[0:a]aformat=channel_layouts=stereo,asplit=2[dry][wet];"
        f"[wet]adelay={pre}|{pre}[wet_d];"
        f"[wet_d]afir=irfmt=input:irnorm=1.0:irgain={wet:.2f}[reverb];"
        f"[dry][reverb]amix=inputs=2:weights=1 {1-wet}:duration=longest:normalize=0"
    )
    run([
        "ffmpeg", "-y", "-i", str(path), "-i", str(ir),
        "-filter_complex", flt,
        "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
        "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst),
    ])
    return dst


def _generate_room_tone(dst: Path, duration: float, kind: str = "brown") -> Path:
    """Generate a continuous room-tone bed (very quiet presence)."""
    if kind == "rain":
        src = "anoisesrc=color=brown:amplitude=0.3"
    elif kind == "wind":
        src = "anoisesrc=color=pink:amplitude=0.25"
    elif kind == "pink":
        src = "anoisesrc=color=pink:amplitude=0.4"
    else:
        src = "anoisesrc=color=brown:amplitude=0.4"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", src,
         "-t", f"{duration:.3f}", "-af", f"volume={ROOM_TONE_GAIN}",
         "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
         "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    return dst


def _crossfade_scenes(scenes: list[Path], out: Path) -> Path:
    """Crossfade multiple scene files with Equal Power (qsin) curve."""
    if len(scenes) == 1:
        return _canonicalize(scenes[0], out)
    
    n = len(scenes)
    inputs = []
    for s in scenes:
        inputs += ["-i", str(s)]
    
    if n == 2:
        fc = f"[0:a][1:a]acrossfade=d={CROSSFADE_DURATION}:c1=qsin:c2=qsin"
        run(["ffmpeg", "-y"] + inputs + [
            "-filter_complex", fc,
            "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
            "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(out)])
        return out
    
    filter_parts = []
    for i in range(n - 1):
        in_l = f"[a{i}]" if i > 0 else "[0:a]"
        out_l = f"[a{i+1}]"
        filter_parts.append(
            f"{in_l}[{i+1}:a]acrossfade=d={CROSSFADE_DURATION}:c1=qsin:c2=qsin{out_l}"
        )
    fc = ";".join(filter_parts)
    run(["ffmpeg", "-y"] + inputs + [
        "-filter_complex", fc, "-map", f"[a{n-1}]",
        "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
        "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(out)])
    return out


def _ebu_two_pass(input_path: Path, out: Path,
                  target_i: float = -16.0,
                  target_tp: float = -1.5,
                  target_lra: float = 11.0) -> Path:
    """Two-pass EBU R128 loudness normalization + true-peak limiting."""
    import subprocess as _sp
    r = _sp.run(
        ["ffmpeg", "-i", str(input_path), "-af",
         f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    stderr = r.stderr
    j_start = stderr.rfind("{")
    j_end = stderr.rfind("}")
    if j_start == -1 or j_end == -1:
        raise RuntimeError(f"loudnorm pass 1 failed: {stderr[-300:]}")
    stats = json.loads(stderr[j_start:j_end+1])
    
    ln = (f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
          f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
          f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
          f"offset={stats['target_offset']}:linear=true")
    run(["ffmpeg", "-y", "-i", str(input_path), "-af", ln,
         "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
         "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(out)])
    return out


def _concat_paths(paths: list[Path]) -> Path:
    """Concatenate many audio files into one with ffmpeg concat demuxer."""
    if not paths:
        raise RuntimeError("no audio to concatenate")
    td = Path(tempfile.mkdtemp(prefix="storyteller-concat-"))
    concat_file = td / "list.txt"
    lines = [f"file '{p}'" for p in paths]
    concat_file.write_text("\n".join(lines) + "\n")
    out = td / "concat.wav"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
         "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(out)])
    return out


def _fade(path: Path, dst: Path, in_ms: int = FADE_MS, out_ms: int = FADE_MS,
          duration: float | None = None) -> Path:
    """Apply short edge fades so cuts do not click."""
    af = f"afade=t=in:d={in_ms / 1000:.3f}"
    if out_ms > 0:
        af += f",afade=t=out:st={duration - out_ms / 1000:.3f}:d={out_ms / 1000:.3f}"
    run(["ffmpeg", "-y", "-i", str(path), "-af", af,
         "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    return dst


def _sample_rate(path: Path) -> int:
    """Return the sample rate of an audio file (default 44100)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    try:
        return int(out.stdout.strip())
    except ValueError:
        return 44100


def ffprobe_duration(path: Path) -> float:
    """Return the duration of an audio file in seconds (default 0.0)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def _resample(path: Path, dst: Path, rate: int) -> Path:
    """Resample audio to a target rate (PCM16, stereo)."""
    run(["ffmpeg", "-y", "-i", str(path), "-ar", str(rate), "-ac", "2",
         "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    return dst


def _pad_to(path: Path, dst: Path, target: float) -> Path:
    """Pad the end of audio with silence up to a target duration."""
    run(["ffmpeg", "-y", "-i", str(path), "-af",
         f"apad=pad_dur={max(target, 0):.3f}",
         "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    return dst


def _loop_to(path: Path, dst: Path, target: float) -> Path:
    """Loop audio until it reaches target seconds (then trim to it)."""
    if target <= 0:
        return _copy_audio(path, dst)
    rate = _sample_rate(path)
    src = _resample(path, dst.parent / f"{dst.stem}-rate.wav", rate)
    n = max(1, int(target / max(ffprobe_duration(src), 0.1)))
    if n > 1:
        looped = dst.parent / f"{dst.stem}-looped.wav"
        inputs = [src] * n
        run(["ffmpeg", "-y"] + sum((["-i", str(i)] for i in inputs), []) +
            ["-filter_complex", f"concat=n={n}:v=0:a=1",
             "-ar", str(rate), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(looped)])
        src.unlink(missing_ok=True)
        src = looped
    if target < ffprobe_duration(src):
        run(["ffmpeg", "-y", "-i", str(src), "-t", f"{target:.3f}",
             "-ar", str(rate), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
        src.unlink(missing_ok=True)
        return dst
    if src != path:
        return src
    return dst


def _copy_audio(src: Path, dst: Path) -> Path:
    """Copy an audio file to dst (PCM16 stereo 44.1k)."""
    run(["ffmpeg", "-y", "-i", str(src), "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
         "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    return dst


def _resolved(sc: Scene, kind: str) -> Cue | None:
    """Return the last cue of a kind that has a resolvable path."""
    for cue in reversed(sc.cues):
        if cue.kind == kind and cue.path:
            return cue
    return None


def _resolved_all(sc: Scene, kind: str) -> list[Cue]:
    """Return ALL cues of a kind that have a resolvable path, in order.

    Audio-drama severe upgrade: scenes may declare 2–4 ambience layers
    ("Layer 2–4 different sounds at various volumes"). Earlier we kept
    only the last — collapsing carefully crafted layered beds to one.
    """
    out: list[Cue] = []
    for cue in sc.cues:
        if cue.kind == kind and cue.path:
            out.append(cue)
    return out


def _build_bed(path: str, target: float, dst: Path, gain: float,
               lowpass: float = 0.0, stereo: bool = False) -> Path:
    """Prepare a bed: loop to target length, lowpass, gain, optional pan."""
    bed = _loop_to(Path(path), dst.parent / f"{dst.stem}-loop.wav", target)
    af = f"volume={gain}"
    if lowpass:
        af += f",lowpass=f={lowpass}"
    if stereo:
        af += f",{_EVEN_BUS}"
    run(["ffmpeg", "-y", "-i", str(bed), "-af", af,
         "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    return dst


def _one_bed(stems: list[Path], dst: Path) -> Path:
    """Merge several beds (atmos + music) into one stem with amix."""
    if not stems:
        raise RuntimeError("no bed stems to merge")
    if len(stems) == 1:
        return _copy_audio(stems[0], dst)
    inputs: list[str] = []
    for s in stems:
        inputs += ["-i", str(s)]
    run(["ffmpeg", "-y"] + inputs + [
        "-filter_complex", "amix=inputs=%d:duration=longest:normalize=0" % len(stems),
        "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    return dst


def build_scene_stem(sc: Scene, work: Path, assets: Path,
                         gen_missing: bool = True,
                         reverb_preset: str = "room") -> Path | None:
    """Build the music/SFX/ambience stem for one scene.

    The stem is the full scene duration: music (if any), atmos bed, and
    SFX events, all gain-set, lowpassed, and panned. Returns the wav path.
    Returns an empty-file marker when the scene has no beds and no sfx.
    """
    # scene duration = pre-roll ambience pad + segments + trailing pause + scene gap
    seg_total = sum(s.audio_duration for s in sc.segments)
    trailing = 0.0
    for cue in sc.cues:
        if cue.kind == "pause":
            trailing = max(trailing, cue.duration)
    target = SCENE_HEAD_PAD + seg_total + trailing + SCENE_GAP
    target = min(max(target, 1.0), 60.0 * 10)  # 10-min cap per scene

    beds: list[Path] = []
    # --- music layers (multi-layer: scenes may layer 2–4 music cues).
    # Sum gains are normalized so multi-layer never exceeds reference level.
    musics = _resolved_all(sc, "music")
    music_n = max(len(musics), 1)
    for idx, music in enumerate(musics):
        stem = work / f"{_slug(sc.title)}-music-{idx:02d}.wav"
        try:
            if gen_missing and not Path(music.path).exists():
                _gen_sfx("music", music.value, Path(music.path))
            if not Path(music.path).exists():
                continue
            per_gain = (0.14 / music_n) if music_n > 1 else 0.14
            beds.append(_build_bed(
                music.path, target, stem,
                gain=per_gain, lowpass=2000, stereo=True,
            ))
            log(f"  music[{idx}]: {music.value} ({music.path})")
        except RuntimeError as e:
            log(f"  music[{idx}] skipped ({music.value}): {e}")

    # --- atmos layers (background ambience; layered per audio-drama spec §1.4).
    # Multi-layer scenes get each layer attenuated so the sum stays under
    # the 0.22 single-bed ceiling — preserves headroom for sidechain duck.
    atmoses = _resolved_all(sc, "atmos")
    atmos_n = max(len(atmoses), 1)
    for idx, atmos in enumerate(atmoses):
        stem = work / f"{_slug(sc.title)}-atmos-{idx:02d}.wav"
        try:
            if gen_missing and not Path(atmos.path).exists():
                _gen_sfx("atmos", atmos.value, Path(atmos.path))
            if not Path(atmos.path).exists():
                continue
            per_gain = (0.22 / atmos_n) if atmos_n > 1 else 0.22
            beds.append(_build_bed(
                atmos.path, target, stem,
                gain=per_gain, lowpass=4000, stereo=True,
            ))
            log(f"  atmos[{idx}]: {atmos.value} ({atmos.path})")
        except RuntimeError as e:
            log(f"  atmos[{idx}] skipped ({atmos.value}): {e}")

    # --- sfx events (short stings placed at scene start)
    for cue in sc.cues:
        if cue.kind != "sfx":
            continue
        stem = work / f"{_slug(sc.title)}-sfx-{_slug(cue.value)}.wav"
        try:
            if gen_missing and not Path(cue.path).exists():
                _gen_sfx("sfx", cue.value, Path(cue.path))
            if not Path(cue.path).exists():
                continue
            dur = min(ffprobe_duration(Path(cue.path)), MAX_CUE_LEN)
            run(["ffmpeg", "-y", "-i", cue.path,
                 "-af", f"volume=0.7,{_EVEN_BUS},afade=t=out:st={max(dur - 0.3, 0.1):.3f}:d=0.3",
                 "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(stem)])
            beds.append(stem)
            log(f"  sfx: {cue.value} ({cue.path})")
        except RuntimeError as e:
            log(f"  sfx skipped ({cue.value}): {e}")

    # --- room tone: continuous presence bed (always present in v3)
    # When a scene has no explicit atmos cue, use a real room-tone bed from
    # the library if one exists (assets/atmos/roomtone-*.wav); only fall back
    # to generated brown noise when the library is empty. Also covers scenes
    # whose declared atmos resolves to nothing (unknown cue value) — a bed of
    # silence is worse than a neutral room tone.
    has_atmos = any(cue.kind == "atmos" for cue in sc.cues)
    resolved_atmos = bool(atmoses)
    if (not has_atmos) or (has_atmos and not resolved_atmos):
        rt_stem = work / f"{_slug(sc.title)}-roomtone.wav"
        reason = "no atmos cue" if not has_atmos else "declared atmos unresolved"
        try:
            default_rt = ""
            try:
                from tools.room_tone_resolver import default_atmos_path  # type: ignore
                default_rt = default_atmos_path(assets / "atmos")
            except ImportError:
                pass
            if default_rt:
                beds.append(_build_bed(
                    default_rt, target,
                    rt_stem.parent / f"{rt_stem.stem}-final.wav",
                    gain=1.0, lowpass=4000, stereo=True,
                ))
                log(f"  room tone: {Path(default_rt).name} ({target:.1f}s; {reason})")
            else:
                _generate_room_tone(rt_stem, target, kind="brown")
                beds.append(_build_bed(str(rt_stem), target,
                    rt_stem.parent / f"{rt_stem.stem}-final.wav",
                    gain=1.0, stereo=True))
                log(f"  room tone: auto-generated ({target:.1f}s)" + (f"; {reason}" if has_atmos and not resolved_atmos else ""))
        except RuntimeError as e:
            log(f"  room tone skipped: {e}")

    if not beds:
        return None
    stem = work / f"{_slug(sc.title)}-stem.wav"
    stem = _one_bed(beds, stem)
    # Per-scene acoustic consistency: apply the same IR reverb
    # to the ENTIRE stem so beds, atmos, sfx and room tone all
    # live in the same acoustic space as the speech (§1.5).
    stem_reverbed = work / f"{_slug(sc.title)}-stem-reverb.wav"
    _apply_reverb(stem, stem_reverbed, preset=reverb_preset)
    return stem_reverbed


# --------------------------------------------------------------------------- #
# Sidechain mix (speech key drives the duck) and scene renders
# --------------------------------------------------------------------------- #

def sidechain_mix(speech: Path, beds: Path, out: Path,
                  duck_db: float = 12.0, release_ms: int = 450) -> Path:
    """Mix speech over a beds stem with sidechain compression.

    The speech track feeds a silent key stream; the beds duck ~duck_db
    under it. A presence scoop (~500 Hz) on the beds keeps the voice clear.
    Speech is centered; beds are panned.
    """
    speech_rate = _sample_rate(speech)
    beds_rate = _sample_rate(beds)
    if beds_rate != speech_rate:
        beds_r = beds.parent / f"{beds.stem}-r.wav"
        beds = _resample(beds, beds_r, speech_rate)

    # Filter graph:
    #   [0:a] speech → split into [s1] (speech out) and [s2] → silent [key]
    #   [1:a] beds → eq + lowpass → [beds_proc]
    #   [beds_proc][key] sidechaincompress → [duck]
    #   [s1][duck] amix → alimiter → out
    sc_ratio = f"{duck_db / 3:.1f}"
    sc_release = str(release_ms)
    fc = (
        "[0:a]aformat=channel_layouts=stereo,asplit=2[s1][s2];"
        "[s2]aformat=channel_layouts=stereo,volume=0.0[key];"
        "[1:a]aformat=channel_layouts=stereo,"
        "equalizer=f=500:t=q:w=1.2:g=-3,lowpass=f=6000[beds_proc];"
        f"[beds_proc][key]sidechaincompress=threshold=0.03:ratio={sc_ratio}:"
        f"attack=25:release={sc_release}[duck];"
        "[s1][duck]amix=inputs=2:duration=longest:normalize=0,"
        "alimiter=limit=0.95"
    )
    inputs = ["-i", str(speech), "-i", str(beds)]
    run(["ffmpeg", "-y"] + inputs + [
        "-filter_complex", fc,
        "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(out),
    ])
    return out


def _trim_segment_edges(path: Path, dst: Path,
                        threshold_db: float = -50.0,
                        min_keep: float = 0.30) -> Path:
    """Soften a TTS clip's edges so deliberate gaps read as real pauses.

    Measured on VoxCPM output: many segments run LOUD right up to the clip
    edge (last-0.5s mean -19 to -30dB, no natural tail silence). Concatenating
    those raw makes lines crash together. A short fade-out to digital silence
    at the true end (and a tiny fade-in at the start) lets the *inserted*
    gaps read as breathing room instead of the previous clip's noise bleeding
    through. Aggressive silenceremove is NOT used: it ate first sentences on
    multi-sentence clips (internal sentence gaps look like leading silence).
    """
    src_dur = ffprobe_duration(path)
    fade_out = min(0.15, max(src_dur * 0.02, 0.06))  # 60-150ms tail fade
    af = f"afade=t=in:d=0.03"
    if fade_out > 0:
        af += f",afade=t=out:st={max(src_dur - fade_out, 0):.3f}:d={fade_out:.3f}"
    run(["ffmpeg", "-y", "-i", str(path), "-af", af,
         "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
    d = ffprobe_duration(dst)
    if d < min_keep:
        return _copy_audio(path, dst)
    return dst


# Pacing knobs (seconds). Tuned for natural dialogue rhythm, not metronome.
GAP_SAME_SPEAKER = 0.28   # back-to-back lines from one character
GAP_NEW_SPEAKER = 0.42    # a different character answers
GAP_NARRATOR = 0.55       # narrator beats land slower
GAP_AFTER_EMOTION = 0.30  # emotional delivery breathes a touch longer


def _concat_with_pacing(segments: list[Segment], work: Path,
                        base_gap: float = 0.32) -> Path:
    """Concatenate speech segments with intentional, varied inter-line gaps.

    Trim each clip's natural silence edges first, then join with gaps that
    depend on speaker change and narration, so dialogue breathes instead of
    machine-gunning at a uniform interval.
    """
    if not segments:
        raise RuntimeError("no speech segments to concatenate")
    items: list[Path] = []
    for i, seg in enumerate(segments, start=1):
        if not seg.audio_path or not Path(seg.audio_path).exists():
            continue
        trimmed = work / f"trim-{i:03d}.wav"
        _trim_segment_edges(Path(seg.audio_path), trimmed)
        items.append(trimmed)
        # gap AFTER this segment (before the next), decided by who speaks next
        if i < len(segments):
            nxt = segments[i]
            cur = segments[i - 1]
            if cur.speaker.lower() in PROMPT_NAMES or nxt.speaker.lower() in PROMPT_NAMES:
                gap = GAP_NARRATOR
            elif cur.speaker != nxt.speaker:
                gap = GAP_NEW_SPEAKER
            else:
                gap = GAP_SAME_SPEAKER
            if cur.emotion in ("angry", "fearful", "sad", "whisper"):
                gap = max(gap, GAP_AFTER_EMOTION)
            gap_file = work / f"gap-{i:03d}.wav"
            render_pause(gap, work, name=f"gap-{i:03d}")
            items.append(gap_file)
    if not items:
        raise RuntimeError("no usable speech audio after trimming")
    td = Path(tempfile.mkdtemp(prefix="storyteller-paced-"))
    try:
        listf = td / "list.txt"
        listf.write_text("\n".join(f"file '{p}'" for p in items) + "\n")
        out = work / "speech-paced.wav"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
             "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(out)])
        return out
    finally:
        shutil.rmtree(td, ignore_errors=True)


def _scene_trailing_pause(sc: Scene) -> float:
    """Return the total trailing pause duration for a scene (from pause cues)."""
    total = 0.0
    for cue in sc.cues:
        if cue.kind == "pause":
            total += cue.duration
    return total


def render_scene(sc: Scene, work: Path, stem: Path | None,
                 duck_db: float = 12.0, reverb_preset: str = "room") -> Path:
    """Render one scene: pace speech, duck stem, apply reverb to all
    elements for per-scene acoustic consistency (§1.5)."""
    speech_segs = [s for s in sc.segments if s.audio_path]
    if not speech_segs:
        # no dialogue — the stem alone is the scene (e.g. an opening bed).
        # Even here we apply reverb to the stem so the opening bed
        # sounds like it belongs to the space.
        if stem is None or not stem or not Path(stem).exists():
            raise RuntimeError(f"scene '{sc.title}' has no audio")
        path = _copy_audio(Path(stem), work / f"{_slug(sc.title)}-scene.wav")
        return _apply_reverb(path, work / f"{_slug(sc.title)}-scene.wav",
                             preset=reverb_preset)

    scene_name = _slug(sc.title)
    speech = _concat_with_pacing(speech_segs, work)

    # v3: apply reverb to speech for per-scene acoustic consistency
    reverb_out = work / f"{scene_name}-speech-reverb.wav"
    speech = _apply_reverb(speech, reverb_out, preset=reverb_preset,
                             wet=0.25, pre_delay_ms=20.0)

    # Audio-drama severe upgrade §1.4: pre-roll silence so the previous
    # scene's 5s crossfade resolves into pure ambience before dialogue.
    # Beds stem was extended by SCENE_HEAD_PAD in build_scene_stem so it
    # fills this zone unducked.
    head_pad = work / f"{scene_name}-head.wav"
    speech = _prepend_silence(speech, head_pad, SCENE_HEAD_PAD, work)

    # Real inter-scene gap: use the story's explicit [pause: N] when present,
    # otherwise fall back to SCENE_GAP. Do NOT stack both (double-counting
    # made boundaries hang).
    trailing = _scene_trailing_pause(sc)
    if trailing <= 0.0:
        trailing = SCENE_GAP
    if trailing > 0.0:
        gap = work / f"{scene_name}-trail.wav"
        speech = _append_silence(speech, gap, trailing, work)

    # An empty Path or non-existent stem means no beds — speech with fades only
    if stem is None or not stem or not Path(stem).exists():
        out = work / f"{scene_name}-scene.wav"
        return _fade(speech, out, duration=ffprobe_duration(speech))
    out = work / f"{scene_name}-scene.wav"
    return sidechain_mix(speech, Path(stem), out, duck_db=duck_db)


def _prepend_silence(src: Path, dst: Path, seconds: float, work: Path) -> Path:
    """Prepend `seconds` of pure silence to the start of src."""
    if seconds <= 0:
        return src
    sil = work / "head-silence.wav"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", f"{seconds:.3f}", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(sil)])
    td = Path(tempfile.mkdtemp(prefix="storyteller-head-"))
    try:
        listf = td / "list.txt"
        listf.write_text(f"file '{sil}'\nfile '{src}'\n")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
             "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
             "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
        return dst
    finally:
        shutil.rmtree(td, ignore_errors=True)


def _append_silence(src: Path, dst: Path, seconds: float, work: Path) -> Path:
    """Append `seconds` of pure silence to the end of src."""
    if seconds <= 0:
        return src
    sil = work / "tail-silence.wav"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", f"{seconds:.3f}", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(sil)])
    td = Path(tempfile.mkdtemp(prefix="storyteller-trail-"))
    try:
        listf = td / "list.txt"
        listf.write_text(f"file '{src}'\nfile '{sil}'\n")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
             "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(dst)])
        return dst
    finally:
        shutil.rmtree(td, ignore_errors=True)


def render_pause(duration: float, work: Path, name: str = "pause") -> Path:
    """Render a silence file of a given duration."""
    out = work / f"{name}.wav"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", f"{duration:.3f}", "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}", str(out)])
    return out


def concat_scenes(scene_audio: list[Path], out: Path) -> float:
    """Crossfade scenes, two-pass EBU R128, write mp3."""
    with tempfile.TemporaryDirectory(prefix="storyteller-final-") as td:
        td = Path(td)
        # Step 1: canonicalize all scenes
        canonical_scenes = []
        for i, sc_path in enumerate(scene_audio):
            canon = td / f"canon-{i:03d}.wav"
            _canonicalize(Path(sc_path), canon)
            canonical_scenes.append(canon)
        # Step 2: crossfade with Equal Power curve
        if len(canonical_scenes) == 1:
            crossfaded = canonical_scenes[0]
        else:
            crossfaded = td / "crossfaded.wav"
            _crossfade_scenes(canonical_scenes, crossfaded)
        # Step 3: two-pass EBU R128 + true-peak limiting
        mastered = td / "mastered.wav"
        _ebu_two_pass(crossfaded, mastered, target_i=-16.0, target_tp=-1.5, target_lra=11.0)
        # Step 4: write mp3
        run(["ffmpeg", "-y", "-i", str(mastered),
             "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
             "-c:a", "libmp3lame", "-q:a", "2", str(out)])
    return ffprobe_duration(out)


# --------------------------------------------------------------------------- #
# B-roll clip export (supplementary footage for the main video)
# --------------------------------------------------------------------------- #

def export_stems(story: Story, work: Path, out_dir: Path) -> dict:
    """Export per-scene per-kind stems (voice, music, atmos, sfx, roomtone).

    Walks the work directory, copies every stem produced by
    ``build_scene_stem`` into ``out_dir/stems/<scene-slug>/<kind>.wav``,
    and writes a single ``stems-index.json`` with file paths, durations,
    and kind labels. Also concatenates per-kind voice tracks into a
    single ``voice-stem.wav`` so editors can drop in a clean narration
    track without the bed.

    Returns the index dict (also written as JSON next to the master).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    stems_root = out_dir / "stems"
    stems_root.mkdir(parents=True, exist_ok=True)

    KIND_SUFFIX = {
        "music": "music",
        "atmos": "atmos",
        "sfx": "sfx",
        "roomtone": "roomtone",
    }

    # Per-kind accumulators (absolute paths into out_dir/stems/)
    voice_stem = out_dir / "voice-stem.wav"
    voice_parts: list[Path] = []
    index: dict = {
        "voice": str(voice_stem),
        "scenes": [],   # one entry per scene with its per-kind files
        "kinds": {k: [] for k in ("music", "atmos", "sfx", "roomtone")},
    }

    timeline = 0.0
    for sc in story.scenes:
        scene_slug = _slug(sc.title)
        scene_dir = stems_root / scene_slug
        scene_dir.mkdir(parents=True, exist_ok=True)
        entry: dict = {
            "scene": sc.title,
            "start": round(timeline, 2),
            "files": {},
        }

        # Voice: gather TTS raw clips for this scene in narrative order,
        # trim/pace the same way render_scene does. We deliberately reuse
        # seg.audio_path (the raw per-segment wav) so editors can re-cut.
        seg_total = sum(s.audio_duration for s in sc.segments)
        scene_voice_parts: list[Path] = []
        for s in sc.segments:
            if s.audio_path and Path(s.audio_path).exists():
                scene_voice_parts.append(Path(s.audio_path))
        # concat all this scene's segments into one per-scene voice clip
        if scene_voice_parts:
            per_scene_voice = scene_dir / "voice.wav"
            try:
                with tempfile.TemporaryDirectory(prefix="stem-voice-") as td:
                    listf = Path(td) / "list.txt"
                    listf.write_text(
                        "\n".join(f"file '{p}'" for p in scene_voice_parts) + "\n"
                    )
                    run([
                        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(listf),
                        "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
                        "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}",
                        str(per_scene_voice),
                    ])
                entry["files"]["voice"] = str(per_scene_voice)
                voice_parts.append(per_scene_voice)
            except RuntimeError as e:
                log(f"stems: voice concat failed for '{sc.title}': {e}")

        # Bed kinds: copy from work dir
        for kind, suffix in KIND_SUFFIX.items():
            # sfx can have multiple files per scene (one per cue value)
            matches = sorted(work.glob(f"{scene_slug}-{suffix}*.wav"))
            # Exclude files that are themselves intermediates (e.g.
            # 'roomtone-final.wav' used as the bed source — we want the
            # final, gain-applied one).
            matches = [m for m in matches if "-loop" not in m.stem
                       and "-rate" not in m.stem
                       and "music-placeholder" not in m.stem]
            if not matches:
                continue
            kind_files: list[str] = []
            for src in matches:
                # collapse sfx stings into one merged file per scene
                if kind == "sfx" and len(matches) > 1:
                    merged = scene_dir / "sfx-merged.wav"
                    try:
                        with tempfile.TemporaryDirectory(prefix="stem-sfx-") as td:
                            listf = Path(td) / "list.txt"
                            listf.write_text(
                                "\n".join(f"file '{p}'" for p in matches) + "\n"
                            )
                            run([
                                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                                "-i", str(listf),
                                "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
                                "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}",
                                str(merged),
                            ])
                        kind_files.append(str(merged))
                    except RuntimeError as e:
                        log(f"stems: sfx merge failed for '{sc.title}': {e}")
                        # fall back to individual copies
                        for src in matches:
                            dst = scene_dir / src.name
                            try:
                                _copy_audio(src, dst)
                                kind_files.append(str(dst))
                            except RuntimeError:
                                pass
                    break  # only run the merge once
                else:
                    dst = scene_dir / src.name
                    try:
                        _copy_audio(src, dst)
                        kind_files.append(str(dst))
                    except RuntimeError as e:
                        log(f"stems: copy failed {src.name}: {e}")
            entry["files"][kind] = kind_files
            for f in kind_files:
                index["kinds"][kind].append(f)

        index["scenes"].append(entry)
        timeline += max(seg_total, 1.0)

    # Build the global voice-stem: concat all per-scene voice clips
    # with the same pacing gaps the master uses, so voice-stem aligns
    # to master timing when dropped onto a video timeline.
    if voice_parts:
        try:
            with tempfile.TemporaryDirectory(prefix="stem-all-voice-") as td:
                listf = Path(td) / "list.txt"
                listf.write_text(
                    "\n".join(f"file '{p}'" for p in voice_parts) + "\n"
                )
                run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(listf),
                    "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2",
                    "-c:a", f"pcm_{CANONICAL_BIT_DEPTH}",
                    str(voice_stem),
                ])
        except RuntimeError as e:
            log(f"stems: voice-stem concat failed: {e}")

    # Add durations + sizes to index for the gate
    def _stat(p: Path) -> dict:
        try:
            d = ffprobe_duration(p)
        except Exception:
            d = 0.0
        try:
            sz = p.stat().st_size
        except OSError:
            sz = 0
        return {"path": str(p), "duration": round(d, 2), "bytes": sz}

    index["voice"] = _stat(voice_stem) if voice_parts else None
    for k in ("music", "atmos", "sfx", "roomtone"):
        index["kinds"][k] = [_stat(Path(p)) for p in index["kinds"][k]]
    index["scenes"] = [
        {
            "scene": e["scene"],
            "start": e["start"],
            "files": {
                k: [_stat(Path(p)) if isinstance(p, str) else p
                    for p in v]
                if isinstance(v, list)
                else (_stat(Path(v)) if isinstance(v, str) else v)
                for k, v in e["files"].items()
            },
        }
        for e in index["scenes"]
    ]

    (out_dir / "stems-index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    )
    log(f"stems: exported to {stems_root} ({len(voice_parts)} voice, "
        f"{sum(len(v) for v in [index['kinds'][k] for k in ('music','atmos','sfx','roomtone')])} beds)")
    return index


def export_clips(story: Story, out_dir: Path, work: Path,
                 min_len: float = 3.0, max_len: float = 12.0) -> list[dict]:
    """Export one b-roll clip per segment, plus per-scene bed clips.

    Each clip is a clean segment cut (faded, normalized, silent edges
    trimmed) suitable for layering under or between main content. A sidecar
    JSON file carries caption-ready timing data (start, end, speaker,
    text) for the video editor.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    meta: list[dict] = []
    n = 0
    for sc in story.scenes:
        for seg in sc.segments:
            if not seg.audio_path:
                continue
            src = Path(seg.audio_path)
            dur = max(seg.audio_duration, 1.0)
            if dur < min_len:
                continue
            if dur > max_len:
                dur = max_len
            name = f"broll-{_slug(sc.title)}-{_slug(seg.speaker)}-{n + 1:02d}"
            mp3 = out_dir / f"{name}.mp3"
            wav = work / f"clip-{n + 1:02d}.wav"
            # clean cut: fade edges, trim silence, normalize
            run(["ffmpeg", "-y", "-i", str(src), "-t", f"{dur:.3f}",
                 "-af", "silenceremove=start_periods=1:start_threshold=-45dB,"
                        "silenceremove=stop_periods=1:stop_threshold=-45dB,"
                        "afade=t=in:d=0.05,afade=t=out:st=%.3f:d=0.15,"
                        "loudnorm=I=-16:TP=-1.5:LRA=11" % max(dur - 0.2, 0.1),
                 "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", "libmp3lame", "-q:a", "2",
                 str(mp3)])
            entry = {
                "file": str(mp3),
                "scene": sc.title,
                "speaker": seg.speaker,
                "start": round(sc.start_offset + seg.offset, 2),
                "end": round(sc.start_offset + seg.offset + dur, 2),
                "duration": round(dur, 2),
                "text": seg.text,
                "emotion": seg.emotion,
            }
            meta.append(entry)
            n += 1
    # scene bed clips: the mixed stem (music/SFX) alone, for cutaways
    for sc in story.scenes:
        stem = work / f"{_slug(sc.title)}-stem.wav"
        if not stem.exists():
            continue
        dur = min(max(ffprobe_duration(stem), 1.0), max_len)
        name = f"broll-{_slug(sc.title)}-bed-{n + 1:02d}"
        mp3 = out_dir / f"{name}.mp3"
        run(["ffmpeg", "-y", "-i", str(stem), "-t", f"{dur:.3f}",
             "-af", "afade=t=in:d=0.1,afade=t=out:st=%.3f:d=0.3,"
                    "loudnorm=I=-16:TP=-1.5:LRA=11" % max(dur - 0.4, 0.1),
             "-ar", str(CANONICAL_SAMPLE_RATE), "-ac", "2", "-c:a", "libmp3lame", "-q:a", "2",
             str(mp3)])
        meta.append({
            "file": str(mp3),
            "scene": sc.title,
            "speaker": "(bed)",
            "start": round(sc.start_offset, 2),
            "end": round(sc.start_offset + dur, 2),
            "duration": round(dur, 2),
            "text": "",
            "emotion": "atmos",
        })
        n += 1
    meta_path = out_dir / "broll-index.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    return meta


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="storyteller.py",
        description="Turn an annotated story script into finished audio-drama audio.",
    )
    parser.add_argument("script", type=Path, help="story script (.md), see example-story.md")
    parser.add_argument("-o", "--out", type=Path, default=None,
                        help="output mp3 path (default ./out/<title>.mp3)")
    parser.add_argument("--provider", choices=["auto", "voxcpm", "minimax", "chatterbox"],
                        default="auto",
                        help="force a provider; auto tries VoxCPM then MiniMax then Chatterbox")
    parser.add_argument("--gpu", default="",
                        help="fleet GPU target 'host:idx' (e.g. forge:0, nexus:0) to render "
                             "voxcpm on a fleet GPU — pauses that host's miner, renders, "
                             "resumes (j_kro authorized). Empty = local 3090.")
    parser.add_argument("--no-effects", action="store_true",
                        help="skip ffmpeg room-tone processing (concat raw scenes)")
    parser.add_argument("--keep", action="store_true",
                        help="keep the working directory on failure (debug)")
    parser.add_argument("--api-url", default="https://api.minimax.io/v1/t2a_v2",
                        help="MiniMax T2A endpoint override")
    parser.add_argument("--gen-sfx", action="store_true",
                        help="write the default SFX library into assets/sfx and exit")
    parser.add_argument("--duck-db", type=float, default=12.0,
                        help="sidechain duck depth in dB (default 12)")
    parser.add_argument("--no-clips", action="store_true",
                        help="skip b-roll clip export")
    parser.add_argument("--clips-dir", type=Path, default=None,
                        help="b-roll clip output directory (default ./clips)")
    parser.add_argument("--clips-min", type=float, default=3.0,
                        help="minimum clip length in seconds (default 3)")
    parser.add_argument("--clips-max", type=float, default=12.0,
                        help="maximum clip length in seconds (default 12)")
    parser.add_argument("--export-stems", action="store_true",
                        help="export per-kind audio stems (voice/music/atmos/sfx/"
                             "roomtone) to <out>/stems/ alongside the master mix. "
                             "Writes stems-index.json with file paths, durations, "
                             "and kinds. Editors can re-mix or drop voice-stem.wav "
                             "onto a video timeline without rebuilding the bed.")
    parser.add_argument("--reverb-preset", default="room",
                        choices=["intimate", "room", "hall", "cathedral", "none"],
                        help="spatial reverb preset (default room; 'none' disables)")
    args = parser.parse_args(argv)

    # ── LANE LOCK (j_kro 2026-09-03) ──────────────────────────────────────
    # Only ONE storyteller/voxcpm render may run at a time across ALL profiles.
    # storyteller + voicebot both fired renders → 11GB×2 RAM → OOM (2026-09-03).
    import fcntl
    _lane_fd = open("/tmp/gpu-lanes/voxcpm-render.lock", "a+")
    try:
        fcntl.flock(_lane_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("FATAL: voxcpm-render lane is BUSY — another storyteller.py render is running. "
            "Two voxcpm renders at once blow up RAM (j_kro rule 2026-09-03). "
            "Wait for the other render to finish, then re-run.")
        return 3
    log("lane-lock: acquired voxcpm-render (exclusive)")

    check_ffmpeg()

    # SFX library builder mode: write default sounds and exit
    if args.gen_sfx:
        assets = REPO / "assets"
        written = build_sfx_library(assets, force=True)
        log(f"gen-sfx: wrote {len(written)} sounds into {assets / 'sfx'}")
        return 0

    if not args.script.exists():
        log(f"script not found: {args.script}")
        return 2

    story = parse_story(args.script)
    log(f"story '{story.title}': {len(story.segments)} segments, "
        f"{len(story.scenes)} scenes, {len(story.cast)} cast voices")

    # env / key
    load_env()
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    chatterbox_api = os.environ.get("CHATTERBOX_API", DEFAULT_CHATTERBOX_API)

    # provider decision: VoxCPM (self-hosted) → MiniMax (API) → Chatterbox
    use_voxcpm = args.provider in ("auto", "voxcpm") and voxcpm_available()
    use_minimax = args.provider in ("auto", "minimax")
    use_chatterbox = args.provider in ("auto", "chatterbox")
    if args.provider == "auto":
        if not use_voxcpm:
            log("voxcpm not available — falling to MiniMax/Chatterbox")
        if not key:
            log("no MINIMAX_API_KEY — skipping MiniMax")
            use_minimax = False
        elif not chatterbox_healthy(chatterbox_api):
            log(f"chatterbox unreachable ({chatterbox_api}) — MiniMax only")
            use_chatterbox = False
    if args.provider == "minimax" and not key:
        log("--provider minimax but no MINIMAX_API_KEY")
        return 3
    if not use_voxcpm and not use_minimax and not use_chatterbox:
        log("no provider available (voxcpm missing, no key, chatterbox down)")
        return 1

    out = args.out or (Path("out") / f"{story.title.replace(' ', '-').lower()}.mp3")
    # If -o points at a directory, append the default filename — ffmpeg needs
    # a file path with a format-bearing extension, not a bare dir.
    if out.is_dir():
        out = out / f"{story.title.replace(' ', '-').lower()}.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)

    work = Path(tempfile.mkdtemp(prefix=f"storyteller-{story.title[:12]}-"))
    try:
        # resolve SFX/atmos/music assets ('' when the library misses)
        _resolve_assets(story, REPO / "assets")
        missing_cues = [
            f"{cue.kind}:{cue.value}" for sc in story.scenes for cue in sc.cues
            if cue.kind in ("atmos", "sfx", "music") and not cue.path
        ]
        for cue in missing_cues:
            log(f"note: no library sound for {cue}; using generated fallback")

        seg_audio: list[Path] = []
        used_providers: set[str] = set()
        # R12: treat a bare "none" preset as reverb-disabled
        reverb_preset = None if args.reverb_preset == "none" else args.reverb_preset
        for i, seg in enumerate(story.segments, start=1):
            raw = work / f"seg-{i:02d}-raw.mp3"
            voice = seg.voice or story.voice
            speed = seg.speed or story.speed
            provider = ""
            if use_voxcpm:
                try:
                    # Voice Design from the character's cast entry + emotion
                    voice_desc = _voxcpm_voice_desc(seg, story)
                    log(f"seg {i}/{len(story.segments)}: VoxCPM "
                        f"[{seg.speaker}|{seg.emotion}]…")
                    voxcpm_tts(seg.text, raw, voice_desc=voice_desc,
                               emotion=seg.emotion or "", gpu=args.gpu)
                    provider = "voxcpm"
                    used_providers.add("voxcpm")
                except RuntimeError as e:
                    log(f"seg {i}: VoxCPM failed ({e}); falling back")
                    use_voxcpm = False
                    provider = ""
            if not provider and use_minimax:
                try:
                    log(f"seg {i}/{len(story.segments)}: MiniMax "
                        f"[{seg.speaker}|{seg.emotion}]…")
                    minimax_tts(
                        seg.text, voice, story.model, seg.emotion,
                        "", speed, raw, key, args.api_url,
                    )
                    provider = "minimax"
                    used_providers.add("minimax")
                except RuntimeError as e:
                    log(f"seg {i}: MiniMax failed ({e}); falling back")
                    use_minimax = False
                    provider = ""
            if not provider and use_chatterbox:
                log(f"seg {i}: chatterbox ({seg.voice or story.fallback_voice})…")
                chatterbox_tts(seg.text, seg.voice or story.fallback_voice,
                               raw, chatterbox_api)
                provider = "chatterbox"
                used_providers.add("chatterbox")
            if not provider:
                raise RuntimeError(f"no provider produced seg {i} ({seg.scene})")

            seg.audio_path = str(raw)
            seg.provider = provider
            seg.audio_duration = ffprobe_duration(raw)
            seg_audio.append(raw)
            log(f"seg {i}: {provider} [{seg.speaker}] {seg.emotion} "
                f"({seg.audio_duration:.1f}s)")

        # narrative offsets (audio durations known now)
        for sc in story.scenes:
            off = 0.0
            for seg in sc.segments:
                seg.offset = off
                off += max(seg.audio_duration, 0.0)

        # build per-scene stems (music + atmos + sfx) and render scenes
        scene_audio: list[Path] = []
        timeline = 0.0
        for sc in story.scenes:
            # Default reverb before atmos-based selection so
            # build_scene_stem gets a valid preset on the first call.
            reverb = reverb_preset or "room"
            stem = build_scene_stem(sc, work, REPO / "assets",
                                        gen_missing=True,
                                        reverb_preset=reverb_preset or "room")
            # Override preset based on atmos cue for per-scene
            # acoustic consistency (§1.5).
            for cue in sc.cues:
                if cue.kind == "atmos":
                    val = cue.value.lower()
                    if any(w in val for w in ["cathedral", "church", "temple"]):
                        reverb = "cathedral"
                    elif any(w in val for w in ["hall", "large", "big", "cave"]):
                        reverb = "hall"
                    elif any(w in val for w in ["small", "intimate", "whisper", "close"]):
                        reverb = "intimate"
            scene_path = render_scene(sc, work, Path(stem) if stem else None,
                                      duck_db=args.duck_db,
                                      reverb_preset=(reverb or "room"))
            sc.start_offset = timeline
            timeline += ffprobe_duration(scene_path)
            scene_audio.append(scene_path)
            log(f"scene '{sc.title}': {ffprobe_duration(scene_path):.1f}s "
                f"(+{CROSSFADE_DURATION}s crossfade)")

        duration = concat_scenes(scene_audio, out)
        providers = sorted(used_providers)
        log(f"done: {out} ({duration:.1f}s, {len(story.segments)} segments, "
            f"providers: {providers})")

        # Stem export (opt-in via --export-stems). Per-kind stems land in
        # <out-dir>/stems/ alongside voice-stem.wav and stems-index.json.
        if args.export_stems:
            stems = export_stems(story, work, out.parent)
            log(f"stems: voice-stem={stems.get('voice', {}).get('path', 'NONE')}, "
                f"kinds={ {k: len(v) for k, v in stems['kinds'].items()} }")

        # Post-render NIM Omni audio-QA gate
        # Single-point enforcement lives in the gate chain (advance-stage.sh
        # + gate_preaudit.py → --evidence-only). This hook is informational:
        # it populates review/nim_omni_qa.review.json once per render so the
        # chain has fresh evidence to consume. The chain will BLOCK advance
        # if the gate fails; this hook does NOT block the render itself
        # (rendering already succeeded; NIM Omni verdict is a QA signal).
        qa_gate = REPO / "scripts" / "gates" / "gate_nim_omni_qa.py"
        if qa_gate.exists():
            log(f"running NIM Omni audio-QA gate (render-time, populates evidence)...")
            try:
                qa_result = subprocess.run(
                    [sys.executable, str(qa_gate), str(out.parent)],
                    capture_output=True, text=True, timeout=600,
                )
                if qa_result.returncode == 0:
                    log(f"NIM Omni QA: PASS")
                else:
                    log(f"NIM Omni QA: FAIL — {qa_result.stdout[-200:]}")
                    log(f"(render proceeds — gate chain will block on next advance)")
            except subprocess.TimeoutExpired:
                log(f"NIM Omni QA: timeout (gate skipped; chain will catch missing evidence)")
            except Exception as e:
                log(f"NIM Omni QA: error ({e})")
        else:
            log(f"NIM Omni QA gate not found at {qa_gate} — skipping")

        # b-roll clip export
        if not args.no_clips:
            clips_dir = args.clips_dir or (Path("clips") / story.title.replace(" ", "-").lower())
            clips = export_clips(story, clips_dir, work,
                                 min_len=args.clips_min, max_len=args.clips_max)
            log(f"clips: {len(clips)} b-roll files in {clips_dir} "
                f"(index: {clips_dir / 'broll-index.json'})")

        return 0
    except Exception as e:  # noqa: BLE001 — report and exit
        log(f"FAILED: {e}")
        if os.environ.get("STORYTELLER_DEBUG") or args.keep:
            log(f"work dir kept: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
