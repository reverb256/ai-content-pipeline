# Voice Acting — AI TTS Narration & Character Voice Engineering (2026-09-02)

> Meticulous reference for narration pacing, character voice design, emotional
> acting, and the storyteller.py pacing system. Every number is measurable.
> Complies with `brain/QUALITY_DOCTRINE.md` (spec + mechanical gate + scored
> review) and the stage specs `brain/stage-specs/voice.md` + `audio-drama.md`.

## 1. Narration pacing — words-per-minute by content type

Spoken audio is SLOWER than voice-over narration. Two distinct rates:

| Content type | Target WPM | Words/min | Source |
|---|---|---|---|
| **VO narration** (YouTube, faceless, single voice) | **150–165** | ~160 | voice.md stage spec, QUALITY_DOCTRINE |
| **Audio-drama dialogue** (multi-character, paced) | **120–140** | ~130 | audio-drama.md, storyteller.py |

**Duration math** (mechanical gate — count words, derive seconds):
```
narration_seconds = word_count / 160
dialogue_seconds  = word_count / 130
PASS if actual_duration >= expected * 0.90
FAIL if actual_duration < expected * 0.90  (truncation)
```

**Pacing rules for the script** (measurable before synthesis):
- Target **12–18 words per sentence** for narration; vary between 6-word and
  22-word sentences every 3–5 lines (measured by line).
- **No run-on sentences** > 25 words without a comma/pause break.
- Insert `[pause: N]` cues at paragraph boundaries and after rhetorical
  questions (1.0–2.0s). storyteller.py honors these as real silence.
- Insert `[pause: 0.5]` after short punch lines that need a beat.

## 2. Breath & pause placement (storyteller.py constants)

The pipeline inserts INTER-LINE GAPS by role change (not metronomic):

| Transition | Gap (seconds) | Constant |
|---|---|---|
| Same speaker, back-to-back | **0.28** | `GAP_SAME_SPEAKER` |
| New speaker answers | **0.42** | `GAP_NEW_SPEAKER` |
| Narrator beat | **0.55** | `GAP_NARRATOR` |
| After emotional line (angry/fearful/sad/whisper) | **0.30** (min) | `GAP_AFTER_EMOTION` |
| Explicit `[pause: N]` cue | N (story value) | `Cue.duration` |
| Scene trailing gap (default) | **1.20** | `SCENE_GAP` |

**Gate check** (ffmpeg silencedetect — from audio-drama.md):
```bash
ffmpeg -i audio.mp3 -af silencedetect=noise=-35dB:d=0.25 -f null - 2>&1 | \
  grep silence_duration | awk '{print $NF}'
```
PASS only if: at least one gap ≥ 0.9s (scene boundary) AND gaps are not
all identical. Uniform ~0.28s everywhere = FAIL (pacing bug).

## 3. Emphasis & rhetorical strategy

Emphasis is carried by **Voice Design description + emotion cue**, NOT by
CAPS or punctuation. storyteller.py builds Voice Design from:

```
"<cast baseline>, now <emotion_voice_desc>"
```

Example (from `_voxcpm_voice_desc`):
```
cast:  "a woman in her late 30s, steady, weary, quiet authority"
angry: "a woman in her late 30s, steady, weary, quiet authority,
         now speaking angrily — sharp, forceful, clipped"
```

**Rhetorical devices that work in audio** (add to script markup):
- **Rule of three** — list three items; the third carries the punch.
- **Contrast pause** — `[pause: 0.8]` before the turn/reversal.
- **Anaphora** — repeat the opening phrase 2–3 lines in a row.
- **Rising action** — shorten sentences toward the climax (words per
  sentence drops from ~18 → ~8).
- **Hook cadence** — first 7 seconds must contain ONE short sentence
  (≤ 8 words) + pattern interrupt.

## 4. Character voice design table

Voice Design = natural-language description in parentheses BEFORE text.
Format: `(gender, age, temperament + texture, emotion/pace)`.

| Archetype | Voice Design string | Pitch hint | Rate |
|---|---|---|---|
| Young hero (20s, earnest) | `a young man, early 20s, earnest and clear, a touch of wonder` | medium-high | 1.0 |
| Weary detective (50s, gruff) | `a gruff 50-year-old man, world-weary, slight smoker's rasp` | low | 0.95 |
| Warm elder (60s, kind) | `an older woman, warm and gentle, a soft southern lilt` | low-medium | 0.9 |
| Cold villain (40s, controlled) | `a cold, precise man, flat affect, measured and menacing` | low | 0.85 |
| Anxious sidekick (30s, nervous) | `a nervous man, hesitant, quick speech, higher pitch` | medium-high | 1.1 |
| Authoritative commander | `a steady, authoritative woman, clipped military diction` | medium | 0.95 |
| Whisper/secretive | `a hushed whisper, intimate and secretive` | low | 0.8 |
| Expressive narrator (default) | `a clear, expressive narrator` | medium | 1.0 |

**Contrast rule**: in any scene with N characters, the pitch/rate pair must
differ by ≥ 15% between each (measured: two characters at same pitch/rate =
indistinguishable → rewrite one's Voice Design).

## 5. Consistency across episodes (reusable config)

Store each character's Voice Design as a **cast entry in frontmatter** —
reusable across every story:

```yaml
---
title: The Last Signal
cast:
  Mara: "a woman in her late 30s, steady, weary, quiet authority"
  Commander Voss: "a gruff 50-year-old detective, world-weary, slight smoker's rasp"
  Elias: "an older man, warm, cracked voice, distant"
narrator_voice: English_expressive_narrator
model: speech-2.8-hd
speed: 1.0
---
```

**Identity lock**: the cast block is the SAME across all episodes of a
series. Never rewrite a character's baseline between episodes — only the
per-line emotion changes. If a character sounds different episode-to-episode,
the cast block drifted → revert to canonical copy.

## 6. Emotion → vocal parameter mapping

Emotion is delivered via `_EMOTION_VOICE_DESC` in storyteller.py + raised CFG:

| Emotion | Voice Design hint | CFG | Effect |
|---|---|---|---|
| happy | `a bright, cheerful voice, warm and upbeat` | 2.8 | faster, brighter |
| sad | `a soft, sorrowful voice, gentle and subdued` | 2.8 | slower, lower, breathy |
| angry | `a sharp, forceful voice, intense and clipped` | 2.8 | clipped, sharp |
| fearful | `a trembling, anxious voice, hushed and tense` | 2.8 | faster, higher, trembling |
| surprised | `a wide-eyed, startled voice, quick and bright` | 2.8 | rising pitch |
| disgusted | `a flat, repelled voice, cold and dismissive` | 2.8 | flat, deliberate |
| whisper | `a hushed whisper, intimate and secretive` | 2.8 | barely audible |
| tense | `a taut, strained voice, measured and tight` | 2.8 | measured, tight |
| excited | `a fast, bright voice, eager and forward` | 2.8 | fast, bright |
| exhausted | `a slow, dragged voice, fading and weary` | 2.8 | slow, dragged |
| calm | `a steady, even voice, composed and unhurried` | 2.0 | neutral baseline |
| neutral/narrator | `a clear, expressive narrator` | 2.0 | neutral |

**Prompt format per line**:
```
Speaker (emotion): spoken text here
```
or for narrator (no prefix), a bare line reads as narration with the
pending scene emotion.

**When to use a separate take**: if a line needs an emotion that contradicts
the scene's pending emotion, use `Speaker (different_emotion): text` to
override. If > 50% of a scene's lines override the scene emotion, the scene
heading emotion is wrong — fix the scene cue.

## 7. TTS model selection by job

| Job | Provider | Why | Config |
|---|---|---|---|
| Audio-drama, characters, emotive narration | **VoxCPM2** (self-hosted, GPU) | Voice Design carries emotion + identity | `quality=f16` (best), `q8` near-lossless, `q4` fastest |
| Clean VO narration, fallback, cleanup | **edge-tts** (hermes venv) | Flat, reliable, fast | no emotion control |
| MiniMax (API) | MiniMax `speech-2.8-hd` | per-line voice IDs | requires `MINIMAX_API_KEY` (NOT AVAILABLE — do not attempt) |
| Chatterbox | self-hosted `http://10.1.1.130:8004` | fallback for drama | NOT RUNNING — do not attempt |

**Provider routing** (from `audio-workflow-context.md`):
- Drama / characters → VoxCPM
- Narration / cleanup → edge-tts
- Log every scene's provider to `performance/model-routing.log`

**Seed / temperature for repeatability**:
- VoxCPM: deterministic per `voice_desc` string + text. Same input → same
  voice. CFG 2.0 (calm) or 2.8 (emotion) controls adherence strength.
- edge-tts: deterministic per voice + text + rate.

## 8. Multi-voice scene engineering

**Speaker alternation** — keep characters distinguishable:
1. **Tag every line** with `Speaker (emotion): text` — no untagged dialogue.
2. **Distinct Voice Design per character** (see §4) — ≥ 15% pitch/rate delta.
3. **Inter-line gap** auto-increases to 0.42s on speaker change (vs 0.28s
   same speaker) — gives each voice room.
4. **Narrator beats** land slower (0.55s gap) — narrator never collides with
   dialogue.

**Ducking / BGM levels** (storyteller.py `sidechain_mix`):
| Layer | Gain / Duck | Filter |
|---|---|---|
| Speech (centered) | 0 dB (reference) | none |
| Music bed | **gain=0.14**, ducks **12 dB** under speech | lowpass 2000 Hz, stereo-panned |
| Atmos bed | **gain=0.22**, ducks **12 dB** under speech | lowpass 4000 Hz, stereo-panned |
| SFX events | short sting at scene start | as-is |

**Sidechain**: speech feeds silent key → beds duck 12 dB with 25 ms attack,
450 ms release. Presence scoop at 500 Hz (−3 dB) on beds keeps voice clear.

**Final loudness normalization** (EBU R128):
```
loudnorm=I=-16:TP=-1.5:LRA=11
```
Output: 44.1 kHz stereo, libmp3lame q2.

## 9. Quality checks — listen-test rubric

Score 1–10 per criterion. Min pass = 7. Kill on any score ≤ 5.

| # | Criterion | Defect (FAIL) | PASS bar |
|---|---|---|---|
| 1 | **Completeness** | Any script line missing or out of order | All lines present, in order |
| 2 | **Duration match** | Actual < 90% of (words / rate) | Within ±10% |
| 3 | **Pacing** | Metronomic gaps (±0.05s variance), no scene breaths | Varied rhythm, ≥ 1 gap ≥ 0.9s |
| 4 | **Emotive accuracy** | Emotion cues don't land (flat read) | Listener identifies intended emotion |
| 5 | **Robotic cadence** | Machine-gun delivery, no sentence-length variation | Natural prosody, varied phrase length |
| 6 | **Clipped consonants** | Plosives (p/t/k) clip or distort | Clean transients, no crunch |
| 7 | **Upspeak** | Sentence-final pitch rise on declaratives | Declaratives fall; questions rise |
| 8 | **Mush-mouth** | Consonants swallowed, words unintelligible | Every word intelligible |
| 9 | **Silence gaps** | Mid-section silence > 2s (unintended) | No dead air > 2s inside a section |
| 10 | **Loudness** | Clipping, or < −25 dB mean | −20 to −30 dB mean, no clip |

**Duration-vs-wordcount sanity** (run before listen):
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 audio.mp3
# compare to: words / 160 (narration) or words / 130 (dialogue)
```

**Non-silence gate**:
```bash
ffmpeg -i audio.mp3 -af volumedetect -f null - 2>&1 | grep mean_volume
# expect −20 to −30 dB; −90 dB = silent (FAIL)
```

## 10. Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Generic Voice Design ("a person speaking") | Flat read, no identity | Add gender + age + temperament + emotion |
| Same Voice Design for all characters | Listener can't tell speakers apart | ≥ 15% pitch/rate delta per character |
| No `[pause:]` cues | No scene breaths, crashes together | Add 1.0–3.0s at scene boundaries |
| Metronomic uniform gaps | Robotic, listener fatigue | Use storyteller.py inter-line gaps (varied by speaker) |
| Emotion only in script annotation, not Voice Design | Emotion doesn't reach audio | Blend emotion into Voice Design string |
| Overriding CFG when calm | Unnecessary sharpness | Use CFG 2.0 for calm/neutral, 2.8 only for emotion |
| Music louder than speech | Voice buried | Music gain ≤ 0.14, atmos ≤ 0.22, 12 dB duck |
| Rewriting cast block between episodes | Character sounds different | Lock cast block, only change per-line emotion |

## 11. Sources

- `brain/QUALITY_DOCTRINE.md` — word budgets, 160 wpm, scored gates, bounded retries
- `brain/audio-workflow-context.md` — VoxCPM Voice Design, emotion vocabulary, provider routing
- `brain/stage-specs/voice.md` — narration stage contract, duration math, mechanical gate
- `brain/stage-specs/audio-drama.md` — dialogue pacing, scene-gap gate, completeness check
- `scripts/audio/storyteller.py` — all pacing constants (GAP_*, SCENE_GAP), sidechain mix, loudnorm, `_EMOTION_VOICE_DESC`, `_voxcpm_voice_desc`
