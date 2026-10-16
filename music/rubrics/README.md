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
                       duration, loudness, BPM candidates, silence map,
                       crest factor, RMS spread, high-energy fraction
  panel.py             the panel runner: measures the artifact, prompts
                       every judge, aggregates by geometric median,
                       writes review.json + panel-detail.json
  probe_judges.py      one-token liveness probe for each judge endpoint
  test_panel_math.py   unit tests: Weiszfeld math, aggregation, rubric
                       schema, registry coverage (run before any change)
```

## Genre-generic contract

Genre -> family -> rubric is DATA: `music/genres.yaml` maps every genre
to a family; every family in the registry must have a rubric file. Adding
a genre with a NEW family means adding one JSON file — never a code edit.
`test_panel_math.py` enforces this (fails if a registry family has no
rubric).

Panel membership is data too: profiles named on the command line
(default: reviewer-deepseek, reviewer-longcat, reviewer-minimax,
reviewer-nemotron), resolved from their Hermes profile configs, with
endpoint fallback via scripts/fleet-route.py ENDPOINTS.

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
   the prompt forbids inventing measurements.
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
