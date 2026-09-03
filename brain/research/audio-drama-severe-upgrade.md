# Audio Drama Severe Upgrade — Research Findings

> **Date:** 2026-09-02
> **Scope:** Professional audio drama production standards + best 2026 open-source AI tooling per layer
> **Audience:** ai-content-pipeline storyteller.py redesign

---

## 1. Professional Radio Drama / Audio Drama Production Standards

### 1.1 The Mixing Hierarchy (Dialogue-First Architecture)

Professional audio drama is **dialogue-first**. The BBC, NRK, and EBU R128 specifications agree on a strict hierarchy:

| Layer | Role | Relative Level | % of Storytelling |
|-------|------|---------------|-------------------|
| **Dialogue/Narration** | Primary narrative carrier | Reference (loudest) | ~75% |
| **Sound Effects (hard/spot)** | Action punctuation | Slightly below dialogue | ~10% |
| **Music (beds/score)** | Emotional scaffolding | Well below dialogue | ~15% |
| **Ambience/Atmosphere** | Location establishment | Lowest (felt, not heard) | Continuous bed |

**Key rule:** Dialogue and narration contribute roughly 75% to overall storytelling, music ~15%, SFX ~10%. The moment a sound effect or music cue grows loud enough to obscure speech, the drama fails.¹ ²

### 1.2 Sidechain Ducking (Volume Automation)

The professional solution to dialogue/background balance is **sidechain ducking** (aka "ducking under"):

- When a character speaks → background (music + ambience) is automatically pulled down
- When dialogue stops → background swells back to fill silence
- Achieved via DAW envelope automation or sidechain compression
- Typically 6–12 dB of gain reduction on music beds during speech
- Should be subtle enough that listeners never consciously notice — they simply hear every word clearly while feeling surrounded by the world ¹ ²

**EBU R128 anchor-based normalization** (Supplement 4) describes using Dialogue Loudness as the anchor — all other elements are balanced relative to speech. This is the gold standard for drama.³

### 1.3 Sound Design Layering

Professional productions separate audio into distinct stem categories:⁴

- **D (Dialogue)** — All spoken word, clean, de-essed, not heavily reverb-wet
- **M (Music)** — Background music and score, dry and not ducked (for stems)
- **E (Effects)** — Foley and hard effects (doors, footsteps, gunshots)
- **A (Ambience/Atmos)** — Room tone, crowd noise, environmental beds

**Foley vs. synthesized SFX:**
- **Foley** = custom-recorded sounds that sync with character actions (clothing rustles, paper shuffling, keys jingling) — recorded specifically for the production
- **Hard/spot effects** = door slams, gunshots, phone rings — can be from libraries
- **Atmospheric backgrounds** = city traffic, forest, office hum — layer 2–4 sounds at various volumes for depth
- **Designed effects** = sounds that don't exist naturally, built from scratch (sci-fi, fantasy)

**Pro tip:** "Less is more. Once an atmosphere is established in the listener's mind, the effects can sit quietly in the background. They do not need to keep asserting themselves throughout the scene."¹

### 1.4 Room Tone & Ambience Beds

- Every scene needs a **continuous ambience bed** that establishes location
- Layer 2–4 different sounds at various volumes (e.g., city street: general traffic medium, distant sirens quiet, wind quiet, occasional car horn as punctuation)¹
- **Scene transitions:** First and last 5 seconds of a scene should play ambience only — lets the listener settle in/out of the world²
- **Crossfades:** 5-second overlap with "Equal Power Fade" shape prevents volume dips during transitions¹

### 1.5 Reverb & Spatial Consistency

**Critical rule:** All sounds in a scene must share similar reverb characteristics. If dialogue sounds like it's in a cathedral but footsteps sound dry and close, listeners notice the disconnect. Apply consistent reverb to place all sounds in the same acoustic environment.¹

Use **Impulse Responses (IRs)** for authentic spaces — short IRs for room presence, long tails for dramatic passages.⁵

### 1.6 EQ & Frequency Management

Standard voice processing chain for spoken word:⁵

1. High-pass filter at 60–80 Hz (remove sub rumble)
2. Gentle subtractive EQ to remove boxiness (200–400 Hz) and tame sibilance (4–8 kHz)
3. De-essing targeted to transients
4. Fast-attack compressor with slow release for body (or parallel compression)
5. Harmonic saturation / tape emulation at low settings (2–5%) to "glue"
6. Limiter as final safeguard — not to squash dynamics

**Music EQ under dialogue:** Cut mid-range on music tracks (250–5000 Hz) to create spectral space for dialogue to sit. High-pass filter music to remove low-end mud.¹ ⁵

### 1.7 Technical Delivery Specifications

| Parameter | Broadcast (BBC/EBU) | Podcast/Streaming | Our Target |
|-----------|---------------------|-------------------|------------|
| **Sample Rate** | 48 kHz | 44.1 or 48 kHz | 48 kHz |
| **Bit Depth** | 24-bit (BWF) | 16–24 bit | 24-bit |
| **Integrated Loudness** | -23 LUFS ±0.5 | -16 LUFS | -16 LUFS (podcast) / -23 (broadcast) |
| **True Peak** | ≤ -1.0 dBTP | ≤ -1.0 dBTP | ≤ -1.5 dBTP |
| **Loudness Range (LRA)** | 6–11 LU (drama) | 5–13 LU | 8–12 LU |
| **Format** | BWF/WAV interleaved stereo | MP3/AAC | 24-bit WAV master + MP3 distribution |
| **Channel Format** | A/B (L/R) stereo, mono-compatible | Stereo or mono | Stereo with mono-sum check |
| **Noise Floor** | Inaudible (< -60 dBFS) | Clean | < -60 dBFS |

**Sources:** BBC Radio Technical Spec 2022,⁶ NRK Delivery Standards,⁷ EBU Tech 3343,⁸ 11c Media broadcaster guide⁹

---

## 2. Best Open-Source AI Tooling Per Layer (2026)

### 2.1 Voice Acting / Dialogue (Per-Character Consistency)

| Model | License | Clone Speed | Languages | Strengths | Best For |
|-------|---------|-------------|-----------|-----------|----------|
| **Qwen3-TTS** (1.7B) | Apache 2.0 | 3-second zero-shot | 10 | VoiceDesign (text→voice), emotion control, streaming 97ms latency, batch consistency | ⭐ **Top pick for multi-character drama** |
| **Chatterbox Multilingual v3** | MIT | ~7s reference | 23+ langs + 4 dialects | Beat ElevenLabs 63.75% in blind A/B, PerTh watermarking, paralinguistic tags ([laugh], [cough]) | Broad language coverage, watermark compliance |
| **F5-TTS** | CC-BY-NC-4.0 | ~10s reference | EN, ZH | Highest raw quality (9/10) | English/Chinese quality-first |
| **XTTS-v2** (Coqui) | CPML | ~6s reference | 17 | Mature ecosystem, multilingual default | Established workflows (non-commercial) |

**Recommendation:** **Qwen3-TTS** is the clear winner for our pipeline:
- Apache 2.0 (clean commercial license)
- **VoiceDesign** — generate character voices from text descriptions ("deep raspy British male", "elderly woman with a soft Scottish lilt")
- **Three-Lock consistency** (voice + seed + per-emotion overrides) — every line from a character has identical timbre across a full production¹⁰
- Batch all character lines in a single model call with word-level alignment timestamps²
- 1.7B model is expressive; 0.6B fits tight hardware

**Multi-character engineering:** Per-character voice casting with distinct pitch, pace, accent. Concatenate all of a character's lines and synthesize together in one model call for maximum consistency.²

### 2.2 Sound Effects (SFX)

| Model | License | Output | Strengths | Best For |
|-------|---------|--------|-----------|----------|
| **MMAudio Large 44k v2** (CVPR 2025) | MIT | 44.1kHz, ≤10s clips | Text/video→audio, 1.23s for 8 clip, SOTA quality | ⭐ **Top pick for spot SFX** |
| **Stable Audio Open 1.0** | Stability AI Community | 44.1kHz, ≤47s | Text→audio, SFX/ambient/foley, fine-tunable | Long-form ambient beds, fine-tunable |
| **ACE Step** (ComfyUI) | Varies | 48kHz+ | Music + SFX in one, ambient generation | Ambient beds >47s |
| **Woosh** (Sony Research) | Apache 2.0 / CC-BY-NC | Multi-sample | Text→audio foundation model, CLAP conditioning | High-quality open SFX |
| **AudioGen** (Meta) | MIT | 16kHz | Environmental sounds, public SFX trained | Background ambiences |
| **HunyuanVideo-Foley** | Apache 2.0 | 48kHz | Video→audio, SOTA on benchmarks | Video-aligned SFX (overkill for audio-only) |
| **MiDashengLM-Gen** | Apache 2.0 | 16kHz | Unified speech+music+SFX+env in one model | Experimental: full scene generation |

**Recommendation:** Use **three SFX engines, auto-routed by duration** (as aeon-radio-drama does):¹⁰
- ≤10s: **MMAudio Large 44k** (primary — best quality)
- 10–47s: **Stable Audio Open 1.0**
- 47s+: **ACE Step** (ambient beds)

**Alternative/backup:** Freesound.org (CC-licensed, 500k+ sounds) for common effects like doors, footsteps, weather — still essential for sounds AI models handle poorly.¹

### 2.3 Music Beds (Instrumental Under Dialogue)

| Model | License | Output | Strengths | Best For |
|-------|---------|--------|-----------|----------|
| **MusicGen (Stereo)** | MIT / Apache 2.0 | 32kHz, up to ~30s | Text→music, melody conditioning, open-source | ⭐ **Top pick for BGM beds** |
| **Stable Audio Open** | Stability AI Community | 44.1kHz stereo, ≤47s | Instrumental loops, ambient textures, sound design | Loops, beds, short ambient |
| **ACE Step** | Varies | 48kHz | Full music generation, long-form | Cinematic scores |
| **SongGeneration v2 (LeVo 2)** | Research only | Multi-lingual | Commercial-grade with 4B model, `--bgm` flag for pure music | Chinese/EN commercial quality |
| **SongGen** | Research only | EN only, 30s | Lyrics + music, dual-track mode | Songs with vocals |

**Recommendation:** **MusicGen (medium or large, stereo variant)** for instrumental beds under dialogue:
- Pure instrumental (no vocals — we generate those separately via TTS)
- 32kHz output, up to ~30s per segment (crossfade segments for longer)
- Melody conditioning lets you reference a style/tempo
- Can batch-generate variations to pick from
- Open-source, runs locally, no API costs

**For longer beds:** Generate 30s segments and crossfade-loop with Stable Audio Open or ACE Step.

**Prompt strategy:** Be specific — "mellow ambient background with warm synth pads, 80 bpm, dreamy reverb, no melody, underscore for dialogue" works far better than "background music."¹¹

### 2.4 Mastering (LUFS, EQ, Compression, Limiting)

| Tool | Type | License | Strengths |
|------|------|---------|-----------|
| **Keel** | Automix + automaster | AGPL-3.0 | Deterministic stem balancing, exact LUFS target, 4x oversampled true-peak limiter, PASS/FAIL compliance report |
| **CALP** | Content-aware loudness | Open source | Preserves dynamics, multiband shaping, no destructive brickwall |
| **damp** | Limiter + mastering engine | Commercial (free tier) | 6 mastering algorithms, 38 presets, phase-aware look-ahead limiting |
| **oXygen** | JUCE mastering plugin | BSD-3 | 15-band EQ, multiband comp, stereo imager, Master Assistant, Reference Match |
| **ffmpeg-normalize** | Batch loudness | GPL-3.0 | EBU R128 two-pass, presets (podcast/streaming), simple |
| **audio-mastering-mcp** | MCP server + ffmpeg chain | Open source | Full chain: EQ → comp → multiband → saturation → stereo → limiter → 2-pass loudnorm |
| **LUFSNormalizer** | Batch normalization | Commercial (free tier) | 10 presets, BWF/iXML metadata, watch folder, parallel |
| **bravoh-loudness** | TypeScript meter | MIT | BS.1770-4 verified, zero-deps, EBU conformance suite |

**Recommendation — our mastering chain:**
1. **ffmpeg-normalize** or **pyloudnorm** for two-pass EBU R128 measurement + linear normalization to -16 LUFS
2. **damp** or **CALP** for transparent true-peak limiting at -1.5 dBTP
3. Optional: **oXygen** (VST3) for manual EQ/compression tweaks if needed

**Critical:** Don't use ffmpeg `loudnorm` alone — it's a blunt instrument. Combine with true-peak limiting and ideally multiband processing. The aeon-radio-drama pipeline's chain (alimiter → sidechaincompress → loudnorm) is close but should be augmented with proper oversampled true-peak limiting and pre-EQ.¹⁰

---

## 3. How Multi-Voice Scenes Should Be Engineered

### 3.1 Per-Character Model Strategy

**Best practice (from Dramarrator research and aeon-radio-drama):**² ¹⁰

1. **Define character voice profiles** at production start (not per-line):
   - Qwen3-TTS: VoiceDesign from text descriptions OR clone from 3–30s reference WAV
   - Three-Lock: voice + seed + per-emotion overrides
   - Store as reusable `voice_clone_prompt` (not re-extracted per line)

2. **Batch all lines per character** in a single model call:
   - Concatenate all of a character's dialogue
   - Synthesize together → word-level alignment timestamps split back
   - Ensures consistent timbre across the entire production

3. **Per-line emotional control via instructions:**
   - Append emotion/label to base instruct: `"speak softly, with a hint of fear"`
   - Inline delivery notes from script cues (shouting, whispering, breathless)

4. **Quality scoring per take:**
   - UTMOSv2 MOS prediction (1–5 scale)
   - If below threshold, regenerate (up to 5 takes) and keep best

### 3.2 Ensemble Scene Rendering

- **Record/render characters individually** (isolated stems) — never together
- Apply **consistent reverb** to all characters in a scene (same acoustic space)
- **Pan characters subtly** L/R to differentiate (but keep centered enough for mono compatibility)
- Keep **low frequencies mono** (bass centered), widen only highs/ambience
- **Room tone/ambience** sits under the entire scene continuously

---

## 4. Audiobook Production Craft — The Target Standard for Smoothness & Clarity

> **Why audiobooks:** j_kro explicitly requested researching how audiobooks work. The audiobook model (ACX/Audible, BBC Audio, Penguin Random House Audio) is the single best reference for **smoothness, clarity, and intelligibility** in narrated audio. Audiobook production standards are stricter than radio drama in key areas (noise floor, RMS consistency, room tone, mastering chain) while sharing the same dialogue-first principles.

### 4.1 ACX/Audible Technical Requirements (The De Facto Industry Standard)

ACX (Audiobook Creation Exchange) specifications are the most demanding and widely adopted technical standard for spoken-word audio. Meeting ACX specs means you pass virtually every other platform.⁵ ⁶ ⁷

| Requirement | ACX Spec | What It Measures |
|-------------|----------|------------------|
| **RMS Loudness** | -23 dB to -18 dB RMS per file | Average perceived volume across the whole file |
| **Peak Level** | ≤ -3 dBFS | Loudest single sample (headroom against clipping) |
| **Noise Floor** | ≤ -60 dB RMS | Background hiss/hum during silence |
| **Sample Rate** | 44.1 kHz | Do NOT submit at 48 kHz — will be rejected or downconverted with artifacts |
| **Bit Rate** | 192 kbps minimum CBR | Constant Bit Rate (VBR rejected even at higher averages) |
| **Format** | MP3 (mono or stereo, consistent) | All files same channel format |
| **Room Tone (Opening)** | 0.5–1.0 seconds | Natural silence before speech begins |
| **Room Tone (Closing)** | 1.0–5.0 seconds | Natural silence after final word |
| **File Structure** | One file per chapter/section | Max 120 min per file (build to 78 min for wider compatibility) |

**Key insight:** AI-generated audio has a noise floor below -90 dB RMS by default (no room noise, no mic hiss), far exceeding the ACX -60 dB requirement. The hardest part of ACX compliance for human narrators is trivially satisfied by AI.⁵

### 4.2 The ACX Mastering Chain (Step-by-Step)

This is the canonical mastering chain for professional audiobook production:⁸ ⁹

1. **Noise reduction** (if recording yourself): Capture noise profile from room tone, reduce gently — over-reduction sounds worse than mild hiss
2. **High-pass filter** at 60–80 Hz: Removes rumble, plosive energy that eats headroom
3. **EQ** (subtle): Cut mud 200–400 Hz, de-ess 4–8 kHz, gentle presence boost 2–4 kHz
4. **Compression** (light, 2:1–3:1): Evens out delivery so RMS lands in target window without peaks spiking. Ratio 2:1–3:1, moderate attack/release
5. **Loudness normalization**: Bring RMS to -20 dB (midpoint of ACX window)
6. **Peak limiting**: Final limiter at -3 dB ceiling catches any transient that escapes compression

**Critical:** Apply limiter LAST, after compression. If you compress after limiting, new peaks exceed the ceiling. Order matters.⁸

### 4.3 Character Introduction & Voicing in Audiobooks

**How professionals handle character introduction and distinction:**¹⁰ ¹¹ ¹² ¹³

#### The Narrator/Character Divide
- **Narrator voice**: Steady, neutral, easy to listen to for hours. Carries description, action beats, and dialogue tags ("she said"). Should be warm, clear, unhurried — never theatrical or heavily accentented (gets exhausting over a full book)
- **Character voices**: Only appear inside dialogue. Distinct from narrator AND from each other. The moment a new voice speaks, the listener should know who changed without being told

#### Character Voice Casting Principles
Professional narrators use a hierarchical approach with multiple "sliders":

| Dimension | What It Does | Example |
|-----------|-------------|---------|
| **Pitch** | High, medium, low baseline | Mentor = low, teenager = higher |
| **Pace** | Speech rate (words/min) | Nervous = faster, weary = slower |
| **Resonance/Placement** | Head, chest, mask, throat | Villain = chest resonance, scholar = head |
| **Texture** | Breathy, booming, silky, gravelly | Rogue = gravelly, noble = smooth |
| **Accent** | Regional/international (use sparing) | One British character among Americans |
| **Verbal Tics** | Unique phrases, filler words, habits | "Well now..." / "Indeed." |

**Key principle: Contrast beats realism.** Two "correct" voices that sound alike are worse than two slightly stylized ones that are clearly different. The test: "When these two trade lines with NO dialogue tag, can I still tell them apart?"¹⁰ ¹¹

#### How Many Distinct Voices?
- **Sweet spot: 3–5 distinct character voices + narrator** for most books¹⁰ ¹²
- Comfortable listening tops out around 6–7 voices
- Rank characters by **line count**, not plot importance — a chatty sidekick present every chapter needs a voice more than a hero who appears twice
- Minor characters with 1–2 lines can share the narrator's voice

#### Character Documentation (The "Character Voice Bible")
Before recording, professional narrators create a reference document for each character:¹² ¹³

```
CHARACTER: [Name]
VOICE: [Voice ID or clone reference]
PACE: [Baseline speed, variations for emotional scenes]
PITCH: [High/Medium/Low + specific notes]
PRONUNCIATION: [Names/words they use often]
NOTES: [Personality, how they sound alongside other characters]
```

**For AI narration:** This maps directly to per-character voice profiles with:
- Qwen3-TTS voice design parameters OR clone reference
- Pace/emotion overrides per scene
- Pronunciation dictionary (critical for invented names/places)
- Documented contrast notes ("deeper than James", "faster than Sarah")

#### The Introduction Problem
When a new character first speaks, the listener has no prior auditory reference. Best practices:
- **First appearance:** Slightly more distinct delivery to "set" the voice in the listener's mind
- **Dialogue tags in the manuscript** ("said Marcus") are your friend — they tie a name to a voice on first meeting
- **Avoid untagged rapid exchanges** with new characters — listener loses the thread after 4–5 volleys

### 4.4 Pacing in Audiobook Production

Professional audiobook pacing conventions:¹⁰ ¹⁴

- **Narration pace:** Steady, conversational — roughly 150–160 words per minute for fiction, 130–150 for non-fiction
- **Dialogue pace:** Slightly faster and more energetic than narration to signal "someone is speaking"
- **Scene transitions:** 1–2 second pause between paragraphs/scenes — lets the listener "reset" into the new context
- **Chapter transitions:** 2–5 seconds of silence (room tone) between chapters
- **Punch-and-roll recording:** Narrators correct errors on the fly, maintaining flow — for AI, this maps to quality scoring + regeneration

**The pacing problem in current storyteller.py:** No consistent pacing model. Each line is synthesized independently with no awareness of the surrounding lines' tempo or emotional arc. Professional audiobooks have GLOBAL pacing coherence.

### 4.5 Scene Transitions & Smoothness

**Why transitions are where amateur productions die:**¹⁵ ¹⁶

Professional audiobook scene/transition techniques:

1. **Crossfade between scenes:** 2–5 second overlap with Equal Power fade shape — not hard cuts
2. **Consistent room tone under scene:** Ambient bed continues across the transition so the listener never hears "dead air"
3. **Context-aware pacing gaps:** Insert trailing silence (1.2s) between scenes so episode transitions breathe
4. **Emotional arc bridging:** Don't cut from high drama to quiet reflection instantly — brief musical/ambience cue smooths the emotional transition
5. **Music bed crossfade:** When music mood changes (e.g., tension → relief), crossfade 3–5 seconds rather than hard switch

**For AI audio dramas:** This is where sidechain-ducked ambient beds + generated musical transitions make the difference between "stitched clips" and "immersive world."

### 4.6 Intelligibility — The #1 Rejection Reason

ACX and Audible reject audiobooks for intelligibility failures more than any other reason:⁵ ⁶ ⁷

- **Volume inconsistent between chapters:** Different recording sessions at different levels → listener constantly adjusting volume. Fix: Master every chapter through the SAME chain to the SAME target
- **Mouth noise and artifacts:** Clicks, plosives, excessive breath sounds. AI narration eliminates this entirely
- **Music/SFX too loud under dialogue:** Sidechain ducking solves this
- **Wrong RMS target:** Too quiet = listener cranks volume and hears noise floor. Too loud = fatiguing and clips
- **Missing room tone:** Dead digital silence at chapter boundaries sounds jarring and unprofessional

**The storyteller.py intelligibility gap:** The current pipeline has no RMS normalization, no sidechain ducking, no room tone, and no quality scoring. Each line is independently generated and concatenated with hard cuts. This produces the exact failure pattern j_kro described: "volume changes were bad/inconsistent," "segments hard to hear," "pacing was a mess."

### 4.7 Audiobook Structure & File Organization

Professional audiobook deliverables:² ⁵

- **Opening credits:** "This is [Title] written by [Author], narrated by [Narrator]." (Separate file)
- **Chapter files:** One MP3 per chapter, numbered sequentially, with room tone at head/tail
- **Closing credits:** "End of [Title]..." with finality statement. (Separate file)
- **Retail sample:** First 1–5 minutes, representative, no spoilers
- **File naming:** `ID_NofM.mp3` (Google Play) or `Chapter_01.mp3` per distributor convention

**For audio dramas:** Same structure per episode — opening title sequence (with music), scene/chapter files, closing credits. The "episode" is the container; "scenes" are the chapters.

### 4.8 Summary: What Audiobook Craft Teaches Us

| Problem | Audiobook Solution | Our Implementation |
|---------|-------------------|-------------------|
| Characters not introduced | Character voice bible + distinct casting + dialogue tags | Per-character profiles with documented contrast |
| Pacing is a mess | Global pace model + scene-aware pauses + consistent room tone | Pace normalization + transition gaps |
| Volume inconsistent | Two-pass RMS normalization + ACX chain per file | Two-pass EBU R128 + true-peak limiting |
| Segments hard to hear | Sidechain ducking + presence EQ + noise floor control | Sidechain music under speech + HPF + noise gate |
| Transitions jarring | Crossfades + ambient bed continuity + emotional bridging | 5s crossfades + continuous ambience + EQ-matched reverb |

---

## 5. What a Pro Audio Drama Sounds Like (Technical)

| Spec | Value | Notes |
|------|-------|-------|
| Sample Rate | **48 kHz** | Broadcast standard (BBC, NRK, EBU) |
| Bit Depth | **24-bit** | Production masters; 16-bit minimum for distribution |
| Integrated Loudness | **-16 LUFS** (podcast) / **-23 LUFS** (broadcast) | EBU R128 compliant |
| True Peak | **≤ -1.5 dBTP** | Headroom for lossy codec transients |
| Loudness Range | **6–12 LU** | Drama: 6–11 LU; preserves dynamic storytelling |
| Stereo Width | Compatible with mono | Side signal ≤ Mid signal; mono-sum check essential |
| Noise Floor | **< -60 dBFS** | Clean recording, no hiss/hum |
| Frequency Response | 20 Hz – 20 kHz | Full bandwidth, gentle HPF at 60–80 Hz for voice |
| Dialogue-Music Separation | **≥ 4 LU** minimum gap | Music always sits well under speech |
| Reverb Consistency | Same IR per scene | All elements share acoustic space |
| Fades/Crossfades | 5s crossfade, Equal Power shape | Smooth transitions between scenes |

**Pro productions to reference:** BBC Radio Dramas (gold standard), The Magnus Archives, The White Vault, Wolf 359, Welcome to Night Vale.¹

---

## 6. Existing Open-Source Audio Drama Pipelines

### 5.1 aeon-radio-drama (AEON-7) — ⭐ **Top Pick**

**URL:** https://github.com/AEON-7/aeon-radio-drama

> Full-pipeline radio drama / audiobook production. From JSON script → mastered audio. Multi-character TTS (Qwen3) → ACE Step music → MMAudio/SAO/ACE-Step SFX (auto-routed by duration) → sidechain-ducked loudness-normalized mix.

**Why it's the best model for our upgrade:**
- Same stack we recommend (Qwen3 + MMAudio + Stable Audio + sidechain)
- Three-Lock voice persistence (voice + seed + emotion overrides)
- Sidechain-ducked mix bus: music drops ~12 dB under speech
- EBU R128 −16 LUFS / −1.5 dBTP / LRA 11
- Per-stage idempotency (re-runs skip rendered work)
- Standalone helpers: `music_mixer.py`, `sfx_maker.py`
- MIT licensed, Python, ComfyUI-based

**Our pipeline is currently ~70% of aeon-radio-drama. The gap:**¹⁰
- ❌ No sidechain ducking
- ❌ No true-peak limiting
- ❌ Synthesized SFX via ffmpeg sine sweeps (not AI-generated)
- ❌ No ambient beds
- ❌ No per-character voice persistence (re-extracts per line)
- ❌ No quality scoring/regeneration

### 5.2 Other Notable Pipelines

| Pipeline | Stack | Notes |
|----------|-------|-------|
| **auditorium** (KrishnaGarg27) | GPT-4.1 + ElevenLabs API + ffmpeg | Full-stack web app; uses ElevenLabs for TTS/SFX/Music; sidechain + presence EQ; closed-source APIs ¹² |
| **xil-pipeline** | ElevenLabs API + ffmpeg | Markdown script → podcast MP3; DAW layer export; API-dependent ¹³ |
| **radio-drama-generator** | llama.cpp + OuteTTS/Parler | CPU-only, lightweight; proof-of-concept quality ¹⁴ |
| **ComfyUI-OldTimeRadio** | IndexTTS2 + Kokoro + Stable Audio 3 + LLM | Full radio-drama video; ComfyUI-based; 48 kHz master; frozen audio-first architecture ¹⁵ |
| **PocketVerse** | GPT-4o + ElevenLabs + ffmpeg | Serialized audio drama with continuity; 8-min episode in 10s via parallel chunks ¹⁶ |

**Verdict:** aeon-radio-drama is the closest open-source analogue to our pipeline and should be the primary reference for our severe upgrade. Our storyteller.py has the script parser and structure but lacks the modern AI stack, mixing quality, and broadcast compliance.

---

## 7. Ranked Recommendations (By Impact)

### 🔴 Critical (Do First)

1. **Replace TTS with Qwen3-TTS (1.7B)** — Apache 2.0, VoiceDesign for character creation, 3-second cloning, batch consistency, emotion control. This single upgrade transforms voice quality.¹⁷

2. **Implement sidechain ducking on music/ambience** — Use ffmpeg `sidechaincompress` with speech as key input. Music drops 8–12 dB during dialogue. Without this, dialogue is always competing with beds.¹⁰

3. **Upgrade SFX from ffmpeg sine sweeps → MMAudio + Stable Audio Open** — AI-generated SFX instead of synthesized beeps. MMAudio for ≤10s spot effects, SAO for longer ambiences.¹⁸

4. **Implement two-pass EBU R128 loudness normalization + true-peak limiting** — Target -16 LUFS (podcast) / -23 (broadcast), True Peak ≤ -1.5 dBTP. Use ffmpeg-normalize (two-pass) + damp/CALP (oversampled limiter).¹⁹ ²⁰

### 🟠 High Impact

5. **Add continuous ambience beds per scene** — Layer 2–4 ambient sounds at varying volumes. Establishes location. Crossfade scene transitions (5s, Equal Power).¹

6. **Implement per-character voice persistence (Three-Lock)** — voice + seed + emotion overrides. Batch all lines per character in one model call for consistency. No more per-line voice drift.¹⁰ ²

7. **Add quality scoring + auto-regeneration (UTMOSv2)** — Score each TTS take; regenerate up to 5× if below MOS threshold. Eliminates "lucky dip" quality.²¹

8. **Force all audio to canonical 48 kHz / stereo / 24-bit before mixing** — Fixes sample-rate-cross distortion that plagues ffmpeg pipelines.¹⁰

9. **Implement per-scene reverb consistency** — All elements in a scene share the same acoustic space via IR or consistent reverb parameters.¹

### 🟡 Medium Impact

10. **Replace ffmpeg concatenation with proper crossfades** — 5s Equal Power crossfade between scenes, not hard cuts.¹

11. **Add music generation (MusicGen stereo)** — Generate instrumental beds that fit emotional context instead of stock loops. Crossfade 30s segments for longer cues.¹¹

12. **Implement EQ chain on dialogue** — HPF 60–80 Hz, cut 200–400 Hz mud, de-ess 4–8 kHz, presence boost 3–5 kHz for intelligibility.¹ ⁵

13. **Add Freesound.org library integration** — For common SFX AI handles poorly (doors, footsteps, keys). CC-licensed, 500k+ sounds.¹

14. **Generate dialogue, music, SFX on separate stems** — Enables post-production remixing, platform-specific masters (D/M/E/A).⁴

15. **Mono-sum compatibility check** — Ensure stereo mix collapses to mono without phase cancellation. Critical for smart speaker/listening on phone.⁶ ⁷

### 🟢 Polish

16. **BWF metadata embedding** — Loudness measurements, ISRC, iXML chunks for broadcaster acceptance.²²

17. **Add paralinguistic tags** — `[laugh]`, `[cough]`, `[whisper]` via Chatterbox Turbo for realism.²³

18. **Reference Match mastering** — Match tonal balance to a professional audio drama reference track (e.g., BBC production).²⁰

19. **Loudness Range (LRA) targeting** — Keep LRA 6–12 LU for drama (not over-compressed).²⁴

20. **Generate multiple takes/variation per cue** — 3–5 SFX variations, 3 music variations — curate best fit.

---

## Sources

1. Journalism University — Audio Drama Post-Production (2025) — https://journalism.university/audio-podcast/audio-drama-post-production-editing-mixing/
2. Dramarrator (arXiv 2026) — https://arxiv.org/html/2608.08349v1
3. Producing Audio Drama (Routledge, 2024) — https://www.routledge.com/Producing-Audio-Drama/p/book/9781032822860
4. EBU R128 Stems (D/M/E/A) — https://harmonica.live/studio-to-stream-how-to-prepare-mixes-for-broadcasters-vs-yo
5. Sound Design for Audio Dramas — Complete Guide — https://tommylawpi.com/sound-design-for-audio-dramas-complete-podcast-sound-guide/
6. BBC Radio Technical Spec (2022) — https://www.bbc.co.uk/commissioning/radio/documents/technicalspecificationradiojuly2022_v01.7.pdf
7. NRK Technical Delivery Standards — https://info.nrk.no/wp-content/uploads/2023/06/NRK-RadioTechnical-Delivery-Standards.pdf
8. EBU Tech 3343 Production Guidelines — https://tech.ebu.ch/docs/tech/tech3343v4_1.pdf
9. 11c Media — What Broadcasters Actually Want — https://11c.media/what-broadcasters-actually-want-when-you-deliver-audio/
10. aeon-radio-drama (AEON-7) — https://github.com/AEON-7/aeon-radio-drama
11. MusicGen (Meta AudioCraft) — https://github.com/facebookresearch/audiocraft
12. auditorium — https://github.com/KrishnaGarg27/auditorium
13. xil-pipeline — https://github.com/xilcmd/xil-pipeline
14. radio-drama-generator — https://github.com/stefanfrench/radio-drama-generator
15. ComfyUI-OldTimeRadio — https://github.com/jbrick2070/ComfyUI-OldTimeRadio
16. PocketVerse — https://github.com/chethanhrx/pocketverse
17. Qwen3-TTS — https://github.com/QwenLM/Qwen3-TTS
18. MMAudio (CVPR 2025) — https://github.com/hkchengrex/MMAudio
19. CALP — https://github.com/aston89/CALP-Content-Aware-Loudness-Processor
20. Keel — https://github.com/fcarvajalbrown/Keel
21. multivoice (Qwen3-TTS + UTMOSv2) — https://github.com/wcharliebrown/multivoice
22. LUFSNormalizer — https://github.com/vitaleaudio/LUFSNormalizer
23. Chatterbox TTS — https://github.com/resemble-ai/chatterbox
24. ffmpeg-normalize — https://github.com/slhck/ffmpeg-normalize
25. audio-mastering-mcp — https://github.com/ope-olatunji/audio-mastering-mcp
26. Woosh (Sony) — https://github.com/SonyResearch/Woosh/
27. AudioGen (Meta) — https://ai.meta.com/resources/models-and-libraries/audiocraft/
28. Stable Audio Open — https://stability.ai/news-updates/introducing-stable-audio-open
29. bravoh-loudness — https://github.com/ozzaii/bravoh-loudness
30. damp — https://github.com/bogware/damp
31. ACX Audio Submission Requirements — https://help.acx.com/s/article/what-are-the-acx-audio-submission-requirements
32. ACX Check Your Production Blog — https://www.acx.com/mp/blog/check-your-production-before-you-wreck-your-production
33. TomeVox ACX Requirements Guide 2026 — https://tomevox.com/blog-acx-requirements
34. Midsummerr Audiobook File Requirements 2026 — https://www.midsummerr.com/blog/audiobook-audio-file-requirements
35. Coharmonify Industry Standards for Audiobook Production 2026 — https://coharmonify.com/resource-articles/industry-standards-for-audiobook-production-in-2026/
36. ACX Audio Specs Explained (Narration Box) — https://narrationbox.com/blog/acx-audio-specs-explained-2025-2026
37. Auphonic RMS Loudness for Audible/ACX — https://auphonic.com/blog/2026/01/15/rms-loudness-normalization-for-audible-acx/
38. Mastering.to Audible/ACX Guide — https://mastering.to/audible
39. AudioUtils ACX Workflow — https://audioutils.com/guide/audio-for-audiobooks
40. Jay Myers Voiceover — How Audiobook Narrators Voice Characters — https://www.jaymyersvoiceover.com/blog-ideas/how-audiobook-narrators-make-characters-sound-distinct-believable-and-consistent
41. Suchavoice — Create Consistent Characters — https://www.suchavoice.com/blog/2019/08/01/create-consistent-characters/
42. Digibookstudio — Audiobook Script Preparation — https://digibookstudio.com/audiobook-script/
43. Coharmonify — Creating Character Voices For Fiction Audiobooks — https://coharmonify.com/resource-articles/creating-character-voices-for-fiction-audiobooks/
44. Pozotron — How to Prep an Audiobook for Recording — https://blog.pozotron.com/how-to-prep-an-audiobook-for-recording
45. Audie — How to Give Every Character a Different Voice — https://www.audie.ai/how-to-give-every-character-a-different-voice-in-your-audiobook
46. Audie — Narrator Voice vs Character Voices — https://www.audie.ai/narrator-voice-vs-character-voices-getting-dialogue-right
47. Vois — Creating Distinct Character Voices for Audiobooks — https://vois.so/blog/character-voices-audiobooks
