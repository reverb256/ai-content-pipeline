# Brief — sentimental-piano: "Room With The Light Going"

Card: kanban `music` t_9f7d6889 · stage: brief
Oracle score: 8.9/10 · card created 2026-10-09 03:27:44
Brief written: 2026-10-16 (music-producer, run 3)
Track slug: room-with-the-light-going
Genre class: **instrumental** (no lyrics by design — see §4)

This brief resolves the oracle card against the live registry and the live
generation path. Every number and quoted string below comes from a command or a
file read during this stage. Nothing here is recalled.

## 1. Resolved registry entry

Command: `/usr/bin/python3 music/registry.py validate` (rc=0)

```
registry OK: 14 genres, 10 lanes
genres: activist, anime-ending, anime-opening, chill-lounge, chiptune-8bit,
        commentary-beds, elemental-air, elemental-earth, elemental-fire,
        elemental-water, epic-orchestral-boss, jungle-dnb, sentimental-piano, trance
lanes: direct-fan, direct-license, game-assets, stock-ai-native, streaming,
       sync, sync-documentary, youtube-gaming, youtube-longform, youtube-mix
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

1. **No lyric sheet exists and none is wanted.** Command:
   `find /home/j_kro/ai-content-pipeline/music /var/lib/music-plans -iname '*sentimental*'`
   → one hit: `music/prompts/sentimental-piano.md`. No lyrics directory, no plan,
   no audio.
2. **The `lyrics` stage is a no-op for this genre.** The `writer` dispatch in
   `music/stages.yaml` produces a lyric sheet; for this genre that output would be
   out of genre. The stage must be recorded as not-applicable, not skipped silently.
3. **The `lyrics: human-original` registry default does not bind.** It exists so
   the copyright path is preserved for vocal tracks. The instrumental genres take
   the other path: no lyrics, no authorship claim, and the ACE renderer is driven
   with `--allow-empty` (measured — see §6).
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

## 5. Evidence measured during this stage

Quota — command `/usr/bin/python3 music/gates/gate_quota.py` (rc=0):

```
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

`music/quota-ledger.json`: period 2026-10, standard_downloads_used 0,
limit 60, studio_exports 0, credits_used 0, credits_limit 10000.

Lyrics gate: **not run — not applicable.** `gate_lyrics_original.py` requires a
lyric sheet; this genre has none by design (§4).

Audio: none. `/var/lib/music-plans/` (nexus) holds `final-round.json`,
`smoke-chill-lounge.json`, `testplan.json` and their `.rendered` markers. No
sentimental-piano plan or render exists anywhere.

## 6. The live generation path (measured, not assumed)

Two engines exist. Only one of them can render an instrumental today.

### 6a. The planning/render CronJobs (namespace `mining`)

| Stage | Job | Schedule | Input | Output |
|---|---|---|---|---|
| plan | `music-pipeline` | `17 */6 * * *` | ConfigMap `music-pipeline-briefs` key `briefs.json` | `/var/lib/music-plans/<name>.json` |
| render | `music-pipeline-render` | `41 */4 * * *` | plans with no `.rendered` marker | audio via `music/scripts/acestep_plan.py` |

The live queue holds one entry today (ConfigMap read):

```json
[{"brief":"a late-night kitchen where someone finally stops working and just listens to the rain",
  "genre":"chill-lounge","lyricsMode":"draft","name":"smoke-chill-lounge","title":"Kitchen Light"}]
```

The marker files show what that queue actually produced:

| Marker | Bytes | Content | Meaning |
|---|---|---|---|
| `final-round.rendered` | 0 | (empty) | rendered |
| `smoke-chill-lounge.rendered` | 8 | `refused` | draft plan, refused by the renderer |
| `testplan.rendered` | 8 | `refused` | draft plan, refused by the renderer |

### 6b. The live service — `sunolocal` (the path that can render this genre)

`sunolocal-source` deployment, image tag **v0.1.2**, Service ClusterIP
`10.43.164.190:8123`. Probes run during this stage:

```
GET /health        -> {"status":"ok"}
GET /api/v1/models -> {"engines":{"ace":{"kind":"ACE-Step 1.5","via":"acestep_plan.py -> comfyui-zephyr window"},
                                   "yue2":{"kind":"YuE2-3B","via":"yue2-zephyr http"}},
                      "default":"ace"}
```

The instrumental branch is deployed and verified present **inside the running pod**
(`kubectl exec deploy/sunolocal-source`), `translate.py`:

```
33:    if req.instrumental and not lyrics:
34:        caption = caption + ", instrumental, no vocals"
38:        lyrics = "[Instrumental]\n"
42:    bpm = 120
45:        bpm = int(60 + req.style_weight * 120)
49:    key = req.style or "C major"
```

The renderer the adapter calls exists in the pod:
`/opt/sunolocal/music/scripts/acestep_plan_direct.py` (9190 bytes) — the repo's
`acestep_plan.py` plus an HTTP fetch of the result back into the container. Its
flags: `plan --seed --name --allow-empty --qa --qa-genre --timeout`.
`adapters/ace_comfy.py` passes `--allow-empty`, which is what lets an instrumental
plan (no singable sections) render at all.

### 6c. What this brief translates to, executed against the deployed code

Local execution of the deployed `translate.suno_to_aceplan` with this track's
parameters (no GPU, no network — the module is imported from the chart payload and
the same file is present in the pod):

```
caption_chars : 674
--- variant A: lyrics empty ---
  plan.lyrics    : '[Instrumental]\n'
  caption tail   : ...' and hopeful at once, instrumental, no vocals'
  caption chars  : 843   ('instrumental, no vocals' present: True)
  render check   : sections=1 empty=['Instrumental']   -> renders with --allow-empty
--- variant B: lyrics = tag sheet ---
  caption tail   : ...' to solo piano, nostalgic and hopeful at once'
  caption chars  : 818   ('instrumental, no vocals' present: False)
  render check   : sections=6 empty=[Intro, Verse, Verse, Bridge, Verse, Outro] -> renders with --allow-empty
```

**Routing rule derived from that measurement.** Variant A is the default and the
safe route: pass `instrumental: true` with an empty `lyrics`, and the caption gains
the ", instrumental, no vocals" steering text. Variant B (passing the template's
tag sheet as `lyrics`) keeps the section structure but **loses** the instrumental
cue, because `translate.py` only appends it when `lyrics` is empty. To get both,
send the tag sheet as `lyrics` **and** append ", instrumental, no vocals" to the
`style` text yourself.

## 7. Defects that will block this genre downstream (measured)

**D1 — BPM is not expressible; the genre anchor cannot be honoured.**
`translate.py:42` hardcodes `bpm = 120`. The only override is
`translate.py:45`, `bpm = int(60 + style_weight * 120)`, which repurposes Suno's
*style-adherence* dial as a tempo control. This genre's anchor is 72 BPM
(template §4). Measured: the live translation yields **120 BPM, 1.67x too fast**.
Reaching 72 costs `style_weight = 0.1` — i.e. telling the engine to barely follow
the style it was given, to buy the right tempo. Effect: any sentimental-piano render
on the current route is out of genre on tempo alone.

**D2 — the key field receives the style caption.**
`translate.py:49`, `key = req.style or "C major"`. `req.style` is the 674-character
caption, and `acestep_plan.py` passes it straight into the ACE node as `keyscale`
(`"keyscale": plan["key"]`). So the model is handed a 674-character paragraph where
a key signature belongs. Measured in the probe: `key` = the full caption string.

**D3 — the planner queue cannot express an instrumental track.**
The brief schema in `mining-k8s/helm/charts/music-pipeline/values.yaml`
(`{name, genre, brief, lyricsMode?, language?, title?, duration?}`) has **no
`instrumental` field**, and `planner.py` has no instrumental mode
(`--lyrics-mode` accepts only `draft` or `ai`). A sentimental-piano entry queued
there therefore produces either a draft scaffold or AI-written lyrics. Both are
wrong: the scaffold is refused by `acestep_plan.py` (exit 1) — exactly what the two
`refused` markers in §6a record — and AI lyrics are (a) out of genre for an
instrumental track and (b) void the human-authorship claim.

Counted on disk, not recalled. Command:
`grep -li 'is instrumental|leave the lyrics box empty' music/prompts/*.md`
→ **8 of the 14 templates declare the instrumental path**: chill-lounge,
chiptune-8bit, commentary-beds, elemental-air, elemental-earth, elemental-fire,
elemental-water, sentimental-piano. So this defect affects most of the registry.

Note for whoever fixes D3: the inline comment in the deployed `translate.py`
(heavily relied on by §6b) says "8 of the 14 genre templates are instrumental" and
then lists **9** names, including `epic-orchestral-boss`. That name does not declare
the instrumental path anywhere in `music/prompts/epic-orchestral-boss.md`
(measured: 0 matches for the marker). Use the 8 measured above.

**D4 — stale stage prompt.** `music/stages.yaml` tells the generate stage to run
`music/suno-gen.py`. No file named `suno-gen*` exists under `/home/j_kro` other than
`music/gates/fixtures/suno-generated-umbrellas-in-space.txt` (a test fixture). The
generate stage currently names a missing script.

## 8. The generation entry for this track

`brief.json` beside this file is the machine-readable entry.

Canonical fields (`name`, `genre`, `brief`, `title`, `duration`) match the
`music-pipeline` brief schema so the entry can join the shared queue unchanged.
`instrumental: true` and `lyricsMode: null` are stated explicitly and documented as
**not honoured** by that schema (D3) — they are there so no downstream reader
mistakes this for a vocal track.

- name `sentimental-piano-room-with-the-light-going`
- genre `sentimental-piano`
- title `Room With The Light Going`
- duration **180 s**, basis: 72 BPM in 4/4 → one bar = 4×60/72 = 3.3333 s;
  54 bars = 180.0 s. Inside the planner's 30-420 s guard rail
  (`planner.py` MIN_DURATION_S=30, MAX_DURATION_S=420).
- lyrics: none (instrumental, §4)

The route that can render this today is `sunolocal`, not the planner queue:

```
POST http://sunolocal.mining.svc.cluster.local:8123/api/v1/generate
{"style": "<674-char caption from prompts/sentimental-piano.md, + ', instrumental, no vocals'>",
 "instrumental": true, "lyrics": "", "duration": 180, "title": "Room With The Light Going",
 "engine": "ace", "customMode": true}
```

BPM and key must be corrected before or at that call, or the render is out of genre
(D1, D2).

Queueing into `mining-k8s/helm/charts/music-pipeline/values.yaml` is a GitOps change
in another repo, so it is handed off, not done here. The chart's `briefs:` list is
currently `[]` while the live ConfigMap holds `smoke-chill-lounge` — chart values and
the live ConfigMap have drifted.

## 9. Next stage

Stage `brief` is complete. Next: `genre-select`.
