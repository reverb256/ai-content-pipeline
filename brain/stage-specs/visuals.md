# Stage Spec — Visuals (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. SPEC + MECHANICAL GATE + SCORED REVIEW.

## STAGE
visuals

## BOT
videobot

## INPUT
- `campaigns/<name>/script.md` (has per-section visual notes + word counts)
- `campaigns/<name>/audio/narration.mp3` (the audio track to match)
- `brain/QUALITY_DOCTRINE.md` (anti-slideshow rule) + `brain/RULINGS.md`

## OUTPUT
- `campaigns/<name>/video/final.mp4` — video WITH the narration audio muxed.
- Kanban comment: path, duration, scene count, gate result.

## SPEC (measurable — this is where the truncation bugs lived)
1. **Narration must be FULLY muxed.** The final video's audio track duration
   MUST equal the narration file duration (±2s), NOT the sum of short scenes.
   This is the #1 historical failure: 7-min narration → 88s video because
   scenes were too short and the audio got cut at scene-total length.
2. **Visual beat rule (anti-slideshow).** Every visible beat 5-16s. A section
   whose narration is N words needs ≥ ceil(N/45) visual beats. If script.md
   gives a section 200 words, that section needs ≥5 beats — build them.
3. **Total video duration ≈ narration duration.** Scenes extend to fill the
   narration; visuals never truncate it.
4. **No parked visuals.** Never hold one static visual for a full 60s+
   narration section.

## MECHANICAL GATE (BLOCKS — run before commenting done)
```bash
# 1) Video valid + has audio stream
ffprobe -v error -show_entries stream=codec_type -of compact \
  campaigns/<name>/video/final.mp4    # MUST list both video AND audio
# 2) THE TRUNCATION CHECK (critical):
NARR_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 \
  campaigns/<name>/audio/narration.mp3)
VID_DUR=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration \
  -of csv=p=0 campaigns/<name>/video/final.mp4)
# PASS if VID_DUR >= NARR_DUR - 2  (audio not truncated)
# FAIL if VID_DUR << NARR_DUR  → rebuild scenes to match narration length
# 3) Not silent, not frozen: check a few frames aren't black
ffmpeg -i campaigns/<name>/video/final.mp4 -vf "select='eq(n,120)+eq(n,600)'" \
  -vsync vfr -f null - 2>&1 | grep -c 'frame=' # smoke: renders frames
```
FAIL → the bot must REBUILD the scenes longer (more beats per narration
section) — do NOT advance a truncated video.

## SCORED REVIEW (1-10, min pass 7)
1. **Audio complete** — narration fully present (not cut at scene end).
2. **Visual beat pacing** — no visual parks >16s; beats match narration.
3. **Variation** — scenes visually distinct (not template-slop; inauthentic
   content risk).
4. **Sync** — visuals roughly match the spoken section (a number on screen
   when the number is said).
5. **Technical** — no black frames, no frozen segments, resolution ≥720p.
6. **Overall** — would a viewer stay?

## DONE WHEN
final.mp4 exists, has audio stream, audio duration ≥ narration-2s, scenes
satisfy the 5-16s beat rule with ≥ ceil(words/45) beats per section, and the
comment reports durations + gate result.
