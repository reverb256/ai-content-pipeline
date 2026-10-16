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
> 5. `sha256 fb78ecde6d5ae120e4fb7e9e742ee19100f7c6888ddce914310c26a655d5a13b` (971 lines /
>    64 164 B) — two `check_brief_absences.py` findings cleared (`t_bdb94fb7`, 2026-10-16);
>    §17 records them.
> 6. `sha256 e51cd0b293e286d6d98afbfaaaa67806bf97a174903e84685b6a3ed1cf505c71` (1000 lines /
>    65 873 B) — **superseded by THIS pass** (`t_6aa1e97f`): the §14 Runbook bullet's line count
>    corrected from 88 to 133 after the runbook gained the `asset-pack` stage section; §18
>    records it.
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
**battle tracks MUST pass battle_energy**"*, while the criterion's own `name` said the broader
`elemental-*` — `Boss/battle energy (elemental-*, epic-orchestral-boss)`. v1 carried no `scope`
field at all, so nothing read that name. The computed consequences that were measured then, for
the reviewer's benefit:

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


## 9. Generation path — the three blockers are CLOSED; what remains is this genre's queue entry

The lane's own generate prompt names `music/suno-gen.py`. **That file is in this checkout**
(50 030 B, `is_instrumental_template()` at `music/suno-gen.py:265`) — card `t_8a715681`
(diverged checkout, now `done`) reconciled the tree, so the file can be read from disk rather than
from a git object — the pair read **0 behind / 86 ahead** of `origin/main` at 16:50 CDT on
2026-10-16 (the local tip rises with every commit this lane lands) — and `is_instrumental_template()` keys on the template's `## Lyrics guidance` section and
**names all four elementals** (`elemental-fire/water/earth/air`);
`music/prompts/elemental-water.md:16` says *"Instrumental. Leave the **lyrics box empty**"*, so
this genre is detected as instrumental and **needs no lyric sheet** — which is why the `lyrics`
stage skips (§13).

The live route is in-cluster, not the kanban stage machine: the brief queue (Argo Application
`helm/apps/music-pipeline.yaml` `briefs:` → ConfigMap `music-pipeline-briefs`, chart
`/home/j_kro/mining-k8s/helm/charts/music-pipeline/`, whose payload carries
`prompts/elemental-water.md`) → CronJob `music-pipeline` (plans, `17 */6`, last schedule 3 h 53 m
before this measurement) → CronJob `music-pipeline-render` (`41 */4`, last schedule 3 h 29 m) →
pod `sunolocal-source-75d58dbc97-7jfmc`, image **`localhost/sunolocal:v0.1.3`**. Renders now run
per queue card — jobs `music-pipeline-plan-t97c92df2`, `music-pipeline-render-t97c92df2`,
`…-t6d7ad524`, `…-t8c5a6b91` and `music-pipeline-manual-1792181262` all measured `Completed`,
and `/var/lib/sunolocal/artifacts/` holds 9 rendered FLACs from 2026-10-14…10-16 (largest
53.7 MB). **The rail works; it is not short of machinery.**

**The three blockers this section used to carry are all fixed** — cards `t_25a6499c` (render
gaps) and `t_8c5a6b91` (the deployed wrapper dropping the instrumental flag) are both `done`,
and this was re-measured on the running pod and the live planner:

1. **"Instrumental" is now a first-class mode.** `music/planner/planner.py:905`
   `--lyrics-mode choices=["draft", "ai", "instrumental"]`, with a refusal guard: `instrumental`
   on a *vocal* genre exits 2 (`epic-orchestral-boss` is named in the guard), and `draft`/`ai` on
   an instrumental genre warns loudly. The ConfigMap already uses
   `"lyricsMode":"instrumental"` for `elemental-air`, `elemental-earth`, `elemental-fire`,
   `sentimental-piano`, `chill-lounge-slow-gold` and both `commentary-beds` entries — the mode is
   in production use, not merely available.
2. **Tempo is 82 — not 100, and not 120.** The deployed `translate.py` reads an EXPLICIT tempo
   first (`bpm = None`; `if req.bpm is not None: bpm = int(req.bpm)`, pod lines 62-64); the
   `int(60 + req.style_weight × 120)` mapping survives only as a documented fallback and 120 is
   the last-resort default. The planner resolves the genre's own anchor —
   `bpm_anchor_for()` = `ctx["blueprint"].get("bpm_anchor") or ctx.get("template_bpm")`
   (`planner.py:203-212`), with `template_bpm = bpm_in_caption(caption)`. Measured live for this
   genre in this pass:

   ```
   $ /usr/bin/python3 music/planner/planner.py show --genre elemental-water
   { "caption_chars": 537, "blueprint": false, "bpm_anchor": null, "instrumental": true,
     "structure_source": "template",
     "structure": ["Intro","Instrumental","Instrumental","Instrumental Break","Instrumental","Outro"] }
   $ context_for("elemental-water")   →   template_bpm = 82, bpm_anchor_for = 82
   ```

   So the plan's `bpm` reads **82**, the §4 loop math (41 bars = 120.000 s, 205 bars = 600.000 s)
   holds, and the "plans at 100" failure is closed. **Acceptance stands:** the plan's `bpm` field
   must read 82 — and the queue entry should state `bpm: 82` explicitly rather than rely on
   caption parsing.
3. **Key reaches the engine.** `translate.py` (pod line 76) is `key = req.keyscale or "C major"`,
   and `SunoGenerateRequest` carries the sunolocal extensions `bpm` / `keyscale` / `instrumental`.
   The 537-char style string is no longer written into the key slot. **Acceptance for this genre:
   the queue entry must state `keyscale: C minor`.** The planner's own default is the literal
   `"C minor"` (plan path: `args.keyscale or args.key or "C minor"`), which happens to be this
   genre's key — but a default that coincides is not a decision (card `t_f65b0f4c`, running when
   this pass measured, owns exactly that gap; another worker was editing `planner.py` during this
   pass, so the line numbers above are the ones this pass read, not a promise about the file's
   next revision).

**Still open for this genre, and it is not a code defect: `elemental-water` has no queue entry
and no queue card.** Measured: the ConfigMap holds **12 entries across 10 genres** —
`chill-lounge` ×2, `commentary-beds` ×2, `anime-ending`, `epic-orchestral-boss`, `trance`,
`sentimental-piano`, `elemental-air`, `elemental-earth`, `elemental-fire`, `jungle-dnb` — and
**no `elemental-water`**. The Argo Application states the reason in its own words:

```
# NOT in this list, with the reason (so nobody re-derives it):
# - the other 2 instrumental genres (chiptune-8bit, elemental-water):
#   the mode they need now exists (card t_25a6499c), and each has its
#   own queue card on the music board, so each entry is written once by
#   the card that owns the genre's title and duration.
```

Half of that is accurate: the mode exists, and the entries above are the record of what landed
(`t_28146d70` fire, `t_640cc2a1` commentary-beds, `t_6d7ad524` chill-lounge, `t_78bd4754`
epic-orchestral-boss, `t_791b48f7` trance, `t_909069f0` earth, `t_97c92df2` jungle-dnb,
`t_a14e5d52` anime-ending, `t_b8afb055` air — all `done`). The other half is not: **there is no
queue card for `elemental-water` on this board** — measured against every card title containing
`water` and every card whose title contains `queue`. The genre needs the fields such a card owns
(`name`, `title`, `duration`, `bpm: 82`, `keyscale: C minor`, `lyricsMode: instrumental`) before
the render rail can see it. `music/plans/` holds only `.gitignore`, and no plan, master, stem or
render for this genre exists yet (§12).

All three fixed blockers are the family card **t_25a6499c** (instrument/tempo/key render gaps,
nexus-core, `done`); this section keeps the acceptance criteria it produced — `bpm` 82,
`keyscale` C minor, `lyricsMode` instrumental — and the one open item it does not cover.


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

**That "still open" is now closed, too.** `music-gate-matrix.timer` / `.service` were installed
at 15:22 CDT and run the matrix on a schedule; the first logged run is rc=0:

```
2026-10-16T15:22:22-05:00 — gate matrix run starting (repo=/home/j_kro/ai-content-pipeline interpreter=/usr/bin/python3 …)
2026-10-16T15:22:22-05:00 — gate matrix: rc=0 OK pass=18 expected_failures=26 misbehaved=0 fatal=0 interpreter=/usr/bin/python3 duration=272s
$ systemctl --user list-timers music-gate-matrix.timer
Sat 2026-10-17 06:20:00 CDT   14h   music-gate-matrix.timer   music-gate-matrix.service
$ /usr/bin/python3 music/scripts/check_gate_matrix_scheduled.py     → PASS, last run rc=0 state=OK
```

So a defect in the gate library is now found by the timer, not only by a human who happens to
run the suite.


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

**Measured now: rc=0 — the defect is fixed** (`music/oracle.py`, commit `b2d11f7`;
card `t_bf0e5edd` `done`). The check is unchanged; the code under it changed:

```
$ /usr/bin/python3 music/scripts/check_oracle_determinism.py
  warn: trend fetch failed for elemental-water (URLError('stub: fetch failed')); scoring it as no signal (3.0)
  warn: trend fetch failed for elemental-water (URLError('stub')); scoring it as no signal (3.0)
oracle under test : /home/j_kro/ai-content-pipeline/music/oracle.py
genre             : elemental-water
trend 200/0-snippet: 3.0   trend fetch-fails: 3.0
total 200/0-snippet: 7.0 (= 7.0)   total fetch-fails: 7.0
WEIGHTS sum       : 1.0
PASS check_oracle_determinism: trend fetch failure never outscores an empty success; score_genre is deterministic; WEIGHTS closes at 1.0
rc=0

$ /usr/bin/python3 music/scripts/check_oracle_determinism.py --selftest
SELFTEST PASS check_oracle_determinism: correct pair (zero=3.0 fail=3.0) errors=0 (want 0),
                                       inverted pair (zero=3.0 fail=5.0) errors=1 (want 1)
rc=0
```

`--selftest` still proves the A1 assertion fires on an inverted pair and stays silent on a
correct one, so the check cannot go green by rot: it is the code that had to change, and the
independent 14-genre stub measurement in §2 (max |delta| = 0.0) corroborates the verdict from
outside the check itself. The live `warn:` lines above are the same failure being *reported*
instead of paid — the observable behaviour change this pass measured.


## 12. Existing assets for this genre

Measured 2026-10-16 16:3x CDT: **none.** `music/lyrics/` holds `activist/`, `anime-opening/`,
`chill-lounge/`, `trance/` plus `blueprints/{activist,anime-ending,anime-opening,chill-lounge,epic-orchestral-boss,jungle-dnb,trance}.yaml`
— **7 blueprints** (the census §9 uses) and no `elemental-water` sheet or blueprint. That is
expected for an instrumental genre: there is no lyric sheet to write. `music/plans/` holds only
`.gitignore`. No campaign directory, master, stem, loop point, cover or asset pack exists for this
genre anywhere in the tree. The only genre-named visual asset is a prototype clip —
`music/visuals/element_water.mp4`, ffprobe-measured **5.000 s, 1280×720, h264 + aac, 14 812 B**
(2026-10-09) — i.e. a fixture, not the `loop-10min` render §7 specifies. Quota is untouched:

```
$ /usr/bin/python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

The ledger now also carries a `renders[]` log — this lane's local ACE renders consume no Suno
quota and are recorded there instead (the `elemental-air` entry names its job, sha256, measured
duration and `quota_consumed: 0`). **This genre has no such entry**, which is the same fact as
§9's missing queue card, stated from the other side.

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
(`music/autonomy.yaml`: `game-assets`, `youtube-gaming` and `streaming` each carry
`rung: advisory` with zero evidence) — every publish is proposed with evidence and approved by
j_kro. The human gates in `music/stages.yaml` (`human-approval`, with `auto_next: publish`, and
`escalate`) are never auto-dispatched.

**Stage-advance facts that govern the next worker** (re-measured 2026-10-16 16:2x CDT):
`music/stages.yaml` gives the `brief` stage one job, and it is the one this pass closes on — post
the marker `stage: genre-select` on the card **with the `kanban_comment` tool**, because a
dispatcher-spawned worker's terminal is fenced and `hermes kanban --board music comment` is
refused (`t_5a93164a`; `bash scripts/automation/advance-stage.sh <card> genre-select --board
music` is the labelled CLI fallback for the non-worker caller). The `visual` stage resolves its
gate from the genre's own lanes — `/usr/bin/python3 music/registry.py gate-for-stage --stage
visual --genre elemental-water` → `gate_youtube_authentic`, since `youtube-gaming` is one of this
genre's three lanes — rather than assuming the YouTube gate (`t_d9983bb9`).


## 14. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` — validated live (14 genres, 10 lanes)
- Template: `music/prompts/elemental-water.md` (3810 B; style field measured 537/1000 chars)
- Visual: `music/visuals/element-water.md` (1046 B)
- Runbook: `brain/runbooks/music-game-assets.md` (**133 lines**, re-measured again in this pass —
  the write-time transcript said 53, the 16:1x pass measured 88, and the file gained the
  `asset-pack` stage section, §18) — of the executables it names, `butler` and
  `~/.hermes/vault/itch_io_key` are still absent (§10); the pack builder it names is here:
  `music/assets/pack.py` exists
- Gates: `music/gates/` — `gate_quota` PASS live; `gate_sync_ready` exercised live on an empty
  dir (16 findings, quoted in §5); `bash music/gates/check_gate_suite.sh` **rc=0**, interpreter
  `/usr/bin/python3`, on 2026-10-16 16:3x CDT
- Rubric: `music/rubrics/gamer.json` **v2** — 6 criteria, family total weight 14, so each
  `gamer` genre is scored on **Σw 8** (this genre: `elemental_atmosphere`, `loop_safety`,
  `asset_packaging`, `loudness_target`), pass 7.0; scope is data (`applies_to`), enforced by
  `music/rubrics/panel.py` + `test_panel_math.py` (§8)
- Autonomy: `music/autonomy.yaml` (game-assets / youtube-gaming / streaming all `advisory`,
  `clean_publishes: 0`)
- Stage contract: `music/stages.yaml` (`brief` → `producer`) — the brief prompt advances to
  `genre-select` via the kanban tool; advance channel fixed in `7c4fbf2` (`t_5a93164a`), stage
  gate rule in `54f6d3c` (`t_d9983bb9`) (§13)

- Oracle internals read live in **this** pass: `oracle.py:221` (`cadence_fit_score`, body to
  `:254`), `:283` (`trend_signal_score`, body to `:305`, with `TREND_NO_SIGNAL = 3.0` at `:280`),
  `:189` (`lane_coverage_score`), `:256` (`policy_risk_score`), `:158` (`load_quota`), `:312`
  (`score_genre`), `:54` (`WEIGHTS`). Three citations moved since the write: `trend_signal` was
  `:272-289`, `cadence_fit` ends at `:254`, and the dry-run board-read guard is now `:459`
  (was `:439`) with its second use at `:478`
- Checks run in **this** pass (`/usr/bin/python3 music/scripts/…`), all from
  `/home/j_kro/ai-content-pipeline` at `e597bb6`: `check_brief_figures.py` **rc=1 before the
  edit** — its one finding was *this* brief's `53 lines` line (§16), rc=0 after;
  `check_brief_drift.py` rc=0 (2 live counts in this brief); `check_brief_paths.py` rc=0;
  `check_brief_line_refs.py` rc=1 with **no finding naming this brief** (all three name
  `elemental-fire.md`); `check_brief_absence.py` **rc=1 named this brief's `music/suno-gen.py`
  claim — corrected in this pass** (§9); `check_brief_absences.py` rc=1 (findings name
  `activist.md`, `chiptune-8bit.md`, `jungle-dnb.md`); `check_stage_scripts.py` rc=0;
  `check_prompt_style_counts.py` rc=0; `check_oracle_board.py` rc=0 (this card is the single open
  `elemental-water` card); `check_oracle_determinism.py` rc=0 (§11a);
  `check_gate_lane_surface.py`, `check_video_shapes.py` (2 warnings, other genres),
  `check_doc_refs.py`, `check_stage_advance.py`, `check_scheduler_units.py` (NOTE: driver
  `DRY_RUN=1`), `check_gate_matrix_scheduled.py`, `check_brief_bpm_solutions.py` rc=0;
  `bash music/gates/check_gate_suite.sh` rc=0
- Upstream truth read from disk in this pass: `music/suno-gen.py:265` (`is_instrumental_template`)
  — the git-object read the write-time brief used is no longer necessary at 0 behind
- Engine truth read from the running pod in this pass: **`sunolocal-source-75d58dbc97-7jfmc`**,
  image `localhost/sunolocal:v0.1.3` (`/opt/sunolocal/music/sunolocal/translate.py` lines 62-76,
  `spec.py` `SunoGenerateRequest`), plus ConfigMap `music-pipeline-briefs`, the two CronJobs,
  `/var/lib/music-plans/` and `/var/lib/sunolocal/artifacts/`; planner truth from
  `music/planner/planner.py show --genre elemental-water` and `context_for()` called directly

- **Dangling reference — RESOLVED (`t_b0a4db92`, done).** `brain/playbooks/music-lane-architecture.md`
  is cited as "READ FIRST" by this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`,
  `autonomy.yaml` and `gates/*`, and it is in this tree and in `HEAD` now (rewritten at
  `7411afa`, head touching it `6b24a52`). `brain/research/music-monetization-2026.md` (11 067 B)
  is there too. The doc's §2 genre registry carries this genre's row, §3 its lanes and §13 its
  pack lane; `music/scripts/check_doc_refs.py` resolves every `§` reference to a heading. Card
  `t_fa731c5b` stripped this reading from the sibling briefs.
- **Statuses of every card this brief cites, re-measured 2026-10-16 16:2x CDT (board read-only):**
  all `done` — `t_bab8aa19` (gate_loop_points), `t_25a6499c` (render gaps), `t_8c5a6b91` (wrapper
  dropped the instrumental flag), `t_8a715681` (diverged checkout), `t_41f354be` (scheduler
  checkout), `t_bf0e5edd` (oracle duplication + the 0.20 artifact), `t_b0a4db92` (missing
  architecture docs), `t_75aacf8b` (profile workdir + kanban env), `t_9546841b` (`gate_loudness`
  ruler), `t_5ed495eb` (game-assets pack failed its own gate), `t_426a82a3` (`battle_energy`
  mis-scoping), `t_16d011e6` (review rubrics), `t_ce063b87` / `t_14d438ea` (publish adapters,
  glass-break checklist), `t_d3b9e218` / `t_d8cc0a38` (this genre's superseded cards). **Nothing
  this brief cites is still open** — so the fix list it produced has been consumed, and the open
  work is the three items below.
- **Open, and owned elsewhere (status when this pass measured):** `t_1a5b018b` (`ready`,
  music-producer) reconciles the stale **§8** text in the sibling briefs — this pass resolved its
  `elemental-water` leg here and left the `elemental-air` leg on that card; `t_f65b0f4c`
  (`running`) owns the plan's placeholder `key`; `t_6599927d` (`running`) owns re-emitted oracle
  cards that carry `stage: brief` for genres whose brief is already on disk; `t_eb648761` (`done`)
  was the trend-signal fallback card that `b2d11f7` closed. The `t_aac32db8` / `t_bdb94fb7` /
  `t_6dd13d76` / `t_34f496d7` family owns the remaining `check_brief_absence(s)` /
  `check_brief_figures` findings in *other* briefs.
- **Filed by this brief (one card, after checking the board for duplicates):** the gate matrix is
  never run by anything (§11) → `nexus-core`. That is **`t_b16b9046`, now `done`** —
  `music-gate-matrix.timer` runs it (first logged run rc=0, 15:22 CDT). The §8 rubric finding
  and the §10 publish-path finding were **already carded** (`t_426a82a3`, `t_5ed495eb` /
  `t_ce063b87`) and are referenced, not duplicated; §10's stranded-ref measurement was left as a
  comment on **t_8a715681**, and the still-live half of it (two refs,
  `origin/wip/atlas-backup-20261014` @ `3882292` and the local `wip/atlas-backup-20261014` @
  `abcf169`, neither on `main`) is carded as **`t_9682a610`** (`ops`, `running` when this line was
  written — "decide origin/wip/atlas-backup-20261014 @ 3882292").


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
- **hotspot re-measured 2026-10-16 16:1x–16:5x CDT (surviving-card pass, `t_354d5d25`):** the
  collision is now measurable *on this file*. **7 cards were `running`** while this pass ran
  (`t_97494e6a` fire oracle twin, `t_354d5d25` this card, `t_99e6d789`, `t_eb648761`,
  `t_e86c2110`, `t_e2375c5a`, `t_fa731c5b`), and **`t_fa731c5b` committed this brief mid-edit**
  — commit `b2a1220` (16:16:37) swept up this pass's in-flight edits to
  `music/briefs/elemental-water.md` (399 changed lines in that commit) together with its own
  one-paragraph §9 correction, and touched five other briefs in the same commit. Nothing was
  lost, but two writers committed one file, which is exactly the hazard this bullet records:
  **a brief-stage worker cannot assume it owns its own file while it holds it.** This pass
  therefore kept its own commit path-scoped to `music/briefs/elemental-water.md` and recorded the
  superseded sha256 above rather than rewriting a sibling's section. `music/planner/planner.py`
  was simultaneously dirty from `t_f65b0f4c` and `t_6599927d` was mid-run on the oracle stage
  markers — neither was touched here.


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
  not. This genre still has none — but §9's "flat 100 fallback" no longer follows from that:
  `bpm_anchor_for()` falls back to the template's own caption, and this genre's caption states
  82 BPM (measured live, §9 blocker 2). The 2026-10-16 15:31 pass behind this section measured
  the census at six; what landed since is `music/lyrics/blueprints/jungle-dnb.yaml` (card
  `t_e6d422ec`).
- **Corrected in place:** the header table row 4, §9 blocker 2 and §12's asset listing.
- **Superseded by this pass (card `t_e6d422ec`, 2026-10-16):** `sha256 6478e55ceee1267a299abf2ff0a95f6d4987ae826ba71e8eb8ff9a3ca27cf52a` (669 lines / 41998 B) — the census counts above and in §6.3 were restated as live claims when `music/lyrics/blueprints/jungle-dnb.yaml` landed.

## 16. Surviving-card pass — what this pass re-measured and corrected (card `t_354d5d25`)

This card is the surviving one of three for `elemental-water` (`t_d3b9e218` 7.5 and `t_d8cc0a38`
7.7 are the superseded pair, both `done`; the oracle's ruling on this card states the true score
is **7.0**, and that is what `music/oracle.py --dry-run` returns). Briefs in this lane are keyed
by genre, so all three resolve to this file: **no second brief was written, no second chain was
started, and no stage was re-run.** What this pass did is re-measure every checkable claim
against live state and correct the ones that had aged.

**Revision chain for this file, with the sha256 this pass replaced:**

| Revision | Size / lines | Superseded by |
|---|---|---|
| `578e8dd1…` | write-time | duplicate pass `t_d8cc0a38` (13:52 CDT) |
| `b3284178…` | 40590 B / 653 | `t_0f7aed63` (15:34) |
| `6478e55c…` | 41998 B / 669 | `t_e6d422ec` (15:56) |
| **`3f19591d395550df4778cd21bdf461690b8848bf6923b192f202efb578cceca4`** | **42450 B / 671** | **this pass (`t_354d5d25`)** — and, mid-pass, commit `b2a1220` (`t_fa731c5b`) committed a version that contained this pass's in-flight edits plus its own one-paragraph §9 correction; the corrections below are relative to **both** |

**Corrected in this pass, class by class** (each re-measured, not inferred):

1. **Header** — card identity (this card is the surviving one; both twins `done`), the divergence
   pair (0 behind / 81 ahead at `e597bb6`, `origin/main` `ba28f55`), the board census
   (108 done / 36 ready / 8 blocked / 7 running / 4 todo / 1 archived), the running-card list,
   and the score (7.00, reproducible — not the 7.2 title).
2. **§1** — the registry transcript gained `, 1 stage gate rule(s)` and the `stage gate visual:`
   line.
3. **§2** — rewritten around the **fix**: `b2d11f7` removed the failed-fetch premium, so a
   timeout/403 now scores `TREND_NO_SIGNAL = 3.0` and reports itself. Added the stubbed
   14-genre measurement (both fetch branches, **max |delta| = 0.0**, range 6.5–8.4) and the live
   oracle-card census (43 cards: 41 `done`, 2 `running`).
4. **§5** — `gate_sync_ready` on an empty dir now returns **16 findings** (was 8: the pack
   manifest counts and `LICENCE.txt` classes), and `gate_loop_points` now measures **loop level**
   as well as curvature: a faded tail FAILS ("loop level drops"), so the paragraph claiming the
   gate cannot see a faded tail was wrong as of this pass.
5. **§8** — the rubric it asked to be fixed **has been fixed** (`56dc465`, `t_426a82a3`):
   criteria carry `applies_to` as data, `elemental_atmosphere` (w3) exists, and this genre's
   scored set is `elemental_atmosphere` + `loop_safety` + `asset_packaging` + `loudness_target`
   (Σw 8, ≥56 points at the 7.0 threshold). The reject signal that fired on a correct water theme
   is now scoped to fire + boss.
6. **§9** — all three blockers are **closed** (`t_25a6499c`, `t_8c5a6b91`): the planner has
   `--lyrics-mode instrumental`, the plan's `bpm` resolves to **82** from the caption, and
   `keyscale` reaches the engine (pod `translate.py` line 76). `music/suno-gen.py` is in the
   checkout now. What remains is **this genre's missing queue entry / queue card**, measured
   against the ConfigMap's 12 entries and every `queue` card on the board.
7. **§11 / §11a** — the gate matrix is now run by `music-gate-matrix.timer` (first run rc=0,
   272 s, 18 pass / 26 expected failures / 0 misbehaved), and `check_oracle_determinism.py` is
   **rc=0** with `--selftest` still proving A1 fires on an inverted pair.
8. **§12** — the blueprint census is 7 (`jungle-dnb.yaml` landed); the ledger carries a
   `renders[]` log with no entry for this genre; the only genre-named asset is a 5.000 s
   1280×720 prototype clip (ffprobe-measured).
9. **§13 / §14** — the advance channel (`kanban_comment` tool, `t_5a93164a`), the genre-resolved
   visual gate (`gate_for_stage` → `gate_youtube_authentic`, `t_d9983bb9`), the runbook's line
   count **as it stood in that pass** (**88**, not 53; **133** now that the runbook documents the
   `asset-pack` stage — §18), the rubric version, the moved `oracle.py` line citations, the
   re-run check list, the engine pod (`sunolocal-source-75d58dbc97-7jfmc`, v0.1.3) and the status
   of every cited card (all `done`).
10. **Two standing-check findings that named this brief were cleared**: `check_brief_figures`
    ("53 lines" → 88) and `check_brief_absence` — its 2026-10-16 finding about
    `music/suno-gen.py` is cleared; the file is in the tree now (§9).
    No check names this brief now.

**Not done in this pass, on purpose:** the genre was re-scored, not re-scored *by hand* — 7.0 is
reproduced from `oracle.py`, and no card was re-emitted. No queue entry was written: that belongs
to the `nexus-core` queue card this genre does not yet have, and writing the render queue from
the brief would collide with the card that owns the genre's title and duration. No file outside
`music/briefs/elemental-water.md` was modified by this pass.

## 17. Two absence findings on this file cleared (card `t_bdb94fb7`, 2026-10-16)

`music/scripts/check_brief_absences.py` FAILed rc=1 on two lines of this file, both ways a
line-scoped check reads prose as a claim about a path:

| # | Site | Before | After |
|---|---|---|---|
| 1 | §14, Runbook bullet | the pack builder and the runbook's own unfindable executables shared one line at 2026-10-16, so `music/assets/pack.py` sat beside the word "absent" | the pack builder gets its own sentence; the runbook's unfindable executables (`butler`, `~/.hermes/vault/itch_io_key`) keep the claim |
| 2 | §16 item 10 | a CLEARED `check_brief_absence` finding quoted in the present tense | stamped as the 2026-10-16 finding it was; the file is in the tree now (§9) |

Neither line denied the file that was there, so neither was a stale figure — the check is
line-scoped, and the remedy is the one its own FAIL text prints: correct the citing brief. No check
was edited or weakened.

```
$ /usr/bin/python3 music/scripts/check_brief_absences.py
PASS check_brief_absences: 0 file-absence claim(s) ...                                          # rc=0
```

The counts after that headline are elided on purpose: they are live readings, and this section
itself adds candidate lines to them.

- **Superseded revision of this file:** `sha256 fb78ecde6d5ae120e4fb7e9e742ee19100f7c6888ddce914310c26a655d5a13b` (971 lines / 64 164 B).

## 18. The runbook stopped describing the pack step as manual-only; its line count moved to 133 (card `t_6aa1e97f`, 2026-10-16)

`brain/runbooks/music-game-assets.md` presented the pack step as a command a human runs
by hand, so the runbook was the only place a reader learned the step exists — while
`music/stages.yaml` had already grown the `asset-pack` stage (bot `producer`, after
`gate`, before `package`; card `t_eb079b91`). The runbook now documents that stage: the
stage's position, the per-genre resolution

```
/usr/bin/python3 music/registry.py derived-for-stage --stage asset-pack --genre <g>
```

(`build: yes` for the six gamer genres, `build: no` for the other eight — resolved live
in this pass), the output convention `packages/<master-stem>-asset-pack`, the
generator's rc (`0` ACCEPTED, `1` REJECTED), both gates, and that publish stays behind
the `human-approval` gate. It points at
`brain/playbooks/music-lane-architecture.md` §13 instead of being the sole record. The
manual commands stay as the fallback for one pack built by hand.

The runbook therefore measures **133 lines** (88 before this pass), and the §14 Runbook
bullet above was corrected to match in the same commit. Checks run in this pass
(`/usr/bin/python3`, from `/home/j_kro/ai-content-pipeline`):
`music/scripts/check_brief_figures.py` **rc=0** and `music/scripts/check_doc_refs.py`
**rc=0**.

- **Superseded revision of this file:** `sha256 e51cd0b293e286d6d98afbfaaaa67806bf97a174903e84685b6a3ed1cf505c71` (1000 lines / 65873 B).

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

    /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --print-truth elemental-water

```json
{
  "rubric_scope": {
    "genre": "elemental-water",
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
