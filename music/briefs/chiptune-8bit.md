# Brief — chiptune-8bit

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`)
> **Card:** t_9cc9b48f (`music-oracle: chiptune-8bit (score 7.5)`)
> **Duplicate card:** t_05b640f6 (`music-oracle: chiptune-8bit (score 7.7)`) — same genre,
> same lanes, emitted by an earlier oracle run before the dedupe guard existed.
> Both resolve to THIS brief; the brief is keyed by genre, not by card.
> **Written:** 2026-10-16T13:17-05:00 (CDT), profile `music-producer`, run 77
> **Verified (duplicate-card pass, `t_05b640f6`):** 2026-10-16T13:40-05:00 (CDT) — see §12.
> One claim was withdrawn (§8.4); three items were corrected (§6.1, §8.3, §8.5). The canonical
> card `t_9cc9b48f` is `done`; this brief is the one artifact both oracle cards resolve to.
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `afa242e` (main) at this pass — NOT `~/Projects/ai-content-pipeline`,
> which is a second clone without a `music/` tree (both verified below).
> **Oracle score:** 7.5/10 (quota headroom 10.0, lane coverage 6.0, revenue 8.0,
> cadence fit 6.7, policy risk 9.0, trend signal 3.0). Threshold 5.0 → produce.

Every number and quoted string below comes from a command run or a file read during this
stage. Nothing is recalled. Where something is unknown, it says so.

---

## 1. Genre resolution (live, not transcribed)

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

Registry `defaults:` that bind every track (`music/genres.yaml` lines 19–25):
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

Its `reject_signals` list includes two that will bite a lazy render:

- "chiptune claim with reverb/pads/realistic instruments or >2-note chords per channel"
- "fade-out or truncated ending on a game-loop claim"

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
3. **The `loop-10min` shape is 600 s, and no stage renders 600 s of audio.** The shape
   template measures exactly 600.000 s (ffprobe), but the planner caps a plan at 420 s
   (`planner.py` `MAX_DURATION_S = 420`) and the deployed engine's bpm/duration handling is
   unguarded (§6). Decision: **render one ≤ 420 s loop whole-bar-exact, mark the loop point,
   and let the visual stage tile it to 600 s.** That is what a game loop is for, and it is
   the only arrangement the current engine supports.
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
| 256 | 409.60 s | longest whole-bar length under the 420 s planner cap (420 s = 262.5 bars, not whole) |

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
- **No blueprint is required.** `music/lyrics/blueprints/` holds `activist.yaml`,
  `anime-ending.yaml`, `anime-opening.yaml`, `chill-lounge.yaml`, `epic-orchestral-boss.yaml`, `trance.yaml`. The planner falls back to `bpm = 100` when a
  blueprint is absent — for a 150 BPM genre that fallback is wrong, and it is one more reason
  the plan's `bpm` must be set explicitly rather than inherited (§6.3).
- **`--lyrics-mode ai` is not a temptation here.** There are no lyrics to generate. The
  generate stage must pass the instrumental flag, not an AI-written sheet.

---

## 5. Throughput budget (derived, not assumed)

Cadence 2 tracks/week (§1) × the lane set (game-assets pack + one 10-minute gaming video +
one streaming release per track) = **2 loops/week, 104/year**. At 64 bars each that is ≈ 3.4
minutes of new audio per week — small. The real cost is downstream per-track packaging, not
rendering: stems, loop points, metadata, ISRC, artwork, and a distinct visual per upload.

This is why the genre's oracle score shows lane coverage 6.0 and cadence fit 6.7 — it is a
low-volume, high-packaging genre. Budget the packaging, not the generation.

---

## 6. The generation path — measured, with one genre-blocking defect

### 6.1 Two rails exist. Only one is live.

**Rail A — the cluster planner/render queue** (this is what runs by itself):

| Stage | Job | Schedule | Input | Output |
|---|---|---|---|---|
| plan | CronJob `music-pipeline` (ns `mining`) | `17 */6 * * *` | ConfigMap `music-pipeline-briefs` key `briefs.json` | `/var/lib/music-plans/<name>.json` |
| render | CronJob `music-pipeline-render` (ns `mining`) | `41 */4 * * *` | plans without a `.rendered` marker | audio via `sunolocal` |

Both ran in the last hour. Real logs:

```
$ kubectl logs job/music-pipeline-render-29869541 -n mining --tail=5
ComfyUI up at http://comfyui-zephyr.mining.svc.cluster.local:8188
skip   final-round (already rendered)
skip   smoke-chill-lounge (already rendered)
skip   testplan (already rendered)
done: found=3 rendered=0 skipped=3 failed=0
```

The planner job's last line was `done: 1/1 planned`. The queue is live, and it is empty of
useful work: `/var/lib/music-plans/` holds only `final-round`, `smoke-chill-lounge` and
`testplan` (all `.rendered`). **No chiptune plan exists.** The brief ConfigMap still carries
one entry, the chill-lounge smoke brief.

**Rail B — `music/suno-gen.py` (Suno over CDP).** `music/stages.yaml` tells the generate stage
to use it. It does **not** exist in this checkout, and never appears in the history of the
local `main` branch. It does exist on `origin/main`, added by `ba28f55`. Measured now:

```
$ git log --oneline -1 main          → ade6e87
$ git log --oneline -1 origin/main   → ba28f55
$ git merge-base main origin/main    → e278f61
$ git rev-list --left-right --count main...origin/main → 6   15   # 22   15 at the t_05b640f6 pass
$ git cat-file -e origin/main:music/suno-gen.py → EXISTS on origin/main
$ ls music/suno-gen.py               → No such file or directory
```

The two lineages have diverged: `rev-list --left-right --count main...origin/main` measured
**22  15** at the verification pass — up from `6  15` when this brief was written, because
this wave's brief commits landed on local main. `music/suno-gen.py` is still absent from
local main and still present on `origin/main`. The generate stage as written cannot run in
this tree. Fix is a branch reconciliation, not a rewrite.

### 6.2 The live engine and its exact contract (probed, not assumed)

```
$ kubectl get deploy sunolocal-source -n mining   → image localhost/sunolocal:v0.1.2, Ready 1/1, age 2d14h
$ kubectl exec deploy/sunolocal-source -n mining -- \
    curl? no — probed over HTTP from an in-cluster pod:
    GET /health        → {"status":"ok"}
    GET /api/v1/models → {"engines":{"ace":{"kind":"ACE-Step 1.5","via":"acestep_plan.py -> comfyui-zephyr window"},
                          "yue2":{"kind":"YuE2-3B","via":"yue2-zephyr http"}},"default":"ace"}
```

The deployment's own env names the renderer:
`SUNOLOCAL_ACESTEP_SCRIPT=/opt/sunolocal/music/scripts/acestep_plan_direct.py` (9190 bytes on
disk in the pod). Request schema (`sunolocal/spec.py`) has **no `bpm` field**: the wire
contract is `prompt, style, lyrics, title, instrumental, model, customMode, negativeTags,
vocalGender, duration, styleWeight, weirdnessConstraint, audioWeight, variety, callBackUrl,
seed, engine`.

The engine **can** render an instrumental. `sunolocal/translate.py` in the pod:

```python
if req.instrumental and not lyrics:
    caption = caption + ", instrumental, no vocals"
    lyrics = "[Instrumental]\n"
```

and `adapters/ace_comfy.py` passes `--allow-empty` to the renderer, so the empty-body
instrumental passes the renderer's loader. The instrumental path exists end to end on the
engine side.

### 6.3 THE BLOCKER: the scheduled wrapper hardcodes `instrumental: False`

The render CronJob runs `/payload/music/scripts/acestep_plan.py`, mounted from ConfigMap
`music-pipeline-payload` (volume `payload`, `workingDir: /payload`). Extracted from the live
ConfigMap, that wrapper contains:

```python
"instrumental": False,  # we assume lyrics present; if empty and allow-empty, still instrumental?
```

That is line 87 of the deployed wrapper. Consequences for **this** genre:

- The request can never carry `instrumental: true` on the scheduled rail. Chiptune-8bit is
  instrumental by its own template (§4), so the scheduled path would submit the genre's
  parenthetical tag sheet as `lyrics` with the vocal flag off — a vocal-shaped hole, which is
  the exact failure the engine-side comment warns about.
- The CronJob invokes the wrapper **without** `--allow-empty`, and the wrapper's own
  `check_lyrics` exits 1 on an empty body. A plan with `lyrics: ""` would therefore be marked
  `.rendered` containing `refused` (visible precedent:
  `/var/lib/music-plans/smoke-chill-lounge.rendered` and `testplan.rendered` both say
  `refused`), i.e. silently parked as "waiting for a human" forever.
- **The request carries no BPM, and the deployed `translate.py` hardcodes `bpm = 120`**
  (`bpm = 120` unless `styleWeight` is set, then `bpm = int(60 + style_weight * 120)`, clamped
  30–240). This genre is specified at **150 BPM**. Rendered through the as-deployed wrapper
  (`"style_weight": None`) the engine will produce **120 BPM** chiptune — out of genre. The
  arithmetic remedy exists and is exact: `60 + 0.75 * 120 = 150`, i.e. **`styleWeight = 0.75`
  yields 150 BPM**. With `styleWeight` left `None`, 120 is unavoidable.

So three things must change before the generate stage can produce a correct chiptune track:
carry `instrumental: true` for this genre, pass `--allow-empty`, and pin the tempo (either
`styleWeight = 0.75` or a fixed `bpm` plumbed through `translate.py`). None of these is
plausible to do inside this brief stage; all three are named here so the generate stage does
not rediscover them as mysteries.

### 6.4 What the engine cannot do at all today

A 600 s render. The planner's guard rail is 30–420 s, and `translate.py` takes `duration`
straight from the request with no upper guard. §3.3 resolves this by tiling at the visual
stage rather than asking for one 10-minute render.

---

## 7. Existing assets for this genre

Measured: **none.**

- `music/lyrics/` holds `activist/`, `anime-opening/`, `chill-lounge/`, `trance/` plus
  `blueprints/{activist,anime-ending,anime-opening,chill-lounge,epic-orchestral-boss,trance}.yaml`. No chiptune lyric dir or blueprint —
  expected, the genre is instrumental.
- No campaign directory, no masters, no stems, no cover artwork, no `loop_points.json`.
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

`music/stages.yaml` runs `gate_quota`, `gate_lyrics_original`, `gate_stems_present`,
`gate_loudness`, `gate_quality`, `gate_release_ready` and `gate_youtube_authentic` — and
**never** `gate_sync_ready` or `gate_loop_points`. The `package` stage runs
`gate_release_ready` (the streaming gate) for every genre, whatever its lanes.

So a chiptune card would pass the pipeline while never having its loop seam measured, and the
one gate that exists specifically for the seam is referenced only by a runbook and by the
`check_gate_suite.sh` fixtures. `lane.game-assets.gate: gate_sync_ready` in `lanes.yaml` is a
declaration nothing consumes at stage level; `gate_sync_ready` itself only checks that the
*file* `loop_points.json` exists, and it says so: "run gate_loop_points.py for the seam
check". The seam gate is in the toolbox, in the runbook, and in the fixture suite — and in
no stage of the pipeline.

### 8.2 The chart's payload-sync check FAILS on this host (wrong source path + real drift)

The ConfigMap `music-pipeline-payload` is generated by `mining-k8s`
(`helm/charts/music-pipeline`, Argo app `music-pipeline` — `Synced/Healthy`). Its sync scripts:

```
$ bash helm/charts/music-pipeline/check-payload-sync.sh
DRIFT  music/planner/planner.py
DRIFT  music/genres.yaml
DRIFT  music/scripts/acestep_plan.py
RESULT: FAIL — run sync-payload.sh
```

Two independent problems, both measured:

1. **`SRC` defaults to the wrong checkout.** Both scripts use
   `SRC="${SRC:-/home/j_kro/Projects/ai-content-pipeline}"`. That tree has **no `music/`
   directory** (`ls /home/j_kro/Projects/ai-content-pipeline` → no `music`), so
   `cmp -s "$SRC/$rel" "$dst/$rel"` reports DRIFT on every file, and `sync-payload.sh`
   (which is `set -euo pipefail`) would abort at its first `cp`. This is the same wrong-path
   bug that killed the systemd music units, in a third place.
2. **The chart copy is newer than the repo, not older.** The chart's
   `files/music/scripts/acestep_plan.py` is a *sunolocal-API* wrapper
   (`SUNOLOCAL_HOST=...:8123`, `POST /api/v1/generate`). The repo's copy — local and on
   `origin/main` (`diff` → identical) — is still the older *direct-ComfyUI* version. The
   wrapper's history lives in `mining-k8s` (`b326135`, `f1d9f66`, `7fdb9d2`), not in
   ai-content-pipeline (`git log --all -- music/scripts/acestep_plan.py` → one commit,
   `6b5cb56`).

**Therefore "just run sync-payload.sh" is wrong advice**: with `SRC` corrected it would
regress the live wrapper back to direct-ComfyUI. The instrumental-flag fix in §6.3 has to land
in the chart's wrapper (and be back-ported to the repo), not the other way round.

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
passing ones. Re-confirmed verbatim at this pass: `PASS seamless loop (1.6x curvature)` /
`FAILS phase-slip loop (6.0x curvature) fails`.

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
**Status at the `t_05b640f6` pass (re-measured):** `t_9cc9b48f` is **done** — it wrote this
brief (`c3e2f23`) — and `t_05b640f6` is the running duplicate whose pass produced §12. The
pair is resolved, not duplicated. Board-wide residue has shrunk as this wave closed out:
**6 `ready` and 3 `running`** `music-oracle:*` cards (was 15 / 7 at the brief stage).

---

## 9. Gate path for the finished artifact

1. `gate_stems_present` — ≥ 4 stems, non-zero bytes, ±0.5 s of the master (natural split:
   pulse 1 / pulse 2 / triangle / noise)
2. `gate_loop_points` — seam curvature ratio ≤ 3.0x, loop region not silent, span ≥ 2 s
3. `gate_loudness` — this gate measures `ffmpeg volumedetect` mean_volume, **not gated LUFS**
   (measured 1.4–2.4 dB below ebur128 on a real album). Note the ruler difference before
   calling a master defective.
4. `gate_quality` — reviewer model **different** from the producer; scored against
   `music/rubrics/gamer.json` (pass 7.0), where `chip_timbre_authenticity` and `loop_safety`
   each weight 3
5. `gate_sync_ready --lane game-assets` — stems + `loop_points.json` + manifest metadata
   (title, artist, bpm, key, mood, genre) + clearance doc + AI disclosure + instrumental
   version that is not a byte-copy of the master
6. `gate_release_ready` — streaming package (ai_disclosure, ISRC per ISO 3901 — 12 chars, no
   check digit, artwork)
7. `gate_youtube_authentic` — ≥ 10 distinct frame signatures across the visual, Jaccard
   ≤ 0.85 vs prior uploads, AI disclosure beside the video
8. `gate_human_approval` — j_kro. Never auto-passes.

---

## 10. Recommended next stage

**`lyrics` → advance immediately as instrumental** (§4), then **`generate`**, whose prompt the
next worker must treat as needing three corrections before it can succeed for this genre:

1. `instrumental: true` must reach the engine — the deployed wrapper hardcodes `False` (§6.3).
2. `--allow-empty` must be passed, or an empty-body plan is marked `.refused` and parked (§6.3).
3. The tempo must be pinned — the deployed `translate.py` hardcodes 120 BPM and the request has
   no `bpm` field; `styleWeight = 0.75` is the exact lever for this genre's 150 BPM (§6.3).

Deliverable for `generate`: **one 64-bar (102.40 s) whole-bar loop at 150 BPM**, no reverb, no
pads, four voices, ending on the loop phrase — plus a second take for curation. Render on the
`sunolocal` rail; do not attempt Rail B (Suno) until `music/suno-gen.py` exists in this tree
(§6.1). Then `curate` → `stems` → `master` → `gate` → `package`
(`gate_sync_ready --lane game-assets` + `gate_loop_points`, both currently un-wired, §8.1) →
`visual` (a real 600 s pixel-scene video, not the 4-signature template, §3.4) →
**human-approval** → `publish` (PRIVATE / draft only — never public without j_kro) → `track`.

Human queue raised by this brief (reported, not fixed here — none of these is this stage's
work): the payload-sync source path and wrapper drift (§8.2), the missing game-assets gate
wiring in `stages.yaml` (§8.1), and the branch divergence that hides `suno-gen.py` (§6.1). The
duplicate chiptune card (§8.5) is **closed** by the `t_05b640f6` pass recorded in §12.

---

## 11. Provenance

- Registry: `music/genres.yaml` (lines 19–25, 119–125), `music/lanes.yaml`, `music/autonomy.yaml`
  — validated live (`registry OK: 14 genres, 10 lanes`)
- Rubric: `music/rubrics/gamer.json` (read in full)
- Gates: `music/gates/` — `gate_quota`, `gate_loop_points`, `gate_sync_ready`,
  `gate_youtube_authentic`, `gate_release_ready` read; suite executed
- Stage contract: `music/stages.yaml` (read in full)
- Runbook: `brain/runbooks/music-game-assets.md`
- Cluster: CronJobs `music-pipeline`, `music-pipeline-render`; Deployments
  `sunolocal-source` (v0.1.2), `comfyui-zephyr`; ConfigMap `music-pipeline-payload`;
  Argo apps `music-pipeline`, `sunolocal` (`Synced/Healthy`)
- Chart: `/home/j_kro/mining-k8s/helm/charts/music-pipeline/` (`values.yaml`, `sync-payload.sh`,
  `check-payload-sync.sh`, executed), `helm/charts/sunolocal/files/music/sunolocal/{spec,studio,translate}.py`
- Media: `ffprobe` on `music/visuals/pixel_scene.mp4` and `loop_10min.mp4`
  (`/home/j_kro/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin/ffprobe` — ffmpeg is not on PATH)
- **Still dangling:** `brain/playbooks/music-lane-architecture.md` is cited as "READ FIRST" by
  this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`, `autonomy.yaml`,
  `gates/README.md` and the gate docstrings — the file does not exist in this repo. Section
  numbers quoted from it (§3, §5, §11.2, §13) cannot be checked.

---

## 12. Duplicate-card verification pass (`t_05b640f6`, 2026-10-16T13:40-05:00 CDT)

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
- Bar arithmetic (1.600 s/bar), the planner cap `MAX_DURATION_S = 420`, and the fallback
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
- Rail B: `music/suno-gen.py` is absent from local `main` **and** from all of local `main`'s
  history (`git log main -- music/suno-gen.py` → empty), present on `origin/main` from
  `ba28f55`; merge-base `e278f61`.
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
- **Blueprint census, re-measured 2026-10-16 15:31 CDT:** 6 of the 14 genres have a lyric
  blueprint (`activist`, `anime-ending`, `anime-opening`, `chill-lounge`,
  `epic-orchestral-boss`, `trance`); the other 8 do not. This genre still has none, and none is
  wanted — §4's decision is unchanged.
- **Clone divergence, re-measured 2026-10-16 15:31 CDT:** the pair §12's correction row records
  holds at `061b5dc` (13:34). At `e40c7f9` (15:31) it reads 0 behind / 61 ahead, because the
  reconciliation merge `ab33ad1` (14:23) cleared the 15-commit upstream deficit. The local tip
  is the part that moves.
- **Corrected in place:** §4 (the blueprint-list bullet), §7 (the `music/lyrics/` asset listing),
  §12's "Held as written" bullet and §12's corrections row 3.
