# Brief — elemental-fire

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`; on this board the cards
> are assigned `music-producer` and claimed by the generic kanban dispatcher).
> **Card:** t_6f0d261e (`music-oracle: elemental-fire (score 7.5)`)
> **Duplicate card:** t_42a01e18 (`music-oracle: elemental-fire (score 7.7)`) — `ready`,
> created 599 s later by the second oracle wave. It differs in ONE component: trend signal
> 5.0 vs 3.0. Both resolve to THIS brief; the brief is keyed by **genre**, not by card.
> **Written:** 2026-10-16T13:16-05:00 (CDT)
> **Verified (duplicate-card pass, `t_42a01e18`):** 2026-10-16T13:50-05:00 (CDT) — see §13.
> One attribution was corrected (§9: the tail/head dB column belongs to the `loop/` render,
> not to `loop2/`); the loop-gate finding itself reproduced on BOTH renders, and the second
> ruler §9 asks for now exists as `music/scripts/loop_seam_check.py`.
> **Superseded revision of this file (before that pass):**
> `sha256 86436b4b2c2c757756a7644b79907fbebc1872b3f6686d340e771a8e0516ace1` (508 lines).
> `brief.json` superseded: `sha256 ebb875bd2472d0fab0a41766519db7b948bcd03334372fb53245acfe6bcc6013`.
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `d491663` (main) at write time. The working tree
> is shared by 6–7 concurrent brief-stage workers; HEAD moved 5 times while this brief was
> written (the last commits were the sibling elemental briefs `elemental-air`, `sentimental-piano`,
> `commentary-beds`, `anime-opening`). Re-measured by the duplicate-card pass (2026-10-16T13:50
> CDT): `main` @ `fa3163f`, **29 ahead / 15 behind** `origin/main` — the 15-commit upstream
> deficit has not moved all day; the local tip moves every few minutes.
> **Oracle:** 7.5/10 — quota headroom 10.0, **lane coverage 6.0**, revenue 8.0, cadence fit
> 6.7, policy risk 9.0, **trend signal 3.0**. Threshold 5.0 → produce.

## 1. Genre resolution (live, not transcribed)

Resolved from `music/genres.yaml` through the registry loader:

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
shell: `python3` resolves to `~/.hermes/tools/python-3.14.7+…/bin/python3`, which has no
PyYAML. `/usr/bin/python3` (3.14.7) validates cleanly. Use `/usr/bin/python3` in every stage
prompt. (`python3 -c` and heredocs are BLOCKED in an unattended worker shell — write a probe
script to a file and run it.)

Entry from `music/genres.yaml` (lines 86–93):

| Field | Value |
|---|---|
| Genre | `elemental-fire` |
| Family | `gamer` |
| Prompt template | `music/prompts/elemental-fire.md` (4008 B) |
| Visual style | `music/visuals/element-fire.md` (1103 B) |
| Lanes | `game-assets`, `youtube-gaming`, `streaming` |
| Cadence | 2/wk |
| Video shape | `loop-10min` |
| Registry note | "Boss/battle theme. Target indie devs + gaming music channels." |

### The composite score, re-derived (arithmetic checked, not eyeballed)

`music/oracle.py:54` — weights 0.25 / 0.20 / 0.20 / 0.15 / 0.10 / 0.10.
Recomputed from the card's own components: **7.505 → 7.5**, matching the card. Per-component
derivation, each re-executed live against the registry:

| Component | Value | Derivation (all re-run live) |
|---|---|---|
| Quota headroom | 10.0 | `10 × (1 − 0/58)`; `gate_quota` PASS 0/60 |
| Lane coverage | 6.0 | 3 viable lanes, 0 banned → `min(3×2, 10)` = 6 |
| Revenue potential | 8.0 | itch.io 300 + unity-asset-store 300 + gamedev-market 300 + youtube 500 + distributor 200 = 1600 → `min(1600/200, 10)` |
| Cadence fit | 6.7 | 2/wk, 21 days left in period → `(6.0 − 2)/6 × 10` = 6.67 |
| Policy risk | 9.0 | 0 banned surfaces, −1 for `youtube-gaming` |
| Trend signal | 3.0 | DuckDuckGo returns **0** `result__snippet` matches for `"elemental-fire music trend 2026"` |

Two facts fall out of that table and both matter downstream:

1. **`trend_signal` is a network artifact, not a signal.** The function returns **3.0** when
   the fetch succeeds and finds 0 snippets, and **5.0** on an exception
   (`oracle.py:284–289`). The duplicate card scores 5.0 for the same genre and the same day.
   The 7.5-vs-7.7 spread across the duplicate pair is a fetch result, not genre heat. Do not
   read either number as market evidence.
2. **`cadence_fit` decays every day and `quota_headroom` does not.** Cadence fit was 6.67
   when the card was scored (2026-10-09, 21 days left in the period). Re-run **today**
   (2026-10-16, 14 days left) it measures **3.333**, putting the same genre at **7.0**
   (trend 3.0) or 7.2 (trend 5.0). Still above the 5.0 threshold, but the margin is the
   calendar, not the product. The oracle's largest weight (quota headroom 10.0) is a
   constant that only moves when we spend downloads — it will keep padding every genre's
   score until the ledger fills.

## 2. Intent — the product is a game-asset LOOP PACK, not a single track

`game-assets` is the lane that defines this genre's product. Per `music/lanes.yaml` its
surface is `itch.io,unity-asset-store,gamedev-market` and its required artifacts are
`[stems, loop_point, seamless_loop, metadata]`. The buyer is an indie developer who needs a
boss loop they can drop into a level; the YouTube channel is the shop window, not the
product.

What the pack must contain:

| Pack element | Spec |
|---|---|
| Master loop | **120.0 s = 75 bars** at 150 BPM — the full fight arc, seamless |
| Stems | ≥ 4, each within ±0.5 s of the master (ffprobe-measured) |
| `loop_points.json` | `{"loop_start_s": 0.0, "loop_end_s": 120.0, "seamless": true}` |
| Short loops | 32 bars = **51.2 s** and 16 bars = **25.6 s** cutdowns for in-engine use |
| BPM / key | **150 BPM**, **D Phrygian** — stated in the manifest (`asset_packaging`, weight 1) |
| Cover | 3000×3000, palette from `music/visuals/element-fire.md` |
| Video | 600.0 s (loop-10min) = exactly **5 × the 120.0 s master** |

Three things must hold or the generation is out of spec (the template says reject it):

1. **Percussion is the protagonist.** The fight's urgency lives in the taiko/frame-drum
   galloping triplets at 150 BPM. A version that reads as "epic orchestral with drums
   underneath" is the wrong genre — that is `epic-orchestral-boss`.
2. **The low-register string ostinato is the engine**, with braams and brass swells as
   *answers*, not as wallpaper.
3. **Loop discipline is a lane requirement, not a nicety.** The outro must resolve back into
   the intro tension bed. A fade-out ending is a hard reject (`music/rubrics/gamer.json`
   `reject_signals`: "fade-out or truncated ending on a game-loop claim").

## 3. Target lanes and what each one demands

From `music/lanes.yaml`. These are the gates that will actually run.

| Lane | Surface | Gate | Requires |
|---|---|---|---|
| `game-assets` | itch.io, unity-asset-store, gamedev-market | `gate_sync_ready --lane game-assets` **+** `gate_loop_points` | `stems`, `loop_point`, `seamless_loop`, `metadata` |
| `youtube-gaming` | youtube | `gate_youtube_authentic` | edited visual ≥ 640×360, ≥ 10 distinct frames, + disclosure |
| `streaming` | distributor (distrokid; alt tunecore) | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` |

All requirements below were measured by **executing** the gates against an empty package
directory — nothing is inferred from a filename.

`gate_sync_ready --lane game-assets` on an empty package (the requirement list the package
stage must satisfy):

```
FAIL gate_sync_ready
  - full_mix.wav is not a real audio file (ffprobe could not read a duration)
  - no stems/ directory — a sync track without stems is not sync-ready (architecture HARD RULE 4)
  - only 0 stem(s) found; 4 required (drums, bass, keys, vocals, ...)
  - instrumental.wav is not a real audio file (sync needs an instrumental version)
  - no manifest.json
  - no clearance_doc.pdf (or .txt) — sync requires a clearance document
  - no ai_disclosure.txt — the AI role must be declared for sync platforms
  - game-assets lane requires loop_points.json (run gate_loop_points.py for the seam check)
rc=1
```

`gate_release_ready` on the same empty package:

```
FAIL gate_release_ready
  - no master.wav
  - no artwork (one of artwork.jpg, artwork.jpeg, artwork.png)
  - no manifest.json
  - no ai_disclosure.txt
rc=1
```

`gate_stems_present` with no stems: `only 0 stem(s) …; 4 required` (rc=1).

Decisions locked here so no later stage re-litigates them:

- **`instrumental.wav` must be a distinct render, not a copy of the master.**
  `gate_sync_ready` fails an instrumental byte-identical to `full_mix.wav`. This genre is
  already instrumental, so the pack must ship a real variation (e.g. the percussion-light
  smoldering-breakdown stem mix) and name it in the manifest.
- **ISRC: do NOT compute a check digit.** `gate_release_ready`'s docstring claims the gate
  checks "the ISRC check digit (ISO 3901)". It does not — `isrc_syntax()` validates only the
  element rules (12 characters: 2 letters + 3 alphanumeric + 2 digits + 5 digits). That is
  correct: an ISRC has **no check digit** (IFPI International ISRC Agency Bulletin 2015/01
  rev 3, ISO 3901:2019). The docstring overstates the code. Do not fabricate a 13-character
  code and do not "fix" the validator to require a check digit. Verify with the distributor
  card's precedent: `CARVB26` + `5292` + track number.
- **Autonomy rung is `advisory` for all three lanes** (`music/autonomy.yaml`): every publish
  is proposed with evidence and approved by j_kro. Promotion needs 10 clean advisory
  publishes.
- **The streaming lane is the weakest of the three** — see §6.

## 4. Rhythm math and throughput (derived, not assumed)

At the genre's 150 BPM in 4/4, one bar is **exactly 1.60 s**. Measured:

```
bar   = 4 × 60 / 150 = 1.600 s
16 bars  =  25.6 s      32 bars  =  51.2 s
75 bars  = 120.0 s      375 bars = 600.0 s  (the loop-10min video)
```

**Finding — the 10-minute video only tiles cleanly at a specific loop length.**
`video_shape: loop-10min` is a 600.0 s video built by repeating the master loop. The loop
must tile into 600 s an integer number of times, or the video's last seam is a jump cut.
Measured candidates at 150 BPM:

| Loop length | Bars | Tiles into 600 s | Verdict |
|---|---|---|---|
| 51.2 s | 32 | 11.719 | ✗ fractional — seam breaks at the end |
| 89.6 s | 56 | 6.696 | ✗ |
| 102.4 s | 64 | 5.859 | ✗ |
| **120.0 s** | **75** | **5.000** | ✓ **locked** |
| 200.0 s | 125 | 3.000 | ✓ (a longer alternative) |

**Decision: the master loop is 120.0 s (75 bars).** It tiles exactly 5× into the 600 s
video, and 75 bars divides into a seven-section fight arc:

```
[tension intro]      9 bars   14.4 s
[burning theme]     12 bars   19.2 s
[development]       12 bars   19.2 s
[molten peak]       12 bars   19.2 s
[smolder]            9 bars   14.4 s
[full blaze]        12 bars   19.2 s
[loop-safe outro]    9 bars   14.4 s
                   -----      ------
                   75 bars  120.0 s   ← matches the template's 7-tag sheet
```

`MAX_DURATION_S` in `music/planner/planner.py` is **420 s**, so 120 s is inside the guard
rail with room to spare — but note that 600.0 s is **not**, which is why the 10-minute
artifact is a video, never a single render.

Throughput: cadence 2/wk = **2 pack-grade generations per week**, each needing its own stems,
loop points, short loops and cover. At `advisory` rung nothing publishes without j_kro, so
the binding constraint is generation + packaging labour, not quota.

Export policy: exports go through **Suno Studio** (unlimited), never the standard download
button (60/month cap). Run `gate_quota` before every export; the standard meter is 0/60 today
(measured). Two separate meters exist — Suno's Download dialog meters *download credits*
(1/song, format-independent) while `music/quota-ledger.json` tracks the 60/month standard
counter and Studio exports. Record both.

## 5. Audio identity (locked for this genre)

Style field, verbatim from the template — **583/1000 chars, measured**:

```
fire elemental boss battle theme, 150 BPM, driving taiko and frame-drum percussion with galloping triplets, aggressive staccato string ostinato in the low register, low brass swells and braams answering the strings, cracking rhythmic fire-crackle texture layer, shredding modal melody on horns or erhu, minor key with flat-2 Phrygian color, phrased as a fight: tension intro, burning theme, molten peak, brief smoldering breakdown, full blaze reprise, loop-safe ending that resolves back to the opening tension, seamless game loop, high energy throughout, cinematic hybrid orchestral
```

Settings (from the template): **Weirdness 40 %**, **Style Influence 80 %**.
Exclude Styles: `pop vocals, EDM drop, trap, happy major key, ambient drone, lo-fi`.
The "happy major key" exclusion matters: fire reads as danger and drive, not picnic.

Lyrics: **empty box, always** — Suno's instrumental path. Structure comes from metatags only
(`[Intro]`, `[Instrumental]`, `[Break]`, `[Outro]` + parenthetical direction, never singable
words). A wordless low choir "ahh" is acceptable as texture.

Key and tempo for the plan: **150 BPM, D Phrygian** (D minor with the flat-2 — the modal
signature that separates a fire theme from generic epic minor).

### ⚠ Style Influence 80 % collides with the 150 BPM spec on the current engine

The template's own number is the problem. Executed against the deployed
`sunolocal/translate.py` (read from `origin/main`, the deployed path — see §7):

```
42:    bpm = 120
45:        bpm = int(60 + req.style_weight * 120)
```

The style-adherence dial is doing double duty as a tempo control. Consequences, computed:

| Path | Resulting BPM | vs the 150 spec |
|---|---|---|
| `style_weight` unset | 120 | −20 % |
| `style_weight = 0.80` (the template's own setting) | **156** | +4 % — 1 bar = 1.538 s, not 1.600 s |
| `style_weight = 0.75` (the only value that yields 150) | 150 | ✓ but contradicts the template's stated 80 % |
| local `planner.py` fallback, no blueprint | **100** | −33 % — 1 bar = 2.400 s |

So through the current engine **there is no setting of the dial that both honours the
template's 80 % style adherence and produces 150 BPM.** The genre also has no
`music/lyrics/blueprints/elemental-fire.yaml` (only `activist`, `chill-lounge`, `trance`
have one), so the local planner falls back to **100 BPM** —
`music/planner/planner.py` ~line 470, `"bpm": ctx["blueprint"].get("bpm_anchor") or 100`.
At 100 BPM a bar is 2.400 s, so the 120.0 s master would be 50 bars and the whole §4
structure above is wrong. **Acceptance for this genre: the plan's `bpm` field must read
150, never 100, 120 or 156.**

## 6. Rights — this genre has NO registrable human-authorship portion

Measured against `music/docs/pro-registration.md` §1 and §3:

- SOCAN accepts **AI-Assisted Works** ("substantial human input … generative AI as a tool")
  and rejects **AI-Generated Outputs** ("minimally human input"). Registering a fully-AI work
  is a breach of the Membership Agreement and can put royalties on hold.
- A pipeline track qualifies as AI-Assisted **because its lyrics are human-authored**. That
  is the entire basis of the claim (`gate_lyrics_original` hash-binds it).
- `elemental-fire` is **instrumental by design** — `music/prompts/elemental-fire.md` says
  "Leave the **lyrics box empty**", and upstream `music/suno-gen.py:141
  is_instrumental_template()` names elemental-fire among the 8 instrumental templates.

Therefore this genre is an **AI-Generated Output with no registrable portion**: no PRO
registration, no publishing-royalty path, and a US Copyright Office registration would have
to disclaim the whole composition. That is not a blocker for `game-assets` (a licence sale)
or `youtube-gaming` (ad revenue), but it removes one revenue mechanism from the `streaming`
lane that the oracle's `revenue_potential` 8.0 does not adjust for. Record it; do not
"fix" it by bolting lyrics onto a boss theme — the template says sung lyrics have narrow
sync utility and a sung chorus is explicitly OUT of genre.

## 7. Generation path — measured on this host

**The lane's own generate prompt names `music/suno-gen.py`. That file is not in this
checkout.** It exists on `origin/main` (commits `295fc49`, `ba28f55`). This checkout has
diverged: `git rev-list --count HEAD..origin/main` = **15** commits of this lane's own work
missing locally. Already carded (t_8a715681, nexus-core) — flagged, not fixed: seven workers
share this tree and a pull/rebase would auto-stash their in-flight edits.

Read from the git object (`origin/main:music/suno-gen.py`, not from disk):

- `is_instrumental_template(genre)` — keys on the template's `## Lyrics guidance` section
  and its own docstring lists **elemental-fire** among the 8 instrumental templates. This is
  the decision that lets the rail accept a track with no human lyric sheet.
- `music/sunolocal/**` — the local Suno-shaped service (ACE-Step + YuE2 adapters).

**Render gaps that bite this genre** (all already carded on t_25a6499c, nexus-core — cited so
later stages do not rediscover them):

1. **BPM is not expressible** — §5 above. For elemental-fire the gap is sharper than for any
   sibling genre, because this genre is the fastest in the registry (150 BPM; the other three
   elementals anchor 82 / 88 / 92) and it is the one whose product *depends* on the tempo
   (§4's loop math and the 75-bar structure).
2. **Instrumental tracks cannot be expressed in the planner queue.**
   `mining-k8s` `values.yaml` brief schema is `{name, genre, brief, lyricsMode?, language?,
   title?, duration?}` and `planner.py --lyrics-mode` accepts only `draft|ai`. For an
   instrumental genre both are wrong: `draft` produces a scaffold `acestep_plan.py` refuses
   (exit 1, `.refused` marker), `ai` writes lyrics for a track that must have none. An
   `instrumental` mode is required before this genre can render.
3. **`key = req.style or "C major"`** (`translate.py:49`) — the engine receives the whole
   583-character caption where a key signature belongs. D Phrygian must be carried
   explicitly.

Live route into audio (in-cluster, not the kanban stage machine): ConfigMap
`music-pipeline-briefs` → CronJob `music-pipeline` (plans via `planner.py` →
`/var/lib/music-plans/<name>.json`) → CronJob `music-pipeline-render` (`acestep_plan.py` →
sunolocal studio API). Chart: `/home/j_kro/mining-k8s/helm/charts/music-pipeline/`.

## 8. Existing assets for this genre

Measured:

- **No lyric sheet and no blueprint** — expected: the genre is instrumental, so there is no
  sheet to write, and `music/lyrics/blueprints/` holds only `activist`, `chill-lounge`,
  `trance`.
- **No campaign directory, no masters, no stems, no cover, no package.** The first render is
  genuine work, not a re-run.
- **`music/visuals/element_fire.mp4` is a TEST FIXTURE, not a product.** It is 5.000 s,
  1280×720, 14 133 B, built by `music/gates/_visual_fixtures.py` for `check_gate_suite.sh`.
  Executed against the real gate:

```
$ python3 music/gates/gate_youtube_authentic.py --visual music/visuals/element_fire.mp4
FAIL gate_youtube_authentic
  - visual has only 2 distinct frame signature(s) across 5.0s (sampled every 2.0s; 10 required) — this is a raw dump (static image + audio), which YouTube's inauthentic-content policy penalizes
  - no disclosure file (one of disclosure.txt, ai_disclosure.txt) beside the visual — the AI role in the video must be disclosed
rc=1
```

  Do not mistake this fixture for a rendered visual and do not ship it.

Quota is untouched:

```
$ /usr/bin/python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

## 9. ⚠ `gate_loop_points` PASSES a broken loop — measured, with the reproduction

This is the most important finding in this brief. The `game-assets` lane's defining gate does
not catch the break its own rubric names. Measured on real synthesized artifacts at this
genre's 16-bar loop length (25.6 s), in `…/workspaces/t_6f0d261e/`.

**The artifacts exist as two renders of the same four signals** — `loop/` (`seamless.wav`,
`faded.wav`; the first probe, rendered at 1/8 amplitude) and `loop2/` (`A_seamless.wav`,
`B_faded.wav`, `C_phaseslip.wav`, `D_truncated.wav`; full scale). The curvature ratio is
level-invariant, so the verdicts are identical in both; the absolute dB is not, so every
level figure below is attributed to the render it was measured on. **Corrected 2026-10-16 by
the duplicate-card pass `t_42a01e18` (§13):** this table previously attributed the whole
`loop_safety` column to `loop2/`. Those numbers are the `loop/` render's; `loop2/` gives the
same Δ, 18 dB louder.

| Artifact | `gate_loop_points` | Rubric `loop_safety` tail/head RMS, `loop/` render | Same ruler, `loop2/` render |
|---|---|---|---|
| A seamless tone | **PASS** 1.56× (`loop2/` measures 1.57×) | −21.1 / −21.1 dB (Δ 0.0) ✓ | −3.0 / −3.0 dB (Δ 0.0) ✓ |
| B 1.6 s fade-out tail | **PASS 2.21×** ← false pass | **−21.1 / −29.9 dB (Δ 8.8 dB)** ✗ | **−3.0 / −11.9 dB (Δ 8.9 dB)** ✗ |
| C half-period phase slip | FAIL 5.99× ✓ | Δ 0.0 — the level ruler is blind to a pure click | Δ 0.0 |
| D truncated 1/4 cycle | FAIL 34.01× ✓ | Δ 0.0 — same | Δ 0.0 |

Each ruler has one hole and the holes are different: curvature cannot see level, the tail/head
comparison cannot see a click. Neither number alone verifies a loop.

```
$ python3 music/gates/gate_loop_points.py \
    --master …/t_6f0d261e/loop/faded.wav --loop-points …/t_6f0d261e/loop/lp.json
PASS gate_loop_points
  master   : …/t_6f0d261e/loop/faded.wav (25.600s)
  loop     : [0.000s -> 25.600s] (span 25.600s)
  seam     : curvature ratio 2.21x (max 3.0x) — seamless
  region   : RMS 0.08610 (not silent)
rc=0
```

The `master` line and the artifact path are shown because the failure this table documents is a
**false pass** — a reader must be able to tell which render produced the number. The same run on
`…/t_6f0d261e/loop2/B_faded.wav` prints `seam : curvature ratio 2.21x` and
`region : RMS 0.69183` (both re-measured 2026-10-16, §13).

**Root cause.** The gate measures *junction curvature* — the discrete second difference of
the PCM across the wrap — so it detects **derivative kinks** (a click). A linear fade-out is
perfectly smooth; it removes energy without introducing a kink, so the curvature ratio stays
under the 3.0× ceiling. The gate's own calibration note ("clean 5 s-period = 1.6×,
half-period phase-slip = 6.0×") is honest about what it separates; a fade is neither case.

**Why it matters here.** `music/rubrics/gamer.json` lists "fade-out or truncated ending on a
game-loop claim" as a `reject_signal`, and its `loop_safety` criterion (weight 3 of 10) names
exactly the evidence that catches B: "last-1s RMS within ~6 dB of first-1s RMS, no
fade-to-silence on a loop claim". So the two rulers have one hole each and the hole is
different in each. **The package stage must run BOTH** — `gate_loop_points` for the click, and
the tail/head RMS comparison for the level discontinuity. A loop that passes only one is not
verified.

Carded as **t_bab8aa19** (nexus-core) with the reproduction and the regression check that must
land with the fix (a faded-tail fixture that must FAIL). Do not "fix" this by lowering the
`--click-ratio-max` for this genre: B measures 2.21× and C measures 5.99×, so no single
threshold separates them. The gate needs a second measurement, not a different number.

**The second measurement now exists (added 2026-10-16 by `t_42a01e18`, §13):**
`music/scripts/loop_seam_check.py` runs BOTH rulers — it delegates the curvature check to the
real gate and adds the rubric's tail/head level comparison — and PASSes only when both agree.
Until nexus-core folds the ruler into `gate_loop_points`, the package stage runs this in
addition to the gate:

```
$ python3 music/scripts/loop_seam_check.py \
    --master …/t_6f0d261e/loop/faded.wav --loop-points …/t_6f0d261e/loop/lp.json
FAIL loop_seam_check
  master   : …/t_6f0d261e/loop/faded.wav
  curvature: PASS 2.21x — no click at the wrap
  level    : FAIL tail-1s -29.9 dB vs head-1s -21.1 dB (delta 8.8 dB, max 6.0)
    the rubric's `loop_safety` reject (fade-out on a game-loop claim) — this is the break gate_loop_points cannot see
rc=1

$ python3 music/scripts/loop_seam_check.py --selftest
artifact                curvature         level (tail vs head)  verdict
A_seamless             PASS 1.57x   PASS 0.0 dB (-3.0 vs -3.0)     PASS
B_faded                PASS 2.21x  FAIL 8.9 dB (-11.9 vs -3.0)     FAIL
C_phaseslip            FAIL 5.99x   PASS 0.0 dB (-3.0 vs -3.0)     FAIL
D_truncated           FAIL 34.01x   PASS 0.0 dB (-3.0 vs -3.0)     FAIL
SELFTEST PASS loop_seam_check: A both rulers PASS; B curvature PASS / level FAIL (the fade is caught); C and D curvature FAIL
rc=0
```

The selftest builds its own four fixtures at a given `--bpm`/`--bars`, so the finding is
reproducible from the repo alone, without the probe directories under any card's workspace.

## 10. Stage plan for this genre (skips locked)

`brief` ✓ → `genre-select` → **`lyrics` SKIPPED** (instrumental: the template's empty-box
statement is the spec and `is_instrumental_template` keys on it; there is no lyric sheet to
write and no authorship claim to record — §6) → `generate` (quota gate first; **two
generations per week**, and the plan's `bpm` must read **150**, not 100/120/156) → `curate`
(pick the winner; record a reject reason per loser) → `stems` (≥ 4, ±0.5 s, plus the distinct
instrumental render) → `master` (`gate_loudness --target streaming`, −14 ±1; note the gate
measures ffmpeg `volumedetect` mean_volume, **RMS dB, not gated LUFS** — known ruler defect,
card t_9546841b) → `gate` (independent review, different model than the producer, against
`music/rubrics/gamer.json`: 5 criteria, pass threshold 7.0 on the geometric-median panel
aggregate; `battle_energy` and `loop_safety` carry weight 3 each) → `package`
(`gate_sync_ready --lane game-assets` + `gate_release_ready` + `gate_stems_present` +
`gate_loop_points` **and** the tail/head RMS check from §9 — implemented as
`music/scripts/loop_seam_check.py`, one call, both rulers; `loop_points.json`; ISRC with no
check digit) → `visual` (**applies** — `video_shape: loop-10min`: a 600.0 s visual, exactly
5 × the 120.0 s master, that passes `gate_youtube_authentic`, ≥ 10 distinct frames, with
`ai_disclosure.txt`) → `human-approval` (j_kro) → `publish` (private/draft only).

The visual has a real tension to resolve at the visual stage: the template requires the
visual cycle to **tile seamlessly** ("ember positions reset exactly") while
`gate_youtube_authentic` requires **≥ 10 distinct 64×64-gray frame signatures** sampled every
2.0 s. A short visual tile repeated verbatim fights the distinct-frame check — and this was
MEASURED, not assumed. Three synthetic 600.0 s (loop-10min) visuals were built and put
through the real gate:

| Probe | Frame samples | Distinct | Verdict |
|---|---|---|---|
| 12.8 s tile (the 8-bar cycle) tiled to 600 s | 300 | **22** | PASS, thin margin |
| 12.8 s tile + 16 Hz ember flicker | 300 | **21** | PASS, thin margin |
| continuous non-repeating drift | 290 | **170** | PASS, comfortable |

The gate's floor is 10, so a tiled visual clears it — but with **~8× less headroom** than a
continuous one (22 against 170). The distinct count is set by how many geometrically
different phases the 2.0 s sample grid lands on, not by how "busy" the visual looks. **A
longer tile, or a lower-motion treatment closer to the coal-bed macro the spec actually
asks for, moves that 22 toward the floor.** The visual stage must therefore measure the
distinct count on the real render and, if it is near 10, lengthen the visual cycle rather
than re-timing the sample grid.

Two more requirements, both measured rather than documented: the visual must be **≥ 640×360**
(`gate_youtube_authentic.py:146` — a 160×90 render FAILs with "below the 640x360 floor") and
carry a `disclosure.txt` or `ai_disclosure.txt` beside it. The existing 5 s fixture fails on
2 distinct signatures; do not extrapolate from it in either direction.

## 11. Portfolio warning — four near-identical products are in flight

`elemental-fire`, `-water`, `-earth` and `-air` share **family, lanes, cadence and
video_shape**; they differ in tempo (150 / 82 / 88 / 92 BPM), palette and scene. Their oracle
cards score identically (7.5/7.7) because every score component except trend signal is a
function of the lane set, which is identical for all four. Consequences:

- 4 genres × 2/wk = **8 packs/week** of the same shape, same lanes, same loop-video format.
  `gate_youtube_authentic`'s Jaccard ceiling (0.85 vs prior uploads) is exactly the check
  that punishes near-duplicate uploads, and its `--upload-index` path only bites once an
  upload index exists — which means the first four uploads set the baseline for each other.
  Vary the visual scene rotation (the visual doc already asks for coal-field / forge /
  volcano-crack per upload) and the palette, and expect the index to start rejecting.
- The board currently carries **8 elemental cards** (4 genres × 2 oracle waves) and 28 oracle
  cards for 14 genres in total. Already carded: t_bf0e5edd (assignee `oracle`). Do not create
  a new card for it; this brief's own duplicate is t_42a01e18.

## 12. Provenance

- Registry: `music/genres.yaml` (lines 86–93), `music/lanes.yaml` — validated live
  (`/usr/bin/python3 music/registry.py validate` → 14 genres, 10 lanes)
- Template: `music/prompts/elemental-fire.md` (4008 B; style field 583/1000 chars measured)
- Visual: `music/visuals/element-fire.md` (1103 B); fixture `music/visuals/element_fire.mp4`
  (5.000 s, 1280×720, 14133 B) — FAILs the real gate, measured
- Gates exercised live: `gate_quota` PASS; `gate_sync_ready --lane game-assets` FAIL on an
  empty package (full requirement list quoted in §3); `gate_release_ready` FAIL (quoted);
  `gate_stems_present` FAIL (quoted); `gate_loop_points` PASS on a seamless loop **and PASS
  on a faded loop** (§9); `gate_youtube_authentic` FAIL on the 5 s fixture (quoted)
- Oracle math: `music/oracle.py` lines 54, 179–305 — every score component re-executed live
  against the registry and `music/quota-ledger.json`
- Rubric: `music/rubrics/gamer.json` (family `gamer`, includes `elemental-fire`;
  pass_threshold 7.0; `battle_energy`, `loop_safety`, `chip_timbre_authenticity` weight 3)
- Autonomy: `music/autonomy.yaml` (all three lanes `advisory`)
- Rights: `music/docs/pro-registration.md` §1 (AI-Assisted vs AI-Generated Output),
  §3 (what disqualifies a track), §4 (the standing rule covers vocal tracks only)
- ISRC: IFPI International ISRC Agency Bulletin 2015/01 rev 3 (ISO 3901:2019) — 12
  characters, no check digit; `music/gates/gate_release_ready.py:92 isrc_syntax()` implements
  the element rules correctly while its own docstring:13–15 still claims a check digit
- Upstream truth read from git objects (this checkout is 15 commits behind): 
  `origin/main:music/suno-gen.py` (`is_instrumental_template`), 
  `origin/main:music/sunolocal/translate.py` (bpm 120 / style_weight mapping / `key = style`),
  `origin/main:music/sunolocal/checks/g3_translate.sh:21` (asserts the default `bpm == 120`)
- **Dangling reference (unchanged):** `brain/playbooks/music-lane-architecture.md` is cited as
  "READ FIRST" by this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`,
  `autonomy.yaml` and every gate script, but no copy exists on this machine. Same for
  `brain/research/music-monetization-2026.md`. Quoted section numbers (§3, §5, §13) cannot be
  checked. Carded: t_b0a4db92 (coo).
- Visual probe: three synthetic 600.0 s visuals built and run through the real gate —
  tiled-seamless 22 distinct / 300 samples, tiled+flicker 21 / 300, continuous 170 / 290;
  a 160×90 variant FAILs on the 640×360 floor (`gate_youtube_authentic.py:146`). Probe
  scripts: `…/workspaces/t_6f0d261e/probe_visual.py`, `probe_loop.py`
- **Not fixed here (other owners, already carded):** the new loop-gate defect **t_bab8aa19**
  (this brief's §9 reproduction); the queue entry for this brief is **t_28146d70**;
  instrument/tempo/key render gaps t_25a6499c; diverged checkout t_8a715681; scheduler units
  running the wrong checkout t_41f354be; oracle card duplication t_bf0e5edd; missing
  architecture docs t_b0a4db92; profile workdir + kanban env vars t_75aacf8b; the
  `gate_loudness` RMS-vs-LUFS ruler t_9546841b.
- **hotspot:** `music/briefs/` — six concurrent workers write this directory and commit to one
  working tree (`ade6e87`, `1553da2`, `4bb1ea6`, `9ebf6af`, `d491663` landed inside ~20
  minutes, one of them a sibling elemental brief). `music/gates/check_gate_suite.sh` is being
  edited in the same tree right now while this brief runs.
- **Lane checks re-run by the duplicate-card pass `t_42a01e18` (2026-10-16T13:50 CDT):**
  `music/scripts/check_brief_figures.py` — 56 of 58 recomputed figures lane-wide OK; the 2
  mismatches are `commentary-beds.md`'s "4,133 B" (card `t_47491ec0`), and no figure in THIS
  file was flagged. `music/scripts/check_brief_paths.py` — PASS (2 WARNs, other briefs).
  `music/scripts/check_prompt_style_counts.py` — PASS, 15 claims across 14 templates.
  `music/gates/check_gate_suite.sh` — `OK: every gate passed its good artifact and failed its
  broken one`, rc=0. New tool from that pass: `music/scripts/loop_seam_check.py` (§9, §13).

## 13. Duplicate-card verification pass — `t_42a01e18`, 2026-10-16T13:50 CDT

This card is the second-wave twin of `t_6f0d261e`: same genre, same lanes, same cadence, one
score component apart (trend signal 5.0 vs 3.0, which `music/oracle.py:284–289` returns on a
fetch failure). The brief is keyed by **genre**, so both cards resolve to this file. The twin
therefore owes a verification pass, not a second brief: nothing here is new work product, and
no stage chain was started (this genre already sits at `stage: genre-select`).

### Every checkable figure re-measured, live

| Section | Claim | Re-measured 2026-10-16 | Verdict |
|---|---|---|---|
| §1 | registry 14 genres / 10 lanes; `gate_quota` PASS 0/60 | `/usr/bin/python3 music/registry.py validate` → rc=0, identical line; `gate_quota` → `PASS`, 0/60, 0 studio exports | ✓ |
| §1 | composite 7.505 → 7.5; components 10 / 6 / 8 / 6.7 / 9 / 3 | recomputed with `oracle.py`'s weights (line 54): 7.505000 and 7.705000 for the twin | ✓ |
| §1 | re-run today: `cadence_fit` 3.333, total 7.0 | live `score_genre("elemental-fire")` → `cadence_fit 3.3333`, `trend_signal 3.0`, `total 7.0` | ✓ |
| §4 | bar 1.600 s; 16/32/75/375 bars = 25.6 / 51.2 / 120.0 / 600.0 s | all exact; 600÷51.2 = 11.71875, ÷89.6 = 6.6964, ÷102.4 = 5.8594, ÷120 = 5.000, ÷200 = 3.000 | ✓ |
| §4 | 75-bar sheet 9+12+12+12+9+12+9, 120.0 s; `MAX_DURATION_S` 420 | sums exact; `planner.py:83 MAX_DURATION_S = 420` | ✓ |
| §5 | style field 583/1000 chars; template 4008 B | block measures 583 chars / 583 bytes; template 4008 B | ✓ |
| §5 | `translate.py:42` bpm=120, `:45` `int(60 + style_weight*120)`; 120 / 156 / 150; `key` at `:49` | read from `origin/main`; all four derived BPMs and the line numbers exact | ✓ |
| §5 | no `elemental-fire.yaml`; planner falls back to 100 BPM at `planner.py ~470` | `music/lyrics/blueprints/` = activist, chill-lounge, trance; line 470 is exactly the fallback | ✓ |
| §7 | `music/suno-gen.py` absent here, on `origin/main` from `295fc49` / `ba28f55` | absent from the worktree; both commits present on `origin/main` | ✓ |
| §8 | fixture 5.000 s, 1280×720, 14 133 B; fails the real gate | ffprobe exact (h264+aac); gate FAIL, 2 distinct signatures, disclosure line — verbatim | ✓ |
| §8 | `gate_sync_ready` / `gate_release_ready` / `gate_stems_present` FAIL on an empty package | all three FAIL; every quoted reason line reproduced word for word | ✓ |
| §9 | the four verdicts and ratios | reproduced: 1.56× / **2.21× false pass** / 5.99× / 34.01× | ✓ (see correction) |
| §10 | 300 samples → 22 / 21 / 170 distinct; 640×360 floor at `gate_youtube_authentic.py:146` | re-ran the real gate on the three stored probes: 22, 21, 170 distinct, all PASS; floor line 146 exact | ✓ |
| §10 | rubric panel: 5 criteria, threshold 7.0, geometric median | `gamer.json` pass_threshold 7.0, 5 criteria, weights 3/3/3/1/1; geometric median implemented in `music/rubrics/panel.py` | ✓ |
| §10 | `gate_loudness` measures volumedetect mean_volume, not gated LUFS | gate docstring + `MEAN_RE`: confirmed; card `t_9546841b` still open | ✓ |
| §11 | 8 elemental cards, 28 oracle cards for 14 genres; `t_bf0e5edd` | board read (sqlite, read-only): 28 `music-oracle:%`, 8 elemental oracle cards, `t_bf0e5edd` `ready`/`oracle` | ✓ |
| §12 | `gate_release_ready.py:92` `isrc_syntax`; docstring 13–15 claim a check digit; `gate_youtube_authentic.py:146` | line numbers exact; validator is shape-only | ✓ |
| §12 | this genre's queue entry is `t_28146d70` | present, `todo`, `nexus-core`, "gated on instrumental mode t_25a6499c; bpm must read 150" | ✓ |

### The one correction applied

| # | Section | Claimed at the brief stage | Measured at this pass |
|---|---|---|---|
| 1 | §9 (table + prose), `brief.json: _loop_verification_warning` | the whole §9 table was "built in `…/t_6f0d261e/loop2/`" | the four signals exist as **two renders**: `loop/` (1/8 amplitude) and `loop2/` (full scale). `2.21×` and `1.56×` are the `loop/` set's numbers; `loop2/` measures `2.21×` and `1.57×`. The `loop_safety` column (−21.1 / −29.9, Δ 8.8) and the quoted `region : RMS 0.08610` are `loop/faded.wav`'s; `loop2/B_faded.wav` gives −3.0 / −11.9 (Δ 8.9) and `region : RMS 0.69183`. The finding is unchanged and the Δ reproduces on both renders — only the absolute level, which depends on the render gain, was attached to the wrong directory |

Nothing else needed correcting: every other figure in the file reproduced, including the ones
this pass expected to be stale (the repo divergence is still **15** commits behind
`origin/main`; only the "ahead" count moves, 26 → 29).

### Regression check added (FAILURE → TEST)

The failure above is not a wrong number, it is a **measurement attached to the wrong artifact
set** — the class where a table's absolute figures come from a different render than the one
its prose names. Two guards now exist:

- `music/scripts/loop_seam_check.py` (new): implements the second ruler §9 demands — it
  delegates curvature to the real `gate_loop_points.py` and adds the rubric's tail/head level
  comparison (`--tolerance-db`, default 6.0 from `gamer.json` `loop_safety`), and prints the
  measured artifact's **absolute path** next to its numbers, so a level figure can never again
  float free of the file it came from. `--selftest` builds the four fixtures from scratch and
  asserts the documented behaviour, so the finding is reproducible from the repo alone. This
  also closes the practical hole: the package stage now has a callable that FAILs a faded loop
  even while `gate_loop_points` passes it (nexus-core still owns folding it into the gate,
  `t_bab8aa19`).
- `music/scripts/check_brief_figures.py` (sibling card, commit `cab0415`): recomputes every
  brief figure and checks its unit. It covers `B` / `chars` / `lines`; it does **not** cover
  dB or RMS figures, which is why the ruler above carries that job.

### Not changed, not re-filed

No registry value, gate, plan, blueprint, chart file, cluster object or campaign artifact was
modified. No child card was created: every item §9–§12 raise already has an owner — `t_bab8aa19`
(the gate fix + its faded-tail fixture), `t_25a6499c` (BPM/key/instrumental render gaps),
`t_8a715681` (the 15-commit divergence), `t_bf0e5edd` (the oracle duplicate sweep),
`t_b0a4db92` (the dangling `brain/` citations), `t_9546841b` (the loudness ruler),
`t_28146d70` (this brief's queue entry), `t_41f354be` (scheduler units on the wrong checkout),
`t_426a82a3` (`battle_energy` scoping), and `t_75aacf8b` / `t_a14e5d52` (profile workdir, kanban
env, payload drift).

hotspot: `music/briefs/` — 14 briefs written and re-verified by ~8 concurrent `music-producer`
workers on 2026-10-16; every write needs a path-scoped commit and a lock retry. This file now
has two commits, both on this genre. `music/gates/check_gate_suite.sh` was being edited in the
same tree during this pass (it ran green at 13:48).
