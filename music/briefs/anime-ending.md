# Brief — anime-ending

> **Stage:** brief (`music/stages.yaml`: `brief` → bot `producer`)
> **Card:** t_9dfa74d9 (`music-oracle: anime-ending (score 7.6)`) — the surviving card.
> **Superseded cards:** t_2541fd9c (`score 7.65`) and t_932abbb7 (`score 7.85`) — the
> 2026-10-09 double emission, ten minutes apart, both closed as an audit trail. All three
> cards resolve to THIS brief; the brief is keyed by genre, not by card.
> **Written:** 2026-10-16T13:06-05:00 (CDT)
> **Verified (duplicate-card pass, `t_932abbb7`):** 2026-10-16T13:35-05:00 (CDT) — see §10.
> Three corrections came out of it: §7 (installed-unit state), §8 item 2 (the render-refusal
> string), §8 item 4 (duplicate-card status).
> **Re-measured (surviving-card pass, `t_9dfa74d9`):** 2026-10-16T15:56-05:00 (CDT) — see §11.
> The pass the file was in before this one is `sha256
> 15fbf7567866791efca4287f11d0a9fdf21874d8f419cdf70cec4bba3d2155db` (23307 B, commit
> `061b5dc`); this pass supersedes it. A day of sibling work landed in between, and §11 lists
> every claim that changed.
> **Repo:** `/home/j_kro/ai-content-pipeline` @ `1a450e00f05d1674ff03c49e7fd8073ea57ef29f` (main)
> **Oracle score (true, re-scored live 2026-10-16):** 7.4/10 (quota headroom 10.0, lane
> coverage 8.0, revenue 10.0, cadence fit 0.0, policy risk 10.0, trend signal 3.0).
> Threshold 5.0 → produce. **The 7.6 in the card title is unreachable from the fixed scorer**:
> it is the old failed-trend-fetch premium (0.10 × (5.0 − 3.0) = 0.20) removed in `b2d11f7`.
> The 7.65 in the two superseded titles is the same class of number. Re-scored live here:
> `anime-ending: 7.4/10`, components `cadence_fit 0.0`, `trend_signal 3.0` (§11).

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

*(Corrected in the surviving-card pass, `t_9dfa74d9`, 2026-10-16 15:56: the transcript read
`registry OK: 14 genres, 10 lanes` and stopped at the quota line when the brief was written.
The validator prints the stage-gate rule on its own line live — first line and the gate line
both corrected to the live output. Genre and lane lists are unchanged.)*

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
| Lyric blueprint | `music/lyrics/blueprints/anime-ending.yaml` — **PRESENT** (4422 B, added 2026-10-16 14:03 by card `t_a14e5d52`; `bpm_anchor: 92` + the 10-section structure). It was ABSENT when this brief was written — corrected in the surviving-card pass (§11) |
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

All eight gate files the lanes name exist in `music/gates/` and were listed live.
Sizes re-measured 2026-10-16 15:56 (the sizes below are the live ones; `gate_sync_ready`
grew 9229 → 30038 B when a sibling card rewrote its lane selection in `54f6d3c`):
`gate_quota` (5913 B), `gate_lyrics_original` (7908 B), `gate_loudness` (5089 B),
`gate_quality` (5908 B), `gate_stems_present` (4947 B), `gate_release_ready` (7848 B),
`gate_sync_ready` (**30038 B**), `gate_youtube_authentic` (8969 B).
Two further gates exist and are not named by this genre's lanes:
`gate_human_approval` (5705 B) and `gate_loop_points` (24143 B) — the directory holds
10 gates, not 8.

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

None for this genre. Measured live 2026-10-16 15:56 (this section was corrected in the
surviving-card pass — four of its claims had gone stale; §11):

- `music/lyrics/` holds sheets for `activist`, `anime-opening`, `chill-lounge` and
  `trance`. No `anime-ending` sheet exists, so `gate_lyrics_original` has nothing to
  pass yet. (When the brief was written the list was `activist`, `chill-lounge`,
  `trance`; `anime-opening/becoming` landed later the same day. That sheet is anisong
  family, so it is a sibling work product, not this genre's sheet.)
- `music/lyrics/blueprints/anime-ending.yaml` is **present** (4422 B) — see §1. The
  planner anchor for this genre now exists.
- `~/Music` is still empty — **0** wav/mp3/flac files. But **a render now exists on this
  host**: the in-cluster render rail wrote `/var/lib/music-plans/elemental-fire-emberfall.flac`
  (11421612 B, mtime 15:52) and a loop cut at
  `/var/lib/music-plans/loops/elemental-fire-emberfall.loop.wav` (614444 B) plus its
  `.loop_points.json` (317 B). So "no render exists on this host" is no longer true; no
  *anime-ending* render exists, which is the claim that matters here.
- `campaigns/virtual-reflections/` **now exists on nexus**: `ALBUM-RECORD.md` (3807 B,
  commit `a97c760`). It records the album as live on Suno — album id
  `21e76d85-15f3-42d7-92a6-cf8a35248795`, owner `@reverb256`, **6 tracks · ~20:27**,
  **Draft** (private), Premier plan with commercial rights, stems and Studio present.
  `music/packages/` is still **absent** (measured).
  The CoS host note on `t_9546841b` (2026-10-16) — "the nexus copy of this repo is on a
  different branch with no campaigns/…" — is now false: the album record is in this
  tree's HEAD and the branch is `main`. Treat the note as history, and re-measure the
  host question before routing master/stem work anywhere.

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

1. **Brief queue** — ConfigMap `music-pipeline-briefs`, key `briefs.json`. It holds **11
   entries** live, and this genre's is one of them:
   `{"name":"anime-ending-reflections","genre":"anime-ending","title":"Reflections","language":"ja","duration":300,"lyricsMode":"draft"}`.
   *(Corrected in the surviving-card pass `t_9dfa74d9`, 15:56: this bullet said "one entry
   today" — `smoke-chill-lounge` only — when the brief was written. Card `t_a14e5d52` queued
   this brief later the same day.)* **The queue is not fed from `values.yaml`:** the live
   list comes from the Argo Application's inline `helm.values` override
   (`helm/apps/music-pipeline.yaml`), which wins on Helm precedence over the chart's
   `values.yaml` that `templates/configmap-briefs.yaml` reads. Both copies now carry the
   same 11 entries and `check-queue-sync.sh` fails when they disagree — measured by
   `t_a14e5d52`. So "add it to values.yaml" alone fails silently: the chart read
   `briefs: []` in git while the cluster served the live list.
2. **Planner** — CronJob `music-pipeline`, schedule `17 */6 * * *`, plans every brief
   that has no plan yet through `music/planner/planner.py`, and writes
   `/var/lib/music-plans/<name>.json` on the node.
3. **Render** — CronJob `music-pipeline-render`, schedule `41 */4 * * *`, renders every
   plan with no `.rendered` marker via `music/scripts/acestep_plan.py`, which posts to
   the sunolocal studio API (`http://sunolocal.mining.svc.cluster.local:8123`).
   *(Corrected: the run this bullet quoted, `done: found=3 rendered=0 skipped=3 failed=0`,
   was superseded.)* Latest render job, `music-pipeline-render-t6d7ad524` (created
   2026-10-16T20:15:26Z): `done: found=13 rendered=1 skipped=12 failed=0`.

So the route for this brief is a **queue entry**, not a kanban stage — **and it has already
been taken.** Live on nexus:

```
$ ls /var/lib/music-plans/anime-ending-reflections.*
/var/lib/music-plans/anime-ending-reflections.json      2989 B  14:10
/var/lib/music-plans/anime-ending-reflections.rendered     8 B  14:18   ("refused\n")
```

The plan is real (`"bpm": 92`, `"key": "C minor"`, `"language": "ja"`,
`_meta.blueprint: true`), and the render **refused it** — correctly. The scaffold carries
section tags but no sung lines, so no audio was made and no GPU was spent. That is the
state the lyrics stage has to change.

**The route the card names was dead. It is now repaired and armed in dry-run.** The card
says "Route to the pipeline driver". The driver is
`scripts/automation/pipeline-driver.sh --board music`. It could not route this card when the
brief was written, for two reasons. Both are fixed — measured 2026-10-16 15:56:

1. **The installed unit pointed at a checkout with no music lane.** *(Resolved 14:05.)*
   `~/.config/systemd/user/music-pipeline-driver.service` ran
   `/home/j_kro/Projects/ai-content-pipeline/scripts/automation/pipeline-driver.sh --board music`.
   `/home/j_kro/Projects` is a symlink to `/data/fast/home-relocated/Projects`, and that
   checkout (`9aa1a23`, branch `fix/driver-explicit-stage-advance`) has **no `music/`**.
   Its copy of the driver is the pre-parameterisation version: `BOARD="faceless-youtube"`
   hardcoded at line 25, no `--board` parsing — so it ignored the flag, walked the
   faceless-youtube board, and logged `dispatched 0` every 30 minutes.
   **Live now:** the installed unit (mtime Oct 16 14:05) runs
   `/bin/bash /home/j_kro/ai-content-pipeline/scripts/automation/pipeline-driver.sh --board music`
   with `WorkingDirectory=/home/j_kro/ai-content-pipeline`, and it walks the **music** board.
   `performance/pipeline-driver.log`, 2026-10-16T14:33:00–03, records
   `card t_2c99a1cb → stage brief`,
   `dispatching producer for card t_2c99a1cb (stage brief, board music)` and
   `pipeline driver run complete (board music, dispatched 37, running 3/99)`.
2. **Three of four installed units were stale, the driver among them.** *(Resolved
   13:08–15:32.)* `ade6e87` (13:09:58) committed the corrected paths in all four
   `music/scheduler/*.service` units and made `pipeline-driver.sh` resolve `REPO` from its
   git root. **All five** installed music units now run from
   `/home/j_kro/ai-content-pipeline`: `music-oracle.service` (mtime 14:04, runs
   `/usr/bin/python3 /home/j_kro/ai-content-pipeline/music/oracle.py`),
   `music-pipeline-driver.service` (14:05), `music-policy-watch.service` (14:04),
   `music-weekly-digest.service` (15:32) and the newer `music-gate-matrix.service` (15:22).
   The oracle succeeds — journal 13:08:45: `Cards created: 0`,
   `Cards skipped (genre already open): 14`. Nothing points at `~/Projects` any more.

**But the repaired driver still launches nothing: it is armed `DRY_RUN=1`.** The live unit
carries `Environment=DRY_RUN=1`, with a comment naming the reason — two mechanisms claim the
music board (this driver, and the generic kanban dispatcher that owns every oracle card), and
arming both double-dispatches every card. The gate is section 4 of card `t_41f354be`, a j_kro
decision. So the driver resolves card → stage → bot and logs
`[dry-run] would dispatch <bot>` without launching a bot. Recent timer runs also stop early on
the concurrency cap: `concurrency cap reached (1/1) — stopping dispatch` (15:00:02, 15:30:03).
**A card that advances by marker comment does not depend on this driver; the dispatcher path
does.** Treat "driver installed but dry-run" as an open route, not a closed one.

The oracle's pre-fix failure, for the record (the Errno line belongs to the Oct 15
run; Oct 16 08:00 fails with no python traceback line):

```
$ journalctl --user -u music-oracle.service --no-pager | grep -A4 "Oct 15 08:00"
Oct 15 08:00:00 nexus python3[185521]: /usr/bin/python3: can't open file
  '/home/j_kro/Projects/ai-content-pipeline/music/oracle.py': [Errno 2] No such file or directory
Oct 15 08:00:00 nexus systemd[1895]: music-oracle.service: Failed with result 'exit-code'.
Oct 16 08:00:00 nexus systemd[1895]: music-oracle.service: Main process exited, code=exited, status=2/INVALIDARGUMENT
Oct 16 08:00:00 nexus systemd[1895]: music-oracle.service: Failed with result 'exit-code'.
```

Evidence and routing for the host-path defect: comment added to the open ops card
`t_75aacf8b` (same "declared path does not match disk" class). That card is **done**.

**In-repo half, 2026-10-16 13:07 (commit `9c2d2d3`, card `t_38e84953`).** `advance-stage.sh` is
board-parameterized (it had `BOARD="faceless-youtube"` hardcoded, so a music card's stage
marker never moved), and all 12 producing prompts in `music/stages.yaml` now call it with
`--board music`. That is the path this card's own `stage: genre-select` marker uses.

**Route decision for this brief:** queue it in `briefs:`, with the payload gaps fixed first
(§8, items 1–3). That is a chart/GitOps change, so it was routed to `nexus-core` on card
`t_a14e5d52` rather than written from here.

**That routing is done.** (Corrected in the surviving-card pass — this paragraph used to be a
forward-looking decision; `t_a14e5d52` has since closed.) The queue entry is live (§7 step 1),
the payload carries the visual templates and the blueprint (§8 item 3), the entry planned to
`bpm 92` and was refused at render (§7), and the chart change is pushed (`01c37bc`, `e9d27f5`)
with Argo at `Synced / Healthy`. No routing action remains for this brief.

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
bpm/key  : 100 BPM · C minor · 4/4          <-- as written at 13:06
duration : 300s   language: ja
validation: PASS
next: write the lyrics into the plan, then run acestep_plan.py
```

**Re-measured 2026-10-16 15:54: the same command now prints `bpm/key  : 92 BPM · C minor ·
4/4` and writes `"bpm": 92, "blueprint": true` into `_meta`.** The 100 BPM line above is kept
as history — it is what the brief was written against, and item 1 below records what fixed it.

The structure matches the template's 10 sections, including the KEY LIFT. Two things in that
output were defects, not taste:

1. **BPM mismatch.** *(RESOLVED 2026-10-16 — kept for the record; the sibling card
   measured the cause more precisely than this brief did.)* The caption (which is what the
   engine reads) says **92 BPM**; the plan's `bpm` field said **100** because the draft path
   had no blueprint for this genre. Two things fixed it: `music/planner/planner.py` gained
   `bpm_in_caption()` (so the caption's own tempo is read instead of a flat 100), and
   `music/lyrics/blueprints/anime-ending.yaml` now exists with `bpm_anchor: 92` and the
   10-section structure (§1). Card `t_a14e5d52` measured the A/B in-cluster: without the
   blueprint `{"bpm": 92, "blueprint": false}`, with it `{"bpm": 92, "blueprint": true}` — so
   the blueprint's effect here is `structure_source: blueprint` and a tempo that is a repo
   decision, not a regex over prose. **Re-measured here on the lane repo, 15:54: `92 BPM`,
   `_meta.blueprint: true`.** The 100 this brief reported came from the lane checkout's
   then-stale `planner.py`, which lacked `bpm_in_caption()` — the brief was measuring a
   stale copy of the tool. Lesson recorded in §11.
2. **The draft is refused at render, by design.** Re-measured in the verification pass
   (`t_932abbb7`, 13:35): `/usr/bin/python3 music/scripts/acestep_plan.py
   <draft plan>` on the output of the run above exits **rc=1** with

   ```
   FATAL: 10 section(s) have no lyrics: Intro, Verse 1, Pre-Chorus, Chorus, Verse 2,
          Pre-Chorus, Chorus, Bridge, Final Chorus — KEY LIFT, Outro.
          This is a DRAFT plan — a human writes the lines into it first.
          (--allow-empty renders anyway, for instrumental or scratch passes.)
   ```

   *(The earlier wording of this item quoted a message the script does not emit —
   "FATAL: plan has empty lyrics — a draft section needs human input". The refusal is
   real and fires before any network call; the exact string is the one above, from
   `music/scripts/acestep_plan.py:82-86`.)* The render CronJob catches rc=1 and writes a
   `.refused` marker instead of retrying — read live from the deployed spec
   (`kubectl -n mining get cronjob music-pipeline-render -o yaml`, container `render`:
   `if r.returncode == 1: marker.write_text("refused\n")`). So queueing a draft **burns no
   GPU**. The gate to rendering this track is a **human-authored Japanese lyric sheet**.
   That is correct: AI-written lyrics void the copyright claim, which is the whole point
   of the lyrics stage (`gate_lyrics_original`).

Open items for `genre-select` / `lyrics` / `generate` (state re-measured 2026-10-16 15:56
— three of the five closed since the brief was written):

1. **OPEN — write the Japanese lyric sheet** (10 sections, human authorship, claim recorded
   by `music/lyrics/lyrics.py`). Nothing renders before this exists: the queued plan was
   refused at render for exactly this reason (§7). **This is the gate on this track.**
   `music/lyrics/anime-ending/` is absent (measured).
2. **CLOSED** — the anisong blueprint exists (4422 B) and the plan now reads `bpm 92`
   (item 1 above).
3. **CLOSED** — the payload gap was fixed as a class, not one file. `music-pipeline-payload`
   held no `music/visuals/**` at all; it now holds **39 keys**, including **14
   `music__visuals__*.md`** templates and 6 lyric blueprints (`music__lyrics__blueprints__*`).
   *(Still open and unrelated to the payload: `instrumental_version`, licence tiers and the
   clearance document for the `sync` and `direct-license` lanes.)*
4. **CLOSED** — the oracle board carries one card per genre. *(Corrected in the
   surviving-card pass: this item said "the leftover cards are not" cleaned up and named
   `t_bf0e5edd` as the owner. That card is **done**, and `music/scripts/check_oracle_board.py`
   passes live: 10 open cards across 10 genres, one each.)* The guard itself is unchanged:
   `open_oracle_genres()` in `music/oracle.py` skips a genre with an open card, and an
   unreadable board fails closed; `music/test_oracle_dedupe.py` is green. This brief's own
   card is the surviving one of the three (§11).
5. **PARTLY OPEN — this is album work.** The registry makes anime-ending track 9 of Virtual
   Reflections, and `campaigns/virtual-reflections/ALBUM-RECORD.md` (3807 B) now exists in
   this tree — so the album record is on nexus (§6). The album itself is on Suno: 6 tracks,
   **Draft**, owner `@reverb256`, album id `21e76d85-15f3-42d7-92a6-cf8a35248795`. What is
   still absent is the master/stem/package work for *this* track — `music/packages/` does not
   exist (measured). Re-measure the host question before routing that work (§6).

## 9. Provenance

- Registry: `music/genres.yaml`, `music/lanes.yaml` (validated live: 14 genres, 10 lanes)
- Template: `music/prompts/anime-ending.md` (5523 B) — caption 576 chars, 10 sections,
  weirdness 30%, style influence 80%, 6 exclude terms, tempo pocket 85–100
- Visual: `music/visuals/anime-ending.md` (2223 B)
- Gates: `music/gates/` — the eight gates this genre's lanes name are all present, and
  `gate_quota` was exercised live; the directory now holds **10** gates (`gate_human_approval`,
  `gate_loop_points` added since the brief was written)
- Quota: `music/quota-ledger.json` + `gate_quota` PASS (ledger also carries a `renders` list
  now — the durable render log, added by card `t_b8afb055`)
- Autonomy: `music/autonomy.yaml` (every lane `advisory`)
- Stage contract: `music/stages.yaml` (`brief` → bot `producer`)
- Planner: `music/planner/planner.py` (draft run above; now reads `bpm_in_caption()`)
- Live route: chart `music-pipeline` (`values.yaml`, `templates/configmap-briefs.yaml`,
  `templates/cronjob.yaml`, `templates/cronjob-render.yaml`), **the Argo Application's inline
  `helm.values` override** (`helm/apps/music-pipeline.yaml` — it wins over `values.yaml`),
  ConfigMap `music-pipeline-briefs`, host dir `/var/lib/music-plans`
- **Dangling reference — RESOLVED.** *(Corrected in the surviving-card pass.)*
  `brain/playbooks/music-lane-architecture.md` is cited as "READ FIRST" by this lane's profile,
  `stages.yaml`, `genres.yaml`, `lanes.yaml`, `autonomy.yaml`, `gates/README.md` and
  `gates/*.py`. Live now it **exists**: 34 328 B, tracked in HEAD, rewritten at `7411afa` (head touching
  it `6b24a52`).
  `brain/research/music-monetization-2026.md` exists too (11067 B), as does `brain/RULINGS.md`
  (4118 B). All three are absent from `origin/main` — they are committed locally only. So the
  section numbers this brief quotes from the architecture (§4, §5, §11.2) **are** checkable
  now, and the citations resolve.

## 10. Verification pass — the duplicate card `t_932abbb7` (2026-10-16 13:35)

This brief is keyed by genre, so the twin oracle card `t_932abbb7` (`score 7.85`) resolves to
this same file. It closed as a duplicate after re-measuring every checkable claim against live
state. Measured, not asserted:

| Claim | Re-measured how | Result |
|---|---|---|
| Artifact identity | `sha256sum`, `git log --follow -- music/briefs/anime-ending.md` | one commit before this pass (`4bb1ea6`), `2541feb8…`, `16549 B` |
| Registry 14 genres / 10 lanes | `/usr/bin/python3 music/registry.py validate` | OK — same genre and lane lists, `period 2026-10, standard 0/60` |
| Template 5523 B, visual 2223 B | `stat -c '%s %n'` | 5523, 2223 — match |
| Caption 576 chars; weirdness 30%; style influence 80%; 6 exclude terms | byte-length of the caption line; template settings lines | 576 (line 13), 30%, 80%, six terms — match |
| Eight gate files and their sizes | `stat` over `music/gates/*.py` | all eight present, byte-for-byte as written |
| Blueprint absent | `ls music/lyrics/blueprints/` | `activist.yaml`, `chill-lounge.yaml`, `trance.yaml` only |
| Lyric sheets absent; `~/Music` empty | `ls -R music/lyrics/`; `find ~/Music -type f` | three genre dirs + `lyrics.py`; **0** audio files |
| `campaigns/virtual-reflections/`, `music/packages/` absent | `ls -d` | both absent (`campaigns/` holds nine other campaigns) |
| Planner dry-run: 100 BPM vs caption 92, `_meta.blueprint false`, 10 sections, PASS | re-ran the same planner command; read the plan JSON | reproduced exactly — `bpm 100`, `key "C minor"`, `_meta.blueprint False`, caption 576, ten `[Section]` tags, `validation: PASS` |
| Draft refused at render | ran `acestep_plan.py` on that plan | rc=1, `FATAL: 10 section(s) have no lyrics: …` (string corrected — §8 item 2) |
| `.refused` marker exists | `kubectl -n mining get cronjob music-pipeline-render -o yaml` | present in the deployed container command |
| Queue holds one entry | `kubectl -n mining get configmap music-pipeline-briefs -o jsonpath` | `smoke-chill-lounge` only |
| Render job result | `kubectl -n mining logs job/music-pipeline-render-29869541` | `done: found=3 rendered=0 skipped=3 failed=0` |
| Plan dir | `ls -la /var/lib/music-plans` | three plans, all `.rendered` |
| Installed units | `grep ExecStart ~/.config/systemd/user/music-*.service` + journal | three of four reinstalled at 13:08; the driver unit is still stale — §7 corrected |
| Oracle duplicates | `ade6e87`, `music/test_oracle_dedupe.py` under unittest, oracle journal 13:08:45 | 12 tests OK; live run `0 created / 14 skipped` — §8 item 4 corrected |

Three corrections came out of the pass, all applied in place: §7's unit state, §8 item 2's
refusal string, §8 item 4's duplicate status. Every other claim stands as written.

The pass changed no registry value, gate, plan, or cluster config, and created no card: every
remaining blocker already has one — `t_a14e5d52` (queue this brief + payload gaps),
`t_75aacf8b` (host path; updated with the narrowed unit state), `t_bf0e5edd` (oracle duplicates).

**Those three cards are all `done` now, and the table above is a point-in-time record.** Four of
its rows went stale later the same day — the blueprint row, the queue count, the unit row and
the plan-dir row. §11 re-measures them and lists every correction.

## 11. Surviving-card pass — `t_9dfa74d9` (2026-10-16 15:56)

**Why this card exists.** The oracle emitted three cards for this one genre: `t_2541fd9c`
(7.65) and `t_932abbb7` (7.85) on 2026-10-09, ten minutes apart, and this card on 2026-10-16.
The oracle's ruling (posted on this card, and owned by card `t_bf0e5edd`, now done) is: **the
newest scoring run owns the genre, and the higher-scoring twin is never automatically right** —
an oracle score is a function of live state (quota ledger, registry lanes, calendar-driven
cadence, a live web fetch), so an older number cannot be reproduced and cannot win a tie. All
three cards resolve to THIS brief, because the brief is keyed by genre rather than by card.
**The brief stage is therefore already delivered — this pass does not re-run it.** The chain
resumes at the stage after `brief`, and this card posts `stage: genre-select` as its last act.

### Score — re-measured live, not transcribed

Read from `music/oracle.py` itself (`score_genre()` for this genre, plus a full `--dry-run`
sweep), 2026-10-16 15:54:

| Component | Weight | Live score | Contribution |
|---|---|---|---|
| quota headroom | 0.25 | 10.0 | 2.50 |
| lane coverage | 0.20 | 8.0 | 1.60 |
| revenue potential | 0.20 | 10.0 | 2.00 |
| cadence fit | 0.15 | 0.0 | 0.00 |
| policy risk | 0.10 | 10.0 | 1.00 |
| trend signal | 0.10 | 3.0 | 0.30 |
| **total** | **1.00** | | **7.40** |

- The `--dry-run` sweep printed `anime-ending: 7.4/10` in the same run. Threshold 5.0 → produce.
- `cadence_fit_score("1/wk")` returns **0.0** live (not the 1.7 the header carried): it is a
  function of days left in the period, and the period is nearly spent.
- The trend fetch timed out for all 14 genres in this run
  (`URLError(TimeoutError('timed out'))`), and the fixed scorer returns the no-signal floor
  (`TREND_NO_SIGNAL = 3.0`) for a failed fetch. **That failure is the whole 0.20 between 7.4 and
  the 7.6 in this card's title** — the premium the old `except` branch paid, removed in `b2d11f7`.
- The score table the header used to carry (7.65, cadence fit 1.7) was not reproducible: it was
  transcribed from a superseded run, not measured. Corrected in the header.

### Re-measured and unchanged

| Claim | Re-measured how | Result |
|---|---|---|
| Registry 14 genres / 10 lanes | `/usr/bin/python3 music/registry.py validate` | OK — same genre and lane lists, `period 2026-10, standard 0/60`, plus a stage-gate line the transcript omitted (§1) |
| Lanes and their requirements | `music/lanes.yaml` through the registry | `streaming` / `sync` / `direct-license` / `youtube-longform`, same gates and `requires` lists |
| Template 5523 B, visual 2223 B | `stat -c '%s %n'` | 5523, 2223 — match |
| Caption 576 chars, weirdness 30%, style influence 80%, 6 exclude terms, 10 template sections | template read + `check_prompt_style_counts.py` | PASS — all match |
| Eight lane-named gates present | `stat` over `music/gates/*.py` | present; sizes corrected for `gate_sync_ready` (§3) |
| `gate_quota` PASS | ran it | `period 2026-10 · 0/60 · studio exports 0` — verbatim match |
| Autonomy: every lane `advisory` | `music/autonomy.yaml` | match |
| Stage contract `brief` → bot `producer` | `music/stages.yaml` | match |
| Planner: 10 sections incl. KEY LIFT, `validation: PASS` | re-ran the planner command | match |
| Draft refused at render, exact string | ran `acestep_plan.py` on the fresh plan | **rc=1**, string matches §8 item 2 verbatim |
| `~/Music` holds 0 audio files | `find ~/Music -type f` | **0** — match |
| `music/packages/` absent | `ls -d` | absent — match |
| No `anime-ending` lyric sheet | `ls music/lyrics/` | absent — match |

### Corrections applied in place

1. **Header** — card identity (this card survives; the two 2026-10-09 cards are the superseded
   pair), the true score 7.4 with its component table, the superseded revision hash, and the
   repo revision (`1a450e00f05d1674ff03c49e7fd8073ea57ef29f`).
2. **§1 registry transcript** — the validator prints a stage-gate line; first line and gate line
   corrected to the live output.
3. **§1 blueprint row** — `anime-ending.yaml` now **PRESENT** (4422 B), not ABSENT.
4. **§3 gate sizes** — `gate_sync_ready` 9229 → **30038 B**; the directory holds **10** gates,
   not 8 (`gate_human_approval`, `gate_loop_points` were not in the original count).
5. **§6 assets** — `music/lyrics/` now also holds an `anime-opening` sheet; a render now exists
   on this host (`elemental-fire-emberfall.flac`, 11421612 B, plus a loop cut and its
   `.loop_points.json`); `campaigns/virtual-reflections/ALBUM-RECORD.md` (3807 B) now exists, so
   "do not exist anywhere on nexus" and the CoS host note are both corrected.
6. **§7 queue** — 11 entries live, this genre's among them; the queue is fed from the Argo
   Application's inline `helm.values`, not `values.yaml`.
7. **§7 unit state** — the stale `music-pipeline-driver.service` was reinstalled; all five
   installed music units now run from `/home/j_kro/ai-content-pipeline`, and the driver walks the
   music board (`dispatched 37`) — but it is armed `DRY_RUN=1`. Both "it is dead" bullets
   corrected, and the dry-run gate stated.
8. **§7 render evidence** — the quoted run was superseded; latest job
   `music-pipeline-render-t6d7ad524` → `done: found=13 rendered=1 skipped=12 failed=0`, and this
   brief's own plan is on disk with a `refused` marker.
9. **§8 item 1 (BPM)** — closed. Re-measured on the lane repo: `92 BPM`, `_meta.blueprint: true`.
   The brief's "100" came from a stale copy of `planner.py` lacking `bpm_in_caption()`.
10. **§8 items 2–5 and §9's dangling reference** — items 2, 3 and 4 closed; item 5 narrowed; the
    two `brain/` files this brief called dangling now exist on disk and in HEAD (absent from
    `origin/main`).

### Closed since the brief was written

`t_a14e5d52` (queue + payload gaps — **done**), `t_75aacf8b` (host path — **done**),
`t_bf0e5edd` (oracle duplicates — **done**). `music/scripts/check_oracle_board.py` passes live:
10 open oracle cards across 10 genres, one each.

### Still open

1. **The lyrics are the gate on this track.** A human-authored Japanese sheet for 10 sections
   (`music/lyrics/anime-ending/` is absent). Card `t_9917d23b` (writer) covers the scaffold
   and draft sheets; the human authorship claim is still j_kro's. Nothing renders before it —
   the queued plan was refused for exactly this reason (§7).
2. `instrumental_version`, `license_tiers` and a real `clearance_doc` for the `sync` and
   `direct-license` lanes. Still absent (§3).
3. **The kanban route is open but gated:** the board driver runs and routes correctly, armed
   `DRY_RUN=1` pending a j_kro decision on board ownership (card `t_41f354be` §4). Stage markers
   written by comment (the path this card uses) do not depend on it.
4. Master / stems / package for this track: not built. `music/packages/` is absent. The
   album record is now in this tree (§6), so re-measure the host question before routing it.
5. The payload carries 6 lyric blueprints; the repo has 7 (`jungle-dnb.yaml`, added 15:49, is
   not in the payload). Could be sync timing rather than a gap — unverified, so recorded, not
   filed.

### Checks run (all live, this pass)

```
check_brief_figures.py       FAIL rc=0 — 2 findings, both in other briefs (elemental-water,
                             epic-orchestral-boss); 71 recomputed OK. None in this file.
check_brief_drift.py         PASS rc=0 — 13 live counts match (0 behind / 70 ahead,
                             14 genres, 7 blueprints)
check_brief_line_refs.py     FAIL rc=0 — 5 failures, all in other briefs; this file's
                             citations hold
check_brief_paths.py         PASS rc=0 — 15 mining-k8s citations resolve
check_prompt_style_counts.py PASS rc=0 — 15 declared style-field lengths match
check_stage_scripts.py       PASS rc=0 — 11 referenced script paths present
check_oracle_board.py        PASS rc=0 — 10 open cards, one per genre
check_oracle_determinism.py  PASS rc=0 — a failed trend fetch never outscores an empty success
check_brief_absences.py      FAIL rc=1 — new in this pass; 15 findings across 8 briefs, none in
                             this file (card filed for the class)
```

(The FAILs in other briefs are pre-existing and already carded — `t_6dd13d76`, `t_e86c2110`,
`t_34f496d7`.)

### FAILURE → TEST

The class that let this brief rot is specific and was unchecked: **a brief asserting that a repo
path is absent, after the path appeared.** `check_brief_figures.py` skips a claim whose referent
the repo cannot prove, and `check_brief_paths.py` says in its own docstring that it deliberately
excludes `music/`, `brain/` and `campaigns/` because "briefs legitimately cite artifacts that
must not exist yet". That argument covers the absent-then-still-absent case and misses this one.

`music/scripts/check_brief_absences.py` is the regression for it: a line that asserts absence of
a *file* path under those roots, with no date / clock time / card id / commit on it and no
git-scoped framing, FAILs if the path exists. It found 15 stale claims across 8 sibling briefs
and none in this one (verified after the corrections above).
