# Local LLM Model Plan — by VRAM tier (2026-09-02)

> Purpose: run meticulous content-craft knowledge (cinematography, voice, story,
> character, ComfyUI determinism, media literacy) on LOCAL models for speed,
> reliability, privacy, and zero marginal cost. Research-grounded (sources at
> bottom). Consensus 2026 guidance: run right-sized modern models at Q4_K_M,
> not the biggest quant you can squeeze.

## Fleet VRAM inventory (verified live)

| Host | GPU | VRAM | Backend | Tier |
|---|---|---|---|---|
| zephyr (workstation) | RTX 3090 | 24GB | CUDA | **big** |
| zephyr | RTX 3060 Ti | 8GB | CUDA | mid |
| nexus | RTX 3060 Ti | 8GB | CUDA | mid |
| forge | 2× RTX 4060 | 8GB ea | CUDA (miners — only when idle) | mid |
| sentry | RX 5600 XT | 6GB | AMD RDNA1 (ROCm weak) | small |

## Recommended models per tier

### 24GB (RTX 3090 — zephyr, the workhorse)
| Model | Quant | VRAM | Speed | Use |
|---|---|---|---|---|
| **Qwen 3.6 27B** | Q4_K_M | ~17GB | 25-35 t/s | **Daily driver** — best overall; agentic, reasoning, 262K ctx native (use 16-32K) |
| Qwen3.5 35B-A3B (MoE) | Q4_K_M | ~20GB | ~110 t/s | Fast interactive chat (only 3B active/token) |
| Gemma 4 26B-A4B | Q4_K_M | ~16GB | ~71 t/s | Multimodal (vision input) |
| Qwen 2.5 14B | Q8_0 | ~16GB | ~35 t/s | Near-lossless quality when text-quality > speed |
| Mistral Small 3.2 24B | Q4_K_M | ~14GB | — | Lightest dense; room for long context |

Pick order for our content work: Qwen3.6-27B for script/story/review reasoning;
Gemma 4 26B-A4B when images need understanding (thumbnail OCR, character
reference checking). Do NOT attempt 70B at Q2 on 24GB — degraded thinking.

### 8GB (3060 Ti / 4060 — zephyr 2nd GPU, nexus, forge)
| Model | Quant | VRAM | Speed | Use |
|---|---|---|---|---|
| **Qwen 3.5 9B** | Q4_K_M | ~6.1GB | 54-58 t/s | **Winner** — full GPU at 32K ctx, best intelligence in class |
| Qwen 3 8B | Q4_K_M | ~6.2GB | 40-46 t/s | Reliable daily, hybrid thinking, multilingual |
| Gemma 4 E4B | Q4_K_M | ~5.5GB | ~49 t/s | Light, tool-calling; forge already has E2B/E4B |
| Phi-4-mini 3.8B | Q4_K_M | ~3.5GB | 55-70 t/s | Speed champion, autocomplete, shell scripts |
| DeepSeek-R1-Distill-7B | Q4_K_M | ~5GB | 38-45 t/s | Reasoning/math specialist |
| Qwen2.5-Coder 7B | Q4_K_M | ~5GB | 40-48 t/s | Coding specialist |

Rule: Q4_K_M default; Q5 only at short ctx. Never below Q4 (severe quality loss).
Never 12B+ on 8GB — offload penalty makes a 9B fully-in-VRAM win everything.

### 6GB (RX 5600 XT — sentry, AMD)
Reality: RDNA1 (gfx1010) has poor official ROCm support; use llama.cpp **Vulkan**
backend or CPU. Models:
| Model | Quant | VRAM | Note |
|---|---|---|---|
| Phi-4-mini 3.8B | Q4_K_M | ~3.5GB | Safe, fast, best fit |
| Gemma 4 E2B / E4B | Q4_K_M | ~3-5.5GB | forge already has the GGUFs; copy over |
| Qwen 3.5 4B | Q4_K_M | ~3.5GB | Chat + tool calling |
| Qwen 2.5 7B | Q3_K_M | ~4GB | Tight; only if 4B insufficient |

Honest ceiling: 3-4B class on sentry. That's fine for embeddings, routing,
fast classification — not for craft reasoning (that's the 3090's job).

## Serving infrastructure plan

1. **llama.cpp server** (llama-server) on zephyr bound to the 3090 — OpenAI-compatible
   `/v1/chat/completions` endpoint on localhost (or tailscale 100.91.11.2).
   - Qwen3.6-27B Q4_K_M + Gemma 4 26B-A4B (multimodal) both fit sequentially.
   - Systemd user unit `llama-craft.service`, GPU 0 (3090) via CUDA_VISIBLE_DEVICES.
2. **8GB nodes**: llama-server on nexus (and forge when not mining) serving
   Qwen3.5-9B — cheap tier for high-volume routine checks (gate scoring,
   classification, metadata) where the 27B is overkill.
3. **Sentry**: llama.cpp Vulkan with Phi-4-mini or Gemma 4 E4B — embeddings/routing.
4. **Hermes wiring**: add each local endpoint as an OpenAI-compatible provider in
   config.yaml (`provider: llama-craft` etc). Route craft-knowledge-heavy prompts
   and the scored-review layer to the local 27B: free, private, fast, no quota.
5. **Craft context injection**: the brain/craft/*.md docs become the system-prompt
   context for local review/synthesis — that's what makes local models "meticulous".

## Files to download (GGUF Q4_K_M, bartowski or official)
- Qwen3.6-27B-Instruct-Q4_K_M.gguf (~17GB) — zephyr
- Gemma-4-26B-A4B-it-Q4_K_M.gguf (~16GB) — zephyr (multimodal)
- Qwen3.5-9B-Instruct-Q4_K_M.gguf (~6GB) — nexus + forge
- Qwen2.5-7B-Instruct-Q4_K_M.gguf (~5GB) — nexus (alt)
- Phi-4-mini-Q4_K_M.gguf (~3.5GB) — sentry

## Sources
- insiderllm.com — what runs on 24GB (2026)
- popularai.org / canitrun.dev — best LLMs RTX 3090 24GB 2026
- quantized.fyi / inferencerig.com / mayhemcode.com — 8GB VRAM tested & ranked
- llmconfigurator.com / 9bench.com — VRAM requirements guide 2026
