# Brief — anime-opening

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`) — DELIVERED; the chain
> resumes at `genre-select` (its resolution is §1–§3).
> **Card:** t_58072b6c (`music-oracle: anime-opening (score 7.5)`) — the surviving OPEN card for
> this genre. Live board check: `anime-opening → t_58072b6c [running]`, one open card per open
> genre, rc=0 (`music/scripts/check_oracle_board.py`, re-run in this pass — 8 open oracle genres
> at 16:00 CDT).
> **Superseded cards:** t_96821eed (score 7.55, `done`) wrote this brief; t_abaa7e2d (score 7.75,
> `done`) was its duplicate-card verification pass (§9), emitted ten minutes later by the second
> unguarded 2026-10-09 oracle run. Briefs in this lane are keyed by **genre**, not by card, so all
> three cards resolve to this one file.
> **Verification pass:** 2026-10-16T16:03-05:00 (CDT), card `t_58072b6c` — every checkable claim
> below re-measured live against the worktree, the cluster and the board. §10 records the oracle
> ruling, the corrections and what changed after the brief stage.
> **Written:** 2026-10-16T13:00-05:00 (CDT), profile `music-producer`, run 7
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `2611770` (main; the tree is shared by 6–7
> concurrent music workers and HEAD moves under this pass). Divergence measured at 16:03 CDT: 0 behind / 73 ahead of `origin/main` — clock-anchored, because the ahead count moves all day.
> **Oracle:** **true score 7.3/10** — oracle dedupe ruling 2026-10-16 (`music/oracle.py` @
> `b2d11f7`): quota headroom 10.0, lane coverage 8.0, revenue potential 10.0, cadence fit 0.0,
> policy risk 9.0, trend signal 3.0. Threshold 5.0 → produce. The title's 7.5 and the twins'
> 7.55 / 7.75 are all unreachable from the fixed scorer; §10.1 lists the reachable totals.
> **Revision:** the superseded blob was
> `0e5cdfc97c7356c72e08ecae267b684ef27ad75ae9b8fd3bfa86f9b35b7ac9cc` (337 lines / 21 236 B, the
> §9 revision, commit `afa242e`); the current digest is re-readable with
> `sha256sum music/briefs/anime-opening.md`.
> **Consumed:** the Virtual Reflections album, tracks 7–8 (registry note).

Every number and quoted string below comes from a command or a file read during
this stage. Nothing is recalled. Commands and their real output are shown.

---

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

That transcript is the live output of this pass (2026-10-16T16:00 CDT). The brief stage's
copy was one line and one clause short of live: it read `registry OK: 14 genres, 10 lanes`
where the loader now prints `…, 1 stage gate rule(s)`, and it lacked the `stage gate visual`
line. The rule it describes is *a genre with a YouTube lane gets `gate_youtube_authentic`; where
the lane is absent the answer is `none`* — `anime-opening` HAS the lane, so the gate applies.

`/usr/bin/python3` is the interpreter the systemd units invoke, and it has
PyYAML. The shell's bare `python3` is the Hermes bundled interpreter and does
not — `python3 music/registry.py validate` fails with
`ModuleNotFoundError: No module named 'yaml'` and exits 1 (re-measured in this
pass). Use the absolute path.

| Field | Value |
|---|---|
| Genre | `anime-opening` |
| Family | `anisong` |
| Prompt template | `music/prompts/anime-opening.md` — resolves; style block measures 754 bytes / 752 characters (`awk` between the first ```` ```text ```` fences, `wc -c` counts bytes — the block holds one 3-byte em dash, so the character count is 752; corrected in the §9 pass) |
| Visual style | `music/visuals/anime-opening.md` — resolves |
| Lanes | `streaming`, `sync`, `direct-license`, `youtube-gaming` |
| Cadence | 1/wk |
| Video shape | `single-4min` |
| Lyric blueprint | `music/lyrics/blueprints/anime-opening.yaml` — **PRESENT** (5 765 B, added 2026-10-16T14:31 by card `t_53da62e5`). The brief stage recorded this file ABSENT and only `activist`, `chill-lounge`, `trance` on disk; **7 of the 14 genres** now carry one (`activist`, `anime-ending`, `anime-opening`, `chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`, `trance`) |
| Lyric sheet | `music/lyrics/anime-opening/becoming/lyrics.suno.txt` — **DRAFT, UNCLAIMED** (2 063 B). Siblings in the same track dir: `manifest.json` (2 424 B, `authorship.status: incomplete`), `title.txt` (9 B, `Becoming`). `gate_lyrics_original` FAILs on 5 findings — the claim is j_kro's, see §10.3 |
| Registry note | "Anison idiom: 130-180 BPM, IV-V-iii-vi royal road, FINAL CHORUS JUMPS UP ONE KEY (the defining gesture), 90-second TV-edit density, Japanese vocals in Japanese script. Required by the Virtual Reflections album (tracks 7-8). A generation without the key-changed final chorus is OUT of genre - reject it." |

Registry `defaults:` that bind this track (`music/genres.yaml` lines 20–25, the block the key
`defaults:` opens; the brief stage cited lines 19–25 and line 19 is blank —
`check_brief_line_refs` caught it in this pass):
export `studio`, stems `true`, lyrics `human-original`, release_private `true`,
gate_profile `reviewer-deepseek`.

---

## 2. Intent

An anime opening in the idiom's own grammar: a 90-second-density showpiece that
survives being cut to a TV edit, front-loads its hook, and pays off with a final
chorus that jumps up a key. It is not a rock song with anime stickers, and it is
not a loop — the registry's `single-4min` shape and the template's "this is a
SHOWPIECE ... not a loop" fix that.

The registry names the consumer: **Virtual Reflections, tracks 7–8** ("Opening
Theme", "Becoming") — "the explosive end of the intimate→explosive arc".

### Craft contract (from `music/prompts/anime-opening.md` — the write-to spec)

| Constraint | Value |
|---|---|
| Tempo | 130–180 BPM; J-rock pocket 160–170 (template style field uses 160) |
| Harmony | IV–V–iii–vi "royal road" (王道進行) **under the chorus** |
| Form | Hook inside 15 s; no wasted bars; must survive a 90-second cut |
| Layers | Busy double-kick drums, melodic eighth-note bass, piano **and** strings over rhythm guitars, synth pads beneath, brass stabs on the chorus |
| Vocals | Japanese, in **Japanese script** (kana/kanji) — Suno mangles romaji |
| Bridge | Half-time, piano + strings + voice only. "This silence is load-bearing" |
| Final chorus | **Jumps up one key.** "The single most important line in this template" |
| Ending | Hard unison hit, cut like a TV edit to black. **A fade-out is a defect** |
| Weirdness / Style Influence | 35% / 85% |
| Exclude styles | `acoustic folk, lo-fi, trap beats, EDM drop, rap verse, ballad, English lyrics` |

A generation without the key-changed final chorus, with English lyrics, or with a
long ambient intro is out of genre. Reject it.

---

## 3. Target lanes and what each lane demands

Live reads from `music/lanes.yaml` and `music/autonomy.yaml`.

| Lane | Surface | Gate | Required artifacts | Autonomy rung |
|---|---|---|---|---|
| `streaming` | distributor (DistroKid; alt TuneCore) | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` | advisory |
| `sync` | songtradr, audiosparx | `gate_sync_ready` | `stems`, `metadata`, `clearance_doc`, `instrumental_version` | advisory |
| `direct-license` | own-site | `gate_sync_ready` | `stems`, `license_tiers` | advisory |
| `youtube-gaming` | youtube (shape `loop-10min`) | `gate_youtube_authentic` | — | advisory |

Every rung is `advisory` (clean_publishes 0, platform_strikes 0, revenue_usd 0).
No lane may publish itself.

Re-measured 2026-10-16T16:00 CDT: every cell above holds against the live
`music/lanes.yaml` and `music/autonomy.yaml` (including `youtube-gaming` having
**no** `requires:` list), and `music/scripts/check_gate_lane_surface.py` PASSes —
each gate accepts the lane `lanes.yaml` gives it. The `visual` stage's gate is now
RESOLVED from the genre's own lanes rather than assumed to be the YouTube gate
(`music/registry.py gate-for-stage`, card `t_d9983bb9`); for this genre it resolves to
`gate_youtube_authentic`, because the genre carries the `youtube-gaming` lane.

Two consequences that are decisions, not details:

1. **Stems are mandatory.** `sync`, `direct-license`, and the
   soundtradr/audiosparx package all require them. A track without stems is not
   sync-ready.
2. **The video shapes collide.** The genre's shape is `single-4min`; the
   `youtube-gaming` lane's own shape is `loop-10min`. One 4-minute showpiece
   render does not satisfy the gaming lane. Either render two shapes, or accept
   that `youtube-gaming` stays unreached. Flagged for j_kro — not resolved here.

---

## 4. Quota position (live read)

```
$ python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

Full headroom: 0 standard downloads used this period. Generate and export
**through Suno Studio only** (unlimited), never the standard download button.
Run `gate_quota` before every generation and export.

---

## 5. Gate path for the finished artifact

1. `gate_lyrics_original` — human-authored lyric sheet, sha256-bound claim
2. `gate_stems_present` — ≥ 4 stems, non-zero bytes, ±0.5 s of the master
3. `gate_loudness` — −14 LUFS streaming / −16 LUFS sync, ±1 dB
4. `gate_quality` — reviewer model **different** from the producer model
5. `gate_release_ready` (streaming) / `gate_sync_ready` (sync, direct-license)
6. `gate_youtube_authentic` (youtube-gaming)
7. `gate_human_approval` — j_kro. Never auto-passes.

---

## 6. Engine path — measured live in this pass

The brief stage left this section as a pointer to the sibling briefs and told the next stage to
verify before routing. This pass did that. Everything below is a read of the running cluster or of
the engine's own stores at 2026-10-16T16:00 CDT — not a transcript from another run.

| Fact | Measured value |
|---|---|
| Service | `sunolocal` in namespace `mining`, ClusterIP `10.43.164.190:8123` |
| Image | `localhost/sunolocal:v0.1.3` (workload `sunolocal-source`) |
| Pod | `sunolocal-source-75d58dbc97-7jfmc`, `Running`, 1 restart, age 91 min |
| Plan renderer inside the pod | `/opt/sunolocal/music/scripts/acestep_plan_direct.py`, 9 190 B — it reads `plan["bpm"]` and `plan["key"]` (sent as the engine's `keyscale`), so an explicit tempo and key travel with the plan |
| Planner rail | CronJob `mining/music-pipeline`, `17 */6 * * *`, not suspended |
| Render rail | CronJob `mining/music-pipeline-render`, `41 */4 * * *`, not suspended. It probes `COMFY_URL` first and treats an unreachable ComfyUI as a **normal** "window closed" exit 0; it then renders every `/plans/*.json` that has no marker and runs the loop-close rail on a loop claim (card `t_b21aeb51`) |
| Queue — chart | `/home/j_kro/mining-k8s/helm/charts/music-pipeline/values.yaml` → `briefs:` holds 11 entries |
| Queue — live | ConfigMap `mining/music-pipeline-briefs`, key `briefs.json` → 11 entries |
| This genre in the queue | **absent from both lists** |

Two consequences the routing stage must carry:

1. **This track is not queued, and nothing will pick it up for it.** No anime-opening entry exists
   in the chart or in the live ConfigMap, so the planner rail has nothing to plan for this genre.
   Queueing it is a deliberate step: the entry needs `bpm` and `keyscale` stated explicitly (the
   160 BPM anchor and the key are decisions this brief does not make — §10.4), because the local
   planner's `bpm` fallback for a genre is not the anchor.
2. **An OLD anime-opening plan exists on disk and is not usable as a master.**
   `/var/lib/music-plans/final-round.json` (2 831 B, 2026-10-09T03:27) carries this template's
   style block verbatim as its caption, `bpm` 160, `key` `D minor`, `duration` 90, `language` `ja`
   — and `_meta.lyrics_mode: "ai"`, `authorship: "AI-GENERATED (not eligible for a human-authorship
   claim)"`, `_meta.blueprint: false`, and `_meta.template` pointing at
   `/home/j_kro/Projects/ai-content-pipeline/music/prompts/anime-opening.md`, the OTHER checkout.
   Its `final-round.rendered` marker is 0 bytes (2026-10-09T03:37), so the pre-`v0.1.3` rail
   accepted it, but the artifact it certified is not in the live engine's job store
   (`/var/lib/sunolocal/jobs.sqlite3`, 18 jobs, earliest 2026-10-14 01:59). Do not ship it: its
   lyrics are AI-written, which voids the authorship claim this lane registers, and it predates
   every engine fix above.

---

## 7. Defects found while writing this brief (with evidence)

### 7.1 The oracle emitted 28 cards for 14 genres — FIXED here

```
$ cat performance/music-oracle-runs.log      # before this run
2026-10-09T03:27:53 — oracle run: 14 scored, 14 created, top=chill-lounge(8.9)
2026-10-09T03:37:53 — oracle run: 14 scored, 14 created, top=chill-lounge(9.1)
```

`music/oracle.py` had no guard against a genre that already had an open card, and
the score drifts between runs (this genre: 7.55 → 7.75; chill-lounge 8.9 → 9.1 →
8.4 in a dry run today), so every run re-created every card. Each duplicate put a
second full stage chain in flight.

Fixed: `open_oracle_genres()` now maps genre → open card id from
`hermes kanban --board music list --json`, `create_kanban_card()` skips a genre
that is already open, and an unreadable board **fails closed** (no cards at all,
exit 1). Regression test: `music/test_oracle_dedupe.py` (12 tests, exit 0).

Proof against the real board payload, not a fixture:

```
$ python3 (probe) … /usr/bin/python3 …
tasks in payload      : 72
status distribution   : {'blocked': 3, 'done': 31, 'ready': 26, 'running': 6, 'todo': 6}
open genres from guard: 14        (one per registry genre)
cards created by a real run: 0 (create calls: 0)
skipped (genre already open): 14
guard vs live board: PASS
```

And end to end, in the unit's own context:

```
$ systemctl --user cat music-oracle.service   # ExecStart: /usr/bin/python3 …/music/oracle.py
$ systemctl --user start music-oracle.service
Result=success  ExecMainStatus=0
$ tail -1 performance/music-oracle-runs.log
2026-10-16T13:08:45 — oracle run: 14 scored, 0 created, 14 skipped (open),
  board_read_ok=True, top=chill-lounge(8.4)
```

Re-measured in this pass (2026-10-16T16:00 CDT):

- That log line is still in `performance/music-oracle-runs.log` (line 6 of 16). The file has
  grown: the unit ran for real at **14:05:50** and created the 13 cards the board now carries,
  including THIS card (`t_58072b6c`, created 14:05:44).
- `open_oracle_genres('music')` called from **a dispatcher-worker shell** now returns a real
  mapping — `8` genres, `anime-opening → t_58072b6c` — where §9's pass measured a REFUSED board
  read. The read-only CLI path is no longer fenced (see §10.2).
- `music/scripts/check_oracle_board.py`: **8 open oracle genres, one open card each, rc=0** at
  16:00 CDT (7 by 16:07 — the count falls as cards complete under this pass). The
  28-card backlog §7.1 describes is gone; `t_bf0e5edd` (the dedupe sweep) is `done`.
- Board census at 16:00 CDT (it moves all day): **160 tasks — `done` 100, `ready` 42, `blocked` 8,
  `running` 6, `todo` 3, `archived` 1.**
- The log also gained `--dry-run` lines (15:45–15:58) that read `0 skipped (open)`. That is
  dry-run by construction, not a broken guard: `oracle.py` consults the guard only when it is not
  dry-running (`open_cards = open_oracle_genres(BOARD) if not dry_run else {}`), so a dry run
  always reports 0 created / 0 skipped with `board_read_ok=True`. Read the two lines together.

### 7.2 The scheduled units pointed at the wrong repository — FIXED here

```
$ journalctl --user -u music-oracle.service -n 4     # before this run
Oct 16 08:00:00 nexus python3[185521]: /usr/bin/python3: can't open file
  '/home/j_kro/Projects/ai-content-pipeline/music/oracle.py': [Errno 2] No such file or directory
Oct 16 08:00:00 nexus systemd[1895]: music-oracle.service: Failed with result 'exit-code'.
```

`~/Projects/ai-content-pipeline` is a different tree with no `music/` directory.
The same mispointing was installed in all four music units. The oracle failed at
08:00 daily and the driver logged "dispatched 0" all day. The repo copies of the
units already held the correct path; the install step had been missed.

Installed and verified `music-oracle.service`, `music-policy-watch.service`,
`music-weekly-digest.service` (each byte-identical to the repo file after copy;
`daemon-reload` done). Backups of the previous units:
`/home/j_kro/.hermes/profiles/music-producer/cache/scratch/unit-backup-20261016/`.

Re-measured 2026-10-16T16:00 CDT: **all four** installed units are now byte-identical to their
`music/scheduler/` copies — `music-oracle`, `music-policy-watch`, `music-weekly-digest` **and**
`music-pipeline-driver`, which was still mispointed when this section was written (§7.3). And
`music/scripts/check_scheduler_units.py` PASSes: 10 unit files match
`/home/j_kro/.config/systemd/user` and every path they name resolves. The backup directory holds
**8** files (four units × service + timer), not the 7 §9's table records — counted in this pass.

### 7.3 Two dispatchers compete for the `music` board — half closed, decision still open

`music/stages.yaml` routes by **stage** (`brief` → `producer`, `lyrics` → `writer`,
`gate` → `reviewer-deepseek`, `visual` → `videobot`, `publish` → `publishbot`).
The Hermes kanban dispatcher routes by **assignee**, and the oracle creates every
card with `--assignee music-producer`. The assignee path wins: the six oracle
cards running today were all claimed at 12:59:50 (event `claimed`, payload
`{"lock": "nexus:1113295", "run_id": 7}`) as `music-producer`, whatever their stage.

The installed `music-pipeline-driver.service` was inert and misdirected when this
section was written: it ran the pre-parameterization driver from the other tree,
which hardcoded `BOARD="faceless-youtube"` and ignored `--board music`. **That half is now
CLOSED** (card `t_41f354be`). Re-measured 2026-10-16T16:00 CDT, the installed unit reads
`ExecStart=/bin/bash /home/j_kro/ai-content-pipeline/scripts/automation/pipeline-driver.sh --board music`
with the same checkout as `WorkingDirectory`, it is byte-identical to the repo copy, and
`performance/pipeline-driver.log` shows it walking THIS board —
`card t_6599927d → stage brief` / `dispatching producer for card t_6599927d (stage brief, board music)`.

What keeps it from competing is now a deliberate switch rather than a mispointing: the unit pins
`Environment=DRY_RUN=1`, so every dispatch logs `[dry-run] would dispatch producer` and no agent
runs behind it. `music/scripts/check_scheduler_units.py` PASSes and prints that state as an OPEN
item — `NOTE music-pipeline-driver.service: Environment=DRY_RUN=1 (driver walks in dry-run;
section 4 open)`. The ownership decision is j_kro's and is carded:
**`t_19d0714b` (assignee `ops`, `blocked`)** — pick the dispatcher that owns the board, install or
retire.

### 7.4 Gaps this stage could not close — three of the four are now closed

- **The anisong lyric blueprint — CLOSED.** `music/lyrics/blueprints/anime-opening.yaml` exists
  (5 765 B, 2026-10-16T14:31, card `t_53da62e5`), so the planner no longer falls back to a BPM
  parsed out of caption prose for this genre, and the lyrics stage has a structure to scaffold
  from. A **draft, unclaimed** Japanese lyric sheet exists beside it
  (`music/lyrics/anime-opening/becoming/`, §1). What remains is the human authorship claim:
  `gate_lyrics_original` FAILs on 5 findings against that draft (§10.3), and card `t_53da62e5`
  (assignee `writer`) is `blocked` on exactly that human step — not on the blueprint.
- **The campaign document — PARTLY closed.** `campaigns/virtual-reflections/` did NOT exist when
  this section was written; it does now, and holds `ALBUM-RECORD.md` (3 807 B, 2026-10-16T14:23).
  The specific file the template cites — `campaigns/virtual-reflections/CAMPAIGN.md` — is still
  absent (`find campaigns/virtual-reflections -type f` returns `ALBUM-RECORD.md` only). The album
  record answers most of what that citation was used for: the album is on the Discord-SSO account
  `@reverb256`, is **Draft** (not published), holds 6 tracks (~20:27) and has id
  `21e76d85-15f3-42d7-92a6-cf8a35248795` — §10.4.
- **`music-policy-watch.service` — fixed, not yet proven.** The unit's `TimeoutStartSec` was
  raised 300 → 1800 (card `t_75aacf8b`), and the repo unit now records why: the analyst oneshot is
  a FULL agent run (web searches across six platforms) and 300 s killed it before it could finish.
  The last attempt still failed the old way — journal `Oct 16 07:05:00 …
  start operation timed out. Terminating.` / `status=130`, 5 min 2.932 s wall, the same shape as
  Oct 15 — but that attempt PREDATES the fix and no run has happened since. Treat the longer
  timeout as **unproven** until the next 07:00 run, and do not restate "will still fail".
- **The Virtual Reflections masters for tracks 7–8 — answered, with a refinement.** The album
  record (§10.4) lists six tracks and no track 7 or 8, so no album master for the anime-opening
  pair exists yet — nothing is at risk of being duplicated by generating. But the GENRE does have
  one accepted plan on disk from the pre-`v0.1.3` rail, `final-round.json`, carrying AI lyrics
  (§6 item 2). It is not the album's master and must not ship as one.

---

## 8. Recommended next stage

**`lyrics` → `writer`**, not `genre-select`: this brief already performs the
resolution `genre-select` would (§1–§3). The advance marker this pass posts is still
`stage: genre-select` — that is the next stage `music/stages.yaml` declares after `brief`, so it
is what the driver's chain expects, and for this genre it is a re-verification of work already
done here rather than new work.

The lyrics stage's deliverable is **partly on disk already**: the anisong blueprint
(`music/lyrics/blueprints/anime-opening.yaml`) is DELIVERED, and a Japanese draft sheet with the
royal road under the chorus and a marked, key-changed final chorus section is DELIVERED
(`music/lyrics/anime-opening/becoming/lyrics.suno.txt`) — but it is **unclaimed**: no human has
authored or approved it, `authorship.status` is `incomplete`, and the gate records 5 findings
against it (§10.3). That claim is the writer stage's remaining job and it needs j_kro.
`--lyrics-mode ai` is forbidden for this genre: the copyright path is the point, the registry
default is `lyrics: human-original`, and the one plan the genre has on disk that used `ai` lyrics
is exactly why it cannot ship (§6 item 2).

Then, in order: `generate` (2 takes, Suno CDP, Studio export only — after
`gate_quota`), `curate`, `stems`, `master`, `gate` (different model),
`package`, `visual`, `publish` (PRIVATE / draft only — never public without
j_kro's approval), `track`.

## 9. Verification pass — the duplicate card `t_abaa7e2d` (2026-10-16 13:36)

This brief is keyed by genre, so the twin oracle card `t_abaa7e2d` (`score 7.75`) resolves to
this same file. It closes as a duplicate after re-measuring every checkable claim against live
state. Measured, not asserted:

| Claim | Re-measured how | Result |
|---|---|---|
| Artifact identity | `sha256sum`; `git show ade6e87:…`; `git status --porcelain` | 268 lines / `13120 B`, `sha256 539fae3f…`, disk == `HEAD` == `ade6e87`, tree clean |
| Registry 14 genres / 10 lanes | `/usr/bin/python3 music/registry.py validate` | OK — identical genre and lane lists, `period 2026-10, standard 0/60`. **t_58072b6c: the transcript has since gained `, 1 stage gate rule(s)` and the `stage gate visual:` line — §1 now carries the live output** |
| Genre row: family `anisong`, lanes `[streaming, sync, direct-license, youtube-gaming]`, cadence `1/wk`, shape `single-4min` | `music/genres.yaml` read live | exact match, including the quoted registry note character for character (re-checked character for character in this pass — `music/genres.yaml` lines 139–146) |
| Registry `defaults:` | `music/genres.yaml` lines 20–25 | `export: studio`, `stems: true`, `lyrics: human-original`, `release_private: true`, `gate_profile: reviewer-deepseek` — match. **t_58072b6c: §1 cited 19–25 and line 19 is blank; `check_brief_line_refs` caught it and §1 now cites 20–25** |
| Template and visual resolve | `stat` | `music/prompts/anime-opening.md` 6578 B, `music/visuals/anime-opening.md` 2111 B — both present, sizes re-measured identical |
| Style block is the first `text` fence pair | fence scan | 2 ```` ```text ```` blocks in the template; the first is the style field. **t_58072b6c: re-measured 754 bytes / 752 characters (one 3-byte em dash), and the template header's own `752/1000 chars` claim matches — `check_prompt_style_counts` PASSes** |
| Blueprint absent | `ls music/lyrics/blueprints/` | `activist.yaml`, `chill-lounge.yaml`, `trance.yaml` only — match **AT 13:36**. **t_58072b6c: FALSE NOW — the genre's own `anime-opening.yaml` (5 765 B) landed at 14:31 and the directory holds 7 blueprints; §1 and §7.4 corrected** |
| Gate path | `music/gates/` | all nine scripts present: `gate_lyrics_original`, `gate_stems_present`, `gate_loudness`, `gate_quality`, `gate_release_ready`, `gate_sync_ready`, `gate_youtube_authentic`, `gate_human_approval`, `gate_quota`. **t_58072b6c: still all present, plus a tenth, `gate_loop_points.py`** |
| Lane gates and `requires` lists | `music/lanes.yaml` | `streaming` → `gate_release_ready` (`ai_disclosure, isrc, metadata, master`); `sync` → `gate_sync_ready` (`stems, metadata, clearance_doc, instrumental_version`); `direct-license` → `gate_sync_ready` (`stems, license_tiers`); `youtube-gaming` → `gate_youtube_authentic` — exact, re-read in this pass |
| The shape collision | `music/genres.yaml` + `music/lanes.yaml` | genre `single-4min`, `youtube-gaming` lane `loop-10min` — the collision in §3 stands |
| Every rung `advisory`, 0 publishes / 0 strikes / $0 | `music/autonomy.yaml` | exact for all four lanes, re-read in this pass |
| Quota `PASS`, 0/60, warn 55, hard_stop 58 | `music/gates/gate_quota.py` | reproduced exactly in this pass (`/usr/bin/python3` rc=0) |
| §4's transcript runs with the bare `python3` that §1 warns against | ran it literally on nexus | reproduced, `rc=0` — `gate_quota` needs no PyYAML, so the trap is latent, not active; §1's warning is real (`python3 music/registry.py validate` → `ModuleNotFoundError: No module named 'yaml'`, rc=1). Same trap the chill-lounge duplicate (`t_4c838339`) recorded. **t_58072b6c: both halves re-measured — bare `python3 gate_quota.py` rc=0, bare `python3 registry.py validate` rc=1** |
| Craft contract (key-changed final chorus, royal road, 90-second density, Japanese script, no fade) | `music/prompts/anime-opening.md` lines 8, 14, 19, 68, 77–78, 81, 123, 126–127 | every quoted requirement present in the template |
| Consumer names ("Opening Theme", "Becoming") | template lines 6–7 | quoted verbatim from the template. **t_58072b6c: the lyric sheet's `title.txt` reads `Becoming`** |
| 28 cards for 14 genres | `performance/music-oracle-runs.log` | `03:27:53 — 14 created` and `03:37:53 — 14 created` — 28, match. **t_58072b6c: both lines still in the file (lines 2 and 4 of 16); the log has since grown to 16 lines** |
| Dedupe guard and its test | `music/test_oracle_dedupe.py`; `music/oracle.py:119,436–446`; oracle journal | `Ran 12 tests … OK` (rc=0); `open_oracle_genres()` and the fail-closed read present; unit `Result=success ExecMainStatus=0` at 13:08:45 with `0 created, 14 skipped (open), board_read_ok=True`. **t_58072b6c: 12 tests OK rc=0 re-run; the unit's 14:05:50 run is the one that created THIS card (13 created, 1 skipped)** |
| Fail-closed behaviour | ran `open_oracle_genres('music')` from a worker shell | board read refused (`delegate_task child contexts cannot mutate Kanban tasks or boards`) → guard returned `None` → `would fail closed (0 cards created)` — verified live, not by reading the code. **t_58072b6c: NOT REPRODUCIBLE ANY MORE — the same call from a worker shell now RETURNS a mapping (8 genres, `anime-opening → t_58072b6c`), so the read-only CLI path is no longer fenced. The fail-closed path was re-proven the other way: `open_oracle_genres('no-such-board')` → `None` (§10.2)** |
| Scheduler path fix (§7.2) | `sha256sum` of each installed unit vs `music/scheduler/<unit>` | `music-oracle`, `music-policy-watch`, `music-weekly-digest` byte-identical to the repo copies; `music-pipeline-driver` still differs (installed `ExecStart` → `~/Projects/ai-content-pipeline/…`) — §7.2 and §7.3 stand **AT 13:36**. **t_58072b6c: all FOUR are byte-identical now, and `check_scheduler_units` PASSes (10 files) — §7.2/§7.3 corrected** |
| The 08:00 daily failure | `journalctl --user -u music-oracle.service --since 07:50 --until 08:15` | `08:00:00 Main process exited, code=exited, status=2/INVALIDARGUMENT` / `Failed with result 'exit-code'` — match. **t_58072b6c: history; the unit's last run (14:05:50) is `Result=success ExecMainStatus=0`** |
| Driver "dispatched 0 all day" | `performance/pipeline-driver.log` | `13:04:32 … dispatched 0, running 0/1` and `13:28:19 … dispatched 0` — match. **t_58072b6c: the log now shows the driver walking the music board in dry-run (`16:00:12 card t_6599927d → stage brief` / `[dry-run] would dispatch producer`); the 0 is `DRY_RUN=1`, not a mispointing — §7.3** |
| Unit backups kept | `ls …/scratch/unit-backup-20261016/` | 7 files, 13:07 — match. **t_58072b6c: the directory holds 8 files (4 units × service + timer) — §7.2 corrected** |
| `music-policy-watch` still times out | `systemctl --user show` + journal | `Result=timeout`, `ExecMainStatus=130`, 5 min 2.932 s wall (2026-10-16 07:05:03) — match, and its own log file was never written. **t_58072b6c: `TimeoutStartSec` is 1800 in both the repo and installed unit now (t_75aacf8b); that 07:05 failure PREDATES the fix and no run has happened since — unproven, see §7.4** |
| `campaigns/virtual-reflections/` absent | `find . -iname '*virtual*'` | no output — match **AT 13:36**. **t_58072b6c: FALSE NOW — `campaigns/virtual-reflections/ALBUM-RECORD.md` (3 807 B) landed at 14:23; the template's cited `CAMPAIGN.md` is still absent — §7.4** |
| VR masters for tracks 7–8 | `find` for `opening-theme` / `becoming` / `virtual-reflection` | no output — §7.4's open question is answered: no master exists, so nothing can be duplicated by generating. **t_58072b6c: refined — the album record lists 6 tracks and no track 7/8 (nothing to duplicate), but the GENRE has one accepted pre-`v0.1.3` plan on disk (`/var/lib/music-plans/final-round.json`, AI lyrics, 90 s) that must not ship — §6 item 2** |
| Live engine | `kubectl get cronjob -n mining`; ConfigMap `music-pipeline-briefs` | `music-pipeline` (`17 */6 * * *`) and `music-pipeline-render` (`41 */4 * * *`) both live, not suspended; the queue holds `smoke-chill-lounge` only — §6's "verify, do not trust" is discharged. **t_58072b6c: schedules and suspend state identical; the queue holds 11 entries in BOTH the chart and the ConfigMap, and this genre is in neither — §6 carries the full measured route** |

**One correction came out of the pass, applied in place:** §1 said the style block "measures
754 chars". The measurement is real and the number is what the stated pipeline prints, but
`wc -c` counts **bytes**, and the block holds one 3-byte em dash (`—`), so the block is 754
bytes and **752 characters**. The label is corrected; zero decision impact. This is the second
known instance of the same unit-label class in this lane — `music/briefs/commentary-beds.md`
carries the first ("4133 B" for 4133 characters, both directions of the same confusion). Both
are now cited in `t_55379aba`.

**Expected drift, not a defect:** §7.1's board snapshot (72 tasks; `done 31 / ready 26 /
running 6 / todo 6 / blocked 3`) has moved with the day's completions. Live at 13:36 it was 95
tasks — `done 50`, `ready 31`, `running 2`, `todo 7`, `blocked 4`, `archived 1` — and at
16:00 CDT (this pass) **160 tasks: `done` 100, `ready` 42, `blocked` 8, `running` 6, `todo` 3,
`archived` 1**. The eight pre-guard oracle duplicates this paragraph recorded are **cleared**:
`t_bf0e5edd` (the dedupe sweep) is `done`, and `check_oracle_board.py` found 8 open oracle
genres carrying exactly one open card each at 16:00 CDT (7 by 16:07). No j_kro decision was needed
for that either.

**One card created — for a gap, not a blocker.** Every blocker this brief names has an owner,
and the stage handoff exists: `t_53da62e5` (assignee `writer`, parent `t_96821eed`) owns the
anisong blueprint plus the original Japanese lyric sheet — exactly the `lyrics` advance §8
recommends. Live status of every card this brief names (board read at 16:00 CDT):
`t_53da62e5` **blocked** — the blueprint and the draft sheet are DELIVERED; the open half is the
human authorship claim, which is j_kro's. `t_bf0e5edd` **done** (oracle duplicates),
`t_41f354be` **done** and `t_75aacf8b` **done** (scheduler checkout and profile path),
`t_8a715681` **done** (diverged checkout), `t_5a93164a` **done** (stage advance refused),
`t_bae1a3e1` **done** (the worker-shell CLI fence — see the fail-closed row above),
`t_55379aba` **done** (the figure check this pass created), and `t_19d0714b` **blocked**
(assignee `ops` — which dispatcher owns the board; §7.3).

What had no owner was the missing check: this lane cannot recompute the evidence figures in a
brief, which is how §1's unit label survived a write, a commit and a completion. Created
`t_55379aba` (assignee `nexus-core`, parent this card) for a deterministic figure check that
must fail against the pre-correction revisions of both known instances. FAILURE → TEST: the
incident now has its check, and the check is not self-assigned.

---

## 10. Verification pass — the surviving card `t_58072b6c` (2026-10-16 16:03 CDT)

This brief is keyed by **genre**, so all three anime-opening oracle cards resolve to this one file.
This pass belongs to the surviving card: it wrote **no second brief** and started **no second
chain**. It re-measured every checkable claim in the file against live state, corrected the claims
that had aged in place, and applied the oracle's dedupe ruling. Live board check at 16:00 CDT:
`anime-opening → t_58072b6c [running]`, one open card per open genre,
`music/scripts/check_oracle_board.py` rc=0.

### 10.1 Oracle ruling applied — true score 7.3; the title's 7.5 is unreachable

Reproduced with the repo's own scorer (`music/oracle.py` imported as a module; `load_registry()`
returns `{"genres": …, "lanes": …}`, `load_quota()`, then `score_genre("anime-opening", …)`):

```
quota_headroom 10.0 (w .25)   lane_coverage   8.0 (w .20)   revenue_potential 10.0 (w .20)
cadence_fit     0.0 (w .15)   policy_risk     9.0 (w .10)   trend_signal       3.0 (w .10)
WEIGHTS sum 1.0               TOTAL 7.3        base without trend 7.0
reachable by trend outcome: 7.3  7.44  7.58  7.72  7.86  8.0
```

A live `--dry-run` agrees: `anime-opening: 7.3/10`, with
`warn: trend fetch failed for anime-opening (URLError(TimeoutError('timed out'))); scoring it as no
signal (3.0)`. The title's **7.5 = 7.0 + 5.0 × 0.10** — the premium the pre-`b2d11f7` `except`
branch paid to a FAILED trend fetch. It is not in the reachable set, and neither are the superseded
twins' 7.55 and 7.75. `check_oracle_determinism.py` PASSes rc=0.

Provenance, measured from the board and the oracle's own log: this card was created
**2026-10-16T14:05:44** by the unit run logged at **14:05:50** (`14 scored, 13 created, 1 skipped
(open)`, journal `Result=success`). That run executed the pre-`b2d11f7` `oracle.py` (mtime 14:15),
which is why its body carries 7.5. The 2026-10-09 pair (`t_96821eed` 7.55, `t_abaa7e2d` 7.75) was
the double emission; this card is the third and NEWEST scoring run, so it owns the genre under the
scoring gate. Threshold 5.0 → produce either way: the ruling corrects the number, not the decision.

### 10.2 Corrected in place

1. **Header** — names `t_58072b6c` as the surviving card, records both superseded cards, the 7.3
   ruling with its components, the superseded digest (`0e5cdfc9…`), and that the chain resumes at
   `genre-select`. It previously named the 2026-10-09 writer card and the 7.55 score.
2. **§1** — the registry transcript was one line and one clause short of live
   (`1 stage gate rule(s)`, the `stage gate visual:` line); the block is refreshed from live output.
3. **§1 table** — the lyric-blueprint row said **ABSENT** ("only `activist`, `chill-lounge`,
   `trance` exist"). FALSE now: the genre's own blueprint exists (5 765 B, card `t_53da62e5`) and
   the census is **7 of the 14**. A lyric-sheet row was added for the draft that also exists.
4. **§1 citation** — `music/genres.yaml` "lines 19–25" → **lines 20–25**.
   `check_brief_line_refs` FAILed on it (`BLANK OPEN — line 19 is empty`); §9's own table had
   already written 20–25, so the two disagreed. This is the defect this pass was able to FIX.
5. **§3** — added the measured note that every cell holds live, and that the `visual` stage's gate
   is resolved from the genre's own lanes (`t_d9983bb9`), which `check_gate_lane_surface` PASSes.
6. **§6** — was "another run's report, verify before routing". Replaced with the measured route:
   service/image/pod, both live CronJobs and what the render rail does, the queue in both places
   (11 entries) and the fact that **this genre is in neither**, plus the pre-`v0.1.3`
   `final-round.json` plan that must not ship.
7. **§7.1** — added the live board census, the guard's live output, the 14:05:50 run that created
   this card, and the reading rule for the log's new `--dry-run` lines.
8. **§7.2** — all four units are byte-identical now (the driver was the holdout); the backup
   directory holds 8 files, not the 7 §9 recorded.
9. **§7.3** — the mispointing is CLOSED (`t_41f354be`); the driver now walks the music board with
   `DRY_RUN=1`, which is what keeps it from competing. The ownership decision is `t_19d0714b`.
10. **§7.4** — blueprint CLOSED; campaign directory PARTLY closed (`ALBUM-RECORD.md` exists,
    `CAMPAIGN.md` still absent); the policy-watch timeout is fixed but unproven; the VR-master
    question is answered with the `final-round.json` refinement.
11. **§8** — the lyrics deliverable is partly on disk; the remaining half is the human claim, and
    the advance marker posted is `genre-select` (the stage the driver's chain declares next).
12. **§9** — every row whose Result cell claimed "match" against the present now carries its 16:00
    re-measurement, and the two paragraphs after the table carry the live board census and the live
    status of every card this brief names.

### 10.3 The lyrics state — measured, and it is the real blocker

`gate_lyrics_original` against `music/lyrics/anime-opening/becoming` FAILs with five findings:

```
- authorship.status='incomplete'; expected 'human-original'
- no named human author in authorship.authors
- authorship claim is undated
- authorship.ai_assist is empty — the claim must state what the AI did and did not do
- manifest.files['lyrics.suno.txt'] has no sha256 — claim not recorded via 'lyrics.py claim'
```

That is the intended state for an unclaimed draft, not a defect: the manifest records
`draft.status: "draft-unclaimed"` and `suno_generated_lyrics: false`, and names the claim command
(`/usr/bin/python3 music/lyrics/lyrics.py claim --track-dir music/lyrics/anime-opening/becoming
--author "j_kro"`). The words are Japanese, in script, with the royal road under the chorus and a
marked `[Final Chorus — KEY CHANGE UP ONE SEMITONE/TONE]` section — the genre's defining gesture is
in the draft. Nothing here may be replaced by AI lyrics: that is exactly what voids the claim.

### 10.4 Still open — not this card's to close

- **The human authorship claim** on the draft sheet (§10.3). j_kro's.
- **The key is not decided.** No anime-opening key is researched in this brief or in the blueprint;
  the one plan on disk carries `D minor`, which came from the old planner, not from a decision. A
  queue entry must state `keyscale` explicitly (§6 item 1) — that value is j_kro's.
- **Tempo is anchored, not decided per track.** The template's style field says 160 BPM (the
  J-rock pocket inside the 130–180 genre range); a queue entry must state `bpm: 160` explicitly or
  the planner's fallback applies.
- **Queueing.** This genre is in neither the chart nor the live ConfigMap; queueing it is
  deliberate work with the two values above.
- **The shape collision** (§3): genre `single-4min` vs the `youtube-gaming` lane's `loop-10min` —
  one render or two is still j_kro's call.
- **Stems, master, package, clearance doc and `license_tiers`** do not exist for this track;
  `curate` onward and both stem lanes are genuine first work.
- **The dispatcher ownership decision** `t_19d0714b` (§7.3).

### 10.5 Checks run on the committed content

This brief, run per-brief at 16:09 CDT against the committed content:

```
PASS check_brief_figures      8 recomputed figure(s) for this brief, 20 skipped     rc=0
PASS check_brief_drift        1 live count for this brief (0 behind / 77 ahead,
                              14 genres, 7 blueprints)                              rc=0
PASS check_brief_line_refs    6 cited line range(s) resolve and hold, 1 anchored skip rc=0
```

Repo-wide, at the same 16:09 CDT (these move as other workers commit):

```
PASS check_brief_drift        15 live count(s) across 14 briefs                      rc=0
PASS check_brief_paths        22 `mining-k8s/...` citations across 14 briefs resolve  rc=0
PASS check_prompt_style_counts 15 declared lengths / 14 templates                    rc=0
PASS check_brief_bpm_solutions 5 styleWeight claim(s) buy the BPM they state          rc=0
PASS check_stage_scripts      11 referenced script path(s) all present               rc=0
PASS check_gate_lane_surface  every gate accepts the lanes lanes.yaml gives it        rc=0
PASS check_stage_advance      12 producing stages advance reachably, 2 human gates   rc=0
PASS check_scheduler_units    10 unit file(s) match; every named path resolves        rc=0
PASS check_oracle_board       6 open oracle genres, one open card each                rc=0
PASS check_oracle_determinism failed fetch never outscores an empty success           rc=0
PASS gate_quota               period 2026-10, standard 0/60, studio 0                 rc=0
```

Fail-before / pass-after, both measured in this pass — and the second one is the checks doing
their job on THIS file:

```
BEFORE  check_brief_line_refs  FAIL: music/briefs/anime-opening.md:54  `music/genres.yaml`
                               lines 19–25  BLANK OPEN — line 19 is empty            rc=1
AFTER   check_brief_line_refs  PASS (8 ranges, 1 anchored skip)                        rc=0

BEFORE  check_brief_drift      FAIL: music/briefs/anime-opening.md:18  claimed
                               "0 behind / 73 ahead"  measured 0 behind / 74 ahead
                               [STALE DIVERGENCE]                                     rc=1
AFTER   check_brief_drift      PASS — the claim is now clock-anchored on its own line rc=0
```

The drift FAIL was a claim this pass wrote: an unanchored divergence count in the new header,
caught within the same pass and anchored to `16:03 CDT`. That is the intended behaviour — an
unanchored count is a claim about now, and now moves (0 behind / 73 ahead at 16:03, 74 ahead
four minutes later).

Two repo-wide FAILs were live in OTHER briefs at 16:09 CDT. Reported, not touched here — this
pass stages one file. Each is a concurrent worker's file, and each is the same class this brief
just cleared for anime-opening:

```
FAIL check_brief_figures       `music/briefs/elemental-water.md`    — a figure no longer matches
FAIL check_brief_line_refs     `music/briefs/chiptune-8bit.md` and `music/briefs/elemental-fire.md`
                               — cited ranges that open on a blank line
```

A third one this pass saw, `check_brief_bpm_solutions` on `music/briefs/elemental-earth.md`, was
PASSing again by 16:09 — the shared tree moves under every run, which is why every figure above
carries its clock.

Quoted without their figures and ranges on purpose: a check's own output, pasted whole, is a
fresh claim about live state. This pass proved that the hard way — the first version of this
block pasted those three lines verbatim, and two of them became claims about THIS brief:

```
BEFORE  check_brief_figures    FAIL: this brief — a pasted foreign FAIL line named another
                               brief's file and carried its line counts, so both were
                               recomputed against that brief and neither matched          rc=1
BEFORE  check_brief_line_refs  FAIL: this brief — the same pasted block carried a
                               planner.py range that opens on a blank line (BLANK OPEN)   rc=1
AFTER   both PASS — the quotation names each brief and the CLASS that failed, with no
        figure and no line range for a checker to recompute                              rc=0
```

That is the checks catching a claim the pass wrote about someone else's artifact — the same
shape as the drift FAIL above, and it is why this block quotes classes and not numbers.

### 10.6 What this pass did not do

It wrote no second brief, started no second chain, changed no registry value, gate, plan, cluster
config or quota ledger, and touched exactly one file: `music/briefs/anime-opening.md`. The advance
marker it posts is `stage: genre-select`.

hotspot: `music/briefs/` — 6–7 concurrent `music-producer` workers commit to one shared tree. HEAD
moved under this pass and `music/briefs/activist.md`, `music/briefs/epic-orchestral-boss.md`,
`music/briefs/chiptune-8bit.md`, `music/briefs/elemental-earth.md`, `music/briefs/jungle-dnb.md`
and `music/briefs/trance/signal-before-dawn/brief.md` were dirty from other workers while it ran.
Every write here needs a path-scoped `git add`; this pass staged only this genre's file.

## 11. Declared scoring scope — machine-checked against the live rubric (card `t_00ac4f10`, 2026-10-16)

`music/scripts/check_brief_rubric_scope.py` reads the `rubric_scope` block below and
compares it, field by field, to this genre's scope COMPUTED from `music/rubrics/anisong.json`
by the panel's own resolver (`music/rubrics/panel.py`: `applicable_criteria()`,
`applicable_signals()`). The anisong family is the one whose two genres do NOT score the
same set — `tv_edit_density` is scoped to the opening and one reject signal is scoped to
each — so this block is a per-genre claim, and a change in that scoping fails this brief
instead of going unnoticed. The block is a claim about NOW, and the check never reads prose.

Regenerate the block after any rubric edit — one command, no hand-edit:

    /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --print-truth anime-opening

```json
{
  "rubric_scope": {
    "genre": "anime-opening",
    "family": "anisong",
    "rubric_version": 1,
    "pass_threshold": 7.0,
    "criteria": [
      "tempo_idiom",
      "royal_road",
      "final_chorus_key_change",
      "tv_edit_density",
      "japanese_vocals",
      "loudness_target"
    ],
    "weights": {
      "tempo_idiom": 3,
      "royal_road": 3,
      "final_chorus_key_change": 3,
      "tv_edit_density": 2,
      "japanese_vocals": 2,
      "loudness_target": 1
    },
    "weight_sum": 14,
    "reject_signals": [
      "opening_no_key_change"
    ],
    "reject_signals_unnamed": 3
  }
}
```
