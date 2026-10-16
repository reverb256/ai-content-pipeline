# Brief — elemental-fire

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`; on this board the cards
> are assigned `music-producer` and claimed by the generic kanban dispatcher).
> **Card (surviving, owns the chain):** t_97494e6a (`music-oracle: elemental-fire (score 7.2)`)
> — the third and newest card for this genre.
> **Superseded cards (closed, audit trail):** t_6f0d261e (7.5, `done`) and t_42a01e18
> (7.7, `done`), the 2026-10-09 double emission. All three resolve to THIS brief; the brief
> is keyed by **genre**, not by card.
> **Superseded by the loop-tile decision (`t_b75ccb4a`, 2026-10-16T17:39-05:00 CDT):**
> `sha256 f9d153e613a4c44933ad72e1959db2921c5937b3b3178fb42ce72cb1af1c8e09` (70626 B, 962 lines)
> — the revision whose §2 and §4 locked a **120.0 s (75 bars)** delivered loop. That length is
> unreachable on this render (its own trailing 4.803 s is digital silence) and does not
> survive the rail's refusal, so §2 and §4 now carry the **DECIDED** length, **25 bars =
> 40.000 s, 15 exact tiles** (§16), with the delivered-loop / master distinction stated in
> both places.
> **Written:** 2026-10-16T13:16-05:00 (CDT)
> **Verified (duplicate-card pass, `t_42a01e18`):** 2026-10-16T13:50-05:00 (CDT) — see §13.
> One attribution was corrected (§9: the tail/head dB column belongs to the `loop/` render,
> not to `loop2/`); the loop-gate finding itself reproduced on BOTH renders, and the second
> ruler §9 asks for now exists as `music/scripts/loop_seam_check.py`.
> **Verified (surviving-card pass, `t_97494e6a`):** 2026-10-16T16:07-05:00 (CDT) — see §14.
> Every checkable claim was re-measured against live state; §14 lists all 22 findings, and the
> ones that had moved are corrected in place. **No second brief was written and no second
> stage chain was started.**
> **Superseded revisions of this file (newest first):**
> `sha256 040693b7c8ca758d108f5e0bf56e3f017a29d63a4d69b05077d97a50024a19da` (42628 B, 664 lines)
> — the revision the surviving card inherited (last touched 15:15 by `t_bab8aa19`'s gate-fold
> edit); `sha256 86436b4b2c2c757756a7644b79907fbebc1872b3f6686d340e771a8e0516ace1` (508 lines) —
> the revision before the duplicate-card pass.
> `brief.json` superseded: `sha256 ebb875bd2472d0fab0a41766519db7b948bcd03334372fb53245acfe6bcc6013`.
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `d491663` (main) at write time. The working tree
> is shared by 6–7 concurrent brief-stage workers; HEAD moved 5 times while this brief was
> written (the last commits were the sibling elemental briefs `elemental-air`, `sentimental-piano`,
> `commentary-beds`, `anime-opening`). Re-measured by the surviving-card pass: `main` @
> `2611770` = **0 behind / 73 ahead** `origin/main` (`ba28f55`), anchored to that revision at
> 2026-10-16T16:07 CDT — the 15-commit upstream deficit both earlier passes recorded is GONE
> (§14 row 9; card `t_8a715681`, `done`).
> **Oracle:** the surviving card's title says 7.2 and the superseded pair says 7.5 / 7.7; the
> live re-score is **7.0/10** — quota headroom 10.0, **lane coverage 6.0**, revenue 8.0,
> cadence fit **3.333**, policy risk 9.0, **trend signal 3.0**. Threshold 5.0 → produce. The
> spread is the calendar plus one network fetch, not genre heat.
> **Superseded by the citation sweep (`t_e86c2110`):**
> `sha256 eac7238cab6cc98e3257200e4828e1fd3d9e866d4c7126263d4095610f080bc4` (67041 B, 921 lines) —
> the revision that still cited the blank line 54 of `music/oracle.py`. The `WEIGHTS` dict moved to
> line 75 when `oracle.py` grew its stage-marker block, so that citation opened on a blank line.
> Both references are corrected in place (§15); nothing else in this file changed.

## 1. Genre resolution (live, not transcribed)

Resolved from `music/genres.yaml` through the registry loader:

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

(`stage gate rule(s)` and the `stage gate visual` line were not in the output this brief
first quoted — the loader gained a stage-gate section; re-run 2026-10-16 by this pass.)

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
| Visual style | `music/visuals/element-fire.md` (1522 B) |
| Lanes | `game-assets`, `youtube-gaming`, `streaming` |
| Cadence | 2/wk |
| Video shape | `loop-10min` |
| Registry note | "Boss/battle theme. Target indie devs + gaming music channels." |

### The composite score, re-derived (arithmetic checked, not eyeballed)

`music/oracle.py:75` — weights 0.25 / 0.20 / 0.20 / 0.15 / 0.10 / 0.10 (`WEIGHTS` sums to 1.0,
re-measured). *(t_e86c2110: this cited line 54; line 54 is blank since `oracle.py` grew its
stage-marker block, and `WEIGHTS` is the dict at 75.)* Recomputed from the scored card's own
components: **7.505 → 7.5**, the pair's
scoring-day number. Per-component derivation, each re-executed live against the registry:

| Component | Value | Derivation (all re-run live) |
|---|---|---|
| Quota headroom | 10.0 | `10 × (1 − 0/58)`; `gate_quota` PASS 0/60 |
| Lane coverage | 6.0 | 3 viable lanes, 0 banned → `min(3×2, 10)` = 6 |
| Revenue potential | 8.0 | itch.io 300 + unity-asset-store 300 + gamedev-market 300 + youtube 500 + distributor 200 = 1600 → `min(1600/200, 10)` |
| Cadence fit | 6.7 | 2/wk, 21 days left in period → `(6.0 − 2)/6 × 10` = 6.67 |
| Policy risk | 9.0 | 0 banned surfaces, −1 for `youtube-gaming` |
| Trend signal | 3.0 | DuckDuckGo returns **0** `result__snippet` matches for `"elemental-fire music trend 2026"` |

**Re-scored live by this pass** — `oracle.score_genre("elemental-fire", spec, lanes, quota)`
under the registry's own loader, 2026-10-16T16:07 CDT: **`total 7.0`** (quota_headroom 10.0,
lane_coverage 6, revenue_potential 8.0, **cadence_fit 3.3333**, policy_risk 9.0,
**trend_signal 3.0**). That is the number the oracle's own dedupe ruling on this card carries
(`t_97494e6a`, comment 2026-10-16 14:19). Two facts fall out of the two tables:

1. **`trend_signal` was a network artifact; it is now a fixed floor.** The function returned
   **3.0** when the fetch succeeded and found 0 snippets and **5.0** on an exception
   (`oracle.py:284–289`, the pre-fix shape). That exception premium is the entire 7.5-vs-7.7
   spread across the superseded pair. `oracle.py` @ `b2d11f7` scores a failed fetch and an
   empty success alike at `TREND_NO_SIGNAL = 3.0`, which is why the pair's numbers cannot be
   reproduced and the surviving card's can. Re-measured this pass: the live fetch timed out
   and scored 3.0 — exactly as a 200/0-snippet page does
   (`music/scripts/check_oracle_determinism.py` PASS, `total 7.0` both ways).
2. **`cadence_fit` decays every day and `quota_headroom` does not.** Cadence fit was 6.67
   when the pair was scored (2026-10-09, 21 days left in the period). Re-run today
   (2026-10-16, 14 days left) it measures **3.333**, putting the genre at **7.0**. Still above
   the 5.0 threshold, but the margin is the calendar, not the product. The oracle's largest
   weight (quota headroom 10.0) is a constant that only moves when we spend downloads — it
   will keep padding every genre's score until the ledger fills.

## 2. Intent — the product is a game-asset LOOP PACK, not a single track

`game-assets` is the lane that defines this genre's product. Per `music/lanes.yaml` its
surface is `itch.io,unity-asset-store,gamedev-market` and its required artifacts are
`[stems, loop_point, seamless_loop, metadata]`. The buyer is an indie developer who needs a
boss loop they can drop into a level; the YouTube channel is the shop window, not the
product.

What the pack must contain:

| Pack element | Spec |
|---|---|
| Master (the render) | 120.000 s = 75 bars at 150 BPM — the full fight arc (measured; unchanged by this card) |
| Delivered loop (the video tile) | **25 bars = 40.000 s** — the `loop_bars` the registry now declares, tiling **exactly 15×** into the 600.000 s `loop-10min` video (**decided by card `t_b75ccb4a`, §16**; the rail previously closed 4 bars / 6.400 s, which tiles 93.75× — FRACTIONAL) |
| Stems | ≥ 4, each within ±0.5 s of the master (ffprobe-measured) |
| `loop_points.json` | `{"loop_start_s": 0.0, "loop_end_s": 40.0, "seamless": true}` — the delivered loop IS the master, so the span is 0 → its own duration (§16; the 120.0 s span this row first carried is impossible — the master ends in 4.803 s of digital silence) |
| Short loops (cutdowns) | 32 bars = **51.2 s** and 16 bars = **25.6 s** for in-engine use. These are the PACK lane's cutdowns: a game engine repeats whatever it is handed, so they carry **no tiling requirement** and 16/32 bars is not a defect. Only the video tile must divide 600 s (§16) |
| BPM / key | **150 BPM**, **D Phrygian** — stated in the manifest (`asset_packaging`, weight 1) |
| Cover | 3000×3000 (this brief's own spec — no gate enforces a cover dimension; `gate_release_ready` only PIL-opens the artwork), palette from `music/visuals/element-fire.md` |
| Video | 600.0 s (loop-10min) = exactly **15 × the 40.000 s delivered loop** (§16; the 5 × 120.0 s master this row first carried cannot be built — the master's trailing 4.803 s is digital silence, so a 120.0 s loop is refused and 5 × 120.0 s would put five silent gaps in the video) |

**Measured status of that spec (2026-10-16, live — §14 rows 10–12).** The master now exists:
`/var/lib/music-plans/elemental-fire-emberfall.flac`, **120.000 s**, FLAC 48 kHz stereo,
`sha256 013339ab7c5dd8b6c6f21826512be400ed58fc37a357222823de78274a82382f`. The rail closed a
loop out of it — `/var/lib/music-plans/loops/elemental-fire-emberfall.loop.wav`, **6.400 s /
4 bars** (`loop_points.json`: `bars 4`, `bpm 150`, `seam_method pre-roll-crossfade-20ms`,
level delta 0.3 dB) — and that loop PASSes both loop rulers (measured, §9). What does **not**
exist yet: stems, cover, package, ISRC, disclosure file, 600 s visual. Two spec problems are
now measured rather than theoretical: the delivered loop is **4 bars**, and 4 does not tile
into 600.000 s (375/4 = 93.75 tiles — fractional), while the 120 s master ends in **4.787 s of
digital silence** (`silencedetect noise=-50dB:d=0.5` → `115.196687 .. 119.983688`), so it can
not carry a `seamless: true` claim itself. Card `t_b75ccb4a` owns that decision.

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

`gate_sync_ready --package-dir <empty> --lane game-assets` on an empty package — the
requirement list the package stage must satisfy. **Re-run 2026-10-16 by this pass; the list
has grown since the brief first quoted it** (pack mode is now the game-assets default, and the
gate validates a manifest *schema* and a licence file, not just the presence of files):

```
FAIL gate_sync_ready
  - no manifest.json
  - manifest.json has no metadata object
  - manifest metadata missing 'title'
  - manifest metadata missing 'artist'
  - manifest metadata missing 'bpm'
  - manifest metadata missing 'key'
  - manifest metadata missing 'mood'
  - manifest metadata missing 'genre'
  - manifest metadata missing 'sample_rate'
  - manifest.json has no pack_manifest count object (loops/stems/one_shots/sfx) — a pack must declare its contents and the declaration must match the files
  - pack_manifest has no 'loops' count — a game-assets pack ships loops and stems
  - pack_manifest has no 'stems' count — a game-assets pack ships loops and stems
  - no loop_points.json — the game-assets lane requires loop points (run gate_loop_points.py --pack-dir for the seam check)
  - no clearance_doc.pdf (or .txt) — sync requires a clearance document
  - no ai_disclosure.txt — the AI role must be declared for sync platforms
  - no LICENCE.txt — §13 requires a licence with explicit permitted use, distribution and derivative-work rules (music/licences/perpetual_game_asset_v1.txt)
rc=1
```

The track-shaped reasons the first pass recorded (`full_mix.wav is not a real audio file`,
`no stems/ directory`, `instrumental.wav is not a real audio file`) no longer appear for this
lane: `--mode pack` is the default for `game-assets`, and in pack mode the manifest comes
first — the gate cannot ask about stems it has no declaration for. In `--mode track` the
track-shaped checks still run.

`gate_release_ready` on the same empty package:

```
FAIL gate_release_ready
  - no master.wav
  - no artwork (one of artwork.jpg, artwork.jpeg, artwork.png)
  - no manifest.json
  - no ai_disclosure.txt
rc=1
```

`gate_stems_present` with no stems: `only 0 stem(s) in <dir>; 4 required` (rc=1, re-measured —
the message now names the directory it looked in).

Decisions locked here so no later stage re-litigates them:

- **`instrumental.wav` must be a distinct render, not a copy of the master.**
  `gate_sync_ready` fails an instrumental byte-identical to `full_mix.wav`. Note the scope
  (re-measured): this is the **track** shape. `--mode pack` is the default for `game-assets`,
  and the gate's own source says a pack has no single `full_mix.wav` and no instrumental
  version (`gate_sync_ready.py:27`) — a pack is loops + stems + a `pack_manifest` whose
  declared counts must match the files. So for this genre the surviving form of the rule is:
  the stems must be real separate renders (a stem set that is one file copied N times is not a
  stem set), and the percussion-light smoldering-breakdown mix this genre wants has to be
  declared as a loop/stem in the manifest.
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
`video_shape: loop-10min` is a 600.0 s video built by repeating the delivered loop. The loop
must tile into 600 s an integer number of times, or the video's last seam is a jump cut. The
legal lengths are the bar counts that divide the shape's bar count — and that count is a
function of the genre's OWN tempo (375 bars at 150 BPM, but 205 at 82, 220 at 88, 230 at 92).
Measured candidates at 150 BPM:

| Loop length | Bars | Tiles into 600 s | Verdict |
|---|---|---|---|
| 6.400 s | 4 | 93.75 | ✗ fractional — what the rail had delivered |
| 24.000 s | 15 | 25.000 | ✓ legal, but the shortest thing that is still a phrase |
| **40.000 s** | **25** | **15.000** | ✓ **DECIDED — the delivered loop (§16)** |
| 120.000 s | 75 | 5.000 | ✓ legal, but UNREACHABLE on this render: it is 120.000 s long and ends in 4.803 s of digital silence, so a 120.000 s window is refused (measured) |
| 200.000 s | 125 | 3.000 | ✗ longer than the render |

**Decision (superseded in place by card `t_b75ccb4a`, 2026-10-16 — this section first locked
120.0 s / 75 bars): the DELIVERED loop is 25 bars = 40.000 s**, tiling exactly **15×** into
the 600.000 s video. The 75-bar answer is unreachable and the reason is measured, not
estimated: the ACE node emits **4.803 s of digital silence inside its own requested window**
(`silencedetect noise=-50dB:d=0.5` → `115.107 .. 119.983` on the delivered master), so a loop
window must fit inside the 115.197 s musical region, and `music/scripts/loop_close.py`
refuses a 75-bar window with *"the musical region (115.197s) is shorter than one 120.000s
loop — nothing to close"*. 25 bars is the largest divisor of 375 that survives that limit.
Measured on the real master, it closes with a **0.0 dB** tail/head level delta — the best of
the four lengths measured (4 bars 0.3 dB, 5 bars 1.0 dB, 15 bars 2.0 dB, 25 bars 0.0 dB) —
and passes all three rulers in `music/gates/gate_loop_points.py` (rc=0) plus
`music/scripts/loop_seam_check.py` (rc=0).

The 75-bar figure keeps its meaning as the **MASTER's** arrangement: the render IS 120.000 s
= 75 bars, and its seven-section fight arc still divides that way:

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

`music/planner/planner.py` now carries `MIN_DURATION_S = 30` (`:103`) and
`MAX_DURATION_S = 600` (`:104`) — raised from the 420 this brief first read, so both the
120 s master and the 600.0 s render length are inside the guard rail (`MIN_DURATION_S <=
dur <= MAX_DURATION_S`, `:696`). The 420 claim's own line number is gone too: `planner.py`
line 83 is a blank line now (`check_brief_line_refs.py` flagged that citation, §14 row 5). The
10-minute artifact is still delivered as a video, but for the tiling reason in this section,
not because the planner refuses the length.

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

### ⚠ Style Influence 80 % collided with the 150 BPM spec — resolved on the deployed engine

**Re-measured 2026-10-16 by this pass: the collision this section described is gone from the
running engine.** The repo's own mirror of the translator (`music/sunolocal/translate.py`,
byte-identical to `origin/main`) still carries the coupling the first pass measured:

```
42:    bpm = 120
45:        bpm = int(60 + req.style_weight * 120)
49:    key = req.style or "C major"
```

But that mirror is not the deployed code. The live engine is **`sunolocal v0.1.3`**
(pod `mining/sunolocal-source-*`; `music/quota-ledger.json` records the engine for the one
render it logs as "sunolocal v0.1.3 -> comfyui-zephyr"), and its
`/opt/sunolocal/music/sunolocal/translate.py` reads:

```
    # BPM. An EXPLICIT tempo wins. The style_weight mapping below is a
    # documented FALLBACK only: it repurposes Suno's style-ADHERENCE dial as a
    # tempo control ...
    bpm = None
    if req.bpm is not None:
        bpm = int(req.bpm)
    elif req.style_weight is not None:
        bpm = int(60 + req.style_weight * 120)
    if bpm is None:
        bpm = 120
```

So the dial no longer has to be sacrificed: an explicit `bpm` **wins** over both the
style mapping and the `120` default, and an explicit key/keyscale is carried the same way
(card `t_25a6499c`, `done`). That is how this genre renders at spec tempo — the plan on disk
reads `"bpm": 150` and `"key": "D Phrygian"` (§8, §14 row 10).

What remains true is the **fallback path**: if a caller sends neither, the style-adherence
dial is still doing double duty as a tempo control. Consequences, computed (fallback only):

| Path | Resulting BPM | vs the 150 spec |
|---|---|---|
| `style_weight` unset, no explicit `bpm` | 120 | −20 % |
| `style_weight = 0.80` (the template's own setting), no explicit `bpm` | **156** | +4 % — 1 bar = 1.538 s, not 1.600 s |
| `style_weight = 0.75`, no explicit `bpm` | 150 | ✓ but contradicts the template's stated 80 % |
| **explicit `bpm` (the live path)** | **150** | ✓ — measured on the delivered plan; the dial is free to stay at the template's 80 % |
| local `planner.py`, no blueprint, no `--bpm` | **150** | ✓ — measured this pass: the planner reads the template caption's own tempo (`bpm_in_caption`, `planner.py:279`); it no longer lands on a bare 100 |

So the **fallback path** still has no setting of the dial that both honours the template's
80 % style adherence and produces 150 BPM — but the deployed engine's explicit-`bpm` branch
bypasses it (above), and the planner's own default no longer lands on 100. Measured this pass:
`planner.py plan --genre elemental-fire --lyrics-mode instrumental` with **no `--bpm`** yields
`"bpm": 150`, because `bpm_anchor_for()` (`planner.py:203–212`) reads the blueprint's anchor
first and then the template's own caption tempo (`bpm_in_caption`, `:279`;
`"bpm": args.bpm or bpm_anchor_for(ctx) or 100` at `:811` / `:830`). The genre holds no
`music/lyrics/blueprints/elemental-fire.yaml` — **only 7 genres with a lyric blueprint**
(activist, anime-ending, anime-opening, chill-lounge, epic-orchestral-boss, jungle-dnb,
trance, counted live) — and it does not need one for tempo.

**Acceptance for this genre: the plan's `bpm` field must read 150, never 100, 120 or 156.**
The queued plan meets it (`bpm 150`). The key is the remaining explicit field: the planner's
default key is `C minor` (measured), the spec's is `D Phrygian`, so the queue entry must
carry `keyscale` — and it does.

At 100 BPM a bar would be 2.400 s and the 120.0 s master would be 50 bars, which is why the
100 fallback was a hard blocker when this brief was written; that row is now gone.

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

**FIXED — `music/suno-gen.py` is now in this checkout.** The first pass could only read it out
of the git object, because the tree was **15 commits behind** `origin/main`. That divergence is
gone (card `t_8a715681`, `done`): measured this pass, `main` @ `2611770` is **0 behind / 73
ahead** `origin/main` (`ba28f55`). The file is on disk — `music/suno-gen.py`, 42 652 B,
`is_instrumental_template()` at `:141`. Read from disk (identical on `origin/main`, commits
`295fc49`, `ba28f55`):

- `is_instrumental_template(genre)` — keys on the template's `## Lyrics guidance` section
  and its own docstring lists **elemental-fire** among the 8 instrumental templates. This is
  the decision that lets the rail accept a track with no human lyric sheet.
- `music/sunolocal/**` — the local Suno-shaped service (ACE-Step + YuE2 adapters).

**Render gaps that bit this genre — all three are now CLOSED** (card `t_25a6499c`, `done`; the
closed state of each was measured by this pass, so later stages do not rediscover them):

1. **BPM is expressible now.** §5 above: the deployed engine takes an explicit `bpm` and it
   *wins* over the style-weight mapping; the queue schema carries `bpm`, the planner carries
   `--bpm`, and the delivered plan reads `bpm 150`. The gap mattered more here than for any
   sibling genre because elemental-fire is the fastest in the registry (150 BPM; the other
   three elementals anchor 82 / 88 / 92) and its product depends on the tempo (§4).
2. **Instrumental tracks can be expressed in the planner queue now.** `planner.py
   --lyrics-mode` accepts `{draft, ai, instrumental}`, and the queue schema takes
   `lyricsMode: instrumental` (or `instrumental: true`); the CronJob maps either to the mode
   and passes `--bpm` / `--keyscale` through. The gap was real: for an instrumental genre
   `draft` produces a scaffold `acestep_plan.py` refuses (exit 1, `.refused` marker) and `ai`
   writes lyrics for a track that must have none. Measured: `elemental-fire-emberfall` is
   queued as `lyricsMode: instrumental`, planned, and rendered (`.flac`, §8).
3. **The key is carried explicitly now.** `translate.py:49`'s `key = req.style or "C major"`
   is the old mirror's line; the deployed engine takes an explicit key/keyscale, the planner
   has `--key` / `--keyscale`, and the queue entry carries `keyscale: "D Phrygian"` — which
   the delivered plan reads back as `"key": "D Phrygian"`. Without it the plan defaults to
   `C minor` (measured), so the explicit field is still mandatory for this genre.

Live route into audio (in-cluster, not the kanban stage machine): ConfigMap
`music-pipeline-briefs` → CronJob `music-pipeline` (plans via `planner.py` →
`/var/lib/music-plans/<name>.json`) → CronJob `music-pipeline-render` (`acestep_plan.py` →
sunolocal studio API). Chart: `/home/j_kro/mining-k8s/helm/charts/music-pipeline/`.
**This route has now run for elemental-fire** — the live ConfigMap carries the entry
(`bpm 150`, `keyscale D Phrygian`, `lyricsMode instrumental`, `duration 120`), the plan and
the `.flac` are on disk, and the rail also closed the loop (§8 above).

## 8. Existing assets for this genre

Measured:

- **No lyric sheet and no blueprint** — expected: the genre is instrumental, so there is no
  sheet to write, and `music/lyrics/blueprints/` holds 7 files, none of them
  `elemental-fire.yaml` (activist, anime-ending, anime-opening, chill-lounge,
  epic-orchestral-boss, jungle-dnb, trance).
- **The render path has since produced this genre's master** (§14 rows 10–12; queued by
  `t_28146d70`, `done`). Measured 2026-10-16:
  - plan `/var/lib/music-plans/elemental-fire-emberfall.json` (1843 B, re-planned 16:57 — the rail
    re-plans the track on every pass) — `bpm 150`,
    `key "D Phrygian"`, `duration 120`, `instrumental true`, `blueprint false`, and `lyrics`
    holding the 7 bare section tags (`[Intro]`, `[Instrumental]`×2, `[Break]`,
    `[Instrumental Break]`, `[Instrumental]`, `[Outro]`) with no singable line;
  - the `.rendered` marker (15:09) and the master
    `/var/lib/music-plans/elemental-fire-emberfall.flac` — **120.000 s**, FLAC 48 kHz stereo,
    11 421 612 B, `sha256 013339ab7c5dd8b6c6f21826512be400ed58fc37a357222823de78274a82382f`;
  - the delivered loop `/var/lib/music-plans/loops/elemental-fire-emberfall.loop.wav`
    (**6.400 s / 4 bars**, PASSes both rulers — measured §9) and its `loop_points.json`.
  Still absent: stems, cover, package, ISRC, disclosure file and the 600 s visual. The render
  is **not recorded in `music/quota-ledger.json`** (its `renders:` list holds one entry,
  elemental-air) — card `t_d6b0cb36` owns that log gap.
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

## 9. ⚠ `gate_loop_points` PASSED a broken loop — FIXED 2026-10-16, with the reproduction

This was the most important finding in this brief: the `game-assets` lane's defining gate did
not catch the break its own rubric names. **It is fixed.** Measured on real synthesized
artifacts at this genre's 16-bar loop length (25.6 s), in `…/workspaces/t_6f0d261e/`, and
re-measured by this pass on 2026-10-16.

**The artifacts exist as two renders of the same four signals** — `loop/` (`seamless.wav`,
`faded.wav`; the first probe, rendered at 1/8 amplitude) and `loop2/` (`A_seamless.wav`,
`B_faded.wav`, `C_phaseslip.wav`, `D_truncated.wav`; full scale). The curvature ratio is
level-invariant, so the verdicts are identical in both; the absolute dB is not, so every
level figure below is attributed to the render it was measured on. **Corrected 2026-10-16 by
the duplicate-card pass `t_42a01e18` (§13):** this table previously attributed the whole
`loop_safety` column to `loop2/`. Those numbers are the `loop/` render's; `loop2/` gives the
same Δ, 18 dB louder.

**One measurement caveat, found by this pass:** those four `loop2/` artifacts do not share a
length — `D_truncated.wav` is 25.598866 s while A/B/C are 25.600 s — and the directory holds a
single `loop2/lp.json` pinned to `loop_end_s: 25.59886621315193` (D's length). Running the
gate on A/B/C with that file cuts the wrap one sample early and reports `34.01x / 3.04x /
34.57x` — a verdict about the loop POINTS, not about the audio. Every number below was taken
with loop points that match the artifact (25.6 s for A/B/C, its own 25.598866 for D).

| Artifact | `gate_loop_points` NOW (both rulers) | Curvature ruler alone (what the old gate ran) | Rubric `loop_safety` tail/head, `loop2/` render |
|---|---|---|---|
| A seamless tone | **PASS** 1.57× + Δ 0.0 dB | PASS 1.57× | −3.0 / −3.0 dB (Δ 0.0) ✓ |
| B 1.6 s fade-out tail | **FAIL — curvature 2.21× (under the 3.0 ceiling) but level Δ 8.9 dB** ← the false pass is now closed | PASS 2.21× ← the old false pass | **−3.0 / −11.9 dB (Δ 8.9 dB)** ✗ |
| C half-period phase slip | FAIL 5.99× ✓ | FAIL 5.99× | Δ 0.0 — the level ruler is blind to a pure click |
| D truncated 1/4 cycle | FAIL 34.01× ✓ | FAIL 34.01× | Δ 0.0 — same |

Each ruler has one hole and the holes are different: curvature cannot see level, the tail/head
comparison cannot see a click. Neither number alone verifies a loop — which is why the gate now
runs both, and a loop must pass both.

```
$ /usr/bin/python3 music/gates/gate_loop_points.py \
    --master …/t_6f0d261e/loop/faded.wav --loop-points …/t_6f0d261e/loop/lp.json
FAIL gate_loop_points
  master   : …/t_6f0d261e/loop/faded.wav (25.600s)
  loop     : [0.000s -> 25.600s]
  seam     : curvature ratio 2.21x (max 3.0x)
  level    : tail-1.0s -29.9 dB vs head-1.0s -21.1 dB (delta 8.8 dB, max 6.0)
  - loop level drops 8.8 dB across the wrap: tail-1.0s -29.9 dB vs head-1.0s -21.1 dB (max 6.0 dB) — a fade or level ramp at the loop end; the loop is NOT seamless
rc=1
```

(For comparison, the same command on `loop/seamless.wav` prints `PASS`, curvature
`1.56x`, level `Δ 0.0 dB`; on `loop2/B_faded.wav` with matching loop points it FAILs on the
level line at Δ 8.9 dB, curvature 2.21× — re-measured 2026-10-16.)

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
game-loop claim" as a `reject_signal`, and its `loop_safety` criterion (weight **3 of the 8
points that apply to this genre** — §10, measured) names exactly the evidence that catches B:
"last-1s RMS within ~6 dB of first-1s RMS, no fade-to-silence on a loop claim". So the two
rulers have one hole each and the hole is different in each. **The package stage must run
BOTH** — `gate_loop_points` for the click, and the tail/head level comparison for the level
discontinuity. A loop that passes only one is not verified. Since the fold below, one call
gives both.

Carded as **t_bab8aa19** (nexus-core) with the reproduction and the regression check that had
to land with the fix (a faded-tail fixture that must FAIL) — **that card is `done`**. Do not
"fix" this by lowering the `--click-ratio-max` for this genre: B measures 2.21× and C measures
5.99×, so no single threshold separates them. The gate needed a second measurement, not a
different number.

**FOLDED INTO THE GATE (2026-10-16, card `t_bab8aa19`, lane commit `ae05548`).**
`music/gates/gate_loop_points.py` now runs BOTH rulers in one call and a loop must pass both:
the junction-curvature ruler (a click) and the rubric's own tail/head level ruler (1.0 s
window, `ffmpeg volumedetect` mean_volume, FAIL above 6.0 dB — `music/rubrics/gamer.json`
`loop_safety`), each printed with its measurement. So the package stage gets both rulers from
its existing `gate_loop_points` call; the runner below stays as the standalone cross-check that
prints both rulers in one report:

**What the level ruler could not see — CLOSED (card `t_8297d2c6`, commit `a664b4e`).** Its window
is the rubric's 1 s, its ceiling the rubric's ~6 dB, so a fade shorter than ~1.15 s hid inside
that budget (a 1.0 s fade measured 4.7 dB and PASSED). The fix landed as a THIRD ruler, not a
lower ceiling: the same 1 s at the loop end split in half (FAIL past the same 6 dB; a fade reads
8.5 dB, a 0.5 s fade 4.7 dB) plus the lane's −50 dB silence floor, because a window that is
itself silence is no evidence of continuity — the boundary is 0.6 s (6.2 dB), measured.

**The standalone second measurement (added 2026-10-16 by `t_42a01e18`, §13):**
`music/scripts/loop_seam_check.py` runs BOTH rulers — it delegates the curvature check to the
real gate and adds the rubric's tail/head level comparison — and PASSes only when both agree.
**Re-measured by this pass: the tool now mis-reports the curvature column, and its own
selftest is red** (card `t_88879c37`). It takes the delegated gate's *exit status* as the
curvature verdict, and since the fold that status is a two-ruler answer — so a level-only
failure is printed as a curvature failure:

```
$ /usr/bin/python3 music/scripts/loop_seam_check.py \
    --master …/t_6f0d261e/loop/faded.wav --loop-points …/t_6f0d261e/loop/lp.json
FAIL loop_seam_check
  master   : …/t_6f0d261e/loop/faded.wav
  curvature: FAIL 2.21x
    seam     : curvature ratio 2.21x (max 3.0x)     ← the gate's own line: this is a PASS
    fix: remove the fade-out / level ramp at the loop end; re-render and re-run the gate
  level    : FAIL tail-1s -29.9 dB vs head-1s -21.1 dB (delta 8.8 dB, max 6.0)
    the rubric's `loop_safety` reject (fade-out on a game-loop claim)
rc=1

$ /usr/bin/python3 music/scripts/loop_seam_check.py --selftest
artifact                curvature         level (tail vs head)  verdict
A_seamless             PASS 1.57x   PASS 0.0 dB (-3.0 vs -3.0)     PASS
B_faded                FAIL 2.21x  FAIL 8.9 dB (-11.9 vs -3.0)     FAIL      ← should read PASS 2.21x
C_phaseslip            FAIL 5.99x   PASS 0.0 dB (-3.0 vs -3.0)     FAIL
D_truncated           FAIL 34.01x   PASS 0.0 dB (-3.0 vs -3.0)     FAIL

FAIL loop_seam_check --selftest: documented behaviour did NOT reproduce:
  - B_faded: curvature ruler measured FAIL, documented PASS (2.21)
rc=1
```

So the correct reading of `loop/faded.wav` today is: **curvature PASS 2.21×, level FAIL Δ 8.8 dB,
verdict FAIL** — and the §9 table above is the authority for that, not the tool's curvature
column. The tool's finding still reproduces; only its report is wrong. That defect is
`t_88879c37`, and it matters because the defect shipped from *this* file's first pass
(`456d525`) and nothing ran the selftest.

The selftest builds its own four fixtures at a given `--bpm`/`--bars`, so the finding is
reproducible from the repo alone, without the probe directories under any card's workspace.

## 10. Stage plan for this genre (skips locked)

`brief` ✓ → `genre-select` → **`lyrics` SKIPPED** (instrumental: the template's empty-box
statement is the spec and `is_instrumental_template` keys on it; there is no lyric sheet to
write and no authorship claim to record — §6) → `generate` (quota gate first; **two
generations per week**, and the plan's `bpm` must read **150**, not 100/120/156) → `curate`
(pick the winner; record a reject reason per loser) → `stems` (≥ 4, ±0.5 s, plus the distinct
instrumental render) → `master` (`gate_loudness --target streaming`, −14 ±1; the gate measures
ffmpeg `volumedetect` mean_volume, **RMS dB, not gated LUFS** — that dialect is deliberate and
is documented in the gate's own header (`gate_loudness.py:14–18`: "architecture pins
volumedetect as the pipeline's measurement tool … a mastering-grade LUFS reading is a separate
instrument"). Card `t_9546841b` is `done`. Measured on the real master by this pass: **PASS,
mean_volume −13.10 dB, max 0.00 dB, deviation +0.90 dB**) → `gate` (independent review,
different model than the producer, against `music/rubrics/gamer.json`: pass threshold 7.0 on
the geometric-median panel aggregate (`music/rubrics/panel.py:463`; `:462` is blank); **4 criteria apply to
this genre** — `battle_energy` 3, `loop_safety` 3, `asset_packaging` 1, `loudness_target` 1,
weights summing to 8 — measured via `panel.applicable_criteria(rubric, "elemental-fire")`. The
file defines 6 criteria; `chip_timbre_authenticity` is scoped to `chiptune-8bit` and
`elemental_atmosphere` to the other three elementals, and `panel.rubric_scope_defects()`
reports none. The "5 criteria, 3/3/3/1/1" reading this brief first carried was wrong for this
genre) → `package`
(`gate_sync_ready --lane game-assets` + `gate_release_ready` + `gate_stems_present` +
`gate_loop_points`, which runs both rulers since card `t_bab8aa19` — curvature ≤ 3.0× **and**
tail/head level delta ≤ 6 dB, so the separate call §9 asked for is no longer required;
`music/scripts/loop_seam_check.py` stays as the standalone cross-check; `loop_points.json`;
ISRC with no
check digit) → `visual` (**applies** — `video_shape: loop-10min`: a 600.0 s visual, exactly
5 × the 120.0 s master, that passes `gate_youtube_authentic`, ≥ 10 distinct frames, with
`ai_disclosure.txt`) → `human-approval` (j_kro) → `publish` (private/draft only).

The visual has a real tension to resolve at the visual stage: the template requires the
visual cycle to **tile seamlessly** ("ember positions reset exactly") while
`gate_youtube_authentic` requires **≥ 10 distinct 64×64-gray frame signatures** sampled every
2.0 s. A short visual tile repeated verbatim fights the distinct-frame check — and this was
MEASURED, not assumed. Three synthetic 600.0 s (loop-10min) visuals were built and put
through the real gate — **re-run by this pass on the stored probes, all three reproduce
exactly (300 / 300 / 290 samples → 22 / 21 / 170 distinct, all PASS)**:

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
- The board now carries **12 elemental cards** (4 genres × 3 oracle waves — the 7.2, 7.5 and
  7.7 titles) and **42 oracle cards** in total for 14 genres. Measured 16:07 by this pass: 34
  `done`, 8 open survivors, one per genre; measured again at 16:2x: 40 `done`, 2 `running`
  (**this** card and elemental-water's) — the other survivors finished during this pass, so
  the open set is transient but the invariant is not: exactly one open card per genre
  (`music/scripts/check_oracle_board.py` PASS both times). The dedupe itself is card
  `t_bf0e5edd` (assignee `oracle`, **`done`**); do not create a new card for it. This brief's
  chain is owned by the newest card, `t_97494e6a`; `t_6f0d261e` and `t_42a01e18` are closed.

## 12. Provenance

- Registry: `music/genres.yaml` (lines 86–93), `music/lanes.yaml` — validated live
  (`/usr/bin/python3 music/registry.py validate` → 14 genres, 10 lanes)
- Template: `music/prompts/elemental-fire.md` (4008 B; style field 583/1000 chars measured)
- Visual: `music/visuals/element-fire.md` (1522 B — grown by the loop-tile
  decision's visual-period correction, §16); fixture `music/visuals/element_fire.mp4`
  (5.000 s, 1280×720, 14133 B) — FAILs the real gate, measured
- Gates exercised live (re-run 2026-10-16 by this pass): `gate_quota` PASS (0/60, studio
  exports 0); `gate_sync_ready --lane game-assets` FAIL on an empty package (full requirement
  list quoted in §3 — the list has grown since the first pass); `gate_release_ready` FAIL
  (quoted, still verbatim); `gate_stems_present` FAIL (quoted);
  `gate_loop_points` PASS on a seamless loop (1.56×, Δ 0.0 dB) and **FAIL on the faded loop**
  (§9 — this is the fix; the first pass measured a false PASS); `gate_youtube_authentic` FAIL
  on the 5 s fixture (quoted); `gate_loudness` PASS on the delivered master (−13.10 dB, +0.90)
- Oracle math: `music/oracle.py:75` (the `WEIGHTS` dict) and its scorer functions,
  `music/oracle.py` lines 179–305 — every score component re-executed live
  against the registry and `music/quota-ledger.json`; `score_genre()` takes
  `(genre_name, genre_spec, lanes, quota)` and `WEIGHTS` sums to 1.0 (both re-measured).
  **t_e86c2110: this cited `lines 54, 179–305`; `WEIGHTS` is at 75 — see §15.**
- Rubric: `music/rubrics/gamer.json` (family `gamer`, includes `elemental-fire`;
  pass_threshold 7.0; **applicable to this genre: `battle_energy` 3, `loop_safety` 3,
  `asset_packaging` 1, `loudness_target` 1** — measured through `panel.applicable_criteria()`,
  not read off the file's 6 entries)
- Autonomy: `music/autonomy.yaml` (all three lanes `advisory`)
- Rights: `music/docs/pro-registration.md` §1 (AI-Assisted vs AI-Generated Output),
  §3 (what disqualifies a track), §4 (the standing rule covers vocal tracks only)
- ISRC: IFPI International ISRC Agency Bulletin 2015/01 rev 3 (ISO 3901:2019) — 12
  characters, no check digit; `music/gates/gate_release_ready.py:92 isrc_syntax()` implements
  the element rules correctly while its own docstring (**now `:15–17`**, re-read this pass)
  still claims a check digit
- Upstream truth: **read from the checkout now, not from git objects** (the tree is 0 behind
  `origin/main`; §14 row 9): `music/suno-gen.py` on disk (42 652 B,
  `is_instrumental_template` at `:141`, elemental-fire named at `:152`),
  `music/sunolocal/translate.py` (bpm 120 / style_weight mapping / `key = style` — the
  repo MIRROR, which is not the deployed code; see §5),
  `music/sunolocal/checks/g3_translate.sh:21` (asserts the DEFAULT `bpm == 120` — still true
  for a request with no explicit bpm)
- **Dangling reference — RESOLVED (`t_b0a4db92`, `done`):** `brain/playbooks/music-lane-architecture.md`
  is cited as "READ FIRST" by this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`,
  `autonomy.yaml` and the gates, and the copy **now exists on this machine** (45 674 B,
  re-measured 2026-10-16T17:47 CDT — the doc grew with card `t_d6b0cb36`, superseding the
  16:07 figure), as
  does `brain/research/music-monetization-2026.md` (11 067 B). The quoted section numbers
  (§3, §5, §13) are now referenceable — the gates' §13 licence citation above is one of them.
- Visual probe: three synthetic 600.0 s visuals built and run through the real gate —
  tiled-seamless 22 distinct / 300 samples, tiled+flicker 21 / 300, continuous 170 / 290 (all
  three re-run this pass, identical); a 160×90 variant FAILs on the 640×360 floor
  (`gate_youtube_authentic.py:146`, re-read — the line still holds). Probe scripts:
  `…/workspaces/t_6f0d261e/probe_visual.py`, `probe_loop.py` (both still on disk)
- **Status of everything this brief carded — re-read on the board this pass** (`done` unless
  stated): the loop-gate fold **t_bab8aa19** `done` (§9, commit `ae05548`); the queue entry
  **t_28146d70** `done` (the genre is queued and rendered, §8); instrument/tempo/key render
  gaps **t_25a6499c** `done`; the diverged checkout **t_8a715681** `done`; oracle duplication
  **t_bf0e5edd** `done`; the missing architecture docs **t_b0a4db92** `done`; the
  `gate_loudness` ruler **t_9546841b** `done` (dialect kept, §10); `battle_energy` scoping
  **t_426a82a3** `done`; the queue entries for the sibling elementals `t_909069f0` /
  `t_b8afb055` `done`. Still open, each already owned: **t_b75ccb4a** (`ready`, the 4-bar loop vs
  the 600 s video shape, §2/§4), **t_d6b0cb36** (`ready`, the render log undercounts the delivered
  renders — §8), **t_d7f6d053** (`ready`, elemental-earth has no delivered loop — not this genre),
  **t_75aacf8b** / **t_a14e5d52** / **t_41f354be** (profile workdir, kanban env vars, scheduler
  units on the wrong checkout), and the defect this pass found, **t_88879c37** (§9's tool). The
  1.0 s short-fade hole **t_8297d2c6** is now `done` (end guard landed, commit `a664b4e`, §9);
  nothing else needed a new card.
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
| §4 | 75-bar sheet 9+12+12+12+9+12+9, 120.0 s; `MAX_DURATION_S` 420 | sums exact; `planner.py` line 83 held `MAX_DURATION_S = 420` in the 13:51 tree (`git show 456d525:music/planner/planner.py` line 83) — true then, and the line moved when `52ae620` rewrote that block (§14 row 5) | ✓ |
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
  also closed the practical hole: the package stage had a callable that FAILs a faded loop
  even while `gate_loop_points` passed it. **That fold has now landed** — `gate_loop_points`
  itself runs the level ruler since card `t_bab8aa19` (lane commit `ae05548`), so this runner is
  the independent second opinion, not the only guard.
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

*(Everything in this section is the state at 13:50. It is superseded by §14 — the file has
four commits now: `49d506b`, `456d525`, `67c99a8` and the surviving-card pass. The 15-commit
divergence, the "8 elemental / 28 oracle cards" census and the §9 false pass are all gone.)*

## 14. Surviving-card verification pass — `t_97494e6a`, 2026-10-16T16:07 CDT

**Disposition: this card is the surviving open card for the genre, and the brief stage's
artifact already exists.** Briefs in this lane are keyed by **genre**, not by card, so all
three elemental-fire oracle cards resolve to this one file. This pass wrote no second brief and
started no second stage chain: it re-measured every checkable claim against live state,
corrected the 22 findings below in place, and left a record. `t_6f0d261e` (7.5) and
`t_42a01e18` (7.7) are the superseded 2026-10-09 pair, both `done`.

**Oracle ruling applied.** The card title says 7.2; the live re-score is **7.0/10** — the
number the oracle's dedupe ruling on this card carries (comment 2026-10-16 14:19). The
0.20 that separates the three titles is `WEIGHTS['trend_signal'] × (5.0 − 3.0)`, the premium
the pre-`b2d11f7` `except` branch paid to a FAILED trend fetch; `b2d11f7` scores a failed
fetch and an empty success alike at the no-signal floor, so the surviving card's number is
the reproducible one.

### Every claim re-measured, live — 22 findings

| # | Claim in this brief | Re-measured 2026-10-16 | Verdict |
|---|---|---|---|
| 1 | Oracle 7.5 with cadence_fit 6.7; "re-run today → 7.0 or 7.2" | `score_genre("elemental-fire", …)` → `total 7.0`, cadence_fit `3.3333`, trend `3.0` (live fetch timed out; the determinism check shows an empty 200 scores the same) | CORRECTED (§1) |
| 2 | `registry OK: 14 genres, 10 lanes` | `registry OK: 14 genres, 10 lanes, 1 stage gate rule(s)` + a `stage gate visual` line | CORRECTED (§1) |
| 3 | `gate_sync_ready` empty-package list (8 track-shaped reasons) | 17 reasons, pack-mode: manifest schema fields, `pack_manifest` counts, `loop_points.json`, clearance, `ai_disclosure.txt`, `LICENCE.txt` | CORRECTED (§3) |
| 4 | `gate_stems_present`: `only 0 stem(s) …; 4 required` | `only 0 stem(s) in <dir>; 4 required` | CORRECTED (§3) |
| 5 | `planner.py` `MAX_DURATION_S` = **420**, and the claim was cited at `planner.py` line 83 | `MIN_DURATION_S = 30` (`:103`), `MAX_DURATION_S = 600` (`:104`); line 83 is a blank line now, which `check_brief_line_refs.py` flagged (it held `MAX_DURATION_S = 420` in the 13:51 tree — the line moved when `52ae620` rewrote the block) | CORRECTED (§4; this was the one citation that check failed on in this file) |
| 6 | The planner "falls back to **100 BPM**" with no blueprint | **150**, measured by running `planner.py plan --genre elemental-fire` with no `--bpm`: `bpm_in_caption` reads the template (`:279`), `bpm_anchor_for` chains at `:203–212` | CORRECTED (§5) |
| 7 | "only `activist`, `chill-lounge`, `trance`" have a lyric blueprint | **7** blueprints (activist, anime-ending, anime-opening, chill-lounge, epic-orchestral-boss, jungle-dnb, trance); still none for elemental-fire | CORRECTED (§5, §8) |
| 8 | The deployed `translate.py` makes 150 BPM unreachable at 80 % style adherence | The repo mirror still does, but it is NOT the deployed code: the live engine (sunolocal **v0.1.3**) takes an **explicit `bpm`, which wins**. The plan on disk reads `bpm 150` | CORRECTED (§5, §7) |
| 9 | `music/suno-gen.py` "is not in this checkout"; tree **15 behind** `origin/main` | On disk (42 652 B, `is_instrumental_template` `:141`); `main` @ `2611770` = **0 behind / 73 ahead** `origin/main` (`t_8a715681` done) | CORRECTED (§7, §12, header) |
| 10 | "No lyric sheet and no blueprint… no masters" (genre unrendered) | Plan `/var/lib/music-plans/elemental-fire-emberfall.json` exists: `bpm 150`, `key D Phrygian`, `duration 120`, `instrumental true`, bare tag sheet (queued by `t_28146d70`, done) | CORRECTED (§7, §8) |
| 11 | (same) | Master rendered: `/var/lib/music-plans/elemental-fire-emberfall.flac`, **120.000 s**, 48 kHz stereo, `sha256 013339ab…`, `.rendered` marker; **not** in `music/quota-ledger.json` (card `t_d6b0cb36`) | CORRECTED (§8) |
| 12 | "the master loop is 120.0 s (75 bars)… tiles exactly 5×" | Delivered loop is **4 bars / 6.400 s** (PASSes both rulers); 4 does not tile 600 s (93.75); the 120 s master ends in **4.787 s of digital silence** (`115.196687 .. 119.983688`). Card `t_b75ccb4a` owns the decision | CORRECTED (§2, §4) |
| 13 | §9's headline: `gate_loop_points` PASSES a broken loop | **FIXED** (fold, `t_bab8aa19`/`ae05548`): `loop/faded.wav` now FAILs — curvature 2.21× under the ceiling, level Δ 8.8 dB over it; `loop2/B_faded` Δ 8.9 dB; A still PASSes, C 5.99× / D 34.01× still FAIL | CORRECTED (§9) |
| 14 | `loop_seam_check.py` prints `curvature: PASS 2.21x` and `SELFTEST PASS` | It now prints `curvature: FAIL 2.21x` (it inherits the delegated gate's two-ruler exit status) and `--selftest` is **red, rc=1**: "B_faded: curvature ruler measured FAIL, documented PASS (2.21)". Its finding is still right; its report is not. **New card `t_88879c37`** | NEW DEFECT (§9) |
| 15 | The `loop2/` table's per-render numbers | They reproduce — but only with loop points that match each artifact. `loop2/lp.json` is pinned to `25.59886621315193` (D_truncated's length), and running A/B/C through the gate with it reports `34.01x / 3.04x / 34.57x` — a verdict about the loop points, not the audio | CORRECTED (§9, caveat added) |
| 16 | Rubric panel: "5 criteria… weights 3/3/3/1/1" | **4 criteria apply**: `battle_energy` 3, `loop_safety` 3, `asset_packaging` 1, `loudness_target` 1 (sum 8), via `panel.applicable_criteria()`; the file's other two are scoped elsewhere; `rubric_scope_defects()` → none | CORRECTED (§9, §10, §12) |
| 17 | `gate_loudness` measures `volumedetect` mean_volume, "known ruler defect" | It does — and that dialect is deliberate (`gate_loudness.py:14–18`); `t_9546841b` is `done`. On the delivered master: **PASS, −13.10 dB, +0.90 dB deviation** | CORRECTED (§10, §12) |
| 18 | Visual probes: 22 / 21 / 170 distinct | Re-ran the real gate on the stored probes: **22 / 21 / 170**, 300/300/290 samples, all PASS; floor line `gate_youtube_authentic.py:146` still holds | REPRODUCED (§10) |
| 19 | Fixture `element_fire.mp4` = 5.000 s, 1280×720, 14 133 B, FAILs the gate | `ffprobe` 5.000 s / 1280×720 / 14 133 B; gate FAIL with the same 2-signature reason | REPRODUCED (§8, §12) |
| 20 | Board: 8 elemental cards, 28 oracle cards | **12** elemental (4 genres × 3 waves), **42** oracle for 14 genres — 40 `done` + 2 `running`, one open card per genre (`check_oracle_board.py` PASS). `t_bf0e5edd` done | CORRECTED (§11) |
| 21 | `brain/playbooks/music-lane-architecture.md` + `brain/research/music-monetization-2026.md` "no copy exists on this machine" | Both exist — `brain/playbooks/music-lane-architecture.md` is 45 674 B (re-measured 2026-10-16T17:47 CDT; it grew with card `t_d6b0cb36`, superseding the 16:07 figure) and `brain/research/music-monetization-2026.md` is 11 067 B; `t_b0a4db92` done, so §13's licence citation is referenceable. Also re-read: `isrc_syntax` `:92`, its docstring's check-digit claim now `:15–17` | CORRECTED (§12; the size re-measured by `t_b75ccb4a`) |
| 22 | §13's own dated numbers (15 behind; "two commits"; 56-of-58 figures) | History of that pass, kept as such. The live values are §14's: 0 behind, four commits, and `check_brief_figures.py` now recomputes **119 of 120** lane-wide (the one miss is `elemental-water.md`, carded `t_34f496d7`) | HISTORY (superseded) |

### Checks run after the edit (all quoted from real runs)

`check_brief_figures.py` — FAIL lane-wide on 1 of 120 recomputed figures, and it is **not** in
this file (`elemental-water.md:600`, card `t_34f496d7`); this file's figures all recompute ·
`check_brief_drift.py` — **PASS** (15 live counts; the blueprint census is now written in the
shape the checker recognises, so it is guarded from here on) · `check_brief_line_refs.py` —
**PASS lane-wide, 118 citations, 52 skipped**; elemental-fire's `planner.py` line-83 cite is
cleared (the other briefs' cites were corrected by their own workers during this pass) ·
`check_brief_paths.py` — PASS (22 `mining-k8s/…` citations) ·
`check_brief_absences.py` — FAIL lane-wide on 10 stale "path is absent" claims, none in this
file (they are `activist`, `chiptune-8bit`, `elemental-air`, `elemental-earth`,
`epic-orchestral-boss`, `jungle-dnb`, `anime-opening` — card `t_bdb94fb7`) ·
`check_stage_scripts.py` — PASS (11/11) · `check_prompt_style_counts.py` — PASS (15 claims /
14 templates) · `check_oracle_board.py` — PASS (one open card per genre; 8 at 16:07, 2 at
16:2x as survivors finished) · `check_oracle_determinism.py` — PASS.
`music/tests` loop suite: **15 tests, OK**.

### Deliverable + supersession

Path-scoped commit on `music/briefs/elemental-fire.md` (this file only; `brief.json` was left
as `t_bab8aa19` wrote it). It supersedes the revision the surviving card inherited —
`sha256 040693b7c8ca758d108f5e0bf56e3f017a29d63a4d69b05077d97a50024a19da`, 42628 B —
and that supersession is recorded in the header with the earlier one. Nothing else was
modified, and the only new card is `t_88879c37` (§9's tool defect), whose acceptance is a green
`loop_seam_check --selftest` wired into a scheduled runner.

hotspot: `music/briefs/` — this file was written and re-verified by three `music-producer` cards
on 2026-10-16 while other workers wrote the 13 sibling briefs in the same tree; every write
needs a path-scoped commit and a lock retry. `music/briefs/elemental-fire.md` now holds four
commits, all on this genre.

---

## 15. Citation sweep — `t_e86c2110`, 2026-10-16T16:45 CDT

That card was filed for the `genres.yaml` defaults-range class in two OTHER briefs; it found those
two sites already fixed, and found this file's last remaining defect while verifying the regression
repo-wide: two references to line 54 of `music/oracle.py`, which is a BLANK line.

| Section | Claimed | Measured live at 16:45 CDT | Verdict |
|---|---|---|---|
| §1 score block | the weights were cited at line 54 of `music/oracle.py` | line 54 is empty; `WEIGHTS = {` is line **75**, holding `quota_headroom 0.25 / lane_coverage 0.20 / revenue_potential 0.20 / cadence_fit 0.15 / policy_risk 0.10 / trend_signal 0.10` — every value the sentence claims | **corrected** |
| §12 provenance | "lines 54, 179–305" of `music/oracle.py` | 179 is `def load_quota()` and 305 is inside `trend_signal_score()` — the range holds; only the leading 54 was blank | **corrected** |

Why it drifted: `oracle.py` grew its stage-marker block (its comment now names card `t_6599927d`),
which pushed `WEIGHTS` from 54 to 75. No figure, gate result, lane, registry value or `brief.json`
was touched.

### What the regression itself needed

`music/scripts/check_brief_line_refs.py` could not finish. Its link-gap pattern nested a repeat
inside a repeat over two overlapping character classes — the `(a+)+` shape — so it backtracked
exponentially on any gap that fails to match: 8 spaces then `#` measured 0.002 s, 12 → 0.27 s,
16 → 35 s. `music/briefs/elemental-water.md` aligns a trailing comment 23 spaces out inside a
fenced transcript, so one brief took >45 s and the repo-wide run >200 s: **this file's two sites
were invisible because the tool never reached them.** The pattern is now one unrolled alternation
that accepts the same language (brute-forced over every string up to length 6: 0 disagreements),
the repo-wide run takes **0.8 s**, and `--selftest` asserts the incident gap stays under 50 ms.

- **Superseded revision of this file:** `sha256 eac7238cab6cc98e3257200e4828e1fd3d9e866d4c7126263d4095610f080bc4` (67041 B, 921 lines).
- **Superseded by this pass (card `t_6dd13d76`, 2026-10-16T17:22-05:00 CDT):** `sha256 0fa019b079dd738f1bf4f93ff593e6beb41335fd0fd62262ca4e8df70ac96ef1` (960 lines / 69893 B) — §8's plan reading was refreshed against the live file (`/var/lib/music-plans/` is rewritten by every planning pass; the 15:07 reading was the earlier plan) and §10's panel citation was re-pointed from `music/rubrics/panel.py:462` to `:463` —  `:462` is blank and `:463` opens `call_judge`, the block the prose names. The plan's own content claims (bpm 150, `D Phrygian`, 120 s, instrumental, 7 bare section tags) were re-read and still hold. No genre finding was reopened.

---

## 16. The loop-tile decision — `t_b75ccb4a`, 2026-10-16T17:39 CDT

The card: the delivered loop was 4 bars (6.400 s) and 4 does not divide 375, so it tiles
93.75× into the 600.000 s `loop-10min` video — a jump cut at the video's last seam. The
genre's own §4 had locked 120.0 s (75 bars) *for exactly this reason*, and 75 bars turned
out to be unreachable. This section decides one answer. **Nothing was re-rendered:** the
master and the delivered loop on nexus are the artifacts `t_28146d70` verified, and every
number below is a measurement taken in this pass (2026-10-16 ~22:00–22:40 UTC).

### The decision

**The delivered loop for a `loop-10min` genre is declared per genre in `music/genres.yaml`
as `loop_bars` — a whole number of bars — and for `elemental-fire` it is 25 bars =
40.000 s, which tiles exactly 15× into the 600.000 s video.**

The rule, which is what makes the value checkable rather than declared:

```
bar_s      = 240 / bpm                      a 4/4 bar; at 150 BPM exactly 1.600 s
shape_bars = 600.0 / bar_s = 2.5 x bpm      the shape's bar count — TEMPO-DEPENDENT
loop_bars  must DIVIDE shape_bars           or the video's last seam is a jump cut
span       = loop_bars x bar_s              must be <= 120.000 s (ceiling: the
                                            master-loop length the briefs locked)
                                            and    >=  24.000 s (floor: below
                                            that it is a fragment, not a phrase)
tiles      = 600.0 / span                   must be an INTEGER
```

`shape_bars = 2.5 × bpm` is the finding that reframed the card's own question. The card asks
"which divisor of 375", but 375 is only the 150 BPM answer: **205** bars at 82 BPM, **220** at
88, **230** at 92. So no single number is right for the shape — the legal set is a function of
the genre's tempo, and the declared value is therefore per genre. The card's own reasoning
already had this shape once: `elemental-water`'s brief independently derived **41 bars =
120.000 s** for its own 82 BPM, and the rule above reproduces it exactly.

### The per-genre values, and the arithmetic

Tempo read from each template's own caption through the planner's own
`planner.bpm_in_caption()` (none of these five genres has a lyric blueprint, so the caption is
the whole resolution chain); the shape's duration from `music/visuals/loop_10min.mp4`, measured
**600.000000 s** by ffprobe.

| Genre | bpm | shape_bars | `loop_bars` | span | tiles into 600 s | why this one |
|---|---|---|---|---|---|---|
| `elemental-fire` | 150 | 375 | **25** | **40.000 s** | **15.000** | 75 bars (120.000 s) is REFUSED on a 120.000 s render — see below; 25 is the largest divisor that survives |
| `elemental-water` | 82 | 205 | 41 | 120.000 s | 5.000 | the ceiling; matches this genre's own brief |
| `elemental-earth` | 88 | 220 | 44 | 120.000 s | 5.000 | the ceiling |
| `elemental-air` | 92 | 230 | 46 | 120.000 s | 5.000 | the ceiling |
| `chiptune-8bit` | 150 | 375 | 75 | 120.000 s | 5.000 | the ceiling — its queue entry plans a 600 s render, so 375 bars is whole-bar and the render is long enough |

Exact arithmetic, `Fraction`, not float (a float is how 93.75 hides):

```
fire   150 BPM: bar 1.600 s   loop 25 x 1.600 = 40.000 s   600 / 40.000 = 15     EXACT
water   82 BPM: bar 2.926829  loop 41 x 2.926829 = 120.000 s  600 / 120.000 = 5 EXACT
earth   88 BPM: bar 2.727273  loop 44 x 2.727273 = 120.000 s  600 / 120.000 = 5 EXACT
air     92 BPM: bar 2.608696  loop 46 x 2.608696 = 120.000 s  600 / 120.000 = 5 EXACT
chip   150 BPM: loop 75 x 1.600 = 120.000 s                   600 / 120.000 = 5 EXACT

the delivered 4-bar loop: 4 x 1.600 = 6.400 s                 600 / 6.400   = 93.75 FRACTIONAL
```

### Why 25 and not 15 for `elemental-fire`

Both 15 bars (24.000 s, 25 tiles) and 25 bars (40.000 s, 15 tiles) are legal, deliverable, and
pass both rulers — measured on the real master in this pass. 25 is taken, on three measured
grounds and one product one:

1. **It is the largest legal length this render can carry.** Measured with
   `loop_close.py` driven at each length against the delivered master (probe
   `…/workspaces/t_b75ccb4a/probe_loops_result.json`): 75 bars → **rc=1**, *"the musical
   region (115.197s) is shorter than one 120.000s loop — nothing to close"*. The ACE node
   emits 4.803 s of digital silence inside its own 120.000 s window, so a loop as long as the
   render can never be closed. 25 bars is the next divisor down.
2. **It closes on the best seam of the four lengths measured** — 0.0 dB tail/head level
   delta, against 0.3 dB (4 bars), 1.0 dB (5 bars), 2.0 dB (15 bars) — and passes all three
   rulers of `gate_loop_points.py` (rc=0: curvature 0.33×, level Δ 0.0 dB, end-ramp −1.8 dB)
   plus `loop_seam_check.py` (rc=0).
3. **It wraps 15× instead of 25×.** Fewer seams in the 600 s video is fewer chances of an
   audible one, and the tile is the longest phrase the render supports, i.e. it discards the
   least of the master's 75-bar arc.
4. **15 bars would invert this genre's own loop ladder.** §2 specs cutdowns at 25.6 s and
   51.2 s "for in-engine use"; a 24.000 s delivered loop would be shorter than the genre's own
   shortest cutdown and the video would be built from that fragment.

### Where it lives (question 2)

`music/genres.yaml` — a `loop_bars` key on each of the five loop-claiming genres, with the rule
and the arithmetic written out in the gamer-family comment block, and the schema note updated.
**Not** in the rail: the rail already reads this file (its PyYAML-free reader in
`music/scripts/loop_close.py` resolves each genre's `video_shape` at runtime), and a length
hardcoded in `cronjob-render.yaml` could not follow a genre. The field is enforced by a new
lane check, `music/scripts/check_loop_tiling.py` — 12-case `--selftest`, run in this pass:

```
$ /usr/bin/python3 music/scripts/check_loop_tiling.py
elemental-fire      loop-10min      150         375         25    40.000   15.00  OK
    legal: 15 (24.000s/25x), 25 (40.000s/15x), 75 (120.000s/5x)   [tempo: template caption]
… (5 loop-claiming genres, all OK)
PASS check_loop_tiling (5 loop-claiming genre(s): every declared loop_bars divides
its shape's bar count exactly)
```

Its selftest reproduces this card's incident (`4 bars @150 BPM → 93.75 tiles FAILS`), the
shipped values, `4 bars @88 BPM` (which *does* tile 55× and still fails the 24 s phrase
floor), and every fail-closed path (no field, no tempo, unreadable shape artifact, a field on
a shape that is not tiled). The failure it guards against is not "a wrong number", it is
"nothing checked the contract": the tiling arithmetic previously lived in this brief's prose,
which is why a 4-bar loop reached the rail.

### Audio and visual (question 3)

**The visual cycle must share the delivered loop's own period** — for `elemental-fire` 25 bars
= 40.000 s, not the 8-bar / 12.800 s cycle `music/visuals/element-fire.md` currently asks for.
Two reasons, one structural and one measured:

- The visual's motion grammar is driven by the audio's own events (taiko hits → ember flares,
  ostinato → shimmer speed, the reprise downbeat → the white-hot flash). A visual period that
  differs from the audio's re-phases the audio's arc against the picture after the first
  cycle: the "peak flash on the reprise" lands somewhere else every time. One period for the
  whole video is also what makes the video exactly periodic — every seam, audio and visual,
  is the same seam.
- The spec's 8-bar figure does not tile 600 s at all: 600 / 12.8 = **46.875**. A shared
  40.000 s period gives 15.000 for both.
- Measured (`gate_youtube_authentic`, real gate, synthetic 600 s tiled visuals in
  `…/workspaces/t_b75ccb4a/vis_probe/`): a 12.8 s tile → **22 distinct** frame signatures,
  a 24.0 s tile → **12**, a 40.0 s tile → **12**, against the gate's floor of 10. So the
  §10 warning holds and is sharper than it was: a tiled visual clears the floor with only
  **2 signatures of headroom** at either candidate length, and the distinct count is set by
  the tile length, not by how busy the picture looks. The visual stage must measure the
  distinct count on the real 600 s render; if it lands near 10, lengthen the cycle.

`music/visuals/element-fire.md` is corrected in place by this pass to name the loop's period.

### What was not re-decided

- **`BARS_PREFERRED = 4` in `music/assets/pack.py` stays.** It is the PACK lane's own cutdown
  default and is bound bitwise to the rail's port by `music/tests/test_loop_close.py`.
  Deciding otherwise would change every loop-claiming genre's cutdowns. Recorded here so a
  later reader does not "fix" the pack to match this number: a pack cutdown loop is repeated
  by the game engine, which will loop any length it is handed — it carries **no tiling
  requirement**. Only the video tile does.
- **Nothing re-rendered.** The master (`sha256 013339ab…a82382f`, 120.000000 s) and the
  delivered loop (`sha256 a5e3dd5d…12aa9c5`, 6.400000 s) are the artifacts `t_28146d70`
  verified. The 6.400 s loop is now **out of contract** and the rail-side card below rebuilds
  it at 25 bars; until then, `loop_points.json` on disk still describes the 4-bar artifact and
  is correct about *that* artifact (it passes both rulers).
- **No sibling brief was edited in this pass**, and none is left unspecified: `elemental-water`
  already states 41 bars = 120.000 s (the value this rule derives); `elemental-earth` (4 bars
  = 10.909 s), `elemental-air` and `chiptune-8bit` carry loop lengths that the registry field
  now supersedes — card `t_00d3dbbd` owns correcting those three in prose.

### Checks run after the edit (all quoted from real runs, 2026-10-16T17:47 CDT)

`/usr/bin/python3 music/registry.py validate` → rc=0, `14 genres, 10 lanes, 1 stage gate
rule(s), 1 derived product(s)` (the new `loop_bars` key changes nothing the validator
requires) · `music/scripts/check_loop_tiling.py` → rc=0, the five genres table above ·
`--selftest` → rc=0, 12 cases · `check_brief_figures.py` → **clean for this file** (the
lane-wide FAIL is 7 stale claims in six OTHER briefs about the architecture playbook's size,
which grew to 45 674 B in `6725ed7`; this file's two sites were corrected here, card
`t_b29712b8` owns the rest) · `check_brief_drift.py` → PASS (22 live counts) ·
`check_brief_line_refs.py` → this file's citations all resolve (117 OK lane-wide; the rc=1
lane-wide failures are in `jungle-dnb.md` and `elemental-*`'s own ranges, not here) ·
`check_brief_paths.py` → PASS (21 `mining-k8s/…` citations) · `check_video_shapes.py` → PASS
(2 pre-existing WARNs) · `check_stage_scripts.py` → PASS (21 script paths) ·
`python3 -m unittest music.tests.test_loop_close` → OK, 15 tests (the pack parity is intact —
this pass did not touch `loop_close.py` or `pack.py`).

The visual-period correction grew `music/visuals/element-fire.md` to **1522 B** (35 lines), so
the two claims in this file that cite its size were re-measured in the same edit. (Do not
write the previous size as a `B` figure when citing it: `check_brief_figures.py` parses any
such token against the referent in the sentence and flags the sentence you just corrected.)
`brain/playbooks/music-lane-architecture.md`'s size was re-measured the same way
(45 674 B), because `check_brief_figures.py` had it stale here too.

### Handoff

`music/genres.yaml` (the field + the rule), `music/scripts/check_loop_tiling.py` (the check),
`music/visuals/element-fire.md` (the visual period), and this file (§2, §4, §16) are the
decision. The rail side — building the delivered loop at the declared length, refusing a
length that does not tile, and wiring the check into the scheduled matrix — is
**`t_2f4fae09`** (assignee `nexus-core`).

hotspot: `music/briefs/` — this file was written and re-verified by four `music-producer`
cards on 2026-10-16 and sits in a directory ~8 concurrent workers write; every write needs a
path-scoped commit and a lock retry. `music/scripts/run_gate_matrix.sh` and
`music/gates/check_gate_suite.sh` were being edited by sibling cards during this pass, so this
decision touched neither.
