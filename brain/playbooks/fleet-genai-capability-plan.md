# Fleet Gen-AI Capability Plan — voice, music, video, image (2026-09-02)

> Purpose: map cluster GPUs to professional-grade local generation for the
> content pipeline. Research from X + web (2026-09-02, cutting-edge).
> Existing assets inventoried live. This is the plan — execution is staged.

## Fleet GPU inventory (verified)

| Host | GPU | VRAM | Status |
|---|---|---|---|
| zephyr | RTX 3090 + 3060 Ti | 24+8GB | workstation; 3060 Ti runs peakminer; 3090 runs ollama qwen3.8 (32K) |
| nexus | RTX 3060 Ti | 8GB | free for gen work |
| forge | 2× RTX 4060 | 8GB ea | miners (use only when idle/paused) |
| sentry | RX 5600 XT | 6GB | AMD; weakest — skip gen, keep for LLM/embeddings |

## What we already have (inventoried live)

- StabilityMatrix packages on zephyr: **ComfyUI** (installed, ~no models loaded),
  **InvokeAI**, **Wan2GP** (the 8GB-friendly video/audio studio).
- ComfyUI MCP server repo: ~/Projects/comfyui-mcp + ~/.comfyui-mcp.
- 10 ComfyUI skills installed (inventory, lora-training, nodes-dev, prompt-eng,
  prompt-interview, research, troubleshooter, video-pipeline, voice-pipeline,
  workflow-builder).
- ~/.cache/huggingface = 4.7GB models already downloaded.
- FLUX2 workflows in hairathome; flux3_video_tool.py in hermes-agent.
- Audio-drama pipeline: VoxCPM2 + storyteller.py (TTS, working).
- ComfyUI AGENTS.md defines engineering style + NO-internet-requests rule.

## 8GB-vram ideal models (X + web research 2026-09-02)

### All-in-one: Wan2GP (already installed!)
- Browser-based AI video/image/audio studio, optimized for 6-8GB VRAM.
- Models: Wan 2.1/2.2 (cinematic video), LTX-2 (video + native sync audio),
  Hunyuan Video, Flux (images), Qwen Image. Has MCP server.
- Best low-friction path for parallel video gen on the 8GB cards.

### Image
- **Flux (dev/2.x)** GGUF Q4/Q5 — best local images. Works in Wan2GP/ComfyUI.
  Flux.2 Klein 4B GGUF fits 8GB easily (the 3060 Ti/4060s).

### Video
- **LTX-2 / LTX-2.5** (distilled GGUF) — accessible high-quality local video,
  I2V, native audio. Quantized builds fit modest VRAM.
- **Wan 2.2** — cinematic quality (in Wan2GP).
- Expect 4-16s clips; use low CFG, turbo LoRAs on 8GB.

### Music / Audio
- **LTX-2 native synchronized audio** — video + matching audio in one model.
- **Heart-MuLa 3B/7B** — open autoregressive music, ComfyUI nodes; text-to-music,
  singing, 4+ min, BPM/key control, LoRA trainable.
- **MiniMax Music3 / H3** — music gen + audio refinement in ComfyUI.

### Voice / TTS / cloning (ComfyUI nodes — 2026 frontrunners)
- **ComfyUI-FL-Qwen3TTS** (filliptm) — zero-shot clone from 5-15s audio,
  natural-language voice design ("warm raspy soul singer, female, 30s"),
  10 languages, fine-tune UI.
- **ComfyUI-Qwen-TTS** (flybirdxx) — same class, low-latency streaming.
- **ComfyUI-OmniVoice-TTS** (Saganaki22) — 600+ languages, clone 3-15s,
  multi-speaker dialogue, non-verbal tags (laughter/sighs).
- **ComfyUI-Breeze-TTS-2** — top voice-design benchmarks, fast, character
  consistency.
- Chatterbox TTS — zero-shot clone 5s, 23 languages (we have chatterbox skill).
- VoiceStudio — local ElevenLabs alt (16 TTS + 11 ASR, 3s clone, dubbing).

### Singing / full songs
- **ComfyUI_FL-SongGen (Tencent LeVo)** — full songs with vocals+instrumentals
  from lyrics, style transfer, dual-track, ~4:30, 10-12GB VRAM (zephyr 3090).
- Stable Audio 2/2.5 — instrumentals, inpainting, commercial-friendly.
- **ComfyUI_MusicTools** (jeankassio) — stems, vocal naturalizer, mastering,
  LUFS normalization (post-processing essential).
- Pro singing pipeline: SongGen/TTS → UVR stems → RVC voice conversion →
  recombine + master in MusicTools.

## Fleet mapping (which job on which GPU)

| Job | Host/GPU | Tooling | Notes |
|---|---|---|---|
| Heavy LLM craft review | zephyr 3090 | ollama qwen3.8:27b | running (32K ctx — see ceiling test) |
| Music/singing | zephyr 3090 | SongGen, Heart-MuLa, Stable Audio | 10-12GB fits 24GB |
| TTS/cloning quality | zephyr 3090 | Qwen3TTS / OmniVoice / Breeze | best quality |
| Image gen batch | zephyr 3060 Ti OR nexus/forge 8GB | Flux.2 Klein GGUF | parallelize when not mining |
| Video gen batch | nexus/forge 8GB | Wan2GP (already installed), LTX-2 GGUF | parallel Vox/shorts when miners idle |
| TTS high-volume | nexus/forge 8GB | Chatterbox / Qwen3TTS quantized | offload from 3090 |
| Audio-drama production | zephyr 3090 + 8GB fleet | VoxCPM2 + storyteller (existing) + MusicTools | existing pipeline |
| Embeddings/routing | sentry 6GB | Phi-4-mini/Gemma (Vulkan) | AMD-friendly |

## Gaps to close (execution backlog)

1. **Wire ComfyUI**: load models into StabilityMatrix ComfyUI (it has ~none),
   or use Wan2GP for 8GB jobs; start the server + MCP.
2. **Install the audio nodes** (Qwen3TTS/OmniVoice/Breeze, SongGen, MusicTools)
   via ComfyUI Manager.
3. **Big-parallelize voice/video**: cron/systemd job that when miners idle,
   dispatches batch TTS/video jobs across nexus+forge (2×4060s + 3060 Ti).
4. **Music capability**: Heart-MuLa + SongGen for music beds and audio-drama
   scoring (currently missing entirely).
5. **Register the MCPs** so bots can invoke generation (comfyui-mcp exists).
6. Confirm agent needs (DMs sent to videobot/voicebot/thumbnailbot/storyteller).

## Sources (X + web 2026-09-02)
- X: @MAXdeg0 (Wan2GP), @Machinedelusion (Heart-MuLa), @wildmindai (TTS nodes),
  @shiqway92 (LTX-2 + audio), official ComfyUI.
- Web: github.com/deepbeepmeep/Wan2GP; ComfyUI Manager registry.
