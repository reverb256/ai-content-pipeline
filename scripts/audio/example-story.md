---
title: The Last Signal
voice: English_expressive_narrator
fallback_voice: Connor.wav
model: speech-2.8-hd
speed: 1.0
cast:
  Mara: "woman in her late 30s, steady, weary, quiet authority"
  Elias: "older man, warm, cracked voice, distant"
---

# FORMAT DOCUMENTATION

This file is the format reference AND a runnable example story.

The storyteller parses this markup:

1. Frontmatter (between the first `---` lines) sets story-level defaults:
   - `title` — used for the output filename
   - `voice` — MiniMax voice id for all scenes (override per scene)
   - `fallback_voice` — Chatterbox predefined voice used when MiniMax is down
   - `model` — MiniMax speech model (speech-2.8-hd | speech-02-hd | turbo variants)
   - `speed` — default speech speed 0.5-2.0

2. Every `# Heading` starts a new scene. The heading is the scene title.

3. The line directly under the heading sets the scene mood:
   `[emotion]` or `[emotion | sound_effect=... | voice=... | speed=...]`
   - emotion: happy | sad | angry | fearful | disgusted | surprised | calm | fluent | whisper
   - sound_effect: spacious_echo | auditorium_echo | lofi_telephone | robotic
   - voice: per-scene voice override
   - speed: per-scene speed override (0.5-2.0)

4. **Speaker lines** (multi-character): `Speaker: dialogue` or
   `Speaker (emotion): dialogue`. The default speaker is the Narrator.
   Speakers map to the `cast:` frontmatter block (voice description per
   character for VoxCPM Voice Design), so a character's voice persists
   across every line and every episode.

5. Blank lines separate takes. Non-blank lines are spoken text.

6. Story text without any heading becomes an implicit "intro" scene.

Run it:
    python3 scripts/audio/storyteller.py scripts/audio/example-story.md -o /tmp/last-signal.mp3

<!-- DOC-END -->

# Scene 1 — The Call

[calm]

Narrator: The console beeped once. Then it stopped. Mara pressed her palm to
the cold glass and listened. Nothing came back.

Mara (angry): Who left this running?

Narrator: The silence answered her. The silence had always answered her.

# Scene 2 — The Message

[sad | speed=0.9]

Narrator: On the third day, the signal returned. Not a voice. A pattern. Old
radio etiquette, tapped out in the dark by someone who still believed someone
was listening.

Elias (fearful): You are not alone out here.

Narrator: She stared at the screen until her eyes burned. She had not told it
where she was. She had told no one.

# Scene 3 — The Return

[whisper | speed=0.85]

Narrator: Outside, the wind died. The station hummed its one low note.
Somewhere in the dark, something had begun to move toward the light.

Mara (calm): I've been waiting for company a long time.

# Scene 4 — The Close

[fluent]

Narrator: The log ended there. What you heard tonight is the last
transmission from Station Seven, recovered and restored. If you found your
way here, you are not alone either.
