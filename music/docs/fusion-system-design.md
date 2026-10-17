# Fusion genre system — research and design

Research date 2026-10-09. Sources are named inline; nothing here is inferred from
local state.

## The ask

Produce chill-lounge-rooted tracks that drift across **drum & bass** and
**trance** — separate tracks of 5–8 minutes — then assemble them into a
**2-hour DJ mix for YouTube**. Build the *system*, not one batch.

Two hard constraints fall out of that, and neither is obvious:

1. **A DJ mix needs the tracks to share a tempo grid.** Chill lounge (~75), DnB
   (~174) and trance (~138) do not mix as written.
2. **A three-way genre blend is the documented failure case** for AI fusion.

Both are solvable, and the fixes are the design.

---

## 1. Genre fusion — the 3-axis method

Source: suno.bi, "AI Music Genre Fusion Methodology (2026) — A 3-Axis Engineering
Approach". https://suno.bi/en/blog/ai-music-genre-fusion-method-sunomv-2026/

**Why keyword stuffing fails.** Pile `lo-fi jazz trap pop city pop synthwave` into
a prompt and the model "finds the strongest consensus tag as the spine and
compresses the other genres into decoration". Two outcomes: ~90% collapses into
the first genre, or everything dilutes to a beige average.

**The method — assign each axis an owner:**

| Axis | Owner | What it carries |
|---|---|---|
| **Rhythm** | exactly ONE genre | BPM + drum pattern + groove |
| **Harmony** | a DIFFERENT genre | chord progression + mode |
| **Instrumentation** | split **7:3** | primary 70%, secondary 30% |

The secondary genre must be **≥30% of instrumentation** and must appear in a
**high-visibility slot** (chorus or bridge) or the listener will not register the
fusion at all.

### The failure that matters most here

> **Failure 1 — Both genres fight for rhythm.**
> Broken example: `Lo-fi boom bap + drum & bass 174 BPM + jazz swing`.
> **Fix:** rhythm axis hosts exactly one genre's BPM and kit. Other genres'
> rhythmic elements must be **explicitly routed to bridge/transition slots**.

**That fix is exactly the "drift" being asked for.** A track whose rhythm axis is
owned by one genre, with the other two genres' rhythmic material confined to
bridge/transition sections, produces a tune that *sounds* like it drifts between
genres without the rhythm layer fighting itself. The drift is a structural
decision, not a prompt wish.

### Other failures to design against

- **Emotionally opposed genres** (attack vs soothe) never fuse. Lounge/DnB/trance
  are all warm-to-uplifting, so this one does not bite.
- **Secondary genre too quiet** — hence the 7:3 floor and the visibility slot.
- **Lyrics disconnected from the fusion** — a chill track with club lyrics reads
  as costume.

---

## 2. Tempo — how real DJs cross genre gaps

Source: Vibes DJ, "DJ Transitions: The Complete Guide".
https://vibesdj.io/dj-tools/dj-transitions
Corroborated by DJ.Studio "9 DJ Tempo Change Techniques" and MusicRadar.

### The pitch ladder

| Gap | What works |
|---|---|
| ≤ ~4% | ride the pitch fader; nobody on the floor hears it |
| 4–8% | audible but workable — spread across a phrase or split between decks |
| > 8% | pitching "sounds wrong even with keylock on, because the groove itself changes character" |

Key cost: ~6% pitch = one semitone (keylock off).

### The bridge rule — this is the load-bearing finding

> **Halftime and doubletime bridges.** Tracks at a **2:1 tempo ratio share a
> pulse**: drum and bass at 174 BPM reads as 87 in halftime, so an **87 BPM track
> blends into it with zero pitch change**. The same logic pairs 70 with 140, and
> explains why trap at 150 feels like 75.

**So 87 and 174 are one tempo, not two.** That single fact decides the whole
tempo design.

### When there is no direct bridge

> House at 124 and DnB at 174 do not line up: 124 doubled is 248, 174 halved is
> 87. The working route is a **stepping stone**: echo out into something around
> 87, then blend that into 174 as a seamless doubletime layer. **Two clean moves
> instead of one impossible one.**

And where no route exists at all: *"make the jump a moment: cut on the one, echo
out, spinback, or step through an intermediate track. Gaps like this often become
the most memorable switch of the set."*

### Three rules under every technique

1. **Phrasing** — dance music is built in **16 and 32 bar** phrases. Every move
   (first fader up, bass swap, final fader down) lands on a phrase boundary.
2. **The one-bass rule** — never two basslines at full level. The incoming track
   enters with its **low EQ fully cut**, and the bass swap is **one decisive move
   (1–2 beats)**, not a slow crossfade.
3. **Energy direction** — decide lift / hold / reset *before* choosing technique.

### The nine techniques (the ones this system will use)

| # | Technique | Length | Use |
|---|---|---|---|
| 1 | **EQ Blend (bassline swap)** | 16–32 bars | default for beatmatched 4/4 |
| 3 | **Echo Out** | 1 bar | works between **any** two tempos |
| 4 | **Filter Fade** | a phrase | melodic material |
| 7 | **Drop Swap** | 8 bars | DnB double drops |
| 9 | **Long Ambient Blend** | 32–64 bars | "core skill of deep and melodic sets" |

Technique 9 is the one a chill 2-hour mix is built on; technique 3 is the escape
hatch for any tempo gap.

### Harmonic mixing

Camelot wheel: same number, ±1 step, or the relative major/minor. **+2** is the
classic energy lift.

**The practical loophole:** if the blend happens over intros, outros, or
percussive sections — drums against drums — a key clash is inaudible, because
nothing tonal is fighting. So key compatibility constrains *long melodic
overlaps*, not transitions as such.

---

## 3. Tooling

### pyCrossfade — the transition engine

https://github.com/oguzhan-yilmaz/pyCrossfade — **MIT**, v0.4.0 (Aug 2026),
actively maintained.

- Beat matching **on the level of every bar**, which is what makes it survive
  humanised (non-grid) timing where naive whole-track stretching fails.
- **Gradual BPM shift across downbeats** — master's speed ramps linearly
  (1.01x, 1.02x … 1.10x) over K bars, so a tempo change is not a jolt.
- **3-band DJ EQ crossfade** — master shelves low+high out while slave shelves
  them in, both taking a mid dip. Click-protected seams.
- Fade profiles: `linear`, `cosine`, `equal_power`.
- CLI: `song`, `extract` (BPM + key via Essentia), `mark-downbeats`, `cut-song`,
  `crossfade`, `crossfade-many`.
- `crossfade()` returns a typed `Transition` with every component slice — so the
  mix is an inspectable artifact, not a rendered blob.
- Beat tracking via madmom is slow (45–150 s/file) but **caches annotations**.

### ComfyUI — the render and master engine

Confirmed live from `/object_info` (1124 node types, 111 audio-related):

| Role | Nodes available |
|---|---|
| **Generation** | `RunningHub ACE-Step *`, `FL_YuE2_*`, `EmptyMiniMaxMusic3LatentAudio` + `MiniMaxMusic3TextEncode`, `ConditioningStableAudio`, `SoniloTextToMusic`, `ByteDanceSeedAudio` |
| **Structure control** | `FL_YuE2_Plan`, `FL_YuE2_ScoreEditor` — ABC-notation score editing, so composition is an editable artifact |
| **Mastering** | `Music_LufsNormalizer`, `Music_MasterAudioEnhancement`, `Music_Compressor`, `Music_Equalize`, `Music_Gain`, `Music_StereoEnhance` |
| **Stems** | `Music_StemSeparation`, `Music_StemRecombination` |
| **Assembly** | `AudioConcat`, `AudioMerge`, `AudioEqualizer3Band`, `TrimAudioDuration`, `AudioAdjustVolume` |
| **Repair** | `Music_AudioRepair`, `Music_NoiseRemove`, `Music_AudioUpscale`, `Music_AudioTrimmer` |

**Division of labour, and why it is split this way:**

- ComfyUI can **concatenate and EQ**, but it has **no beatmatching, no
  phrase-alignment, and no tempo ramp** — nothing that reasons about bars. A DJ
  mix is precisely those things. So ComfyUI cannot build the mix.
- pyCrossfade **does** beatmatch and crossfade but is not a mastering chain.
- Therefore: **pyCrossfade builds the transitions; ComfyUI masters the result**
  (`Music_LufsNormalizer` to release spec, `Music_MasterAudioEnhancement`,
  `Music_StemSeparation` if stems are wanted).

Reachability fixed this session: ComfyUI was ClusterIP-only, so nothing on the
host could reach it and every call fell back to `kubectl exec`. It now publishes
**NodePort 32188** (Argo-managed), reachable at `http://127.0.0.1:32188`.

### MCPs — what exists and what does not

Searched the tool catalog (28 connected servers, 2815 tools) **and** the web.

- **No DJ-mixing MCP.** Nothing offers beatmatching or set assembly.
- `comfyui` MCP exists (24 tools: `submit_workflow`, `wait_for_completion`,
  `get_history`, `list_node_types`, `list_models`, …) — now reachable.
- Web findings, for the record: `cloudygetty-ai/mixxx-mcp` (Mixxx DJ software),
  `TwelveTake-Studios/reaper-mcp` and `dschuler36/reaper-mcp-server` (REAPER DAW),
  `ReaperMCP` (150 tools). All target a **DAW GUI on the same machine** and none
  is packaged for this fleet. Not adopted — pyCrossfade is a library, which is
  what a batch pipeline wants.
- **Suno has no official API.** `sunoapi.org`, `sunor.cc`, `worthable/suno-api`
  are unofficial third-party wrappers. Not adopted: the account is Premier and
  the browser session already works, so a wrapper would add a dependency and a
  third party holding the credential for no capability gain.

---

## 4. The design that follows

### Tempo: one grid, not three

**Everything on the 87 / 174 grid.**

| Tier | BPM | Why |
|---|---|---|
| **Lounge** | **87** | 87 = 174/2. Top of the chill-lounge range, and it *is* the halftime of DnB — so it blends into 174 with **zero pitch change** |
| **Breaks** | **174** | canonical DnB tempo, and the other half of the same pulse |
| **Trance** | **87** | the trance *elements* (arps, pads, builds) work at any tempo; at 87 this is psychill / downtempo trance, a real and established form |

This is the decisive design choice. It means **every lounge↔breaks transition is
free** — no pitch ride, no echo out, no stepping stone — and the 2-hour mix can
drift between the two poles as often as it likes.

Tracks that genuinely need the 140 trance tempo can exist, but they are a
**separate tier** and cost a stepping-stone transition to reach. Not in the first
mix.

### Fusion: 3 axes, one owner each

The constant across the family is **harmony = chill lounge** — jazz-voiced maj7 /
min7 / dom9. That is what makes a DnB track and a lounge track sound like the
same family.

| Tier | Rhythm owner | Harmony | Instrumentation 7:3 | Secondary in |
|---|---|---|---|---|
| Lounge | lounge (87, swung hats, laid-back) | lounge jazz | lounge 70 / DnB+trance 30 | bridge |
| Breaks | **DnB** (174, Amen-style break) | lounge jazz | DnB 70 / lounge+trance 30 | chorus |
| Trance | lounge/psychill (87, soft pulse) | lounge jazz | lounge 70 / trance 30 | build + chorus |

Note what this avoids: **no track ever has two rhythm owners.** The DnB tier
*owns* 174; the other tiers keep their breakbeats in bridge slots only. That is
failure-case-1 handled by construction rather than by hoping the prompt works.

### Track lengths

5–8 minutes, which is also what the DJ research implies: a transition wants the
outgoing track's **final 32–64 bars** to mix over, and a long ambient blend needs
long intros and outros. Short tracks leave nothing to blend with.

### The mix

- Target 2 hours of continuous audio.
- Transitions: **Long Ambient Blend** (32–64 bars) as the default between
  same-tempo tracks; **EQ Blend** where phrasing allows; **Drop Swap** on the
  breaks tier; **Echo Out** only where a gap needs one.
- **Phrase-aligned** throughout — pyCrossfade works in downbeats, so the mix
  plan is expressed in bars, not seconds.
- **One-bass rule** enforced by the 3-band EQ in the crossfade settings.
- Mastered by ComfyUI (`Music_LufsNormalizer` → −14 LUFS streaming / −16 LUFS
  sync), then measured, not claimed.

### Ownership

- **pyCrossfade** — transitions and the assembled mix.
- **ComfyUI** — track generation (ACE-Step) and final mastering.
- **Argo** — the pipeline stages, as CronJobs in `helm/charts/music-pipeline`.
- **The planner** — writes the per-track fusion spec (which axis owns what)
  from the genre registry, and validates it before anything renders.

## Open question for j_kro

Trance at **87** (psychill, blends free) versus a real **140** tier (canonical
trance, but every transition to it needs a stepping stone or an echo out). The
design above takes 87 so the mix is seamless. Say the word and the 140 tier goes
in as a separate section of the mix with a deliberate tempo change as its
feature.
