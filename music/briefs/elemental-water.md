# Brief — elemental-water

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`; on this board the cards are
> assigned `music-producer` and claimed by the generic kanban dispatcher).
> **Card:** t_d3b9e218 (`music-oracle: elemental-water (score 7.5)`)
> **Duplicate card:** t_d8cc0a38 (`music-oracle: elemental-water (score 7.7)`) — same genre,
> same three lanes, status `ready`. Both resolve to THIS brief; the brief is keyed by genre,
> not by card (precedent: `music/briefs/commentary-beds.md`).
> **Written:** 2026-10-16T13:20-05:00 (CDT)
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `49d506b` (main — HEAD when this brief was
> written; it moved 6 times during the run, to `89d6eb2` by the time of writing this line).
> **6 cards were `running` on this board** while this brief was written (5 music briefs +
> `t_aba9d2c3`), and 15 commits landed in the last 40 minutes.
> **Oracle (card):** 7.5/10. **Oracle (measured now):** 7.00/10. See §2 — the difference is not
> a re-scoring, it is a frozen number.

## 1. Genre resolution (live, not transcribed)

```
$ /usr/bin/python3 music/registry.py validate
registry OK: 14 genres, 10 lanes
genres: activist, anime-ending, anime-opening, chill-lounge, chiptune-8bit, commentary-beds,
        elemental-air, elemental-earth, elemental-fire, elemental-water,
        epic-orchestral-boss, jungle-dnb, sentimental-piano, trance
lanes: direct-fan, direct-license, game-assets, stock-ai-native, streaming, sync,
       sync-documentary, youtube-gaming, youtube-longform, youtube-mix
quota ledger: period 2026-10, standard 0/60 (warn_at 55, hard_stop_at 58)
```

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

## 2. The card's score is a frozen number — measured, with the root cause

The card says 7.5. Re-scoring the same genre right now gives **7.00**:

```
$ /usr/bin/python3 music/oracle.py --dry-run
  elemental-water: 7.0/10
```

Per component, read from `score_genre()` live and compared with the card body:

| Component | Card | Measured now | Why it moved |
|---|---|---|---|
| quota_headroom | 10.0 | **10.0** | `10·(1 − 0/58)` — ledger `0/60` (unchanged) |
| lane_coverage | 6.0 | **6.0** | `min(3 viable × 2, 10)` — static |
| revenue_potential | 8.0 | **8.0** | lane revenue bands — static |
| cadence_fit | **6.7** | **3.3333** | **time-dependent** (see below) |
| policy_risk | 9.0 | **9.0** | `10 − 1` (one `youtube-gaming` lane penalty) |
| trend_signal | 3.0 | **3.0** | DuckDuckGo scrape (see below) |

**`cadence_fit` decays as the quota period advances.** `oracle.py:221-253` computes
`days_remaining = (last_day_of_period − now).days`, `expected_tracks = per_week × days/7`, then
`(expected_tracks − 2)/6 × 10`. For `2/wk` on 2026-10-31: 14 days left → 4.0 expected → 3.3333.
The card was created **2026-10-09 03:27 CDT** (epoch `1791534471`), when ~21 days remained and
the same expression gave 6.7. Same genre, same registry, different period position.

**The 7.5 vs 7.7 duplicate is a failed web fetch, not more demand.** `trend_signal_score()`
(oracle.py:272-289) scrapes `https://html.duckduckgo.com/html/?q=<genre> music trend 2026` and
counts `class="result__snippet"` occurrences: `≥5 → 10.0`, `0 → 3.0`, `1-4 → 3.0 + n/5·7`, and
**any exception → 5.0**. Measured directly:

```
$ /usr/bin/python3 trend_probe.py
elemental-water      snippet_matches=  0  html_bytes=  14280  -> trend_signal_score=3.0
chill-lounge         snippet_matches=  0  html_bytes=  14292  -> trend_signal_score=3.0
trance               snippet_matches=  0  html_bytes=  14262  -> trend_signal_score=3.0
sentimental-piano    FETCH FAILED (HTTPError: HTTP Error 403: Forbidden) -> trend_signal_score=5.0
```

The endpoint returns HTTP 200 with ~14.3 KB and **zero** matching snippets, so every genre in
the registry scores 3.0; when DuckDuckGo rate-limits to 403, the `except` branch scores
**higher (5.0)**. The board confirms the arithmetic across all 28 cards:

```
$ /usr/bin/python3 oracle_deltas.py
oracle cards on board: 28   distinct genres: 14
activist        n=2  scores=[7.25, 7.45]  spread=0.20
…
elemental-water n=2  scores=[7.5,  7.7 ]  spread=0.20
spread distribution across genres: {0.2: 14}
0.2 == WEIGHTS['trend_signal'] * (5.0 - 3.0) = 0.2
```

**Every one of the 14 duplicate pairs differs by exactly +0.20, and 0.20 is the 403 fallback.**
A genre whose trend fetch *fails* outranks the same genre whose fetch succeeds. The higher-scoring
card is the broken run. `trend_signal` is weight 0.10 and carries no signal at all: the search
string is the registry's invented slug (`elemental-water music trend 2026`), which matches nothing
in any corpus, and it floors at 3.0 by construction. Carded: **t_bf0e5edd** (oracle duplication).

**Consequence for this brief: none for the go/no-go.** 7.00 ≥ 5.0 → produce, same verdict as
7.5. Downstream stages must not read the card's 7.5 as a live measurement, and must not treat
the 0.20 pair-delta as evidence that one run saw more demand.

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
$ /usr/bin/python3 music/gates/gate_sync_ready.py --package-dir <empty> --lane game-assets
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

The full gate matrix is green on its own fixtures after this run's fix (§11):

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

**`gate_loop_points` — already found defective by a sibling, not re-derived here.** The fire
sibling (card t_6f0d261e) measured that `gate_loop_points` **PASSES a loop with a 1.6 s fade-out
tail at 2.21× curvature** because it measures junction *curvature* (a derivative kink) and a
linear fade introduces no kink. Its calibration — 1.6× clean, 6.0× half-period phase slip,
ceiling 3.0× — reproduced exactly in this run's suite output. Carded: **t_bab8aa19** (nexus-core).
For elemental-water this matters more than for most genres: the template asks for a
reverb-heavy, blurred texture, the most likely correct-sounding ending is a tail that thins —
which is precisely the shape the gate cannot see. **The seam must be verified by the reviewer's
own tail/head RMS test, not by `gate_loop_points` alone.**

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

## 8. ⚠ The rubric as written cannot pass a correct water theme — decision + card

`music/rubrics/gamer.json` (family `gamer`, pass threshold 7.0 on the geometric-median panel
aggregate) defines five criteria; the review stage applies them per the criterion's declared
scope:

| Criterion | Weight | Declared scope | Applies to `elemental-water`? |
|---|---|---|---|
| `chip_timbre_authenticity` | 3 | "chiptune-8bit only" | no — scope says so |
| `battle_energy` | 3 | "**elemental-***, epic-orchestral-boss" | scope says **yes** — but see below |
| `loop_safety` | 3 | "all gamer genres" | yes |
| `asset_packaging` | 1 | game-assets lane | yes |
| `loudness_target` | 1 | streaming lane | yes |

**The `battle_energy` scope is wrong for 3 of the 4 elementals.** Measured from each template:

| Genre | Stated tempo | Template's own words |
|---|---|---|
| `elemental-fire` | **150 BPM** | "Boss/battle theme for the fire element" → battle_energy **is** correct |
| `elemental-water` | **82 BPM** | "underwater cave ambient theme" · "Water does not rush" |
| `elemental-earth` | **88 BPM** | "ancient cavern earth theme" · "patient and heavy" |
| `elemental-air` | **92 BPM** | "open sky heights theme" · "no percussion kit, no bass weight" |

The criterion's own anchor demands **130–200 BPM** (typical 140–180) and its own guide ends
`"1 = slow ambient track with a battle label"`. 82 BPM is 63 % of the anchor's lowest tempo.
Worse, the rubric's `reject_signals` include *"boss/battle claim with no fast-tempo candidate
(under 130 BPM)"* — applied to this genre that reject signal fires on a **correct** water theme.

The rubric **contradicts itself**: its own `notes` field (line 70) says
*"elemental-\* tracks choose per their prompt; chiptune-8bit MUST pass chip_timbre_authenticity;
**battle tracks MUST pass battle_energy**"*. The name string is broader than the notes. Computed
consequences, for the reviewer's benefit:

```
Non-battle scope (loop 3 + packaging 1 + loudness 1 = weight 5, need 35 pts):
  a correct track scoring 7.0 or better on all three PASSES (35/5 = 7.0 exactly).
Battle scope applied as the name reads (chip dropped, total weight 8, need 56 pts):
  a track scoring 10/10/10 on loop/packaging/loudness still needs battle_energy >= 2.0.
  battle_energy = 1 -> aggregate 6.625  FAIL   (and this is the score the guide prescribes
                                               for an 82 BPM ambient track)
If a judge scores the N/A chip criterion as 0 instead of dropping it (total weight 11):
  only battle_energy = 10 can reach 7.0 (7.273); every correct water theme FAILS.
```

**DECISION LOCKED for this genre:** the reviewer scores **`loop_safety` (w3), `asset_packaging`
(w1), `loudness_target` (w1)**; `battle_energy` and `chip_timbre_authenticity` are **N/A** and
their weight is dropped, not zeroed. A correct `elemental-water` track must reach ≥7.0 on those
three. The same three apply to `elemental-earth` and `elemental-air`.

**NOT fixed here — the rubric belongs to the review panel, and a producer editing its own grading
sheet is the self-review failure mode this lane forbids (`t_16d011e6` was `editor`'s). Already
filed as **t_426a82a3** (`editor`), from the elemental-air brief. What this brief adds is
independent: the 82/88/92 BPM set for water/earth/air against fire's 150 BPM, the second failure
mode (reject_signal #2 *"boss/battle claim with no fast-tempo candidate (under 130 BPM)"* firing
on a correct water theme), and the three computed aggregate outcomes above. The fix is the scope
string `(elemental-*, epic-orchestral-boss)` → `(elemental-fire, epic-orchestral-boss)`, mirroring
the pattern the `chip` criterion already uses, plus narrowing reject_signal #2 to the same set.
**No duplicate card filed.**

## 9. Generation path — three blockers, measured on the live engine

The lane's own generate prompt names `music/suno-gen.py`. **That file is not in this checkout.**
This tree has diverged from `origin/main`: `git rev-list --count HEAD..origin/main` = **15**
commits of this lane's own work are missing locally. Read from the git object (not from disk),
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
   `"bpm": ctx["blueprint"].get("bpm_anchor") or 100` (`planner.py:470`), and **only 3 of 14
   genres have a blueprint** (`activist`, `chill-lounge`, `trance`). So this genre plans at 100
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
| `~/.hermes/vault/itch_io_key` | **`~/.hermes/vault/` does not exist** — no vault at all |
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

## 12. Existing assets for this genre

Measured: **none.** `music/lyrics/` holds `activist/`, `chill-lounge/`, `trance/` plus
`blueprints/{activist,chill-lounge,trance}.yaml` — no `elemental-water` sheet or blueprint
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
- Upstream truth read from git objects: `origin/main:music/suno-gen.py:141`
  (`is_instrumental_template`), `origin/main:music/sunolocal/translate.py`
- Engine truth read from the running pod: `sunolocal-source-65fcc845d-fd5r6`,
  `/opt/sunolocal/music/sunolocal/translate.py` lines 33-59; `music-pipeline-briefs` ConfigMap
- **Dangling reference (unchanged):** `brain/playbooks/music-lane-architecture.md` is cited as
  "READ FIRST" by this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`, `autonomy.yaml`
  and `gates/*`, but no copy exists on this machine. `brain/research/music-monetization-2026.md`
  likewise (`brain/research/` does not exist). Carded: **t_b0a4db92**.
- **Not fixed here (other owners, already carded):** gate_loop_points false pass **t_bab8aa19**;
  instrument/tempo/key render gaps **t_25a6499c**; diverged checkout — now with a **third stranded
  ref**, see §10 — **t_8a715681**; scheduler units running the wrong checkout **t_41f354be**;
  oracle card duplication + the 0.20 trend artifact **t_bf0e5edd**; missing architecture docs
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
