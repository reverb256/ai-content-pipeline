# Brief — activist

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`; on this board the
> cards are assigned `music-producer` and claimed by the generic kanban dispatcher).
> **Card:** t_ace3bfb1 (`music-oracle: activist (score 7.25)`)
> **Duplicate card:** t_b7dd5655 (`music-oracle: activist (score 7.45)`) — same genre,
> same lanes, still `ready`. Both resolve to THIS brief; the brief is keyed by genre,
> not by card.
> **Written:** 2026-10-16T13:35-05:00 (CDT)
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `9ebf6af` (main; **15 commits behind
> `origin/main`, 7 ahead** — see §8. Six sibling brief-stage workers share this tree).
> **Oracle:** 7.25/10 as filed — quota headroom 10.0, lane coverage 6.0, revenue 10.0,
> **cadence fit 1.7**, policy risk 10.0, trend signal 3.0. Threshold 5.0 → produce.
> **Live re-score today: 7.00** (§2).

## 1. Genre resolution (live, not transcribed)

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

**Activist is one of only three genres with a lyric blueprint** — `music/lyrics/blueprints/`
holds exactly `activist.yaml`, `chill-lounge.yaml`, `trance.yaml`. So this genre does not
inherit the planner's flat `bpm = 100` fallback: the draft path reads the 96 anchor.

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

`cadence_fit_score()` is a pure function of today's date and the genre's cadence
(`oracle.py:221`): `expected_tracks = per_week × days_remaining/7`, then
`(expected-2)/6 × 10` clipped at 0. For 1/wk in a 31-day period that is:

| Date | days_remaining | expected (1/wk) | cadence_fit |
|---|---|---|---|
| 2026-10-09 (card filed, epoch 1791534472) | 21 | 3.00 | **1.667** → filed as 1.7 |
| 2026-10-16 (today, this run) | 14 | 2.00 | **0.000** |

So the card's 7.25 cannot be reproduced today: the same weights give **7.00** (6.7 +
trend_signal 3.0 × 0.10), or 6.7 if the trend term is dropped. Both are above the 5.0
threshold → still produce. The conclusion: for a 1/wk genre the score decays to exactly
0.0 for cadence fit at the two-week remaining mark and stays there to month end.
**Do not read the oracle score as evidence about the genre** — for the low-cadence genres
it is mostly evidence about the calendar.

Also measured, so nobody re-derives it: `trend_signal` 3.0 is the `count == 0` branch of
a five-second DuckDuckGo HTML scrape (`oracle.py:272`), not a measured trend. The
exception default is 5.0. Either way the term is uninformative at weight 0.10.

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
  - no clearance_doc.pdf (or .txt) — sync requires a clearance document
  - no ai_disclosure.txt — the AI role must be declared for sync platforms
rc=1

$ /usr/bin/python3 music/gates/gate_human_approval.py --package-dir <empty>
FAIL gate_human_approval
  - no approval.json — nothing has been approved. Publish approval is j_kro's decision
    (architecture §7, item 1).
  This gate cannot be satisfied by a bot: it needs a human approval record for THIS artifact.
rc=1
```

### DEFECT — the sync-documentary lane cannot invoke its own gate

`music/lanes.yaml:66` gives `sync-documentary` `gate: gate_sync_ready`, but the gate's
argparse rejects that lane name:

```
$ /usr/bin/python3 music/gates/gate_sync_ready.py --package-dir <empty> --lane sync-documentary
gate_sync_ready.py: error: argument --lane: invalid choice: 'sync-documentary'
  (choose from 'sync', 'direct-license', 'game-assets')
rc=2
```

`gate_sync_ready.py:47` is `LANES = ("sync", "direct-license", "game-assets")`. The
lane's `requires` list is byte-for-byte the `sync` set (`stems`, `metadata`,
`clearance_doc`, `instrumental_version`), so `--lane sync` runs the correct checks today
and the workaround is exact — but a stage that passes the lane name through will fail
with rc=2 and report a gate failure that is really an argument error. Carded (§11).

Decisions locked here so no later stage re-litigates them:

- **Two loudness targets, one master each.** Streaming wants −14 (rubric `loudness_target`
  anchors on −14), sync wants −16. Ship the −14 `master.wav` in the streaming package and
  the −16 cut as the sync package's `full_mix.wav`. Do not re-encode one file twice and
  call it two masters. `gate_loudness` measures ffmpeg `volumedetect` RMS, not gated LUFS
  — known ruler defect, card t_9546841b.
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
- **No YouTube lane at all.** Ad revenue is not the business here; §7 explains why the
  `lyric-video` shape still exists.

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
-- title -- "What Runs Beneath"; the title phrase appears verbatim in the chorus and in the outro
-- concrete images -- kettle, gravel, aquifer, tap, letter, February, sample, company man,
   town clerk, minutes, hardware hall, forty folding chairs, boots, signatures, panel,
   deadline, hall lights, door   (23 distinct hits)
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

Tempo, measured and locked: **96 BPM** (`blueprints/activist.yaml: bpm_anchor: 96`, and
confirmed to reach the planner — `planner.context_for("activist")` returns `blueprint: True`,
`bpm_anchor: 96`, so the draft path emits `bpm: 96`, not the flat 100 fallback that the
seven blueprint-less genres get). At 96 BPM, 4/4:

```
1 bar  = 4 × 60 / 96            = 2.500 s exactly
32 bars                          = 80.0 s
a 4-minute single (240 s)        = 96.0 bars exactly
```

Bar math is exact to the millisecond, so sync buyers can cut on bar lines. A default
3-minute plan (180 s) is 72 bars.

**Key is unclaimed.** The template names no key; the blueprint names none; the planner's
`--key` default is `"C minor"`. Decision: the render picks, and whatever it picks is
declared in the sync metadata and in `loop_points`/`clearance` provenance. Do not carry a
key field that was never measured — see D2 in §8, which currently hands the engine a
585-character paragraph where a key belongs.

One legitimate palette swap, per the template: hip-hop-format activist tracks change the
backing (boom-bap drums, spoken-word flow) but keep every lyric rule above.

## 7. Visual identity — locked style, missing shape

`music/visuals/documentary-grain.md` is the style and it is unambiguous: handheld 16 mm
truth, palette `#6b6257` dust / `#9c8f7a` skin-and-paper / `#232019` shadow with **one**
accent colour per video (the movement's colour, used sparingly); gate weave and occasional
focus hunt, because steadicam polish reads as an ad; grain 6–8 %; hand-lettered or
typewriter lyrics appearing **on** the phrase, never after it; the chorus swaps to a crowd
of hands writing the same line. No glossy kinetic-type effects. No clickbait thumbnail —
design for the documentary supervisor.

**DEFECT — the `lyric-video` shape has no artifact.** Measured: `music/visuals/` holds
shape templates for four of the five real shapes in the registry, and none for the fifth.
(The sixth registry value, `none`, means no visual at all — commentary-beds — and correctly
has no template.)

| video_shape | template | exists | genres |
|---|---|---|---|
| `album-30-60min` | `album_30_60min.mp4` | yes | chill-lounge, sentimental-piano, anime-ending |
| `mix-60min` | `mix_60min.mp4` | yes | trance, jungle-dnb |
| `loop-10min` | `loop_10min.mp4` | yes | the four elementals, chiptune-8bit |
| `single-4min` | `single_4min.mp4` | yes | epic-orchestral-boss, anime-opening |
| **`lyric-video`** | `lyric_video.mp4` | **no** | **activist (only)** |

The card that built the shapes (t_85db696a, videobot, done) defined shape 4 as
"`single-4min` — lyric video" and rendered exactly four shapes. `lyric-video` was never a
shape it produced. So activist's `video_shape` names a deliverable no renderer owns, and
nothing in the repo reads `video_shape` except `registry.py`'s validator — grep for
`video_shape` across `*.py`/`*.sh` returns only the registry. Two clean fixes, both cheap:
point activist at `single-4min` (the shape that *is* a lyric video), or have videobot render
a true `lyric_video.mp4` this genre can use. Carded (§11).

**Second consequence: no YouTube lane, but the visual stage runs the YouTube gate.**
`music/stages.yaml:74` unconditionally runs `gate_youtube_authentic` at the visual stage and
then advances to `human-approval`. Activist declares no YouTube lane, so that gate guards a
surface this genre never publishes to. The lyric video's real consumers are the direct-fan
post and the sync-documentary pitch. The stage machine's gate selection is not lane-aware —
same root cause as the `gate_sync_ready` lane defect in §3, carded together.

## 8. Generation path — measured on this host

### The vocal rail already accepts this track (best news in the brief)

`suno-gen.py` is **not in this checkout** — `find /home/j_kro -name 'suno-gen.py'` returns
zero hits — but it is on `origin/main` (`git cat-file -e origin/main:music/suno-gen.py` →
present, added by `ba28f55`). Read from the git object into a scratch mirror and executed
against this repo's data (no CDP, no browser, no GPU — these are pure file-I/O functions):

```
$ /usr/bin/python3 probe_vocal_rail.py
-- is_instrumental_template() for every registered genre (origin code) --
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
-- gate_quota (origin code) --  PASS gate_quota; used=0 period=2026-10
```

So activist is the **first genre in this lane whose generate stage can run end-to-end
against its own artifact**: the rail detects it as vocal (correctly), finds the human sheet,
verifies the `provenance: human-original` header, and refuses the instrumental shortcut.
The 39-line sheet yields 7 section tags for the renderer. Nothing in the vocal path needs
building — only unblocking (§ t_8a715681, the diverged checkout).

### The live queue path still cannot carry this track

The in-cluster route is ConfigMap `music-pipeline-briefs` → CronJob `music-pipeline`
(`planner.py` → `/var/lib/music-plans/<name>.json`) → CronJob `music-pipeline-render`
(`acestep_plan.py` → sunolocal studio API). Against that route, three measured gaps:

1. **No lyrics mode fits a human sheet.** `planner.py --lyrics-mode` accepts only
   `draft|ai` (`planner.py:528`). For activist `draft` emits a scaffold that
   `acestep_plan.py` refuses (exit 1), and `ai` writes model lyrics that void the human
   authorship claim the whole copyright path rests on — the sheet at
   `music/lyrics/activist/what-runs-beneath/lyrics.suno.txt` cannot be loaded by this
   queue at all. This is a **third** case alongside the instrumental gap: not "no lyrics",
   not "AI lyrics", but "load the claimed sheet". Recorded on t_25a6499c, which is still
   `ready`, scoped to the instrumental cases; the human-sheet case is stated here.
2. **Tempo is fixed at 120 in the deployed translator.** Measured in the chart checkout
   (`mining-k8s/helm/charts/sunolocal/files/music/sunolocal/translate.py:42`):
   `bpm = 120`, and `:45` `bpm = int(60 + req.style_weight * 120)`. Activist anchors
   **96**, so a queue render is 1.25× too fast and every bar-aligned assumption in §6 is
   wrong. Acceptance for this genre: the plan's `bpm` field reads **96**, never 120 and
   never the 100 fallback.
3. **The key field receives the entire caption.** `translate.py:49`
   `key = req.style or "C major"`, and `acestep_plan.py` passes `plan["key"]` straight into
   the ACE node as `keyscale`. For activist `req.style` is the 585-character caption
   measured in §6 — a paragraph where a key signature belongs.

Both (2) and (3) are D1/D2 on t_25a6499c (open, nexus-core). The queue's own brief list is
empty — `mining-k8s/helm/charts/music-pipeline/values.yaml:39` reads `briefs: []`
(measured), and no activist entry has been requested against it (sibling cards exist for
trance `t_791b48f7` and anime-ending `t_a14e5d52`; commentary-beds is `t_640cc2a1`).

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
  holds nine campaigns, none for this genre). `~/Music` is empty. `music/generated/` does
  not exist. The first render is genuine work, not a re-run.
- Quota untouched:

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
(lyric video — blocked on the missing shape, §7) → `human-approval` (j_kro) → `publish`
(private/draft only; Patreon/Ko-fi posts are `socialbot`'s, and no bot may approve its own
publish).

## 11. Provenance

- Registry and template: `music/genres.yaml`, `music/lanes.yaml`, `music/prompts/activist.md`,
  `music/visuals/documentary-grain.md` — all resolved live; `registry.py validate` → 14
  genres / 10 lanes, rc=0
- Blueprint: `music/lyrics/blueprints/activist.yaml` read through `planner.context_for()`
  (`blueprint: True`, `bpm_anchor: 96`)
- Gates exercised live: `gate_quota` PASS; `gate_lyrics_original` PASS (plain + `--strict`);
  `gate_sync_ready` FAIL rc=1 (`--lane sync`) and **rc=2 for `--lane sync-documentary`**;
  `gate_release_ready` FAIL rc=1; `gate_human_approval` FAIL rc=1
- Oracle: `music/oracle.py` imported and every component recomputed on this host for
  §2 (`WEIGHTS`, `REVENUE_BANDS`, `BANNED_SURFACES` read from source at lines 54/64/81)
- Vocal rail: `origin/main:music/suno-gen.py` (1025 lines) read from the git object and
  executed in a scratch mirror (`probe_vocal_rail.py`); `is_instrumental_template`,
  `load_track`, `load_style_prompt`, `gate_quota` all exercised
- Engine defects read from the chart checkout, not from memory:
  `mining-k8s/helm/charts/sunolocal/files/music/sunolocal/translate.py` lines 42/49;
  `mining-k8s/helm/charts/music-pipeline/values.yaml:39` (`briefs: []`)
- Rulings: `brain/RULINGS.md` read in full (the protest-lyric ruling at §Music, line 61,
  plus the panel mechanics); `brain/playbooks/music-lane-architecture.md` is still cited by
  the profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`, `autonomy.yaml` and every gate,
  and still does not exist anywhere on this machine — the same dangling reference the
  sibling briefs record (card t_b0a4db92)
- **Not fixed here (other owners, already carded):** diverged checkout t_8a715681; scheduler
  units on the wrong checkout t_41f354be; render-path D1/D2 + queue schema t_25a6499c;
  duplicate oracle cards t_bf0e5edd; missing architecture doc t_b0a4db92; `gate_loudness`
  ruler t_9546841b; profile workdir/kanban env t_75aacf8b
- **Duplicate card:** t_b7dd5655 (`music-oracle: activist (score 7.45)`, `ready`) resolves to
  this brief; only one brief exists per genre.
- **hotspot:** `music/briefs/` — six concurrent brief-stage workers write this directory and
  commit into one working tree; HEAD moved twice while this brief was written and the
  checkout is 15 behind / 7 ahead of `origin/main`. `music/stages.yaml` and `music/oracle.py`
  were edited in this same tree minutes before this run.
