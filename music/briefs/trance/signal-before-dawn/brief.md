# Brief — trance: "Signal Before Dawn"

Card: kanban `music` t_a7a7d998 · stage: brief
Oracle score: 7.8/10 · card created 2026-10-09 03:27:45
Brief written: 2026-10-16 (music-producer, run 4) · re-measured 2026-10-16 by t_a7a7d998 (§11)
Track slug: signal-before-dawn

Superseded digest: this file was sha256 `59992a334a44d63a4e2791e222330bd342c8087e580444255d82d310f6a2532b`
(14 677 B) when the oracle ruling named it. The revision below supersedes that copy, and the
figure pass of card `t_6dd13d76` (2026-10-16T17:21-05:00 CDT) supersedes
`sha256 cb9a11c10edac5303b830da725acbef882c1ce08db7ec93604a3408c772e616b` (408 lines / 23449 B).

The scorer's ruling (oracle, 2026-10-16, `music/oracle.py` @ `b2d11f7`): the NEWEST scoring
run owns the genre. This card (`t_a7a7d998`) is that run, and its true score is **7.8** —
not the 8.0 in its own title, and not the 8.3 / 8.5 on the two `done` twins (`t_6272da09`,
`t_1a6a7d74`). The 0.20 gap is WEIGHTS['trend_signal'] x (5.0 - 3.0): the premium the old
`except` branch paid to a FAILED trend fetch. Re-measured live in §11 — fetch-fails,
empty-200 and a live fetch all score 7.8, so the number is now reproducible.

This brief resolves the oracle card against the live registry and the live
generation path. Every number below comes from a command run during this stage.

## 1. Resolved registry entry

Command: `/usr/bin/python3 music/registry.py validate`
Output: `registry OK: 14 genres, 10 lanes`

`music/genres.yaml` block for trance:

| Field | Value |
|---|---|
| family | edm |
| prompt_template | prompts/trance.md (resolves) |
| visual_style | visuals/neon-horizon.md (resolves) |
| lanes | streaming, youtube-mix, direct-license, sync |
| cadence | 2/wk |
| video_shape | mix-60min |

Registry defaults that bind this track: export `studio`, stems `true`,
lyrics `human-original`, release_private `true`, gate_profile `reviewer-deepseek`.

Genre note in the registry: "Beatport BANNED (2026-08-12). Independent release +
DJ mixes only. No label path."

## 2. Target lanes and what each lane demands

From `music/lanes.yaml` and `music/autonomy.yaml`:

| Lane | Surface | Gate | Required artifacts | Autonomy rung |
|---|---|---|---|---|
| streaming | distributor (DistroKid; alt TuneCore) | gate_release_ready | ai_disclosure, isrc, metadata, master | advisory |
| youtube-mix | youtube | gate_youtube_authentic | platform-native mix-60min video | advisory |
| direct-license | own-site | gate_sync_ready | stems, license_tiers | advisory |
| sync | songtradr, audiosparx | gate_sync_ready | stems, metadata, clearance_doc, instrumental_version | advisory |

Every rung is `advisory`: clean_publishes 0, platform_strikes 0, revenue_usd 0.
No lane may publish itself. Promotion needs 10 clean advisory publishes and
j_kro's approval.

Stems are mandatory for two of the four lanes (sync, direct-license), so stems
are mandatory for this track.

## 3. Cadence and video shape

- Cadence: 2 tracks/week (registry).
- Video shape: `mix-60min` — one continuous DJ-mix video, no per-track cuts.
- Visual template `visuals/neon-horizon.md` pairs with it: night-to-dawn horizon,
  sunline pulsing on the 138 BPM kick, 60-minute continuous journey.

## 4. Intent

The theme is already fixed by two existing artifacts, so this brief does not
invent a new one.

`music/lyrics/blueprints/trance.yaml`:

> Holding on through the long stretch before dawn. Not a party song — a 3am
> promise. One voice against a big sky. The build is the meaning.

The lyric sheet for this theme exists. Title: **Signal Before Dawn**.
Music direction from `prompts/trance.md`: uplifting trance, 138 BPM, 4/4
four-on-the-floor, offbeat 16th bassline, JP-8000-style supersaw lead,
i-VI-III-VII (Am-F-C-G), 32-bar sections, DJ-friendly intro and outro, the
two-beat silence before each drop. A generation with a half-time drop, a trap
hat, or no DJ-usable intro is out of genre.

## 5. Evidence

Quota — command `python3 music/gates/gate_quota.py`:

```
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

Lyrics — command
`python3 music/gates/gate_lyrics_original.py --track-dir music/lyrics/trance/signal-before-dawn`:

```
PASS gate_lyrics_original
  track        : Signal Before Dawn (music/lyrics/trance/signal-before-dawn)
  sections     : 9
  unique words : 84
  authorship   : j_kro @ 2026-10-08T12:48:59+00:00
  suno markers : none
```

Hash binding: `sha256(lyrics.suno.txt) = e667e248627e5c985e76018d424fa1e18d33fc2379381025d7da4a98734505da`,
identical to `manifest.json`. The authorship claim is bound to the text on disk.

Audio: none. No trance audio exists. As of 2026-10-16 a trance PLAN does, and the render
rail refused it (§8):
- `/var/lib/music-plans/trance-signal-before-dawn.json` — 2511 B, re-planned 2026-10-16 16:57.
  (The 14:10 reading this section first recorded was 2434 B; the rail re-plans the track on
  every pass.) Its refusal marker is now
  `/var/lib/music-plans/trance-signal-before-dawn.refused` (written 2026-10-16 17:15) — the
  `.rendered` marker recorded at 14:18 is not on disk (re-read 17:21).
- No `.flac`, `.wav` or `.mp3` for trance exists under `/var/lib/music-plans/` or in the
  repo. The only master file on that volume is `elemental-fire-emberfall.flac`
  (11 421 612 B); `/var/lib/music-plans/loops/` holds its loop pair.
- `/var/lib/music-plans/` now holds 13 plans plus their markers: `final-round`,
  `smoke-chill-lounge`, `testplan` and ten from the 2026-10-16 queue.
- A file search for `*signal*before*dawn*` returns the lyrics dir, the brief dir and those
  two plan files. Nothing else.

## 6. The live generation path (measured, not assumed)

The engine that exists today is ACE-Step in the cluster, driven by two CronJobs
in namespace `mining`:

| Stage | Job | Schedule | Input | Output |
|---|---|---|---|---|
| plan | music-pipeline | `17 */6 * * *` | ConfigMap `music-pipeline-briefs` key `briefs.json` | `/var/lib/music-plans/<name>.json` |
| render | music-pipeline-render | `41 */4 * * *` | plans without a `.rendered` marker | audio via `music/scripts/acestep_plan.py` |

Evidence: the last render job (2026-10-16, 21 min before this run) printed
`ComfyUI up at http://comfyui-zephyr.mining.svc.cluster.local:8188` and
`done: found=3 rendered=0 skipped=3 failed=0`.

The live brief queue now holds 11 entries, and the trance entry is one of them. Read back
with `kubectl get configmap -n mining music-pipeline-briefs -o jsonpath='{.data.briefs\.json}'`
(2026-10-16 15:5x); the trance entry is:

```json
{"brief":"Signal Before Dawn. Holding on through the long stretch before dawn. ... Uplifting trance at 138 BPM in A minor.",
 "duration":417,"genre":"trance","language":"en","lyricsMode":"draft",
 "name":"trance-signal-before-dawn","title":"Signal Before Dawn"}
```

The plan CronJob then logged `skip  trance-signal-before-dawn (plan exists)` and
`done: 11/11 planned` (job `music-pipeline-t6d7ad524`). That is why the plan in §5 exists.

### Defects found while resolving this brief

**1. The checkout could not run the generate stage as written — RESOLVED 2026-10-16 14:23.**
`music/stages.yaml` tells the generate stage: "generate 2 tracks via Suno CDP
(music/suno-gen.py)". When this brief was written, no `music/suno-gen.py` existed in the
working tree of `/home/j_kro/ai-content-pipeline`; the file lived only on `origin/main`
(commit `ba28f55`, "music: instrumental mode in generation path"), while the local `main`
carried this lane's own unmerged commits.

Merge commit `ab33ad1` ("merge: reconcile the live checkout with origin/main", card
`t_8a715681`, 2026-10-16 14:23:43) joined the two lineages; its second parent is `ba28f55`.
Re-measured live 2026-10-16 15:53:54 CDT:

| Fact | Value |
|---|---|
| remote `main` (the real one) | `ba28f55` (`git ls-remote origin main`) |
| local `main` | `1a450e0` — 69 commits ahead of `origin/main`, 0 behind |
| `origin/main` an ancestor of `main`? | YES (`git merge-base --is-ancestor`) |
| `music/suno-gen.py` in the working tree | present, 42 652 B |
| `music/sunolocal/` in the working tree | present (`adapters/`, `checks/`, `GATES.md`) |
| `check_stage_scripts.py` | **PASS** — `11 referenced script path(s) all present` |

The standing check that guards this defect (`music/scripts/check_stage_scripts.py`, commit
`7f2ded8`) went FAIL -> PASS with the merge, and it stays in place as the regression. The
ahead-count is anchored to revision `1a450e0` and to the clock on purpose: this lane keeps
committing, so an unanchored count ages within minutes (it read 65 at 15:48 and 69 at 15:54
today).

The engine actually in service is still the ACE-Step cluster path in the table above; the
Suno CDP path needs a logged-in browser session on a host. One consequence is recorded and
not fixed here: local `main` is now 69 commits ahead of `origin/main` and 0 behind, so this
lane's work — including this brief — is still not on the remote. Pushing is a separate
action; no step in this brief depends on it.

**2. The oracle re-emitted every card on every run — FIXED 2026-10-16 13:09, 95 s
after this brief was corrected.** When this brief was written, `music/oracle.py`
(`create_kanban_card`) created cards with no `idempotency_key` and no check for an
open card for the same genre. Observed 2026-10-09: 14 cards at 03:27 and 14 more at
03:37 — including a second trance card, `t_1a6a7d74` (score 8.5), which duplicates
this one, and `music-oracle.timer` runs daily, so each duplicate put a whole stage
chain in flight.

Commit `ade6e87` added the guard (`open_oracle_genres` / `skip_genres`) and
`music/test_oracle_dedupe.py`. Both are in this working tree; the test file passes
12/12 (`python3 music/test_oracle_dedupe.py`, rc=0). `performance/music-oracle-runs.log`
shows the guard doing its job live:

```
2026-10-16T13:07:40 — oracle run: 14 scored, 0 created,           0 skipped (open), board_read_ok=True
2026-10-16T13:08:45 — oracle run: 14 scored, 0 created,          14 skipped (open), board_read_ok=True
```

The 13:08 run is the real one: it skipped all 14 genres instead of creating 14 more
cards. The two runs that log `0 skipped` are `--dry-run` invocations — `run_oracle`
sets `open_cards = {}` when `dry_run` is set (`music/oracle.py:439`), so a dry run
never reads the board and logs `board_read_ok=True` regardless. Nothing anomalous.

What the guard does NOT do: it cannot remove the 14 duplicate cards already on the
board from the 2026-10-09 second wave (the fixes prevent new dupes; they do not clean
up old ones). Card `t_bf0e5edd` (assignee `oracle`, now `done`) owned that cleanup and
the score conflict; the oracle's dedupe ruling has since resolved the conflict for this
genre — the surviving card is `t_a7a7d998` at the true score **7.8** (header, §11).
`t_1a6a7d74` and `t_6272da09` were pre-guard duplicates and are `done`.

**3. No music stage advanced its card's stage marker (fixed during this run).**
Every music stage prompt omitted `advance-stage.sh`, and that script hardcoded
`BOARD=faceless-youtube`, so a music card re-dispatched the same stage forever.
Commit `9c2d2d3` (card t_38e84953, another worker) added the
`advance-stage.sh {card} <next-stage> --board music` step to every stage prompt. No
action needed; recorded here so the finding is not lost.

### Repo state for this deliverable

Files under `music/briefs/trance/signal-before-dawn/`: first committed as `4daf132`,
corrected by `132a781`, re-measured by §10, re-measured again by §11 (`t_a7a7d998`).
The branch reconciliation defect 1 names is DONE (`ab33ad1`), so the checkout is no longer
diverged. The revision carrying these files is still **not** on `origin/main` — measured
2026-10-16 15:53:54: `main` @ `1a450e0` is 69 ahead / 0 behind `ba28f55`. That is a publish
step, not a blocker for this stage.

## 7. Queue entry for this track

`brief.json` beside this file is the entry for the live brief queue. Field names
and types match the live schema in
`mining-k8s/helm/charts/music-pipeline/values.yaml` (comment block above
`briefs: []`) and the observed ConfigMap payload.

- name `trance-signal-before-dawn`
- genre `trance`
- title `Signal Before Dawn`
- lyricsMode `draft` (placeholder only — see below)
- duration 417 s (240 bars at 138 BPM; the planner cap is 600 s — corrected below)

**Queueing is DONE.** It was handed off as card `t_791b48f7` (`nexus-core`), now `done`. The
live chart carries this entry under `briefs:` in
`/home/j_kro/mining-k8s/helm/charts/music-pipeline/values.yaml` (line 110, comment: "Card
t_791b48f7. 417 s = 240 bars at 138 BPM"), ArgoCD synced it, and the live ConfigMap serves
it (§6). The drift this brief reported is resolved: `values.yaml:76` now holds
`smoke-chill-lounge` too, with a comment recording that the chart read `briefs: []` while
the cluster held one entry.

**Correction — the planner cap is 600 s, not 420 s.** When this brief was written,
`music/planner/planner.py` read `MIN_DURATION_S = 30`, `MAX_DURATION_S = 420`. Commit
`52ae620` (card `t_25a6499c`) raised the cap for the registry's `loop-10min` shape; the file
now reads `MIN_DURATION_S = 30` (line 103) and `MAX_DURATION_S = 600` (line 104). The 417 s
track sits inside both, so no routing verdict changes — the quoted number was stale.

## 8. Blocker for the next stages

**This blocker is LIVE, not hypothetical — measured 2026-10-16.** The queued plan
`/var/lib/music-plans/trance-signal-before-dawn.json` carries the `--lyrics-mode draft`
scaffold: 1011 B, nine section tags, and 0 singable lines. The render rail refused it.
Refusal reproduced verbatim from the plan on disk (2026-10-16):

```
FATAL: 9 section(s) have no lyrics: Intro, Verse 1, Pre-Chorus, Chorus, Verse 2, Chorus, Bridge, Chorus, Outro.
       This is a DRAFT plan — a human writes the lines into it first.
       (--allow-empty renders anyway, for instrumental or scratch passes.)
```

The rail wrote `refused` into the marker at 14:18 and skips the plan on every later run
(`skip   trance-signal-before-dawn (already rendered)`). The human-authored sheet
(`lyrics.suno.txt`, sha256 `e667e248…`) is **not** in the plan: `plan["lyrics"]` does not
contain the sheet's first line, and the two byte counts differ (1011 B scaffold vs 1219 B
sheet). The requirement below therefore holds, and no tool satisfies it yet.

This track must not use `--lyrics-mode ai`: AI-written lyrics void the human-authorship
claim this pipeline registers with SOCAN.

So the plan for this track must carry the existing sheet verbatim. No tool does
that today: `planner.py` has no `--lyrics-file` input. Two paths exist, and the
implementer picks one:

1. Plan with `--lyrics-mode draft`, then replace `plan["lyrics"]` with the sheet
   text and verify the sha256 against the manifest.
2. Add a `--lyrics-file` input to `planner.py` (the durable fix; needs its own card).

## 9. Next stage

Stage `brief` is complete, and the brief stage is NOT re-run — the genre-keyed artifact
above already exists for all three cards this genre produced. Next: `genre-select`, the
stage after `brief` in `music/stages.yaml`. That stage resolves the genre to a complete
registry entry, verifies that every referenced lane exists in `music/lanes.yaml`, and
advances to `lyrics`.

Evidence the next worker needs is already measured in §11 and §1: `registry OK: 14 genres,
10 lanes`; the four lanes `streaming`, `youtube-mix`, `direct-license`, `sync` all present;
all four at autonomy rung `advisory`.

The one real blocker on the track is §8 — the plan on disk is refused because it carries the
draft scaffold instead of the human-authored sheet. It now has its own card: `t_e69368ff`
("the plan must carry the human-authored sheet — planner.py has no --lyrics-file"), a child of
this card, gated on its completion.

## 10. Duplicate-card verification pass — `t_1a6a7d74` (2026-10-16 13:29)

`t_6272da09` (trance, score 8.3) wrote this brief and is `done`. Card `t_1a6a7d74`
(trance, score 8.5, second oracle wave) is the duplicate. Briefs in this lane are
keyed by **genre**, so both cards resolve to this one artifact. **No second brief
was written; no second stage chain was started.** The surviving queue handoff is
`t_791b48f7` (assignee `nexus-core`, status `ready`), already created from
`t_6272da09`. Nothing was re-scored — the 8.3-vs-8.5 conflict is `t_bf0e5edd`'s call.

Every figure in this brief was re-measured this pass. Results:

| Claim | Re-measured | Verdict |
|---|---|---|
| `registry OK: 14 genres, 10 lanes` | same string, rc=0 | reproduced |
| trance entry (family edm, 4 lanes, 2/wk, mix-60min) | byte-identical to §1 table | reproduced |
| all four lanes at rung `advisory`, 0/0/$0 | same | reproduced |
| `PASS gate_quota`, period 2026-10, 0/60, studio 0 | same | reproduced |
| `PASS gate_lyrics_original`, 9 sections, 84 words, j_kro | same | reproduced |
| `sha256(lyrics.suno.txt)` = `e667e248…` matches manifest | same hash from `sha256sum` | reproduced |
| planner cap 420 s, floor 30 s | `planner.py:82-83` (`MIN_DURATION_S=30`, `MAX_DURATION_S=420`) | reproduced |
| 417 s = 240 bars at 138 BPM | 240 × 1.7391 = 417.4 s | reproduced |
| no trance plan, no trance audio | `/var/lib/music-plans/` = `final-round`, `smoke-chill-lounge`, `testplan` only; repo-wide search finds the lyrics and brief dirs only | reproduced |
| live queue = `smoke-chill-lounge` only | ConfigMap `mining/music-pipeline-briefs` key `briefs.json` read back | reproduced |
| last render job output quoted in §6 | job `music-pipeline-render-29869541`: `ComfyUI up at http://comfyui-zephyr.mining.svc.cluster.local:8188` / `skip×3` / `done: found=3 rendered=0 skipped=3 failed=0` | reproduced |
| `values.yaml` reads `briefs: []` | same; live ConfigMap holds only `smoke-chill-lounge` → drift stands | reproduced |

Two facts were **stale** and are corrected above:

1. The divergence counts in §6 defect 1 (`9c2d2d3` / 2 ahead) — the local tip is now
   `0e4fe5b` / 19 ahead. Cause: this lane keeps committing while `origin/main` stays
   at `ba28f55`. The invariant (same merge base `e278f61`, `suno-gen.py` on the
   remote and not in the working tree) is unchanged.
2. §6 defect 2 (`the oracle re-emits every card on every run`) — fixed at 13:09 by
   `ade6e87`, 95 s after this brief's `132a781` correction. The guard is verified
   live in `performance/music-oracle-runs.log`.

Also confirmed on the live rail: the plan CronJob (`music-pipeline-29869517`) logged
`skip smoke-chill-lounge (plan exists)` → `done: 1/1 planned`, and the `.rendered`
markers read `refused` for `smoke-chill-lounge` and `testplan`, `""` for
`final-round`. That is the §8 blocker in production: a `draft`-mode plan carries no
sections, so `acestep_plan.py` refuses it.

No new handoff cards: every blocker named here already has one — `t_8a715681`
(divergence), `t_25a6499c` + `t_8c5a6b91` (instrumental/BPM/render rail), `t_5a93164a`
(stage advance refused), `t_791b48f7` (queue this brief), `t_bf0e5edd` (oracle dupes).

## 11. Surviving-card pass — `t_a7a7d998` (2026-10-16 15:45–16:0x)

`t_6272da09` (trance, 8.3) wrote this brief; `t_1a6a7d74` (trance, 8.5) verified it in §10;
both are `done`. `t_a7a7d998` is the third card this genre produced — the one the oracle's
dedupe ruling names as the **surviving** card — and it carries the true score **7.8**. Briefs
in this lane are keyed by **genre**, so all three cards resolve to this one artifact. **No
second brief was written and no second stage chain was started.** The queue handoff
(`t_791b48f7`) is `done`; the plan it produced is on disk and refused (§8).

Every checkable figure in this brief was re-measured against live state this pass.

| Claim | Re-measured 2026-10-16 | Verdict |
|---|---|---|
| `registry OK: 14 genres, 10 lanes` | same string, rc=0 (`/usr/bin/python3 music/registry.py validate`) | reproduced |
| trance entry (family edm, 4 lanes, `2/wk`, `mix-60min`, Beatport note) | byte-identical to §1 | reproduced |
| all four lanes at rung `advisory`, 0 / 0 / $0 | same (`music/autonomy.yaml`) | reproduced |
| `PASS gate_quota`; period 2026-10, 0/60, studio 0 | same, rc=0 | reproduced |
| `PASS gate_lyrics_original`; 9 sections, 84 words, j_kro, no Suno markers | same, rc=0 | reproduced |
| `sha256(lyrics.suno.txt)` = `e667e248…` = the manifest's | `sha256sum` returns the same 64 hex chars | reproduced |
| `prompts/trance.md` and `visuals/neon-horizon.md` resolve | both exist; the visual pulses the sunline on the 138 BPM kick | reproduced |
| true score 7.8 | `oracle.score_genre("trance")` = 7.8 with the fetch stubbed to fail, stubbed to a 200/0-snippet page, **and** with a live fetch (quota 10.0, lanes 8.0, revenue 10.0, cadence 3.3333, policy 9.0, trend 3.0) | reproduced |
| 417 s = 240 bars at 138 BPM | 240 x (4 x 60 / 138) = 417.4 s; the plan itself carries `"duration": 417` | reproduced |
| no trance audio | no `.flac` / `.wav` / `.mp3` for trance anywhere | reproduced |
| `check_stage_scripts` FAIL (defect 1) | **PASS** — `11 referenced script path(s) all present` | **STALE — fixed by `ab33ad1`** |
| divergence `main` 19 ahead / 15 behind, merge base `e278f61` | `main` @ `1a450e0` = 69 ahead / 0 behind `ba28f55`; `origin/main` is an ancestor | **STALE — the merge landed** |
| live queue = `smoke-chill-lounge` only | 11 entries; `trance-signal-before-dawn` among them | **STALE — the queue grew** |
| `values.yaml` reads `briefs: []` | 11 entries; trance at line 110 | **STALE — the GitOps card landed** |
| no trance plan | plan exists (2511 B, re-planned 16:57), `refused` marker | **STALE — the queue ran** |
| planner cap 420 s | `MIN_DURATION_S = 30` (l.103), `MAX_DURATION_S = 600` (l.104) | **STALE — `52ae620` raised it** |

Corrections applied in place, this revision: the header (surviving card, true score 7.8,
superseded digest, the ruling), §5 (the plan and its marker), §6 (the 11-entry queue; defect 1
marked RESOLVED with live ref numbers; defect 2's owner now `done`), the repo-state note
(§6), §7 (queueing DONE; the cap), §8 (the refusal, measured verbatim), §9, and
`brief.json._duration_basis` (cap 420 -> 600).

Standing checks run after the edit, scoped to this brief:
`check_brief_figures.py --briefs music/briefs/trance/signal-before-dawn/brief.md`,
`check_brief_drift.py`, `check_brief_line_refs.py`, `check_brief_paths.py`,
`check_stage_scripts.py`, `check_oracle_board.py`, `check_oracle_determinism.py`. The
repo-wide FAILs they print live in **other** briefs (elemental-water, epic-orchestral-boss,
chiptune-8bit, anime-opening, elemental-earth, elemental-fire, activist, commentary-beds,
jungle-dnb) and are already owned by cards `t_1a5b018b`, `t_34f496d7`, `t_6dd13d76`,
`t_c5a98379`, `t_e86c2110`.

Open items this pass did NOT close, each carrying a card:

- `t_f65b0f4c` — the plan's `key` is the planner's hardcoded default `C minor`, so the queued
  trance plan carries `"key": "C minor"` while its own caption and this brief say **A minor**.
  The caption is what the engine receives, so this is wrong metadata rather than a wrong
  render; that card's acceptance is the code fix plus a regression test.
- `t_69cab80b` — a refused draft plan is never re-rendered (the marker is read as "already
  rendered"), which is why the refusal in §8 waits for a human, not another cron tick.
- `t_6599927d` — a re-emitted oracle card still carries `stage: brief` for a genre whose brief
  is already on disk. That is exactly this card's shape.
- `t_e69368ff` — NEW this pass: `planner.py` has no `--lyrics-file`, so nothing can put the
  human-authored sheet into the plan. This is §8's next real step and the only blocker on the
  track that had no card.

## 12. Declared scoring scope — machine-checked against the live rubric (card `t_00ac4f10`, 2026-10-16)

`music/scripts/check_brief_rubric_scope.py` reads the `rubric_scope` block below and
compares it, field by field, to this genre's scope COMPUTED from `music/rubrics/edm.json`
by the panel's own resolver (`music/rubrics/panel.py`: `applicable_criteria()`,
`applicable_signals()`). `edm.json` declares `applies_to` on every criterion, so both of
its genres are covered: a criterion added, dropped or re-weighted in that file fails this
brief instead of going unnoticed. The block is a claim about NOW, and the check never reads
prose.

Regenerate the block after any rubric edit — one command, no hand-edit:

    /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --print-truth trance

```json
{
  "rubric_scope": {
    "genre": "trance",
    "family": "edm",
    "rubric_version": 1,
    "pass_threshold": 7.0,
    "criteria": [
      "tempo_pocket",
      "dance_structure",
      "genre_engine",
      "low_end_discipline",
      "loudness_target",
      "arrangement_development"
    ],
    "weights": {
      "tempo_pocket": 3,
      "dance_structure": 2,
      "genre_engine": 3,
      "low_end_discipline": 2,
      "loudness_target": 1,
      "arrangement_development": 1
    },
    "weight_sum": 12,
    "reject_signals": [],
    "reject_signals_unnamed": 5
  }
}
```
