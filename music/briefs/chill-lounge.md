# Brief — chill-lounge

> **Stage:** brief (stages.yaml: `brief` → bot `producer`)
> **Card:** t_38e84953 (`music-oracle: chill-lounge (score 8.9)`)
> **Duplicate card:** t_4c838339 (`music-oracle: chill-lounge (score 9.1)`) — same genre,
> same lanes. Both resolve to THIS brief; keyed by genre, not by card.
> **Written:** 2026-10-16T13:03:27-05:00 (CDT)
> **Repo:** /home/j_kro/ai-content-pipeline @ `e278f614fb0d98a6f74e7e8682c0336740e8a79e` (main)
> **Oracle:** score 8.9/10 (quota headroom 10.0, lane coverage 8.0, revenue 10.0,
> cadence fit 10.0, policy risk 10.0, trend signal 3.0). Threshold 5.0 → produce.

## 1. Genre resolution (live, not transcribed)

Resolved from `music/genres.yaml` — not copied by hand:

```
$ python3 music/registry.py validate
registry OK: 14 genres, 10 lanes
genres: activist, anime-ending, anime-opening, chill-lounge, chiptune-8bit,
        commentary-beds, elemental-air, elemental-earth, elemental-fire,
        elemental-water, epic-orchestral-boss, jungle-dnb, sentimental-piano, trance
lanes: direct-fan, direct-license, game-assets, stock-ai-native, streaming,
       sync, sync-documentary, youtube-gaming, youtube-longform, youtube-mix
quota ledger: period 2026-10, standard 0/60 (warn_at 55, hard_stop_at 58)
```

The validator checks that every referenced lane exists and every
`prompt_template` / `visual_style` path resolves to a real file. It passed, so the
chill-lounge block and its four lanes are internally consistent.

| Field | Value |
|---|---|
| Genre | `chill-lounge` |
| Family | `ambient` |
| Prompt template | `music/prompts/chill-lounge.md` (resolves) |
| Visual style | `music/visuals/lofi-room-rain.md` (resolves) |
| Lanes | `youtube-longform`, `streaming`, `sync`, `direct-license` |
| Cadence | 3/wk |
| Video shape | `album-30-60min` |
| Lyric blueprint | `music/lyrics/blueprints/chill-lounge.yaml` |
| Note (registry) | "Highest-volume lane. Needs visual identity to survive inauthentic-content review." |

## 2. Intent

A late-night room you want to stay in. Downtempo loop music for passive listening —
the product is **watch time and repeat play**, not a song that develops. Warm,
degraded, unhurried; jazz voicings over a swung hat loop; tape flutter and vinyl
crackle as the texture. The genre is worth 3 uploads/week because a 30–60 min
album video holds listeners for the full runtime, which is where both the ad
revenue and the platform-authority signal come from.

Three things must hold, or a generation is out of genre:

1. **Tempo 70–90 BPM** (sweet spot 75–85). Above 90 it drifts to boom-bap.
2. **Jazz harmony** — maj7/min7/dom9, close voicings, ii–V–I as the default loop.
3. **Degradation is the sound** — top end rolled off 8–12 kHz, crackle bed at
   −18 to −22 dBFS, tape flutter 10–20%.

A generation with a vocal hook, a build-drop, or a bright modern top end is **rejected**.

## 3. Target lanes and what each one demands

From `music/lanes.yaml`. These are the gates that will actually run, not advisory text.

| Lane | Shape / surface | Gate that must pass | Required artifacts |
|---|---|---|---|
| `youtube-longform` | album-30-60min on YouTube | `gate_youtube_authentic` | shot diversity (not a raw image dump), Jaccard similarity vs prior uploads, AI disclosure |
| `streaming` | via `distributor` (DistroKid; TuneCore alt) | `gate_release_ready` | `ai_disclosure`, `isrc`, `metadata`, `master` |
| `sync` | Songtradr / AudioSparx | `gate_sync_ready` | `stems`, `metadata`, `clearance_doc`, `instrumental_version` (which must differ from the master) |
| `direct-license` | own-site | `gate_sync_ready` | `stems`, `license_tiers` |

Lane requirements that shape the work, decided here so later stages do not re-litigate:

- **Stems are not optional.** Two of the four lanes (`sync`, `direct-license`) require
  them, and `sync` additionally requires an **instrumental version that differs from
  the master**. Export stems through Suno **Studio** (unlimited), never the standard
  download button (60/month cap).
- **`gate_sync_ready` needs a real PDF clearance doc.** A placeholder fails it.
- **Autonomy rung for all four lanes is `advisory`** (`music/autonomy.yaml`): every
  publish is proposed with evidence and approved by j_kro. Rung promotion needs 10
  clean advisory publishes.

## 4. Throughput budget (derived, not assumed)

Cadence 3 videos/week (`genres.yaml`) × 8–12 tracks per album video
(`music/visuals/lofi-room-rain.md`: "30–60 min runtime = 8–12 tracks + chapter
cards between, not one static image") = **24–36 tracks/week**.

That number is the real constraint on this lane. It only works because this genre is
**instrumental-first**: `music/prompts/chill-lounge.md` states the lyrics box stays
empty (Suno's instrumental path) and warns against pasting production notes as sung
lyrics. Instrumental tracks skip the human-authorship bottleneck entirely. Treat the
vocal route as the exception, not the default.

Where vocals are wanted, the blueprint (`music/lyrics/blueprints/chill-lounge.yaml`)
carries a full 7-section structure at a 72 BPM anchor and requires **human-authored**
lyrics to keep the copyright claim.

## 5. Audio identity (locked for this genre)

Style caption, verbatim from `music/prompts/chill-lounge.md` (545/1000 chars):

```
downtempo chill lounge, 75 BPM, 4/4, heavy swung hats, warm jazz chords on felt
electric piano, maj7 min7 dom9 voicings, soft round bassline following chord roots,
tape saturation and gentle wow-and-flutter pitch drift, vinyl crackle bed at the
noise floor, slow low-pass filter movement across the loop, light sidechain pump on
the chords, unhurried 8-bar loop that barely develops, kick and snare sitting behind
the chords, muted guitar answering phrases, airy reverb, no bright modern top end,
warm not loud, late-night room with rain outside
```

Settings: **Weirdness 40%**, **Style Influence 70%**,
**Exclude Styles:** `EDM, big drops, autotuned pop vocals, trap hats, bright synth
leads, loud drums` (six terms, the documented maximum).

Structure: 4–8 bar loop, minimal development, small per-pass variation
(filter, crackle shift, one melody note). Arrangement is texture, not a song arc.

## 6. Visual identity (locked for this genre)

`music/visuals/lofi-room-rain.md`: one continuous lived-in room per video —
amber desk lamp (#d9a066), muted teal window (#4a6670), base #2a2321; rain-streaked
glass at ~12 fps; drift 0.5–2 px/frame; grain 4–6%. Cut only on track boundaries.
**Each upload must use a different room variant** (rain / coffee shop / night porch /
studio) and never reuse the exact frame stack — `gate_youtube_authentic` measures
frame similarity against prior uploads, and this is the lane's stated survival risk.

## 7. Existing assets for this genre

`music/lyrics/chill-lounge/amber-hour/` is a complete human-authored lyric sheet
(title "Amber Hour", author j_kro, written 2026-10-08). Measured live:

```
$ python3 music/gates/gate_lyrics_original.py --track-dir music/lyrics/chill-lounge/amber-hour
PASS gate_lyrics_original
  track        : Amber Hour (music/lyrics/chill-lounge/amber-hour)
  sections     : 7
  unique words : 93
  authorship   : j_kro @ 2026-10-08T12:48:59+00:00
  suno markers : none
```

So the lyrics half of one chill-lounge track exists and passes its gate. **No audio
exists yet** — `~/Music` is empty and `music/` holds no masters or stems. The first
render is genuine work, not a re-run.

Quota is untouched, measured live:

```
$ python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

## 8. Open items for the next stage (`genre-select` / `lyrics` / `generate`)

1. **Instrumental vs vocal split.** The blueprint is written for vocals; the prompt
   says this lane is almost always instrumental. Decide per track: instrumental for
   album beds (24–36 tracks/wk), vocal only where a lyric sheet like `amber-hour`
   exists. Do not let the vocal path gate the album lane.
2. **Clearance doc.** `sync` and `direct-license` both need a real PDF clearance
   document. None exists in the tree. This is a blocker for those two lanes, not for
   `youtube-longform`.
3. **License tiers.** `direct-license` requires `license_tiers`; nothing defines them yet.
4. **Two duplicate stack-ups.** (a) This genre has two oracle cards (t_38e84953 8.9,
   t_4c838339 9.1). (b) Every other oracle genre has two as well — 28 oracle cards
   for 14 genres. Deduplicate before the driver dispatches, or the same brief is
   produced twice.

## 9. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` (validated live, 14 genres / 10 lanes)
- Gates: `music/gates/` (all four lane gates present, exercised live above)
- Quota: `music/quota-ledger.json` (measured)
- Autonomy: `music/autonomy.yaml` (all lanes `advisory`)
- Stage contract: `music/stages.yaml` (`brief` → `producer`)
- **Dangling reference:** `brain/playbooks/music-lane-architecture.md` is cited as
  "READ FIRST" by this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`,
  `autonomy.yaml`, `gates/README.md`, and `gates/*.py` — but the file does not exist
  anywhere on this machine (`find /home/j_kro -name 'music-lane-architecture.md'` → no
  hits). Same for `brain/research/music-monetization-2026.md`. Section numbers quoted
  from it (e.g. §3, §4, §5, §11.2) cannot be checked.
