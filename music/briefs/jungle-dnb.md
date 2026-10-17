# Brief — jungle-dnb

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`)
> **Card:** t_006db63d (`music-oracle: jungle-dnb (score 7.0)`)
> **Duplicate card:** t_f8b2fa7f (`music-oracle: jungle-dnb (score 7.2)`) — same genre,
> same lanes, emitted 10 minutes after this one on an earlier oracle run. Both resolve to
> THIS brief; the brief is keyed by genre, not by card. Close one, do not work both.
> **Written:** 2026-10-16 (CDT), profile `music-producer`, run 83
> **Verified (duplicate-card pass, `t_f8b2fa7f`):** 2026-10-16T14:15-05:00 (CDT) — see §14.
> The twin card met this file instead of writing a second brief: every checkable figure was
> re-measured live, and every claim that no longer held was corrected in place (§1.2's
> recomputed total and its decay forecast, §6.1's CronJob schedule and clone divergence, §6.3's
> three quoted code blocks, §11.1's driver log, §13's RAM figure, the `genres.yaml`
> default-block range in §1 and §13, and the board snapshot in §11.6). The operator's oracle
> re-score ruling (true score **6.5**, not this title's 7.2) is recorded at §14. Two cards were
> created where no owner existed — one of them superseded inside the same pass by an in-flight
> fix (§12).
> **Superseded revision of this file (before that pass):**
> `sha256 675813e634f36c882b1f846b71a1995cc096f70471557ab96dde3bad5e23045c` (836 lines).
> **Repo, re-measured at that pass:** `main` @ `456d525`, **30 ahead / 15 behind** `origin/main`
> — the 15-commit upstream deficit has not moved all day; the local tip moves every few minutes.
> **This card (`t_f8b2fa7f`, 7.2) is the twin.** Both cards' component vectors were re-read off
> the board: identical except `trend_signal` — 5.0 here, 3.0 on `t_006db63d`. That 0.2 gap is
> the oracle's network-failure fallback (§1.2), not market heat.
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `0e4fe5b` (main; the working tree moved twice
> while this brief was being written — sibling cards are committing to the same clone).
> NOT `~/Projects/ai-content-pipeline`, which has no `music/` tree at all (§11.1).
> **Oracle score:** the surviving card `t_006db63d` emitted **7.0/10** on 2026-10-09 (quota
> headroom 10.0, lane coverage 6.0, revenue 5.5, cadence fit 6.7, policy risk 9.0, trend signal
> 3.0); this card's title says 7.2 (identical vector except `trend_signal` 5.0). **True score
> 6.5/10** — re-scored live on 2026-10-16 against the current registry, quota ledger and
> calendar at `music/oracle.py` @ `b2d11f7`: `cadence_fit` decayed 6.7 → 3.33 (days left in the
> period, which ends 2026-10-31) and `trend_signal` is 3.0 again now that a failed fetch no
> longer earns the 5.0 premium. Threshold 5.0 → produce: the number moved, the routing verdict
> did not. Both live components and the floor the total flattens at are in §1.2; the oracle
> ruling and the re-scored digest are in §14.
> **Verified (citation sweep, `t_e86c2110`):** 2026-10-16T16:12-05:00 (CDT) — see §17. The
> `genres.yaml` defaults-range class this file's §14 regression exists to catch is now GREEN
> repo-wide: `check_brief_line_refs.py` → PASS, 118 cited ranges across 14 briefs, rc=0, and
> `--selftest` PASS. The two sites §14 left open were fixed by their own genres' cards before
> this card was claimed; this pass verified the landing, re-measured the sweep, and corrected the
> three §14 claims that still described it as open.
> **Superseded revision of this file (before that pass):**
> `sha256 5b3914191c5108814cccaaaa2c51f8a5b5eff1efc17455f7ddc4c173dac486ea` (1168 lines / 76 392 B).
> **Superseded revision of this file (before the absence-claim pass, `t_bdb94fb7`, 2026-10-16):**
> `sha256 dbec2ef82dee346e751ff0cc1f95fab2dec2e77b682d657bc2c0d00fadb1bc82` (1375 lines / 94 569 B).
> §19 records the one line corrected.

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
| Lyric blueprint | `music/lyrics/blueprints/jungle-dnb.yaml` — **added 2026-10-16 by card `t_e6d422ec`** (§16). 7 of the 14 genres have one (activist, anime-ending, anime-opening, chill-lounge, epic-orchestral-boss, jungle-dnb, trance); it was 4 at the §14 pass, when `anime-ending.yaml` landed |
| Registry note | `"Same Beatport ban applies. Amen-break / ragga vocal direction."` |

Registry `defaults:` that bind every track (`music/genres.yaml` lines 20–25; line 19 is blank,
and this range was cited as 19–25 before the §14 pass):
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
| Trend Signal | 0.10 | 3.0 | **3.0** (post-`b2d11f7`; 5.0 while the old fallback stood) |
| **Total** | | **7.0** | **6.5** |

Each number reproduces from `music/oracle.py`:

- `quota_headroom` = 10 × (1 − 0/58) = 10.0
- `lane_coverage` = 3 viable lanes × 2 = 6.0
- `revenue_potential` = (youtube 500 + distributor 200 + own-site 400) / 200 = 5.5
- `policy_risk` = 10 − 1 (a `youtube-mix` lane) = 9.0
- `trend_signal` = **3.0, live** — re-measured on 2026-10-16 14:26 CDT at `b2d11f7`:

  ```
  $ /usr/bin/python3 probe_oracle3.py
    warn: trend fetch failed for jungle-dnb (URLError(TimeoutError('timed out'))); scoring it
    as no signal (3.0)
  {"trend_signal": 3.0, "cadence_fit": 3.3333, "quota_headroom": 10.0, "lane_coverage": 6,
   "revenue_potential": 5.5, "policy_risk": 9.0, "total": 6.5}
  ```

  **The fetch still fails; the score no longer rises for it.** `oracle.py` @ `456d525` (the
  revision this pass started against) returned **5.0 on any exception** — 0.2 ABOVE the
  successful-but-empty reading of 3.0, so a broken probe earned the genre a *premium*. That
  premium is the whole of this card's 7.2 title against its **6.5** true score, and the same
  pattern sits behind the `elemental-fire` pair (7.5 vs 7.7). It was fixed at `b2d11f7`
  (card `t_bf0e5edd`, ~14:17 today): the exception branch now returns
  `TREND_NO_SIGNAL = 3.0` and warns on stderr. A card this pass raised for the same defect
  before finding that fix in the same working tree, `t_eb648761`, is superseded by it and
  should be closed.

  Consequence for reading this brief: while the pre-fix fallback stood, this pass's own
  recompute read **6.70**; the authoritative value is **6.5**, which is what the oracle
  ruling re-scored (§14). Never read a trend component of 5.0 as market heat; it is a failed
  measurement.
- `cadence_fit` = f(days left in period). 2/wk with 21 days left → 6.67 on 2026-10-09;
  2/wk with 14 days left → 3.33 today (live `cadence_fit_score("2/wk")` = 3.3333).

**Consequence for the board — corrected at the §14 pass.** Every oracle card's score decays
with the calendar until `cadence_fit` hits its floor. `music/oracle.py:250–251` (unchanged at
`b2d11f7`) returns **0.0** once `expected_tracks < 2`, i.e. once `days_left < 7` (2026-10-24
and later), and `weeks_remaining` never goes below 0.5. The other components are
calendar-independent, so with `trend_signal` back at its no-signal value this genre's total
flattens at **6.00** and does **not** fall to 5.4 by 2026-10-26: it cannot cross the 5.0
threshold inside the 2026-10 period at all. Measured across the curve (`probe_decay2.py`, the
source's arithmetic verbatim; the right-hand column is the pre-`b2d11f7` failed-fetch premium,
kept to show what the fix removed):

| Days left | `expected_tracks` | `cadence_fit` | Total (trend 3.0 / 5.0) |
|---|---|---|---|
| 21 (2026-10-09) | 6.00 | 6.67 | 7.00 / 7.20 |
| 14 (today) | 4.00 | 3.33 | **6.50** / 6.70 |
| 8 | 2.29 | 0.48 | 6.07 / 6.27 |
| 7 → 0 (2026-10-24 → 10-31) | 2.00 → 1.00 | **0.00** | 6.00 / 6.20 |

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

1. This genre **had no blueprint until 2026-10-16**, when card `t_e6d422ec` added
   `music/lyrics/blueprints/jungle-dnb.yaml` (§16). So this counterexample is now history rather
   than a live gap: before it, `lyrics.py scaffold --genre jungle-dnb` refused outright (rc=2,
   "no lyric blueprint"), `planner.py`'s `load_blueprint()` returned `{}`, and `bpm_anchor_for()`
   fell through to the caption — which works (§6.3), but the `theme` and `title_candidates` a
   blueprint supplies were absent. `anime-ending.yaml` landed at 14:03 the same afternoon
   (commit `1356e28`).
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
| A — `sunolocal` (in-cluster, CPU-plan + GPU render via ComfyUI on zephyr) | `music-pipeline` CronJob (17 */6 * * * → planner) → `music-pipeline-render` CronJob (41 */4 * * *) → `/payload/music/scripts/acestep_plan.py` → `sunolocal.mining.svc.cluster.local:8123` | **YES.** Service answers `{"status":"ok"}`. |
| B — Suno CDP (Premier session, `music/suno-gen.py`) | `music/suno-gen.py` | **Rail reachable now.** The file was missing when this table was first measured and is in this tree (42 652 B, mtime 14:23 — card `t_8a715681` reconciled). Rail A is still the rail the CronJobs run. |

```
$ cd /home/j_kro/ai-content-pipeline && git status -sb | head -1
## main...origin/main [ahead 30, behind 15]      # re-measured at the §14 pass; was ahead 19
```

The clone is ahead of its own origin by a count that moves every few minutes (sibling briefs
commit to this one tree — 19 at write time, **30** at the §14 pass) and **15 behind** until the reconciliation merge `ab33ad1` (14:23), after which the pair reads 0 behind / 61 ahead at `e40c7f9` (15:31)
(`origin/main` carries the missing `suno-gen.py`; card t_8a715681 tracks the reconciliation;
that deficit has not moved all day). Until it lands, the only rail a queued jungle-dnb brief
can use is Rail A. A generate stage that plans around Suno CDP has planned around a file that
is not there.

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

The planner resolves this genre's tempo correctly. The live payload planner
(`music__planner__planner.py` — the deployed copy. Measured 2026-10-16 17:31:54 CDT: 1157 lines,
md5 `a1dd2b33727f8c607541b47d2e0491e5`, against this repo's `music/planner/planner.py` at 1371
lines and md5 `1cb05ecd…`. The two were byte-identical earlier the same hour; the repo has grown
since, so the payload LAGS the repo rather than being a different program. The fence below is the
deployed copy's own text):

```python
def bpm_in_caption(caption: str):
    """The BPM the genre's own caption states, e.g. "ragga jungle, 168 BPM".

    Every template in music/prompts/ states one. It is the researched tempo for
    the genre and the only tempo signal available for the 11 genres that have no
    blueprint yet - without it the draft path fell back to a flat 100, which is
    right for almost nothing: jungle-dnb came out at 100 against its own stated
    168, and anime-opening at 100 against its stated 160.
    """
    m = re.search(r"(\d{2,3})\s*BPM", caption or "", re.I)
    return int(m.group(1)) if m else None
```

**That fence is a superseded revision, and it is the DEPLOYED copy's own wording.** Its two census
figures are `3 of 15 genres` and `11` genres with no blueprint, and the payload carried both
at the 2026-10-16 17:31:54 CDT read above — that reading is the one this sentence records, and it
is now itself superseded. Card `t_a54fb00d` corrected the repo's copy in the same
commit that wrote this note — `load_blueprint` now reads `(7 of 14 genres do)` and `bpm_in_caption`
`the 7 genres that have no blueprint yet` — against a live census of **14** registered genres and
**7** files in `music/lyrics/blueprints/`. The payload picked the correction up at the next
`sync-payload.sh`: re-read at 2026-10-16 18:55 CDT, the deployed `planner.py` (key
`music__planner__planner.py`) reads `(7 of 14 genres do)` at line 329, so the two copies agree and
this note's fence is a historical artifact only.

The jungle caption opens `ragga jungle, 168 BPM, chopped and resequenced Amen break …`, so
`template_bpm = 168`, and with no blueprint present `bpm_anchor_for()` returns **168**. The
plan says 168. That is the last point in the chain where anyone sees 168.

The payload's API client then throws it away — verbatim, the deployed
`music__scripts__acestep_plan.py` lines 79–100 (md5 `d18f779a`, §11.4):

```python
def build_suno_request(plan: dict) -> dict:
    """Map plan fields to SunoGenerateRequest JSON."""
    # Required fields: prompt (caption), lyrics, title, duration.
    # Optional: we set defaults for others.
    return {
        "prompt": plan.get("caption", ""),
        "lyrics": plan.get("lyrics", ""),
        "title": plan.get("title", ""),
        "instrumental": False,  # we assume lyrics present; if empty and allow-empty, still instrumental?
        "model": "v6",
        "custom_mode": False,
        "negative_tags": None,
        "vocal_gender": None,
        "duration": int(plan.get("duration", 180)),
        "style_weight": None,
        "weirdness_constraint": None,
        "audio_weight": None,
        "variety": None,
        "callback_url": None,
        "seed": None,  # we will pass seed separately if needed
        "engine": os.environ.get("SUNOLOCAL_ENGINE", "ace"),
    }
```

Read the fields it does NOT carry: no `bpm`, no `key`, no `style`, and `style_weight` is
hardcoded `None`. The plan's tempo, key and style have no wire field to travel in.

There is no `bpm` field to send (the wire model `SunoGenerateRequest` has none) and
`style_weight` is hardcoded `None`. So `translate.py` takes its default branch — verbatim,
`/opt/sunolocal/music/sunolocal/translate.py` lines 41–49, read inside the running pod
`sunolocal-source-65fcc845d-fd5r6`:

```python
    # BPM: default 120; could derive from style_weight or variety
    bpm = 120
    if req.style_weight is not None:
        # map 0-1 to 60-180
        bpm = int(60 + req.style_weight * 120)
    # Clamp BPM to reasonable range
    bpm = max(30, min(240, bpm))
    # Key: default C major; we could leave empty
    key = req.style or "C major"
```

and lines 55–56 of the same file hand both straight into the ACE plan: `"bpm": bpm,` and
`"key": key,`.

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
| Lyric blueprint | `music/lyrics/blueprints/jungle-dnb.yaml` | **added 2026-10-16** by card `t_e6d422ec` (§16) — 7 331 B, the 12 schema keys, `title_candidates[0]` `Two Speeds`; 7 of the 14 genres have one (4 at the §14 re-read) |
| Lyrics/track dir | — | none (`music/lyrics/` has activist, anime-opening, chill-lounge, trance only) |
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
  2. **Run the A/B test first** (§6.3): one render at `style_weight = 0.9`, one with the field
     left unset, both measured with `music/rubrics/measure.py`. Until that is done, nobody
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
(`.../performance/pipeline-driver.log`, 1 565 253 B, last written 13:50 today — 1 564 983 B /
13:19 at write time) runs every 30 minutes and never names a board:

```
2026-10-16T13:50:37-05:00 pipeline driver run start
2026-10-16T13:50:40-05:00 pipeline driver run complete (dispatched 0, running 0/1)
```

(re-measured at the §14 pass; the same two lines with 13:19 timestamps are what the brief
recorded at write time. The log grows ~270 B every 30 minutes and has still never named a
board.)

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
who copies the repo file into the payload would bypass sunolocal entirely. The PLANNER does not
show that drift at the 2026-10-16 17:31:54 CDT read: the payload's `music__planner__planner.py` is
1157 lines at md5 `a1dd2b33727f8c607541b47d2e0491e5`, this repo's `music/planner/planner.py` is
1371 lines at md5 `1cb05ecd…`, and the two were byte-identical earlier the same hour — the payload
LAGS the repo, it is not a different program (§16 records the correction; the `759 lines /
47839397` vs `545 lines / e2cb6eea` pair written here does not reproduce). The flat fallback the
repo carries is `"bpm": args.bpm or bpm_anchor_for(ctx) or 100`, at `planner.py:1159` and `:1181`
— `:470` is inside `load_element_index`, not the draft path.

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
t_006db63d|music-oracle: jungle-dnb (score 7.0)|running     # write time; §14 re-read: done 13:31
t_f8b2fa7f|music-oracle: jungle-dnb (score 7.2)|ready       # write time; §14 re-read: running
```

`ade6e87` added the open-card guard, so no new duplicates are created; these two predate it
(2026-10-09 03:27:53 and 03:37:53 CDT — 600 s apart, re-read from the board's `created_at`).
Both resolve to this one genre-keyed brief. Already enumerated in t_19d0714b Decision 5, which
lists 10 genres carrying two open cards each. Working both would render the same track twice.

**Re-read at the §14 pass — the pair is resolved, and a third card now carries the handoff:**

```
t_006db63d|done|music-producer|created 2026-10-09 03:27:53|done 13:31:08
t_f8b2fa7f|running|music-producer|created 2026-10-09 03:37:53|started 13:52:32   <- this card
t_97c92df2|ready|nexus-core|created 13:30:42                                      <- §12 handoff
```

The twin (`t_f8b2fa7f`) met this file rather than writing a second one, so nothing is left
open for this genre at the brief stage.

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
| t_b0a4db92 | coo | `brain/playbooks/music-lane-architecture.md` is cited by 10+ files and was reported absent, which left every `§` reference in this lane uncheckable, including §2/§3/§5/§11.2 quoted in `lanes.yaml`, `autonomy.yaml` and `gates/README.md` — **RESOLVED**: the doc is in `HEAD` (rewritten `7411afa`, head touching it `6b24a52`) and `music/scripts/check_doc_refs.py` PASSes |
| t_9546841b | music-producer | `gate_loudness` ruler (volumedetect RMS vs ebur128 LUFS) |

**New, created by this brief (one card, because the genre needs a queue entry no existing
card covers):** nexus-core — *queue the jungle-dnb brief into the generation path*, carrying
the four generate-stage preconditions from §10 and the §6.3 A/B test as its acceptance.
→ `t_97c92df2`, `ready`, nexus-core, created 13:30:42 — verified on the board at the §14 pass.

**New, created by the §14 verification pass — two cards, each for a defect no existing card
covers:**

| Card | Assignee | Defect |
|---|---|---|
| `t_eb648761` | oracle | `trend_signal`'s fallback scores a **failed** fetch (5.0) above a measured-null scrape (3.0) — the whole of this genre's 7.2-vs-7.0 spread (§1.2). **Superseded before dispatch:** the card that owns this defect, `t_bf0e5edd`, had an uncommitted fix in the same working tree by 14:25 (`TREND_NO_SIGNAL = 3.0` + `music/scripts/check_oracle_determinism.py`), so this card should be closed as a duplicate, not worked. |
| `t_e86c2110` | music-producer | `anime-opening` and `chiptune-8bit` cited the `genres.yaml` **defaults block as 19–25** when it is **20–25** (line 19 is blank). `music/scripts/check_brief_line_refs.py`, added by the §14 pass, is the regression and FAILed on exactly those two sites at that reading. **Landed before this card was claimed:** `t_58072b6c` fixed `anime-opening.md` at 16:08:03 (commit `80b25a1`) and `t_60767fb1` fixed `chiptune-8bit.md` at 16:08:47 (`41b7b1e`); the sweep card verified the landing — PASS, 118 ranges, rc=0 (§17). |

**Open item for j_kro (creative direction, not this lane's call):** the brief queue entry
needs a `title`. `music/lyrics/blueprints/jungle-dnb.yaml` (card `t_e6d422ec`, §16) now supplies
three candidates — `Two Speeds`, `Slow Grid Toast`, `Wheel It Forward` — and `[0]` is also the
track-dir slug `music/lyrics/jungle-dnb/two-speeds` that `lyrics.py scaffold` derives. This brief
still does not decide: j_kro owns the release title.

---

## 13. Provenance

- Registry: `music/genres.yaml` (lines 20–25 defaults, 47–54 this genre), `music/lanes.yaml`,
  `music/autonomy.yaml` — validated live (`registry OK: 14 genres, 10 lanes`)
- Rubric: `music/rubrics/edm.json` read in full; anchors quote EDMProd, Veena Studio,
  Transmission Samples (URLs in its `sources`)
- Template: `music/prompts/jungle-dnb.md` read in full; style-field length measured (653)
- Oracle: `music/oracle.py` — weights, `REVENUE_BANDS`, `BANNED_SURFACES`, `OPEN_STATUSES`;
  this card's components recomputed live (**6.7** today with the trend fetch failing, 6.5 when
  it succeeds with 0 snippets; 7.0 at emit — §1.2)
- Board: `~/.hermes/kanban/boards/music/kanban.db` (read-only SQL) — tasks, comments
- Schedulers: `systemctl --user` units, timers, `performance/pipeline-driver.log` in both
  trees, `DRY_RUN=1` A/B run at 13:28
- Cluster: `kubectl -n mining` — CronJobs `music-pipeline` (17 */6 * * *),
  `music-pipeline-render` (41 */4 * * *); Deployment `sunolocal-source` (2d15h at the §14
  re-read); ConfigMaps `music-pipeline-payload` (21 keys, md5-compared to the repo),
  `music-pipeline-briefs`; plans on nexus at `/var/lib/music-plans/`
- Engine: ComfyUI `GET /object_info` + `/queue` at `http://localhost:32188` (200); sunolocal
  `/health` → `{"status":"ok"}` (both re-probed at the §14 pass, all four node schemas
  re-read); `jobs.sqlite3` and the artifacts copied out of the pod and measured with
  `music/rubrics/measure.py` under the numpy-bearing interpreter
- Gates: `gate_quota` executed (PASS); `gate_youtube_authentic` executed on both visuals
  (FAIL, 2 and 4 signatures — both re-executed at the §14 pass with identical output);
  `gate_lyrics_original`, `gate_stems_present`, `gate_loudness`, `gate_quality`,
  `gate_sync_ready`, `gate_release_ready` help-read
- Media: ffprobe/ffmpeg 9.0.1 (`/home/j_kro/.hermes/tools/ffmpeg-9.0.1-linux-x64/bin`)
- Resources before the read-heavy probes (standing rule): VRAM 885/8 192 MiB used, RAM
  available 17 GiB at write time (16 GiB at the §14 re-read) — no render was launched, no GPU
  window consumed
- Standing checks at the §14 pass: `check_brief_figures.py` (5 figures recomputed for this
  brief, 0 failed), `check_brief_line_refs.py` (new, this card), `check_brief_drift.py` (the
  live-count check; it caught the blueprint census moving 3 → 4 mid-pass, clean after the §14
  update), `check_brief_bpm_solutions.py` (the 0.9 → 168 claim), `check_brief_paths.py`,
  `check_prompt_style_counts.py`, `check_stage_scripts.py` (FAILs only on `music/suno-gen.py`,
  the divergence t_8a715681 owns — not this brief) — the jungle-dnb brief is clean in all of them
- **Dangling reference — RESOLVED (`t_b0a4db92`, done).** `brain/playbooks/music-lane-architecture.md`
  is in this repo and in `HEAD` (rewritten at `7411afa`, head touching it `6b24a52`),
  so the section numbers quoted from it elsewhere in this lane **are** verifiable:
  `music/scripts/check_doc_refs.py` → `OK: every section reference resolves to a heading in the
  doc`. The doc's §2 genre registry carries this genre's row, and its §14 citation map lists the
  files that read it.

---

## 14. Duplicate-card verification pass — `t_f8b2fa7f`, 2026-10-16T14:15 CDT

This card is the twin of `t_006db63d`: same genre, same lanes, same cadence, emitted 600 s
later by the pre-`ade6e87` second oracle wave. The two cards' component vectors are identical
except `trend_signal` (5.0 here vs 3.0 there) — the 0.2 spread is `oracle.py`'s fetch-failure
fallback, not market heat (§1.2). The brief is keyed by **genre**, so both cards resolve to
this file: the twin owes a verification pass, not a second brief. No second brief was written,
no stage chain was started, and no registry value, gate, plan, blueprint, chart file, cluster
object or campaign artifact was modified.

### Every checkable figure re-measured, live

| Section | Claim | Re-measured 2026-10-16 (14:00–14:15 CDT) | Verdict |
|---|---|---|---|
| §1 | `registry OK: 14 genres, 10 lanes`; quota `0/60` | `/usr/bin/python3 music/registry.py validate` → rc=0, identical lines; `gate_quota` → PASS 0/60, 0 studio exports | ok |
| §1 | template 4 032 B, style field 653/1000, 347 chars headroom | `wc -c` 4032; fenced block 653 chars / 653 bytes (pure ASCII — both counting conventions agree); 1000−653 = 347 | ok |
| §1 | visual style doc 1 157 bytes | `wc -c` 1157 **bytes** / 1151 characters — the unit label is right this time | ok |
| §1 | this genre's block is `genres.yaml` lines 47–54 | line 47 is `  jungle-dnb:`, line 54 is the `notes:` line — exact | ok |
| §1 | the `defaults:` block is lines **19–25** | the block is lines **20–25**; line 19 is blank | **corrected** |
| §1 | deployed template + registry md5s match the repo | `kubectl` payload md5 `c91b4d0e0f53d3abf9c17dc501801088` (template) and `3386db64eb5780da5988cdb5a37f8f03` (registry) — both identical to the worktree files | ok |
| §1.1 | rubric `edm.json`: 6 criteria, weights 3/3/2/2/1/1, threshold 7.0, `genres: [trance, jungle-dnb]` | every value exact | ok |
| §1.2 | components 10 / 6 / 5.5 / 6.7 / 9 / 3 → 7.0; recomputed **6.5** | live `score_genre("jungle-dnb")` (registry loader, live quota) → `trend_signal` **3.0**, `cadence_fit` **3.3333**, **total 6.5** at `b2d11f7`; it read 6.70 between this pass's start and `b2d11f7`, while the pre-fix fallback returned 5.0 | **6.5 (re-scored)** |
| §1.2 | "will be 5.4 on 2026-10-26 … ages out of its own justification" | `cadence_fit` returns 0.0 once `expected_tracks < 2` (`days_left < 7`), and `weeks_remaining` floors at 0.5, so the total floors at **6.00 / 6.20** — it cannot cross 5.0 in this period | **corrected** |
| §2 | every quoted template string (168 BPM, two speeds, 40–60 Hz, 12-bit crunch, exclude list, weirdness 55% / style influence 80%, instrumental fallback) | all present in `music/prompts/jungle-dnb.md`, verbatim | ok |
| §2 | lyrics-guidance block is 473 chars | 474 chars raw, **473** under the lane's own `.strip()` rule (`music/prompts/validate_templates.py:67`, `extract_fenced_blocks` → `[m.strip() for m in re.findall(...)]`) — the same rule that gives 653 for the style field | ok |
| §4 | `lyrics.py scaffold` / `claim`; schema `music/track-lyrics-manifest v1`; the activist manifest quote; 4 of 14 blueprints at the §14 pass (was 3 — `anime-ending.yaml` landed 14:03, commit `1356e28`; 6 at the 2026-10-16 15:31 re-measure); `final-round.json` `authorship: AI-GENERATED` + `lyrics_mode: ai` | all read live and identical to the quoted text | **updated** |
| §5 | `gate_quota` PASS; 2/wk over 31 days ≈ 9 tracks; a 60-min mix is ≥6 renders | `gate_quota` PASS 0/60; 2 × 31/7 = 8.86; 3600 s ÷ 600 s = 6 | ok |
| §6.1 | CronJob schedules; `music/suno-gen.py` absent; plans dir; the live briefs queue; clone divergence | `music-pipeline` is `17 */6 * * *` — **five** fields, the brief had six; `music-pipeline-render` `41 */4 * * *` exact; `suno-gen.py` still absent from the worktree; `/var/lib/music-plans/` holds the same three plans; `briefs.json` still the single `smoke-chill-lounge` entry; divergence measured on 2026-10-16 14:05 CDT at `456d525`: **30 ahead / 15 behind** (the pair read 38/15 at 14:25 — the local tip is the moving part; it was 19/15 at write time) | **corrected (2)** |
| §6.2 | ComfyUI node schemas — `bpm` INT default 100 min 30 max 300, `duration` FLOAT default 160 max 600, `keyscale` default `B minor`, Loader default 4B, Artist `instrumental` BOOLEAN, empty queue, sunolocal `/health` ok | all re-read from `http://localhost:32188/object_info` and the service — identical | ok |
| §6.3 | the tempo is dropped: `translate.py:41–49` (`bpm = 120`, `int(60 + style_weight × 120)`, the clamp, `key = req.style or "C major"`), and the API client carries no bpm / key / style | read inside pod `sunolocal-source-65fcc845d-fd5r6`; line numbers exact. The three `python` blocks in §6.3 were **editorial paraphrases inside a fence** (invented inline comments, a merged key line); all three are now verbatim source with the read path named | **corrected** |
| §6.3 | `int(60 + 0.8 × 120)` = 156, four below the pocket floor; 0.9 → 168 | `check_brief_bpm_solutions.py` PASSes the 0.9 → 168 claim | ok |
| §6.3 | the smoke artifact: 30.0 s / 48 kHz / stereo / flac, mean −16.8, max 0.0, crest 17.1, bpm 76.0 (conf 0.24) with a 152.0 octave, silence 19.98→30.00 s, 1.69% energy >8 kHz, RMS spread 48.3 | copied `suno-260e4b344cef4b668c94d8871ad5723c.flac` out of the pod and re-ran `music/rubrics/measure.py`: every figure identical to the digit | ok |
| §6.3 | the stored request carries no `styleWeight` key; the store holds 6 jobs | `jobs.sqlite3` out of the pod: 6 rows, 0 requests contain `styleWeight`, and the chill job's `style_weight` is `null` | ok |
| §6.4 | `ace_comfy.py` passes `--allow-empty` unconditionally | pod source lines 62–71: `--seed`, `--allow-empty`, `--timeout` | ok |
| §7 | both visuals — bytes, duration, frames, resolution, and the gate verdicts (2 and 4 signatures) | ffprobe: 14 151 B / 5.000 s / 125 frames / 1280×720 and 42 857 593 B / 3600.000 s / 90 000 frames / 1280×720; `gate_youtube_authentic` FAILed on both, output word-for-word identical | ok |
| §11.1 | the driver unit walks the `Projects/` checkout, HEAD `9aa1a23`, driver 12 618 B dated Sep 3, log grows every 30 min without naming a board | all reproduced; the log is now 1 565 253 B, last written 13:50 | **corrected (log)** |
| §11.2 | `advance-stage.sh` ends in a fenced `hermes kanban` call | the script's tail is that call; from this worker `hermes kanban --board music list` → `kanban: delegate_task child contexts cannot mutate Kanban tasks or boards`, rc=1 | ok |
| §11.3 | driver A/B: default PATH → `ModuleNotFoundError: No module named 'yaml'`, exit 2; `/usr/bin` first → exit 0 | re-ran both; identical, and the correct tree's log carries the matching `ERROR: failed to parse stage config` line | ok |
| §11.4 | payload client 9 027 B md5 `d18f779a`; repo `acestep_plan.py` md5 `068c80fa`; pod direct renderer 9 190 B md5 `2b66e525`; live planner 759 lines `47839397` vs repo 545 lines `e2cb6eea` with the flat `or 100` at line 470 | every figure reproduced from the ConfigMap and the pod | ok |
| §11.6 | two cards `running` / `ready`, created 2026-10-09 03:27 and 03:37 | `created_at` → 03:27:53 and 03:37:53 (600 s apart); states now `done` 13:31:08 / `running` (this card), plus `t_97c92df2` | **refreshed** |
| §12 | every cited card exists with the stated assignee and status | all eight re-read as cited; `t_97c92df2` (the queue-entry handoff) is `ready`, `nexus-core` | ok |
| §13 | the payload ConfigMap carries 21 keys; VRAM/RAM at write time | 21 keys counted; VRAM 885/8 192 MiB unchanged; RAM available 16 GiB (was 17) | ok (RAM updated) |

### The corrections applied

| # | Section | Claimed at the brief stage | Measured at this pass |
|---|---|---|---|
| 1 | §1, §13 | the registry `defaults:` block was cited as `19–25` | lines **20–25**; line 19 is blank (see the regression below) |
| 2 | §1.2, header | recomputed total **6.5** with `trend_signal` 3.0 | This pass first measured **6.70**, because the DuckDuckGo fetch fails (`URLError: <urlopen error timed out>`) and the pre-`b2d11f7` fallback returned 5.0 for that. `b2d11f7` landed mid-pass (`t_bf0e5edd`) and removed the premium, so the authoritative value is back to **6.5** — the number the oracle ruling re-scored. Both readings are dated in §1.2 |
| 3 | §1.2 | "will be **5.4** on 2026-10-26 … any card not worked this month ages out of its own justification" | **6.00** — `cadence_fit` clamps at 0.0 for `days_left < 7`, so this genre cannot fall below 6.0 inside the 2026-10 period |
| 4 | §6.1 | `music-pipeline` CronJob schedule `17 */6 * * * *` | `17 */6 * * *` — five fields, per live `kubectl` output |
| 5 | §6.1 | clone divergence `ahead 19` | `ahead 30` (`behind 15` unchanged; the local tip moves every few minutes) |
| 6 | §6.3 | three `python` blocks carrying editorial annotation (`# <-- no bpm, no key, no style`; a comment re-inlined onto the code line; `"key": req.style or "C major",`) | replaced with the deployed source, verbatim, with line numbers and the read path named |
| 7 | §11.1 | driver log 1 564 983 B, last written 13:19 | 1 565 253 B, last written 13:50 |
| 8 | §11.6 | the two cards `running` / `ready` | `done` 13:31:08 / `running` (this card); `t_97c92df2` added |
| 9 | §13 | RAM available 17 GiB | 16 GiB (VRAM unchanged at 885/8 192 MiB) |
| 10 | §1, §4, §8 | **3** of 14 genres have a lyric blueprint (activist, chill-lounge, trance) | **4** of 14 at the §14 pass — `music/lyrics/blueprints/anime-ending.yaml` landed at 14:03 (commit `1356e28`) while that pass was running. Caught by the sibling `music/scripts/check_brief_drift.py` (`t_b7dd5655`), which recomputes this census live; **6** of 14 at the 2026-10-16 15:31 re-measure (card `t_0f7aed63`) |
| 11 | header, §1.2 | this card's title score **7.2** (and the twin's 7.0) | **6.5 true** — the operator's oracle ruling, re-scored at `b2d11f7`; the 0.7 delta is the failed-fetch premium (0.20, now fixed) plus `cadence_fit` decay (0.505). Recorded in full below |

Nothing else needed correcting. Both of the brief's counter-intuitive findings reproduced
exactly: the artifact's measured **76.0 BPM** (§6.3 — neither the 120 the chain carries nor the
75 its own caption states, which is why §6.3 still refuses to pick between "the caption steers
tempo" and "the estimate is unreliable here"), and **both visuals failing their own lane gate**
(§7).

### Regression check added (FAILURE → TEST)

The first correction is not a wrong number: it is a **range citation that opens on a blank
line** — the one citation class `check_brief_figures.py` cannot see, because a bare line number
carries no unit token. Nothing measured it, so the same one-line error sat in three briefs.
`music/briefs/anime-opening.md` shows why a hand fix does not hold: that genre's own
duplicate-card pass corrected the range to 20–25 inside its comparison table while the body
kept `19–25`.

`music/scripts/check_brief_line_refs.py` (new, this pass) reads every `music/briefs/**/*.md`
and measures each line citation — `<path>:A`, `<path>:A-B`, `<path> lines A–B`, and the
inherited `line A` / `, A–B` forms — against the referent file in the worktree. It FAILs when
a range or point lies outside the file, or opens or closes on a blank line. It **skips, never
guesses**, a referent it cannot resolve uniquely: this lane carries `gate_sync_ready.py` at
both `music/` and `music/gates/`, so a bare basename is a real ambiguity, and revision- or
pod-qualified paths are out of the worktree by construction. `--selftest` builds the incident
shape in a throwaway repo and asserts the FAIL, the PASS and the skip.

Repo-wide **at this pass's own reading (2026-10-16T14:15 CDT): 3 of 62 citations FAILed** —
`anime-opening.md:54` and `chiptune-8bit.md:51,541` (the same one-line error in two other
genres; 59 OK, 40 skipped as unresolvable, never guessed). Card `t_e86c2110` owns that sweep.
**The sweep is green (§17):** the two sites were fixed by their own genres' cards at 16:08 CDT
(commits `80b25a1`, `41b7b1e`), and `t_e86c2110` re-measured the check at 16:12 CDT → **PASS,
118 cited ranges across 14 briefs, rc=0**, `--selftest` PASS. The 62-citation census above is the
§14 reading and is left as a dated record, not restamped.

### Oracle ruling (operator note, 2026-10-16) — true score **6.5**

The oracle re-scored this genre against the live registry, quota ledger and calendar at
`music/oracle.py` @ `b2d11f7`, and ruled:

- **True score 6.5/10**, not the 7.2 in this card's title. The delta is two effects:
  `trend_signal` 5.0 → 3.0 (0.20 — the failed-fetch premium removed at `b2d11f7`) plus
  `cadence_fit` 6.67 → 3.33 (0.505 — days left in the current period). Measured independently
  at this pass: `score_genre("jungle-dnb")` → **6.5**, `trend_signal` 3.0.
- **Rule applied (scoring gate):** the NEWEST scoring run owns the genre, and the
  higher-scoring twin is never automatically right — the score is a function of live state plus
  a live web fetch, so an older number cannot be reproduced and cannot win a tie. All 14 genres
  stay above the 6.0 produce line (true scores 6.5–8.4), so the ruling corrects a number, not a
  routing verdict.
- **Superseded cards:** the twin `t_006db63d` (7.0) is closed `done`; the chain continues from
  this genre-keyed brief, not from a second brief.
- **Route:** the brief stage is already delivered — **do not re-run it**. The surviving chain
  resumes at the stage after `brief` (`genre-select`), which is what this card's stage marker
  now carries; `t_97c92df2` (`ready`, nexus-core) holds the generation-path queue entry.
- **Board invariant:** `music/scripts/check_oracle_board.py` — one open oracle card per genre.
  Re-run at this pass: `rc=0`, *"every one of the 14 open oracle genre(s) carries exactly one
  open card; every open title parses into a genre"*.

**Digest caution.** The ruling quoted this brief as 66 222 B /
`sha256 6da17333e6a04a40…`. That was a **mid-edit** state — this pass was still writing the
file. The artifact at the first §14 commit (`973a38c`) is **1 054 lines / 66 293 B /
`sha256 d6be6da5d1ad62d3d1f8a3a0e3527af35d575010bdef6121a76d535c17028a51`**, and this ruling
pass edits the file again. Re-measure before citing a digest (`sha256sum`, or
`git rev-parse HEAD:music/briefs/jungle-dnb.md` to name the committed blob): a digest is not
stable while a worker is editing, and the correct response to a moving digest is to measure it,
never to trust the last number seen.

### Not changed, not re-filed

No registry value, gate, plan, blueprint, chart file, cluster object or campaign artifact was
modified. One child card was created for a defect with no owner — `t_e86c2110` (the two stale
citations in `anime-opening` / `chiptune-8bit`; landed by those genres' cards and verified by the
sweep, §17). A second, `t_eb648761` (the trend fallback),
was created before this pass found that the card owning that defect, `t_bf0e5edd`, already had
an uncommitted fix for it in the same working tree at 14:25: **close `t_eb648761` as a
duplicate, do not work it.** Everything else this brief raises already has an owner in §12.

hotspot: `music/briefs/` — 14 briefs written and re-verified by ~8 concurrent `music-producer`
workers on one shared working tree. Every write needs a path-scoped `git add` and a lock retry;
this file now has two commits, both on this genre.

## 15. Aged live counts re-measured (card `t_0f7aed63`, 2026-10-16)

`music/scripts/check_brief_drift.py` (added by card `t_b7dd5655`) flagged this brief's blueprint
census as stale — it moved from 4 to 6 during the afternoon — and the same class of aged live
count sat in §1, §4, §6.1, §8 and §14. Re-measured and corrected in place.

- **Superseded revision of this file:** `sha256 52891a79d8dde47744a00dd2ba1e8ca595b205c7fdfe91b9b8ebc129828e1800` (1096 lines / 69660 B).
- **Blueprint census, re-measured 2026-10-16 15:31 CDT:** the census read six, listing
  `activist`, `anime-ending`, `anime-opening`, `chill-lounge`, `epic-orchestral-boss` and
  `trance`; `jungle-dnb` was then among the genres that had none, so §4's counterexample was live
  and only the count and the file list had moved. This bullet is the pass record and is not
  restamped: the live census, which moved when `music/lyrics/blueprints/jungle-dnb.yaml` landed,
  is stated in §16.
- **Clone divergence:** the pair this brief records holds at `456d525` (30 ahead / 15 behind). At
  `e40c7f9` (15:31) it reads 0 behind / 61 ahead: the reconciliation merge `ab33ad1` (14:23)
  cleared the 15-commit upstream deficit that had "not moved all day".
- **Corrected in place:** §1's table row, §4 counterexample 1, §6.1's divergence sentence, §8's
  asset table, §14's re-measured row and §14's correction 10.

---

## 16. The lyric blueprint landed (card `t_e6d422ec`, 2026-10-16)

`music/lyrics/blueprints/jungle-dnb.yaml` is in the tree. Card `t_e6d422ec` wrote it because the
queue entry for this genre could not land without it: the chart's `check-queue-sync.sh` FAILs any
`draft` entry whose genre has no blueprint in the payload (reproduced rc=1 without the file, rc=0
with it — card `t_97c92df2` §4), and the lane side failed the same way,
`lyrics.py scaffold --genre jungle-dnb` → **rc=2**, "FAIL: no lyric blueprint".

**The live blueprint census: 7 of the 14 genres carry a lyric blueprint** — `activist`,
`anime-ending`, `anime-opening`, `chill-lounge`, `epic-orchestral-boss`, `jungle-dnb`, `trance`;
the other 7 do not. Read live at this pass through the registry loader plus the
`music/lyrics/blueprints/*.yaml` glob, not transcribed.

What the file carries, and how each piece was checked:

| Field | Value | Evidence |
|---|---|---|
| `bpm_anchor` | **168** | the genre's caption states 168 and the queue entry pins `bpm: 168`; `planner.py show --genre jungle-dnb` prints `"bpm_anchor": 168` where it printed `null` before |
| `structure` | `Intro`, `Break`, `Hook`, `Break`, `Hook`, `Break`, `Outro` | the template's own tag sheet, verbatim and in order — compared programmatically against `planner.load_template("jungle-dnb")["structure"]`: identical, repeats included |
| `genre` / `family` | `jungle-dnb` / `edm` | `music/genres.yaml` lines 47–54 |
| `theme` / `voice_notes` | brief §2 Intent and §4 | transcription of the human-authored artifacts, not invention |
| `avoid` | the template's Exclude Styles plus the clinical-DnB drift | 3 quoted phrases, which `planner.validate()` enforces against a finished sheet |
| `title_candidates` | `Two Speeds`, `Slow Grid Toast`, `Wheel It Forward` | the field the queue entry was blocked on; §12 keeps the release title j_kro's call |
| `rhyme` / `line_length` / `mood_words` | this lane's craft call | brief §2's contract: ragga toast on the slow grid, 2-4 chantable lines, call-and-response |

Before and after, measured with the repo's own readers:

```
planner.py show --genre jungle-dnb    BEFORE  "structure_source": "template", "blueprint": false, "bpm_anchor": null
                                      AFTER   "structure_source": "blueprint", "blueprint": true,  "bpm_anchor": 168
lyrics.py scaffold --genre jungle-dnb BEFORE  rc=2  FAIL: no lyric blueprint for 'jungle-dnb'
                                      AFTER   rc=0  scaffolded music/lyrics/jungle-dnb/two-speeds
```

- **Superseded revision of this file:** `sha256 1f866e212992a6dc4485bf78f4b408a32b2d1d79e15a31396460817cba606c37` (1113 lines / 71235 B).
- **The scaffold is still refused, and no track dir was left behind.** `gate_lyrics_original --track-dir … --strict` FAILs the scaffolded sheet with 7 × "placeholder guidance left in" plus `authorship.status=incomplete`, so the draft guard is intact; the scaffold was written into a scratch copy of `music/`, not this worktree, so `music/lyrics/jungle-dnb/` is absent here.
- **Still owed, and not this card's step:** the chart payload copy. `music-pipeline-payload` does not carry `jungle-dnb.yaml` until card `t_97c92df2` runs `sync-payload.sh` under `/home/j_kro/mining-k8s/helm/charts/music-pipeline/` and commits that repo; `check-payload-sync.sh` holds the two copies identical.
- **Census consequence, corrected in the same commit:** the briefs that cited the census as six were restated as live claims — `activist.md` (§1 and its §13), `chiptune-8bit.md` (§13), `elemental-earth.md` (§15), `elemental-water.md` (§6.3 and §15) and this file (§1, §4, §8, §12, §15). `commentary-beds.md` was **not** touched: card `t_b976f49f` had that file modified and uncommitted while this pass ran, so its census bullet stays with that card.
- **Same class, filed as this card, and corrected by the next pass (the fence below is the BEFORE revision).** `music/planner/planner.py` and `music/tests/test_planner.py` still quote the blueprint census as it stood when they were written:

  ```text
  planner.py:297  (load_blueprint docstring)   "… when it exists (3 of 15 genres do)."
  planner.py      (bpm_in_caption docstring)   "the only tempo signal available for the 11 genres that have no blueprint yet"
  tests/test_planner.py:44  (comment)          "Only 3 of 14 genres have a blueprint, so 11 …"
  ```

  Each figure was accurate when written; each now reads 7 of 14. Filed as a follow-up card rather than edited inside this one.

- **Superseded by the next pass (card `t_a54fb00d`, 2026-10-16).** The three sites now read
  `7 of 14` and `7`: `planner.py:325` `(7 of 14 genres do)`, `planner.py:337` `the 7 genres that
  have no blueprint yet`, `tests/test_planner.py:62` `The 7 of 14 genres with no blueprint fell
  back`. The first two moved from `:297`/`:309` while this pass ran — other cards took
  `planner.py` from 1157 to 1371 lines — so those two citations are the 17:31 CDT reading, where
  the pass left them. Each figure in the fence above describes the revision that wrote it, and not
  one of the three matched live state at either reading:

  * `3 of 15 genres do` — the `3` was true from `3967dea` (2026-10-09 00:26, the commit that wrote
    it) until `8f0fd9a` added the 7th blueprint. The **`15` matches no tracked revision**:
    `music/genres.yaml` was untracked when the docstring was written, and every tracked reading
    from `b0d4007` (2026-10-09 03:24) gives **14** genres. A figure no revision carries is the one
    no check can recompute, which is why nothing flagged it.
  * `the 11 genres that have no blueprint yet` — true at `dda0d32` (2026-10-09 03:39), the commit
    that wrote it, against a 3-file `music/lyrics/blueprints/`: 14 − 3 = 11. The 2026-10-16 15:31
    CDT re-measure in §1 read 8, and the live count is 7 (`music/lyrics/blueprints/*.yaml`).
  * `Only 3 of 14 genres have a blueprint, so 11` — true at `dda0d32`. The test itself was never
    stale: it compares every genre's planned `bpm` against `bpm_anchor_for(ctx)`, so it read the
    7th blueprint correctly the moment it landed.
  * The class now has a check: `music/scripts/check_code_census.py`, which reads the lane's own
    comments and docstrings and recomputes this census. Measured on this pass: `--rev HEAD` (the
    pre-correction revision) FAILs rc=1 with exactly these three sites plus the one historical
    line in `check_brief_drift.py`'s own comments; the worktree PASSes rc=0 with 3 live claims
    across 113 `.py` files and no false positive; `--selftest` PASS, 16 census cases plus a
    prose-extraction case. The standing pass reads the WORKTREE, not a revision, since these
    files move under other cards.

---

## 17. Citation-sweep verification (card `t_e86c2110`, 2026-10-16T16:12 CDT)

§14 created `t_e86c2110` for the two sites its new regression left open, expecting the sweep card
to fix them. It did not have to: each genre's own card fixed its §1 citation first. So this pass
owes verification, not another edit — no second brief was written, and no registry value, gate,
plan, blueprint, chart file or cluster object was touched.

| # | §14 claim | Measured 2026-10-16 at 16:12 CDT | Verdict |
|---|---|---|---|
| 1 | `anime-opening` §1 cites the `genres.yaml` defaults block as 19–25 | line 73 of `music/briefs/anime-opening.md` reads **20–25** (commit `80b25a1`, 16:08:03). The 19–25 strings left further down (:74, :391, :496, :588) are that pass's own before/after records, not live citations | **landed** |
| 2 | `chiptune-8bit` §1 cites it as 19–25 | line 61 of `music/briefs/chiptune-8bit.md` reads **20–25** (commits `41b7b1e` 16:08:47, `472ad9f`); the 19–25 left at :798 is its corrected-claim row | **landed** |
| 3 | repo-wide "3 of 62 citations FAIL" | PASS at 16:12 CDT: **118 cited line range(s) across 14 brief(s), rc=0**, 53 skipped (ambiguous referent ×28, anchored to a rev/time ×12, not in the worktree ×13); **119 ranges at 16:20, still 0 failing** — siblings kept adding citations while this section was written | **green** |
| 4 | the two files on their own | `--briefs music/briefs/anime-opening.md` → PASS, 6 ranges, rc=0; `--briefs music/briefs/chiptune-8bit.md` → PASS, 12 ranges, rc=0 | ok |
| 5 | `--selftest` | PASS — correct range rc=0, off-by-one rc=1 with one caught citation, ambiguous basename rc=0 and skipped | ok |
| 6 | the fix must carry its supersession | `chiptune-8bit.md`'s header records the superseded digest `sha256 2e603d85…` (692 lines / 39 339 B); `anime-opening.md`'s records `sha256 0e5cdfc9…` (337 lines, commit `afa242e`) | ok |

**The census moved from 62 to 118 and that is not a regression.** The briefs grew while this class
was being worked — the same ~8 concurrent `music-producer` workers expanded them — and the check
measures every citation it can resolve. The population is unchanged at 14 briefs. §14's 62 is left
standing as its own dated reading, and every number in this section is stamped with the time and
revision it was read at, because the tree does not hold still: within five minutes of the 16:15
readings below, `check_brief_line_refs` read 119 ranges (from 118) and `check_brief_figures` read 2
findings (from 8), both with nothing in this file either way.

**One FAIL that fired during the fix belongs to the check, not to the briefs, and is filed.** At the
16:10 run the check reported a third failure, at line 835 of `music/briefs/chiptune-8bit.md`, for a
path-and-line token *quoted* inside a fenced block labelled "Verbatim results": that block records
the check's own output at revision `c296db6`, named on the prose line above the fence. The brief
makes no claim about the referent's line — it reports what the tool said. The failure was also
transient (the referent was being rewritten by a live card, `t_97494e6a`, so the target line moved
and the same citation passed two minutes later) and mis-attributed (the message asks the citing
brief to correct another genre's line numbering). Filed as `t_8d6c40ac` with the root cause — the
revision anchor sits on the fence's prose line, not on the quoting line — and two narrow candidate
fixes. The quoted output was left verbatim: mutating it would falsify the record.

**The regression itself could not finish, and was repaired in this pass** (the long form is §15 of
`music/briefs/elemental-fire.md`; the fix and its assertions are in the check). `LINK_RE` nests a
repeat inside a repeat over two overlapping classes — the `(a+)+` shape — so it backtracked
exponentially on any gap that fails to match: a gap of 8 spaces then `#` measured 0.002 s, 12 →
0.27 s, 16 → 35 s. `music/briefs/elemental-water.md` aligns a trailing comment 23 spaces out inside
a fenced transcript, so one brief took >45 s and the repo-wide run >200 s — and **the two sites this
section is about were invisible for as long as that lasted.** `LINK_RE` is now one unrolled
alternation over the same vocabulary, accepting the same language (brute-forced over every string up
to length 6: 0 disagreements), and `--selftest` asserts the incident gap stays under 50 ms.
That repair made the check reach the end of the briefs list, where it found two more blank-open
citations in `music/briefs/elemental-fire.md` (it cited a blank line 54 of `music/oracle.py` for a
`WEIGHTS` dict that now sits at 75). Both are corrected, with the supersession recorded in that
file's header.

**Final reading at 16:50 CDT, after the repair and those two corrections:**
`PASS check_brief_line_refs: 117 cited line range(s) across 14 brief(s) resolve and hold`, rc=0, in
**0.86 s**; `--selftest` PASS with the incident gap at 0.003 ms. `check_brief_figures` still FAILs —
7 of 122, and every finding is the playbook's superseded size after
`brain/playbooks/music-lane-architecture.md` grew twice today under other cards
(`t_fa731c5b`, `t_6dd13d76`); **none of the seven is this file.**

**Standing checks at this pass** (`/usr/bin/python3 music/scripts/<name>.py`, all at 16:12–16:15 CDT
@ `5aed5cc`): `check_brief_line_refs` PASS, 118 ranges across 14 briefs; `check_brief_paths` PASS,
22 citations; `check_brief_bpm_solutions` PASS, 5 styleWeight claims; `check_prompt_style_counts`
PASS, 15 declared lengths; `check_brief_drift` PASS, 16 live counts (0 behind / 82 ahead at `5aed5cc`,
14 genres, 7 blueprints); `check_stage_scripts` PASS, 11 script paths;
`check_brief_figures` **FAIL** — **1 of 120** at 16:12 (line 600 of `music/briefs/elemental-water.md`);
at 16:16, 8 of 122, seven of them briefs still carrying `brain/playbooks/music-lane-architecture.md`'s
recorded size while card `t_fa731c5b` fixed them; that 8-of-122 reading was taken with an
UNCOMMITTED working-tree edit by that card holding the playbook at a size it never landed with
(the card reverted it before committing — editing the doc invalidates the byte size many briefs
record — so the committed doc read, at `b2a1220`, 34 328 B, `sha256
1658b9126574a66be01791b8d28a07a3e8efe0b6ca6cf6ec2b20da63f9f2c1da`); at 16:20, 2 of 122, the same class shrinking live. **No finding is this
file's in any of the three readings**, and this pass changed no figure — the differences are other
people's writes landing under a shared tree.

- **Superseded revision of this file:** `sha256 5b3914191c5108814cccaaaa2c51f8a5b5eff1efc17455f7ddc4c173dac486ea` (1168 lines / 76 392 B).
- **Superseded by this pass (card `t_6dd13d76`, 2026-10-16T17:21-05:00 CDT):** `sha256 3411f2eb58de226cc6d7d5ef524b6c06d78fd34e1c2a99c445278eabc21cd15f` (1261 lines / 85229 B) — the code-comment citation above was re-pointed from `planner.py:182` to `planner.py:297`: the file grew since that reading and `:182` is blank now, while `:297` is the `load_blueprint` docstring the line names. The census text it quotes was corrected by card `t_a54fb00d` in the pass that follows — see the
bullet two below and §16.
- **Not changed, not re-filed otherwise:** the trend-fallback card `t_eb648761` is still a
  duplicate to close, and the blueprint-census comments in `music/planner/planner.py` and
  `music/tests/test_planner.py` were corrected by card `t_a54fb00d` (§16).

---

## 18. Code-prose census pass (card `t_a54fb00d`, 2026-10-16T17:31–17:45 CDT)

§16 listed three census figures in the lane's own code prose and filed them here. This pass
corrected all three and gave the class a check. No registry value, gate, plan, blueprint, chart
file or cluster object was touched, and no figure in THIS file moved.

| # | §16 site (17:31 CDT reading) | before (revision named) | after |
|---|---|---|---|
| 1 | `planner.py:325` `load_blueprint` docstring | `(3 of 15 genres do)` at `3967dea` | `(7 of 14 genres do)` |
| 2 | `planner.py:337` `bpm_in_caption` docstring | `the 11 genres that have no blueprint yet` at `dda0d32` | `the 7 genres that have no blueprint yet` |
| 3 | `tests/test_planner.py:62` comment | `Only 3 of 14 genres have a blueprint, so 11` at `dda0d32` | `The 7 of 14 genres with no blueprint fell back` |

The first two citations moved from `:297`/`:309` to `:325`/`:337` at the 2026-10-16 17:34:46 CDT
commit `f832112`, which took `planner.py` from 1157 to 1371 lines. Live census at the 17:31 CDT
reading, recomputed through the registry loader plus the `music/lyrics/blueprints/*.yaml` glob:
**14** registered genres and **7** blueprints.

**The new check — and what it deliberately does not read.** `music/scripts/check_code_census.py`
reads every `music/**/*.py` comment and docstring, applies the census shapes and the ANCHORED
escape hatch IMPORTED from `check_brief_drift.py`, and recomputes this census:

```text
$ /usr/bin/python3 music/scripts/check_code_census.py --selftest
SELFTEST PASS check_code_census: 16 census case(s) plus one prose-extraction case      # rc=0
$ /usr/bin/python3 music/scripts/check_code_census.py --rev HEAD     # the BEFORE revision
FAIL check_code_census: 4 stale census claim(s) in revision HEAD                       # rc=1
  music/planner/planner.py:297  claimed "3 of 15 genres"  measured 7 of the 14
  music/planner/planner.py:309  claimed "the 11 genres that have no blueprint"  measured 7
  music/tests/test_planner.py:62  claimed "3 of 14 genres"  measured 7 of the 14
  music/scripts/check_brief_drift.py:119  `**eleven** blueprint-less genres` — a historical
      comment line, anchored "when written" in this pass so history stays history
$ /usr/bin/python3 music/scripts/check_code_census.py                # the worktree
PASS check_code_census: 3 live census claim(s) across 113 .py file(s)                  # rc=0
```

Three limits, recorded so a later pass does not "fix" them: a bare string literal is DATA and is
not read (the fixtures in `check_brief_drift.py` are deliberately stale census strings); the `of`
pair with no `genres` after it is that check's S4 shape — a brief shape, not read here, because a
docstring can mention blueprints in one clause and count a different census in the next; and the
brace-list shape is a PATH, which code prose does not write as a census.

It was also run the way the fleet suite runs this lane's other checks — against a clean
`git archive HEAD music` extract (`verify-fleet.sh` section 13i, PR #42): PASS rc=0, 3 claims
across 114 `.py` files. Two environment behaviours were measured and are handled on purpose: a
partial extract with no `music/visuals/*.md` makes the registry refuse to load (the `visual_style`
paths), and the check then FAILs rc=1 with `cannot recompute the census …` plus a fix line instead
of a traceback — a stack trace in the fleet suite reads as a lane regression, and this is not one.

**Standing checks at this pass** (2026-10-16 17:35–17:44 CDT, worktree with other cards' writes
landing): `check_code_census` PASS, 3 claims across 113 files; `check_brief_drift` PASS, 21 live
counts (0 behind / 9 ahead of `origin/main` at `bacf245`, 14 genres, 7 blueprints);
`check_brief_paths` PASS, 21 citations; `check_brief_bpm_solutions` PASS, 5 styleWeight claims;
`check_prompt_style_counts` PASS, 15 declared lengths; `check_stage_scripts` PASS, 21 script paths;
`check_doc_refs` PASS.

Two checks FAIL, and neither finding is this file's (each was re-measured before and after this
pass, same readings): `check_brief_figures` **7 of 125** at 2026-10-16 17:40 CDT — six other
briefs cite `brain/playbooks/music-lane-architecture.md` at its `6b24a52` size of 34 328 B while an UNCOMMITTED sibling
edit holds that file at 45 674 B, the class §17 already records; `check_brief_line_refs` **4 of
127** at that same reading — `elemental-air/above-the-weather/brief.md` and `elemental-earth.md`
cite `planner.py` ranges that the 1157 to 1371 line growth moved. `music/tests/`: `test_planner`
PASS, `test_acestep_plan` PASS, `test_loop_close` PASS, `test_gate_loop_points_fade` PASS,
`test_lyrics_gate_language` PASS; `test_acestep_sheet_guard` FAIL 3 (three committed lyric sheets
against a widened placeholder rule — a sibling's gate change in flight).

- **Superseded by this pass (card `t_a54fb00d`, 2026-10-16):** `sha256 f9d76960fb3c836b84653e7f5037bad161f01d7d75699fe965e3e9868bfd572c` (1262 lines / 85 699 B).
- **Superseded by this pass, same card, second commit (the environment-failure hardening of the new check, 2026-10-16):** `sha256 710fbd9bceca8d3b9528448a6f9e1e4cc72ed387ead673b23b58f53fa8f1a3fe` (1367 lines / 93 767 B).

## 19. A `measure.py` line that only looked like an absence claim (card `t_bdb94fb7`, 2026-10-16)

`music/scripts/check_brief_absences.py` FAILed rc=1 on item 2 of the generate prompt (line 765
at `178be75`): "one render at `style_weight = 0.9`, one with it absent, both measured
with `music/rubrics/measure.py`". The absence belongs to the `style_weight` FIELD, not to the
measurement script — and `music/rubrics/measure.py` is present, which the line never denied. A
line-scoped check cannot tell use from mention, so the sentence is reworded to "one with the field
left unset": the A/B instruction and its meaning are unchanged. `check_brief_absences.py` is rc=0
repo-wide after the four-brief pass of this card.

- **Superseded by this pass (card `t_bdb94fb7`, 2026-10-16):** `sha256 dbec2ef82dee346e751ff0cc1f95fab2dec2e77b682d657bc2c0d00fadb1bc82` (1375 lines / 94 569 B).

## 20. Declared scoring scope — machine-checked against the live rubric (card `t_00ac4f10`, 2026-10-16)

`music/scripts/check_brief_rubric_scope.py` reads the `rubric_scope` block below and
compares it, field by field, to this genre's scope COMPUTED from `music/rubrics/edm.json`
by the panel's own resolver (`music/rubrics/panel.py`: `applicable_criteria()`,
`applicable_signals()`). `edm.json` declares `applies_to` on every criterion, so both of
its genres are covered: a criterion added, dropped or re-weighted in that file fails this
brief instead of going unnoticed. The block is a claim about NOW, and the check never reads
prose.

Regenerate the block after any rubric edit — one command, no hand-edit:

    /usr/bin/python3 music/scripts/check_brief_rubric_scope.py --print-truth jungle-dnb

```json
{
  "rubric_scope": {
    "genre": "jungle-dnb",
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

    ## 21. The payload-census class — the skipped site re-measured (card `t_34f5e94a`, 2026-10-16 18:55 CDT)

    `check_brief_drift.py`'s S7 prints the census claims that name the deployed payload as SKIPs
    rather than guessing at them, because the payload is cluster state and no repo-local check can
    recompute it. The one SKIP site in this brief is not a licence to leave the line alone: this pass
    re-read the live ConfigMap and corrected it.

    **Live census, `kubectl -n mining get configmap music-pipeline-payload -o json` at 2026-10-16
    18:55 CDT (this host, nexus):** **43 keys** — 7 blueprints, 15 prompt entries, 14 visuals,
    `genres.yaml`, `planner.py`, `acestep_plan.py`, `loop_close.py`, `backfill_render.py`,
    `check_render_landed.py`, `render_state.py`. The 17:18 CDT reading was 42 keys / 7 blueprints;
    the 15:31 reading was 38 / 6.

    **Convention (card `t_34f5e94a` §3).** A payload claim carries the clock time it was taken at, in
    the ANCHORED form the census classes already use — `check_brief_drift.py` skips a stamped line,
    and a payload line is skipped anyway, so the two rules coincide for this class. The payload is
    re-synced from the repo, so an unstamped payload number reads as a claim about now and is stale
    by the next `sync-payload.sh`. This pass uses the stamped form everywhere it writes one.

    **Site corrected, in this brief:**

    | § | Was | Is |
    |---|---|---|
    | §18 | "the payload still carried both at the 2026-10-16 17:31:54 CDT read above … the fence stays as the deployed revision and the two copies differ by this one docstring until then" | the 17:31 reading is the one this sentence records and is itself superseded; re-read at 18:55 CDT, the deployed `planner.py` reads `(7 of 14 genres do)` at line 329, so the two copies agree and the fence is a historical artifact only |

    The payload's own docstring was verified as part of this pass, not assumed: dumped the
    `music__planner__planner.py` key to `scratch/planner_deployed.py` and read line 329 from it.
    `check_brief_drift.py` was **not** widened to read the cluster — it stays runnable with no cluster
    access, and the payload line remains a SKIP. No genre finding was reopened; only the one
    supersession sentence moved.
