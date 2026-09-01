#!/usr/bin/env python3
"""storyteller.py — audio-drama orchestrator for the faceless AI content machine.

Reads a story script with scene/emotion markup, synthesizes per-scene audio
through MiniMax Speech T2A (primary) with Chatterbox (self-hosted, local GPU)
as fallback, assembles the scenes with ffmpeg, applies simple sound effects
(reverb / echo / telephone / robotic / loudness) for atmosphere, and writes a
finished audio file.

Usage:
    storyteller.py story.md -o out/finished.mp3 [options]

Input format (documented in scripts/audio/example-story.md):

    ---
    title: The Last Signal
    voice: English_expressive_narrator
    fallback_voice: Connor.wav
    model: speech-2.8-hd
    speed: 1.0
    ---

    # Scene 1 — The Call
    [calm]
    The console beeped once. Then it stopped.

    [angry | sound_effect=spacious_echo]
    "Who left this running?" Mara snapped.

Every H2 line starts a new scene. A [bracket] line under it sets the emotion
(and optional sound_effect / voice / speed). Blank lines separate takes.

Scenes synthesize independently, so per-scene emotion and sound effects land
in the voice itself. The final mix applies ffmpeg room tone (aecho) unless the
scene already carries a MiniMax sound effect.

Environment:
    MINIMAX_API_KEY  — required for the MiniMax path (loaded from ~/.hermes/.env)
    CHATTERBOX_API   — Chatterbox base URL, default http://10.1.1.130:8004
    STORYTELLER_DEBUG — set to 1 to keep the working directory

Exit codes:
    0 success (finished audio written)
    1 fatal error (no provider available, no scenes parsed)
    2 usage error
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
import time
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
class Scene:
    """A scene heading. Scene text accumulates into per-directive Segments."""
    title: str
    text: str = ""


@dataclass
class Segment:
    """One TTS synthesis unit: a directive block within a scene."""
    scene: str
    emotion: str = "calm"
    sound_effect: str = ""
    voice: str = ""
    speed: float = 1.0
    text: str = ""
    audio_path: str = ""


@dataclass
class Story:
    title: str = "untitled"
    voice: str = "English_expressive_narrator"
    fallback_voice: str = "Connor.wav"
    model: str = "speech-2.8-hd"
    speed: float = 1.0
    scenes: list[Scene] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)


def _parse_frontmatter(block: str) -> dict:
    meta: dict = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        meta[k.strip().lower().replace(" ", "_")] = v.strip().strip('"').strip("'")
    return meta


def _parse_scene_directive(line: str) -> tuple[str, dict]:
    """Parse '[angry | sound_effect=spacious_echo]' → ('angry', {...})."""
    inner = line.strip().strip("[]").strip()
    parts = [p.strip() for p in inner.split("|")]
    emotion = parts[0].lower()
    opts: dict = {}
    for p in parts[1:]:
        if "=" in p:
            k, _, v = p.partition("=")
            opts[k.strip().lower().replace(" ", "_")] = v.strip()
    if emotion not in VALID_EMOTIONS:
        emotion = "calm"
    for k in ("sound_effect", "voice", "speed"):
        if k in opts:
            opts[k] = opts[k]
    return emotion, opts


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
        except ValueError:
            pass
        text = text[m.end():]

    # Strip the FORMAT DOCUMENTATION block (everything up to the DOC-END
    # marker). Story scripts do not carry this block; only the format
    # reference file does.
    doc_end = text.find("<!-- DOC-END -->")
    if doc_end != -1:
        text = text[doc_end + len("<!-- DOC-END -->"):]

    scene: Scene | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^#{1,6}\s+", line):
            # new scene heading: flush the current scene, start a new one
            if scene is not None and scene.text.strip():
                story.scenes.append(scene)
            scene = Scene(title=re.sub(r"^#{1,6}\s+", "", stripped))
            continue
        if scene is None:
            # text before any scene heading → implicit scene
            scene = Scene(title="intro")
        # a directive line: [emotion] or [emotion | key=val ...]
        # It starts a new TTS segment: flush the current segment, apply the
        # directive to the next block of lines.
        if stripped.startswith("[") and stripped.endswith("]"):
            emotion, opts = _parse_scene_directive(stripped)
            seg = Segment(
                scene=scene.title,
                emotion=emotion,
                sound_effect=opts.get("sound_effect", ""),
                voice=opts.get("voice", ""),
                speed=1.0,
            )
            if "speed" in opts:
                try:
                    seg.speed = float(opts["speed"])
                except ValueError:
                    pass
            story.segments.append(seg)
            continue
        # normal line → append to the last segment (or open a new one)
        if not story.segments or story.segments[-1].scene != scene.title:
            story.segments.append(Segment(scene=scene.title))
        if story.segments[-1].text:
            story.segments[-1].text += "\n"
        story.segments[-1].text += stripped
        # also accumulate into the scene's text (for scene-level checks)
        if scene.text:
            scene.text += "\n"
        scene.text += stripped

    # flush the final scene
    if scene is not None and scene.text.strip() and (
        not story.scenes or story.scenes[-1] is not scene
    ):
        story.scenes.append(scene)

    if not story.segments:
        raise ValueError(f"no segments parsed from {path}")

    return story


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
    resp = _post_json(f"{api}/tts", payload, {})
    # Chatterbox returns raw audio bytes in the response body.
    if isinstance(resp, dict) and "error" in resp:
        raise RuntimeError(f"Chatterbox error: {resp['error']}")
    # _post_json already parsed JSON; the API returns binary. Fall through to a
    # binary path instead: issue the raw request here.
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

VOXCPM_QUALITY = os.environ.get("VOXCPM_QUALITY", "q8")  # f16 | q8 | q4

def voxcpm_tts(text: str, out: Path, voice_desc: str = "",
               quality: str = VOXCPM_QUALITY, timeout: float = 300.0) -> Path:
    """Synthesize via local VoxCPM (self-hosted, no API key, emotive).

    quality: f16 = full precision (best), q8 = Q8_0 (near-lossless, default),
             q4 = Q4_K (fastest, slightly lower).
    Uses a small wrapper script that calls the voxcpm Python API; the model
    loads once and stays cached per process. Raises RuntimeError on failure.
    """
    import sys
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

def _voxcpm_voice_desc(seg) -> str:
    """Build a Voice Design description for a segment from its emotion."""
    if seg.voice:
        # An explicit per-scene voice override exists; keep it simple.
        return ""
    return _EMOTION_VOICE_DESC.get(seg.emotion, "a clear, expressive narrator")


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #

def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def mix_segment(seg: Segment, src: Path, dst: Path) -> Path:
    """Apply atmosphere to one segment's audio via ffmpeg.

    - MiniMax `sound_effect` already baked into the voice → only loudness.
    - No MiniMax effect → apply aecho room tone (decaying echo, mixed low).
    - Emotion whisper → add a high-pass to keep it airy without mud.
    """
    if seg.sound_effect:
        # The voice carries its own effect (spacious_echo etc). Normalize only.
        run(["ffmpeg", "-y", "-i", str(src), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
             "-c:a", "libmp3lame", "-q:a", "2", str(dst)])
        return dst

    # Room tone: aecho with a long-ish decay mixed at low level. This gives a
    # segment a sense of space without overpowering the narrator.
    # 0.8|0.88|60|0.4 → in_gain 0.8, out_gain 0.88, delays 60ms, decay 0.4
    aecho = "aecho=0.8:0.88:60|120:0.35|0.25"
    if seg.emotion == "whisper":
        aecho += ",highpass=f=120"
    af = f"{aecho},loudnorm=I=-16:TP=-1.5:LRA=11"
    run(["ffmpeg", "-y", "-i", str(src), "-af", af,
         "-c:a", "libmp3lame", "-q:a", "2", str(dst)])
    return dst


def assemble(seg_audio: list[Path], out: Path) -> float:
    """Concat segments with a short silence gap, normalize, write mp3."""
    with tempfile.TemporaryDirectory(prefix="storyteller-concat-") as td:
        concat_file = Path(td) / "list.txt"
        gap = Path(td) / "gap.mp3"
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
             "-t", "0.7", "-c:a", "libmp3lame", "-q:a", "9", str(gap)])
        lines: list[str] = []
        for i, audio in enumerate(seg_audio):
            if i > 0:
                lines.append(f"file '{gap}'")
            lines.append(f"file '{audio}'")
        concat_file.write_text("\n".join(lines) + "\n")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
             "-c:a", "libmp3lame", "-q:a", "2", str(out)])
    return ffprobe_duration(out)


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
    args = parser.parse_args(argv)

    check_ffmpeg()

    if not args.script.exists():
        log(f"script not found: {args.script}")
        return 2

    story = parse_story(args.script)
    log(f"story '{story.title}': {len(story.segments)} segments, "
        f"voice={story.voice}, fallback={story.fallback_voice}")

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
        seg_audio: list[Path] = []
        used_providers: set[str] = set()
        for i, seg in enumerate(story.segments, start=1):
            raw = work / f"seg-{i:02d}-raw.mp3"
            voice = seg.voice or story.voice
            speed = seg.speed or story.speed
            provider = ""
            if use_voxcpm:
                try:
                    # Voice Design from the scene's emotion: build a voice
                    # description so VoxCPM narrates with the right tone.
                    voice_desc = _voxcpm_voice_desc(seg)
                    log(f"seg {i}/{len(story.segments)}: VoxCPM ({seg.emotion})…")
                    voxcpm_tts(seg.text, raw, voice_desc=voice_desc)
                    provider = "voxcpm"
                    used_providers.add("voxcpm")
                except RuntimeError as e:
                    log(f"seg {i}: VoxCPM failed ({e}); falling back")
                    use_voxcpm = False
                    provider = ""
            if not provider and use_minimax:
                try:
                    log(f"seg {i}/{len(story.segments)}: MiniMax ({seg.emotion})…")
                    minimax_tts(
                        seg.text, voice, story.model, seg.emotion,
                        seg.sound_effect, speed, raw, key, args.api_url,
                    )
                    provider = "minimax"
                    used_providers.add("minimax")
                except RuntimeError as e:
                    log(f"seg {i}: MiniMax failed ({e}); falling back")
                    use_minimax = False  # do not retry MiniMax for later segments
                    provider = ""
            if not provider and use_chatterbox:
                log(f"seg {i}: chatterbox ({seg.voice or story.fallback_voice})…")
                chatterbox_tts(seg.text, seg.voice or story.fallback_voice,
                               raw, chatterbox_api)
                provider = "chatterbox"
                used_providers.add("chatterbox")
            if not provider:
                raise RuntimeError(f"no provider produced seg {i} ({seg.scene})")

            if args.no_effects:
                seg_audio.append(raw)
                continue

            mixed = work / f"seg-{i:02d}-mix.mp3"
            mix_segment(seg, raw, mixed)
            seg_audio.append(mixed)
            log(f"seg {i}: {provider} → {seg.emotion} "
                f"{seg.sound_effect or 'room-tone'} ({ffprobe_duration(mixed):.1f}s)")

        duration = assemble(seg_audio, out)
        providers = sorted(used_providers)
        log(f"done: {out} ({duration:.1f}s, {len(story.segments)} segments, "
            f"providers: {providers})")
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
