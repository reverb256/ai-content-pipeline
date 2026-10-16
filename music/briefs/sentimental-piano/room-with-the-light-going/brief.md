# Brief — sentimental-piano: "Room With The Light Going"

> **Stage:** brief (stages.yaml: `brief` → bot `producer`) — DELIVERED; the chain resumes at
> `genre-select` (§9, §12).
> **Card:** t_fe2e10da (`music-oracle: sentimental-piano (score 8.6)`) — the surviving OPEN card
> for this genre. Board check re-run in this pass: `sentimental-piano → t_fe2e10da [running]`,
> one open card per genre, rc=0 (`music/scripts/check_oracle_board.py`).
> **Superseded cards:** t_9f7d6889 (score 8.9, done) wrote this brief; t_d706d0a3 (score 9.1,
> done) was its duplicate. Briefs in this lane are keyed by **genre**, not by card, so all three
> cards resolve to this one file.
> **Track slug:** room-with-the-light-going
> **Genre class:** **instrumental** (no lyrics by design — §4)
> **Written:** 2026-10-16 (music-producer, card t_9f7d6889) · verification passes 2026-10-16
> (card t_d706d0a3 → §10; card t_fe2e10da → §11).
> **Repo:** /home/j_kro/ai-content-pipeline @ `main`
> **Oracle:** **true score 8.4/10** — oracle dedupe ruling 2026-10-16 (`music/oracle.py` @
> `b2d11f7`): quota headroom 10.0, lane coverage 8.0, revenue potential 10.0, cadence fit 6.67,
> policy risk 10.0, trend signal 3.0. Threshold 5.0 → produce. The card title's 8.6 is not
> reachable from the fixed scorer (§11.1).
> **Revision:** the superseded blob was
> `1010965f2d911039f32c98c1eb6958692c0b1072bb54f0ef3167ee335572fa9d` (21918 B, 460 lines,
> committed by the brief stage 2026-10-16T13:21); the current digest is re-readable with
> `sha256sum music/briefs/sentimental-piano/room-with-the-light-going/brief.md`.
> **Superseded by card `t_6dd13d76` (2026-10-16T17:21-05:00 CDT):** the pre-edit blob was
> `sha256 6fdc85d43cd15c4c80a0c6cc619c9f3759bacc14f60646cf3631f44ddf3295d7` (563 lines / 30164 B).

This brief resolves the oracle card against the live registry and the live
generation path. Every number and quoted string below comes from a command or a
file read during one of this file's three passes. Nothing here is recalled.

## 1. Resolved registry entry

Command: `/usr/bin/python3 music/registry.py validate` (rc=0)

```
registry OK: 14 genres, 10 lanes, 1 stage gate rule(s)
genres: activist, anime-ending, anime-opening, chill-lounge, chiptune-8bit,
        commentary-beds, elemental-air, elemental-earth, elemental-fire,
        elemental-water, epic-orchestral-boss, jungle-dnb, sentimental-piano, trance
lanes: direct-fan, direct-license, game-assets, stock-ai-native, streaming,
       sync, sync-documentary, youtube-gaming, youtube-longform, youtube-mix
stage gate visual: lane_gate -> gate_youtube_authentic (when_absent: none)
quota ledger: period 2026-10, standard 0/60 (warn_at 55, hard_stop_at 58)
```

`music/genres.yaml` block for `sentimental-piano`:

| Field | Value |
|---|---|
| family | acoustic |
| prompt_template | `prompts/sentimental-piano.md` — resolves (4126 bytes) |
| visual_style | `visuals/soft-window-light.md` — resolves (1199 bytes) |
| lanes | sync, streaming, direct-license, youtube-longform |
| cadence | 3/wk |
| video_shape | album-30-60min |

Genre note in the registry: "Sync-friendly: slow, predictable structure, easy to
clear. Mood discovery trend."

Registry defaults that bind this track: export `studio`, stems `true`,
lyrics `human-original`, release_private `true`, gate_profile `reviewer-deepseek`.
Note on the `lyrics` default — this genre is instrumental, so the human-authorship
path does not apply to it. See §4.

The `stage gate visual:` line resolves from the genre's OWN lane set (added
2026-10-16, card t_d9983bb9): this genre has a `youtube-longform` lane, so the
visual stage is guarded by `gate_youtube_authentic`. Read it with
`/usr/bin/python3 music/registry.py gate-for-stage --stage visual --genre sentimental-piano`.

## 2. Target lanes and what each lane demands

From `music/lanes.yaml` and `music/autonomy.yaml`:

| Lane | Surface | Gate | Required artifacts | Autonomy rung |
|---|---|---|---|---|
| sync | songtradr,audiosparx | gate_sync_ready | stems, metadata, clearance_doc, instrumental_version | advisory |
| streaming | distributor (DistroKid; alt TuneCore) | gate_release_ready | ai_disclosure, isrc, metadata, master | advisory |
| direct-license | own-site | gate_sync_ready | stems, license_tiers | advisory |
| youtube-longform | youtube | gate_youtube_authentic | platform-native album-30-60min video | advisory |

Every rung is `advisory`: clean_publishes 0, platform_strikes 0, revenue_usd 0
for all four lanes. No lane may publish itself. Per `autonomy.yaml`, promotion to
`supervised` needs 10 clean advisory publishes, and j_kro approves the rung change.

Stems are mandatory for two of the four lanes (sync, direct-license), so stems are
mandatory for this track.

Instrumental sync music is the commercial reason this genre exists: the `sync`
lane requires `instrumental_version` explicitly, so deliver it as the primary
asset, not as a derived extra.

`gate_sync_ready` reads the lane's own `requires:` list at run time instead of a
hardcoded lane set (commit `54f6d3c`, card t_d9983bb9), so a lane that
`music/lanes.yaml` assigns to that gate can no longer be rejected by it.

## 3. Cadence and video shape

- Cadence: 3 tracks/week (registry) — the highest cadence of any non-utility genre.
- Video shape: `album-30-60min` (registry) and the `youtube-longform` lane shape.
- Visual template `visuals/soft-window-light.md` pairs with it: one room, one
  window, one hour of light. Palette `#f2e8d5` / `#8a7a66` / `#3a342c`. Light does
  the moving — curtain sway (8 s period), dust motes, cloud shadows every 40-90 s.
  Fixed camera, no cuts within a track, chapter fades between tracks.
- The visual template carries an authentic-content rule: vary the light story per
  upload (morning rain / golden hour / winter blue / dusk lamp). Same room is
  allowed; light and season must differ. This track's light story is **dusk,
  lamp on** (see §4).

## 4. Intent — and why this genre carries no lyrics

`music/prompts/sentimental-piano.md` states it plainly:

> This genre is instrumental. Leave the **lyrics box empty** — that is Suno's
> instrumental path.

Consequences, all binding on the downstream stages:

1. **No lyric sheet exists and none is wanted.** The only files under
   `music/` and `/var/lib/music-plans/` whose names carry `sentimental` are this
   brief directory, `music/prompts/sentimental-piano.md`, and the track's own plan
   and render markers (§5). No lyrics directory, no lyric sheet.
2. **The `lyrics` stage is a no-op for this genre.** The `writer` dispatch in
   `music/stages.yaml` produces a lyric sheet; for this genre that output would be
   out of genre. The stage must be recorded as not-applicable, not skipped silently.
3. **The `lyrics: human-original` registry default does not bind.** It exists so
   the copyright path is preserved for vocal tracks. The instrumental genres take
   the other path: no lyrics, no authorship claim. The plan this track rendered
   carries `authorship: "instrumental — no human-authored portion (AI-Generated
   Output; not registrable with a PRO)"` — read from
   `/var/lib/music-plans/sentimental-piano-room-with-the-light-going.json`.
4. The template's tag sheet is **structure control, not lyrics**: 7 tags —
   `[Intro] [Verse] [Verse] [Bridge] [Chorus] [Verse] [Outro]` — each followed by a
   parenthetical direction, e.g. `(solo felt piano, the motif, alone, pedal noise
   audible)`. Treat those parentheticals as engineering notes, never as singable text.

### The subject for this track

**Title: "Room With The Light Going."** Light story: dusk, lamp on.

The brief handed to the planner:

> A late-evening room with the light going. One person stops working and does not
> start again. The cup goes cold, the chair stays where it was, the room keeps the
> shape of the day. No words: a felt piano holds one four-note motif while the
> window light moves across the floor, reaches the wall, and leaves.

Music direction, from `prompts/sentimental-piano.md` (674-character style caption
extracted from its Style field — measured):

- neoclassical sentimental piano, **72 BPM**, 4/4
- felt piano, close-mic'd, soft hammers, audible pedal and key mechanism noise
- one singable 4-6 note motif, repeated with tiny variations
- diatonic harmony with add9/sus2/sixth colour; changes every 2-4 bars
- broken-chord left-hand ostinato; the strictness underneath makes the rubato read human
- cello and upper strings enter **only** at the peak, one soft reversed swell before phrases
- piano dry and close, world distant and reverb-washed; mid-register focus, low velocities
- exclude styles: `drums, percussion, EDM, synths, pop vocals, dramatic trailer crescendo, virtuosity`

Reject conditions — a render with any of these is **out of genre**:
- drums, percussion, or a synth pad as the lead voice
- a virtuosic run; many ideas or dense counterpoint (over-composing is the documented
  #1 failure mode for this genre)
- a trailer crescendo: the bloom is a whisper, not a wall of sound

## 5. Evidence measured during this stage — and its live state now

Quota — command `/usr/bin/python3 music/gates/gate_quota.py` (rc=0):

```
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

`music/quota-ledger.json`: period 2026-10, standard_downloads_used 0,
limit 60, studio_exports 0, credits_used 0, credits_limit 10000. The ledger also
carries a `renders:` list — **one** entry, genre `elemental-air` — with the note
that a local ACE render consumes no Suno quota. The sentimental-piano render is
NOT in that list (§11.5).

Lyrics gate: **not run — not applicable.** `gate_lyrics_original.py` requires a
lyric sheet (`--track-dir` or `--lyrics-file`); this genre has none by design (§4).

Audio — **this changed after the brief was written.** Then: none, and
`/var/lib/music-plans/` (nexus) held `final-round.json`, `smoke-chill-lounge.json`,
`testplan.json` and their markers. Now, measured live:

```
$ ls /var/lib/music-plans/
13 *.json plans + 13 *.rendered markers (plus the t_8c5a6b91/ fixture directory)
$ cat /var/lib/music-plans/sentimental-piano-room-with-the-light-going.rendered
(0 bytes -> rendered, not refused)
```

The track's plan was written at 2026-10-16T14:33 and its render completed at
14:36. The delivered master is in the engine's artifact store:

| Item | Value |
|---|---|
| artifact | `/var/lib/sunolocal/artifacts/suno-9d35527ba64645ccab967fc654681d4b.flac` |
| job | `9d35527ba64645ccab967fc654681d4b` in `/var/lib/sunolocal/jobs.sqlite3`, completed |
| bytes | 11798965 |
| duration | 180.000000 s (ffprobe) — the plan's 180 s, to the sample |
| format | flac, 48000 Hz, 2 channels |
| sha256 | `d909ad910a0cf8476bd210f671d09ef699e60fe993d42c79704b9c9318135eb9` |

No stems, no master and no release package exist for this track. `/var/lib/sunolocal/artifacts/`
holds 15 files at this pass (14 `.flac`, 1 `.wav`), newest mtime 2026-10-16T15:43.

## 6. The live generation path (measured, not assumed)

Two engines exist. Both of them can render an instrumental today — that was not
true when this brief was written, and §7 records what changed.

### 6a. The planning/render CronJobs (namespace `mining`)

| Stage | Job | Schedule | Input | Output |
|---|---|---|---|---|
| plan | `music-pipeline` | `17 */6 * * *` | ConfigMap `music-pipeline-briefs` key `briefs.json` | `/var/lib/music-plans/<name>.json` |
| render | `music-pipeline-render` | `41 */4 * * *` | plans with no `.rendered` marker | audio via `music/scripts/acestep_plan.py` |

Both schedules are live and unchanged (re-read this pass).

The live queue now holds **10** entries (ConfigMap read). Then it held one. This
track's entry is in it:

```json
{"bpm":72,"brief":"A late-evening room with the light going. ...","duration":180,
 "genre":"sentimental-piano","keyscale":"C minor","lyricsMode":"instrumental",
 "name":"sentimental-piano-room-with-the-light-going","title":"Room With The Light Going"}
```

The three markers the original brief quoted still read exactly as it recorded them:

| Marker | Bytes | Content | Meaning |
|---|---|---|---|
| `final-round.rendered` | 0 | (empty) | rendered |
| `smoke-chill-lounge.rendered` | 8 | `refused` | draft plan, refused by the renderer |
| `testplan.rendered` | 8 | `refused` | draft plan, refused by the renderer |

The render CronJob now also runs the loop-close rail added by card t_b21aeb51
(`music/scripts/loop_close.py`): a plan that claims a loop must deliver a measured
seamless loop, or the job writes a `.looprefused` marker instead of `.rendered`.

### 6b. The live service — `sunolocal`

`sunolocal-source` deployment, image tag **v0.1.3** (this brief said v0.1.2 —
the pod was rebuilt), Service ClusterIP `10.43.164.190:8123`. Probes run this pass:

```
GET /health        -> {"status":"ok"}                                            200
GET /api/v1/models -> {"engines":{"ace":{"kind":"ACE-Step 1.5","via":"acestep_plan.py -> comfyui-zephyr window"},
                                   "yue2":{"kind":"YuE2-3B","via":"yue2-zephyr http"}},
                      "default":"ace"}
```

The instrumental branch is deployed and verified present **inside the running pod**
(`kubectl exec deploy/sunolocal-source`), `sunolocal/translate.py`:

```
38:    if req.instrumental:
46:        if "instrumental, no vocals" not in caption:
47:            caption = caption + ", instrumental, no vocals"
48:        if not lyrics:
53:            lyrics = "[Instrumental]\n"
62:    bpm = None
63:    if req.bpm is not None:
64:        bpm = int(req.bpm)
65:    elif req.style_weight is not None:
67:        bpm = int(60 + req.style_weight * 120)
68:    if bpm is None:
69:        bpm = 120
72:    # Key. An EXPLICIT key signature wins ...
76:    key = req.keyscale or "C major"
```

The renderer the adapter calls exists in the pod:
`/opt/sunolocal/music/scripts/acestep_plan_direct.py` (9190 bytes) — the repo's
`acestep_plan.py` plus an HTTP fetch of the result back into the container. Its
flags: `plan --seed --name --allow-empty --qa --qa-genre --timeout`.
`sunolocal/adapters/ace_comfy.py` passes `--allow-empty`, which is what lets an
instrumental plan (no singable sections) render at all.

**Which copy is authoritative.** The pod runs v0.1.3. This repo's own mirror,
`music/sunolocal/translate.py` (113 lines), is **no longer pre-v0.1.3**: card
`t_42bc85ba` (done) reconciled it with the deployed copy, so it carries the explicit-tempo
branch (`bpm = None` at line 62, `bpm = int(req.bpm)` at line 64) and
`key = req.keyscale or "C major"` at line 76, and the two copies are byte-identical now
(`sha256 25fb26eefb6a9418d60caa0f57025753cadf13838fcc3daf18b0d000005d6fa5`); the dead third
copy was deleted by `t_0be5f2bf`. Cite the pod when the question is "what will render",
the mirror when the question is "what is in this repo". Re-measured by card `t_6dd13d76`
(§11.3).

### 6c. What this brief translates to, executed against the deployed code

Local execution of the **deployed pod copy** of `translate.suno_to_aceplan`
(fetched out of the running container; no GPU, no network) with this track's
parameters:

```
caption_chars : 674
--- variant A: lyrics empty ---
  plan.lyrics    : '[Instrumental]\n'
  caption chars  : 699   ('instrumental, no vocals' present: True)
--- variant B: lyrics = tag sheet ---
  caption chars  : 699   ('instrumental, no vocals' present: True)
  section tags   : 7  [Intro, Verse, Verse, Bridge, Chorus, Verse, Outro]
--- the plan on disk, translated by the live pod ---
  caption chars  : 699   (cue appended: True)
  bpm / key      : 72 / C minor
```

**Routing rule (corrected).** The original brief measured 843 chars for variant A
and 818 for variant B, and concluded that variant B *loses* the instrumental cue
because the old code appended it only when `lyrics` was empty. That is no longer
true: since card t_909069f0 ("variant D") the cue is appended for **every**
instrumental request. Both variants are safe; passing the template's tag sheet as
`lyrics` adds section structure and keeps the cue. This track's plan on disk takes
variant B — 7 bare tags — and the engine-side caption carried the cue.

## 7. The defects this genre faced — status now

Five defects were measured on 2026-10-16 against the then-deployed v0.1.2 engine
and the then-current queue schema. **All five are closed.** Each closure is read
from live state, not from the closing card's summary.

**D1 — BPM was not expressible; the 72 BPM anchor could not be honoured. CLOSED.**
Then: `translate.py:42` hardcoded `bpm = 120`, and the only override repurposed
Suno's style-adherence dial (`bpm = int(60 + style_weight * 120)`), so a render came
out 1.67x the anchor. Now: `bpm` is a sunolocal body extension, an explicit value
wins, and `acestep_plan.py` passes `plan["bpm"]` through verbatim. Proof on the
delivered artifact, not on the code: the render job
`9d35527ba64645ccab967fc654681d4b` recorded `"bpm": 72` in its request and the
engine plan behind it reads `"bpm": 72`. Card t_25a6499c.

**D2 — the key field received the style caption. CLOSED.** Then:
`key = req.style or "C major"`, so the ACE node received 674 characters of
paragraph as `keyscale`. Now: `key = req.keyscale or "C major"` — never the style
caption. Proof: the same job's request carries `"keyscale": "C minor"` and the
engine plan reads `"key": "C minor"`. Card t_25a6499c.

**D3 — the planner queue could not express an instrumental track. CLOSED.** Then:
the brief schema had no `instrumental` field and `planner.py --lyrics-mode` accepted
only `draft` or `ai`; a `draft` scaffold was refused by `acestep_plan.py`, and AI
lyrics are out of genre and void the authorship claim. Now: `lyricsMode:
instrumental` (or `instrumental: true`) is a first-class queue mode, `planner.py`
accepts it and refuses it on a vocal genre. Proof: the live ConfigMap entry quoted
in §6a uses `lyricsMode: instrumental`, and its plan rendered. Card t_25a6499c;
queueing done by t_a14e5d52 / t_b8afb055 / t_6d7ad524 / this genre's own entry.

**D4 — the generate stage named a script absent from this checkout. CLOSED.**
Then: `music/suno-gen.py` existed only on `origin/main` and the worktree did not
carry it. Now the file is in the worktree (42652 bytes) and on `HEAD`:
`git ls-tree -r --name-only HEAD | grep -i suno-gen` returns it.
`music/scripts/check_stage_scripts.py` therefore PASSes (§11.4). Card t_8a715681
(reconcile the diverged checkout) is done.

**D5 — the scheduled render rail could not render an instrumental. CLOSED.**
Then, two independent causes: the payload's `acestep_plan.py` hardcoded
`"instrumental": False`, and the render CronJob passed no `--allow-empty`, so an
empty-section plan exited 1 and the job wrote `refused`. Now the payload carries the
plan's own `instrumental` value, a plan that declares itself instrumental is exempt
from the draft refusal by design, and the rail rendered this genre: the marker is
0 bytes, not `refused` (§5). Card t_8c5a6b91 is done.

### Residual risks (open, and not this brief's to close)

- **The plan's key is a placeholder, not a decision.** `"key": "C minor"` in the plan
  is `planner.py`'s documented default; this genre carries no researched key. The
  release key remains j_kro's creative call. Card t_f65b0f4c.
- **The render is not in the ledger.** `music/quota-ledger.json` records exactly one
  render (`elemental-air`). This genre's render is absent, so the ledger undercounts
  delivered work. §11.5.
- **The delivered master is not durable in the pipeline.** The render rail writes the
  audio into the render pod's `/tmp` and discards it (card t_320bae4c); the copy that
  survives is the engine's own artifact store, cited in §5.
- **No stems, no master, no package.** The `stems`, `master` and `package` stages are
  still ahead of this track.
- **The clearance document and `license_tiers` do not exist** for any track in this
  lane, so the `sync` and `direct-license` gates cannot pass yet.

## 8. The generation entry for this track

`brief.json` beside this file is the machine-readable entry.

The queue hand-off the original brief deferred ("a GitOps change in another repo, so
it is handed off, not done here") **has since been done in both places**, and this
pass verified it rather than assuming it:

- `/home/j_kro/mining-k8s/helm/charts/music-pipeline/values.yaml` carries the entry
  `sentimental-piano-room-with-the-light-going` (11 briefs in the chart's list).
- the live ConfigMap `mining/music-pipeline-briefs` carries the same entry (§6a).
- the chart ships `check-queue-sync.sh`, which renders both lists and fails when they
  disagree — the drift the original brief reported ("chart `briefs: []` while the
  ConfigMap holds `smoke-chill-lounge`") is closed.

The entry's fields, from the live ConfigMap:

| Field | Value | Basis |
|---|---|---|
| name | `sentimental-piano-room-with-the-light-going` | queue key |
| genre | `sentimental-piano` | registry |
| title | `Room With The Light Going` | this brief |
| duration | 180 s | 54 bars of 4/4 at 72 BPM (bar = 3.333333 s); inside the planner's 30-420 s guard rail |
| bpm | 72 | the genre's own anchor in `prompts/sentimental-piano.md` |
| keyscale | `C minor` | the planner's documented default, NOT a creative decision (t_f65b0f4c) |
| lyricsMode | `instrumental` | §4 — no lyrics, and the scaffold path is refused |

BPM and key travel in the queue because the engine's body has no field for either;
that is what D1/D2 were about, and the render in §5 proves they arrive.

Plans are produced by `mining/music-pipeline` and rendered by
`mining/music-pipeline-render`, both scheduled (§6a). No manual
`POST /api/v1/generate` call is needed for this genre any more; the route below
stays documented because it is the path the brief stage originally measured.

```
POST http://sunolocal.mining.svc.cluster.local:8123/api/v1/generate
{"style": "<674-char caption from prompts/sentimental-piano.md>",
 "instrumental": true, "lyrics": "", "duration": 180, "title": "Room With The Light Going",
 "bpm": 72, "keyscale": "C minor", "engine": "ace", "customMode": true}
```

`bpm` and `keyscale` are required on that call, not optional: without them the
engine falls back to its own defaults (120 BPM, "C major"), which is out of genre
on tempo alone (§6b).

## 9. Next stage

Stage `brief` is complete. Next: `genre-select`.

## 10. Earlier verification pass (card t_d706d0a3, 2026-10-16) — readings, and their live value now

That pass re-measured §1-§6 and corrected §7. Its readings are recorded here as the
audit trail; where the live value has moved since, the row says so and points at the
section that carries the current text.

| Then | Live now | Where |
|---|---|---|
| deployed image tag `v0.1.2` | `v0.1.3` | §6b |
| deployed `translate.py:33-49` (bpm 120, key = style) | rewritten; explicit bpm/keyscale | §6b, §6c |
| variant A / B caption 843 / 818 chars | 699 / 699; the cue is appended in both | §6c |
| ConfigMap holds 1 queue entry | 10 entries, this track among them | §6a |
| chart `briefs: []`, ConfigMap drifted | 11 in the chart, mirrored by the ConfigMap | §8 |
| D4: `music/suno-gen.py` absent from this checkout | present, 42652 B, on `HEAD` | §7 D4 |
| D5: payload hardcodes `"instrumental": False`; rail never passes `--allow-empty` | payload carries the plan's own flag; the rail rendered this genre | §7 D5 |
| `check_stage_scripts.py` FAIL, 1 of 11 paths absent | PASS, 11 of 11 present | §11.4 |
| "no sentimental-piano plan or render exists anywhere" | plan 14:33:41, render 14:36, 180.000 s | §5 |
| board: t_9f7d6889 done, t_d706d0a3 running | both done; t_fe2e10da is the surviving open card | header |
| registry transcript ends at the quota line | one line longer: `, 1 stage gate rule(s)` + `stage gate visual:` | §1 |
| `gate_sync_ready` MIN_STEMS 4, `%PDF-` clearance, `instrumental.wav` distinct | unchanged, and the gate now reads its lane set from `lanes.yaml` | §2, §11.3 |

Still accurate as written: the renderer path and its `--allow-empty` flag, the
`gate_sync_ready` artifact requirements, the "refused" marker contents, and the
defect numbering D1-D5.

## 11. Verification pass — card t_fe2e10da (2026-10-16)

This card is the surviving oracle card for the genre. Briefs in this lane are keyed
by **genre**, so this pass wrote no second brief and started no second chain: it
re-measured the file against live state and corrected it in place.

### 11.1 Oracle ruling applied — true score 8.4, title 8.6 unreachable

Recomputed with the repo's own scorer (`music/oracle.py` imported as a module, with
`load_registry()` and `load_quota()` feeding `score_genre`): quota headroom 10.0,
lane coverage 8.0, revenue potential 10.0, cadence fit **6.6667**, policy risk 10.0,
trend signal **3.0** → **8.4**. Every total this genre can reach by trend-fetch
outcome:

| snippets | trend_signal | total |
|---|---|---|
| 0 | 3.0 | 8.4 |
| 1 | 4.4 | 8.54 |
| 2 | 5.8 | 8.68 |
| 3 | 7.2 | 8.82 |
| 4 | 8.6 | 8.96 |
| 5 or more | 10.0 | 9.1 |
| fetch raises | 3.0 | 8.4 |

So the title's **8.6 is unreachable** — it is the premium the pre-`b2d11f7` code
paid a FAILED trend fetch (`trend_signal` 5.0, which no longer exists as an output),
and **8.9 is unreachable** too (a 2026-10-09 number with a full cadence fit). 9.1
needs five or more trend snippets. Live run this pass:
`/usr/bin/python3 music/oracle.py --dry-run` prints
`sentimental-piano: 8.4/10` with the warning
`trend fetch failed for sentimental-piano (URLError(TimeoutError('timed out'))); scoring it as no signal (3.0)`.
`check_oracle_determinism.py` PASS rc=0. Threshold 5.0 → produce, so the ruling
corrects the number, not the decision.

### 11.2 Re-measured this pass, unchanged

Registry entry identical (family `acoustic`, lanes `sync, streaming, direct-license,
youtube-longform`, cadence 3/wk, `video_shape: album-30-60min`). Prompt template
4126 bytes, visual template 1199 bytes; style caption 674 characters; 7 section tags
in the template's tag sheet; one bar at 72 BPM = 3.333333 s, so 54 bars = 180.0 s.
Instrumental census still **8 of the 14** templates. `gate_quota` PASS (2026-10,
0/60, studio 0). Cluster service IP, `/health` 200, and the `/api/v1/models`
payload all identical. CronJob schedules identical. The three markers quoted in §6a
byte-identical.

### 11.3 What changed, and what this pass corrected

1. **Header** — named t_fe2e10da as the surviving card, recorded both superseded
   cards, the 8.4 ruling, the reachable-total table and the superseded digest
   `check_brief_figures.py` requires.
2. **§1** — the registry transcript was one line short of live; refreshed.
3. **§5** — audio is no longer "none": the plan and the render exist, with artifact,
   job id, size, duration and digest recorded.
4. **§6a** — the queue holds 10 entries, not 1; this track's entry quoted verbatim;
   the loop-close rail added to the render job.
5. **§6b** — image tag v0.1.3; the deployed `translate.py` quoted at its new line
   numbers; the repo mirror's pre-v0.1.3 divergence named. **Superseded by card
   `t_6dd13d76` (2026-10-16T17:21-05:00 CDT):** card `t_42bc85ba` reconciled the two
   copies, so the mirror is 113 lines and no longer diverges — §6b and this entry are
   restated, and the pre-edit blob was
   `sha256 6fdc85d43cd15c4c80a0c6cc619c9f3759bacc14f60646cf3631f44ddf3295d7` (563 lines /
   30164 B).
6. **§6c** — the variant measurement re-run against the deployed code (699/699, cue
   present in both) and the routing rule corrected.
7. **§7** — D1-D5 re-read against live state and marked CLOSED with artifact proof;
   the residual risks separated out.
8. **§8** — the queue hand-off verified in both the chart and the live ConfigMap,
   with the entry's fields and their basis; `bpm`/`keyscale` required on the manual
   route.
9. **§2** — `gate_sync_ready`'s lane set now derives from `music/lanes.yaml`.
10. **`brief.json`** — the machine-readable sibling carried the same stale readings
    (queue "1 entry", chart `briefs: []`, tag v0.1.2, D1-D5 open); re-measured and
    corrected in this pass.

### 11.4 Checks run on the committed content

```
PASS check_brief_figures      4 recomputed figure(s), 13 skipped (not repo-provable)  rc=0
PASS check_brief_drift        0 live count(s)                                          rc=0
PASS check_brief_line_refs    2 cited line range(s) resolve and hold in the worktree   rc=0
PASS check_brief_paths        14 citations across 14 briefs resolve under /home/j_kro  rc=0
PASS check_prompt_style_counts 15 declared lengths / 14 templates                      rc=0
PASS check_brief_bpm_solutions 0 styleWeight claims buy the BPM they state             rc=0
PASS check_stage_scripts      11 referenced script path(s) all present                 rc=0
PASS check_oracle_board       every one of the 12 open oracle genres carries exactly
                              one open card                                            rc=0
PASS check_oracle_determinism trend fetch failure never outscores an empty success     rc=0
PASS gate_quota               period 2026-10, 0/60, studio 0                           rc=0
```

`check_brief_paths` reported a WARN on this brief when this pass began: it cites
`mining-k8s/` without naming the checkout root, so a reader cannot tell which clone.
§8 now names `/home/j_kro/mining-k8s`.

### 11.5 Still open — not this pass's to close

- **The key is a default.** `planner.py` wrote `"key": "C minor"` (t_f65b0f4c).
- **The render ledger is incomplete.** `music/quota-ledger.json` records one render
  (`elemental-air`); this genre's render is missing from it.
- **The engine source has two divergent copies.** aip's mirror is pre-v0.1.3
  (t_42bc85ba) while the pod runs v0.1.3 (§6b).
- **The delivered master is not pipeline-durable.** The render rail writes audio into
  the render pod's `/tmp` and discards it; the durable copy is the engine's artifact
  store (t_320bae4c).
- **Stems, master, package, clearance doc and `license_tiers`** do not exist yet, so
  `curate` onward and both stem lanes are genuine first work.
- **Who dispatches this card.** The generic kanban dispatcher claims oracle cards;
  `music-pipeline-driver.service` runs the right checkout with `--board music`
  (t_41f354be) but its unit pins `Environment=DRY_RUN=1`. Until j_kro rules on
  t_41f354be §4, this card's advance to `genre-select` is posted as a card comment
  (the `hermes kanban` CLI is refused inside a dispatcher-spawned worker, t_5a93164a).

## 12. Next stage

Stage `brief` is complete and verified. Next: `genre-select` — `music/stages.yaml`
maps it to bot `producer`, and §1-§3 already carry that stage's resolution.
