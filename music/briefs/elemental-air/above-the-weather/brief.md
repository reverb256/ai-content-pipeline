# Brief — elemental-air: "Above The Weather"

Card: kanban `music` **t_dd248457** (surviving card; the genre's first card was `t_92a09bdc`)
· stage: `brief` · assignee: `music-producer`
Oracle score: **7.0/10**, reproduced 2026-10-16 16:07 CDT under `music/oracle.py` (`b2d11f7`). The three card
titles for this genre carry 7.2 (this card), 7.5 (`t_92a09bdc`) and 7.7 (`t_3cb6e654`) — none is
reproducible: each came from a run whose trend fetch failed, and the old `except` branch paid the
failure a +0.20 premium (`WEIGHTS['trend_signal'] x (5.0 - 3.0)`). Card `t_92a09bdc` was created
2026-10-09 03:27:49 CDT (epoch 1791534469; the first revision of this header said 03:27:46 — a
3-second rendering error, corrected 2026-10-16 13:45 CDT by the duplicate pass, `t_3cb6e654`).
`t_dd248457` is the second wave's 03:37:49 CDT card.
Brief written: 2026-10-16 (CDT) · track slug: `above-the-weather`
Repo: `/home/j_kro/ai-content-pipeline` — local `main` @ `c296db6`, **72 ahead / 0 behind
`origin/main`** (`ba28f55`), measured 2026-10-16 16:07 CDT by this surviving-card pass (`t_dd248457`). The
15-commit upstream deficit that the first two revisions of this header recorded is gone (card
`t_8a715681`, `done`); the ahead count moves as this lane commits briefs on the same tree.
(Write-time reading: `ade6e87`, 7 ahead / 15 behind. Duplicate-pass reading: `7f0b3cc`, 24 ahead
/ 15 behind.)

Superseded revisions of this file:
- before the duplicate pass of 2026-10-16 13:45 CDT — `sha256
  ba6fbbf8f13d81a61f8cd7e58cfe47e8bf657169c48865991728953b2ea85cfd`;
- before this surviving-card pass of 2026-10-16 16:07 CDT — `sha256
  7c2c790faf648932f24e383824cc03014e55d388a466b79c721a8ad87d26e93f`;
- before the figure re-measurement pass of 2026-10-16 17:21 CDT (card `t_6dd13d76`) — `sha256
  0487c2c8feee739099055ecc4819ea8cc10c5ed6096598903dbac64b76ccf370`; §7's plan reading was
  refreshed against the live file under `/var/lib/music-plans/`, which the rail rewrites on
  every planning pass, so that figure is a reading at a time, not a constant.

`brief.json` superseded: `sha256 de3ec94ee74d93a786b2f7d9e19a4e25f3c7fa1ebd6047cd5dfd67a5daf67c09`
(before the duplicate pass,
`sha256 8bfd6c7195525308877e0e98fad1ef02a57fa7ec08da1ec1585d10b7f4a84ad7`). The duplicate pass
corrected three figures (§7 instrumental-count attribution, §11 O4 licence-file location, this
header's card-creation time) and re-measured the branch divergence. This pass corrects every
stale claim listed in the table at §15.

Briefs in this lane are keyed by **GENRE**, not by card. Three oracle cards exist for this genre,
one per wave — `t_92a09bdc` (7.5) and `t_3cb6e654` (7.7), both `done`, and `t_dd248457` (7.2, this
card, the surviving open card). All three resolve to **this** brief. Do not produce it twice.
Both twins closed at the brief stage: no second brief written, no second stage chain started.

Every number below comes from a command run during this stage. Nothing is transcribed
from another brief.

---

## 1. Resolved registry entry (live, not copied)

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
| Lyric blueprint | **none** — `music/lyrics/blueprints/` holds 7 files as of 2026-10-16 16:07 CDT (`activist.yaml`, `anime-ending.yaml`, `anime-opening.yaml`, `chill-lounge.yaml`, `epic-orchestral-boss.yaml`, `jungle-dnb.yaml`, `trance.yaml`). None of them is `elemental-air`, so the tempo comes from the caption, as below. |
| Registry note | *(no note block on this genre; `elemental-fire` carries the family note "Boss/battle theme. Target indie devs + gaming music channels." — re-read verbatim 2026-10-16 16:07 CDT)* |

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

### A fourth surface also exists in this checkout now

`music/assets/pack.py` (card `t_4906bc6e`; its size is not restated here — the file is live, so a live figure ages, §14) and its executable gate `scripts/gates/gate_asset_pack.py`
(2981 B) are both present in this checkout at 2026-10-16 16:07 CDT — the "upstream-only" reading the first two
revisions of this brief carried is stale (card `t_5ed495eb`, `done`). The sample pack is here
too: `packages/welcome-asset-pack/` (manifest.json, loops/, one_shots/, LICENCE.txt,
clearance_doc.pdf, ai_disclosure.txt). The gate's own required counts, read from the source:
**loops 5, stems 12, one_shots 5**, and every loop's measured seam must clear
`CLICK_FREE_THRESHOLD_DBFS = -60.0`. So the game-assets package shape for this track can be
built from this tree. What the tree still lacks is a stage that builds it (card `t_eb079b91`).

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

The lane's guard rail is `MIN_DURATION_S = 16` (`music/planner/planner.py:147`) and
`MAX_DURATION_S = 600` (`:148`). The cap was 420 when this brief was written and was raised to
600 for the `loop-10min` shape (**anchored**); the floor moved 30 -> 16 when card `t_96dfc521`
made it the shortest shape the registry names (re-read 2026-10-16 by card `t_ae1d9243`). The
wire format takes an integer
(`SunoGenerateRequest.duration: Optional[int]`), so the plan value is **334**.

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

Two documentation defects surfaced in this census. Only one of them is still live.

- The **deployed** translator's list is now correct. `/opt/sunolocal/music/sunolocal/translate.py`
  (line 29, read inside pod `sunolocal-source-75d58dbc97-7jfmc`, image `localhost/sunolocal:v0.1.3`,
  2026-10-16 16:07 CDT) says **"8 of the 14 genre templates are instrumental"** and names exactly eight:
  `chill-lounge, chiptune-8bit, commentary-beds, elemental-air, elemental-earth, elemental-fire,
  elemental-water, sentimental-piano`. Its own comment records the fix: "The previous list here
  named NINE by wrongly including epic-orchestral-boss ... (card t_25a6499c)". The earlier
  revisions of this brief reported the opposite; that reading was true of image v0.1.2 and is not
  true now.
- `music/suno-gen.py` (line 184) still says **"8 of the 12 genre templates"** and still repeats
  `epic-orchestral-boss` in the same sentence. Both numbers are wrong. Re-measured 2026-10-16 16:07 CDT: the file
  is now in THIS checkout (`music/suno-gen.py`, 42652 B), not `origin/main`-only as the earlier
  revisions said.

Census re-measured by this pass over the `## Lyrics guidance` section of `music/prompts/*.md`:
8 of 14 genres are instrumental, and `epic-orchestral-boss` is not one of them.

### Engine A (live now): sunolocal → ACE-Step

```
$ kubectl get pods -n mining | grep -E "sunolocal|comfy"
sunolocal-source-75d58dbc97-7jfmc     1/1  Running  1 (54m ago)  87m
comfyui-zephyr-599b69bb7c-fhjs9       1/1  Running  0           2d3h

$ kubectl get svc -n mining sunolocal        # ClusterIP 10.43.164.190, port 8123
$ kubectl get deploy -n mining sunolocal-source -o jsonpath='{..image}'
localhost/sunolocal:v0.1.3

$ curl -s http://10.43.164.190:8123/health
{"status":"ok"}

$ curl -s http://10.43.164.190:8123/api/v1/models
{"engines":{"ace":{"kind":"ACE-Step 1.5","via":"acestep_plan.py -> comfyui-zephyr window"},
            "yue2":{"kind":"YuE2-3B","via":"yue2-zephyr http"}},"default":"ace"}
```

Live routes on the running pod: `GET /health`, `GET /api/v1/models`,
`POST /api/v1/generate`, `GET /api/v1/task/{task_id}`, `GET /api/v1/audio?path=…`.
`POST /api/v1/lyrics`, `/stems`, `/extend` and `/cover` are still **`_deferred` stubs** — they
answer but do not work (`/opt/sunolocal/music/sunolocal/studio.py`, lines 155-179, read inside the
pod; the same stubs sit at `music/sunolocal/studio.py` lines 148-172 here). **Stems cannot come
from this service.**

Request shape (Suno camelCase; read from the deployed `sunolocal/spec.py`):
`prompt`, `style`, `lyrics`, `title`, `instrumental`, `model`, `customMode`,
`negativeTags`, `vocalGender`, `duration` (int seconds), `styleWeight`,
`weirdnessConstraint`, `audioWeight`, `variety`, `callbackUrl`, `seed`, **`bpm`** (int),
**`keyscale`** (string), `engine` (`ace|yue2|fixture`). The two bold fields are new in v0.1.3
(card `t_25a6499c`) — see the D1/D2 table below.

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

### Two defects that WERE live in the deployed translator, and are fixed in v0.1.3

Read from `/opt/sunolocal/music/sunolocal/translate.py` **inside the running pod**
(`localhost/sunolocal:v0.1.3`, 2026-10-16 16:07 CDT):

| # | Defect | Deployed code at v0.1.2 | Deployed code at v0.1.3 (now) |
|---|---|---|---|
| D1 | **BPM was not expressible.** The 92 BPM anchor could not be honoured. | `bpm = 120`; then `bpm = int(60 + req.style_weight * 120)` if `styleWeight` is set. Reaching 92 needed `styleWeight ≈ 0.2667`. | `if req.bpm is not None: bpm = int(req.bpm)` — an explicit tempo wins; the `styleWeight` mapping is a documented fallback only. |
| D2 | **The key field received the whole style caption.** | `key = req.style or "C major"` — the ACE `keyscale` was handed a 494-character paragraph. | `key = req.keyscale or "C major"` — an explicit key wins; `req.style` is never read. |

Both fixes cite card `t_25a6499c` in the code's own comments, and the pod's `spec.py` now
declares `bpm: Optional[int]` and `keyscale: Optional[str]`. The queue entry for this track
carries `bpm: 92` and `keyscale: C major`; the plan on disk carries them too (§9).

**The in-genre tempo no longer needs the 0.2667 workaround.** The `styleWeight ≈ 0.2667` value
the first two revisions of this brief prescribed is obsolete for the live engine. Send
`bpm: 92`.

**One drift remains, and it is a checkout drift, not a pod drift.** This repo's mirror
`music/sunolocal/translate.py` is still the v0.1.2 text: it has no `req.bpm` branch, it sets
`key = req.style or "C major"`, and `music/sunolocal/spec.py` carries no `bpm` or `keyscale`
field. The pod is built from the chart payload
`mining-k8s/helm/charts/sunolocal/files/music/sunolocal/translate.py` (commit `a80ab4e`) —
`mining-k8s` is a second checkout, at `/home/j_kro/mining-k8s`, not a directory inside this
repo. Read the pod, not the repo mirror.

### The checkout CAN run the generate stage (defect resolved 2026-10-16)

`music/stages.yaml` tells the generate stage to generate "via Suno CDP
(`music/suno-gen.py`)". The first two revisions of this brief recorded that this file was not in
this checkout. Re-measured 2026-10-16 16:07 CDT:

```
$ ls -la music/suno-gen.py
-rw-r--r-- 1 j_kro j_kro 42652 Oct 16 14:23 music/suno-gen.py
$ git rev-list --left-right --count main...origin/main
72      0        # 72 ahead / 0 behind, on local tip c296db6; origin/main is ba28f55
```

The branch reconciliation landed (card `t_8a715681`, `done`): the local lineage is no longer
behind `origin/main`, and `music/suno-gen.py` (with its `is_instrumental_template()` at line
141), `music/sunolocal/`, `music/assets/pack.py` and `scripts/gates/gate_asset_pack.py` are all
present here.

### A one-line doc/code mismatch in the streaming gate

`music/gates/gate_release_ready.py` docstring says the ISRC "must match the ISRC syntax
CC-XXX-YY-NNNNN and **pass the ISRC check digit (ISO 3901)**". The code in the same file
enforces `^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$` — **12 characters, no check digit** (IFPI
Bulletin 2015/01: an ISRC has no check digit). The regex is right; the docstring is wrong
and will send a human looking for a check digit that the standard does not define.

---

## 8. What "instrumental" means for each remaining stage

| Stage | Consequence |
|---|---|
| `lyrics` | **Not applicable.** The stage prompt already anticipates this: "an instrumental genre … skips this stage — advance it with a comment saying the genre is instrumental." No sheet, no `gate_lyrics_original` run, no authorship claim to register with SOCAN for this track. |
| `generate` | Requires a **track dir with `title.txt`** and, because `--instrumental` is passed, a marker: `"instrumental": true` in the track dir's `manifest.json`, or an empty file named `instrumental`. Code-enforced, with a FATAL message that says exactly this. The lyrics box is sent **empty**; the caption gets `, instrumental, no vocals` appended by the translator. |
| `curate` | Critical for this genre, because D1 (120 BPM default) and out-of-genre drift into percussion are both audible. Reject on: any drum kit, any bass weight, a resolved cadence, a hard/faded ending. |
| `stems` | Export through **Suno Studio** (unlimited) — never the standard download button (60/month cap). The local service's `/api/v1/stems` is a deferred stub. `music/assets/pack.py` (now in this checkout) derives 12 time-aligned stems by HPSS (scipy) as the asset-pack path (card `t_5ed495eb`, `done`). |
| `master` | −14 LUFS ±1 for streaming. **Careful:** the `gate_loudness` in THIS checkout still measures `ffmpeg volumedetect` mean_volume (plain RMS), not LUFS. Card `t_9546841b` is `done` and its decision was to move the ruler to EBU R128 integrated loudness, but that commit (`e783a96`) sits on `origin/publish/audio-lane-2026-10-16` and is not on `main`; `music/mix/master.py` (card `t_568c67d2`) is on that branch only and is not in this checkout at all. So a gate FAIL here is not by itself evidence of a bad master. Measure both. |
| `gate` | `gate_quality` requires a `review.json` whose `reviewer_model` differs from the producer model and which is sha256-bound to this master. The panel rubric for this family is `music/rubrics/gamer.json` (pass threshold 7.0). |
| `package` | `loop_points.json` + `clearance_doc.pdf` + `ai_disclosure.txt` are required for game-assets; `gate_release_ready` adds an ISRC, artwork (PIL-openable), and manifest `{title, artist, isrc, genre, ai_disclosure}` for streaming. Artwork is j_kro's creative gate — do not fabricate a cover. |
| `visual` | `loop-10min`, 600 s, dawn/noon/high-wind rotation per upload, `gate_youtube_authentic` (≥10 distinct frames, Jaccard ≤ 0.85, disclosure). |
| `human-approval` | j_kro. `gate_human_approval` has no `--force`/`--auto-approve` flag by design. Uploads stay private/draft. |

---

## 9. Existing assets and quota (measured)

**Assets: no audio yet, and the first plan now exists.** No `music/lyrics/elemental-air/`
directory, no master, no stems, no render. The generation rail has planned this track:
`/var/lib/music-plans/elemental-air-above-the-weather.json` (re-planned 2026-10-16 16:57 CDT)
carries `bpm: 92`, `key: "C major"`, `duration: 334`, `instrumental: true` and the template's six
section tags in the lyrics field. Beside it sits
`elemental-air-above-the-weather.rendered` (0 B, 15:00 CDT) and **no audio file** — the render
rail reports the entry "already rendered" and produces nothing (card `t_69cab80b`, `ready`).

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

## 10. Rubric note — the sub-idiom scope is now DATA

`music/rubrics/gamer.json` supplies the judging panel for the family. The question the earlier
revisions of this brief raised as F2 is closed. Since commit `56dc465` (card `t_426a82a3`,
`done`) every criterion carries an `applies_to` field, and `music/rubrics/panel.py` scores a
criterion only for the genres it names. `battle_energy` (weight 3) carries
`applies_to: ["elemental-fire", "epic-orchestral-boss"]` — **it does not score this genre at
all.** The floor case that criterion's guide prescribed ("1 = slow ambient track with a battle
label") can no longer touch a 92 BPM suspension theme.

`elemental-air` scores four criteria. Their weights sum to 8:

| Criterion | Weight | Type | Scope | What it measures here |
|---|---|---|---|---|
| `elemental_atmosphere` | 3 | craft | `["elemental-air", "elemental-water", "elemental-earth"]` | in-pocket 70-100 BPM (or a half/double that folds in), a steady level (`rms_1s_spread_db`), the element's signature device claimed in the caption (air: sus2 harmony / no kit), `pct_energy_above_8khz` shimmer |
| `loop_safety` | 3 | measured | all | bar math + tail/head RMS within ~6 dB + no fade-to-silence on a loop claim |
| `asset_packaging` | 1 | craft | all | stated BPM/key + stems + loop-point marker |
| `loudness_target` | 1 | measured | all | mean_volume_db vs -14 for the streaming lane |

`chip_timbre_authenticity` (weight 3) is `applies_to: ["chiptune-8bit"]` and does not apply.
`pass_threshold` is 7.0. The reject signal that now names this genre is
`elemental_fight_material` — "elemental-air, elemental-water or elemental-earth delivered as a
fight: drum-kit groove, bass drop, or a 130+ BPM battle claim on an exploration-theme label
(= OUT of genre, the element is wrong)" — together with the family-wide
`loop_fade_or_truncation`, `clipped_master` and `no_stated_tempo_key`. The rubric's
`elemental_atmosphere` guide is the criterion this track must answer: air's signature device is
sus2 harmony with no percussion kit.

**What was broken — the pre-fix record, kept as evidence (incident card `t_426a82a3`).** Read back
with `git show 56dc465^:music/rubrics/gamer.json`, version 1 of the family's rubric carried five
criteria and no `applies_to` field at all:

| v1 criterion | Weight | Scope as that file wrote it |
|---|---|---|
| `chip_timbre_authenticity` | 3 | name suffix `(chiptune-8bit only)` |
| `battle_energy` | 3 | name `Boss/battle energy (elemental-*, epic-orchestral-boss)` |
| `loop_safety` | 3 | name suffix `(all gamer genres)` |
| `asset_packaging` | 1 | none |
| `loudness_target` | 1 | none |

**Σw = 11**, and the panel scored all five on every gamer genre. `panel.py` had no scope code path,
so the earlier revision of this section was WRONG when it asserted that the panel already honoured
the name-level scope: the scope sat in the criterion NAME and nothing read it. Both w3 hazards hit
this genre at once, and a criterion a judge left out scored **1.0 (absent)** and was flagged
(`music/rubrics/panel.py:508-519`). The reject signal *"boss/battle claim with no fast-tempo
candidate (under 130 BPM)"* was family-common, so it fired on a correct 82 BPM water theme — the
fatal path, worse than the lost points.

The measured consequence, kept as the incident record: a correct 92 BPM `elemental-air` track
scored **41/11 = 3.73** against the 7.0 threshold — asserted by
`music/rubrics/test_panel_math.py:235-249` (`abs(aggregate - 41 / 11) < 0.01`). Two figures must
not be misread:

- The claim *"criterion weights sum to 8"* (card `t_426a82a3`'s own body) was never true of the
  pre-fix file. Its Σw was 11. **8 is the FIXED file's figure, and only per genre** — the result
  of the new scoping, not a property of the old file.
- **41/11** is pre-fix arithmetic. Under v2 this genre is scored on Σw = 8, so the threshold
  maths is **≥56 weighted points (7.0 × 8)**, not 41/11.

---

## 11. Open items

Seven of the eight items this section carried are now closed by other cards. Each entry below
states the live measurement, the card that closed it, and what remains.

- **O1 — Engine defects D1/D2. CLOSED** (card `t_25a6499c`, `done`; pod image
  `localhost/sunolocal:v0.1.3`, 2026-10-16 16:0x CDT). An explicit `bpm` and `keyscale` now win
  in the deployed translator, and the pod's `spec.py` declares both fields (§7). What the brief
  asked for as a workaround (`styleWeight ≈ 0.2667`) is obsolete: send `bpm: 92`. The queue
  entry and the plan on disk both do exactly that (§9).
- **O2 — Branch divergence. CLOSED** (card `t_8a715681`, `done`). Local `main` @ `c296db6` is
  72 ahead / 0 behind `origin/main` (`ba28f55`), measured 2026-10-16 16:0x CDT; `music/suno-gen.py`
  is present here (42652 B). **Partial residue:** the CM fix for the loudness ruler
  (card `t_9546841b`, `done`) and `music/mix/master.py` (card `t_568c67d2`, `done`) live on
  `origin/publish/audio-lane-2026-10-16` only, 5 commits this branch does not carry. The
  generate stage is unaffected; the master stage is.
- **O3 — Video/loop alignment. OPEN.** 334 s is not an exact divisor of the 600 s `loop-10min`
  shape (1.80 plays). The visual stage must seam at the track's verified loop point
  (`gate_loop_points`), not at a simple repeat boundary. If the videobot cannot seam audio,
  revisit the duration (**115 bars = 300.000 s**, exactly 2 plays). Related live defect found
  since: a delivered loop of 4 bars cannot tile a 600 s video at all (card `t_b75ccb4a`).
- **O4 — Clearance doc and licence tiers. HALF CLOSED.** The licence of record exists in this
  checkout at `music/licences/perpetual_game_asset_v1.txt` (1615 B, added by commit `c0bd386`,
  card `t_5ed495eb`), and the sample pack ships it as `packages/welcome-asset-pack/LICENCE.txt`.
  Two residues: the file is still absent from `origin/main` (measured: `git cat-file -e
  origin/main:music/licences/perpetual_game_asset_v1.txt` fails), so the upstream README's
  pointer to it still dangles there; and the README promises "multi-tier (personal / commercial
  / exclusive)" while the file grants one perpetual non-exclusive licence with no tier block.
  `clearance_doc.pdf` now exists for the sample pack
  (`packages/welcome-asset-pack/clearance_doc.pdf`, 2061 B); none exists for this track yet.
- **O5 — Asset pack machinery. CLOSED** (card `t_5ed495eb`, `done`). `music/assets/pack.py`
  (54971 B) and `scripts/gates/gate_asset_pack.py` (2981 B) are in this checkout (§3). The open
  residue is a different one: no stage builds a pack (card `t_eb079b91`, `ready`).
- **O6 — Brief cards never advance. CLOSED** (card `t_5a93164a`, `done`). `music/stages.yaml`
  now tells the stage to post the marker with the `kanban_comment` tool and to treat
  `advance-stage.sh` exit 1 as a failed advance; the script's own header records that a
  dispatcher-spawned worker's CLI is fenced and names the tool call instead. This card's own
  resolution comment ends `stage: genre-select` — the advance the earlier revisions could not
  perform.
- **O7 — Duplicate oracle card. CLOSED.** Three cards exist for this genre (one per wave):
  `t_92a09bdc` (7.5) and `t_3cb6e654` (7.7), both `done` at the brief stage with no second brief
  and no second stage chain, and `t_dd248457` (7.2), the surviving open card that ran this pass.
  The dedupe guard landed locally in `ade6e87`; `music/scripts/check_oracle_board.py` reports
  one open card per genre (rc 0, measured 2026-10-16 16:0x CDT).
- **F2 — Rubric/genre mismatch. CLOSED** (card `t_426a82a3`, `done`; commit `56dc465`).
  Sub-idiom scope is DATA now: `applies_to` decides which criterion scores which genre, and
  `elemental-air` no longer takes a 1 on `battle_energy`. It scores the new
  `elemental_atmosphere` criterion instead (§10).

---

## 12. Handoffs

| Card | Profile | Status measured 2026-10-16 16:0x CDT | What this brief contributes |
|---|---|---|---|
| `t_25a6499c` | nexus-core | `done` | The 92 BPM / `styleWeight` 0.2667 numbers. Closed: the pod now takes an explicit `bpm` and `keyscale`. |
| `t_8a715681` | nexus-core | `done` | The measured 7/15 → 24/15 → 72/0 divergence counts and the missing paths. Closed: `music/suno-gen.py` is here. |
| `t_5ed495eb` | distributor | `done` | The asset-pack ↔ game-assets gate mismatch. Closed: the pack generator, the gate and the licence are in this checkout. |
| `t_b8afb055` | nexus-core | `done` | The elementaire render parameters — instrumental true, engine `ace`, duration 334, `bpm` 92, `keyscale` C major. Delivered as the `elemental-air-above-the-weather` queue entry in `mining-k8s/helm/charts/music-pipeline/values.yaml`. |
| `t_5a93164a` | nexus-core | `done` | The silent no-op in `advance-stage.sh`. Closed: the stage prompt now names the `kanban_comment` tool. |
| `t_426a82a3` | editor | `done` | The `battle_energy` scope finding (F2). Closed: `applies_to` is data and `elemental_atmosphere` now covers this genre. |
| `t_69cab80b` | nexus-core | `ready` | New, from this pass: the `.rendered` marker makes a refused or empty render permanent (§9). |
| `t_eb079b91` | music-producer | `ready` | New, from this pass: nothing in the pipeline builds an asset pack (§3, §11 O5). |

---

## 13. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` — `music/registry.py validate` → rc 0.
- Gates read and quoted from source: `music/gates/gate_sync_ready.py`, `gate_loop_points.py`,
  `gate_youtube_authentic.py`, `gate_release_ready.py`, `gate_quality.py`,
  `gate_stems_present.py`, `gate_human_approval.py`, `gate_quota.py`.
- Templates: `music/prompts/elemental-air.md` (494-char caption measured),
  `music/visuals/element-air.md`.
- Rubric: `music/rubrics/gamer.json` **v2** (`applies_to` scope is data; 6 criteria, family total
  weight 14 — this genre's scored set, the pre-fix record and the arithmetic are in §10).
- Stage contract: `music/stages.yaml` (`brief` → bot `producer`).
- Live engine: cluster `mining` — `kubectl` reads of `sunolocal-source-75d58dbc97-7jfmc`
  (image `localhost/sunolocal:v0.1.3`, 1/1 Running), `/health`, `/api/v1/models`, and the
  deployed `translate.py` / `spec.py` / `studio.py` read **inside the pod**; `yue2-zephyr` 0/0,
  endpoints `<none>`, health code 000. (Write-time reading, superseded 2026-10-16 16:07 CDT: pod
  `sunolocal-source-65fcc845d-fd5r6`, image `localhost/sunolocal:v0.1.2`.)
- Upstream reads (`git show origin/main:…`): `music/suno-gen.py`, `music/sunolocal/translate.py`,
  `music/sunolocal/checks/g9_instrumental.sh`, `music/assets/pack.py`,
  `scripts/gates/gate_asset_pack.py`, `packages/welcome-asset-pack/README.md`,
  `music/docs/fusion-system-design.md`.
- Board: `kanban` `music` — card + duplicate read from a read-only snapshot of
  `~/.hermes/kanban/boards/music/kanban.db`.
- **Duplicate-card pass, 2026-10-16 13:45 CDT (`t_3cb6e654`) — re-measured, not re-read.**
  `music/registry.py validate` (rc 0, 14 genres / 10 lanes); `music/gates/gate_quota.py`
  (rc 0, 0/60); `git rev-list --left-right --count main...origin/main` (24/15 @ `7f0b3cc`);
  `music/scripts/check_stage_scripts.py` (rc 1, unchanged); `ffprobe
  music/visuals/loop_10min.mp4` (600.000000 s, 1280×720, video+audio) and
  `music/visuals/element_air.mp4` (5.000000 s); caption char count 494; `music/visuals/element-air.md`
  read in full; `music/rubrics/gamer.json` read (weights 3/3/3/1/1, `pass_threshold` 7.0,
  reject-signal strings); gate sources re-read (`gate_sync_ready` `MIN_STEMS=4` /
  `STEM_TOLERANCE_S=0.5` / `REQUIRED_META`; `gate_loop_points` `CLICK_RATIO_MAX=3.0`, span ≥ 2.0 s;
  `gate_youtube_authentic` cadence 2.0 / 10 frames / 0.85, `DISCLOSURE_NAMES`;
  `gate_release_ready` `ISRC_RE`, `ARTWORK_NAMES`, `REQUIRED_META`; `music/planner/planner.py`
  30/420). Live engine re-read: `mining/sunolocal-source` 1/1 Running, image
  `localhost/sunolocal:v0.1.2`, `GET /health` → `{"status":"ok"}`, `GET /api/v1/models` → the
  `ace`/`yue2` block quoted in §7, pod-local `translate.py` line 29 (`8 of the 14`) and the four
  `_deferred` stubs in `studio.py`; `yue2-zephyr` 0/0, endpoints `<none>`, health code 000.
  Upstream re-reads: `git cat-file -e origin/main:music/licences/perpetual_game_asset_v1.txt`
  → absent; `git log --all --source -1 -- music/licences/perpetual_game_asset_v1.txt` →
  `origin/wip/atlas-backup-20261014`; `origin/main:music/suno-gen.py:184`;
  `origin/main:scripts/gates/gate_asset_pack.py` (`loops` 5 / `stems` 12 / `one_shots` 5,
  `CLICK_FREE_THRESHOLD_DBFS` −60.0); `origin/main:packages/welcome-asset-pack/README.md`
  (184.57 BPM / C major / 44100 Hz / 16-bit). Two corrections and one re-measurement came out
  of it — §7 and §11 O4, plus the header divergence line.
- **Dangling references (RESOLVED 2026-10-16 16:07 CDT).** `brain/playbooks/music-lane-architecture.md` and
  `brain/research/music-monetization-2026.md` are cited as authoritative by `stages.yaml`,
  `genres.yaml`, `lanes.yaml`, `autonomy.yaml`, `gates/README.md` and every gate script. The
  earlier revisions of this brief recorded that neither existed on this machine. Both are on
  disk and in `HEAD` now: `brain/playbooks/music-lane-architecture.md` and
  `brain/research/music-monetization-2026.md` (11067 B). Card `t_b0a4db92` is `done`, and card
  `t_fa731c5b` stripped the same old reading from the sibling briefs; the playbook was rewritten
  at `7411afa` (head touching it `6b24a52`). Every §-number this brief quotes is still quoted
  from the gate or template that states it.

## 14. Next stage

Stage `brief` is complete and this card advances to `genre-select`. The advance is performed by
this card's own resolution comment, which ends with the marker `stage: genre-select` — the
`kanban_comment` route that `music/stages.yaml` names since card `t_5a93164a` closed (§11 O6).
The production path for this track is the queue entry `elemental-air-above-the-weather`, which
is live in `mining-k8s/helm/charts/music-pipeline/values.yaml` and planned on disk (§9).

## 15. Surviving-card pass — 2026-10-16 16:07 CDT (card `t_dd248457`)

The oracle ruling of 2026-10-16 names `t_dd248457` the surviving card for `elemental-air` and
scores the genre **7.0/10**, not the 7.2 in this card's title. The brief stage's artifact
already existed (briefs are keyed by genre), so this pass wrote no second brief and started no
second stage chain. It re-measured every checkable claim in this file and corrected the ones
that had aged. The superseded revision is recorded in the header.

### The score, reproduced three ways

`oracle.score_genre("elemental-air", ...)` under the registry's own loader, 2026-10-16 16:07 CDT, with the
network call stubbed three different ways:

| Call | warning emitted | trend_signal | total |
|---|---|---|---|
| live fetch (timed out) | "trend fetch failed for elemental-air" | 3.0 | **7.0** |
| fetch stubbed to 200-with-0-snippets | none | 3.0 | **7.0** |
| fetch stubbed to raise `OSError` | "trend fetch failed for elemental-air (OSError)" | 3.0 | **7.0** |

The three calls agree, which is the whole point of the fix in `b2d11f7`: a broken fetch and an
empty success now score the same floor.

Components: quota_headroom 10.0, lane_coverage 6.0, revenue_potential 8.0, cadence_fit
3.3333, policy_risk 9.0, trend_signal 3.0; `WEIGHTS` closes at 1.0. The same run scored all 14
genres 6.5 (jungle-dnb) to 8.4 (chill-lounge, sentimental-piano), so the correction moves no
genre across the 6.0 produce line. The card's own breakdown table shows trend_signal 5.0 — the
broken-fetch premium — which is the entire 0.20 gap.

### Corrections made by this pass

| # | Where | Was | Is (measured 2026-10-16 16:07 CDT) |
|---|---|---|---|
| 1 | header | card `t_92a09bdc`, score 7.5 | surviving card `t_dd248457`, true score 7.0 reproduced; the three title scores named and their non-reproducibility explained |
| 2 | header | `main` 24 ahead / 15 behind @ `7f0b3cc` | `main` @ `c296db6`, 72 ahead / 0 behind `origin/main` (`ba28f55`) |
| 3 | §1 | registry prints "14 genres, 10 lanes" | prints "14 genres, 10 lanes, 1 stage gate rule(s)" plus the `visual` stage-gate line |
| 4 | §1 | blueprints hold "only activist, chill-lounge, trance" | 7 files, listed |
| 5 | §3 | pack.py and gate_asset_pack.py are upstream-only, "cannot be built from this tree today" | both in this checkout (52690 B / 2981 B), with the sample pack |
| 6 | §5 | `MAX_DURATION_S = 420` (**anchored**) | 600 — the constant is at `planner.py:148` now, not `:103-104` (card `t_ae1d9243`) |
| 7 | §7 | the deployed translator "names nine" | v0.1.3 names exactly eight and records the fix |
| 8 | §7 | suno-gen.py:184 is an `origin/main`-only file | it is in this checkout (42652 B) and the wrong string is still at line 184 |
| 9 | §7 | Engine A runs image v0.1.2 on pod `sunolocal-source-65fcc845d-fd5r6` | image v0.1.3 on pod `sunolocal-source-75d58dbc97-7jfmc` |
| 10 | §7 | request shape has no tempo/key fields | `bpm` and `keyscale` are declared in the pod's `spec.py` |
| 11 | §7 | D1/D2 "STILL LIVE" | both fixed in the deployed v0.1.3; the repo mirror is the stale copy |
| 12 | §7 | the checkout cannot run the generate stage | `music/suno-gen.py` present, `main` 72/0 |
| 13 | §8 | pack.py not in this checkout; loudness ruler defect open under `t_9546841b` | pack.py present; `t_9546841b` is `done` but its commit is on `origin/publish/audio-lane-2026-10-16`, so this checkout still measures volumedetect |
| 14 | §9 | no render of any kind exists | plan (1557 B) + a 0 B `.rendered` marker exist; no audio |
| 15 | §10 | `battle_energy` is id-scoped to all `elemental-*` and scores this genre 1 (F2) | sub-idiom scope is data; `battle_energy` excludes this genre; new `elemental_atmosphere` (w 3) binds it |
| 16 | §11 | O1, O2, O5, O6, O7, F2 open | all closed, each with its card; O4 half closed with two residues; a new residue recorded for O2 (the audio-lane branch) |
| 17 | §12 | six handoff cards `ready` | all six `done`; two new `ready` cards from this pass |
| 18 | §13 | both `brain/` documents "do not exist" | both on disk and in `HEAD` |

### Checks after the edit (all quoted from real runs, 2026-10-16 16:09 CDT)

| Check | rc | elemental-air |
|---|---|---|
| `check_brief_figures` | 1 | no finding — its one stale figure is in `elemental-water.md` |
| `check_brief_drift` | 0 | PASS (15 live counts across 14 briefs) |
| `check_brief_line_refs` | 1 | no finding — its three are in `chiptune-8bit.md` and `elemental-fire.md` |
| `check_brief_paths` | 0 | PASS (22 citations, no ambiguity warning) |
| `check_brief_absences` | 1 | no finding — its ten are in `activist.md`, `chiptune-8bit.md`, `jungle-dnb.md` |
| `check_stage_scripts` | 0 | PASS (11/11) |
| `check_prompt_style_counts` | 0 | PASS |
| `check_oracle_board` | 0 | PASS (one open card per genre) |
| `check_oracle_determinism` | 0 | PASS |
| `check_doc_refs` | 0 | PASS |

The repo-wide FAILs are all in **other** briefs, and the sibling passes own them:
`t_bdb94fb7` and `t_aac32db8` (the stale absence claims), `t_fa731c5b` (the playbook class),
`t_6dd13d76` (the stale figure and the line citations), `t_e86c2110` (the `genres.yaml` range),
`t_c5a98379` (the drift shapes).

### Rubric-history reconciliation — card `t_1a5b018b` (2026-10-16 16:47 CDT)

Card `t_1a5b018b` (filed by `t_426a82a3`) named three brief sections that quoted the pre-fix gamer
scope. State of each leg, re-measured this pass:

| Leg | State measured 2026-10-16 16:47 CDT | Evidence |
|---|---|---|
| `elemental-water.md` §8 | already reconciled | commit `7d3d440` (that genre's surviving-card pass, card `t_354d5d25`) |
| `elemental-earth.md` §9/§14 | already reconciled | commit `fb612c4` (that genre's surviving-card pass, card `t_8fa97d4e`) |
| this file §10 | reconciled by the 16:07 pass; the pre-fix RECORD was still missing | commit `2dac605` rewrote §10 against v2; this pass added the history the card asked to keep |

Work this pass did, measured against `music/rubrics/gamer.json` v2 and
`git show 56dc465^:music/rubrics/gamer.json` v1:

- §10 gained the pre-fix record: v1 carried five criteria, **Σw = 11**, no `applies_to`, the scope
  only in the criterion NAME, and a criterion a judge left out recorded as 1.0 by the panel
  (`music/rubrics/panel.py:508-519`); plus the incident
  arithmetic **41/11 = 3.73** (`music/rubrics/test_panel_math.py:235-249` asserts `41 / 11`).
- §13's rubric pointer named a v1-shaped criterion set with no `applies_to`; it now names the v2
  data (6 criteria, family total weight 14) and points at §10.
- `elemental-water.md` §8 said the pre-fix scope lived in "the criterion's `scope` string". v1
  carried no `scope` field, so it lived in the criterion `name`. Corrected in place.

Checks after the edits (real runs, 2026-10-16 16:47 CDT):

| Check | rc | This work |
|---|---|---|
| `check_brief_drift` | 0 | PASS (14 counts across 14 briefs) |
| `check_brief_line_refs` | 0 | PASS — the new `test_panel_math.py:235-249` and `panel.py:508-519` citations hold |
| `check_brief_paths` | 0 | PASS |
| `check_stage_scripts` | 0 | PASS (16 paths) |
| `check_prompt_style_counts` | 0 | PASS (15 lengths) |
| `check_oracle_board` | 0 | PASS (0 open oracle genres) |
| `music/rubrics/test_panel_math.py` | 0 | ALL CHECKS PASSED |
| `check_brief_figures` | 1 | no finding in this file from this pass — its remaining one was §13's `34,328 B` (`6b24a52`), owned by `t_f7889dd6` / `t_fa731c5b` |
| `check_brief_absences` | 1 | no finding in this file — its two name `elemental-water.md` §14 and the closing pass note, owned by `t_bdb94fb7` |

This pass did NOT edit the rubric (`music/rubrics/*` belongs to the review panel, `editor`) and did
NOT touch the two pre-existing check failures above, which have owners.

Re-run note (16:48-16:50 CDT): the shared tree kept moving under these runs, and neither movement is
this file. `check_brief_drift` raised `registry.RegistryError` for the stage `asset-pack` named in
`music/lanes.yaml`, because that file and `music/registry.py` carried another worker's uncommitted
edits at that moment (card `t_eb079b91`, the asset-pack stage). And `check_brief_line_refs` moved
from rc 0 to rc 1, on three ranges in OTHER briefs (`activist.md`, `commentary-beds.md`,
`elemental-fire.md`) — the class card `t_6dd13d76` owns. Nothing in this file regressed; re-run
`check_brief_line_refs` and the count of findings in this file is still zero.

---

## 16. Supersession record — the pack-key pass (card `t_4906bc6e`, 2026-10-16 17:57 CDT)

This pass changed three LIVE figures in this file and nothing else. `music/assets/pack.py` moved
from **52690 B** to **54971 B** when card `t_4906bc6e` removed the fabricated short-input key from
`estimate_key()`: the analyser now declares its own window, returns no key below it, and the
generator records an explicit `unknown` instead of `"C minor"`. `check_brief_figures` recomputes
this size, and it flagged three present-tense claims — §3's "A fourth surface" note, §8's `stems`
row and §11's O5 entry. All three are corrected above.

Two sites were left ALONE on purpose, because they are history rather than live claims: §15's
corrections-table row 5, which records what that pass measured at 16:07 CDT, and the 14:50 `ls -l`
transcript in `elemental-earth.md` (the file WAS 52690 B at that instant).

The header's "Superseded revisions of this file" list was deliberately NOT extended: every
citation into this file (`activist.md` and `music/scripts/check_brief_absence.py` both cite the
line at :404) points at a line number, and the correction above was made without moving one.

Superseded revision of this file: `sha256
97ad6977c8ff4637536a4a653934c0357fc071933f098ef5e82a6c12c2174581` (777 lines / 50366 B).

Superseded by the pack manifest-path pass (card `t_5f814f2f`, 2026-10-16 18:25 CDT): `sha256
4fc255fad1cddc2e31fdc66c6a2b85475795bbded9ef8489ef2f4142825ed618` (843 lines / 53268 B) — the
content this pass started from. The commit that lands these hunks replaces the blob carried by
`ad6cfbe` (the rubric-scope pass, card `t_00ac4f10`), whose §17 is untouched: the diff is the two
dropped size figures and this record.

That pass changed `music/assets/pack.py`: the manifest's `file` field has ONE definition
(`manifest_file()` writes it against the pack tree root, `resolve_manifest_file()` inverts it and
RAISES on a miss), and the one-shots are cut from the declared stem instead of a second `hpss()`
computed in `main()`. The two LIVE size figures this brief carried for that file were DROPPED,
not corrected — the file is live, so any size ages (§14). No cited line number moved. Regression
check: `music/scripts/check_pack_manifest_paths.py` (card `t_5f814f2f`).

## 17. Declared scoring scope — machine-checked against the live rubric (card `t_00ac4f10`, 2026-10-16)

`music/scripts/check_brief_rubric_scope.py` reads the `rubric_scope` block below and
compares it, field by field, to this genre's scope COMPUTED from `music/rubrics/gamer.json`
by the panel's own resolver (`music/rubrics/panel.py`: `applicable_criteria()`,
`applicable_signals()`). It FAILs when the criterion set, the weights, the weight sum, the
applicable reject signals or the rubric version disagree with the live file. The block is a
claim about NOW; the prose above keeps this family's pre-fix record (gamer v1: five
criteria, Σw 11, scope only inside a criterion NAME) and the check never reads prose, so
that record keeps passing.

Regenerate the block after any rubric edit — one command, no hand-edit:

    /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --print-truth elemental-air

```json
{
  "rubric_scope": {
    "genre": "elemental-air",
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

## 18. Loop-tiling prose correction (card `t_00d3dbbd`, 2026-10-16)

`music/briefs/elemental-fire.md` §16 locked the loop-tiling contract and the per-genre values
into `music/genres.yaml` (`loop_bars`), `music/scripts/check_loop_tiling.py` (the enforcing
check) and that brief's own prose. This pass corrects the two sites in this brief that still
asserted the old lengths.

| Site | Was | Is |
|---|---|---|
| §4, line 180-181 | "the 600 s video is therefore exactly 230.00 bars — the loop grid and the video length are in register at this tempo" | 230 bars is the **shape** and stays; the **delivered loop** is **46 bars = 120.000 s (5 tiles)**, per the contract of `t_b75ccb4a` |
| §5, line 548-552 | O3 names the 4-bar defect as "a delivered loop of 4 bars cannot tile a 600 s video at all" | unchanged — it is the incident this card's family fixes. The render must still be longer than the loop: the engine emits 1.5–6.2 s of trailing silence inside its requested window, so a loop as long as the render is refused (measured, `t_b75ccb4a`) |

**Superseded revision of this file:** `sha256
d275d9ce4c6691508aded2a920c3575a1a5dd8b034055d6b650f68ee5d1c6a1c` (868 lines /
55304 B) — the content this pass started from. The diff is this §18 and the header supersession
line above.
