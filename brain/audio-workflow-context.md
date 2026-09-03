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

## Real SFX / music assets (MMAudio, added 2026-09-03)

- **MMAudio** (~/Projects/MMAudio, large_44k_v2, CVPR 2025, MIT code /
  CC-BY-NC weights) now generates real SFX/atmos/music beds into
  assets/{sfx,atmos,music}/ — NO more ffmpeg sine-tone fallbacks.
- Runs in the VoxCPM venv: `~/Projects/VoxCPM/.venv/bin/python`.
- Usage gotchas (all hit live):
  - Generate under `torch.inference_mode()` — autograd errors otherwise.
  - `torchaudio.save` is BROKEN (torchcodec vs system ffmpeg 9 mismatch).
    Save with `soundfile` after `.cpu()[0].squeeze().numpy()`.
  - Prompt must say "no voice / no music" via negative_text for SFX.
  - Models auto-download (~4GB main + CLIP + bigvgan) to ~/.cache/huggingface
    and ~/Projects/MMAudio/{weights,ext_weights}/.
- Generator scripts: ~/Projects/MMAudio/gen_assets_mmaudio.py (sfx/atmos),
  gen_music_mmaudio.py (music leitmotifs).
- Music leitmotif convention: assets/music/<leitmotif-slug>.wav where
  leitmotif names are defined in the story frontmatter (e.g. chen_theme,
  finch_curiosity, entity_pulse, perihelion_hum).

## Room tone / ambience beds (2026-09-03)

- **General-purpose library** now lives in `assets/atmos/` (31 beds): indoor
  room tones (quiet/office/cafe/library/basement), weather (rain, rain-on-
  window, wind, storm, ocean, forest, thunder, crickets, snowfall, desert),
  city/harbor, sci-fi (spacecraft, alien jungle, cavern), and drama moods
  (tension-room, hospice-ward) plus the Cartographer space-station hums.
  Generated by `scripts/audio/tools/gen_general_atmos.py` (MMAudio) and
  normalized by `scripts/audio/tools/canonicalize_assets.py` to 48 kHz /
  24-bit / stereo with a ~-22 dBFS RMS anchor so every bed lands consistently
  under the fixed 0.22 mix gain (~-34 dB in a bed-only zone — audible but not
  loud; above the gate_ambience.py -40 dB floor).
- **Fuzzy resolution**: storyteller's `_resolve_sound` for atmos now consults
  `scripts/audio/tools/room_tone_resolver.py` — `[ATMOS: rain on tin roof]`
  resolves to `assets/atmos/rain-on-window.wav`, `[ATMOS: city street]` to
  `city-street.wav`. Unknown cues fall back to the default room-tone bed
  (`roomtone-indoor-quiet.wav`) instead of silence or brown noise.
- **silence.wav is intentional digital silence** for `[ATMOS: silence]` — the
  RMS anchor explicitly skips it (do not re-anchor).

## EQ / frequency management (added 2026-09-03)

**Gate: `scripts/gates/gate_eq.py`** — the spectral-health companion to
gate_loudness.py. Loudness (LUFS/TP/LRA) can pass while the spectrum is
muddy or lacks intelligibility. gate_eq measures energy in bass (60-250),
low-mid (250-500), intelligibility (1k-4k), sibilance (5k-8k), and the
spectral centroid, across 5 windows (10/30/50/70/90%) and FAILS on the
worst one.

Targets (calibrated on real repo files, Hann-windowed):
- narration: intel ≥ 10%, mud ≤ 65%, centroid 450-4000 Hz
- drama: intel ≥ 8%, mud ≤ 65%, centroid 450-4200 Hz
- sibilance > 15% → WARN (de-ess candidate)

**CRITICAL methodology (Ruling 2026-09-03-02):** ALWAYS apply a Hann window
before an FFT. An unwindowed FFT produced a false "catastrophic mud" reading
on the Cartographer v3 file (reported 463 Hz centroid / 5% intelligibility
when the windowed truth is 24-49% intel / ~2100 Hz). Spectral leakage from
DC + low room-tone inflates bass bins. Any spectral claim without windowing
is not trustworthy.

Run:
```bash
python3 scripts/gates/gate_eq.py <audio-or-campaign-dir>   # dir scans all audio
python3 scripts/gates/gate_eq.py path/to/file.mp3          # single file
python3 scripts/gates/test_gate_eq_regression.py           # regression (5 cases)
```
Wired into advance-stage.sh (voice/audio/audio-drama/story) + gate_preaudit.py.
