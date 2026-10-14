"""
Translate Suno request to internal parameters for ACE-Step and YuE2.
"""
from __future__ import annotations

from .spec import SunoGenerateRequest

def suno_to_aceplan(req: SunoGenerateRequest) -> dict:
    """
    Convert Suno request to a plan dict for ACE-Step (as used by acestep_plan.py).
    Expected keys: caption, lyrics, bpm, key, duration, timesignature.
    Missing fields get sensible defaults.
    """
    # Caption: combine prompt and style if both present
    parts = []
    if req.prompt:
        parts.append(req.prompt.strip())
    if req.style:
        parts.append(req.style.strip())
    caption = " ".join(parts).strip()
    if not caption:
        caption = "music"
    # Lyrics: use lyrics as-is (they may contain meta tags)
    lyrics = req.lyrics or ""
    # Instrumental: the request carries the flag explicitly. When set, the
    # lyrics box is empty and the caption must say so — an instrumental
    # rendered from a caption that never mentions vocals still comes back
    # with a vocal-shaped hole, and the caption is the only steering text
    # the engine sees. 8 of the 14 genre templates are instrumental
    # (chill-lounge, sentimental-piano, commentary-beds, the four elementals,
    # chiptune-8bit, epic-orchestral-boss); this is the path that lets them
    # render at all.
    if req.instrumental and not lyrics:
        caption = caption + ", instrumental, no vocals"
        # The renderer (acestep_plan.py) refuses a plan with empty lyrics
        # outright. Give it the canonical section header so the loader passes;
        # --allow-empty (already passed by the adapter) accepts the empty body.
        lyrics = "[Instrumental]\n"
    # Duration: default 30 seconds if not provided
    duration = float(req.duration) if req.duration is not None else 30.0
    # BPM: default 120; could derive from style_weight or variety
    bpm = 120
    if req.style_weight is not None:
        # map 0-1 to 60-180
        bpm = int(60 + req.style_weight * 120)
    # Clamp BPM to reasonable range
    bpm = max(30, min(240, bpm))
    # Key: default C major; we could leave empty
    key = req.style or "C major"
    # Timesignature: default 4/4
    timesignature = "4"
    return {
        "caption": caption,
        "lyrics": lyrics,
        "bpm": bpm,
        "key": key,
        "duration": duration,
        "timesignature": timesignature,
        "instrumental": req.instrumental,
    }

def suno_to_yue2(req: SunoGenerateRequest) -> dict:
    """
    Convert Suno request to kwargs for YuE2-3B generate endpoint.
    Expected: style, lyrics, seed, cfg_scale, abc, cot.
    """
    style = req.style or ""
    lyrics = req.lyrics or ""
    seed = req.seed
    # cfg_scale from style_weight? map 0-1 to 1-10 maybe
    cfg_scale = None
    if req.style_weight is not None:
        # style_weight 0-1 -> cfg_scale 1-10
        cfg_scale = 1.0 + req.style_weight * 9.0
    # abc from audio_weight? Not sure; we'll leave empty
    abc = None
    # cot: we can set "full" default
    cot = "full"
    return {
        "style": style,
        "lyrics": lyrics,
        "seed": seed,
        "cfg_scale": cfg_scale,
        "abc": abc,
        "cot": cot,
    }