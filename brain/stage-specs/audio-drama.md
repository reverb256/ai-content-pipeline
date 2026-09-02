# Stage Spec — Audio-Drama Synthesis (meticulous contract v1, 2026-09-02)

> Follows brain/QUALITY_DOCTRINE.md. SPEC + MECHANICAL GATE + SCORED REVIEW.
> Covers the `audio`, `audio-drama`, and `story→audio` driver stages (bot
> storyteller). Applies to any storyteller.py synthesis run.

## STAGE
audio / audio-drama

## BOT
storyteller

## INPUT
- The story script: `campaigns/<name>/story.md` (cast block, scenes, cues).
- `brain/audio-workflow-context.md` (voice engines, emotive scripting).
- `brain/QUALITY_DOCTRINE.md` + `brain/RULINGS.md`.

## OUTPUT
- `campaigns/<name>/audio/<name>.mp3` — the finished mix.
- Kanban comment: output path, duration, provider, word count, gate result.

## SPEC (measurable)
1. **Target duration from tier** (brain/audio-workflow-context.md spectrum):
   Short 15-45 min / Long 1-2 hr / Epic 4-8 hr. Word budget = minutes ×
   130-150 words (spoken audio is slower than VO narration). The story.md
   must state its tier and target; the finished audio must land within ±10%.
2. **Complete coverage.** EVERY scene + every line in story.md is audible, in
   order. No truncated scenes, no skipped characters.
3. **Real pacing (the 2026-09-02 fix).** Scene boundaries have REAL pauses:
   the story's `[pause: N]` cues are honored as silence (1.0-3.0s), scene
   gaps are not metronomic-uniform. The final audio's silence structure is
   VARIED (internal sentence pauses ~0.3s, dialogue exchanges ~0.4-0.6s,
   scene breaks ≥1.0s) — not a wall of identical ~0.4s gaps.
4. **CLI correctness.** `-o` MUST be a file path ending `.mp3` — NEVER a
   directory (known hang: storyteller waits on ffmpeg concat when -o is a
   dir). Run via `uv run --project /home/j_kro/Projects/VoxCPM python3
   scripts/audio/storyteller.py`.
5. **Loudness.** Normalized (storyteller.py applies loudnorm). Not clipping.

## MECHANICAL GATE (BLOCKS — run before commenting done)
```bash
# 1) Output exists + non-empty
ffprobe -v error -show_entries format=duration -of csv=p=0 \
  campaigns/<name>/audio/<name>.mp3      # > 0
# 2) Duration vs tier word budget (>= 0.85x expected)
# 3) THE PACING CHECK — real scene pauses present (not uniform):
ffmpeg -i campaigns/<name>/audio/<name>.mp3 \
  -af silencedetect=noise=-35dB:d=0.25 -f null - 2>&1 | \
  grep silence_duration | awk '{print $NF}' | \
  python3 -c "import sys; d=[float(x) for x in sys.stdin];
print('PASS varied' if any(x>=0.9 for x in d) and len(d)>5 else 'FAIL uniform/no-scene-pauses')"
# PASS only if there is at least one >=0.9s pause (scene boundary) AND the
# gaps are not all identical. Uniform ~0.4s everywhere = FAIL (the pacing
# bug from 2026-09-02).
```
FAIL → re-render with fixed pacing (scripts/audio/storyteller.py now inserts
real scene pauses per [pause:] cues). Do NOT advance a metronomic file.

## SCORED REVIEW (1-10, min pass 7)
1. **Pacing** — varied rhythm, scene breaths present, not robotic-uniform.
2. **Emotive delivery** — character voices match cast + emotion cues.
3. **Completeness** — every scene/line present.
4. **Character consistency** — same character sounds like the same voice.
5. **Mix quality** — no clipping, loudness normalized, beds under dialogue.
6. **Story clarity** — a listener can follow who is speaking and what happens.

## DONE WHEN
mp3 exists, duration ≥ 85% of tier word-budget, pacing check PASSED (scene
pauses present + varied), every story scene audible, comment reports
duration + provider + gate result.
