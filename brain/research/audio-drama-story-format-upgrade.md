# Audio Drama Story Format Upgrade — Research Findings & Recommendations

> **Date:** 2026-09-02
> **Author:** Research subagent
> **Purpose:** Recommend story.md format upgrades that force professional-quality audio dramas.
> **Sources:** BBC Writers Room (Scene/Cue/Taped Drama formats), Jellypod, ZenMic, Inworld AI Voice Design, Qwen3-TTS Voice Design, Hume Octave, Dubsmart voice science, Epic Scribe, Behind the Draft, Screenweaver, Latent Scholar (S3F framework), Midsummerr, Vois, Narration Box, Demodokos, Audie, AudioPod, Narratory, ScribeCount, Narrators Roadmap, StoryVox, and the existing in-repo craft docs (`brain/craft/storycraft.md`, `brain/craft/voice-acting.md`, `brain/stage-specs/audio-drama.md`).

---

## Executive Summary

The current `story.md` format is a **flat script container** — it captures *what is said* but not *how it should sound*, *why the scene exists*, or *whether the listener can follow*. Professional audio drama is not "prose read aloud"; it is a distinct medium with its own grammar. The format must **enforce** the craft constraints that separate amateur AI audio drama from professional radio drama.

The 23 recommendations below are organized into 6 layers:
1. **Structural craft** (scene/act architecture, hooks, transitions)
2. **Character introduction mechanics** (audiobook craft: narrator separation, name-tagging, contrast casting)
3. **Voice engineering** (distinctness, dimensions, consistency)
4. **Sound design** (levels, beds, silence as tool)
5. **Character craft** (arc, want/need, vocabulary lock)
6. **Mechanical gates** (parseable checks the format forces before synthesis)

Each recommendation states: the **gap** in the current format, the **professional standard** (with source), and the **format-level rule** to enforce it.

---

## 1. Structural Craft

### R1. Every scene must declare its ONE goal (reveal / escalate / decision)

| | |
|---|---|
| **Gap** | Current format allows scenes that "exist for vibe" — no check that a scene changes the listener's understanding, raises stakes, or forces a choice. |
| **Standard** | `storycraft.md` §3.1: "Every scene must have ONE of these goals: Reveal, Escalate, Decision." BBC: "Everything must earn its keep." |
| **Format rule** | Scene heading line MUST carry a goal tag: `# Scene 1 — The Call [goal: reveal]`. Parser rejects scenes without a valid goal. This forces the writer to know *why the scene exists* before writing dialogue. |

### R2. Cold-open is mandatory — first 7–15 seconds must state tension or payoff

| | |
|---|---|
| **Gap** | Current format has no constraint on opening. AI dramas routinely open with channel intros, "welcome back," or context-before-conflict — the fastest way to lose a listener. |
| **Standard** | BBC: "Radio has the fastest turn-off rate of all drama. Hit the ground running." `storycraft.md` §1: "Cold-open is MANDATORY for any content < 15 min." Jellypod: "Write the last three seconds of an episode first." |
| **Format rule** | First scene MUST carry `[cold-open]` tag. The first segment in the first scene must be ≤ 25 words (parser counts). If the first scene is narration-only with no tension statement, reject. |

### R3. Scene transitions must be causal (therefore / but), never "and then"

| | |
|---|---|
| **Gap** | Current format does not track scene-to-scene causation. Episodic, unlinked storytelling is the #1 structural failure mode. |
| **Standard** | `storycraft.md` §3.3: "Transitions MUST be one of two types: Therefore, But. Forbidden: 'And then'." |
| **Format rule** | After each scene heading, an optional `[link: therefore]` or `[link: but]` tag describes the causal chain from the previous scene. If missing, parser warns. This makes the writer *name* the causal mechanism. |

### R4. Act structure for serialized content (2-act minimum for ad-friendly breaks)

| | |
|---|---|
| **Gap** | Current format has no act structure. Podcast ad insertion and listener retention both require act breaks with hooks. |
| **Standard** | Rick Toscan (Backstage): "Episodes structured in two acts with a hook at the end of the first act to hold listeners through the ad." Screenweaver: "Cold opens, recaps, act-like scene clusters, ad breaks, and end tags." |
| **Format rule** | For serialized stories, frontmatter MUST declare `acts: 2` (or 3/5). Act breaks use `[act-break]` cue with a required `[hook]` tag on the last scene before the break. Parser validates that act-break scenes have rising tension (emotion tag ≠ calm). |

### R5. Scene length targets by tier (enforce word budget per scene)

| | |
|---|---|
| **Gap** | Current format has no per-scene word limit. Scenes can sprawl past 10 minutes (which BBC calls "eternity"). |
| **Standard** | `storycraft.md` §5.1: Audio drama Short = ~300 words/scene, Long = ~400, Epic = ~500. Toscan: "10 minutes is eternity — 10 seconds is forever." Epic Scribe: "Establishment 10-15%, Development 60-70%, Climax 10-15%, Transition 5-10%." |
| **Format rule** | Frontmatter declares `tier: short|long|epic`. Parser counts words per scene and warns if exceeding tier max. Scene heading can override: `# Scene 3 [words: 250]`. |

---

## 2. Character Introduction Mechanics (Audiobook Craft)

> **Why this section exists:** The production was rejected partly because characters were not introduced properly. Research into audiobook narration — where the same problem (who is speaking?) is solved daily at scale — reveals precise mechanics for introducing and distinguishing characters by voice alone. These must be REQUIRED, not optional, in the audio-drama format.

### How audiobook narrators introduce and distinguish characters

Professional audiobook narration solves the "who is speaking" problem through three coordinated mechanics:

| Mechanic | What it does | Source |
|----------|-------------|--------|
| **Narrator-voice separation** | The narrator is a distinct, neutral "anchor voice" that carries all prose, description, and dialogue tags ("she said"). Character voices only appear *inside dialogue*. This creates an immediate auditory binary: narrator = description, character = speech. | Audie: "The narrator is the anchor voice... dialogue tags are narration, not dialogue, so they belong in the narrator's voice, delivered flat and low, almost swallowed." |
| **Name-tagging at first appearance** | When a character first speaks, the narrator almost always uses their name in the dialogue tag ("said Marcus," "Elena whispered"). This anchors the voice-to-name mapping before the listener has to track it. After anchoring, tags can drop. | Audie: "Clean 'said Name' tags give speaker detection the best possible input." ScribeCount: "Character names in dialogue tags tie a name to a quote." |
| **Contrast-first casting** | Characters are cast for *auditory contrast* against the narrator and each other — not for realism. Pitch, pace, and provider (different TTS engine) are the primary axes. A narrator + 2-4 principal voices is the sweet spot; beyond 6-8 voices, listeners lose track. | Audie: "Contrast beats realism... 3-5 distinct voices carries most books." Vois: "Aim for four to eight clear dialogue voices plus the narrator for a typical audiobook." AudioPod: "Listeners reliably track only six to eight." |

### Audiobook pacing conventions (chapter/scene boundaries)

Audiobooks treat silence as **navigation infrastructure**, not empty space. There is a strict hierarchy of pause lengths that signals structural level to the listener:

| Boundary type | Pause duration | Purpose | Source |
|--------------|---------------|---------|--------|
| **Paragraph break** | ~0.3-0.5s | One thought unit ends, another begins | NarrationBox: "Paragraph pauses tell the listener that one thought unit has ended and another has started." |
| **Soft scene break** | ~1.0-1.5s | Same scene, new beat or time shift | NarrationBox: "A soft scene break should feel noticeably longer than a paragraph pause." |
| **Hard scene break** | ~2.0-3.0s | New scene, location, POV, or time | Narrators Roadmap (Audible standard): "At least 2 and no more than 3.5 for mid-chapter section breaks." ScribeCount: "A scene break is handled with a pause — the narrator pauses for 2–3 seconds." |
| **Chapter ending** | ~3.5-5.0s (with room tone) | Major structural break; natural stopping point | ACX: "3.5 seconds at the tail of each chapter." Narrators Roadmap: ".5 at beginning of file, 2.5 after chapter announcement, 3.5 at end of file." |
| **Mid-chapter section break (####)** | ~2.0-2.5s | Scene change within a chapter | Audible standard: "At least 2 and no more than 3.5 for mid-chapter section breaks designated by ####, ****, ———, or blank space." |

**Key insight:** The amateur mistake is using the *same pause everywhere*. Professional audiobooks use a **pause convention system** where each structural level gets a distinct silence length. This is exactly the "messy pacing" failure mode from the rejected production — the format must enforce varied, level-appropriate pauses.

### R19. Mandatory first-appearance name tags (character introduction rule)

| | |
|---|---|
| **Gap** | Current format has no rule for how a character is first introduced. Characters appear mid-dialogue with no name anchor — the listener has no idea who is speaking or what they are called. |
| **Standard** | Audie: "Start with the narrator, because that voice does the most work. Then cast each character against the narrator so they contrast." Audie: "Clean 'said Name' tags give speaker detection the best possible input." |
| **Format rule** | When a character speaks for the **first time in the story**, their first line MUST use an explicit name tag in one of these forms: `Character Name (emotion): dialogue` OR `Narrator: "dialogue," said Character Name.` The parser tracks first appearances; if a character's first line has no name tag, reject with: "Character X's first appearance lacks a name tag — anchor the voice-to-name mapping." |
| **Why** | This forces the writer to *introduce* the character, not just drop them in. The listener hears the name before having to track the voice. After the first anchor, subsequent lines can use bare `Character Name:` or `(emotion)` variants. |

### R20. Narrator-voice separation (prose vs. dialogue contract)

| | |
|---|---|
| **Gap** | Current format blurs the line between narrator and character. Sometimes narration reads like a character, sometimes characters read like narration. No structural distinction. |
| **Standard** | Audie: "Your narrator is the anchor voice. It reads everything that is not dialogue: the description, the action beats, the internal narration, and crucially the dialogue tags." Audie: "If you let a character voice bleed into the tag, it sounds cartoonish." |
| **Format rule** | Two enforced rules: (1) **Dialogue tags are narrator speech** — any line containing `said [Name]`, `[Name] replied`, `he muttered`, `she whispered` as attribution must be tagged as `Narrator:` (or left as bare prose, which defaults to narrator). (2) **Dialogue must use character voice** — any line inside quotes or attributed to a named speaker uses that character's cast voice. Parser flags lines where a character speaks a dialogue tag (e.g., `Mara: "Get out," she said.` → the `she said` part bleeds into character voice). |
| **Why** | This creates the narrator/character binary that lets the listener track *who is speaking* without effort. Narrator = neutral carrier, character = distinct voice. |

### R21. Contrast-first casting with voice-distance validation

| | |
|---|---|
| **Gap** | Current cast block is free-text. Writers can (and do) create characters with identical or near-identical voice profiles — indistinguishable to the listener. |
| **Standard** | Audie: "For a two-hander scene, you want clear pitch separation, so do not put two similar mid-range voices next to each other." AudioPod: "Force differentiation: if both are '30-year-old American men,' make one a bass and one a tenor." |
| **Format rule** | Parser enforces **minimum voice distance** between any two characters who share a scene: (1) **Pitch delta ≥ 15%** (one low, one medium, one high — not two mediums). (2) **Pace delta ≥ 10%** (one steady, one quick — not two identical). (3) **Texture difference** (one smooth, one raspy — not two identical). If two characters in the same scene violate this, parser rejects with a diagnostic showing the conflict. The narrator must also differ from all characters by ≥ 20% (anchor separation). |
| **Why** | This forces the writer to *cast for contrast*, not for realism. The listener's ear needs separation; the format must enforce it. |

### R22. Pause convention system (level-appropriate silence)

| | |
|---|---|
| **Gap** | Current format has `[pause: N]` but no rules about *which* N to use where. Result: uniform pauses, messy pacing, no structural signal to the listener. |
| **Standard** | Audible/ACX standard: ".5 at beginning, 2.5 after chapter announcement, 3.5 at end." NarrationBox: "A paragraph pause, scene pause, section pause, and chapter ending should not sound the same." Narrators Roadmap: "2-2.5 seconds usually works well for mid-chapter section breaks." |
| **Format rule** | The format defines a **pause taxonomy**: |
| | `[pause: short]` = 0.3-0.5s (paragraph break, same scene) |
| | `[pause: scene]` = 1.0-1.5s (soft scene break, new beat) |
| | `[pause: section]` = 2.0-3.0s (hard scene break, new scene/location/POV) |
| | `[pause: chapter]` = 3.5-5.0s (major break, room tone) |
| | Parser warns if a `[pause: chapter]` is < 3.0s, or if a `[pause: short]` is > 1.0s. Also warns if all pauses in a script are the same value (the "metronomic gap" anti-pattern). |
| **Why** | This forces the writer to *signal structure through silence*. The listener feels the difference between a paragraph break and a scene change without seeing it. |

### R23. Character voice guide in cast block (audience-facing voice description)

| | |
|---|---|
| **Gap** | Current cast block has a `voice` field but no structured way to describe how a character *should sound* to the listener or how it contrasts with others. |
| **Standard** | ScribeCount: "For fiction with multiple significant characters, a brief character voice guide helps the narrator make consistent choices... Vaelindra — the protagonist. Confident, dry wit. Age 28. A slightly lower than average female pitch, measured pacing." Audie: "Comparable performer references are the most useful direction you can give." |
| **Format rule** | Cast block MUST include a `description` field (1-2 sentences, audience-facing) alongside the structured voice fields: |
```yaml
cast:
  Mara:
    gender: female
    age: late 30s
    pitch: low-medium
    pace: steady
    texture: weary, quiet authority
    description: "A composed, understated woman who has learned not to raise her voice. Think: quiet control, not fragility."
```
| | Parser warns if description is missing for any character with > 2 lines. The description field is not used for TTS — it is for *human director guidance* and for prompt-engineering Voice Design. |
| **Why** | This gives the writer (and any future human director) an explicit statement of the character's vocal identity, distinct from the mechanical voice parameters. |

---

## 3. Voice Engineering

### R6. Voice Design must include 5 dimensions (gender, age, pitch, pace, texture)

| | |
|---|---|
| **Gap** | Current cast block is a free-text string. Many entries are vague ("a person speaking") — producing flat, indistinguishable voices. |
| **Standard** | Inworld AI: "Include details about age, gender, language, accent, pitch, pace, timbre, tone, and emotional quality." Qwen3-TTS: "Gender, Age, Pitch, Pace, Emotion, Characteristics, Use case." Dubsmart/Kreiman & Sidtis: "Listeners separately perceive pitch, loudness, roughness, breathiness, and tempo as independent dimensions." |
| **Format rule** | Cast block MUST use structured fields: |
```yaml
cast:
  Mara:
    gender: female
    age: late 30s
    pitch: low-medium
    pace: steady
    texture: weary, quiet authority
    accent: general_american
```
Parser rejects cast entries missing ≥ 3 dimensions. This forces the writer to *design* the voice, not just name it.

### R7. Pitch/rate delta ≥ 15% between characters in the same scene

| | |
|---|---|
| **Gap** | Current format has no check that characters sound different. AI drama's #1 listener complaint: "all voices same tempo." |
| **Standard** | `voice-acting.md` §4: "In any scene with N characters, the pitch/rate pair must differ by ≥ 15% between each." BBC: "Beware peer groups where characters have the same gender, age, class/status and accent/dialect — they might be indecipherable on radio." |
| **Format rule** | Parser computes a voice-distance score from the structured cast fields. If two characters in a scene have < 15% delta in pitch × pace, reject with a diagnostic: "Mara (low-medium/steady) and Elias (low-medium/steady) are indistinguishable — adjust one's pitch or pace." |

### R8. Pronunciation guide for proper nouns (lexicon lock)

| | |
|---|---|
| **Gap** | Current format has no pronunciation control. Mispronounced names repeat hundreds of times and signal "nobody read this." |
| **Standard** | Midsummerr: "A mispronounced proper noun is the single most damaging tell — it repeats hundreds of times." Jellypod: "Character names get a phonetic entry in the pronunciation guide." |
| **Format rule** | Frontmatter MUST include a `pronunciation` block for any non-obvious name: |
```yaml
pronunciation:
  Voss: "VOSS (rhymes with boss)"
  Xian: "SHEE-ahn"
```
Parser extracts proper nouns from the script and warns if any lack a pronunciation entry.

### R9. Emotion must be blended into Voice Design, not just annotated

| | |
|---|---|
| **Gap** | Current format uses `[emotion]` cues that may not reach the TTS engine. Emotion as a tag ≠ emotion in the voice. |
| **Standard** | `voice-acting.md` §3: "Emphasis is carried by Voice Design description + emotion cue, NOT by CAPS or punctuation." Inworld: "The model will tailor the voice to the script." |
| **Format rule** | Per-line emotion `(angry)` must map to a Voice Design transformation string (already in `voice-acting.md` §6). Parser validates that every emotion tag has a corresponding `_EMOTION_VOICE_DESC` entry. If a writer uses `[angry]` but the cast baseline doesn't have an angry variant, the parser warns. |

---

## 4. Sound Design

### R10. Silence must be varied — no metronomic gaps

| | |
|---|---|
| **Gap** | The 2026-09-02 pacing bug: uniform ~0.4s gaps everywhere. Current format does not force varied pause structure. |
| **Standard** | `audio-drama.md` §3: "Scene gaps are not metronomic-uniform. The final audio's silence structure is VARIED." BBC: "Don't be afraid of silence, or varying the distance between the speaker and the mike." |
| **Format rule** | Parser requires ≥ 3 distinct pause durations in the script (e.g., `[pause: 0.5]`, `[pause: 1.2]`, `[pause: 2.0]`). If all `[pause:]` cues are identical, reject. Scene boundaries must use `[pause: 1.0–3.0]` (not a single default). |

### R11. Music and atmos beds must declare levels (ducking contract)

| | |
|---|---|
| **Gap** | Current format has `[MUSIC: name]` and `[ATMOS: name]` but no level control. Music too loud = buried dialogue (amateur tell). |
| **Standard** | `voice-acting.md` §8: "Music bed gain=0.14, ducks 12 dB under speech. Atmos bed gain=0.22, ducks 12 dB under speech." |
| **Format rule** | Music/atmos cues MUST declare gain: `[MUSIC: tense | gain: 0.14 | duck: 12]`. Parser warns if gain > 0.18 for music or > 0.25 for atmos. This makes the mixing contract explicit in the script. |

### R12. Every scene must establish aural environment (atmos or SFX)

| | |
|---|---|
| **Gap** | Current format allows "silent" scenes with no ambience — sounds like a studio, not a world. |
| **Standard** | BBC: "Choose a setting with a distinct aural environment and use those sounds to underscore the story." Jellypod: "Ambience beds handle the 'SFX: distant train rumble' layer under the dialogue." |
| **Format rule** | Every scene MUST have at least one `[ATMOS:]` or `[SFX:]` cue in its first 3 lines. Parser rejects scenes with no aural establishment. This forces the writer to *build the world in sound*. |

---

## 5. Character Craft

### R13. Character sheet with want / need / flaw / arc (frontmatter)

| | |
|---|---|
| **Gap** | Current cast block is voice-only. No tracking of what the character wants, needs, or how they change. |
| **Standard** | `storycraft.md` §4.1: "Want = concrete, achievable-seeking. Need = unconscious truth they resist. Flaw = the specific blindness. Arc = belief at scene 1 vs. opposite at end." |
| **Format rule** | Cast block MUST include want/need/flaw: |
```yaml
cast:
  Mara:
    voice: ...
    want: "find the source of the signal"
    need: "accept that she's been running"
    flaw: "trusts systems over people"
    arc: "isolation → connection"
```
Parser warns if a character speaks in > 2 scenes but lacks a want/need. This forces the writer to know *who* the character is, not just how they sound.

### R14. Per-character vocabulary lock (dialogue test)

| | |
|---|---|
| **Gap** | Current format has no check that characters sound different *in their words*, not just their voice. |
| **Standard** | `storycraft.md` §4.4: "Dialogue test: remove all attributions — can you still tell who speaks by word choice and rhythm alone?" Jellypod: "Give each character a distinct vocabulary, sentence length, and thing they always do." BBC: "Every character needs their own 'grammar'." |
| **Format rule** | Cast block SHOULD include a `speech_pattern` field: |
```yaml
  Mara:
    speech_pattern: "short sentences, technical vocabulary, never asks questions"
    grammar: "fragments when stressed"
```
Parser can run a heuristic: if two characters have identical average sentence length and no distinctive vocabulary markers, warn. This is a soft gate (warning, not reject) but makes the writer *think* about voice lock.

### R15. Listener orientation — characters must use each other's names

| | |
|---|---|
| **Gap** | Current format has no constraint on listener orientation. In audio, you can't see who's talking — names in dialogue are the only cue. |
| **Standard** | ZenMic: "Use characters' names naturally in dialogue to orient listeners." BBC: "The only means of establishing a character's presence is to have them speak or be referred to by name." |
| **Format rule** | In scenes with > 2 characters, parser checks that each character is referred to by name at least once every 6 lines. If a character is only referred to as "he/she/they," warn. This forces the writer to *orient the listener*. |

---

## 6. Mechanical Gates (Format-Level Rules)

### R16. Plant / payoff tracking (no loose threads)

| | |
|---|---|
| **Gap** | Current format has no mechanism to track setups that must pay off. Untracked plants = loose threads = coherence failure. |
| **Standard** | `storycraft.md` §5.4: "Every object, line of dialogue, or skill shown in Act 1 must EITHER pay off in Act 3 OR be a deliberate red herring." `storycraft.md` §8.1: "bible/plants.md — Outstanding plants + target resolution episode." |
| **Format rule** | Cues can tag a plant: `[SFX: gun on mantle | plant: true]`. A later scene must resolve it: `[SFX: gun fires | pays: gun on mantle]`. Parser tracks plant/payoff pairs and warns if a plant is declared but never paid by the final scene. |

### R17. Show-don't-tell gate (emotion in words, not annotation)

| | |
|---|---|
| **Gap** | Current format allows `[emotion]` tags as a crutch — "he was sad" instead of showing sadness through action or dialogue. |
| **Standard** | `storycraft.md` §5.3: "For every emotion beat, write the PHYSICAL MANIFESTATION first. Only use the emotion word if the physical beat is ambiguous." |
| **Format rule** | If a line uses an emotion tag `(sad)` but the dialogue itself contains no physical manifestation (no action, no sensory detail, no behavior), parser warns: "Emotion tag 'sad' with no physical beat — show, don't tell." This trains the writer to *write for the ear*. |

### R18. Read-aloud validation gate (sentence length + punctuation rhythm)

| | |
|---|---|
| **Gap** | Current format allows long, written-style sentences that sound stiff when spoken. |
| **Standard** | `voice-acting.md` §1: "Target 12–18 words per sentence. No run-on sentences > 25 words without a comma/pause break." Vois: "If a sentence has more than 20 words, split it." |
| **Format rule** | Parser flags any line > 25 words without a comma. Also flags lines > 40 words regardless. Punctuation rhythm check: if a scene has > 5 lines with identical sentence length (e.g., all 15 words), warn about monotone cadence. |

---

## Summary: The Upgraded story.md Contract

The upgraded format enforces professional audio drama craft through **parseable constraints**:

| Layer | Constraint | Enforcement |
|-------|-----------|-------------|
| **Structure** | Scene goal, cold-open, therefore/but links, act breaks, word budget | Parser rejects/warns |
| **Character Introduction** | First-appearance name tags, narrator-voice separation, contrast-first casting, pause convention system, voice guide | Parser rejects missing name tags, narrator bleed, < 15% voice delta, uniform pauses |
| **Voice** | 5-dimension Voice Design, 15% pitch/rate delta, pronunciation lexicon | Parser rejects if < 3 dimensions or delta < 15% |
| **Sound** | Varied silence, music/atmos levels, aural establishment per scene | Parser rejects uniform pauses, missing atmos |
| **Character** | Want/need/flaw/arc, vocabulary lock, listener orientation | Parser warns on missing fields or indistinguishable dialogue |
| **Mechanical** | Plant/payoff tracking, show-don't-tell, sentence length | Parser warns on loose threads, tell-only emotion, run-on sentences |

---

## What This Fixes (Anti-Pattern → Format Rule)

| Amateur Anti-Pattern | Format Rule That Prevents It |
|---------------------|------------------------------|
| Characters not introduced / listener can't tell who's speaking | **R19** (first-appearance name tags) + **R20** (narrator-voice separation) + **R21** (contrast-first casting) |
| All voices same tempo/pitch | R6 (5-dimension Voice Design) + R7 (15% delta) |
| Messy pacing / no scene space / metronomic gaps | **R22** (pause convention system) + R10 (varied silence) + R12 (atmos per scene) |
| Music louder than speech | R11 (gain/duck contract) |
| Flat emotion / "he was sad" | R17 (show-don't-tell gate) + R9 (emotion in Voice Design) |
| Scenes that exist for vibe | R1 (scene goal required) |
| "And then" episodic structure | R3 (therefore/but transitions) |
| Long written-style sentences | R18 (sentence length gate) |
| Mispronounced names repeating | R8 (pronunciation lexicon) |
| Loose threads / unfired Chekhov's gun | R16 (plant/payoff tracking) |
| Opening with "welcome back" | R2 (cold-open mandatory) |
| No act structure for ads | R4 (2-act minimum) |

---

## Sources

1. **BBC Writers Room** — "Writing Radio Drama" (bbc.co.uk/writers) — cold-open, significant sound, character distinctness, less-is-more.
2. **BBC Scene Style / Cue Style / Taped Drama Format** (Matt Carless, PDF) — character cues in caps, parenthetical directions, SFX sparingly, (OFF)/(V.O)/(LOW)/(CLOSE) conventions.
3. **Jellypod** — "How to Write an Audio Drama Script" — three-part structure (character cue, parenthetical, dialogue), bracketed sound cues on own line, cliffhanger engineering.
4. **ZenMic** — "How to Write a Fiction Podcast Script" — 2-4 characters per episode sweet spot, 150-180 wpm, distinct vocabulary per character.
5. **Epic Scribe** — "Mastering Pacing in Audio Drama Scripts" — micro/macro/act pacing, wave pattern, scene % breakdown.
6. **Behind the Draft** — "Audio Drama Script Format" — 3-5 acts, scene transitions, FADE OUT/CUT TO.
7. **Screenweaver** — "Structuring and Formatting Audio Fiction" — 10-episode template, episode function table, identification through voice.
8. **Latent Scholar** — "Seriality and Suspense in Podcast Fiction" (S3F Framework) — cold open enigmas, recaps, ad breaks as suspense levers, cliffhanger mechanics.
9. **Rick Toscan / Backstage** — "Tips on Writing Fiction Podcasts" — 2-act structure for ads, scene length < 2 min, 10 min = eternity.
10. **Inworld AI** — Voice Design best practices — 5 dimensions (gender, age, accent, pitch, pace, timbre, tone, emotion), "Perfect broadcast quality audio" anchor.
11. **Qwen3-TTS / Voice Creator Pro** — Voice Design prompting — Gender/Age/Pace/Emotion/Characteristics/Use case, structured key-value format.
12. **Hume Octave** — Voice design — voice prompt + input text holistically, character and setting context.
13. **Dubsmart** — "Voice Descriptors Explained" — Kreiman & Sidtis perceptual dimensions (tone, pace, texture, identity, emotional undertone), combinatorial not holistic.
14. **Midsummerr** — "AI Narrator Tells: What Listeners Actually Hear" — 6 tells: wrong proper nouns, one voice for everyone, flat affect, uniform pacing, mechanical silence, breath artifacts.
15. **Vois** — "Why Your AI Voiceover Sounds Amateur" — 5 mistakes: wrong voice, no mastering, monotone pacing, first-take acceptance, wrong export.
16. **Narration Box** — "Why AI Narration Sounds Flat" — 3 layers (what is said, what is meant, how it should feel), emotional compression, chunking with no emotional memory.
17. **Demodokos** — "Why AI Voices Lose Emotion in Long Audio" — chunking drift, expressiveness-vs-stability tradeoff, local model consistency.
18. **Cliptude** — "Why Your AI Voiceover Sounds Robotic" — punctuation as sheet music, contractions mandatory, read aloud before generating.
19. **Audie** — "Narrator Voice vs Character Voices" — narrator as anchor voice, dialogue tags are narration, contrast beats realism, 3-5 voices sweet spot.
20. **Audie** — "How to Give Every Character a Different Voice" — speaker detection, dialogue tag parsing, provider mixing for separation.
21. **Vois** — "Creating Distinct Character Voices for Audiobooks" — character map, pace as differentiator, 4-8 voices plus narrator.
22. **AudioPod** — "Multi-Character AI Audiobook Narration" — 3 production styles, casting rules, 6-8 voice tracking limit.
23. **Narratory** — "How to Add Character Voices to Your AI Audiobook" — narrator voice first, 3-5 principals, preview dialogue-heavy chapter.
24. **ScribeCount** — "How to Format Your Manuscript for Audiobook Production" — pronunciation guide, character voice guide, performer references.
25. **NarrationBox** — "Scene Break & Section Pause Conventions for AI Audiobooks" — pause taxonomy (paragraph/soft scene/hard scene/section/chapter), ACX room tone standards.
26. **Midsummerr** — "Audiobook Pacing: How Pauses and Silence Shape a Performance" — pacing as production not playback, genre-specific pacing, silence as tool.
27. **Narrators Roadmap** — "Standards for Silence in the Book" — Audible/ACX pause standards (.5 head, 2.5 after chapter, 3.5 tail, 2-3.5 mid-chapter).
28. **StoryVox** — "How Long Should Audiobook Chapters Be" — 15-25 min sweet spot, split at scene breaks, genre conventions.
29. **In-repo: `brain/craft/storycraft.md`** — narrative structures, scene mechanics, character design, 15-point QA rubric.
30. **In-repo: `brain/craft/voice-acting.md`** — WPM targets, breath/pause constants, Voice Design table, emotion mapping, anti-patterns.
31. **In-repo: `brain/stage-specs/audio-drama.md`** — tier durations, pacing gate, scored review rubric.
32. **In-repo: `brain/playbooks/audio-dramas.md`** — production loop, script annotation rules, provider routing.

---

## Implementation Note

These rules should be implemented as **progressive gates** in `storyteller.py`:
- **Reject** (hard gate): missing scene goal, missing cold-open, < 3 Voice Design dimensions, < 15% pitch/rate delta, uniform pauses, missing atmos, first-appearance without name tag, narrator-voice bleed, identical voice profiles in same scene, wrong pause type for structural level.
- **Warn** (soft gate): therefore/but missing, want/need missing, tell-only emotion, long sentences, missing pronunciation, loose plants, missing voice guide.

The format should remain **writer-friendly** (markdown, readable) while being **machine-checkable** (structured fields, parseable tags). The goal is not to make writing harder — it is to make *professional craft* the path of least resistance.
