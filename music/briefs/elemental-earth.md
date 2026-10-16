# Brief — elemental-earth

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`) — **DELIVERED**; the chain
> resumes at `genre-select` (already resolved in §1–§3).
> **Card:** t_8fa97d4e (`music-oracle: elemental-earth (score 7.2)`) — the surviving OPEN card
> for this genre. The board check reports `elemental-earth → t_8fa97d4e [running]` with one open
> card per genre, rc=0 (`music/scripts/check_oracle_board.py`, re-run in this pass).
> **Superseded cards:** t_55e37b88 (score 7.5, done) wrote this brief; t_c92f566d (score 7.7,
> done) ran the §14 verification pass. Briefs in this lane are keyed by **genre**, not by card,
> so all three cards resolve to this one file — no second brief, no second stage chain.
> **Written:** 2026-10-16T13:14-05:00 (CDT)
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `c296db6` (main, shared working tree; 6–7 music
> workers commit into it concurrently, so HEAD moves between passes — **every count below is
> stamped with its own revision**).
> **Oracle:** **true score 7.0/10** — re-scored live in this pass through
> `music/oracle.py:score_genre()`: quota headroom 10.0, lane coverage 6.0, revenue 8.0, cadence
> fit 3.3333, policy risk 9.0, trend signal 3.0. Threshold 5.0 → produce. The 7.5 / 7.7 / 7.2 in
> the three card titles are **not** reproducible: 7.5 and 7.7 come from the 2026-10-09 double
> emission (two cards ten minutes apart) and 7.2 pays the pre-`b2d11f7` failed-fetch premium.
> §14 corrects 1 and §16 reproduce the arithmetic live.
> **Revision:** the superseded blob is
> `sha256 036395fe8bf403840e1b0b84096c46e474fd55c354125cab21c4e42587eb1ea0` (705 lines /
> 44176 B, commit `c296db6`); this pass supersedes it. Earlier recorded supersessions: §14
> (`0e9bf0de…`, 537 lines / 30576 B), §15 (`b3a31d2a…`, 679 lines / 41686 B, then `55e049c8…`,
> 703 lines / 43754 B).
> **Verification passes:** §14 (`t_c92f566d`, 13:53 CDT), §15 (`t_0f7aed63` + `t_e6d422ec`,
> 15:31 CDT), §16 (`t_8fa97d4e`, this pass — every checkable claim re-measured). The genre
> decision is unchanged: **produce**.

## 1. Genre resolution (live, not transcribed)

Resolved through the registry loader, not copied by hand:

```
$ /usr/bin/python3 music/registry.py validate
registry OK: 14 genres, 10 lanes, 1 stage gate rule(s)
genres: activist, anime-ending, anime-opening, chill-lounge, chiptune-8bit,
        commentary-beds, elemental-air, elemental-earth, elemental-fire,
        elemental-water, epic-orchestral-boss, jungle-dnb, sentimental-piano, trance
lanes: direct-fan, direct-license, game-assets, stock-ai-native, streaming,
       sync, sync-documentary, youtube-gaming, youtube-longform, youtube-mix
stage gate visual: lane_gate -> gate_youtube_authentic (when_absent: none)
quota ledger: period 2026-10, standard 0/60 (warn_at 55, hard_stop_at 58)
```

Re-run in this pass (2026-10-16 16:05 CDT, `c296db6`). The transcript gained one clause and one
line since the brief stage wrote it: the board now declares a **stage gate rule** for the
`visual` stage and the header count reads `1 stage gate rule(s)`. Resolved for this genre the
rule answers `gate_youtube_authentic`:

```
$ /usr/bin/python3 music/registry.py gate-for-stage --stage visual --genre elemental-earth
stage   : visual
genre   : elemental-earth
lanes   : game-assets, youtube-gaming, streaming
gate    : gate_youtube_authentic
script  : music/gates/gate_youtube_authentic.py
reason  : lane 'youtube-gaming' is guarded by gate_youtube_authentic (surface: youtube)
action  : run that script against this stage's artifact
rc=0
```

This genre does carry a YouTube lane, so the rule's `when_absent: none` branch does not apply to
it — the visual stage has a real gate to run (§3, §10).

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
for 5–10 tracks, per `brain/runbooks/music-game-assets.md`), and **as of this pass it PASSES** on
the only asset pack in the repo — `packages/welcome-asset-pack`, which now exists **in this
worktree** (the reconciliation merge, §7c D4). Measured live (2026-10-16 16:05 CDT):

```
$ /usr/bin/python3 music/gates/gate_sync_ready.py \
      --package-dir packages/welcome-asset-pack --lane game-assets
PASS gate_sync_ready
  package     : packages/welcome-asset-pack
  lane        : game-assets
  mode        : pack
  pack        : welcome-asset-pack
  counts      : loops 5, one_shots 7, sfx 6, stems 12 (matched against the files on disk)
  metadata    : title, artist, bpm, key, mood, genre, sample_rate present
  sample_rate : 44100 Hz (ffprobe-verified on every audio file)
  stems       : 12 (mutually time-aligned within +/-0.5s)
  loops       : 5 (each carries loop points with a span >= 2s and declares seamless)
  seam        : loop_01_bpm184_key-Cmajor.wav 0.28x, loop_02 0.23x, loop_03 0.04x,
                loop_04 0.20x, loop_05 0.05x (measured, max 3.0x)
  clearance   : clearance_doc.pdf
  disclosure  : ai_disclosure.txt
  licence     : LICENCE.txt
rc=0
```

**The mismatch this brief opened on is closed** (card `t_5ed495eb`, distributor, done). History,
kept as evidence: when this brief was written the gate read a *per-track package* layout only
(`full_mix.wav`, `instrumental.wav`, `stems/`, a `metadata` object, a clearance PDF, an AI
disclosure) while the generator emitted a *pack* layout (`loops/`, `stems/`, `one_shots/`,
`sfx/`, `manifest.json` with `pack_name`/`counts`), so the same command reported **12 findings**
and the lane was not passable. The gate now has an explicit `mode: pack` path, reads the pack's
own loop index, and the pack carries the clearance document, the AI disclosure and the metadata
object. Both layouts live: on a *per-track package* directory the same gate still reports the two
layout findings (`full_mix.wav`, `instrumental.wav`) — correct, a pack is not a per-track
package.

Superseded figures from the brief stage, re-measured: the loops it recorded as **1.3 s** are now
**5.201270 s** each (ffprobe; 4 bars @ 184.57 BPM), the pack carries **7** one-shots (it said 8),
and the 12 stems all measure **51.605011 s**.


The seam half is also measured, and **the gate has grown a second ruler** since the brief stage
wrote this section (card `t_b21aeb51`): it now checks junction curvature against body curvature
(≤ 3.0×) **and** the level delta between the loop's last second and its first (≤ 6.0 dB), and it
requires a span ≥ 2 s. It also has a `--pack-dir` entry point that reads a pack's own loop
index. All three live runs (2026-10-16 16:05 CDT):

```
$ /usr/bin/python3 music/gates/gate_loop_points.py \
      --master packages/welcome-asset-pack/loops/loop_01_bpm184_key-Cmajor.wav \
      --loop-points <lp.json>                 # {"loop_start_s":0.0,"loop_end_s":1.3}
FAIL gate_loop_points
  master   : …/loops/loop_01_bpm184_key-Cmajor.wav (5.201s)
  loop     : [0.000s -> 1.300s]
  - loop span is 1.30s — too short to be musical (minimum 2s)
  - loop_points.json does not declare 'seamless': true
rc=1

$ /usr/bin/python3 music/gates/gate_loop_points.py \
      --master packages/welcome-asset-pack/stems/01_bass.wav \
      --loop-points <lp.json>       # {"loop_start_s":0.0,"loop_end_s":51.605,"seamless":true}
FAIL gate_loop_points
  master   : packages/welcome-asset-pack/stems/01_bass.wav (51.605s)
  loop     : [0.000s -> 51.605s]
  seam     : curvature ratio 0.21x (max 3.0x)
  level    : tail-1.0s -79.5 dB vs head-1.0s -45.3 dB (delta 34.2 dB, max 6.0)
  - loop level drops 34.2 dB across the wrap: tail-1.0s -79.5 dB vs head-1.0s -45.3 dB
    (max 6.0 dB) — a fade or level ramp at the loop end; the loop is NOT seamless
rc=1

$ /usr/bin/python3 music/gates/gate_loop_points.py --pack-dir packages/welcome-asset-pack
PASS gate_loop_points
  pack     : packages/welcome-asset-pack (5 loops)
  loop 1/5: loops/loop_01_bpm184_key-Cmajor.wav
            [0.000s -> 5.201s] span 5.201s  seam 0.28x (max 3.0x)  level 1.7 dB  RMS 0.07762
  loop 2/5: loops/loop_02_…  0.23x  level 0.8 dB  RMS 0.07674
  loop 3/5: loops/loop_03_…  0.04x  level 1.9 dB  RMS 0.06310
  loop 4/5: loops/loop_04_…  0.20x  level 0.8 dB  RMS 0.10471
  loop 5/5: loops/loop_05_…  0.05x  level 1.9 dB  RMS 0.07499
  verdict  : all 5 loops seamless (curvature <= 3.0x AND tail/head level delta <= 6.0 dB)
rc=0
```

Three consequences this brief now carries, all measured. (1) The 51.605 s stem that PASSED the
brief stage **curvature-only** gate at 0.24× now FAILs the **level** ruler at 34.2 dB — a
curvature-only PASS was not a seamlessness proof. (2) The two seam runs the brief stage quoted
reproduce only in part: the span finding is correct, and the abbreviated document also now trips
the `seamless` finding (`gate_loop_points.py:241`), a third finding the quoted output did not
show. (3) A pack index must be read with `--pack-dir`, not `--loop-points`: passing it as
`--loop-points` is refused with "is a pack index (it carries 'loops'); run it with
`--pack-dir <the pack>` instead". The gate's method is sound on real rendered audio — the
generated loops of the brief stage failed on length and level, not on curvature.


Decisions locked here so later stages do not re-litigate them:

- **The pack must be emitted in the shape the gate reads — DONE.** The gate grew an explicit
  `mode: pack` path (§3 above), so the pack layout `music/assets/pack.py` emits is the layout the
  `game-assets` gate accepts. A *per-track package* (sync/streaming shape) is still a different
  layout: build the per-track package only for the lanes that demand it, and never assume the
  pack's PASS covers a per-track surface.
- **`instrumental.wav` must be a real, distinct render** — the per-track gate (sync/streaming)
  fails an instrumental that is byte-identical to `full_mix.wav`. An earth master is already
  instrumental, so ship the drone+percussion-only alternate mix as the instrumental version and
  say which variation it is. (This requirement is NOT enforced by the pack mode.)
- **Stems: ≥ 4 files, each within ±0.5 s of the master duration** (ffprobe-measured, not file
  size). Export through Suno Studio, never the standard download button.
- **Loop points are mandatory** for this lane, and `gate_loop_points` must pass on them. Since
  `t_b21aeb51` the gate runs **three rulers**: junction curvature ≤ 3.0×, tail/head level delta
  ≤ 6.0 dB (the level finding is `gate_loop_points.py:310`, quoted verbatim in the FAIL above),
  and — since `t_8297d2c6`, lane commit `a664b4e` — an **end guard** that measures the envelope
  inside the loop's last 1 s (split in half; the second half must not sit more than the same
  6.0 dB below the first) and refuses a loop whose first or last 1 s is at/below the lane's
  −50 dB silence floor. A
  document must also declare **`"seamless": true`** (`:241`) and a span ≥ 2 s. Read a pack's index
  with `--pack-dir <pack>`; pass a single-track document with `--loop-points` — the two paths are
  not interchangeable (measured: a pack index passed as `--loop-points` is refused). The two seam
  runs the brief stage quoted reproduce only with the `seamless` key present.
- **`clearance_doc.pdf` must be a real PDF** (`%PDF-` header parsed) and `license_tiers.*`
  must exist for the licence the pack ships (perpetual game-asset v1 is the runbook's licence).
- **`youtube-gaming`**: `gate_youtube_authentic` requires a decodable video, **≥ 10 distinct
  frame signatures** (a static image dumped with audio fails) and Jaccard ≤ 0.85 against a
  prior-upload index (`gate_youtube_authentic.py:43` `DEFAULT_MIN_DISTINCT = 10`, `:27`
  `--sim-max 0.85`). Measured in this pass: no `upload_index.json` exists anywhere in the repo
  (`find` over the worktree: 0 hits), so the first upload has nothing to be compared against —
  the index has to be created at the visual stage or the check is silently vacuous.
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
- **The planner cap is now 600 s — this genre is the reason it moved.** When this brief was
  written the guard rail was `MAX_DURATION_S = 420` (`music/planner/planner.py`), so 600 s could
  only be reached through the `sunolocal` API by hand. The cap was raised to the longest shape
  the registry names, and the code comment records the measurement this genre supplied
  (`planner.py:98-101`: "t_909069f0 measured the consequence — elemental-earth's documented entry
  is 220 whole bars at 88 BPM = 600.0 s, the planner refused it"). Live read of the guard rails:
  `MIN_DURATION_S = 30` (`planner.py:103`), `MAX_DURATION_S = 600` (`planner.py:104`).

So the planner queue **can** express this genre's own video shape now, and it already does: the
live entry for this genre is `elemental-earth-chamber-loop`, `instrumental`, `duration 600`
(§7b, §8). The line a reader must not carry forward is the brief stage's "a 600 s render has to
go through the `sunolocal` API" — true at 13:14 CDT, false since the cap moved.

Throughput: cadence 2/wk → 2 tracks/week, each feeding one pack. The pack generator's own
minimums are `MIN_LOOPS = 5` and `MIN_ONESHOTS = 5` (`music/assets/pack.py:85-86`), and the
sample pack carries 5 loops / 12 stems / 7 one-shots / 6 SFX (re-measured this pass). The loops
it now generates are **5.201270 s** each (4 bars @ 184.57 BPM, measured); the gate's floor is
**2 s**. At 88 BPM a 2 s loop is under one bar (2.73 s), so the real minimum worth shipping is
**one bar = 2.727 s, or better 4 bars = 10.909 s**. The brief stage recorded the pack's loops as
1.3 s, which was below the gate floor; they are not any more.


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

**The tempo trap was real and is now FIXED in the deployed engine** (§7a, card `t_25a6499c`,
done). History, kept as evidence: when this brief was written the request carried no tempo field,
so the 88 BPM anchor was unreachable by asking for it — it could only be bought by setting the
*style-adherence* dial to `styleWeight = 0.2334` (telling the engine to follow the style at
**23%** when the template asks for **80%**), and the algebraic solve `(88-60)/120 = 0.2333` was
one BPM short because the engine truncates with `int()` (`0.2333 → 87`, `0.2334 → 88`). At the
template's own adherence the plan came out at **156 BPM = 1.77× the anchor**, a rushing tempo the
template names as an automatic reject.

Engine tag **v0.1.3** (live in the pod today) added an explicit `bpm` field and a `keyscale`
field to the request, and re-ordered `translate.py` so an explicit value wins:

```
bpm = int(req.bpm) if req.bpm is not None else (int(60 + req.style_weight * 120) if … else 120)
key = req.keyscale or "C major"
```

So the correct instruction for this genre is **`bpm: 88`** (and `keyscale: "C minor"`), not a
styleWeight solve; `styleWeight` is now a documented fallback only. Measured in the live pod this
pass: `bpm=88 → 88`; `bpm=88, keyscale="C minor" → key "C minor"`; `styleWeight=0.8 → 156`
(still the counter-example); `styleWeight=0.2334 → 88` (the fallback still works). The queued plan
for this genre already carries `"bpm": 88` and `"key": "C minor"` (§7b, §8).


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
image tag **`localhost/sunolocal:v0.1.3`** (re-read this pass; the brief stage recorded v0.1.2, and
the interface changed with the tag — see below). Probed live 2026-10-16 16:05 CDT:

```
GET /health        -> {"status":"ok"}
GET /api/v1/models -> {"engines":{"ace":{"kind":"ACE-Step 1.5","via":"acestep_plan.py -> comfyui-zephyr window"},
                                   "yue2":{"kind":"YuE2-3B","via":"yue2-zephyr http"}},
                      "default":"ace"}
```

The `POST /api/v1/generate` body schema, read from the live `openapi.json` — **19 properties**
(the brief stage measured 17):

```
prompt, style, lyrics, title, instrumental(bool, default false), model, customMode,
negativeTags, vocalGender(enum m/f), duration(int), styleWeight(number), weirdnessConstraint,
audioWeight, variety(int), callBackUrl, seed(int), engine,
bpm, keyscale
has 'bpm' property: True        has 'key' property: False        has 'keyscale' property: True
```

**The tempo field and the key field now exist.** `music/sunolocal/translate.py` (read from inside
the running pod at `/opt/sunolocal/music/sunolocal/translate.py`) makes an explicit value win and
keeps the old style-dial mapping as a documented fallback:

```
bpm = None
if req.bpm is not None:
    bpm = int(req.bpm)
elif req.style_weight is not None:
    bpm = int(60 + req.style_weight * 120)   # the legacy tempo control, fallback only
if bpm is None:
    bpm = 120
bpm = max(30, min(240, bpm))
key = req.keyscale or "C major"              # NEVER req.style (that was the caption-as-key bug)
```

and `acestep_plan.py` passes `plan["key"]` into the ACE node as `keyscale`. The pod's own
docstring records the two defects this genre was a victim of as fixed: `t_25a6499c` D1 (bpm
hardcoded) and D2 (`key` = the whole style caption).

**Executed against the deployed v0.1.3 module with this genre's own 487-char caption** (no GPU,
no network — the module is copied in and imported in the pod; script `inpod_probe.py` of this
pass). Variants A–G are all re-measured live this pass; the A–E lines the brief stage recorded
were run against v0.1.2:


```
caption_chars : 487
--- A: instrumental=True, lyrics empty, nothing else (v0.1.3 defaults) ---
  plan.bpm        : 120      key: 'C major' (7 chars — NOT the caption)
  plan.lyrics     : '[Instrumental]\n'
  caption chars   : 512      cue present: True
  bpm vs 88 anchor: +32 BPM (1.36x)
--- B: instrumental=True, bpm=88 (the v0.1.3 path) ---
  plan.bpm        : 88       key: 'C major'      bpm vs 88 anchor: +0 BPM (1.00x)
  caption chars   : 512      cue present: True
--- C: bpm=88 + keyscale="C minor" (the v0.1.3 path, key set) ---
  plan.bpm        : 88       plan.key: 'C minor' (7 chars)      cue present: True
--- D: tag sheet as lyrics + instrumental=True + bpm=88 ---
  plan.bpm        : 88       cue present: True   (the cue is now appended on the caption
  plan.lyrics     : the 6-tag sheet, structure kept            for EVERY instrumental request)
--- E: styleWeight=0.8 (the template's own Style Influence — legacy fallback only) ---
  plan.bpm        : 156      bpm vs 88 anchor: +68 BPM (1.77x)   ← the counter-example
--- F: styleWeight=0.2334 (the legacy 4-decimal solve) ---
  plan.bpm        : 88       bpm vs 88 anchor: +0 BPM (1.00x)
--- G: tag sheet as lyrics, no bpm, no styleWeight ---
  plan.bpm        : 120      cue present: True
```

Three of these differ from the variants the brief stage recorded, and the differences are the
point: variant A's `key` is now the 7-char default `C major`, **not** the 487-char caption
(D2 fixed); variant D keeps the section tag sheet **and** the instrumental cue, where it used to
drop the cue (that defect is why a caller had to append the cue to `style` by hand); and the
anchor is now reachable by asking for it (B/C), with the styleWeight solve demoted to a fallback
(E/F).


**Routing rule derived from that measurement (v0.1.3).** For a render that holds both the tempo
anchor and the section structure:

- send **`bpm: 88`** explicitly — that is the anchor, and the field exists. Do **not** reach for
  `styleWeight`: at the template's own 80% it renders 156 BPM (E), and the 4-decimal solve
  `0.2334` is a fallback for a caller that cannot send `bpm` at all (F). The legacy interval,
  kept for reference only: any 4-decimal weight in `[0.2334, 0.2416]` bought 88, and `0.2333`
  truncates to 87.
- send **`keyscale: "C minor"`** (the earth plan's own key) — or omit it and accept the engine's
  `C major` default. Do **not** leave the key to `style`: that was the captioned-as-key bug (D2),
  fixed.
- pass the tag sheet as `lyrics` **and** keep the instrumental cue on the caption. Since v0.1.3
  the cue is appended for every `instrumental: true` request, so the caller no longer has to
  append ``, instrumental, no vocals`` by hand — but the caption is still the only steering text
  the engine sees, so check it (512 chars = 487 + the 25-char cue) before queueing.

The instrumental plumbing itself works: `instrumental: true` + empty `lyrics` appends the cue
and substitutes `[Instrumental]\n` so the renderer's loader passes; `adapters/ace_comfy.py`
passes `--allow-empty` for the empty body. The genre's live plan (§7b, §8) carries exactly the
three values above: `bpm 88`, `key "C minor"`, `instrumental true` with the 6-tag sheet.


### 7b. The planning/render CronJobs (namespace `mining`)

| Stage | Job | Schedule | Input | Output |
|---|---|---|---|---|
| plan | `music-pipeline` | `17 */6 * * *` | ConfigMap `music-pipeline-briefs` key `briefs.json` | `/var/lib/music-plans/<name>.json` |
| render | `music-pipeline-render` | `41 */4 * * *` | plans with no `.rendered` marker | audio via `music/scripts/acestep_plan.py` |

Live reads in this pass (2026-10-16 16:05 CDT):

```
$ kubectl -n mining get cm music-pipeline-briefs -o jsonpath='{.data.briefs\.json}'
11 entries. This genre's is one of them:
{"brief":"ancient cavern earth theme, open-fifth drone with no third, heartbeat hide-drum pulse,
  wooden marimba figure, breathy low flute, ritual hush, seamless loop","duration":600,
 "genre":"elemental-earth","instrumental":true,"name":"elemental-earth-chamber-loop",
 "title":"Megalith Chamber"}              (plus smoke-chill-lounge, anime-ending-reflections,
 epic-orchestral-boss-the-last-gate, trance-signal-before-dawn, elemental-air-above-the-weather,
 sentimental-piano-room-with-the-light-going, commentary-beds-lo-fi-jazz-sting,
 commentary-beds-lo-fi-jazz-bed, elemental-fire-emberfall, chill-lounge-slow-gold)

$ kubectl -n mining get cronjob music-pipeline music-pipeline-render
music-pipeline                   17 */6 * * *   suspend=False
music-pipeline-render            41 */4 * * *   suspend=False        ← both schedules unchanged

$ kubectl -n mining logs job/music-pipeline-render-t6d7ad524 | grep -E 'earth|done:|audio saved'
audio saved to /tmp/chill-lounge-slow-gold.flac
skip   elemental-earth-chamber-loop (already rendered)
done: found=13 rendered=1 skipped=12 failed=0        ← "already rendered" for 12, earth among them

$ kubectl -n mining logs job/music-pipeline-t6d7ad524 | grep -E 'earth|done:'
skip  elemental-earth-chamber-loop (plan exists)
done: 11/11 planned

$ ls -la /var/lib/music-plans/          # on nexus
13 plans + their markers; 1 delivered master and its loop:
  elemental-earth-chamber-loop.json      1331 B   elemental-earth-chamber-loop.rendered   0 B
  elemental-fire-emberfall.json          1817 B   elemental-fire-emberfall.rendered       0 B
  elemental-fire-emberfall.flac      11421612 B   loops/elemental-fire-emberfall.loop.wav 614444 B
  smoke-chill-lounge / testplan / final-round / anime-ending-reflections / trance-…
  epic-orchestral-boss-…marker = "refused";  the rest 0 B
```

The marker files are the whole story, and it takes the wrapper to read them: the render CronJob
writes an **empty** marker on `rc=0` and `refused\n` on `rc=1`, and since `t_b21aeb51` a
`loop-10min` plan whose loop cannot be certified gets `.looprefused` with the reasons. Three
readings that the brief stage did not have: (1) **an elemental-earth plan EXISTS and its marker
is empty, i.e. that render exited 0** (§8 — the audio is real but not persisted on this volume);
(2) the plan CronJob logs `skip elemental-earth-chamber-loop (plan exists)` and
`done: 11/11 planned`, so the queue is live for this genre; (3) the counts moved — 13 plans, 1
delivered master, 1 delivered loop, and only three markers still read `refused`
(`smoke-chill-lounge`, `testplan`, `epic-orchestral-boss-the-last-gate`, the last because it is a
draft-mode scaffold).

**The instrumental half of this section is closed.** The brief stage measured
`planner.py --lyrics-mode choices=["draft","ai"]` with no `--instrumental`, so an instrumental
genre "cannot enter this queue either". Live now: `planner.py:905`
`--lyrics-mode choices=["draft", "ai", "instrumental"], default="draft"`, and `planner.py:215`
`is_instrumental_template(genre)` derives the flag from the template's own "Leave the **lyrics box
empty**" sentence. The consequence is visible in the queue above — the earth entry carries
`"instrumental": true` and its plan carries `"lyrics_mode": "instrumental"` (§8).

The payload ConfigMap `music-pipeline-payload` mounts the data the jobs consume. Read back
2026-10-16 16:05 CDT: **39 keys** — 6 blueprints (activist, anime-ending, anime-opening,
chill-lounge, epic-orchestral-boss, trance), 15 prompt entries (the 14 genre templates plus
`anisong-genre-blocks.yaml`, `elemental-earth.md` among them), 14 visuals, `genres.yaml`,
`music__planner__planner.py`, `music__scripts__acestep_plan.py` and `music__scripts__loop_close.py`
(the key `t_b21aeb51` added). It does **not** mount the gates or the asset-pack generator — the
gates run on the host, not in the jobs.


### 7c. Defects found while resolving this brief — all five are now CLOSED

**D1/D2/D3 — RESOLVED** (card `t_25a6499c`, nexus-core, done; shipped as engine tag v0.1.3).
History: bpm was hardcoded, `key` received the whole style caption, and the planner queue had no
instrumental field, with this genre's four-elemental family among the 8 affected templates. The
fix is measured in §7a: the request carries `bpm` and `keyscale`, an explicit value wins, and
`planner.py --lyrics-mode` takes `instrumental`. This brief's own contribution to that card —
the exact legacy styleWeight for this genre (**0.2334**, not the algebraic 0.2333) and what the
template's own 80% produced (**156 BPM = 1.77×** the anchor) — is retained in §5 and §7a as the
pre-v0.1.3 record. Do not re-file.

**D4 — RESOLVED.** The brief stage measured `git rev-list --count main..origin/main` = **15** and
`origin/main..main` = **7**, and `music/suno-gen.py`, `music/sunolocal/`, `music/assets/pack.py`
and `brain/runbooks/music-game-assets.md` existed only on `origin/main`, so the generate stage's
own instruction (`music/suno-gen.py`) could not be executed from this tree. The reconciliation
merge `ab33ad1` (card `t_8a715681`, done) joined the lineages. Re-measured this pass: `main` @
`c296db6` is **72 ahead / 0 behind** `origin/main` (`ba28f55`), and every path is present in the
worktree:

```
$ ls -la music/suno-gen.py music/assets/pack.py; ls -d music/sunolocal packages
-rw-r--r-- 1 j_kro j_kro 42652 Oct 16 14:23 music/suno-gen.py
-rw-r--r-- 1 j_kro j_kro 52690 Oct 16 14:50 music/assets/pack.py
music/sunolocal
packages
```

`check_stage_scripts` (the check that reads every script the stage prompts name) is **PASS,
11/11** on this tree. The 72-commit publish gap is the lane's standing pattern (local `main`
only), not a defect of this genre.

**D5 — RESOLVED** (card `t_5ed495eb`, distributor, done). The pack generator and the
`game-assets` gate are reconciled: `gate_sync_ready --lane game-assets` now returns **PASS,
`mode: pack`** on `packages/welcome-asset-pack`, and the pack's loops are 5.201270 s against the
gate's 2 s floor. See §3 for the live output and for what the old FAIL block said.


## 8. Existing assets for this genre

Measured in this pass: **the render exists, the delivery does not.** There is still no lyric
sheet (none is wanted — instrumental), **still no blueprint**, still no master, still no loop and
still no pack for this genre — but "no audio, no plan" is no longer true, and the difference
matters for the next card.

```
$ cat /var/lib/music-plans/elemental-earth-chamber-loop.json      # 1331 B, written 14:52
{"title":"Megalith Chamber", "caption":"ancient cavern earth theme, 88 BPM, deep didgeridoo
 drone on a low open root, …", "bpm":88, "key":"C minor", "duration":600,
 "timesignature":"4", "language":"en", "lyrics":"[Intro]\n[Instrumental]\n[Instrumental]\n
 [Instrumental Break]\n[Instrumental]\n[Outro]\n", "instrumental":true,
 "authorship":"instrumental — no human-authored portion (AI-Generated Output; not registrable
 with a PRO)", "_meta":{"genre":"elemental-earth","lyrics_mode":"instrumental",
 "blueprint":false, …}}

$ ls -la /var/lib/music-plans/elemental-earth-chamber-loop.rendered
-rw-r--r-- 1 root root 0 Oct 16 14:58 …     ← EMPTY: the render exited 0

$ ffprobe /var/lib/sunolocal/artifacts/suno-83d28d87c4894484afec77877a5819d2.flac
codec_name=flac  sample_rate=48000  channels=2  duration=600.000000  size=53736489
```

So: a **600.000 s stereo render of this genre exists** on the engine's artifact volume, and its
plan carries the three values §7a prescribes (`bpm 88`, `key "C minor"`, `instrumental true`,
6-tag sheet). What does **not** exist is the delivered product — no master on
`/var/lib/music-plans/`, no `loops/*.loop.wav`, no `loop_points.json`, no pack. The reason is
measured and carded: a `loop-10min` render cannot carry a `seamless: true` claim when its tail
collapses in level, and the rail will not certify a loop it did not just build. **Card
`t_d7f6d053` measured this render's tail at a ~40 dB level collapse over the final 1.522 s** (that
number is the card's, not re-measured here); the fire master failed the same ruler at 33.6 dB
(`t_b21aeb51`). The backfill is **card `t_d7f6d053`** (nexus-core, ready) — route A re-renders on
the GPU, route B closes the loop from the existing artifact with no re-render. This brief records
the state; the backfill is that card's job, not the brief's.

```
$ find music/lyrics -maxdepth 2
music/lyrics/blueprints/{activist,anime-ending,anime-opening,chill-lounge,epic-orchestral-boss,
                         jungle-dnb,trance}.yaml        # 7 of 14 genres — earth is NOT one
music/lyrics/activist/what-runs-beneath  music/lyrics/chill-lounge/amber-hour
music/lyrics/trance/signal-before-dawn
$ grep -rl "elemental-earth" --exclude-dir=.git . | wc -l
31
```

The same `grep -rl` returns **31 paths** (it was 20 at 13:53 CDT, 16 brief files then): this
brief, 17 brief files under `music/briefs/` (every brief names every genre in its registry list),
`genres.yaml`, the template, the visual style, the rubric + its test, the planner, the bpm-solution
check, `brain/playbooks/music-lane-architecture.md` (which exists now — see §13), the sunolocal
instrumental check, two loop/planner tests and three `.pyc` artefacts. The claim it supports is
unchanged: **no lyric sheet, no blueprint, no delivered master or loop, no pack** exists for this
genre.

Quota is untouched, measured:

```
$ /usr/bin/python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

The only asset pack in existence is `packages/welcome-asset-pack`, now **in this worktree**, and
it is a **chill-lounge** pack from a 184.57 BPM source (5 loops of 5.201270 s, 12 stems of
51.605011 s) — it is a shape sample, not this genre's product. It **passes** the `game-assets`
gate (§3); it is not a substitute for an earth pack.


## 9. What the gate stage will score (gamer rubric) — the ambiguity is FIXED

`music/rubrics/gamer.json` is **v2**, and sub-idiom scope is now **DATA** (`applies_to` on every
criterion), fixed by card `t_426a82a3` (commit `56dc465`). Re-read in this pass:

| Criterion | Weight | `applies_to` | Applies to elemental-earth? |
|---|---|---|---|
| `chip_timbre_authenticity` | 3 | `["chiptune-8bit"]` | **No** |
| `battle_energy` | 3 | `["elemental-fire","epic-orchestral-boss"]` | **No** |
| `elemental_atmosphere` | 3 | `["elemental-air","elemental-water","elemental-earth"]` | **Yes — this genre's own craft criterion** |
| `loop_safety` | 3 | *(absent — family-common)* | Yes |
| `asset_packaging` | 1 | *(absent — family-common)* | Yes |
| `loudness_target` | 1 | *(absent — family-common)* | Yes |

Pass threshold **7.0** on the geometric-median aggregate of the judges' weighted means. The
applicable set for this genre is four criteria and **Σ w = 8**; the panel scores only those
(`music/rubrics/panel.py:235` `applicable_criteria()`, `:590-593` splits applied/excluded and
records both in `review.json`):

```
elemental-earth  Σw=8  [elemental_atmosphere, loop_safety, asset_packaging, loudness_target]
excluded: chip_timbre_authenticity, battle_energy     (named to the judge, not scored)
```

**What was broken — history, kept as evidence.** Before `56dc465` the rubric carried no
`applies_to`: scope lived only inside the criterion NAME, and the aggregate was summed over the
whole file, `Σ w = 11`. A correct 88 BPM earth theme was therefore scored on
`chip_timbre_authenticity` and on `battle_energy` — whose anchor is "fast tempos 130-200 BPM
(typical 140-180)" with the guide `1 = slow ambient track with a battle label` — and a criterion
a judge left out scored **1.0 (absent)** and was flagged (`panel.py:508-519`). §14 of this brief
computed the margins under that arithmetic; they are superseded, not deleted. The same defect put
a correct 92 BPM elemental-air track at **41/11 = 3.73** against the 7.0 threshold.

**What the margin looks like now.** The two criteria that used to cost this genre points are not
scored at all, and the slow elementals have a craft criterion of their own:
`elemental_atmosphere` (w3), named *"Elemental exploration craft: slow-pocket atmosphere, not a
fight (elemental-air, elemental-water, elemental-earth)"*, anchored on the 70-100 BPM game
exploration pocket and earth's open-fifth drone with an 80-90 BPM heartbeat pulse. The reject
signals are scoped too: `elemental_fight_material` ("elemental-air, elemental-water or
elemental-earth delivered as a fight: drum-kit groove, bass drop, or a 130+ BPM battle claim on an
exploration-theme label") now guards this label, while `battle_no_fast_tempo` applies only to
`elemental-fire` and `epic-orchestral-boss` — so an 88 BPM earth render can no longer be fatally
rejected for not being fast. Verified by the rubric's own suite in this pass:
`/usr/bin/python3 music/rubrics/test_panel_math.py` → **ALL CHECKS PASSED** (rc=0), including the
cases "an inapplicable score a judge volunteers cannot drag the aggregate" and "pre-fix maths
would have failed that track (incident record: 41/11 = 3.73)".

**Still open, and it is the reason the gate stage is not a formality:** the panel must reach
judges. Card `t_3d84acfe` (filed by `t_426a82a3`) measures that both reviewer profiles route to
one provider and the panel currently reaches **zero** reachable judges, so `gate_quality.py` sees
`fail` for every track. That is a reviewer-panel defect, not a rubric one, and it is carded — do
not try to fix it from this brief.


## 10. Stage plan for this genre (skips locked)

| Stage | Bot | What happens here |
|---|---|---|
| brief | producer | this file ✅ |
| genre-select | producer | registry entry already resolved in §1; nothing left to select |
| lyrics | writer | **NOT APPLICABLE — instrumental** (`prompts/elemental-earth.md:15`). The stage must be recorded as not-applicable, not skipped silently. Do not let `planner.py --lyrics-mode ai` write lyrics: it would both contradict the template and void the human-authorship default. |
| generate | producer | `sunolocal /api/v1/generate` with **`bpm: 88`**, **`keyscale: "C minor"`**, `instrumental: true`, the tag sheet as `lyrics` (§7a — the v0.1.3 path; the legacy styleWeight fallback is not used for this genre). The queued plan for this genre already carries exactly those values. Suno CDP (`music/suno-gen.py`) is the alternative route and is present in this worktree now (D4 closed). |
| curate | producer | pick the winner; reject reason per loser. Reject conditions are §2 — electronic drums, defined tonality, rushed tempo, non-loop ending. |
| stems | producer | Studio export; ≥ 4 stems within ±0.5 s of the master. |
| master | producer | `gate_loudness --target streaming` (-14) for the streaming lane; -16 for sync-family. **Ruler state, measured this pass:** the card `t_9546841b` is closed but this checkout's gate still measures `volumedetect` mean volume and says so in its own docstring (`music/gates/gate_loudness.py:2`, `:14-16`); the LUFS-reporting fix of `t_568c67d2` (`music/mix/master.py`, commit `6824709`) is on `origin/publish/audio-lane-2026-10-16` and is **not** an ancestor of `HEAD`, so it is absent from this tree (`find` → no `master.py`). Report the measured number with its ruler name. |
| gate | reviewer-deepseek / panel | `music/rubrics/panel.py --genre elemental-earth` → `review.json`, then `gate_quality`. Four criteria, Σw = 8 — see §9. Note the panel reachability defect (`t_3d84acfe`). |
| package | producer/distributor | build the pack in the layout `gate_sync_ready --lane game-assets` reads — that gate **PASSes** on a pack now (§3, D5 closed) — and ship loop points that pass **both** `gate_loop_points` rulers (`--pack-dir`). The earth loop itself is the open item: card `t_d7f6d053` closes the loop from the existing 600 s render. |

| visual | videobot | `loop-10min` chamber render + `gate_youtube_authentic` (≥ 10 distinct frames, Jaccard ≤ 0.85, disclosure). |
| human-approval | — | j_kro. Nothing publishes without it. |
| publish | publishbot | upload **private/draft only**; itch.io via `butler` (`brain/runbooks/music-game-assets.md`). No public release without the human gate. |

## 11. What the sibling cards mean for this genre (statuses re-read live)

Read from the board this pass (`sqlite3 -readonly …/boards/music/kanban.db`), not from memory:

- **This card `t_8fa97d4e` is `running`** and is the only open card for `elemental-earth`.
  `music/scripts/check_oracle_board.py` → **PASS**: 9 open oracle cards across 9 genres, exactly
  one each, `elemental-earth → t_8fa97d4e [running]`.
- **Both superseded twins are `done`:** `t_55e37b88` (7.5 — wrote this brief) and `t_c92f566d`
  (7.7 — ran the §14 pass). Neither wrote a second brief and neither started a second stage chain;
  briefs here are keyed by genre.
- **Every handoff this brief filed is now `done`:** `t_25a6499c` (instrumental mode / bpm / key),
  `t_8a715681` (checkout reconciliation), `t_5ed495eb` (pack ↔ gate), `t_909069f0` (queue this
  track), `t_9546841b` (loudness ruler), `t_b0a4db92` (`brain/` docs), `t_426a82a3` (rubric scope),
  `t_bf0e5edd` (oracle dedupe). Nothing this brief filed is still open — the open items below are
  newer cards, filed by other workers.
- **Two live follow-ups touch this genre.** `t_1a5b018b` (music-producer, ready) was filed by
  `t_426a82a3` to reconcile the pre-fix rubric scope in three briefs — elemental-water §8,
  elemental-air §10 and **elemental-earth §9/§14**. **§9 is reconciled in this pass** (§9 above
  carries the measurement); the card's earth leg can be marked satisfied, and only the water and
  air legs remain. `t_d7f6d053` (nexus-core, ready) owns the loop backfill for this genre's 600 s
  render (§8).
- **The dedupe guard holds.** `music/oracle.py` refuses to open a second card for a genre that
  already has one in flight and the fetch-failure premium is gone (`check_oracle_determinism`
  PASS; `b2d11f7`), so the 2026-10-09 double emission should not recur.


## 12. Handoffs — every one this brief filed is now DONE

Re-read live this pass (board DB). Nothing in this list is open, and this pass files **no new
card**: the two live follow-ups that touch the genre already exist (§11).

- **`t_25a6499c`** (nexus-core) — **done.** bpm hardcoded / `key` = the caption / no instrumental
  field in the queue. Shipped as engine tag v0.1.3; measured in §7a (explicit `bpm`/`keyscale`
  win, `--lyrics-mode instrumental` exists).
- **`t_8a715681`** (nexus-core) — **done.** Reconciled the diverged checkout (merge `ab33ad1`).
  Measured at `c296db6` (2026-10-16 15:56 CDT): `main` is 72 ahead / 0 behind
  `origin/main` (`ba28f55`), and the missing paths are in the worktree (§7c D4).
- **`t_5ed495eb`** (distributor) — **done.** The asset-pack ↔ `game-assets` gate mismatch:
  `gate_sync_ready --lane game-assets` returns PASS `mode: pack` (§3, §7c D5). It unblocked the
  primary lane of all six gamer genres, not just this one.
- **`t_909069f0`** (nexus-core) — **done.** Queued this track into the live generation path.
  Delivered: the queue entry and the 600 s plan with `bpm 88`, `key "C minor"`, `instrumental
  true` (§7b, §8) — and, on the way, the planner's 420 → 600 s cap raise, whose code comment
  cites this genre's own measurement (§4).
- **`t_1a5b018b`** (music-producer, **open**) — reconcile the pre-fix rubric scope in three
  briefs. The **elemental-earth leg (§9/§14) is done in this pass**; only elemental-water §8 and
  elemental-air §10 remain. A comment on that card records this.
- **`t_d7f6d053`** (nexus-core, **open**) — close the loop for this genre's 600 s render (§8).
  This is the one open item between this genre and a licensable pack; it is not brief work.


## 13. Provenance (re-measured 2026-10-16 16:05 CDT unless stamped otherwise)

- Registry: `music/genres.yaml`, `music/lanes.yaml` — `/usr/bin/python3 music/registry.py validate`
  → OK (14 genres, 10 lanes, 1 stage gate rule)
- Lanes/gates: `music/lanes.yaml`, `music/gates/` — `gate_sync_ready` run live on the sample pack
  in **both** layouts (`--lane game-assets` → PASS `mode: pack`; per-track package → the two
  layout findings), `gate_loop_points` run live three ways (span FAIL, level FAIL, `--pack-dir`
  PASS over 5 loops), `gate_quota` PASS
- Quota: `music/quota-ledger.json` + `gate_quota` → 0/60, studio 0
- Engine: `mining/sunolocal` deployment **v0.1.3** — `/health`, `/api/v1/models`, the live
  `openapi.json` (19 properties, `bpm` + `keyscale` present) and `translate.py` read from inside
  the running pod; the variant probe (A–G) executed in-pod against the deployed module
- Queue: CronJobs `music-pipeline` (`17 */6 * * *`) / `music-pipeline-render` (`41 */4 * * *`),
  both unsuspended; ConfigMaps `music-pipeline-briefs` (11 entries) and `music-pipeline-payload`
  (39 keys); `/var/lib/music-plans/` on nexus (13 plans + markers, 1 master, 1 loop);
  `/var/lib/sunolocal/artifacts/` (this genre's 600 s render)
- Rubric: `music/rubrics/gamer.json` v2 (`applies_to`) + `music/rubrics/panel.py`,
  `music/rubrics/test_panel_math.py`, `music/gates/gate_quality.py`
- Skills/rubric rule: `brain/runbooks/music-game-assets.md` — **present in this worktree**
  (4371 B)
- **Repo state at this pass:** HEAD `c296db6` (2026-10-16 15:56:54 CDT), divergence
  **72 ahead / 0 behind** `origin/main` (`ba28f55`). The 72-commit publish gap is the lane's
  standing pattern (local `main` only). Every path the brief stage recorded as missing —
  `music/suno-gen.py` (42652 B), `music/sunolocal/`, `music/assets/pack.py`,
  `packages/welcome-asset-pack` — is now in the worktree.
- **The dangling-reference bullet is closed.** `brain/playbooks/music-lane-architecture.md`
  and `brain/research/music-monetization-2026.md` (11067 B) both exist in this worktree
  now (card `t_b0a4db92`, done). The architecture playbook documents `music-lane-architecture.md`
  §5/§13 as a rubric source, so the section numbers this brief quotes from it are checkable at
  last — but a full re-read of that playbook is not this pass's job and is not claimed here.
- **Checks run on the committed content** (§16): `check_brief_figures`, `check_brief_drift`,
  `check_brief_line_refs`, `check_brief_paths`, `check_stage_scripts`,
  `check_prompt_style_counts`, `check_brief_bpm_solutions`, `check_brief_absences`,
  `check_oracle_board`, `check_oracle_determinism` — see §16 for the rc of each, run after the
  edit.


## 14. Verification pass (card `t_c92f566d`, 2026-10-16)

The duplicate card did not write a second brief. It re-measured this one against live state and
corrected what had drifted. Everything below was run again; only the deltas are listed.

**Held up as written.** `registry.py validate` → `registry OK: 14 genres, 10 lanes`; ledger
period 2026-10, 0/60, warn 55, hard 58; `gate_quota` 0/60, studio 0. Template 3643 B, caption
**487** chars, theme 88 BPM, Weirdness 35 %, Style Influence 80 %, 6 exclude terms (leading space
included), 6 tag-sheet sections in the order quoted, and the instrumental marker on
`prompts/elemental-earth.md:15` with **8 of 14** templates carrying it — all four `loop-10min`
genres among them (`video_shape` re-read for all four elementals). Visual style 1088 B. Bar math
exact: 88 BPM → bar 2.727273 s, 420 s = 154.000 bars, 480 s = 176.000, 600 s = 220.000, 4 bars =
10.909 s, 5 bars = 13.636 s. `planner.py:82-83` `MIN_DURATION_S = 30` / `MAX_DURATION_S = 420`;
`planner.py:528` `--lyrics-mode choices=["draft","ai"]`, no `--instrumental`. `packages/welcome-asset-pack`
extracted from `origin/main` (`83cd0ce`) → `gate_sync_ready --lane game-assets` **FAIL, the same 12
findings verbatim**; 5 loops / 12 stems / 8 one-shots / 6 SFX; `gate_loop_points` on the 1.3 s loop
**FAIL** (span), on the 51.605 s stem **PASS, curvature 0.24×, RMS 0.02570** — byte-for-byte the
quoted output. Live rail re-read: svc `sunolocal` ClusterIP `10.43.164.190:8123`, image
`localhost/sunolocal:v0.1.2`, `/health` ok, `/api/v1/models` as quoted, CronJobs `17 */6 * * *` and
`41 */4 * * *` both unsuspended, briefs ConfigMap still the one `smoke-chill-lounge` entry, payload
ConfigMap still 14 prompts + 6 blueprints + planner + `acestep_plan.py` and **no** gates (blueprint count re-measured 2026-10-16 15:31 CDT: 38 keys, 6 of them blueprints).
`openapi.json`: `/api/v1/generate` has **17 properties and no `bpm`, no `key`** — so `translate.py`
owns the tempo, which is what makes §7a C matter. `/var/lib/music-plans/` as quoted. No
`upload_index.json` anywhere in the repo; no `music/lyrics/**` and no pack for this genre.

**Corrections (this revision).**

1. **§5 / §7a C+E / §10 / §12 — the `styleWeight` value was wrong by one BPM.** 0.2333 was
   derived algebraically and never executed. In-pod, deployed v0.1.2: `0.2333 → 87`,
   `0.2334 → 88`, `0.23334 → 88`; the accepting interval is `[0.233333.., 0.241666..)`, and the
   algebra's own endpoint truncates to 87. Corrected to **0.2334** everywhere, including the
   child card's parameter list. Regression check added:
   `music/scripts/check_brief_bpm_solutions.py` (§14.1).
2. **§3 — `loop_points.json` must declare `"seamless": true`** (`gate_loop_points.py:189`). The
   two seam runs quoted here reproduce only with that key; the abbreviated document shown in the
   command comment fails with a third finding.
3. **§7b — "nothing has rendered on this route" was false.** The wrapper writes an empty marker
   on `rc=0` and `refused` on `rc=1`, so `final-round` **did render**; two plans were refused.
   The revision also miscounted three plans as two.
4. **§9 — the panel's arithmetic is over all five criteria (`Σ w = 11`), with no applicability
   filter**, and an omitted criterion scores 1.0. The tabulated margin figures hold only if
   `chip_timbre_authenticity` scores 10; at 1 the margin collapses (7.55 razor → 5.91 with
   `battle_energy` 4). Numbers added. **Cited, not duplicated:** `t_426a82a3` (editor) owns the
   `battle_energy` scope question — and its body states "weights sum to 8", which `panel.py`
   contradicts; a comment carries the measurement rather than an edit to another card's artefact.
5. **§8 / §11 / §13 census.** The `elemental-earth` grep now returns 20 paths, the card statuses
   moved (this card and the air/fire twins `running`, water `ready`), HEAD is `940c210` and the
   divergence is **15 behind / 26 ahead** at `940c210` (13:43); the overall pair reads 0 behind / 61 ahead of `origin/main` at `e40c7f9` (15:31), because the reconciliation merge `ab33ad1` (14:23) cleared the 15-commit upstream deficit.
6. **§7a D-note — the in-pod `translate.py` docstring lists nine templates while claiming eight.**
   It names `epic-orchestral-boss` among the instrumental eight; the measured census is 8 of 14
   and that genre is **not** in it. Same class as the note in the epic-orchestral-boss brief; the
   comment is the deployed module's, so it is recorded here and not filed again.

**Not corrected, because it is not drift.** The card's own score table (quota 10.0, lane 6.0,
revenue 8.0, cadence 6.7, policy 9.0) reproduces under `music/oracle.py` only with the ledger
arithmetic of **2026-10-09**, when the two oracle cards were created ten minutes apart —
`t_55e37b88` at 03:27:50 CDT and `t_c92f566d` at 03:37:50 CDT, the duplicate-card incident, not
this run (`created_at` read from the board).
`cadence_fit_score("2/wk")` is date-dependent: it returns **6.6667** on 2026-10-09 and **3.3333**
today, so a re-score today gives elemental-earth **7.0** (trend 3.0) or **7.2** (trend 5.0) —
still above the 5.0 produce threshold, so the decision to produce is unchanged either way.
`oracle.py` computes the total as `round(Σ score·weight, 2)` over the six components; the 7.5 and
7.7 on the two cards differ only in `trend_signal` (3.0 = zero search snippets, vs 5.0 = the
search raised, which the function scores 5.0).

### 14.1 Regression check (FAILURE → TEST)

`music/scripts/check_brief_bpm_solutions.py` — recomputes, for every `music/briefs/**/*.md`
claim that pairs a `styleWeight` value with the BPM it buys (or with the `(NNN-60)/120` solve
form), what the **deployed rule** `int(60 + w·120)` actually returns against that genre's anchor
in its own template caption. It failed on the pre-correction revision with exactly three
findings, all in this brief (`:242`, `:324`, `:335`), and passes across the other 6 claims in the
tree — so it is signal, not noise. Run:

```
$ /usr/bin/python3 music/scripts/check_brief_bpm_solutions.py
PASS check_brief_bpm_solutions: 9 styleWeight claim(s) across 14 brief(s) buy the BPM they state
```

It deliberately does not check every `style_weight` in a brief: a brief may quote the template's
own Style Influence as the counter-example it is (elemental-fire's `0.80 → 156 BPM`), and that
number is supposed to miss the anchor.

## 15. Aged live counts re-measured (card `t_0f7aed63`, 2026-10-16)

`music/scripts/check_brief_drift.py` (added by card `t_b7dd5655`) flagged the §14 divergence as
aged. The same pass re-measured the blueprint census this brief cites in §7b and §14, which had
also moved, and read the deployed payload back from the cluster.

- **Superseded revision of this file:** `sha256 b3a31d2a2bb46f6ab392f9005d5ac1787da559dc9c7c4cd3d81ebb9a5d3f0baf` (679 lines / 41686 B).
- **Clone divergence:** the pair §14 records holds at `940c210` (13:43) — 15 behind / 26 ahead of
  `origin/main`. At `e40c7f9` (15:31) the pair reads 0 behind / 61 ahead: the 15-commit upstream
  deficit was cleared by the reconciliation merge `ab33ad1` (14:23). A divergence count is
  stamped with the revision it was measured at, because it ages in minutes.
- **Blueprint census:** 7 of the 14 genres carry a lyric blueprint (`activist`, `anime-ending`,
  `anime-opening`, `chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`, `trance`); the other 7 do
  not. Measured through the registry loader plus the `music/lyrics/blueprints/*.yaml` glob. The
  2026-10-16 15:31 pass behind this section measured the census at six, and it was 3 when this
  brief was written; what landed since is `music/lyrics/blueprints/jungle-dnb.yaml` (card
  `t_e6d422ec`). `elemental-earth` still has none, so §8's "nothing exists for elemental-earth"
  stands.
- **Deployed payload, re-read 2026-10-16 15:31 CDT from `music-pipeline-payload`:** 38 keys —
  6 blueprints, 15 prompt entries (the 14 genre templates plus `anisong-genre-blocks.yaml`),
  14 visuals, `genres.yaml`, the planner and `acestep_plan.py`. Still no gates, still no
  `music/lyrics/` sheets. §7b and §14 said "three blueprints", which was true when measured.
- **Corrected in place:** §7b (the payload's blueprint count), §14 (correction 5's divergence and
  the payload sentence).
- **Superseded by this pass (card `t_e6d422ec`, 2026-10-16):** `sha256 55e049c8ef45d1af0772847a755838d589417292da83aa094b59b03f3026c9c2` (703 lines / 43754 B) — the census bullet above was restated as a live claim when `music/lyrics/blueprints/jungle-dnb.yaml` landed. No genre finding was reopened.

## 16. Surviving-card pass (card `t_8fa97d4e`, 2026-10-16) — every claim re-measured

This card is the genre's surviving OPEN oracle card after the 2026-10-09 double emission
(`t_55e37b88` and `t_c92f566d`, both `done`). Briefs are keyed by genre, so all three cards
resolve to this file: **no second brief was written, no second stage chain was started, and the
brief stage was not re-run.** This section records the pass: the oracle ruling reproduced live,
the corrections made in place, and the checks that were run after the edit.

### 16.1 The oracle ruling, reproduced live

`oracle.score_genre()` called under the registry's own loader (script `probe_oracle.py` of this
pass), with the live trend fetch timing out:

```
scores : quota_headroom 10.0, lane_coverage 6.0, revenue_potential 8.0,
         cadence_fit 3.333333333333333, policy_risk 9.0, trend_signal 3.0
total  : 7.0     lanes: game-assets, youtube-gaming, streaming     cadence: 2/wk
cadence_fit_score("2/wk") today: 3.3333    TREND_NO_SIGNAL: 3.0    WEIGHTS sum: 1.0
```

The card title's **7.2 is not reproducible** and the ruling's **7.0 is**. §14's arithmetic still
explains all three numbers: `cadence_fit_score` is date-dependent (**6.6667** on 2026-10-09, when
the twin cards were created ten minutes apart; **3.3333** today) and `trend_signal` is 3.0 (the
floor — a failed fetch and an empty success both score it that way since `b2d11f7`) or 5.0. The
produce decision is unchanged either way, and `check_oracle_board` confirms this card is the
genre's only open one.

### 16.2 Corrections in place (each measured in this pass)

| # | Section | Was (brief stage) | Is (measured) |
|---|---|---|---|
| 1 | header | card `t_55e37b88`, score 7.5, supersession `0e9bf0de…` | surviving card `t_8fa97d4e`, true score **7.0** (live re-score), superseded blob `036395fe…` recorded |
| 2 | §1 | registry transcript short of the stage-gate rule | live transcript + `gate-for-stage` resolution for this genre |
| 3 | §3 | `gate_sync_ready` FAIL, 12 findings, lane "not passable" | **PASS `mode: pack`** (`t_5ed495eb` closed); pack loops **5.201270 s** not 1.3 s; 7 one-shots not 8 |
| 4 | §3 | seam PASS on a 51.605 s stem (curvature only) | the gate now has **three** rulers; that stem FAILs the level ruler at 34.2 dB, `--pack-dir` PASSes all 5 loops |
| 5 | §4 | planner refuses > 420 s, so the queue cannot express `loop-10min` | cap is **600 s** (`planner.py:103-104`), raised because of this genre's own measurement; the entry exists |
| 6 | §5, §7a | anchor reachable only via `styleWeight 0.2334`; `key` = the caption | engine **v0.1.3**: explicit `bpm`/`keyscale` win; variants A–G re-measured in-pod |
| 7 | §7b | briefs ConfigMap = 1 entry; no `--lyrics-mode instrumental`; payload 38 keys | 11 entries including this genre; `instrumental` is a mode; payload 39 keys; earth plan exists, marker 0 B (rc=0) |
| 8 | §7c | D1–D5 open or filed | all five **closed**, each with the card/commit that closed it |
| 9 | §8 | "no lyric sheet, no blueprint, no audio, no plan, no pack" | plan exists (1331 B), a **600.000 s render exists** on the artifact volume; no delivered master/loop/pack (card `t_d7f6d053`) |
| 10 | §9 | rubric scores all five criteria, Σw = 11, the chip criterion the live hazard | v2 scope: earth scores **4** criteria, **Σw = 8**, `elemental_atmosphere` is its craft criterion |
| 11 | §10 | generate via `styleWeight`; the loudness ruler card open | generate via `bpm`/`keyscale`; ruler card closed but this checkout's gate still measures `volumedetect` |
| 12 | §11, §12 | handoffs `ready` / `todo` | every handoff filed by this brief is **done**; the two open follow-ups named |
| 13 | §13 | dangling `brain/` references; `suno-gen.py` only on `origin/main` | both `brain/` docs present; all paths in the worktree; at `c296db6`: **72 ahead / 0 behind** `origin/main` |

### 16.3 Checks after the edit

Run against the worktree after this pass's edits landed. `rc` and the summary line of each:

```
check_brief_paths          rc=0  PASS every cited checkout path resolves
check_stage_scripts        rc=0  PASS 11 referenced script path(s) all present
check_prompt_style_counts  rc=0  PASS 15 declared style-field length(s) match their blocks
check_oracle_determinism   rc=0  PASS trend fetch failure never outscores an empty success …
check_oracle_board         rc=0  PASS every one of the 7 open oracle genre(s) carries exactly
                                 one open card (elemental-earth → t_8fa97d4e)
check_brief_figures        rc=1  FAIL 3 of 117 recomputed figure(s) — none in this brief
check_brief_drift          rc=1  FAIL 3 stale count(s)            — none in this brief
check_brief_line_refs      rc=1  FAIL 2 of 119 cited line range(s) — none in this brief
check_brief_absences       rc=1  FAIL 10 absence claim(s)          — none in this brief
check_brief_bpm_solutions  rc=0  PASS 6 styleWeight claim(s) buy the BPM they state
```

**This brief carries zero findings in all four failing checks** (each was re-run filtered on
`elemental-earth` — no output). The findings those runs print belong to sibling briefs that other
workers are editing concurrently at the time of writing: `music/briefs/elemental-water.md:600` and
`anime-opening.md:605` (stale figures, carded `t_34f496d7`), `chiptune-8bit.md:847-848` (a stale
divergence, this lane's known moving-count class), `anime-opening.md:606`, `chiptune-8bit.md:834`
and `elemental-fire.md:620` (line refs), and absence claims in `activist.md`, `chiptune-8bit.md`
and `jungle-dnb.md` — all of them the "says a path is absent that exists now" class this genre's
§7c D4 was also in, and all carded. Two of this brief's own pre-existing findings were fixed in
this pass: `check_brief_line_refs` no longer flags the §9 citation range (rewritten against the
live `music/rubrics/panel.py` lines) and `check_brief_absences` no longer flags the §7c D4 quote
that named `music/suno-gen.py`.

### 16.4 Open items — all carded, none filed by this pass

- `t_d7f6d053` (nexus-core, ready) — deliver the loop for this genre's 600 s render (§8).
- `t_1a5b018b` (music-producer, ready) — the rubric-scope reconciliation; the **earth leg is
  done in this pass**, water and air remain.
- `t_3d84acfe` — the reviewer panel reaches zero judges, so `gate_quality` fails every track
  (a panel defect, filed by `t_426a82a3`).
- **The publish gap is not a defect:** the lane's local `main` is 72 commits ahead of
  `origin/main` (`ba28f55`) and nothing in this lane is pushed; that is the standing pattern for
  this lane, and no card claims otherwise.

Hotspot note for the orchestrator: `music/briefs/*.md` is being edited by many concurrent workers
(this pass touched `music/briefs/elemental-earth.md` only; `t_1a5b018b` also plans to touch
`elemental-water.md` and `elemental-air/above-the-weather/brief.md`).

---

## 17. Supersession record — the pack-key pass (card `t_4906bc6e`, 2026-10-16 17:57 CDT)

§13's "Repo state at this pass" bullet stated the generator's size as a LIVE figure (52690 B).
Card `t_4906bc6e` — the pack's key is measured or explicitly unknown, never fabricated — grew the
generator, and `check_brief_figures` recomputes a size claim, so the bullet now carries none: a
live file's size ages (§14). §19 records the next pass on that same file (card `t_5f814f2f`). The
14:50 `ls -l` transcript in the same section is left alone: it records what the file measured at
that instant, and history is not a live claim.

Superseded revision of this file: `sha256
e26c416b407862d63c52d94e743c462df3647862d2ad615dfeb6945ae74f3776` (1031 lines / 67737 B).

## 18. Declared scoring scope — machine-checked against the live rubric (card `t_00ac4f10`, 2026-10-16)

`music/scripts/check_brief_rubric_scope.py` reads the `rubric_scope` block below and
compares it, field by field, to this genre's scope COMPUTED from `music/rubrics/gamer.json`
by the panel's own resolver (`music/rubrics/panel.py`: `applicable_criteria()`,
`applicable_signals()`). It FAILs when the criterion set, the weights, the weight sum, the
applicable reject signals or the rubric version disagree with the live file. The block is a
claim about NOW; the prose above keeps this family's pre-fix record (gamer v1: five
criteria, Σw 11, scope only inside a criterion NAME) and the check never reads prose, so
that record keeps passing.

Regenerate the block after any rubric edit — one command, no hand-edit:

    /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --print-truth elemental-earth

```json
{
  "rubric_scope": {
    "genre": "elemental-earth",
    "family": "gamer",
    "rubric_version": 2,
    "pass_threshold": 7.0,
    "criteria": [
      "elemental_atmosphere",
      "loop_safety",
      "asset_packaging",
      "loudness_target"
    ],
    "weights": {
      "elemental_atmosphere": 3,
      "loop_safety": 3,
      "asset_packaging": 1,
      "loudness_target": 1
    },
    "weight_sum": 8,
    "reject_signals": [
      "elemental_fight_material",
      "loop_fade_or_truncation",
      "clipped_master",
      "no_stated_tempo_key"
    ],
    "reject_signals_unnamed": 0
  }
}
```

---

## 19. Supersession record — the pack manifest-path pass (card `t_5f814f2f`, 2026-10-16 18:25 CDT)

`music/assets/pack.py` changed again. The generator resolved a pack asset's manifest `file` field
against `music/` while the field itself is relative to the PACK TREE ROOT (`out_dir.parent.parent`
— the repository root for every pack the lane writes), so the lookup never resolved and a silent
`.exists()` guard hid the miss. Measured on the committed pack, 2026-10-16 (nexus):

    music/packages/welcome-asset-pack/stems/02_drums.wav   -> exists=False   # the base the reader used
    packages/welcome-asset-pack/stems/02_drums.wav         -> exists=True    # the base the writer used

`file` now has ONE definition: `manifest_file()` writes it, `resolve_manifest_file()` inverts it
and RAISES on a miss, and the one-shots are cut from the declared stem (`declared_drum_bus()`)
instead of a second `hpss()` computed in `main()`. Measured effect on one 30 s master, before and
after: the only bus-derived one-shot (a kick) moved by at most 4 int16 LSB, 0.012% of full scale;
the four synthesised one-shots are byte-identical.

The `music/assets/pack.py` size figures §13 and §17 carried are DROPPED, not restated: the file is
live, so any size ages (§14). Regression check: `music/scripts/check_pack_manifest_paths.py`
(1 control + 10 failure shapes, and an out-of-tree build of the real generator), wired into
`scripts/automation/weekly-review.sh`.

Superseded revision of this file: `sha256
8ec7a9ac79c2ae615925e1674116772d84a0e8aae15b01bb901f2af27d607e12` (1090 lines / 69994 B) — the
content this pass started from. The commit that lands these hunks replaces the blob carried by
`ad6cfbe` (the rubric-scope pass, card `t_00ac4f10`), whose §18 is untouched: the diff is this
§19, one dropped figure in §13, and the §17 restatement above.
