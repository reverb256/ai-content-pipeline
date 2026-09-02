# Quality Doctrine — Meticulous AI Content Pipeline (2026-09-02)

Source: research into production pipelines (video-factory, kanban-video-pipeline,
manim-agent, ContentMachine, video-recap-skills QC, OpenMontage) + YouTube
retention data. This document defines what "meticulous" means operationally
and applies to EVERY pipeline stage and EVERY profile.

## 1. The core principle

Quality is engineered, not vibed. Every stage must have:
1. A SPEC — what "done" means, measured in observable terms (word counts,
   durations, scores, structural rules), never vibes.
2. A DETERMINISTIC VALIDATION — mechanical checks that BLOCK (ffprobe,
   word-count, file-exists, duration-match). No model judgment required.
3. A SCORED REVIEW GATE — the model judges against explicit 1-10 criteria
   with a pass threshold, and reworks on failure (bounded retries).
4. FED-BACK LESSONS — every correction becomes a rule in the spec so the
   failure does not repeat (RULINGS.md + playbooks).
5. MAKER-CHECKER TRUST — the bot that did the work is the WORST judge of
   the work. A claim is done only with independent evidence + a checker
   who did not make the claim. Completion is a disputed claim, not a
   self-grade. (Source: Grok Build /goal, Lauren Tan pstack, Compound
   Engineering, H. Floyd field notes — the trust doctrine.)

## 1b. The trust model

```
A claim is not done.
A claim + independent evidence + a checker who did not make the claim
is done.
```

- The maker's "Done" is performance, not proof. The maker's todo list is
  forgeable.
- Evidence = tests/screenshots/source URLs/diffs produced by a DIFFERENT
  profile, or harness facts the model cannot forge (file hashes, command
  exit codes, URLs fetched, wall-clock, which profile produced what).
- Gate/Reviewer can KILL the handoff. A producer never grades its own exam.
- Every artifact ships with a sidecar: `artifact.evidence.json` written
  from the runtime, not the model. An artifact without its evidence file
  is incomplete and will not route.

### Laziness classifier — reject the package if any tell fires
1. "I'll do that next" / "working on it" with no tool call in the same turn.
2. Declares complete with no artifact path.
3. Cites its own earlier draft as a source.
4. "I verified" with no attached command/screenshot/test log/URL.
5. Invented background work that contradicts wall-clock.
6. Plan skipped ("this is simple") on multi-step work.
7. Thin coverage: 1 source for a factual claim, 1 test for a feature.
8. Scope shrink to make the job easier (dropped the hard requirement).
9. "Looks good / professional / solid" as a quality sentence.
10. Asking permission for an obvious reversible step to burn a turn.

### Contract block every brief must carry
Outcome / Not-done-if (3 falsifiers) / Sources allowed / Tools allowed /
Deliverable path / Evidence path / Handoff schema (Objective, Artifact,
Evidence, Unknowns, Status, Next) / DONE means / Outside the fence.

### Review gate default
- Default vote is REJECT. Must cite a rule that failed or a missing
  evidence pointer. Cannot praise. Score 1-10, kill line at 8.
- First-round rejects are success. If Gate never rejects, Gate is lazy.
- Lessons compound to the RIGHT layer: wrong fact → fix source of truth;
  right facts used badly → fix bot description; wrote too far → tighten fence.
- Never let the learning loop grade itself: a separate reviewer or human
  promotes a skill, not the closed loop.

## 2. What the research proves

### From video-factory (1164-line meticulous prompt system)
- **Word budgets, not time guesses.** "You MUST write at least N words — NON-
  NEGOTIABLE, we measure by counting words." The system computes timing from
  words. We guessed durations and produced 88s videos from 7-min scripts.
- **Per-slot visual pacing.** Every visual beat must be 5-16s. Longer narration
  needs MORE slots — never park one visual. A section that would need >5
  visible beats should be split. THIS EXACT RULE prevents the aviation bug
  (8 scenes trying to hold ~60s of narration each).
- **10 scored review criteria** (hook, pacing, engagement, SEO, cultural,
  section balance, watchability, structure, safety, funnel). JSON pass/fail.
  Content-safety = score 1 instant-reject. "Do NOT evaluate duration —
  validated separately by the system" (separation of concerns).
- **Bounded retries per gate** (script 3, image 2, thumbnail 2, final 1) —
  fails stop, don't loop.
- **Channel config as a contract**: target_duration, resolution, fps, music
  pool, per-type pacing/style/thumbnail strategy, review thresholds. The
  channel's identity is a CONFIG, not improvised per video.
- **Mechanical validator** (221 lines): sequential section ids, no empty
  narration, >50 words total, images exist + meet min size, audio exists +
  non-empty, video valid, thumbnail exists. Blocks before AI review.

### From the retention data
- 70% retention at 30s = the algorithmic threshold. 55% of viewers gone by 60s.
  Hook in first 7 seconds. Pattern interrupt every 60-90s. Re-hook before
  each section resolve.
- 10% retention improvement ≈ 25% more impressions. AVD 50%+ = 3x more
  recommended.
- Video length benchmarks: under 5min 50-60%, 5-10min 50%+, over 10min 40-60%.
- "The edit IS the personality" for faceless content. Cut dead air, music
  -10 to -14dB under voice, change music energy per chapter.
- **Uniformity is the demonetization risk.** YouTube's "inauthentic content"
  policy targets template content with no variation. Per-video variance is
  mandatory, not optional.

### From the pipeline architectures (all of them)
- Planning-first: Director/scene-plan before generation (EduVid-LLM proved
  planning-centric > monolithic).
- AI reviews the RENDERED artifact (frames, audio), not just the plan —
  multi-modal critique + repair loop (vibe_video, Chalkboard, kanban-pipeline).
- Human approval BEFORE expensive generation; checkpoints/resume; decision
  logs so every choice is auditable.

## 3. The doctrine for OUR pipeline

Every stage contract must include (per stage):

```
STAGE: <name>
BOT: <owner>
INPUT: <exact artifact it reads + where>
OUTPUT: <exact artifact it writes + where>
SPEC (measurable):
  - word budget: >= N words (counted, not estimated)
  - structure: [exact required structure with numbered sections]
  - slot/beat pacing: every visual beat 5-16s, more narration = more slots
  - duration target: derived from words at ~160 wpm, verified after
REVIEW (scored, 1-10, min pass = 7):
  - <5-8 explicit criteria specific to the stage>
  - feedback must name exactly what changes
  - retry up to N times, then STOP and flag
MECHANICAL GATE (blocks):
  - <what a script/validator checks before the bot can advance>
DONE WHEN: <observable conditions>
```

## 4. Immediate gaps in our pipeline (measured)

| Gap | Evidence | Fix (from research) |
|---|---|---|
| No word budgets | 2175-word script → 88s video | word budget + count check |
| No visual beat rule | 8 scenes held ~60s narration each | max 16s/beat, min slots |
| No scored review gate | analyst gave 7.8 with no rubric | 10-criteria scored JSON gate |
| No mechanical validator | truncation shipped | validate duration==narration |
| Vague stage prompts | "write retention-optimized script" | full spec per stage |
| No per-format template | every video ad hoc | channel config w/ video_types |
| No bounded retries | thumbnail loop ran forever | max_attempts per gate |
| No rendered-artifact review | pacing bug shipped | NIM omni listens to audio |

## 5. Sources
- github.com/NesDevr/video-factory (prompts.py, core/validator.py, config/channels/)
- github.com/NousResearch/kanban-video-pipeline (tools/media_analyze.py)
- github.com/gqy20/manim-agent (prompts.py multi-phase)
- github.com/Saganaki22/ContentMachine (scene planning, model-aware pacing)
- github.com/iRaees/OpenMontage (quality gates, slideshow-risk scoring)
- deepwiki.com/worldwonderer/video-recap-skills (QC contract, deterministic vs advisory)
- virvid.ai, facelesshustle.ai, layer3labs.io (retention benchmarks)
- aivideobootcamp.com, root-nation.com (inauthentic content policy)
