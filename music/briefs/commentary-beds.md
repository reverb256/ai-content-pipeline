# Brief — commentary-beds

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`; on this board the
> cards are assigned `music-producer` and claimed by the generic kanban dispatcher).
> **Card:** t_47491ec0 (`music-oracle: commentary-beds (score 8.1)`)
> **Duplicate card:** t_4187b092 (`music-oracle: commentary-beds (score 8.3)`) — same genre,
> same lanes, created by the second oracle run ten minutes later. Both resolve to THIS
> brief; the brief is keyed by genre, not by card.
> **Verified (unit-correction pass, `t_e504b516`):** 2026-10-16T15:22-05:00 (CDT) — §1 registry
> table and §10 provenance. Both cited the prompt template's size with the unit `B`, but the
> value they gave was that file's CHARACTER count, so the label understated the byte count.
> Both labels are corrected in place; no other figure in this brief was touched. The 13:20
> revision of this file is
> `sha256 d6fbd52f800199fe501a41556835e0b582dfd82f458a4c4c4c9a8bab9139b590` (commit `9ebf6af`);
> this pass supersedes it.
> **Written:** 2026-10-16T13:20-05:00 (CDT)
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `ade6e87` (main; the working tree is shared
> by 6–7 concurrent brief-stage workers and HEAD moved 4 times while this brief was written).
> **Oracle:** 8.1/10 — quota headroom 10.0, **lane coverage 4.0**, revenue 10.0, cadence fit
> 10.0, policy risk 10.0, trend signal 3.0. Threshold 5.0 → produce.

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
$ python3 music/gates/gate_sync_ready.py --package-dir <empty> --lane sync
FAIL gate_sync_ready
  - full_mix.wav is not a real audio file (ffprobe could not read a duration)
  - no stems/ directory — a sync track without stems is not sync-ready (architecture HARD RULE 4)
  - only 0 stem(s) found; 4 required (drums, bass, keys, vocals, ...)
  - instrumental.wav is not a real audio file (sync needs an instrumental version)
  - no manifest.json
  - no clearance_doc.pdf (or .txt) — sync requires a clearance document
  - no ai_disclosure.txt — the AI role must be declared for sync platforms
rc=1
```

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

**The lane's own generate prompt names `music/suno-gen.py`. That file is not in this
checkout.** It exists on `origin/main` (`music/suno-gen.py`, commits `295fc49`, `ba28f55`).
This checkout has diverged: `git rev-list --count HEAD..origin/main` = **15** commits of this
lane's own work missing locally, plus local brief commits that are not upstream. Already
carded (t_8a715681, nexus-core) — flagged, not fixed: seven workers share this tree and a
pull/rebase would auto-stash their in-flight edits.

What `origin/main` contains, read from the git object (not from disk):

- `music/suno-gen.py:141 is_instrumental_template(genre)` — the decision that lets the rail
  accept a track with no human lyric sheet. Its own docstring names the 8 instrumental
  templates: **chill-lounge, sentimental-piano, commentary-beds, elemental-fire/water/earth/air,
  chiptune-8bit, epic-orchestral-boss**, and it keys on the template's `## Lyrics guidance`
  section. `music/prompts/commentary-beds.md` says "Leave the **lyrics box empty**" — so this
  genre is detected as instrumental and needs **no lyric sheet**. That is the whole reason a
  5/wk kit cadence can close.
- `music/sunolocal/**` — the local Suno-shaped service (ACE-Step + YuE2 adapters); the live
  render engine is the in-cluster `sunolocal` deployment.

**Two render gaps that bite this genre** (both already carded on t_25a6499c, nexus-core —
cited here so the stages after this one do not rediscover them):

1. **Instrumental tracks cannot be expressed in the planner queue.** `mining-k8s`
   `values.yaml` brief schema is `{name, genre, brief, lyricsMode?, language?, title?,
   duration?}` and `planner.py --lyrics-mode` accepts only `draft|ai`. For an instrumental
   genre both are wrong: `draft` produces a scaffold `acestep_plan.py` refuses (exit 1,
   `.refused` marker), `ai` writes lyrics for a track that must have none. An
   `instrumental` mode is required before this kit can render. (Measured on the
   sentimental-piano card: `/var/lib/music-plans/smoke-chill-lounge.rendered` and
   `testplan.rendered` both contain `refused`.)
2. **Tempo.** The deployed `sunolocal/translate.py` hardcodes `bpm = 120`. For most of the 8
   instrumental genres that is wrong (sentimental-piano anchors 72), but for
   **commentary-beds 120 BPM is exactly the product spec** — the hardcode is accidentally
   correct here and must not be "fixed" into a different value for this genre. The local
   planner, by contrast, falls back to `bpm = 100` when
   `music/lyrics/blueprints/<genre>.yaml` is absent (`music/planner/planner.py` ~line 470,
   `"blueprint": false`), and only 3 of 14 genres have a blueprint (`activist`,
   `chill-lounge`, `trance`). **Acceptance for this genre: the plan's `bpm` field must read
   120, never 100.** At 100 BPM a bar is 2.40 s and every bar-aligned cutdown in the kit is
   wrong.

Live route into audio (in-cluster, not the kanban stage machine): ConfigMap
`music-pipeline-briefs` → CronJob `music-pipeline` (plans via `planner.py` →
`/var/lib/music-plans/<name>.json`) → CronJob `music-pipeline-render` (`acestep_plan.py` →
sunolocal studio API). Chart: `/home/j_kro/mining-k8s/helm/charts/music-pipeline/`; its
payload already carries `music/prompts/**` (including `commentary-beds.md`),
`music/genres.yaml`, `planner.py`, `acestep_plan.py` and `lyrics/blueprints/`. `values.yaml` `briefs:` reads `[]` (line 39,
measured 2026-10-16); sibling cards have requested the first additions for trance
(`t_791b48f7`) and anime-ending (`t_a14e5d52`), neither applied yet.

## 8. Existing assets for this genre

Measured: **none.** `music/lyrics/` holds `activist/`, `chill-lounge/`, `trance/` and
`blueprints/{activist,chill-lounge,trance}.yaml` — no commentary-beds sheet or blueprint
(expected: the genre is instrumental, so there is no lyric sheet to write). No campaign
directory, no masters, no stems, no cover exist for this genre. The first render is genuine
work, not a re-run. Quota is untouched:

```
$ python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

## 9. Stage plan for this genre (skips locked)

`brief` ✓ → `genre-select` → **`lyrics` SKIPPED** (instrumental: the template's empty-box
statement is the spec; `is_instrumental_template` keys on it) → `generate` (quota gate first;
**two** generations per kit — sting and bed separately) → `curate` (pick the winning sting and
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
- Upstream truth read from git objects: `origin/main:music/suno-gen.py` (`is_instrumental_template`),
  `music/sunolocal/translate.py` (bpm hardcode, quoted from the deployed pod on t_25a6499c)
- **Dangling reference (unchanged):** `brain/playbooks/music-lane-architecture.md` is cited as
  "READ FIRST" by this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`,
  `autonomy.yaml`, `gates/README.md` and `gates/*.py`, but no copy exists on this machine
  (`find /home/j_kro -name 'music-lane-architecture.md'` → no hits). Same for
  `brain/research/music-monetization-2026.md` (`brain/research/` does not exist). Quoted
  section numbers (§3, §5, §11.2) cannot be checked. Carded: t_b0a4db92 (coo).
- **Not fixed here (other owners, already carded):** diverged checkout t_8a715681; scheduler
  units running the wrong checkout t_41f354be; instrumental/in-genre render gaps t_25a6499c;
  28 oracle cards for 14 genres t_bf0e5edd; missing architecture docs t_b0a4db92; profile
  workdir + kanban env vars t_75aacf8b.
- **hotspot:** `music/briefs/` — six concurrent workers write this directory and commit to one
  working tree (`4daf132`, `9c2d2d3`, `132a781`, `4bb1ea6`, `ade6e87` landed inside 15
  minutes). `music/stages.yaml`, `music/oracle.py` and `scripts/automation/*` are also being
  edited in the same tree while this brief runs.
