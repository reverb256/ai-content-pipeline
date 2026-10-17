# Reference Implementations — What We Stole (2026-08-29)

> Working open-source faceless-content pipelines we studied, and the patterns
> we adapted. Clones live in `~/Projects/reference-pipelines/` (not part of
> this repo — reference only).

## Repos Studied

| Repo | What it proved |
|------|----------------|
| **faceless-video-engine** (Mystery-CLI, MIT) | The closest to our design. Runs a REAL channel daily (Proof of Necessity). Config-driven per channel. Has the critic pass, AI-disclosure, one-video/day policy guard, Remotion→ffmpeg fallback render. |
| **youtube-agentic-ai-studio** (raunakpatil, MIT) | 100% free stack (Gemini + Edge TTS + Pexels). 8-model fallback chain, human review dashboard, Shorts support. |
| **MoneyPrinterTurbo** (harry0703, 100k+ stars) | The battle-tested one-command Shorts/long-form pipeline. |
| **YT-Automator** (khan-masud, MIT) | FFmpeg-native (no MoviePy — faster, no leaks), GitHub Actions cloud daily execution, resilient Gemini cascade. |
| **youtube-shorts-pipeline / Verticals v3** (rushindrasinha) | Niche intelligence (per-niche tone/visuals/music) = our oracle's job. Anti-hallucination source tracing. Private-by-default upload. |
| **TubeAssistant** (metiu1, MIT) | 24/7 autonomous daemon, Telegram control, analytics-driven topic selection, crash-recovery checkpoints. |

## Patterns We Adopted

### 1. The Critic Pass (from faceless-video-engine)
The script is written, then a **critic** judges it on: what the viewer learns,
surprise, clarity, interactivity. If it fails, the script is rewritten ONCE
with the critique injected. The gate never breaks an unattended run — a
failure ships the current draft.

**Adoption:** add a critic step to scriptwriter's contract (judge → one
rewrite round → ship). This is the quality guard that keeps scripts from
going stale/templated (which is also the anti-inauthentic-content policy
guard).

### 2. Pexels Stock Footage with Layered Fallback (from faceless-video-engine)
```
1. Pexels exact search term (with retries)
2. Pexels first word (broader)
3. Pexels generic niche terms (from config)
4. Gradient/placeholder clip (never blank)
```
Free, topic-aware, and a frame is never blank.

**Adoption:** wire Pexels API into our videobot's "stock" tier. Need a
PEXELS_API_KEY (free, 200 req/hour). This replaces the "stock" fallback with
a real free footage source.

### 3. Config-Driven Channel Design (from faceless-video-engine)
One `config.json` per channel: niche, channel_persona, editorial (CTA, banned
topics, required stakes, hook examples, visual_direction), video.ai_style,
captions, playlists, upload, schedule. Everything channel-specific is config,
not code.

**Adoption:** our per-niche profiles should be config files, not hardcoded
prompts. The oracle routes to a niche → loads that niche's config → the bots
produce within it. This is the "niche intelligence" from Verticals v3 too.

### 4. AI-Disclosure on Upload (from faceless-video-engine)
`containsSyntheticMedia` is set automatically on upload because the voice is
synthetic. Keeps the channel monetizable (deceptive synthetic = not
monetizable; disclosed synthetic educational = monetizable).

**Adoption:** publishbot must set `containsSyntheticMedia: true` on every
upload. (Our video/voice are AI-generated, so this is mandatory.)

### 5. One Quality Video Per Day (from faceless-video-engine)
Mass, repetitive uploads trigger YouTube's *inauthentic content* policy and
can disqualify a channel. The engine enforces one/day by design.

**Adoption:** our cron cadence should cap at 1 quality video/day per channel.
Volume is NOT the strategy — quality + consistency is.

### 6. Human Review Before Upload (from agentic-studio + faceless)
Uploads default to private/unlisted; a human reviews then publishes. Most
sensible implementations do this.

**Adoption:** publishbot uploads as **private** by default; the review gate
(a human glance at hook + thumbnail) approves the flip to public. This is
already in our design — confirmed correct.

### 7. FFmpeg-Native Rendering (from YT-Automator)
Direct FFmpeg subprocess pipelines (no MoviePy) = no memory leaks, low CPU,
fast rendering. We already use ffmpeg directly (manim output + ffmpeg
stitch) — confirmed correct.

## NOT Adopted (deliberately)

- **Edge TTS** — j_kro directive: use Chatterbox or something newer. Edge TTS
  is free but we have Chatterbox (local GPU) + xai TTS as better options.
- **MoviePy** — we use ffmpeg-native (faster, no leak).
- **Telegram control** — not needed yet; our kanban + cron is the control
  surface. Could add later if useful.

## Repo Locations

- `~/Projects/reference-pipelines/faceless-video-engine/`
- `~/Projects/reference-pipelines/youtube-agentic-ai-studio/`
- (Others studied via GitHub, not cloned: MoneyPrinterTurbo, YT-Automator,
  Verticals v3, TubeAssistant)
