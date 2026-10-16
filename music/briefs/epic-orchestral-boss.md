# Brief — epic-orchestral-boss

> **Stage:** `brief` (`music/stages.yaml`: `brief` → bot `producer`)
> **Card:** t_2a798908 (`music-oracle: epic-orchestral-boss (score 7.55)`)
> **Duplicate card:** t_67fc5307 (`music-oracle: epic-orchestral-boss (score 7.75)`) — same
> genre, same lanes, second oracle wave. Both resolve to THIS brief; the brief is keyed by
> genre, not by card.
> **Written:** 2026-10-16T13:16-05:00 (CDT), music-producer
> **Verified (duplicate-card pass, `t_67fc5307`):** 2026-10-16T13:42-05:00 (CDT) — see §14.
> The pass re-measured every checkable claim and fixed four: §1 (the payload checkout
> root — `mining-k8s/...` is relative to `$HOME`, not to this repo), §8b (job ages
> replaced with job names), §8c/§8d (the section split's real source, and the scaffold's
> 8-of-8 empty result), §13 (tip, divergence, gate census). Pre-pass revision:
> `sha256 fcf97717…`, 542 lines. New regression check:
> `music/scripts/check_brief_paths.py`.
> **Repo:** `/home/j_kro/ai-content-pipeline` — the lane repo. Its `main` tip at write time
> was `d491663`; re-measured 13:38 it is `afa242e` (this lane commits constantly, so the tip
> is a timestamp, not an identity). **`/home/j_kro/mining-k8s` is a second checkout**; every
> `mining-k8s/...` citation below is relative to `$HOME`.
> **Oracle score:** 7.55/10 — quota headroom 10.0, lane coverage 8.0, revenue 10.0,
> cadence fit 1.7, policy risk 9.0, trend signal 3.0. Threshold 5.0 → produce.
> **Genre class:** **choral vocal** (choir/chant, no solo singing). NOT instrumental —
> see §6, which corrects a live claim in the deployed engine.

Every number, quoted string and verdict below comes from a command run or a file read
during this stage. Nothing here is recalled.

## 1. Genre resolution (live)

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

`/usr/bin/python3` is the interpreter the systemd units and CronJobs use; it has PyYAML.
The shell's bare `python3` is the Hermes bundled interpreter and has no PyYAML.

| Field | Value |
|---|---|
| Genre | `epic-orchestral-boss` |
| Family | `gamer` |
| Prompt template | `music/prompts/epic-orchestral-boss.md` — exists, 4525 bytes |
| Visual style | `music/visuals/dark-fantasy.md` — exists, 1387 bytes |
| Lanes | `game-assets`, `youtube-gaming`, `sync`, `streaming` |
| Cadence | `1/wk` |
| Video shape | `single-4min` |
| Family rubric | `music/rubrics/gamer.json` (6606 bytes), `pass_threshold` 7.0 |
| Lyric blueprint | `music/lyrics/blueprints/epic-orchestral-boss.yaml` — **ABSENT** |
| Registry defaults | export `studio`, stems `true`, lyrics `human-original`, release_private `true`, gate_profile `reviewer-deepseek` |

The registry note for this genre is empty; the template's own header carries the intent.
Measured live: the same template is present in the chart payload
(`/home/j_kro/mining-k8s/helm/charts/music-pipeline/files/music/prompts/epic-orchestral-boss.md`)
and is **byte-identical** to the lane repo copy (`cmp` → identical, no output). Note the
root: `mining-k8s` is a **second checkout** at `/home/j_kro/mining-k8s`, so that citation
resolves from `$HOME`, never from inside this repo. Read against the lane repo it looks like
the payload is missing — the pass hit exactly that and fixed the citation here. A regression
check now guards the class: `music/scripts/check_brief_paths.py` (PASS, 13 citations).

## 2. Intent — the three-act trailer contract

`music/prompts/epic-orchestral-boss.md` fixes the product, not a mood:

> "The flagship boss theme: full hybrid orchestral, choir, taiko, three-act trailer form."

Five things must hold, or the render is **out of genre — reject it** (template craft notes):

1. **Staccato low-string ostinato never stops.** It is the engine and the editor's rhythmic
   sync points. No ostinato = wallpaper.
2. **Taiko + timpani battery**, not a drum kit. Percussion is artillery.
3. **Choir is a weapon.** Syncopated choral HITS and chant that DOUBLES the brass theme.
   Sustained vocal pads are the template's named "#1 tell of AI epic slop."
4. **The false ending is load-bearing.** Near-silence before the climax — one sub-boom, a
   breath, a single string sustain. "Skip the silence and the climax lands as a nudge."
5. **Sudden breathless finale.** End on a hit with a short tail. **A fade-out is a defect
   in this genre.**

Anchor: **150 BPM in C minor**, 4/4. 140–160 is the boss pocket. Style Influence 80%,
Weirdness 40%. Exclude Styles (6 terms, the documented maximum):
`pop vocals, EDM drop, trap, lo-fi, ambient drone, cheerful major` — do **not** exclude
"EDM" wholly; hybrid trailer music keeps synths and risers.

Working title for this first track: **"The Last Gate."** The title is a proposal for
j_kro's creative gate, not a decision this stage can make. Subject for the planner:

> A gate that has not opened in a thousand years opens once. Three acts: the dread of the
> thing behind it, the escalation of the thing that walks through, and the silence in which
> the music decides whether the world ends. It ends on a hit, not a fade.

## 3. Target lanes and what each one demands

From `music/lanes.yaml` and `music/autonomy.yaml`. These are the gates that will run.

| Lane | Surface / bot | Gate | Required artifacts | Autonomy |
|---|---|---|---|---|
| `game-assets` | itch.io, unity-asset-store, gamedev-market / distributor | `gate_sync_ready` (+`gate_loop_points`) | `stems`, `loop_point`, `seamless_loop`, `metadata` | advisory |
| `youtube-gaming` | youtube / videobot renders, publishbot uploads | `gate_youtube_authentic` | platform-native visual + AI disclosure | advisory |
| `sync` | songtradr, audiosparx / distributor | `gate_sync_ready` | `stems`, `metadata`, `clearance_doc`, `instrumental_version` | advisory |
| `streaming` | distributor (DistroKid; TuneCore alt) | `gate_release_ready` (+`gate_loudness`) | `ai_disclosure`, `isrc`, `metadata`, `master` | advisory |

All four rungs are `advisory`, evidence `0 / 0 / 0` (clean_publishes, platform_strikes,
revenue_usd). No lane may publish itself. Promotion to `supervised` needs 10 clean advisory
publishes and j_kro's approval.

What the gates actually require, read from the gate code (not from prose):

- `gate_sync_ready` — `full_mix.wav`; **≥ 4 stems** (`MIN_STEMS`), each within ±0.5 s of the
  master; `instrumental.wav`; `manifest.json` with `title, artist, bpm, key, mood, genre`;
  a non-empty `clearance_doc.pdf`/`.txt`; a non-empty `ai_disclosure.txt`; **plus
  `loop_points.json` for the `game-assets` lane.**
- `gate_loop_points` — does not trust `loop_points.json`; it renders the seam
  (tail window + head window, 3.0 s default) and PASSes when junction curvature ÷ body
  curvature ≤ 3.0. Documented separation: a clean synthetic loop measures 1.6x, a
  half-period phase slip 6.0x.
- `gate_release_ready` — `master.wav`; `artwork.jpg|jpeg|png`; `manifest.json` with
  `title, artist, isrc, genre`; non-empty `ai_disclosure.txt`. ISRC must match
  `^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$` — 12 characters, **no check digit** (verified in the
  pass: `ISRC_RE` plus `isrc_syntax()` test shape only — 2 letters, 3 alphanumeric, 2-digit
  year, 5-digit designation; there is no checksum to fail. The gate's own docstring claims it
  enforces "the ISRC check digit (ISO 3901)", which the code does not do. A shape-valid but
  invented ISRC passes. Doc-vs-code gap, recorded here, not filed as its own card).
- `gate_loudness` — `TARGETS = {"streaming": -14.0, "sync": -16.0}`, tolerance 1.0 dB.
  (The ruler itself is contested: t_9546841b.)
- `gate_youtube_authentic` — real video ≥ 640x360; **≥ 10 distinct frame signatures** when
  sampled every 2.0 s; Jaccard similarity ≤ 0.85 against prior uploads when an upload
  index is supplied; a disclosure file beside the visual.

Three requirements collide with this genre and are settled here, not later:

**L1 — the master is not a loop, and game-assets demands a loop.** The lane requires
`loop_point` + `seamless_loop`; the genre's product is a three-act trailer with a
load-bearing silence and a hard hit ending ("fade outs are a defect"). A loop of the master
is impossible without destroying the genre. **Decision:** the master keeps the three-act
form; the `game-assets` deliverable is a **separate loop edit** built from the Act II
escalation (ostinato + taiko + brass, no false ending), delivered with its own
`loop_points.json`. At 150 BPM one bar is 1.6000 s, so a 64-bar loop region is **102.4 s**
and lands on the bar; 16 bars is 25.6 s if a short loop is wanted. The family rubric scores
`loop_safety` (weight 3) against the loop edit, never against the showpiece master.

**L2 — `youtube-gaming` declares `loop-10min`, this genre declares `single-4min`.**
`music/lanes.yaml` gives the lane `shape: loop-10min`; `music/genres.yaml` gives the genre
`video_shape: single-4min`; `music/visuals/dark-fantasy.md` says "Video shape: single-4min"
and calls the genre "a SHOWPIECE video… not a loop wallpaper". No script reads either field
(measured: `grep -rn video_shape` finds only declarations and comments); the `visual` stage
prompt reads **the genre's** `video_shape`. **Decision:** `single-4min` wins for this
genre; `loop-10min` is the youtube-gaming default for the loop genres (elemental-*,
chiptune-8bit).

**L3 — `instrumental_version` on a choir track.** `gate_sync_ready` requires
`instrumental.wav` to be real audio and to not be a byte-identical copy of `full_mix.wav`
(that is the whole test). For a genre whose lead element is a choir, the orchestral-only
bed **is** the instrumental version. **Decision:** derive it from the choir stem at the
`stems` stage (stems are already mandatory for `sync` and `game-assets`), and record the
derivation in the manifest. Do not ship a copy of the master under a second name.

## 4. Audio identity (locked for this genre)

Style caption, verbatim from `music/prompts/epic-orchestral-boss.md` — **640 characters**,
matching the template's own "640/1000 chars" declaration, inside the 1000-character
Styles field:

```
epic hybrid orchestral boss battle, 150 BPM in C minor, dark atmospheric intro with low sub-drone and whispered choir breaths, aggressive staccato string ostinato as the engine, thunderous taiko and timpani battery, roaring low-brass braams and power-chord stabs, Latin-esque chant choir rising in intensity, fifth-heavy brass fanfare theme, trailer sound design with risers and sub-boom impacts, three-act build: dread intro, rhythmic escalation with layered ostinato, near-silence false ending, apocalyptic wall-of-sound climax with full choir and brass fanfare, sudden breathless final hit, heroic and terrifying at once, cinematic scale
```

Structure: the template's **8 sections**, in this order —
`Intro, Choir, Build, Instrumental, Choir, Breakdown, Chorus, Outro`.
The `Breakdown` is the false ending. The `Outro` is the hard cut.

Duration: **240 s**. Basis: 150 BPM in 4/4 → one bar = 4×60/150 = 1.6000 s;
240 s = **exactly 150 bars**, and it is the `single-4min` shape. Inside the planner's guard
rail (`planner.py` `MIN_DURATION_S=30`, `MAX_DURATION_S=420`). For comparison, measured:
300 s = 187.5 bars (fractional), 420 s = 262.5 bars (fractional) — 240 s is the only clean
choice of the three.

## 5. Visual identity (locked for this genre)

`music/visuals/dark-fantasy.md`: obsidian `#0e0b12`, blood crimson `#8c1f28`, cold steel
`#6e7b8a`, pale gold `#d8c9a3` for choir/magic accents. The boss arena: gargantuan scale,
backlit boss silhouette, one light source (throne fire / rift / eclipse). The camera mirrors
the three acts — Act I slow push-in on darkness (0.5 px/frame), Act II orbiting mid-shots
with 2–4 px impact shake, breakdown = hold on black with a single ember, climax = rapid cuts
on the choir hits with 2–4 frame strobes on downbeats. Final hit = hard cut to black, no
fade. Volumetric haze, rising embers, 5% grain, chromatic aberration 2% on impact frames
only. Each song gets its own boss silhouette and arena.

**Measured state of the existing asset.** `music/visuals/dark_fantasy.mp4` is 1280x720,
25 fps, **5.0 s**, 14552 bytes. It fails the lane's gate today:

```
$ python3 music/gates/gate_youtube_authentic.py --visual music/visuals/dark_fantasy.mp4
FAIL gate_youtube_authentic
  - visual has only 2 distinct frame signature(s) across 5.0s (sampled every 2.0s;
    10 required) — this is a raw dump (static image + audio)
  - no disclosure file (one of disclosure.txt, ai_disclosure.txt) beside the visual
```

(The album-shape render next to it, `album_30_60min.mp4` — 1280x720, 1800.0 s — fails the
same way with 4 distinct signatures; re-measured in the pass, unchanged.) So the `visual`
stage must render a real 240 s
showpiece and place a disclosure file beside it. The 5 s template render is a colour
reference, not a deliverable.

## 6. Lyrics — the genre is CHORAL, not instrumental

This is the one structural place where the live pipeline contradicts this genre, so it is
recorded here as a measured fact.

The deployed engine's translation module asserts otherwise. From the running pod
(`kubectl -n mining exec deploy/sunolocal-source -- cat
/opt/sunolocal/music/sunolocal/translate.py`, image tag `localhost/sunolocal:v0.1.2`):

> "8 of the 14 genre templates are instrumental (chill-lounge, sentimental-piano,
> commentary-beds, the four elementals, chiptune-8bit, **epic-orchestral-boss**); this is
> the path that lets them render at all."

That list has 9 names under a count of 8, and the last name is wrong. Measured with
`grep -Ei 'is instrumental|leave the lyrics box empty|lyrics box empty'` over all 14
templates:

```
activist.md 0   anime-ending.md 0   anime-opening.md 0   chill-lounge.md 1
chiptune-8bit.md 1   commentary-beds.md 1   elemental-air.md 1   elemental-earth.md 1
elemental-fire.md 1   elemental-water.md 1   epic-orchestral-boss.md 0
jungle-dnb.md 0   sentimental-piano.md 1   trance.md 0
```

**8 of 14 declare the instrumental path. `epic-orchestral-boss` is not one of them.** Its
template says the opposite: "Choir only — no solo lyrical singing. Latin or pseudo-Latin
chant syllables as TEXTURE… Mark it explicitly so Suno does not invent English lyrics."
Its `[Instrumental]` line is one *section* of the choir piece, not a declaration that the
track has no vocals.

Consequences, binding downstream:

1. **Do not pass `instrumental: true`.** That path appends `", instrumental, no vocals"` to
   the caption — measured: the 640-character caption becomes 665 characters ending
   `'…cinematic scale, instrumental, no vocals'` — and substitutes `lyrics = "[Instrumental]\n"`.
   For this genre that steers the engine away from its single defining element.
2. **The `lyrics` stage is NOT a no-op for this genre.** A human-authored chant sheet is
   required, and the copyright claim rides on it (`registry` default `lyrics:
   human-original`).
3. The template's tag sheet is **structure control, not lyrics**. Its parentheticals
   ("low male chant murmurs, one held chord, no drums") are engineering notes.

### What the lyric sheet must satisfy (measured, by running the gate)

The lyrics gate was exercised against two probe sheets in the worker scratch dir (not
deliverables, no authorship claimed):

```
$ python3 music/gates/gate_lyrics_original.py --lyrics-file <8-tag chant probe>
FAIL gate_lyrics_original
  - only 13 unique words; 25 required
  - only 13 unique words (minimum 25)

$ python3 music/gates/gate_lyrics_original.py --lyrics-file <same> --strict
FAIL gate_lyrics_original
  - only 13 unique words; 25 required
  - only 13 unique words (minimum 25)
  - unknown section tag [Choir] (not a Suno metatag)
  - unknown section tag [Choir] (not a Suno metatag)

$ python3 music/gates/gate_lyrics_original.py --lyrics-file <the template's own lyric block>
FAIL gate_lyrics_original
  - [Choir] placeholder guidance left in: '(low male chant murmurs, one held chord, no drums)'
  - [Instrumental] placeholder guidance left in: '(brass states the fanfare theme over full percussion)'
  - [Choir] placeholder guidance left in: '(chant doubles the theme, medium intensity, syllabic)'
```

(Re-run in the verification pass. The verdict reproduces, and the real output lists **three**
placeholder findings — both Choir lines and the Instrumental direction — not the one quoted
here. The pass's chant-sheet probe also reported **8** unique words against the
`MIN_UNIQUE_WORDS = 25` floor rather than the 13 recorded above; which words the probe sheet
uses changes that count, and the FAIL verdict is the same either way. The floor and the
verdict are the load-bearing facts. §14.)

Three hard requirements follow, plus one defect:

- **≥ 25 distinct tokens** (`MIN_UNIQUE_WORDS = 25` in `music/lyrics/lyrics.py`; the gate
  imports the same constant). The tokenizer is `re.findall(r"[a-z']+", line.lower())`, so
  **hyphenated chant syllables split at the hyphen** — "for-tis" yields two tokens "for" and
  "tis". Measured in the pass: `unique_word_count([("Choir", ["for-tis as-tra"])])` = **4**,
  against **3** for the same syllables written unhyphenated. Write chant words unhyphenated.
  A five-word "Fortis Astra Dominus" chant repeated eight times FAILS this gate.
- **No parenthetical-only lines** in any section: they are rejected as "placeholder guidance
  left in". Every Choir/Build section needs real chant lines.
- **≥ 2 content sections** (`MIN_SECTIONS = 2`) and the 8 template sections in order.
- **Defect D4 — `[Choir]` is not a known section tag.** `KNOWN_SECTIONS` in
  `music/lyrics/lyrics.py` lists Intro, Verse, Pre-Chorus, Chorus, Post-Chorus, Bridge,
  Refrain, Hook, Breakdown, Drop, Build, Rise, Interlude, Solo, Instrumental, Vamp, Outro,
  Fadeout, End, Spoken Word, Ad-Lib — **no `Choir`**. The default (non-strict) gate
  invocation passes; `--strict` fails this genre's mandated structure. Reported on the
  existing engine card (see §9).

**Prerequisite for the lyrics stage:** `music/lyrics/blueprints/epic-orchestral-boss.yaml`
does not exist (only `activist`, `chill-lounge`, `trance` do; `planner.py:load_blueprint`
docstring says "3 of 15 genres do"). `lyrics.py cmd_scaffold` **refuses to scaffold without
a blueprint** (`FAIL: no lyric blueprint for '<genre>'`), so the lyrics stage cannot start
until the blueprint lands. It must carry `family`, `theme`, `title_candidates`, `structure`
(the schema `lyrics.py` requires) plus `bpm_anchor: 150` and `mood_words`, so the planner's
BPM matches the caption (see D1).

## 7. Existing assets for this genre

Measured, not assumed.

- `music/lyrics/` holds sheets for `activist`, `chill-lounge`, `trance` only. No
  epic-orchestral-boss sheet, so `gate_lyrics_original` has nothing to pass yet.
- No blueprint (§6).
- No plan, no render, no master anywhere. `find` over the lane repo returns exactly one
  epic-orchestral-boss path: `music/prompts/epic-orchestral-boss.md`. `/var/lib/music-plans/`
  holds `final-round.json`, `smoke-chill-lounge.json`, `testplan.json` and their `.rendered`
  markers — nothing for this genre. `~/Music` is **empty** (0 files).
- `music/visuals/dark_fantasy.mp4` exists and is a 5 s placeholder (§5).
- Quota is untouched:

```
$ /usr/bin/python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

## 8. The generation path (measured live)

### 8a. The live service — `sunolocal`

```
$ kubectl -n mining get deploy sunolocal-source    -> 1/1 READY, image localhost/sunolocal:v0.1.2
$ curl -s http://10.43.164.190:8123/health          -> {"status":"ok"}
$ curl -s http://10.43.164.190:8123/api/v1/models   -> {"engines":{"ace":{"kind":"ACE-Step 1.5",
     "via":"acestep_plan.py -> comfyui-zephyr window"},"yue2":{"kind":"YuE2-3B","via":"yue2-zephyr http"}},
     "default":"ace"}
```

Service `sunolocal` ClusterIP `10.43.164.190:8123`; `comfyui-zephyr` is Running in the same
namespace (NodePort `8188:32188`). The GPU stays on zephyr — no local model load, per lane
GPU rules.

### 8b. The planning/render CronJobs (namespace `mining`)

| Stage | Job | Schedule | Input | Output |
|---|---|---|---|---|
| plan | `music-pipeline` | `17 */6 * * *` | ConfigMap `music-pipeline-briefs`, key `briefs.json` | `/var/lib/music-plans/<name>.json` |
| render | `music-pipeline-render` | `41 */4 * * *` | plans with no `.rendered` marker | audio via `/payload/music/scripts/acestep_plan.py` |

The live queue holds one entry (ConfigMap read, verbatim):

```json
[{"brief":"a late-night kitchen where someone finally stops working and just listens to the rain",
  "genre":"chill-lounge","lyricsMode":"draft","name":"smoke-chill-lounge","title":"Kitchen Light"}]
```

The chart's own list is empty — `mining-k8s/helm/charts/music-pipeline/values.yaml:39`
reads `briefs: []` — so **chart values and the live ConfigMap have drifted** (GitOps will
revert the ConfigMap on the next sync). Both job histories are healthy and quiet. Measured
at 13:42 (the pass replaced the relative ages that were here — ages decay, names do not):
`music-pipeline-29869517` Complete (created 79 m before the write, run 7 s),
`music-pipeline-render-29869541` Complete (created 55 m before the write, run 5 s), both
still the newest of their series. The markers record what the queue produced:
`smoke-chill-lounge.rendered` = `refused`, `testplan.rendered` = `refused`,
`final-round.rendered` = empty (rendered).

Two different `--allow-empty` postures exist and must not be confused:
- the **CronJob render path** invokes `acestep_plan.py` **without** `--allow-empty`, so a
  draft plan with empty sections exits 1 and gets a `refused` marker;
- the **sunolocal adapter path** (`adapters/ace_comfy.py`) passes `--allow-empty`, so the
  same draft renders there with the empty sections read as a vocal-shaped hole.

### 8c. What this brief translates to, executed against the deployed code

The deployed `translate.suno_to_aceplan` was imported (copied from the running pod, no GPU,
no network) and run with this genre's real 640-character caption:

```
--- variant A, style_weight=0.80 (template Style Influence 80%) ---
  bpm            : 156
  key field      : 640 chars; full caption? True
  caption chars  : 640
  sections       : 8  empty=['Choir', 'Instrumental', 'Choir']
  render verdict : needs --allow-empty

--- variant A, style_weight=0.75 ---
  bpm            : 150
  key field      : 640 chars; full caption? True

--- variant B, instrumental=True, lyrics empty ---
  caption tail   : '...cinematic scale, instrumental, no vocals'   (665 chars)
  lyrics         : '[Instrumental]\n'
  bpm            : 156
```

Read off that measurement:

- **The template's Style Influence 80% renders this genre at 156 BPM, 1.04x fast.** 150 BPM
  is only reachable at `style_weight = 0.75` — i.e. by telling the engine to follow the
  style *less* than the template asks. Either value is a workaround for defect D1.
- **The `key` field receives the whole 640-character caption**, which `acestep_plan.py`
  passes straight into the ACE node as `keyscale` (`"keyscale": plan["key"]`). C minor is
  carried only as text inside the caption. Whether ACE recovers the key from that paragraph
  is **unverified** — it needs a render, which is the `generate` stage, not this one. Do not
  claim the render is broken; claim the input is malformed.
- The empty-section note matters for the lyrics stage: `Intro`, `Build`, `Breakdown`,
  `Chorus` and `Outro` count as *non-empty* to the checker only because their wrapped
  parenthetical direction lines continue on a second line that does not start with "(".
  Three sections are genuinely empty. See D5. Measured in the pass, with the splitter named:
  the `sections` list does **not** come from `translate.py` (the plan dict it returns has no
  `sections` key); it comes from `music/scripts/acestep_plan.py`'s own regex
  `^\[([^\]]+)\][ \t]*\n(.*?)(?=\n\[|\Z)`. Fed the template's tag sheet verbatim it returns
  **8 sections, 3 empty — `['Choir', 'Instrumental', 'Choir']`**, exactly as recorded here.
  Fed the *planner's own scaffold* for this genre (which puts every direction line on one
  line) it returns **8 of 8 empty**, and `check_lyrics(plan, allow_empty=False)` refuses:
  `FATAL: 8 section(s) have no lyrics: Intro, Choir, Build, Instrumental, Choir, Breakdown,
  Chorus, Outro.` So the "3 of 8" hole is a property of the raw template sheet; the CronJob
  route's own scaffold is refused as it should be. Both measurements are in §14.

### 8d. Planner dry-run (measured, no network)

```
$ /usr/bin/python3 music/planner/planner.py plan \
    --brief "the boss arena, three-act: dread, escalation, the false ending, then the wall of sound" \
    --genre epic-orchestral-boss --lyrics-mode draft --title "The Last Gate" \
    --duration 240 --out plan-epic.json
plan     : plan-epic.json
genre    : epic-orchestral-boss   lyrics_mode: draft
structure: Intro -> Choir -> Build -> Instrumental -> Choir -> Breakdown -> Chorus -> Outro
bpm/key  : 100 BPM · C minor · 4/4
duration : 240s   language: en
validation: PASS
```

The structure is the template's 8 sections, in order — correct. Two fields are wrong:

1. **BPM 100, not 150.** `--genre` has no blueprint to anchor it, so `planner.py` falls back
   to 100 and records `"_meta": {"blueprint": false}`. The caption (which is what the engine
   reads) still says 150. Fix: the blueprint in §6, and `planner.py`'s own validation then
   enforces the anchor (it rejects a plan more than 12% off a declared `bpm_anchor`).
2. **`language: en`.** This genre's lyrics are Latin-esque chant. `--language` only feeds the
   `ai` lyrics mode, which this track must never use, so the value is cosmetic — but set it
   to `la` so no downstream reader mistakes this for an English vocal.

## 9. Defects that block this genre downstream (all measured)

**D1 — BPM is not expressible; the 150 BPM anchor cannot be honoured.** Deployed
`translate.py:42` hardcodes `bpm = 120`; the only override (`:45`) repurposes Suno's
*style-adherence* dial as a tempo control. Measured above: 0.80 → 156 BPM, 0.75 → 150 BPM.
Already filed as **t_25a6499c** (nexus-core); the epic-orchestral-boss numbers are added to
that card as a comment.

**D2 — the `key` field receives the style caption.** `translate.py:49`,
`key = req.style or "C major"`, and `acestep_plan.py:100` passes it as `keyscale`. Measured:
the 640-character caption, verbatim. Same card as D1.

**D3 — the deployed comment misclassifies this genre as instrumental.** The list names
`epic-orchestral-boss`, which declares no instrumental path (0 marker matches). Following
that comment would strip the choir. Same card as D1; corrected here for the record.

**D4 — `[Choir]` is not a known section tag** (`music/lyrics/lyrics.py:KNOWN_SECTIONS`).
Non-strict passes; `--strict` fails. Measured by running the gate. Same card as D1 (it is
the same artifact set, `music/lyrics/lyrics.py` ships in the chart payload).

**D5 — the draft guard passes wrapped direction lines as lyrics.**
`music/scripts/acestep_plan.py:check_lyrics` treats a section as empty only when every line
starts with `#` or `(`. The template's direction lines wrap, so continuation lines like
`heartbeat pulse)` count as singable text. Measured with this genre's own tag sheet: 8
sections, only 3 reported empty. On the adapter path — which **always** passes
`--allow-empty` — a draft of this genre would render with the craft notes sung. Filed as a
new card **t_bc6a0c00** (nexus-core) with the reproduction and the regression test.

**D6 — the payload sync check compares against the wrong checkout, and the payload has
drifted.** `mining-k8s/helm/charts/music-pipeline/check-payload-sync.sh` defaults
`SRC=/home/j_kro/Projects/ai-content-pipeline`, the checkout that has no `music/` tree, so
it reports false DRIFT for every file. Run with the correct source it still fails:

```
$ SRC=/home/j_kro/ai-content-pipeline bash check-payload-sync.sh
DRIFT  music/planner/planner.py
DRIFT  music/scripts/acestep_plan.py
RESULT: FAIL — run sync-payload.sh
```

`music/genres.yaml`, `music/prompts/*` (including this genre's template) and the blueprints
match. Also measured: the payload carries **no `music/visuals/**`** (`files/music/` =
genres.yaml, lyrics, planner, prompts, scripts), so the video stage has no visual template
in-cluster, and the blueprint fix in §6 must ship in the payload to reach the CronJobs.
Reported on the existing payload card **t_a14e5d52** (nexus-core) and the ops path card
**t_75aacf8b**.

## 10. The generation entry for this track

Canonical fields match the `music-pipeline` brief schema
(`{name, genre, brief, lyricsMode?, language?, title?, duration?}`), so the entry can join
the shared queue unchanged.

```json
{
  "name": "epic-orchestral-boss-the-last-gate",
  "genre": "epic-orchestral-boss",
  "brief": "The Last Gate. A gate that has not opened in a thousand years opens once: the dread of what is behind it, the escalation of what walks through, and the silence in which the music decides whether the world ends. Three-act hybrid orchestral boss cue, 150 BPM in C minor, choir as the weapon.",
  "title": "The Last Gate",
  "lyricsMode": "draft",
  "language": "la",
  "duration": 240
}
```

- `lyricsMode` **must stay `draft`**. `ai` writes lyrics for a track whose claim rides on
  human authorship; it is forbidden here.
- `duration` 240 s = 150 bars at 150 BPM (§4).
- `instrumental` is **not** set — this is a choral track (§6). If a future schema adds the
  field, it must be `false` for this genre.
- Planned out: `/var/lib/music-plans/epic-orchestral-boss-the-last-gate.json`; render via
  `music-pipeline-render`; engine `ace`.

Queueing is a GitOps change in `mining-k8s` (`values.yaml` `briefs:`), so it is handed off,
not done here: card **t_78bd4754** (nexus-core).

## 11. Decisions locked here so later stages do not re-litigate

1. **Two deliverables, one master.** The showpiece master keeps the three-act form and the
   hard-cut ending. A separate **64-bar (102.4 s) loop edit** of Act II serves `game-assets`
   and carries the `loop_points.json` (§3 L1).
2. **Video shape is `single-4min`** for this genre, whatever the lane declares (§3 L2).
3. **`instrumental.wav` = orchestral bed without choir**, derived from the choir stem, not a
   copy of the master (§3 L3).
4. **Choir, not "instrumental, no vocals"** — the caption must not gain that steering text
   (§6).
5. **150 BPM, C minor, 240 s, 8 sections** — the genre's own anchors; 156 BPM and 100 BPM
   are defects, not variants (§8c, §8d).
6. **Lyrics come from a human, in Latin-esque chant**, ≥ 25 distinct tokens, no
   parenthetical-only sections, one sheet covering all 8 sections (§6).
7. **Stems are mandatory** (sync + game-assets). Master loudness: -14 LUFS for `streaming`,
   -16 LUFS for `sync` — the same master cannot satisfy both within ±1 dB, so the `sync`
   deliverable gets its own normalisation pass.
8. **Nothing publishes itself.** All four lanes are `advisory`; every release is a proposal
   with evidence and j_kro approves.

## 12. Next stage

Stage `brief` is complete. Next: `genre-select`. Two prerequisites sit before the lyrics
stage and both are handed off: the lyric blueprint (§6, payload change) and the queue entry
(§10, GitOps). Neither blocks `genre-select`.

## 13. Provenance

- Registry: `music/genres.yaml` (epic-orchestral-boss block, lines 127–133),
  `music/lanes.yaml`, validated live: 14 genres, 10 lanes
- Template: `music/prompts/epic-orchestral-boss.md` (4525 B) — caption 640 chars, 8 sections,
  weirdness 40%, style influence 80%, 6 exclude terms, anchor 150 BPM / C minor
- Visual: `music/visuals/dark-fantasy.md` (1387 B); rendered `dark_fantasy.mp4` probed and
  gate-run
- Rubric: `music/rubrics/gamer.json` (family criteria `battle_energy`, `loop_safety`,
  `asset_packaging`, `loudness_target`; `pass_threshold` 7.0)
- Gates: `music/gates/` — measured in the pass: **10 `gate_*.py` + 2 `*.sh`** present, plus
  two private fixture modules (`_loop_fixtures.py`, `_visual_fixtures.py`). `gate_quota`,
  `gate_lyrics_original`, `gate_youtube_authentic` exercised live this stage and re-run in
  the pass. `check_gate_suite.sh` runs the suite; `music/gates/README.md` is the index.
- Planner: `music/planner/planner.py` (`MIN_DURATION_S=30`, `MAX_DURATION_S=420`,
  `load_blueprint`)
- Lyrics mechanics: `music/lyrics/lyrics.py` (`MIN_UNIQUE_WORDS=25`, `MIN_SECTIONS=2`,
  `KNOWN_SECTIONS`, `cmd_scaffold`, `unique_word_count`)
- Engine: deployment `sunolocal-source` v0.1.2, `sunolocal/translate.py` (read from the pod),
  `music/scripts/acestep_plan.py`
- Live route: chart `music-pipeline`, ConfigMap `music-pipeline-briefs`, CronJobs
  `music-pipeline` / `music-pipeline-render`, host dir `/var/lib/music-plans`,
  `mining-k8s/helm/charts/music-pipeline/{values.yaml,files/,check-payload-sync.sh}`
- Autonomy: `music/autonomy.yaml` (all lanes `advisory`, `0/0/0`)
- Oracle: `music/oracle.py` (`WEIGHTS`, `cadence_fit_score`) — measured today, `1/wk`
  scores **0.0** with 14 days left in the period (`weeks_remaining` 2.0, `expected_tracks`
  2.0); the card records 1.7 from the 2026-10-09 scoring wave. The duplicate card carries
  7.75. Both resolve to this brief. Re-computed in the pass with `oracle.WEIGHTS`: the
  survivor's components total **7.555 → 7.55** and the duplicate's **7.755 → 7.75** — the
  two differ only in `trend_signal` (3.0 vs 5.0), so the duplicate's higher score is not a
  better genre and nothing needs re-scoring.
- **Repo state (measured 2026-10-16 13:38):** local `main` = `afa242e`, **22 commits ahead**
  of the merge base with `origin/main` = `ba28f55`, 15 behind (`git rev-list --left-right
  --count main...origin/main` → `22  15`). `origin/main` carries `music/suno-gen.py` and
  `music/sunolocal/`; this checkout carries neither. `music/scripts/check_stage_scripts.py`
  (commit `7f2ded8`) stays **red** on exactly that
  (`FAIL … 1 of 11 referenced path(s) absent … music/suno-gen.py … CHECKOUT DIVERGENCE`), so
  the gap cannot go quiet; the merge is owned by `t_8a715681`. Both are facts about the
  checkout, not about this brief's artifacts.
- **Checks added by neighbouring passes:** `music/scripts/check_stage_scripts.py` (`7f2ded8`)
  and, from this pass, `music/scripts/check_brief_paths.py` — a brief that cites
  `mining-k8s/...` must have that citation resolve under `$HOME`, and the pass fixed this
  brief's ambiguous paths (§14).
- **Dangling reference (unchanged):** `brain/playbooks/music-lane-architecture.md` and
  `brain/research/music-monetization-2026.md` are cited by this lane's profile, `stages.yaml`,
  `genres.yaml`, `lanes.yaml`, `autonomy.yaml`, `gates/README.md`, `gates/*.py` and
  `rubrics/gamer.json` (`"arch"` source) but do not exist on this machine. Section numbers
  quoted from them cannot be checked. Filed as t_b0a4db92.

## 14. Verification pass — the duplicate card `t_67fc5307` (2026-10-16 13:42)

This brief is keyed by **genre**, so the twin oracle card `t_67fc5307` (`music-oracle:
epic-orchestral-boss (score 7.75)`, the 2026-10-09 03:37 wave) resolves to this same file.
That card **wrote no second brief and started no second stage chain**. The surviving queue
handoff is `t_78bd4754` (assignee `nexus-core`, `ready`, created 13:17:40), already created
from the survivor `t_2a798908`. Nothing was re-scored; no registry value, gate, plan or
cluster config was changed.

Every checkable claim was re-measured against live state. Results:

| Claim (section) | Re-measured how | Result |
|---|---|---|
| `registry OK: 14 genres, 10 lanes`; ledger period 2026-10, 0/60, warn 55, hard 58 (§1) | `/usr/bin/python3 music/registry.py validate` | reproduced, rc=0 |
| Template 4525 B, caption **640** chars, the 8 sections in order, weirdness 40%, Style Influence 80%, 6 exclude terms (§2, §4) | `wc -c`, `awk length`, `grep`, tag grep | reproduced exactly |
| Payload copy byte-identical (§1) | `cmp` against `/home/j_kro/mining-k8s/...` | identical — **but the bare `mining-k8s/...` path resolves nowhere inside the lane repo**; root now stated in §1 |
| `dark-fantasy.md` 1387 B; `dark_fantasy.mp4` 1280x720 / 25 fps / 5.0 s / 14552 B (§5) | `wc -c`, `ffprobe` | reproduced |
| `gate_youtube_authentic` FAILs the 5 s render with 2 distinct signatures; the album render fails with 4 (§5) | gate run on both | reproduced, rc=1 both |
| `MIN_STEMS = 4`; loop ratio PASS ≤ 3.0 (clean 1.6 / slip 6.0); `TARGETS {"streaming": -14.0, "sync": -16.0}` tolerance 1.0; ISRC `^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$` (§3) | grep of the four gate sources | reproduced |
| 8 of 14 templates declare the instrumental path; this genre **0** (§6) | `grep -Eci 'is instrumental\|leave the lyrics box empty\|lyrics box empty'` over all 14 | reproduced, name by name |
| Deployed `translate.py` lists this genre as instrumental (D3) | read from the running pod | reproduced verbatim |
| style_weight 0.80 → **156** BPM; 0.75 → **150** BPM; `key` = the 640-char caption (D1, D2, §8c) | pod package copied out and imported, run with the real caption | reproduced (156 / 150; `key_chars` 640; `key == caption`) |
| Instrumental variant: caption **665** chars, tail `…cinematic scale, instrumental, no vocals`, `lyrics='[Instrumental]\n'` (§6, §8c) | same probe | reproduced exactly |
| Template tag sheet → 8 sections, **3 empty `['Choir','Instrumental','Choir']`** (§8c, D5) | `acestep_plan.py`'s regex (the splitter's real home; `translate.py`'s dict has no `sections` key) | reproduced |
| **NEW** planner scaffold → **8 of 8** sections empty; refusal fires (§8d, D5) | planner run, then `acestep_plan.check_lyrics(plan, allow_empty=False)` | `FATAL: 8 section(s) have no lyrics: Intro, Choir, Build, Instrumental, Choir, Breakdown, Chorus, Outro.` — the "3 of 8" hole belongs to the raw sheet, not the scaffold |
| `[Choir]` absent from `KNOWN_SECTIONS`; `--strict` fails (§6, D4) | gate run with `--strict` | reproduced: `unknown section tag [Choir] (not a Suno metatag)` ×2 |
| Hyphenated chant splits at the hyphen (§6) | `unique_word_count` on `"for-tis as-tra"` = **4** vs **3** unhyphenated | reproduced |
| Planner dry-run: 8 sections in order, **100 BPM · C minor · 4/4**, 240 s, `language: en`, `validation: PASS`, `"blueprint": false` (§8d) | `planner.py plan … --duration 240` | reproduced verbatim |
| `sunolocal-source` 1/1, image `localhost/sunolocal:v0.1.2`; `/health` `{"status":"ok"}`; models `ace`/`yue2`; ClusterIP `10.43.164.190:8123` (§8a) | `kubectl get deploy/svc -o wide`, `curl` | reproduced |
| CronJobs `17 */6 * * *` and `41 */4 * * *`; ConfigMap queue holds `smoke-chill-lounge` only; chart `briefs: []` (§8b) | `kubectl get cronjob`, ConfigMap jsonpath, `grep values.yaml` | reproduced (job ages now given as names + creation offsets) |
| `/var/lib/music-plans/`: three plans; `.rendered` markers `refused`, `refused`, empty (§8b) | `ls -l` | reproduced |
| `check-payload-sync.sh` defaults to the dead `~/Projects/ai-content-pipeline`; with the right `SRC` DRIFT on `planner.py` + `acestep_plan.py`; payload carries no `music/visuals/**` (§9 D6) | script run both ways, `ls files/music/` | reproduced (the default-`SRC` run additionally reports `genres.yaml`) |
| `oracle.cadence_fit_score("1/wk")` = **0.0** today (§13) | direct call | reproduced |
| Both cards are one genre: 7.555 → 7.55 and 7.755 → 7.75, differing only in `trend_signal` (§header, §13) | weighted sum with `oracle.WEIGHTS` | reproduced; no re-scoring needed |
| Blueprints absent (only `activist`, `chill-lounge`, `trance`); lyric sheets for those three only (§6, §7) | `ls music/lyrics/blueprints`, `ls music/lyrics` | reproduced |
| Every cross-referenced card exists (§9) | board read (`sqlite3 -readonly`) | `t_25a6499c`, `t_bc6a0c00`, `t_a14e5d52`, `t_75aacf8b`, `t_78bd4754`, `t_b0a4db92`, `t_9546841b` — all `ready`, all carrying this genre's evidence |

### Corrections applied by this pass

1. **§1 — the payload citation had no root.** `mining-k8s` is a second checkout
   (`/home/j_kro/mining-k8s`). Resolved from the lane repo the cited payload path looks
   missing, which is how the pass found it (`cmp` → "No such file or directory"). The brief
   now names the root, and §1 says the same for every later reader.
2. **§8b — relative job ages replaced with job names.** "56 m ago" was true when written and
   decays; the names `music-pipeline-29869517` / `music-pipeline-render-29869541` and their
   creation offsets are stable.
3. **§8c/§8d — the section splitter named, and the scaffold measured.** The brief implied the
   section list came from the engine translation; it comes from `acestep_plan.py`'s regex.
   With that named, the same probe shows the planner's *own scaffold* reports 8 of 8 sections
   empty and is refused — the D5 wrapped-parenthetical hole is narrower than the §8c wording
   suggests.
4. **§13/§1 — repo and check census refreshed.** `main` moved `d491663` → `061b5dc` →
   `afa242e` within the hour; divergence is now 22 ahead / 15 behind (owned by `t_8a715681`);
   the gate directory census is exact (10 `gate_*.py` + 2 `*.sh` + 2 fixture modules).

### Regression check added (FAILURE → TEST)

The citation defect above is now guarded: `music/scripts/check_brief_paths.py` (new in this
pass) fails if any `mining-k8s/...` citation in any brief resolves nowhere under `$HOME`, and
warns when a brief cites that checkout without naming its root. Measured on this tree, before
this pass's §1 fix (which clears the second warning):

```
$ /usr/bin/python3 music/scripts/check_brief_paths.py
PASS check_brief_paths: 13 `mining-k8s/...` citation(s) across 14 brief(s) resolve under /home/j_kro
  WARN music/briefs/activist.md: cites `mining-k8s/` without naming the checkout root ...
  WARN music/briefs/epic-orchestral-boss.md: cites `mining-k8s/` without naming the checkout root ...
  WARN music/briefs/sentimental-piano/room-with-the-light-going/brief.md: cites `mining-k8s/` ...
rc=0
```

The second warning is cleared by this pass's own §1 fix. The other two briefs belong to
`t_ace3bfb1` (activist) and `t_9f7d6889` (sentimental-piano); they are one-line fixes for
whoever next touches those files, and this pass did not edit another card's artifact. It
deliberately does **not** assert that every cited path exists — briefs legitimately cite
artifacts that must not exist yet (the absent blueprints, the unbuilt `music/assets/` and
`music/publish/` trees).

### Not fixed here (already owned, no new cards)

`t_25a6499c` (deployed engine: BPM/key/instrumental comment — D1–D4), `t_bc6a0c00` (draft
guard, D5), `t_a14e5d52` + `t_75aacf8b` (payload drift + the `SRC` default, D6),
`t_78bd4754` (queue this brief), `t_8a715681` (checkout divergence), `t_bf0e5edd` (oracle
duplicate-card sweep), `t_b0a4db92` (the dangling `brain/` citations). One further
un-filed observation, recorded rather than carded because it is prose, not behaviour:
`music/gates/gate_release_ready.py`'s docstring claims it enforces "the ISRC check digit
(ISO 3901)"; the code enforces shape only (§3).

hotspot: `/home/j_kro/ai-content-pipeline/music/briefs/` — the 14 briefs under it were
written and re-verified by ~8 concurrent `music-producer` workers on 2026-10-16; every write
needs a path-scoped commit and a lock retry. This file has two commits, both on this genre.
