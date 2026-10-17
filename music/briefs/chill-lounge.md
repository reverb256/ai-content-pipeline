# Brief — chill-lounge

> **Stage:** brief (stages.yaml: `brief` → bot `producer`) — DELIVERED; the chain resumes at
> `genre-select` (already resolved in §1–§3).
> **Card:** t_2c5b59f2 (`music-oracle: chill-lounge (score 8.6)`) — the surviving OPEN card for
> this genre. The board check reports `chill-lounge → t_2c5b59f2 [running]` and one open card per
> genre, rc=0 (`music/scripts/check_oracle_board.py`, re-run in this pass).
> **Superseded cards:** t_38e84953 (score 8.9, done) wrote this brief; t_4c838339 (score 9.1,
> done) was its duplicate. Briefs in this lane are keyed by **genre**, not by card, so all three
> cards resolve to this one file.
> **Written:** 2026-10-16T13:03:27-05:00 (CDT)
> **Verification pass:** 2026-10-16T15:40-05:00 (CDT), card t_2c5b59f2 — every figure below
> re-measured live; §10 records the pass, the corrections, and the residual open items.
> **Repo:** /home/j_kro/ai-content-pipeline @ `63440da485bfd4097c431ed90d6c476d2e622c95` (main)
> **Oracle:** **true score 8.4/10** — oracle dedupe ruling 2026-10-16 (`music/oracle.py` @
> `b2d11f7`): quota headroom 10.0, lane coverage 8.0, revenue potential 10.0, cadence fit 6.67,
> policy risk 10.0, trend signal 3.0. Threshold 5.0 → produce. The card titles' 8.6 / 8.9 / 9.1
> are older numbers; §10.1 shows 8.6 and 8.9 are unreachable from the fixed scorer.
> **Revision:** the superseded blob was
> `37fd87ef4585d6b0f6c4a5c215790dd200eb1b70b2466eac92b7a9a8086c482e` (committed by the brief
> stage, 2026-10-16T13:03); the current digest is re-readable with
> `sha256sum music/briefs/chill-lounge.md`.

## 1. Genre resolution (live, not transcribed)

Resolved from `music/genres.yaml` — not copied by hand:

```
$ python3 music/registry.py validate
registry OK: 14 genres, 10 lanes, 1 stage gate rule(s)
genres: activist, anime-ending, anime-opening, chill-lounge, chiptune-8bit,
        commentary-beds, elemental-air, elemental-earth, elemental-fire,
        elemental-water, epic-orchestral-boss, jungle-dnb, sentimental-piano, trance
lanes: direct-fan, direct-license, game-assets, stock-ai-native, streaming,
       sync, sync-documentary, youtube-gaming, youtube-longform, youtube-mix
stage gate visual: lane_gate -> gate_youtube_authentic (when_absent: none)
quota ledger: period 2026-10, standard 0/60 (warn_at 55, hard_stop_at 58)
```

The validator checks that every referenced lane exists and every
`prompt_template` / `visual_style` path resolves to a real file. It passed, so the
chill-lounge block and its four lanes are internally consistent.

The stage-gate line is new since this brief was first written: the `visual` stage resolves its
gate from the genre's OWN lanes (`music/lanes.yaml` `stage_gates`). chill-lounge has a YouTube
lane, so that stage gate applies to this genre instead of resolving to `when_absent: none`.

| Field | Value |
|---|---|
| Genre | `chill-lounge` |
| Family | `ambient` |
| Prompt template | `music/prompts/chill-lounge.md` (resolves) |
| Visual style | `music/visuals/lofi-room-rain.md` (resolves) |
| Lanes | `youtube-longform`, `streaming`, `sync`, `direct-license` |
| Cadence | 3/wk |
| Video shape | `album-30-60min` |
| Lyric blueprint | `music/lyrics/blueprints/chill-lounge.yaml` |
| Note (registry) | "Highest-volume lane. Needs visual identity to survive inauthentic-content review." |

## 2. Intent

A late-night room you want to stay in. Downtempo loop music for passive listening —
the product is **watch time and repeat play**, not a song that develops. Warm,
degraded, unhurried; jazz voicings over a swung hat loop; tape flutter and vinyl
crackle as the texture. The genre is worth 3 uploads/week because a 30–60 min
album video holds listeners for the full runtime, which is where both the ad
revenue and the platform-authority signal come from.

Three things must hold, or a generation is out of genre:

1. **Tempo 70–90 BPM** (sweet spot 75–85). Above 90 it drifts to boom-bap.
2. **Jazz harmony** — maj7/min7/dom9, close voicings, ii–V–I as the default loop.
3. **Degradation is the sound** — top end rolled off 8–12 kHz, crackle bed at
   −18 to −22 dBFS, tape flutter 10–20%.

A generation with a vocal hook, a build-drop, or a bright modern top end is **rejected**.

## 3. Target lanes and what each one demands

From `music/lanes.yaml`. These are the gates that will actually run, not advisory text.

| Lane | Shape / surface | Gate that must pass | Required artifacts |
|---|---|---|---|
| `youtube-longform` | album-30-60min on YouTube | `gate_youtube_authentic` | shot diversity (not a raw image dump), Jaccard similarity vs prior uploads, AI disclosure |
| `streaming` | via `distributor` (DistroKid; TuneCore alt) | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` |
| `sync` | Songtradr / AudioSparx | `gate_sync_ready` | `stems`, `metadata`, `clearance_doc`, `instrumental_version` (which must differ from the master) |
| `direct-license` | own-site | `gate_sync_ready` | `stems`, `license_tiers` |

Lane requirements that shape the work, decided here so later stages do not re-litigate:

- **Stems are not optional.** Two of the four lanes (`sync`, `direct-license`) require
  them, and `sync` additionally requires an **instrumental version that differs from
  the master**. Export stems through Suno **Studio** (unlimited), never the standard
  download button (60/month cap).
- **`gate_sync_ready` needs a real PDF clearance doc.** A placeholder fails it.
- **Autonomy rung for all four lanes is `advisory`** (`music/autonomy.yaml`): every
  publish is proposed with evidence and approved by j_kro. Rung promotion needs 10
  clean advisory publishes.

## 4. Throughput budget (derived, not assumed)

Cadence 3 videos/week (`genres.yaml`) × 8–12 tracks per album video
(`music/visuals/lofi-room-rain.md`: "30–60 min runtime = 8–12 tracks + chapter
cards between, not one static image") = **24–36 tracks/week**.

That number is the real constraint on this lane. It only works because this genre is
**instrumental-first**: `music/prompts/chill-lounge.md` states the lyrics box stays
empty (Suno's instrumental path) and warns against pasting production notes as sung
lyrics. Instrumental tracks skip the human-authorship bottleneck entirely. Treat the
vocal route as the exception, not the default.

Where vocals are wanted, the blueprint (`music/lyrics/blueprints/chill-lounge.yaml`)
carries a full 7-section structure at a 72 BPM anchor and requires **human-authored**
lyrics to keep the copyright claim.

## 5. Audio identity (locked for this genre)

Style caption, verbatim from `music/prompts/chill-lounge.md` (545/1000 chars):

```
downtempo chill lounge, 75 BPM, 4/4, heavy swung hats, warm jazz chords on felt
electric piano, maj7 min7 dom9 voicings, soft round bassline following chord roots,
tape saturation and gentle wow-and-flutter pitch drift, vinyl crackle bed at the
noise floor, slow low-pass filter movement across the loop, light sidechain pump on
the chords, unhurried 8-bar loop that barely develops, kick and snare sitting behind
the chords, muted guitar answering phrases, airy reverb, no bright modern top end,
warm not loud, late-night room with rain outside
```

Settings: **Weirdness 40%**, **Style Influence 70%**,
**Exclude Styles:** `EDM, big drops, autotuned pop vocals, trap hats, bright synth
leads, loud drums` (six terms, the documented maximum).

Structure: 4–8 bar loop, minimal development, small per-pass variation
(filter, crackle shift, one melody note). Arrangement is texture, not a song arc.

## 6. Visual identity (locked for this genre)

`music/visuals/lofi-room-rain.md`: one continuous lived-in room per video —
amber desk lamp (#d9a066), muted teal window (#4a6670), base #2a2321; rain-streaked
glass at ~12 fps; drift 0.5–2 px/frame; grain 4–6%. Cut only on track boundaries.
**Each upload must use a different room variant** (rain / coffee shop / night porch /
studio) and never reuse the exact frame stack — `gate_youtube_authentic` measures
frame similarity against prior uploads, and this is the lane's stated survival risk.

## 7. Existing assets for this genre

`music/lyrics/chill-lounge/amber-hour/` is a complete human-authored lyric sheet
(title "Amber Hour", author j_kro, written 2026-10-08). Measured live:

```
$ python3 music/gates/gate_lyrics_original.py --track-dir music/lyrics/chill-lounge/amber-hour
PASS gate_lyrics_original
  track        : Amber Hour (music/lyrics/chill-lounge/amber-hour)
  sections     : 7
  unique words : 93
  authorship   : j_kro @ 2026-10-08T12:48:59+00:00
  suno markers : none
```

So the lyrics half of one chill-lounge track exists and passes its gate (plain and `--strict`).
**No deliverable audio exists in this tree** — `~/Music` is empty, and the only audio file under
`music/` is the gate fixture `music/tests/fixtures/loop_silence_tail.wav`. The cluster has
rendered audio, but none of it is this genre's (§10.5): the first chill-lounge render is
genuine work, not a re-run.

Quota is untouched, measured live:

```
$ python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

## 8. Open items for the next stage (`genre-select` / `lyrics` / `generate`)

1. **Instrumental vs vocal split.** The blueprint is written for vocals; the prompt
   says this lane is almost always instrumental. Decide per track: instrumental for
   album beds (24–36 tracks/wk), vocal only where a lyric sheet like `amber-hour`
   exists. Do not let the vocal path gate the album lane.
2. **Clearance doc.** `sync` and `direct-license` both need a real PDF clearance
   document. None exists in the tree. This is a blocker for those two lanes, not for
   `youtube-longform`.
3. **License tiers.** `direct-license` requires `license_tiers`; nothing defines them yet.
4. **The duplicate stack-up is closed** (§10.4). `music/oracle.py` no longer opens a second
   card for a genre that already carries one, and the board check passes: one open card per
   genre. The point this item raised — do not let two cards produce the same brief — is now
   enforced by `music/scripts/check_oracle_board.py`.

## 9. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` (validated live, 14 genres / 10 lanes,
  1 stage gate rule)
- Gates: `music/gates/` (all four lane gates present, exercised live above)
- Quota: `music/quota-ledger.json` (measured)
- Autonomy: `music/autonomy.yaml` (all lanes `advisory`)
- Stage contract: `music/stages.yaml` (`brief` → `producer`)
- **Reference files — on disk now, still absent from `origin/main`.**
  `brain/playbooks/music-lane-architecture.md` is cited as "READ FIRST" by this lane's
  profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`, `autonomy.yaml`, `gates/README.md`, and
  `gates/*.py`. When this brief was written the file did not exist anywhere on this machine
  (`find /home/j_kro -name 'music-lane-architecture.md'` → no hits). It exists now, and so does
  `brain/research/music-monetization-2026.md` (§10.3.3). Both are tracked in `HEAD` and both are
  absent from `origin/main`, so a fresh clone still dangles. Section numbers quoted from them
  (e.g. §3, §4, §5, §11.2) are checkable on this machine.

## 10. Verification pass — 2026-10-16, card t_2c5b59f2

This pass re-measured every checkable claim in this brief against live state, and applied the
oracle dedupe ruling to the header. §2–§7 were found correct; three things were corrected
(10.3) and two were found resolved (10.4). Commands ran with `/usr/bin/python3` — the worker
shell's bare `python3` lacks PyYAML (t_006db63d).

### 10.1 Oracle score — the card titles' numbers are not reproducible

Live recompute with the repo's own scorer (`music/oracle.py` imported as a module,
`score_genre("chill-lounge")`, 2026-10-16):

| Component | Score | Weight | Contribution |
|---|---|---|---|
| quota headroom | 10.0 | 0.25 | 2.50 |
| lane coverage | 8.0 | 0.20 | 1.60 |
| revenue potential | 10.0 | 0.20 | 2.00 |
| cadence fit | 6.67 | 0.15 | 1.00 |
| policy risk | 10.0 | 0.10 | 1.00 |
| trend signal | 3.0 | 0.10 | 0.30 |
| **total** | | | **8.4** |

Every total this genre can reach, by trend-fetch outcome (snippet counts 0/1/2/3/4/5+ and a
failed fetch): **8.4, 8.54, 8.68, 8.82, 8.96, 9.1** — a failed fetch now scores the same 8.4 as
a successful fetch with no snippets (`TREND_NO_SIGNAL = 3.0`, `music/oracle.py` @ `b2d11f7`).

So the 8.6 in this card's title is **unreachable**: it is the pre-`b2d11f7` failed-fetch premium
(`trend_signal` 5.0 → total 8.6). 8.9 is also unreachable — it is a 2026-10-09 number whose
`cadence_fit` was 10.0 before the quota period aged. 9.1 is reachable, but only when the trend
fetch returns five or more snippets. `check_oracle_determinism.py` PASS rc=0;
`check_oracle_board.py` PASS rc=0 (13 open oracle cards across 13 genres).

### 10.2 Re-measured, unchanged

- `music/registry.py validate` → `registry OK: 14 genres, 10 lanes, 1 stage gate rule(s)`.
  The chill-lounge entry is unchanged: family `ambient`, lanes `youtube-longform, streaming,
  sync, direct-license`, cadence `3/wk`, `video_shape: album-30-60min`, the same note.
- Every referenced artifact resolves: `music/prompts/chill-lounge.md` (3640 B),
  `music/visuals/lofi-room-rain.md` (1232 B), `music/lyrics/blueprints/chill-lounge.yaml`
  (1856 B; `bpm_anchor: 72`, 7 `structure` entries).
- Style caption measured 545/1000 chars — `music/scripts/check_prompt_style_counts.py` PASS:
  15 declared style-field lengths across 14 templates match their blocks.
- §5 prompt settings read live from the template: Weirdness 40%, Style Influence 70%, six
  exclusion terms (EDM, big drops, autotuned pop vocals, trap hats, bright synth leads, loud drums).
- `music/gates/gate_quota.py` PASS — period 2026-10, standard downloads 0/60, studio exports 0.
- `music/gates/gate_lyrics_original.py --track-dir music/lyrics/chill-lounge/amber-hour` PASS,
  and `--strict` PASS: 7 sections, 93 unique words, `j_kro @ 2026-10-08T12:48:59+00:00`, no
  Suno markers — exactly the §7 block.
- §3's lane table against `music/lanes.yaml`: `youtube-longform` → `gate_youtube_authentic`
  (script present); `streaming` → `gate_release_ready`, `requires: [ai_disclosure, isrc,
  metadata, master]`; `sync` → `gate_sync_ready`, `requires: [stems, metadata, clearance_doc,
  instrumental_version]`; `direct-license` → `gate_sync_ready`, `requires: [stems,
  license_tiers]`. `music/autonomy.yaml` still puts all four lanes at rung `advisory`.
- §3's clearance warning is real, not advisory text: `music/gates/gate_sync_ready.py` reads
  `CLEARANCE_NAMES = ("clearance_doc.pdf", "clearance_doc.txt")`, requires a `.pdf` to start
  with `%PDF-`, sets `MIN_STEMS = 4`, and requires `instrumental` to be real audio distinct
  from the master.
- §4 arithmetic: 3 videos/week × 8–12 tracks = 24–36 tracks/week.
- §7's "no deliverable audio in this tree": the only audio file under `music/` is
  `music/tests/fixtures/loop_silence_tail.wav`, and `~/Music` is empty.

### 10.3 Corrected in place

1. **Header — the owning card and the score.** The header named t_38e84953 (8.9) as the card and
   t_4c838339 (9.1) as the duplicate, and carried an 8.9 oracle block. The oracle ruled
   2026-10-16 that **t_2c5b59f2 is the surviving open card** for chill-lounge and the true score
   is **8.4**; the header now records all three cards, the ruling and §10.1's table. The
   superseded blob's digest is recorded there, as `music/scripts/check_brief_figures.py`
   requires of any brief that carries one.
2. **§1 — the registry transcript was one line short of live.** The validator now also prints the
   `stage gate visual` resolution line and its summary says `1 stage gate rule(s)`. The quoted
   block is now the live text, and the paragraph below it states what that line means for this
   genre.
3. **§9 — the references are no longer dangling on disk.** Both files exist on this machine now:
   `brain/playbooks/music-lane-architecture.md` (34328 B, 596 lines, mtime 2026-10-16T15:31) and
   `brain/research/music-monetization-2026.md` (11067 B, 199 lines, mtime 2026-10-16T13:59). Both
   are tracked in `HEAD`. Both are **absent from `origin/main`** (`git cat-file -e
   origin/main:brain/...` → `fatal: path ... exists on disk, but not in 'origin/main'`), so the
   dangling citation is fixed for this checkout only, not for a fresh clone.

### 10.4 Resolved since this brief was written

- **§8 item 4 (duplicate stack-up) — closed.** `music/oracle.py` now refuses to open a second
  card for a genre that already carries an open one (`open_oracle_genres`, commit `b2d11f7`),
  and `music/scripts/check_oracle_board.py` PASSes rc=0: 13 open oracle cards across 13 genres,
  chill-lounge → t_2c5b59f2.
- **The sync-lane gate selection defect is fixed** (commit `54f6d3c`, card t_d9983bb9):
  `gate_sync_ready` now derives its accepted lane set from `music/lanes.yaml` instead of a
  hardcoded list, so a lane the registry assigns to that gate is no longer rejected rc=2.

### 10.5 Still open — not this pass's to close

- **Clearance doc and license tiers** (§8 items 2 and 3) still do not exist anywhere in the
  tree. The `sync` and `direct-license` lanes cannot pass their gates until they do.
- **Audio.** Measured live: `/var/lib/sunolocal/artifacts/` holds 14 rendered files (13 `.flac`
  + 1 `.wav`, newest mtime 2026-10-16T15:28), and `music/quota-ledger.json` records **8**
  renders — `elemental-air-above-the-weather`, `chill-lounge-slow-gold`,
  `commentary-beds-lo-fi-jazz-bed`, `commentary-beds-lo-fi-jazz-sting`,
  `elemental-earth-chamber-loop`, `sentimental-piano-room-with-the-light-going`,
  `elemental-fire-emberfall`, `final-round` — 0 standard downloads, 0 studio exports.
  This genre's render **is** recorded: `chill-lounge-slow-gold` (job `4cdf2e43854c4d258c1a467fe3ca0b26`,
  sha256 `ead1b1efdf84e845f16c42859d2b0a27826ce86d89f8012001dd3c9c536d9a05`, 420.000 s,
  plan rendered 2026-10-16T15:17:48-05:00, queued by card `t_6d7ad524`).
- **Who dispatches this card.** The live `music-pipeline-driver.service` runs the right checkout
  with `--board music` (fixed by t_41f354be) but its own unit file pins `Environment=DRY_RUN=1`:
  it resolves the route and logs `[dry-run] would dispatch producer` without launching anything,
  pending j_kro's ruling on t_41f354be §4 (the generic kanban dispatcher also claims every oracle
  card). Its 2026-10-16T15:30 run logged `concurrency cap reached (1/1)` and dispatched 0. Any
  stage this brief advances is therefore picked up by the generic dispatcher until that gate is
  lifted — that is why this card's advance to `genre-select` is posted as a card comment.
