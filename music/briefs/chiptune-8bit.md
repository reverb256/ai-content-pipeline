# Brief — chiptune-8bit

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`)
> **Card (surviving):** t_60767fb1 (`music-oracle: chiptune-8bit (score 7.2)`)
> **Superseded cards:** t_9cc9b48f (score 7.5, `done`) and t_05b640f6 (score 7.7, `done`) —
> the same genre, emitted by earlier oracle runs before the dedupe guard existed. The brief is
> keyed by genre, not by card, so all three cards resolve to THIS file.
> **Written:** 2026-10-16T13:17-05:00 (CDT), profile `music-producer`, run 77
> **Verified (duplicate-card pass, `t_05b640f6`):** 2026-10-16T13:40-05:00 (CDT) — see §12.
> One claim was withdrawn (§8.4); three items were corrected (§6.1, §8.3, §8.5).
> **Aged counts re-measured (card `t_0f7aed63`):** 2026-10-16 — see §13.
> **Re-measured (surviving-card pass, `t_60767fb1`):** 2026-10-16 15:58–16:08 CDT (commit
> `41b7b1e`) — see §14.
> **Census correction anchored (card `t_c5a98379`):** 2026-10-16 — §12's correction row 5 now
> carries the stamp for the blueprint census it quotes; see §15.
> Every section the live world has moved past carries its correction inline; §14 tabulates all
> of them against the revision that supersedes this copy.
> **Repo:** `/home/j_kro/ai-content-pipeline` (main) — NOT `~/Projects/ai-content-pipeline`,
> which is a second clone without a `music/` tree.
> **Oracle score:** **7.0/10** — the true score of the surviving card `t_60767fb1` (quota
> headroom 10.0, lane coverage 6.0, revenue 8.0, cadence fit 3.3, policy risk 9.0, trend
> signal 3.0). The 7.2 in the card's title is the pre-`b2d11f7` failed-fetch premium,
> WEIGHTS['trend_signal'] × (5.0 − 3.0) = 0.20. Threshold 5.0 → produce. See §14.
> **Superseded digest:** this file was
> `sha256 2e603d85ef4e5b3ce41c2d69b5ff1b9210828e289bb2b6c6c3ed1dda64974457`
> (692 lines / 39 339 B) when this pass began. The revision below supersedes that copy.
> **Rail B absence claim corrected (card `t_bdb94fb7`, 2026-10-16):** §7 had said `music/suno-gen.py`
> was out of local `main` and out of its history; the reconciliation merge put it in both. §16
> records the correction and the superseded revision.

Every number and quoted string below comes from a command run or a file read during this
stage. Nothing is recalled. Where something is unknown, it says so.

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

`/usr/bin/python3` is the interpreter with PyYAML. The bare `python3` on this worker's PATH
is the Hermes bundled 3.14.7 and has no `yaml` module, so `python3 music/registry.py validate`
and every gate that imports `music/lyrics/lyrics.py` fail on it (measured in §8.3).

| Field | Value |
|---|---|
| Genre | `chiptune-8bit` |
| Family | `gamer` |
| Prompt template | `music/prompts/chiptune-8bit.md` — resolves; style block measures **567 chars / 568 bytes** (1 line) — the header’s "567/1000" is accurate, see §8.4 |
| Visual style | `music/visuals/pixel-scene.md` — resolves |
| Lanes | `game-assets`, `youtube-gaming`, `streaming` |
| Cadence | 2/wk |
| Video shape | `loop-10min` |
| Lyric blueprint | none — and none is needed (§4) |
| Registry note | **absent** — this block has no `notes:` key, unlike chill-lounge/trance/anime-* |

Registry `defaults:` that bind every track (`music/genres.yaml` lines 20–25):
export `studio`, stems `true`, lyrics `human-original`, release_private `true`,
gate_profile `reviewer-deepseek`.

The genre's own block (`music/genres.yaml` lines 119–125) in full:

```yaml
  chiptune-8bit:
    family: gamer
    prompt_template: prompts/chiptune-8bit.md
    visual_style: visuals/pixel-scene.md
    lanes: [game-assets, youtube-gaming, streaming]
    cadence: 2/wk
    video_shape: loop-10min
```

### Where this genre sits in the fleet's own scoring

`music/rubrics/gamer.json` (family `gamer`, pass_threshold 7.0) carries a criterion that
applies to **this genre only**:

> `chip_timbre_authenticity` (weight 3): "NES Ricoh 2A03: EXACTLY five voices — 2 pulse,
> 1 triangle, 1 noise, 1 DPCM; no reverb on the chip, no filter ... A stacked chord that
> rings as a chord is a hardware-impossible defect."

Re-measured 2026-10-16 (§14): the rubric carries six criteria — `chip_timbre_authenticity`
3, `battle_energy` 3, `elemental_atmosphere` 3, `loop_safety` 3, `asset_packaging` 1,
`loudness_target` 1 — and six `reject_signals`. Two of them will bite a lazy render:

- "chiptune claim with reverb/pads/realistic instruments or >2-note chords per channel
  (hardware-impossible = OUT of genre)" (`chip_impossible_timbre`)
- "fade-out or truncated ending on a game-loop claim" (`loop_fade_or_truncation`)

Two more bear directly on this genre's deliverable:

- `no_stated_tempo_key`: "no stated BPM/key for a game-asset product"
- `clipped_master`: "clipped master (max_volume_db >= -0.1)"

So the quality gate for this genre is not "does it sound nice" — it is a hardware-budget
audit. Plan for that now.

---

## 2. Intent

A game-ready 8-bit loop. The product is **utility**: an indie dev drops it into a level and
it does not fight the code. The genre's identity is constraint, not mood — five voices on a
Ricoh 2A03, no reverb anywhere, chords faked by a frame-rate arpeggio in one voice. The
charm is discipline inside that budget; anything a real chip could not do reads as "synth
pretending" and is out of genre.

### Craft contract (from `music/prompts/chiptune-8bit.md` — the write-to spec)

| Constraint | Value |
|---|---|
| Tempo | **150 BPM**, 4/4, bright and energetic |
| Voices | Exactly four jobs: pulse lead, pulse harmony/fast-arp, triangle bass, noise percussion. "The moment a fifth sustained layer appears, the illusion dies" |
| Timbre control | Duty-cycle contrast between the two pulse channels (12.5% thin/nasal, 25% reedy classic lead, 50% hollow square) |
| Harmony | Implied, not stacked: one voice cycles chord tones at ~60 Hz so the ear fuses them |
| Space | Key-triggered echo (a single quiet re-triggered note), **never reverb**. "A hall tail on a chip lead instantly reads as 'synth pretending'" |
| Dynamics | 16-step volume envelopes, plucked staccato attacks. "A smooth fade is not a thing the hardware did" |
| Ending | **Loop point** — the theme clipped to one punchy phrase that leads back to bar 1. A fade-out is a defect |
| Structure | Intro → call-and-response → arp phase → breakdown (one pulse + triangle) → full energy → loop point |
| Weirdness / Style Influence | 35% / 85% |
| Exclude styles | `reverb, lush pads, realistic instruments, drums with long tails, modern synths, detuned supersaws` |

**Reject signals for the curate stage:** any reverb tail, any lush/analog pad, a real drum
kit, a chord that actually rings as a stack, a fade-out ending, or a tempo near 120 instead
of 150 (see §6.3 — this one is a real risk on the deployed engine, not a hypothetical).

---

## 3. Target lanes and what each lane demands

Live reads from `music/lanes.yaml` and `music/autonomy.yaml`.

| Lane | Surface | Gate | Required artifacts | Autonomy rung |
|---|---|---|---|---|
| `game-assets` | itch.io, unity-asset-store, gamedev-market | `gate_sync_ready` (`--lane game-assets`) | `stems`, `loop_point`, `seamless_loop`, `metadata` | advisory |
| `youtube-gaming` | youtube (shape `loop-10min`) | `gate_youtube_authentic` | — | advisory |
| `streaming` | distributor (DistroKid; alt TuneCore) | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` | advisory |

Every rung is `advisory` (clean_publishes 0, platform_strikes 0, revenue_usd 0). No lane may
publish itself.

Four consequences that are decisions, not details:

1. **Stems are mandatory.** `game-assets` requires them; `gate_sync_ready` needs ≥ 4 real
   audio stems, each within ±0.5 s of the master duration (ffprobe-measured, not filename-
   trusted). A four-voice chip track maps naturally onto a four-stem split — pulse 1, pulse 2,
   triangle, noise — which is exactly what an indie dev wants in an asset pack.
2. **The seamless loop is a measured artifact, not a claim.** `loop_points.json` must carry
   `loop_start_s` / `loop_end_s` / `seamless: true`, and `gate_loop_points` renders the tail
   and head windows, concatenates them, and measures the junction curvature against the body
   (PASS ≤ 3.0x). Verified live on the gate's own fixtures:
   `PASS seamless loop (1.6x curvature)`, `FAILS phase-slip loop (6.0x curvature)`.
3. **The `loop-10min` shape is 600 s, and the planner now accepts 600 s.** The shape
   template measures exactly 600.000 s (ffprobe). When this brief was written the planner
   capped a plan at 420 s (`MAX_DURATION_S = 420`); re-measured 2026-10-16 (§14) the cap is
   **600 s** (`music/planner/planner.py:148`, raised by commit `52ae620` for this very shape — the constant moved from `:104`; re-read 2026-10-16 by card `t_ae1d9243`).
   **600.000 s is whole-bar at this genre's tempo — 375 bars × 1.600 s a bar — so the loop can
   be rendered at full length.** Revised decision: plan the loop at 375 bars / 600 s; cut it
   to a shorter whole-bar master only if the game-asset pack wants one.
4. **The `youtube-gaming` gate rejects the existing shape template.** Measured: the lane's own
   `music/visuals/loop_10min.mp4` (600.0 s, 1280×720, 25 fps) **FAILS**
   `gate_youtube_authentic` with `only 4 distinct frame signature(s) across 600.0s (10 required)
   — this is a raw dump`. The videobot must author a real pixel-scene visual with shot
   variation; reusing the shipped template verbatim fails the gate.

Bar arithmetic at the genre's 150 BPM (4/4 → one bar = 240/150 = **1.600 s**), computed live:

| Bars | Duration | Verdict |
|---|---|---|
| 32 | 51.20 s | short NES-style level loop |
| 64 | 102.40 s | **recommended primary** — whole-bar, phrase-multiple, loop-safe |
| 128 | 204.80 s | long-form variant |
| 256 | 409.60 s | long-form variant |
| 375 | 600.00 s | **the full `loop-10min` shape** — whole-bar at 150 BPM and inside the 600 s planner cap |

---

## 4. The lyrics stage does NOT apply to this genre (decision, with evidence)

`music/prompts/chiptune-8bit.md`, under `## Lyrics guidance`:

> "Instrumental. Leave the **lyrics box empty** — that is Suno's instrumental path.
> (Vocal chiptune exists but kills the game-asset lane utility.)"

`music/stages.yaml` already anticipates this and instructs the lyrics stage to advance an
instrumental genre with a comment instead of writing a sheet. Nothing here overrides that.

Why it matters beyond bookkeeping:

- **The copyright path is not at risk.** The lane's copyright claim depends on human-authored
  lyrics; an instrumental has none to author, so there is nothing to fake and nothing to
  lose. The registry default `lyrics: human-original` is satisfied vacuously.
- **No blueprint is required.** `music/lyrics/blueprints/` holds seven files — `activist`,
  `anime-ending`, `anime-opening`, `chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`,
  `trance` (re-measured §14; `jungle-dnb.yaml` landed after this brief was written).
  `planner.py show --genre chiptune-8bit` reports `"blueprint": false`, and that is not a
  defect: with no blueprint the planner reads the BPM the genre's own caption states
  (`bpm_in_caption`, `planner.py:199`; `bpm_anchor_for`, `planner.py:212`), so this genre plans
  at its template's 150 BPM. The hardcoded `100` is reachable only when neither a blueprint
  anchor nor a caption BPM exists. Measured live: `structure_source: template`,
  `bpm_anchor: null`, `caption_chars: 567`, `instrumental: true`.
- **`--lyrics-mode ai` is not a temptation here.** There are no lyrics to generate. The
  generate stage must pass the instrumental flag, not an AI-written sheet.

---

## 5. Throughput budget (derived, not assumed)

Cadence 2 tracks/week (§1) × the lane set (game-assets pack + one 10-minute gaming video +
one streaming release per track) = **2 loops/week, 104/year**. At 64 bars each that is ≈ 3.4
minutes of new audio per week — small. The real cost is downstream per-track packaging, not
rendering: stems, loop points, metadata, ISRC, artwork, and a distinct visual per upload.

The surviving card's true score is **7.0**, with lane coverage 6.0 and cadence fit **3.3**
(§14; the title's 7.2 carried cadence fit 6.7 — the pre-`b2d11f7` failed-fetch premium). The
genre is low-volume and high-packaging: budget the packaging, not the generation.

---

## 6. The generation path — measured, with one genre-blocking defect

### 6.1 Two rails exist. Only one is live.

**Rail A — the cluster planner/render queue** (this is what runs by itself):

| Stage | Job | Schedule | Input | Output |
|---|---|---|---|---|
| plan | CronJob `music-pipeline` (ns `mining`) | `17 */6 * * *` | ConfigMap `music-pipeline-briefs` key `briefs.json` | `/var/lib/music-plans/<name>.json` |
| render | CronJob `music-pipeline-render` (ns `mining`) | `41 */4 * * *` | plans without a `.rendered` marker | audio via `sunolocal` |

Both ran inside the hour before this pass. Real logs, re-measured 2026-10-16 (§14):

```
$ kubectl logs job/music-pipeline-render-t6d7ad524 -n mining --tail=4
skip   smoke-chill-lounge (already rendered)
skip   testplan (already rendered)
skip   trance-signal-before-dawn (already rendered)
done: found=13 rendered=1 skipped=12 failed=0

$ kubectl logs job/music-pipeline-t6d7ad524 -n mining --tail=4
bpm/key  : 72 BPM · C minor · 4/4
duration : 420s   language: en
validation: PASS
done: 11/11 planned
```

The queue is live and no longer empty of useful work: `/var/lib/music-plans/` holds 13 plans,
12 markers, one rendered master (`elemental-fire-emberfall.flac`, 11 421 612 B) and `loops/`
carrying that track's loop pair. **No chiptune plan exists, and the brief ConfigMap carries no
chiptune entry** — 11 entries, 5 of them `lyricsMode: instrumental`. This genre is not queued
yet, and adding its entry is the generate stage's first action (§10).

**Rail B — `music/suno-gen.py` (Suno over CDP) — RESOLVED 2026-10-16 14:23.** When this brief
was written the file lived only on `origin/main`; the reconciliation merge `ab33ad1` (card
`t_8a715681`) joined the two lineages. Measured live at this pass (§14):

```
$ git log --oneline -1                              → c296db6
$ git ls-remote origin main                         → ba28f55
$ git rev-list --left-right --count origin/main...HEAD → 0   72
$ git merge-base --is-ancestor origin/main HEAD     → YES
$ ls -l music/suno-gen.py                           → 42 652 B in the working tree
$ /usr/bin/python3 music/scripts/check_stage_scripts.py
PASS check_stage_scripts: 11 referenced script path(s) all present in /home/j_kro/ai-content-pipeline
```

Local `main` is 72 commits ahead of `origin/main` and 0 behind. The ahead-count is anchored to
revision `c296db6` on purpose: this lane commits every few minutes. Nothing is pushed to the
remote — that is a separate action and no step of this brief depends on it.

### 6.2 The live engine and its exact contract (probed, not assumed)

```
$ kubectl get deploy sunolocal-source -n mining
sunolocal-source   1/1   1   1   2d17h     → image localhost/sunolocal:v0.1.3
$ kubectl get deploy -n mining sunolocal-source -o jsonpath='{.spec.template.spec.containers[0].env}'
SUNOLOCAL_ENGINE=ace · SUNOLOCAL_COMFY_URL=http://comfyui-zephyr.mining.svc.cluster.local:8188
SUNOLOCAL_ACESTEP_SCRIPT=/opt/sunolocal/music/scripts/acestep_plan_direct.py
```

The image was `v0.1.2` when this brief was written; **re-measured at this pass it is
`v0.1.3`** (§14). The request schema in the pod (`/opt/sunolocal/music/sunolocal/spec.py`,
3478 B on the pod's filesystem) now carries the two fields this genre needs:

```
bpm: Optional[int] = None        # explicit tempo; beats the style_weight fallback
keyscale: Optional[str] = None   # explicit key signature, e.g. "C major"
```

Both were card `t_25a6499c` D1/D2, and both are fixed on the deployed engine. The wire
contract is otherwise `prompt, style, lyrics, title, instrumental, model, customMode,
negativeTags, vocalGender, duration, styleWeight, weirdnessConstraint, audioWeight, variety,
callBackUrl, seed, engine`.

The engine **can** render an instrumental. `sunolocal/translate.py` in the pod:

```python
if req.instrumental and not lyrics:
    caption = caption + ", instrumental, no vocals"
    lyrics = "[Instrumental]\n"
```

and `adapters/ace_comfy.py` passes `--allow-empty` to the renderer, so the empty-body
instrumental passes the renderer's loader. The instrumental path exists end to end on the
engine side.

### 6.3 The three blockers — ALL RESOLVED on the deployed rail (re-measured §14)

When this brief was written the wrapper mounted from ConfigMap `music-pipeline-payload`
(volume `payload`) hardcoded `"instrumental": False` at its line 87, invoked no
`--allow-empty`, and carried no BPM — so an instrumental 150 BPM genre could only render as a
120 BPM vocal-shaped track. All three are fixed on the deployed rail. Evidence, re-measured
2026-10-16 (§14):

- The deployed wrapper is now **354 lines** and byte-identical to the repo copy
  (`diff -q music/scripts/acestep_plan.py <chart>/files/music/scripts/acestep_plan.py` →
  identical). Its body carries
  `"instrumental": bool(plan.get("instrumental"))` (line 174),
  `"bpm": int(plan["bpm"]) if plan.get("bpm") is not None else None` (line 189) and
  `"keyscale": (str(plan["key"]).strip() or None) if plan.get("key") else None` (line 190).
  Its own docstring records the defect it fixes: "`plan["bpm"]` never left the plan, so the
  engine answered its own default", and "`instrumental` … used to be dropped, so an
  instrumental plan rendered as a vocal track with an empty lyrics box".
- `check_lyrics` (line 95) returns early for an instrumental plan (line 119), so the
  `--allow-empty` refusal no longer reaches this genre. The render CronJob still invokes
  `acestep_plan.py <plan> --name <stem>` without the flag, and no longer needs it.
- Live proof on the rail: `/var/lib/music-plans/t_8c5a6b91/t8c5a6b91-empty-lyrics.json` plus a
  0-byte `.rendered` marker — the empty-lyrics fix was exercised on the cluster. The plan job's
  log line for an instrumental genre reads
  `mode : INSTRUMENTAL — no lyrics; the template declares an empty lyrics box. The renderer's
  draft refusal does not apply.`
- The tempo travels with the plan. `music/planner/planner.py` writes `bpm` and `key`, and the
  wrapper passes both through. Measured on queued plans: `elemental-fire-emberfall` reads
  `bpm=150, keyscale=D Phrygian`; `elemental-air-above-the-weather` reads
  `bpm=92, keyscale=C major, instrumental=true`. The pod's `translate.py` resolves
  `bpm = int(req.bpm)` first (line 63), the `styleWeight` formula second (line 67), and `120`
  only as the last resort (line 69).

Consequence for this genre: plan `bpm: 150`, let the template caption supply the key, and the
engine renders 150 BPM. The `styleWeight = 0.75` workaround this section used to recommend is
no longer needed.

### 6.4 Duration — corrected: a 600 s render is plannable and has been rendered

~~A 600 s render is impossible.~~ Corrected 2026-10-16 (§14): the planner's guard rail is now
16–600 s (`planner.py:147-148`, card `t_ae1d9243`), and `/var/lib/music-plans/elemental-earth-chamber-loop.json`
carries `duration: 600` with a `.rendered` marker — the rail has rendered a 600 s plan.
`translate.py` still takes `duration` straight from the request with no upper guard (line 55:
`float(req.duration)` else `30.0`), so the planner remains the only duration guard. §3.3 now
recommends the full 375-bar / 600 s loop.

### 6.5 New since this brief: the render rail refuses a loop claim it cannot verify

`music/scripts/loop_close.py` now runs inside `music-pipeline-render`. For every plan it
renders, the job asks `--claims-loop --plan <plan> --genres-yaml music/genres.yaml`, which
reads the claim from the genre's own `video_shape` in `music/genres.yaml`. This genre's shape
is `loop-10min`, so **a chiptune master is a loop claim**: the rail then requires the rendered
master to exist, closes the loop with `loop_close.py`, and re-checks the closed loop with
`--check-only`. A failure writes `<stem>.looprefused`, prints the reason, and exits the job
non-zero (card `t_b21aeb51`).

Effect on the generate stage: a chiptune render that cannot carry a seamless loop is refused
at generation time, before `gate_loop_points` ever sees it. That is an improvement, not a
blocker — but the plan's loop length must be whole-bar, which is why §3.3's 375-bar figure
matters.

---

## 7. Existing assets for this genre

Measured: **none.**

- `music/lyrics/` holds `activist/`, `anime-opening/`, `chill-lounge/`, `trance/` plus seven
  blueprints (`activist, anime-ending, anime-opening, chill-lounge, epic-orchestral-boss,
  jungle-dnb, trance`). No chiptune lyric dir or blueprint — expected, the genre is
  instrumental.
- No chiptune plan, master, stems, cover artwork or `loop_points.json`, and no queue entry.
  Other genres now have some: `/var/lib/music-plans/elemental-fire-emberfall.flac` (11 421 612 B)
  and its `loops/` pair. Nothing of this genre's exists.
- `music/visuals/pixel_scene.mp4` is a **5.000 s**, 1280×720 reference render (14 244 bytes),
  not a 10-minute visual. `music/visuals/loop_10min.mp4` is the 600 s shape template — and it
  fails its own lane gate (§3.4).
- The first render is genuine work, not a re-run.

Quota is untouched, measured live:

```
$ python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

`music/quota-ledger.json`: `standard_downloads_used 0 / 60`, `studio_exports 0`,
`credits_used 0 / 10000`. Full headroom. If Rail B (Suno) is ever used for this track, export
**through Suno Studio only** — the standard download button is the capped meter.

---

## 8. Defects found while writing this brief (with evidence)

### 8.1 The `game-assets` gate chain is not wired into any stage

`brain/runbooks/music-game-assets.md` — the itch.io distribution runbook, the only
game-asset procedure in the repo — ends with this checklist:

```
- [ ] music/gates/gate_loop_points.py PASS
- [ ] music/gates/gate_sync_ready.py PASS (--lane game-assets)
- [ ] All stems named according to game-assets.py naming convention.
- [ ] perpetual_game_asset_v1.txt included in /docs.
- [ ] Sample rate (44.1k/48k) explicitly stated in metadata.json.
```

`music/stages.yaml` names six gates — `gate_quota`, `gate_lyrics_original`,
`gate_stems_present`, `gate_loudness`, `gate_quality`, `gate_release_ready` — and **never**
`gate_sync_ready` or `gate_loop_points`. The `package` stage runs `gate_release_ready` (the
streaming gate) for every genre, whatever its lanes. The visual stage's gate is no longer
hardcoded in the stage map: that stage now resolves it from the registry
(`music/lanes.yaml` `stage_gates.visual`, selector `lane_gate`, `when_absent: none`):

```
$ /usr/bin/python3 music/registry.py gate-for-stage --stage visual --genre chiptune-8bit
gate    : gate_youtube_authentic
script  : music/gates/gate_youtube_authentic.py
reason  : lane 'youtube-gaming' is guarded by gate_youtube_authentic (surface: youtube)
```

So a chiptune card would still pass the pipeline while never running `gate_sync_ready` — the
game-assets lane's own gate — and the seam gate is still not a stage gate. Two things have
narrowed the gap since this brief was written (§14): `gate_sync_ready` now **measures** every
seam itself (`music/gates/gate_sync_ready.py:347`, importing the loop floor from
`gate_loop_points` at line 80) instead of only asserting that `loop_points.json` exists, and
the render rail now refuses an unverifiable loop claim at generation time (§6.5). The
remaining defect is the wiring, not the measurement.

### 8.2 The chart's payload-sync check FAILS on this host (wrong source path + real drift)

The ConfigMap `music-pipeline-payload` is generated by `mining-k8s`
(`helm/charts/music-pipeline`, Argo app `music-pipeline`). When this brief was written both
sync scripts defaulted to the wrong checkout and the chart's wrapper was ahead of the repo's.
Both defects are fixed; re-measured at this pass (§14):

```
$ bash /home/j_kro/mining-k8s/helm/charts/music-pipeline/check-payload-sync.sh
source : /home/j_kro/ai-content-pipeline  (worktree 2611770)
ref    : origin/main = ba28f55
RESULT: PASS — chart payload matches the lane repo (/home/j_kro/ai-content-pipeline / origin/main)

$ grep -n 'SRC=' helm/charts/music-pipeline/{check-payload-sync,sync-payload}.sh
check-payload-sync.sh:34:SRC="${SRC:-/home/j_kro/ai-content-pipeline}"
sync-payload.sh:5:SRC="${SRC:-/home/j_kro/ai-content-pipeline}"

$ wc -l helm/charts/music-pipeline/files/music/scripts/acestep_plan.py music/scripts/acestep_plan.py
354 both  ·  diff -q → identical
```

`SRC` now names the checkout that carries `music/`, and "run sync-payload.sh" is safe again:
the chart copy and the repo copy are the same 354-line file, so a sync cannot regress the live
wrapper. The §6.3 fixes live in both.

### 8.3 The gate suite's interpreter hazard — FIXED since the brief stage

At the brief stage the suite reported:

```
$ bash music/gates/check_gate_suite.sh ; tail -1
BROKEN: 2 check(s) misbehaved
```

**Re-measured at the `t_05b640f6` pass — the suite is green:**

```
$ bash music/gates/check_gate_suite.sh ; tail -3
FAILS no approval record fails (exit 1, as expected)

OK: every gate passed its good artifact and failed its broken one
```

The fix landed in `757f3ab` (2026-10-16T13:21:38-05:00, card `t_d3b9e218`), which reworked
`music/gates/check_gate_suite.sh` (+81/−27) to prefer `/usr/bin/python3` — or an explicit
`PY=` override — and to abort loudly when no PyYAML-capable interpreter exists. The hazard the
brief identified is unchanged and still real: re-measured at this pass, bare `python3` on this
host is Hermes's bundled **3.14.7** and `import yaml` raises `ModuleNotFoundError`. The two
fixtures were never a gate defect — they pass under the right interpreter.

At the brief stage the two failing checks were both `gate_lyrics_original` fixtures (`BAD chill-lounge lyrics pass`,
`BAD trance lyrics pass`) with `ModuleNotFoundError: No module named 'yaml'` — the suite calls
bare `python3`, and this worker's bare `python3` is Hermes's bundled 3.14.7 without PyYAML.
Same file, right interpreter, live:

```
$ python3 music/gates/gate_lyrics_original.py --track-dir music/lyrics/chill-lounge/amber-hour
  → ModuleNotFoundError: No module named 'yaml'
$ /usr/bin/python3 music/gates/gate_lyrics_original.py --track-dir music/lyrics/chill-lounge/amber-hour
PASS gate_lyrics_original
  track        : Amber Hour (music/lyrics/chill-lounge/amber-hour)
  sections     : 7
  unique words : 93
  authorship   : j_kro @ 2026-10-08T12:48:59+00:00
  suno markers : none
```

The gates were never broken — the suite's interpreter was unpinned, and it is pinned now.
Every section passes its fixtures (quota, stems, loudness, quality, sync-ready, release-ready,
loop-points, youtube-authentic, human-approval), and this genre's own loop gate is among the
passing ones. Re-confirmed at this pass (§14): `OK: every gate passed its good artifact and
failed its broken one`, with `PASS seamless loop (1.6x curvature) passes` /
`FAILS phase-slip loop (6.0x curvature) fails` verbatim. The loop section has grown since:
it also refuses a faded tail on the LEVEL ruler, and both pack fixtures.

### 8.4 WITHDRAWN — the template's style-field count was already accurate

The brief stage claimed the header's "567/1000 chars" was stale and that the style block
measured **844 chars**. Re-measured at the `t_05b640f6` pass, on the same file — clean
against HEAD, mtime `2026-10-09 03:22:34`, exactly one commit in its history (`96aece4`),
and byte-identical to the deployed ConfigMap copy `music__prompts__chiptune-8bit.md`:

```
style block : 1 line · 568 bytes · 568 chars · 567 with the newline stripped
header claim: "567/1000 chars"
file        : 4103 bytes · 4075 chars · 83 lines
```

**567**, exactly as the header says — the header was never stale. A brute-force sweep of
every fence-to-fence slice of the template found **no** 844-character slice, and no other
genre template has a text block of 844 chars. The number is not reproducible from any
artifact, so the defect is withdrawn instead of carried forward. No template edit is
warranted.

### 8.5 Two cards for one genre on the board

```
$ sqlite3 "file:~/.hermes/kanban/boards/music/kanban.db?mode=ro" \
    "select id,title,status,assignee from tasks where title like '%chiptune%';"
t_9cc9b48f|music-oracle: chiptune-8bit (score 7.5)|running|music-producer
t_05b640f6|music-oracle: chiptune-8bit (score 7.7)|ready|music-producer
```

`ade6e87` added an open-card guard to `music/oracle.py`, so new runs no longer duplicate. The
existing pair was created before it. Both resolve to this one genre-keyed brief; the duplicate
should be closed rather than worked, or the generate stage will render the same track twice.
**Status re-measured at this pass (§14):** `t_9cc9b48f` **done**, `t_05b640f6` **done**,
`t_60767fb1` **running** — the surviving card. Three cards, one genre, one brief: resolved, not
duplicated. Board-wide `music-oracle:*` residue, read from the board database: **37 `done`,
7 `running`, 3 `ready`**, and `music/scripts/check_oracle_board.py` reports one open card per
open genre (`PASS`, rc=0) — the board invariant holds live.

---

## 9. Gate path for the finished artifact

1. `gate_stems_present` — ≥ 4 stems, non-zero bytes, ±0.5 s of the master (natural split:
   pulse 1 / pulse 2 / triangle / noise)
2. `gate_loop_points` — seam curvature ratio ≤ 3.0x, loop region not silent, span ≥ 2 s
3. `gate_loudness` — this gate measures `ffmpeg volumedetect` mean_volume, **not gated LUFS**
   (measured 1.4–2.4 dB below ebur128 on a real album). Note the ruler difference before
   calling a master defective.
4. `gate_quality` — reviewer model **different** from the producer; scored against
   `music/rubrics/gamer.json` (pass 7.0), whose six criteria are `chip_timbre_authenticity` 3,
   `battle_energy` 3, `elemental_atmosphere` 3, `loop_safety` 3, `asset_packaging` 1,
   `loudness_target` 1
5. `gate_sync_ready --lane game-assets` — stems + `loop_points.json` + manifest metadata
   (title, artist, bpm, key, mood, genre) + clearance doc + AI disclosure + instrumental
   version that is not a byte-copy of the master. Since this pass it also **measures** every
   seam with `gate_loop_points.check_loop` (§8.1)
6. `gate_release_ready` — streaming package (ai_disclosure, ISRC per ISO 3901 — 12 chars, no
   check digit, artwork)
7. `gate_youtube_authentic` — ≥ 10 distinct frame signatures across the visual, Jaccard
   ≤ 0.85 vs prior uploads, AI disclosure beside the video
8. `gate_human_approval` — j_kro. Never auto-passes.

Ahead of all of them, at generation time: the render rail's own loop check
(`music/scripts/loop_close.py`, §6.5). It runs on the cluster before any gate above sees the
master.

---

## 10. Recommended next stage

**`lyrics` → advance immediately as instrumental** (§4), then **`generate`**. The three
corrections this brief originally demanded are all in place on the deployed rail (§6.3, §14):

1. `instrumental: true` reaches the engine — the deployed wrapper carries
   `bool(plan.get("instrumental"))` (wrapper line 174).
2. No `--allow-empty` is needed — `check_lyrics` returns early for an instrumental plan
   (wrapper line 119).
3. The tempo travels: the planner writes `bpm`/`key` into the plan and the wrapper passes both
   (lines 189-190); the pod's `translate.py` reads `req.bpm` first (line 63).

What the generate stage must add instead: a **queue entry** for this genre (the ConfigMap
carries none, §6.1) with `lyricsMode: instrumental`, `bpm: 150` and a duration that is
whole-bar, and it must satisfy the render rail's loop check — this genre's `loop-10min` shape
makes the master a loop claim (§6.5).

Deliverable for `generate`: **one 375-bar (600.000 s) whole-bar loop at 150 BPM** — the full
`loop-10min` shape, whole-bar and inside the planner's 600 s cap (§3.3) — no reverb, no pads,
four voices, ending on the loop phrase; plus a second take for curation. A 64-bar (102.40 s)
whole-bar master is the acceptable game-asset pack cut. Render on the `sunolocal` rail: it is
what runs by itself, and `music/suno-gen.py` is present now but needs a logged-in browser
session on a host (§6.1). Then `curate` → `stems` → `master` → `gate` → `package`
(`gate_sync_ready --lane game-assets` + `gate_loop_points`, both currently un-wired, §8.1) →
`visual` (a real 600 s pixel-scene video, not the 4-signature template, §3.4) →
**human-approval** → `publish` (PRIVATE / draft only — never public without j_kro) → `track`.

Human queue raised by this brief (reported, not fixed here): the missing game-assets gate
wiring in `stages.yaml` (§8.1) is the one item still open. The payload-sync path and wrapper
drift (§8.2) and the divergence that hid `suno-gen.py` (§6.1) are **resolved** — §14. The
duplicate chiptune cards (§8.5) are **closed**, and §14 records the oracle's surviving-card
ruling that made this card the owner of the genre.

---

## 11. Provenance

- Registry: `music/genres.yaml` (lines 20–25 defaults, 119–125 genre block — re-measured §14),
  `music/lanes.yaml`, `music/autonomy.yaml` — validated live
  (`registry OK: 14 genres, 10 lanes, 1 stage gate rule(s)`)
- Rubric: `music/rubrics/gamer.json` (read in full)
- Gates: `music/gates/` — `gate_quota`, `gate_loop_points`, `gate_sync_ready`,
  `gate_youtube_authentic`, `gate_release_ready` read; suite executed
- Stage contract: `music/stages.yaml` (read in full)
- Runbook: `brain/runbooks/music-game-assets.md`
- Cluster: CronJobs `music-pipeline`, `music-pipeline-render` (last jobs `…-t6d7ad524`);
  Deployments `sunolocal-source` (**v0.1.3**, re-measured §14), `comfyui-zephyr`; ConfigMaps
  `music-pipeline-briefs`, `music-pipeline-payload`; `/var/lib/music-plans` (hostPath,
  `PLANS_DIR=/plans`)
- Chart: `/home/j_kro/mining-k8s/helm/charts/music-pipeline/` (`values.yaml`, `sync-payload.sh`,
  `check-payload-sync.sh`, executed), `helm/charts/sunolocal/files/music/sunolocal/{spec,studio,translate}.py`
- Media: `ffprobe` on `music/visuals/pixel_scene.mp4` and `loop_10min.mp4`
  (`/home/j_kro/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin/ffprobe` — ffmpeg is not on PATH)
- **Dangling reference — RESOLVED 2026-10-16 (§14).** `brain/playbooks/music-lane-architecture.md`
  was reported absent when this list was written; it is in this tree and in `HEAD` now —
  rewritten at `7411afa` (head touching it `6b24a52`, card `t_b0a4db92` done). The
  genre block in §2 and the gate table in §5 carry this brief's claims, and
  `music/scripts/check_doc_refs.py` resolves every `§` reference to a heading.

---

## 12. Duplicate-card verification pass (`t_05b640f6`, 2026-10-16T13:40-05:00 CDT)

> **Historical.** This section records what that pass measured at 13:40. Where the live world
> has moved since, §14 carries the correction. §12 is not rewritten.

This brief is genre-keyed, so both oracle cards for `chiptune-8bit` resolve to it. `t_9cc9b48f`
(score 7.5) wrote it at 13:17 and is `done`; `t_05b640f6` (score 7.7 — the earlier emission,
created before `ade6e87` added the open-card guard) is the duplicate and owns this pass. No
second brief was written and no stage chain was started from the duplicate.

Everything below was re-measured live at this pass. Nothing was changed in the registry, the
gates, the plans, the chart, or the cluster; no new card was created.

### Held as written (re-measured, unchanged)

- `registry.py validate` → `registry OK: 14 genres, 10 lanes`; `gate_quota` → `period 2026-10,
  standard dl used: 0/60`, `studio exports: 0`; `quota-ledger.json` = 0/60 · 0 studio · 0/10000
  credits · warn 55 · hard stop 58.
- The genre block and the five `defaults:` keys are as quoted, and the genre block still has
  **no** `notes:` key.
- Lanes → gates: `game-assets` → `gate_sync_ready` (`requires: [stems, loop_point,
  seamless_loop, metadata]`), `youtube-gaming` → `gate_youtube_authentic`,
  `streaming` → `gate_release_ready` (DistroKid, alt TuneCore). All three rungs `advisory` with
  `clean_publishes 0 / platform_strikes 0 / revenue_usd 0`.
- `music/rubrics/gamer.json`: `pass_threshold 7.0`; `chip_timbre_authenticity` weight 3 and
  `loop_safety` weight 3; both `reject_signals` quoted in §2 verbatim.
- Template `music/prompts/chiptune-8bit.md`: instrumental ("leave the lyrics box empty"),
  150 BPM, weirdness 35%, Style Influence 85%, six exclude terms, loop-point ending. Blueprints
  are `activist, anime-ending, anime-opening, chill-lounge, epic-orchestral-boss, trance` (6 of the 14); still no chiptune lyric dir, no
  `loop_points.json`, no master, no stems.
- Bar arithmetic (1.600 s/bar), the planner cap `MAX_DURATION_S = 420` (**anchored** — this section is that pass's record; §14 row 4 corrects it), and the fallback
  `bpm_anchor or 100` (`music/planner/planner.py:470`).
- `ffprobe`: `loop_10min.mp4` = 600.000000 s · 1280×720 · 25/1 fps; `pixel_scene.mp4` =
  5.000000 s · 14 244 bytes. `gate_youtube_authentic --visual music/visuals/loop_10min.mp4`
  still **FAILS** with the §3.4 string, plus the missing-disclosure reason
  (`disclosure.txt` / `ai_disclosure.txt`).
- `gate_loop_points` fixtures, verbatim: `PASS seamless loop (1.6x curvature) passes` /
  `FAILS phase-slip loop (6.0x curvature) fails`; the ceiling is `CLICK_RATIO_MAX` 3.0.
- Rail A live: CronJobs `music-pipeline` (`17 */6 * * *`) and `music-pipeline-render`
  (`41 */4 * * *`). The last render job's log is identical to §6.1 to the line
  (`done: found=3 rendered=0 skipped=3 failed=0`); the last plan job logged
  `done: 1/1 planned`. `/var/lib/music-plans/` holds only `final-round`, `smoke-chill-lounge`
  and `testplan`, all `.rendered`; `smoke-chill-lounge.rendered` and `testplan.rendered` both
  contain `refused`. ConfigMap `music-pipeline-briefs` still carries exactly one entry,
  `smoke-chill-lounge` (196 bytes), and **no chiptune plan exists**.
- Engine: Deployment `sunolocal-source` runs `localhost/sunolocal:v0.1.2` (age 2d14h) with
  `SUNOLOCAL_ACESTEP_SCRIPT=/opt/sunolocal/music/scripts/acestep_plan_direct.py`. `spec.py`
  (100 lines) has **no** `bpm` field. `translate.py` (85 lines): `bpm = 120`;
  `if req.style_weight is not None: bpm = int(60 + req.style_weight * 120)`; clamp 30–240; the
  instrumental branch appends `, instrumental, no vocals`. `ace_comfy.py:70` passes
  `--allow-empty`. The pod copies are byte-identical to the chart copies.
- The three §6.3 blockers, all re-confirmed against the **deployed** wrapper (ConfigMap
  `music-pipeline-payload`, key `music__scripts__acestep_plan.py`, 261 lines): line 87
  `"instrumental": False`, line 93 `"style_weight": None`, and the render CronJob invokes
  `acestep_plan.py <plan> --name <stem>` with **no** `--allow-empty` — the wrapper defines the
  flag at line 115, but the CronJob never passes it.
- Rail B: `music/suno-gen.py` (42 652 B) **is in this tree and in local `main`** — the
  reconciliation merge `ab33ad1` (14:23) is what brought it in (its diff adds the file, +1025
  lines), so `git log main -- music/suno-gen.py` now returns both commits that carry it
  (`295fc49`, 2026-10-09 added it; `ba28f55`, 2026-10-14 touched it), and the worktree copy is
  byte-identical to `main:music/suno-gen.py`. **This reverses the brief-stage claim** that local
  `main` carried neither the file nor any commit touching it: the reference stands, the absence
  does not. Merge-base with `origin/main` was `e278f61` at the brief stage and is `97be84f` now
  (measured `178be75`, 2026-10-16).
- §8.1: `stages.yaml` references exactly seven gates and neither `gate_sync_ready` nor
  `gate_loop_points` is among them; `gate_sync_ready.py:204-207` only asserts that
  `loop_points.json` exists and then says `run gate_loop_points.py for the seam check`.
- §8.2: `check-payload-sync.sh` → `DRIFT ×3` (`music/planner/planner.py`, `music/genres.yaml`,
  `music/scripts/acestep_plan.py`), `SRC` defaults to `/home/j_kro/Projects/ai-content-pipeline`,
  that tree has no `music/` directory, and the chart wrapper is 261 lines against the repo's 173
  — so `sync-payload.sh` would regress the live wrapper, exactly as §8.2 argues. All 14 deployed
  prompt-template copies are byte-identical to the repo's.
- Prompt templates: all 14 resolve; every deployed ConfigMap prompt copy matches the repo copy.

### Corrections applied

| # | Section | Claimed at the brief stage | Measured at this pass |
|---|---|---|---|
| 1 | §1, §8.4 | style block measures **844 chars**; the template header's "567/1000" is stale | **567** chars (568 bytes, 1 line) — the header is accurate. Claim withdrawn |
| 2 | §8.3 | `BROKEN: 2 check(s) misbehaved`; suite interpreter unpinned | suite green — `OK: every gate passed its good artifact and failed its broken one`; interpreter pinned by `757f3ab` |
| 3 | §6.1 | lineages diverged `6 ahead, 15 behind` | **22 ahead, 15 behind** at `061b5dc` (13:34) — this wave's brief commits landed on local `main`; the pair reads 0 behind / 61 ahead at `e40c7f9` (15:31) |
| 4 | §8.5 | residue 15 `ready` + 7 `running` oracle cards; the pair was running/ready | **6 `ready` + 3 `running`**; the pair is `t_9cc9b48f` done / `t_05b640f6` this pass |

### Not changed, not re-filed

No registry value, gate, plan, blueprint, chart file, or cluster object was modified. No child
card was created: every item §8 and §10 raise already has an owner — `t_8c5a6b91` (nexus-core,
the wrapper `instrumental`/`--allow-empty` fix plus the payload-sync path), `t_bf0e5edd` (the
pre-guard duplicate-card sweep), and `t_41f354be` (the two-dispatcher ownership question).

Hotspot, flagged rather than piled on: `music/briefs/` — ten-plus workers of this wave commit to
one working tree; this file has two commits, both mine on this genre.

### Standing check added — the regression for the §8.4 class

A wrong figure in a brief cannot be caught by prose parsing, so the check guards the fact
itself: `music/scripts/check_prompt_style_counts.py` FAILs when a template's declared
`N/M chars` figure is not what its block measures, when the block overruns the `M` limit
(the Styles box truncates silently), and when a style heading has no block at all.

```
$ /usr/bin/python3 music/scripts/check_prompt_style_counts.py
PASS check_prompt_style_counts: 15 declared style-field length(s) across 14 template(s) match their blocks

$ /usr/bin/python3 music/scripts/check_prompt_style_counts.py --selftest
SELFTEST PASS check_prompt_style_counts: checked=3 false-claim=1 overflow=1
```

Negative control — declaring `844/1000` for this template reproduces §8.4 to the digit:

```
$ /usr/bin/python3 music/scripts/check_prompt_style_counts.py --dir <copy with 844 declared>
FAIL check_prompt_style_counts: 1 false or unsafe style-field claim(s) across 15 checked claim(s)
  chiptune-8bit.md:7: declares 844/1000 chars, block measures 567 (-277) — the header claim is FALSE
```

It is stdlib-only, so both `/usr/bin/python3` and the bundled interpreter run it. Incident
cited in the script docstring: this card, plus the sibling unit mislabel in the anime-opening
brief (`t_abaa7e2d`, commit `afa242e`).

## 13. Aged live counts re-measured (card `t_0f7aed63`, 2026-10-16)

`music/scripts/check_brief_drift.py` (added by card `t_b7dd5655`) flagged this brief: the clone
divergence its §12 correction row records has aged, and the blueprint lists it prints were down
to three files while the directory had grown to six. Re-measured and corrected in place.

- **Superseded revision of this file:** `sha256 12c6e2cf9883379b35988e6715c652e2a0612573511dbd8911baf38b484fadc9` (672 lines / 37365 B).
- **Blueprint census:** 7 of the 14 genres have a lyric blueprint (`activist`, `anime-ending`,
  `anime-opening`, `chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`, `trance`); the other 7 do
  not. This genre still has none, and none is wanted — §4's decision is unchanged. The
  2026-10-16 15:31 pass behind this section measured the census at six; what landed since is
  `music/lyrics/blueprints/jungle-dnb.yaml` (card `t_e6d422ec`).
- **Clone divergence, re-measured 2026-10-16 15:31 CDT:** the pair §12's correction row records
  holds at `061b5dc` (13:34). At `e40c7f9` (15:31) it reads 0 behind / 61 ahead, because the
  reconciliation merge `ab33ad1` (14:23) cleared the 15-commit upstream deficit. The local tip
  is the part that moves.
- **Corrected in place:** §4 (the blueprint-list bullet), §7 (the `music/lyrics/` asset listing),
  §12's "Held as written" bullet and §12's corrections row 3.
- **Superseded by this pass (card `t_e6d422ec`, 2026-10-16):** `sha256 fd4a7a6b8e106b41ee380b0c28dd09882b72d7af20d52653f8c7b287b742da4b` (690 lines / 38897 B) — the census bullet above was restated as a live claim when `music/lyrics/blueprints/jungle-dnb.yaml` landed. No genre finding was reopened.

## 14. Surviving-card pass (`t_60767fb1`, 2026-10-16)

### The scorer's ruling

`music/oracle.py` @ `b2d11f7` re-scored this genre against the live registry, the quota ledger
and the calendar. Its ruling, posted on this card: **the NEWEST scoring run owns the genre.**
This card is that run, and its true score is **7.0/10** — not the 7.2 in its own title, and not
the 7.5 / 7.7 on the two `done` cards. The pre-guard pair differed by exactly
0.20 = WEIGHTS['trend_signal'] × (5.0 − 3.0): the premium the old `except` branch paid to a
FAILED trend fetch. `b2d11f7` made a failed fetch and an empty success score the same no-signal
floor (3.0), so the number is reproducible; `music/scripts/check_oracle_determinism.py` PASS.

Briefs are keyed by GENRE, so all three cards resolve to this one file. **The brief stage is
NOT re-run.** The surviving chain resumes at the stage after brief — `genre-select`.

### Every checkable claim, re-measured live

| # | Section | Claimed before this pass | Measured 2026-10-16 15:58–16:08 CDT |
|---|---|---|---|
| 1 | header | card `t_9cc9b48f` (7.5) owns the genre | surviving card `t_60767fb1`, true score **7.0**; digest `2e603d85…` superseded |
| 2 | §1, §11 | the registry `defaults:` block cited at 19–25 | the block is **20–25**; line 19 is blank (`check_brief_line_refs` FAIL) — corrected |
| 3 | §1 | two quoted `reject_signals` | rubric carries **6 criteria** and **6 reject_signals**; `no_stated_tempo_key` and `clipped_master` added to the quotes |
| 4 | §3.3, §6.4 | planner cap `MAX_DURATION_S = 420` (**anchored**); a 600 s render is impossible | cap **600** (`planner.py:148`, card `t_ae1d9243`; commit `52ae620` raised it, and the constant moved from `:104`); `elemental-earth-chamber-loop.json` is `duration: 600` with a `.rendered` marker; 600.000 s = 375 bars at 150 BPM, whole-bar |
| 5 | §4, §7, §12 | 6 lyric blueprints; `bpm = 100` fallback wrong for 150 BPM | **7** blueprints (+`jungle-dnb.yaml`, added 15:49 by card `t_e6d422ec`); the fallback reads the caption's own BPM (`planner.py:199`, `:212`), so this genre plans at 150 |
| 6 | §5 | cadence fit 6.7 | **3.3** (surviving card's true breakdown) |
| 7 | §6.1 | render log `found=3 rendered=0 skipped=3`; 3 plans; 1 queue entry | `found=13 rendered=1 skipped=12 failed=0`; **13 plans, 12 markers, 1 master + `loops/`**; queue holds **11 entries**, none of this genre |
| 8 | §6.1 | `music/suno-gen.py` absent; lineages diverged | present (42 652 B); `origin/main` is an ancestor; **0 behind / 72 ahead** at `c296db6`; `check_stage_scripts` PASS 11/11 |
| 9 | §6.2 | engine `v0.1.2`; `spec.py` has no `bpm` field | engine **`v0.1.3`**; `spec.py` carries `bpm` and `keyscale` (card `t_25a6499c` D1/D2) |
| 10 | §6.3 | three blockers: `instrumental: False`, no `--allow-empty`, hardcoded 120 BPM | **all resolved**: wrapper 354 lines = the repo copy, carrying `instrumental`/`bpm`/`keyscale` (lines 174/189/190); `check_lyrics` early-returns for instrumental (line 119); live fixture `t_8c5a6b91/t8c5a6b91-empty-lyrics.json` + `.rendered`; `translate.py` reads `req.bpm` at line 63 |
| 11 | §6.5 (new) | — | the render rail refuses a loop-claim master that fails `loop_close.py --check-only` (`.looprefused`, job rc=1, card `t_b21aeb51`); this genre's `loop-10min` shape makes its master a loop claim |
| 12 | §8.1 | `gate_sync_ready` only checks that `loop_points.json` exists | it now **measures** every seam via `gate_loop_points.check_loop` (`gate_sync_ready.py:347`); the visual gate is resolved from the registry (`stage_gates.visual`), not hardcoded |
| 13 | §8.2 | payload sync FAILs; `SRC` names a tree with no `music/`; chart wrapper ahead of the repo's | `check-payload-sync.sh` → **PASS**; `SRC` default is the lane checkout; chart wrapper 354 lines, identical to the repo's |
| 14 | §8.3 | suite green | still green — `OK: every gate passed its good artifact and failed its broken one` |
| 15 | §8.5, §12 | residue 6 `ready` + 3 `running` | **37 done / 7 running / 3 ready**; `check_oracle_board` PASS rc=0, one open card per open genre |
| 16 | §11 | `brain/playbooks/music-lane-architecture.md` reported absent | exists in this tree and in `HEAD`, rewritten at `7411afa` (head touching it `6b24a52`) |
| 17 | §3.4, §9 | `gate_youtube_authentic` fails the shipped template | unchanged: `only 4 distinct frame signature(s) across 600.0s (10 required) — this is a raw dump`, plus the missing-disclosure reason |

Held as written (re-measured, unchanged): the genre block and the five `defaults:` keys; the
genre has no `notes:` key; `gate_quota` `0/60`, `0` studio exports; the template's style block
**567 chars / 568 bytes** (1 line) — the header's "567/1000" is accurate; the template caption
`150 BPM`, instrumental, six exclude terms; `ffprobe` `pixel_scene.mp4` 5.000000 s / 14 244 B
and `loop_10min.mp4` 600.000000 s · 1280×720 · 25/1 fps; the lane → gate → required-artifact
table and all three `advisory` rungs; the `gate_loop_points` fixtures; `gate_loudness` still
the volumedetect ruler.

The checks cited above were run at revision `c296db6` (2026-10-16, before this pass's commit),
against a repository that concurrent workers were committing to — the live census values
(figures recomputed, line ranges cited, commits ahead, open cards) move while the checks run.

### Checks run at this pass

Commands: `/usr/bin/python3 music/scripts/<check>.py` and `bash music/gates/check_gate_suite.sh`,
run at revision `c296db6` (2026-10-16, before this pass's commit), against a repository that
concurrent workers were still committing to — so the live census figures move between runs of
the same check. Verbatim results:

```
FAIL check_brief_line_refs rc=1: 1 of 107 cited line range(s) does not hold — music/briefs/elemental-fire.md:605 (106 OK)
FAIL check_brief_figures  rc=1: 1 of 102 recomputed figure(s) does not match — music/briefs/elemental-water.md:600 (101 OK)
PASS check_brief_paths: 19 `mining-k8s/...` citation(s) across 14 brief(s) resolve under /home/j_kro (rc=0)
PASS check_brief_bpm_solutions: 9 styleWeight claim(s) across 14 brief(s) buy the BPM they state (rc=0)
PASS check_stage_scripts: 11 referenced script path(s) all present (rc=0)
PASS check_prompt_style_counts: 15 declared style-field length(s) across 14 template(s) match (rc=0)
PASS check_oracle_board: every open oracle genre carries exactly one open card (rc=0)
PASS check_oracle_determinism: trend fetch failure never outscores an empty success (rc=0)
PASS check_gate_lane_surface: every gate accepts the lanes lanes.yaml gives it (rc=0, card t_d9983bb9)
PASS check_doc_refs: 25 section ref(s) resolve to headings in brain/playbooks/music-lane-architecture.md (rc=0)
PASS gate suite: OK: every gate passed its good artifact and failed its broken one (rc=0)
```

`check_brief_drift` did not hold still while this pass ran: with revision `c296db6` checked out
it passed on every count in one run, and named `anime-opening.md:18` for a stale divergence in
the next, minutes later — a concurrent worker's commit had aged that count in between. Same
command, same revision, different world. Neither reading is this file's.

**This file is clean in both of the checks that were failing on it.** The residual failures
live on other briefs and are not this card's work: one figure defect
(`elemental-water.md:600`, 53 claimed lines against 88) and one line-range defect
(`elemental-fire.md:605`). The `genres.yaml` defaults-range class that this pass fixed here is
also carried by card `t_e86c2110` (`ready` on this board) for the remaining files, so that card
has one fewer file to touch. The two `FAIL` checks exit non-zero, so no failure is silent.

### Supersession chain for this file

| Revision | sha256 | Size | Pass |
|---|---|---|---|
| 1 | `12c6e2cf…` | 672 lines / 37 365 B | the revision the oracle ruling named |
| 2 | `fd4a7a6b…` | 690 lines / 38 897 B | `t_0f7aed63` aged-count pass |
| 3 | `2e603d85ef4e5b3ce41c2d69b5ff1b9210828e289bb2b6c6c3ed1dda64974457` | 692 lines / 39 339 B | the copy this pass supersedes |
| 4 | this revision | — | `t_60767fb1` surviving-card pass |

Two commits carry this pass, both path-scoped to this file: `41b7b1e` (every correction above)
and a follow-up of the same pass that condensed the pass's own time window — this file first
said `15:5x–16:2x CDT`, which is not a measured range, and it now says `15:58–16:08 CDT`, read
from the first measurement and the commit clock.

### Open items (reported, not created here)

Every open item this pass raises already has an owner card on the board, so this pass created
none:

- No queue entry exists for this genre. Adding one is the generate stage's first action (§10).
- `gate_sync_ready` and `gate_loop_points` are still not stage gates (§8.1) — the measurement
  gap is closed, the wiring gap is not.
- The residual check failures this file does not carry belong to `t_6dd13d76` (the stale-figure
  and line-range class) and `t_e86c2110` (the `genres.yaml` defaults-range class, now one file
  smaller); `t_bdb94fb7` owns the stale "path is absent" class that §6.1 and §8.2 used to
  carry. The re-emitted-card stage marker this card arrived with is `t_6599927d`.
- The loop-10min delivery chain — the discarded render output and the rail's loop close — is
  `t_320bae4c` and `t_d7f6d053`; neither changes this brief's recommendation.

## 15. The census correction row is stamped; the drift check now sees every shape this lane writes (card `t_c5a98379`, 2026-10-16)

`music/scripts/check_brief_drift.py` could see a bare count and a "N of the M genres" census, but
not the other ways this lane states the blueprint census. Card `t_c5a98379` widened it and ran it
across `music/briefs/**`. On the widened check this brief FAILed once, in §12's correction table.

- **Superseded revision of this file:** `sha256 d0dbe76af7c0fc57ee94390402de61ac8949356238f6c91339caa9e6c42036cc` (889 lines / 54 344 B).
- **Corrected in place (§12 correction row 5):** the row reads "**7** blueprints
  (+`jungle-dnb.yaml`, added 15:49 by card `t_e6d422ec`)". The number was already the live one;
  what was missing is the stamp — the row quotes BOTH the pre-pass value ("6 lyric blueprints")
  and the pass's value, and a line carrying the measurement it was taken at is a history record,
  which the check skips by rule. That rule is the remedy the check's own FAIL text prints.
- **Live at this pass (2026-10-16 17:18 CDT):** `music/lyrics/blueprints/*.yaml` holds 7 files —
  `activist`, `anime-ending`, `anime-opening`, `chill-lounge`, `epic-orchestral-boss`,
  `jungle-dnb`, `trance`. This genre still has none, so §4's decision that none is needed stands.
- **The check's change:** four shapes it could not see — an emphasis-wrapped number, a census pair
  with no `genres` after it, the same pair split across two lines, and a brace list of the
  blueprints directory — plus a bare count of blueprints. Anchoring, the fenced-quote rule and the
  two classes it already covered are unchanged. `--selftest` runs 23 cases.
- **Regression proof, same card:** `--rev e40c7f9` FAILs with 20 stale counts, 8 of them in the
  new shapes (this brief's brace list at `e40c7f9:321` among them) and none of them visible to the
  previous check; this worktree PASSes. Re-run both from the repo root.

## 16. The Rail B absence claim was stale (card `t_bdb94fb7`, 2026-10-16)

`music/scripts/check_brief_absences.py` FAILed rc=1 on §7's Rail B bullet. The brief-stage claim
(13:17) that `music/suno-gen.py` was absent from local `main` **and from all of its history** no
longer held. Re-measured on `178be75`:

```
$ git log --diff-filter=A --format='%h %ad %s' --date=short main -- music/suno-gen.py
295fc49 2026-10-09 suno-gen: instrumental mode — the reason 8 genre templates could never validate
$ git log --oneline main -- music/suno-gen.py
ba28f55 music: instrumental mode in generation path (8/12 templates unblocked)
295fc49 suno-gen: instrumental mode — the reason 8 genre templates could never validate
$ git diff --stat ab33ad1^ ab33ad1 -- music/suno-gen.py
 music/suno-gen.py | 1025 +++++++++++++++++++++++++++++++++++++++++++++++++++++
```

The reconciliation merge `ab33ad1` (14:23) is what brought the file into this checkout's `main`,
and the worktree copy is byte-identical to `main:music/suno-gen.py`. §7's bullet is corrected in
place: the reference stands, the absence does not. `check_brief_absences.py` is rc=0 repo-wide
after the four-brief pass of this card.

- **Superseded revision of this file:** `sha256 f797b25c257522d3bf4d8cec493f96d1a319d76b71d99611b580a9922f14fc3d` (914 lines / 56 493 B).

No registry value, gate, plan, blueprint, chart file or cluster object was touched, and the two
open `check_brief_line_refs` findings in this brief (its `music/genres.yaml` ranges) are not this
pass's — they were left exactly as they stand.

## 17. Declared scoring scope — machine-checked against the live rubric (card `t_00ac4f10`, 2026-10-16)

`music/scripts/check_brief_rubric_scope.py` reads the `rubric_scope` block below and
compares it, field by field, to this genre's scope COMPUTED from `music/rubrics/gamer.json`
by the panel's own resolver (`music/rubrics/panel.py`: `applicable_criteria()`,
`applicable_signals()`). It FAILs when the criterion set, the weights, the weight sum, the
applicable reject signals or the rubric version disagree with the live file. The block is a
claim about NOW; the prose above keeps this family's pre-fix record (gamer v1: five
criteria, Σw 11, scope only inside a criterion NAME) and the check never reads prose, so
that record keeps passing.

Regenerate the block after any rubric edit — one command, no hand-edit:

    /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --print-truth chiptune-8bit

```json
{
  "rubric_scope": {
    "genre": "chiptune-8bit",
    "family": "gamer",
    "rubric_version": 2,
    "pass_threshold": 7.0,
    "criteria": [
      "chip_timbre_authenticity",
      "loop_safety",
      "asset_packaging",
      "loudness_target"
    ],
    "weights": {
      "chip_timbre_authenticity": 3,
      "loop_safety": 3,
      "asset_packaging": 1,
      "loudness_target": 1
    },
    "weight_sum": 8,
    "reject_signals": [
      "chip_impossible_timbre",
      "loop_fade_or_truncation",
      "clipped_master",
      "no_stated_tempo_key"
    ],
    "reject_signals_unnamed": 0
  }
}
```
