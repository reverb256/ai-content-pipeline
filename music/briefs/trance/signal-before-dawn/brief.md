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

### Defect found while resolving this brief

`music/stages.yaml` gives the generate stage the instruction
"generate 2 tracks via Suno CDP (music/suno-gen.py)". That file does not exist:
a repo-wide search for `suno-gen` returns no match. The Suno CDP path in the
stage prompt is stale. The live engine is the ACE-Step cluster path above.
Until `stages.yaml` is corrected, the generate stage tells its bot to run a
missing script.

Second defect: no music stage prompt calls
`scripts/automation/advance-stage.sh`, and that script hardcodes
`BOARD=faceless-youtube`. A music card can therefore never advance its own stage
marker; it re-dispatches the same stage. The oracle, in addition, creates cards
with no `idempotency_key`, so each daily run re-emits the same 14 genre cards
(observed: 14 cards at 03:27 and 14 more at 03:37 on 2026-10-09, including a
second trance card `t_1a6a7d74` at score 8.5).

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
