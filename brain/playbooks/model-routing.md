# Model & Provider Routing — Automated Content Machine

> How the machine picks the best model per stage and falls back when quota
> runs out. Production never stalls on a quota limit. The rule: use the BEST
> available, fall back to the CHEAP/UNLIMITED tier, then to LOCAL.

## The Fallback Principle

Every stage has a primary (best quality) and a fallback chain (cheaper, then
local/free). If the primary 429s, fails, or hits quota, the machine drops to
the next tier WITHOUT stopping. It logs which tier served, so the weekly
review knows what to bump.

```
BEST (quality) → CHEAP (volume) → LOCAL (free, always available)
```

## Video Generation

| Tier | Provider | Cost | Notes |
|------|----------|------|-------|
| **Primary** | xAI Imagine (video_generate) | Paid, quota-limited | Image-to-video, up to 15s, 720p. Best motion/quality. |
| **Fallback 1** | Manim CE (local) | Free, CPU/GPU | 3Blue1Brown-style animated explainers. Programmatic, unlimited, policy-safe. |
| **Fallback 2** | ComfyUI (local, nexus) | Free, GPU | FLUX/Wan for images + video. We have the comfyui MCP. |
| **Fallback 3** | Stock footage + ffmpeg | Free/low | Pexels/Storyblocks B-roll + Ken Burns + captions. Last resort, still original enough with real narration. |

**Rule:** xAI for short cinematic clips (Shorts, intros). Manim for anything
explanatory (long-form education — also the most policy-safe). ComfyUI when
we need custom visuals at scale. Stock last.

## Voice / TTS

| Tier | Provider | Cost | Notes |
|------|----------|------|-------|
| **Primary** | Chatterbox (local GPU, zero-shot clone) | Free, local | Resemble AI neural voice, GPU-accelerated (3.8s per 8s audio on 3090). Voice cloning from 10-30s ref. The established homelab TTS. |
| **Fallback 1** | xAI TTS (text_to_speech, tts.provider=xai) | Paid, quota | Currently wired in Hermes. Good quality, cloud. |
| **Fallback 2** | Edge TTS (built-in, free) | Free | Microsoft Edge voices, unlimited, decent quality. |
| **Fallback 3** | piper / espeak (local) | Free | Robotic but always available. Never stall on voice. |

**Rule:** Chatterbox when it's up (best quality, free, local). xAI when
Chatterbox is down. Edge for volume. Local last.

## LLM / Scripting

| Tier | Provider | Cost | Notes |
|------|----------|------|-------|
| **Primary** | Nous (longcat-2.0 / glm-5.2) | Free tier, RPM-limited | Best reasoning for scripts/plans. |
| **Fallback 1** | opencode-zen (nemotron-3-super) | Unlimited RPM | High-volume work. |
| **Fallback 2** | opencode-go (deepseek-v4-flash) | Cheap/free | Fast drafting. |
| **Fallback 3** | nous hy3:free | Free | Last resort, fast. |

Already the configured fallback chain in profiles. The machine inherits it.

## Images (thumbnails, visuals)

| Tier | Provider | Cost | Notes |
|------|----------|------|-------|
| **Primary** | ComfyUI FLUX (local, nexus) | Free, GPU | Best quality, local. |
| **Fallback 1** | xAI / Gemini image gen | Paid quota | Cloud quality. |
| **Fallback 2** | Ideogram / Canva | Free tier | Thumbnails with text (Ideogram is best for text-in-image). |

## Quota Detection

The machine checks for quota exhaustion before picking a provider:

- **xAI video/voice:** 429 / "quota exceeded" / "insufficient credits" → next tier
- **Nous LLM:** 429 / 529 → fallback chain (already configured)
- **Chatterbox:** container down / timeout → xAI → Edge
- **ComfyUI:** nexus unreachable → stock footage fallback

A helper script `scripts/api/pick-provider.sh` reads the current health of
each provider and echoes the tier to use. The bots call it before production.

## The 90-Second Review Gate (still human)

Even with full automation, the research is clear: the hook + thumbnail need a
human glance per batch to avoid the "inauthentic content" demonetization trap.
This is NOT content work — it's a 90-second approve/reject per batch.

## Rules

1. Best quality first, always. Fall back only on failure/quota, never by
   default.
2. Log which tier served every asset (`performance/model-routing.log`). The
   weekly review uses this to tune the chain.
3. Never stall. If the best tier is down, produce with the next tier. A
   decent video now beats a perfect video never.
4. Policy safety is absolute. The fallback to stock/Manim is also the
   policy-safe choice — it produces original content, not slop.
5. When a quota resets (monthly), the primary tier comes back automatically —
   the chain is checked per-asset, not cached.
