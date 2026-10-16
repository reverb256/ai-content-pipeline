# Brief — elemental-air: "Above The Weather"

Card: kanban `music` **t_92a09bdc** · stage: `brief` · assignee: `music-producer`
Oracle score: **7.5/10** · card created 2026-10-09 03:27:46 (epoch 1791534469)
Brief written: 2026-10-16 (CDT) · track slug: `above-the-weather`
Repo: `/home/j_kro/ai-content-pipeline` — local `main` @ `ade6e87`, **7 ahead / 15 behind `origin/main`**

Briefs in this lane are keyed by **GENRE**, not by card. A second oracle card for the
same genre exists — `t_3cb6e654` ("music-oracle: elemental-air (score 7.7)", status `ready`)
from the second scoring wave. Both cards resolve to **this** brief. Do not produce it twice.

Every number below comes from a command run during this stage. Nothing is transcribed
from another brief.

---

## 1. Resolved registry entry (live, not copied)

```
$ /usr/bin/python3 music/registry.py validate
registry OK: 14 genres, 10 lanes
genres: activist, anime-ending, anime-opening, chill-lounge, chiptune-8bit,
        commentary-beds, elemental-air, elemental-earth, elemental-fire,
        elemental-water, epic-orchestral-boss, jungle-dnb, sentimental-piano, trance
lanes: direct-fan, direct-license, game-assets, stock-ai-native, streaming,
       sync, sync-documentary, youtube-gaming, youtube-longform, youtube-mix
quota ledger: period 2026-10, standard 0/60 (warn_at 55, hard_stop_at 58)
```

| Field | Value |
|---|---|
| Genre | `elemental-air` |
| Family | `gamer` |
| Prompt template | `music/prompts/elemental-air.md` (resolves) |
| Visual style | `music/visuals/element-air.md` (resolves) |
| Lanes | `game-assets`, `youtube-gaming`, `streaming` |
| Cadence | 2/wk |
| Video shape | `loop-10min` |
| Tempo | **92 BPM** — the caption's own stated tempo |
| Lyric blueprint | **none** — `music/lyrics/blueprints/` holds only `activist.yaml`, `chill-lounge.yaml`, `trance.yaml` |
| Registry note | *(no note block on this genre; `elemental-fire` carries the family note "Boss/battle theme. Target indie devs + gaming music channels.")* |

Registry defaults that bind this track: export `studio`, stems `true`,
lyrics `human-original`, release_private `true`, gate_profile `reviewer-deepseek`.

**Where 92 BPM comes from.** There is no blueprint for this genre, so the tempo is
resolved from the template caption — which is exactly the resolution order the lane
adopted in commit `dda0d32` ("resolve the tempo from the genre's own research, not a
flat 100"): blueprint first, caption second, nothing third. The caption says
`open sky heights theme, 92 BPM`. A planner run against a blueprint-less genre
previously fell back to a flat 100 BPM; that fallback is gone upstream.

---

## 2. Intent

Air is the lightest of the four elements: **breath, lift, suspension**. The product is
not a song that develops — it is a place that stays open. The template states the intent
through instrumentation rather than a story: two flutes trade short phrases (breath made
audible), chimes and glass mallets sparkle above them (unquantized randomness = wind),
and the harmony never resolves.

Three things must hold, or a generation is **out of genre**:

1. **Csus2 harmony that does not resolve.** No third, no leading-tone pull. Phrases end
   open (sus2, add9). `prompts/elemental-air.md`: "Everything rises or suspends. Air
   never lands: avoid resolved cadences."
2. **No weight.** No percussion kit, no bass below the pads, no drum groove. The template's
   own words: "no percussion kit, no bass weight", and "Gravity = wrong element."
3. **92 BPM with rubato feel, and rise-only motion.** Upward-moving figures; the outro
   disperses into the intro's wind bed instead of landing on a tonic.

The template's own rejection test, verbatim: *"A generation with heavy low end, drum
groove, or resolved cadences is OUT of genre — reject it."*

Boundary check against the sibling style: `elemental-fire` (150 BPM, Phrygian, taiko)
is a battle theme. `elemental-air` shares the family and the lanes and **none** of the
idiom. Do not let a "gamer family" template pull this into percussion.

---

## 3. Target lanes and what each one demands

From `music/lanes.yaml` and `music/autonomy.yaml`. These are the gates that will run,
read from the gate sources, not from advisory text.

| Lane | Surface | Gate | Required artifacts | Rung |
|---|---|---|---|---|
| `game-assets` | itch.io, unity-asset-store, gamedev-market | `gate_sync_ready --lane game-assets` (`music/gates/gate_sync_ready.py`) | `stems`, `loop_point`, `seamless_loop`, `metadata` | advisory |
| `youtube-gaming` | youtube (shape `loop-10min`) | `gate_youtube_authentic` | platform-native loop video + disclosure | advisory |
| `streaming` | distributor (DistroKid; alt TuneCore) | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` | advisory |

All three rungs are `advisory` (`clean_publishes: 0`, `platform_strikes: 0`,
`revenue_usd: 0`). No lane may publish itself; promotion needs 10 clean advisory
publishes plus j_kro's approval.

### What `gate_sync_ready --lane game-assets` actually checks

Read from the source, and it **executes** the artifacts (ffprobe, file headers):

- `full_mix.wav` — ffprobe must report an audio stream **and** a duration; zero bytes fails.
- `stems/` — **≥ 4** audio files (`MIN_STEMS = 4`), each non-zero, each within
  **±0.5 s** of the master's duration.
- `instrumental.wav` — a real audio file **and not byte-identical to the master**. A copied
  master is not an instrumental version.
- `manifest.json` → `metadata` must carry `title`, `artist`, `bpm`, `key`, `mood`, `genre`.
- `clearance_doc.pdf` (must start with `%PDF-`) or `clearance_doc.txt`.
- `ai_disclosure.txt`, non-empty.
- `loop_points.json` — **game-assets only** (the `--lane` switch adds this one requirement;
  the checks above are unconditional in the code).

`gate_loop_points.py` then measures the seam itself: it renders `[loop_end − W, loop_end]`
and `[loop_start, loop_start + W]`, concatenates them, and compares the junction's discrete
second-difference curvature against the body's. PASS at **ratio ≤ 3.0×** (verified separation
on synthetic loops: clean 1.6×, phase-slip 6.0×). It also requires `0 ≤ loop_start < loop_end
≤ duration`, a loop span **≥ 2 s**, and a non-silent loop region. Input schema:
`{"loop_start_s": 0.0, "loop_end_s": 60.0, "seamless": true}`.

**Stems are mandatory** — the cluster default (`genres.yaml → defaults.stems: true`) and the
game-assets lane both require them.

### Decision: the shape does not collide here

`anime-opening` had to flag a collision (genre shape `single-4min` vs the `youtube-gaming`
lane's `loop-10min`). **elemental-air has no collision**: the genre's registry shape and the
lane's shape are both `loop-10min`. One render satisfies both.

### A fourth surface exists upstream but not in this checkout

Upstream `origin/main` adds an asset-pack generator (`music/assets/pack.py`) and its
executable gate (`scripts/gates/gate_asset_pack.py`), with a sample pack proving the
path (`packages/welcome-asset-pack/`, built from a Virtual Reflections master at 184.57 BPM,
C major, 44.1 kHz / 16-bit). Its required counts are **loops ≥ 5, stems ≥ 12, one_shots ≥ 5**,
and every loop's measured seam must be **≤ −60 dBFS`. Neither file exists in this checkout
(both are in the 15 commits `origin/main` is ahead), so the game-assets package shape for
this track is specified here but **cannot be built from this tree today**.

---

## 4. Cadence and throughput

- Cadence 2 tracks/week (registry).
- Video shape `loop-10min` → **600.000 s** — measured with ffprobe on the shape template
  `music/visuals/loop_10min.mp4` (1280×720, video + audio, duration 600.000000 s).
- The genre's own visual artifact `music/visuals/element_air.mp4` is a **5.0 s** shape
  placeholder, not a render.

At 92 BPM one bar = 4 × 60 / 92 = **2.608696 s**. The 600 s video is therefore exactly
**230.00 bars** — the loop grid and the video length are in register at this tempo.

---

## 5. Audio identity (locked for this genre)

Style caption, verbatim from `music/prompts/elemental-air.md` — **494/1000 chars**, measured:

```text
open sky heights theme, 92 BPM, breathy alto and pan flutes trading short phrases, wind chimes and glass mallets sparkling above, Csus2 suspended-second harmony that never resolves downward, airy string suspension pads, high shimmering bell tones, upward-moving figures that keep opening instead of landing, gentle white-noise wind texture, no percussion kit, no bass weight, transparent spacious mix with everything high and light, unforced floating motion, hopeful clarity, seamless game loop
```

| Setting | Value |
|---|---|
| Weirdness | **45%** — "air tolerates shimmer and strangeness in the textures; keep the flute phrases singable" |
| Style Influence | **70%** — "flute + chimes + sus2 + weightless" must hold |
| Exclude Styles | ` bass drops, heavy drums, EDM, dark minor, tense thriller, epic brass` — the leading space is in the template; the "epic brass" exclusion is load-bearing (brass turns sky into war) |

Structure, from the template's tag sheet (section tags and parenthetical direction only —
never singable words):

| Tag | Bars | Musical job |
|---|---|---|
| `[Intro]` | 16 | wind texture, one chime swell, breathy flute states the opening phrase alone |
| `[Instrumental]` | 16 | flute melody floats over sus2 pads, glass mallets answer in the gaps |
| `[Instrumental]` | 32 | pan flute takes the phrase higher, chimes sparkle, the figure keeps rising |
| `[Instrumental Break]` | 16 | the clear height: pads and chimes only, near-silence, one bell held long |
| `[Instrumental]` | 32 | both flutes in dialogue over the full airy bed |
| `[Outro]` | 16 | flute phrase disperses upward into chimes — **LOOP POINT** into the intro wind |
| **total** | **128** | 128 × 2.608696 s = **333.913 s** |

Every section is a whole 16-bar phrase (8 × 16 = 128), so the loop point and every section
boundary land on a phrase boundary.

### Duration decision: 334 s (128 bars)

The lane's guard rail is `MIN_DURATION_S = 30`, `MAX_DURATION_S = 420` (`music/planner/planner.py`,
read in this checkout). The wire format takes an integer (`SunoGenerateRequest.duration: Optional[int]`),
so the plan value is **334**.

The binding check is the family rubric, not taste. `music/rubrics/gamer.json` →
criterion `loop_safety` (weight 3, type `measured`) states its evidence as:

> "bar math: `duration_s * bpm / 240` should land near a whole bar count"

`334 × 92 / 240 = 128.03` bars — a whole bar count. The same criterion's other two
requirements also bind this track: last-1s RMS within ~6 dB of first-1s RMS, and **no
fade-to-silence on a loop claim** (the rubric's reject list includes "fade-out or truncated
ending on a game-loop claim"). The outro must disperse into bar 1, not fade out.

**Tradeoff, stated so the visual stage does not have to re-derive it.** 334 s is not an exact
divisor of the 600 s video (600 s = 1.80 track plays). The alternative that *is* an exact
divisor is **115 bars = 300.000 s** → exactly 2 plays, one audio seam at 05:00. It was **not**
chosen because 115 = 7 × 16 + 3, which breaks the 16-bar phrase grid that keeps the template's
six sections on phrase boundaries. Decision: **musical phrase structure wins**; the
`loop-10min` render must place its audio seam at the track's own verified loop point
(`gate_loop_points`), not at a simple repeat boundary. Recorded as open item O3.

---

## 6. Visual identity (locked for this genre)

`music/visuals/element-air.md`:

- **Palette**: cloud white `#f4f7fa`, high-altitude blue `#9fc4e8`, pale gold sun-veil
  `#e8d9b0`. **No ground horizon** — pure altitude.
- **Scene**: above-cloud drift / cirrus fields / mountain-top mist; height without vertigo edges.
- **Motion**: cloud parallax, 3 layers, speeds 2 : 1.5 : 0.5 px/s — gentle forward glide.
  Chime sparkles: single-frame iridescent glints above the cloud line, sparse, 1–3 per 8 s.
- **Texture**: soft light bloom, **film grain 2%** (the lightest of all the visuals), airy haze.
- **Audio-visual sync**: flute phrases = a light breeze crossing (the cloud edge sharpens
  slightly on the breath attack); chime tones = the glints; the near-silence breakdown =
  full whiteout mist for one phrase, clearing as the flutes return.

**`gate_youtube_authentic` binds the variation, not just the render.** Read from the source:

1. the visual must be a real decodable video (ffprobe: video stream + duration + resolution);
2. it must carry a real edit — **≥ 10 distinct frame signatures** sampled at 2.0 s cadence
   (a still image dumped with audio has 1 and fails);
3. its frame-signature set must not be a near-duplicate of a prior upload — **Jaccard ≤ 0.85**
   against `upload_index.json`;
4. `disclosure.txt` or `ai_disclosure.txt` must state the AI role.

The template answers (2) by construction (parallax + glints) and answers (3) with its own rule:
**rotate dawn / noon / high-wind cloudscape scenes per upload.**

---

## 7. The live generation path (measured, not assumed)

This genre is **instrumental**, and that decides which engine path is even legal.

### It is instrumental — measured, not inferred

Census over `music/prompts/*.md`, reading only the `## Lyrics guidance` section:

| Genre | Lyrics box stays empty |
|---|---|
| chill-lounge, chiptune-8bit, commentary-beds, **elemental-air**, elemental-earth, elemental-fire, elemental-water, sentimental-piano | yes (8 of 14) |
| activist, anime-ending, anime-opening, epic-orchestral-boss, jungle-dnb, trance | no |

`elemental-air` is one of the **8 instrumental genres**. The template's words:
"Leave the **lyrics box empty** — that is Suno's instrumental path." No lyric sheet exists
for it and none is wanted:

```
$ ls music/lyrics/
activist  blueprints  chill-lounge  lyrics.py  trance      # no elemental-* directory
```

Two documentation defects surfaced in this census (both upstream, not this checkout's to fix):

- Deployed `sunolocal/translate.py` and `suno-gen.py` both say **"8 of the 12 genre
  templates"**, and the `suno-gen.py` docstring then lists nine names including
  **epic-orchestral-boss**, whose template contains no instrumental marker. The count is
  **8 of 14**; the correct list is the table above.
- Thus: 8 of 14 (not 8 of 12, not 9).

### Engine A (live now): sunolocal → ACE-Step

```
$ kubectl get pods -n mining | grep -E "sunolocal|comfy"
sunolocal-source-65fcc845d-fd5r6                1/1     Running     1 (40h ago)   2d7h
comfyui-zephyr-599b69bb7c-fhjs9                 1/1     Running     0             2d

$ kubectl get svc -n mining sunolocal        # ClusterIP 10.43.164.190, port 8123
$ kubectl get deploy -n mining sunolocal-source -o jsonpath='{..image}'
localhost/sunolocal:v0.1.2

$ curl -s http://10.43.164.190:8123/health
{"status":"ok"}

$ curl -s http://10.43.164.190:8123/api/v1/models
{"engines":{"ace":{"kind":"ACE-Step 1.5","via":"acestep_plan.py -> comfyui-zephyr window"},
            "yue2":{"kind":"YuE2-3B","via":"yue2-zephyr http"}},"default":"ace"}
```

Live routes on the running pod: `GET /health`, `GET /api/v1/models`,
`POST /api/v1/generate`, `GET /api/v1/task/{task_id}`, `GET /api/v1/audio?path=…`.
`POST /api/v1/lyrics`, `/stems`, `/extend` and `/cover` are **`_deferred` stubs** — they
answer but do not work. **Stems cannot come from this service.**

Request shape (Suno camelCase; read from the deployed `sunolocal/spec.py`):
`prompt`, `style`, `lyrics`, `title`, `instrumental`, `model`, `customMode`,
`negativeTags`, `vocalGender`, `duration` (int seconds), `styleWeight`,
`weirdnessConstraint`, `audioWeight`, `variety`, `callbackUrl`, `seed`, `engine` (`ace|yue2|fixture`).

### Engine B (advertised, DOWN — measured)

```
$ kubectl get deploy -n mining yue2-zephyr
yue2-zephyr    0/0    0    0    8d
$ kubectl get endpoints -n mining yue2-zephyr
yue2-zephyr    <none>    8d
$ curl -s -o /dev/null -w "%{http_code}" http://10.43.95.191:8080/health   → 000
```

**YuE2 is scaled to zero replicas.** `/api/v1/models` still advertises it. This track must
therefore be requested with `engine: "ace"` (also the service default).

### Instrumental mode IS deployed — the previous blocker is gone

The deployed `translate.py` (read inside the running pod, not from git) carries:

```python
if req.instrumental and not lyrics:
    caption = caption + ", instrumental, no vocals"
    lyrics = "[Instrumental]\n"
```

The comment above it names the elementals as the reason: an instrumental rendered from a
caption that never mentions vocals "still comes back with a vocal-shaped hole", and the
renderer refuses a plan with an empty lyrics body unless `--allow-empty` is set (the ACE
adapter sets it). The matching CDP-side fix is `suno-gen.py`'s `is_instrumental_template()`,
which reads the template's Lyrics guidance section rather than guessing.

Cards `t_82ed3b8a` (instrumental mode in the generation path) and `t_295fc49`/`ba28f55`
(upstream) are the fix. Verified present in the running image and on `origin/main`.

### Two defects that are STILL LIVE in the deployed translator

Read from `/opt/sunolocal/music/sunolocal/translate.py` **inside the running pod**:

| # | Defect | Deployed code |
|---|---|---|
| D1 | **BPM is not expressible.** The 92 BPM genre anchor cannot be honoured. | `bpm = 120`; then `bpm = int(60 + req.style_weight * 120)` if `styleWeight` is set. Reaching 92 needs `styleWeight ≈ 0.2667`. |
| D2 | **The key field receives the whole style caption.** | `key = req.style or "C major"` — the ACE `keyscale` is handed a 494-character paragraph. |

D1 means a default render of this genre comes back at **120 BPM — 1.30× the genre anchor**,
which is out of genre on tempo alone. D2 is a payload-shape bug for every genre.
Both are recorded, not fixed here (this card writes a brief).

### A third live defect: the checkout cannot run the generate stage as written

`music/stages.yaml` tells the generate stage to generate "via Suno CDP
(`music/suno-gen.py`)". In this checkout:

```
$ ls music/suno-gen.py
ls: cannot access 'music/suno-gen.py': No such file or directory
$ git rev-list --left-right --count main...origin/main
7       15
```

The file exists on `origin/main` (added by `295fc49`, completed by `ba28f55`), and the local
lineage is 15 commits behind it — `music/suno-gen.py`, `music/sunolocal/`, the instrumental
handling and the asset-pack generator are all upstream-only. The engine actually in service
is the ACE-Step path above; the Suno CDP path additionally needs a logged-in CDP browser.
Fix is branch reconciliation, not a rewrite. (Same finding as the trance brief, re-measured:
the gap was 2/15 then, 7/15 now.)

### A one-line doc/code mismatch in the streaming gate

`music/gates/gate_release_ready.py` docstring says the ISRC "must match the ISRC syntax
CC-XXX-YY-NNNNN and **pass the ISRC check digit (ISO 3901)**". The code in the same file
enforces `^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$` — **12 characters, no check digit** (IFPI
Bulletin 2015/01: an ISRC has no check digit). The regex is right; the docstring is wrong
and will send a human looking for a checksum that does not exist.

---

## 8. What "instrumental" means for each remaining stage

| Stage | Consequence |
|---|---|
| `lyrics` | **Not applicable.** The stage prompt already anticipates this: "an instrumental genre … skips this stage — advance it with a comment saying the genre is instrumental." No sheet, no `gate_lyrics_original` run, no authorship claim to register with SOCAN for this track. |
| `generate` | Requires a **track dir with `title.txt`** and, because `--instrumental` is passed, a marker: `"instrumental": true` in the track dir's `manifest.json`, or an empty file named `instrumental`. Code-enforced, with a FATAL message that says exactly this. The lyrics box is sent **empty**; the caption gets `, instrumental, no vocals` appended by the translator. |
| `curate` | Critical for this genre, because D1 (120 BPM default) and out-of-genre drift into percussion are both audible. Reject on: any drum kit, any bass weight, a resolved cadence, a hard/faded ending. |
| `stems` | Export through **Suno Studio** (unlimited) — never the standard download button (60/month cap). The local service's `/api/v1/stems` is a deferred stub. Upstream, `music/assets/pack.py` derives 12 time-aligned stems by HPSS (scipy) as the asset-pack path, but that file is not in this checkout. |
| `master` | −14 LUFS ±1 for streaming. **Careful:** `gate_loudness` measures `ffmpeg volumedetect` mean_volume (plain RMS), not LUFS — a known ruler defect, card `t_9546841b`. For a light, waitless mix the RMS-vs-gated-LUFS gap will be at the wide end, so a gate FAIL is not by itself evidence of a bad master. Measure both. |
| `gate` | `gate_quality` requires a `review.json` whose `reviewer_model` differs from the producer model and which is sha256-bound to this master. The panel rubric for this family is `music/rubrics/gamer.json` (pass threshold 7.0). |
| `package` | `loop_points.json` + `clearance_doc.pdf` + `ai_disclosure.txt` are required for game-assets; `gate_release_ready` adds an ISRC, artwork (PIL-openable), and manifest `{title, artist, isrc, genre, ai_disclosure}` for streaming. Artwork is j_kro's creative gate — do not fabricate a cover. |
| `visual` | `loop-10min`, 600 s, dawn/noon/high-wind rotation per upload, `gate_youtube_authentic` (≥10 distinct frames, Jaccard ≤ 0.85, disclosure). |
| `human-approval` | j_kro. `gate_human_approval` has no `--force`/`--auto-approve` flag by design. Uploads stay private/draft. |

---

## 9. Existing assets and quota (measured)

**Assets: none.** No `music/lyrics/elemental-air/`, no masters, no stems, no render for this
genre anywhere in the tree. The first render is genuine work, not a re-run.

Quota is untouched:

```
$ python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

Ledger: `credits_used 0 / 10000`. Run `gate_quota` before **every** generate and export.

---

## 10. Rubric note — one criterion does not fit this genre

`music/rubrics/gamer.json` supplies the judging panel for the family. Its own `notes` field
resolves the sub-idiom question honestly: *"Two sub-idioms live in this family: chip
(hardware-constraint timbre) and orchestral battle (tempo/ostinato/phase). elemental-* tracks
choose per their prompt; chiptune-8bit MUST pass chip_timbre_authenticity; battle tracks MUST
pass battle_energy. Loop safety is common to all game-asset delivery."*

But the criterion **`battle_energy`** (weight 3) carries the id-level scope
`"(elemental-*, epic-orchestral-boss)"` and an anchor built for battle themes (130–200 BPM,
timpani, ostinato, chromaticism), with a guide that scores "1 = slow ambient track with a
battle label". `elemental-air` is a 92 BPM suspension theme that the registry explicitly
forbids bass weight and a percussion kit. Scored literally against that criterion it takes a
1, which is 3/8 of the weighted total — a genre the registry says to produce would be failed
by the ruler. Recorded as finding F2 for the rubric owner; the brief does not override the
rubric.

Criterion `chip_timbre_authenticity` (weight 3) is explicitly `chiptune-8bit only` and does
not apply. The criteria that do bind this track: **`loop_safety`** (weight 3, bar math +
seam levels), **`asset_packaging`** (weight 1, stated BPM/key + loop-point marker),
**`loudness_target`** (weight 1, −14 LUFS ±1 for streaming). Reject signals that apply here:
"fade-out or truncated ending on a game-loop claim", "clipped master
(`max_volume_db >= -0.1`)", "no stated BPM/key for a game-asset product".

---

## 11. Open items

- **O1 — Engine defects D1/D2.** The deployed translator cannot carry 92 BPM and puts the
  caption into `key`. Any render taken at defaults is out of genre on tempo. Workaround until
  fixed: send `styleWeight ≈ 0.2667` for 92 BPM and accept that the ACE keyscale receives the
  caption (or bypass `translate.py` and post the ACE plan directly).
  **Already filed: `t_25a6499c`** (nexus-core, ready) — bpm hardcoded 120 / key = style
  caption / queue schema has no instrumental field. This brief adds no new defect there.
- **O2 — Branch divergence.** Local `main` (7 ahead) lacks 15 upstream commits, including the
  entire `music/suno-gen.py` the generate stage names. Reconcile before the generate stage runs
  against this checkout. **Already filed: `t_8a715681`** (nexus-core, ready) — reconcile the
  diverged live checkout.
- **O3 — Video/loop alignment.** 334 s is not an exact divisor of the 600 s `loop-10min` shape
  (1.80 plays). The visual stage must seam at the track's verified loop point. If the videobot
  cannot seam audio, revisit the duration (**115 bars = 300.000 s**, exactly 2 plays).
- **O4 — Clearance doc and license tiers.** `game-assets` and `streaming` need a real
  `clearance_doc.pdf`; none exists in the tree for any genre. `direct-license` (not a lane here)
  needs `license_tiers`. Upstream ships `music/licences/perpetual_game_asset_v1.txt`; this
  checkout has no `music/licences/`.
- **O5 — Asset pack machinery is upstream-only.** `music/assets/pack.py` and
  `scripts/gates/gate_asset_pack.py` do not exist in this checkout, so the game-assets pack
  (loops ≥5, stems ≥12, one_shots ≥5, seams ≤ −60 dBFS) cannot be built here yet. This is the
  lane's main product for this genre; it is blocked on O2. **Already filed: `t_5ed495eb`**
  (distributor, ready) — "asset-pack output does not satisfy the game-assets gate".
- **O6 — Brief cards never advance.** `music/stages.yaml` tells the brief stage to advance to
  `genre-select`, but all four previous brief cards (`t_38e84953`, `t_2541fd9c`, `t_9f7d6889`,
  `t_6272da09`) ended `done`, so no card has ever reached `genre-select`. Additionally, the
  documented advance step cannot work from a dispatcher-spawned worker:
  `bash scripts/automation/advance-stage.sh t_92a09bdc genre-select --board music` →
  `kanban: delegate_task child contexts cannot mutate Kanban tasks via the CLI`, **script exit
  code 1**, and the script aborts before its own success echo, so the no-op is quiet. The stage
  prompt and the worker's permissions disagree; decide which side changes. **Filed: `t_5a93164a`**
  (nexus-core) during this stage.
- **O7 — Duplicate oracle card.** `t_3cb6e654` (elemental-air, 7.7) duplicates this card. The
  dedupe guard landed locally in `ade6e87`; the pre-existing duplicates still need closing.
- **F2 — Rubric/genre mismatch (raised here, not fixed here).** `music/rubrics/gamer.json`
  criterion `battle_energy` (weight 3 of 8) is id-scoped `"(elemental-*, epic-orchestral-boss)"`
  with a battle anchor and a guide whose floor case is "1 = slow ambient track with a battle
  label", while the rubric's own `notes` say elemental-* choose their sub-idiom per prompt.
  `elemental-air` is a 92 BPM suspension theme with no percussion by genre rule. **Filed:
  `t_426a82a3`** (editor — the profile that owns the music rubrics card `t_16d011e6`).

---

## 12. Handoffs
- **`t_25a6499c`** (nexus-core, ready) — bpm hardcoded / key = caption / queue has no
  instrumental field. This brief adds the elemental-air numbers (92 BPM, `styleWeight` 0.2667)
  and nothing new to file.
- **`t_8a715681`** (nexus-core, ready) — reconcile the diverged checkout. This brief adds the
  measured 7/15 counts and the missing paths; nothing new to file.
- **`t_5ed495eb`** (distributor, ready) — the asset-pack ↔ game-assets gate mismatch. Blocks O5.
- **`t_b8afb055`** (NEW, nexus-core; parents = this card + `t_25a6499c`) — queue this track into
  the live generation path. Carries the exact measured render parameters (instrumental true,
  engine `ace`, `styleWeight` 0.2667 → 92 BPM, duration 334, `/api/v1/generate` →
  `/api/v1/task/{id}` → `/api/v1/audio`), the reason `yue2` must not be selected (0/0), and the
  fact that `/api/v1/stems` is a deferred stub. Gated so it cannot run before the instrumental
  fix lands.
- **`t_5a93164a`** (NEW, nexus-core; parent = this card) — no stage can advance its own card;
  `advance-stage.sh` is refused for dispatcher-spawned workers. Decision needed (O6).
- **`t_426a82a3`** (NEW, editor; parent = this card) — the `gamer` rubric's `battle_energy`
  scope. Decision needed (F2).

---

## 13. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` — `music/registry.py validate` → rc 0.
- Gates read and quoted from source: `music/gates/gate_sync_ready.py`, `gate_loop_points.py`,
  `gate_youtube_authentic.py`, `gate_release_ready.py`, `gate_quality.py`,
  `gate_stems_present.py`, `gate_human_approval.py`, `gate_quota.py`.
- Templates: `music/prompts/elemental-air.md` (494-char caption measured),
  `music/visuals/element-air.md`.
- Rubric: `music/rubrics/gamer.json` (`loop_safety`, `battle_energy`, `asset_packaging`,
  `loudness_target`, `reject_signals`, `notes`).
- Stage contract: `music/stages.yaml` (`brief` → bot `producer`).
- Live engine: cluster `mining` — `kubectl` reads of `sunolocal-source-65fcc845d-fd5r6`
  (image `localhost/sunolocal:v0.1.2`), `/health`, `/api/v1/models`, and the deployed
  `translate.py` / `spec.py` / `studio.py` read **inside the pod**; `yue2-zephyr` 0/0.
- Upstream reads (`git show origin/main:…`): `music/suno-gen.py`, `music/sunolocal/translate.py`,
  `music/sunolocal/checks/g9_instrumental.sh`, `music/assets/pack.py`,
  `scripts/gates/gate_asset_pack.py`, `packages/welcome-asset-pack/README.md`,
  `music/docs/fusion-system-design.md`.
- Board: `kanban` `music` — card + duplicate read from a read-only snapshot of
  `~/.hermes/kanban/boards/music/kanban.db`.
- **Dangling references (unchanged):** `brain/playbooks/music-lane-architecture.md` and
  `brain/research/music-monetization-2026.md` are cited as authoritative by `stages.yaml`,
  `genres.yaml`, `lanes.yaml`, `autonomy.yaml`, `gates/README.md` and every gate script, and
  **neither exists on this machine** (`find /home/j_kro -name 'music-lane-architecture.md'` →
  no hits; `brain/playbooks/` holds angles/arbitrage/audio-dramas/hooks/model-routing/
  performance/platforms/viral-moments). Every §-number quoted in this brief is quoted from the
  gate or template that cites it, not from the missing document. Filed as `t_b0a4db92`.

## 14. Next stage

Stage `brief` is complete. Next: `genre-select` — with O6 noted, because this card's advance
step cannot be executed from inside this worker and no previous brief card has advanced.
The production path for this track is `t_b8afb055` (queue into the generation path, gated on
the instrumental fix `t_25a6499c`).
