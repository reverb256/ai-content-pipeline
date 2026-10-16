# Brief — trance: "Signal Before Dawn"

Card: kanban `music` t_6272da09 · stage: brief
Oracle score: 8.3/10 · card created 2026-10-09 03:27:45
Brief written: 2026-10-16 (music-producer, run 4)
Track slug: signal-before-dawn

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

Audio: none. No trance audio exists anywhere.
- `/var/lib/music-plans/` (nexus) holds `final-round.json`, `smoke-chill-lounge.json`,
  `testplan.json` and their `.rendered` markers. No trance plan.
- A file search for `*signal*before*dawn*` returns the lyrics directory only.

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

The live brief queue holds one entry today:

```json
[{"brief":"a late-night kitchen where someone finally stops working and just listens to the rain",
  "genre":"chill-lounge","lyricsMode":"draft","name":"smoke-chill-lounge","title":"Kitchen Light"}]
```

### Defects found while resolving this brief

**1. The checkout cannot run the generate stage as written.** `music/stages.yaml`
tells the generate stage: "generate 2 tracks via Suno CDP (music/suno-gen.py)".
No `music/suno-gen.py` exists in the working tree of `/home/j_kro/ai-content-pipeline`,
and the file never appears in the history of the local `main` branch. It does exist
on `origin/main`, added by commit `ba28f55` ("music: instrumental mode in generation
path", 2026-10-14, card t_82ed3b8a).

Measured 2026-10-16 13:0x, after a concurrent worker fetched:

| Ref | Tip | Gap |
|---|---|---|
| local `main` | `9c2d2d3` | 2 commits ahead of the merge base `e278f61` |
| `origin/main` | `ba28f55` | 15 commits ahead of the merge base `e278f61` |

The lineages have diverged. The local checkout — the tree the systemd
`music-pipeline-driver.service` runs against — is missing 15 commits of this lane's
own work (`music/suno-gen.py`, `music/sunolocal/`, the instrumental-mode handling),
while the stage map assumes that work is present.

Fix: reconcile the branches (merge `origin/main` into `main`), not "delete the
reference". The engine actually in service is still the ACE-Step cluster path in the
table above; the Suno CDP path needs a logged-in browser session on a host.

**2. The oracle re-emits every card on every run.** `music/oracle.py`
(`create_kanban_card`) creates board cards with no `idempotency_key` and no check for
an open card for the same genre. Observed 2026-10-09: 14 cards at 03:27 and 14 more
at 03:37 — including a second trance card, `t_1a6a7d74` (score 8.5, still `ready`),
which duplicates this one. The `music-oracle.timer` runs daily, so the board grows by
~14 cards per day and each duplicate card is independently dispatched.

**3. No music stage advanced its card's stage marker (fixed during this run).**
Every music stage prompt omitted `advance-stage.sh`, and that script hardcoded
`BOARD=faceless-youtube`, so a music card re-dispatched the same stage forever.
Commit `9c2d2d3` (card t_38e84953, another worker) added the
`advance-stage.sh {card} <next-stage> --board music` step to every stage prompt. No
action needed; recorded here so the finding is not lost.

### Repo state for this deliverable

Commit `4daf132` on local `main`, files under `music/briefs/trance/signal-before-dawn/`.
It is **not** on `origin/main` (local `main` is 2 ahead, 15 behind). Pushing it needs
the branch reconciliation in defect 1.

## 7. Queue entry for this track

`brief.json` beside this file is the entry for the live brief queue. Field names
and types match the live schema in
`mining-k8s/helm/charts/music-pipeline/values.yaml` (comment block above
`briefs: []`) and the observed ConfigMap payload.

- name `trance-signal-before-dawn`
- genre `trance`
- title `Signal Before Dawn`
- lyricsMode `draft` (placeholder only — see below)
- duration 417 s (240 bars at 138 BPM; planner cap is 420 s)

Queueing is a GitOps change in another repo, so it is handed off, not done here:
add the entry under `briefs:` in
`/home/j_kro/mining-k8s/helm/charts/music-pipeline/values.yaml`.
ArgoCD then syncs it into the ConfigMap. Note the live ConfigMap currently holds
`smoke-chill-lounge`, which is not in that `values.yaml` — the chart values and
the live ConfigMap have drifted.

## 8. Blocker for the next stages

`acestep_plan.py` refuses a plan whose sections carry no lyrics (exit 1, "left
for a human"). `planner.py` produces exactly that scaffold under
`--lyrics-mode draft`. This track must not use `--lyrics-mode ai`: AI-written
lyrics void the human-authorship claim this pipeline registers with SOCAN.

So the plan for this track must carry the existing sheet verbatim. No tool does
that today: `planner.py` has no `--lyrics-file` input. Two paths exist, and the
implementer picks one:

1. Plan with `--lyrics-mode draft`, then replace `plan["lyrics"]` with the sheet
   text and verify the sha256 against the manifest.
2. Add a `--lyrics-file` input to `planner.py` (the durable fix; needs its own card).

## 9. Next stage

Stage `brief` is complete. Next: `genre-select`.
