# Brief — jungle-dnb

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`)
> **Card:** t_006db63d (`music-oracle: jungle-dnb (score 7.0)`)
> **Duplicate card:** t_f8b2fa7f (`music-oracle: jungle-dnb (score 7.2)`) — same genre,
> same lanes, emitted 10 minutes after this one on an earlier oracle run. Both resolve to
> THIS brief; the brief is keyed by genre, not by card. Close one, do not work both.
> **Written:** 2026-10-16 (CDT), profile `music-producer`, run 83
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `0e4fe5b` (main; the working tree moved twice
> while this brief was being written — sibling cards are committing to the same clone).
> NOT `~/Projects/ai-content-pipeline`, which has no `music/` tree at all (§11.1).
> **Oracle score:** 7.0/10 as emitted on 2026-10-09 (quota headroom 10.0, lane coverage 6.0,
> revenue 5.5, cadence fit 6.7, policy risk 9.0, trend signal 3.0). Threshold 5.0 → produce.
> **Recomputed today: 6.5/10** — only `cadence_fit` decayed (6.7 → 3.33), because the score
> is a function of the days left in the quota period and the period ends 2026-10-31.

Every number and quoted string below comes from a command run or a file read during this
stage. Nothing is recalled. Where something is unknown, it says so and names the test.

**Bottom line:** the genre and its registry entry are healthy, the prompt template is the
strongest part of the block, and the live generation rail **cannot currently render this
genre in genre**: the plan's tempo (168 BPM, correctly resolved) is dropped between the
planner and the engine and replaced with 120 BPM — 40 BPM below the jungle pocket — while
the text field the engine does receive still says "168 BPM". Details and evidence in §6.3.

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

`/usr/bin/python3` is the interpreter that has PyYAML (6.0.3). The bare `python3` on this
worker's PATH resolves to `/home/j_kro/.hermes/tools/python-3.14.7+20260901-linux-x64/bin/python3`
and has **no `yaml` module** — measured:

```
$ /usr/bin/python3 probe_yaml_import.py   → interpreter /usr/bin/python3, PyYAML PRESENT 6.0.3
$ python3        probe_yaml_import.py   → interpreter .../tools/python-3.14.7+..., PyYAML MISSING
                                          ModuleNotFoundError: No module named 'yaml'
```

That is not trivia: it is the root cause of a live dispatch failure (§11.3).

| Field | Value |
|---|---|
| Genre | `jungle-dnb` |
| Family | `edm` |
| Prompt template | `music/prompts/jungle-dnb.md` — resolves, 4 032 bytes |
| Visual style | `music/visuals/urban-grain.md` — resolves, 1 157 bytes |
| Lanes | `streaming`, `youtube-mix`, `direct-license` |
| Cadence | 2/wk |
| Video shape | `mix-60min` |
| Lyric blueprint | **none** — 3 of 14 genres have one (activist, chill-lounge, trance) |
| Registry note | `"Same Beatport ban applies. Amen-break / ragga vocal direction."` |

Registry `defaults:` that bind every track (`music/genres.yaml` lines 19–25):
export `studio`, stems `true`, lyrics `human-original`, release_private `true`,
gate_profile `reviewer-deepseek`.

The genre's own block (`music/genres.yaml` lines 47–54) in full:

```yaml
  jungle-dnb:
    family: edm
    prompt_template: prompts/jungle-dnb.md
    visual_style: visuals/urban-grain.md
    lanes: [streaming, youtube-mix, direct-license]
    cadence: 2/wk
    video_shape: mix-60min
    notes: "Same Beatport ban applies. Amen-break / ragga vocal direction."
```

Deployment check — the live planning payload carries this exact template and registry:

```
$ kubectl -n mining get configmap music-pipeline-payload -o go-template='{{index .data "music__prompts__jungle-dnb.md"}}' | md5sum
c91b4d0e0f53d3abf9c17dc501801088     (repo: c91b4d0e0f53d3abf9c17dc501801088 — identical)
$ ... '{{index .data "music__genres.yaml"}}' | md5sum
3386db64eb5780da5988cdb5a37f8f03     (repo: 3386db64eb5780da5988cdb5a37f8f03 — identical)
```

So the in-cluster planner reads the same genre block this brief resolved.

### 1.1 Where this genre sits in the fleet's own scoring

`music/rubrics/edm.json` — family `edm`, `genres: ["trance", "jungle-dnb"]`,
`pass_threshold: 7.0`. Six criteria, and the three heavy ones are the ones this genre
can fail on:

| Criterion | Weight | Type |
|---|---|---|
| `tempo_pocket` | 3 | measured |
| `genre_engine` | 3 | craft |
| `dance_structure` | 2 | craft |
| `low_end_discipline` | 2 | measured |
| `loudness_target` | 1 | measured |
| `arrangement_development` | 1 | craft |

The tempo anchor is genre-specific and narrow:

> **Jungle: 160–175 BPM, classic jungle 160–170, modern DnB 170–176 with 174 the centre**
> (EDMProd jungle guide; Veena DnB table). … If the top candidate is a clean double/half of
> an in-range candidate, prefer the interpretation that matches the claimed substyle.

And one reject signal is written for this genre alone:

> "jungle claim with straight un-chopped feel and no reese/sub evidence in the style claim"

Two others will bite a lazy render: "measured BPM has no candidate inside any substyle
pocket (tempo fraud: wrong genre wearing the label)" and "clipped master
(max_volume_db >= -0.1) — digital clipping is never genre-authentic".

### 1.2 The oracle's own arithmetic, recomputed

| Component | Weight | Card (2026-10-09) | Recomputed 2026-10-16 |
|---|---|---|---|
| Quota Headroom | 0.25 | 10.0 | 10.0 |
| Lane Coverage | 0.20 | 6.0 | 6.0 |
| Revenue Potential | 0.20 | 5.5 | 5.5 |
| Cadence Fit | 0.15 | 6.7 | **3.33** |
| Policy Risk | 0.10 | 9.0 | 9.0 |
| Trend Signal | 0.10 | 3.0 | 3.0 |
| **Total** | | **7.0** | **6.5** |

Each number reproduces from `music/oracle.py`:

- `quota_headroom` = 10 × (1 − 0/58) = 10.0
- `lane_coverage` = 3 viable lanes × 2 = 6.0
- `revenue_potential` = (youtube 500 + distributor 200 + own-site 400) / 200 = 5.5
- `policy_risk` = 10 − 1 (a `youtube-mix` lane) = 9.0
- `trend_signal` = 3.0 — the DuckDuckGo scrape returned **0** result snippets. This is a
  null reading, not a signal that jungle is cold. Do not read it as market intelligence.
- `cadence_fit` = f(days left in period). 2/wk with 22 days left → 6.7 on 2026-10-09;
  2/wk with 14 days left → 3.33 today.

**Consequence for the board:** every oracle card's score silently decays with the calendar.
A card that scored 7.0 on 2026-10-09 is a 6.5 today and will be 5.4 on 2026-10-26. The
threshold is 5.0. Any card not worked this month ages out of its own justification.

---

## 2. Intent

A soundsystem jungle record: **168 BPM drums over an ~84 BPM bassline**, built from chopped
breaks rather than loops, with a ragga toast on the slow grid. The product is the genre's
function, not a mood — it has to sound like UK pirate radio in 1994, not like a modern DnB
roller. The template states the failure mode in one line: *"If a generation sounds polished
and synth-bassed, it has crossed into DnB — reject it."*

### Craft contract (from `music/prompts/jungle-dnb.md` — the write-to spec)

| Constraint | Value |
|---|---|
| Tempo | **168 BPM** drums; **160–175** pocket, sweet spot 165–170 |
| The load-bearing relationship | **Two speeds.** Drums 168, bassline at half that (~84 BPM, reggae/dancehall feel). "A bassline that fights the break at 170 kills the jungle feel instantly." |
| Breaks | Chopped and resequenced — Amen (The Winstons "Amen, Brother") lineage, plus Think/Apache/Hot Pants. Sliced into 1/8–1/32 fragments, ghost notes, pitch variances, reverse hits, edits every few bars |
| Timbral era | **12-bit sampler crunch** is authentic (Akai S950/SP-1200 heritage), vinyl crackle, time-stretch artifacts allowed. "Clean 24-bit breaks are wrong for this genre." |
| Sub-bass | Sine/triangle, **40–60 Hz, mono**, long sliding notes answering the kick, not doubling it |
| Vocal | Ragga toasting on the **slow grid** against the bass, never chopped to the fast drum grid. Short chantable phrases, call-and-response, crowd address ("massive!", "rewind!") |
| Dub techniques | Delays, tape echo, spring reverb splashes, airhorns, sirens, rewinds |
| Weirdness / Style Influence | 55% / **80%** per the template — see §6.3, this 80% is a problem on the live rail |
| Exclude styles | `liquid DnB rollers, pop EDM, half-time dubstep, autotune R&B, stadium house` |
| Structure | Intro → break states once → hook → re-chop → call-and-response hook → filtered tension → full pressure → outro subtracts |
| Instrumental fallback | The template allows it: "If Suno cannot deliver a convincing ragga toast, generate the instrumental and treat the vocal hook as a stem-layer edit downstream." |

Style-field length: the template header claims **"653/1000 chars"**. Measured between the
first ```` ```text ```` fences, newlines stripped: **653 chars**. The claim is accurate
(unlike chiptune-8bit's, which is 277 chars wrong). Inside Suno's 1 000-char Styles box with
347 chars of headroom — none of the §2 table has to be trimmed to fit.

The lyrics-guidance block is 473 chars and is a section map, not lyrics. It is not
copyrightable and must not be shipped as a lyric sheet (§4).

---

## 3. Target lanes and what each lane demands

Live reads from `music/lanes.yaml` and `music/autonomy.yaml`.

| Lane | Surface | Shape | Gate | Required artifacts | Rung |
|---|---|---|---|---|---|
| `streaming` | distributor (DistroKid; alt TuneCore) | — | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` | advisory |
| `youtube-mix` | youtube | `mix-60min` | `gate_youtube_authentic` | — (gate checks the visual) | advisory |
| `direct-license` | own-site | — | `gate_sync_ready --lane direct-license` | `stems`, `license_tiers` | advisory |

All three lanes are at rung **advisory**: nothing publishes without j_kro. The evidence
counters in `music/autonomy.yaml` are all zero (0 clean publishes, 0 strikes, $0).

**Beatport is banned for this genre** (registry note; `BANNED_SURFACES` in `music/oracle.py`
line 83 lists `beatport`). The registry note reads "Same Beatport ban applies", meaning the
trance ban of 2026-08-12 also covers jungle-dnb. This is the genre's natural home and it is
closed, which is why the oracle's `revenue_potential` lands at 5.5 rather than higher: the
best-paying surface for jungle is not available to this operation. The three open lanes are
the compensation.

**Lane consequence for the deliverable:** `streaming` wants one master per track;
`youtube-mix` wants a 60-minute continuous mix; `direct-license` wants stems **and** a
license-tier document. The mix is the expensive artifact (§5, §6.5) — the engine renders at
most 600 s per pass, so a 60-minute mix is 6+ renders stitched, and every one of them must
carry the same two-speed relationship or the mix will drift out of genre across its length.

---

## 4. The lyrics stage APPLIES (decision, with evidence)

**This genre is VOCAL.** `music/prompts/jungle-dnb.md` spends a third of its length on
lyrics guidance: a `[Hook]` marked "(ragga toast, 2-4 short lines, crowd-addressing: 'all
massive inside!')", a `[Hook]` marked "(call-and-response: lead vocal line, then a chopped
vocal answer)", and the rule "Short chants, not verses". The 8-ish instrumental genres
(chill-lounge, sentimental-piano, commentary-beds, the four elementals, chiptune-8bit,
epic-orchestral-boss) say the opposite in their templates. jungle-dnb does not.

So the `lyrics` stage runs, and its contract is a **human** one:

```
$ /usr/bin/python3 music/lyrics/lyrics.py scaffold --genre jungle-dnb ...   # writes a scaffold + manifest
   ... a human writes the sung lines ...
$ /usr/bin/python3 music/lyrics/lyrics.py claim --track-dir music/lyrics/jungle-dnb/<slug>
```

`claim` records the authorship claim in `manifest.json` (schema
`music/track-lyrics-manifest v1`) bound to a **sha256 of the sheet**, with `authors` and
`written_at`. The repository's one completed example,
`music/lyrics/activist/what-runs-beneath/manifest.json`, reads:

```json
"authorship": {
  "status": "human-original",
  "authors": ["j_kro"],
  "written_at": "2026-10-08T12:48:59+00:00",
  "ai_assist": "Lyric text written by j_kro. Suno will only render vocals from this text; it did not write or edit any line.",
  "suno_generated_lyrics": false
}
```

**This is the pipeline's only hard human dependency before the approval gate.** No bot can
satisfy it: `registry defaults` set `lyrics: human-original`, and `cmd_claim` refuses to
record a claim over an empty or machine-generated sheet. A ragga toast for this genre must
be written by j_kro. Plan the card around that, not as a blocker discovered later.

Two live counterexamples make the rule concrete rather than theoretical:

1. There is **no blueprint for jungle-dnb**. Blueprints exist for 3 of 14 genres
   (`music/lyrics/blueprints/{activist,chill-lounge,trance}.yaml`). The planner's
   `load_blueprint()` returns `{}` for this genre, so `bpm_anchor_for()` falls through to
   the caption — which works (§6.3), but the `[theme]` and `title_candidates` a blueprint
   would supply are absent.
2. `planner.py`'s own docstring records the incident that created the caption-BPM path:
   *"without it the draft path fell back to a flat 100, which is right for almost nothing:
   **jungle-dnb came out at 100 against its own stated 168**, and anime-opening at 100
   against its stated 160."* This genre is the named regression case for that fix.
3. A rendered plan on this host, `/var/lib/music-plans/final-round.json` (anime-opening),
   carries `"authorship": "AI-GENERATED (not eligible for a human-authorship claim)"` and
   `"lyrics_mode": "ai"`. That is a vocal track whose lyrics void the copyright path the
   registry defaults exist to protect. jungle-dnb must not be queued that way.

---

## 5. Throughput budget (derived, not assumed)

- Cadence 2/wk → ~9 tracks across the 31-day period at full rate.
- Quota ledger, live: `standard_downloads_used: 0 / 60` (warn 55, hard stop 58),
  `studio_exports: 0` (unlimited), `credits_used: 0 / 10000`. `gate_quota` PASSES today:

  ```
  $ /usr/bin/python3 music/gates/gate_quota.py
  PASS gate_quota
    period          : 2026-10
    standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
    studio exports  : 0
  ```

- The registry binds `export: studio`, so the 60/month standard-download cap does not bind
  as long as exports go through Studio. Rule 2 of the lane is unchanged: **never the
  standard download button.**
- Per track the artifact set is: 1 master (streaming, −14 ±1 dB), 1 instrumental version
  (a real render, not a byte-copy — `gate_sync_ready` checks this), ≥4 stems, plus a 60-min
  mix for the youtube lane. Stems are mandatory.
- The 60-minute mix is the throughput bottleneck, not the songs: at the engine's 600 s
  per-render ceiling (§6.5) a 60-min mix needs ≥6 renders whose tempos agree.

---

## 6. The generation path — measured, with the genre-blocking defect

### 6.1 Two rails exist. Only one is live.

| Rail | Entry point | Live? |
|---|---|---|
| A — `sunolocal` (in-cluster, CPU-plan + GPU render via ComfyUI on zephyr) | `music-pipeline` CronJob (17 */6 * * * * → planner) → `music-pipeline-render` CronJob (41 */4 * * *) → `/payload/music/scripts/acestep_plan.py` → `sunolocal.mining.svc.cluster.local:8123` | **YES.** Service answers `{"status":"ok"}`. |
| B — Suno CDP (Premier session, `music/suno-gen.py`) | `music/suno-gen.py` | **NO — the file does not exist in this tree.** `ls music/suno-gen.py` → `No such file or directory` |

```
$ cd /home/j_kro/ai-content-pipeline && git status -sb | head -1
## main...origin/main [ahead 19, behind 15]
```

The clone is 19 commits ahead and 15 behind its own origin (`origin/main` carries the
missing `suno-gen.py`; card t_8a715681 tracks the reconciliation). Until that lands, the
only rail a queued jungle-dnb brief can use is Rail A. A generate stage that plans around
Suno CDP has planned around a file that is not there.

The live render CronJob, verbatim from its template:

```python
r = subprocess.run(
    [sys.executable, "/payload/music/scripts/acestep_plan.py",
     str(plan), "--name", stem])
```

Note what is **not** passed: there is no `--allow-empty` at this call site (§6.4).

The node-side plans directory, read live:

```
$ ls -la /var/lib/music-plans/
final-round.json  final-round.rendered       # anime-opening, AI lyrics
smoke-chill-lounge.json  smoke-chill-lounge.rendered
testplan.json  testplan.rendered
```

**No jungle-dnb plan exists.** The live brief queue holds exactly one entry:

```
$ kubectl -n mining get configmap music-pipeline-briefs -o go-template='{{index .data "briefs.json"}}'
[{"brief":"a late-night kitchen where someone finally stops working and just listens to the rain",
  "genre":"chill-lounge","lyricsMode":"draft","name":"smoke-chill-lounge","title":"Kitchen Light"}]
```

Queue entry schema is `{name, genre, brief, lyricsMode?, language?, title?, duration?}`
(chart `values.yaml`, `briefs:` — currently `[]` in git, overridden by GitOps). jungle-dnb
needs an entry there before the render stage can see it — that is the handoff in §12.

### 6.2 The live engine and its exact contract (probed, not assumed)

The chain, read from the deployed source:

1. `music-pipeline-render` → `/payload/music/scripts/acestep_plan.py` (the API client).
2. → `POST http://sunolocal.mining.svc.cluster.local:8123/api/v1/generate` with
   `build_suno_request(plan)`.
3. `studio.py` → `_to_internal(body)` → `_run_job` → `render_acestep(suno_to_aceplan(request))`.
4. `translate.py::suno_to_aceplan` produces the ACE plan.
5. `adapters/ace_comfy.py::render_acestep` writes that plan to a temp file and runs
   `/opt/sunolocal/music/scripts/acestep_plan_direct.py --allow-empty`, which builds a
   4-node ComfyUI workflow and POSTs it to ComfyUI.
6. ComfyUI (zephyr, :8188) runs `RunningHub ACE-Step` nodes.

`/opt/sunolocal/music/scripts/acestep_plan_direct.py` is byte-identical in the pod and both
chart copies (`md5 2b66e52562fa2aaa6b3161f543c8081d`). Step 5's workflow node, verbatim:

```python
"2": {"class_type": "RunningHub ACE-Step GenerationParams",
      "inputs": {"caption": plan["caption"],
                 "lyrics": plan["lyrics"],
                 "bpm": int(plan["bpm"]),
                 "duration": float(plan["duration"]),
                 "keyscale": plan["key"],
                 "timesignature": str(plan["timesignature"])}},
```

The engine's own schema, read live from ComfyUI (`GET /object_info` on
`http://localhost:32188` → 200; `/queue` → `{"queue_running": [], "queue_pending": []}`):

| Node | Inputs (live) |
|---|---|
| `RunningHub ACE-Step GenerationParams` | `caption` STRING, `lyrics` STRING, **`bpm` INT default 100, min 30, max 300**, **`duration` FLOAT default 160, min 10, max 600**, `keyscale` STRING, `timesignature` STRING. No optional inputs. |
| `RunningHub ACE-Step Creator` | `dit_handler`, `llm_handler`, `params`, `seed` INT 0–4294967295 |
| `RunningHub ACE-Step Loader` | `llm type` ∈ {`acestep-5Hz-lm-1.7B`, `acestep-5Hz-lm-4B`}, default 4B |
| `RunningHub ACE-Step Artist` | `llm_handler`, `prompt`, `vocal_language` (50 languages), **`instrumental` BOOLEAN**, `seed` |

Three facts fall straight out of that table and they matter for this genre:

1. **`bpm` is a real input and it is accepted** (INT 30–300). There is no silent-ignore
   excuse available: whatever value the chain hands the node is the value ACE-Step is asked
   to render at.
2. **The manual node has no `instrumental` input.** Instrumental-ness is expressed only by
   the `lyrics` text. `instrumental` exists solely on the `Artist` node — the node this
   pipeline deliberately refuses to use (the direct renderer's docstring: *"Handing the
   same brief back to Artist would throw the plan away and re-invent it"*).
3. **`duration` is capped at 600 s per render.** A 60-minute mix cannot be one render.

### 6.3 THE BLOCKER: the plan's tempo is dropped and replaced with 120 BPM

The planner resolves this genre's tempo correctly. `planner.py`:

```python
def bpm_in_caption(caption):
    """The BPM the genre's own caption states, e.g. "ragga jungle, 168 BPM". ...
    jungle-dnb came out at 100 against its own stated 168"""
    m = re.search(r"(\d{2,3})\s*BPM", caption or "", re.I)
    return int(m.group(1)) if m else None
```

The jungle caption opens `ragga jungle, 168 BPM, chopped and resequenced Amen break …`, so
`template_bpm = 168`, and with no blueprint present `bpm_anchor_for()` returns **168**. The
plan says 168. That is the last point in the chain where anyone sees 168.

The payload's API client then throws it away:

```python
def build_suno_request(plan: dict) -> dict:
    return {
        "prompt": plan.get("caption", ""),
        "lyrics": plan.get("lyrics", ""),
        "title": plan.get("title", ""),
        "instrumental": False,
        "duration": int(plan.get("duration", 180)),
        "style_weight": None,        # <-- no bpm, no key, no style
        ...
    }
```

There is no `bpm` field to send (the wire model `SunoGenerateRequest` has none) and
`style_weight` is hardcoded `None`. So `translate.py` takes its default branch:

```python
# BPM: default 120; could derive from style_weight or variety
bpm = 120
if req.style_weight is not None:
    bpm = int(60 + req.style_weight * 120)      # 0-1 -> 60-180
bpm = max(30, min(240, bpm))
...
"key": req.style or "C major",                  # style is never sent -> always "C major"
```

| Plan says | Client sends | `translate.py` yields | ACE node receives |
|---|---|---|---|
| `bpm: 168` | `style_weight: None` (and no bpm field) | `bpm = 120` | `bpm: 120` |
| `key: "E minor"` (example) | (no key field) | `key = "C major"` | `keyscale: "C major"` |
| `caption` | `prompt` (caption) | `caption` | **caption still contains the text "168 BPM"** |

Consequences, in order of severity for this genre:

1. **120 BPM is 40 BPM below the jungle pocket (160–175)** — 25% slow. The rubric weights
   `tempo_pocket` at 3 and its first reject signal is *"measured BPM has no candidate inside
   any substyle pocket (tempo fraud: wrong genre wearing the label)"*. A render from this
   rail is not merely imperfect; by the fleet's own rubric it is a different genre.
2. **The caption contradicts the parameter.** The engine is handed `bpm: 120` while the only
   text it reads says "ragga jungle, 168 BPM, chopped and resequenced Amen break …". Two
   conflicting tempo instructions, one numeric, one textual.
3. **The template's own Style Influence value under-shoots even if wired.** The template
   says Style Influence **80%**. Under the deployed formula that is
   `int(60 + 0.8 × 120) = 156 BPM` — 4 BPM below the pocket floor of 160, and 12 below the
   genre's stated 168. **The lever for 168 is `style_weight = 0.90`** (`60 + 0.9 × 120 =
   168`). Expecting the documented 80% to produce this genre is a documented mistake, not a
   possible one.
4. **Key is always `C major`.** `translate.py` derives the key from the wire `style` field,
   which the client never sets. The engine's `keyscale` default is `B minor`; the chain
   overrides it with `C major`. Nothing in the plan's key reaches the engine.

**What I measured, and what I did not.** I did not render a jungle-dnb track: no plan
exists, and consuming a GPU window is not this stage's work. What is measured is:

- The live sunolocal job store (6 jobs, `jobs.sqlite3` copied out of the pod). The one
  completed ACE job for the chill-lounge smoke render,
  `260e4b344cef4b668c94d8871ad5723c`, stored a request with **no `styleWeight` key at all**
  — so by the code path above, the plan it rendered carried `bpm: 120`.
- Its artifact, fetched from `/var/lib/sunolocal/artifacts/` and measured with the panel's
  own tool (`music/rubrics/measure.py`, ffmpeg 9.0.1):

  ```
  duration_s 30.0 · 48 000 Hz · stereo · flac
  mean_volume_db -16.8 · max_volume_db 0.0 · crest_factor_db 17.1
  bpm 76.0 (confidence 0.24) · candidates [76.0 (0.24), 152.0 (0.109)]
  silences_ge_1s: 19.98s -> 30.00s      (the last 10 s of a 30 s file are silent)
  pct_energy_above_8khz 1.69 · rms_1s_spread_db 48.3
  ```

  **That artifact measures 76.0 BPM, which matches neither the 120 the chain carries nor
  exactly the 75 written in its own caption text.** So I can prove the value *sent to the
  engine* (code + stored request) and I cannot yet prove how ACE-Step converts that value
  into audio. Two readings are consistent with the evidence and I will not pick one by
  guessing: (a) ACE-Step conditions tempo primarily on the caption text and largely ignores
  `bpm`; (b) the estimate is unreliable here — the file ends in 10 s of silence, only ~20 s
  of music remains, and confidence is 0.24 with a plausible 152 BPM octave.
  Also note `max_volume_db 0.0`: **the live rail produced a clipped master**, which is a
  reject signal in the edm rubric in its own right (`max_volume_db >= -0.1`).

  The test that settles (a) vs (b) is one controlled A/B on the GPU rail:
  render the same caption twice, once with `style_weight = 0.9` (→ 168 BPM) and once with it
  absent (→ 120 BPM), and measure both with `measure.py`. If both come back near 76, the
  `bpm` input is cosmetic and the fix must be a caption-level tempo strategy; if they
  diverge with the parameter, the wrapper fix in §10 is sufficient. That test is the first
  work item of the generate stage, and it is written into the handoff card in §12.

**Correction to the record.** An earlier sibling brief attributed this to the deployed
wrapper "hardcoding `instrumental: False`". For jungle-dnb that flag is *correct* — this
genre has vocals. The genre-blocking field is the tempo, not instrumental-ness. The
instrumental problem belongs to the 8 instrumental genres, and on this rail it is worse than
a flag: see §6.4.

### 6.4 The wrapper forces `--allow-empty`, so the draft guard never fires

`adapters/ace_comfy.py` invokes the renderer as:

```python
cmd = [sys.executable, str(script), str(plan_path), "--seed", ..., "--name", stem,
       "--allow-empty", "--timeout", "600"]
```

`--allow-empty` is passed **unconditionally**. The renderer's own guard exists precisely to
catch this (`check_lyrics`): *"A draft plan scaffolds sections for a human and they are
EMPTY. Rendering a draft silently produces an instrumental with a vocal-shaped hole, which
looks like a model failure and is not one."* On the sunolocal rail that guard is dead code:
the adapter always says the emptiness is fine.

For a vocal genre that is the silent failure mode to watch: a draft or scaffold lyric sheet
renders as a vocal-less track that passes `acestep_plan_direct.py`, gets saved as audio, and
only looks wrong much later. Card t_bc6a0c00 already tracks the adjacent defect (the draft
guard accepts wrapped parenthetical direction lines as lyrics). Both belong to the same
theme: **nothing between the planner and the engine refuses an un-singable lyric sheet.**

### 6.5 What the engine can and cannot do for this genre

- **Duration:** 600 s per render max (§6.2). This is fine for one track (the rubric's
  `dance_structure` anchor puts jungle at 4–7 min) and it is the constraint on the
  60-minute mix — ≥6 renders, all at the same tempo, stitched.
- **No loop-point or stem export on this rail.** Suno Studio is the only path that produces
  the stems the `direct-license` lane requires (`requires: [stems, license_tiers]`); the
  ACE render returns a single stereo file. Whoever runs the stems stage must know which rail
  can actually produce stems.
- **Two-speed bass is not expressible as one `bpm`.** The genre's core is 168 BPM drums over
  ~84 BPM bass. One integer cannot carry both; the second speed must live in the caption
  text and the lyrics/bassline writing, or the render will come back one-tempo. State it in
  the plan's caption explicitly (the template already does) and do not expect the `bpm`
  field to imply it.
- **`12-bit sampler crunch`** (the template's authenticity requirement) is a *production*
  requirement the text-to-music engine does not reliably deliver. Expect to satisfy it in
  the stem/master stage (bitcrush + vinyl noise on the break bus), not to get it free.

---

## 7. Visual identity — and a measured gate failure

`music/visuals/urban-grain.md` (1 157 bytes) is the write-to spec: 1994 London night,
sodium-streetlight orange `#e8871e` on wet asphalt black `#101216`, sodium-and-neon palette,
frame-rate play as the signature (chop between 12/24 fps every few bars), stutter-cuts of
2–4 frames on the chopped snares, 12-bit grain 8–10%, VHS head-switching noise bar, and a
vertical 0.5 s tape-rewind roll on airhorn hits. 60-minute continuous mix, scenes cut on
phrase boundaries (every 32 bars max), rotating street corner / rooftop / warehouse doorway
between uploads.

Two rendered assets exist. Both FAIL the lane's own gate:

```
$ /usr/bin/python3 music/gates/gate_youtube_authentic.py --visual music/visuals/urban_grain.mp4
FAIL gate_youtube_authentic
  - visual has only 2 distinct frame signature(s) across 5.0s (sampled every 2.0s;
    10 required) — this is a raw dump (static image + audio), which YouTube's
    inauthentic-content policy penalizes
  - no disclosure file (one of disclosure.txt, ai_disclosure.txt) beside the visual

$ ... --visual music/visuals/mix_60min.mp4
FAIL gate_youtube_authentic
  - visual has only 4 distinct frame signature(s) across 3600.0s (sampled every 2.0s;
    10 required) — this is a raw dump (static image + audio), which YouTube's
    inauthentic-content policy penalizes
  - no disclosure file (one of disclosure.txt, ai_disclosure.txt) beside the visual
```

Measured with ffprobe:

| Asset | Bytes | Duration | Frames | Resolution | Verdict |
|---|---|---|---|---|---|
| `urban_grain.mp4` | 14 151 | 5.0 s | 125 @ 25 fps | 1280×720 | FAIL, 2 signatures (genre stub — not a mix) |
| `mix_60min.mp4` | 42 857 593 | 3600.0 s | 90 000 @ 25 fps | 1280×720 | FAIL, 4 signatures (the shape template itself) |

**The 60-minute template declared as this genre's `video_shape` cannot pass
`gate_youtube_authentic` as it stands.** The `visual` stage must render a real edit (the
`urban-grain.md` motion grammar exists for exactly this) and write the AI-disclosure file.
The genre's own 5-second stub is not a mix and cannot be stretched into one.

---

## 8. Existing assets for this genre

| Asset | Path | State |
|---|---|---|
| Prompt template | `music/prompts/jungle-dnb.md` | complete, 4 032 B, style field 653/1000 |
| Visual style doc | `music/visuals/urban-grain.md` | complete, 1 157 B |
| Visual render | `music/visuals/urban_grain.mp4` | 5 s stub — fails the gate (§7) |
| Lyric blueprint | — | **does not exist** (3 of 14 genres have one) |
| Lyrics/track dir | — | none (`music/lyrics/` has activist, chill-lounge, trance only) |
| Cluster payload | `music-pipeline-payload` ConfigMap | carries the template + registry, md5-verified (§1) |
| Plans | `/var/lib/music-plans/` | **no jungle-dnb plan** |
| Brief queue | `music-pipeline-briefs` ConfigMap | **no jungle-dnb entry** (only `smoke-chill-lounge`) |
| Rendered audio | — | none. Three artifacts in the sunolocal store, all from other genres/tests. |

---

## 9. Gate path for the finished artifact

In stage order, with what each one actually executes:

1. `gate_lyrics_original --track-dir music/lyrics/jungle-dnb/<slug>` — parses the sheet,
   measures sections + unique words, scans for Suno-generator markers, verifies the
   sha256-bound human claim in `manifest.json`. `--strict` additionally enforces known Suno
   section tags. **This gate cannot pass without j_kro's lines** (§4).
2. `gate_quota` — live PASS, 0/60.
3. `gate_stems_present --master <master> --stems-dir <dir>` — ≥4 stems (default), non-zero
   bytes, durations within tolerance of the master. Mandatory for `direct-license`.
4. `gate_loudness --master <master> --target streaming` — `ffmpeg volumedetect`
   `mean_volume`, −14 dB for streaming / −16 for sync, ±1 dB default tolerance. This is RMS
   in the volumedetect dialect, **not gated LUFS** — a known ruler difference, already filed
   as card t_9546841b. Do not call a master defective on the ruler's word alone.
5. `gate_quality --package-dir <pkg>` — verifies the review record exists, is sha256-bound to
   the master, and that the reviewer model DIFFERS from the producer model. Review is
   `reviewer-deepseek` per the stage map; an independent review, not self-review.
6. `gate_sync_ready --package-dir <pkg> --lane direct-license` — stems + master +
   instrumental (which must differ from the master) + manifest metadata + a real clearance
   document + AI disclosure.
7. `gate_release_ready --package-dir <pkg>` — ffprobes the master, PIL-verifies artwork,
   ISO 3901 ISRC syntax, manifest metadata + `ai_disclosure`.
8. `gate_youtube_authentic --visual <mp4>` — ≥10 distinct frame signatures, Jaccard
   ≤ 0.85 against `upload_index.json` prior uploads, disclosure file present. Currently
   **FAILS on both existing assets** (§7).
9. `gate_human_approval` — j_kro. Never auto-passes, by design.

---

## 10. Recommended next stage

**`genre-select` → `lyrics` (human) → `generate`.** In that order, for these reasons:

- `genre-select` is one command now that the entry is resolved and verified here
  (`registry OK: 14 genres, 10 lanes`, all three lanes present in `lanes.yaml`): nothing is
  left to resolve.
- `lyrics` is the card's **real critical path** and it needs j_kro. Start it early; do not
  discover it at the generate stage. The deliverable is a track dir under
  `music/lyrics/jungle-dnb/<slug>/` containing a complete `lyrics.suno.txt`, a
  `manifest.json` with `authorship.status: human-original`, and the `claim` record. Ragga
  toast: 2–4 short chantable lines per hook, call-and-response, crowd address, written on
  the slow grid — plus, if the vocal path is dropped, the template's documented fallback is
  a separate `instrumental` version built as a stem-layer edit (§2).
- `generate`, whose prompt the next worker must treat as needing four corrections before it
  can succeed for this genre:

  1. **The tempo must reach the engine.** Today the plan's 168 is replaced by 120 in
     `translate.py` because the payload client sends no bpm and `style_weight: None`
     (§6.3). Either pass the plan's bpm through the client, or set `style_weight = 0.9`
     (→ 168) — 0.9, not the template's documented 0.8, which yields 156 and lands below the
     pocket floor.
  2. **Run the A/B test first** (§6.3): one render at `style_weight = 0.9`, one with it
     absent, both measured with `music/rubrics/measure.py`. Until that is done, nobody
     knows whether the `bpm` input even steers ACE-Step. Do not spend a queue slot
     pretending it does.
  3. **The lyric sheet must be complete before render**, because `ace_comfy.py` passes
     `--allow-empty` and nothing else will stop an empty scaffold from rendering a
     vocal-shaped hole (§6.4).
  4. **Duration:** ≤600 s per render; target 300 s (5 min) for the streaming master, inside
     the rubric's 4–7 min jungle anchor. The 60-minute mix is assembled from ≥6 renders at
     the same tempo — the tempo correction above must hold for every one of them, or the
     mix drifts out of genre mid-length.

Then `curate` → `stems` (the Suno Studio rail is the only one that yields stems, §6.5) →
`master` (−14 streaming, ±1 dB, and fix the 0.0 dBFS clipping the live rail produces) →
`gate` (reviewer-deepseek, `music/rubrics/edm.json`, pass 7.0) → `package` →
`visual` (a real `urban-grain` edit with a disclosure file — both existing assets fail the
gate today, §7) → **human-approval** → `publish` (PRIVATE / draft only) → `track`.

---

## 11. Defects found while writing this brief

Everything in this section was measured today on nexus. Items 11.1–11.6 reproduce unless
stated otherwise. The board already carries cards for most of this; where it does, the card
id is named and this brief adds the genre-specific consequence rather than a duplicate.

### 11.1 The live stage driver walks a checkout with no `music/` tree

```
$ grep ExecStart ~/.config/systemd/user/music-pipeline-driver.service
ExecStart=/bin/bash /home/j_kro/Projects/ai-content-pipeline/scripts/automation/pipeline-driver.sh --board music
$ ls -d /home/j_kro/Projects/ai-content-pipeline/music
ls: cannot access ... : No such file or directory
```

That tree is at HEAD `9aa1a23` and its driver is dated Sep 3 (12 618 B) — the
pre-parameterization copy that cannot route by board. Its own log
(`.../performance/pipeline-driver.log`, 1 564 983 B, last written 13:19 today) runs every
30 minutes and never names a board:

```
2026-10-16T13:19:37-05:00 pipeline driver run start
2026-10-16T13:19:40-05:00 pipeline driver run complete (dispatched 0, running 0/1)
```

The correct tree's log names the board but has not dispatched since 2026-10-09. Filed as
t_41f354be (`ready`, nexus-core) and t_19d0714b (`blocked`, ops — the dispatcher-ownership
decision). Nothing in this brief changes those; the point for THIS card is that no stage
advance it can perform would be consumed.

### 11.2 `advance-stage.sh` cannot advance anything from a worker

`scripts/automation/advance-stage.sh` ends in
`hermes kanban --board "$BOARD" comment "$CARD" "stage: $STAGE"`. From a dispatcher-spawned
worker that CLI is fenced:

```
$ hermes kanban --board music list
kanban: delegate_task child contexts cannot mutate Kanban tasks or boards
```

The script therefore reports success while writing nothing — the silent no-op already filed
as t_5a93164a. The working substitute is to write the `stage: <name>` marker as a kanban
comment through the `kanban_*` tools, which is what this stage did.

### 11.3 The driver's stage-config parse fails under a worker shell (measured A/B)

```
$ DRY_RUN=1 bash scripts/automation/pipeline-driver.sh --board music          # default PATH
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
ModuleNotFoundError: No module named 'yaml'
exit=2
→ performance/pipeline-driver.log: 2026-10-16T13:28:18 ERROR: failed to parse stage config
                                     /home/j_kro/ai-content-pipeline/music/stages.yaml

$ PATH=/usr/bin:$PATH bash scripts/automation/pipeline-driver.sh --board music  # /usr/bin first
exit=0
→ performance/pipeline-driver.log: 2026-10-16T13:28:19 pipeline driver run start (board music)
                                     2026-10-16T13:28:19 pipeline driver run complete (board music, dispatched 0, running 0/1)
```

The config file is fine — `yaml.safe_load` under `/usr/bin/python3` gives 14 stages,
`default_stage: brief`. The driver's YAML parse runs as `python3 - … <<PYEOF` and `python3`
on a Hermes worker's PATH is the bundled 3.14.7 with no PyYAML (§1). So the driver cannot
even route when a bot runs it, and the correct-tree log line
`2026-10-16T13:04:26 ERROR: failed to parse stage config …` is this, not a YAML error.
Under the systemd user environment the mise shim's python3 (3.14.8) *does* have PyYAML, so
the same script parses there — the failure is specific to worker shells. Fix: call
`/usr/bin/python3` explicitly in the driver (one line), or install PyYAML for the bundled
interpreter.

### 11.4 The same filename is two different programs, and one drops the tempo

| Path | Bytes | md5 | What it is |
|---|---|---|---|
| chart payload `files/music/scripts/acestep_plan.py` (= the live ConfigMap) | 9 027 | `d18f779a` | the sunolocal **API client** — sends no bpm, `style_weight: None` |
| repo `music/scripts/acestep_plan.py` | — | `068c80fa` | the **direct renderer** — passes `bpm` straight to ComfyUI |
| pod `/opt/sunolocal/music/scripts/acestep_plan_direct.py` | 9 190 | `2b66e525` | byte-identical to both chart copies of the direct renderer |

The repo and the deployment disagree about what `acestep_plan.py` *is*. A worker who reads
the repo copy will conclude the tempo is honored and be wrong about the live rail; a worker
who copies the repo file into the payload would bypass sunolocal entirely. There is also
planner drift on the same pattern: the live payload planner (759 lines, `47839397`) is not
the repo's (545 lines, `e2cb6eea`) — the repo still carries the flat
`"bpm": ctx["blueprint"].get("bpm_anchor") or 100` fallback at line 470 whose jungle-at-100
outcome the live version's docstring records as the fixed incident.

### 11.5 Cosmetic: the repo's planner/registry drift is not visible from the card

The card's lane set, cadence and video shape are all reproducible from the registry, but the
*engine* the generate stage will actually reach is defined in a different repository
(`/home/j_kro/mining-k8s`). Nothing in `music/` points at it except prose comments. A stage
prompt that says "render via sunolocal" and a stage prompt that says "render via ComfyUI" are
describing the same chain from two ends, which is why §6.2 spells the whole chain out.

### 11.6 Two cards for one genre

```
$ sqlite3 -readonly ~/.hermes/kanban/boards/music/kanban.db \
    "select id,title,status from tasks where title like '%jungle%';"
t_006db63d|music-oracle: jungle-dnb (score 7.0)|running
t_f8b2fa7f|music-oracle: jungle-dnb (score 7.2)|ready
```

`ade6e87` added the open-card guard, so no new duplicates are created; these two predate it
(2026-10-09 03:27 and 03:37). Both resolve to this one genre-keyed brief. Already enumerated
in t_19d0714b Decision 5, which lists 10 genres carrying two open cards each. Working both
would render the same track twice.

---

## 12. Handoffs

**Already on the board — cited, not duplicated:**

| Card | Assignee | Why it matters here |
|---|---|---|
| t_41f354be | nexus-core | the live driver runs the wrong checkout (§11.1) |
| t_8a715681 | nexus-core | diverged checkout hides `music/suno-gen.py`; Rail B unreachable (§6.1) |
| t_25a6499c | nexus-core | engine's bpm/style path (the family §6.3 belongs to) |
| t_5a93164a | nexus-core | `advance-stage.sh` is a silent no-op in workers (§11.2) |
| t_bc6a0c00 | nexus-core | the draft-lyric guard passes parenthetical direction lines (§6.4) |
| t_19d0714b | ops | dispatcher ownership + the duplicate-card decision (§11.6) |
| t_b0a4db92 | coo | `brain/playbooks/music-lane-architecture.md` is cited by 10+ files and does not exist — every `§` reference in this lane is uncheckable, including §2/§3/§5/§11.2 quoted in `lanes.yaml`, `autonomy.yaml` and `gates/README.md` |
| t_9546841b | music-producer | `gate_loudness` ruler (volumedetect RMS vs ebur128 LUFS) |

**New, created by this brief (one card, because the genre needs a queue entry no existing
card covers):** nexus-core — *queue the jungle-dnb brief into the generation path*, carrying
the four generate-stage preconditions from §10 and the §6.3 A/B test as its acceptance.

**Open item for j_kro (creative direction, not this lane's call):** the brief queue entry
needs a `title`, and this genre has no blueprint supplying `title_candidates`. Nothing in
this brief invents one.

---

## 13. Provenance

- Registry: `music/genres.yaml` (lines 19–25 defaults, 47–54 this genre), `music/lanes.yaml`,
  `music/autonomy.yaml` — validated live (`registry OK: 14 genres, 10 lanes`)
- Rubric: `music/rubrics/edm.json` read in full; anchors quote EDMProd, Veena Studio,
  Transmission Samples (URLs in its `sources`)
- Template: `music/prompts/jungle-dnb.md` read in full; style-field length measured (653)
- Oracle: `music/oracle.py` — weights, `REVENUE_BANDS`, `BANNED_SURFACES`, `OPEN_STATUSES`;
  this card's components recomputed live (6.5 today vs 7.0 at emit)
- Board: `~/.hermes/kanban/boards/music/kanban.db` (read-only SQL) — tasks, comments
- Schedulers: `systemctl --user` units, timers, `performance/pipeline-driver.log` in both
  trees, `DRY_RUN=1` A/B run at 13:28
- Cluster: `kubectl -n mining` — CronJobs `music-pipeline` (17 */6 * * *),
  `music-pipeline-render` (41 */4 * * *); Deployment `sunolocal-source` (2d14h);
  ConfigMaps `music-pipeline-payload` (21 keys, md5-compared to the repo),
  `music-pipeline-briefs`; plans on nexus at `/var/lib/music-plans/`
- Engine: ComfyUI `GET /object_info` + `/queue` at `http://localhost:32188` (200);
  sunolocal `/health` → `{"status":"ok"}`; `jobs.sqlite3` and the artifacts copied out of the
  pod and measured with `music/rubrics/measure.py` under the numpy-bearing interpreter
- Gates: `gate_quota` executed (PASS); `gate_youtube_authentic` executed on both visuals
  (FAIL, 2 and 4 signatures); `gate_lyrics_original`, `gate_stems_present`, `gate_loudness`,
  `gate_quality`, `gate_sync_ready`, `gate_release_ready` help-read
- Media: ffprobe/ffmpeg 9.0.1 (`/home/j_kro/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin`)
- Resources before the read-heavy probes (standing rule): VRAM 885/8 192 MiB used, RAM
  available 17 GiB — no render was launched, no GPU window consumed
- **Still dangling:** `brain/playbooks/music-lane-architecture.md` does not exist in this
  repo (t_b0a4db92), so section numbers quoted from it elsewhere in this lane cannot be
  verified.
