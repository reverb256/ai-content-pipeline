"""
Internal request/response models for sunolocal.

The wire format (what clients send) is Suno-shaped camelCase; `studio.py`
converts it into these internal dataclasses. Field names here follow the
public Suno reference (customMode, negativeTags, styleWeight, ...).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any


@dataclass
class SunoGenerateRequest:
    """A generation request, internal form."""
    prompt: Optional[str] = None            # description / core idea
    style: Optional[str] = None             # the style tags box
    lyrics: Optional[str] = None            # lyrics, meta tags allowed
    title: Optional[str] = None
    instrumental: bool = False
    model: str = "v6"
    custom_mode: bool = False
    negative_tags: Optional[str] = None
    vocal_gender: Optional[Literal["male", "female"]] = None
    duration: Optional[int] = None          # seconds
    style_weight: Optional[float] = None    # 0.0-1.0
    weirdness_constraint: Optional[float] = None
    audio_weight: Optional[float] = None
    variety: Optional[int] = None           # 0-4
    callback_url: Optional[str] = None
    seed: Optional[int] = None
    engine: Optional[str] = None            # sunolocal extension: ace | yue2 | fixture
    # sunolocal extensions. Suno's own API carries neither, and without them the
    # engine had to guess: `bpm` was hardcoded 120 and `key` was filled from the
    # style caption (674 chars for sentimental-piano) which is what the ACE node
    # receives as `keyscale`. Both defects are t_25a6499c D1/D2.
    bpm: Optional[int] = None               # explicit tempo; beats the style_weight fallback
    keyscale: Optional[str] = None          # explicit key signature, e.g. "C major"


@dataclass
class SunoGenerateResponse:
    task_id: str
    status: str = "pending"


@dataclass
class SunoTaskResponse:
    task_id: str
    status: str
    progress: Optional[float] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    title: Optional[str] = None
    lyrics: Optional[str] = None
    duration_s: Optional[float] = None
    stems: Optional[Dict[str, str]] = None
    lrc: Optional[str] = None
    manifest: Optional[Dict[str, Any]] = None


@dataclass
class SunoLyricsResponse:
    lyrics: str
    task_id: str


@dataclass
class SunoStemsResponse:
    stems: Dict[str, str]


@dataclass
class SunoExtendRequest:
    clip_id: str
    prompt: Optional[str] = None
    style: Optional[str] = None
    lyrics: Optional[str] = None
    instrumental: bool = False
    model: str = "v6"
    custom_mode: bool = False
    negative_tags: Optional[str] = None
    vocal_gender: Optional[Literal["male", "female"]] = None
    duration: Optional[int] = None
    style_weight: Optional[float] = None
    weirdness_constraint: Optional[float] = None
    audio_weight: Optional[float] = None
    variety: Optional[int] = None


@dataclass
class SunoCoverRequest:
    prompt: Optional[str] = None
    style: Optional[str] = None
    lyrics: Optional[str] = None
    model: str = "v6"
    custom_mode: bool = False
    negative_tags: Optional[str] = None
    vocal_gender: Optional[Literal["male", "female"]] = None
    duration: Optional[int] = None
    style_weight: Optional[float] = None
    weirdness_constraint: Optional[float] = None
    audio_weight: Optional[float] = None
    variety: Optional[int] = None
