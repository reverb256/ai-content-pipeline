# Music Lane Architecture — genre-generic AI music operation

**Created:** 2026-10-08. **Reconciled with live code:** 2026-10-16 (card t_b0a4db92).
**Owner lane:** `music` board. **Account:** Suno Premier ($30/mo, 10,000 credits/mo).
**Platform research:** `brain/research/music-monetization-2026.md` (11,067 B, committed
2026-10-16, commit `5a01157`).

## Provenance and status

This file is authoritative for the music lane. Every section below describes code that
exists. Where a claim is a plan and not yet a fact, the text says so.

| Event | Commit | Date |
|---|---|---|
| First written (WIP backup branch) | `3882292` on `wip/atlas-backup-20261014` | 2026-10-14 |
| Restored into `main` (ops card t_75aacf8b) | `5a01157` | 2026-10-16 14:12 |
| Audited against live files and rewritten (card t_b0a4db92) | see `git log -1 -- <this file>` | 2026-10-16 |
| Declaration re-measured after the `music-producer` SOUL fix (card t_e2375c5a) | see `git log -1 -- <this file>` | 2026-10-16 16:15 |

**Two checkouts hold this repo. They have diverged. Read this before you trust a path.**

| Host | Path | Role | State measured 2026-10-16 14:15 |
|---|---|---|---|
| nexus | `/home/j_kro/ai-content-pipeline` | lane run host — the systemd units run this tree | 37 ahead / 15 behind `origin/main` |
| zephyr | `/home/j_kro/Projects/ai-content-pipeline` | lane dev checkout — closest to trunk | 2 ahead of `origin/main` |

Consequences you must know:

- `music/mix/master.py`, `music/suno-gen.py`, `music/packages/` and `music/tests/` exist
  on zephyr and NOT on nexus. They arrive on nexus with the 15 upstream commits.
  - **Re-measured 2026-10-16 16:15 (card t_e2375c5a):** `music/suno-gen.py` (42,652 B)
    and `music/assets/pack.py` are now tracked in the nexus `main` as well, so those two
    are on BOTH hosts. Still absent on nexus: `music/mix/`, `music/lanes/`,
    `music/publish/` — all three present on zephyr (`lanes/` and `publish/` as untracked
    working files there). The guard for the whole class is
    `music/scripts/check_soul_declarations.py`: it fails when the `music-producer` SOUL
    declares a `music/...` path that is absent on this host and carries no marker.
- The loudness ruler is already EBU R128 on zephyr and still volumedetect on nexus. See
  §5.1. Never push the nexus copy of `music/gates/` over the zephyr copy.
- The systemd units run the nexus tree (`ExecStart=/…/ai-content-pipeline/…`). A fix that
  lands only on zephyr does not run.

> **Core design rule: the pipeline is GENRE-GENERIC.** Genres are DATA, not code. Add a
> genre by adding one row to the genre registry. Never edit a script to add a genre.
> j_kro's target set is open-ended ("infinite variety"), so a hardcoded genre list is a
> defect by construction.

---

## 1. Why a registry, not lanes-per-genre

The failure mode this avoids: five genre folders, five near-identical scripts, five places
to fix one bug. Acceptance differs by genre (Beatport bans trance, stock libraries ban all
AI, YouTube accepts all genres but punishes sameness). Genre and lane are two orthogonal
axes. They must combine declaratively.

```
genre registry (data)  ×  lane registry (data)  →  generated pipeline graph
```

Add `boss-battle-epic` to the registry. The pipeline then knows its prompt template, its
visual style, its lane set, and its cadence. No code change.

---

## 2. Genre registry — `music/genres.yaml`

`music/genres.yaml` is the registry. It holds 14 genres (`/usr/bin/python3
music/registry.py validate` → `registry OK: 14 genres, 10 lanes`, measured 2026-10-16).
`registry.py validate` enforces the schema: every `prompt_template` and `visual_style`
path must resolve, and every entry in `lanes` must exist in `music/lanes.yaml`.

| Genre | Family | Lanes | Cadence | Video shape |
|---|---|---|---|---|
| `chill-lounge` | ambient | youtube-longform, streaming, sync, direct-license | 3/wk | album-30-60min |
| `trance` | edm | streaming, youtube-mix, direct-license, sync | 2/wk | mix-60min |
| `jungle-dnb` | edm | streaming, youtube-mix, direct-license | 2/wk | mix-60min |
| `sentimental-piano` | acoustic | sync, streaming, direct-license, youtube-longform | 3/wk | album-30-60min |
| `commentary-beds` | utility | direct-license, sync | 5/wk | none |
| `activist` | vocal | direct-fan, sync-documentary, streaming | 1/wk | lyric-video |
| `elemental-fire` | gamer | game-assets, youtube-gaming, streaming | 2/wk | loop-10min |
| `elemental-water` | gamer | game-assets, youtube-gaming, streaming | 2/wk | loop-10min |
| `elemental-earth` | gamer | game-assets, youtube-gaming, streaming | 2/wk | loop-10min |
| `elemental-air` | gamer | game-assets, youtube-gaming, streaming | 2/wk | loop-10min |
| `chiptune-8bit` | gamer | game-assets, youtube-gaming, streaming | 2/wk | loop-10min |
| `epic-orchestral-boss` | gamer | game-assets, youtube-gaming, sync, streaming | 1/wk | single-4min |
| `anime-opening` | anisong | streaming, sync, direct-license, youtube-gaming | 1/wk | single-4min |
| `anime-ending` | anisong | streaming, sync, direct-license, youtube-longform | 1/wk | album-30-60min |

Registry `defaults` (apply to every genre): `export: studio`, `stems: true`,
`lyrics: human-original`, `release_private: true`, `gate_profile: reviewer-deepseek`.

Genre notes that carry a hard rule:

- `trance` and `jungle-dnb` — Beatport banned (2026-08-12). Independent release and DJ
  mixes only. No label path.
- `activist` — ad-suitability risk. Audience-funded beats ad-funded. Documentary sync is
  the professional outlet; the lane is `sync-documentary`.
- `anime-opening` — the final-chorus key change is load-bearing. A generation without the
  key-changed final chorus is out of genre. Reject it.
- `commentary-beds` — loopable and stemmed. No lead melody under speech.

### Extensibility contract

A new genre requires ONLY a `prompts/<name>.md` template, a `visuals/<name>.md` style, and
a registry block. The driver, the gates, and the dispatch are genre-blind.

---

## 3. Lane registry — `music/lanes.yaml`

`music/lanes.yaml` holds 10 lanes. The registry validator fails on any genre lane with no
block here.

| Lane | Surface | Owning bot | Gate | Required artifacts |
|---|---|---|---|---|
| `youtube-longform` | youtube | videobot → publishbot | `gate_youtube_authentic` | video, disclosure |
| `youtube-mix` | youtube | videobot → publishbot | `gate_youtube_authentic` | video, disclosure |
| `youtube-gaming` | youtube | videobot → publishbot | `gate_youtube_authentic` | video, tracklist |
| `streaming` | distributor | distributor | `gate_release_ready` | ai_disclosure, isrc, metadata, master |
| `sync` | songtradr, audiosparx | distributor | `gate_sync_ready` | stems, metadata, clearance_doc, instrumental_version |
| `sync-documentary` | songtradr, audiosparx | distributor | `gate_sync_ready` | stems, metadata, clearance_doc, instrumental_version |
| `direct-license` | own-site | distributor | `gate_sync_ready` | stems, license_tiers |
| `direct-fan` | patreon, ko-fi | socialbot | `gate_human_approval` | — |
| `game-assets` | itch.io, unity-asset-store, gamedev-market | distributor | `gate_sync_ready` | stems, loop_point, seamless_loop, metadata |
| `stock-ai-native` | loudly, soundraw, musicapi | distributor | `gate_release_ready` | — |

Decisions recorded in the file:

- **Distribution: DistroKid primary** ($24.99/yr, no caps, no exclusions, explicit AI
  disclosure step). **TuneCore secondary**, for Suno partner-model releases (eligible since
  2026-09-08). Never send one track through two distributors — duplicate listings are a
  Spotify spam-filter target. Source: `brain/research/music-monetization-2026.md` §1.2.
- `sync-documentary` is NOT in the 2026-10-08 draft. It was added because the `activist`
  genre declares it. `registry.py validate` fails on a genre lane with no block.
- `stock-ai-native` is the only remaining stock door. Pond5, AudioJungle/Envato, Artlist,
  Epidemic Sound, Soundstripe, PremiumBeat and Musicbed all ban AI (research §1.1).
- **Gate selection is derived from the registry, never hardcoded** (2026-10-16, card
  `t_d9983bb9`). Two measured defects had one root cause — the registry and the gate could
  disagree and nothing noticed: (a) `sync-documentary` declared `gate: gate_sync_ready` while
  that gate's argparse rejected the lane name and exited **2** — a usage error that a stage
  reads as a gate FAILURE, on the lane the activist genre's entire `revenue_potential`
  depends on; (b) the `visual` stage ran `gate_youtube_authentic` for every genre, including
  genres with no YouTube lane. So: a gate's accepted lane set is read from `lanes.yaml`
  (every lane whose `gate:` is that gate), each lane's `requires:` tokens must map to a check
  the gate can produce evidence with (an unmapped token fails the run), and a stage's gate is
  resolved from the genre's lanes through `music/registry.py gate-for-stage`. Guarded by
  `music/scripts/check_gate_lane_surface.py`.

---

## 4. Pipeline stages — `music/stages.yaml`

`music/stages.yaml` is the stage → bot map for the music board. The driver reads it when
`BOARD=music`, so the lane is data-driven: add a stage by adding a block here, never by
editing the driver. The file holds 15 stages, 13 producing plus 2 human gates.

| Stage | Bot | Output | Gate / advance rule |
|---|---|---|---|
| `brief` | producer | card with genre + lane + intent | registry match exists |
| `genre-select` | producer | resolved registry entry | genre in `genres.yaml` |
| `lyrics` | writer | original lyrics (human-authored claim) | `gate_lyrics_original` (instrumental genres skip) |
| `generate` | producer | 2 tracks via Suno CDP | `gate_quota` first; export through Studio only |
| `curate` | producer | picked track + reject reason | — |
| `stems` | producer | stems from Suno Studio | `gate_stems_present` |
| `master` | producer | loudness-normalised master | `gate_loudness` |
| `gate` | reviewer-deepseek | pass/fail + findings | `gate_quality` (different model than the maker) |
| `asset-pack` | producer | asset pack derived from the master (loops, stems, one-shots, SFX) — only for a genre whose lanes include `game-assets` | `gate_sync_ready` (pack mode) + `gate_loop_points`, both resolved from `lanes.yaml` `game-assets.derived_product` by `registry.py derived-for-stage`; the generator's own rc is checked (`0` accepted, `1` REJECTED); no genre builds it unless its lanes sell it |
| `package` | producer | manifest + metadata + ISRC + artwork | `gate_release_ready` |
| `visual` | videobot | platform-native video | resolved from the genre's lanes: `lanes.yaml` `stage_gates` → `gate_youtube_authentic` when a lane of that genre is guarded by it, else `none` (stated on the card) |
| `publish` | publishbot / distributor | private upload or distribution | human approval before public |
| `track` | analyst | streams, revenue, lane ROI | closes the card with `kanban_complete` |
| `human-approval` | — | parked for j_kro | `human_gate: true`, `auto_next: publish` |
| `escalate` | — | parked for j_kro | `human_gate: true` |

Each producing prompt ends with an explicit advance step, because the driver re-reads the
stage marker every 30 min. That step must name a channel **the caller can reach** — two
different processes run a music stage, and only one channel works for both:

| Caller | Its environment | Channel that works |
|---|---|---|
| the driver: `hermes -p <bot> chat -q "<prompt>"` | unfenced, no kanban toolset | CLI: `bash scripts/automation/advance-stage.sh {card} <next-stage> --board music` |
| the generic kanban dispatcher: a spawned kanban worker | terminal and every subprocess it starts are fenced | tool: `kanban_comment(task_id="{card}", body="stage: <next-stage>")` |

So each prompt names the `kanban_comment` **tool** first, keeps the CLI as the labelled
fallback, and requires the caller to CHECK the exit status. The marker must be the LAST
`stage:` match in the card's `hermes kanban show` output (body, then run summary, then
comments) — the driver takes the last match. A stage whose gate FAILS must not advance.

Measured 2026-10-16 (card t_5a93164a): a dispatcher-spawned worker that runs the CLI step
gets

```
kanban: delegate_task child contexts cannot mutate Kanban tasks via the CLI   # exit 1
```

so the marker never moves and the driver re-dispatches the same stage. That is the exact
failure the advance step was added to prevent, one layer down; `advance-stage.sh` now fails
loudly and names the tool route instead. Guarded by `music/scripts/check_stage_advance.py`.

The `--board music` flag is required on the CLI fallback. `advance-stage.sh` defaults to
`faceless-youtube`, so before the 2026-10-16 fix (card t_38e84953) every music advance went
to the wrong board.

### 4.1 Who dispatches a music card — the answer

**Design of record: `scripts/automation/pipeline-driver.sh --board music` owns stage
dispatch on the music board.** The card's `assignee` field is not the route.

The driver walks every card in `ready`, resolves that card's stage marker under the ONE
convention, and routes the stage to the bot named in `music/stages.yaml`. It ignores the
assignee. Unknown stages are logged and skipped. A card with no marker defaults to `brief`.
The default concurrency cap is 1 bot at a time (`MAX_CONCURRENT_BOTS`, default 1). Raise it
only for CPU-only bots.

**The marker convention (card `t_669bb02b`, 2026-10-16).** A marker is a LINE that IS
`stage: <token>` — nothing before it and nothing after it on that line — and it is read
from the card BODY and from COMMENT bodies only, never from a run summary, a result or an
event. The implementation is `scripts/automation/stage_marker.py`; the driver and
`music/scripts/check_stage_markers.py` both call it, so one rule decides every route.

Why the read is not "the last `stage:` marker anywhere": `hermes kanban show` prints the
body, then `Result:`/`Latest summary:`, then `Comments`, then `Events` (whose `completed`
payload carries the FULL run summary) and `Runs`. The run summary is therefore rendered
AFTER the comments, and prose in it wins. Measured on the live music board — card
`t_92a09bdc` resolved to the undeclared stage `advance-stage` (from "...Did not advance the
stage: advance-stage.sh is refused..."), which makes the driver log `unknown stage` and SKIP
the card: a silent stall instead of a route. Writer rule, therefore: post the marker as its
own line, and never write a lone `stage: <word>` line anywhere else in the card.

**The conflict.** A second mechanism also claims the board: the generic kanban dispatcher
claims whatever card is `ready` and matches an assignee profile. Every oracle card is
assigned `music-producer` (`music/oracle.py`, `--assignee music-producer`). Armed
together, the two mechanisms dispatch every card twice, to two different profiles.

Measured 2026-10-16: one live double dispatch. At 14:00:03 the driver dispatched `producer`
for card `t_de485c84` (stage `brief`); at 14:01 the generic dispatcher spawned the same card
as `thumbnailbot` (its assignee). Two profiles, one card.

**Operational rule while the decision is open.** As measured 2026-10-16 14:15:

- The driver timer is active (every 30 min) and the installed unit carries
  `Environment=DRY_RUN=1`. The driver logs `[dry-run] would dispatch <bot>` and launches
  nothing.
- The generic dispatcher works the board as it does today.
- Do NOT delete the `DRY_RUN=1` line. Do NOT enable live dispatch.
- A card's `assignee` is a placeholder, not an ownership sign. The `stage:` marker plus
  `music/stages.yaml` is the route.

**The decision belongs to j_kro.** Card `t_2eaa39ba` (blocked) carries it with the
evidence. Two options, with the consequence of each:

| Option | Action | Consequence |
|---|---|---|
| A — the driver owns the board | delete `Environment=DRY_RUN=1`, and fix `KillMode` | the lane runs stage → bot per `stages.yaml`. The generic dispatcher must stop claiming music cards, or it still double-dispatches. |
| B — the generic dispatcher owns the board | retire the driver timer | `music/stages.yaml` stops being the route. Every stage then runs as `music-producer`, so the stage → bot mapping must move into assignee rewrites. |

Two defects must be fixed whichever option wins:

1. **A live dispatch cannot survive its own tick.** The unit is `Type=oneshot` with the
   default `KillMode=control-group`, and the driver starts each bot with `nohup … &`.
   systemd tears down the cgroup when the oneshot exits, so the bot dies with it. Set
   `KillMode=process`, or dispatch into its own scope.
2. **`systemd-run --user` on nexus does not forward the caller's environment.** The command
   `DRY_RUN=1 systemd-run --user …` runs the driver LIVE. Pass the gate with `--setenv=DRY_RUN=1`.

---

### 4.2 Resuming a re-emitted card — where a card STARTS

One open card per genre (incident `t_bf0e5edd`) means a card that reaches `done`
leaves the open set, and the next oracle wave re-emits the genre. That re-emitted
card must start where the genre's chain actually stands. Incident `t_6599927d`
(2026-10-16): the emitter wrote `stage: brief` unconditionally, so the 13 cards of
the 14:05 wave sent a `music-producer` run back through the brief stage although
**all 14 genres' briefs were already on disk** — and the briefs are keyed by
GENRE, so both cards of a twin pair resolve to one artifact.

The rule has ONE implementation, `music/stage_state.py`:

- The stage ORDER comes from `music/stages.yaml` — the file that declares it —
  read at call time. Neither the emitter nor the checks carry a stage list.
- A stage declares a **proof** (a glob) when its output is measurable on disk:
  `brief` (`music/briefs/<genre>.md` or `music/briefs/<genre>/<slug>/brief.md`)
  and `lyrics` (`music/lyrics/<genre>/<slug>/lyrics.suno.txt` — the sheet
  `gate_lyrics_original` gates, not the bare track directory).
- A stage with **no** declared proof counts as UNPROVED, and the walk stops at
  the first unproved stage. That direction is the safety argument: the rule can
  never skip work that was not actually done. A human gate is never proved, so a
  fully delivered chain stops at the gate and the card parks for j_kro — right.
- `genre-select` declares no proof (it resolves and verifies a registry entry; it
  produces no artifact), so today the answers are `brief` (no artifact on disk) or
  `genre-select` (a brief exists). Resuming PAST a stage that leaves no artifact
  needs the board's own advance marker, and that is the stage-semantics question
  on `t_2eaa39ba` — not this rule's to guess.

Three callers, one rule:

| Caller | What it does with the rule |
|---|---|
| `music/oracle.py` | writes the resolved stage as the new card's `stage:` marker; fails CLOSED (creates no cards) when the rule cannot be resolved, like an unreadable board |
| the `brief` stage prompt (`music/stages.yaml`) | checks the artifact FIRST: a delivered brief is verified and the card advances with no writing work |
| `music/scripts/check_oracle_board.py` | invariant B3 fails any OPEN card sitting BEHIND its genre's resume point; B4 fails a marker naming no declared stage |

Guards: `music/test_stage_state.py` (the rule, 16 cases), `music/test_oracle_dedupe.py`
(the emitter's body marker and its fail-closed path), `check_oracle_board.py --selftest`
(B1–B4 on known-bad boards), and B3 fired on real board data (a copy of the live db
with one delivered-stage card re-opened, board untouched). The check reads a card's
stage by the marker **convention** (`scripts/automation/stage_marker.py`, card
`t_669bb02b`) rather than the driver's old last-match read: measured 2026-10-16 it
agrees with that read on 40 of the 42 oracle cards and is right on both differences
(`t_92a09bdc` → an undeclared token out of summary prose; `t_354d5d25` → `brief`
although its own comment marker said `genre-select`).

---

### 4.3 Where a finished render lands — the render output contract

Added 2026-10-16 (card `t_320bae4c`). Before it, the answer to "where does a render
land?" was whatever `SUNOLOCAL_WRAPPER_OUT` happened to be, and the wrapper's default
was `/tmp` — inside the render pod that is pod-local storage, so the rail's own copy
was unreachable minutes later (`kubectl cp <pod>:/tmp/...flac .` → `NotFound`, pod GC'd
with `successfulJobsHistoryLimit 3`). The bytes survived in two other places, both
measured byte-identical (`sha256 d909ad91…`: `/var/lib/sunolocal/artifacts/suno-9d35527ba64645ccab967fc654681d4b.flac`
and zephyr `~/Music/acestep/suno-1792179221760-1_00001.flac`), but nothing stated which
of them the next stage reads.

The contract is ONE path, and every consuming stage reads it THERE:

| Where | Path | Notes |
|---|---|---|
| host (nexus) | `/var/lib/music-plans/<plan-stem>.<ext>` | the chart's `outHostPath`; what a bot on the host reads |
| render pod | `/plans/<plan-stem>.<ext>` | the same directory, mounted by the render CronJob |

`<plan-stem>` is the plan JSON's own file name (`/var/lib/music-plans/<stem>.json`);
`<ext>` is the container the engine produced (ace → `.flac`, fixture → `.wav`). The rail
sets `SUNOLOCAL_WRAPPER_OUT` to that mount (mining-k8s `8533861`, card `t_b21aeb51`), so
the wrapper's copy IS the deliverable.

The engine's own copies are NOT that input: `/var/lib/sunolocal/artifacts/suno-<job-key>.<ext>`
is named by the job key, not by the plan stem (it is reachable through the task's
`audio_url`), and the ComfyUI output directory on zephyr belongs to the engine.

`music/scripts/check_render_landed.py` is the executable definition: the rail runs it
after EVERY render, before it writes a success `<stem>.rendered` marker, and it exits 3
when the rail's own mount is no longer the documented host path — so a chart change
cannot move a render silently. `music/stages.yaml` carries the same contract for the
stage prompts, and the `master` stage prompt proves the file with this script before it
normalizes it.

---

## 5. Gates — `music/gates/` (executable, never grep)

Every gate is a script that EXERCISES the artifact. A gate that greps a file for a feature
name is a defect: it passes while the artifact is broken. Exit codes: 0 = PASS, 1 = FAIL
(reasons on stderr), 2 = usage error.

| Gate | Checks |
|---|---|
| `gate_quota` | reads `music/quota-ledger.json`; blocks at `hard_stop_at` 58, warns at 55 |
| `gate_lyrics_original` | parses the lyric sheet, measures sections + unique words, scans Suno markers, hash-binds the authorship claim |
| `gate_stems_present` | ffprobes every stem: ≥4 stems, non-zero bytes, duration within ±0.5 s of the master |
| `gate_loudness` | measured via `ffmpeg ebur128` (integrated loudness, LUFS; the `volumedetect` RMS ruler was retired 2026-10-16, card t_9546841b); −14 LUFS streaming / −16 sync, within ±1 |
| `gate_quality` | reviewer verdict present, reviewer model DIFFERENT from the maker, sha256-bound to the master |
| `gate_sync_ready` | two shapes (card t_5ed495eb). The accepted LANE SET and each lane's requirements are READ from `music/lanes.yaml` (`gate: gate_sync_ready` → every such lane is runnable by name; `requires:` tokens are each mapped to a check and an unmapped token FAILS the run — card t_d9983bb9). track (`sync`/`sync-documentary`/`direct-license`): stems + master + instrumental (must differ from the master) + manifest metadata + real PDF clearance doc + AI disclosure + `license_tiers` when the lane requires it. pack (`game-assets`, the lane's default): every audio file ffprobed, `pack_manifest` counts vs the files on disk, `metadata` incl. a stated sample rate verified against each file, stems mutually time-aligned, per-loop loop points with a span ≥ 2 s, every loop's seam measured, clearance + disclosure + licence |
| `gate_release_ready` | ffprobes the master, PIL-verifies the artwork, ISO 3901 ISRC syntax, manifest metadata + ai_disclosure |
| `gate_youtube_authentic` | samples and hashes frames: shot diversity, Jaccard similarity vs prior uploads, disclosure |
| `gate_loop_points` | renders the loop windows and measures junction curvature; seamless ≤ 3.0x. Single mode: `--master` + `--loop-points`. Pack mode: `--pack-dir <pack>` sweeps EVERY loop in the pack's `loop_points.json` |
| `gate_human_approval` | j_kro's gate — never auto-passes; requires a dated, sha256-bound approval record naming a human approver |

Run the acceptance matrix:

```
bash music/gates/check_gate_suite.sh
# measured 2026-10-16 on nexus: "OK: every gate passed its good artifact
# and failed its broken one"
```

The matrix is scheduled, not only documented (card t_b16b9046): the
`music-gate-matrix.timer` systemd user unit runs
`music/scripts/run_gate_matrix.sh` daily at 06:20 on nexus, which prunes +
rebuilds `$GATE_SCRATCH`, runs the suite with a pinned yaml-capable interpreter,
writes `performance/music-gate-matrix.log` + `.status.json`, and on a non-zero
run posts to the fleet alert feed and files a card on the music board. Before
that unit existed, NOTHING ran the matrix — a gate regression surfaced only when
a human happened to run the suite (the PyYAML false-BAD, t_d3b9e218).

### 5.1 The loudness ruler — one ruler, one unit

The ruler is **EBU R128 integrated loudness** (ITU-R BS.1770), target −14 LUFS streaming /
−16 sync, tolerance ±1 LUFS. Decided 2026-10-16 on card `t_9546841b`, commit `e783a96`
(host zephyr). Reason: `volumedetect` emits a plain RMS mean in dB, with no K-weighting and
no gating, so it cannot produce the LUFS unit the spec, `MANIFEST.json`
(`master_loudness_lufs`) and the pipeline's own `loudnorm=I=-14:TP=-1.0:LRA=11`
normalization all use. The two rulers disagreed by 1.2–2.6 dB on the Virtual Reflections
masters, and flop three of five verdicts.

**Migration state measured 2026-10-16 14:15** (this is why two checkouts disagree):

- zephyr: `music/gates/gate_loudness.py` measures ebur128. Docstring: "MEASURED with
  ffmpeg ebur128". `music/gates/README.md` and `brain/RULINGS.md` carry the same ruler.
- nexus: the committed gate still measures volumedetect (blob from `898e48f`). The 15
  upstream commits that hold `e783a96` have not landed here. `music/rubrics/edm.json`
  still anchors "volumedetect mean_volume, the pipeline's loudness dialect".

Do not write a volumedetect row back into this table. A volumedetect row re-introduces the
ruler/unit contradiction the card removed.

---

## 6. Quota ledger — `music/quota-ledger.json`

The 60/month standard-download cap is the pipeline's binding constraint. Suno introduced
metered downloads 2026-09-03. Suno Studio downloads are unlimited. Every export path runs
through Studio, never the standard download button.

```json
{
  "period": "2026-10",
  "standard_downloads_used": 0,
  "standard_downloads_limit": 60,
  "studio_exports": 0,
  "credits_used": 0,
  "credits_limit": 10000,
  "warn_at": 55,
  "hard_stop_at": 58
}
```

`gate_quota` reads the ledger before `generate` and before `export`. Measured 2026-10-16:

```
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

A 55/60 reading is a warning. 58 is a hard stop: route the export through Studio, or halt.

---

## 7. Human gates (j_kro's desk — never dispatched to a bot)

1. **Publish approval** — every public release. Unchanged from the existing 90-second gate.
2. **Distributor accounts** — DistroKid/TuneCore signup + annual fee = money decision.
3. **PRO registration** — SOCAN (Canadian) enrolment, needs identity documents. Path:
   `music/docs/pro-registration.md`.
4. **Sync platform accounts** — Songtradr / AudioSparx signup.
5. **Direct-licensing storefront** — domain + licence tiers + payment processor.
6. **Platform accounts that need login or OAuth** — Fiverr, Patreon, itch.io seller, Unity
   Asset Store publisher.

Per the CoS dispatch boundary: a bot must never be sent to "go get credentials."

Open human decisions on the board (2026-10-16):

| Card | Question |
|---|---|
| `t_2eaa39ba` | who owns the music board (§4.1) |
| `t_c10a8513` | two masters sit +1.1 and +1.2 LU over the streaming target: widen the window, or re-normalize them two-pass |

---

## 8. Reuse map — what existed vs what the lane added

Paths verified on both hosts unless the row says otherwise.

| Need | Existing component | Music lane |
|---|---|---|
| Board + stage driver | `scripts/automation/pipeline-driver.sh` (board-parameterized, cap 1), `scripts/automation/advance-stage.sh` | `music/stages.yaml`, `music` board |
| Gate framework | `music/gates/check_gate_suite.sh` (10-gate matrix) | 10 music gates |
| Registry + validation | — | `music/registry.py`, `music/genres.yaml`, `music/lanes.yaml` |
| Quota tracking | — | `music/quota-ledger.json`, `gate_quota` |
| Oracle / card source | — | `music/oracle.py`, `music/scheduler/music-oracle.timer` (daily 08:00, nexus) |
| Scheduler units | — | `music/scheduler/music-{oracle,policy-watch,pipeline-driver,weekly-digest}.{service,timer}` |
| Lane checks (drift guards) | — | `music/scripts/check_*.py` (stage scripts, stage advance, scheduler units, gate↔lane surface, brief figures, brief drift, brief line refs, oracle determinism, prompt style counts) |
| Lyrics | `writer` profile | `music/lyrics/`, `music/prompts/*` |
| Video render | `videobot`, `music/visuals/*.mp4` shape templates | album / mix / loop shapes |
| Review | `reviewer-deepseek` + panel | `music/rubrics/*.json`, `music/rubrics/measure.py` |
| Audio mix/master | `scripts/audio/storyteller.py` | `music/mix/master.py` (zephyr only, as of 2026-10-16) |
| Suno generation | — | `music/suno-gen.py` (both hosts — tracked on nexus from 2026-10-16; re-measured 16:15, t_e2375c5a) |
| GPU jobs | zephyr/host GPU scheduling | not wired into the music lane |
| Human review surface | content.lan (music section, card t_98c95aad) | — |

Two rows of the 2026-10-08 draft were wrong. Corrected above:

- `scripts/gates/*` (which sits in the faceless lane) does not exist on nexus.
- `scripts/audio/gpu-director.sh` does not exist in either checkout as of 2026-10-16.

---

## 9. Build order (2026-10-08 plan) — current state

1. **Registries + quota ledger** — done. 14 genres, 10 lanes, ledger live.
2. **Suno CDP generator** — `music/suno-gen.py` exists on both hosts (tracked in the
   nexus `main` from 2026-10-16; re-measured 16:15, card t_e2375c5a).
3. **Gates** — done. 10 gates, suite green.
4. **Board + driver wiring** — wired. Live dispatch is gated on card `t_2eaa39ba` (§4.1).
5. **Genre templates** — done. 14 prompt templates, 14 visual styles.
6. **Lane adapters** — package builders and prep sheets exist; first distributor upload is
   human-gated.
7. **First proof — one track per genre family end-to-end** — open (card `t_667cda4a`).

---

## 10. Automatability matrix — what self-run requires

Verified 2026-10-08. A lane with an API needs no human after one-time account setup. A lane
without one needs a Playwright adapter.

### 10.1 Full API / CLI — zero human after setup

| Surface | Mechanism | Notes |
|---|---|---|
| **itch.io** | `butler` CLI (`butler push`), plus a GitHub Action | Game assets, loops, SFX packs |
| **Gumroad** | official API — `POST /v2/products`, `POST /files/presign` | Digital downloads: sample packs, stem packs, albums |
| **Songtradr** | official API 3.0.0 + Python client (`songtradr-api-client-python`) | Sync submission, deep metadata |
| **Roblox** | `publish.roblox.com/docs/json/v1` → `UploadAudioRequest` | Game audio |
| **RouteNote** | free distribution, keep 85% | Excludes Content ID, Meta, Korean stores |

### 10.2 No API — Playwright adapter required

| Surface | Status | Mechanism |
|---|---|---|
| **DistroKid** | no official API | Playwright on the logged-in session |
| **Fab / Unreal publisher portal** | onboarding + 15-business-day review | Playwright after one-time publisher account |
| **Unity Asset Store** | publisher portal, moderation | Playwright after one-time publisher account |
| **Splice / Loopmasters / ProducerLoops** | curated submission | email/form, semi-automated |

### 10.3 Closed — do not build

Pond5, AudioJungle/Envato, Artlist, Epidemic Sound, Soundstripe, PremiumBeat, Musicbed,
**Bandcamp (banned 2026-01-13, "Keeping Bandcamp Human")**, **Beatport (banned 2026-08-12,
enforced by Beatdapp at ingestion)**, CD Baby (no AI).

Dates and sources: `brain/research/music-monetization-2026.md` §1.1, §1.4, §1.5.

### 10.4 Standing permission

j_kro (2026-10-08): "we can use api watchers to scrape or playwright and stuff like that if
necessary too." Playwright, API watchers and scraping are authorized as the mechanism of
record for any lane without an API. The automation breaks the glass. j_kro does not.

---

## 11. Self-run design — the autonomous loop

Target: an individual's self-running music business. After setup, human involvement is
limited to the approval gate (rung-configurable) and money decisions.

```
┌─ MUSIC ORACLE (daily 08:00, nexus) ───────────────────────────────────┐
│  Scores all 14 genres: lane coverage, revenue potential, trend signal,│
│  quota headroom, cadence fit. Emits scored cards to the `music` board.│
└───────────────────────────────────────────────────────────────────────┘
                              ↓
┌─ PIPELINE DRIVER (every 30 min, nexus, cap 1 bot) ────────────────────┐
│  Walks the music board's ready cards, routes stage → bot from          │
│  music/stages.yaml, enforces gates, advances or rejects.               │
│  DRY_RUN=1 while card t_2eaa39ba is open (§4.1).                       │
└───────────────────────────────────────────────────────────────────────┘
                              ↓
   brief → genre-select → lyrics → generate → curate → stems → master
        → gate → package → visual → [human-approval] → publish → track
                              ↓
┌─ PUBLISH LAYER (API-first, Playwright fallback) ──────────────────────┐
│  itch.io (butler) │ Gumroad (API) │ Songtradr (API) │ DistroKid (PW)   │
│  Uploads go PRIVATE/draft by default. A policy flag decides public.    │
└───────────────────────────────────────────────────────────────────────┘
                              ↓
┌─ ANALYST (weekly digest, Mon 06:00) ──────────────────────────────────┐
│  Revenue per genre × lane × hour. Feeds cadence weights back to the    │
│  registry (earning genres get more cadence; losers pause).             │
└───────────────────────────────────────────────────────────────────────┘
```

Also installed on nexus: `music-policy-watch.timer` (daily 07:00) scans Suno, YouTube,
DistroKid, Songtradr, itch.io and Gumroad for AI-policy changes and files an `escalate`
card on a change. It never auto-adapts.

### 11.1 The three always-on rules

1. **The scheduler runs on an ALWAYS-ON host (nexus), not zephyr.** Workstation crons pause
   when the workstation sleeps. A self-running business cannot sleep with the laptop.
2. **Event where an event exists; timer for time, drift, and absence.** Platform policy
   changes and quota resets are time-based. New-artifact detection is an event.
3. **Every open item is owned in code.** The backlog register is the carry-forward. A
   completed item moves to the changelog, or it is not done.

### 11.2 The autonomy ladder — earn it per lane

Lanes start at **advisory** and graduate. `music/autonomy.yaml` implements the ladder.

| Rung | Behaviour | Promotion evidence |
|---|---|---|
| advisory | produces, human approves each publish | — |
| supervised | publishes to private/draft, human flips public | 10 clean advisory publishes |
| monitored | publishes public, human audits weekly | 20 clean supervised publishes, zero platform strikes |
| full | publishes public, human audits monthly | 50 clean monitored publishes, revenue positive |

Promotion is proposed on the board with evidence. j_kro approves the rung change. This is
how the system earns the right to self-run rather than being handed it.

Live state measured 2026-10-16: all 10 lanes are at `advisory`. Every counter
(`clean_publishes`, `platform_strikes`, `revenue_usd`) is 0.

### 11.3 Quota-aware pacing

The 60/month standard-download cap (Studio unlimited), the YouTube one-quality-video-per
day-per-channel guard, and the anti-spam rules bound the loop. `gate_quota` runs before
every generation. The driver never outruns the quota.

### 11.4 Failure handling — self-healing, not self-stopping

From `music/autonomy.yaml` `failure_handling`:

- Platform 429/5xx → cooldown, retry with backoff (max 3 retries), log to the watcher.
- Gate failure → return to the maker with the specific finding. Never advance.
- Credential expiry → surface in the daily digest as a human-gated item. Never a bot
  hunting for credentials.
- Sustained failure → the lane pauses itself and pages the digest. It does not loop.

---

## 12. The glass-break — one-time human actions

Everything after this list is autonomous. These actions need identity, money, or a legal
agreement.

| # | Action | Why human-only | Cost |
|---|---|---|---|
| 1 | **DistroKid account** | annual fee + legal agreement | $24.99/yr |
| 2 | **Gumroad account + API token** | identity + payout setup | free |
| 3 | **itch.io account + butler API key** | identity | free |
| 4 | **Songtradr account** | identity + sync agreement | free tier |
| 5 | **SOCAN registration** | legal identity, Canadian PRO | free/join fee |
| 6 | **Payout/tax details** on each | tax law | — |
| 7 | **Approve the publish policy** — the autonomy rung per lane | creative-direction call | — |

After 1–6 exist and 7 is set, the loop runs. The system generates, gates, packages,
uploads, and reports. j_kro reviews a weekly digest and audits on the cadence the rung
allows.

The checklist deliverable (exact URL, exact fields, credential location) exists per card
`t_14d438ea`.

---

## 13. Additional lane: asset packs

j_kro: "any sort of 'assets' pack type market things too."

An asset pack is a derived product. It monetizes work already done for the sync lane.

| Product type | Surface | Automation |
|---|---|---|
| Loop packs (elemental, chiptune, jungle breaks) | itch.io (butler), Gumroad (API) | full |
| Stem packs | Gumroad, itch.io | full |
| One-shots / SFX | Gumroad, itch.io | full |
| Sample packs | Gumroad, itch.io (Splice/Loopmasters = curated) | full for own store |
| Game music asset packs | itch.io (AI Audio tag), Unity/Fab (Playwright) | itch.io full |
| Album / track bundles | Gumroad (Bandcamp banned 2026-01-13) | Gumroad |

**Packaging requirements** (from the research): loops must be seamless and click-free, with
stated BPM and key. Stems must be time-aligned. Clean WAV with a stated sample rate.
Consistent file naming. Multi-tier licences with explicit permitted use, distribution and
derivative-work rules. Vague licence language is the #1 failure mode.

**Market rates from the research:** production libraries $50–500/track; perpetual licences
$1,000–10,000; asset packs $2,500–7,500 for 5–10 tracks; indie game sync $500–15,000/track.

The asset lane is the highest-automation, lowest-gatekeeper revenue path. That makes it the
natural first lane to run at full autonomy.

**Automation — the `asset-pack` stage (2026-10-16, card t_eb079b91).** The lane had a
generator (`music/assets/pack.py`) and two gates and no stage: `music/stages.yaml` declared
14 stages and not one ran the generator, so the primary lane of all six gamer genres ended at
a master plus a manual step a human had to remember. The stage now exists and hardcodes
nothing:

* the product is declared ON THE LANE — `music/lanes.yaml` → `game-assets.derived_product`
  (stage, generator, interpreter, output convention, gates, required modules). A declared
  product whose stage does not exist FAILS `registry.py validate`, so "a generator nothing
  runs" cannot come back;
* `music/registry.py derived-for-stage --stage asset-pack --genre <g>` resolves whether THIS
  genre builds a pack from the genre's own lanes, and prints the exact command. Same selector
  shape as `gate-for-stage` (t_d9983bb9): a decision hardcoded in a prompt cannot see that the
  prompt and the registry disagree;
* position: AFTER `gate`, BEFORE `package` — a pack derives from a master the independent
  quality gate already vetted, and a pack is not a release package;
* output convention: `packages/<master-stem>-asset-pack` (repo root), the generator's own
  default, keyed to the master's stem;
* dependency answer: the interpreter is PINNED (`/usr/bin/python3`) and a check EXECUTES the
  generator's entrypoint under it rather than trusting a declaration (t_5ed495eb measured that
  the generator could not run at all when scipy was missing);
* publish is untouched: the itch.io draft goes through publishbot behind the
  `human-approval` gate, and the stage never uploads.

Guarded by `music/scripts/check_pack_stage.py`.

---

## 14. Citation map — who reads which section

Every file below cites this document. Each reference resolves to a heading in this file.

| Citing file | Section | Heading here |
|---|---|---|
| `music/genres.yaml` (header) | §2 | 2. Genre registry |
| `music/lanes.yaml` (header) | §3 | 3. Lane registry |
| `music/lanes.yaml` (`game-assets.derived_product`) | §13 | 13. Additional lane: asset packs |
| `music/registry.py` (`derived-for-stage`) | §3, §13 | 3. Lane registry, 13. Asset packs |
| `music/gates/gate_loop_points.py` | §3 | 3. Lane registry (`game-assets`) |
| `music/gates/gate_sync_ready.py` | §3, §5 | 3. Lane registry, 5. Gates |
| `music/stages.yaml` (header) | §4 | 4. Pipeline stages |
| `music/stages.yaml` (human-approval prompt) | §7 | 7. Human gates |
| `music/stages.yaml` (`asset-pack` prompt + header contract) | §13 | 13. Additional lane: asset packs |
| `music/gates/gate_loudness.py` | §5 | 5. Gates (row `gate_loudness`) |
| `music/gates/gate_release_ready.py` | §5 | 5. Gates |
| `music/gates/gate_stems_present.py` | §5 | 5. Gates |
| `music/gates/README.md` | §5, §3 | 5. Gates, 3. Lane registry |
| `music/rubrics/*.json` | §5, §13 | 5. Gates, 13. Asset packs |
| `music/autonomy.yaml` | §11.2, §11.4 | 11.2 ladder, 11.4 failure handling |
| `music/lyrics/lyrics.py` | §2, §7 | 2. Genre registry, 7. Human gates |
| `music/cards/original-lyrics-pipeline-(copyrightability).md` | all | this file, first |
| `brain/research/music-monetization-2026.md` | §1–§13 | pointer back to this file |
| `~/.hermes/profiles/music-producer/SOUL.md` | all | READ FIRST |
| card `t_a22307e9` | §11 | 11. Self-run design |

**Note on the genre briefs.** Eleven briefs under `music/briefs/` carry a paragraph titled
"Dangling reference" that states this file does not exist. Those paragraphs are dated
measurements from before 2026-10-16 14:12. They are stale. Card filed to strip them.
