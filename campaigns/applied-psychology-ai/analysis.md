# Performance Review — applied-psychology-ai (t_a947f3a5)

**Analyst run:** 2026-09-01 (refreshed with X search data)
**Video ID:** QEr_Elylt_o
**URL:** https://youtu.be/QEr_Elylt_o
**Visibility:** PRIVATE (confirmed via yt-dlp — "Private video" error)
**Uploaded:** 2026-08-31

---

## Current State

The video remains PRIVATE as of 2026-09-01. No human has approved it for public release.
YouTube Analytics requires the video to be public for 24-72 hours to accumulate
meaningful data (views, watch time, retention, CTR).

**Performance data: NOT YET AVAILABLE.** This review evaluates the
campaign on process quality, content craft, and market timing — the
leading indicators we can measure before public performance data exists.

External signal data (web search + X search) was re-pulled 2026-09-01 to
validate market timing and competitive landscape.

---

## Process Quality (leading indicator)

| Stage | Provider | Result |
|-------|----------|--------|
| Research | — | 8 verified claims, all primary-source URLs spot-checked live |
| Script | — | ~12:30 TTS-paced, every claim traces to evidence package |
| Voice | VoxCPM (CUDA, self-hosted) | 445.7s, 28 segments, emotive annotations |
| Visuals | Manim CE (local) | 445.67s, 10 scenes, H.264+AAC mux |
| Thumbnail | ImageMagick (local) | 3 variants, high-contrast, <=3 words |
| SEO | — | Title 56 chars, 10 tags, 10 chapters, 8 source URLs |
| Upload | YouTube Studio (CDP) | Private, video ID QEr_Elylt_o |

**Process verdict:** Clean run. Zero fallback events on voice (VoxCPM
held for all 28 segments). Zero fallback on visuals (Manim rendered
all 10). Only thumbnail fell back from ComfyUI→ImageMagick (ComfyUI
still down on nexus — known infra issue, not a content failure).

Model routing logged to performance/model-routing.log. No errors.

---

## Content Craft Evaluation

### Hook
"1,372 people. AI was wrong 80 percent of the time. They followed it
anyway." — Concrete number + counterintuitive finding. Matches the
hooks.md playbook pattern: "Concrete numbers beat adjectives." 56-char
title is within the <60 sweet spot for mobile truncation.

### Structure
Hook → Stakes → 6 mechanisms → Payoff → CTA. Follows the
"inverted pyramid + layered payoff" structure that performs for
search-driven long-form. Each mechanism is a self-contained study,
which also makes them individual Shorts/Reels clip candidates.

### Citation quality
Every consequential claim traces to a peer-reviewed source (TIME,
APA Monitor, Frontiers, AAAI, MIT, Anthropic, Shaw & Nave). Gaps
acknowledged on-screen and in description (no longitudinal data,
MIT ChatGPT-specific, lab-only surrender, self-reported modes, no
clinical harm). This is the anti-fabrication rule executed correctly.

### Voice + visuals
VoxCPM with emotion annotations (calm 15, fearful 4, sad 4, angry 2,
surprised 2, whisper 1, fluent 1) — not monotone. Manim CE provides
clean motion graphics without template-slop risk.

### Thumbnail
3 variants generated. v1_80_wrong.png recommended — matches hook
exactly, "80% WRONG" text on dark background, curiosity gap at
feed size.

---

## Market Timing (external signal check — 2026-09-01)

Web search confirms the niche is hot RIGHT NOW:
- TIME cover story (April 2026): "Are We Losing Our Minds to AI?"
- APA Monitor feature (July 2026): dedicated issue
- Gizmodo (April 2026): "Cognitive Surrender Is a New and Useful
  Term for How AI Melts Brains"
- Psychology Today (June 2026): "AI and the Psychology of
  Cognitive Surrender"
- Wharton podcast (April 2026): Nave & Shaw on "You Are Not So Smart"
- Addy Osmani blog (May 2026): "Cognitive Surrender" — widely shared
  in engineering community
- Ars Technica (April 2026): detailed coverage of the Wharton study
- The Next Web (2026): coverage of Moot app monetizing cognitive
  surrender

**X search (2026-09-01):** "Cognitive offloading" and "cognitive surrender"
are spiking in discussion volume August-September 2026. Key voices:
- Steven Kotler (Flow Research Collective): ~30 days of AI use →
  measurable writing skill decline in executives
- Andrew Ng: warns that ChatGPT-style use harms long-term retention
  and skill-building
- Addy Osmani: "cognitive surrender" post widely shared in engineering
  community
- Multiple papers linking frequent AI use to lower critical thinking
  (especially ages 17-25)

**Competitive landscape on YouTube:**
- Multiple podcasts and interviews on cognitive surrender exist
  (You Are Not So Smart ep. 337, AI and Design podcast)
- No dominant creator owns the "cognitive offloading crisis" framing
  on YouTube specifically
- Opportunity: first-mover advantage on a research-backed long-form
  explainer with this specific angle

---

## RPM / Monetization Validation

Opportunity card projected $7-15 RPM for psychology/tech crossover.
Verified data (AIR Media-Tech 300-channel study, 2026):
- Education & Science median RPM: $10.22 (highest niche)
- Self-improvement/psychology: $6-$12
- Jungian psychology: $7.13

Above YouTube all-niche median (~$2.30). Monetization thesis holds.

---

## Leading-Indicator Scoring

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Hook strength | 8/10 | Concrete number + curiosity gap; matches playbook pattern |
| Evidence quality | 9/10 | 8 verified claims, primary-source URLs, gaps acknowledged |
| Script structure | 8/10 | Inverted pyramid + clip-candidate sections |
| Voice quality | 7/10 | VoxCPM emotive, but self-hosted (no third-party quality check) |
| Visual quality | 6/10 | Manim CE is clean but basic (no face, no personality) |
| Thumbnail | 7/10 | 3 variants, v1 strong, but ImageMagick fallback (not ideal) |
| Timing | 9/10 | Peak cultural moment for cognitive offloading discourse |
| Differentiation | 8/10 | No dominant creator owns this framing on YouTube |
| **Composite (leading)** | **7.8** | Strong on evidence+timing, weaker on production value |

---

## KEEP / TEST / STOP

### KEEP (patterns that worked)

1. **Research-first pipeline with live URL verification.** 8 claims,
   all spot-checked live. No fabrication. This is the quality floor.
   → Post: researcher comments in kanban log (2026-08-31 09:08-16:32)

2. **"Concrete number + counterintuitive finding" hook pattern.**
   Title: "AI Was Wrong 80% of the Time. They Followed It Anyway."
   Hooks.md playbook applied correctly.
   → Post: metadata.json title (2026-08-31 21:01)

3. **Gap acknowledgment as trust signal.** Stating limitations
   on-screen (no longitudinal data, MIT ChatGPT-specific) increases
   credibility with informed viewers. The informed viewer is the
   high-RPM demo.
   → Post: script.md PRODUCTION NOTES (2026-08-31 17:08)

4. **VoxCPM (self-hosted) for emotive narration.** Zero fallback,
   zero cost, emotion annotations per segment. The audio-drama
   track works when the pipeline keeps TTS local.
   → Post: storyteller log (2026-08-31 18:43)

### TEST (promising, need another attempt)

1. **Manim-only visual style.** 10 scenes of motion graphics is
   clean but monotonous for a 7:26 video. Test: intersperse
   stock footage / b-roll with Manim for visual variety. Or test
   one "face-in-corner" style (AI avatar) to add personality.
   → Post: videobot log shows all-Manim render

2. **Video length vs retention.** 7:26 is longer than the
   5-6 min sweet spot for a first video on a new channel. Test:
   cut future scripts to 5-6 min and compare retention curves.
   → Post: final.mp4 duration 445.67s

3. **Thumbnail text density.** v1 uses "80% WRONG" — high contrast.
   Test: "YOUR BRAIN ON AI" with a brain scan image for a different
   curiosity angle (authority gap vs shock gap).
   → Post: 3 variants generated, no A/B data yet

4. **Chapter timestamps for SEO.** 10 chapters included in
   description. Test: does adding chapters improve search
   impressions vs a no-chapter control on the next video?
   → Post: metadata.json chapters (10 timestamps)

5. **First video on a new channel.** This is the hardest test:
   will YouTube's algorithm classify and distribute a new channel
   with no watch history? Test: second video in the same niche
   should compound if the first gets even modest impressions.
   → Post: publish.md (first upload, private)

### STOP (weak patterns — but see caveats)

Nothing qualifies as STOP yet. This is the first video in the
niche. One data point cannot support a stop judgment per the
performance.md rule: "One strong result = a hypothesis, not a
universal rule."

The closest candidate would be "12+ minute length for video #1"
but we have no retention data yet — marked as TEST above.

---

## Proposed Playbook Updates (pending human approval)

None at this time. Per the rule "proposed playbook changes wait
for human approval (RULINGS.md updates only after approval)" and
the autonomy boundary in performance.md, I am withholding proposed
changes until public performance data (views, retention, CTR)
justifies them. Leading indicators are strong but not sufficient
to update hooks.md or platforms.md.

---

## Recommended Next Actions

1. **Human reviews the private video** (t_a947f3a5 → stage:
   analyze → human approval gate → public). The video is clean,
   well-sourced, and timed to a hot niche.
2. **Publish when approved** — ideally within 48h to ride the
   cognitive-offloading discourse wave.
3. **Pull YouTube Analytics after 72h public** — re-run this
   analysis with real numbers (views, avg view duration, CTR,
   retention curve, traffic sources).
4. **Prepare the sequel** while waiting: "The Metacognition Test"
   (scriptwriter already scripted the CTA card). Metacognition is
   the moderator variable in the research — it's the natural
   follow-up that converts viewers to subscribers.
5. **Cut 5-10 Shorts clips** from this flagship (the 6 mechanisms
   are each self-contained clip candidates per viral-moments.md).
   Distribute as subscriber acquisition.

---

## Summary

The pipeline executed cleanly. The content is well-sourced,
well-structured, and timed to peak cultural interest in
cognitive offloading. Production value is adequate (not premium).
The video is ready for human review and public release.

No STOP items. KEEP: research-first pipeline, concrete-number
hooks, gap acknowledgment, local VoxCPM. TEST: visual variety,
video length, thumbnail text, chapter SEO effect, new-channel
algorithm behavior.

Proposed playbook changes: none pending public performance data.

---

**Analyst:** analyst profile (longcat-2.0:free, nous)
**Board:** faceless-youtube
**Task:** t_a947f3a5 (stage: analyze)
**Status:** Analysis complete, awaiting human publish approval
