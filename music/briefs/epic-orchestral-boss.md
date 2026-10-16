# Brief — epic-orchestral-boss

> **Stage:** `brief` (`music/stages.yaml`: `brief` → bot `producer`) — DELIVERED; the chain
> resumes at `genre-select` (§12).
> **Surviving card:** `t_bbe26b75` (`music-oracle: epic-orchestral-boss (score 7.5)`) — the one
> open card for this genre. `music/scripts/check_oracle_board.py` reports
> `epic-orchestral-boss → t_bbe26b75` and one open card per genre (rc=0, re-run in this pass).
> Its surviving-card pass re-measured every checkable claim on 2026-10-16 16:00 (CDT) — see §15.
> **Superseded cards:** `t_2a798908` (score 7.55, done) wrote this brief; `t_67fc5307`
> (score 7.75, done) was its duplicate from the second oracle wave (§14). Briefs in this lane
> are keyed by **genre**, not by card, so all three cards resolve to this one file.
> **Written:** 2026-10-16T13:16-05:00 (CDT), music-producer
> **Verified (duplicate-card pass, `t_67fc5307`):** 2026-10-16T13:42-05:00 (CDT) — see §14.
> The pass re-measured every checkable claim and fixed four: §1 (the payload checkout
> root — `mining-k8s/...` is relative to `$HOME`, not to this repo), §8b (job ages
> replaced with job names), §8c/§8d (the section split's real source, and the scaffold's
> 8-of-8 empty result), §13 (tip, divergence, gate census). Pre-pass revision:
> `sha256 fcf97717…`, 542 lines. New regression check:
> `music/scripts/check_brief_paths.py`.
> **Verified (surviving-card pass, `t_bbe26b75`):** 2026-10-16T16:00-05:00 (CDT) — see §15.
> Fourteen claims had aged while the shared tree moved `afa242e` → `c296db6`; every one of them
> is corrected in place in this revision. Superseded revision:
> `sha256 22a596a42832aae7a36583cf1c2b31871c0779bfb530602cd7a51d772ef14e9c` (44182 B, 691
> lines, written 13:43). The current digest re-reads with
> `sha256sum music/briefs/epic-orchestral-boss.md`.
> **Rubric size re-measured (card `t_6dd13d76`, 2026-10-16T17:21-05:00 CDT):** the family
> rubric `music/rubrics/gamer.json` reads 12 444 bytes (12 428 characters) on disk now — it
> grew again after the 12 000-byte rewrite the surviving-card pass recorded. §1 and §13 are
> corrected in place. Superseded revision of this file:
> `sha256 7bc9752f68011a6dbeb4ef5a3b9c78828f842d7592c300500a0d2bbd38e472bc` (948 lines /
> 65354 B).
> **Repo:** `/home/j_kro/ai-content-pipeline` — the lane repo. Its `main` tip at write time
> was `d491663`, then `afa242e` (13:38), then `c296db6` (16:00) — this lane commits
> constantly, so the tip is a timestamp, not an identity. Re-measured 16:00:
> `git rev-list --left-right --count main...origin/main` → `72  0` (the divergence that §13
> used to record is closed). **`/home/j_kro/mining-k8s` is a second checkout**; every
> `mining-k8s/...` citation below is relative to `$HOME`.
> **Oracle true score: 7.3/10** (oracle dedupe ruling, `music/oracle.py` @ `b2d11f7`) — quota
> headroom 10.0, lane coverage 8.0, revenue potential 10.0, cadence fit **0.0**, policy risk
> 9.0, trend signal 3.0. The weighted sum re-computed with `oracle.WEIGHTS` in this pass is
> 7.3; the card titles' 7.5 / 7.55 / 7.75 are that 7.3 plus the failed-fetch and
> stale-calendar premiums (§15.1). Threshold 5.0 → produce.
> **Genre class:** **choral vocal** (choir/chant, no solo singing). NOT instrumental —
> see §6, which corrected a live claim in the deployed engine; that claim is now fixed
> upstream (§15.2).

Every number, quoted string and verdict below comes from a command run or a file read
during this stage. Nothing here is recalled.

## 1. Genre resolution (live)

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

That transcript is the live output of the surviving-card pass (2026-10-16T16:00 CDT). It
gained one clause and one line since the earlier revisions wrote it: the header now counts
`1 stage gate rule(s)`, and the board declares a stage gate for the `visual` stage. The rule
reads *a genre that carries a YouTube lane gets `gate_youtube_authentic`; where the lane is
absent the answer is `none`* — this genre has a YouTube lane (`youtube-gaming`), so the rule
applies to it.

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
| Family rubric | `music/rubrics/gamer.json` (12444 bytes), `pass_threshold` 7.0 |
| Lyric blueprint | `music/lyrics/blueprints/epic-orchestral-boss.yaml` — **PRESENT**, 7073 bytes (§6) |
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

- `gate_sync_ready` — exercised live against an empty package in this pass: **14 findings** for
  `sync`, **16** for `game-assets`. It demands `full_mix.wav`; **≥ 4 stems** (`MIN_STEMS`),
  each within ±0.5 s of the master; `instrumental.wav`; `manifest.json` with a `metadata`
  object carrying `title, artist, bpm, key, mood, genre`; a non-empty `clearance_doc.pdf`/`.txt`;
  a non-empty `ai_disclosure.txt`. The `game-assets` lane adds `sample_rate`, a
  `pack_manifest` count object whose `loops`/`stems` counts must match the files on disk, and
  `loop_points.json`, plus a `LICENCE.txt` (architecture §13: explicit permitted use,
  distribution and derivative-work rules).
- `gate_loop_points` — does not trust `loop_points.json`; it renders the seam
  (tail window + head window, 3.0 s default) and PASSes when junction curvature ÷ body
  curvature ≤ 3.0 (`CLICK_RATIO_MAX = 3.0`). Documented separation: a clean synthetic loop
  measures 1.6x, a half-period phase slip 6.0x.
- `gate_release_ready` — exercised live against an empty package in this pass: **4 findings**
  (`no master.wav`, `no artwork`, `no manifest.json`, `no ai_disclosure.txt`). Requires
  `master.wav`; `artwork.jpg|jpeg|png`; `manifest.json` with `title, artist, isrc, genre`;
  non-empty `ai_disclosure.txt`. ISRC must match
  `^[A-Z]{2}[A-Z0-9]{3}\d{2}\d{5}$` — 12 characters, **no check digit** (verified in the
  pass: `ISRC_RE` plus `isrc_syntax()` test shape only — 2 letters, 3 alphanumeric, 2-digit
  year, 5-digit designation; there is no checksum to fail. The gate's own docstring claims it
  enforces "the ISRC check digit (ISO 3901)", which the code does not do. A shape-valid but
  invented ISRC passes. Doc-vs-code gap, recorded here, not filed as its own card).
- `gate_loudness` — `TARGETS = {"streaming": -14.0, "sync": -16.0}`, tolerance 1.0 dB.
  **Ruler, measured in this pass:** the file on this checkout still measures
  `ffmpeg -af volumedetect` `mean_volume` — a plain RMS mean, not gated LUFS — and says so in
  its own NOTE. The migration to EBU R128 integrated loudness that `t_9546841b` implemented
  (commit `e783a96`) is committed on **`origin/publish/audio-lane-2026-10-16`** and is *not*
  on `main` or `origin/main` (`git show <branch>:music/gates/gate_loudness.py | grep -c
  'ebur128='` → 2 on that branch, 0 here). `music/mix/master.py` (`t_568c67d2`, commit
  `6824709`) is absent from this checkout for the same reason: both live on the publish
  branch. Whoever runs the `mix`/`master` stage must read the ruler from the branch it will
  run from.
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
same way with 4 distinct signatures; re-measured in the surviving-card pass, unchanged.) The
shape-matched render is now on disk too: `music/visuals/single_4min.mp4` — 1280x720, 25 fps,
**240.0 s**, 2896696 bytes — and it fails the same gate with **4** distinct signatures and no
disclosure file. So the `visual` stage must render real motion for this 240 s showpiece and
place a disclosure file beside it. The 5 s template render is a colour reference, not a
deliverable, and a longer static dump is not a deliverable either.

## 6. Lyrics — the genre is CHORAL, not instrumental

This is the one structural place where the live pipeline contradicted this genre. It was
recorded here as a measured fact, and the deployed engine has since been fixed (§15.2).

**What the deployed engine said at the time.** From the running pod
(`kubectl -n mining exec deploy/sunolocal-source -- cat
/opt/sunolocal/music/sunolocal/translate.py`, then image tag `localhost/sunolocal:v0.1.2`):

> "8 of the 14 genre templates are instrumental (chill-lounge, sentimental-piano,
> commentary-beds, the four elementals, chiptune-8bit, **epic-orchestral-boss**); this is
> the path that lets them render at all."

That list named 9 names under a count of 8, and the last name was wrong.

**What the deployed engine says now** (pod `sunolocal-source-75d58dbc97-7jfmc`, image
`localhost/sunolocal:v0.1.3`, re-read in the surviving-card pass):

> "8 of the 14 genre templates are instrumental; this is the path that lets them render at
> all: chill-lounge, chiptune-8bit, commentary-beds, elemental-air, elemental-earth,
> elemental-fire, elemental-water, sentimental-piano … The previous list here named NINE by
> wrongly including epic-orchestral-boss, whose template declares no instrumental path
> ("Choir only — no solo lyrical singing") — routing it down this branch would strip its
> defining element (card t_25a6499c)."

The count and the eight names now agree, and this genre is not among them. Measured with
`grep -Ei 'is instrumental|leave the lyrics box empty|lyrics box empty'` over all 14
templates (counts are LINES matched, the convention `grep -c` uses):

```
activist.md 0   anime-ending.md 0   anime-opening.md 0   chill-lounge.md 1
chiptune-8bit.md 1   commentary-beds.md 1   elemental-air.md 1   elemental-earth.md 1
elemental-fire.md 1   elemental-water.md 1   epic-orchestral-boss.md 0
jungle-dnb.md 0   sentimental-piano.md 1   trance.md 0
```

`sentimental-piano.md` matches 2 occurrences on 1 line, so an occurrence count reads 2 and a
`grep -c` line count reads 1; the census of *templates that declare the path* is 8 either way.

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
deliverables, no authorship claimed). **Re-run in the surviving-card pass** — both probe
files are still under the pass's scratch dir, and the verdicts reproduce:

```
$ /usr/bin/python3 music/gates/gate_lyrics_original.py --lyrics-file <8-tag chant probe>
FAIL gate_lyrics_original
  - only 18 unique words; 25 required
  - only 18 unique words (minimum 25)
rc=1

$ /usr/bin/python3 music/gates/gate_lyrics_original.py --lyrics-file <same> --strict
FAIL gate_lyrics_original
  - only 18 unique words; 25 required
  - only 18 unique words (minimum 25)
rc=1

$ /usr/bin/python3 music/gates/gate_lyrics_original.py \
      --lyrics-file <the template's own lyric block>
FAIL gate_lyrics_original
  - [Intro] placeholder guidance left in: '(sub-drone, distant metallic echoes, whispered choir breaths'
  - [Intro] placeholder guidance left in: 'heartbeat pulse)'
  - [Choir] placeholder guidance left in: '(low male chant murmurs, one held chord, no drums)'
  ... 14 findings in total, one per direction line and wrapped continuation
rc=1
```

Read off those runs: the chant probe's FAIL is the **unique-word floor**, not the section
tags — the `--strict` invocation adds nothing, because `[Choir]` is a known tag (§D4 is
fixed). The template's own block FAILs on **14** placeholder-guidance findings — one per
direction line *and* per wrapped continuation line — which is the same rule the renderer's
`check_lyrics` applies (§8c). The floor and the verdicts are the load-bearing facts.

Three hard requirements follow, plus one defect that is now closed:

- **≥ 25 distinct tokens** (`MIN_UNIQUE_WORDS = 25` in `music/lyrics/lyrics.py`; the gate
  imports the same constant). The tokenizer is `WORD_TOKEN_RE` — Latin words (`[a-z']+`) plus
  a kana/kanji class, so the sheet stays measurable in a non-Latin script. It **splits at the
  hyphen**: re-measured in this pass, `unique_word_count([("Choir", ["for-tis as-tra"])])` =
  **4**, and the same syllables written as separate words (`"for tis as tra"`) = **4** too,
  while `"for-tis astra"` = **3** and the un-hyphenated, unspaced form `"fortis astra"` = **2**.
  The reproducible rule is: a hyphen manufactures tokens, so write chant words unhyphenated
  and count the floor on the words the sheet really states. A five-word "Fortis Astra Dominus"
  chant repeated eight times FAILS this gate.
- **No parenthetical-only lines** in any section: they are rejected as "placeholder guidance
  left in". Every Choir/Build section needs real chant lines.
- **≥ 2 content sections** (`MIN_SECTIONS = 2`) and the 8 template sections in order.
- **Defect D4 — CLOSED.** `[Choir]` was missing from `KNOWN_SECTIONS` in
  `music/lyrics/lyrics.py`, so `--strict` failed this genre's mandated structure. Re-measured
  in this pass: `KNOWN_SECTIONS` now lists `"Choir"` (between `"Vamp"` and `"Outro"`), and the
  `--strict` invocation on the chant probe returns the unique-word findings only — no
  unknown-tag finding. Fixed under card `t_25a6499c`.

**Prerequisite for the lyrics stage — DELIVERED.** `music/lyrics/blueprints/epic-orchestral-boss.yaml`
now exists: **7073 bytes**, authored by card `t_78bd4754` (lane commit `59c6e78`, copied into
the chart payload). Re-measured in this pass: it carries the four fields `lyrics.py cmd_scaffold`
requires (`family`, `theme`, `title_candidates`, `structure`), plus `bpm_anchor: 150` and 20
`mood_words`, and its eight `structure` tags equal the template's eight tags **in order**
(`Intro, Choir, Build, Instrumental, Choir, Breakdown, Chorus, Outro` — compared programmatically).
`lyrics.py cmd_scaffold --genre epic-orchestral-boss` therefore no longer refuses with
`FAIL: no lyric blueprint for '<genre>'`, so the lyrics stage can start. Blueprint census on
disk at 16:00: **7 of the 14 genres** (`activist`, `anime-ending`, `anime-opening`,
`chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`, `trance`; `jungle-dnb.yaml` is still
untracked in the lane tree). `planner.py:load_blueprint`'s docstring read
"(3 of 15 genres do)" — a stale docstring, not a behaviour: the loader reads the directory. Card
`t_a54fb00d` corrected that figure to "(7 of 14 genres do)" on 2026-10-16; the deployed payload
copy of the same function picks the correction up at the next `sync-payload.sh`.

## 7. Existing assets for this genre

Measured, not assumed.

- `music/lyrics/` holds sheets for `activist/what-runs-beneath`, `chill-lounge/amber-hour`,
  `trance/signal-before-dawn` and `anime-opening/becoming` (each a directory with
  `lyrics.txt`/`lyrics.suno.txt`/`title.txt`). Still **no epic-orchestral-boss sheet**, so
  `gate_lyrics_original` has nothing of this genre's to pass yet — the lyrics stage writes it.
- The lyric blueprint now exists (§6), so the stage that writes that sheet is unblocked.
- **A plan for this genre exists on disk.** `/var/lib/music-plans/epic-orchestral-boss-the-last-gate.json`
  is **3910 bytes**: `bpm` 150, `key` `C minor`, `duration` 240, `language` `la`,
  `instrumental` false, and `"_meta": {"blueprint": true, "lyrics_mode": "draft"}` — the plan
  agrees with this brief. Its marker
  `/var/lib/music-plans/epic-orchestral-boss-the-last-gate.rendered` reads **`refused`**, which
  is the correct verdict for a draft scaffold (§8b). No render, no master, no stems yet: the
  `generate`/`stems`/`mix` stages have not run for this genre. `/var/lib/music-plans/` now
  holds plans for 11 queued entries plus the 2026-10-09 `final-round` / `smoke-chill-lounge` /
  `testplan` trio. `~/Music` is still **empty** (0 files).
- `music/visuals/dark_fantasy.mp4` exists and is a 5 s placeholder; `single_4min.mp4` is the
  240 s static dump (§5).
- Quota is untouched (re-run in this pass):

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
$ kubectl -n mining get deploy sunolocal-source    -> 1/1 READY, image localhost/sunolocal:v0.1.3
     (pod sunolocal-source-75d58dbc97-7jfmc)
$ curl -s http://10.43.164.190:8123/health          -> {"status":"ok"}
$ curl -s http://10.43.164.190:8123/api/v1/models   -> {"engines":{"ace":{"kind":"ACE-Step 1.5",
     "via":"acestep_plan.py -> comfyui-zephyr window"},"yue2":{"kind":"YuE2-3B","via":"yue2-zephyr http"}},
     "default":"ace"}
```

Service `sunolocal` ClusterIP `10.43.164.190:8123`; `comfyui-zephyr` is Running in the same
namespace (NodePort `8188:32188`). The GPU stays on zephyr — no local model load, per lane
GPU rules. **The image tag moved `v0.1.2` → `v0.1.3`** between the earlier revisions and this
pass; v0.1.3 is the build that carries the explicit `bpm`/`keyscale` extensions (§8c, §9 D1/D2).

### 8b. The planning/render CronJobs (namespace `mining`)

| Stage | Job | Schedule | Input | Output |
|---|---|---|---|---|
| plan | `music-pipeline` | `17 */6 * * *` | ConfigMap `music-pipeline-briefs`, key `briefs.json` | `/var/lib/music-plans/<name>.json` |
| render | `music-pipeline-render` | `41 */4 * * *` | plans with no `.rendered` marker | audio via `/payload/music/scripts/acestep_plan.py` |

The live queue now holds **11 entries** (ConfigMap read at 16:00). This genre's entry is in it
(verbatim from the ConfigMap), and it carries the explicit `bpm`/`keyscale` the useful §8c
variant needs:

```json
{"bpm":150,"brief":"The Last Gate. A gate that has not opened in a thousand years opens once: …",
 "duration":240,"genre":"epic-orchestral-boss","keyscale":"C minor","language":"la",
 "lyricsMode":"draft","name":"epic-orchestral-boss-the-last-gate","title":"The Last Gate"}
```

The chart values and the ConfigMap no longer disagree: `mining-k8s/helm/charts/music-pipeline/values.yaml`
carries the same list (this genre's entry is commented `# Card t_78bd4754`), the Argo
Application override carries it too, and `helm/charts/music-pipeline/check-queue-sync.sh`
renders both and PASSes (`RESULT: PASS — the chart's values.yaml briefs match the
Application's override`). The "chart reads `briefs: []`" drift recorded in the earlier
revisions is closed. Both job histories are healthy and quiet. Newest of each series at
16:00: `music-pipeline-t6d7ad524` Complete (run 7 s, created 41 m before the read) and
`music-pipeline-render-t6d7ad524` Complete (run 2 m 26 s, created 41 m before the read).
The markers record what the queue produced: `smoke-chill-lounge.rendered` = `refused`,
`testplan.rendered` = `refused`, `final-round.rendered` = empty (rendered), and **this
genre's** `epic-orchestral-boss-the-last-gate.rendered` = `refused` — the draft guard
working (§8c).

Two different `--allow-empty` postures exist and must not be confused:
- the **CronJob render path** invokes `acestep_plan.py` **without** `--allow-empty`, so a
  draft plan with empty sections exits 1 and gets a `refused` marker;
- the **sunolocal adapter path** (`adapters/ace_comfy.py`) passes `--allow-empty`, so the
  same draft renders there with the empty sections read as a vocal-shaped hole.

### 8c. What this brief translates to, executed against the deployed code

The deployed `translate.suno_to_aceplan` was imported (copied out of the running pod, no GPU,
no network) and run with this genre's real 640-character caption. **Re-run in the
surviving-card pass against `v0.1.3`** — the numbers below are the live ones:

```
--- variant A, style_weight=0.80 (template Style Influence 80%), no explicit bpm ---
  bpm            : 156
  key            : 'C major'   (the DEFAULT key — no longer the caption)
  duration       : 30.0        (no explicit duration)
  caption chars  : 640

--- variant A2, style_weight=0.75 ---
  bpm            : 150

--- variant B, EXPLICIT bpm=150 + keyscale='C minor' (the live queue entry) ---
  bpm            : 150
  key            : 'C minor'
  duration       : 240.0

--- variant C, explicit bpm/keyscale, instrumental=True, lyrics empty ---
  caption chars  : 665   tail: '…at once, cinematic scale, instrumental, no vocals'
  lyrics         : '[Instrumental]\n'

--- variant D, no bpm, no keyscale, no style_weight (bare defaults) ---
  bpm            : 120
  key            : 'C major'
```

Read off that measurement:

- **The style_weight fallback still maps 0.80 → 156 BPM**, so the template's own Style
  Influence is still 1.04x fast *on that fallback path*. It no longer matters for this genre:
  `v0.1.3` gives an **explicit `bpm` precedence** over the fallback (`bpm = int(req.bpm)` when
  present), and the live queue entry carries `bpm: 150`. The plan on disk agrees (§7).
- **The key defect is fixed.** `key` now reads `req.keyscale or "C major"` — the default is
  a key signature, never `req.style`. Measured: variant A's `key` is 7 characters
  (`'C major'`), not the 640-character caption; variant B carries `'C minor'` because the
  queue states it. The old behaviour (`key = req.style`, so `acestep_plan.py` handed the
  whole style paragraph to the ACE node as `keyscale`) is gone; `v0.1.3`'s own comment names
  it as `t_25a6499c D2`.
- Whether ACE recovers a key from caption *text* is still **unverified** — it needs a render,
  which is the `generate` stage, not this one. Do not claim the render is broken.
- The empty-section note still matters for the lyrics stage, and it is now measured the same
  way on both sides. The `sections` list does **not** come from `translate.py` (the plan dict
  it returns no `sections` key); it comes from `music/scripts/acestep_plan.py`'s own regex
  `^\[([^\]]+)\][ \t]*\n(.*?)(?=\n\[|\Z)`. Fed the template's tag sheet verbatim, that regex
  returns **8 sections, 3 empty — `['Choir', 'Instrumental', 'Choir']`** by the raw `#`/`(`
  line test. The guard no longer uses that test: `acestep_plan.singable_lines()` now tracks
  **parenthesis depth**, so a direction that wraps across lines keeps its continuations out of
  the sung text. Re-measured in this pass on both the template's tag sheet and the planner's
  own scaffold, `check_lyrics(plan, allow_empty=False)` refuses both with the same verdict —
  **8 of 8 empty**:
  `FATAL: 8 section(s) have no lyrics: Intro, Choir, Build, Instrumental, Choir, Breakdown,
  Chorus, Outro.` The "3 of 8 hole" that D5 described is closed: wrapped direction lines are
  no longer counted as singable, and a sheet with real chant lines passes the same guard
  (measured: the pass's chant probe, `allow_empty=False` → no refusal). The `refused` marker
  on this genre's plan (§7) is that guard firing as designed.

### 8d. Planner dry-run (measured, no network)

```
$ /usr/bin/python3 music/planner/planner.py plan \
    --brief "the boss arena, three-act: dread, escalation, the false ending, then the wall of sound" \
    --genre epic-orchestral-boss --lyrics-mode draft --title "The Last Gate" \
    --duration 240 --out plan-epic.json
plan     : plan-epic.json
genre    : epic-orchestral-boss   lyrics_mode: draft
structure: Intro -> Choir -> Build -> Instrumental -> Choir -> Breakdown -> Chorus -> Outro
bpm/key  : 150 BPM · C minor · 4/4
duration : 240s   language: en
validation: PASS
next: write the lyrics into the plan, then run acestep_plan.py
```

The structure is the template's 8 sections, in order — correct. **BPM is now correct too:**
the earlier revisions measured `100 BPM · C minor · 4/4` with `"_meta": {"blueprint": false}`,
because the genre had no blueprint to anchor the tempo. Re-measured in this pass, with
`music/lyrics/blueprints/epic-orchestral-boss.yaml` on disk, the same command returns
**150 BPM** — read from the blueprint's `bpm_anchor`. The one remaining cosmetic wart is
**`language: en`**, the planner's default: `--language` only feeds the `ai` lyrics mode, which
this track must never use, and the **live queue entry sets `language: la`** instead (§8b), so
no downstream reader treats this track as an English vocal. The plan on disk also records
`"language": "la"` (§7).

## 9. Defects that blocked this genre downstream — all six closed (measured)

**All six defects are CLOSED.** The brief stage filed them; the lane closed them while this
brief sat on the board. Each row below is a live re-measurement from the surviving-card pass,
with the card that landed the fix.

**D1 — BPM is not expressible; the 150 BPM anchor cannot be honoured. CLOSED (`t_25a6499c`).**
Deployed `v0.1.2` hardcoded `bpm = 120` and its only override repurposed Suno's
*style-adherence* dial as a tempo control. Deployed **`v0.1.3`** now reads
`bpm = int(req.bpm)` when the request carries one, before the style_weight fallback; the
fallback survives as a documented fallback (§8c). The live
queue entry carries `bpm: 150` and the plan on disk records `bpm: 150`.

**D2 — the `key` field received the style caption. CLOSED (`t_25a6499c`).**
Deployed `v0.1.2` read `key = req.style or "C major"`, so `acestep_plan.py` handed the whole
640-character paragraph to the ACE node as `keyscale`. Deployed `v0.1.3` reads
`key = req.keyscale or "C major"` and says so in its own comment; measured: the key field is
7 characters, `'C major'`, and `'C minor'` when the request states it (§8c).

**D3 — the deployed comment misclassified this genre as instrumental. CLOSED (`t_25a6499c`).**
The `v0.1.2` comment named `epic-orchestral-boss` under a count of 8; the `v0.1.3` comment lists
the eight correctly and records that naming this genre was the error (§6). This genre's
template declares no instrumental path (0 marker matches).

**D4 — `[Choir]` is not a known section tag. CLOSED (`t_25a6499c`).**
`music/lyrics/lyrics.py:KNOWN_SECTIONS` now lists `"Choir"`; the `--strict` gate run on the
chant probe returns the unique-word findings only, with no `unknown section tag [Choir]`
finding (§6).

**D5 — the draft guard passed wrapped direction lines as lyrics. CLOSED (`t_bc6a0c00`).**
Both halves were fixed. The renderer's `acestep_plan.singable_lines()` now tracks parenthesis
depth, so a wrapped direction keeps its continuations out of the sung text; and the gate's own
`sung_lines()` applies the same rule. Measured: the template's tag sheet and the planner's
scaffold both now refuse with **8 of 8 empty** — the "3 of 8 hole" is gone (§8c) — and a sheet
with real chant lines passes. The regression test the card asked for is in the tree.

**D6 — the payload sync check compared against the wrong checkout. HALF CLOSED.** The script's
`SRC` default is fixed: re-run in this pass it reports
`source : /home/j_kro/ai-content-pipeline`, i.e. the lane repo, not the stale
`~/Projects` clone, so the false-DRIFT-for-every-file behaviour is gone. What remains is a real
drift, one file:

```
$ bash /home/j_kro/mining-k8s/helm/charts/music-pipeline/check-payload-sync.sh
source : /home/j_kro/ai-content-pipeline  (worktree <tip>)
ref    : origin/main = ba28f55
MISSING music/lyrics/blueprints/jungle-dnb.yaml   (the script's own word: the chart payload
                                                   has not copied that file yet)
RESULT: FAIL — run sync-payload.sh (SRC=/home/j_kro/ai-content-pipeline)
```

The two DRIFTs this brief first recorded (`planner.py`, `acestep_plan.py`) are gone, and the
payload now **does** carry `music/visuals/` (`files/music/` = genres.yaml, lyrics, planner,
prompts, scripts, **visuals**). The remaining `MISSING` entry is another genre's blueprint
(`jungle-dnb.yaml`, still untracked in the lane tree) and belongs to that genre's chain, not
this one; it is recorded here because the same script covers both. Cards `t_a14e5d52` and
`t_75aacf8b` are `done`.

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
- Planned out: `/var/lib/music-plans/epic-orchestral-boss-the-last-gate.json` **exists**
  (3910 B, §7); render via `music-pipeline-render`; engine `ace`.

**Queueing is DONE** (card `t_78bd4754`, `done`). The entry landed through the chain this
brief described as "handed off, not done here": it is in
`mining-k8s/helm/apps/music-pipeline.yaml` (the Argo Application override), in
`helm/charts/music-pipeline/values.yaml`, and in the live ConfigMap `music-pipeline-briefs`
(§8b). The same card authored the lyric blueprint (§6) and stated the tempo and key explicitly,
so the entry carries `bpm: 150` and `keyscale: C minor` in addition to the fields quoted above.
The first render attempt is on disk and its marker reads `refused` — the draft guard waiting
for the human-authored chant sheet (§7).

## 11. Decisions locked here so later stages do not re-litigate

1. **Two deliverables, one master.** The showpiece master keeps the three-act form and the
   hard-cut ending. A separate **64-bar (102.4 s) loop edit** of Act II serves `game-assets`
   and carries the `loop_points.json` (§3 L1).
2. **Video shape is `single-4min`** for this genre, whatever the lane declares (§3 L2).
3. **`instrumental.wav` = orchestral bed without choir**, derived from the choir stem, not a
   copy of the master (§3 L3).
4. **Choir, not "instrumental, no vocals"** — the caption must not gain that steering text
   (§6).
5. **150 BPM, C minor, 240 s, 8 sections** — the genre's own anchors. 150 BPM is now the
   measured planner output and the queued value (§8b, §8d); the 100 BPM reading came from the
   missing blueprint and is gone; 156 BPM survives only as the `style_weight` fallback, which
   an explicit `bpm` overrides (§8c).
6. **Lyrics come from a human, in Latin-esque chant**, ≥ 25 distinct tokens, no
   parenthetical-only sections, one sheet covering all 8 sections (§6).
7. **Stems are mandatory** (sync + game-assets). Master loudness: -14 LUFS for `streaming`,
   -16 LUFS for `sync` — the same master cannot satisfy both within ±1 dB, so the `sync`
   deliverable gets its own normalisation pass.
8. **Nothing publishes itself.** All four lanes are `advisory`; every release is a proposal
   with evidence and j_kro approves.

## 12. Next stage

Stage `brief` is complete. Next: `genre-select`. Both prerequisites that sat before the lyrics
stage are now **delivered**, not handed off: the lyric blueprint (§6 — in the lane repo and in
the chart payload) and the queue entry (§10 — in the Argo Application override, the chart
values and the live ConfigMap). What the lyrics stage still needs is the one thing only a
human authors: the chant sheet. The plan's `refused` marker is that requirement, enforced by
the renderer rather than stated as policy (§7).

## 13. Provenance

- Registry: `music/genres.yaml` (epic-orchestral-boss block, lines 127–133),
  `music/lanes.yaml`, validated live: 14 genres, 10 lanes
- Template: `music/prompts/epic-orchestral-boss.md` (4525 B) — caption 640 chars, 8 sections,
  weirdness 40%, style influence 80%, 6 exclude terms, anchor 150 BPM / C minor
- Visual: `music/visuals/dark-fantasy.md` (1387 B); rendered `dark_fantasy.mp4` probed and
  gate-run, plus the shape-matched `single_4min.mp4` (240.0 s, §5)
- Rubric: `music/rubrics/gamer.json` (**12444 B**, `version` 2, `pass_threshold` 7.0). The
  criteria are data now, each with an `applies_to` scope: "Boss/battle energy
  (elemental-fire, epic-orchestral-boss)" weight 3, "Loop safety for game use (all gamer
  genres)" weight 3, "Asset-pack packaging (stems, BPM/key metadata, naming)" weight 1,
  "Master hits the lane loudness target" weight 1, plus the chiptune and elemental-exploration
  criteria scoped to the other genres. Overall = weighted mean over the APPLICABLE criteria,
  aggregated across the panel as a geometric median. (The earlier revisions named the criteria
  `battle_energy`, `loop_safety`, `asset_packaging`, `loudness_target` — that was the pre-v2
  shape; the sub-idiom scope moved into data under card `t_426a82a3`.)
- Gates: `music/gates/` — re-measured in this pass: **10 `gate_*.py` + 2 `*.sh`** present, plus
  **four** private modules (`_lane_registry.py`, `_loop_fixtures.py`, `_pack_fixtures.py`,
  `_visual_fixtures.py`; the earlier revisions counted two). `gate_quota`,
  `gate_lyrics_original`, `gate_youtube_authentic`, `gate_sync_ready`, `gate_release_ready`
  exercised live in this pass. `check_gate_suite.sh` runs the suite; `music/gates/README.md` is
  the index.
- Planner: `music/planner/planner.py` (`MIN_DURATION_S=30`, `MAX_DURATION_S=420`,
  `load_blueprint` — which now finds this genre's blueprint, §6)
- Lyrics mechanics: `music/lyrics/lyrics.py` (`MIN_UNIQUE_WORDS=25`, `MIN_SECTIONS=2`,
  `KNOWN_SECTIONS` incl. `Choir`, `WORD_TOKEN_RE`, `cmd_scaffold`, `unique_word_count`)
- Engine: deployment `sunolocal-source` **v0.1.3** (pod `sunolocal-source-75d58dbc97-7jfmc`),
  `sunolocal/translate.py` (read from the pod), `music/scripts/acestep_plan.py`
- Live route: chart `music-pipeline`, ConfigMap `music-pipeline-briefs`, CronJobs
  `music-pipeline` / `music-pipeline-render`, host dir `/var/lib/music-plans`,
  `mining-k8s/helm/charts/music-pipeline/{values.yaml,files/,check-payload-sync.sh,check-queue-sync.sh}`
  and the Argo Application `mining-k8s/helm/apps/music-pipeline.yaml`
- Autonomy: `music/autonomy.yaml` (all ten lanes `advisory`, `0/0/0` — re-read in this pass)
- Oracle: `music/oracle.py` (`WEIGHTS`, `cadence_fit_score`) — re-measured today, `1/wk`
  scores **0.0** (14 days left in the period); the **true score is 7.3/10** under the oracle
  dedupe ruling (`b2d11f7`). The card titles' numbers are that 7.3 plus premiums: 7.5 = 7.3 +
  `WEIGHTS['trend_signal'] × (5.0 − 3.0)` (the old failed-fetch premium), and 7.55/7.75 carry
  the stale-calendar `cadence_fit` 1.7 as well. Re-computed in this pass with `oracle.WEIGHTS`:
  the ruling's components total **7.3**; adding the trend premium gives 7.5; adding
  `cadence_fit` 1.7 instead gives 7.555. See §15.1.
- **Repo state (measured 2026-10-16 16:00):** local `main` = `c296db6`, **72 commits ahead** of
  `origin/main` = `ba28f55`, **0 behind** (`git rev-list --left-right --count
  main...origin/main` → `72  0`). The divergence this entry used to record (22 ahead / 15
  behind, owned by `t_8a715681`) is **closed**: `origin/main` was merged as `ab33ad1`, and
  `music/suno-gen.py` (42652 B) plus `music/sunolocal/` are now **present in this checkout**.
  `music/scripts/check_stage_scripts.py` — which used to stay red on exactly that gap — is
  **PASS** (`11 referenced script path(s) all present`).
- **Checks added by neighbouring passes:** `music/scripts/check_stage_scripts.py` (`7f2ded8`)
  and, from the duplicate-card pass, `music/scripts/check_brief_paths.py` — a brief that cites
  `mining-k8s/...` must have that citation resolve under `$HOME`. The lane also added
  `check_brief_figures.py`, `check_brief_drift.py`, `check_brief_line_refs.py`,
  `check_oracle_board.py`, `check_oracle_determinism.py` and `check_gate_lane_surface.py`
  during the same window; all are re-run in §15.
- **Dangling reference — RESOLVED (`t_b0a4db92`).** `brain/playbooks/music-lane-architecture.md`
  and `brain/research/music-monetization-2026.md` (11067 B) are now on disk and in
  the `main` index; they were written 2026-10-08, stranded on `wip/atlas-backup-20261014`, and
  restored by ops mid-audit (`5a01157`). `music/scripts/check_doc_refs.py` re-run in this pass
  reports 24 headings, 32 citing files, 22 section references checked, and
  `OK: every section reference resolves to a heading in the doc`. Both docs are still **absent
  from `origin/main`**, so a fresh clone of `origin/main` would not have them — a fact about the
  remote, not about this brief.

## 14. Verification pass — the duplicate card `t_67fc5307` (2026-10-16 13:42)

This brief is keyed by **genre**, so the twin oracle card `t_67fc5307` (`music-oracle:
epic-orchestral-boss (score 7.75)`, the 2026-10-09 03:37 wave) resolves to this same file.
That card **wrote no second brief and started no second stage chain**. The surviving queue
handoff is `t_78bd4754` (assignee `nexus-core`, `ready`, created 13:17:40), already created
from the survivor `t_2a798908`. Nothing was re-scored; no registry value, gate, plan or
cluster config was changed.

**Read this section as a snapshot of 13:42, not as current state.** Its measurements were
correct when taken; the lane moved under them within the hour. §15 re-measured every one of
them at 16:00 and lists which changed (the blueprint, the rubric size, the queue, the engine
tag, the planner's BPM, the defect statuses) and which reproduced exactly.

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

**Status of that list at 16:00: every one of those cards is `done`** (board read, §15.3) —
and §15 records what each closure changed in this brief.

## 15. Surviving-card pass — card `t_bbe26b75` (2026-10-16 16:00 CDT)

This brief is keyed by **genre**, so the surviving open oracle card `t_bbe26b75`
(`music-oracle: epic-orchestral-boss (score 7.5)`) resolves to this same file. That card
**wrote no second brief and started no second stage chain**. It re-measured every checkable
claim against live state and corrected the ones that had aged while the shared tree moved
`afa242e` → `c296db6` and the lane closed the whole defect set (§9). The superseded revision of
this file is `sha256 22a596a42832aae7a36583cf1c2b31871c0779bfb530602cd7a51d772ef14e9c`
(44182 B, 691 lines, written 13:43); the current digest is printed by
`sha256sum music/briefs/epic-orchestral-boss.md`. No registry value, template, gate, plan,
blueprint, cluster config or queue entry was changed by this pass — the brief was corrected to
match them.

### 15.1 The oracle ruling this pass applies

The card title's **7.5** is not the genre's score. The 2026-10-09 double emission produced this
genre's cards within ten minutes of each other; the pairs differ by exactly
`WEIGHTS['trend_signal'] × (5.0 − 3.0)` = 0.20, the premium the old `except` branch paid to a
**failed** trend fetch. Fixed in `music/oracle.py` @ `b2d11f7`: a failed fetch and a working
fetch with no results both score the no-signal floor (3.0), so the number is reproducible
(`music/scripts/check_oracle_determinism.py`: FAIL rc=1 → PASS rc=0).

Re-computed in this pass with `oracle.WEIGHTS` and the ruling's components:

```
quota_headroom 10.0 × 0.25 + lane_coverage 8.0 × 0.20 + revenue_potential 10.0 × 0.20
  + cadence_fit 0.0 × 0.15 + policy_risk 9.0 × 0.10 + trend_signal 3.0 × 0.10   =  7.3
  + trend premium 0.10 × 2.0                                                    =  7.5   (this title)
  + stale cadence_fit 0.15 × 1.7 instead of 0.0                                 =  7.555 (t_2a798908)
```

`oracle.cadence_fit_score("1/wk")` = **0.0** today (14 days left in the period). The ruling
stands: **true score 7.3/10**, still above the 5.0 produce threshold, so the routing verdict is
unchanged — the number is corrected, not the decision. The rule applied: *the newest scoring run
owns the genre, and the higher-scoring twin is never automatically right* — an oracle score is a
function of live state plus a live web fetch, so an older number cannot be reproduced and cannot
win a tie. `music/scripts/check_oracle_board.py` reports one open card per genre, rc=0, with
`epic-orchestral-boss → t_bbe26b75`.

### 15.2 Corrections applied in this revision

| § | Claim as written | Re-measured live | Correction |
|---|---|---|---|
| hdr, §1 | `registry OK: 14 genres, 10 lanes` | `…, 10 lanes, 1 stage gate rule(s)` + a `stage gate visual:` line | transcript refreshed, clause explained |
| §1, §13 | `gamer.json` **6606 bytes** | **12000 bytes** (`8738a76` → `56dc465`, card `t_426a82a3`) | figure corrected in place |
| §1, §6, §7, §13 | lyric blueprint **ABSENT**; "only activist, chill-lounge, trance" | **present**, 7073 B, fields + 8 tags in order | prerequisite rewritten as delivered |
| §3 | `gate_sync_ready` requirement list | 14 findings (sync) / 16 (game-assets), incl. `pack_manifest` + `LICENCE.txt` | list replaced with the live findings |
| §3 | loudness ruler "contested: t_9546841b" | this checkout still measures `volumedetect`; `ebur128` lives on `origin/publish/audio-lane-2026-10-16` (`e783a96`) | measured state recorded with the branch |
| §5 | only the 5 s and album renders measured | `single_4min.mp4` (240.0 s) also fails with 4 signatures | added |
| §6 | deployed `translate.py` (v0.1.2) lists this genre as instrumental | `v0.1.3` lists the eight correctly and cites the fix | both readings recorded |
| §6 | chant probe: 13 unique words; template block: 3 findings | 18 unique words; **14** findings | outputs replaced with the live runs |
| §6 | hyphenation "4 vs **3**" | 4 vs 4 (spaced), 3 (`for-tis astra`), 2 (`fortis astra`) | irreproducible pair replaced |
| §6, §9 | "Defect D4 `[Choir]` unknown"; "the draft guard passes wrapped lines (D5)" | both fixed; `KNOWN_SECTIONS` has `Choir`; `singable_lines` tracks depth | marked CLOSED |
| §7 | "no plan, no render anywhere" | plan on disk (3910 B, `bpm` 150, `key` C minor, `_meta.blueprint` true), marker `refused` | replaced |
| §8a, §13 | image `v0.1.2` | `v0.1.3` (pod `sunolocal-source-75d58dbc97-7jfmc`) | corrected |
| §8b | queue holds one entry; chart `briefs: []` — drifted | **11** entries incl. this genre's (`bpm` 150, `keyscale` C minor); chart + Application + ConfigMap agree, `check-queue-sync.sh` PASS | replaced |
| §8c | `key` = the 640-char caption | `key` = `req.keyscale or "C major"` (7 chars measured) | D2 recorded as fixed |
| §8d, §11 | planner `100 BPM`, `"blueprint": false` | **150 BPM · C minor**, blueprint true | corrected |
| §9 | D1–D6 open, cards `ready` | all six closed; every card `done` | section retitled and rewritten |
| §10, §12 | queue + blueprint "handed off" | both delivered (`t_78bd4754` done) | statuses corrected |
| §13 | divergence `22 15`; `check_stage_scripts` red on `music/suno-gen.py` | `72 0`; `suno-gen.py` present; check **PASS** | corrected |
| §13 | gate census "10 + 2 + **2** fixture modules" | 10 + 2 + **4** private modules | corrected |
| §13 | rubric criteria `battle_energy`, … (4 names) | v2 data criteria with `applies_to` scopes | corrected |
| §13 | `brain/` docs "do not exist on this machine"; carried `t_b0a4db92` | both exist and `check_doc_refs.py` PASSes | resolved |

Claims that **reproduced unchanged** and were therefore left alone: the template (4525 B), its
640-character caption, the 8 tag sheet in order, weirdness 40% / Style Influence 80% / 6 exclude
terms, `lanes.yaml` lane→gate→requires→surface rows, `autonomy.yaml` (all lanes `advisory`,
`0/0/0`), `MIN_STEMS = 4`, `CLICK_RATIO_MAX = 3.0` (1.6x / 6.0x separation), the ISRC shape
regex, `TARGETS`/tolerance 1.0, `MIN_DURATION_S`/`MAX_DURATION_S`, the gate_youtube_authentic
thresholds, `dark-fantasy.md` (1387 B), `dark_fantasy.mp4` (1280x720 / 25 fps / 5.0 s / 14552 B,
2 signatures), the album render (4 signatures), the 8-of-14 instrumental census, the
instrumental caption variant (665 chars, `[Instrumental]\n`), `gate_quota` (0/60), `~/Music`
empty, the CronJob schedules, the `refused`/`refused`/empty marker trio, and
`oracle.cadence_fit_score("1/wk")` = 0.0.

### 15.3 Checks and card states read in this pass

```
$ /usr/bin/python3 music/registry.py validate            -> registry OK: 14 genres, 10 lanes, 1 stage gate rule(s)
$ /usr/bin/python3 music/gates/gate_quota.py             -> PASS (0/60, warn 55, hard 58)
$ /usr/bin/python3 music/scripts/check_brief_paths.py    -> PASS (15 `mining-k8s/...` citations resolve)
$ /usr/bin/python3 music/scripts/check_prompt_style_counts.py -> PASS (15 style-field lengths)
$ /usr/bin/python3 music/scripts/check_stage_scripts.py  -> PASS (11 referenced script paths present)
$ /usr/bin/python3 music/scripts/check_brief_bpm_solutions.py -> PASS (9 styleWeight claims)
$ /usr/bin/python3 music/scripts/check_brief_line_refs.py-> 5 findings, NONE in this brief
$ /usr/bin/python3 music/scripts/check_brief_drift.py    -> no finding in this brief (PASS at the edit run:
                                                            15 live counts, 0 behind / 73 ahead; sibling
                                                            briefs' counts move with every commit)
$ /usr/bin/python3 music/scripts/check_brief_figures.py  -> FAIL, 2 findings, BOTH in other briefs
                                                            (activist, elemental-water) — this brief's
                                                            figure was the third finding before the fix
$ /usr/bin/python3 music/scripts/check_oracle_board.py   -> PASS, epic-orchestral-boss -> t_bbe26b75
$ /usr/bin/python3 music/scripts/check_oracle_determinism.py -> PASS, determinism
$ /usr/bin/python3 music/scripts/check_doc_refs.py       -> OK, every section reference resolves
$ /usr/bin/python3 music/scripts/check_video_shapes.py   -> PASS (2 warnings, other genres)
$ /usr/bin/python3 music/scripts/check_stage_advance.py  -> PASS
$ /usr/bin/python3 music/scripts/check_gate_lane_surface.py -> PASS
$ /usr/bin/python3 music/scripts/check_scheduler_units.py-> PASS
```

Board read (`sqlite3 -readonly ~/.hermes/kanban/boards/music/kanban.db`): `t_25a6499c`,
`t_bc6a0c00`, `t_a14e5d52`, `t_75aacf8b`, `t_78bd4754`, `t_8a715681`, `t_b0a4db92`, `t_9546841b`
are all `done`; the genre's open card is `t_bbe26b75`; `t_34f496d7` (a corrections card for the
two `check_brief_figures` findings, this brief among them) is `todo`, gated on a blocked parent
— **its epic-orchestral-boss half is applied here**, so it will find the figure already
correct. Nothing was re-scored and no artifact outside this brief was touched.

### 15.4 Regression checks this pass leans on (FAILURE → TEST)

Every correction above is guarded by a check that already exists in `music/scripts/`, and each
was run after the edit: `check_brief_figures.py` (the rubric byte count), `check_brief_drift.py`
(unanchored counts), `check_brief_line_refs.py` (cited ranges), `check_brief_paths.py`
(`mining-k8s/...` citations), `check_prompt_style_counts.py`, `check_stage_scripts.py`,
`check_oracle_board.py` (one open oracle card per genre), `check_oracle_determinism.py` (the
failed-fetch premium that produced this card's 7.5). Nothing here was left to prose.

hotspot: `/home/j_kro/ai-content-pipeline/music/briefs/` — the 14 briefs under it were
written and re-verified by ~8 concurrent `music-producer` workers on 2026-10-16; every write
needs a path-scoped commit and a lock retry. This file's revisions are all on this genre, and
this pass adds one path-scoped commit that supersedes `22a596a4…`.

### 15.5 Code-prose census follow-up (card `t_a54fb00d`, 2026-10-16 17:31 CDT)

§6 above recorded `planner.py:load_blueprint`'s docstring `(3 of 15 genres do)` at `3967dea`, and
called it a stale docstring. Card `t_a54fb00d` corrected the repo's copy to `(7 of 14 genres do)`
at the 2026-10-16 17:31 CDT reading, live census then 14 registered genres and 7 files in
`music/lyrics/blueprints/`, and gave the class a check (`music/scripts/check_code_census.py`). No
figure in THIS file moved — the §6 census sentence is anchored to its own 16:00 reading — and the
deployed payload copy of the same docstring keeps the old figure until the next `sync-payload.sh`.

- **Superseded by this pass (card `t_a54fb00d`, 2026-10-16):** `sha256 c8fcacf49e949e17b56eaa8692113668b15541de7e89ff2e73f5b3b5ebf48fa7` (954 lines / 65 789 B).

## 16. Declared scoring scope — machine-checked against the live rubric (card `t_00ac4f10`, 2026-10-16)

`music/scripts/check_brief_rubric_scope.py` reads the `rubric_scope` block below and
compares it, field by field, to this genre's scope COMPUTED from `music/rubrics/gamer.json`
by the panel's own resolver (`music/rubrics/panel.py`: `applicable_criteria()`,
`applicable_signals()`). It FAILs when the criterion set, the weights, the weight sum, the
applicable reject signals or the rubric version disagree with the live file. The block is a
claim about NOW; the prose above keeps this family's pre-fix record (gamer v1: five
criteria, Σw 11, scope only inside a criterion NAME) and the check never reads prose, so
that record keeps passing.

Regenerate the block after any rubric edit — one command, no hand-edit:

    /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --print-truth epic-orchestral-boss

```json
{
  "rubric_scope": {
    "genre": "epic-orchestral-boss",
    "family": "gamer",
    "rubric_version": 2,
    "pass_threshold": 7.0,
    "criteria": [
      "battle_energy",
      "loop_safety",
      "asset_packaging",
      "loudness_target"
    ],
    "weights": {
      "battle_energy": 3,
      "loop_safety": 3,
      "asset_packaging": 1,
      "loudness_target": 1
    },
    "weight_sum": 8,
    "reject_signals": [
      "battle_no_fast_tempo",
      "loop_fade_or_truncation",
      "clipped_master",
      "no_stated_tempo_key"
    ],
    "reject_signals_unnamed": 0
  }
}
```
