# ComfyUI Determinism — Engineering Reference (2026-09-02)

> **Read before any batch generation, character lock, or reproducible pipeline run.**
> Defines how to make ComfyUI outputs *repeatable* and *versioned-as-code* — not vibes.

## 1. Determinism Model — Reproducibility Contract

| Knob | Reproducible? | Impact | Notes |
|------|:------------:|--------|-------|
| `seed` | ✅ | Total | Same seed + model + params = near-identical (bar GPU drift) |
| `sampler_name` | ✅ | High | `euler`, `dpmpp_2m`, `uni_pc` — distinct noise schedules |
| `scheduler` | ✅ | High | `normal`, `karras`, `exponential` — step weighting |
| `steps` | ✅ | Medium | More = convergence; 20-50 typical |
| `cfg` | ✅ | High | Classifier-free guidance; model-dependent sweet spot |
| Model file (hash) | ✅ | Total | Different quant of same name ≠ same output |
| VAE | ✅ | Medium | Color science, sharpness, artifacts |
| Resolution | ✅ | High | Native only (512 SD1.5, 1024 SDXL/FLUX) |
| Prompt text | ✅ | Total | Tokenizer deterministic |
| LoRA / ControlNet strength | ✅ | High | Stacking requires weight reduction |
| **GPU architecture** | ❌ | Low | bf16 accumulation differs Ampere vs Ada |
| **Attention backend** | ❌ | Low | `sdpa`/`xformers`/`flash-attn` — tiny pixel drift |
| **ComfyUI / node version** | ⚠️ | Medium | Pin in manifest |

```
Reproducibility contract:
  Identical seed + model_hash + vae_hash + lora_hash + sampler + scheduler +
  steps + cfg + resolution + prompt + versions + SAME GPU → ≈99.5% pixel match
  Across GPU architectures → ≈95-98% (bf16 drift, acceptable for production)
```

**Rule:** Never claim "identical" — claim "reproducible within architecture tolerance."

---

## 2. Declarative Workflow Practice — Version-as-Code

```
workflows/
├── templates/                    # Reusable base graphs
├── jobs/                         # Parameterized instances
└── manifests/                    # Sidecar records (§6)
```

**Requirements:**
1. Flat JSON — no embedded base64, no API calls inside graphs
2. Parameters at top level (seed, prompt, model, lora) in `_meta` block
3. Version field: `"version": "1.2.0"`
4. Node versions pinned: `"comfyui_version": "0.2.47"`
5. No hardcoded paths — use ComfyUI model dropdown names

**Template rule:** Reused 3+ projects → template. Single campaign → job file. Naming: `{pipeline}_{model}_{semver}.json`

---

## 3. Control Hierarchy — Decision Flow

```
Need to control...          → Method
─────────────────────────────────────────────────────────
Subject identity            → 1-5 refs: IP-Adapter Face/Plus
                            → 15+ refs: Train LoRA
                            → Photoreal face: InstantID/PuLID
Composition/layout          → Edges: Canny → Depth: Depth → Pose: OpenPose
                            → Sketch: Scribble → Multiple: Stack (order matters)
Style/aesthetic             → Ref image: IP-Adapter Style → Trained: LoRA
                            → Prompt-only: Style keywords (weakest)
Start from existing image   → img2img + denoise 0.3-0.7
Text only, no constraints   → txt2img (least control)
```

**Stacking weights** (signals compete, not add):

| Combo | LoRA | IP-Adapter | ControlNet |
|-------|------|------------|------------|
| Identity + Structure | 0.8 | 0.5 | 0.6 |
| Identity + Style | 0.7 | 0.6 | — |
| All three | 0.7 | 0.4 | 0.5 |

**Stack order:** LoRA → IP-Adapter → ControlNet → Prompt

---

## 4. Character/Scene Lock

```
[Load Checkpoint] → [LoRA (0.7-0.9)] → [IP-Adapter (0.4-0.7)] → [ControlNet] → [KSampler, FIXED SEED]
```

**Per-character profile** (`projects/{char}/profile.yaml`):
```yaml
character: sage
trigger_word: sage_character
lora: { file: sage_flux_v3.safetensors, strength: 0.8 }
ip_adapter: { model: ip-adapter-plus-face_sdxl_vit-h.safetensors, weight: 0.5 }
seed_base: 1234567890
```

**Drift fixes:**

| Symptom | Fix |
|---------|-----|
| Face changes | Raise IP-Adapter weight, add ControlNet OpenPose |
| Body proportions shift | Add ControlNet Depth + Canny |
| Style bleeds | Lower IP-Adapter style weight, separate face/style |
| LoRA too strong (ignores prompt) | Drop to 0.6-0.7 |
| LoRA too weak (loses identity) | Raise to 0.9, add IP-Adapter |

---

## 5. Prompt Discipline — Structure for Determinism

```
{SUBJECT}, {MEDIUM}, {STYLE}, {LIGHTING}, {CAMERA}, {QUALITY}, {MOOD}
```

| Slot | Example | Purpose |
|------|---------|---------|
| Subject | `sage_character, woman, green eyes` | Trigger word FIRST |
| Medium | `photorealistic portrait, dslr photo` | Material/format |
| Style | `cinematic, editorial, film grain` | Aesthetic family |
| Lighting | `soft studio light, rim lighting` | Light direction/quality |
| Camera | `85mm lens, f/1.4, shallow DOF` | Lens character |
| Quality | `8k, sharp focus, highly detail` | Resolution hints |
| Mood | `confident, contemplative, intense` | Emotional register |

**Negative prompt (standard):**
```
low quality, blurry, distorted, deformed, bad anatomy, extra limbs,
text, watermark, signature, jpeg artifacts, worst quality, low resolution,
oversaturated, underexposed, noise, grain, cropped, out of frame
```

**Consistency rules:**
1. Same character → same trigger word (never swap mid-project)
2. Same style → same keyword set (copy verbatim)
3. Same quality → same tags (don't alternate `8k`/`4k`)
4. Prompt order matters — earlier tokens condition stronger. Subject first.
5. Avoid semantic contradictions — `photorealistic, oil painting` fights itself.

---

## 6. Repeatability Workflow — The Generation Manifest

### Sidecar Manifest (`*.manifest.json`)

```json
{
  "version": "1.0.0",
  "timestamp": "2026-09-02T14:30:00Z",
  "output_file": "product_shot_a_001.png",
  "workflow": "jobs/2026-09-02_product_shot_a.json",
  "workflow_version": "1.2.0",
  "comfyui_version": "0.2.47",
  "gpu": "NVIDIA RTX 4090",
  "seed": 1234567890,
  "model": { "file": "flux1-dev.safetensors", "hash_sha256": "abc123..." },
  "vae": { "file": "ae.safetensors", "hash_sha256": "def456..." },
  "loras": [{ "file": "product_style_lora.safetensors", "strength": 0.8, "hash_sha256": "ghi789..." }],
  "sampler": "euler", "scheduler": "normal", "steps": 25, "cfg": 3.5,
  "resolution": [1024, 1024], "denoise": 1.0,
  "prompt": "sage_character, woman, ...",
  "negative_prompt": "low quality, blurry, ...",
  "ip_adapter": { "model": "ip-adapter-plus-face_sdxl_vit-h.safetensors", "weight": 0.5 },
  "controlnets": [],
  "output_hash_sha256": "xyz987..."
}
```

### The Gate

```
DECLARATIVE when: ✅ Manifest exists + all fields + model hashes + exact seed
                  + workflow versioned in git + re-run possible from manifest only
UNREPRODUCIBLE when: ❌ No manifest / "random seed" / workflow modified / model replaced
```

**Rule:** No output ships without its manifest. Manifest written at generation time.

---

## 7. Batching/Iteration — Controlled Variation

**One-Knob Rule:** Change exactly ONE parameter between comparison images.

**Seed offset:** `base_seed = 1234567890` (from profile), `variant_n = base_seed + n`. Never reuse seeds across different prompts.

**Grid sweeps:**

| Sweep | Fixed | Delta |
|-------|-------|-------|
| Sampler | seed, model, prompt, steps, cfg | sampler_name: [euler, dpmpp_2m, uni_pc] |
| CFG sweet spot | seed, model, prompt, sampler, steps | cfg: [1.5, 3.0, 5.0, 7.0] |
| LoRA strength | seed, model, prompt, sampler | lora: [0.5, 0.6, 0.7, 0.8, 0.9, 1.0] |
| Seed variance | model, prompt, sampler, steps, cfg | seed: [base, +1, +2, +3] |

**Comparison:** Render all variants in one session. Save all. Log sweep: `sweeps/2026-09-02_cfg_sweep.md`. Select winner by pre-defined criteria — not vibes.

---

## 8. Common Failure Modes + Fixes

| Failure | Cause | Fix |
|---------|-------|-----|
| **Doubled limbs** | Low steps, high CFG | Steps 30+, lower CFG 0.5-1.0, add OpenPose |
| **Text gibberish** | Model can't render text | Avoid text in prompts; add post-render in editing |
| **Character drift** | LoRA weak, no IP-Adapter | LoRA 0.8+, add IP-Adapter face, fixed seed |
| **Style bleed** | IP-Adapter style too high | Lower to 0.4, separate face + style adapters |
| **VAE artifacts** | Wrong VAE or tiling | Use model-matched VAE, enable VAE tiling |
| **Blurry output** | Few steps, wrong res, low CFG | Increase steps, native res, raise CFG |
| **Over-saturated** | CFG too high | Lower CFG 1.0, `oversaturated` in negative |
| **Frozen motion** (video) | Denoise too low | Raise denoise 0.5-0.7, add motion LoRA |
| **Temporal flicker** (video) | No deflicker | Apply deflicker post-process |
| **Face morphing** (video) | No face lock | IP-Adapter + FaceDetailer per-frame |
| **Checkerboard** | VAE decode tiling | Enable `vae_tiled` in ComfyUI |
| **Prompt ignored** | LoRA overfit, CFG low | Lower LoRA, raise CFG, subject tokens earlier |

### Pre-Flight Checklist

- [ ] Model hash matches manifest
- [ ] VAE matches model family
- [ ] LoRA trigger word correct in prompt
- [ ] Resolution native for model
- [ ] Seed set (not random)
- [ ] Sampler + scheduler valid for model
- [ ] CFG in sweet-spot range
- [ ] Output directory writable
- [ ] Manifest template ready

---

## Sources

- ComfyUI Docs — https://docs.comfyui.com/
- ComfyUI GitHub — https://github.com/comfyanonymous/ComfyUI
- FLUX — black-forest-labs/FLUX
- IP-Adapter — https://github.com/tencent-ailab/IP-Adapter
- ControlNet — https://github.com/lllyasviel/ControlNet
- Wan 2.2 — https://github.com/Wan-Video/Wan2.2
- AnimateDiff — https://github.com/ArtVentureX/animatediff-motionlora
- Kohya_ss — https://github.com/bmaltais/kohya_ss
- AI-Toolkit — https://github.com/ostris/ai-toolkit
- FramePack — https://github.com/lllyasviel/framepack
