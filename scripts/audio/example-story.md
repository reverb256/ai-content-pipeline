---
title: The Last Signal
tier: short
acts: 2
narrator_voice: English_expressive_narrator
model: speech-2.8-hd
speed: 1.0
pronunciation:
  Voss: "VOSS (rhymes with boss)"
cast:
  narrator:
    gender: male
    age: middle_aged
    pitch: high_medium
    pace: steady
    texture: warm, clear
    description: "A steady, unhurried narrator. Warm, clear, authoritative without being cold."
  Mara:
    gender: female
    age: late_30s
    pitch: low_medium
    pace: quick
    texture: weary, quiet authority
    description: "A composed, understated woman who has learned not to raise her voice. Think: quiet control, not fragility."
    want: "find the source of the signal"
    need: "accept that she's been running"
    flaw: "trusts systems over people"
    arc: "isolation to connection"
    speech_pattern: "short sentences, technical vocabulary, never asks questions"
  Elias:
    gender: male
    age: 60s
    pitch: very_low
    pace: slow
    texture: cracked, warm
    description: "An older man with a warm but cracked voice, speaking like each word costs something."
    want: "warn her before it is too late"
    need: "be heard before he dies"
    flaw: "speaks in riddles when directness would save lives"
    arc: "distant to intimate"
    speech_pattern: "fragments, pauses mid-sentence, repeats key words"
---

# FORMAT DOCUMENTATION

This file is the v3 format reference AND a runnable example story.

Format v3 enforces professional audio drama craft (R1-R23):

1. Frontmatter declares structured cast with 5-dimension Voice Design
2. Every scene declares a goal: [goal: reveal|escalate|decision]
3. First scene must carry [cold-open]
4. First-appearance name tags anchor voice-to-name mapping
5. Narrator-voice separation: dialogue tags are narrator speech
6. Contrast casting: characters in same scene must differ by >=15% pitch, >=10% pace
7. Pause taxonomy: short (0.3-0.5s), scene (1.0-1.5s), section (2.0-3.0s), chapter (3.5-5.0s)
8. Every scene establishes aural environment (atmos or SFX)

Run it:
    python3 scripts/audio/storyteller.py scripts/audio/example-story.md -o /tmp/last-signal.mp3

<!-- DOC-END -->

# Scene 1 — The Call [goal: reveal] [cold-open]

[ATMOS: rain on tin roof | gain: 0.22 | duck: 12]
[emotion: calm]

Narrator: The console beeped once. Then it stopped. Mara pressed her palm to the cold glass and listened. Nothing came back.

Narrator: "Who left this running?" said Mara.

Mara (angry): Who left this running?

[pause: short]

# Scene 2 — The Message [goal: escalate] [link: but]

[ATMOS: static | gain: 0.18]
[emotion: sad | speed=0.9]

Narrator: On the third day, the signal returned. Not a voice. A pattern. Old radio etiquette, tapped out in the dark by someone who still believed someone was listening.

Narrator: "You are not alone out here," said Elias.

Elias (fearful): You are not alone out here.

[pause: scene]

# Scene 3 — The Return [goal: decision] [link: therefore]

[SFX: door creak | gain: 0.7]
[emotion: whisper | speed=0.85]

Narrator: Outside, the wind died. The station hummed its one low note. Somewhere in the dark, something had begun to move toward the light.

Mara (calm): I have been waiting for company a long time.

[pause: section]

# Scene 4 — The Close [goal: reveal]

[ATMOS: soft room tone | gain: 0.18]
[MUSIC: soft piano | gain: 0.14 | duck: 12]
[emotion: fluent]

Narrator: The log ended there. What you heard tonight is the last transmission from Station Seven, recovered and restored. If you found your way here, you are not alone either.

Mara (calm): End log.

[pause: chapter]
