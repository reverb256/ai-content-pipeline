# Cinematography — Engineering Reference for AI Video

> Read before any video generation. This is the shot grammar, composition,
> lighting, color, and motion contract videobot applies so visuals are
> non-amateur and deterministically verifiable. Pairs with
> `brain/stage-specs/visuals.md` and `brain/QUALITY_DOCTRINE.md`.

## 0. Pacing constant (NON-NEGOTIABLE)

From `brain/stage-specs/visuals.md`:
```
MAX_WORDS_PER_BEAT = 45
MIN_BEATS_PER_SECTION = ceil(narration_words / 45)
BEAT_DURATION_RANGE = 5..16 seconds
```
A 200-word section needs ≥ 5 visual beats. A 60-word section needs ≥ 2.
Every beat <5s = strobe; every beat >16s = parked slide. Both FAIL.

---

## 1. Shot Grammar — decision table

| Shot size | Abbv. | Coverage | When to use |
|-----------|-------|----------|-------------|
| Extreme Close-Up | ECU | Eyes, hands, detail | Reveal, tension, precision |
| Close-Up | CU | Face, chin-to-crown | Emotion, reaction |
| Medium Close-Up | MCU | Chest up, ~10% headroom | Dialogue default |
| Medium Shot | MS | Waist up | Interaction, demos |
| Medium Long | MLS | Knees up | Walking, context |
| Long / Wide | WS/LS | Full body + environment | Establishing, scale |
| Extreme Wide | EWS | Subject tiny/absent | Vastness, cosmic |

### Framing rules (measurable)
- **Headroom**: 8-15% of frame height. >20% = dead space; 0% = oppressive (tension only).
- **Lead room**: ≥ 2x space in gaze direction vs behind head. Reverse only for menace.
- **Eyeline**: eyes at upper-third line. Never center eyes.
- **Crops**: clavicle (MCU) or sternum (MS). Never at joints.

### 180-degree rule
Draw axis through subjects. Keep ALL cameras on ONE side. Cross only when:
subject crosses on camera, dolly across in one shot, or deliberate disorientation.
Break without intent = amateur. Eyeline match: A screen-right → B screen-left.

---

## 2. Composition — poor / good / great

| Rule | Poor | Good | Great |
|------|------|------|-------|
| **Rule of Thirds** | Dead-center | On third line | On power intersection + directional negative space |
| **Leading lines** | None, flat | Points at subject | Converge precisely on focal point |
| **Negative space** | Fills frame | Clear on one side | Directional with meaning |
| **Depth** | One plane | FG + subject + BG | Foreframe, mid, deep BG; parallax |
| **Edges** | Crops at joints | Clean clavicle/sternum | No distractions |

---

## 3. Camera Movement — cue → movement mapping

| Movement | Emotional cue | When |
|----------|---------------|------|
| **Push-in** | Intimacy, dread, realization | Reveal, emotional peak |
| **Pull-out** | Isolation, scale, loss | Scene end, twist |
| **Pan** | Surveillance, reveal | Establishing, scan |
| **Tilt** | Power (up=dominance, down=vulnerability) | Introduce tall subject |
| **Tracking** | Momentum, journey | Walking, travel |
| **Static** | Stability, tension, authority | Interview, lecture |
| **Handheld** | Urgency, fear, realism | Action, panic |
| **Orbit** | Power, evaluation | Product reveal |

### Movement rules
- Vary movement type ≥ 3 times per 60s. Two identical push-ins = template slop.
- Every move needs an emotional beat. Script the cue, then move.
- Every move must begin and end on a composed frame.

---

## 4. Lighting — setup → mood

### Three-point baseline
| Light | Position | Ratio |
|-------|----------|-------|
| **Key** | 30-45° off axis, above eyes | 1.0 |
| **Fill** | Opposite key, lower | 0.3-0.7 |
| **Rim/Back** | Behind subject, opposite key | 0.8-1.5 |

### Key-to-fill ratio → mood
| Ratio | Look | Use |
|-------|------|-----|
| 1:1 | Flat, news | Info, authority |
| 2:1 | Natural | Interview, tutorial |
| 4:1 | Cinematic | Story, tension |
| 8:1+ | Noir | Villain, thriller |

### Color temperature (K)
| K | Hue | Association |
|---|-----|-------------|
| 1800-2700 | Warm orange | Hearth, nostalgia, danger |
| 3200 | Tungsten | Indoor, intimate |
| 5600-6500 | Daylight | Truth, clinical, outdoor |
| 7000-10000 | Cool blue | Night, tech, melancholy |

### Checklist
- Every light needs an in-world source (window, lamp, screen).
- Eye light: catchlight in BOTH eyes. Dead eyes = corpse/uncanny.

---

## 5. Color Theory for Video

### Palette strategies
| Strategy | Construction | Effect |
|----------|-------------|--------|
| **Complementary** | Opposite wheel (teal-orange) | Pop, energy, blockbuster |
| **Analogous** | Adjacent (blue-teal-green) | Calm, cohesive, natural |
| **Monochromatic** | Single hue, varied value | Stylized, emotional |
| **Split-complement** | One hue + adjacent to opposite | Tension, less clash |

### Grade direction
| Direction | Association |
|-----------|-------------|
| **Teal-orange** | Blockbuster, travel |
| **Desaturated cool** | Dystopian, clinical |
| **Warm vintage** | Nostalgia, period |
| **Green-yellow** | Horror, corruption |

### LUT rules
- Grade CONTRAST first (lift/gamma/gain), then hue.
- Keep skin tones in 0-30° hue band. Off-hue = sick/dead. Mask skin if needed.
- Same base LUT across sequence; vary only intensity.

---

## 6. Motion / Energy — anti-slideshow rule

```
HOOK_WINDOW = first 7 seconds
PATTERN_INTERRUPT = every 60-90 seconds
MIN_BEATS_PER_SECTION = ceil(narration_words / 45)
BEAT_DURATION_RANGE = 5..16 seconds
```

### Cut density guide
| Content type | Cuts/min | Beat target |
|--------------|----------|-------------|
| Tutorial/explainer | 4-10 | 6-15s |
| Documentary/interview | 2-6 | 10-20s |
| Product/hero | 6-12 | 5-10s |
| Cinematic/story | 3-8 | 8-16s |

### Anti-slideshow (deterministic)
A section with N words needs ≥ ceil(N/45) visual beats. Each beat must differ
from previous in ≥ 1 of: shot size, angle, movement, or subject.

### Pattern interrupts (retention)
Every 60-90s insert ONE of: camera movement, shot size jump, subject change,
graphic/text overlay, audio sting, silence drop. Data: 55% gone by 60s
without re-hook (QUALITY_DOCTRINE.md).

---

## 7. Deterministic Checks — run on every render

### Technical gate (blocks)
```bash
# 1) Not frozen: compare frames 5s apart
ffmpeg -i out.mp4 -vf "select='eq(n,0)+eq(n,125)'" -vsync vfr \
  frame_%d.png 2>/dev/null && \
  magick compare -metric RMSE frame_1.png frame_2.png null: 2>&1 | \
  awk '{print ($1<0.05)?"FAIL frozen":"PASS motion"}'

# 2) Blackdetect: reject if >5% near-black
ffmpeg -i out.mp4 -vf blackdetect=d=0.1:pix_th=0.00 -f null - 2>&1 | \
  grep -c black_duration | awk '{print ($1>0)?"FLAG black":"PASS"}'

# 3) Freezedetect: reject if any freeze > 2s
ffmpeg -i out.mp4 -vf freezedetect=n=-60dB:d=2 -f null - 2>&1 | \
  grep -c freeze | awk '{print ($1>0)?"FAIL frozen":"PASS"}'

# 4) Resolution gate: reject < 1280x720
ffprobe -v error -select_streams v:0 -show_entries stream=width,height \
  -of csv=p=0 out.mp4 | awk -F, '$1<1280||$2<720{print "FAIL <720p";exit 1}'
```

### Slideshow detector
```bash
ffmpeg -i out.mp4 -vf "select='gt(scene,0.35)',showinfo" -f null - 2>&1 | \
  grep -c pts_time
# Scene count < ceil(words/45) → FAIL anti-slideshow rule.
```

---

## 8. AI-Gen Specific — FLUX / ComfyUI video

### Model capabilities
| Capability | FLUX | Video (Wan, Hunyuan) |
|------------|------|----------------------|
| Texture/material | Excellent | Good |
| Lighting/mood | Excellent | Good |
| Composition | Good | Moderate |
| Hands/faces | Moderate | Poor-moderate (flag) |
| Temporal consistency | N/A | Moderate |
| Camera movement | N/A | Good if prompted |

### Prompt structure (deterministic)
```
[subject], [shot size], [angle], [movement], [lighting: key dir + temp + ratio],
[color palette + grade], [mood], [medium/film stock], [technical: res, fps, lens],
[negative: exclusions]
```

### Seed discipline
- **Lock seed** for same composition across variations.
- **Seed sweep**: run N..N+10 identical prompts. Pick best; that seed = master.
- **Document**: log seed per frame in `campaigns/<name>/video/seed_manifest.json`.
- **Model version pinning**: log exact model hash. Different revision = different output.

### Known failure modes → prompt fixes
| Failure | Fix |
|---------|-----|
| Extra fingers/limbs | `--neg extra fingers, extra limbs, mutated hands` |
| Garbled text | `--neg text, letters, words, caption` |
| Floating objects | `--neg floating, disconnected, levitating` |
| Inconsistent character | Lock seed + reference image (IP-Adapter) |
| Temporal flicker | Consistent seed + keyframe lock; increase guidance |
| Face distortion | `--neg deformed face, asymmetrical eyes, bad teeth` |
| Watermark | `--neg watermark, logo, signature, artist name` |

### Workflow integration
1. Scriptwriter notes visual beats (≤45 words/beat) in script.md.
2. Videobot generates one clip per beat using prompt structure above.
3. Videobot logs seed + model per frame to `seed_manifest.json`.
4. Videobot runs deterministic checks (Section 7) before muxing.
5. Mux → final.mp4 → run truncation gate from `visuals.md`.

---

## 9. Anti-patterns (instant reject)

| Anti-pattern | Why it fails |
|--------------|--------------|
| Subject dead-center, no offset | Compositionally dead |
| Single visual >45 words | Anti-slideshow FAIL |
| Uniform lighting every shot | Template slop; demonetization risk |
| Jump cuts same angle | Spatial confusion; amateur |
| Break 180° without intent | Viewer loses orientation |
| Limb crops at joints | Visually uncomfortable |
| Skin tone off-hue after grade | Sick/uncanny |
| No catchlight in eyes | Corpse-like |
| Two identical shots in a row | Template; zero variation |
| Prompt omits lighting/color/mood | Generic AI slop |
| No seed documented | Cannot reproduce winning frame |

---

Sources: brain/QUALITY_DOCTRINE.md, brain/stage-specs/visuals.md,
brain/stage-specs/script.md, github.com/NesDevr/video-factory,
github.com/Saganaki22/ContentMachine, ffmpeg.org/ffmpeg-filters.html,
xe.com/colors
