# Brief — anime-ending

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`)
> **Card:** t_2541fd9c (`music-oracle: anime-ending (score 7.65)`)
> **Duplicate card:** t_932abbb7 (`music-oracle: anime-ending (score 7.85)`) — same genre,
> same lanes, same day. Both resolve to THIS brief; the brief is keyed by genre, not by card.
> **Written:** 2026-10-16T13:06-05:00 (CDT)
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `e278f614fb0d98a6f74e7e8682c0336740e8a79e` (main)
> **Oracle score:** 7.65/10 (quota headroom 10.0, lane coverage 8.0, revenue 10.0,
> cadence fit 1.7, policy risk 10.0, trend signal 3.0). Threshold 5.0 → produce.

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

`/usr/bin/python3` is the interpreter the systemd units use; it has PyYAML. The
shell's bare `python3` is the Hermes bundled interpreter and has no PyYAML.

| Field | Value |
|---|---|
| Genre | `anime-ending` |
| Family | `anisong` |
| Prompt template | `music/prompts/anime-ending.md` — exists, 5523 bytes |
| Visual style | `music/visuals/anime-ending.md` — exists, 2223 bytes |
| Lanes | `streaming`, `sync`, `direct-license`, `youtube-longform` |
| Cadence | 1/wk |
| Video shape | `album-30-60min` |
| Lyric blueprint | `music/lyrics/blueprints/anime-ending.yaml` — **ABSENT** (only `activist`, `chill-lounge`, `trance` exist) |
| Registry note | "Anison ballad idiom: 70-120 BPM, IV-V-iii-vi royal road, gentle key lift in the final chorus, brushed drums from verse 2, Japanese vocals in Japanese script. Required by the Virtual Reflections album (track 9). Hard-cut ending is a defect - the tail fades the light." |

## 2. Intent

The emotional exhale after the opening's explosion. A Japanese-language anison
ballad for the close of an arc — intimate, reflective, dense with meaning and
deliberately low on energy. The registry fixes the job: this genre is **track 9
of the Virtual Reflections album** ("Reflections", per `music/prompts/anime-ending.md`).
It is not a standalone single; it sits inside the album video.

Three things must hold, or the generation is out of genre (from the template's
craft notes, which are the idiom's convention):

1. **Tempo 85–100 BPM** (the template's ballad pocket; the genre window is 70–120).
   Below 70 is a film-score cue, above 120 is mid-tempo pop.
2. **IV–V–iii–vi royal road under the chorus, landing on the minor vi.** The same
   progression as the opening, used for its bittersweet colour.
3. **Final chorus lifts a key, gently** — the anison gesture at ending gain. A warm
   swell, not the opening's explosion. Omit it and the track is a generic ballad.

A generation with a hard unison ending, a fast drum intro, or English lyrics is
**out of genre — reject it**.

## 3. Target lanes and what each one demands

From `music/lanes.yaml`. These are the gates that will run, not advisory text.

| Lane | Surface / bot | Gate | Required artifacts |
|---|---|---|---|
| `streaming` | distributor (DistroKid; TuneCore alt) | `gate_release_ready` (+`gate_loudness`) | `ai_disclosure`, `isrc`, `metadata`, `master` |
| `sync` | Songtradr, AudioSparx | `gate_sync_ready` | `stems`, `metadata`, `clearance_doc`, `instrumental_version` |
| `direct-license` | own-site | `gate_sync_ready` | `stems`, `license_tiers` |
| `youtube-longform` | videobot renders, publishbot uploads | `gate_youtube_authentic` | shot diversity, Jaccard similarity vs prior uploads, AI disclosure |

All eight gate files the lanes name exist in `music/gates/` and were listed live:
`gate_quota` (5913 B), `gate_lyrics_original` (7908 B), `gate_loudness` (5089 B),
`gate_quality` (5908 B), `gate_stems_present` (4947 B), `gate_release_ready` (7848 B),
`gate_sync_ready` (9229 B), `gate_youtube_authentic` (8969 B).

Lane requirements that shape the work, decided here so later stages do not re-litigate:

- **Stems are mandatory.** `sync` and `direct-license` both require them, and `sync`
  also requires an **instrumental version that differs from the master**.
- **`gate_sync_ready` needs a real clearance document.** A placeholder fails it, and
  no clearance document exists in the tree. This blocks `sync` and `direct-license`,
  not `streaming`.
- **`direct-license` needs `license_tiers`.** Nothing defines them yet.
- **Autonomy rung for every lane is `advisory`** (`music/autonomy.yaml`). Every
  publish is a proposal with evidence; j_kro approves. Promotion needs 10 clean
  advisory publishes.

## 4. Audio identity (locked for this genre)

Style caption, verbatim from `music/prompts/anime-ending.md` — **576 characters**,
inside the 1000-character Styles field:

```
japanese anime ending (anison ballad), 92 BPM, emotional ballad territory, slow 8th-note piano with sustained strings, warm clean guitar arpeggios, soft melodic bass, brushed drums entering on the second verse, IV-V-iii-vi "royal road" progression, gentle Japanese-language vocals, intimate and reflective, maximum information density with space between phrases, orchestral swell under the final chorus, gentle key lift in the last chorus, bittersweet and hopeful at once, sparse intro that blooms, final line hanging on a single held piano note, long reverb tail into silence
```

Settings from the same template: **Weirdness 30%**, **Style Influence 80%**,
**Exclude Styles:** `EDM, heavy drums, distorted guitars, rap, autotune, English lyrics`
(six terms — the documented maximum). Do not exclude "orchestral" or "piano"; they
are this idiom.

Structure: the template's **10 sections** — `Intro, Verse 1, Pre-Chorus, Chorus,
Verse 2, Pre-Chorus, Chorus, Bridge, Final Chorus — KEY LIFT, Outro`. Lyrics are
Japanese script (kana/kanji, never romaji).

## 5. Visual identity (locked for this genre)

`music/visuals/anime-ending.md`: dusk palette, warm amber `#ffb347` fading to
deep blue-violet `#2b2d5c`, one practical light source; a figure by a window seen
from behind or in silhouette. Camera drifts 0.3–0.5 px/frame. Verse near-static,
pre-chorus light dims one stop, chorus bokeh bloom, bridge a held frame, **final
chorus key lift = one-stop brightening and a slight camera rise**, outro fades to
a single point over the reverb tail. Grain 5%, bloom 8% on the practical light
only. Typography: none during the song; end card in the last 2 seconds.

The ending **fades the light**; the opening cuts the door. A hard cut is a defect.

## 6. Existing assets for this genre

None. Measured live:

- `music/lyrics/` holds sheets for `activist`, `chill-lounge`, `trance` only. No
  anisong sheet exists, so `gate_lyrics_original` has nothing to pass yet.
- `music/lyrics/blueprints/anime-ending.yaml` is absent (§1), so the planner has no
  BPM anchor or structure override for this genre.
- `~/Music` is empty — **0** wav/mp3/flac files. No render exists on this host.
- `campaigns/virtual-reflections/` and `music/packages/` do **not** exist anywhere on
  nexus (`find` over `/home/j_kro`, `/data/fast/home-relocated`, `/mnt`, `/srv`,
  `/opt`, `/var/lib`, `/media`). The album tree is on the host that ran the album
  cards. The CoS host note on `t_9546841b` (2026-10-16) says the same: the canonical
  clone and its in-flight working-tree edits are on **zephyr**, at the same path
  `/home/j_kro/Projects/ai-content-pipeline`. So the master, stem and package work for
  this track runs on zephyr; the nexus lane clone carries the code and the briefs.

Quota is untouched:

```
$ /usr/bin/python3 music/gates/gate_quota.py
PASS gate_quota
  period          : 2026-10
  standard dl used: 0/60 (warn_at=55, hard_stop_at=58)
  studio exports  : 0
```

## 7. Route — how this brief actually reaches the pipeline

**The pipe the lane runs on (live, verified).** The music pipeline is in-cluster
(`mining` namespace, Argo-managed chart `music-pipeline`), not the kanban stage machine:

1. **Brief queue** — ConfigMap `music-pipeline-briefs`, key `briefs.json`. It holds one
   entry today: `{"name":"smoke-chill-lounge","genre":"chill-lounge",...}`. The chart
   takes the list from `values.yaml` `briefs:` (`templates/configmap-briefs.yaml`).
2. **Planner** — CronJob `music-pipeline`, schedule `17 */6 * * *`, plans every brief
   that has no plan yet through `music/planner/planner.py`, and writes
   `/var/lib/music-plans/<name>.json` on the node.
3. **Render** — CronJob `music-pipeline-render`, schedule `41 */4 * * *`, renders every
   plan with no `.rendered` marker via `music/scripts/acestep_plan.py`, which posts to
   the sunolocal studio API (`http://sunolocal.mining.svc.cluster.local:8123`). Last
   run: `done: found=3 rendered=0 skipped=3 failed=0`.

So the route for this brief is a **queue entry**, not a kanban stage.

**The route the card names is dead.** The card says "Route to the pipeline driver".
The driver is `scripts/automation/pipeline-driver.sh --board music`. It cannot route
this card, for two independent reasons, both measured:

1. **The installed unit points at a checkout with no music lane.**
   `~/.config/systemd/user/music-pipeline-driver.service:17` runs
   `/home/j_kro/Projects/ai-content-pipeline/scripts/automation/pipeline-driver.sh --board music`.
   `/home/j_kro/Projects` is a symlink to `/data/fast/home-relocated/Projects`, and that
   checkout (`9aa1a23`, branch `fix/driver-explicit-stage-advance`) has **no `music/`**.
   The copy of the driver there is the pre-parameterisation version: `BOARD="faceless-youtube"`
   hardcoded at line 25, no `--board` parsing. It ignores the flag, walks the
   faceless-youtube board, and logs `dispatched 0` every 30 minutes — which is exactly
   what its log shows, most recently `2026-10-16T13:00:02` .
2. **The repair sits uncommitted and uninstalled.** The lane repo has the corrected unit
   paths in the working tree (`music/scheduler/*.service` → `/home/j_kro/ai-content-pipeline`),
   but `git status` shows them modified, not committed, and the *installed* units still
   carry the old path. The same defect kills the oracle: it fails every morning —

```
$ journalctl --user -u music-oracle.service --since "2 days ago" | tail -4
Oct 16 08:00:00 nexus python3[185521]: /usr/bin/python3: can't open file
  '/home/j_kro/Projects/ai-content-pipeline/music/oracle.py': [Errno 2] No such file or directory
Oct 16 08:00:00 nexus music-oracle.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
Oct 16 08:00:00 nexus music-oracle.service: Failed with result 'exit-code'.
```

Evidence and routing for that defect: comment added to the open ops card `t_75aacf8b`
(same "declared path does not match disk" class).

**Update, 2026-10-16 13:07 (commit `9c2d2d3`, card `t_38e84953`).** The in-repo half of
this route is now repaired by a sibling worker on this same wave: `advance-stage.sh` is
board-parameterized (it had `BOARD="faceless-youtube"` hardcoded, so a music card's stage
marker never moved), and all 12 producing prompts in `music/stages.yaml` now call it with
`--board music`. So the only remaining blocker for the kanban route is **host state**: the
four installed music units on nexus still point at `~/Projects/ai-content-pipeline`.
Reinstalling them from `music/scheduler/` (working tree already carries the corrected
paths) re-enables this route. Do not enable the driver before the handoff question below
is settled.

**Route decision for this brief:** queue it in `values.yaml` `briefs:`, with the two
payload gaps fixed first (§8, items 1–2). That is a chart/GitOps change, so it is
routed to `nexus-core` on card `t_a14e5d52` rather than written from here: the file is
Argo-synced cluster config and six sibling cards are running the same wave.

## 8. Planner dry-run (measured) and open items

The planner accepts this genre today. Run on the lane repo, draft mode, no network:

```
$ /usr/bin/python3 music/planner/planner.py plan \
    --brief "the last light of the album: an anison ballad for the close of the arc, \
where the thing that was lost is named once and then left in the room" \
    --genre anime-ending --lyrics-mode draft --language ja --title "Reflections" \
    --duration 300 --out plan-anime-ending.json
plan     : plan-anime-ending.json
genre    : anime-ending   lyrics_mode: draft
structure: Intro -> Verse 1 -> Pre-Chorus -> Chorus -> Verse 2 -> Pre-Chorus -> Chorus
           -> Bridge -> Final Chorus — KEY LIFT -> Outro
bpm/key  : 100 BPM · C minor · 4/4
duration : 300s   language: ja
validation: PASS
next: write the lyrics into the plan, then run acestep_plan.py
```

The structure matches the template's 10 sections, including the KEY LIFT. Two things
in that output are defects, not taste:

1. **BPM mismatch.** The caption (which is what the engine reads) says **92 BPM**; the
   plan's `bpm` field says **100**, because `--genre anime-ending` has no blueprint to
   anchor it and the planner falls back to 100 (`"_meta": {"blueprint": false}`). The
   template pins 92 BPM and the ballad pocket is 85–100. Fix: add
   `music/lyrics/blueprints/anime-ending.yaml` with `bpm_anchor: 92` and the 10-section
   structure, and ship it in the chart payload.
2. **The draft is refused at render, by design.** `acestep_plan.py` exits 1 with
   `FATAL: plan has empty lyrics — a draft section needs human input`, and the render
   job records a `.refused` marker instead of retrying. So queueing a draft **burns no
   GPU**. The gate to rendering this track is a **human-authored Japanese lyric sheet**.
   That is correct: AI-written lyrics void the copyright claim, which is the whole point
   of the lyrics stage (`gate_lyrics_original`).

Open items for `genre-select` / `lyrics` / `generate`:

1. **Write the Japanese lyric sheet** (10 sections, human authorship, claim recorded by
   `music/lyrics/lyrics.py`). Nothing renders before this exists.
2. **Add the anisong blueprint** so the plan's BPM matches the caption's 92.
3. **Add `visuals/anime-ending.md` to the chart payload.** The payload (`music-pipeline-payload`)
   carries `music/prompts/**` but **no `music/visuals/**`** — the video stage has no
   template in-cluster, and `instrumental_version` / licence tiers / clearance docs are
   all still open for the sync and direct-license lanes.
4. **Duplicate cards.** 14 genres × 2 cards = 28 oracle cards for 14 genres (two oracle
   runs 10 minutes apart, each creating 14; `oracle.py` passes no `--idempotency-key`
   even though `hermes kanban create` supports one). Deduplicate before dispatch, or the
   same brief is produced twice. Decision needed from j_kro; the sweep is not a bot call.
5. **This is album work.** The registry makes anime-ending track 9 of Virtual Reflections.
   The album tree is not on nexus (§6), so the master, package and stem work belongs on
   the album host.

## 9. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` (validated live: 14 genres, 10 lanes)
- Template: `music/prompts/anime-ending.md` (5523 B) — caption 576 chars, 10 sections,
  weirdness 30%, style influence 80%, 6 exclude terms, tempo pocket 85–100
- Visual: `music/visuals/anime-ending.md` (2223 B)
- Gates: `music/gates/` (all eight named gates present, `gate_quota` exercised live)
- Quota: `music/quota-ledger.json` + `gate_quota` PASS
- Autonomy: `music/autonomy.yaml` (every lane `advisory`)
- Stage contract: `music/stages.yaml` (`brief` → `producer`)
- Planner: `music/planner/planner.py` (draft run above)
- Live route: chart `music-pipeline` (`values.yaml`, `templates/configmap-briefs.yaml`,
  `templates/cronjob.yaml`, `templates/cronjob-render.yaml`), ConfigMap
  `music-pipeline-briefs`, host dir `/var/lib/music-plans`
- **Dangling reference:** `brain/playbooks/music-lane-architecture.md` is cited as
  "READ FIRST" by this lane's profile, `stages.yaml`, `genres.yaml`, `lanes.yaml`,
  `autonomy.yaml`, `gates/README.md` and `gates/*.py`, but it does not exist on this
  machine. Same for `brain/research/music-monetization-2026.md`. Section numbers quoted
  from it (for example §4, §5, §11.2) cannot be checked.
