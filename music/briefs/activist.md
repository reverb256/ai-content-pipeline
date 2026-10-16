# Brief — activist

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`; on this board the
> cards are assigned `music-producer` and claimed by the generic kanban dispatcher).
> **Card:** t_ace3bfb1 (`music-oracle: activist (score 7.25)`)
> **Duplicate card:** t_b7dd5655 (`music-oracle: activist (score 7.45)`) — same genre,
> same lanes, still `ready`. Both resolve to THIS brief; the brief is keyed by genre,
> not by card.
> **Written:** 2026-10-16T13:35-05:00 (CDT) — **verified in place 2026-10-16T13:54-05:00**
> by the duplicate card t_b7dd5655; every checkable figure re-measured (§12).
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `9ebf6af` when written — 15 behind / 7 ahead of
> `origin/main` at 13:35 (CDT); @ `fa3163f` when verified — 15 behind / 29 ahead at 13:54, and
> 15 behind / 32 ahead at 13:58. The shared tree is a moving target: re-measure it, do not
> copy this line (§11, §12).
> **Supersedes `sha256 a47b0f9bcdb5f937b5681b4c907456f28ef15bf524743359729e00f579a1026a`**
> (the blob committed in `a4ba657`). This pass edits the file in place and records the
> supersession here and in §12, as `music/scripts/check_brief_figures.py` requires.
> **Oracle:** 7.25/10 as filed — quota headroom 10.0, lane coverage 6.0, revenue 10.0,
> **cadence fit 1.7**, policy risk 10.0, trend signal 3.0. Threshold 5.0 → produce.
> **Live re-score today: 7.20** (§2; 6.70 without the trend term).

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

`cadence_fit_score()` is a pure function of today's date and the genre's cadence
(`oracle.py:221`): `expected_tracks = per_week × days_remaining/7`, then
`(expected-2)/6 × 10` clipped at 0. For 1/wk in a 31-day period that is:

| Date | days_remaining | expected (1/wk) | cadence_fit |
|---|---|---|---|
| 2026-10-09 (card filed, epoch 1791534472) | 21 | 3.00 | **1.667** → filed as 1.7 |
| 2026-10-16 (today, this run) | 14 | 2.00 | **0.000** |

So the card's 7.25 cannot be reproduced today: the same weights give **7.20** (re-measured
in §12: quota 10.0 + lane 6.0 + revenue 10.0 + cadence 0.0 + policy 10.0 = 6.70, plus
trend_signal 5.0 × 0.10), or **6.70** if the trend term is dropped. Both are above the 5.0
threshold → still produce. The conclusion holds: for a 1/wk genre cadence fit reaches
exactly 0.0 at the two-week remaining mark (`days_remaining` ≤ 14 → `expected` 2.0 →
`(2-2)/6` = 0) and stays there to month end.
**Do not read the oracle score as evidence about the genre** — for the low-cadence genres
it is mostly evidence about the calendar.

Also measured, so nobody re-derives it: `trend_signal` is neither a measured trend nor
reproducible run to run. `trend_signal_score()` (`oracle.py:272`) returns **3.0** on the
`count == 0` branch of a five-second DuckDuckGo HTML scrape and **5.0** on any exception.
This brief was written against 3.0 (the scrape answered with zero result snippets); this
verification pass measured **5.0** (the request raised). That 0.20 swing is 2 % of the
total, so the term is uninformative at weight 0.10 either way.

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
with rc=2 and report a gate failure that is really an argument error. Carded as
**t_d9983bb9** (`music-producer`, `ready`, 2026-10-16) — now named in §11, which the
earlier text promised but did not list.

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
-- title -- "What Runs Beneath"; verbatim in the chorus twice (its lines 1 and 3 are the
   same line). The outro repeats the phrase in lower case ("What runs beneath keeps
   running") — not the title line in title case; a later stage must not count that as one
-- concrete images -- kettle, gravel, aquifer, tap, letter, February, sample, company man,
   town clerk, minutes, hardware hall, forty folding chairs, boots, signatures, panel,
   deadline, hall lights, door   (all 18 present verbatim — §12 re-measured each one. The
   earlier "(23 distinct hits)" counted a wider candidate list this brief never printed;
   18 is the count this brief can reproduce)
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
live reads agree, §12: `music/planner/planner.py show --genre activist` prints
`"structure_source": "blueprint", "blueprint": true, "bpm_anchor": 96`;
`planner.context_for("activist")` returns `{genre, registry, template, blueprint}` with
`blueprint["bpm_anchor"] == 96` (a `dict`, not the flat keys `show` prints); and a live
`plan --lyrics-mode draft` writes `"bpm": 96` because `:470` reads
`ctx["blueprint"].get("bpm_anchor") or 100`. So this genre never takes the flat 100
fallback that the **seven blueprint-less genres** take (`load_blueprint()` returns `{}`
when `music/lyrics/blueprints/<genre>.yaml` is absent, and only 7 of the 14 genres have one — its own
docstring still quotes an old genre total). At 96 BPM, 4/4:

```
1 bar  = 4 × 60 / 96            = 2.500 s exactly
32 bars                          = 80.0 s
a 4-minute single (240 s)        = 96.0 bars exactly
```

Bar math is exact to the millisecond, so sync buyers can cut on bar lines. A default
3-minute plan (180 s) is 72 bars.

**Key is unclaimed.** The template names no key; the blueprint names none. The planner's
`--key` flag defaults to `None` (`music/planner/planner.py:533`) and the draft path writes
`args.key or "C minor"` (`:471`), so an unkeyed draft plan's key field reads **C minor**
(measured, §12 — not a planner default the flag itself carries). Decision: the render
picks, and whatever it picks is
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
a true `lyric_video.mp4` this genre can use. Carded as **t_ec378832** (`videobot`, `ready`,
2026-10-16), which carries both halves of this defect plus the YouTube-gate mismatch below
— now named in §11.

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
  (ComfyUI, not the studio service).
- **studio rail** — Deployment `sunolocal-source` (image `localhost/sunolocal:v0.1.2`,
  Service `sunolocal.mining:8123`, FastAPI `music.sunolocal.studio:app`); `studio.py`
  imports `suno_to_aceplan` from `translate.py`, so `translate.py` is this rail's
  translator. The 120 BPM default below belongs to THIS rail.

Against that route, three measured gaps:

1. **No lyrics mode fits a human sheet.** `music/planner/planner.py --lyrics-mode` accepts
   only `draft|ai` (`music/planner/planner.py:528`), and `plan` has no flag that loads a
   sheet at all (flags: `--brief --genre --lyrics-mode --language --title --key --duration
   --out --endpoint --model --temperature`). Re-measured end to end: `draft` rc=0 produces
   seven empty sections (bpm 96, key C minor), which `acestep_plan.py` then refuses with
   rc=1 `FATAL: 7 section(s) have no lyrics: ...`; and `ai` writes model lyrics that void
   the human authorship claim the whole copyright path rests on. Harder than either: the
   render payload (`ConfigMap mining/music-pipeline-payload`, mounted at `/payload`)
   carries `music/genres.yaml`, the six blueprints, `music/planner/planner.py`, the 14
   prompt templates and `music/scripts/acestep_plan.py` — and **no `music/lyrics/` at all**
   (and no `music/suno-gen.py`). The claimed sheet is not in the pod. This is a **third**
   case alongside the instrumental gap: not "no lyrics", not "AI lyrics", but "load the
   claimed sheet". Recorded on t_25a6499c, which is still `ready`, scoped to the
   instrumental cases; the human-sheet case is stated here.
2. **Tempo: the plan rail is right, the studio rail is not.** `acestep_plan.py:98-100`
   passes `plan["bpm"]`, `plan["key"]` and `plan["duration"]` verbatim into
   `RunningHub ACE-Step GenerationParams`, so the CronJob render rail honours 96. The
   fixed 120 is the studio rail's, in the sunolocal chart checkout
   (`/home/j_kro/mining-k8s/helm/charts/sunolocal/files/music/sunolocal/translate.py:42`):
   `bpm = 120`, and `:45` `bpm = int(60 + req.style_weight * 120)`. So a studio-service
   render is 1.25× too fast and every bar-aligned assumption in §6 is wrong for it.
   Acceptance for this genre stays: the plan's `bpm` field reads **96**, never 120 and
   never the 100 fallback.
3. **The key field.** Same file, `translate.py:49` `key = req.style or "C major"` — a
   studio request would put its 585-character caption (§6) where a key signature belongs.
   On the plan rail the value is `plan["key"]`, which for a draft is the unmeasured
   `"C minor"` (§6) — not the caption, but still not a key anyone selected.

(2) and (3) as they affect the studio rail are D1/D2 on t_25a6499c (open, nexus-core).
Brief list: the chart reads `briefs: []`
(`/home/j_kro/mining-k8s/helm/charts/music-pipeline/values.yaml:39`), while the live
ConfigMap `mining/music-pipeline-briefs` carries exactly one entry — chill-lounge,
`name: smoke-chill-lounge`, `lyricsMode: draft` — so Git and cluster differ, and **no
activist entry exists either way** (sibling cards exist for trance `t_791b48f7` and
anime-ending `t_a14e5d52`; commentary-beds is `t_640cc2a1`).

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
- Engine defects read from the chart checkout, not from memory (root
  `/home/j_kro/mining-k8s`): `helm/charts/sunolocal/files/music/sunolocal/translate.py`
  lines 42/45/49; `helm/charts/music-pipeline/values.yaml:39` (`briefs: []`). Live cluster
  reads (2026-10-16, `kubectl`): CronJobs `mining/music-pipeline` + `music-pipeline-render`,
  ConfigMaps `music-pipeline-briefs` (1 entry) + `music-pipeline-payload` (no
  `music/lyrics/`), Deployments `sunolocal-source` + `comfyui-zephyr`
- Rulings: `brain/RULINGS.md` read in full (the protest-lyric ruling at §Music, line 61,
  plus the panel mechanics); `brain/playbooks/music-lane-architecture.md` is still cited by
  the profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`, `autonomy.yaml`, every gate and
  `music/rubrics/vocal.json` (source `"arch"`). **The file existed nowhere on this machine
  at 13:35 when this brief was written and at 13:50 when this pass went looking — and it
  appeared, UNTRACKED, at 13:59:25 during the same pass: 21 696 B / 502 lines, beside an
  untracked `brain/research/music-monetization-2026.md` (11 067 B).** Neither is committed
  and neither is on `origin/main` (`git cat-file -e` → absent), so every committed citation
  of that path still dangles for anyone who clones; the authoring card **t_b0a4db92** must
  commit them. Until then do not treat either file as authoritative — an untracked
  working-tree file is not a citation target. (The doc embeds a registry snapshot, and at
  line 101 it carries the same `video_shape: lyric-video` whose artifact §7 shows is
  missing; it does not resolve that defect.)
- **Standing checks, run at verification (§12):**
  `music/scripts/check_brief_figures.py` → `--selftest` PASS, then 56 of 58 recomputed
  figures OK across 14 briefs (the 2 failures are commentary-beds, another genre, card
  t_e504b516); `check_prompt_style_counts.py` PASS (15 claims / 14 templates);
  `check_brief_paths.py` PASS 14 citations, with a WARN fixed here (this brief now names
  the `mining-k8s` root); `check_stage_scripts.py` FAIL — `music/suno-gen.py` is absent
  from this working tree while `origin/main` carries it, i.e. the known checkout
  divergence t_8a715681, not a wrong reference
- **Not fixed here (other owners, already carded):** diverged checkout t_8a715681; scheduler
  units on the wrong checkout t_41f354be; render-path D1/D2 + queue schema t_25a6499c;
  duplicate oracle cards t_bf0e5edd; missing architecture doc t_b0a4db92; `gate_loudness`
  ruler t_9546841b; profile workdir/kanban env t_75aacf8b; the sync-documentary gate lane
  **t_d9983bb9**; the `lyric-video` shape + YouTube-gate mismatch **t_ec378832**;
  commentary-beds "4133 B" unit labels t_e504b516
- **Duplicate card:** t_b7dd5655 (`music-oracle: activist (score 7.45)`) resolves to this
  brief; only one brief exists per genre. That card ran this verification pass (§12) and
  started no second brief and no stage chain.
- **hotspot:** `music/briefs/` — concurrent brief-stage workers write this directory and
  commit into one shared tree. At 13:54 verification: HEAD `fa3163f` read 15 behind / 29 ahead
  of `origin/main`; at 13:58 the same tree read 15 behind / 32 ahead, and at 13:35 it read
  7 ahead. The count is not a stable fact — re-measure it, never copy it. Board census at
  13:54: 4 running / 24 ready / 7 todo / 4 blocked / 57 done. `music/briefs/` also gained
  `check_brief_figures.py` (`fa3163f`, `cab0415`) and this pass's `check_brief_drift.py`
  after the brief was written — the check directory changes under the file it checks.

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
template, `lyric_video.mp4` does not); 6 blueprints now (3 when this pass ran); autonomy all `advisory`;
`campaigns/` nine campaigns and none for this genre; `~/Music` empty; no `music/generated/`;
`~/Music` and `find /home/j_kro -name suno-gen.py` both empty; the rubric's 3/3/2/2/1/1
weights at `pass_threshold` 7.0. **§8.1 reproduced exactly** by re-running
`origin/main:music/suno-gen.py` in a scratch mirror against this repo's data: 8 instrumental
/ 6 vocal genres (same two lists), `activist -> False`, `load_style_prompt` 585 chars,
`load_track` → title/1079 chars/39 lines/7 tags, `instrumental=True` refused with the same
`FATAL` string.

**Corrected (seven, plus one amendment after the first commit):**

1. Header/§2 — live re-score is **7.20**, not 7.00: `trend_signal` measured **5.0** (the
   exception branch) this run against **3.0** when the brief was written. Both values are
   live; the term is not reproducible, which is itself the finding.
2. Header/§11 — at `fa3163f` (13:54) the divergence was 15 behind / 29 ahead of `origin/main`.
   The brief had recorded 15/7 at `9ebf6af` (13:35), and the same tree read 15/32 at 13:58.
   A live count in a committed brief ages in minutes; `check_brief_drift.py` now exists for
   exactly this (§12, "Standing check added").
3. §6 — `--key`'s argparse default is `None`; `"C minor"` comes from the draft path
   (`planner.py:471`, `args.key or "C minor"`). Verified against a live draft plan.
4. §6 — `bpm_anchor: 96` as a flat pair of keys is `planner.py show`'s output;
   `context_for()` returns a `blueprint` dict, and the draft path reads
   `blueprint["bpm_anchor"] or 100` (`:470`).
5. §6 — **eleven** genres took the 100 fallback, not seven: 14 registered genres, 3
   blueprints at 13:54; six at 15:31, so **eight** genres take it. (`load_blueprint()`'s own docstring still quotes an old genre total.)
6. §5 — the concrete-image claim is **18 named terms, all present verbatim**; the earlier
   "(23 distinct hits)" cannot be reproduced from the list the brief prints. The title is
   verbatim in the chorus; the outro repeats it in lower case.
7. §8 — the render rail posts to **ComfyUI** (`COMFY_URL` =
   `comfyui-zephyr.mining.svc.cluster.local:8188`) and passes the plan's own bpm/key
   (`acestep_plan.py:98-100`), so the 120 BPM / caption-as-key defects belong to the
   **studio rail** (`sunolocal.mining:8123`, `translate.py`), not to the CronJob queue. The
   render payload mounts no `music/lyrics/`. The chart's `briefs: []` is still empty, but
   the live ConfigMap carries one chill-lounge entry — Git and cluster differ.

**Also true and left standing:** `music/suno-gen.py` is genuinely absent from this working
tree (`find /home/j_kro -name suno-gen.py` → zero hits) and genuinely present on
`origin/main` (last touched `ba28f55`, 2026-10-14). That is the divergence t_8a715681, not
a wrong citation: do not delete the reference, merge the refs.

**8. §11 amendment (§12) — the "missing" architecture doc appeared mid-pass.** `7e54e03`
recorded, correctly at measurement time, that
`brain/playbooks/music-lane-architecture.md` "does not exist anywhere on this machine". At
13:59:25 — between that commit and this amendment, in the same working tree — another worker
wrote it: 21 696 B / 502 lines, plus `brain/research/music-monetization-2026.md` (11 067 B).
Both are untracked and both are absent from `origin/main`, so the citation still dangles for
anyone who clones, and the corrected §11 now says exactly that. Same drift class as
corrections 1 and 2 — this time the artifact itself moved, not a count. It was caught only
because the pass re-read the tree after committing instead of trusting its own earlier read.

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
  music/briefs/activist.md:281  claimed "seven" blueprint-less genres  measured 11 ...
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
