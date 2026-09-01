# Audio Workflow — Shared Context (READ FIRST)

> Source of truth for every agent that touches speech synthesis:
> scriptwriter (writes scripts), storyteller (produces audio), voicebot (narrates).
> Last verified: 2026-09-01.

## The mandate (j_kro, 2026-09-01)

> "The scripting of the emotive language needs to be a natural part of the
> workflow whenever any agent is working with the speech model."

Emotive control is FIRST-CLASS, not an afterthought. Every script carries
emotion. Every synthesis honors it. Flat reads fail.

## Voice engines (verified 2026-09-01)

| Engine | Status | Emotion control | Use for |
|--------|--------|-----------------|---------|
| **VoxCPM2** | ✅ WORKS (uv env at ~/Projects/VoxCPM, F16 python path, 5.5 it/s) | **Voice Design** — natural-language description: gender, age, tone, emotion, pace | Drama, characters, emotive narration |
| **edge-tts** | ✅ WORKS (edge-tts binary in hermes venv) | None (flat) | Clean narration, fallback |
| **MiniMax** | ❌ NO KEY — never attempt | would-be per-line | — |
| **Chatterbox** | ❌ NOT RUNNING — never attempt | — | — |

## VoxCPM2 Voice Design — the emotive control

VoxCPM2 (openbmb/VoxCPM2, 2B params) creates voices from natural-language
description alone. The description goes in parentheses BEFORE the text:

```
(a young woman, late 20s, gentle but weary voice, speaking softly with a hint
of sadness)Who left this running?
```

The wrapper `voxcpm_generate.py` already supports `--voice-desc`. The
storyteller's `_voxcpm_voice_desc()` builds this from cast descriptions.

**Emotion words that work in Voice Design:** angry, sad, happy, fearful,
surprised, disgusted, calm, whisper, excited, tense, exhausted, defiant,
warm, cold, distant, hesitant, urgent, amused, sorrowful, hopeful.

**Emotion + pace combos:** "speaking fast, panicked", "slow, deliberate,
menacing", "soft, barely audible, trembling".

## The emotive scripting format (story.md)

Every script uses this markup. The storyteller parses it:

```markdown
---
title: My Drama
cast:
  Mara: "woman in her late 30s, steady, weary, quiet authority"
  Elias: "older man, warm, cracked voice, distant"
---

# Scene 1 — The Call

[calm]

Narrator: The console beeped once. Then it stopped.

Mara (angry): Who left this running?

Elias (fearful): I heard it too. It was answering.
```

Rules:
1. **Every scene has one emotion** — `[emotion]` line under the heading.
2. **Per-line emotion overrides** — `Speaker (emotion): text`.
3. **Voice Design descriptions** carry gender/age/tone/emotion/pace — the
   cast block sets the baseline, per-line emotion steers the delivery.
4. **SFX cues** — `[SFX: door creak]`, `[ATMOS: rain]`, `[MUSIC: tense]`.
5. **Pacing** — `[pause: 1.2]` for beats; blank lines separate takes.

## The emotion vocabulary

| Emotion | Voice Design hint |
|---------|-------------------|
| calm | steady, even pace, soft |
| angry | clipped, sharp, raised |
| sad | slow, lower pitch, breathy |
| fearful | fast, trembling, higher pitch |
| surprised | quick intake, rising pitch |
| disgusted | flat, sneering, deliberate |
| whisper | barely audible, close |
| tense | measured, tight, deliberate |
| excited | fast, bright, forward |
| exhausted | slow, dragged, fading |

## Duration spectrum (j_kro direction 2026-09-01)

Target lengths: 15 min, 30 min, 45 min, 1 hr, 1:30, 2 hr, 4 hr, 8 hr.

| Tier | Length | Structure |
|------|--------|-----------|
| Short | 15-45 min | one arc, 2-3 chars, tight scenes |
| Long | 1-2 hr | multi-arc, 3-5 chars, scene depth |
| Epic | 4-8 hr | serialized chapters, consistent cast, ambient depth |

Estimate: ~120-150 words of dialogue ≈ 1 minute of finished audio.

## Production workflow

1. **scriptwriter** writes `story.md` with emotive annotations (above format).
2. **storyteller** runs:
   ```bash
   cd ~/Projects/ai-content-pipeline
   uv run --project /home/j_kro/Projects/VoxCPM python3 scripts/audio/storyteller.py <story.md> -o <out-dir>/
   ```
   (VoxCPM must run in the VoxCPM uv environment — NOT the hermes venv.)
3. **storyteller** verifies: MP3 exists, duration matches target, every scene
   carried its emotion (check the routing log).
4. **deploy** to content.lan: copy to `nexus:/data/media/content-lan/audio-dramas/`
   (the site serves from nexus via sshfs bind).

## Provider routing (verified)

- Drama / characters → **VoxCPM** (Voice Design carries emotion)
- Narration / cleanup → **edge-tts** (flat, reliable)
- Log every scene's provider to `performance/model-routing.log`

## Pitfalls

1. **VoxCPM runs under uv** — `uv run --project /home/j_kro/Projects/VoxCPM`
   is the ONLY working invocation. The hermes venv python does NOT have
   voxcpm installed.
2. **Never check MINIMAX_API_KEY** — it doesn't exist.
3. **Never curl chatterbox** — it's not running.
4. **Emotion must survive synthesis** — verify per-scene emotion made it
   into the Voice Design description, not just the script annotation.
5. **A flat read kills the drama** — if the output sounds flat, the Voice
   Design description is too generic. Add emotion + pace words.
