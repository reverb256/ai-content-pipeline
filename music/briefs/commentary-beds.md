# Brief — commentary-beds

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`) — DELIVERED; the chain
> resumes at `genre-select` (already resolved in §1–§3).
> **Card:** t_b976f49f (`music-oracle: commentary-beds (score 8.3)`) — the surviving OPEN card
> for this genre. The board check reports `commentary-beds → t_b976f49f [running]` and one open
> card per genre, rc=0 (`music/scripts/check_oracle_board.py`, re-run in this pass).
> **Superseded cards:** t_47491ec0 (score 8.1, done) wrote this brief; t_4187b092 (score 8.3,
> done) was its duplicate, created by the second oracle run ten minutes later. Briefs in this
> lane are keyed by **genre**, not by card, so all three cards resolve to this one file.
> **Verified (unit-correction pass, `t_e504b516`):** 2026-10-16T15:22-05:00 (CDT) — §1 registry
> table and §10 provenance. Both cited the prompt template's size with the unit `B`, but the
> value they gave was that file's CHARACTER count, so the label understated the byte count.
> Both labels are corrected in place; no other figure in this brief was touched. The 13:20
> revision of this file is
> `sha256 d6fbd52f800199fe501a41556835e0b582dfd82f458a4c4c4c9a8bab9139b590` (commit `9ebf6af`);
> that pass supersedes it.
> **Written:** 2026-10-16T13:20-05:00 (CDT)
> **Verification pass:** 2026-10-16T15:50-05:00 (CDT), card t_b976f49f — every checkable claim
> below re-measured live against the worktree and the running pipeline. §12 records the oracle
> ruling, the corrections and what changed after the brief stage.
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `4b1ba88` (main; the working tree is shared by
> 6–7 concurrent music workers and HEAD moved many times while this brief was written).
> **Oracle:** **true score 8.1/10** — oracle dedupe ruling 2026-10-16 (`music/oracle.py` @
> `b2d11f7`): quota headroom 10.0, **lane coverage 4.0**, revenue potential 10.0, cadence fit
> 10.0, policy risk 10.0, trend signal 3.0. Threshold 5.0 → produce. The card titles' 8.3 and
> 8.1 are the two halves of the 2026-10-09 double emission; §12.1 shows which numbers are
> reachable from the fixed scorer.
> **Revision:** the superseded blob was
> `7db8ea568da53bd1983bb53737680223dc72d4f862421900e299c481aeea1398` (commit `63440da`); the
> current digest is re-readable with `sha256sum music/briefs/commentary-beds.md`.

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

That transcript is the live output of this pass (2026-10-16T15:50 CDT). It gained one line and
one clause since the brief stage wrote it: the board now declares a stage gate rule for the
`visual` stage, and the header count reads `1 stage gate rule(s)`. The rule reads *a genre with a
YouTube lane gets `gate_youtube_authentic`; where the lane is absent the answer is `none`* —
which is this genre's case (§3, last bullet): `commentary-beds` has no YouTube lane.

**Interpreter trap, measured.** Plain `python3 music/registry.py validate` fails in a
worker shell with `ModuleNotFoundError: No module named 'yaml'`: `python3` here resolves to
`~/.hermes/tools/python-3.14.7+…/bin/python3`. `/usr/bin/python3` (3.14.7) has PyYAML and
validates cleanly. The systemd music units run `/usr/bin/python3`, so the units are
unaffected — but any stage prompt that says `python3 music/…` inherits the trap.

| Field | Value |
|---|---|
| Genre | `commentary-beds` |
| Family | `utility` |
| Prompt template | `music/prompts/commentary-beds.md` (4159 B, resolves) |
| Visual style | `music/visuals/none.md` (resolves; the file exists to say **no visual**) |
| Lanes | `direct-license`, `sync` — two lanes only |
| Cadence | 5/wk |
| Video shape | `none` — no YouTube lane, no MP4, no thumbnail |
| Registry note | "Loopable + stemmed. Market: 82% of podcasts license stock themes." |

`lane_coverage` 4.0 is the lowest score in the registry: every other genre opens 3–4 lanes.
The genre is therefore only viable as a **kit product** — the value is the stemmed,
loopable pack sold direct and licensed for sync, not streams.

## 2. Intent — the product is a KIT, not a track

One motif generates a whole kit, and the kit is what the buyer licences:

| Kit element | Spec (from the prompt template) |
|---|---|
| Intro sting | 8 bars = **16.0 s** at 120 BPM; ends on a clean decisive hit, then one beat of silence, **no fade-out** |
| Loopable talk bed | 16 bars = **32.0 s**; chords + root bass + rimshot ticks on 2 and 4; no melody |
| Stings / outro | derived from the same motif (outro = its answering phrase, clipped short, hard stop) |
| Cutdowns | 15/30/60 s of the sting — see the off-grid finding in §4 |
| Stems | mandatory (both lanes require them) |
| Cover | 3000×3000 PNG, palette by show flavour |

Three things must hold or the generation is **out of spec** (the template says reject it):

1. **The motif is the show's audio brand** — 4–6 notes, stated exactly twice. One statement
   is not memorable; three is annoying.
2. **The bed is anti-melody.** The ear follows a tune over a voice. Every musical event in a
   bed fights the speaker. "No fills, no builds, no surprises" is the job description.
3. **Mono compatibility is non-negotiable.** A large share of podcast listening is a single
   phone speaker; wide-stereo stings collapse into phase soup there.

Flavours by show type (the same kit, re-voiced): warm lo-fi jazz (interview), bright indie
electronic (tech news), tense pulsing minimal (true crime).

## 3. Target lanes and what each one demands

From `music/lanes.yaml`. These are the gates that will actually run.

| Lane | Surface | Gate | Required artifacts |
|---|---|---|---|
| `sync` | songtradr, audiosparx | `gate_sync_ready` | `stems`, `metadata`, `clearance_doc`, `instrumental_version` |
| `direct-license` | own-site | `gate_sync_ready` | `stems`, `license_tiers` |

`gate_sync_ready` executes the artifact — nothing is trusted from a filename. Measured live
against an empty package directory (this is the requirement list the package stage must
satisfy):

```
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
```

Re-measured in this pass. The requirement list is longer than the brief stage recorded: the gate
now also demands a `manifest.json` `metadata` object carrying `title`, `artist`, `bpm`, `key`,
`mood` and `genre` — one finding each. `--lane direct-license` returns the same list plus a
fifteenth finding, `direct-license lane requires license_tiers`, so the `license_tiers` bullet
below is enforced by the gate itself, not only by this brief.

Decisions locked here so no later stage re-litigates them:

- **`instrumental.wav` must be a real, distinct render.** The gate fails an instrumental
  that is byte-identical to `full_mix.wav`. Every commentary bed is already instrumental, so
  the pack cannot copy the master — ship the bed-only/alternate mix as the instrumental
  version and state which variation it is in the manifest.
- **Stems: ≥ 4 files, each within ±0.5 s of the master duration** (ffprobe-measured, not
  file size). Suno Studio export, never the standard download button.
- **`clearance_doc.pdf` must be a real PDF** (`%PDF-` header is parsed). A placeholder fails.
- **`license_tiers.*` must exist for the direct-license lane.** Nothing defines the tiers
  yet; that is genuine work for the package stage.
- **Loop verification is self-imposed.** `loop_points.json` + `gate_loop_points` are listed
  as `game-assets` requirements, and this genre is not in that lane — but the kit is *sold*
  as loopable, so the bed ships with `loop_points.json` and passes `gate_loop_points`
  (junction/body curvature ratio ≤ 3.0×, loop span ≥ 2 s). A beautiful non-loopable bed is
  inventory, not product (`music/rubrics/utility.json`).
- **Autonomy rung is `advisory` for both lanes** (`music/autonomy.yaml`): every publish is
  proposed with evidence and approved by j_kro. Promotion needs 10 clean advisory publishes.
- **No YouTube surface** → `gate_youtube_authentic`, thumbnails and the visual stage do not
  apply to this genre at all.

## 4. Rhythm math and throughput (derived, not assumed)

At the genre's 120 BPM, 4/4, one bar is **exactly 2.00 s**. Measured:

```
bar = 2.00 s   8 bars = 16.0 s (intro sting)   16 bars = 32.0 s (talk bed)
15 s = 7.50 bars   30 s = 15.00 bars   60 s = 30.00 bars
```

**Finding — the 15 s cutdown is off-grid.** The template says "every bar = exactly 2 seconds …
editors cut on those marks" and asks for 15/30/60 s cutdowns. 30 s and 60 s land on whole
bars (15 and 30); **15 s is 7.5 bars**, i.e. it cuts on beat 3 of a bar. Decision: ship the
short cutdown as **16 s (8 bars)** and label it as such, or make it 15 s and accept a cut
mid-bar in the deliverable README. Do not silently ship a 15 s file and call the kit
bar-aligned.

Throughput: cadence 5/wk. The sting and the bed are **two separate generations — never one**
(the template is explicit: a generation asked for both grows melodies into the bed). So the
lane needs **10 generations/week**, each with its own stems and cutdowns. This is the number
that makes the kit viable as a repeatable product — and it is why the instrumental path
matters: no human lyric sheet gates the loop (§7).

Export policy: exports go through Suno Studio (unlimited). Run `gate_quota` before every
export; the standard-download meter is 0/60 today (measured). Note the two meters are
separate: Suno's Download dialog meters *download credits* (1/song, format-independent,
66→64 observed on 2026-10-16), while `music/quota-ledger.json` tracks the 60/month standard
counter and Studio exports. Record both in the ledger when exporting.

## 5. Audio identity (locked for this genre)

Style field — INTRO STING (420/1000 chars, measured):

```
short podcast intro theme, 120 BPM, instrumental, warm lo-fi jazz palette, one memorable
4-6 note bell-pluck motif stated twice over electric piano chords, punchy but soft kick and
rimshot, quick 8-bar build, tight modern podcast production, mono-compatible mix for phone
speakers, ends with a clean decisive hit then one beat of silence, no fade-out, no long
reverb tails, bright enough to read on earbuds at low volume
```

Style field — LOOPABLE TALK BED (422/1000 chars, measured):

```
minimal instrumental podcast talk bed, 120 BPM, same warm lo-fi jazz palette, muted chords
and soft bass on the loop's chord roots, NO melody, no lead instrument, sparse rimshot ticks
on the 2 and 4, extremely repetitive on purpose, low dynamic range, seamless loop-friendly
phrasing, sits quietly under a speaking voice, no drum fills, no builds, no surprises,
midrange leaves the vocal frequencies clear, mono-compatible
```

Settings: **Weirdness 25 % (sting) / 20 % (bed)**; **Style Influence 85 % (sting) / 90 %
(bed)**. Exclude Styles — bed: `lead melody, vocal samples, fills, drum solos, builds, EDM
drops, big dynamics`; sting: `long reverb tails, fade-outs, vocals, EDM`.

Lyrics: **empty box, always** — that is Suno's instrumental path. Structure comes from
metatags only (`[Intro]`, `[Instrumental]`, `[Outro]` + parenthetical direction, never
singable words).

## 6. Visual — none

`music/visuals/none.md` is explicit: this genre ships as audio + stems + licence. No MP4, no
platform-native video, no thumbnail. The only visual artifact is the flat 3000×3000 kit
cover (podcast name, the motif rendered as a simple mark, palette by flavour: amber/teal for
warm lo-fi jazz, blue/white for tech news, red/black for true crime). Cover art is metadata,
not content.

Because `video_shape: none`, the pipeline's `visual` stage must be **skipped** for this
genre rather than dispatched to videobot (see §9).

## 7. Generation path — measured on this host

**The file the lane's own generate prompt names is in this checkout now.** `music/suno-gen.py`
is on disk (42652 B, mtime 2026-10-16T14:23) and its history is `origin/main`'s (`295fc49`,
`ba28f55`). The divergence the brief stage recorded is closed, measured in this pass:
`git rev-list --count HEAD..origin/main` = **0** (it read 15 when the brief was written) and
`git rev-list --count origin/main..HEAD` = **66** at 15:52 CDT (the tree is shared by concurrent
workers, so the ahead count moves). Read live from the working tree:

- `music/suno-gen.py:141 is_instrumental_template(genre)` — the decision that lets the rail
  accept a track with no human lyric sheet. Its own docstring names the 8 instrumental
  templates: **chill-lounge, sentimental-piano, commentary-beds, elemental-fire/water/earth/air,
  chiptune-8bit, epic-orchestral-boss**, and it keys on the template's `## Lyrics guidance`
  section. `music/prompts/commentary-beds.md` says "Leave the **lyrics box empty**" — so this
  genre is detected as instrumental and needs **no lyric sheet**. That is the whole reason a
  5/wk kit cadence can close.
- `music/sunolocal/**` — the local Suno-shaped service (ACE-Step + YuE2 adapters); the live
  render engine is the in-cluster `sunolocal` deployment (`localhost/sunolocal:v0.1.3`, engine
  `ace`).

**The two render gaps the brief stage recorded are CLOSED** (card `t_25a6499c`: `mining-k8s`
`a80ab4e` + this repo `52ae620`, engine `localhost/sunolocal:v0.1.3`):

1. **Instrumental tracks are expressible in the planner queue now.** The schema gained
   `lyricsMode: instrumental` (or the boolean `instrumental: true` — either spelling, same
   effect) and `planner.py --lyrics-mode` accepts it. An instrumental plan declares itself with
   its own `instrumental: true` field. Measured on this genre's own plan (§8):
   `"instrumental": true`, `"_meta": {"lyrics_mode": "instrumental"}`, no `.refused` marker.
   `draft` is still refused on purpose; it is not a workaround for this genre.
2. **Tempo travels with the queue entry.** `bpm` and `keyscale` are optional entry fields,
   passed to the planner as `--bpm`/`--keyscale` and carried to the engine, so the 100-fallback
   for a genre with no blueprint does not apply once the entry states the tempo. Measured on
   this genre's own plan: `"bpm": 120`, `"key": "C minor"`, `"_meta": {"blueprint": false}` —
   **the acceptance is met: the plan reads 120, not 100.** At 100 BPM a bar would be 2.40 s and
   every bar-aligned cutdown in the kit would be wrong. The deployed engine used to hardcode
   `bpm = 120`; nothing in this brief now depends on that hardcode, because the tempo travels
   with the entry — and the rendered durations confirm the tempo was honoured: 16.000000 s and
   32.000000 s are exactly 8 and 16 bars at 2.00 s (§8).

**Two rail walls found while this kit rendered** (card `t_640cc2a1` — cited so the stages after
this one do not rediscover them):

1. **The planner's floor refused the 16 s sting.** `music/planner/planner.py:103`
   `MIN_DURATION_S = 30` (ceiling `MAX_DURATION_S = 600`), so the sting plans with
   `VALIDATION FAILED (1): duration 16s outside 30-600s` and that pod exits 1. The engine has no
   such floor: the 16 s render completed and measures 16.000000 s (§8). Carded `t_96dfc521`. The
   entry keeps its spec length — do not raise the sting to 30 s to dodge the planner.
   **FIXED by card `t_96dfc521`**: the floor is 16 s now — the shortest shape the registry
   actually names — and a duration outside the rail writes no plan at all, so the render rail
   cannot read one (see `music/tests/test_planner.py` §6).
2. **The planner used to read the FIRST style field; this template carries two.**
   `music/planner/planner.py:169` (`parse_style_fields`) parses EVERY `## Style field` block and
   `music/planner/planner.py:188` (`resolve_style_caption`) resolves the one the QUEUE ENTRY
   names — there is no fallback to the first block. `music/prompts/commentary-beds.md` still
   declares INTRO STING (line 7) before LOOPABLE TALK BED (line 13), and before the fix BOTH
   kit plans carried the sting caption, byte-identical. **FIXED by card `t_3497b627`** (fix +
   re-plan): re-measured 2026-10-16 by card `t_6dd13d76`, the two plans on disk now carry
   DIFFERENT captions — `caption` 420 characters for the sting plan, 422 for the bed plan — so
   the sting's caption is no longer the bed's. The 32 s artifact on disk is still the sting at
   32 s, not the anti-melody bed §2 defines: re-render before shipping it as the talk bed.

Live route into audio (in-cluster, not the kanban stage machine): ConfigMap
`music-pipeline-briefs` → CronJob `music-pipeline` (plans via `planner.py` →
`/var/lib/music-plans/<name>.json`) → CronJob `music-pipeline-render` (`acestep_plan.py` →
sunolocal studio API). Chart: `/home/j_kro/mining-k8s/helm/charts/music-pipeline/`; its payload
carries `music/prompts/**` (including `commentary-beds.md`), `music/genres.yaml`, `planner.py`,
`acestep_plan.py` and `lyrics/blueprints/`.

**This genre's kit is already on that route.** Measured in this pass from the live ConfigMap
(`kubectl -n mining get cm music-pipeline-briefs -o jsonpath='{.data.briefs\.json}'`): the
`briefs` list holds **11 entries**, two of them this genre's, and the two are the pair §2
specifies:

| name | duration | bpm | keyscale | lyricsMode |
|---|---|---|---|---|
| `commentary-beds-lo-fi-jazz-sting` | 16 | 120 | C minor | instrumental |
| `commentary-beds-lo-fi-jazz-bed` | 32 | 120 | C minor | instrumental |

Both plans are written to `/var/lib/music-plans/` and each carries a 0-byte `.rendered` marker
with no `.refused` marker. The list no longer reads `[]`; card `t_640cc2a1` (`mining-k8s`
`fb03105`) filled this genre's half of it.

## 8. Existing assets for this genre

**In `music/`: no sheet and no blueprint of this genre's own — unchanged.** `music/lyrics/` holds
`activist/`, `anime-opening/`, `chill-lounge/`, `trance/` and a `blueprints/` directory whose
files are listed in §11 — no commentary-beds sheet or blueprint (expected: the genre is
instrumental, so there is no lyric sheet to write, and §7 shows the tempo no longer needs a
blueprint). No campaign directory, no masters, no stems, no cover, nothing published.

**The kit has been rendered, though.** The generate stage's first pass ran through the live
in-cluster route (card `t_640cc2a1`, entries in §7). Measured in this pass with `ffprobe` 9.0.1
against the engine's artifacts directly, not transcribed from the card's report:

| Entry | engine job id | artifact | duration | sha256 |
|---|---|---|---|---|
| `commentary-beds-lo-fi-jazz-sting` | `c27fc133641540259517cb235af10207` | `/var/lib/sunolocal/artifacts/suno-c27fc133641540259517cb235af10207.flac` | **16.000000 s** | `bf8ca7f419d3ea1acef87b3e84366d1556c1de1781a75993047027317401acdd` |
| `commentary-beds-lo-fi-jazz-bed` | `0e3fb7b2728747ce816c3e6a760c3c69` | `/var/lib/sunolocal/artifacts/suno-0e3fb7b2728747ce816c3e6a760c3c69.flac` | **32.000000 s** | `082c9c79b6764490ccfdb674bcc5d0ab5366b2429067576038508dcf8e1d0f0b` |

Both are 48 kHz stereo FLAC and both land exactly on §4's bar math (8 bars and 16 bars at
2.00 s). The 32 s artifact is **not** the talk bed, though: it carries the sting caption and
needs the re-render `t_3497b627` owns (§7). Nothing here is a published asset — both lanes are
rung `advisory` and publish is a j_kro gate.

Quota is untouched:

```
$ /usr/bin/python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

A local ACE render consumes no Suno quota — it is neither a download nor a Studio export — so
the counters stay at 0.

## 9. Stage plan for this genre (skips locked)

`brief` ✓ → `genre-select` → **`lyrics` SKIPPED** (instrumental: the template's empty-box
statement is the spec; `is_instrumental_template` keys on it) → `generate` (quota gate first;
**two** generations per kit — sting and bed separately; this genre's first pass already ran
through the live in-cluster route — §7, §8) → `curate` (pick the winning sting and
bed per flavour; record a reject reason per loser) → `stems` (≥ 4, ±0.5 s, plus the distinct
instrumental) → `master` (sync target −16 LUFS ±1; note `gate_loudness` measures ffmpeg
`volumedetect` RMS, not gated LUFS — known ruler defect, card t_9546841b) → `gate`
(independent review against `music/rubrics/utility.json`: 5 weighted criteria, pass
threshold 7.0 on the geometric-median panel aggregate; `voice_headroom` and `seamless_loop`
carry weight 3 each) → `package` (`gate_sync_ready` per lane, `loop_points.json`,
`license_tiers`, clearance PDF) → **`visual` SKIPPED** (`video_shape: none`; cover art only)
→ `human-approval` (j_kro) → `publish` (private/draft only).

## 10. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` — validated live (14 genres, 10 lanes)
- Template: `music/prompts/commentary-beds.md` (4159 B / 4133 chars; style fields measured 420 / 422 chars)
- Visual: `music/visuals/none.md` ("THIS FILE EXISTS TO SAY 'NO VISUAL'")
- Gates: `music/gates/` — `gate_quota` PASS live; `gate_sync_ready` exercised live (FAIL
  output quoted, requirement list above); `gate_loop_points`, `gate_stems_present`,
  `gate_loudness`, `gate_quality` present
- Rubric: `music/rubrics/utility.json` (family `utility`, genres `["commentary-beds"]`)
- Autonomy: `music/autonomy.yaml` (both lanes `advisory`)
- Stage contract: `music/stages.yaml` (`brief` → `producer`; advance calls added in `9c2d2d3`)
- Generation-path truth read from the working tree in this pass: `music/suno-gen.py`
  (`is_instrumental_template`, 42652 B) and the live plans in `/var/lib/music-plans/`
  (`"bpm": 120`, `"key": "C minor"`, `"instrumental": true`)
- **Dangling reference — corrected in this pass.** Both documents exist on this machine and are
  tracked in `HEAD`: `brain/playbooks/music-lane-architecture.md` (mtime
  2026-10-16T15:31) and `brain/research/music-monetization-2026.md` (11067 B, mtime
  2026-10-16T13:59). `find /home/j_kro -name 'music-lane-architecture.md'` now returns that
  path. Both are still **absent from `origin/main`** (`git cat-file -e
  origin/main:brain/playbooks/music-lane-architecture.md` → "exists on disk, but not in
  'origin/main'"), so a fresh clone still dangles: the local-citation problem is closed, the
  upstream one is not. Carded: t_b0a4db92 (coo).
- **Resolved since the brief stage:** the checkout divergence (t_8a715681) — measured
  `HEAD..origin/main` = 0 in this pass; the instrumental + in-genre render gaps (t_25a6499c);
  the missing architecture docs (t_b0a4db92) now exist on disk (see above).
- **Still open (other owners, already carded):** the scheduler units running the wrong checkout
  t_41f354be; re-emitted oracle cards carrying `stage: brief` for genres whose brief is on disk
  t_6599927d; the planner's 30 s floor t_96dfc521 and the first-style-field caption bug
  t_3497b627; the 28-oracle-cards-for-14-genres class t_bf0e5edd; profile workdir + kanban env
  vars t_75aacf8b.
- **hotspot:** `music/briefs/` — six concurrent workers write this directory and commit to one
  working tree (`4daf132`, `9c2d2d3`, `132a781`, `4bb1ea6`, `ade6e87` landed inside 15
  minutes). `music/stages.yaml`, `music/oracle.py` and `scripts/automation/*` are also being
  edited in the same tree while this brief runs.

## 11. Aged live counts re-measured (card `t_0f7aed63`, 2026-10-16)

`music/scripts/check_brief_drift.py` (added by card `t_b7dd5655`) flagged this brief's blueprint
census as stale. Re-measured and corrected in place. The §1 and §10 unit labels corrected by card
`t_e504b516` are untouched.

- **Superseded revision of this file:** `sha256 293c7cfe781d6f90c46357e39121a83fc739724148fa581e5b09cac4b3254aac` (307 lines / 18366 B).
- **Blueprint census, re-measured 2026-10-16 15:52 CDT:** 7 of the 14 genres carry a lyric
  blueprint (`activist`, `anime-ending`, `anime-opening`, `chill-lounge`, `epic-orchestral-boss`,
  `jungle-dnb`, `trance`); the other 7 do not. `commentary-beds` has none, and the 100-fallback
  blocker this census once implied is gone: the queue entry states `bpm: 120` itself, so the
  plan reads 120 with `"_meta": {"blueprint": false}` (§7.2). The original measurement of this
  bullet, 15:31 CDT, read 6 and was correct then — `jungle-dnb.yaml` (7331 B) landed at 15:49
  under card `t_e6d422ec`, so this count is a moving number. The class is carded `t_c5a98379`.
- **Corrected in place:** §7 (the census sentence) and §8 (the `music/lyrics/` listing).

## 12. Surviving-card pass (card `t_b976f49f`, 2026-10-16T15:50 CDT)

Disposition: this card is the **surviving open card** for the genre, and the brief stage's
artifact already exists. Briefs in this lane are keyed by **genre**, so all three
commentary-beds cards resolve to this one file: no second brief was written, no second chain
started. Verified live — `music/scripts/check_oracle_board.py` reports
`commentary-beds → t_b976f49f [running]`, 12 open cards across 12 genres, one open card each,
rc=0.

### 12.1 Oracle ruling — true score 8.1, the title's 8.3 is not the live number

Recomputed with the repo's own scorer (`music/oracle.py` imported as a module; `score_genre`
called directly; `WEIGHTS` closes at 1.0):

```
quota_headroom     10.0  (w 0.25)      lane_coverage   4.0  (w 0.20)
revenue_potential  10.0  (w 0.20)      cadence_fit    10.0  (w 0.15)
policy_risk        10.0  (w 0.10)      trend_signal    3.0  (w 0.10)
TOTAL 8.1
```

Every total this genre can reach by trend-fetch outcome: **8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7,
8.8** (trend signal 3.0 → 10.0 in tenth-point steps). The title's **8.3 is reachable only at
trend_signal 5.0** — the premium the pre-`b2d11f7` `except` branch paid to a FAILED fetch. Fixed
in `b2d11f7`: a failed fetch and a working fetch with no results both score the no-signal floor
3.0, so the live number is 8.1.
`music/scripts/check_oracle_determinism.py` PASS rc=0. The ruling corrects the number, not the
decision — threshold 5.0 → produce either way.

### 12.2 Corrected in place in this pass

1. **Header** — named this card as the surviving card, recorded both superseded cards, the 8.1
   ruling and the superseded blob digest. Before this pass the header named the superseded
   writer card as `**Card:**` and never recorded that the chain had moved past `brief`.
2. **§1** — the registry transcript was one clause and one line short of live: it read
   `registry OK: 14 genres, 10 lanes` where the loader prints `…, 1 stage gate rule(s)`, and it
   lacked the `stage gate visual:` line. Block refreshed from live output.
3. **§3** — the quoted `gate_sync_ready` failure was 7 findings; live is 14 for `--lane sync`
   and 15 for `--lane direct-license` (the gate now also demands a `manifest.json` `metadata`
   object carrying `title`, `artist`, `bpm`, `key`, `mood`, `genre`, and enforces
   `license_tiers` on the direct-license lane). Transcript replaced with the measured output.
4. **§7** — three claims were false on disk. `music/suno-gen.py` **is** in this checkout
   (42652 B) and the divergence is closed (`git rev-list --count HEAD..origin/main` = 0, it read
   15 when the brief was written). The two instrumental-render gaps are closed by `t_25a6499c`.
   The queue's `briefs:` list no longer reads `[]` — it carries 11 entries, two of them this
   genre's. The two rail walls the kit's render exposed (`t_96dfc521` duration floor,
   `t_3497b627` first-style-field caption) are recorded there so later stages do not
   rediscover them.
5. **§8** — "Existing assets: none / the first render is genuine work, not a re-run" was false:
   the kit's two renders exist and were re-measured here with `ffprobe` (16.000000 s and
   32.000000 s, digests in the table). The `gate_quota` transcript was refreshed to the
   `/usr/bin/python3` form.
6. **§10** — the dangling-reference bullet was false in both directions: both `brain/` documents
   exist on disk and in `HEAD`, and both are still absent from `origin/main`. The
   upstream-truth bullet now names the working tree instead of git objects. The resolved/open
   lists were re-cut.
7. **§11** — its closing clause ("§7's 100-fallback blocker stands") was superseded by the
   closed tempo gap.
8. **The blueprint census** — §11's "6 of the 14" was live at 15:31 and is not live now:
   `jungle-dnb.yaml` (7331 B) landed at 15:49 under card `t_e6d422ec`, so the census is 7 of 14.
   §11 keeps its clock anchor and cross-references this; §12.3 carries the current number. The
   same census shape is stale in seven other briefs — that class is card `t_c5a98379`, which
   measured the same 13 lines.

### 12.3 Re-measured, unchanged

Registry entry identical: family `utility`, lanes `[direct-license, sync]`, cadence 5/wk,
`video_shape: none`, note "82% of podcasts license stock themes". Both lanes still carry
`gate: gate_sync_ready`, requiring `[stems, metadata, clearance_doc, instrumental_version]` and
`[stems, license_tiers]`; both rungs still `advisory` in `music/autonomy.yaml`. Prompt template
4159 B / 4133 chars, style fields 420 and 422 chars (INTRO STING / LOOPABLE TALK BED), Weirdness
25 % / 20 %, Style Influence 85 % / 90 %, the same six exclusion terms. Blueprint census
re-measured at 15:52 CDT: 7 of the 14 genres carry a lyric blueprint (`activist`,
`anime-ending`, `anime-opening`, `chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`,
`trance`); the other 7 do not, and `commentary-beds` is one of them. It was 6 when §11 measured
it at 15:31 — `jungle-dnb.yaml` landed at 15:49 (card `t_e6d422ec`) — so this census is a moving
number; the class is carded as `t_c5a98379`. Rubric `music/rubrics/utility.json`
unchanged: `pass_threshold` 7.0, five criteria, weights 3 / 3 / 2 / 2 / 1 with `voice_headroom`
and `seamless_loop` at 3. `gate_quota` PASS 0/60, studio 0. `gate_sync_ready` re-exercised on an
empty package dir, rc=1 both lanes. §4's bar math holds: at 120 BPM one bar is exactly 2.00 s,
so 8 bars = 16.0 s, 16 bars = 32.0 s and 15 s = 7.5 bars (the off-grid cutdown finding).
Throughput 5/wk × 2 generations per kit = 10 generations/week.

### 12.4 Checks run on the committed content

```
PASS check_oracle_board: every one of the 12 open oracle genre(s) carries exactly one open card
PASS check_oracle_determinism: trend fetch failure never outscores an empty success
PASS check_brief_figures    --briefs …: 5 recomputed figure(s) across 1 brief(s)
PASS check_brief_drift      --briefs …: 2 live count(s) across 1 brief(s)
PASS check_brief_line_refs  --briefs …: 2 cited line range(s) resolve and hold
PASS check_brief_bpm_solutions  --briefs …: 0 styleWeight claim(s) buy the BPM they state
PASS check_brief_paths / check_stage_scripts / check_prompt_style_counts / check_gate_lane_surface
PASS check_stage_advance / check_doc_refs / check_video_shapes
```

Repo-wide `check_brief_figures` still FAILs on **other** briefs (`elemental-water.md:600`,
`epic-orchestral-boss.md:53`) — filed as `t_34f496d7` / `t_6dd13d76`, not touched here.

**Supersession record.** Superseded blob
`7db8ea568da53bd1983bb53737680223dc72d4f862421900e299c481aeea1398` (320 lines / 19360 B, commit
`63440da`); this pass's revision is committed on `main` and its digest is re-readable with
`sha256sum music/briefs/commentary-beds.md`. The figure pass of card `t_6dd13d76`
(2026-10-16T17:21-05:00 CDT) supersedes
`sha256 695a48c6de68ab892ca9e3bafd2edde8eef2fc97d19589a9d63850d1aca2e064` (515 lines / 32830 B):
the two-rail-walls entry was restated — the style-field wall is FIXED by `t_3497b627` and both
kit plans were re-measured. The chain resumes at the stage after `brief` —
`genre-select`, whose resolution §1–§3 already carry. The re-emitted card's body marker
(`stage: brief`) is the defect card `t_6599927d` owns, not a reason to re-run the brief stage.
