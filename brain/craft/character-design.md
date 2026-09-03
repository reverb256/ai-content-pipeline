# Character Design — Engineering Reference (2026-09-02)

> Meticulous reference for consistent characters across AI video + audio drama.
> Follows brain/QUALITY_DOCTRINE.md: SPEC + VALIDATION + SCORED REVIEW.

## 1. Character Sheet Schema

Every character gets ONE canonical sheet at `brain/craft/characters/<name>/README.md`.

### Required Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | Canonical identifier | Mara Voss |
| `role` | Narrative function | protagonist / antagonist / supporting |
| `archetype` | 2-3 word shorthand | weary commander |
| `want` | External goal (drives plot) | Keep the station running |
| `need` | Internal truth (drives arc) | Let go of control |
| `flaw` | Limiting belief (creates conflict) | Cannot delegate without suspicion |
| `voice_params` | Reusable voice config (§3) | base_desc, pitch, rate, timbre, emotion_presets |
| `visual_signature` | Reusable visual anchors (§2) | key_anchor, color_palette, clothing |
| `backstory_lite` | 3-5 bullets — only what affects behavior | — |
| `relationships` | Map + tone per other character | — |

### YAML Template (reusable)

```yaml
character:
  name: "Mara Voss"
  role: "protagonist"
  archetype: "weary commander"
  want: "Keep the station running"
  need: "Let go of control"
  flaw: "Cannot delegate without suspicion"
  voice_params:
    model: voxcpm2
    base_desc: "woman in her late 30s, steady, weary, quiet authority"
    pitch_shift: 0.0
    rate: 0.95
    timbre: "alto, slightly husky, close-mic"
    emotion_presets:
      calm: "steady, even pace, soft"
      angry: "clipped, sharp, raised, tense"
      sad: "slow, lower pitch, breathy"
      fearful: "fast, trembling, higher pitch"
      defiant: "measured, tight, deliberate"
  visual_signature:
    gender: woman
    age: late 30s
    hair: "dark brown, tight bun, grey streaks at temples"
    face: "sharp jaw, tired eyes, faint scar on left cheek"
    clothing: "dark grey flight suit, collar up"
    color_palette: ["#2b2b2b", "#6b6b6b", "#8b4513"]
    key_anchor: "grey-streaked bun + scar on left cheek"
  backstory_lite:
    - "Former fleet engineer, demoted after Kessel incident"
    - "Runs a decommissioned relay station alone"
    - "Doesn't trust automated systems"
  relationships:
    - { to: "Elias", type: "mentor", tone: "warm but distant" }
    - { to: "The Station", type: "antagonist", tone: "adversarial" }
```

---

## 2. Visual Consistency

| Method | Consistency | Cost | Data | Best For |
|--------|-------------|------|------|----------|
| **LoRA per character** | ★★★★★ | High | 20-50 imgs | Recurring, series |
| **IP-Adapter** | ★★★★☆ | Medium | 5-10 imgs | One-shot, tight budget |
| **Seed anchor + descriptor** | ★★★☆☆ | Low | 0 | Background NPCs |
| **Descriptor lock only** | ★★☆☆☆ | None | 0 | Throwaway |

### Specs

- **LoRA**: Trigger `char_maravoss`, strength 0.7-0.9. Store at `characters/<name>/lora/<name>.safetensors`.
- **IP-Adapter**: Strength 0.6-0.8, CLIP Vision Plus. Pair with ControlNet pose if needed.
- **Seed anchor**: Fix seed (e.g. `12345`). Brittle — any prompt change breaks it.

### Descriptor Lock (always apply)

Every prompt MUST contain `key_anchor`:
```
char_maravoss, grey-streaked bun, scar on left cheek,
dark grey flight suit, tired eyes, sharp jaw
```

---

## 3. Voice Consistency

Store at `brain/craft/characters/<name>/voice.yaml` (same as `voice_params`).

### Voice Design Assembly

```
{base_desc}, {emotion_preset}, {timbre}
```

In story.md:
```
Mara (angry): (woman in her late 30s, steady, weary, quiet authority,
clipped, sharp, raised, tense, alto, slightly husky, close-mic)
Who left this running?
```

### Anti-Drift Rules

1. Never improvise base_desc — copy from voice.yaml verbatim.
2. Emotion presets are the ONLY variable — everything else fixed.
3. Pitch shift and rate are global — never change per line.
4. Timbre is a constant — the character's physical fingerprint.
5. New emotion? Add to voice.yaml first — no ad-hoc emotions.

---

## 4. Behavior / Psychology

Map Big-5 axes to dialogue patterns:

| Axis | High | Low |
|------|------|-----|
| **Openness** | Curious questions, metaphor, abstract | Concrete, literal, routine-bound |
| **Conscientiousness** | Structured speech, plans, pauses | Spontaneous, impulsive, loose |
| **Extraversion** | Talks first, fills silence | Reserved, short answers, monotone |
| **Agreeableness** | Softens disagreement, asks permission | Direct, challenges, interrupts |
| **Neuroticism** | Repeats worries, self-doubt | Steady, unbothered, dismissive |

### Catchphrase Discipline

Max ONE use per episode per character. Never consecutive episodes. Overuse kills distinctiveness.

---

## 5. Character Arc

| Format | Arc Type | Beats | Duration |
|--------|----------|-------|----------|
| Short video (1-3 min) | Micro-arc | 1 emotional shift | Single scene |
| Long video (5-15 min) | Mini-arc | 2-3 beats | One narrative turn |
| Audio drama (episodic) | Full arc | 5+ beats | Season-long |

### Full Arc Tracking (Audio Drama)

```yaml
arc:
  want: "Keep the station running"
  need: "Let go of control"
  flaw: "Cannot delegate without suspicion"
  beats:
    - { ep: 1, beat: "Refuses help, insists on solo fix", state: "flaw dominant" }
    - { ep: 2, beat: "Accepts Elias's advice", state: "flaw challenged" }
    - { ep: 3, beat: "Delegates, it fails", state: "flaw reinforced" }
    - { ep: 4, beat: "Realizes failure was micromanaging", state: "flaw broken" }
    - { ep: 5, beat: "Lets go — station stabilizes", state: "need realized" }
```

**Rule**: Every episode's story.md references the current arc beat per character.

---

## 6. Canon Management

### File Structure

```
brain/craft/
├── character-design.md
└── characters/
    ├── mara-voss/
    │   ├── README.md            ← character bible (sheet + arc)
    │   ├── voice.yaml           ← voice config
    │   ├── lora/                ← LoRA weights
    │   ├── references/          ← IP-Adapter images
    │   └── changelog.md         ← who changed what when
    └── elias-cairn/
        └── ...
```

### Change-Log Discipline

```markdown
# Changelog

## 2026-09-02 — j_kro (MINOR)
- Added `defiant` emotion preset to voice.yaml
- Updated arc beat 3: failure cause changed from "sabotage" to "micromanaging"
- Reason: Sabotage contradicted Elias's loyalty established in ep 2
```

### Versioning

- **MAJOR** — personality rewrite, arc reversal, relationship change
- **MINOR** — new emotion preset, new catchphrase, visual anchor added
- **PATCH** — typo fix, wording clarification, no behavioral change

---

## 7. Deterministic QA — Consistency Checklist

Reviewers score 1-10. Average ≥ 7.0 AND no single criterion < 5 = PASS.
Any criterion < 5 = FAIL (rework required).

### Visual QA

| # | Criterion | Pass Condition |
|---|-----------|----------------|
| 1 | Key anchor present | Both `key_anchor` features in frame |
| 2 | Color palette match | 2 of 3 palette colors within ±10% HSL |
| 3 | Clothing match | Same outfit, no contradictions |
| 4 | Age/gender match | No drift to different demographic |
| 5 | LoRA/IP-Adapter applied | Trigger word in prompt log |

### Voice QA

| # | Criterion | Pass Condition |
|---|-----------|----------------|
| 1 | Base desc match | Exact match to voice.yaml |
| 2 | Emotion preset valid | Present in voice.yaml presets |
| 3 | Pitch/rate match | Within ±0.1 of voice.yaml |
| 4 | Timbre consistent | Same actor impression |
| 5 | No cross-contamination | Distinct voice per character |

### Behavior QA

| # | Criterion | Pass Condition |
|---|-----------|----------------|
| 1 | Personality axis match | Dialogue matches Big-5 profile |
| 2 | Arc beat correct | Matches arc tracker for this episode |
| 3 | No bible contradiction | Zero contradictions with README.md |
| 4 | Catchphrase discipline | ≤1 use per episode |
| 5 | Relationship tone | Matches relationship map |

---

## 8. Anti-Patterns

### Visual

| Anti-Pattern | Symptom | Fix |
|--------------|---------|-----|
| **Face drift** | Different look every shot | LoRA + key_anchor in every prompt |
| **Outfit amnesia** | Clothing changes mid-scene | Lock clothing descriptor + reference |
| **Age sliding** | Character ages/regresses | Explicit age in prompt + LoRA |
| **Palette bleed** | Colors shift to defaults | Explicit hex palette in prompt |

### Voice

| Anti-Pattern | Symptom | Fix |
|--------------|---------|-----|
| **Same-voice syndrome** | All characters sound identical | Distinct base_desc + timbre per char |
| **Emotion soup** | Every line different emotion | Scene emotion default, override sparingly |
| **Pitch creep** | Pitch drifts over time | Lock pitch_shift in voice.yaml |
| **Ad-lib voice** | New emotion not in voice.yaml | Add to voice.yaml FIRST |

### Behavior

| Anti-Pattern | Symptom | Fix |
|--------------|---------|-----|
| **Personality drift** | Acts out of profile mid-season | Re-read Big-5 before writing |
| **Arc amnesia** | No change across episodes | Track arc beats per episode |
| **Catchphrase spam** | Signature line every scene | Max 1x per episode |
| **Flat character** | No want/need/flaw | Complete the sheet — no blanks |
| **Bible contradiction** | New episode violates facts | Check README.md before writing |

---

## Sources

- brain/QUALITY_DOCTRINE.md — quality framework (SPEC + VALIDATION + REVIEW)
- brain/audio-workflow-context.md — VoxCPM2 Voice Design, emotion vocabulary
- brain/stage-specs/audio-drama.md — character consistency as scored criterion
- character-profile skill (Hermes) — character sheet structure
- video-factory (NesDevr) — channel config as contract, per-video variance rule
- OpenMontage (iRaees) — quality gates, scored review with pass threshold
