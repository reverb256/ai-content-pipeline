# Brief — elemental-water

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`; on this board the cards are
> assigned `music-producer` and claimed by the generic kanban dispatcher). The stage prompt
> advances this card to `genre-select`, and the driver reads the LAST `stage:` marker — so the
> surviving chain resumes at the stage after brief.
> **Card:** **t_354d5d25** (`music-oracle: elemental-water (score 7.2)`) — the SURVIVING card.
> **Superseded twin cards (both `done`):** t_d3b9e218 (`… (score 7.5)`), t_d8cc0a38
> (`… (score 7.7)`) — same genre, same three lanes. All three resolve to THIS brief: briefs are
> keyed by **genre**, not by card (precedent: `music/briefs/commentary-beds.md`). No second
> brief was written and no second chain was started.
> **Written:** 2026-10-16T13:20-05:00 (CDT)
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `49d506b` (main — HEAD when this brief was
> written; it moved 6 times during the run, to `89d6eb2` by the time of writing this line).
> **6 cards were `running` on this board** while this brief was written (5 music briefs +
> `t_aba9d2c3`), and 15 commits landed in the last 40 minutes.
>
> **Surviving-card pass — every claim below re-measured 2026-10-16 16:10–16:45 CDT
> (`t_354d5d25`).** The contradictions are resolved in place; §16 records what moved. Four
> header figures were true when written and have moved. None of them changes the brief:
>
> | Header claim (at write time) | Re-measured 2026-10-16 16:1x–16:4x CDT |
> |---|---|
> | twin `t_d8cc0a38` `running` | **`done`** — both twins closed; this card is the only open `elemental-water` card on the board (`check_oracle_board` rc=0 names it running) |
> | local `main` @ `89d6eb2`; pair 0 behind / 61 ahead at `e40c7f9` (15:31) | @ **`e597bb6`**, **0 behind / 81 ahead** of `origin/main` (`ba28f55`) — 21 commits landed since 15:31 |
> | 6 cards `running` (5 music briefs + `t_aba9d2c3`) | **7 `running`** — `t_97494e6a` (elemental-fire oracle twin), `t_354d5d25` (this card), `t_99e6d789` (ops), `t_eb648761` (oracle trend-signal), `t_e86c2110`/`t_e2375c5a`/`t_fa731c5b` (music-producer). Board census: **108 done / 36 ready / 8 blocked / 7 running / 4 todo / 1 archived** |
> | the score is a frozen 7.5 or a 7.00–7.20 spread | **7.00/10, and reproducible**: `b2d11f7` removed the failed-fetch premium, so both fetch branches now score 7.0 (§2, §11a). The 7.2 in this card's title is the pre-fix broken-fetch number |
>
> Superseded revisions of this file, each recorded in the commit that replaced it:
> 1. `sha256 578e8dd10ab9bc6d45c034fa09b10b1880735b485e963a26eed376613137d26d` — the write-time
>    revision; header figures + §2 trend state corrected by the duplicate pass (`t_d8cc0a38`, 13:52 CDT).
> 2. `sha256 b3284178afd72ca29714abc2e743466d754da7539ee718b0b79c8738a07a0d0d` (653 lines /
>    40590 B) — the aged divergence + blueprint-census counts corrected by `t_0f7aed63` (15:34).
> 3. `sha256 6478e55ceee1267a299abf2ff0a95f6d4987ae826ba71e8eb8ff9a3ca27cf52a` (669 lines /
>    41998 B) — census restated when `music/lyrics/blueprints/jungle-dnb.yaml` landed
>    (`t_e6d422ec`, 15:56).
> 4. `sha256 3f19591d395550df4778cd21bdf461690b8848bf6923b192f202efb578cceca4` (671 lines /
>    42450 B) — **superseded by THIS pass** (`t_354d5d25`); §16 lists the classes it corrected.
>
> **Oracle (card title):** 7.2/10. **Oracle (measured now, live):** **7.00/10**, reproduced by
> `music/oracle.py --dry-run` in this pass. 7.00 ≥ 5.0, so the routing verdict — produce — is
> unchanged. The number was never demand evidence; §2 gives the root cause and the fix.


## 1. Genre resolution (live, not transcribed)

```
$ /usr/bin/python3 music/registry.py validate
registry OK: 14 genres, 10 lanes, 1 stage gate rule(s)
genres: activist, anime-ending, anime-opening, chill-lounge, chiptune-8bit, commentary-beds, elemental-air, elemental-earth, elemental-fire, elemental-water, epic-orchestral-boss, jungle-dnb, sentimental-piano, trance
lanes: direct-fan, direct-license, game-assets, stock-ai-native, streaming, sync, sync-documentary, youtube-gaming, youtube-longform, youtube-mix
stage gate visual: lane_gate -> gate_youtube_authentic (when_absent: none)
quota ledger: period 2026-10, standard 0/60 (warn_at 55, hard_stop_at 58)
```

*Re-measured 2026-10-16 16:2x CDT (surviving-card pass).* Two lines changed since the write-time
transcript: the count line now ends **`, 1 stage gate rule(s)`**, and a new
`stage gate visual:` line prints the lane→gate resolution the `visual` stage runs on
(added with the genre-aware visual gate, card `t_d9983bb9`). The genre row is unchanged.


| Field | Value | Source |
|---|---|---|
| Genre | `elemental-water` | `music/genres.yaml` |
| Family | `gamer` | — |
| Prompt template | `music/prompts/elemental-water.md` (3810 B, resolves) | registry |
| Visual style | `music/visuals/element-water.md` (1046 B, resolves) | registry |
| Lanes | `game-assets`, `youtube-gaming`, `streaming` | registry |
| Cadence | 2/wk | registry |
| Video shape | `loop-10min` | registry |
| Registry note | **absent** — the block carries no `notes:` key | `elemental-fire` has one; this does not |

**Interpreter trap, measured (again).** Plain `python3 music/registry.py validate` fails in a
worker shell with `ModuleNotFoundError: No module named 'yaml'`: `python3` resolves to
`/home/j_kro/.hermes/tools/python-3.14.7+…/bin/python3` (3.14.7, no PyYAML). `/usr/bin/python3`
(3.14.7) has PyYAML and validates cleanly. Always use `/usr/bin/python3` for `music/*.py`.

## 2. The card's score is 7.0 — fixed, and reproducible from the tree

The card says 7.2. Re-scoring the same genre right now gives **7.00**, and the same command
gave the same number before and after this pass:

```
$ /usr/bin/python3 music/oracle.py --dry-run
  warn: trend fetch failed for elemental-water (URLError(TimeoutError('timed out'))); scoring it as no signal (3.0)
  elemental-water: 7.0/10
  [DRY RUN] Would create card: music-oracle: elemental-water (score 7.0)
```

Per component, read from `score_genre()` live and compared with the card body:

| Component | Card | Measured now | Why it moved |
|---|---|---|---|
| quota_headroom | 10.0 | **10.0** | `10·(1 − 0/58)` — ledger `0/60` (unchanged) |
| lane_coverage | 6.0 | **6.0** | `min(3 viable × 2, 10)` — static |
| revenue_potential | 8.0 | **8.0** | lane revenue bands — static |
| cadence_fit | 6.7 | **3.3333** | **time-dependent** (see below) |
| policy_risk | 9.0 | **9.0** | `10 − 1` (one `youtube-gaming` lane penalty) |
| trend_signal | 5.0 (the failed fetch) | **3.0** | the failed-fetch premium was **removed** — `b2d11f7` |

`10·0.25 + 6·0.20 + 8·0.20 + 3.3333·0.15 + 9·0.10 + 3.0·0.10 = **7.00**` — re-computed with
`oracle.WEIGHTS` in this pass, and the card's title score is unreachable from the current code.

**`cadence_fit` decays as the quota period advances.** `oracle.py:221-254` computes
`days_remaining = (last_day_of_period − now).days`, `weeks_remaining = max(days/7, 0.5)`,
`expected_tracks = per_week × weeks_remaining`, then `(expected_tracks − 2)/6 × 10`. Measured
2026-10-16 16:2x CDT: period `2026-10`, last day `2026-10-31`, **14 days remaining** → `2/wk ×
2.0 = 4.0` expected → `(4.0 − 2)/6 × 10 = 3.3333`. The card was created **2026-10-09 03:27 CDT**
(epoch `1791534471`), when ~21 days remained and the same expression gave 6.7. Same genre, same
registry, different period position — this component is a calendar reading, not demand.

**The 7.2 vs 7.0 difference was a failed web fetch, and it is fixed.** `trend_signal_score()`
(`oracle.py:283-305`) scrapes `https://html.duckduckgo.com/html/?q=<genre> music trend 2026` and
counts `class="result__snippet"` occurrences. `b2d11f7` made **both** non-answers score the same
floor — a working fetch that finds nothing *and* a fetch that raises:

```python
TREND_NO_SIGNAL = 3.0                      # oracle.py:280
        if count >= 5:  return 10.0
        elif count == 0: return TREND_NO_SIGNAL      # 200 with no snippets
        else: return TREND_NO_SIGNAL + (count / 5.0) * 7.0
    except Exception as exc:
        # A failed probe is degraded signal, not a bonus. Report it so the ...
```

The observable consequence is the `warn:` line in the transcript above: a timeout, a 403 or a
DNS failure now *reports itself* and scores 3.0 instead of silently paying 5.0. The three
network states this genre was measured in across the day — 200-with-zero-snippets, 403, socket
timeout — now all score the same:


```
$ /usr/bin/python3 trend_probe.py
elemental-water      snippet_matches=  0  html_bytes=  14280  -> trend_signal_score=3.0
chill-lounge         snippet_matches=  0  html_bytes=  14292  -> trend_signal_score=3.0
trance               snippet_matches=  0  html_bytes=  14262  -> trend_signal_score=3.0
sentimental-piano    FETCH FAILED (HTTPError: HTTP Error 403: Forbidden) -> trend_signal_score=5.0
```

*History, kept because it is the evidence for the fix.* Re-measured 2026-10-16 13:51 CDT
(duplicate pass, `t_d8cc0a38`) the same probe against the same endpoint returned **no HTTP
status at all** — all five genres timed out, and under the pre-fix code that scored **5.0**
each:

```
$ /usr/bin/python3 trend_probe.py                       # 2026-10-16 13:51 CDT, pre-fix behaviour
elemental-water      FETCH FAILED (URLError: <urlopen error timed out>) -> trend_signal_score=5.0
chill-lounge         FETCH FAILED (URLError: <urlopen error timed out>) -> trend_signal_score=5.0
trance               FETCH FAILED (URLError: <urlopen error timed out>) -> trend_signal_score=5.0
sentimental-piano    FETCH FAILED (URLError: <urlopen error timed out>) -> trend_signal_score=5.0
elemental-fire       FETCH FAILED (URLError: <urlopen error timed out>) -> trend_signal_score=5.0
```

So the observation *"returns HTTP 200 with ~14.3 KB and zero matching snippets, so every genre
in the registry scores 3.0"* described **one of three observed states**, and two of the three
paid the broken fetch **more**. That was the defect. After `b2d11f7` the three states are
indistinguishable in the score, and this pass measured that directly, with the fetch stubbed
both ways so the measurement does not depend on the network:

```
$ /usr/bin/python3 re-measure probe (fetch stubbed: 200-with-no-snippets vs urlopen raising)
 genre                  200/0-snippet  fetch-fails  delta
  activist               7.0            7.0          0.0
  anime-ending           7.4            7.4          0.0
  anime-opening          7.3            7.3          0.0
  chill-lounge           8.4            8.4          0.0
  chiptune-8bit          7.0            7.0          0.0
  commentary-beds        8.1            8.1          0.0
  elemental-air          7.0            7.0          0.0
  elemental-earth        7.0            7.0          0.0
  elemental-fire         7.0            7.0          0.0
  elemental-water        7.0            7.0          0.0
  epic-orchestral-boss   7.3            7.3          0.0
  jungle-dnb             6.5            6.5          0.0
  sentimental-piano      8.4            8.4          0.0
  trance                 7.8            7.8          0.0
max |delta|: 0.0   |  genres above the 6.0 produce line: 14 of 14  |  range 6.5 - 8.4
```

**The 0.20 pair-delta no longer exists.** It was `WEIGHTS['trend_signal'] × (5.0 − 3.0)`, i.e.
exactly the failed-fetch premium, and every one of the 14 duplicate pairs carried it. The board
still shows the old numbers on the superseded cards — **43 oracle cards for 14 genres: 41 `done`,
2 `running`** (this card and its `elemental-fire` twin) — because a card title is a record of the
run that emitted it, not a live reading. `check_oracle_board` (rc=0, live) confirms every open
genre carries exactly one open card, which is the invariant `t_bf0e5edd` (now `done`) asked for.

**`trend_signal` still carries no usable signal**, and no stage should read it as demand: the
search string is the registry's invented slug (`elemental-water music trend 2026`), which matches
nothing in any corpus, and it floors at `TREND_NO_SIGNAL = 3.0` by construction for every genre.

**Consequence for this brief: none for the go/no-go.** 7.00 ≥ 5.0 → produce. Downstream stages
must not read a card title as a live measurement, and must not treat the historical 0.20 as
evidence that one run saw more demand than another.


## 3. What the genre IS

The reference point is stated in the template: David Wise's **"Aquatic Ambience"** (Donkey Kong
Country, 1994). The template's seven craft notes are the acceptance frame, and three of them are
load-bearing because a generic "underwater pad" generation misses them:

1. **Wave-sequencing / evolving arpeggios are the core sound.** Aquatic Ambience came from a Korg
   Wavestation preset ("The Wave Song") — eight samples cycling so the bass and arp continuously
   **evolve**. *A static arp is a pad; a morphing arp is water.*
2. **Minor key with add9/ninth harmony** — the benchmark's DNA (`Cmadd9 – Abadd9 – F7sus4 –
   Bbadd9`). The emotional target is Wise's own description: **sad and uplifting at once.** Not
   ominous, not cheerful.
3. **Pitch-bent whale-call tones** (Shepard-style illusions that seem to rise forever) — the
   signature melodic gesture.
4. **Percussion as sonar, not drums.** Morphing pings and filtered ticks read as submarine
   distance; a drum kit is out of genre.
5. **Tempo 80–90, slow harmonic rhythm.** Water does not rush; motion lives in texture, not
   harmony.
6. **Cavernous reverb is the space itself** — the listener is suspended in a medium.
7. **Loop discipline**, same as every gamer genre: stems + loop point + `seamless_loop`.

Template reject line, verbatim: *"A generation with a drum kit, major-key bounce, or menace is
OUT of genre — reject it."* The template's own header calls it a **"Water-level / exploration
theme"** — utility music for a game level, not a track to listen to once.

## 4. Tempo, and the loop math that falls out of it (derived, measured)

Stated tempo: **82 BPM**, 4/4 (style field; craft note 5 anchors the pocket at 80–90). One bar is
therefore **not** a whole number of seconds:

```
1 bar  = 240/82        = 2.9268292682 s
4 bars =                = 11.7073 s
8 bars =                = 23.4146 s
32 bars =               = 93.6585 s
205 bars =              = 600.0000 s   <- exactly 10:00
```

**Finding — 82 BPM divides the 10-minute shape exactly.** `600 / (240/82) = 205.0000 bars`. The
`loop-10min` video shape is a whole-bar, zero-remainder duration. Because
`41 × 240/82 = 9840/82 = 120.000 s` exactly:

| Unit | Bars | Duration | Use |
|---|---|---|---|
| loop unit | **41** | **120.000 s** | the audio loop point: state `loop_start_s 0.0 → loop_end_s 120.0` |
| video shape | **205** | **600.000 s** | `loop-10min`, exactly 5 × the loop unit |

**Decisions locked here so no later stage re-derives them:**

- **The genre-native loop unit is 41 bars = 120.000 s**, not a "standard" 32 bars: 32 bars is
  93.6585 s, which lands mid-nowhere in both the loop point and the 10-minute shape. Use 41.
- **Second-aligned cutdowns are impossible at this tempo.** A bar is 2.926829 s, so there is no
  useful sub-second grid. Any cutdown must be specified in **bars**, and its real duration stated
  (8 bars = 23.415 s, not "23 s"). Do not repeat the commentary-beds pattern of asking for a
  15 s cut — at 82 BPM 15 s is 5.125 bars.
- The outro must resolve into the intro's texture (template tag sheet: *"arps thin back to the
  intro texture — LOOP POINT into bar 1"*), so the loop point is at 0.0 and the **tail must wrap**.
- **`gate_loop_points` is the gate that governs this, and it is currently defective** — see §5.

## 5. Target lanes and the gates that will actually run

From `music/lanes.yaml`, each one exercised live:

| Lane | Surface | Gate | Required artifacts |
|---|---|---|---|
| `game-assets` | itch.io, unity-asset-store, gamedev-market | `gate_sync_ready` (+ `loop_points.json`) | `stems`, `loop_point`, `seamless_loop`, `metadata` |
| `youtube-gaming` | youtube | `gate_youtube_authentic` | (visual) |
| `streaming` | distributor (DistroKid; alt TuneCore) | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` |

`game-assets` is the PRIMARY lane for this genre — it is the first lane in the registry list and
the only one whose requirements include a loop point. Measured against an empty package
directory, this is the exact requirement list the package stage must satisfy:

```
$ /usr/bin/python3 music/gates/gate_sync_ready.py --package-dir <empty dir> --lane game-assets
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

*Re-measured 2026-10-16 16:2x CDT (surviving-card pass).* Two classes were added since the
write-time run: the `pack_manifest` declaration counts (`loops`, `stems`) and `LICENCE.txt`
(the licence template now exists at `music/licences/perpetual_game_asset_v1.txt`). The write-time
transcript's first four findings (`full_mix.wav`, `stems/`, `instrumental.wav`) are gone because
the gate now reads the pack manifest instead of probing those filenames — the requirement list
the package stage must satisfy is the one above, and `pack.py` is the generator the runbook names.

The full gate matrix is green on its own fixtures — re-run in this pass:


```
$ bash music/gates/check_gate_suite.sh
interpreter: /usr/bin/python3
…
OK: every gate passed its good artifact and failed its broken one
```

**Two measurement facts the stems stage must plan for:**

- **≥4 stems, each ffprobe-measured within ±0.5 s of the master.** The template's parts map
  cleanly onto four: (1) morphing wave-sequence arps, (2) the minor-add9 melody, (3) sub-bass
  "currents", (4) sonar-ping percussion + whale-call textures. A water theme has no vocal to
  make a fifth; the count is satisfiable without padding.
- `instrumental.wav` **must differ byte-wise from `full_mix.wav`** (`gate_sync_ready` rejects a
  copy), and *this genre is already instrumental* — so ship the alternate mix (e.g. the arps +
  space pass without melody) and say which variation it is in the manifest. Same trap the
  commentary-beds kit hit.

**`gate_loop_points` — the curvature-only false pass was found by a sibling and has since been
FIXED.** The fire sibling (card `t_6f0d261e`) measured that `gate_loop_points` **passed a loop
with a 1.6 s fade-out tail at 2.21× curvature**, because it measured junction *curvature* (a
derivative kink) and a linear fade introduces no kink. Card `t_bab8aa19` (nexus-core, now `done`)
added the missing ruler. Re-run in this pass, the gate now measures both properties and the
suite asserts each one:

```
## gate_loop_points
PASS  seamless loop (1.6x curvature) passes
FAILS phase-slip loop (6.0x curvature) fails (exit 1, as expected)
FAILS faded loop tail fails on the LEVEL ruler, not the curvature one (exit 1, refused for "loop level drops", as expected)

## gate_loop_points --pack-dir (checks EVERY loop)
FAILS pack: a faded loop is not seamless (LEVEL ruler, not curvature) (exit 1, refused for "loop level drops", as expected)
FAILS pack: no loop_points.json fails (exit 1, as expected)
```

That does not lower this genre's risk, it moves it: the template asks for a reverb-heavy,
blurred texture, and the most likely correct-sounding ending is a tail that thins — exactly the
shape that was invisible before. The seam must therefore be cut to a **level-neutral** tail
(the gate's own reading), and the reviewer still owes the tail/head RMS comparison on top of
`loop_points.json` at `0.0 → 120.0 s`.


## 6. Audio identity (locked for this genre)

Style field, measured at **537/1000 chars** — identical to the header's declared count:

```
underwater cave ambient theme, 82 BPM, evolving wave-sequencing synth arpeggios that morph
between bell, glass and bubble timbres, slow melancholic melody in a minor key with add9 color,
soft electric-piano chords, deep sub-bass swell like slow currents, pitch-bent whale-call synth
tones that seem to rise forever, sparse morphing percussion like distant sonar pings, reverb-heavy
cavernous space, bubbles and filtered water textures, everything breathes and never rushes, dreamy
floating sad-but-comforting, seamless game loop, C minor
```

Settings, from the template: **Weirdness 55 %** (water benefits from strangeness, but the melody
must stay findable) · **Style Influence 70 %** · **Exclude Styles:**
`drums kit, aggressive percussion, EDM, vocals, major key pop, horror drone`.

Lyrics: **empty box, always** — Suno's instrumental path. Structure comes from the optional tag
sheet (535 chars / 21 lines: `[Intro]`, 3 × `[Instrumental]`, `[Instrumental Break]`, `[Outro]`),
which uses section tags and parenthetical direction and **never singable words**.

Key/tempo metadata the package must state: **C minor, 82 BPM, 4/4.**

## 7. Visual — `loop-10min`, and the YouTube-authentic defense

`music/visuals/element-water.md` (1046 B) is a full visual spec, so unlike a
`video_shape: none` genre the `visual` stage **does** apply and goes to videobot:

- Palette: deep teal `#0b2e33`, mid cyan `#1e6f78`, caustic light `#cdeef2`, bioluminescent
  accents `#6ff2c8` (sparse). Scenes: sunlit shallows / abyssal drift / cavern lake; god rays;
  suspended particles.
- Motion grammar is a *drift budget*: rays 0.5°/s, particles 1–3 px/s, kelp sway 6–10 s period.
  **Nothing moves faster than bubbles rise.** This is a constraint, not a mood description — a
  drifting-but-busy render violates the spec.
- Loop & variation, which is what `gate_youtube_authentic` measures: **rotate shallows / cavern /
  abyss per upload. Same palette, different depth.** The gate samples frames, hashes them, and
  fails a raw dump on shot diversity and on Jaccard similarity against prior uploads; the suite
  measured "5 distinct scenes, low similarity" PASS vs "static image" FAIL. The three named scenes
  are the intended rotation set — same palette across uploads is safe, same **frames** is not.
- Audio-visual sync: arp cycle → caustic shimmer phase; whale-call → one distant large shape
  passing the rays per phrase; breakdown → light dims to abyssal blue-green, then returns.

Cover art (streaming/game-assets metadata) is not content: flat teal-with-caustic mark, the
palette above.

## 8. ✓ The rubric was fixed — this genre's scored set is now explicit (was the blocking finding)

`music/rubrics/gamer.json` (family `gamer`, pass threshold **7.0** on the geometric-median panel
aggregate) was rewritten on 2026-10-16 (commit `56dc465`, card `t_426a82a3`, now `done`) — and
this section's original finding is what drove the fix. The review stage now resolves scope from
**data**, not from prose:

```
$ /usr/bin/python3 music/rubrics/panel.py applicable set, read live (music/rubrics/gamer.json v2)
  elemental-water   Σw=8  need>=56.0  ['elemental_atmosphere', 'loop_safety', 'asset_packaging', 'loudness_target']
```

| Criterion | Weight | `applies_to` (live) | Scored for `elemental-water`? |
|---|---|---|---|
| `elemental_atmosphere` | 3 | elemental-air, elemental-water, elemental-earth | **yes** — the NEW exploration-craft criterion |
| `loop_safety` | 3 | *(no field → whole family)* | **yes** |
| `asset_packaging` | 1 | *(no field → whole family)* | **yes** |
| `loudness_target` | 1 | *(no field → whole family)* | **yes** |
| `battle_energy` | 3 | **elemental-fire, epic-orchestral-boss** | no — out of scope for this genre |
| `chip_timbre_authenticity` | 3 | chiptune-8bit | no — out of scope for this genre |

`applicable_criteria()` (`music/rubrics/panel.py`) drops an out-of-scope criterion and its weight;
a correct `elemental-water` track must therefore earn **≥56 of the 80 weighted points available
(7.0 × 8)** across the four criteria above. The `chip_timbre_authenticity` name-shadowing problem
is gone as well: the criterion is named for its idiom, not for a string prefix.

**Reject signals are scoped to the same data.** `boss_no_fast_tempo` ("boss/battle claim with no
fast-tempo candidate (under 130 BPM)") now applies **only** to `elemental-fire` and
`epic-orchestral-boss`, and a new `elemental_fight_material` signal rejects the opposite error —
"elemental-air, elemental-water or elemental-earth delivered as a fight: drum-kit groove, bass
drop, or a 130+ BPM battle claim on an exploration-theme label (= OUT of genre, the element is
wrong)".

**What the original §8 measured, kept as the record of why the rubric changed.** The pre-fix file
scoped `battle_energy` to the string `elemental-*`, so a *correct* water theme was graded against
a fight criterion whose own anchor demands 130–200 BPM (typical 140–180) and whose guide ends
`"1 = slow ambient track with a battle label"`. Measured from the templates:

| Genre | Stated tempo | Template's own words |
|---|---|---|
| `elemental-fire` | **150 BPM** | "Boss/battle theme for the fire element" → battle_energy **is** correct |
| `elemental-water` | **82 BPM** | "underwater cave ambient theme" · "Water does not rush" |
| `elemental-earth` | **88 BPM** | "ancient cavern earth theme" · "patient and heavy" |
| `elemental-air` | **92 BPM** | "open sky heights theme" · "no percussion kit, no bass weight" |

82 BPM is 63 % of the anchor's lowest tempo, so under the old scope the rubric's own
`reject_signals` entry *"boss/battle claim with no fast-tempo candidate (under 130 BPM)"* fired
on a **correct** water theme. The fixed rubric carries the 82/88/92 BPM split as its own
justification: the new criterion's anchor cites the 70–100 BPM game-exploration/open-world pocket
(tunee "Exploration & Open World" 70–100 against its own Boss Battle 130–170; Mubert exploration
70–90 against action 120–140) and the 75 BPM / C minor `Aquatic Ambience` water-level benchmark —
this genre's own reference point from §3.


*History — the contradiction that produced the fix.* The v1 file's own `notes` said
*"elemental-\* tracks choose per their prompt; chiptune-8bit MUST pass chip_timbre_authenticity;
**battle tracks MUST pass battle_energy**"*, while the criterion's `scope` string said the
broader `elemental-*`. The computed consequences that were measured then, for the reviewer's
benefit:

```
Non-battle scope (loop 3 + packaging 1 + loudness 1 = weight 5, need 35 pts):
  a correct track scoring 7.0 or better on all three PASSES (35/5 = 7.0 exactly).
Battle scope applied as the name read (chip dropped, total weight 8, need 56 pts):
  a track scoring 10/10/10 on loop/packaging/loudness still needed battle_energy >= 2.0.
  battle_energy = 1 -> aggregate 6.625  FAIL  (the score the guide prescribes for 82 BPM ambient)
If a judge scored the N/A chip criterion as 0 instead of dropping it (total weight 11):
  only battle_energy = 10 could reach 7.0 (7.273); every correct water theme FAILED.
```

The v2 file resolves that arithmetic by construction: the scored set is now exactly the
four-criterion set above, the out-of-scope criteria are dropped **with their weight**, and
`music/rubrics/test_panel_math.py` enforces the invariants. The live `notes` field states the
rule:

> Sub-idiom scope is DATA, not prose: a criterion that carries `applies_to` is scored ONLY for
> the genres it names; a criterion without the field is common to the whole family
> (`music/rubrics/panel.py applicable_criteria(); music/rubrics/test_panel_math.py` enforces the
> invariants). Three sub-idioms live in this family, each with one craft criterion at weight 3:
> battle (elemental-fire, epic-orchestral-boss → `battle_energy`), chip (chiptune-8bit →
> `chip_timbre_authenticity`), elemental exploration (elemental-air, elemental-water,
> elemental-earth → `elemental_atmosphere`).

**DECISION for this genre, restated against the fixed rubric:** the reviewer scores
**`elemental_atmosphere` (w3), `loop_safety` (w3), `asset_packaging` (w1), `loudness_target`
(w1)** — Σw 8, pass at ≥7.0 (≥56 weighted points) on the geometric-median panel aggregate.
`battle_energy` and `chip_timbre_authenticity` are out of the genre's scope and are **not
scored, zeroed, or judged** — that is now the file's own rule, not a producer-side exception.
The same set applies to `elemental-earth` and `elemental-air`; `elemental-fire` and
`epic-orchestral-boss` take `battle_energy` instead of `elemental_atmosphere`.

**Ownership:** the fix landed through `editor` (card `t_426a82a3`) after this brief's finding was
corroborated by the elemental-air and elemental-earth briefs. This section records the decision
and the live measurement; it does not edit the grading sheet. The follow-up card about stale §8
text in the sibling briefs is `t_1a5b018b` — this pass resolved its `elemental-water` leg here
and leaves the `elemental-air` leg to that card.


## 9. Generation path — three blockers, measured on the live engine

The lane's own generate prompt names `music/suno-gen.py`. **That file is in this checkout now**
(42 652 B, mtime 14:23 — the reconciliation of card `t_8a715681`); it was missing when §9 was
written, and the lane's own work then sat **15** commits off `origin/main`. Read from the git
object as well as from disk,
`origin/main:music/suno-gen.py:141 is_instrumental_template(genre)` decides whether a track may
render with no human lyric sheet, keying on the template's `## Lyrics guidance` section — and its
docstring **names all four elementals**, `elemental-fire/water/earth/air`. `music/prompts/
elemental-water.md:16` says *"Instrumental. Leave the **lyrics box empty**"*, so this genre is
detected as instrumental and **needs no lyric sheet**. That is why the lyrics stage skips (§13).
Already carded: **t_8a715681** (diverged checkout).

The live route is in-cluster, not the kanban stage machine: ConfigMap `music-pipeline-briefs` →
CronJob `music-pipeline` (plans) → CronJob `music-pipeline-render` (`acestep_plan.py` →
sunolocal studio API). Chart `/home/j_kro/mining-k8s/helm/charts/music-pipeline/`; its payload
already carries `prompts/elemental-water.md`. Measured now:

```
$ kubectl -n mining get configmap music-pipeline-briefs -o jsonpath='{.data}'
{"briefs.json":"[{\"brief\":\"a late-night kitchen…\",\"genre\":\"chill-lounge\",
  \"lyricsMode\":\"draft\",\"name\":\"smoke-chill-lounge\",\"title\":\"Kitchen Light\"}]"}
$ grep -n briefs /home/j_kro/mining-k8s/helm/charts/music-pipeline/values.yaml
39:briefs: []
$ ls /var/lib/music-plans/*.rendered   →  smoke-chill-lounge: "refused", testplan: "refused"
```

Both CronJobs run and `Completed` on schedule — with nothing to render. **No elemental-water brief
is queued anywhere.** The three blockers, all measured:

1. **The planner cannot express "instrumental".** `music/planner/planner.py:528`
   `--lyrics-mode choices=["draft","ai"]`. `draft` emits a scaffold whose section tags have empty
   bodies, and `music/scripts/acestep_plan.py:82` FATALs on empty sections unless `--allow-empty`
   — which is the observed `refused` marker (`"FATAL: N section(s) have no lyrics"`). `ai` would
   write lyrics for a track that must have none, and forfeits the copyrightability the lane's
   HARD RULE 3 exists to protect. An `instrumental` mode is required.
2. **Tempo.** The **deployed** engine hardcodes it. Read from the running pod:
   `/opt/sunolocal/music/sunolocal/translate.py:42 bpm = 120`, overridden only by
   `bpm = int(60 + req.style_weight * 120)` (line 45). The local planner falls back to
   `"bpm": ctx["blueprint"].get("bpm_anchor") or 100` (`planner.py:470`), and **only 7 of the 14 genres have a blueprint**
   (`activist`, `anime-ending`, `anime-opening`, `chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`, `trance`). So this genre plans at 100
   and translates at 120 — both wrong. **Acceptance for this genre: the plan's `bpm` field must
   read 82.** At 100 BPM a bar is 2.40 s and the 41-bar/120.000 s loop unit in §4 is wrong.
3. **Key cannot reach the engine.** `translate.py:49` is `key = req.style or "C major"` — the
   style string is used **as the key**. `music/sunolocal/spec.py`'s `SunoGenerateRequest` has
   `style` and no `key` field, so a 537-char style string would be written into the key slot and
   the genre's **C minor** requirement cannot be expressed at all. `key = req.style` needs a real
   `key` field to read from.

All three are the same family as **t_25a6499c** (instrument/tempo/key render gaps, nexus-core) —
cited here so §§10-12 do not rediscover them, and extended with the three measured line numbers.

## 10. ⚠ The game-assets publish path is built — and stranded on an unmerged ref

`brain/runbooks/music-game-assets.md` is the package stage's contract for this genre's primary
lane. Every artifact it names **exists in the repository — but in exactly one commit, reachable
from no branch this checkout runs.** Measured:

```
$ git log --all --oneline -- music/publish music/docs/GLASS-BREAK.md music/licences
3882292 WIP backup 2026-10-14 (atlas)
$ git log -1 --format="%h %ad %an %s" --date=short 3882292
3882292 2026-10-14 Reverb WIP backup 2026-10-14 (atlas)
$ git branch -a --contains 3882292
  remotes/origin/wip/atlas-backup-20261014
$ git ls-tree -r --name-only 3882292 | grep -E 'music/(publish|lanes|licences)|GLASS-BREAK'
music/cards/glass-break-checklist.md
music/docs/GLASS-BREAK.md          ← the provisioning runbook (has the butler steps, item 3)
music/lanes/game-assets.py         ← the stem-naming convention the runbook names
music/licences/perpetual_game_asset_v1.txt
music/publish/gumroad.py
music/publish/itchio.py
music/publish/playwright/*.py      (distrokid, fab, splice, unity, session, _check_env)
```

None of those paths exist on local `main` **or** on `origin/main`
(`git ls-tree -r --name-only origin/main` lists `music/assets/pack.py` and
`music/docs/{fusion-system-design,pro-registration}.md`, and no `music/publish/`). The local
`wip/atlas-backup-20261014` branch tip (`abcf169`) does **not** contain them either — only the
remote ref does. So the itch.io/Gumroad adapters (card `t_ce063b87`) and the glass-break
provisioning checklist (card `t_14d438ea`) are both `done` on the board while their deliverables
sit on an unmerged WIP backup.

**On this host the only genuinely absent pieces are the human-provisioned ones:**

| Runbook requirement | Measured on this host |
|---|---|
| `butler` (itch.io CLI) | **not installed** — not on PATH, not in `~/.local/bin`, `/usr/local/bin`, `/snap/bin`; referenced only by the runbook |
| `~/.hermes/vault/itch_io_key` | **`~/.hermes/vault/` is absent** — no vault at all |
| adapters / licence / naming / checklist | present in `3882292` only (see above), on no branch this checkout runs |

`music/docs/GLASS-BREAK.md` already contains the exact butler install and login procedure
(`curl -L -o ~/.local/bin/butler https://broth.itch.ovh/butler/linux-amd64/LATEST/default/butler`,
then `butler login`, key from the `wharf` source) — so provisioning is **documented and blocked
only on j_kro**, not unbuilt.

**This does not block the brief or the render; it blocks `publish` for the genre's primary lane.**
It is new evidence for the existing reconciliation card **t_8a715681** (diverged checkout) rather
than a new defect: a third ref — `origin/wip/atlas-backup-20261014` — carries lane work that
neither `main` nor `origin/main` has. Left as a comment on that card.

## 11. Defect fixed in this run (regression check included)

`bash music/gates/check_gate_suite.sh` — the acceptance matrix the runbook and `gates/README.md`
both tell operators to run — reported **BROKEN: 2 check(s) misbehaved** on a clean checkout:

```
BAD   chill-lounge lyrics pass (human claim) (expected exit 0, got 1)
        FATAL: PyYAML is required (pip install pyyaml)
BAD   trance lyrics pass (human claim) (expected exit 0, got 1)
        FATAL: PyYAML is required (pip install pyyaml)
```

**Root cause:** the suite invoked bare `python3` in all 26 places. In a worker shell that is the
Hermes bundled interpreter, which has no PyYAML; `gate_lyrics_original` imports
`music/lyrics/lyrics.py`, which imports `yaml`. Two gates were reported broken that were fine.

**Fix (this run, `music/gates/check_gate_suite.sh`):** resolve **one** interpreter up front —
honour an explicit `PY=` override, else prefer `/usr/bin/python3`, else PATH `python3` — and use
it for every check. If no candidate can `import yaml` the suite now **exits 2 with a FATAL**
instead of reporting a false `BAD`. That FATAL is the regression check: the failure mode was a
silent `ModuleNotFoundError` dressed as a gate defect, and it can no longer pass silently.

**Verified after the fix:** `rc=0`, `interpreter: /usr/bin/python3`, and
`OK: every gate passed its good artifact and failed its broken one` — all 10 gates, PASS on the
good fixture and FAIL on the broken one. `gate_loop_points` measured 1.6× (seamless) vs 6.0×
(phase slip) against the 3.0× ceiling.

**Still open, filed as a new card:** nothing runs this matrix automatically. There is no
`.github/workflows/` in this repo and `scripts/automation/` never calls it. A defect in the gate
library is therefore only found by a human who happens to run the suite — which is exactly how
this one survived.

## 11a. Regression check added in the duplicate pass (`t_d8cc0a38`)

**Failure:** every score this lane quotes as evidence is unreproducible, and the failure mode
is *inverted* — a genre whose trend fetch **breaks** scores higher than the same genre whose
fetch **works**. Nothing detected either property.

**Check:** `music/scripts/check_oracle_determinism.py`. It never touches the network: it
imports `music/oracle.py` and stubs `urllib.request.urlopen`, then measures
`trend_signal_score()` on two branches that differ only in how the fetch behaves — HTTP 200
with zero `result__snippet` matches (the state that floors every genre at 3.0), and `urlopen`
raising (timeout / 403 / DNS). Three assertions: **A1** a failed fetch must not outscore a
successful empty one; **A2** `score_genre()` must be deterministic under a fixed fetch
behaviour, and a failed fetch must not *raise* the total; **A3** `WEIGHTS` must close at 1.0.

**Measured now (rc=1 — the defect is live, cited `t_bf0e5edd`):**

```
$ /usr/bin/python3 music/scripts/check_oracle_determinism.py
trend 200/0-snippet: 3.0   trend fetch-fails: 5.0
total 200/0-snippet: 7.0 (= 7.0)   total fetch-fails: 7.2
WEIGHTS sum       : 1.0
  - A1 VIOLATED: a FAILED trend fetch scores 5.0 but a SUCCESSFUL empty fetch scores 3.0 —
    the broken run outranks the working one by 2.0 on the component, i.e. 0.2 on the 10-point
    total (component delta x WEIGHTS['trend_signal']) ...
  - A2 VIOLATED: a failed trend fetch raises the total for elemental-water (7.2 > 7.0) —
    scoring depends on the network, not on the genre.
FAIL check_oracle_determinism: the trend fetch is not a pure function of the genre
rc=1

$ /usr/bin/python3 music/scripts/check_oracle_determinism.py --selftest
SELFTEST PASS check_oracle_determinism: correct pair (zero=3.0 fail=3.0) errors=0 (want 0),
                                       inverted pair (zero=3.0 fail=5.0) errors=1 (want 1)
rc=0
```

`--selftest` proves the A1 assertion fires on an inverted pair and stays silent on a correct
one, so a future edit that repairs `trend_signal_score()` flips this check to green rather
than leaving it as noise. A failing check on a live, carded defect is the lane's existing
pattern (`check_stage_scripts` fails the same way on `music/suno-gen.py`, cited `t_8a715681`).

## 12. Existing assets for this genre

Measured: **none.** `music/lyrics/` holds `activist/`, `anime-opening/`, `chill-lounge/`, `trance/` plus
`blueprints/{activist,anime-ending,anime-opening,chill-lounge,epic-orchestral-boss,trance}.yaml` — no `elemental-water` sheet or blueprint
(expected: the genre is instrumental, so there is no lyric sheet to write, and no blueprint means
§9's bpm blocker). `music/plans/` holds only `.gitignore`. No campaign directory, master, stem,
loop point, cover or asset pack exists for this genre anywhere in the tree. Quota is untouched:

```
$ /usr/bin/python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

**The first render is genuine work, not a re-run.**

## 13. Stage plan for this genre

`brief` ✓ → `genre-select` → **`lyrics` SKIPPED** (instrumental — the template's empty-box
statement *is* the spec; `is_instrumental_template` names `elemental-water`) → `generate`
(`gate_quota` first; export through **Suno Studio**, never the standard download button) →
`curate` (one reject reason per loser) → `stems` (≥4, each ±0.5 s of the master, plus a
**distinct** instrumental) → `master` (streaming target −14 dB / sync −16 dB per the
`gate_loudness` dialect; note it measures `volumedetect` RMS, not gated LUFS — known ruler defect
**t_9546841b**) → `gate` (independent reviewer, different model, hash-bound; apply the §8 decision)
→ `package` (`gate_sync_ready --lane game-assets`, `loop_points.json` at **0.0 → 120.0 s**,
`gate_release_ready` for streaming) → `visual` (**applies** — `loop-10min`, videobot, same palette
rotating shallows/cavern/abyss, `gate_youtube_authentic`) → `human-approval` (j_kro) → `publish`
(**private/draft only**; game-assets path blocked per §10).

Autonomy: all three lanes are at rung **`advisory`**, `clean_publishes: 0`
(`music/autonomy.yaml`) — every publish is proposed with evidence and approved by j_kro.

## 14. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` — validated live (14 genres, 10 lanes)
- Template: `music/prompts/elemental-water.md` (3810 B; style field measured 537/1000 chars)
- Visual: `music/visuals/element-water.md` (1046 B)
- Runbook: `brain/runbooks/music-game-assets.md` (53 lines) — every executable it names missing (§10)
- Gates: `music/gates/` — `gate_quota` PASS live; `gate_sync_ready` exercised live (FAIL output
  quoted); full suite green after this run's fix (§11)
- Rubric: `music/rubrics/gamer.json` (5 criteria, total weight 11, pass 7.0)
- Autonomy: `music/autonomy.yaml` (game-assets / youtube-gaming / streaming all `advisory`)
- Stage contract: `music/stages.yaml` (`brief` → `producer`; advance calls added in `9c2d2d3`)
- Oracle internals read live: `oracle.py:221-253` (`cadence_fit`), `:272-289` (`trend_signal`),
  `:189-202` (`lane_coverage`), `:256-269` (`policy_risk`), `:439` (dry-run skips the board read)
  — **all five line citations re-verified 2026-10-16 13:52 CDT by the duplicate pass; every one
  still lands on the named function, and `:439` is still the `if not dry_run` board-read guard.**
- Checks run in this pass (`/usr/bin/python3 music/scripts/…`): `check_brief_figures.py
  --briefs music/briefs/elemental-water.md` PASS (7 recomputed figures, 3 skipped as
  cluster-only); `check_oracle_determinism.py` **rc=1 by design** (§11a); `check_brief_paths.py`
  PASS; `check_stage_scripts.py` FAIL on `music/suno-gen.py` (pre-existing, `t_8a715681`);
  `check_prompt_style_counts.py` PASS (15 declared style-field lengths, 14 templates);
  `bash music/gates/check_gate_suite.sh` rc=0
- Upstream truth read from git objects: `origin/main:music/suno-gen.py:141`
  (`is_instrumental_template`), `origin/main:music/sunolocal/translate.py`
- Engine truth read from the running pod: `sunolocal-source-65fcc845d-fd5r6`,
  `/opt/sunolocal/music/sunolocal/translate.py` lines 33-59; `music-pipeline-briefs` ConfigMap
- **Dangling reference — RESOLVED (`t_b0a4db92`, done).** `brain/playbooks/music-lane-architecture.md`
  is cited as "READ FIRST" by this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`,
  `autonomy.yaml` and `gates/*`, and it is in this tree and in `HEAD` now (34 328 B, rewritten at
  `7411afa`, head touching it `6b24a52`). `brain/research/music-monetization-2026.md` (11 067 B)
  is there too. The doc's §2 genre registry carries this genre's row, §3 its lanes and §13 its
  pack lane; `music/scripts/check_doc_refs.py` resolves every `§` reference to a heading. Card
  `t_fa731c5b` stripped this reading from the sibling briefs.
- **Not fixed here (other owners, already carded):** gate_loop_points false pass **t_bab8aa19**;
  instrument/tempo/key render gaps **t_25a6499c**; diverged checkout — now with a **third stranded
  ref**, see §10 — **t_8a715681**; scheduler units running the wrong checkout **t_41f354be**;
  oracle card duplication + the 0.20 trend artifact **t_bf0e5edd** — this pass added the
  reproducibility evidence (the same genre returning 7.0 *and* 7.2 within one session from one
  tree, and the stubbed check that proves it is the fetch branch, §11a) as a comment on that
  card, since the card already owns the root cause; missing architecture docs
  **t_b0a4db92**; profile workdir + kanban env vars **t_75aacf8b**; `gate_loudness` RMS-vs-LUFS
  ruler **t_9546841b**; the game-assets pack failing its own gate **t_5ed495eb**; the
  `battle_energy` mis-scoping **t_426a82a3**.
- **Filed by this brief (one card, after checking the board for duplicates):** the gate matrix is
  never run by anything (§11) → `nexus-core`. The §8 rubric finding and the §10 publish-path
  finding were **already carded** (`t_426a82a3`, `t_5ed495eb` / `t_ce063b87`), so they are
  referenced, not duplicated; §10's stranded-ref measurement is left as a comment on
  **t_8a715681**.
- **hotspot:** `music/briefs/` — concurrent workers write this directory and commit to one
  working tree. Measured while this brief was written: **6 cards `running` on the board** (5
  music briefs + `t_aba9d2c3`) and **13 brief-stage commits plus 2 lane fixes (15 commits) inside
  ~40 minutes** (`4daf132`, `9c2d2d3`, `132a781`, `4bb1ea6`, `1553da2`, `ade6e87`, `9ebf6af`, `7c2f8d1`,
  `880cff1`, `d491663`, `c3e2f23`, `0a24846`, `81c37bb`, `49d506b`), HEAD moving 5 times during
  this run alone. **`music/gates/check_gate_suite.sh` was edited by this brief while
  `elemental-fire` ran** — that sibling's brief named the collision. `music/stages.yaml`,
  `music/oracle.py` and `scripts/automation/*` are also being edited in the same tree.
- **hotspot re-measured 2026-10-16 13:52 CDT (duplicate pass, `t_d8cc0a38`):** the directory is
  still contested. HEAD moved `fa3163f` → `456d525` while this pass ran; **24 commits landed
  between 13:10 and 13:51**; four `music-producer` workers held `running` music-oracle twins
  simultaneously (`t_c92f566d`, `t_42a01e18`, `t_d8cc0a38`, `t_b7dd5655`). This pass adds one new
  file (`music/scripts/check_oracle_determinism.py`) and edits only
  `music/briefs/elemental-water.md` — both untouched by the siblings running beside it
  (earth/fire each touch their own brief; activist touches `music/briefs/activist.md`).

## 15. Aged live counts re-measured (card `t_0f7aed63`, 2026-10-16)

`music/scripts/check_brief_drift.py` (added by card `t_b7dd5655`) flagged this brief on both
families of live count: the clone divergence in the header table and the blueprint census in §9.
Re-measured and corrected in place.

- **Superseded revision of this file:** `sha256 b3284178afd72ca29714abc2e743466d754da7539ee718b0b79c8738a07a0d0d` (653 lines / 40590 B).
- **Clone divergence:** the header pair (29 ahead / 15 behind) holds at `fa3163f` (13:48). At
  `e40c7f9` (15:31) the pair reads 0 behind / 61 ahead: the 15-commit upstream deficit was
  cleared by the reconciliation merge `ab33ad1` (14:23), not by anything this lane did.
- **Blueprint census:** 7 of the 14 genres carry a lyric blueprint (`activist`, `anime-ending`,
  `anime-opening`, `chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`, `trance`); the other 7 do
  not. This genre still has none, so §9 blocker 2 — the flat 100 fallback — stands exactly as
  written. The 2026-10-16 15:31 pass behind this section measured the census at six; what landed
  since is `music/lyrics/blueprints/jungle-dnb.yaml` (card `t_e6d422ec`).
- **Corrected in place:** the header table row 4, §9 blocker 2 and §12's asset listing.
- **Superseded by this pass (card `t_e6d422ec`, 2026-10-16):** `sha256 6478e55ceee1267a299abf2ff0a95f6d4987ae826ba71e8eb8ff9a3ca27cf52a` (669 lines / 41998 B) — the census counts above and in §6.3 were restated as live claims when `music/lyrics/blueprints/jungle-dnb.yaml` landed. The genre's own blocker is untouched.
