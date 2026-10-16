# Brief — elemental-earth

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`; on this board the
> cards are assigned `music-producer` and claimed by the generic kanban dispatcher).
> **Card:** t_55e37b88 (`music-oracle: elemental-earth (score 7.5)`)
> **Duplicate card:** t_c92f566d (`music-oracle: elemental-earth (score 7.7)`) — same genre,
> same lanes, from the second oracle run. Both resolve to THIS brief; the brief is keyed by
> genre, not by card.
> **Written:** 2026-10-16T13:14-05:00 (CDT)
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `9ebf6af` (main; shared working tree — six
> brief-stage workers are running against it and HEAD moved twice while this brief was written).
> **Oracle:** 7.5/10 — quota headroom 10.0, lane coverage 6.0, revenue 8.0, cadence fit 6.7,
> policy risk 9.0, **trend signal 3.0**. Threshold 5.0 → produce.

## 1. Genre resolution (live, not transcribed)

Resolved through the registry loader, not copied by hand:

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

**Interpreter trap, measured.** Plain `python3 music/registry.py validate` fails in a worker
shell with `ModuleNotFoundError: No module named 'yaml'` — `python3` here resolves to
`~/.hermes/tools/python-3.14.7+…/bin/python3`, which has no PyYAML. `/usr/bin/python3` (3.14.7)
has it and validates cleanly. Every command in this brief uses `/usr/bin/python3`. The systemd
music units use `/usr/bin/python3`, so they are unaffected; a stage prompt that says bare
`python3 music/…` inherits the trap.

| Field | Value |
|---|---|
| Genre | `elemental-earth` |
| Family | `gamer` |
| Prompt template | `music/prompts/elemental-earth.md` (3643 B, resolves) |
| Visual style | `music/visuals/element-earth.md` (1088 B, resolves) |
| Lanes | `game-assets`, `youtube-gaming`, `streaming` |
| Cadence | 2/wk |
| Video shape | `loop-10min` |
| Genre note (registry) | *(none — the elemental blocks carry no `notes` key; only `elemental-fire` does)* |

Family position, measured from each template's own style field
(`grep -o "[0-9]\{2,3\} BPM" music/prompts/<genre>.md`):

| Genre | Anchor BPM | Video shape |
|---|---|---|
| elemental-water | 82 | loop-10min |
| **elemental-earth** | **88** | **loop-10min** |
| elemental-air | 92 | loop-10min |
| elemental-fire | 150 | loop-10min |
| epic-orchestral-boss | 150 | single-4min |
| chiptune-8bit | 150 | loop-10min |

**This genre is instrumental.** `music/prompts/elemental-earth.md:15` reads
`Instrumental. Leave the **lyrics box empty** — that is Suno's instrumental path.`
Measured count: `grep -li "leave the .*lyrics box empty" music/prompts/*.md` → **8 of 14**
templates (chill-lounge, chiptune-8bit, commentary-beds, elemental-air, elemental-earth,
elemental-fire, elemental-water, sentimental-piano). All four `loop-10min` genres are in that
set, so the whole loop-10min shape is instrumental-first. Consequences are §10.

Registry defaults that bind this track: export `studio`, stems `true`,
lyrics `human-original`, release_private `true`, gate_profile `reviewer-deepseek`.
The `lyrics: human-original` default does **not** bind here — see §10.

## 2. Intent — the product is a LOOP PACK, not a song

Earth is the grounded element: the music sits still and something old listens. The buyable
unit is a **seamless game loop plus its pack** (loops, stems, one-shots, SFX), because that is
what the `game-assets` lane requires and what an indie dev licences.

The template's craft notes reduce to three rules that decide whether a render is in genre:

1. **Open-fifth drone, no third.** Major/minor stays undecided → "rooted, yet open-ended".
   That unresolved horizon is the element's harmonic signature. A defined major/minor tonic
   is a different element.
2. **Organic materials only** — hide drums (djembe, buffalo frame), wooden marimba, bone/wood
   flute, clap sticks, shakers, didgeridoo. A drum machine is out of genre by name: "the
   heartbeat must sound like hide and wood, not a 909".
3. **Loop discipline.** The outro subtracts to drone and rumble and loops into bar 1. A fade
   ending or a reverb tail across the seam breaks the product.

The template names the tempo band explicitly: earth is 80–90 BPM, below fire (150) and above
water (82 with no pulse). Reject conditions, verbatim from the template: electronic drums,
bright tonality, or a rushing tempo.

Ritual dynamics are not a drop. The breakdown is a hush: drums drop to the pulse alone, one
wordless throat-chant texture at the peak, all torches dim. The whole arc is one intensity
level held for ten minutes with the drone as ground.

## 3. Target lanes and what each one demands

From `music/lanes.yaml` + `music/autonomy.yaml`. These are the gates that will actually run.

| Lane | Surface | Gate | Required artifacts | Autonomy rung |
|---|---|---|---|---|
| `game-assets` | itch.io, unity-asset-store, gamedev-market | `gate_sync_ready` (`--lane game-assets`) | stems, loop_point, seamless_loop, metadata | advisory |
| `youtube-gaming` | youtube | `gate_youtube_authentic` | platform-native loop-10min video + disclosure | advisory |
| `streaming` | distributor (DistroKid; alt TuneCore) | `gate_release_ready` | ai_disclosure, isrc, metadata, master | advisory |

All three rungs are `advisory` with `clean_publishes: 0, platform_strikes: 0, revenue_usd: 0`.
No lane may publish itself. Promotion to `supervised` needs 10 clean advisory publishes and
j_kro's approval.

**`game-assets` is the lane that makes this genre worth producing** (asset packs $2,500–7,500
for 5–10 tracks, per `brain/runbooks/music-game-assets.md`), and it is the lane that is
currently **not passable**. Measured against the only asset pack that exists in the repo —
`packages/welcome-asset-pack`, extracted from `origin/main` (`83cd0ce`):

```
$ /usr/bin/python3 music/gates/gate_sync_ready.py \
      --package-dir <pack> --lane game-assets
FAIL gate_sync_ready
  - full_mix.wav is not a real audio file (ffprobe could not read a duration)
  - instrumental.wav is not a real audio file (sync needs an instrumental version)
  - manifest.json has no metadata object
  - manifest metadata missing 'title'
  - manifest metadata missing 'artist'
  - manifest metadata missing 'bpm'
  - manifest metadata missing 'key'
  - manifest metadata missing 'mood'
  - manifest metadata missing 'genre'
  - no clearance_doc.pdf (or .txt) — sync requires a clearance document
  - no ai_disclosure.txt — the AI role must be declared for sync platforms
  - game-assets lane requires loop_points.json (run gate_loop_points.py for the seam check)
rc=1
```

Twelve problems. The gate does not list a stems problem — the pack carries 12 stems, which is
the one requirement it meets. The generator (`music/assets/pack.py`, `origin/main:83cd0ce`)
emits a **pack** layout (`loops/`, `stems/`, `one_shots/`, `sfx/`, `manifest.json` with
`pack_name`/`counts`); the gate expects a **per-track package** layout (`full_mix.wav`,
`instrumental.wav`, `stems/`, a `metadata` object, a clearance PDF, an AI disclosure). The two
shapes have not been reconciled. Filed as a card (§12).

The seam half is also measured. `gate_loop_points` renders the wrap and compares junction
curvature against body curvature (PASS at ≤ 3.0×), and requires a loop span ≥ 2 s:

```
$ … gate_loop_points.py --master <pack>/loops/loop_01_bpm184_key-Cmajor.wav \
      --loop-points loop_points.json          # {"loop_start_s":0.0,"loop_end_s":1.3}
FAIL gate_loop_points
  - loop span is 1.30s — too short to be musical (minimum 2s)
rc=1

$ … gate_loop_points.py --master <pack>/stems/01_bass.wav \
      --loop-points loop_points.json          # {"loop_start_s":0.0,"loop_end_s":51.605}
PASS gate_loop_points
  master   : …/stems/01_bass.wav (51.605s)
  loop     : [0.000s -> 51.605s] (span 51.605s)
  seam     : curvature ratio 0.24x (max 3.0x) — seamless
  region   : RMS 0.02570 (not silent)
rc=0
```

So the gate's method works on real rendered audio (0.24× on a real stem), and the generated
loops fail it on length, not on seam quality.

Decisions locked here so later stages do not re-litigate them:

- **The pack must be emitted in the shape the gate reads**, or the gate needs an explicit
  pack mode. Both options are open; the mismatch is a blocker either way.
- **`instrumental.wav` must be a real, distinct render** — the gate fails an instrumental that
  is byte-identical to `full_mix.wav`. An earth master is already instrumental, so ship the
  drone+percussion-only alternate mix as the instrumental version and say which variation it is.
- **Stems: ≥ 4 files, each within ±0.5 s of the master duration** (ffprobe-measured, not file
  size). Export through Suno Studio, never the standard download button.
- **`loop_points.json` is mandatory** for this lane, and `gate_loop_points` must pass on it.
- **`clearance_doc.pdf` must be a real PDF** (`%PDF-` header parsed) and `license_tiers.*`
  must exist for the licence the pack ships (perpetual game-asset v1 is the runbook's licence).
- **`youtube-gaming`**: `gate_youtube_authentic` requires a decodable video, **≥ 10 distinct
  frame signatures** (a static image dumped with audio fails) and Jaccard ≤ 0.85 against a
  prior-upload index. Measured: no `upload_index.json` exists anywhere in the repo yet, so the
  first upload has nothing to be compared against — the index has to be created at the visual
  stage or the check is silently vacuous.
- **`streaming`**: `gate_release_ready` needs `master.wav`, `artwork.jpg|png`, an ISRC matching
  `^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$`, a manifest carrying title/artist/isrc/genre and a
  non-empty `ai_disclosure`. Artwork is a j_kro creative gate — do not fabricate covers.

## 4. Rhythm math and throughput (derived, not assumed)

At the genre's 88 BPM in 4/4, one bar is `4 × 60 / 88 = 2.72727… s`. Measured bar math:

```
 88 BPM: bar=2.7273s   420s = 154.000 bars (whole bar)
 88 BPM: bar=2.7273s   480s = 176.000 bars (whole bar)
 88 BPM: bar=2.7273s   600s = 220.000 bars (whole bar)
```

Every candidate length lands on a whole bar, so the loop seam can be bar-aligned at this tempo.
Two constraints pinch from opposite sides:

- **The registry's video shape is `loop-10min` = 600 s = 220 bars.**
- **The planner refuses anything over 420 s** (`music/planner/planner.py:82-83`:
  `MIN_DURATION_S = 30`, `MAX_DURATION_S = 420`). 420 s = 154 bars — a legal, whole-bar render,
  but 7 minutes, not the 10 the shape asks for.

So the planner queue cannot express this genre's own video shape; a 600 s render has to go
through the `sunolocal` API, which passes `duration` straight through to the plan (§7).

Throughput: cadence 2/wk → 2 tracks/week, each feeding one pack. The pack generator's own
minimums are `MIN_LOOPS = 5` and `MIN_ONESHOTS = 5` (`music/assets/pack.py`), and the sample
pack carries 5 loops / 12 stems / 8 one-shots / 6 SFX. The loops it generates are **1.3 s**;
the gate's floor is **2 s**. At 88 BPM a 2 s loop is under one bar (2.73 s), so the real
minimum worth shipping is **one bar = 2.727 s, or better 4 bars = 10.909 s** — a loop of five
bars at this tempo is 13.6 s.

Export policy: exports go through Suno Studio (unlimited). The standard-download meter is
**0/60** today (measured, §8). Note the two separate meters recorded in the lane: Suno's
Download dialog meters *download credits* (1/song, format-independent), while
`music/quota-ledger.json` tracks the 60/month standard counter and Studio exports. Record both.

## 5. Audio identity (locked for this genre)

Style field, verbatim from `music/prompts/elemental-earth.md` — **487/1000 chars, measured**:

```
ancient cavern earth theme, 88 BPM, deep didgeridoo drone on a low open root, steady
heartbeat djembe and buffalo-drum pulse, earthy marimba and wooden mallet figures, breathy
low tribal flute phrases, sub-bass stone rumble, hand-clap sticks and shaker layers, mystical
ritual energy, open fifth drones with no third for a rooted unfinished horizon, slow harmonic
movement every 4-8 bars, cave reverb with distant stone echo, awe and ancient legend, patient
and heavy, seamless game loop
```

Settings: **Weirdness 35%**, **Style Influence 80%**, **Exclude Styles:**
`EDM, synths with fast arpeggios, pop vocals, bright major key, drum machine, trap`
(six terms — the documented maximum; the template's own list starts with a leading space).

Structure: 6 tag-sheet sections — `[Intro]`, `[Instrumental]`, `[Instrumental]`,
`[Instrumental Break]`, `[Instrumental]`, `[Outro]` — each with a parenthetical direction,
ending "layers subtract to drone and rumble — LOOP POINT into bar 1". The tag sheet is
**structure control, not lyrics** (§10).

**The tempo trap, measured against the deployed engine** (§7): the genre anchor 88 BPM is not
reachable by asking for it, because the request has no tempo field. It is reachable only by
setting the *style-adherence* dial to `styleWeight = (88-60)/120 = 0.2333` — i.e. by telling
the engine to follow the style at **23%** when the template asks for **80%**. At the template's
own 80% the plan comes out at **156 BPM, 1.77× the anchor**, i.e. a rushing tempo, which the
template names as an automatic reject. Filed as `t_25a6499c` (§12).

## 6. Visual identity (locked for this genre)

`music/visuals/element-earth.md`:

- Palette: stone gray-brown `#4a4238`, ochre `#a17c4f`, moss green `#5c6b4a`, torch amber
  `#d9962e`, deep shadow `#17130e`.
- Scene: megalith chamber / canyon floor / rune-carved cavern. Scale must read monolithic — a
  human-height reference (stairs, doorway) in at least one frame zone.
- Motion: almost still. Dust drift ~1 px/s, torch flicker 8–12 Hz inside its small radius, one
  slow volumetric shaft sweep per 2–4 min. "Stone does not move. If it animates, it is the
  wrong element."
- Texture: rough rock normal grain, small torch bloom, deep cave falloff, wind-blown dust at
  thresholds.
- **Variation is a gate requirement, not a nicety:** rotate chamber / canyon / ruin scenes per
  upload, palette constant — `gate_youtube_authentic` measures frame-signature diversity
  (≥ 10 distinct) and near-duplication against prior uploads (Jaccard ≤ 0.85).
- Audio-visual sync: heartbeat drum = torch flame breathing (radius pulse on the beat);
  throat-chant breakdown = all torches dim 50%, dust hangs still; drone swell = the light shaft
  slowly widening.

For the `loop-10min` shape the render is one continuous chamber (scale must survive 10 minutes)
with chapter fades, not cuts, and the variation rule above is what keeps the next upload from
being flagged as a duplicate of this one.

## 7. Generation path — measured on this host

Two engines exist. Both were probed live during this stage.

### 7a. `sunolocal` — the service that can render this genre today

Deployment `sunolocal-source` (ns `mining`), Service ClusterIP `10.43.164.190:8123`,
image tag v0.1.2. Probed live:

```
GET /health        -> {"status":"ok"}
GET /api/v1/models -> {"engines":{"ace":{"kind":"ACE-Step 1.5","via":"acestep_plan.py -> comfyui-zephyr window"},
                                   "yue2":{"kind":"YuE2-3B","via":"yue2-zephyr http"}},
                      "default":"ace"}
```

The `POST /api/v1/generate` body schema, read from the live `openapi.json` — **17 properties**:

```
prompt, style, lyrics, title, instrumental(bool, default false), model, customMode,
negativeTags, vocalGender(enum m/f), duration(int), styleWeight(number), weirdnessConstraint,
audioWeight, variety(int), callBackUrl, seed(int), engine
has 'bpm' property: False
has 'key' property: False
```

No tempo field and no key field. `music/sunolocal/translate.py` (read from inside the running
pod at `/opt/sunolocal/music/sunolocal/translate.py`) fills them itself:

```
bpm = 120                                   # hardcoded
if req.style_weight is not None:
    bpm = int(60 + req.style_weight * 120)  # Suno's style dial used as a tempo control
bpm = max(30, min(240, bpm))
key = req.style or "C major"                # the KEY receives the whole caption
```

and `acestep_plan.py` passes `plan["key"]` into the ACE node as `keyscale`.

**Executed against the deployed module with this genre's own 487-char caption** (no GPU, no
network — the module is imported in the pod), outputs verbatim:

```
caption_chars : 487
--- A: instrumental=True, lyrics empty, styleWeight unset (the default) ---
  plan.bpm        : 120
  plan.key chars  : 487  (key IS the caption: True)
  plan.lyrics     : '[Instrumental]\n'
  caption chars   : 512  tail=' and heavy, seamless game loop, instrumental, no vocals'
  cue present     : True
  bpm vs 88 anchor: +32 BPM (1.36x)
--- B: styleWeight=0.8 (the template's own Style Influence) ---
  plan.bpm        : 156                      bpm vs 88 anchor: +68 BPM (1.77x)
--- C: styleWeight solved for the 88 BPM anchor (0.2333) ---
  plan.bpm        : 88                       bpm vs 88 anchor: +0 BPM (1.00x)
--- D: tag sheet as lyrics + instrumental=True (keeps sections, loses cue) ---
  plan.bpm        : 120      cue present: False   (caption stays 487 chars, no instrumental cue)
--- E: tag sheet as lyrics + cue appended to style by hand + styleWeight for 88 ---
  plan.bpm        : 88       cue present: True    key chars: 512 (key IS the caption: False)
```

**Routing rule derived from that measurement.** For a render that holds both the tempo anchor
and the section structure:

- `styleWeight = 0.2333` (buys 88 BPM at the cost of style adherence — the correct value is the
  engine's bug, not a preference; `t_25a6499c` is the fix).
- pass the tag sheet as `lyrics` **and** append ``, instrumental, no vocals`` to `style`
  yourself — variant D silently drops the instrumental cue because `translate.py` only appends
  it when `lyrics` is empty.
- accept that `key` will be a 512-char paragraph until `t_25a6499c` lands. Do not "fix" it by
  shortening the caption — the caption is the only steering text the engine sees.

The instrumental plumbing itself works: `instrumental: true` + empty `lyrics` appends the cue
and substitutes `[Instrumental]\n` so the renderer's loader passes; `adapters/ace_comfy.py`
passes `--allow-empty` for the empty body.

### 7b. The planning/render CronJobs (namespace `mining`)

| Stage | Job | Schedule | Input | Output |
|---|---|---|---|---|
| plan | `music-pipeline` | `17 */6 * * *` | ConfigMap `music-pipeline-briefs` key `briefs.json` | `/var/lib/music-plans/<name>.json` |
| render | `music-pipeline-render` | `41 */4 * * *` | plans with no `.rendered` marker | audio via `music/scripts/acestep_plan.py` |

Live reads during this stage:

```
$ kubectl get cm -n mining music-pipeline-briefs -o jsonpath='{.data.briefs\.json}'
[{"brief":"a late-night kitchen where someone finally stops working and just listens to the rain",
  "genre":"chill-lounge","lyricsMode":"draft","name":"smoke-chill-lounge","title":"Kitchen Light"}]

$ kubectl logs -n mining music-pipeline-render-29869541-h2s2z | tail -4
done: found=3 rendered=0 skipped=3 failed=0
$ kubectl logs -n mining music-pipeline-29869517-s7jq2 | tail -2
done: 1/1 planned

$ ls -la /var/lib/music-plans/          # on nexus
final-round.json  final-round.rendered        (rendered, empty marker)
smoke-chill-lounge.json  smoke-chill-lounge.rendered  (8 bytes: "refused")
testplan.json  testplan.rendered        (8 bytes: "refused")
```

The marker files are the whole story: nothing has rendered on this route, and the two plans
that were attempted were **refused** by the renderer because `--lyrics-mode draft` scaffolds
sections with no lines. `planner.py --lyrics-mode` accepts only `draft|ai` and there is no
`--instrumental` flag (measured, `music/planner/planner.py:528`), so an instrumental genre
cannot enter this queue either. Covered by `t_25a6499c` (§12).

The payload ConfigMap `music-pipeline-payload` mounts the data the jobs consume:
`music__genres.yaml`, the three blueprints, `music__planner__planner.py`,
`music__scripts__acestep_plan.py`, and all 14 `music__prompts__*.md` (including
`elemental-earth.md`). It does **not** mount the gates or the asset-pack generator.

### 7c. Defects found while resolving this brief

**D1/D2/D3 — already filed, and this genre is a named victim.** `t_25a6499c` (nexus-core,
ready): bpm hardcoded, `key` = the style caption, planner queue has no instrumental field. It
lists the four elementals among the 8 affected templates. This brief adds the two numbers that
card does not carry: the **exact** styleWeight for this genre (0.2333) and what the template's
own 80% produces (**156 BPM**, 1.77×). Do not re-file.

**D4 — the live checkout is behind, so this brief cannot be executed as written.**
`git rev-list --count main..origin/main` = **15** and `origin/main..main` = **7** (local tip
`9ebf6af`). `music/suno-gen.py`, `music/sunolocal/`, `music/assets/pack.py` and
`brain/runbooks/music-game-assets.md` exist **only on `origin/main`**:

```
$ ls music/suno-gen.py music/sunolocal
ls: cannot access 'music/suno-gen.py': No such file or directory
ls: cannot access 'music/sunolocal': No such file or directory
```

`music/stages.yaml`'s generate stage tells the worker to run `music/suno-gen.py`, which is not
in this working tree. Already filed as `t_8a715681` (nexus-core, ready). Do not re-file.

**D5 — the asset-pack generator's output does not satisfy the game-assets gate.** Measured in
§3: 12 findings, and its 1.3 s loops are below the gate's 2 s floor. This is new; filed as a
card (§12).

## 8. Existing assets for this genre

Measured: **nothing exists for elemental-earth**. No lyric sheet (none is wanted — instrumental),
no blueprint, no audio, no plan, no pack.

```
$ find music/lyrics -maxdepth 2            # only activist, chill-lounge, trance
music/lyrics/blueprints/{activist,chill-lounge,trance}.yaml
music/lyrics/activist/what-runs-beneath  music/lyrics/chill-lounge/amber-hour
music/lyrics/trance/signal-before-dawn
$ grep -rl "elemental-earth" --exclude-dir=.git .
music/genres.yaml  music/prompts/elemental-earth.md  music/visuals/element-earth.md
music/rubrics/gamer.json  music/briefs/chill-lounge.md  music/briefs/anime-ending.md
music/briefs/anime-opening.md  music/briefs/sentimental-piano/.../brief.{md,json}
```

The last four are the sibling briefs (each mentions every genre in the registry list). There is
no `music/assets/` and no `music/packages/` directory in this working tree at all.

Quota is untouched, measured:

```
$ /usr/bin/python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

The only asset pack in existence is `packages/welcome-asset-pack` (`origin/main:83cd0ce`), and
it is a **chill-lounge** pack from a 184.57 BPM source with 1.3 s loops — it is a shape sample,
not this genre's product, and it fails the game-assets gate (§3).

## 9. What the gate stage will score (gamer rubric) — and a measured ambiguity

`music/rubrics/gamer.json` (family `gamer`, which includes `elemental-earth`), pass threshold
**7.0** on the geometric-median aggregate of the panel's per-judge weighted means:

| Criterion | Weight | Applies to elemental-earth? |
|---|---|---|
| `chip_timbre_authenticity` | 3 | No — the criterion's own name scopes it to chiptune-8bit |
| `battle_energy` | 3 | **Ambiguous — see below** |
| `loop_safety` | 3 | Yes — common to all game-asset delivery |
| `asset_packaging` | 1 | Yes |
| `loudness_target` | 1 | Yes |

**The ambiguity, quoted.** The criterion is named
`"Boss/battle energy (elemental-*, epic-orchestral-boss)"` and its anchor is
"fast tempos 130-200 BPM … typical 140-180", with the guide `1 = slow ambient track with a
battle label`. This genre's own template fixes the opposite: 88 BPM, "earth does not chase".
The rubric's `notes` then say *"elemental-\* tracks choose per their prompt … battle tracks MUST
pass battle_energy"* — so the criterion's scope and its notes disagree for the two slow
elementals (earth 88, water 82).

**Margin arithmetic, computed from the rubric file** (not a measured render — no render exists):

```
battle_energy=10 -> overall 10.00 (PASS)      battle_energy= 4 -> overall 8.36 (PASS)
battle_energy= 7 -> overall  9.18 (PASS)      battle_energy= 1 -> overall 7.55 (PASS)
  …with battle_energy=4 and loop_safety=6, asset_packaging=6 -> overall 6.91 (FAIL)
```

So an in-genre earth render is **not** doomed by the ambiguity — but if a judge reads the
criterion name literally and scores 1, the whole pass margin rests on the other three criteria
being perfect, and two ordinary imperfections elsewhere (6/10 on loop safety and packaging)
flip it to FAIL. Recommendation for the rubric owner: scope `battle_energy` to
`elemental-fire` + `epic-orchestral-boss`, and give the slow elements their own criterion
(drone discipline / patience / no-third harmonic signature) so the panel is scoring the genre
that exists. Recorded here rather than filed, because it is a predicted ambiguity, not an
observed failure.

## 10. Stage plan for this genre (skips locked)

| Stage | Bot | What happens here |
|---|---|---|
| brief | producer | this file ✅ |
| genre-select | producer | registry entry already resolved in §1; nothing left to select |
| lyrics | writer | **NOT APPLICABLE — instrumental** (`prompts/elemental-earth.md:15`). The stage must be recorded as not-applicable, not skipped silently. Do not let `planner.py --lyrics-mode ai` write lyrics: it would both contradict the template and void the human-authorship default. |
| generate | producer | `sunolocal /api/v1/generate` with `instrumental: true`, empty `lyrics`, tag sheet as lyrics, cue appended to `style`, `styleWeight = 0.2333` (§7a). Suno CDP (`music/suno-gen.py`) is the alternative route and needs D4 fixed first. |
| curate | producer | pick the winner; reject reason per loser. Reject conditions are §2 — electronic drums, defined tonality, rushed tempo, non-loop ending. |
| stems | producer | Studio export; ≥ 4 stems within ±0.5 s of the master. |
| master | producer | `gate_loudness --target streaming` (-14) for the streaming lane; -16 for sync-family. Note the open ruler card `t_9546841b` (the gate measures `volumedetect` RMS, not gated LUFS — 1.4–2.4 dB below LUFS on real masters). |
| gate | reviewer-deepseek / panel | `music/rubrics/panel.py --genre elemental-earth` → `review.json`, then `gate_quality`. See §9. |
| package | producer/distributor | build the pack **in the shape `gate_sync_ready --lane game-assets` reads** (§3, D5), plus `loop_points.json` and `gate_loop_points` PASS. |
| visual | videobot | `loop-10min` chamber render + `gate_youtube_authentic` (≥ 10 distinct frames, Jaccard ≤ 0.85, disclosure). |
| human-approval | — | j_kro. Nothing publishes without it. |
| publish | publishbot | upload **private/draft only**; itch.io via `butler` (`brain/runbooks/music-game-assets.md`). No public release without the human gate. |

## 11. What the sibling cards in flight mean for this genre

- `t_c92f566d` (elemental-earth 7.7, **ready**) is the duplicate of this card. Both resolve to
  THIS brief. It should be closed as a duplicate rather than dispatched into a second brief.
- `t_92a09bdc`, `t_6f0d261e`, `t_d3b9e218`, `t_3cb6e654`, `t_42a01e18`, `t_d8cc0a38` — the
  four elementals have two cards each, the same pattern as every other genre on the board.
- The oracle dedupe guard (`ade6e87`, `music/oracle.py` + `music/test_oracle_dedupe.py`) now
  refuses to open a second card for a genre that already has one in flight, so this duplication
  should not recur; the existing duplicate pairs still need clearing (`t_bf0e5edd`).

## 12. Handoffs

- **`t_25a6499c`** (nexus-core, ready) — bpm hardcoded / key = caption / queue has no
  instrumental field. This brief adds the elemental-earth numbers; nothing new to file.
- **`t_8a715681`** (nexus-core, ready) — reconcile the diverged checkout. This brief adds the
  measured 15/7 counts and the missing paths; nothing new to file.
- **`t_5ed495eb`** (NEW, distributor; parent = this card) — the asset-pack ↔ game-assets gate
  mismatch (D5, §3), filed during this stage with the 12 findings and the two seam runs. It
  blocks the primary lane of all six gamer genres, not just this one.
- **`t_909069f0`** (NEW, nexus-core; parents = this card + `t_25a6499c`) — queue this track into
  the live generation path. It carries the exact render parameters measured in §7a
  (`styleWeight` 0.2333, tag sheet as `lyrics`, cue appended to `style`, 600 s duration) and is
  gated so it cannot run before the instrumental-mode fix lands.

## 13. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` — `/usr/bin/python3 music/registry.py validate` → OK (14 genres, 10 lanes)
- Lanes/gates: `music/lanes.yaml`, `music/gates/` (`gate_sync_ready` run live against the
  sample pack, both FAIL and the 51.6 s PASS case; `gate_loop_points` run live twice)
- Quota: `music/quota-ledger.json` + `gate_quota` → 0/60
- Engine: `mining/sunolocal` deployment v0.1.2 — `/health`, `/api/v1/models`, `openapi.json`,
  and `translate.py` read from inside the running pod; the plan probe executed in-pod
- Queue: CronJobs `music-pipeline` / `music-pipeline-render`, ConfigMaps `music-pipeline-briefs`
  and `music-pipeline-payload`, `/var/lib/music-plans/` (nexus)
- Rubric: `music/rubrics/gamer.json` + `music/rubrics/panel.py`, `music/gates/gate_quality.py`
- Skills/rubric rule: `brain/runbooks/music-game-assets.md` (`origin/main`)
- **Dangling reference (unchanged):** `brain/playbooks/music-lane-architecture.md` is cited as
  "READ FIRST" by this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`,
  `autonomy.yaml`, `gates/README.md` and every gate script — and does not exist on this machine
  (`t_b0a4db92`). Same for `brain/research/music-monetization-2026.md`. Section numbers quoted
  from it (§2, §3, §5, §11.2, §13) cannot be checked.
