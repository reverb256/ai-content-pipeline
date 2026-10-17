# music/rubrics — the reviewer panel for music quality

The `gate` stage's independent review: a panel of small judges from
disjoint model families scores a track against CORPUS-ANCHORED rubrics,
using MEASURED evidence from the audio file itself.

## Research basis (papers read in full, 2026-10-08)

| Finding | Source |
|---|---|
| Knowledge-grounded rubrics beat generic ones; generic rubrics let judges anchor on surface heuristics (the "Evaluation Illusion") | arXiv:2603.11027 |
| A panel of small judges from disjoint families beats one big judge, ~7x cheaper (PoLL) | arXiv:2404.18796 |
| Arithmetic-mean aggregation has unbounded bias if one judge is contaminated; the geometric median is robust (breakdown point 1/2, tuning-free) (RoPoLL) | arXiv:2606.30931 |

## Layout

```
rubrics/
  <family>.json        one rubric per genre FAMILY (not per genre):
                       ambient, edm, acoustic, utility, vocal, gamer, anisong
  measure.py           MEASURED evidence extraction (ffmpeg + numpy):
                       duration, loudness, BPM candidates per band, the
                       ac at the requested anchor, silence map, crest factor,
                       RMS spread, high-energy fraction
  panel.py             the panel runner: measures the artifact, prompts
                       every judge, aggregates by geometric median,
                       writes review.json + panel-detail.json
  probe_judges.py      one-token liveness probe for each judge endpoint
  test_panel_math.py   unit tests: Weiszfeld math, aggregation, rubric
                       schema, registry coverage (run before any change)
  test_measure_bpm.py  unit tests: the tempo measurement and the card
                       t_ed609eb0 regression fixtures (run before any change)
```

## Genre-generic contract

Genre -> family -> rubric is DATA: `music/genres.yaml` maps every genre
to a family; every family in the registry must have a rubric file. Adding
a genre with a NEW family means adding one JSON file — never a code edit.
`test_panel_math.py` enforces this (fails if a registry family has no
rubric).

Panel membership is data too: profiles named on the command line
(default: `reviewer`, `reviewer-nemotron`, `reviewer-deepseek`), resolved from
their Hermes profile configs, with endpoint fallback via
`scripts/fleet-route.py ENDPOINTS`.

Each member's OWN `fallback_providers` chain is walked, in order, before that
member counts as dead (card `t_3d84acfe`). The panel used to read only
`model.default` + the provider block, so a profile whose primary was dead was a
dead judge even though its declared chain was live.

### Membership: three families, and the checks that keep it that way

The PoLL contract needs judges from DISJOINT model families. Measured
2026-10-16 (`t_3d84acfe`): the panel reached ZERO judges for every track,
because every `reviewer*` profile's primary was `opencode-go`, which now answers
`HTTP 400 MissingSessionID` (a missing `x-opencode-session` header, not a quota)
— and nothing detected it, because the panel runs only when a human runs it. The
membership is therefore one judge per family, each with a SAME-FAMILY chain so a
fallback can never duplicate a sibling judge:

| profile | primary | family | chain (same family) |
|---|---|---|---|
| `reviewer` | `nous` / `poolside/laguna-s-2.1:free` | poolside | `kilo`, then `openrouter-free` |
| `reviewer-nemotron` | `nvidia` / `nvidia/nemotron-3-super-120b-a12b` | nvidia | `kilo`, then `openrouter-free` |
| `reviewer-deepseek` | `kilo` / `dots-studio/dots-3-note-preview:free` | dots-studio | `openrouter-free` |

A profile NAME is a slot, not a model: the family comes from the model, and the
panel reports a `PANEL FAMILY COLLISION` finding when two judges that answered
share one family. Two checks enforce the shape:

| check | what it does | cost |
|---|---|---|
| `music/scripts/check_panel_membership.py` | offline: every member exists, resolves, families pairwise disjoint, every chain stays in its family, no dead provider or dead slug, endpoint follows the provider | no tokens |
| `music/rubrics/probe_judges.py` | live: asks each member's chain the panel's own question and needs >= `MIN_VALID_JUDGES` members to answer with parseable JSON | one small call per member |

Both run in the scheduled `music-gate-matrix` run
(`music/scripts/run_gate_matrix.sh`, daily 06:20 on nexus). A panel failure exits
that runner with **3**, distinct from a gate defect (1) and from a refused suite
(2), and files the same board card a gate failure files.

## Corpus anchoring

Every criterion cites real production conventions WITH NUMBERS (BPM
pockets, bar counts, LUFS targets, the 2A03's five voices, the anisong
key change) and links its source. `test_panel_math.py` fails any
criterion whose anchor contains no number. Sources for each family are
listed in the rubric JSON's `sources` array.

## Sub-idiom scoping (`applies_to`) — scope is DATA, never prose

A family can hold more than one sub-idiom: `gamer` carries orchestral
battle, chip and elemental exploration; `anisong` carries openings and
endings. A criterion therefore declares the genres it scores:

```json
{"id": "battle_energy",  "applies_to": ["elemental-fire", "epic-orchestral-boss"]}
{"id": "loop_safety",    "applies_to": "all"}
```

- `applies_to: [<genre ids>]` — scored only for those genres.
- `applies_to: "all"` — every genre in the family. A multi-genre rubric
  must say this explicitly, so an omission cannot pass as "everything".
- (field absent) — family-common; only tolerated in a single-genre rubric.

`panel.py` scores the APPLICABLE SUBSET only: the judge prompt lists those
criteria and names the excluded ones, the geometric-median vector and the
weighted mean are taken over them, and `review.json` records the scope the
verdict was computed under (key `rubric_scope`) so the human review queue
need not reconstruct it. A reject signal can be scoped the same way
(`{"id", "signal", "applies_to"}`); a bare string is family-common.

`test_panel_math.py` enforces the invariants via `panel.rubric_scope_defects()`:
a criterion NAME may not declare a scope the data does not carry, a
multi-genre rubric must declare a scope on every criterion, and every genre
must keep at least one applicable criterion.

Incident this encodes — card `t_426a82a3` (2026-10-16): the `gamer` rubric
kept its sub-idiom scope in criterion NAMES only, and `panel.py` had no code
path for it. All five criteria were scored on all six genres, so an 82-92 BPM
exploration theme took the guide's prescribed 1 on `battle_energy` and every
`elemental-*` took 1 on `chip_timbre_authenticity` — 41/11 = 3.73 against the
7.0 threshold for a correct `elemental-air` track the oracle scores 7.5. The
fix scopes the data AND gives the third sub-idiom its own craft criterion,
`elemental_atmosphere`; every gamer genre now scores 4 criteria, Σw = 8.

## How a review runs

1. `measure.py` EXECUTES the artifact (the panel never trusts a filename):
   ffprobe, volumedetect, silencedetect, and a numpy onset-envelope
   autocorrelation BPM estimate (candidates reported honestly, including
   half/double ambiguity).
2. Each judge receives the rubric + measured evidence + the producer's
   style claim, and must score every criterion 1-10, list findings, flag
   reject signals, and mark unverifiable criteria. Judges CANNOT listen —
   the prompt forbids inventing measurements. A member whose primary call
   fails is retried down its own `fallback_providers` chain before it
   counts as a dead judge; every miss is recorded in
   `panel-detail.json:judge_failures`.
3. Aggregation: geometric median across the panel's score vectors
   (modified Weiszfeld iteration, Vardi & Zhang 2000).
4. Verdict:
   - `fail` if aggregate < pass_threshold (7.0), OR
   - `fail` if a MAJORITY of judges hit the same reject signal (fatal,
     genre violation), OR
   - `fail` (with a triage finding) if the panel disagrees — overall
     spread >= 3.0 — or fewer than 3 judges returned valid scores.
     Disagreement routes to human triage; the panel never guesses.
5. Output: `review.json` in the exact record layout `music/gates/
   gate_quality.py` validates (master sha256 binding, reviewer_model
   != producer_model, verdict, findings, reviewed_at) — the gate needs
   no changes. `panel-detail.json` carries the full per-judge evidence.

## Tempo: what the tool measures, and what it does not (card `t_ed609eb0`)

`bpm` is a **candidate set with evidence**, never one bare number. Read
`bpm_candidates` first, then `ac_at_anchor` when an anchor was requested.

| field | meaning |
|---|---|
| `bpm` | the headline candidate (rules below). `null` when nothing is measurable. |
| `bpm_confidence` | the ac of the headline's lag. |
| `bpm_candidates` | every candidate: `bpm`, `ac`, `confidence`, `lag`, `lag_bpm`, `prominence`, `best_band`, `bands`, `edge`. |
| `bpm_bands` | per band (`full`, `bass`, `mid`, `high`): `argmax_bpm`, `argmax_ac`, `median_ac`, `top_peaks`. |
| `bpm_pulse` | `measurable` or `none`. `none` means no candidate reaches ac 0.25. |
| `bpm_note` | why the headline is not the obvious number, when it is not. `null` otherwise. |
| `ac_at_anchor` | with `--anchor-bpm N`: the ac AT the anchor's lag, per band, plus `near` (the best ac within ±10 % of the anchor period) and a `verdict`. |

**Bands.** The onset envelope is measured in four bands: `full` (0 to
Nyquist), `bass` (20-500 Hz), `mid` (500-8000 Hz), `high` (2000-8000 Hz). A
whole-band envelope cannot see a percussion-free bed: the low-frequency pad
energy carries most of the spectral flux, and the weak transients that carry
the tempo are averaged away. The 2-8 kHz band sees them.

**Selection rules**, in order:

1. Candidates are the autocorrelation local maxima of every band inside the
   60-190 BPM lag range, each folded by 0.5 / 1.0 / 2.0 into that range, at ac
   >= 0.20. Folded candidates keep their OWN lag's ac — the pre-fix code read
   the ac at `int(60*fps/b)`, up to a lag away from the peak it claimed, so a
   candidate's confidence could belong to a tempo 5 BPM away.
2. Ranking is by **prominence** = peak ac minus that band's median ac over the
   lag range. Prominence compares peaks of envelopes with different baselines;
   raw ac does not.
3. **The band edge.** The lag search range is cut at 60 BPM. An argmax that
   sits there is a cut, not a located peak, and it is kept in
   `bpm_candidates` with `edge: true`. When a non-edge candidate reaches
   75 % of its ac, the non-edge candidate becomes the headline and
   `bpm_note` names the artefact. A genuine 60 BPM track keeps its edge
   headline, because its half-tempo partner is far weaker.
4. **The anchor.** With `--anchor-bpm N`, a measured candidate within 3 BPM of
   the anchor at ac >= 0.25 becomes the headline, and `bpm_note` names the
   candidate the prominence ranking alone would have reported. No anchor: the
   ranked top wins and octave relations stay visible in the candidate
   list.
5. If the headline's ac is below 0.25, `bpm` is `null` and `bpm_pulse` is
   `none`. The tool says it cannot measure a tempo instead of reporting a
   number it cannot support.

**Lag quantisation.** The envelope frame rate is `sr/HOP` = 43.07 Hz, so the
lag grid steps by about 3 BPM at 92 BPM (lag 28 = 92.3, lag 29 = 89.1).
`ac_at_anchor.lag_bpm` states the tempo the grid can actually express, and
`ac_at_anchor.near` is the honest answer to "is there periodicity at the
anchor".

### The acceptance rule for a percussion-free genre

Every instrumental ambient genre in the registry (elemental-air / earth / fire
/ water, chill-lounge, sentimental-piano) is percussion-free or near it by its
own template. For those genres, judge the tempo like this — this is the
authoritative rule, and it is what a queue card's acceptance text must say:

- **Authoritative tool:** `measure.py`, run with the genre anchor:
  `/usr/bin/python3 music/rubrics/measure.py <artifact> --anchor-bpm <N>` (or
  `panel.py --anchor-bpm N`, which passes it to `measure.py`).
- **Pass:** `ac_at_anchor.verdict == "supported"` — a candidate within 3 BPM of
  the anchor at ac >= 0.25, or the anchor's own lag ac >= 0.25 within ±10 % of
  its period.
- **Not measurable, not a fail:** `bpm_pulse == "none"` and
  `ac_at_anchor.verdict == "not_supported"` means the tool cannot see a pulse.
  `bpm` is `null`. The tempo claim is then decided by the stem or ear check,
  and the card must say so — it is never a silent FAIL and never a pass.
- **Never** accept or reject on `bpm` alone, and never on a bare "within a few
  BPM of the anchor" that does not name the field.

Incident this encodes — card `t_ed609eb0` (2026-10-16). `_bpm()` folded 0.5 /
1.0 / 2.0 only from its whole-band argmax, and on the elemental-air render
(`suno-0fa09abe521341629d4f4c59147ae72f.flac`, sha256 `1543a42b…`, 334.000000
s, requested 92 BPM, no percussion by genre rule) that argmax sat at the 60 BPM
edge. The anchor never entered `bpm_candidates`. Measured, pre-fix:
`bpm 60.1` (conf 0.369), candidates `[60.1 / 0.369, 120.2 / 0.072]` — and
`60.1` (conf 0.706) for a commentary sting that is really 120 BPM, and `86.1`
for the elemental-earth loop that is really 88 BPM. Post-fix, same artifacts:
`92.3` (ac 0.3705, the 2-8 kHz band's top peak, anchor verdict `supported`),
`117.5` (ac 0.5504), `86.1` (ac 0.3902). The band-edge value stays visible as
`bpm_bands.full.argmax_bpm` and as an `edge: true` candidate.
`test_measure_bpm.py` pins all of this; `negctl` it against
`git show <pre-fix>:music/rubrics/measure.py` and the fixture checks fail.

## Verified acceptance run (2026-10-08)

Real track (YuE2 render, "loading screen" ballad, 72 BPM felt piano,
sha a4236d8c...):

```
judges:  longcat (poolside/laguna-s-2.1)  overall 8.0
         minimax (dots-studio/dots-3)     overall 8.0
         nemotron (nvidia/nemotron-3-ultra) overall 8.6
         deepseek — offline (provider out of credits; panel tolerates one
         dead judge, needs >= 3 valid)
aggregate (geometric median): 8.09  -> PASS (threshold 7.0), spread 0.6
```

Deliberately broken version of the SAME material (2.15x wrong-tempo,
hard-clipped 0 dBFS, brick-walled, no phrase space, hard-cut ending):

```
judges:  longcat 5.0 / minimax 4.0 / nemotron 3.7
aggregate: 4.56 -> FAIL, with majority fatal signals:
  - clipped master (max_volume_db >= -0.1)
  - no measured phrase space on an intimate-piano claim
```

Bad < Good by 3.5 points, exactly as the rubric intends. A contaminated
single judge (longcat voted both those signals on the GOOD track) was
correctly outvoted by the majority on the good run — the RoPoLL property
working in production.

## Re-run 2026-10-16 — after the reachability fix (card t_3d84acfe)

The run above had stopped working: every `reviewer*` profile's primary
pointed at `opencode-go`, which now answers `HTTP 400 MissingSessionID`, the
panel never walked the declared fallback chains, and all three profiles named
the SAME model — so the panel reached ZERO judges and wrote
`reviewer_model: panel[none-reachable]`, `verdict: fail` for every track, which
made `gate_quality` unpassable. Same track, re-run on the re-pointed membership
with NO `--panel` override (the DEFAULT panel, three families, three providers):

```
$ /usr/bin/python3 music/rubrics/panel.py \
    --audio packages/welcome-asset-pack/loops/loop_01_bpm184_key-Cmajor.wav \
    --genre elemental-air --style-claim music/prompts/elemental-air.md
[panel] genre=elemental-air family=gamer rubric=gamer.json
        criteria_applied=['elemental_atmosphere','loop_safety','asset_packaging','loudness_target']
        criteria_excluded=['chip_timbre_authenticity','battle_energy']
        members=['reviewer', 'reviewer-nemotron', 'reviewer-deepseek']
[panel] reviewer (poolside/laguna-s-2.1:free via nous, primary): overall=7.0 reject... (48.2s)
[panel] reviewer-nemotron (nvidia/nemotron-3-super-120b-a12b via nvidia, primary): overall=5.875 (65.6s)
[panel] reviewer-deepseek (dots-studio/dots-3-note-preview:free via kilo, primary): overall=3.625 (66.7s)
[panel] aggregate overall = 5.93 (threshold 7.0) judge overalls = [7.0, 5.88, 3.62] spread = 3.38
[panel] fatal signals = [] triage = True -> VERDICT fail
exit 0
```

Three judges answered, so this is a VERDICT, not an autofail: `5.93 < 7.0` and
a spread of `3.38 >= DISAGREE_SPREAD`, so the first finding is `PANEL
DISAGREEMENT — human triage required` and the judgement goes to a human queue.
`reviewer_model` now records all three models;
`music/rubrics/probe_judges.py` reports `3/3 members live, families
['dots-studio', 'nvidia', 'poolside'] disjoint`.

The panel says nothing about reachability by itself — that is what the two
checks under "Membership" above exist for.

## Usage

```
python3 music/rubrics/panel.py \
  --audio <track> --genre <genres.yaml id> \
  [--style-claim <prompt/request file>] [--lyrics <lyrics file>] \
  [--producer-model <model>] [--out-dir <pkg dir>] \
  [--panel reviewer-deepseek,reviewer-longcat,...] [--limit N]
```

Exit code 0 = the panel ran (verdict is in review.json); 1 = hard error
(including zero reachable judges — an honest fail verdict is written).

Notes:
- Run the panel with an interpreter that has numpy + PyYAML:

  ```
  /usr/bin/python3 music/rubrics/panel.py --audio <track> --genre <id>
  ```

  Measured 2026-10-16: the Hermes-managed `python3` on zephyr has neither, so
  the bare documented command dies on `ModuleNotFoundError`. `test_panel_math.py`
  now prints that instruction instead of a traceback.
- `max_tokens` is set high (16k): reasoning models burn tokens before
  emitting the JSON; a low cap silently truncates to empty content
  (observed with dots-3-note-preview).
- 4xx (credits/auth) do not retry; 429/5xx back off and retry (3 tries).
- Never print judge API keys; resolve_judge() loads them into memory only.
