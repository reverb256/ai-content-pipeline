#!/usr/bin/env python3
"""storyteller.py — production audio-drama pipeline for the content machine.

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
    """A scene heading plus the lines and cues that belong to it."""
    title: str
    text: str = ""
    segments: list[Segment] = field(default_factory=list)
    cues: list[Cue] = field(default_factory=list)
    start_offset: float = 0.0  # global timeline position, filled at assembly


@dataclass
class CastMember:
    """One cast entry: the voice that speaks a character."""
    name: str
    voice_desc: str = ""
    voice: str = ""  # MiniMax voice id override


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
    """Parse simple key: value lines plus multi-line 'cast:' lists.

    A line starting with two spaces under 'cast:' continues the previous
    cast entry. A line starting with two spaces and a dash starts a new
    cast entry. Anything else is a flat key: value pair.
    """
    meta: dict = {}
    cast: dict[str, str] = {}
    cast_key = "cast"
    cur_name = ""
    for line in block.splitlines():
        # Continuation lines start with 4+ spaces (deeper than the 2-space
        # cast entries). Detect this BEFORE stripping so we can tell
        # "new entry at 2 spaces" from "continuation at 4+ spaces".
        leading = len(line) - len(line.lstrip())
        if line.startswith("  ") and leading >= 4 and cur_name:
            # continuation of the current cast description
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
                # cast entry (indented key: value, no dash)
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
    """Parse the markup documented in scripts/audio/example-story.md."""
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
        try:
            story.speed = float(meta.get("speed", story.speed))
        except (ValueError, TypeError):
            pass
        raw_cast = meta.get("cast")
        if isinstance(raw_cast, dict):
            for name, desc in raw_cast.items():
                story.cast[name.strip().lower()] = CastMember(name=name.strip(), voice_desc=desc)
        elif isinstance(raw_cast, str) and raw_cast.strip():
            for entry in re.split(r"[;,]", raw_cast):
                if ":" not in entry:
                    continue
                name, _, desc = entry.partition(":")
                story.cast[name.strip().lower()] = CastMember(
                    name=name.strip(), voice_desc=desc.strip()
                )
        text = text[m.end():]

    # Strip the FORMAT DOCUMENTATION block (everything up to the DOC-END
    # marker). Story scripts do not carry this block; only the format
    # reference file does.
    doc_end = text.find("<!-- DOC-END -->")
    if doc_end != -1:
        text = text[doc_end + len("<!-- DOC-END -->"):]

    scene: Scene | None = None
    pending_emotion = DEFAULT_EMOTION
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^#{1,6}\s+", line):
            # new scene heading: flush the current scene, start a new one
            if scene is not None and (scene.text.strip() or scene.segments):
                story.scenes.append(scene)
            scene = Scene(title=re.sub(r"^#{1,6}\s+", "", stripped))
            pending_emotion = DEFAULT_EMOTION
            continue
        if scene is None:
            # text before any scene heading → implicit scene
            scene = Scene(title="intro")
        # a cue line: [SFX: ...] [ATMOS: ...] [MUSIC: ...] [pause: N]
        # or a backward-compatible emotion line [angry | key=val ...]
        if stripped.startswith("[") and stripped.endswith("]"):
            cue = _parse_cue(stripped)
            if cue is None:
                # not a recognized cue; treat as plain text (stage note)
                _append_segment_text(scene, story, stripped)
                continue
            if cue.kind == "emotion":
                pending_emotion = cue.value
                if cue.value in ("fearful", "whisper", "angry", "sad", "surprised"):
                    scene.cues.append(Cue(kind="emotion", value=cue.value))
                continue
            if cue.kind == "pause":
                scene.cues.append(cue)
                continue
            # atmos / sfx / music: record the cue now, resolve the asset later
            scene.cues.append(cue)
            continue
        # a speaker line or a plain narrative line
        speaker, emotion, body = _speaker_of(stripped)
        if speaker and body:
            seg = Segment(
                scene=scene.title,
                speaker=speaker,
                emotion=emotion or pending_emotion,
                text=body,
                speed=story.speed,
            )
            story.segments.append(seg)
            scene.segments.append(seg)
            if scene.text:
                scene.text += "\n"
            scene.text += stripped
            continue
        # plain line → narration
        _append_segment_text(scene, story, stripped)

    # flush the final scene
    if scene is not None and (scene.text.strip() or scene.segments):
        if not story.scenes or story.scenes[-1] is not scene:
            story.scenes.append(scene)

    if not story.segments:
        raise ValueError(f"no segments parsed from {path}")

    # narrator voice resolution: explicit "Narrator" in the cast wins;
    # otherwise the frontmatter voice/fallback drive the description.
    _resolve_narrator(story)

    # narrative offset per segment (for b-roll timestamps and pacing)
    for sc in story.scenes:
        off = 0.0
        for seg in sc.segments:
            seg.offset = off
            off += max(seg.audio_duration, 0.0)
    return story


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
}


def voxcpm_tts(text: str, out: Path, voice_desc: str = "",
               quality: str = VOXCPM_QUALITY, timeout: float = 300.0) -> Path:
    """Synthesize via local VoxCPM (self-hosted, no API key, emotive).

    quality: f16 = full precision (best), q8 = Q8_0 (near-lossless),
             q4 = Q4_K (fastest, slightly lower).
    Uses a small wrapper script that calls the voxcpm Python API; the model
    loads once and stays cached per process. Raises RuntimeError on failure.
    """
    base = Path(__file__).resolve().parent
    wrapper = base / "voxcpm_generate.py"
    if not wrapper.exists():
        raise RuntimeError(f"voxcpm wrapper missing: {wrapper}")
    cmd = [
        sys.executable, str(wrapper),
        "--text", text,
        "--out", str(out),
        "--quality", quality,
    ]
    if voice_desc:
        cmd += ["--voice-desc", voice_desc]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"voxcpm failed: {proc.stderr[-500:]}")
    if not out.exists() or out.stat().st_size < 1000:
        raise RuntimeError("voxcpm produced no/small audio")
    return out


def voxcpm_available() -> bool:
    try:
        import voxcpm  # noqa: F401
        return True
    except Exception:
        return False


def _voxcpm_voice_desc(seg: Segment, story: Story) -> str:
    """Build a Voice Design description for a segment.

    Priority: per-segment override → cast voice description → emotion
    description → default narrator.
    """
    if seg.voice_desc:
        return seg.voice_desc
    member = story.cast_member(seg.speaker)
    if member is not None and member.voice_desc:
        return member.voice_desc
    if seg.speaker.lower() in PROMPT_NAMES:
        return DEFAULT_EMOTION_DESC
    emotion = seg.emotion or DEFAULT_EMOTION
    return _EMOTION_VOICE_DESC.get(emotion, DEFAULT_EMOTION_DESC)


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
    generator (--gen-sfx) writes the same location.
    """
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
        "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(dst),
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
         "afade=t=out:st=0.05:d=0.13", "-ar", "44100", "-ac", "1",
         "-c:a", "pcm_s16le", str(dst)])
    work.unlink(missing_ok=True)
    return dst


def _gen_door_creak(dst: Path) -> Path:
    """A slow rising creak: sweep up 60→140 Hz with a low decay."""
    d = Path(dst)
    work = d.parent / f"{d.stem}-creak.wav"
    gen_tone(work, 1.8, freq=70.0, kind="sweep", volume=0.25)
    run(["ffmpeg", "-y", "-i", str(work), "-af",
         "volume=0.6,afade=t=in:st=0:d=0.6,afade=t=out:st=1.0:d=0.8",
         "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(dst)])
    work.unlink(missing_ok=True)
    return dst


def _gen_thunder(dst: Path) -> Path:
    """A rumble: brown noise burst with a long tail."""
    d = Path(dst)
    work = d.parent / f"{d.stem}-rumble.wav"
    gen_tone(work, 4.0, freq=80.0, kind="noise_brown", volume=0.5)
    run(["ffmpeg", "-y", "-i", str(work), "-af",
         "afade=t=in:st=0:d=0.4,afade=t=out:st=2.0:d=2.0",
         "volume=0.7", "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(dst)])
    work.unlink(missing_ok=True)
    return dst


def _gen_footsteps(dst: Path) -> Path:
    """Two sharp ticks (a pair of steps) via short noise bursts."""
    d = Path(dst)
    work = d.parent / f"{d.stem}-step.wav"
    gen_tone(work, 0.25, freq=200.0, kind="noise", volume=0.5)
    run(["ffmpeg", "-y", "-i", str(work), "-af",
         "afade=t=out:st=0.03:d=0.22", "-ar", "44100", "-ac", "1",
         "-c:a", "pcm_s16le", str(dst)])
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

SCENE_GAP = 1.2  # seconds of trailing silence between scenes
MAX_CUE_LEN = 20.0  # cap for generated sound beds
FADE_MS = 30  # ms fades on segment edges (crossfade-safe cuts)

_EVEN_BUS = "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1"


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
         "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(out)])
    return out


def _fade(path: Path, dst: Path, in_ms: int = FADE_MS, out_ms: int = FADE_MS,
          duration: float | None = None) -> Path:
    """Apply short edge fades so cuts do not click."""
    af = f"afade=t=in:d={in_ms / 1000:.3f}"
    if out_ms > 0:
        af += f",afade=t=out:st={duration - out_ms / 1000:.3f}:d={out_ms / 1000:.3f}"
    run(["ffmpeg", "-y", "-i", str(path), "-af", af,
         "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(dst)])
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
         "-c:a", "pcm_s16le", str(dst)])
    return dst


def _pad_to(path: Path, dst: Path, target: float) -> Path:
    """Pad the end of audio with silence up to a target duration."""
    run(["ffmpeg", "-y", "-i", str(path), "-af",
         f"apad=pad_dur={max(target, 0):.3f}",
         "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(dst)])
    return dst


def _loop_to(path: Path, dst: Path, target: float) -> Path:
    """Loop audio until it reaches target seconds (then trim to it)."""
    if target <= 0:
        return _copy_audio(path, dst)
    rate = _sample_rate(path)
    src = _resample(path, dst.parent / f"{dst.stem}-rate.wav", rate)
    n = max(1, int(target / max(ffprobe_duration(src), 0.1)))
    if n > 1:
        inputs = [src] * n
        run(["ffmpeg", "-y"] + sum((["-i", str(i)] for i in inputs), []) +
            ["-filter_complex", f"concat=n={n}:v=0:a=1",
             "-ar", str(rate), "-ac", "2", "-c:a", "pcm_s16le", str(src)])
    if target < ffprobe_duration(src):
        run(["ffmpeg", "-y", "-i", str(src), "-t", f"{target:.3f}",
             "-ar", str(rate), "-ac", "2", "-c:a", "pcm_s16le", str(dst)])
        src.unlink(missing_ok=True)
        return dst
    return src


def _copy_audio(src: Path, dst: Path) -> Path:
    """Copy an audio file to dst (PCM16 stereo 44.1k)."""
    run(["ffmpeg", "-y", "-i", str(src), "-ar", "44100", "-ac", "2",
         "-c:a", "pcm_s16le", str(dst)])
    return dst


def _resolved(sc: Scene, kind: str) -> Cue | None:
    """Return the last cue of a kind that has a resolvable path."""
    for cue in reversed(sc.cues):
        if cue.kind == kind and cue.path:
            return cue
    return None


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
         "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(dst)])
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
        "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(dst)])
    return dst


def build_scene_stem(sc: Scene, work: Path, assets: Path,
                     gen_missing: bool = False) -> Path | None:
    """Build the music/SFX/ambience stem for one scene.

    The stem is the full scene duration: music (if any), atmos bed, and
    SFX events, all gain-set, lowpassed, and panned. Returns the wav path.
    Returns an empty-file marker when the scene has no beds and no sfx.
    """
    # scene duration = last segment end + trailing pause + scene gap
    seg_total = sum(s.audio_duration for s in sc.segments)
    trailing = 0.0
    for cue in sc.cues:
        if cue.kind == "pause":
            trailing = max(trailing, cue.duration)
    target = seg_total + trailing + SCENE_GAP
    target = min(max(target, 1.0), 60.0 * 10)  # 10-min cap per scene

    beds: list[Path] = []
    # --- music layer (lowest priority; placeholder tone or library file)
    music = _resolved(sc, "music")
    if music is not None:
        stem = work / f"{_slug(sc.title)}-music.wav"
        try:
            if gen_missing and not Path(music.path).exists():
                _gen_sfx("music", music.value, Path(music.path))
            if Path(music.path).exists():
                beds.append(_build_bed(
                    music.path, target, stem,
                    gain=0.14, lowpass=2000, stereo=True,
                ))
                log(f"  music: {music.value} ({music.path})")
        except RuntimeError as e:
            log(f"  music skipped ({music.value}): {e}")

    # --- atmos bed (background ambience)
    atmos = _resolved(sc, "atmos")
    if atmos is not None:
        stem = work / f"{_slug(sc.title)}-atmos.wav"
        try:
            if gen_missing and not Path(atmos.path).exists():
                _gen_sfx("atmos", atmos.value, Path(atmos.path))
            if Path(atmos.path).exists():
                beds.append(_build_bed(
                    atmos.path, target, stem,
                    gain=0.22, lowpass=4000, stereo=True,
                ))
                log(f"  atmos: {atmos.value} ({atmos.path})")
        except RuntimeError as e:
            log(f"  atmos skipped ({atmos.value}): {e}")

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
                 "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(stem)])
            beds.append(stem)
            log(f"  sfx: {cue.value} ({cue.path})")
        except RuntimeError as e:
            log(f"  sfx skipped ({cue.value}): {e}")

    if not beds:
        return None
    stem = work / f"{_slug(sc.title)}-stem.wav"
    return _one_bed(beds, stem)


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
        "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(out),
    ])
    return out


def render_scene(sc: Scene, work: Path, stem: Path | None,
                 duck_db: float = 12.0) -> Path:
    """Render one scene: concatenate its speech segments, duck the stem."""
    speech_paths = [Path(s.audio_path) for s in sc.segments if s.audio_path]
    if not speech_paths:
        # no dialogue — the stem alone is the scene (e.g. an opening bed)
        if stem is None or not stem or not Path(stem).exists():
            raise RuntimeError(f"scene '{sc.title}' has no audio")
        return _copy_audio(Path(stem), work / f"{_slug(sc.title)}-scene.wav")
    speech = _concat_paths(speech_paths)

    scene_name = _slug(sc.title)
    # An empty Path or non-existent stem means no beds — speech with fades only
    if stem is None or not stem or not Path(stem).exists():
        out = work / f"{scene_name}-scene.wav"
        return _fade(speech, out, duration=ffprobe_duration(speech))
    out = work / f"{scene_name}-scene.wav"
    return sidechain_mix(speech, Path(stem), out, duck_db=duck_db)


def render_pause(duration: float, work: Path, name: str = "pause") -> Path:
    """Render a silence file of a given duration."""
    out = work / f"{name}.wav"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", f"{duration:.3f}", "-c:a", "pcm_s16le", str(out)])
    return out


def concat_scenes(scene_audio: list[Path], out: Path) -> float:
    """Concatenate rendered scenes, normalize loudness, write mp3."""
    with tempfile.TemporaryDirectory(prefix="storyteller-final-") as td:
        concat_file = Path(td) / "list.txt"
        lines = [f"file '{p}'" for p in scene_audio]
        concat_file.write_text("\n".join(lines) + "\n")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
             "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-q:a", "2",
             str(out)])
    return ffprobe_duration(out)


# --------------------------------------------------------------------------- #
# B-roll clip export (supplementary footage for the main video)
# --------------------------------------------------------------------------- #

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
                 "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-q:a", "2",
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
             "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-q:a", "2",
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
    args = parser.parse_args(argv)

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
                    voxcpm_tts(seg.text, raw, voice_desc=voice_desc)
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
            stem = build_scene_stem(sc, work, REPO / "assets", gen_missing=True)
            scene_path = render_scene(sc, work, Path(stem) if stem else None,
                                      duck_db=args.duck_db)
            sc.start_offset = timeline
            timeline += ffprobe_duration(scene_path)
            scene_audio.append(scene_path)
            log(f"scene '{sc.title}': {ffprobe_duration(scene_path):.1f}s "
                f"(+{SCENE_GAP}s gap)")

        duration = concat_scenes(scene_audio, out)
        providers = sorted(used_providers)
        log(f"done: {out} ({duration:.1f}s, {len(story.segments)} segments, "
            f"providers: {providers})")

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
