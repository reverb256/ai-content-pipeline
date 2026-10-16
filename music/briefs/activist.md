# Brief — activist

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`; on this board the
> cards are assigned `music-producer` and claimed by the generic kanban dispatcher) —
> DELIVERED; the chain resumes at `genre-select`, which §1–§3 already resolve.
> **Card:** t_752f02a8 (`music-oracle: activist (score 7.2)`) — the surviving OPEN card
> for this genre. The board check reports `activist → t_752f02a8 [running]` with one open
> card per genre, rc=0 (`music/scripts/check_oracle_board.py`, re-run in this pass: 10 open
> cards across 10 genres).
> **Superseded cards:** t_ace3bfb1 (`music-oracle: activist (score 7.25)`, done) wrote this
> brief; t_b7dd5655 (`music-oracle: activist (score 7.45)`, done) was its duplicate,
> created by the second 2026-10-09 oracle run ten minutes later. Briefs in this lane are
> keyed by **genre**, not by card, so all three cards resolve to this one file, and no
> second brief and no second stage chain exists.
> **Written:** 2026-10-16T13:35-05:00 (CDT) — **verified in place 2026-10-16T13:54-05:00**
> by the duplicate card t_b7dd5655; every checkable figure re-measured (§12) — **re-measured
> again 2026-10-16T16:00-05:00 by the surviving card t_752f02a8 (§14)**.
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `9ebf6af` when written — 15 behind / 7 ahead of
> `origin/main` at 13:35 (CDT); @ `fa3163f` when verified — 15 behind / 29 ahead at 13:54, and
> 15 behind / 32 ahead at 13:58; @ `8f0fd9a` at this pass (16:00) — **0 behind / 71 ahead**,
> the upstream deficit having closed with the reconciliation merge (t_8a715681, done). The
> shared tree is a moving target: re-measure it, do not copy this line (§11, §12).
> **Supersedes `sha256 f28792a7ca79628e1993c03e90bf6ea0be02e786bd3536348742c04956ffe21b`**
> (689 lines / 43 914 B — the revision the duplicate card verified and cards `t_0f7aed63` /
> `t_e6d422ec` corrected). The chain before it: `a47b0f9b…026a` (`a4ba657`, 27 917 B) →
> `7e9a1cc8…67c` (41 631 B) → `3b8a9d74…9fc` (43 483 B) → the blob above. This pass edits the
> file in place and records the supersession here and in §14, as
> `music/scripts/check_brief_figures.py` requires.
> **Blueprint census re-measured and corrected (card `t_c5a98379`):** 2026-10-16 — 7 of the 14
> genres carry a lyric blueprint; §14's "re-measured and held" list still said six. Superseded
> blob recorded in §15.
> **Oracle:** **true score 7.0/10** — the oracle's dedupe ruling of 2026-10-16
> (`music/oracle.py` @ `b2d11f7`): quota headroom 10.0, lane coverage 6.0, revenue potential
> 10.0, cadence fit **0.0**, policy risk 10.0, trend signal 3.0. Threshold 5.0 → produce.
> **Reproduced in this pass with the repo's own scorer** —
> `oracle.score_genre("activist", …)` → `total: 7.0`, with the trend fetch failing and being
> floored at 3.0 (§2, §14). The titles' 7.2 / 7.25 / 7.45 are the 2026-10-09 double emission
> and the premium the old broken-fetch branch paid.

## 1. Genre resolution (live, not transcribed)

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

That transcript is the live output of this pass (2026-10-16T16:00 CDT). It gained one clause
and one line since the brief stage wrote it: the board now declares a stage gate rule for the
`visual` stage and the header count reads `1 stage gate rule(s)`. The rule reads *a genre with
a YouTube lane gets `gate_youtube_authentic`; where the lane is absent the answer is `none`* —
which is this genre's case (§3 and §7, both corrected in this pass).

**Interpreter trap, re-measured.** `python3` in a worker shell resolves to
`~/.hermes/tools/python-3.14.7+…/bin/python3`, which has no PyYAML. `/usr/bin/python3`
(also 3.14.7) has it and runs every gate and registry command below. Any stage prompt
that says `python3 music/…` inherits the trap; the systemd units use `/usr/bin/python3`.

| Field | Value |
|---|---|
| Genre | `activist` |
| Family | `vocal` |
| Prompt template | `music/prompts/activist.md` (4448 B, resolves) |
| Visual style | `music/visuals/documentary-grain.md` (1425 B, resolves) |
| Lanes | `direct-fan`, `sync-documentary`, `streaming` — three lanes |
| Cadence | 1/wk |
| Video shape | `lyric-video` |
| Lyric blueprint | `music/lyrics/blueprints/activist.yaml` (2023 B) |
| Blueprint BPM anchor | **96** (measured via `planner.context_for("activist")`) |
| Style caption | 585 chars (template states 585/1000; measured 585) |
| Registry note | "Ad-suitability risk — audience-funded > ad-funded. Sync for doc/film is the pro outlet." |

**Activist is one of only seven genres with a lyric blueprint** — `music/lyrics/blueprints/`
holds exactly `activist.yaml`, `anime-ending.yaml`, `anime-opening.yaml`, `chill-lounge.yaml`,
`epic-orchestral-boss.yaml`, `jungle-dnb.yaml`, `trance.yaml`. So this genre does not inherit the planner's flat `bpm = 100` fallback: the draft path reads the 96 anchor.

## 2. Score audit — the filed 7.25 is stale, and cadence fit is a clock, not a signal

Every component recomputed on this host, this clock, by importing `music/oracle.py`:

```
$ /usr/bin/python3 measure_activist.py        (workspace script, read-only)
  quota_headroom     10.000  weight 0.25  -> 2.5000
  lane_coverage       6.000  weight 0.20  -> 1.2000
  revenue_potential  10.000  weight 0.20  -> 2.0000
  cadence_fit         0.000  weight 0.15  -> 0.0000
  policy_risk        10.000  weight 0.10  -> 1.0000
  total (no trend_signal): 6.7
```

That transcript measured the components one call at a time. The pass of 2026-10-16T16:00
(`t_752f02a8`, §14) went through the scorer the oracle itself uses instead, so the total is
reproducible in one call:

```
$ /usr/bin/python3 probe_score.py             (workspace script, read-only)
  genre spec lane list: ['direct-fan', 'sync-documentary', 'streaming']
  genre cadence field: 1/wk
  cadence_fit_score('1/wk') = 0.0
  scores: {'quota_headroom': 10.0, 'lane_coverage': 6, 'revenue_potential': 10.0,
           'cadence_fit': 0.0, 'policy_risk': 10.0, 'trend_signal': 3.0}
  total: 7.0
```

Note the signatures, because a caller that passes the wrong argument silently gets the
no-cadence default: `quota_headroom_score(quota)`, `lane_coverage_score(genre_lanes, lanes)`,
`revenue_potential_score(genre_lanes, lanes)`, `cadence_fit_score(cadence_str)` — a *cadence
string* like `"1/wk"`, not a genre name, which returns the neutral `5.0` for anything that
does not match `\d+/wk` (`oracle.py:223`) — `policy_risk_score(genre_lanes, lanes)`,
`trend_signal_score(genre_name)`. `score_genre(genre_name, genre_spec, lanes, quota)`
(`oracle.py:312`) is the entry point that composes them.

`cadence_fit_score()` is a pure function of today's date and the genre's cadence
(`oracle.py:221`): `expected_tracks = per_week × max(days_remaining/7, 0.5)`, then
`(expected-2)/6 × 10` below 8 and clipped at 0. For 1/wk in a 31-day period that is:

| Date | days_remaining | expected (1/wk) | cadence_fit |
|---|---|---|---|
| 2026-10-09 (card filed, epoch 1791534472) | 21 | 3.00 | **1.667** → filed as 1.7 |
| 2026-10-16 (today, this run) | 14 | 2.00 | **0.000** — re-measured live |

So the card's 7.25 cannot be reproduced today: the same weights give **7.0** (quota 10.0 +
lane 6.0 + revenue 10.0 + cadence 0.0 + policy 10.0 = 6.70, plus trend_signal 3.0 × 0.10),
or **6.70** if the trend term is dropped. Both are above the 5.0 threshold → still produce.
The conclusion holds: for a 1/wk genre cadence fit reaches exactly 0.0 at the two-week
remaining mark (`days_remaining` ≤ 14 → `expected` 2.0 → the `< 2` test is False → `(2-2)/6`
= 0) and stays there to month end.
**Do not read the oracle score as evidence about the genre** — for the low-cadence genres
it is mostly evidence about the calendar.

Also measured, so nobody re-derives it: `trend_signal` is neither a measured trend nor
reproducible run to run. **CORRECTED 2026-10-16 (§14): the swing described here is gone.**
`trend_signal_score()` (`oracle.py:283`, no longer `:272`) used to return **3.0** on the
`count == 0` branch and **5.0** on any exception, so a BROKEN fetch outscored a working one
by 0.2 on the ten-point total — that is the whole difference between this card's title score
and its twin's. Fixed in `b2d11f7`: `TREND_NO_SIGNAL = 3.0` (`oracle.py:280`) is now returned
by both the zero-snippet branch (`:300`) and the `except` branch (`:309`), and the failure is
printed to stderr. This pass measured the failure path live — `warn: trend fetch failed for
activist (URLError(TimeoutError('timed out'))); scoring it as no signal (3.0)` — and the
regression is `music/scripts/check_oracle_determinism.py` (PASS rc=0, §14). The term is still
uninformative at weight 0.10, but it is now reproducible, which is what the ruling required.

## 3. Target lanes and what each one demands

From `music/lanes.yaml`. These are the gates that will actually run.

| Lane | Surface | Bot | Gate | Required artifacts |
|---|---|---|---|---|
| `direct-fan` | patreon, ko-fi | `socialbot` (profile verified present) | `gate_human_approval` | none declared — a human approval record only |
| `sync-documentary` | songtradr, audiosparx | `distributor` | `gate_sync_ready` | `stems`, `metadata`, `clearance_doc`, `instrumental_version` |
| `streaming` | distributor (DistroKid; TuneCore alt) | `distributor` | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` |

All three lanes are at **rung `advisory`** (`music/autonomy.yaml`): every publish is
proposed with evidence and approved by j_kro. Promotion needs 10 clean advisory publishes.

Gates exercised live against an empty package dir — this is the requirement list the
`package` stage must satisfy, quoted from real output:

```
$ /usr/bin/python3 music/gates/gate_release_ready.py --package-dir <empty>
FAIL gate_release_ready
  - no master.wav
  - no artwork (one of artwork.jpg, artwork.jpeg, artwork.png)
  - no manifest.json
  - no ai_disclosure.txt
rc=1

$ /usr/bin/python3 music/gates/gate_sync_ready.py --package-dir <empty> --lane sync
FAIL gate_sync_ready
  - full_mix.wav is not a real audio file (ffprobe could not read a duration)
  - no stems/ directory — a sync track without stems is not sync-ready (architecture HARD RULE 4)
  - only 0 stem(s) found; 4 required (drums, bass, keys, vocals, ...)
  - instrumental.wav is not a real audio file (sync needs an instrumental version)
  - no manifest.json
  - manifest.json has no metadata object
  - manifest metadata missing 'title'
  - manifest metadata missing 'artist'
  - manifest metadata missing 'bpm'
  - manifest metadata missing 'key'
  - manifest metadata missing 'mood'
  - manifest metadata missing 'genre'
  - no clearance_doc.pdf (or .txt) — sync requires a clearance document
  - no ai_disclosure.txt — the AI role must be declared for sync platforms
rc=1

$ /usr/bin/python3 music/gates/gate_sync_ready.py --package-dir <empty> --lane sync-documentary
FAIL gate_sync_ready
  <the same 14 findings>
rc=1

$ /usr/bin/python3 music/gates/gate_human_approval.py --package-dir <empty>
FAIL gate_human_approval
  - no approval.json — nothing has been approved. Publish approval is j_kro's decision
    (architecture §7, item 1).
  This gate cannot be satisfied by a bot: it needs a human approval record for THIS artifact.
rc=1
```

**CORRECTED 2026-10-16 (§14):** the `sync` transcript quoted 7 findings when this brief was
written; the gate enforces **14** now — it also checks the manifest's `metadata` object and
its six required fields (`title`, `artist`, `bpm`, `key`, `mood`, `genre`). The
`sync-documentary` lane is now an accepted `--lane` and returns the same 14 findings at rc=1,
which is why it is quoted a second time below.

### RESOLVED — the sync-documentary lane now invokes its own gate

`music/lanes.yaml:66` gives `sync-documentary` `gate: gate_sync_ready`, and until 2026-10-16
the gate's argparse rejected that lane name with rc=2 — an argument error a stage reads as a
gate FAILURE, on the lane this genre's whole `revenue_potential` rests on. **Fixed in
`54f6d3c` (card t_d9983bb9, done), measured in this pass:**

```
$ /usr/bin/python3 music/gates/gate_sync_ready.py --package-dir <empty> --lane sync-documentary
FAIL gate_sync_ready            (14 real findings, above)
rc=1

$ grep -n "choices=lanes" music/gates/gate_sync_ready.py
581:    parser.add_argument("--lane", default=default_lane, choices=lanes,
```

The gate **derives** its lane set from `music/lanes.yaml` (via the stdlib-only reader
`music/gates/_lane_registry.py`, because bare `python3` in a worker shell has no PyYAML) and
maps each lane's `requires:` tokens to a check; a token it cannot evidence FAILS the run
instead of passing silently. There is no longer a `LANES` tuple in the gate to drift from the
registry, so the old `gate_sync_ready.py:47` citation is dead. Regression:
`music/scripts/check_gate_lane_surface.py` — *"every gate accepts the lanes lanes.yaml gives it,
and the visual stage's gate follows the genre"*, PASS rc=0, cited to card t_d9983bb9.

Decisions locked here so no later stage re-litigates them:

- **Two loudness targets, one master each.** Streaming wants −14 (rubric `loudness_target`
  anchors on −14), sync wants −16. Ship the −14 `master.wav` in the streaming package and
  the −16 cut as the sync package's `full_mix.wav`. Do not re-encode one file twice and
  call it two masters. `gate_loudness` in THIS branch still measures ffmpeg `volumedetect`
  mean RMS, not gated LUFS — the ruler defect stands in `main` (`music/gates/gate_loudness.py`,
  last touched 2026-10-09). Its fix, `e783a96` *"gate_loudness ruler — retire volumedetect RMS
  for ebur128 integrated loudness"* (card t_9546841b, done), is on
  `origin/publish/audio-lane-2026-10-16` and is **not** an ancestor of `8f0fd9a` — measured
  with `git merge-base --is-ancestor e783a96 HEAD` → not in HEAD. So the streaming master must
  be measured in the volumedetect dialect until that branch lands, and nobody may quote a
  "−14 LUFS" number out of this gate as if it were a BS.1770 reading.
- **Stems: ≥ 4, each within ±0.5 s of the master** (`gate_stems_present.py`
  `DEFAULT_MIN_STEMS = 4`, `DEFAULT_TOLERANCE = 0.5`, ffprobe-measured). This arrangement
  can yield more: percussion, bass, acoustic guitar, lead vocal, group vocal.
- **`instrumental.wav` must be a real, distinct render.** The gate fails one that is
  byte-identical to `full_mix.wav`. Export it from the same generation, not by muting a
  copy.
- **`clearance_doc.pdf` must be a real PDF** (`%PDF-` header parsed) and
  `ai_disclosure.txt` must be non-empty — both fail a placeholder.
- **`approval.json` must bind to the artifact sha256** with an `approver`, an `action`,
  and an `approved_at` later than the artifact — a bot cannot manufacture this.
- **`socialbot` is a real profile** (`hermes profile list`, verified this run), so the
  direct-fan lane has a live owner.
- **No YouTube lane at all**, so the visual stage runs **no video gate** — resolved, not
  assumed. `music/registry.py gate-for-stage --stage visual --genre activist` answers
  `gate: none` with the reason *"no lane in this genre declares gate: gate_youtube_authentic
  (lanes: direct-fan, sync-documentary, streaming) — when_absent: none, so the visual stage
  runs no gate for it"* (rc=0), and `gate-for-stage` for an unknown genre exits 2 rather than
  guessing. Ad revenue is not the business here; §7 records the shape that now exists.

## 4. Intent — a song, not a bed and not a kit

The genre's own template states the product: *the lyrics ARE the genre*. The chorus is
what a crowd sings back at a rally without your recording; the verses carry the reportage
and the chorus carries the demand. Everything the lane earns comes from one of three
things, and none of them is ad impressions:

1. **Direct-fan** — Patreon/Ko-fi. Audience-funded beats ad-funded precisely because
   political content is ad-unsuitable.
2. **Documentary/film sync** — the template calls this the pro outlet; Songtradr and
   AudioSparx carry it. This is where `stems` + `instrumental_version` + `clearance_doc`
   are load-bearing.
3. **Streaming** — DistroKid, no caps, no exclusions.

Cadence 1/wk. The blueprint's own lane note: *"sync buyers need songs that age well and
take no sides by name"* — which is a constraint on future sheets, and it is honoured by
the existing one (§5).

Three things must hold or a generation is **out of genre** (the template says reject it):

1. **Chorus is the crowd's part** — group unison vocals, repeated title line, 4–8 words.
   A chorus nobody could chant while marching is a defect.
2. **Verse imagery beats slogans** — concrete images, one specific injustice; no abstract
   fury. `RULINGS.md` states this as a standing ruling: *"Protest lyrics need a chantable
   chorus and a named target. Vague fury with no concrete image fails the genre's function."*
3. **Hand the mic back** — call-and-response is the genre's oldest technology. A protest
   song that never does is "a speech with chords."

Nothing else earns a place: party energy, club production, autotune, or fist imagery are
explicit excludes (§6).

## 5. Lyrics — the sheet already exists, passes, and matches its blueprint 1:1

`music/lyrics/activist/what-runs-beneath/` holds a complete human-authored sheet
(title **"What Runs Beneath"**, author **j_kro**, written 2026-10-08T12:48:59Z,
`suno_generated_lyrics: false`). Gate, both plain and strict:

```
$ /usr/bin/python3 music/gates/gate_lyrics_original.py --track-dir music/lyrics/activist/what-runs-beneath --strict
PASS gate_lyrics_original
  track        : What Runs Beneath (music/lyrics/activist/what-runs-beneath)
  sections     : 7
  unique words : 112
  authorship   : j_kro @ 2026-10-08T12:48:59+00:00
  suno markers : none
rc=0
```

Measured against this genre's rubric (`music/rubrics/vocal.json`, `pass_threshold` 7.0,
`chantable_chorus` and `named_target` at weight 3 each) and against `RULINGS.md`:

```
-- section map (lyrics.suno.txt), occurrence-sensitive, in order --
  [Verse 1] -> [Chorus] -> [Verse 2] -> [Chorus] -> [Bridge] -> [Verse 3] -> [Outro]
  count: 7   |   blueprint structure == sheet order: True   (both 7 tags, same order)
-- chorus (x2, byte-identical blocks) -- 6 / 7 / 6 / 6 words per line; max 7 (template rule: 4-8)
-- title -- "What Runs Beneath" (title.txt + the sheet's `# title:` header); the PHRASE
   "what runs beneath" appears twice in the chorus, in sentence case at lines 1 and 3
   (which are the same line), and again in the outro ("What runs beneath keeps running").
   CORRECTED 2026-10-16 (§14): the earlier text called the chorus occurrences "verbatim"
   and treated the outro's lower case as a contrast. Measured: the title-cased string
   occurs exactly once in the whole sheet — in its own `# title:` header — so both the
   chorus and the outro carry the same sentence-case phrase. A later stage must not count
   the outro as a second title statement, and must not require title case in the body
-- concrete images -- kettle, gravel, aquifer, tap, letter, February, sample, company man,
   town clerk, minutes, hardware hall, forty folding chairs, boots, signatures, panel,
   deadline, hall lights, door   (all 18 present — §12 re-measured each one; re-measured
   again 2026-10-16 with the case convention stated, because three of them are line-initial
   capitals in the sheet: "Gravel road to school", "Forty folding chairs", "Boots by the
   doorway". The earlier "(23 distinct hits)" counted a wider candidate list this brief
   never printed; 18 is the count this brief can reproduce)
-- abstract-emotion words -- none
-- blueprint avoid-list -- "rise up" absent, "they can't stop us" absent, "revolution" absent,
   "fist" absent, real names absent
```

**Parser warning, recorded because it nearly produced a false finding here:** a
dict-keyed section reader (`sections[tag] = []`) collapses the repeated `[Chorus]` tag and
reports six sections. The occurrence-sensitive count is **seven**, and the sheet's section
sequence is an exact, in-order match to the blueprint's seven `structure` entries, with the
second chorus byte-identical to the first. Any later stage that validates structure should
count occurrences in order, not unique tag names.

That is a strong fit: the title line is stated twice inside the chorus (lines 1 and 3 are
the same line) and the whole chorus repeats verbatim, 6–7 words per line sits inside the
template's 4–8 rule, the images are concrete, there are no slogan clichés, and no real
politician or company is named — which is exactly what a documentary buyer needs. Gate,
blueprint and ruling all agree; nothing in the lyrics needs rewriting.

**One optional enhancement, j_kro's call, not a defect.** The sheet matches the *blueprint*
1:1, but the *prompt template* asks for eight tags —
`[Verse 1] [Pre-Chorus] [Chorus] [Verse 2] [Chorus] [Bridge] [Chorus] [Outro]`, with the
final chorus doubling the clap layer and "everyone sings". The sheet has no `[Pre-Chorus]`
and no post-bridge third chorus. The constraining artifact the planner reads is the
blueprint, and that matches, so no stage may treat this as a gate failure. Because the sheet
is hash-bound human authorship (`manifest.json` records `sha256` for both lyric files), no
bot may add the missing sections; only j_kro can, and the claim would then be re-made for
the new text. Blueprint title candidate #1 is the title actually used, so nothing else in
the sheet needs re-deciding.

## 6. Audio identity (locked for this genre)

Style field, verbatim from `music/prompts/activist.md` (585/1000 chars, measured):

```
modern protest anthem, 96 BPM, acoustic guitar strumming steady quarter-note chords, warm
upright bass, kick and tambourine on the backbeat, group vocals singing the chorus in unison
like a crowd at a march, lead vocal sincere and plainspoken mid-register, call-and-response
between lead and group, foot-stomp and hand-clap percussion layer, one quiet verse over solo
guitar, chorus big and chantable with repeated title line, gospel-choir energy without church
language, handheld-truth vocal production with minimal polish, hope with teeth, quiet-loud
dynamic between verse and chorus
```

Settings: **Weirdness 30 %** (sincerity is the currency; novelty reads as satire and kills
documentary sync), **Style Influence 70 %** (the topical content must come from the human
sheet, not from the model), **Exclude Styles:** `autotune, trap beats, EDM drops, aggressive
metal, party anthems, club`.

Tempo, measured and locked: **96 BPM** (`blueprints/activist.yaml: bpm_anchor: 96`). Three
live reads agree, §12 — **all three re-measured by this pass (§14)**:
`music/planner/planner.py show --genre activist` prints
`"structure_source": "blueprint", "blueprint": true, "bpm_anchor": 96`;
`planner.context_for("activist")` returns `{genre, registry, template, blueprint}` with
`blueprint["bpm_anchor"] == 96` (a `dict`, not the flat keys `show` prints); and a live
`plan --lyrics-mode draft` writes `"bpm": 96` because `planner.py:830` reads
`args.bpm or bpm_anchor_for(ctx) or 100`, where `bpm_anchor_for()` (`:203`) returns
`ctx["blueprint"].get("bpm_anchor") or ctx.get("template_bpm")` (`:212`) — the citations
`:470`/`:471` in the text above are stale after the planner grew its
`instrumental` mode. So this genre never takes the flat 100
fallback that the **seven blueprint-less genres** take (`load_blueprint()` returns `{}`
when `music/lyrics/blueprints/<genre>.yaml` is absent, and only 7 of the 14 genres have one — its own
docstring still quotes an old genre total). The live draft run, this pass:

```
$ /usr/bin/python3 music/planner/planner.py plan --brief "water, a town, a hearing" \
      --genre activist --lyrics-mode draft --out plan_draft.json
structure: Verse 1 -> Chorus -> Verse 2 -> Chorus -> Bridge -> Verse 3 -> Outro
bpm/key  : 96 BPM · C minor · 4/4
duration : 180s   language: en
validation: PASS
```

At 96 BPM, 4/4:

```
1 bar  = 4 × 60 / 96            = 2.500 s exactly
32 bars                          = 80.0 s
a 4-minute single (240 s)        = 96.0 bars exactly
```

Bar math is exact to the millisecond, so sync buyers can cut on bar lines. A default
3-minute plan (180 s) is 72 bars.

**Key is unclaimed.** The template names no key; the blueprint names none. The planner's
`--key` flag defaults to `None` (`music/planner/planner.py:912`) and the draft path writes
`args.keyscale or args.key or "C minor"` (`:831`), so an unkeyed draft plan's key field reads
**C minor** (measured in the run above and in §12 — not a planner default the flag itself
carries). Two flags now carry a key: `--key` and `--keyscale` (`:914`), the second being the
name the queue schema and the engine use; a card that states one of them must state both, or
say which it means. Decision: the render
picks, and whatever it picks is
declared in the sync metadata and in `loop_points`/`clearance` provenance. Do not carry a
key field that was never measured — see D2 in §8, which is now fixed in the live rail
(`v0.1.3` honours an explicit `keyscale`), and card `t_f65b0f4c` (ready) for the placeholder
itself.

One legitimate palette swap, per the template: hip-hop-format activist tracks change the
backing (boom-bap drums, spoken-word flow) but keep every lyric rule above.

## 7. Visual identity — locked style, rendered shape

`music/visuals/documentary-grain.md` is the style and it is unambiguous: handheld 16 mm
truth, palette `#6b6257` dust / `#9c8f7a` skin-and-paper / `#232019` shadow with **one**
accent colour per video (the movement's colour, used sparingly); gate weave and occasional
focus hunt, because steadicam polish reads as an ad; grain 6–8 %; hand-lettered or
typewriter lyrics appearing **on** the phrase, never after it; the chorus swaps to a crowd
of hands writing the same line. No glossy kinetic-type effects. No clickbait thumbnail —
design for the documentary supervisor. (Palette and grain re-read from the file at
`:7`–`:8` and `:21` in this pass; unchanged.)

**RESOLVED 2026-10-16 (§14) — the `lyric-video` shape now has a real artifact.** When this
brief was written `music/visuals/` held templates for four of the five real shapes and none
for the fifth. Card **t_ec378832** (`videobot`, done) rendered it rather than repointing
activist at `single-4min`, because `single_4min.mp4` is a static placeholder card, not a lyric
video. Measured with ffprobe this pass:

```
$ ~/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin/ffprobe -v error \
      -show_entries format=duration,size -show_entries stream=codec_name,width,height \
      music/visuals/lyric_video.mp4
codec_name=h264      width=1280  height=720  avg_frame_rate=25/1
codec_name=aac
duration=240.000000  size=41447357
```

`music/visuals/lyric_video.json` (7 512 B) carries the template's provenance: it is a
TEMPLATE, not a release asset, and its audio bed is a 96 BPM click slate, not a master.
`music/scripts/render_lyric_video.py` is the drivable renderer (lyrics + section timing).
The regression for the old defect is `music/scripts/check_video_shapes.py`, which now reports
every declared shape as present:

| video_shape | template | exists | genres |
|---|---|---|---|
| `album-30-60min` | `album_30_60min.mp4` | yes | chill-lounge, sentimental-piano, anime-ending |
| `mix-60min` | `mix_60min.mp4` | yes | trance, jungle-dnb |
| `loop-10min` | `loop_10min.mp4` | yes | the four elementals, chiptune-8bit |
| `single-4min` | `single_4min.mp4` | yes | epic-orchestral-boss, anime-opening |
| **`lyric-video`** | `lyric_video.mp4` | **yes** (240.000 s, 1280×720) | **activist (only)** |
| `none` | (none by design) | — | commentary-beds |

```
$ /usr/bin/python3 music/scripts/check_video_shapes.py
PASS check_video_shapes (2 warning(s))
  WARN  anime-ending: visual_style 'visuals/anime-ending.md' has no rendered clip anime_ending.mp4
  WARN  anime-opening: visual_style 'visuals/anime-opening.md' has no rendered clip anime_opening.mp4
rc=0
```

**CORRECTED:** the text here used to say *"nothing in the repo reads `video_shape` except
`registry.py`'s validator"*. That is no longer true — `video_shape` is read by
`music/scripts/loop_close.py:301` (`genre_video_shapes()`), `music/scripts/render_lyric_video.py`
and `music/scripts/check_video_shapes.py:66`. The registry now also has a check that would
have caught the original gap, because the gap was that the validator never resolved the value.

**Second consequence: no YouTube lane, and now no YouTube gate either.** The visual stage
previously ran `gate_youtube_authentic` unconditionally (`music/stages.yaml:74` then), so a
genre with no YouTube lane was gated against a surface it never publishes to. **Fixed in
`54f6d3c` (card t_d9983bb9, done), same change as §3:** the stage's gate is declared in
`music/lanes.yaml` under `stage_gates:` (`:118`) and resolved from the GENRE's own lanes. The
visual stage prompt is now `music/stages.yaml:86`, and it instructs the worker to run
`music/registry.py gate-for-stage --stage visual --genre <genre>` and to state explicitly when
the answer is `none`. For activist the live answer is `gate: none`, rc=0 (§3). The lyric
video's real consumers are the direct-fan post and the sync-documentary pitch, both of which
gate elsewhere.

## 8. Generation path — measured on this host

### The vocal rail already accepts this track (best news in the brief)

`suno-gen.py` **is in this checkout now** — `music/suno-gen.py`, 42 652 B / 1025 lines,
mtime 2026-10-16 14:23 — and the previous text's *"not in this checkout; `find
/home/j_kro -name 'suno-gen.py'` returns zero hits"* was true when it was written (the
diverged checkout, card t_8a715681, now done; `origin/main...HEAD` reads 0 behind in §11).
The probe below was originally run against the git object `origin/main:music/suno-gen.py`
in a scratch mirror; **this pass re-ran it against the in-tree file** (no CDP, no browser,
no GPU — these are pure file-I/O functions) and got the same result:

```
$ /usr/bin/python3 probe_vocal_rail.py
-- is_instrumental_template() for every registered genre (in-tree code) --
  instrumental (8): chill-lounge, chiptune-8bit, commentary-beds, elemental-air,
                    elemental-earth, elemental-fire, elemental-water, sentimental-piano
  vocal        (6): activist, anime-ending, anime-opening, epic-orchestral-boss,
                    jungle-dnb, trance
  activist instrumental? -> False
-- load_style_prompt('activist') --  chars: 585
-- load_track(activist/what-runs-beneath) — the VOCAL path --
  PASS load_track
  title        : What Runs Beneath
  lyrics chars : 1079      lyrics lines : 39
  section tags : ['[Verse 1]', '[Chorus]', '[Verse 2]', '[Chorus]', '[Bridge]', '[Verse 3]', '[Outro]']
  sheet header : # provenance: human-original (writer profile) — do not paste Suno-generated lyrics here
-- load_track with instrumental=True on the same dir (must REFUSE) --
  refused -> FATAL: --instrumental given but ... is not marked instrumental.
-- gate_quota (in-tree code) --  PASS gate_quota; used=0 period=2026-10
```

So activist is the **first genre in this lane whose generate stage can run end-to-end
against its own artifact**: the rail detects it as vocal (correctly), finds the human sheet,
verifies the `provenance: human-original` header, and refuses the instrumental shortcut.
The 39-line sheet yields 7 section tags for the renderer. Nothing in the vocal path needed
building, and the unblocking it needed (the diverged checkout, t_8a715681) has landed.

### The live queue path still cannot carry this track

**The in-cluster route has three rails, and they are not one code path** (measured live
with `kubectl` in namespace `mining`, 2026-10-16 — the earlier text called the render rail
the "sunolocal studio API", which is a different deployment):

- **plan rail** — CronJob `music-pipeline` (`17 */6 * * *`), fed by ConfigMap
  `music-pipeline-briefs`, writing `/var/lib/music-plans/<name>.json`.
- **render rail** — CronJob `music-pipeline-render` (`41 */4 * * *`) loops
  `/var/lib/music-plans/*.json` and runs exactly
  `python3 /payload/music/scripts/acestep_plan.py <plan> --name <stem>` — **no
  `--allow-empty`, no `--instrumental`** — then POSTs the ACE workflow to `COMFY_URL`,
  which that CronJob sets to `http://comfyui-zephyr.mining.svc.cluster.local:8188`
  (ComfyUI, not the studio service). **Re-read this pass, and it does more than that now:**
  after a successful render it asks `loop_close.py --claims-loop` whether the plan claims a
  seamless loop (the claim is the genre's `video_shape`, read from `genres.yaml`, not from
  prose), builds and level-checks the loop when it does, and writes `.rendered` /
  `.refused` / `.looprefused` markers so a refusal is not retried every four hours
  (card t_b21aeb51). For **activist the answer is `claim: false`** — measured:
  `loop_close.py --claims-loop --plan <draft>` → `{"claim": false, "genre": "activist",
  "video_shape": "lyric-video"}`, rc=1 — so this genre's renders take the plain
  `.rendered` path. A `lyric-video` single is not a loop claim; only `loop-10min` is.
- **studio rail** — Deployment `sunolocal-source` (image **`localhost/sunolocal:v0.1.3`**
  measured live this pass — the brief recorded v0.1.2; pod
  `sunolocal-source-75d58dbc97-7jfmc`, Service `sunolocal.mining:8123`, FastAPI
  `music.sunolocal.studio:app`); `studio.py` imports `suno_to_aceplan` from `translate.py`,
  so `translate.py` is this rail's translator.

Against that route, three measured gaps:

1. **No lyrics mode fits a human sheet.** `music/planner/planner.py --lyrics-mode` now accepts
   **three** modes — `draft|ai|instrumental` (`music/planner/planner.py:905`; the brief said
   `draft|ai` at `:528`, and `instrumental` was added for the 8 genres whose template declares
   an empty lyrics box) — but `plan` still has no flag that loads a sheet at all (flags:
   `--brief --genre --lyrics-mode --language --title --key --keyscale --bpm --duration --out
   --endpoint --model --temperature`, re-read from `plan --help` this pass). Re-measured end
   to end: `draft` rc=0 produces seven empty sections (bpm 96, key C minor — §6), which
   `acestep_plan.py` then refuses with rc=1 `FATAL: 7 section(s) have no lyrics: ...`
   (`music/scripts/acestep_plan.py:140`); and `ai` writes model lyrics that void
   the human authorship claim the whole copyright path rests on. `--lyrics-mode instrumental`
   is refused outright for this genre, with rc=2 and *"`activist` is not an instrumental
   genre"* (`planner.py:805`). Harder than either: the
   render payload (`ConfigMap mining/music-pipeline-payload`, mounted at `/payload`)
   carries `music/genres.yaml`, the six blueprints, `music/planner/planner.py`, the 14
   prompt templates, the 14 visual style docs, `music/scripts/acestep_plan.py` and
   `music/scripts/loop_close.py` — **39 keys, re-counted this pass** — and **no lyric SHEET**
   (no `music/lyrics/activist/...`; and no `music/suno-gen.py`). CORRECTED: the earlier text
   said "no `music/lyrics/` at all", which is now wrong — the six blueprints are themselves
   payload keys under `music__lyrics__blueprints__*.yaml`. What the pod lacks is the claimed
   sheet. This is a
   **third** case alongside the instrumental gap: not "no lyrics", not "AI lyrics", but "load the
   claimed sheet". Recorded on t_25a6499c, now done as far as the instrumental cases go;
   the human-sheet case is stated here.
2. **Tempo: both rails honour an explicit bpm now.** `acestep_plan.py:234-235`
   passes `plan["bpm"]` and `plan["key"]` into the ACE-Step `GenerationParams` as `bpm` and
   `keyscale` (`:224` carries `duration`), so the CronJob render rail honours 96 — the old
   citation `:98-100` is stale. Re-read by card `t_6dd13d76` (2026-10-16): the `:189`–`:190`
   this brief carried was stale — the file grew under the citation, and `:234`–`:235` is where
   the two fields are set now. The studio rail's chart copy
   (`/home/j_kro/mining-k8s/helm/charts/sunolocal/files/music/sunolocal/translate.py`, 4 907 B)
   now reads `bpm = None; if req.bpm is not None: bpm = int(req.bpm)` (`:62`–`:64`), falls back
   to the style-weight mapping only when no bpm is given (`:67`), and defaults to 120 last
   (`:69`): **an explicit tempo wins**, so a studio-service render of this plan is no longer
   1.25× too fast. The `bpm = 120` / `int(60 + req.style_weight * 120)` lines the brief quoted
   as `:42`/`:45` sit in NEITHER copy now: card `t_42bc85ba` (done) reconciled this repo's
   mirror `music/sunolocal/translate.py` (4 907 B, 113 lines) with the chart's copy and the two
   are byte-identical (`sha256 25fb26ee…`), card `t_0be5f2bf` deleted the dead third copy, and
   the last-resort `bpm = 120` now sits at line 69, after the explicit-tempo branch
   (`bpm = int(req.bpm)` at line 64) and beside `key = req.keyscale or "C major"` at line 76.
   Read the pod, not a mirror: the pod runs v0.1.3.
   Acceptance for this genre stays: the plan's `bpm` field reads **96**, never 120 and
   never the 100 fallback.
3. **The key field is fixed in the live rail.** The chart copy now reads
   `key = req.keyscale or "C major"` (`:76`) with the comment *"NEVER `req.style`: that is the
   genre's whole style caption … and acestep_plan.py passes this value straight to the ACE node
   as `keyscale`"* — so the 585-character caption can no longer land in a key signature.
   The old line, `key = req.style or "C major"`, is `music/sunolocal/translate.py:49` in the
   stale repo mirror. On the plan rail the value is `plan["key"]`, which for a draft is the
   unmeasured `"C minor"` (§6) — not the caption, but still not a key anyone selected; that
   placeholder is card `t_f65b0f4c` (ready).

(2) and (3) as they affect the studio rail were D1/D2 on t_25a6499c, now done — and the fix is
in the image the pod runs, not in the repo mirror.
Brief list: the chart's `briefs:` block is no longer empty
(`/home/j_kro/mining-k8s/helm/charts/music-pipeline/values.yaml:73`, and the comments there
record that the Argo Application's inline `helm.values` is what actually fills the ConfigMap,
with `check-queue-sync.sh` failing when the two lists disagree). The live ConfigMap
`mining/music-pipeline-briefs` carries **11 entries across 9 genres**, re-counted this pass —
not the single chill-lounge entry the brief recorded — and **no activist entry exists either
way**: the queue holds chill-lounge ×2, anime-ending, epic-orchestral-boss, trance,
elemental-air, elemental-earth, elemental-fire, sentimental-piano and commentary-beds ×2.
Sibling cards for trance (`t_791b48f7`) and anime-ending (`t_a14e5d52`) are both done; their
entries are in the queue.

Export policy: exports go through **Suno Studio** (unlimited), never the standard download
button. `gate_quota` PASSes live at 0/60 for period 2026-10 with 0 studio exports. At 1/wk
cadence the standard-download meter is not a constraint for this genre; the CDP session
and the two meters (Suno download credits vs the 60/month standard counter) are, per the
commentary-beds finding.

## 9. Existing assets for this genre

Measured: **the lyrics half of one track and nothing else.**

- `music/lyrics/activist/what-runs-beneath/` — `lyrics.suno.txt` 1399 B, `lyrics.txt`
  1009 B, `manifest.json` 1013 B, `title.txt` 18 B. Gate PASS, strict PASS (§5).
- `music/lyrics/blueprints/activist.yaml` — 2023 B, the planner's constraining brief.
- `music/prompts/activist.md` 4448 B, `music/visuals/documentary-grain.md` 1425 B.
- **No audio. No stems. No master. No cover art. No campaign directory** (`campaigns/`
  holds **ten** campaigns, re-counted this pass — the brief said nine; none for this genre).
  `~/Music` is empty (`ls -A ~/Music | wc -l` → 0). `music/generated/` does
  not exist. The first render is genuine work, not a re-run. One artifact of this genre does
  now exist outside `music/`: the `lyric-video` shape template (§7), which is a template, not
  a release asset.
- Quota untouched — re-measured this pass, counters unchanged. The ledger does now carry a
  `renders` list recording the one local ACE render in the fleet (elemental-air, card
  t_b8afb055); its own note states such renders consume no Suno quota, and the counters below
  are unaffected by it.

```
$ /usr/bin/python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

## 10. Stage plan for this genre

`brief` ✓ → `genre-select` (trivially satisfied by §1–§3; confirm, do not re-derive) →
**`lyrics` — already satisfied** (the sheet exists, `gate_lyrics_original` PASSes plain and
`--strict`, and its section map matches the blueprint in order; the stage records the
authorship claim and must never edit the hash-bound sheet — §5) → `generate` (quota gate first; **vocal path**,
`--instrumental` is refused by the rail for this genre; expect `bpm: 96`) → `curate` (pick
the winning render, record a reject reason per loser) → `stems` (≥ 4, ±0.5 s of master,
plus a genuinely distinct instrumental version) → `master` (**two** deliverables: −14
streaming, −16 sync) → `gate` (independent review on a different model against
`music/rubrics/vocal.json`: weights 3/3/2/2/1/1, geometric-median panel aggregate, pass at
7.0 — the two weight-3 criteria are `chantable_chorus` and `named_target`) → `package`
(`gate_release_ready` for streaming, `gate_sync_ready --lane sync` for sync-documentary,
`gate_human_approval` for direct-fan, clearance PDF, non-empty AI disclosure) → `visual`
(lyric video — the shape template now EXISTS, §7; render with
`music/scripts/render_lyric_video.py`, then resolve the stage's gate per genre:
`music/registry.py gate-for-stage --stage visual --genre activist` answers `none`, so this
stage runs **no** video gate and must state that on the card — a gate for a surface the genre
never publishes to is a false check) → `human-approval` (j_kro) → `publish`
(private/draft only; Patreon/Ko-fi posts are `socialbot`'s, and no bot may approve its own
publish).

## 11. Provenance

- Registry and template: `music/genres.yaml`, `music/lanes.yaml`, `music/prompts/activist.md`,
  `music/visuals/documentary-grain.md` — all resolved live; `registry.py validate` → 14
  genres / 10 lanes / 1 stage gate rule, rc=0
- Blueprint: `music/lyrics/blueprints/activist.yaml` read through `planner.context_for()`
  (`blueprint: True`, `bpm_anchor: 96`)
- Gates exercised live: `gate_quota` PASS; `gate_lyrics_original` PASS (plain + `--strict`);
  `gate_sync_ready` FAIL rc=1 with **14** findings (`--lane sync`) and FAIL rc=1 with the same
  14 for `--lane sync-documentary` (was rc=2 — fixed, §3);
  `gate_release_ready` FAIL rc=1; `gate_human_approval` FAIL rc=1;
  `music/registry.py gate-for-stage --stage visual --genre activist` → `gate: none`, rc=0
  (and rc=2 for an unknown genre)
- Oracle: `music/oracle.py` imported and every component recomputed on this host for
  §2 (`WEIGHTS`, `REVENUE_BANDS`, `BANNED_SURFACES` read from source at lines 54/64/81 —
  unchanged), plus a single `score_genre("activist", …)` call → `total: 7.0`
- Vocal rail: **`music/suno-gen.py` in this tree** (42 652 B, 1025 lines) executed through
  `importlib` (`probe_vocal_rail.py`); `is_instrumental_template`, `load_track`,
  `load_style_prompt`, `gate_quota` all exercised. The earlier pass read the same code out of
  `origin/main:music/suno-gen.py` because the tree lacked it (t_8a715681, now done)
- Engine state read live, not from memory (root `/home/j_kro/mining-k8s`):
  `helm/charts/sunolocal/files/music/sunolocal/translate.py` now honours an explicit
  `bpm` (`:62`–`:64`) and an explicit `keyscale` (`:76`) — the old `:42`/`:45`/`:49` lines the
  brief quoted are gone from the chart and live only in this repo's stale
  `music/sunolocal/translate.py` mirror; `helm/charts/music-pipeline/values.yaml:73` is a
  populated `briefs:` block. Live cluster reads (2026-10-16, `kubectl -n mining`): CronJobs
  `music-pipeline` + `music-pipeline-render` (the render rail now also runs `loop_close.py`),
  ConfigMaps `music-pipeline-briefs` (**11 entries / 9 genres**) + `music-pipeline-payload`
  (**39 keys**: genres.yaml, 6 blueprints, 14 templates, 14 visuals, planner.py,
  acestep_plan.py, loop_close.py — and still no lyric SHEET), Deployment `sunolocal-source`
  (`localhost/sunolocal:**v0.1.3**`) + `comfyui-zephyr`
- Rulings: `brain/RULINGS.md` read again in full this pass (the protest-lyric ruling is
  still at §Music line 61 — *"Protest lyrics need a chantable chorus and a named target. Vague
  fury with no concrete image fails the genre's function"* — plus the panel mechanics and the
  new master rule *"Masters hit lane loudness targets: -14 streaming / -16 sync, +/-1 dB,
  measured (volumedetect dialect)"*, which is the dialect §3 records);
  `brain/playbooks/music-lane-architecture.md` is cited by the profile, `stages.yaml`,
  `genres.yaml`, `lanes.yaml`, `autonomy.yaml`, every gate and `music/rubrics/vocal.json`
  (source `"arch"`). **CORRECTED this pass: both brain files are now TRACKED IN HEAD** —
  `brain/playbooks/music-lane-architecture.md` at 34 328 B (it was untracked when it first
  appeared at 13:59:25 and has grown since) and
  `brain/research/music-monetization-2026.md` (11 067 B);
  `git ls-files` lists both, so the authoring card **t_b0a4db92** (done) did its job. Both are
  still **absent from `origin/main`** (`git cat-file -e origin/main:<path>` → absent), so a
  fresh clone still cannot resolve the citation. Treat them as authoritative only for readers
  of this tree, and note that the doc's line 101 `video_shape: lyric-video` now has its
  artifact (§7).
- **Standing checks, re-run on the pre-correction blob by this pass (§14) and again after
  the edits — every one of them scoped to this brief, because the repo-wide runs FAIL on
  other genres' briefs and that list shifts as their owners edit:**
  `check_brief_figures.py` → `--selftest` PASS, then **104 of 105** recomputed figures OK
  repo-wide with **no failure in this brief** (the one failure moved between runs; other
  genres, not this one); `check_prompt_style_counts.py` PASS (15 claims / 14 templates);
  `check_brief_paths.py` PASS (15 citations); `check_brief_line_refs.py` PASS for this brief
  (its repo-wide failures are other genres' files, and the list shifts); `check_brief_drift.py` PASS **for this brief** (4 live    
  counts) while its repo-wide run FAILs on another genre's file;
  `check_stage_scripts.py` **now PASS** (11 script paths) — the earlier FAIL was
  the missing `music/suno-gen.py`, and that file is in the tree now; plus
  `check_oracle_board.py`, `check_oracle_determinism.py`, `check_gate_lane_surface.py`,
  `check_stage_advance.py`, `check_bpm_solutions.py`, `check_video_shapes.py` and the
  check this pass added, `check_brief_absence.py` (PASS for this brief, FAIL on three other
  briefs — §14.3), all PASS.
- **Carded elsewhere, re-checked for status this pass:** diverged checkout t_8a715681 —
  **done**; scheduler units on the wrong checkout t_41f354be — **done**; render-path D1/D2 +
  queue schema t_25a6499c — **done** (and the fix is in the pod image v0.1.3, §8); duplicate
  oracle cards t_bf0e5edd — **done**; the architecture doc t_b0a4db92 — **done** (committed,
  still not on `origin/main`); `gate_loudness` ruler t_9546841b — **done on a branch**
  (`e783a96` on `origin/publish/audio-lane-2026-10-16`, NOT an ancestor of `8f0fd9a`), so the
  ruler in `main` is unchanged; profile workdir/kanban env t_75aacf8b — **done**; the
  sync-documentary gate lane **t_d9983bb9** — **done** (§3); the `lyric-video` shape +
  YouTube-gate mismatch **t_ec378832** — **done** (§7); platform-native visual shapes
  t_85db696a — **done**; commentary-beds "4133 B" unit labels t_e504b516 — still **blocked**.
  Newly relevant open cards: the plan's placeholder key `t_f65b0f4c` (ready), the two-copy
  sunolocal engine source `t_0be5f2bf` / `t_42bc85ba` (ready), and the music-lane regression
  schedulers `t_207dc413` (ready).
- **Duplicate cards:** t_ace3bfb1 (`music-oracle: activist (score 7.25)`, done) wrote this
  brief; t_b7dd5655 (`music-oracle: activist (score 7.45)`, done) ran its verification pass
  (§12); **t_752f02a8 (this pass, §14) is the surviving open card**. Only one brief exists per
  genre, so all three resolve here, and none of them started a second brief or a second stage
  chain.
- **hotspot:** `music/briefs/` — concurrent brief-stage workers write this directory and
  commit into one shared tree. At the 13:54 verification: HEAD `fa3163f` read 15 behind / 29 ahead
  of `origin/main`; at 13:58 the same tree read 15 behind / 32 ahead, and at 13:35 it read
  7 ahead; at this pass HEAD `8f0fd9a` read **0 behind / 71 ahead** (the deficit closed with
  `ab33ad1`). The count is not a stable fact — re-measure it, never copy it. Board census at
  13:54: 4 running / 24 ready / 7 todo / 4 blocked / 57 done; at this pass:
  **7 running / 41 ready / 4 todo / 8 blocked / 99 done / 1 archived**. `music/briefs/` also
  gained `check_brief_figures.py` (`fa3163f`, `cab0415`), `check_brief_drift.py` (§12) and
  `check_video_shapes.py` after the brief was written — the check directory changes under the
  file it checks. Worktree at this pass held one untracked file (`concat_list.txt`) and two
  other briefs with uncommitted edits (`anime-opening.md`, `epic-orchestral-boss.md`) —
  concurrent workers in the same tree, again; `music/visuals/lyric_video.mp4` (41 447 357 B)
  and `music/scripts/render_lyric_video.py` are both tracked (`1a450e0`). Nothing outside
  `music/briefs/activist.md` was staged by this pass.

## 12. Duplicate-card verification pass (t_b7dd5655, 2026-10-16T13:54-05:00)

This brief was written by t_ace3bfb1. t_b7dd5655 is the second oracle card for the same
genre, so it resolves to this file rather than writing a second one. Its work was a
verification pass: re-measure every checkable claim in place, correct what is wrong, and
record the corrections. No stage chain was started; a brief is keyed by genre, not by card.

**Supersession.** The committed blob was
`sha256 a47b0f9bcdb5f937b5681b4c907456f28ef15bf524743359729e00f579a1026a` (`a4ba657`,
27917 B). This pass edits the file in place; the header records the superseded hash, as
`check_brief_figures.py` requires for a brief that carries a recorded hash.

**Re-measured and held** (no change): registry 14 genres / 10 lanes; the three file sizes
(4448 B prompt, 1425 B visual, 2023 B blueprint); style caption 585 chars; the lyric sheet's
four file sizes (1399/1009/1013/18 B); `gate_lyrics_original --strict` PASS (7 sections,
112 unique words, j_kro @ 2026-10-08T12:48:59Z); `gate_quota` PASS 0/60; `gate_release_ready`
FAIL rc=1 (4 items); `gate_sync_ready --lane sync` FAIL rc=1 (7 items);
`gate_human_approval` FAIL rc=1; `--lane sync-documentary` rc=2 at `gate_sync_ready.py:47`;
`music/lanes.yaml:66`; `music/stages.yaml:74`; the `video_shape` table (4 of 5 shapes have a
template, `lyric_video.mp4` does not); 7 blueprints now (3 when this pass ran); autonomy all `advisory`;
`campaigns/` nine campaigns and none for this genre; `~/Music` empty; no `music/generated/`;
`~/Music` and `find /home/j_kro -name suno-gen.py` both empty; the rubric's 3/3/2/2/1/1
weights at `pass_threshold` 7.0. **§8.1 reproduced exactly** by re-running
`origin/main:music/suno-gen.py` in a scratch mirror against this repo's data: 8 instrumental
/ 6 vocal genres (same two lists), `activist -> False`, `load_style_prompt` 585 chars,
`load_track` → title/1079 chars/39 lines/7 tags, `instrumental=True` refused with the same
`FATAL` string.

**Corrected (seven, plus one amendment after the first commit):**

> Forward note added by the surviving-card pass of 2026-10-16T16:00 (§14): items 1, 5, 6 and 7
> below were correct when measured and have since been overtaken by later commits, and the
> paragraph after them ("Also true and left standing") no longer holds. Each carries a
> `SUPERSEDED (§14)` line. The history is kept, not rewritten, because the figures were real
> measurements of a real clock.

1. Header/§2 — live re-score is **7.20**, not 7.00: `trend_signal` measured **5.0** (the
   exception branch) this run against **3.0** when the brief was written. Both values are
   live; the term is not reproducible, which is itself the finding.
   **SUPERSEDED (§14):** `b2d11f7` removed both live values — a failed fetch now scores the
   no-signal floor like an empty success, so the reachable total is **7.0**, and the oracle's
   dedupe ruling files this genre at 7.0. Re-measured with `oracle.score_genre()` → `total: 7.0`.
2. Header/§11 — at `fa3163f` (13:54) the divergence was 15 behind / 29 ahead of `origin/main`.
   The brief had recorded 15/7 at `9ebf6af` (13:35), and the same tree read 15/32 at 13:58.
   A live count in a committed brief ages in minutes; `check_brief_drift.py` now exists for
   exactly this (§12, "Standing check added"). (Still true as history; the deficit itself was
   cleared at 14:23 by `ab33ad1` — §14 reads 0 behind / 71 ahead at `8f0fd9a`.)
3. §6 — `--key`'s argparse default is `None`; `"C minor"` comes from the draft path
   (`planner.py:471` then; the same expression is `:831` now, `args.keyscale or args.key or
   "C minor"`). Verified against a live draft plan.
4. §6 — `bpm_anchor: 96` as a flat pair of keys is `planner.py show`'s output;
   `context_for()` returns a `blueprint` dict, and the draft path reads
   `bpm_anchor_for(ctx)` (`:203`/`:212`) then `or 100` (`:830`).
5. §6 — **eleven** genres took the 100 fallback, not seven: 14 registered genres, 3
   blueprints at 13:54; six at 15:31, so **eight** genres take it. (`load_blueprint()`'s own
   docstring still quotes an old genre total.)
   **SUPERSEDED (§14):** `jungle-dnb.yaml` landed at 15:49 (`8f0fd9a`), so the census is
   **seven** blueprints / seven fallback genres — the §1 and §6 sentences are correct as they
   stand, and this item's "eight" is the stale one.
6. §5 — the concrete-image claim is **18 named terms, all present verbatim**; the earlier
   "(23 distinct hits)" cannot be reproduced from the list the brief prints. The title is
   verbatim in the chorus; the outro repeats it in lower case.
   **SUPERSEDED (§14) in method, not in count:** 18 holds, but "verbatim" hides three
   line-initial capitals ("Gravel", "Forty folding chairs", "Boots") and the title-cased
   string appears only in the sheet's own header — the chorus and the outro both carry the
   sentence-case phrase. §5 now says so.
7. §8 — the render rail posts to **ComfyUI** (`COMFY_URL` =
   `comfyui-zephyr.mining.svc.cluster.local:8188`) and passes the plan's own bpm/key
   (`acestep_plan.py:98-100`, now `:189`–`:190`), so the 120 BPM / caption-as-key defects belong to the
   **studio rail** (`sunolocal.mining:8123`, `translate.py`), not to the CronJob queue. The
   render payload mounts no `music/lyrics/`. The chart's `briefs: []` is still empty, but
   the live ConfigMap carries one chill-lounge entry — Git and cluster differ.
   **SUPERSEDED (§14):** the ComfyUI half holds; the rest does not. The chart's `briefs:`
   block is populated (11 entries, `values.yaml:73`), the live ConfigMap carries the same 11
   across 9 genres, the payload now does carry `music__lyrics__blueprints__*.yaml` (only the
   lyric SHEET is still absent, 39 keys total), and the studio rail's chart copy honours an
   explicit bpm and `req.keyscale` — the pre-v0.1.3 lines survive only in this repo's
   `music/sunolocal/translate.py` mirror.

**Also true and left standing:** `music/suno-gen.py` is genuinely absent from this working
tree (`find /home/j_kro -name suno-gen.py` → zero hits) and genuinely present on
`origin/main` (last touched `ba28f55`, 2026-10-14). That is the divergence t_8a715681, not
a wrong citation: do not delete the reference, merge the refs.
**SUPERSEDED (§14):** the divergence was reconciled — `music/suno-gen.py` is in this tree
(42 652 B, mtime 14:23), `find` returns it, and `origin/main...HEAD` reads 0 behind. The
reference stays; the absence does not.

**8. §11 amendment (§12) — the architecture doc appeared mid-pass, and is now committed.**
`7e54e03` recorded, correctly at measurement time, that
`brain/playbooks/music-lane-architecture.md` was not on this machine. At 13:59:25 — between
that commit and this amendment, in the same working tree — another worker wrote it: 21 696 B /
502 lines, plus `brain/research/music-monetization-2026.md` (11 067 B). Both are in this tree
and tracked in `HEAD` now — playbook 34 328 B, rewritten at `7411afa` (head touching it
`6b24a52`), card `t_b0a4db92` done. The doc's §11 (self-run design) is the section that
carries this brief's claim, and `music/scripts/check_doc_refs.py` resolves every `§` reference
to it. Only the remote still lags: both files stay off `origin/main`, so a fresh clone of the
remote has no copy. Card `t_fa731c5b` stripped this reading from the sibling briefs. Same
drift class as corrections 1 and 2 — this time the artifact itself moved, not a count. It was
caught only because the pass re-read the tree after committing instead of trusting its own
earlier read.

**Standing check added (the regression for corrections 2 and 5).**
`music/scripts/check_brief_drift.py` — the check that would have caught two of the three
stale figures above. `check_brief_figures.py` only recomputes figures that carry a unit next
to a named file, so a bare divergence number and a blueprint-census count were skipped, and
both sat in a committed brief. The new check recomputes exactly those: any `<n> behind … <m> ahead` pair
against `git rev-list --left-right --count origin/main...HEAD`, and any blueprint census
(`<n> blueprint-less genres`, `only <n> genres with a lyric blueprint`, `<n> of the <m>
genres`) against `registry.load_registry()` minus `music/lyrics/blueprints/*.yaml`. A claim
that stamps its own revision or clock time is treated as a historical fact and skipped;
an unanchored count must hold against the present tree, and that is the deliberate
distinction that makes it catch drift instead of flagging every sentence.

```
$ /usr/bin/python3 music/scripts/check_brief_drift.py --selftest
SELFTEST PASS check_brief_drift: current-claims flagged=0 (want 0), checked=3 (want 3),
  stale-claims flagged=3 (want 3), anchored skipped=True

$ /usr/bin/python3 music/scripts/check_brief_drift.py --rev a4ba657 --briefs music/briefs/activist.md
FAIL check_brief_drift: 2 stale count(s) in revision a4ba657
  music/briefs/activist.md:281  claimed "seven" blueprint-less genres  measured 11 ...   (at `a4ba657`)
  music/briefs/activist.md:480  claimed "15 behind / 7 ahead"  measured 15 behind / 32 ahead ...
```

The pre-correction revision FAILs on both classes, which is the proof the check is not a
no-op; the corrected file PASSes. Its own first draft flagged a correct sentence ("one of
only *three* genres with a lyric blueprint" counts the genres that HAVE one, the opposite
direction from "blueprint-less") — that false positive is fixed and recorded in the code,
because a noisy check is the failure mode this lane cannot afford.

**Method note for the next verifier:** two of the seven corrections sit in the header and one
in a table cell, so a checker that only reads body prose misses them; and three of them were
counts that aged between the write and the read, not mistakes at write time. Re-measure,
then either correct the number or anchor it to the revision you measured — do not copy it
forward.

## 13. Aged live counts re-measured (card `t_0f7aed63`, 2026-10-16)

`music/scripts/check_brief_drift.py` (added by card `t_b7dd5655`) recomputes the two families of
live count a brief cites and FAILs on any that has aged. It flagged this brief on both: the
blueprint census and the clone divergence. Re-measured and corrected in place; no other claim in
this brief was touched.

- **Superseded revision of this file:** `sha256 7e9a1cc897a09f4e5fa6126cc765e9fdf10ff9a74fdb68d4e95ee8a15584967c` (665 lines / 41631 B).
- **Blueprint census:** 7 of the 14 genres carry a lyric blueprint — `activist`, `anime-ending`,
  `anime-opening`, `chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`, `trance`. The other 7 take
  the planner's flat `bpm = 100` fallback. The 2026-10-16 15:31 pass behind this section measured
  the census at six, and it was 3 when this brief was written (13:35); what landed since is two
  anisong blueprints, one gamer blueprint and `jungle-dnb.yaml` (card `t_e6d422ec`).
- **Clone divergence, re-measured 2026-10-16 15:31 CDT:** the pair reads 0 behind / 61 ahead of
  `origin/main` at `e40c7f9`. The 15-commit upstream deficit this brief recorded at 13:35 to
  13:58 was cleared by the reconciliation merge `ab33ad1` (14:23); the local tip still rises
  with every brief this lane commits to the shared tree. Every divergence claim in this brief is
  stamped with the revision it was measured at, because such a count ages in minutes.
- **Corrected in place:** §1 (the census sentence and its file list), §6 (the 100-fallback
  census), §8 (the deployed payload's blueprint count, re-read from the live
  `music-pipeline-payload` ConfigMap: 38 keys, 6 of them blueprints), §11 (the "3 blueprints
  only" line) and §12 correction 5.
- **Superseded by this pass (card `t_e6d422ec`, 2026-10-16):** `sha256 3b8a9d7404380bcf129652902f6892d536ce148b3de224c60b3c3887ba0879fc` (688 lines / 43483 B) — the census statements above and in §1 and §6 were restated as live claims when `music/lyrics/blueprints/jungle-dnb.yaml` landed. Only the counts moved; no genre finding was reopened.
- **Superseded by this pass (card `t_6dd13d76`, 2026-10-16T17:21-05:00 CDT):** `sha256 12d1e1001c001cd2fb0876e590dd222ebc479f824e2c84232a000cd1550f88e5` (1070 lines / 73389 B) — two citations that had aged under the file they name: the ACE-Step tempo/key pair (§3 and §12) now reads `acestep_plan.py:234`–`:235` with `duration` at `:224`, and the engine mirror `music/sunolocal/translate.py` is no longer pre-v0.1.3 — card `t_42bc85ba` reconciled the two copies (4 907 B, 113 lines, `sha256 25fb26ee…`). No genre finding was reopened.

## 14. Surviving-card pass — the oracle ruling and every claim re-measured (`t_752f02a8`, 2026-10-16T16:00-05:00)

This card is the **surviving** oracle card for `activist`. Briefs in this lane are keyed by
**genre**, not by card, so this pass wrote no second brief and started no second stage chain:
it re-measured every checkable claim in the survivor against live state and corrected the ones
that had aged. The board reports one open card per genre, rc=0.

**Supersession.** The blob this pass started from was
`sha256 f28792a7ca79628e1993c03e90bf6ea0be02e786bd3536348742c04956ffe21b` (689 lines /
43 914 B), committed at `8f0fd9a`; the header records that supersession, and the current
digest is re-readable with `sha256sum music/briefs/activist.md`. The chain before it:
`a47b0f9b…026a` (`a4ba657`) → `7e9a1cc8…67c` → `3b8a9d74…9fc`.

### 14.1 The oracle dedupe ruling, applied

The 2026-10-09 double emission gave this genre two cards ten minutes apart (t_ace3bfb1,
t_b7dd5655, both done); the pair differed by exactly 0.20 = `WEIGHTS['trend_signal'] × (5.0 −
3.0)`, the premium the old `except` branch paid to a FAILED trend fetch. **True score
7.0/10**, not the 7.2 in this card's title — quota headroom 10.0, lane coverage 6.0, revenue
potential 10.0, cadence fit **0.0** (14 days left at 1/wk), policy risk 10.0, trend signal
3.0. Reproduced in this pass with the repo's own entry point:

```
$ /usr/bin/python3 probe_score.py
  cadence_fit_score('1/wk') = 0.0
  scores: {'quota_headroom': 10.0, 'lane_coverage': 6, 'revenue_potential': 10.0,
           'cadence_fit': 0.0, 'policy_risk': 10.0, 'trend_signal': 3.0}
  total: 7.0
```

Well above the 5.0 threshold → the routing verdict is unchanged; the number is corrected.
§2 now carries the reachable total and the API note (a caller that passes a genre name where
`cadence_fit_score()` wants a cadence string silently gets the neutral 5.0).

### 14.2 What moved after the brief stage — corrections applied in place

The brief stage measured a tree that has since been reconciled, and the lane closed six of the
defects the brief carded. Twelve claims are corrected, in the header and §1–§13.

| § | Claim as written | Live measurement (this pass) |
|---|---|---|
| header | card t_ace3bfb1; duplicate t_b7dd5655 "still `ready`" | t_752f02a8 is the surviving OPEN card; both twins `done`; oracle true score 7.0 |
| header/§11 | "15 behind / 7 ahead" at 13:35, 15/29 at 13:54, 15/32 at 13:58 | `git rev-list --left-right --count origin/main...HEAD` → **0 / 71** at `8f0fd9a`; the deficit closed at 14:23 with `ab33ad1` |
| §1 | `registry.py validate` → "14 genres, 10 lanes" | live adds `, 1 stage gate rule(s)` and the line `stage gate visual: lane_gate -> gate_youtube_authentic (when_absent: none)` |
| §2 | live re-score 7.20 / 6.70 | **7.0**; `TREND_NO_SIGNAL = 3.0` floors a failed fetch (`oracle.py:280`, `:300`, `:309`), so the swing is gone |
| §3 | `gate_sync_ready --lane sync` FAIL, **7** findings | **14** findings — the gate now also enforces the manifest `metadata` object and its six fields |
| §3 | `--lane sync-documentary` → rc=2, a DEFECT; `gate_sync_ready.py:47` `LANES` tuple | **rc=1 with the same 14 findings**; the gate derives its lanes from `lanes.yaml` (`choices=lanes`, `:581`). Fixed in `54f6d3c` (t_d9983bb9, done) |
| §3 | `gate_loudness` ruler defect, card t_9546841b | still the ruler in `main` (`volumedetect`, file untouched since 2026-10-09); the fix `e783a96` is on `origin/publish/audio-lane-2026-10-16`, **not** an ancestor of `8f0fd9a` — measured with `git merge-base --is-ancestor` |
| §5 | title "verbatim in the chorus twice"; outro differs by case | all 18 image terms present (3 are line-initial capitals); the title-cased string occurs once, in the sheet header; chorus **and** outro both carry the sentence-case phrase |
| §6 | planner `:470`/`:471` read the bpm anchor; `--key` at `:533` | `:830`/`:831`, `bpm_anchor_for()` at `:203`/`:212`, `--key` at `:912`, and a new `--keyscale` at `:914`; live draft plan → 96 BPM · C minor · 180 s |
| §7 | `lyric-video` has **no** artifact; `video_shape` read by nobody but the registry | `music/visuals/lyric_video.mp4` exists — ffprobe: h264 1280×720, **240.000000 s**, 41 447 357 B (t_ec378832, done); readers now incl. `loop_close.py:301`, `render_lyric_video.py`, `check_video_shapes.py:66`; the visual stage resolves its gate per genre → `gate: none` |
| §8 | `suno-gen.py` "not in this checkout"; studio rail `v0.1.2`; `translate.py:42/45/49` in the chart; payload "no `music/lyrics/`"; chart `briefs: []`; 1 queue entry | `music/suno-gen.py` 42 652 B / 1025 lines **in tree** (probe re-run against it, same results); pod runs **`v0.1.3`**; the chart now honours an explicit `bpm` (`:62`–`:64`) and `req.keyscale` (`:76`) — the old lines survive only in `music/sunolocal/translate.py`; payload 39 keys with 6 blueprints but no sheet; chart + ConfigMap both carry **11 entries / 9 genres**; `acestep_plan.py:234`–`:235` (was `:98-100`) |
| §8 | render rail "runs exactly" acestep_plan | it now also runs `loop_close.py` (loop claim → build → level check, t_b21aeb51); for activist `--claims-loop` → `{"claim": false}`, rc=1 |
| §9 | `campaigns/` holds nine campaigns | **ten**; `~/Music` still empty; quota still 0/60 with 0 studio exports (ledger gained a `renders` list that does not touch the counters) |
| §10/§11 | visual "blocked on the missing shape"; brain docs untracked; `check_stage_scripts` FAIL; 12 cards listed as open/ready | visual unblocked; both brain docs **tracked in HEAD** (arch doc now 34 328 B) and still absent from `origin/main`; `check_stage_scripts` PASS; of the 12 carded items, 9 are `done` (t_8a715681, t_41f354be, t_25a6499c, t_bf0e5edd, t_b0a4db92, t_75aacf8b, t_d9983bb9, t_ec378832, t_85db696a), 1 is done **on a branch** (t_9546841b), 1 is still blocked (t_e504b516), and t_9546841b's sibling `t_f65b0f4c` (the placeholder key) is ready |

The two `music/lyrics/` clarifications are worth stating plainly: the payload has **no lyric
sheet** (no `music__lyrics__activist__*`), but it does carry the six blueprints, which live
under `music/lyrics/blueprints/` — so the old phrasing "no `music/lyrics/` at all" was wrong
even though its conclusion (the claimed sheet is not in the pod) still holds.

### 14.3 Checks — fail-before / pass-after, on the committed revisions

```
# after (this pass, worktree) — every check scoped to this brief
PASS check_brief_absence  activist.md: 3 worktree-absence markers, 0 stale              rc=0
PASS check_brief_figures  104 of 105 figures repo-wide OK; 0 failures in activist.md    rc=1 (other genres)
PASS check_brief_drift    4 live counts in this brief (0 behind / 74 ahead at this run) rc=0 for activist.md
PASS check_brief_line_refs / check_brief_paths / check_brief_bpm_solutions /
     check_prompt_style_counts / check_stage_scripts / check_gate_lane_surface /
     check_stage_advance / check_oracle_board / check_oracle_determinism /
     check_video_shapes

# before (revision 8f0fd9a, the pre-correction blob) — the stale class was real
FAIL check_brief_absence: 1 stale absence claim in 1 brief                                 rc=1
  music/briefs/activist.md:371  claims 'suno-gen.py' is absent; it exists at 'music/suno-gen.py'
      `suno-gen.py` is **not in this checkout** — `find /home_j_kro -name 'suno-gen.py'` returns
```

The repo-wide runs of `check_brief_figures`, `check_brief_line_refs`, `check_brief_drift`,
`check_brief_bpm_solutions` and `check_brief_absence` FAIL on **other** briefs — this tree is
shared, six or seven music workers commit into it, and their files move between runs
(`elemental-water.md:600` 53 vs 88 lines; `elemental-fire.md:605` blank-open line 83;
`elemental-earth.md:776` a divergence pair that no longer holds, and `:730` a styleWeight that
buys 88 BPM, not 156; the three absence claims in §14.3). Reported, not touched here: they
belong to their owners' cards.

**Standing check added (the regression for the §8 class).**
`music/scripts/check_brief_absence.py` — no brief may claim a repo path is ABSENT from this
checkout while the path exists. Nothing in the check family could see that sentence:
`check_brief_figures.py` wants a figure with a unit beside a named file,
`check_brief_drift.py` wants a divergence or census count, and this is a present-tense claim
about existence. The check is deliberately narrow: the marker's OBJECT decides scope
(worktree markers are checked; "absent from `origin/main`" is skipped, because present-here /
absent-upstream is a divergence to reconcile, not a stale sentence), and a HISTORY paragraph
(one carrying `SUPERSEDED`, "was true when", "measurement time", or a date+clock stamp) is
skipped, the same distinction `check_brief_drift.py` draws for an anchored count. Its
`--selftest` uses the incident's exact sentence, bold markup and all —

```
$ /usr/bin/python3 music/scripts/check_brief_absence.py --selftest
SELFTEST PASS check_brief_absence: stale-claims flagged=1 (want 1), history paragraph
  skipped=True, remote-object claim skipped=True, absent-path claim not flagged=True
```

— and the first version of the check FAILED that selftest, because it matched markers against
the raw line and the incident text is `is **not in this checkout**`, with the phrase split by
bold markers. That is recorded in the code, because a check that cannot catch its own incident
is the failure mode this lane treats as worse than no check.

**Repo-wide, the new check FAILs on three OTHER briefs** — the same stale class, other
owners' files, reported and not touched here:
`elemental-air/above-the-weather/brief.md:404` (it declares `music/assets/pack.py` missing
although the file exists), and `elemental-water.md:390` + `jungle-dnb.md:359` (both declare
`music/suno-gen.py` missing; it is present). Filed as a card for the brief owners.

`check_brief_figures.py` still FAILs on two *other* briefs (at the last run of this pass:
`chiptune-8bit.md:284` claimed 3 478 B vs 2 991 B; `elemental-water.md:600` claimed 53 lines vs
88) and `check_brief_line_refs.py` on two ranges in two other briefs (`chiptune-8bit.md`,
`elemental-fire.md`) — reported, not touched here. Those lists move as their owners edit their
briefs in this shared tree; this brief is clean on both.

### 14.4 Method note for the next verifier

Three of the corrections above were only findable by **re-reading the artifact, not the claim**
(`music/visuals/lyric_video.mp4` existed, `music/suno-gen.py` existed, the pod image was
`v0.1.3`), and two were **cross-repo** — the chart checkout under `/home/j_kro/mining-k8s` and
the live cluster are not "the worktree", so no repo-local check can see them. When a brief
makes a claim about the pod, the chart, or the board, measure it there (`kubectl -n mining`,
the chart checkout, the board DB) or anchor it to the revision and time you measured; a
present-tense claim about another repository ages exactly as fast as a divergence count.
Also: `git log --grep=<card>` can find a fix that is **not** in your branch — t_9546841b is
`done` and its fix is on a publish branch, so a "done" card is not the same as "fixed here".

## 15. Blueprint census corrected; the drift check now sees every shape this lane writes it in (card `t_c5a98379`, 2026-10-16)

`music/scripts/check_brief_drift.py` covered two of the ways this lane states the blueprint census.
Card `t_c5a98379` widened it to the rest and ran it across `music/briefs/**`. On the widened check
this brief FAILed once — §14's "re-measured and held" list, which still carried the 15:31 value.

- **Superseded revision of this file:** `sha256 12d1e1001c001cd2fb0876e590dd222ebc479f824e2c84232a000cd1550f88e5` (1070 lines / 73 389 B).
- **Corrected in place (§14's list):** "6 blueprints now" → **7 blueprints now (3 when
  this pass ran)**. Live at this pass (2026-10-16 17:18 CDT) `music/lyrics/blueprints/*.yaml` holds
  seven files — `activist`, `anime-ending`, `anime-opening`, `chill-lounge`,
  `epic-orchestral-boss`, `jungle-dnb`, `trance` — the 7 of the 14 genres §13 already states, and
  the 7 that leaves on the planner's flat-`100` fallback is what §6 records.
- **Not corrected here, deliberately:** the *deployed payload* counts. They describe `ConfigMap
  mining/music-pipeline-payload`, not this repo, and no repo-local check can recompute cluster
  state, so the widened check prints them as skips instead of guessing (six lines in this brief,
  in §8, §11, §13 and §14). Measured for the record at this pass, 2026-10-16 17:18 CDT: **42 keys,
  7 of them blueprints**, 15 prompt entries, 14 visuals — the payload has moved since the 15:31
  read (38 keys, 6 of them blueprints) and now matches the repo. The payload-census class is its
  own card, created by this pass.
- **The check's change:** four shapes it could not see — an emphasis-wrapped number, a census pair
  with no `genres` after it, the same pair split across two lines, and a brace list of the
  blueprints directory — plus a bare count of blueprints. The anchored rule, the fenced-quote rule
  and the two classes it already covered are unchanged. `--selftest` runs 23 cases: one per shape
  plus the escapes (anchored, fenced, quoted, cluster).
- **Regression proof, same card:** `--rev e40c7f9` FAILs with 20 stale counts, 8 of them in the
  new shapes across five briefs and none of them visible to the previous check; this worktree
  PASSes. Re-run both from the repo root; the drift pair itself is not quoted here, because a
  clone-divergence pair ages in minutes and §12's corrections already show the anchored form.
