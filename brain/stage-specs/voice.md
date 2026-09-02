# Stage Spec — Voice / Narration (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. SPEC + MECHANICAL GATE + SCORED REVIEW.

## STAGE
voice

## BOT
voicebot

## INPUT
- `campaigns/<name>/script.md` (the narration script)
- `brain/audio-workflow-context.md` (voice engines, emotive scripting)
- `scripts/api/pick-provider.sh voice` (provider router)
- `brain/QUALITY_DOCTRINE.md` + `brain/RULINGS.md`

## OUTPUT
- `campaigns/<name>/audio/narration.mp3` (or the campaign's canonical audio
  path) — the FULL narration read end to end.
- Kanban comment: audio path, duration, provider tier, word count, gate result.

## SPEC (measurable)
1. **Complete coverage** — the audio must contain EVERY narration line in
   script.md in order. No skipped sections, no truncation.
2. **Duration match** — target duration = script narration words / 160 wpm
   (±10%). Example: 1,500 words → 8:45-10:45. If audio is far shorter than
   the word budget implies (e.g. 1,500-word script → 2-min audio), the read
   was truncated — FAIL.
3. **Provider** — use the best available per pick-provider.sh; log the tier
   to performance/model-routing.log.
4. **Voice quality** — no robotic monotony. Pacing follows the script's TTS
   notes (pause beats, numbers as words). If VoxCPM, emotive delivery uses
   the script's emotion cues.

## MECHANICAL GATE (BLOCKS — run before commenting done)
```bash
# 1) Audio exists + non-empty
ffprobe -v error -show_entries format=duration -of csv=p=0 \
  campaigns/<name>/audio/narration.mp3   # must be > 0
# 2) Duration vs word budget (script narration words / 160)
#    PASS if audio_duration >= (words/160)*0.9
# 3) Not silent: mean volume above noise floor
ffmpeg -i campaigns/<name>/audio/narration.mp3 -af volumedetect -f null - 2>&1 | \
  grep mean_volume   # expect around -20 to -30 dB, NOT -90 (silence)
```
Any check failing → re-run the synthesis (fix truncation / provider) before
advancing.

## SCORED REVIEW (1-10, min pass 7)
1. **Complete** — all script lines present, in order.
2. **Duration match** — within ±10% of word-budget estimate.
3. **Natural delivery** — not robotic; pace follows the script notes.
4. **Emotive accuracy** — emotion cues from the script land.
5. **Clarity** — every word intelligible, no clipping/mumbling.
6. **Technical** — no silence gaps > 2s mid-section, no artifacts.

## DONE WHEN
narration.mp3 exists, duration ≥ 90% of word-budget estimate, non-silent,
provider logged, all script lines audible.
