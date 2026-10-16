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
    # the engine sees. 8 of the 14 genre templates are instrumental; this is
    # the path that lets them render at all:
    #   chill-lounge, chiptune-8bit, commentary-beds, elemental-air,
    #   elemental-earth, elemental-fire, elemental-water, sentimental-piano
    # Measured census (grep -Ei 'is instrumental|leave the lyrics box empty'
    # music/prompts/*.md): 8 of 14. The previous list here named NINE by
    # wrongly including epic-orchestral-boss, whose template declares no
    # instrumental path ("Choir only — no solo lyrical singing") — routing it
    # down this branch would strip its defining element (card t_25a6499c).
    if req.instrumental:
        # The cue goes on the caption for EVERY instrumental request, not only
        # when the lyrics box is empty. Measured defect (card t_909069f0,
        # "variant D"): a caller that sends the genre's section tag sheet as
        # structure control silently LOST the cue, because the old condition
        # required empty lyrics. The caption is the only steering text the
        # engine sees, so "no vocals" has to be on it in both variants. The
        # check makes a repeat call idempotent.
        if "instrumental, no vocals" not in caption:
            caption = caption + ", instrumental, no vocals"
        if not lyrics:
            # The renderer (acestep_plan.py) refuses a plan with empty lyrics
            # outright. Give it the canonical section header so the loader
            # passes; --allow-empty (already passed by the adapter) accepts the
            # empty body.
            lyrics = "[Instrumental]\n"
    # Duration: default 30 seconds if not provided
    duration = float(req.duration) if req.duration is not None else 30.0
    # BPM. An EXPLICIT tempo wins. The style_weight mapping below is a
    # documented FALLBACK only: it repurposes Suno's style-ADHERENCE dial as a
    # tempo control, so a genre's anchor is reachable only by telling the
    # engine to follow the style less than its own template asks (measured:
    # sentimental-piano anchors 72 and needs style_weight 0.1; at the
    # template's own adherence it renders 156). t_25a6499c D1.
    bpm = None
    if req.bpm is not None:
        bpm = int(req.bpm)
    elif req.style_weight is not None:
        # map 0-1 to 60-180
        bpm = int(60 + req.style_weight * 120)
    if bpm is None:
        bpm = 120
    # Clamp BPM to reasonable range
    bpm = max(30, min(240, bpm))
    # Key. An EXPLICIT key signature wins; the default is a key signature too.
    # NEVER `req.style`: that is the genre's whole style caption (674 chars for
    # sentimental-piano) and acestep_plan.py passes this value straight to the
    # ACE node as `keyscale`. t_25a6499c D2.
    key = req.keyscale or "C major"
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