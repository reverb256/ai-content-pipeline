# Stage Spec — Story (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. Every stage = SPEC + MECHANICAL GATE +
> SCORED REVIEW. This file is the contract the story bot reads before
> writing and the reviewer uses to judge.

## STAGE
story

## BOT
scriptwriter

## INPUT (read before writing)
- Story selection / oracle score + route
- `brain/audio-workflow-context.md` (emotive scripting format, duration spectrum)
- `brain/QUALITY_DOCTRINE.md` + `brain/RULINGS.md` (non-negotiable)
- Duration target comes from the CARD (set by oracle) or defaults below.

## OUTPUT (write these)
- `campaigns/<name>/story.md` — full story script with cast block, scenes,
  and emotive annotations per the markup format.
- Self-report in the kanban comment: total word count, per-scene counts,
  duration tier, estimated minutes at 130-150 wpm, and the mechanical check
  result.

## SPEC (measurable — the bot MUST satisfy these)

### Duration tier → word budget (NON-NEGOTIABLE, count words)
Target length comes from the oracle card or defaults to the spectrum:

| Tier | Length | Min words | Max words | Structure |
|------|--------|-----------|-----------|-----------|
| Short | 15-45 min | 1,950 | 6,750 | one arc, 2-3 chars, tight scenes |
| Long | 1-2 hr | 7,800 | 18,000 | multi-arc, 3-5 chars, scene depth |
| Epic | 4-8 hr | 31,200 | 72,000 | serialized chapters, consistent cast, ambient depth |

Budget = minutes × 130-150 words, MINIMUM. You MUST write at least the
MINIMUM. The system counts words after generation. Below minimum = FAIL, no
advance.

### Structure (required skeleton)
1. **Frontmatter / cast block** — locked voices. Every named speaker gets a
   Voice Design description (gender, age, tone, emotion, pace). No uncast
   speakers appear in scenes.
2. **Scenes** — every H2 starts a scene. Each scene carries exactly one
   emotion line `[emotion]` under the heading. Emotion changes get their own
   scene.
3. **Per-line emotion overrides** — `Speaker (emotion): text` steers delivery
   within the scene.
4. **Cues** — `[SFX: name]`, `[ATMOS: name]`, `[MUSIC: name]`, `[pause: 1.2]`.
5. **Narrative arc** — hook / tension / payoff. Flat stories make flat audio.

### Emotive scripting format (from audio-workflow-context.md)
- Cast block sets baseline Voice Design per character.
- Every scene has one emotion directive.
- Short sentences. TTS reads short sentences better than long clauses.
- Spell out numbers and abbreviations.
- Stage direction in text: `(sighs)`, `(gasps)`.
- `[pause: 1.2]` for deliberate beats at scene boundaries and before reveals.

### Voice lock
- Once cast block is written, the storyteller parses it. No ad-libbing new
  voices. If a speaker appears in scenes but not in cast, the script is
  INCOMPLETE — return to writing.

## MECHANICAL GATE (blocks advance — run BEFORE commenting done)
After writing story.md, the bot RUNS this check:
```bash
python3 - <<'EOF'
import re, sys
p = "campaigns/<name>/story.md"
text = open(p).read()
# Count words in dialogue + narration lines only.
# Skip frontmatter (between --- fences), blank lines, headings, cue lines,
# and cast block entries.
words = 0
in_frontmatter = False
for line in text.splitlines():
    s = line.strip()
    if s == "---":
        in_frontmatter = not in_frontmatter
        continue
    if in_frontmatter:
        continue
    if not s or s.startswith("#") or s.startswith("[") or s.startswith("("):
        continue
    words += len(s.split())
print(f"narration_words={words}")
print("PASS" if words >= 1950 else "FAIL below minimum (Short tier = 1950)")
EOF
```
- PASS → advance. FAIL → expand the thin sections.
- Verify: every H2 scene has an `[emotion]` line directly under it. No emotion
  = FAIL.
- Verify: every speaker in scenes appears in the cast block. Uncast speaker
  = FAIL.

## SCORED REVIEW (when a review pass runs — 1-10, min pass 7)
1. **Hook strength** — does the opening scene grab a listener?
2. **Emotive arc** — scenes carry distinct emotions; no flat monotone run.
3. **Cast consistency** — every character has a locked voice; descriptions
   are Voice-Design-ready (gender/age/tone/emotion/pace).
4. **Scene structure** — every scene has emotion + arc; no meandering.
5. **Dialogue quality** — short sentences, spoken-English, TTS-readable.
6. **Pacing** — pattern interrupts, tension/reveal/payoff present.
7. **Cue density** — SFX/ATMOS/MUSIC notes where they matter, not absent,
   not over-stuffed.
8. **Narrative coherence** — beginning/middle/end; listener knows what happened.

PASS: all ≥ 7. FAIL: feedback must name the scene + exact fix.

## DONE WHEN
story.md exists, word-count gate PASSED (>= tier minimum, counted), every
scene has an emotion directive, every speaker is in the cast block, and the
comment reports the measured count + tier.
