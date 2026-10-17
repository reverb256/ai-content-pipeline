# Audio-Drama Playbook — Storyteller Track

> How the machine produces audio-drama / narrative-story content: story
> selection, script annotation, emotive TTS, audio assembly, distribution,
> and monetization. Primary voice: MiniMax Speech TTS (API). Fallback:
> Chatterbox (self-hosted, local GPU).

## The Core Principle

Audio drama turns existing story demand into finished audio. Reddit-story and
audio-drama niches are battle-tested: listeners already search for "stories
read aloud", horror narrations, and dramatic retellings. The machine's edge
is emotive control — per-scene emotion and sound effects baked into the
voice — plus assembly that sounds like a produced piece, not a text-to-speech
dump.

```
story selection (niche demand + supply gap)
    → script with scene/emotion annotations
    → per-scene TTS (MiniMax emotion/sfx, Chatterbox fallback)
    → audio assembly (mix, room tone, pauses)
    → optional visuals (static art + waveform, or clip pipeline)
    → upload (YouTube, audio platforms)
    → performance → updated playbook
```

## What Works (niche guidance)

- **Horror / creepypasta / true-adjacent scary stories** — highest engagement
  per view in the story niche. Whisper + fearful + lofi_telephone carry a
  scene alone. Long-form 10-25 min performs.
- **Reddit-story narrations** — battle-tested by channels running
  RedditVideoMakerBot-style pipelines. Use original or permission-cleared
  posts; never scrape and narrate someone's private story without consent.
- **Sci-fi / mystery short audio dramas** — original scripts, strong CTA to
  subscribe ("part 2 next week"). Membership-friendly: fans pay for the next
  episode.
- **True-crime-adjacent dramatizations** — highest RPM but strictest policy
  and demonetization risk. Use fictionalized accounts, no real victims, no
  gore. Verify policy before producing.
- **Classic public-domain fiction** — zero rights risk (check the specific
  translation/edition), evergreen, search-driven. Good for SEO compounding.

## The Production Loop

### 1. Story selection

- Score the story like the oracle scores a niche: demand × supply gap ×
  monetization × automation fit, policy as a gate.
- Prefer stories with emotional beats (tension, reveal, payoff). Flat stories
  make flat audio.
- Original scripts beat scraped ones for policy safety and membership value.
- Keep a story backlog. The oracle routes candidates; the scriptwriter turns
  them into annotated scripts.

### 2. Script with scene/emotion annotations

Write in the markup documented in `scripts/audio/example-story.md`:

- Frontmatter: title, voice, fallback_voice, model, speed.
- Every `# Heading` starts a scene.
- The line under the heading sets the mood:
  `[angry | sound_effect=spacious_echo]`.
- Emotion per scene: happy, sad, angry, fearful, disgusted, surprised, calm,
  fluent, whisper.
- Sound effect per scene: spacious_echo, auditorium_echo, lofi_telephone,
  robotic.
- Voice and speed overrides per scene when a character needs one.

Rules for script quality:

- One emotion per scene. Emotion changes get their own scene or a new
  directive.
- Short sentences. TTS reads short sentences better than long clauses.
- Spell out numbers and abbreviations unless the pronunciation dict covers
  them.
- Put stage direction in the text when it matters: "(sighs)", "(gasps)".
  MiniMax speech-2.8-hd supports interjection tags such as (sighs), (gasps),
  (laughs) directly in the text.
- Pause markers `<#0.5#>` create deliberate silence. Use them at scene
  boundaries and before reveals.

### 3. Per-scene TTS

Primary: MiniMax Speech T2A (HTTP).

- Model: `speech-2.8-hd` for final quality (interjections, best emotion),
  `speech-02-hd` as a solid cheaper HD alternative, turbo variants for drafts.
- Voice: start with `English_expressive_narrator`; clone a house voice from
  10s+ clean audio for brand consistency (voice clone API).
- Emotion: set per scene. Manual emotion beats auto-detection for drama.
- Sound effects: `spacious_echo` for memory/flashback scenes,
  `auditorium_echo` for a crowd or a broadcast, `lofi_telephone` for a
  distant call, `robotic` for AI/computer voices.
- Long-form: the synchronous T2A API handles up to 10,000 chars per request;
  the async T2A (`t2a_async_v2`) handles up to 1M chars for whole chapters.
  The orchestrator synthesizes per scene, so sync is fine for typical scenes.

Fallback: Chatterbox (self-hosted, local GPU).

- Use when MiniMax is down, quota-exhausted, or the key is missing.
- Predefined voices such as `Connor.wav`; cloned house voices for brand
  consistency.
- No emotion control in the API. The orchestrator compensates with ffmpeg
  effects (echo, high-pass for whisper).

Rules:

- Check the key and provider health before starting. Never stall on a quota.
- Log which provider served each scene to `performance/model-routing.log`.
- A scene that fails on MiniMax falls back per-scene, not per-story.

### 4. Audio assembly with sound effects

The orchestrator (`scripts/audio/storyteller.py`) does this:

- Concatenates scenes with a 0.7s silence gap.
- Applies room tone (aecho) to scenes without a MiniMax sound effect.
- Applies loudness normalization (I=-16 LUFS, the YouTube/podcast comfort
  zone).
- Writes a finished mp3.

Optional polish:

- Background music: mix a quiet bed under narration with ffmpeg `amix`
  (fade in/out; keep it 6-10 dB under the voice).
- SFX stings at scene boundaries (door, heartbeat). Keep them short.
- Fade in/out at the very start and end (`afade`).

### 5. Optional visuals

Audio drama works as pure audio; visuals are optional but lift retention on
YouTube:

- Static art + animated waveform (ffmpeg `showwaves` or the videobot).
- AI-generated scene art per scene (thumbnailbot / comfyui), Ken Burns pan
  via ffmpeg zoompan.
- Keep the visual simple. The audio carries the drama.
- For pure audio: upload to Spotify/Apple (podcast), YouTube as a podcast
  format, or audiobook platforms.

### 6. Upload

- YouTube long-form: 8-25 min audio dramas fit watch-time-driven niches.
- Audio platforms: Spotify for Creators, Apple Podcasts — low friction, no
  visuals needed.
- Series format: episodes with "part N of M" CTAs drive subscriptions and
  memberships.
- Batch the pipeline: story selection daily, production per card, upload per
  completed card.

## Monetization

- **YouTube ad revenue** — the primary channel for story niches; RPM varies
  by niche (horror/true-crime-adjacent high, general stories lower).
- **YouTube memberships** — early access, exclusive episodes, voting on the
  next story. Strong fit for serialized audio dramas.
- **Audio platforms** — Spotify/Apple monetization (per-stream + ad support).
- **Audiobook-style sales** — compile a season into a paid audiobook.
- **Affiliate** — headphones, microphones, storytelling tools; match the
  niche audience.

## Policy Notes

- **AI disclosure** — disclose AI narration clearly in descriptions and
  settings where required. Some platforms (YouTube, Spotify) require or
  favor it. Disclosure protects the account.
- **Original content** — original scripts are safest. Public-domain fiction
  is safe. Do NOT narrate private Reddit posts, personal stories, or
  copyrighted fiction without permission. Fabricated "true stories" are
  demonetization bait.
- **No real victims** — true-crime-adjacent drama must be fictionalized.
  Never use real names, real victims, or real gore.
- **Not repetitive slop** — vary structure per episode. Repetitive template
  audio gets flagged as inauthentic content.
- **Check platform policy per market** — AI-content rules change; re-verify
  before a new platform launch.

## Rules

1. The oracle scores the story niche before production. No scored story, no
   card.
2. The scriptwriter produces the annotated script. The storyteller does not
   improvise stories.
3. MiniMax is primary; Chatterbox is fallback. Never stall on a quota.
4. Every scene carries the emotion the script annotates. A flat read fails
   the contract.
5. Log providers to `performance/model-routing.log`.
6. Performance closes the loop: which niches convert, which emotions hold
   retention, which formats flop — feed it back here.
